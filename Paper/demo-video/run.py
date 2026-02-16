#!/usr/bin/env python3
"""
Lars Demo Video - Runner
=========================

Führt SCRIPT.json automatisch aus:
- Öffnet Chrome
- Navigiert zu Lars
- Führt alle Aktionen aus
- Spricht Narration (Qwen3-TTS)
- Nimmt Bildschirm auf

Nutzung:
    python run.py              # Startet Aufnahme
    python run.py --preview    # Zeigt nur Skript-Vorschau
    python run.py --audio      # Generiert nur Audio vorab
    python run.py --step 5     # Startet ab Schritt 5

Das Skript (SCRIPT.json) ist die einzige Wahrheitsquelle.
Bearbeite es direkt, um Änderungen vorzunehmen.
"""

import json
import time
import subprocess
import threading
import os
import sys
import hashlib
import random
import re
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import StaleElementReferenceException
except ImportError:
    print("📦 Installiere selenium...")
    subprocess.check_call(['pip', 'install', 'selenium', 'webdriver-manager', '-q'])
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import StaleElementReferenceException

try:
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    subprocess.check_call(['pip', 'install', 'webdriver-manager', '-q'])
    from webdriver_manager.chrome import ChromeDriverManager


# =============================================================================
# KONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_FILE = str(BASE_DIR / "SCRIPT.json")
AUDIO_DIR = str(BASE_DIR / "audio")
OUTPUT_DIR = str(BASE_DIR / "output")

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")
_ENV_CACHE: Optional[Dict[str, str]] = None


def _load_env_vars() -> Dict[str, str]:
    """Load environment variables with fallback to a .env file."""
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return _ENV_CACHE

    env = dict(os.environ)

    # Prefer .env from repo root or current working directory
    env_file = None
    search_roots = [Path.cwd(), *Path(__file__).resolve().parents]
    for root in search_roots:
        candidate = root / ".env"
        if candidate.exists():
            env_file = candidate
            break

    if env_file:
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[len("export "):]
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in env:
                    env[key] = value
        except Exception:
            pass

    _ENV_CACHE = env
    return env


def _resolve_env_placeholders(text: str) -> str:
    """Replace ${VARNAME} placeholders using env/.env."""
    if not text or "${" not in text:
        return text

    env = _load_env_vars()

    def repl(match: re.Match) -> str:
        key = match.group(1)
        value = env.get(key)
        if value is None:
            print(f"   ⚠️ Env var not found: {key}")
            return ""
        return value

    return ENV_VAR_PATTERN.sub(repl, text)


def _resolve_local_path(path_str: str) -> Path:
    """Resolve a relative path against CWD or the script directory."""
    if not path_str:
        return Path(path_str)
    path = Path(path_str)
    if path.is_absolute():
        return path
    cwd_candidate = (Path.cwd() / path)
    if cwd_candidate.exists():
        return cwd_candidate
    base_candidate = (BASE_DIR / path)
    if base_candidate.exists():
        return base_candidate
    return base_candidate

# Element-Mapping: Lesbare Namen → CSS Selektoren
# Lars nutzt eine Home-Seite mit Feature-Karten, keine Sidebar
ELEMENT_MAP = {
    # Problem Overlay (for highlighting during intro)
    "Problem Expert": "#problem-expert",
    "Problem Developer": "#problem-developer",
    "Problem Gap": "#problem-gap",
    "Problem Painpoints": "#problem-painpoints",
    "Problem Quote": "#problem-quote",

    # Pipeline Overlay Modules (for highlighting during intro)
    "Pipeline Prompt Engineering": "#pipeline-prompt",
    "Pipeline Batch Generation": "#pipeline-batch",
    "Pipeline Evaluation": "#pipeline-eval",
    "Pipeline Outcome": "#pipeline-outcome",
    "Pipeline Credentials": "#pipeline-credentials",

    # Home Page Feature Cards (klickbare Karten auf /Home)
    "Prompt Engineering": ".feature-card:contains('Prompt'), .feature-title:contains('Prompt')",
    "Batch Generation": ".feature-card:contains('Generation'), .feature-card:contains('Batch'), .feature-title:contains('Generation')",
    "Evaluation Hub": ".feature-card:contains('Evaluation'), .feature-title:contains('Evaluation')",
    "Evaluation": ".feature-card:contains('Evaluation'), .feature-title:contains('Evaluation')",
    "Scenarios": ".feature-card:contains('Scenario'), .feature-title:contains('Scenario')",
    "Scenario Manager": ".feature-card:contains('Scenario'), .feature-title:contains('Scenario')",
    "Dashboard": ".feature-card:contains('Dashboard'), .feature-title:contains('Dashboard')",

    # Buttons (Vuetify Buttons) - English UI
    "Create Prompt": ".v-btn:contains('New prompt'), .v-btn:contains('Create prompt'), button:contains('New prompt')",
    "New Prompt": ".v-btn:contains('New prompt'), .v-btn:contains('Create prompt')",
    "Create Job": ".v-btn:contains('New'), .v-btn:contains('Create'), button:contains('New')",
    "Create Scenario": ".v-btn:contains('Create'), button:contains('Create')",
    "Create": ".v-btn:contains('Create'), button[type='submit']",
    "Start Job": ".v-btn:contains('Start'), button:contains('Start')",
    "Test Prompt": ".v-btn:contains('Test'), button:contains('Test')",
    "Run Test": ".v-btn:contains('Run'), button:contains('Run')",
    "To Scenario": ".v-btn:contains('Scenario')",
    "Settings": ".user-menu-list .v-list-item:contains('Settings'), .v-btn:contains('Settings'), .v-icon.mdi-cog, button:contains('Settings')",
    "Export CSV": ".v-btn:contains('Export'), .v-btn:contains('CSV')",
    "Import External": ".v-btn:contains('Import'), button:contains('Import')",
    "Language Toggle": "[data-testid='language-toggle'] .language-toggle-btn, .language-toggle-wrapper .language-toggle-btn, .language-toggle-btn",
    "Language Option English": ".language-option:contains('English'), .v-list-item:contains('English'), button:contains('English')",
    "Language Option German": ".language-option:contains('Deutsch'), .v-list-item:contains('Deutsch'), button:contains('Deutsch')",

    # Prompt Engineering - Sidebar Actions (in .sidebar .actions-grid)
    # Note: Uses lowercase "block" as per en.json translation "New block"
    "New Block": ".actions-grid .l-btn, .sidebar .l-btn:first-child, .v-btn:contains('block'), .v-btn:contains('Block')",
    "Preview": ".v-btn:contains('Preview')",
    "Test": ".l-btn:contains('Test'), .v-btn:contains('Test'), .sidebar .l-btn:contains('Test'), .sidebar .v-btn:contains('Test')",
    "Manage Variables": ".l-btn:contains('Manage Variables'), .v-btn:contains('Manage Variables'), .l-btn:contains('Variables'), .v-btn:contains('Variables')",
    "Download": ".sidebar .l-btn:contains('Download'), .sidebar .v-btn:contains('Download'), .actions-grid .l-btn:contains('Download'), .actions-grid .v-btn:contains('Download')",
    "Import": ".sidebar .l-btn:contains('Import'), .sidebar .v-btn:contains('Import'), .actions-grid .l-btn:contains('Import'), .actions-grid .v-btn:contains('Import')",

    # Inputs (Vuetify Text Fields) - In Dialogs
    "Name Input": ".v-dialog .v-text-field input, .v-dialog input[type='text']",
    "Prompt Name Input": ".v-dialog .v-text-field input",
    "Block Name Input": ".v-dialog .v-text-field input",
    "Provider Name Input": ".v-dialog input[placeholder*='OpenAI'], .v-dialog input[aria-label='Name'], .v-dialog .v-text-field input[type='text']",
    "Provider API Key Input": ".v-dialog input[type='password'], .v-dialog input[aria-label='API Key']",
    "Provider Base URL Input": ".v-dialog input[placeholder*='Base URL'], .v-dialog input[aria-label*='Base URL']",
    "Provider Model Input": ".v-dialog .v-combobox input, .v-dialog .v-autocomplete input, .v-dialog .v-combobox, .v-dialog .v-autocomplete, .v-dialog .v-input:contains('Model'), .v-dialog .v-field:contains('Model'), .v-dialog input[aria-label*='Model'], .v-dialog input[placeholder*='Model'], .v-dialog input[placeholder*='model']",
    "Job Name": ".v-text-field input, input[placeholder*='Name']",
    "Scenario Name": ".v-text-field input, input[placeholder*='Name']",
    "Budget Limit": "input[type='number'], .v-text-field input",

    # Prompt Editor Blocks (Lars uses generic blocks + Quill editor)
    "System Block": ".editor-block:contains('System'), .block-title:contains('System')",
    "User Block": ".editor-block:contains('User'), .block-title:contains('User')",
    # Quill editor - direkt den contenteditable div finden
    "Block Content": ".ql-editor",
    "System Content": ".editor-block:first-child .ql-editor",
    "User Content": ".editor-block:last-child .ql-editor",
    # Block editor areas - einfach den letzten/ersten Block
    "System Block Editor": ".editor-block:first-child .ql-editor",
    "User Block Editor": ".editor-block:last-child .ql-editor",
    "Quill Editor": ".ql-editor",
    "First Block Editor": ".editor-block:first-child .ql-editor",
    "Last Block Editor": ".editor-block:last-child .ql-editor",

    # Test Prompt Dialog
    "Test Variables Preview": ".variables-panel, .variables-list, .variable-item",
    "Test Prompt Dialog": ".test-prompt-card, .v-dialog:contains('Test')",
    "Model Select": ".config-select, .llm-model-select, .v-select",
    "Regenerate": ".l-btn:contains('Regenerate'), .v-btn:contains('Regenerate'), .dialog-actions .l-btn:contains('Regenerate'), .dialog-actions .v-btn:contains('Regenerate')",
    "Response Output": ".response-section, .response-container, .response-text, .test-prompt-card .response-section",
    "Test Prompt Close": ".test-prompt-card .l-btn:contains('Close'), .test-prompt-card button:has(.mdi-close), .test-prompt-card .v-btn:has(.mdi-close)",
    "Close": ".v-dialog .l-btn:contains('Close'), .v-dialog .v-btn:contains('Close'), .wizard-header .v-btn, .l-btn:contains('Close'), .v-btn:contains('Close'), button:contains('Close')",
    "Cancel": ".v-btn:contains('Cancel'), button:contains('Cancel')",
    "Dialog Create Button": ".v-dialog .l-btn:contains('Create'), .v-dialog .v-btn:contains('Create'), .v-dialog button:contains('Create')",
    "Block Create Button": ".v-dialog--active .l-btn:contains('Create'), .v-overlay--active .l-btn:contains('Create')",
    "Prompt Card": ".prompt-card, .v-card:contains('Situation')",
    "Prompt Workspace": ".prompt-workspace, .blocks-container",
    "Collaboration Color": ".v-dialog .color-presets, .v-dialog .color-preview, .color-presets, .color-preview",
    "Collab Color Preset": ".v-dialog .color-presets .color-preset, .color-presets .color-preset",
    "Settings Dialog Close": ".v-dialog .v-card-title .v-btn, .v-dialog .v-card-title button",

    # Generation Wizard (Batch Generation)
    "Generation Wizard": ".generation-wizard, .v-dialog:contains('New Generation Job')",
    "First Model": ".generation-wizard .models-selection .selection-item:first-child, .models-selection .selection-item:first-child",
    "Second Model": ".generation-wizard .models-selection .selection-item:nth-child(2), .models-selection .selection-item:nth-child(2)",
    "Job Name Input": ".generation-wizard .config-form .v-text-field input, .generation-wizard .v-text-field input",

    # Scenario Wizard
    "Scenario Wizard": ".l-btn:contains('Scenario Wizard'), button.l-btn:contains('Scenario Wizard'), .header-actions .l-btn:contains('Scenario Wizard'), .v-btn:contains('Scenario Wizard')",
    "Ranking": ".type-card:contains('Ranking'), .type-name:contains('Ranking'), .v-list-item:contains('Ranking'), .v-radio:contains('Ranking'), label:contains('Ranking')",
    "LLM List": ".llm-category .llm-item, .llm-list .llm-item",
    "First LLM Evaluator": ".llm-category .llm-item, .llm-list .llm-item, .llm-item",
    "Second LLM Evaluator": ".llm-category .llm-item:nth-child(2), .llm-list .llm-item:nth-child(2), .llm-item:nth-child(2)",
    "OpenAI Provider": ".llm-item--user:contains('OpenAI'), .llm-category .llm-item:contains('OpenAI')",
    "Mistral LLM": ".llm-list .llm-item:contains('Mistral'), .llm-category .llm-item:contains('Mistral'), .llm-item:contains('Mistral')",
    "Magistral LLM": ".llm-list .llm-item:contains('Magistral'), .llm-category .llm-item:contains('Magistral'), .llm-item:contains('Magistral')",
    "GPT-5 LLM": ".llm-list .llm-item:contains('GPT-5'):not(:contains('Nano')):not(:contains('Mini')), .llm-category .llm-item:contains('GPT-5'):not(:contains('Nano')):not(:contains('Mini')), .llm-item:contains('gpt-5'):not(:contains('nano')):not(:contains('mini'))",
    "GPT-5 Mini LLM": ".llm-list .llm-item:contains('GPT-5 Mini'), .llm-category .llm-item:contains('GPT-5 Mini'), .llm-item:contains('gpt-5-mini')",
    "User List": ".user-list, .team-section .user-item",
    "Admin User": ".user-item:contains('admin'), .user-item:contains('Admin'), .user-name:contains('admin'), .user-name:contains('Admin')",
    "IJCAI Reviewer 1 User": ".user-item:contains('ijcai_reviewer_1'), .user-item:contains('IJCAI Reviewer 1'), .user-name:contains('ijcai_reviewer_1'), .user-name:contains('IJCAI Reviewer 1')",
    "IJCAI Reviewer 2 User": ".user-item:contains('ijcai_reviewer_2'), .user-item:contains('IJCAI Reviewer 2'), .user-name:contains('ijcai_reviewer_2'), .user-name:contains('IJCAI Reviewer 2')",
    "Create Scenario": ".wizard-actions .v-btn:contains('Create Scenario'), .wizard-actions .l-btn:contains('Create Scenario')",

    # =============================================
    # BATCH GENERATION - Wizard Steps
    # =============================================

    # Hub Buttons
    "New Job": ".header-actions .v-btn:contains('New Job'), .v-btn:contains('New Job')",
    "Create First Job": ".empty-state .v-btn:contains('Create')",

    # Wizard Navigation (inside wizard-actions footer - more specific)
    "Next": ".wizard-actions .l-btn:contains('Next'), .wizard-actions button.l-btn:contains('Next'), .generation-wizard .wizard-actions .l-btn, .v-card-actions .l-btn:contains('Next'), button:contains('Next')",
    "Back": ".wizard-actions .l-btn:contains('Back'), .generation-wizard .wizard-actions .l-btn:contains('Back')",
    "Create Job": ".wizard-actions .l-btn:contains('Create'), .generation-wizard .wizard-actions .l-btn:contains('Create')",

    # Step 1: Source Selection (inside wizard)
    "Source Scenario": ".generation-wizard .source-card:contains('Scenario'), .source-card:contains('Scenario')",
    "Source Upload": ".generation-wizard .source-card:contains('Upload'), .source-card:contains('Upload')",
    "Source Prompt Only": ".generation-wizard .source-card:contains('Prompt'), .source-card:contains('Prompt')",
    "Upload Zone": ".upload-zone",
    "File Input": ".upload-zone input[type='file'], input[type='file']",
    "Manual Data Textarea": ".generation-wizard .source-config textarea, .generation-wizard textarea",

    # Step 2: Prompt Templates (click to select) - in wizard overlay
    "Prompt Item": ".prompts-selection .selection-item",
    "First Prompt": ".prompts-selection .selection-item:first-child",
    "Structured Situation Analysis Item": ".prompts-selection .selection-item:contains('Structured Situation Analysis'), .selection-item:contains('Structured Situation Analysis'), .item-name:contains('Structured Situation Analysis'), .prompts-selection .selection-item:first-child",
    "Situation Summary Item": ".prompts-selection .selection-item:contains('Situation Summary'), .selection-item:contains('Situation Summary'), .item-name:contains('Situation Summary'), .prompts-selection .selection-item:nth-child(2)",

    # Step 3: Models (click to select) - in wizard overlay
    "Model Item": ".models-selection .selection-item",
    "First Model": ".models-selection .selection-item:first-child, .v-overlay--active .selection-item:first-child, .v-overlay--active .selectable-card:first-child",
    "Second Model": ".models-selection .selection-item:nth-child(2), .v-overlay--active .selection-item:nth-child(2), .v-overlay--active .selectable-card:nth-child(2)",
    "Mistral Model": ".models-selection .selection-item:contains('Mistral Small'), .models-selection .selection-item:contains('mistral'), .item-name:contains('mistral'), .models-selection .selection-item:first-child",
    "Magistral Model": ".models-selection .selection-item:contains('Magistral'), .models-selection .selection-item:contains('magistral'), .item-name:contains('Magistral')",
    "GPT-5 Nano Batch Model": ".models-selection .selection-item:contains('GPT-5 Nano'), .models-selection .selection-item:contains('gpt-5-nano'), .item-name:contains('gpt-5-nano')",
    "GPT-5 Batch Model": ".models-selection .selection-item:contains('GPT-5'):not(:contains('Nano')):not(:contains('nano')):not(:contains('Mini')):not(:contains('mini')), .models-selection .selection-item:contains('gpt-5'):not(:contains('nano')):not(:contains('mini'))",
    "GPT-4 Model": ".models-selection .selection-item:contains('gpt-4'), .models-selection .selection-item:contains('gpt4'), .item-name:contains('gpt')",
    "Claude Model": ".models-selection .selection-item:contains('claude'), .models-selection .selection-item:contains('Claude'), .item-name:contains('claude')",

    # Step 4: Configuration
    "Job Name Field": ".config-form .v-text-field input, .config-form input",
    "Temperature Slider": ".config-form .v-slider",
    "Max Tokens Field": ".config-form input[type='number']",
    "Budget Field": ".config-form .v-text-field input",

    # Step 5: Review (use actual class names from GenerationWizard.vue)
    "Matrix Preview": ".matrix-preview, .review-section:contains('Matrix')",
    "Cost Estimate": ".cost-estimate, .cost-value, .review-section:contains('Cost')",
    "Review Summary": ".review-summary",
    "Matrix Value": ".matrix-value",
    "Matrix Items Count": ".matrix-preview .matrix-item:nth-child(1)",
    "Matrix Prompts Count": ".matrix-preview .matrix-item:nth-child(3)",
    "Matrix Models Count": ".matrix-preview .matrix-item:nth-child(5)",
    "Matrix Total": ".matrix-item.total .matrix-value, .matrix-item.total",

    # Job Detail View
    "Start Job": ".header-actions .v-btn:contains('Start'), .v-btn:contains('Start')",
    "Pause Job": ".v-btn:contains('Pause')",
    "Cancel Job": ".v-btn:contains('Cancel')",
    "Progress Bar": ".v-progress-linear, .progress-fill, .card-progress-bar",
    "Outputs List": ".outputs-list",
    "Output Item": ".output-item",
    "Output Detail Dialog": ".v-dialog .output-detail, .v-dialog:has(.output-detail)",
    "Output Detail Meta": ".output-detail .output-detail-meta, .output-detail-meta",
    "Output Prompt": ".output-detail .prompt-pre, .output-detail .prompt-section",
    "Output System Prompt": ".output-detail .prompt-section:contains('System'), .prompt-section:contains('System')",
    "Output User Prompt": ".output-detail .prompt-section:contains('User'), .prompt-section:contains('User')",
    "Output Content": ".output-detail .content-pre, .output-detail .output-full-content",
    "Output Close": ".v-dialog .l-btn:contains('Close'), .v-dialog .v-btn:contains('Close'), .v-dialog button:contains('Close')",

    # Job Cards
    "Job Card": ".job-card",
    "Active Job Card": ".job-card.is-active",
    "Counselling Prompt": ".v-list-item:contains('Situation'), .prompt-item:contains('Situation')",

    # Evaluation Types
    "Ranking": ".type-card:contains('Ranking'), .type-name:contains('Ranking'), .v-list-item:contains('Ranking'), .v-radio:contains('Ranking'), label:contains('Ranking')",
    "Bucket Config": ".v-btn:contains('Bucket'), button:contains('Bucket')",
    "3 Buckets": ".v-list-item:contains('3'), .v-radio:contains('3')",
    "Enable LLM Evaluation": ".v-checkbox:contains('LLM'), .v-switch:contains('LLM'), input[type='checkbox']",
    "GPT-4 as Judge": ".v-list-item:contains('GPT-4'), .v-checkbox:contains('GPT')",
    "Start LLM Evaluation": ".v-btn:contains('Start'), button:contains('Start')",

    # Dashboard Elements
    "Agreement Matrix": ".ranking-agreement-matrix, .agreement-heatmap-section, .agreement-matrix, .summary-grid, .summary-card, .v-card:contains('Agreement')",
    "Krippendorff Alpha": ".metric:contains('Alpha'), .v-card:contains('Krippendorff')",
    "Disagreement Tab": ".v-tab:contains('Disagreement'), button:contains('Disagreement')",
    "Disagreement Chart": ".chart, .v-card:contains('Disagreement')",
    "Correlation Chart": ".chart, .v-card:contains('Correlation')",

    # Drag & Drop Items
    "Summary 1": ".eval-item:nth-child(1), .v-card:nth-child(1)",
    "Summary 2": ".eval-item:nth-child(2), .v-card:nth-child(2)",
    "Summary 3": ".eval-item:nth-child(3), .v-card:nth-child(3)",
    "Best Bucket": ".ranking-interface .buckets-row .bucket:nth-child(1), .ranking-interface .good-bucket",
    "Acceptable Bucket": ".ranking-interface .buckets-row .bucket:nth-child(2), .ranking-interface .moderate-bucket",
    "Poor Bucket": ".ranking-interface .buckets-row .bucket:nth-child(3), .ranking-interface .bad-bucket",

    # Misc
    "Test Output": ".test-result, .v-card:contains('Result'), .output",
    "Progress Bar": ".v-progress-linear, .progress-bar, .v-progress-circular",
    "Cost Estimate": ".cost-estimate, .cost-value, .review-section:contains('Cost')",
    "Import Dialog": ".v-dialog, .v-card.import",
    "Recommended: Ranking": ".recommendation, .v-chip:contains('Ranking')",
    "Counselling Situation Evaluation": ".v-card:contains('Situation'), .scenario-card:contains('Situation')",

    # =============================================
    # ADDITIONAL ELEMENTS FOR DEMO VIDEO
    # =============================================

    # Prompt Engineering - Variable Management
    "Variables Button": ".v-btn:contains('Variables'), .actions-grid .v-btn:contains('Variables')",
    "Variable Dialog": ".v-dialog:contains('Variable'), .variables-dialog",
    "Add Variable": ".v-btn:contains('Add'), .v-dialog .v-btn:contains('Add')",
    "Variable Name Input": ".variable-manager-card .name-input input, .variable-manager-card .new-variable-form input, .variable-input input",
    "Variable Content Input": ".variable-manager-card .content-input textarea, .variable-manager-card textarea",
    "Create Variable": ".variable-manager-card .create-btn, .variable-manager-card .l-btn:contains('Add Variable'), .variable-manager-card .l-btn:contains('Variable'), .variable-manager-card .v-btn:contains('Add Variable')",
    "Variable Dialog Body": ".variable-manager-card .dialog-body",
    "Variable Dialog Close": ".variable-manager-card .dialog-header .v-btn, .variable-manager-card .l-btn:contains('Close')",
    "Variable Save": ".v-btn:contains('Save'), .v-btn:contains('Done')",

    # Test Prompt Dialog - Enhanced
    "Run Test Button": ".v-btn:contains('Run'), .test-dialog .v-btn:contains('Generate'), .v-btn:contains('Generate')",
    "Test Response": ".response-section, .response-container, .response-text, .test-response, .v-card-text",
    "Test Loading": ".v-progress-circular, .loading",

    # Batch Generation - Job List
    "Completed Job": ".job-card.is-completed, .job-card.status-completed, .job-card:contains('Completed'), .job-card:contains('Abgeschlossen'), .job-item:contains('100%')",
    "Demo Job": ".job-card:contains('Counselling'), .job-card:contains('Situation')",
    "Job Status": ".job-status, .status-chip",
    "Job Progress": ".job-progress, .progress-bar",
    "View Results": ".v-btn:contains('Results'), .v-btn:contains('View')",
    "Export Results": ".v-btn:contains('Export')",

    # Batch to Scenario
    "Create Scenario Button": ".v-btn:contains('Create Scenario'), .v-btn:contains('To Scenario'), .header-actions .v-btn:contains('Scenario')",
    "Scenario Type Select": ".v-select:contains('Type'), .scenario-type-select",
    "Ranking Type": ".v-list-item:contains('Ranking'), .v-menu .v-list-item:contains('Ranking')",
    "Rating Type": ".v-list-item:contains('Rating'), .v-menu .v-list-item:contains('Rating')",

    # Evaluator Selection
    "Add Evaluator": ".v-btn:contains('Add Evaluator'), .v-btn:contains('Add')",
    "Evaluator Select": ".v-select:contains('Evaluator'), .evaluator-select",
    "Human Evaluator": ".v-list-item:contains('admin'), .v-list-item:contains('human')",
    "LLM Evaluator": ".v-list-item:contains('LLM'), .v-checkbox:contains('LLM')",
    "GPT-4 Evaluator": ".v-list-item:contains('GPT-4'), .v-checkbox:contains('GPT')",
    "Claude Evaluator": ".v-list-item:contains('Claude'), .v-checkbox:contains('Claude')",

    # Scenario Manager
    "New Scenario": ".v-btn:contains('New Scenario'), .header-actions .v-btn:contains('New')",
    "Scenario List": ".scenario-list, .scenarios-grid, .scenario-cards, .v-list",
    "Scenario Card": ".scenario-card, .v-card.scenario",
    "Counselling Demo Scenario": ".scenario-card:contains('IJCAI Counselling Evaluation'), .v-card:contains('IJCAI Counselling Evaluation'), .scenario-name:contains('IJCAI Counselling Evaluation')",
    "Completed Scenario": ".scenario-card:contains('Complete'), .scenario-card.completed",
    "Demo Scenario": ".scenario-card:contains('Counselling'), .scenario-card:contains('Situation')",
    "Scenario Stats": ".scenario-stats, .stats-card",
    "Open Scenario": ".v-btn:contains('Open'), .scenario-card .v-btn",
    "Scenario Workspace": ".scenario-workspace",
    "Scenario Workspace Back": ".scenario-workspace .back-btn, .scenario-workspace .v-btn.back-btn",
    "Scenario Manager Title": ".scenario-manager .title, .page-header .title:contains('Scenario Manager'), h1.title:contains('Scenario Manager')",
    "Scenario Tabs": ".scenario-workspace .l-tabs, .tab-navigation .l-tabs, .l-tabs",
    "Scenario Tab Overview": ".tab-navigation .l-tab:contains('Overview'), .l-tab:contains('Overview'), .l-tab__label:contains('Overview')",
    "Scenario Tab Data": ".tab-navigation .l-tab:contains('Data'), .l-tab:contains('Data'), .l-tab__label:contains('Data')",
    "Scenario Tab Evaluation": ".tab-navigation .l-tab:contains('Evaluation'), .l-tab:contains('Evaluation'), .l-tab__label:contains('Evaluation')",
    "Scenario Tab Team": ".tab-navigation .l-tab:contains('Team'), .l-tab:contains('Team'), .l-tab__label:contains('Team')",
    "Scenario Live Badge": ".live-badge .live-dot, .live-dot, .stat-item.live-indicator .live-dot",
    "Scenario Progress Cards": ".progress-cards, .progress-card",
    "Scenario Evaluator List": ".evaluators-list, .evaluator-row",
    "Scenario LLM Progress": ".progress-fill.llm, .progress-fill.is-llm, .progress-bar-large .progress-fill, .progress-card .progress-fill, .progress-mini .progress-fill",
    "Evaluation Summary": ".evaluation-tab .summary-grid, .evaluation-tab .summary-card",
    "Evaluation Progress": ".evaluation-tab .progress-bar-container, .evaluation-tab .progress-bar-fill, .evaluation-tab .total-progress-section",
    "Evaluation Export": ".evaluation-tab .header-actions .l-btn, .evaluation-tab .header-actions .v-btn, .evaluation-tab .l-btn:contains('Export')",
    "Export JSON": ".v-list-item:contains('JSON')",
    # Scenario Data Tab
    "Data Stats": ".data-tab .data-stats, .data-stats",
    "Data Threads Table": ".data-tab .threads-table, .data-tab .threads-section, .data-tab .empty-state, .threads-table, .threads-section",
    "Data Status Legend": ".data-tab .status-legend, .data-tab .empty-state, .status-legend",
    # Scenario Team Tab
    "Team Members List": ".team-tab .members-list, .members-list",
    "Team Invite Button": ".team-tab .tab-header .l-btn, .team-tab .l-btn:contains('Invite'), .team-tab .l-btn:contains('Add')",
    "Team Add LLM Button": ".team-tab .section-header .l-btn, .team-tab .l-btn:contains('Add LLM'), .team-tab .l-btn:contains('LLM')",
    "Team Member Menu": ".team-tab .member-actions .v-btn, .team-tab .member-actions button",
    "Scenario Wizard Close": ".scenario-wizard .wizard-header .v-btn",
    # Human Evaluation (Evaluation Hub + Ranking UI)
    "Evaluation Scenario Card": ".overview-content .scenario-card:contains('IJCAI Counselling Evaluation'), .scenarios-grid .scenario-card:contains('IJCAI Counselling Evaluation'), .scenario-card:contains('IJCAI Counselling Evaluation')",
    "Evaluation Items Grid": ".items-grid, .items-content",
    "Evaluation Item Card": ".items-grid .item-card:first-child, .item-card:first-child",
    "Evaluation In Progress Filter": ".filter-chip.in-progress:contains('In progress'), .filter-chip.in-progress:contains('In Progress'), .filter-chip.in-progress:contains('In Arbeit')",
    "Evaluation In Progress Item Card": ".items-grid .item-card.status-in_progress, .item-card.status-in_progress, .items-grid .item-card:first-child, .item-card:first-child",
    "Ranking Interface": ".ranking-interface",
    "Ranking Buckets": ".ranking-interface .buckets-row, .ranking-interface .bucket, .ranking-interface .neutral-bucket, .preview-ranking .buckets-preview, .buckets-preview .bucket-box",
    "Ranking Content": ".ranking-interface .right-panel, .ranking-interface .panel-content, .ranking-interface .content-text",
    "Ranking Item": ".ranking-interface .neutral-bucket .bucket-item:first-child, .ranking-interface .neutral-content .bucket-item:first-child, .ranking-interface .bucket-item:first-child",

    # Scenario Wizard (Button text is "Scenario Wizard")
    "Wizard Button": ".l-btn:contains('Scenario Wizard'), .l-btn:contains('Wizard'), .v-btn:contains('Scenario Wizard'), .v-btn:contains('Wizard')",
    "Scenario Wizard": ".l-btn:contains('Scenario Wizard'), button.l-btn:contains('Scenario Wizard'), .header-actions .l-btn:contains('Scenario Wizard'), .v-btn:contains('Scenario Wizard')",
    "Wizard Dialog": ".scenario-wizard, .wizard-dialog, .v-dialog",
    "Wizard Upload": ".wizard-upload, .upload-zone",
    "Wizard Analysis": ".wizard-analysis, .ai-analysis",
    "Wizard Recommendation": ".wizard-recommendation, .ai-recommendation, .recommendation-card",
    "Wizard Create": ".v-btn:contains('Create'), .wizard-actions .v-btn",

    # Evaluation View
    "Evaluation Items": ".evaluation-items, .items-list",
    "Rating Scale": ".rating-scale, .v-rating",
    "Submit Rating": ".v-btn:contains('Submit'), .v-btn:contains('Next')",
    "Results Tab": ".v-tab:contains('Results'), .v-tab:contains('Statistics')",
    "Agreement Chart": ".agreement-chart, .chart-container",

    # =============================================
    # DEMO VIDEO - Pre-seeded Data Selectors
    # =============================================

    # Home Page - Feature Cards
    "Feature Cards": ".feature-cards, .home-features, .v-row .v-col .v-card",

    # Prompt Engineering - Existing Prompts (seeded by seed_demo_video_data)
    "Structured Situation Analysis": ".prompt-card:contains('Structured Situation Analysis'), .v-card:contains('Structured Situation Analysis'), .prompt-list-item:contains('Structured Situation Analysis')",
    "Situation Summary": ".prompt-card:contains('Situation Summary'), .v-card:contains('Situation Summary'), .prompt-list-item:contains('Situation Summary')",

    # Prompt Engineering - Collaboration
    "Collab Indicator": ".collab-indicator, .user-presence, .collaboration-status, .yjs-status, .online-users",

    # Batch Generation - Existing Jobs (seeded by seed_demo_video_data)
    "Counselling Situation Extraction": ".job-card.is-completed:contains('Counselling Situation Extraction'), .job-card:contains('Counselling Situation Extraction'), .job-row:contains('Counselling Situation'), .v-list-item:contains('Counselling Situation')",
    "Job Summary": ".job-summary, .job-stats, .stats-card, .v-card .stats, .job-info",
    "Job Details": ".job-details, .job-detail-view, .v-card:contains('Details')",
    "Job Outputs": ".outputs-list, .output-cards, .generated-outputs",
    "Cost Display": ".cost-display, .total-cost, .v-chip:contains('$'), .cost-info",

    # Scenario Manager
    "First Scenario Card": ".scenario-card:first-child, .scenarios-grid .v-card:first-child, .scenario-list > *:first-child",
    "Scenario Wizard Button": ".l-btn:contains('Wizard'), .l-btn:contains('Scenario Wizard'), .v-btn:contains('Wizard'), .v-btn:contains('Scenario Wizard'), .wizard-btn",
    # User Settings - LLM Providers
    "User Settings Providers Tab": ".settings-sidebar .nav-item:contains('LLM Providers'), .settings-sidebar .nav-item:contains('Providers')",
    "User Settings Personal Tab": ".settings-sidebar .nav-item:contains('Personal'), .settings-sidebar .nav-item:contains('Profil'), .settings-sidebar .nav-item:contains('Profile')",
    "Language Options": ".language-options, .settings-panel:contains('Language'), .settings-panel:contains('Sprache')",
    "Providers Info": ".llm-providers .v-alert, .llm-providers .v-alert__content",
    "Add Provider": ".llm-providers .l-btn:contains('Add Provider'), .llm-providers .v-btn:contains('Add Provider')",
    "Provider Dialog": ".v-overlay--active .v-dialog, .v-dialog",
    "Provider Type Select": ".v-dialog .v-select",
    "Provider Type Options": ".v-overlay--active .v-list-item",
    "Provider Type OpenAI": ".v-overlay--active .v-list-item:contains('OpenAI'), .v-overlay--active .v-list-item:contains('openai')",
    "OpenAI Provider Card": ".provider-card:contains('OpenAI'), .provider-name:contains('OpenAI')",
    "Provider Model Select": ".v-dialog .v-select:contains('Modelle'), .v-dialog .v-select:contains('OpenAI')",
    "GPT-5 Nano Select Option": ".v-overlay--active .v-list-item:contains('GPT-5 Nano')",
    "GPT-5 Mini Select Option": ".v-overlay--active .v-list-item:contains('GPT-5 Mini')",
    "Sync Models Button": ".l-btn:contains('Sync'), .v-btn:contains('Sync'), .l-btn:contains('sync')",
    "Model List": ".model-list, .v-list:has(.v-list-item)",
    "GPT-5 Nano Model": ".v-list-item:contains('gpt-5-nano'), .v-list-item:contains('GPT-5 Nano'), .model-item:contains('gpt-5-nano')",
    "GPT-5 Model": ".v-list-item:contains('gpt-5'):not(:contains('nano')):not(:contains('mini')):not(:contains('5.')), .model-item:contains('gpt-5'):not(:contains('nano'))",
    # =============================================
    # VERSION CONTROL (Git Panel in Prompt Engineering)
    # =============================================

    # Sidebar Git Widget (PromptGitPanel.vue in sidebar)
    "Git Panel Section": ".sidebar-section:has(.vc-block-list), .sidebar-section:has(.git-panel-expanded), .sidebar-section:has(.git-panel-collapsed)",
    "Git Panel": ".git-panel-expanded, .git-panel-wrapper, .git-panel-collapsed",
    "Version Control Panel": ".git-panel-expanded, .git-panel-wrapper, .vc-block-list, .git-panel-collapsed, .sidebar-section:has(.vc-block-list)",
    "Git Widget Header": ".git-panel-expanded .panel-header, .panel-header",
    "Git Widget Status": ".git-panel-expanded .panel-content, .vc-block-list",
    "Version Control Status": ".vc-block-list, .vc-commit-section, .git-panel-expanded .commit-section, .change-indicator",
    "Git Commit Section": ".vc-commit-section, .commit-section",
    "Git Commit Input": ".vc-commit-input input, .commit-input input, .vc-commit-section input",
    "Git Commit Button": ".vc-commit-section .l-btn, .commit-actions .l-btn:contains('Commit'), .commit-actions .l-btn",
    "Git User Changes": ".user-changes .user-change-item, .user-change-item",
    "Git Change Stats": ".change-indicator, .vc-stat, .stat-badge",
    # Floating Git Panel (PromptFloatingGitPanel.vue)
    "Git Open Floating": ".sidebar-section .section-label .v-btn:contains('mdi-open-in-new'), .sidebar-section .section-label .v-btn[title*='Versionskontrolle'], .sidebar-section .section-label .v-btn[title*='version control'], .sidebar-section .section-label .v-btn:last-of-type",
    "Git Fullscreen Button": ".sidebar-section .section-label .v-btn:contains('mdi-open-in-new'), .sidebar-section .section-label .v-btn[title*='Versionskontrolle'], .sidebar-section .section-label .v-btn[title*='version control'], .sidebar-section .section-label .v-btn:last-of-type",
    "Version Control Fullscreen": ".sidebar-section .section-label .v-btn:contains('mdi-open-in-new'), .sidebar-section .section-label .v-btn[title*='Versionskontrolle'], .sidebar-section .section-label .v-btn[title*='version control'], .sidebar-section .section-label .v-btn:last-of-type",
    "Git Floating Panel": ".l-floating-window, .git-panel-content",
    "Git Floating Panel Close": ".l-floating-window button[aria-label='Close'], .l-floating-window .header-actions button.l-icon-btn:last-of-type, .l-floating-window .header-actions .v-btn:last-of-type",
    "Git History Section": ".history-section, .history-list, .git-panel-content .history-list",
    "Git History Item": ".history-item, .history-list .history-item:first-child",
    "Git Commit Message": ".commit-message",
    "Git Commit Indicator": ".commit-indicator",
    "Git Block Item": ".block-item, .block-list .block-item:first-child",
    "Git Rollback Button": ".block-item .v-btn:has(.mdi-undo)",
    "Git Diff Viewer": ".diff-viewer, .commit-diff-content",

    # =============================================
    # AGREEMENT METRICS (ScenarioEvaluationTab.vue)
    # =============================================

    "Metrics Section": ".metrics-section, .metrics-grid",
    "Metrics Grid": ".metrics-grid",
    "Metric Item": ".metric-item",
    "Metric Value": ".metric-value",
    "Metric Label": ".metric-label",
    "Cohen Kappa Metric": ".metrics-grid .metric-item:nth-child(1)",
    "Krippendorff Alpha Metric": ".metrics-grid .metric-item:nth-child(2)",
    "Fleiss Kappa Metric": ".metrics-grid .metric-item:nth-child(3)",
    "Accuracy Metric": ".metrics-grid .metric-item:nth-child(4)",
    "ICC Metric": ".metrics-grid .metric-item:nth-child(5)",
    "Kendall W Metric": ".metrics-grid .metric-item:nth-child(6)",
    "Agreement Heatmap": ".l-agreement-heatmap, .agreement-heatmap-section, .heatmap-container, .visualization-panel",
    "Heatmap Cell": ".heatmap-cell",
    "Heatmap Grid": ".heatmap-container",
    "Agreement Detail Dialog": ".agreement-detail-dialog .agreement-detail-card, .agreement-detail-card",
    "Agreement Detail Score": ".agreement-detail-card .score-circle, .agreement-detail-body .score-circle",
    "Agreement Detail Breakdown": ".agreement-detail-card .agreement-breakdown, .agreement-breakdown",

    # =============================================
    # ITEM DISTRIBUTION (ScenarioWizard.vue Step 3)
    # =============================================

    "Distribution Settings": ".distribution-settings",
    "Distribution Mode": ".distribution-settings .config-section:first-of-type, .distribution-settings .config-section:nth-of-type(1)",
    "Order Mode": ".distribution-settings .config-section:nth-of-type(2)",
    "LLM Evaluation Toggle": ".distribution-settings .config-section:nth-of-type(3)",
}


# =============================================================================
# TTS
# =============================================================================

class TTS:
    """TTS-Wrapper mit Sprecher-Unterstützung"""

    # Default Sprecher-Konfigurationen für Qwen3-TTS Voice Cloning
    DEFAULT_SPEAKERS = {
        "moderator": {"name": "Alex", "ref_audio": str(BASE_DIR / "voices" / "alex_reference.wav")},
        "guest": {"name": "David", "ref_audio": str(BASE_DIR / "voices" / "david_reference.wav")},
        "default": {"name": "Default", "ref_audio": None},
    }

    def __init__(self, model_size: str = "small", speakers: dict = None, use_voice_cloning: bool = False):
        self.model_size = model_size
        self.use_voice_cloning = use_voice_cloning
        self.speakers = {**self.DEFAULT_SPEAKERS}
        if speakers:
            for speaker_id, config in speakers.items():
                if speaker_id in self.speakers:
                    self.speakers[speaker_id].update(config)
                else:
                    self.speakers[speaker_id] = config

        self._engine = None
        self._loaded = False
        Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)

    def get_speaker_config(self, speaker_id: str) -> dict:
        """Gibt Sprecher-Konfiguration zurück"""
        return self.speakers.get(speaker_id, self.speakers.get("default", {}))

    def preload(self):
        """Lädt das TTS-Modell vorab (blocking)"""
        if self._loaded:
            return

        print("\n" + "="*60)
        print("🎤 TTS-MODELL WIRD GELADEN")
        print("="*60)
        print(f"   Modell: {self.model_size}")
        print(f"   Sprecher: {', '.join(self.speakers.keys())}")
        print("   Dies kann beim ersten Mal mehrere Minuten dauern...")
        print("="*60 + "\n")

        engine = self._get_engine()

        # Modell wirklich laden (nicht nur Engine initialisieren)
        engine._load_model()

        self._loaded = True
        print("\n✓ TTS-Modell geladen und bereit!\n")

    def _get_engine(self):
        if self._engine is None:
            from src.tts import QwenTTS
            self._engine = QwenTTS(
                model_size=self.model_size,
                cache_dir=AUDIO_DIR,
                speakers=self.speakers,
                use_voice_cloning=self.use_voice_cloning
            )
        return self._engine

    def speak(self, text: str, step_id: str, speaker: str = "default"):
        """Spricht Text (blockierend)"""
        audio_file = f"{AUDIO_DIR}/{step_id}.wav"

        if not os.path.exists(audio_file):
            engine = self._get_engine()
            engine.generate(text, audio_file, speaker=speaker)

        # Abspielen
        self._play(audio_file)

    def _generate_qwen(self, text: str, output_path: str, speaker: str = "default"):
        """Generiert Audio mit Qwen3-TTS"""
        engine = self._get_engine()
        engine.generate(text, output_path, speaker=speaker)

    def _play(self, audio_file: str):
        """Spielt Audio ab"""
        import platform
        if platform.system() == 'Darwin':
            subprocess.run(['afplay', audio_file], capture_output=True)
        else:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', audio_file], capture_output=True)

    def speak_async(self, text: str, step_id: str) -> threading.Thread:
        """Spricht Text (nicht-blockierend)"""
        thread = threading.Thread(target=self.speak, args=(text, step_id))
        thread.start()
        return thread


# =============================================================================
# TIMELINE - Präzises Action-Timing synchron zur Narration
# =============================================================================

class Timeline:
    """
    Ermöglicht präzise Synchronisation von Aktionen mit der Narration.

    Aktionen laufen SEQUENTIELL - in der Reihenfolge wie im Script definiert.
    Nur 'sync' pausiert und wartet auf einen bestimmten Punkt in der Narration.

    TIMING-BEFEHLE:
    - {"do": "sync", "after": "click"} → Wartet bis TTS "click" gesagt hat
    - {"do": "sync", "at": 3.5}        → Wartet bis Sekunde 3.5
    - {"do": "sync", "at": "50%"}      → Wartet bis 50% der Narration

    HIGHLIGHT VOR KLICK:
    - {"do": "click", "target": "X", "highlight_before": 2}
      → Highlightet Element 2 Sekunden, dann klickt

    BEISPIEL:
    {
      "narration": "Now I'll click on Create to make a new prompt.",
      "actions": [
        {"do": "sync", "after": "click on"},
        {"do": "click", "target": "Create Prompt", "highlight_before": 1.5},
        {"do": "wait_for_modal"},
        {"do": "type", "target": "Name Input", "text": "My Prompt"}
      ]
    }
    """

    # Durchschnittliche Sprechgeschwindigkeit (Wörter pro Sekunde)
    WORDS_PER_SECOND = 2.5

    def __init__(self, narration: str, audio_duration: float, start_time: float):
        self.narration = narration
        self.audio_duration = audio_duration
        self.start_time = start_time
        self.words = narration.split()
        self.word_count = len(self.words)

        # Berechne Zeit pro Wort basierend auf tatsächlicher Audio-Dauer
        if self.word_count > 0 and audio_duration > 0:
            self.time_per_word = audio_duration / self.word_count
        else:
            self.time_per_word = 1.0 / self.WORDS_PER_SECOND

    def get_sync_time(self, sync_spec: dict) -> float:
        """
        Berechnet den Zeitpunkt (in Sekunden ab Start) für einen Sync-Punkt.
        """
        # Explizite Zeit in Sekunden
        if 'at' in sync_spec:
            at = sync_spec['at']
            if isinstance(at, (int, float)):
                return float(at)
            elif isinstance(at, str) and at.endswith('%'):
                percent = float(at.rstrip('%')) / 100.0
                return self.audio_duration * percent

        # Nach bestimmtem Wort/Phrase
        if 'after' in sync_spec:
            phrase = sync_spec['after'].lower()
            text_lower = self.narration.lower()

            # Finde Position der Phrase
            pos = text_lower.find(phrase)
            if pos >= 0:
                # Zähle Wörter bis zu dieser Position
                words_before = len(text_lower[:pos + len(phrase)].split())
                return words_before * self.time_per_word
            else:
                print(f"      ⚠️ Phrase '{phrase}' nicht in Narration gefunden!")
                return 0.0

        return 0.0

    def wait_until(self, target_time: float):
        """
        Wartet bis der angegebene Zeitpunkt in der Narration erreicht ist.
        """
        elapsed = time.time() - self.start_time
        wait_time = target_time - elapsed
        if wait_time > 0:
            time.sleep(wait_time)
            return wait_time
        return 0.0

    @staticmethod
    def estimate_duration(narration: str) -> float:
        """Schätzt Audio-Dauer basierend auf Wortanzahl (für Vorschau)"""
        words = len(narration.split())
        return words / Timeline.WORDS_PER_SECOND


# =============================================================================
# SCREEN RECORDER
# =============================================================================

class Recorder:
    """Screen Recorder mit Audio-Sync Post-Processing"""

    # Ziel-Auflösung für das Video
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080

    # Audio-Verstärkung (1.0 = normal, 2.0 = doppelt so laut)
    AUDIO_VOLUME = 3.0

    def __init__(self, output_file: str, window_bounds: tuple = None):
        # Verhindere doppeltes output/
        if output_file.startswith('output/'):
            output_file = output_file[7:]
        self.output_file = output_file
        self.process = None
        self.start_time = None
        self.timestamps = []  # [(relative_time, audio_file), ...]
        self.window_bounds = window_bounds  # (x, y, width, height) für Crop
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _find_screen_device() -> str:
        """Find the correct avfoundation screen capture device index.

        Device indices change when iPhones/iPads are connected.
        We search for 'Capture screen 0' in the device list.
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True, text=True, timeout=10
            )
            # Parse: [AVFoundation indev @ ...] [3] Capture screen 0
            for line in result.stderr.split('\n'):
                if 'Capture screen 0' in line:
                    match = re.search(r'\[(\d+)\]', line)
                    if match:
                        idx = match.group(1)
                        print(f"   🖥️ Screen capture device: [{idx}] Capture screen 0")
                        return idx
        except Exception:
            pass
        print("   ⚠️ Screen device not found, falling back to '3'")
        return '3'

    @staticmethod
    def _probe_capture_resolution(device_idx: str) -> tuple:
        """Probe actual ffmpeg avfoundation capture resolution.

        On Retina Macs, capture resolution = 2x the "Looks like" logical resolution.
        This may differ from the native panel resolution.
        """
        try:
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-framerate', '1',
                 '-i', f'{device_idx}:none', '-frames:v', '1', '-y', '/dev/null'],
                capture_output=True, text=True, timeout=10
            )
            match = re.search(r'(\d{3,5})x(\d{3,5})', result.stderr)
            if match:
                w, h = int(match.group(1)), int(match.group(2))
                print(f"   🖥️ Capture resolution: {w}x{h}")
                return w, h
        except Exception:
            pass
        return None, None

    def start(self):
        """Startet Aufnahme (ohne Audio)

        Handles macOS Retina displays correctly:
        1. Finds the correct screen capture device (not iPhone camera)
        2. Probes actual capture resolution (e.g. 3600x2338 on scaled Retina)
        3. Clamps crop to actual capture bounds (Chrome may extend off-screen)
        4. Scales final output to 1920x1080
        """
        import platform

        # Raw video (ohne Audio)
        self.raw_video = os.path.join(OUTPUT_DIR, "raw_" + self.output_file)
        self.final_output = os.path.join(OUTPUT_DIR, self.output_file)

        if platform.system() == 'Darwin':
            # Find correct screen capture device
            screen_device = self._find_screen_device()

            if self.window_bounds:
                x, y, w, h = self.window_bounds

                # Probe actual capture resolution
                cap_w, cap_h = self._probe_capture_resolution(screen_device)
                if cap_w and cap_h:
                    # Calculate scale from capture vs logical screen
                    # macOS always renders at 2x logical for Retina
                    logical_screen_w = cap_w // 2
                    logical_screen_h = cap_h // 2
                    scale = 2  # Always 2x on Retina

                    # Scale logical window bounds → physical
                    px, py = x * scale, y * scale
                    pw, ph = w * scale, h * scale

                    # Clamp to actual capture bounds (Chrome may extend off-screen)
                    pw = min(pw, cap_w - px)
                    ph = min(ph, cap_h - py)

                    # Ensure even dimensions (required by libx264)
                    pw = pw - (pw % 2)
                    ph = ph - (ph % 2)

                    video_filter = f"crop={pw}:{ph}:{px}:{py},scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"
                    print(f"   📐 Logical window: {w}x{h} at ({x},{y})")
                    print(f"   📐 Logical screen: {logical_screen_w}x{logical_screen_h}")
                    print(f"   📐 Physical crop:  {pw}x{ph} at ({px},{py}) [clamped to {cap_w}x{cap_h}]")
                else:
                    # Fallback: no crop, just scale
                    video_filter = f"scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"
                    print(f"   ⚠️ Could not probe capture resolution, using full screen")
            else:
                video_filter = f"scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"

            cmd = [
                'ffmpeg', '-y',
                '-f', 'avfoundation',
                '-framerate', '30',
                '-capture_cursor', '1',
                '-i', f'{screen_device}:none',
                '-vf', video_filter,
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '18',  # Gute Qualität
                '-pix_fmt', 'yuv420p',
                self.raw_video
            ]
        else:
            # Linux: x11grab
            if self.window_bounds:
                x, y, w, h = self.window_bounds
                video_filter = f"scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'x11grab',
                    '-framerate', '30',
                    '-video_size', f'{w}x{h}',
                    '-i', f':0.0+{x},{y}',  # x11grab mit Offset
                    '-vf', video_filter,
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '18',
                    self.raw_video
                ]
            else:
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'x11grab',
                    '-framerate', '30',
                    '-video_size', f'{self.TARGET_WIDTH}x{self.TARGET_HEIGHT}',
                    '-i', ':0.0',
                    '-c:v', 'libx264',
                    '-preset', 'ultrafast',
                    '-crf', '18',
                    self.raw_video
                ]

        self.ffmpeg_log = os.path.join(OUTPUT_DIR, "ffmpeg.log")
        self._ffmpeg_log_fh = open(self.ffmpeg_log, 'w')
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=self._ffmpeg_log_fh
        )
        self.start_time = time.time()
        print(f"🎬 Aufnahme gestartet: {self.raw_video}")
        print(f"   📝 ffmpeg log: {self.ffmpeg_log}")

    def mark_audio(self, audio_file: str):
        """Markiert Zeitpunkt für Audio-Einfügung"""
        if self.start_time:
            relative_time = time.time() - self.start_time
            self.timestamps.append((relative_time, audio_file))

    def stop(self):
        """Stoppt Aufnahme"""
        if self.process:
            import signal
            try:
                # SIGINT (Ctrl+C) is the proper way to stop ffmpeg on macOS
                # Writing 'q' to stdin doesn't work reliably with avfoundation
                self.process.send_signal(signal.SIGINT)
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print("   ⚠️ ffmpeg SIGINT timeout, trying terminate...")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    print("   ⚠️ ffmpeg terminate timeout, killing...")
                    self.process.kill()
                    self.process.wait(timeout=5)
            except (BrokenPipeError, OSError) as e:
                print(f"   ⚠️ Stop error: {e}")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=10)
                except Exception:
                    self.process.kill()
            # Close log file handle
            if hasattr(self, '_ffmpeg_log_fh') and self._ffmpeg_log_fh:
                self._ffmpeg_log_fh.close()

            # Check if recording was saved
            if os.path.exists(self.raw_video):
                size = os.path.getsize(self.raw_video)
                print(f"⏹️ Aufnahme gestoppt ({size / (1024*1024):.1f} MB)")
                if size < 1000:
                    print(f"   ⚠️ Raw video ist nur {size} bytes - Aufnahme fehlgeschlagen!")
                    if hasattr(self, 'ffmpeg_log') and os.path.exists(self.ffmpeg_log):
                        with open(self.ffmpeg_log) as f:
                            log = f.read()[-500:]
                        print(f"   📝 ffmpeg log (letzte 500 Zeichen):\n{log}")
            else:
                print("⏹️ Aufnahme gestoppt (keine Datei)")

    def merge_audio(self):
        """Fügt alle Audio-Dateien zum Video hinzu"""
        if not self.timestamps:
            print("⚠️ Keine Audio-Timestamps vorhanden")
            # Einfach umbenennen
            if os.path.exists(self.raw_video):
                os.rename(self.raw_video, self.final_output)
            return

        print(f"\n🎬 POST-PROCESSING: Füge {len(self.timestamps)} Audio-Tracks hinzu...")

        # Schritt 1: Alle Audio-Dateien zu einer Spur zusammenfügen mit Delays
        combined_audio = os.path.join(OUTPUT_DIR, "combined_audio.wav")

        # FFmpeg filter_complex für Audio-Mixing mit Delays
        filter_parts = []
        inputs = []

        for i, (timestamp, audio_file) in enumerate(self.timestamps):
            if os.path.exists(audio_file):
                inputs.extend(['-i', audio_file])
                # Delay in Millisekunden
                delay_ms = int(timestamp * 1000)
                filter_parts.append(f"[{i}]adelay={delay_ms}|{delay_ms}[a{i}]")

        if not inputs:
            print("⚠️ Keine Audio-Dateien gefunden")
            os.rename(self.raw_video, self.final_output)
            return

        # Alle Audio-Streams mixen und verstärken
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(self.timestamps))])
        # amix + volume Filter für lautere Audio
        filter_parts.append(f"{mix_inputs}amix=inputs={len(self.timestamps)}:duration=longest,volume={self.AUDIO_VOLUME}[aout]")

        filter_complex = ';'.join(filter_parts)
        print(f"   🔊 Audio-Verstärkung: {self.AUDIO_VOLUME}x")

        # Audio zusammenfügen
        cmd_audio = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[aout]',
            '-ar', '44100',
            '-ac', '2',
            combined_audio
        ]

        print("   Kombiniere Audio-Tracks...")
        result = subprocess.run(cmd_audio, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️ Audio-Kombinierung fehlgeschlagen: {result.stderr[:200]}")
            # Fallback: Nur Video
            os.rename(self.raw_video, self.final_output)
            return

        # Schritt 2: Video + Audio zusammenfügen
        print("   Füge Video und Audio zusammen...")
        cmd_merge = [
            'ffmpeg', '-y',
            '-i', self.raw_video,
            '-i', combined_audio,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '18',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            self.final_output
        ]

        result = subprocess.run(cmd_merge, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"   ⚠️ Merge fehlgeschlagen: {result.stderr[:200]}")
            os.rename(self.raw_video, self.final_output)
            return

        # Aufräumen
        if os.path.exists(self.raw_video):
            os.remove(self.raw_video)
        if os.path.exists(combined_audio):
            os.remove(combined_audio)

        # Finale Ausgabe
        file_size = os.path.getsize(self.final_output) / (1024 * 1024)
        duration = self._get_duration(self.final_output)

        print(f"\n{'='*60}")
        print(f"✅ VIDEO FERTIG!")
        print(f"{'='*60}")
        print(f"   📁 Datei: {self.final_output}")
        print(f"   ⏱️ Dauer: {duration:.1f} Sekunden")
        print(f"   💾 Größe: {file_size:.1f} MB")
        print(f"   🎵 Audio-Tracks: {len(self.timestamps)}")
        print(f"{'='*60}\n")

    def _get_duration(self, video_path: str) -> float:
        """Gibt Video-Dauer in Sekunden zurück"""
        result = subprocess.run([
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 0.0


# =============================================================================
# BROWSER CONTROLLER
# =============================================================================

class Browser:
    """Kontrolliert Chrome mit Selenium"""

    # Ziel-Fenstergröße (innere Größe des Browser-Viewports)
    TARGET_WIDTH = 1920
    TARGET_HEIGHT = 1080

    # Highlight CSS
    HIGHLIGHT_CSS = """
    .llars-highlight {
        outline: 3px solid #FF5722 !important;
        outline-offset: 3px !important;
        animation: llars-pulse 0.5s ease infinite alternate !important;
    }
    @keyframes llars-pulse {
        from { box-shadow: 0 0 10px #FF5722; }
        to { box-shadow: 0 0 25px #FFC107; }
    }
    .llars-overlay {
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        background: rgba(0,0,0,0.85);
        z-index: 999999;
        opacity: 0;
        transition: opacity 0.5s ease;
        pointer-events: none;
    }
    .llars-overlay.visible { opacity: 1; }
    .llars-overlay-title {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 64px; font-weight: 700;
        color: #b0ca97; letter-spacing: 2px; margin-bottom: 16px;
    }
    .llars-overlay-subtitle {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 28px; font-weight: 400;
        color: #b0ca97; letter-spacing: 1px;
    }
    .llars-overlay-text {
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 20px; color: #e0e0e0;
        margin-top: 24px; text-align: center;
        line-height: 1.8; white-space: pre-line;
    }
    .llars-overlay-columns {
        display: flex; gap: 64px;
        margin-top: 40px;
    }
    .llars-overlay-column {
        display: flex; flex-direction: column; gap: 20px;
    }
    .llars-overlay-cred-label {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px; color: #888;
        text-transform: uppercase; letter-spacing: 2px;
        margin-bottom: 2px;
    }
    .llars-overlay-cred-value {
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 22px; color: #e0e0e0;
    }
    .pipeline-container {
        display: flex; flex-direction: column;
        align-items: center; gap: 10px;
    }
    .pipeline-row {
        display: flex; align-items: center; gap: 20px;
    }
    .pipeline-actor {
        width: 170px; height: 54px; padding: 0 16px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.2);
        border-radius: 4px; text-align: center;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px; color: #aaa; line-height: 1.4;
    }
    .pipeline-arrow {
        font-size: 22px; color: rgba(255,255,255,0.4);
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    .pipeline-arrow-dash {
        font-size: 18px; color: rgba(255,255,255,0.2);
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    .pipeline-module {
        width: 280px; height: 72px; padding: 0 24px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 6px; text-align: center;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 18px; font-weight: 700; color: #222;
        line-height: 1.3;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .pipeline-prompt { background: #B0CA97; border: 2px solid #8aaa6e; }
    .pipeline-batch { background: #88C4C8; border: 2px solid #6aa0a4; }
    .pipeline-eval { background: #D1BC8A; border: 2px solid #b09a60; }
    .pipeline-module.llars-highlight {
        outline: none !important;
        transform: scale(1.1);
        box-shadow: 0 0 40px rgba(255,255,255,0.5) !important;
        animation: pipeline-pulse 0.6s ease infinite alternate !important;
    }
    @keyframes pipeline-pulse {
        from { box-shadow: 0 0 25px rgba(255,255,255,0.3); }
        to { box-shadow: 0 0 45px rgba(255,255,255,0.6); }
    }
    .pipeline-export {
        width: 130px; height: 42px; padding: 0 12px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
        border-radius: 4px; text-align: center;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 13px; color: #777; line-height: 1.4;
    }
    .pipeline-flow {
        display: inline-flex; align-items: center; gap: 8px;
        transform: translateX(22px);
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px; color: rgba(255,255,255,0.35);
        letter-spacing: 1px;
    }
    .pipeline-flow-label {
        font-size: 13px;
    }
    .pipeline-outcome {
        width: 280px; height: 72px; padding: 0 24px;
        margin-top: 16px;
        transform: translateX(22px);
        display: flex; align-items: center; justify-content: center;
        background: rgba(232,160,135,0.2); border: 2px solid #E8A087;
        border-radius: 6px; text-align: center;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 18px; font-weight: 700; color: #E8A087;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }
    .pipeline-llars-label {
        margin-top: 8px;
        transform: translateX(22px);
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 13px; font-weight: 600;
        color: rgba(176,202,151,0.4); letter-spacing: 3px;
        text-transform: uppercase;
    }
    /* === Problem Animation === */
    .problem-wrapper {
        display: flex; flex-direction: column;
        align-items: center;
    }
    .problem-container {
        position: relative;
        display: flex; align-items: stretch; gap: 0;
    }
    .problem-merge-border {
        position: absolute;
        top: -14px; left: -14px; right: -14px; bottom: -14px;
        border: 2px dashed #b0ca97;
        border-radius: 14px;
        opacity: 0;
        transition: opacity 0.8s ease;
        pointer-events: none;
    }
    .problem-merge-label {
        position: absolute;
        top: -34px; left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.9);
        padding: 4px 24px;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 18px; font-weight: 700;
        color: #b0ca97;
        letter-spacing: 3px;
        opacity: 0;
        transition: opacity 0.8s ease 0.4s;
        pointer-events: none;
    }
    .problem-container.merged .problem-merge-border {
        opacity: 1;
    }
    .problem-container.merged .problem-merge-label {
        opacity: 1;
    }
    .problem-box {
        width: 320px; padding: 32px 28px;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 8px;
        display: flex; flex-direction: column;
        opacity: 0;
    }
    .problem-box.problem-left {
        transform: translateX(-60px);
        animation: problem-slide-left 0.8s ease 0.3s forwards;
    }
    .problem-box.problem-right {
        transform: translateX(60px);
        animation: problem-slide-right 0.8s ease 0.5s forwards;
    }
    @keyframes problem-slide-left {
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes problem-slide-right {
        to { opacity: 1; transform: translateX(0); }
    }
    .problem-box-title {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 22px; font-weight: 700;
        color: #fff; margin-bottom: 6px;
        text-align: center;
    }
    .problem-box-subtitle {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px; color: rgba(255,255,255,0.4);
        text-align: center; margin-bottom: 24px;
        font-style: italic;
    }
    .problem-box-items {
        display: flex; flex-direction: column; gap: 12px;
        flex: 1;
    }
    .problem-item {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 15px; color: #999; line-height: 1.5;
        padding: 10px 16px;
        background: rgba(255,255,255,0.03);
        border-left: 2px solid rgba(255,255,255,0.08);
        border-radius: 0 4px 4px 0;
    }
    .problem-gap {
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        width: 80px; min-height: 100px;
        opacity: 0;
        animation: problem-fade 0.6s ease 1.0s forwards;
    }
    @keyframes problem-fade {
        to { opacity: 1; }
    }
    .problem-gap-line {
        width: 2px; flex: 1;
        background: linear-gradient(to bottom, transparent, rgba(232,160,135,0.3), transparent);
    }
    .problem-gap-x {
        font-size: 28px; color: #E8A087;
        margin: 8px 0; font-weight: 300;
    }
    .problem-painpoints {
        display: flex; align-items: center; gap: 16px;
        margin-top: 36px;
        opacity: 0;
        animation: problem-fade 0.8s ease 2.5s forwards;
    }
    .problem-pain {
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px; color: #E8A087;
        padding: 6px 18px;
        background: rgba(232,160,135,0.08);
        border: 1px solid rgba(232,160,135,0.2);
        border-radius: 20px;
        letter-spacing: 0.5px;
    }
    .problem-pain-dot {
        color: rgba(255,255,255,0.15); font-size: 20px;
    }
    .problem-quote {
        margin-top: 20px;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 17px; font-style: italic;
        color: rgba(255,255,255,0.3);
        letter-spacing: 0.5px;
        opacity: 0;
        animation: problem-fade 0.8s ease 3.5s forwards;
    }
    /* === Data Preview Overlay === */
    .data-preview-wrapper {
        display: flex; flex-direction: column;
        align-items: center;
    }
    .data-preview-code {
        font-family: 'SF Mono', Monaco, Consolas, monospace;
        font-size: 15px;
        color: #888;
        text-align: left;
        line-height: 1.7;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 8px;
        padding: 28px 36px;
        margin-top: 28px;
        max-width: 720px;
        white-space: pre;
    }
    .data-preview-code .dp-key {
        color: #b0ca97;
        font-weight: 700;
    }
    .data-preview-code .dp-str {
        color: #d4d4d4;
    }
    .data-preview-code .dp-bracket {
        color: rgba(255,255,255,0.25);
    }
    .data-preview-code .dp-dots {
        color: rgba(255,255,255,0.3);
        font-style: italic;
    }
    .data-preview-count {
        margin-top: 16px;
        font-family: 'Segoe UI', system-ui, sans-serif;
        font-size: 14px;
        color: rgba(255,255,255,0.35);
        letter-spacing: 0.5px;
    }
    """

    def __init__(self, url: str = "http://localhost:55080"):
        self.base_url = url
        self.driver = None
        self.window_bounds = None  # (x, y, width, height)
        self.collab_driver = None  # Zweiter Browser für Collab-Demo

    @staticmethod
    def _get_logical_screen_size() -> tuple:
        """Get logical screen resolution.

        On macOS Retina, the "Looks like" resolution determines the logical space.
        Chrome windows should not exceed this, or they'll extend off-screen.
        """
        try:
            # Probe ffmpeg capture resolution (physical) → divide by 2 for logical
            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', ''],
                capture_output=True, text=True, timeout=5
            )
            # Find screen device
            screen_idx = '3'
            for line in result.stderr.split('\n'):
                if 'Capture screen 0' in line:
                    match = re.search(r'\[(\d+)\]', line)
                    if match:
                        screen_idx = match.group(1)
                    break

            result = subprocess.run(
                ['ffmpeg', '-f', 'avfoundation', '-framerate', '1',
                 '-i', f'{screen_idx}:none', '-frames:v', '1', '-y', '/dev/null'],
                capture_output=True, text=True, timeout=10
            )
            match = re.search(r'(\d{3,5})x(\d{3,5})', result.stderr)
            if match:
                cap_w, cap_h = int(match.group(1)), int(match.group(2))
                # macOS Retina always renders at 2x logical
                return cap_w // 2, cap_h // 2
        except Exception:
            pass
        return 1920, 1080  # Fallback

    def open(self, username: str = "admin", password: str = "admin123", language: str = "en"):
        """Öffnet Chrome mit exakter Fenstergröße, angepasst an die Bildschirmgröße"""
        options = Options()
        # Starte mit kleinem Fenster, setzen die exakte Größe danach
        options.add_argument('--window-size=1280,800')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # Disable password save prompts and other infobars
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.password_manager_leak_detection': False,
        })

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Fenster an Position (0,0) setzen
        self.driver.set_window_position(0, 0)

        # Detect logical screen size and clamp Chrome to fit
        screen_w, screen_h = self._get_logical_screen_size()
        target_w = min(self.TARGET_WIDTH, screen_w)
        target_h = min(self.TARGET_HEIGHT, screen_h - 39)  # Reserve space for menu bar
        print(f"   🖥️ Logical screen: {screen_w}x{screen_h}")
        print(f"   🖥️ Chrome target: {target_w}x{target_h}")

        # Chrome Fenster-Dekoration (~74px Toolbar oben)
        self.driver.set_window_size(target_w, target_h + 100)

        # Warte kurz und hole exakte Position/Größe
        time.sleep(0.5)
        pos = self.driver.get_window_position()
        size = self.driver.get_window_size()

        # Speichere Fenster-Bounds für Recorder
        self.window_bounds = (pos['x'], pos['y'], size['width'], size['height'])

        print(f"🌐 Chrome geöffnet: {size['width']}x{size['height']} at ({pos['x']},{pos['y']})")

    def get_window_bounds(self) -> tuple:
        """Gibt Fenster-Bounds zurück (x, y, width, height)"""
        if self.driver:
            pos = self.driver.get_window_position()
            size = self.driver.get_window_size()
            return (pos['x'], pos['y'], size['width'], size['height'])
        return self.window_bounds

    def setup(self, username: str = "admin", password: str = "admin123", language: str = "en",
              skip_login: bool = False):
        """
        SETUP PHASE - Vor der Aufnahme:
        1. Prüft ob auf /login oder /Home
        2. Stellt Sprache auf Englisch
        3. Führt Login durch falls nötig (skip_login=True: bleibt auf Login-Seite)
        4. Navigiert zu /Home (unless skip_login)
        """
        print("\n" + "="*60)
        print("🔧 SETUP PHASE")
        print("="*60)

        # Zur Hauptseite navigieren
        self.driver.get(self.base_url)
        time.sleep(2)

        # Aktuelle Seite bestimmen
        page = self._detect_page()
        print(f"   📍 Aktuelle Seite: {page}")

        if page == "login":
            # 1. Sprache auf Englisch stellen (vor Login)
            self._set_language(language)

            if skip_login:
                print("   ⏭️ Login übersprungen (wird während Aufnahme durchgeführt)")
            else:
                # 2. Login durchführen
                self._do_login_on_login_page(username, password)

                # 3. Warten und prüfen ob Login erfolgreich
                for attempt in range(5):
                    time.sleep(1)
                    page = self._detect_page()
                    if page != "login":
                        print(f"   ✓ Login erfolgreich! (Seite: {page})")
                        break
                    print(f"   ⏳ Warte auf Login... (Versuch {attempt + 1}/5)")
                else:
                    print("   ⚠️ Login scheint nicht erfolgreich zu sein!")

        if page == "home":
            print("   ✓ Auf Home-Seite")

        elif page == "authentik":
            # Authentik 2-Step Login
            self._do_authentik_login(username, password)
            time.sleep(3)

        if not skip_login:
            # Final check
            self.driver.get(f"{self.base_url}/Home")
            time.sleep(2)

        # Dismiss cookie consent banner if present
        self._dismiss_cookie_banner()

        # Highlight CSS injizieren
        self._inject_styles()

        # Cleanup alte Demo-Daten
        self._cleanup_demo_data()

        print("="*60)
        print("✓ SETUP COMPLETE")
        print("="*60 + "\n")

    def _cleanup_demo_data(self):
        """
        Cleanup demo data before recording.

        - Production: Calls /api/demo-video/reset via SYSTEM_ADMIN_API_KEY
        - Local (localhost): Tries API reset / service reset, falls back to SQL cleanup
        """
        is_production = 'localhost' not in self.base_url and '127.0.0.1' not in self.base_url

        if is_production:
            self._cleanup_via_api()
            return

        # Preferred path on local too: API reset (if SYSTEM_ADMIN_API_KEY is configured)
        if self._cleanup_via_api(silent_missing_key=True):
            return

        # Fallback path 1: call demo reset service directly inside Flask container
        print("   🔄 Versuche Demo-Reset via Flask-Container-Service...")
        try:
            reset_result = subprocess.run(
                [
                    'docker', 'exec', 'llars_flask_service', 'python3', '-c',
                    (
                        "import json; "
                        "from main import app; "
                        "from services.demo_video_service import reset; "
                        "app.app_context().push(); "
                        "print(json.dumps(reset()))"
                    )
                ],
                capture_output=True,
                text=True,
                timeout=45
            )

            if reset_result.returncode == 0:
                lines = (reset_result.stdout or '').strip().splitlines()
                payload_line = next(
                    (line for line in reversed(lines) if line.strip().startswith('{') and line.strip().endswith('}')),
                    ''
                )
                if payload_line:
                    payload = json.loads(payload_line)
                    if payload.get('success'):
                        print("   ✓ Demo-Daten erfolgreich zurückgesetzt (Service)")
                        return
                print("   ⚠️ Service-Reset lieferte kein erfolgreiches Ergebnis, nutze SQL-Fallback")
            else:
                details = (reset_result.stderr or reset_result.stdout or '').strip()
                print(f"   ⚠️ Service-Reset fehlgeschlagen: {details[:200]}")
        except Exception as e:
            print(f"   ⚠️ Service-Reset nicht verfügbar: {str(e)[:200]}")

        print("   🧹 Räume alte Demo-Daten auf (lokaler Docker, SQL-Fallback)...")

        login_user = self._get_login_username()
        protected_scenario_name = "IJCAI Counselling Evaluation"
        scenario_filter = (
            f"(scenario_name LIKE '%Situation%' OR scenario_name LIKE '%Counselling%') "
            f"AND scenario_name <> '{protected_scenario_name}'"
        )

        # SQL: Delete scenarios and jobs created during previous recordings
        cleanup_sql = f"""
        DELETE FROM scenario_item_distribution WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM scenario_items WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM scenario_users WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM item_dimension_ratings WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM item_labeling_evaluations WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM comparison_evaluations WHERE message_id IN (
            SELECT id FROM comparison_messages WHERE session_id IN (
                SELECT id FROM comparison_sessions WHERE scenario_id IN (
                    SELECT id FROM rating_scenarios WHERE {scenario_filter}
                )
            )
        );
        DELETE FROM comparison_messages WHERE session_id IN (
            SELECT id FROM comparison_sessions WHERE scenario_id IN (
                SELECT id FROM rating_scenarios WHERE {scenario_filter}
            )
        );
        DELETE FROM comparison_sessions WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE {scenario_filter}
        );
        DELETE FROM rating_scenarios WHERE {scenario_filter};
        DELETE FROM generated_outputs WHERE job_id IN (
            SELECT id FROM generation_jobs WHERE created_by = '{login_user}' AND name <> 'Counselling Situation Extraction'
        );
        DELETE FROM generation_jobs WHERE created_by = '{login_user}' AND name <> 'Counselling Situation Extraction';
        """

        # SQL: Reset prompts (delete + re-create setup prompt)
        prompt_reset_sql = f"""
        DELETE FROM prompt_commits WHERE prompt_id IN (
            SELECT prompt_id FROM user_prompts
            WHERE LOWER(TRIM(name)) LIKE 'structured situation analysis%'
               OR LOWER(TRIM(name)) LIKE 'situation summary%'
               OR LOWER(TRIM(name)) LIKE 'live collab%'
        );
        DELETE FROM user_prompt_shares WHERE prompt_id IN (
            SELECT prompt_id FROM user_prompts
            WHERE LOWER(TRIM(name)) LIKE 'structured situation analysis%'
               OR LOWER(TRIM(name)) LIKE 'situation summary%'
               OR LOWER(TRIM(name)) LIKE 'live collab%'
        );
        DELETE FROM user_prompts
        WHERE LOWER(TRIM(name)) LIKE 'structured situation analysis%'
           OR LOWER(TRIM(name)) LIKE 'situation summary%'
           OR LOWER(TRIM(name)) LIKE 'live collab%';
        """

        try:
            result = subprocess.run([
                'docker', 'exec', 'llars_db_service',
                'mariadb', '-u', 'dev_user', '-pdev_password_change_me', 'database_llars',
                '-e', cleanup_sql
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"   ✓ Demo-Daten gelöscht")
            else:
                print(f"   ⚠️ Cleanup abgeschlossen (mit Warnungen)")

            prompt_result = subprocess.run(
                [
                    'docker', 'exec', '-i', 'llars_db_service',
                    'mariadb', '-u', 'dev_user', '-pdev_password_change_me', 'database_llars'
                ],
                input=prompt_reset_sql,
                capture_output=True,
                text=True,
                timeout=10
            )

            if prompt_result.returncode == 0:
                print(f"   ✓ Demo-Prompts zurückgesetzt")
            else:
                details = (prompt_result.stderr or prompt_result.stdout or '').strip()
                if details:
                    print(f"   ⚠️ Prompt-Reset fehlgeschlagen: {details}")
                else:
                    print(f"   ⚠️ Prompt-Reset fehlgeschlagen (ignoriert)")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ Cleanup Timeout (ignoriert)")
        except FileNotFoundError:
            print(f"   ⚠️ Docker nicht verfügbar (ignoriert)")
        except Exception as e:
            print(f"   ⚠️ Cleanup-Fehler (ignoriert): {str(e)[:50]}")

    def _cleanup_via_api(self, silent_missing_key: bool = False) -> bool:
        """Reset demo data on production via the admin API endpoint."""
        env = _load_env_vars()
        api_key = env.get('PRODUCTION_ADMIN_API_KEY') or env.get('SYSTEM_ADMIN_API_KEY', '')
        if not api_key:
            if not silent_missing_key:
                print("   ⚠️ SYSTEM_ADMIN_API_KEY nicht in .env gefunden!")
                print("   ℹ️  Manuell: ssh llars 'docker exec llars_flask_service python3 /app/scripts/demo_video_manage.py reset'")
            return False

        api_url = f"{self.base_url}/api/demo-video/reset"
        print(f"   🔄 Demo-Daten Reset via API: {api_url}")

        try:
            req = urllib.request.Request(
                api_url,
                method='POST',
                headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                data=b'{}'
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())

            if result.get('success'):
                cleanup = result.get('cleanup', {})
                seed = result.get('seed', {})
                deleted = cleanup.get('deleted', [])
                actions = seed.get('actions', [])
                legacy_live_prompt_seeded = any(
                    ("Situation Summary" in str(a)) and (
                        "Created prompt" in str(a)
                        or "Updated prompt" in str(a)
                        or "already exists" in str(a)
                    )
                    for a in actions
                )
                cleanup_live_supported = True
                if deleted:
                    for d in deleted:
                        print(f"      🗑️ {d}")
                for a in actions:
                    print(f"      ✓ {a}")

                # Safety-net: enforce that live prompt does not exist after reset.
                # Newer backends expose this endpoint and remove "Situation Summary"
                # explicitly so it can be created live during recording.
                cleanup_live_url = f"{self.base_url}/api/demo-video/cleanup-live-prompt"
                try:
                    cleanup_live_req = urllib.request.Request(
                        cleanup_live_url,
                        method='POST',
                        headers={'X-API-Key': api_key, 'Content-Type': 'application/json'},
                        data=b'{}'
                    )
                    with urllib.request.urlopen(cleanup_live_req, timeout=15) as resp:
                        cleanup_live_result = json.loads(resp.read().decode())
                    if cleanup_live_result.get('success'):
                        for d in cleanup_live_result.get('deleted', []):
                            print(f"      🗑️ {d}")
                except urllib.error.HTTPError as e:
                    # Backward compatibility: older backend may not expose endpoint yet.
                    if e.code not in (404, 405):
                        body = e.read().decode() if e.fp else ''
                        print(f"      ⚠️ cleanup-live-prompt API-Fehler {e.code}: {body[:200]}")
                    else:
                        cleanup_live_supported = False
                except Exception as e:
                    print(f"      ⚠️ cleanup-live-prompt Aufruf fehlgeschlagen: {e}")

                if legacy_live_prompt_seeded and not cleanup_live_supported:
                    print("      ❌ Backend verwendet alte Demo-Reset-Logik:")
                    print("         'Situation Summary' wird bereits im Setup erzeugt.")
                    print("         Bitte Backend deployen/restarten, damit Live-Anlage wieder funktioniert.")

                print("   ✓ Demo-Daten erfolgreich zurückgesetzt")
                return True
            else:
                print(f"   ⚠️ API Reset fehlgeschlagen: {result}")
                return False
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ''
            print(f"   ⚠️ API-Fehler {e.code}: {body[:200]}")
            return False
        except Exception as e:
            print(f"   ⚠️ API-Aufruf fehlgeschlagen: {e}")
            return False

    def _get_login_username(self) -> str:
        """Get the login username from SCRIPT.json config."""
        try:
            with open(SCRIPT_FILE, 'r') as f:
                script = json.load(f)
            return script.get('config', {}).get('login', {}).get('username', 'admin')
        except Exception:
            return 'admin'

    def _dismiss_cookie_banner(self):
        """Schließt Cookie-Banner falls vorhanden"""
        try:
            # Look for common cookie consent buttons (Accept/Agree)
            accept_selectors = [
                ".v-btn:contains('Accept'), .v-btn:contains('Agree')",
                ".v-btn:contains('ZUSTIMMEN')",  # German
                "button:contains('Accept')",
                "[data-testid='cookie-accept']",
                ".cookie-consent .accept, .cookie-banner .accept"
            ]
            for selector in accept_selectors:
                try:
                    if ':contains(' in selector:
                        base, text = selector.split(':contains(')
                        text = text.rstrip(')').strip("'\"")
                        elements = self.driver.find_elements(By.CSS_SELECTOR, base or '*')
                        for el in elements:
                            if text.lower() in el.text.lower() and el.is_displayed():
                                el.click()
                                print(f"   ✓ Cookie-Banner geschlossen")
                                time.sleep(0.5)
                                return
                    else:
                        el = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if el.is_displayed():
                            el.click()
                            print(f"   ✓ Cookie-Banner geschlossen")
                            time.sleep(0.5)
                            return
                except Exception:
                    continue
        except Exception:
            pass  # No cookie banner or already dismissed

    def _detect_page(self) -> str:
        """Erkennt auf welcher Seite wir sind"""
        current_url = self.driver.current_url.lower()

        if '/login' in current_url:
            return "login"
        elif '/home' in current_url:
            return "home"
        elif 'authentik' in current_url or '/auth/' in current_url:
            return "authentik"
        else:
            # Check for login page elements
            try:
                login_form = self.driver.find_elements(By.CSS_SELECTOR,
                    "[data-testid='login-form'], .login-form, .login-card")
                if login_form:
                    return "login"
            except Exception:
                pass

            # Check for home page elements
            try:
                home_elements = self.driver.find_elements(By.CSS_SELECTOR,
                    ".feature-card, .home-page, .features-grid")
                if home_elements:
                    return "home"
            except Exception:
                pass

        return "unknown"

    def _set_language(self, language: str):
        """Stellt die Sprache auf der Login-Seite ein"""
        print(f"   🌐 Setze Sprache auf: {language.upper()}")
        self._set_language_for_driver(self.driver, language)

    def _set_language_for_driver(self, driver, language: str):
        """Setzt Sprache für einen beliebigen WebDriver (Login-Screen)."""
        try:
            toggle = driver.find_element(
                By.CSS_SELECTOR,
                "[data-testid='language-toggle'] .language-toggle-btn, "
                ".language-toggle-wrapper .language-toggle-btn, "
                ".language-toggle-btn"
            )

            # Klicke um Dropdown zu öffnen
            toggle.click()
            time.sleep(0.5)

            # Wähle die richtige Sprache
            lang_text = "English" if language == "en" else "Deutsch"

            # Suche in der Sprachauswahl-Liste
            lang_option = driver.find_element(By.XPATH,
                f"//button[contains(@class, 'language-option') and contains(., '{lang_text}')]")
            lang_option.click()
            time.sleep(0.5)

            print(f"   ✓ Sprache auf {lang_text} gesetzt")
            return
        except Exception as e:
            print(f"   ⚠️ Sprache konnte nicht über UI gesetzt werden: {e}")

        # Fallback: Direkt localStorage setzen (zuverlässiger)
        try:
            driver.execute_script(f"localStorage.setItem('llars-language', '{language}')")
            driver.refresh()
            time.sleep(1)
            print(f"   ✓ Sprache via localStorage gesetzt")
        except Exception:
            pass

    def _do_login_on_login_page(self, username: str, password: str):
        """Login auf der Lars /login Seite"""
        print(f"   🔐 Login als: {username}")

        try:
            # Warte auf Login-Formular
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".login-form, [data-testid='login-form']"))
            )
            time.sleep(0.5)

            # METHODE 1: Dev Quick Login Button (zuverlässiger für Selenium)
            # Diese Buttons haben data-testid="dev-login-btn-{username}"
            dev_btn_selector = f"[data-testid='dev-login-btn-{username}']"
            try:
                dev_btn = self.driver.find_element(By.CSS_SELECTOR, dev_btn_selector)
                if dev_btn and dev_btn.is_displayed():
                    print(f"   🚀 Nutze Dev Quick Login Button")
                    # JavaScript click ist zuverlässiger für Vue-Komponenten
                    self.driver.execute_script("arguments[0].click()", dev_btn)
                    print("   ✓ Dev-Login-Button geklickt")
                    time.sleep(3)
                    return
            except Exception:
                print(f"   ℹ️ Dev-Button nicht gefunden, nutze Formular-Login")

            # METHODE 2: Formular-Login (Fallback)
            # Username eingeben - Vuetify 3 v-text-field hat input tief verschachtelt
            username_selectors = [
                "[data-testid='username-input'] input",
                ".login-form input[name='username']",
                ".login-form .v-text-field:first-of-type input",
                "input#username",
            ]
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if username_field and username_field.is_displayed():
                        break
                except Exception:
                    continue

            if not username_field:
                print("   ⚠️ Username-Feld nicht gefunden!")
                return

            username_field.clear()
            username_field.send_keys(username)
            print("   ✓ Username eingegeben")

            time.sleep(0.3)

            # Password eingeben
            password_selectors = [
                "[data-testid='password-input'] input",
                ".login-form input[name='password']",
                ".login-form input[type='password']",
                "input#password",
            ]
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field and password_field.is_displayed():
                        break
                except Exception:
                    continue

            if not password_field:
                print("   ⚠️ Password-Feld nicht gefunden!")
                return

            password_field.clear()
            password_field.send_keys(password)
            print("   ✓ Passwort eingegeben")

            time.sleep(0.3)

            # Login Button klicken - JavaScript click für Vue-Komponenten
            login_selectors = [
                "[data-testid='login-btn']",
                ".login-button",
                ".login-form button[type='submit']",
                ".login-form .l-btn",
            ]
            login_btn = None
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn and login_btn.is_displayed():
                        break
                except Exception:
                    continue

            if not login_btn:
                print("   ⚠️ Login-Button nicht gefunden!")
                return

            # JavaScript click ist zuverlässiger für Vue-Komponenten
            self.driver.execute_script("arguments[0].click()", login_btn)
            print("   ✓ Login-Button geklickt")

            time.sleep(3)

        except Exception as e:
            print(f"   ⚠️ Login-Fehler: {e}")

    def _do_authentik_login(self, username: str, password: str):
        """Login auf Authentik (2-Step Flow)"""
        print(f"   🔐 Authentik Login als: {username}")

        try:
            # Step 1: Username
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[name='uidField'], input[name='username'], input[type='text']"))
            )
            username_field.clear()
            username_field.send_keys(username)
            print("   ✓ Username eingegeben")

            # Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], .pf-c-button.pf-m-primary")
            submit_btn.click()
            time.sleep(2)

            # Step 2: Password
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[name='password'], input[type='password']"))
            )
            password_field.clear()
            password_field.send_keys(password)
            print("   ✓ Passwort eingegeben")

            # Final Submit
            submit_btn = self.driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], .pf-c-button.pf-m-primary")
            submit_btn.click()
            print("   ✓ Login abgeschickt")

            time.sleep(3)

        except Exception as e:
            print(f"   ⚠️ Authentik Login-Fehler: {e}")

    def _inject_styles(self):
        """Injiziert Highlight-Styles"""
        self.driver.execute_script(f"""
            if (!document.getElementById('llars-styles')) {{
                var style = document.createElement('style');
                style.id = 'llars-styles';
                style.textContent = `{self.HIGHLIGHT_CSS}`;
                document.head.appendChild(style);
            }}
        """)

    def _find_element(self, target: str):
        """Findet Element anhand des Namens aus ELEMENT_MAP oder per Text-Suche"""
        selectors = ELEMENT_MAP.get(target, target)

        # Mehrere Selektoren versuchen
        for selector in selectors.split(', '):
            try:
                # :contains() Pseudo-Selektor behandeln
                if ':contains(' in selector:
                    base, text = selector.split(':contains(')
                    text = text.rstrip(')').strip("'\"")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, base or '*')
                    for el in elements:
                        if text.lower() in el.text.lower():
                            try:
                                if not el.is_displayed():
                                    continue
                            except Exception:
                                continue
                            return el
                else:
                    el = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if el:
                        try:
                            if not el.is_displayed():
                                continue
                        except Exception:
                            continue
                        return el
            except Exception:
                continue

        # Fallback 1: Feature Cards auf Home Page
        try:
            target_lower = target.lower()
            # Suche nach Feature-Karten mit dem Text
            cards = self.driver.find_elements(By.CSS_SELECTOR, '.feature-card, [class*="feature"], [class*="card"]')
            for card in cards:
                try:
                    if target_lower in card.text.lower():
                        return card
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback 2: Suche nach Text in allen klickbaren Elementen
        try:
            # Links, Buttons, und andere klickbare Elemente
            clickables = self.driver.find_elements(
                By.CSS_SELECTOR,
                'a, button, [role="button"], .v-btn, .v-list-item, .nav-item, input[type="submit"], .v-card'
            )
            target_lower = target.lower()
            for el in clickables:
                try:
                    aria_label = el.get_attribute('aria-label') or ''
                    if target_lower in el.text.lower() or target_lower in aria_label.lower():
                        return el
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback 3: XPath mit Text (Case-insensitive)
        try:
            xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target.lower()}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed():
                        return el
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback 4: Suche nach Teil des Textes in div-Elementen
        try:
            xpath = f"//div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{target.lower()}')]"
            elements = self.driver.find_elements(By.XPATH, xpath)
            for el in elements:
                try:
                    if el.is_displayed() and el.is_enabled():
                        # Prüfe ob es ein klickbares Element ist
                        parent = el.find_element(By.XPATH, '..')
                        if 'card' in (parent.get_attribute('class') or '').lower():
                            return parent
                        return el
                except Exception:
                    continue
        except Exception:
            pass

        # Debug: List available buttons on page
        try:
            buttons = self.driver.find_elements(By.CSS_SELECTOR, '.v-btn, button, .l-btn')
            if buttons:
                btn_texts = [b.text[:20] for b in buttons[:10] if b.text.strip()]
                if btn_texts:
                    print(f"   📋 Available buttons: {btn_texts}")
        except Exception:
            pass

        print(f"⚠️ Element nicht gefunden: {target}")
        return None

    def _find_elements(self, target: str):
        """Findet mehrere Elemente anhand des Namens aus ELEMENT_MAP oder per CSS"""
        selectors = ELEMENT_MAP.get(target, target)
        collected = []

        for selector in selectors.split(', '):
            try:
                if ':contains(' in selector:
                    base, text = selector.split(':contains(')
                    text = text.rstrip(')').strip("'\"")
                    candidates = self.driver.find_elements(By.CSS_SELECTOR, base or '*')
                    for el in candidates:
                        if text.lower() in el.text.lower():
                            collected.append(el)
                else:
                    collected.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
            except Exception:
                continue

        # Filter duplicates + only visible elements
        unique = []
        seen = set()
        for el in collected:
            try:
                if not el.is_displayed():
                    continue
                el_id = el.id
                if el_id in seen:
                    continue
                seen.add(el_id)
                unique.append(el)
            except Exception:
                continue

        return unique

    def goto(self, url: str):
        """Navigiert zu URL"""
        full_url = url if url.startswith('http') else f"{self.base_url}{url}"
        self.driver.get(full_url)
        self._inject_styles()
        time.sleep(0.5)

    def click(self, target: str):
        """Klickt auf Element mit Retry bei StaleElementReferenceException"""
        for attempt in range(3):
            element = self._find_element(target)
            if not element:
                if attempt == 0:
                    return
                time.sleep(0.5)
                continue
            try:
                # Scroll to element
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
                    element
                )
                time.sleep(0.3)

                # Only add highlight if not already highlighted (smooth transition from prior highlight)
                already_highlighted = self.driver.execute_script(
                    "return arguments[0].classList.contains('llars-highlight')",
                    element
                )
                if not already_highlighted:
                    self.driver.execute_script(
                        "arguments[0].classList.add('llars-highlight')",
                        element
                    )
                    time.sleep(0.2)

                # Click
                try:
                    element.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click()", element)

                time.sleep(0.2)

                # Remove highlight
                try:
                    self.driver.execute_script(
                        "arguments[0].classList.remove('llars-highlight')",
                        element
                    )
                except Exception:
                    pass

                print(f"   🖱️ Click: {target}")
                return
            except StaleElementReferenceException:
                print(f"   ↻ Stale element, retry {attempt + 1}/3: {target}")
                time.sleep(0.5)
                continue
            except Exception as e:
                # Last resort: JS click on re-found element
                element = self._find_element(target)
                if element:
                    try:
                        self.driver.execute_script("arguments[0].click()", element)
                        print(f"   🖱️ Click (JS fallback): {target}")
                    except Exception:
                        print(f"   ⚠️ Click fehlgeschlagen: {target} ({e})")
                return

    def type(self, target: str, text: str, speed: str = "fast"):
        """Tippt Text in Element (inkl. contenteditable für Quill Editor)"""
        element = self._find_element(target)
        if element:
            # If a container was targeted, try to drill down to an actual input
            try:
                tag = (element.tag_name or '').lower()
                if tag not in ('input', 'textarea') and element.get_attribute('contenteditable') != 'true':
                    nested = element.find_element(By.CSS_SELECTOR, 'input, textarea, [contenteditable=\"true\"]')
                    if nested:
                        element = nested
            except Exception:
                pass

            # Click to focus
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click()", element)
            time.sleep(0.1)

            # Check if it's a contenteditable element (Quill editor)
            is_contenteditable = element.get_attribute('contenteditable') == 'true'

            # Instant fill for Quill/contenteditable (avoids race conditions while typing placeholders)
            if speed == "instant" and is_contenteditable:
                try:
                    set_ok = self.driver.execute_script("""
                        const editorEl = arguments[0];
                        const text = arguments[1];
                        let quill = null;

                        try {
                            const container = editorEl.closest('.ql-container');
                            if (container && container.__quill) {
                                quill = container.__quill;
                            }
                        } catch (e) {}

                        if (!quill && window.Quill) {
                            try {
                                const found = window.Quill.find(editorEl.closest('.ql-container') || editorEl);
                                if (found && typeof found.setText === 'function') {
                                    quill = found;
                                }
                            } catch (e) {}
                        }

                        if (quill && typeof quill.setText === 'function') {
                            quill.setText(text, 'api');
                            return true;
                        }

                        editorEl.textContent = text;
                        editorEl.dispatchEvent(new Event('input', { bubbles: true }));
                        editorEl.dispatchEvent(new Event('change', { bubbles: true }));
                        return false;
                    """, element, text)

                    if not set_ok:
                        # Fallback when no Quill instance was found
                        try:
                            element.send_keys(Keys.COMMAND + 'a')
                        except Exception:
                            try:
                                element.send_keys(Keys.CONTROL + 'a')
                            except Exception:
                                pass
                        try:
                            element.send_keys(Keys.BACKSPACE)
                        except Exception:
                            pass
                        element.send_keys(text)
                except Exception:
                    # Last-resort fallback
                    try:
                        element.send_keys(Keys.COMMAND + 'a')
                    except Exception:
                        try:
                            element.send_keys(Keys.CONTROL + 'a')
                        except Exception:
                            pass
                    try:
                        element.send_keys(Keys.BACKSPACE)
                    except Exception:
                        pass
                    element.send_keys(text)
                print(f"   ⌨️ Type: {text[:30]}...")
                return

            # Instant fill for normal inputs (faster for variable dialogs)
            if speed == "instant" and not is_contenteditable:
                try:
                    element.clear()
                except Exception:
                    pass
                try:
                    self.driver.execute_script(
                        "arguments[0].value = arguments[1];"
                        "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                        element,
                        text
                    )
                except Exception:
                    element.send_keys(text)
                print(f"   ⌨️ Type: {text[:30]}...")
                return

            # Geschwindigkeit
            delay = {"slow": 0.08, "medium": 0.04, "fast": 0.02, "turbo": 0.005}.get(speed, 0.02)

            if is_contenteditable:
                # For Quill/contenteditable: type character by character
                for char in text:
                    if char == '\n':
                        element.send_keys(Keys.ENTER)
                    else:
                        element.send_keys(char)
                    time.sleep(delay)
            else:
                # Standard input field
                for char in text:
                    element.send_keys(char)
                    time.sleep(delay)

            print(f"   ⌨️ Type: {text[:30]}...")

    def highlight(self, target: str, duration: float = 2, keep: bool = False):
        """Hebt Element hervor. Bei keep=True bleibt Highlight aktiv (für anschließenden Klick)."""
        element = self._find_element(target)
        if element:
            try:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
                    element
                )
                self.driver.execute_script(
                    "arguments[0].classList.add('llars-highlight')",
                    element
                )
                time.sleep(duration)
                if not keep:
                    self.driver.execute_script(
                        "arguments[0].classList.remove('llars-highlight')",
                        element
                    )
            except Exception as e:
                # Stale element or page changed - just continue
                print(f"   ⚠️ Highlight fehlgeschlagen: {str(e)[:50]}")

    def show_title(self, title: str = "", subtitle: str = "", text: str = "",
                   columns: list = None):
        """Shows a fullscreen overlay with title, subtitle, optional text, and optional columns.

        columns: list of lists of {label, value} dicts — each inner list is one column.
        Example: [
            [{"label": "URL", "value": "https://..."}],
            [{"label": "Username", "value": "user"}, {"label": "Password", "value": "pass"}]
        ]
        """
        self._inject_styles()
        # Escape strings for JS
        title_js = title.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        subtitle_js = subtitle.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        text_js = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\n", "\\n")

        # Build columns JS snippet
        columns_js = ""
        if columns:
            import json
            columns_js = f"var cols = {json.dumps(columns)};"
            columns_js += """
                var cWrap = document.createElement('div');
                cWrap.className = 'llars-overlay-columns';
                cols.forEach(function(col) {
                    var cDiv = document.createElement('div');
                    cDiv.className = 'llars-overlay-column';
                    col.forEach(function(item) {
                        var lbl = document.createElement('div');
                        lbl.className = 'llars-overlay-cred-label';
                        lbl.textContent = item.label;
                        cDiv.appendChild(lbl);
                        var val = document.createElement('div');
                        val.className = 'llars-overlay-cred-value';
                        val.textContent = item.value;
                        cDiv.appendChild(val);
                    });
                    cWrap.appendChild(cDiv);
                });
                overlay.appendChild(cWrap);
            """

        self.driver.execute_script(f"""
            var old = document.getElementById('llars-overlay');
            if (old) old.remove();
            var overlay = document.createElement('div');
            overlay.id = 'llars-overlay';
            overlay.className = 'llars-overlay';
            if (`{title_js}`) {{
                var t = document.createElement('div');
                t.className = 'llars-overlay-title';
                t.textContent = `{title_js}`;
                overlay.appendChild(t);
            }}
            if (`{subtitle_js}`) {{
                var s = document.createElement('div');
                s.className = 'llars-overlay-subtitle';
                s.textContent = `{subtitle_js}`;
                overlay.appendChild(s);
            }}
            if (`{text_js}`) {{
                var x = document.createElement('div');
                x.className = 'llars-overlay-text';
                x.textContent = `{text_js}`;
                overlay.appendChild(x);
            }}
            {columns_js}
            document.body.appendChild(overlay);
            requestAnimationFrame(function() {{
                requestAnimationFrame(function() {{
                    overlay.classList.add('visible');
                }});
            }});
        """)
        print(f"   🎬 show_title: {title} - {subtitle}")

    def hide_title(self):
        """Fades out and removes the fullscreen overlay."""
        self.driver.execute_script("""
            var overlay = document.getElementById('llars-overlay');
            if (overlay) {
                overlay.classList.remove('visible');
                setTimeout(function() { overlay.remove(); }, 600);
            }
        """)
        print(f"   🎬 hide_title")

    def show_pipeline(self, title: str = "", subtitle: str = "", columns: list = None):
        """Shows an HTML pipeline diagram as overlay, matching the paper's Figure 1.

        Uses LLARS design colors: Prompt=#B0CA97, Batch=#88C4C8, Eval=#D1BC8A, Outcome=#E8A087.
        Each module has an ID (pipeline-prompt, pipeline-batch, pipeline-eval, pipeline-outcome)
        that can be targeted by the highlight action via ELEMENT_MAP.
        """
        self._inject_styles()
        title_js = title.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        subtitle_js = subtitle.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

        columns_js = ""
        if columns:
            import json
            columns_js = f"var cols = {json.dumps(columns)};"
            columns_js += """
            if (cols && cols.length) {
                var cWrap = document.createElement('div');
                cWrap.className = 'llars-overlay-columns';
                cWrap.id = 'pipeline-credentials';
                cols.forEach(function(col){
                    var c = document.createElement('div');
                    c.className = 'llars-overlay-column';
                    (col || []).forEach(function(item){
                        var l = document.createElement('div');
                        l.className = 'llars-overlay-cred-label';
                        l.textContent = item.label || '';
                        var v = document.createElement('div');
                        v.className = 'llars-overlay-cred-value';
                        v.textContent = item.value || '';
                        c.appendChild(l);
                        c.appendChild(v);
                    });
                    cWrap.appendChild(c);
                });
                overlay.appendChild(cWrap);
            }
            """

        self.driver.execute_script(f"""
            var old = document.getElementById('llars-overlay');
            if (old) old.remove();

            var overlay = document.createElement('div');
            overlay.id = 'llars-overlay';
            overlay.className = 'llars-overlay';

            if (`{title_js}`) {{
                var t = document.createElement('div');
                t.className = 'llars-overlay-title';
                t.textContent = `{title_js}`;
                overlay.appendChild(t);
            }}
            if (`{subtitle_js}`) {{
                var s = document.createElement('div');
                s.className = 'llars-overlay-subtitle';
                s.textContent = `{subtitle_js}`;
                overlay.appendChild(s);
            }}

            var pipeline = document.createElement('div');
            pipeline.className = 'pipeline-container';
            pipeline.innerHTML = `
                <div class="pipeline-row">
                    <div class="pipeline-actor">Domain Experts<br>&amp; Developers</div>
                    <div class="pipeline-arrow">\u2192</div>
                    <div class="pipeline-module pipeline-prompt" id="pipeline-prompt">
                        Collaborative<br>Prompt Engineering
                    </div>
                    <div class="pipeline-arrow-dash">\u27F6</div>
                    <div class="pipeline-export">Prompt</div>
                </div>
                <div class="pipeline-flow"><span class="pipeline-flow-arrow">\u2193</span><span class="pipeline-flow-label">Prompts</span></div>
                <div class="pipeline-row">
                    <div class="pipeline-actor">Domain<br>Data</div>
                    <div class="pipeline-arrow">\u2192</div>
                    <div class="pipeline-module pipeline-batch" id="pipeline-batch">
                        Batch<br>Generation
                    </div>
                    <div class="pipeline-arrow-dash">\u27F6</div>
                    <div class="pipeline-export">LLM Outputs</div>
                </div>
                <div class="pipeline-flow"><span class="pipeline-flow-arrow">\u2193</span><span class="pipeline-flow-label">Outputs</span></div>
                <div class="pipeline-row">
                    <div class="pipeline-actor">Human &amp;<br>LLM Evaluators</div>
                    <div class="pipeline-arrow">\u2192</div>
                    <div class="pipeline-module pipeline-eval" id="pipeline-eval">
                        Evaluation
                    </div>
                    <div class="pipeline-arrow-dash">\u27F6</div>
                    <div class="pipeline-export">Evaluation<br>Results</div>
                </div>
                <div class="pipeline-flow"><span class="pipeline-flow-arrow">\u2193</span></div>
                <div class="pipeline-outcome" id="pipeline-outcome">
                    Best LLM &amp; Prompt Pair
                </div>
                <div class="pipeline-llars-label">LLARS</div>
            `;

            overlay.appendChild(pipeline);
            {columns_js}
            document.body.appendChild(overlay);

            requestAnimationFrame(function() {{
                requestAnimationFrame(function() {{
                    overlay.classList.add('visible');
                }});
            }});
        """)
        print(f"   🎬 show_pipeline")

    def show_problem(self):
        """Shows an animated problem overlay: domain experts vs developers working in isolation.

        Phase 1 (0-1s):   Two boxes slide in from left and right
        Phase 2 (1-2.5s): Gap with X appears between them
        Phase 3 (2.5-4s): Pain point pills and interview quote fade in
        All phases are CSS animation-delay driven, no manual triggering needed.
        """
        self._inject_styles()

        self.driver.execute_script("""
            var old = document.getElementById('llars-overlay');
            if (old) old.remove();

            var overlay = document.createElement('div');
            overlay.id = 'llars-overlay';
            overlay.className = 'llars-overlay';

            var wrapper = document.createElement('div');
            wrapper.className = 'problem-wrapper';
            wrapper.innerHTML = `
                <div class="problem-container">
                    <div class="problem-box problem-left" id="problem-expert">
                        <div class="problem-box-title">Domain Expert</div>
                        <div class="problem-box-subtitle">Knows what quality means</div>
                        <div class="problem-box-items">
                            <div class="problem-item">Defines quality criteria</div>
                            <div class="problem-item">Writes evaluation guidelines</div>
                            <div class="problem-item">Assesses outputs manually</div>
                        </div>
                    </div>
                    <div class="problem-gap" id="problem-gap">
                        <div class="problem-gap-line"></div>
                        <div class="problem-gap-x">\u2715</div>
                        <div class="problem-gap-line"></div>
                    </div>
                    <div class="problem-box problem-right" id="problem-developer">
                        <div class="problem-box-title">Developer</div>
                        <div class="problem-box-subtitle">Knows how to build pipelines</div>
                        <div class="problem-box-items">
                            <div class="problem-item">Configures LLM models</div>
                            <div class="problem-item">Builds generation pipelines</div>
                            <div class="problem-item">Runs technical evaluation</div>
                        </div>
                    </div>
                    <div class="problem-merge-border"></div>
                    <div class="problem-merge-label">LLARS</div>
                </div>
                <div class="problem-painpoints" id="problem-painpoints">
                    <div class="problem-pain">Shared Documents</div>
                    <div class="problem-pain-dot">\u00B7</div>
                    <div class="problem-pain">No Version Control</div>
                    <div class="problem-pain-dot">\u00B7</div>
                    <div class="problem-pain">Manual Evaluation</div>
                </div>
                <div class="problem-quote" id="problem-quote">
                    \u201CTranslation work between disciplines\u201D
                </div>
            `;

            overlay.appendChild(wrapper);
            document.body.appendChild(overlay);

            requestAnimationFrame(function() {
                requestAnimationFrame(function() {
                    overlay.classList.add('visible');
                });
            });
        """)
        print(f"   🎬 show_problem")

    def merge_problem(self):
        """Animates the problem boxes merging: gap shrinks, dashed LLARS border appears."""
        self.driver.execute_script("""
            var container = document.querySelector('.problem-container');
            var gap = document.querySelector('.problem-gap');
            var painpoints = document.querySelector('.problem-painpoints');
            var quote = document.querySelector('.problem-quote');

            // Fade out pain points and quote
            if (painpoints) {
                painpoints.style.transition = 'opacity 0.4s ease';
                painpoints.style.opacity = '0';
            }
            if (quote) {
                quote.style.transition = 'opacity 0.4s ease';
                quote.style.opacity = '0';
            }

            // Shrink the gap (X and lines disappear)
            if (gap) {
                gap.style.transition = 'width 0.6s ease, opacity 0.3s ease, min-height 0.6s ease';
                gap.style.width = '0';
                gap.style.minHeight = '0';
                gap.style.opacity = '0';
                gap.style.overflow = 'hidden';
            }

            // Show dashed border + LLARS label
            if (container) {
                container.classList.add('merged');
            }
        """)
        print(f"   🎬 merge_problem")

    def show_data_preview(self):
        """Shows an overlay with a JSON data preview, highlighting subject/content keys."""
        self._inject_styles()

        self.driver.execute_script("""
            var old = document.getElementById('llars-overlay');
            if (old) old.remove();

            var overlay = document.createElement('div');
            overlay.id = 'llars-overlay';
            overlay.className = 'llars-overlay';

            var wrapper = document.createElement('div');
            wrapper.className = 'data-preview-wrapper';

            var title = document.createElement('div');
            title.className = 'llars-overlay-title';
            title.style.fontSize = '42px';
            title.textContent = 'Source Data';
            wrapper.appendChild(title);

            var subtitle = document.createElement('div');
            subtitle.className = 'llars-overlay-subtitle';
            subtitle.textContent = '10 Counselling Cases (JSON)';
            wrapper.appendChild(subtitle);

            var code = document.createElement('div');
            code.className = 'data-preview-code';
            code.innerHTML = '<span class="dp-bracket">[</span>\\n' +
                '  <span class="dp-bracket">{</span>\\n' +
                '    <span class="dp-key">"subject"</span>: <span class="dp-str">"Custody concerns after separation"</span>,\\n' +
                '    <span class="dp-key">"content"</span>: <span class="dp-str">"Client wrote on 12/01/2026 ..."</span>\\n' +
                '  <span class="dp-bracket">}</span>,\\n' +
                '  <span class="dp-bracket">{</span>\\n' +
                '    <span class="dp-key">"subject"</span>: <span class="dp-str">"School refusal and possible bullying"</span>,\\n' +
                '    <span class="dp-key">"content"</span>: <span class="dp-str">"Client wrote on 05/01/2026 ..."</span>\\n' +
                '  <span class="dp-bracket">}</span>,\\n' +
                '  <span class="dp-dots">... 8 more cases</span>\\n' +
                '<span class="dp-bracket">]</span>';
            wrapper.appendChild(code);

            var count = document.createElement('div');
            count.className = 'data-preview-count';
            count.innerHTML = 'Fields <span style="color:#b0ca97;font-weight:700">subject</span> and <span style="color:#b0ca97;font-weight:700">content</span> map to template variables';
            wrapper.appendChild(count);

            overlay.appendChild(wrapper);
            document.body.appendChild(overlay);

            requestAnimationFrame(function() {
                requestAnimationFrame(function() {
                    overlay.classList.add('visible');
                });
            });
        """)
        print(f"   🎬 show_data_preview")

    def do_visible_login(self, username: str, password: str):
        """Performs login visibly with typed credentials (for recording)."""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".login-form, [data-testid='login-form']"))
            )
            time.sleep(0.3)

            # Type username
            username_field = None
            for selector in [
                "[data-testid='username-input'] input",
                ".login-form input[name='username']",
                ".login-form .v-text-field:first-of-type input",
                "input#username",
            ]:
                try:
                    username_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if username_field and username_field.is_displayed():
                        break
                except Exception:
                    continue

            if username_field:
                username_field.click()
                time.sleep(0.2)
                username_field.clear()
                for char in username:
                    username_field.send_keys(char)
                    time.sleep(0.03)
                print(f"   ⌨️ Username: {username}")
            time.sleep(0.3)

            # Type password
            password_field = None
            for selector in [
                "[data-testid='password-input'] input",
                ".login-form input[name='password']",
                ".login-form input[type='password']",
                "input#password",
            ]:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field and password_field.is_displayed():
                        break
                except Exception:
                    continue

            if password_field:
                password_field.click()
                time.sleep(0.2)
                password_field.clear()
                for char in password:
                    password_field.send_keys(char)
                    time.sleep(0.03)
                print(f"   ⌨️ Password: {'*' * len(password)}")
            time.sleep(0.3)

            # Click login button
            login_btn = None
            for selector in [
                "[data-testid='login-btn']",
                ".login-button",
                ".login-form button[type='submit']",
                ".login-form .l-btn",
            ]:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn and login_btn.is_displayed():
                        break
                except Exception:
                    continue

            if login_btn:
                self.driver.execute_script("arguments[0].click()", login_btn)
                print(f"   🔐 Login button clicked")

            # Wait for redirect
            for attempt in range(10):
                time.sleep(1)
                if '/login' not in self.driver.current_url.lower():
                    print(f"   ✓ Login erfolgreich!")
                    break
            else:
                print(f"   ⚠️ Login redirect timeout")

            time.sleep(1)
            self._inject_styles()
            self._dismiss_cookie_banner()

        except Exception as e:
            print(f"   ⚠️ Visible login error: {e}")

    def drag(self, source: str, target: str):
        """Drag & Drop via JS mouse events (works with SortableJS/vuedraggable)"""
        src = self._find_element(source)
        tgt = self._find_element(target)
        if not src or not tgt:
            print(f"   ✗ drag: {source if not src else target} (NICHT GEFUNDEN)")
            return
        try:
            # Use JS-based drag simulation for SortableJS compatibility
            self.driver.execute_script("""
                function simulateDrag(src, tgt) {
                    var srcRect = src.getBoundingClientRect();
                    var tgtRect = tgt.getBoundingClientRect();
                    var sx = srcRect.left + srcRect.width / 2;
                    var sy = srcRect.top + srcRect.height / 2;
                    var tx = tgtRect.left + tgtRect.width / 2;
                    var ty = tgtRect.top + tgtRect.height / 2;

                    function fire(el, type, x, y) {
                        el.dispatchEvent(new PointerEvent(type, {
                            bubbles: true, cancelable: true,
                            clientX: x, clientY: y, pointerId: 1
                        }));
                    }
                    fire(src, 'pointerdown', sx, sy);
                    // Small movement to trigger SortableJS drag detection
                    setTimeout(function() {
                        fire(src, 'pointermove', sx + 5, sy + 5);
                        setTimeout(function() {
                            fire(tgt, 'pointermove', tx, ty);
                            setTimeout(function() {
                                fire(tgt, 'pointerup', tx, ty);
                            }, 50);
                        }, 100);
                    }, 100);
                }
                simulateDrag(arguments[0], arguments[1]);
            """, src, tgt)
            print(f"   ↔️ Drag: {source} → {target}")
            time.sleep(0.5)
        except Exception:
            # Fallback to ActionChains
            ActionChains(self.driver).drag_and_drop(src, tgt).perform()
            print(f"   ↔️ Drag (fallback): {source} → {target}")
            time.sleep(0.3)

    def upload(self, file_path: str, wait_for_processing: bool = True):
        """Lädt Datei hoch und wartet optional auf Verarbeitung"""
        resolved_path = _resolve_local_path(file_path)
        abs_path = str(resolved_path.resolve())

        # Finde File Input (kann hidden sein)
        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(abs_path)
        print(f"   📁 Upload: {file_path}")

        if not wait_for_processing:
            time.sleep(0.5)
            return

        # Warte auf File-Verarbeitung (Vue parst die Datei async)
        time.sleep(1)

        # Prüfe ob Daten geladen wurden
        for attempt in range(10):
            try:
                # Methode 1: Suche nach LTag mit "items parsed" Text
                tags = self.driver.find_elements(By.CSS_SELECTOR, ".source-config .l-tag, .upload-zone + * .l-tag")
                for tag in tags:
                    if 'parsed' in tag.text.lower() or 'items' in tag.text.lower():
                        print(f"   ✓ Datei verarbeitet: {tag.text}")
                        time.sleep(0.5)
                        return

                # Methode 2: Prüfe ob Next-Button enabled ist
                next_btns = self.driver.find_elements(By.CSS_SELECTOR,
                    ".wizard-actions .l-btn:not([disabled]), .generation-wizard .v-btn:not([disabled])")
                for btn in next_btns:
                    if 'next' in btn.text.lower() and btn.is_enabled():
                        print(f"   ✓ Wizard bereit (Next Button aktiv)")
                        time.sleep(0.5)
                        return

            except Exception as e:
                pass
            time.sleep(0.5)

        print(f"   ⚠️ Timeout beim Warten auf Datei-Verarbeitung")
        time.sleep(1)

    def set_text_from_file(self, target: str, file_path: str):
        """Setzt Textfeld-Inhalt direkt aus Datei (ohne File-Dialog)"""
        abs_path = _resolve_local_path(file_path).resolve()
        if not abs_path.exists():
            print(f"   ⚠️ Datei nicht gefunden: {file_path}")
            return False
        try:
            content = abs_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"   ⚠️ Datei lesen fehlgeschlagen: {str(e)[:50]}")
            return False

        element = self._find_element(target)
        if not element:
            print(f"   ✗ set_text_from_file: {target} (NICHT GEFUNDEN)")
            return False

        try:
            self.driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                element,
                content
            )
            print(f"   ✓ set_text_from_file: {file_path}")
            return True
        except Exception as e:
            print(f"   ⚠️ set_text_from_file Fehler: {str(e)[:50]}")
            return False

    def close_file_dialog(self):
        """Schließt das native Datei-Dialogfenster (z.B. macOS Finder)"""
        import platform
        try:
            if platform.system() == 'Darwin':
                time.sleep(0.2)
                # Mehrere Fallbacks: ESC, Cmd+W, Cmd+., Klick auf Cancel/Abbrechen
                scripts = [
                    'tell application "System Events" to key code 53',  # ESC
                    'tell application "System Events" to keystroke "w" using {command down}',  # Cmd+W
                    'tell application "System Events" to keystroke "." using {command down}',  # Cmd+.
                    # Frontmost app sheet cancel (best-effort)
                    'tell application "System Events" to set frontApp to name of first process whose frontmost is true\n'
                    'tell application "System Events" to tell process frontApp to if (exists sheet 1 of window 1) then\n'
                    'try\n'
                    'click button "Cancel" of sheet 1 of window 1\n'
                    'end try\n'
                    'try\n'
                    'click button "Abbrechen" of sheet 1 of window 1\n'
                    'end try\n'
                    'end if',
                    # Try clicking Cancel/Abbrechen on common browser processes
                    'tell application "System Events" to tell process "Google Chrome" to if (exists sheet 1 of window 1) then click button "Cancel" of sheet 1 of window 1',
                    'tell application "System Events" to tell process "Google Chrome" to if (exists sheet 1 of window 1) then click button "Abbrechen" of sheet 1 of window 1',
                    'tell application "System Events" to tell process "Chromium" to if (exists sheet 1 of window 1) then click button "Cancel" of sheet 1 of window 1',
                    'tell application "System Events" to tell process "Chromium" to if (exists sheet 1 of window 1) then click button "Abbrechen" of sheet 1 of window 1'
                ]
                for script in scripts:
                    subprocess.run(['osascript', '-e', script], capture_output=True)
                    time.sleep(0.15)
                print("   ✓ Datei-Dialog schließen versucht (macOS)")
            else:
                # Fallback: ESC an die Seite senden
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ESCAPE)
                except Exception:
                    pass
                print("   ✓ Datei-Dialog geschlossen (fallback)")
        except Exception as e:
            print(f"   ⚠️ Datei-Dialog schließen fehlgeschlagen: {str(e)[:50]}")

    def wait_for(self, target: str, timeout: float = 10):
        """Wartet auf Element"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._find_element_in_driver(self.driver, target):
                return
            time.sleep(0.2)
        print(f"⚠️ Timeout: {target}")

    def dismiss_dialog(self):
        """Schließt offenes Dialog/Modal via Overlay-Klick und ESC"""
        try:
            # Methode 1: Klick auf Vuetify v-overlay (schließt non-persistent Dialoge)
            overlays = self.driver.find_elements(By.CSS_SELECTOR, ".v-overlay--active .v-overlay__scrim")
            for overlay in overlays:
                try:
                    if overlay.is_displayed():
                        overlay.click()
                        time.sleep(0.3)
                except Exception:
                    pass
            # Methode 2: ESC-Taste als Fallback
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.5)
            # Methode 3: Vue-Zustand zurücksetzen via JS
            self.driver.execute_script("""
                // Force-close any open v-dialogs by resetting their model
                document.querySelectorAll('.v-overlay--active').forEach(el => {
                    el.style.display = 'none';
                });
            """)
            time.sleep(0.3)
        except Exception:
            pass

    def wait_for_modal(self):
        """Wartet auf Modal-Dialog"""
        time.sleep(0.5)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".v-dialog, .modal, [role='dialog']"))
            )
        except Exception:
            pass
        time.sleep(0.3)

    # =========================================================================
    # COLLAB BROWSER - Zweiter Browser für Echtzeit-Kollaboration Demo
    # =========================================================================

    def _disable_stage_manager(self):
        """Deaktiviert macOS Stage Manager für Side-by-Side."""
        import platform
        if platform.system() != 'Darwin':
            return
        try:
            result = subprocess.run(
                ['defaults', 'read', 'com.apple.WindowManager', 'GloballyEnabled'],
                capture_output=True, text=True, timeout=5
            )
            self._stage_manager_was_enabled = result.stdout.strip() == '1'
            if self._stage_manager_was_enabled:
                subprocess.run(
                    ['defaults', 'write', 'com.apple.WindowManager', 'GloballyEnabled', '-bool', 'false'],
                    check=True, timeout=5
                )
                subprocess.run(['killall', 'Dock'], timeout=5)
                time.sleep(2)
                print("   👥 Stage Manager temporär deaktiviert")
        except Exception as e:
            print(f"   ⚠️ Stage Manager Prüfung fehlgeschlagen: {e}")
            self._stage_manager_was_enabled = False

    def _hide_other_windows(self):
        """Blendet alle Fenster außer Chrome aus (nach Positionierung aufrufen!)."""
        import platform
        if platform.system() != 'Darwin':
            return
        try:
            subprocess.run(['osascript', '-e', '''
                tell application "System Events"
                    set visible of every process whose name is not "Google Chrome" ¬
                        and name is not "Dock" ¬
                        and name is not "SystemUIServer" ¬
                        and name is not "Window Manager" ¬
                        and name is not "WindowManager" to false
                end tell
            '''], capture_output=True, timeout=5)
            print("   👥 Alle anderen Fenster ausgeblendet")
        except Exception:
            pass

    def _restore_stage_manager(self):
        """Stellt den vorherigen Stage Manager Zustand wieder her."""
        import platform
        if platform.system() != 'Darwin':
            return
        if getattr(self, '_stage_manager_was_enabled', False):
            try:
                subprocess.run(
                    ['defaults', 'write', 'com.apple.WindowManager', 'GloballyEnabled', '-bool', 'true'],
                    check=True, timeout=5
                )
                subprocess.run(['killall', 'Dock'], timeout=5)
                print("   👥 Stage Manager wiederhergestellt")
            except Exception:
                pass
            self._stage_manager_was_enabled = False

    def _tile_chrome_windows(self, left_bounds, right_bounds):
        """Positioniert Chrome-Fenster per AppleScript (Fallback wenn Selenium nicht reicht)."""
        import platform
        if platform.system() != 'Darwin':
            return
        lx, ly, lw, lh = left_bounds
        rx, ry, rw, rh = right_bounds
        try:
            subprocess.run(['osascript', '-e', f'''
                tell application "System Events"
                    set chromeProcs to every process whose name is "Google Chrome"
                    set allWins to {{}}
                    repeat with proc in chromeProcs
                        repeat with w in windows of proc
                            set end of allWins to w
                        end repeat
                    end repeat
                    if (count of allWins) >= 2 then
                        set position of item 1 of allWins to {{{lx}, {ly}}}
                        set size of item 1 of allWins to {{{lw}, {lh}}}
                        set position of item 2 of allWins to {{{rx}, {ry}}}
                        set size of item 2 of allWins to {{{rw}, {rh}}}
                    end if
                end tell
            '''], capture_output=True, timeout=5)
        except Exception as e:
            print(f"   ⚠️ AppleScript Fenster-Tiling fehlgeschlagen: {e}")

    def collab_open(self, username: str = "researcher", password: str = "admin123"):
        """
        Öffnet einen zweiten Browser für die Kollaborations-Demo.
        Side-by-Side Layout: Hauptbrowser links (50%), Collab-Browser rechts (50%).
        Deaktiviert macOS Stage Manager falls nötig.
        """
        print(f"   👥 Öffne Collab-Browser als '{username}' (Side-by-Side)...")

        # Stage Manager wurde bereits in ScriptRunner.run() deaktiviert

        # 1. Originale Bounds speichern für späteres Restore
        self._original_window_bounds = self.get_window_bounds()
        mx, my, mw, mh = self._original_window_bounds
        half_w = mw // 2

        # 2. Hauptbrowser auf linke Hälfte — Position ZUERST (macOS Window-Manager)
        self.driver.set_window_position(mx, my)
        time.sleep(0.2)
        self.driver.set_window_size(half_w, mh)
        time.sleep(0.5)
        print(f"   👥 Hauptbrowser → links: ({mx},{my}) {half_w}x{mh}")

        # 3. Collab-Browser erstellen — Position/Size als Launch-Flags
        options = Options()
        options.add_argument(f'--window-position={mx + half_w},{my}')
        options.add_argument(f'--window-size={half_w},{mh}')
        options.add_argument('--no-first-run')
        options.add_argument('--no-default-browser-check')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.password_manager_leak_detection': False,
        })

        service = Service(ChromeDriverManager().install())
        self.collab_driver = webdriver.Chrome(service=service, options=options)
        time.sleep(1.0)

        # 4. Positionen reinforcen — Collab zuerst, dann Hauptbrowser
        self.collab_driver.set_window_position(mx + half_w, my)
        self.collab_driver.set_window_size(half_w, mh)
        time.sleep(0.3)
        self.driver.set_window_position(mx, my)
        self.driver.set_window_size(half_w, mh)
        time.sleep(0.5)

        # 5. JETZT andere Fenster ausblenden (NACH Positionierung, sonst verschiebt macOS die Chrome-Fenster)
        self._hide_other_windows()
        print(f"   👥 Collab-Browser → rechts: ({mx + half_w},{my}) {half_w}x{mh}")

        # Zur Login-Seite navigieren
        self.collab_driver.get(self.base_url)
        time.sleep(2)

        # Sprache für Collab-User auf Englisch setzen
        self._set_language_for_driver(self.collab_driver, "en")

        # Login - try dev button first, then form/Authentik login
        self._collab_login(username, password)

    def _collab_login(self, username: str, password: str):
        """Login for the collab browser. Handles dev buttons, form login, and Authentik."""
        driver = self.collab_driver

        # Method 1: Dev Quick Login Button (development only)
        try:
            dev_btn_selector = f"[data-testid='dev-login-btn-{username}']"
            dev_btn = driver.find_element(By.CSS_SELECTOR, dev_btn_selector)
            if dev_btn and dev_btn.is_displayed():
                driver.execute_script("arguments[0].click()", dev_btn)
                print(f"   ✓ Collab-User '{username}' via Dev-Button eingeloggt")
                time.sleep(2)
                return
        except Exception:
            pass

        # Detect page state
        current_url = driver.current_url.lower()
        is_authentik = 'authentik' in current_url or '/auth/' in current_url

        if is_authentik:
            self._collab_authentik_login(driver, username, password)
        else:
            # Method 2: LLARS form login (clicks through to Authentik on production)
            self._collab_form_login(driver, username, password)

        # Verify login succeeded
        for attempt in range(8):
            time.sleep(1)
            url = driver.current_url.lower()
            if '/home' in url or '/promptengineering' in url or '/generation' in url:
                print(f"   ✓ Collab-User '{username}' eingeloggt")
                return
            elif 'authentik' in url or '/auth/' in url:
                # Landed on Authentik - do 2-step login
                self._collab_authentik_login(driver, username, password)
            elif '/login' in url:
                # Still on LLARS login - try form
                self._collab_form_login(driver, username, password)
        print(f"   ⚠️ Collab-Login Status unklar (URL: {driver.current_url})")

    def _collab_form_login(self, driver, username: str, password: str):
        """Form-based login on LLARS login page for collab browser."""
        print(f"   🔐 Collab Formular-Login als: {username}")
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    ".login-form, [data-testid='login-form'], .login-card"))
            )
            time.sleep(0.5)

            # Enter username
            for sel in ["[data-testid='username-input'] input",
                        ".login-form input[name='username']",
                        ".login-form .v-text-field:first-of-type input",
                        "input#username"]:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, sel)
                    if field and field.is_displayed():
                        field.clear()
                        field.send_keys(username)
                        break
                except Exception:
                    continue

            time.sleep(0.3)

            # Enter password
            for sel in ["[data-testid='password-input'] input",
                        ".login-form input[name='password']",
                        ".login-form input[type='password']",
                        "input#password"]:
                try:
                    field = driver.find_element(By.CSS_SELECTOR, sel)
                    if field and field.is_displayed():
                        field.clear()
                        field.send_keys(password)
                        break
                except Exception:
                    continue

            time.sleep(0.3)

            # Click login button
            for sel in ["[data-testid='login-btn']", ".login-button",
                        ".login-form button[type='submit']", ".login-form .l-btn"]:
                try:
                    btn = driver.find_element(By.CSS_SELECTOR, sel)
                    if btn and btn.is_displayed():
                        driver.execute_script("arguments[0].click()", btn)
                        break
                except Exception:
                    continue

            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Collab Formular-Login Fehler: {e}")

    def _collab_authentik_login(self, driver, username: str, password: str):
        """Authentik 2-step login for collab browser."""
        print(f"   🔐 Collab Authentik-Login als: {username}")
        try:
            # Step 1: Username
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[name='uidField'], input[name='username'], input[type='text']"))
            )
            username_field.clear()
            username_field.send_keys(username)

            submit_btn = driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], .pf-c-button.pf-m-primary")
            submit_btn.click()
            time.sleep(2)

            # Step 2: Password
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "input[name='password'], input[type='password']"))
            )
            password_field.clear()
            password_field.send_keys(password)

            submit_btn = driver.find_element(By.CSS_SELECTOR,
                "button[type='submit'], .pf-c-button.pf-m-primary")
            submit_btn.click()
            time.sleep(3)
        except Exception as e:
            print(f"   ⚠️ Collab Authentik-Login Fehler: {e}")

    def collab_goto(self, path: str):
        """Navigiert den Collab-Browser zu einer URL"""
        if not self.collab_driver:
            print("   ⚠️ Collab-Browser nicht geöffnet!")
            return

        url = f"{self.base_url}{path}" if path.startswith('/') else path
        print(f"   👥 Collab navigiert zu: {path}")
        self.collab_driver.get(url)
        time.sleep(2)

    def _find_element_in_driver(self, driver, target: str):
        """Findet Element in einem beliebigen WebDriver (für Collab-Support)"""
        selectors = ELEMENT_MAP.get(target, target)

        for selector in selectors.split(', '):
            selector = selector.strip()
            try:
                if ':contains(' in selector:
                    base, text = selector.split(':contains(')
                    text = text.rstrip(')').strip("'\"")
                    elements = driver.find_elements(By.CSS_SELECTOR, base or '*')
                    for el in elements:
                        if text.lower() in el.text.lower():
                            try:
                                if not el.is_displayed():
                                    continue
                            except Exception:
                                continue
                            return el
                else:
                    el = driver.find_element(By.CSS_SELECTOR, selector)
                    if el:
                        try:
                            if not el.is_displayed():
                                continue
                        except Exception:
                            continue
                        return el
            except Exception:
                continue

        # Fallback: Text-Suche in klickbaren Elementen
        try:
            clickables = driver.find_elements(
                By.CSS_SELECTOR,
                'a, button, [role="button"], .v-btn, .v-list-item, .v-card, .prompt-card'
            )
            target_lower = target.lower()
            for el in clickables:
                try:
                    if target_lower in el.text.lower():
                        return el
                except Exception:
                    continue
        except Exception:
            pass

        return None

    def collab_click(self, target: str):
        """Klickt auf ein Element im Collab-Browser"""
        if not self.collab_driver:
            return

        element = self._find_element_in_driver(self.collab_driver, target)
        if element:
            self.collab_driver.execute_script("arguments[0].click()", element)
            print(f"   👥 Collab klickt: {target}")
        else:
            print(f"   ⚠️ Collab konnte '{target}' nicht finden")

    def collab_type(self, target: str, text: str, delay: float = 0.08, cursor: str = "end"):
        """
        Tippt Text in ein Element im Collab-Browser.
        Der Text erscheint mit dem Cursor des Collab-Users im Hauptbrowser.
        """
        if not self.collab_driver:
            print("   ⚠️ Collab-Browser nicht geöffnet!")
            return

        element = self._find_element_in_driver(self.collab_driver, target)
        if element:
            # Klicke erst in das Element um Fokus zu setzen
            self.collab_driver.execute_script("arguments[0].click(); arguments[0].focus();", element)
            time.sleep(0.3)

            # Optional: Cursor gezielt an den Anfang/ans Ende setzen (z.B. für "oben drüber" schreiben)
            cursor_mode = (cursor or "end").lower()
            if cursor_mode in ("start", "end"):
                self.collab_driver.execute_script(
                    """
                    const el = arguments[0];
                    const atStart = arguments[1];
                    const sel = window.getSelection();
                    const range = document.createRange();
                    range.selectNodeContents(el);
                    range.collapse(atStart);
                    sel.removeAllRanges();
                    sel.addRange(range);
                    """,
                    element,
                    cursor_mode == "start"
                )
                time.sleep(0.1)

            # Tippe jeden Buchstaben einzeln für sichtbaren Effekt
            print(f"   👥 Collab tippt in '{target}' ({cursor_mode}): {text[:30]}...")
            for char in text:
                element.send_keys(char)
                time.sleep(delay)
            print(f"   ✓ Collab-Eingabe abgeschlossen")
        else:
            print(f"   ⚠️ Collab konnte '{target}' nicht finden")

    def collab_focus_editor(self):
        """Fokussiert den Editor im Collab-Browser (für Cursor-Anzeige)"""
        if not self.collab_driver:
            return

        try:
            # Finde den Quill-Editor
            editor = self.collab_driver.find_element(By.CSS_SELECTOR, ".ql-editor")
            # Klicke hinein und bewege den Cursor
            self.collab_driver.execute_script("""
                arguments[0].click();
                arguments[0].focus();
                // Cursor ans Ende setzen
                var range = document.createRange();
                range.selectNodeContents(arguments[0]);
                range.collapse(false);
                var sel = window.getSelection();
                sel.removeAllRanges();
                sel.addRange(range);
            """, editor)
            print(f"   👥 Collab-Cursor im Editor aktiv")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Collab-Editor-Fokus fehlgeschlagen: {e}")

    def collab_close(self):
        """Schließt den Collab-Browser und stellt Hauptbrowser auf volle Breite zurück."""
        if self.collab_driver:
            self.collab_driver.quit()
            self.collab_driver = None
            print("   👥 Collab-Browser geschlossen")

        # Hauptbrowser auf volle Breite zurücksetzen
        if hasattr(self, '_original_window_bounds') and self._original_window_bounds:
            mx, my, mw, mh = self._original_window_bounds
            self.driver.set_window_position(mx, my)
            self.driver.set_window_size(mw, mh)
            print(f"   👥 Hauptbrowser → volle Breite: ({mx},{my}) {mw}x{mh}")
            self._original_window_bounds = None
            time.sleep(0.3)

        # Stage Manager bleibt deaktiviert bis Aufnahme-Ende (ScriptRunner.run() stellt wieder her)

    def close(self):
        """Schließt Browser"""
        # Collab-Browser auch schließen
        if self.collab_driver:
            self.collab_driver.quit()
            self.collab_driver = None
        if self.driver:
            self.driver.quit()


# =============================================================================
# SCRIPT RUNNER
# =============================================================================

class ScriptRunner:
    """Führt SCRIPT.json aus"""

    SECTION_HASHES_FILE = f"{AUDIO_DIR}/.section_hashes.json"
    AUDIO_HASHES_FILE = f"{AUDIO_DIR}/.audio_hashes.json"

    def __init__(self, script_path: str = SCRIPT_FILE):
        self.script_path = script_path
        self.script = None
        self.browser = None
        self.tts = None
        self.recorder = None
        self.tts_model_override = None  # Überschreibt tts_model aus SCRIPT.json
        self.use_voice_cloning = False  # Voice Cloning ist SEHR langsam auf CPU!

    def load_script(self):
        """Lädt Skript"""
        script_path = _resolve_local_path(self.script_path)
        self.script_path = str(script_path)
        with open(self.script_path, encoding="utf-8") as f:
            self.script = json.load(f)
        print(f"✓ Skript geladen: {len(self.script['steps'])} Schritte")

    # =========================================================================
    # SECTION-BASIERTES AUDIO-CACHING
    # =========================================================================

    def _get_sections(self) -> dict:
        """
        Gruppiert Steps nach Sections.

        Gibt zurück: {section_name: [step1, step2, ...]}
        """
        self.load_script()

        sections = {}
        current_section = "INTRO"

        for step in self.script['steps']:
            # Neue Section beginnt
            if '_section' in step:
                # Extrahiere Section-Name aus "=== NAME (30s) ==="
                section_marker = step['_section']
                # Parse: "=== INTRO (25s) ===" → "INTRO"
                import re
                match = re.search(r'===\s*([A-Z\s]+)', section_marker)
                if match:
                    current_section = match.group(1).strip()

            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(step)

        return sections

    def _compute_section_hash(self, steps: list) -> str:
        """
        Berechnet Hash für eine Section basierend auf allen Narrations.

        Inkludiert: narration + speaker für jeden Step
        """
        content_parts = []
        for step in steps:
            narration = step.get('narration', '')
            speaker = step.get('speaker', 'default')
            step_id = step.get('id', '')
            content_parts.append(f"{step_id}|{speaker}|{narration}")

        content = "\n".join(content_parts)
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _load_section_hashes(self) -> dict:
        """Lädt gespeicherte Section-Hashes"""
        if os.path.exists(self.SECTION_HASHES_FILE):
            with open(self.SECTION_HASHES_FILE) as f:
                return json.load(f)
        return {}

    def _save_section_hashes(self, hashes: dict):
        """Speichert Section-Hashes"""
        with open(self.SECTION_HASHES_FILE, 'w') as f:
            json.dump(hashes, f, indent=2)

    def _load_audio_hashes(self) -> dict:
        """Lädt gespeicherte Audio-Hashes (pro Step)"""
        if os.path.exists(self.AUDIO_HASHES_FILE):
            with open(self.AUDIO_HASHES_FILE) as f:
                return json.load(f)
        return {}

    def _save_audio_hashes(self, hashes: dict):
        """Speichert Audio-Hashes (pro Step)"""
        with open(self.AUDIO_HASHES_FILE, 'w') as f:
            json.dump(hashes, f, indent=2)

    def _compute_step_hash(self, step: dict, tts_model: str, language: str) -> str:
        """Berechnet Hash für einen Step basierend auf Narration + Sprecher + TTS-Setup"""
        step_id = step.get('id', '')
        narration = step.get('narration', '')
        speaker = step.get('speaker', 'default')
        speaker_cfg = {}
        if self.tts:
            speaker_cfg = self.tts.get_speaker_config(speaker) or {}

        payload = {
            "id": step_id,
            "speaker": speaker,
            "narration": narration,
            "tts_model": tts_model,
            "language": language,
            "speaker_cfg": speaker_cfg,
        }
        return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:12]

    def check_sections(self) -> dict:
        """
        Prüft welche Sections Audio-Regenerierung brauchen.

        Gibt zurück: {section_name: {"changed": bool, "steps": [...], "hash": str}}
        """
        sections = self._get_sections()
        stored_hashes = self._load_section_hashes()

        result = {}
        for section_name, steps in sections.items():
            current_hash = self._compute_section_hash(steps)
            stored_hash = stored_hashes.get(section_name)

            result[section_name] = {
                "changed": current_hash != stored_hash,
                "steps": steps,
                "hash": current_hash,
                "old_hash": stored_hash
            }

        return result

    def generate_audio_smart(self, force_sections: list = None):
        """
        Generiert Audio nur für geänderte Sections.

        Args:
            force_sections: Liste von Section-Namen die erzwungen werden sollen
        """
        self.load_script()

        config = self.script.get('config', {})
        speakers_config = config.get('speakers', {})
        tts_model = self.tts_model_override or config.get('tts_model', 'custom-small')
        self.tts = TTS(model_size=tts_model, speakers=speakers_config, use_voice_cloning=self.use_voice_cloning)

        section_status = self.check_sections()
        stored_hashes = self._load_section_hashes()

        print("\n" + "="*60)
        print("📚 SECTION-BASIERTE AUDIO-GENERIERUNG")
        print("="*60)

        # Zeige Section-Status
        for section_name, info in section_status.items():
            steps_with_narration = [s for s in info['steps'] if s.get('narration')]
            status = "🔄 GEÄNDERT" if info['changed'] else "✓ unverändert"
            force_marker = " [FORCE]" if force_sections and section_name in force_sections else ""
            print(f"   {section_name}: {len(steps_with_narration)} Audio-Dateien - {status}{force_marker}")

        print("="*60 + "\n")

        # Modell laden falls nötig
        needs_generation = any(
            info['changed'] or (force_sections and section_name in force_sections)
            for section_name, info in section_status.items()
            if any(s.get('narration') for s in info['steps'])
        )

        if needs_generation:
            self.tts.preload()

        total_generated = 0
        total_cached = 0

        for section_name, info in section_status.items():
            steps_with_narration = [s for s in info['steps'] if s.get('narration')]
            if not steps_with_narration:
                continue

            should_regenerate = info['changed'] or (force_sections and section_name in force_sections)

            if should_regenerate:
                print(f"\n🎤 {section_name} ({len(steps_with_narration)} Dateien)")
                print("-" * 40)

                for step in steps_with_narration:
                    step_id = step['id']
                    narration = step['narration']
                    speaker = step.get('speaker', 'default')
                    audio_file = f"{AUDIO_DIR}/{step_id}.wav"

                    speaker_name = self.tts.get_speaker_config(speaker).get('name', speaker)
                    print(f"   🎤 {step_id} [{speaker_name}]")

                    engine = self.tts._get_engine()
                    engine.generate(narration, audio_file, speaker=speaker)
                    total_generated += 1

                # Hash speichern nach erfolgreicher Generierung
                stored_hashes[section_name] = info['hash']
            else:
                total_cached += len(steps_with_narration)

        # Hashes speichern (Sections + Audio)
        self._save_section_hashes(stored_hashes)

        # Audio-Hashes aktualisieren
        language = config.get('language', 'en')
        new_audio_hashes = {}
        for section_name, info in section_status.items():
            for step in info['steps']:
                if step.get('narration'):
                    new_audio_hashes[step['id']] = self._compute_step_hash(step, tts_model, language)
        self._save_audio_hashes(new_audio_hashes)

        print("\n" + "="*60)
        print(f"✓ Fertig: {total_generated} neu generiert, {total_cached} aus Cache")
        print("="*60 + "\n")

    def list_steps(self):
        """Kurze Liste aller Schritte"""
        self.load_script()

        print("\n" + "="*60)
        print("SCHRITTE")
        print("="*60)

        for i, step in enumerate(self.script['steps']):
            step_id = step['id']
            has_audio = os.path.exists(f"{AUDIO_DIR}/{step_id}.wav")
            audio_icon = "🔊" if has_audio else "  "
            narration = step.get('narration', '')[:40]
            print(f"  {i+1:2}. {audio_icon} {step_id:<20} {narration}...")

        print("="*60)
        print(f"  Total: {len(self.script['steps'])} Schritte\n")

    def preview(self):
        """Zeigt detaillierte Skript-Vorschau"""
        self.load_script()

        print("\n" + "="*60)
        print("SKRIPT-VORSCHAU (detailliert)")
        print("="*60)

        for i, step in enumerate(self.script['steps']):
            step_id = step['id']
            narration = step.get('narration', '')
            actions = step.get('actions', [])
            has_audio = os.path.exists(f"{AUDIO_DIR}/{step_id}.wav")

            print(f"\n{'─'*60}")
            print(f"[{i+1}] {step_id}  {'🔊' if has_audio else '🔇'}")
            print(f"{'─'*60}")

            if narration:
                # Wrap text
                words = narration.split()
                line = "📢 "
                for word in words:
                    if len(line) + len(word) > 58:
                        print(line)
                        line = "   " + word + " "
                    else:
                        line += word + " "
                if line.strip():
                    print(line)

            if actions:
                print(f"\n🎬 Aktionen ({len(actions)}):")
                for action in actions:
                    do = action.get('do', '?')
                    target = action.get('target', action.get('url', action.get('title', '')))
                    print(f"   • {do}: {target}")

        print("\n" + "="*60)

    def play_audio(self, step_id: str):
        """Spielt Audio für einen oder alle Schritte ab"""
        self.load_script()

        if step_id == 'all':
            steps = [s for s in self.script['steps'] if s.get('narration')]
        else:
            steps = [s for s in self.script['steps'] if s['id'] == step_id]

        if not steps:
            print(f"⚠️ Schritt nicht gefunden: {step_id}")
            return

        tts = TTS()

        for step in steps:
            sid = step['id']
            audio_file = f"{AUDIO_DIR}/{sid}.wav"

            if os.path.exists(audio_file):
                print(f"▶️  {sid}: {step.get('narration', '')[:50]}...")
                tts._play(audio_file)
            else:
                print(f"⚠️ {sid}: Keine Audio-Datei vorhanden")

    def generate_audio(self, force: bool = False, only_steps: list = None):
        """Generiert Audio-Dateien mit Qwen3-TTS Voice Cloning"""
        self.load_script()

        config = self.script.get('config', {})
        speakers_config = config.get('speakers', {})

        # TTS-Modell: Override > Config > Default
        tts_model = self.tts_model_override or config.get('tts_model', 'custom-small')
        print(f"🎤 TTS-Modell: {tts_model} ({'--model Flag' if self.tts_model_override else 'SCRIPT.json'})")
        print(f"🎤 Voice Cloning: {'AN (langsam!)' if self.use_voice_cloning else 'AUS (schnell)'}")

        self.tts = TTS(model_size=tts_model, speakers=speakers_config, use_voice_cloning=self.use_voice_cloning)

        # Bei --force: Lösche GESAMTEN Cache (inkl. QwenTTS Hash-Cache)
        if force:
            cache_dir = os.path.join(AUDIO_DIR, 'cache')
            if os.path.exists(cache_dir):
                import shutil
                shutil.rmtree(cache_dir)
                print(f"🗑️ Cache-Verzeichnis gelöscht: {cache_dir}")
            # Auch alle .wav Dateien im audio/ Ordner löschen
            for f in Path(AUDIO_DIR).glob("*.wav"):
                f.unlink()
            print(f"🗑️ Alle Audio-Dateien gelöscht")

        # Modell laden
        self.tts.preload()

        # Steps filtern
        if only_steps:
            steps = [s for s in self.script['steps']
                     if s.get('narration') and s['id'] in only_steps]
        else:
            steps = [s for s in self.script['steps'] if s.get('narration')]

        total = len(steps)

        if force:
            print(f"\n🎤 Generiere {total} Audio-Dateien NEU mit Qwen3-TTS...")
        else:
            print(f"\n🎤 Generiere {total} Audio-Dateien mit Qwen3-TTS...")
        print("="*60)

        generated = 0
        cached = 0

        for i, step in enumerate(steps):
            step_id = step['id']
            narration = step['narration']
            speaker = step.get('speaker', 'default')
            audio_file = f"{AUDIO_DIR}/{step_id}.wav"

            # Sprecher-Name für Ausgabe
            speaker_name = self.tts.get_speaker_config(speaker).get('name', speaker)

            if os.path.exists(audio_file) and not force:
                print(f"   [{i+1}/{total}] ♻️  {step_id} [{speaker_name}] (cached)")
                cached += 1
            else:
                print(f"   [{i+1}/{total}] 🎤 {step_id} [{speaker_name}]")
                engine = self.tts._get_engine()
                engine.generate(narration, audio_file, speaker=speaker)
                generated += 1

        # Audio-Hashes aktualisieren
        language = config.get('language', 'en')
        new_audio_hashes = {}
        for step in steps:
            new_audio_hashes[step['id']] = self._compute_step_hash(step, tts_model, language)
        self._save_audio_hashes(new_audio_hashes)

        print("="*60)
        print(f"✓ Fertig: {generated} generiert, {cached} aus Cache\n")

    def resolve_step(self, step_ref: str) -> int:
        """Wandelt Step-ID oder Nummer in Index um"""
        self.load_script()

        # Versuche als Nummer
        try:
            num = int(step_ref)
            if 1 <= num <= len(self.script['steps']):
                return num - 1
        except ValueError:
            pass

        # Versuche als Step-ID
        for i, step in enumerate(self.script['steps']):
            if step['id'] == step_ref:
                return i

        print(f"⚠️ Schritt nicht gefunden: {step_ref}")
        return 0

    def pregenerate_audio(self):
        """Generiert alle Audio-Dateien vorab"""
        self.load_script()

        config = self.script.get('config', {})
        speakers_config = config.get('speakers', {})
        tts_model = self.tts_model_override or config.get('tts_model', 'custom-small')
        self.tts = TTS(model_size=tts_model, speakers=speakers_config, use_voice_cloning=self.use_voice_cloning)

        # Modell laden
        self.tts.preload()

        # Alle Narrations generieren
        steps_with_narration = [s for s in self.script['steps'] if s.get('narration')]
        total = len(steps_with_narration)

        print(f"\n🎤 Generiere {total} Audio-Dateien vorab...")
        print("="*60)

        for i, step in enumerate(steps_with_narration):
            step_id = step['id']
            narration = step['narration']
            speaker = step.get('speaker', 'default')
            audio_file = f"{AUDIO_DIR}/{step_id}.wav"

            if os.path.exists(audio_file):
                print(f"   [{i+1}/{total}] ♻️ Cache: {step_id}")
            else:
                print(f"   [{i+1}/{total}] 🎤 Generiere: {step_id}")
                engine = self.tts._get_engine()
                engine.generate(narration, audio_file, speaker=speaker)

        print("="*60)
        print(f"✓ Alle {total} Audio-Dateien bereit!\n")

        # Audio-Hashes aktualisieren
        language = config.get('language', 'en')
        new_audio_hashes = {}
        for step in steps_with_narration:
            new_audio_hashes[step['id']] = self._compute_step_hash(step, tts_model, language)
        self._save_audio_hashes(new_audio_hashes)

    def run(self, start_step: int = 0, record: bool = True, pregenerate: bool = True,
            silent: bool = False, test_mode: bool = False):
        """Führt Skript aus"""
        self.load_script()

        config = self.script.get('config', {})
        url = config.get('url', 'http://localhost:55080')
        output_file = config.get('output_file', 'demo.mp4')
        speakers_config = config.get('speakers', {})
        tts_model = self.tts_model_override or config.get('tts_model', 'custom-small')
        language = config.get('language', 'en')

        # Login-Daten aus Config
        login_config = config.get('login', {})
        username = login_config.get('username', 'admin')
        password = login_config.get('password', 'admin123')

        # Im Test-Modus: Keine Aufnahme, kein Audio
        if test_mode:
            record = False
            silent = True
            pregenerate = False

        # Komponenten initialisieren
        self.browser = Browser(url)
        self.tts = TTS(model_size=tts_model, speakers=speakers_config, use_voice_cloning=self.use_voice_cloning)

        if record:
            self.recorder = Recorder(output_file)

        try:
            # === PHASE 1: AUDIO PRÜFEN / GENERIEREN ===
            if pregenerate and not test_mode:
                steps_with_narration = [s for s in self.script['steps'] if s.get('narration')]
                total = len(steps_with_narration)

                # Audio-Hashes prüfen (Narration/Sprecher/Model/Config)
                stored_hashes = self._load_audio_hashes()
                new_hashes = {}
                missing_audio = []
                missing_ids = set()

                for step in steps_with_narration:
                    step_id = step['id']
                    audio_file = f"{AUDIO_DIR}/{step_id}.wav"
                    step_hash = self._compute_step_hash(step, tts_model, language)
                    new_hashes[step_id] = step_hash

                    if (not os.path.exists(audio_file)) or stored_hashes.get(step_id) != step_hash:
                        missing_audio.append(step)
                        missing_ids.add(step_id)

                if missing_audio:
                    print(f"\n🎤 {len(missing_audio)} Audio-Dateien sind veraltet/fehlend – regeneriere...")
                    self.tts.preload()

                    for i, step in enumerate(steps_with_narration):
                        step_id = step['id']
                        narration = step['narration']
                        speaker = step.get('speaker', 'default')
                        audio_file = f"{AUDIO_DIR}/{step_id}.wav"

                        if step_id not in missing_ids:
                            print(f"   [{i+1}/{total}] ♻️ {step_id} (cached)")
                        else:
                            speaker_name = self.tts.get_speaker_config(speaker).get('name', speaker)
                            print(f"   [{i+1}/{total}] 🎤 {step_id} [{speaker_name}]")
                            engine = self.tts._get_engine()
                            engine.generate(narration, audio_file, speaker=speaker)
                else:
                    print(f"\n✓ Alle {total} Audio-Dateien aktuell (TTS nicht benötigt)")

                # Hashes persistieren
                self._save_audio_hashes(new_hashes)
                print(f"✓ Alle Audio-Dateien bereit!\n")

            # === STATUS ANZEIGE ===
            if test_mode:
                print("\n🧪 ELEMENT-TEST MODUS")
                print("="*60)
                print("   Prüfe ob alle UI-Elemente gefunden werden")
                print("   Keine Aufnahme, kein Audio")
                print("="*60)
            else:
                print("\n🚀 STARTE DEMO VIDEO")
                print("="*60)
                if pregenerate:
                    print("   Audio-Dateien: Generiert ✓")
                print(f"   Audio-Wiedergabe: {'Aus (silent)' if silent else 'An (live)'}")
                print(f"   Aufnahme: {'An' if record else 'Aus'}")
                print("   Drücke Ctrl+C zum Abbrechen")
                print("="*60)

            time.sleep(1 if test_mode else 2)

            # === PHASE 2: DESKTOP VORBEREITEN + BROWSER ÖFFNEN ===
            # Stage Manager deaktivieren und andere Fenster ausblenden VOR Chrome-Start
            self.browser._disable_stage_manager()
            self.browser._hide_other_windows()

            self.browser.open()
            # skip_login=True: Login happens live during recording (intro steps)
            self.browser.setup(username=username, password=password, language=language, skip_login=True)

            # === PHASE 3: AUFNAHME STARTEN ===
            if self.recorder and not test_mode:
                # Hole Fenster-Bounds für Crop
                window_bounds = self.browser.get_window_bounds()
                if window_bounds:
                    self.recorder.window_bounds = window_bounds
                    print(f"\n🎬 Recording-Bereich: {window_bounds[2]}x{window_bounds[3]}")

                print("🎬 Starte Aufnahme in 3 Sekunden...")
                time.sleep(3)
                self.recorder.start()
                time.sleep(1)

            # Schritte ausführen
            steps = self.script['steps'][start_step:]
            errors = []  # Für Test-Modus: Sammle Fehler

            for i, step in enumerate(steps):
                step_num = start_step + i + 1
                step_id = step.get('id', f'step_{step_num}')
                narration = step.get('narration', '')
                actions = step.get('actions', [])

                if test_mode:
                    print(f"\n{'─'*50}")
                    print(f"[{step_num}/{len(self.script['steps'])}] 🧪 {step_id}")
                else:
                    print(f"\n[{step_num}/{len(self.script['steps'])}] {step_id}")

                # Audio-Timestamp markieren (für Post-Processing)
                audio_file = f"{AUDIO_DIR}/{step_id}.wav"
                audio_duration = 0
                audio_thread = None

                if narration and os.path.exists(audio_file) and not test_mode:
                    # Timestamp für Post-Processing merken
                    if self.recorder:
                        self.recorder.mark_audio(audio_file)

                    # Audio-Dauer ermitteln
                    audio_duration = self._get_audio_duration(audio_file)

                    # Audio abspielen (wenn nicht silent)
                    if not silent:
                        audio_thread = threading.Thread(
                            target=lambda f=audio_file: self.tts._play(f)
                        )
                        audio_thread.start()

                # === AKTION AUSFÜHRUNG ===
                start_time = time.time()

                if test_mode:
                    # Test-Modus: Schnell durchklicken, kein Timing
                    for action in actions:
                        result = self._execute_action(action, test_mode=True)
                        if result is False:
                            errors.append((step_id, action))
                else:
                    # Produktiv-Modus: Sequentielle Ausführung mit Sync-Punkten
                    timeline = Timeline(narration, audio_duration, start_time) if narration and audio_duration > 0 else None

                    if timeline:
                        print(f"   ⏱️ Audio: {audio_duration:.1f}s | {len(actions)} Aktionen")

                    for action_idx, action in enumerate(actions):
                        do = action.get('do')

                        # SYNC: Warte auf Narrations-Zeitpunkt
                        if do == 'sync':
                            if timeline:
                                target_time = timeline.get_sync_time(action)
                                waited = timeline.wait_until(target_time)
                                if waited > 0:
                                    print(f"   ⏸️ sync: wartete {waited:.1f}s")
                                else:
                                    print(f"   ⏸️ sync: bereits bei {target_time:.1f}s")
                            continue

                        # HIGHLIGHT_BEFORE: Vor Klicks automatisch highlighten
                        highlight_before = action.get('highlight_before', 0)
                        if highlight_before > 0 and do == 'click':
                            target = action.get('target', '')
                            self.browser.highlight(target, highlight_before, keep=True)
                            print(f"   ✨ highlight: {target} ({highlight_before}s)")

                        # SMOOTH TRANSITION: highlight → click on same target
                        if do == 'highlight':
                            # Look ahead: if next non-sync action is click on same target, keep highlight
                            keep = False
                            hl_target = action.get('target', '')
                            for next_action in actions[action_idx + 1:]:
                                next_do = next_action.get('do')
                                if next_do == 'sync':
                                    continue
                                if next_do == 'click' and next_action.get('target', '') == hl_target:
                                    keep = True
                                break
                            if keep:
                                self.browser.highlight(hl_target, action.get('duration', 2), keep=True)
                                print(f"   ✨ highlight (→click): {hl_target}")
                                continue

                        # Aktion ausführen
                        self._execute_action(action, test_mode=False)

                # Auf Audio warten
                if audio_thread:
                    audio_thread.join()
                elif audio_duration > 0 and not test_mode:
                    # Silent mode: Warten bis Audio "fertig" wäre
                    elapsed = time.time() - start_time
                    remaining = audio_duration - elapsed
                    if remaining > 0:
                        time.sleep(remaining)

                time.sleep(0.1 if test_mode else 0.2)

            # Ergebnis
            if test_mode:
                print(f"\n{'='*60}")
                if errors:
                    print(f"❌ TEST FEHLGESCHLAGEN: {len(errors)} Probleme")
                    print("="*60)
                    for step_id, action in errors:
                        print(f"   • {step_id}: {action.get('do')} → {action.get('target', action.get('url', ''))}")
                else:
                    print("✅ ALLE ELEMENTE GEFUNDEN!")
                print("="*60)
            else:
                print("\n✅ AUFNAHME FERTIG!")

        except KeyboardInterrupt:
            print("\n⚠️ Abgebrochen")

        finally:
            # Aufnahme stoppen
            if self.recorder:
                self.recorder.stop()
                # Audio ins Video einfügen
                self.recorder.merge_audio()
            if self.browser:
                # Stage Manager wiederherstellen bevor Browser geschlossen wird
                self.browser._restore_stage_manager()
                self.browser.close()

    def _get_audio_duration(self, audio_path: str) -> float:
        """Gibt Audio-Dauer in Sekunden zurück"""
        if not os.path.exists(audio_path):
            return 0.0
        result = subprocess.run([
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True)
        try:
            return float(result.stdout.strip())
        except ValueError:
            return 3.0  # Default 3 Sekunden

    def _execute_action(self, action: dict, test_mode: bool = False):
        """Führt eine einzelne Aktion aus. Gibt False zurück wenn Element nicht gefunden.

        Im Test-Modus werden Aktionen trotzdem ausgeführt (für Navigation),
        aber schneller und ohne Audio-Sync.
        """
        do = action.get('do')
        target = action.get('target', '')

        if do == 'open_browser':
            print(f"   ✓ open_browser (skip)")
            return True

        elif do == 'sync':
            # Sync wird im Loop behandelt, hier nur für Test-Modus
            if test_mode:
                after = action.get('after', '')
                at = action.get('at', '')
                if after:
                    print(f"   ⏸️ sync: after '{after}' (skip in test)")
                elif at:
                    print(f"   ⏸️ sync: at {at} (skip in test)")
            return True

        elif do == 'login':
            login_config = self.script.get('config', {}).get('login', {})
            username = action.get('username', login_config.get('username', 'admin'))
            password = action.get('password', login_config.get('password', 'admin123'))
            self.browser.do_visible_login(username, password)
            print(f"   ✓ login: {username}")
            return True

        elif do == 'goto':
            url = action.get('url', '/')
            self.browser.goto(url)
            print(f"   ✓ goto: {url}")
            return True

        elif do == 'click':
            element = self.browser._find_element(target)
            if element:
                self.browser.click(target)
                print(f"   ✓ click: {target}")
                return True
            else:
                print(f"   ✗ click: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'click_if_present':
            element = self.browser._find_element(target)
            if element:
                self.browser.click(target)
                print(f"   ✓ click_if_present: {target}")
                return True
            print(f"   ↷ click_if_present: {target} (nicht vorhanden)")
            return True

        elif do == 'click_random':
            elements = self.browser._find_elements(target)
            if not elements:
                print(f"   ✗ click_random: {target} (NICHT GEFUNDEN)")
                return False

            if action.get('exclude_selected'):
                filtered = []
                for el in elements:
                    try:
                        cls = (el.get_attribute('class') or '').lower()
                        if 'selected' in cls:
                            continue
                    except Exception:
                        continue
                    filtered.append(el)
                if filtered:
                    elements = filtered

            element = random.choice(elements)
            try:
                self.browser.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
                    element
                )
                time.sleep(0.2)
                self.browser.driver.execute_script(
                    "arguments[0].classList.add('llars-highlight')",
                    element
                )
                time.sleep(0.2)
                try:
                    element.click()
                except Exception:
                    self.browser.driver.execute_script("arguments[0].click()", element)
                time.sleep(0.2)
                self.browser.driver.execute_script(
                    "arguments[0].classList.remove('llars-highlight')",
                    element
                )
            except Exception:
                try:
                    self.browser.driver.execute_script("arguments[0].click()", element)
                except Exception:
                    pass

            print(f"   ✓ click_random: {target}")
            return True

        elif do == 'click_index':
            elements = self.browser._find_elements(target)
            if not elements:
                print(f"   ✗ click_index: {target} (NICHT GEFUNDEN)")
                return False

            index = action.get('index', 0)
            try:
                index = int(index)
            except Exception:
                index = 0

            if index < 0 or index >= len(elements):
                print(f"   ✗ click_index: {target} (Index {index} außerhalb von {len(elements)})")
                return False

            element = elements[index]
            try:
                self.browser.driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
                    element
                )
                time.sleep(0.2)
                self.browser.driver.execute_script(
                    "arguments[0].classList.add('llars-highlight')",
                    element
                )
                time.sleep(0.2)
                try:
                    element.click()
                except Exception:
                    self.browser.driver.execute_script("arguments[0].click()", element)
                time.sleep(0.2)
                self.browser.driver.execute_script(
                    "arguments[0].classList.remove('llars-highlight')",
                    element
                )
            except Exception:
                try:
                    self.browser.driver.execute_script("arguments[0].click()", element)
                except Exception:
                    pass

            print(f"   ✓ click_index: {target} [{index}]")
            return True

        elif do == 'type':
            element = self.browser._find_element(target)
            if element:
                # Im Test-Modus schneller tippen
                speed = 'fast' if test_mode else action.get('speed', 'fast')
                text = _resolve_env_placeholders(action.get('text', ''))
                self.browser.type(target, text, speed)
                print(f"   ✓ type: {target}")
                return True
            else:
                print(f"   ✗ type: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'clear':
            element = self.browser._find_element(target)
            if element:
                # Robust clear for Vuetify inputs: clear(), select-all+backspace, JS value reset + input event
                try:
                    element.clear()
                except Exception:
                    pass
                try:
                    element.send_keys(Keys.COMMAND + 'a')
                except Exception:
                    try:
                        element.send_keys(Keys.CONTROL + 'a')
                    except Exception:
                        pass
                try:
                    element.send_keys(Keys.BACKSPACE)
                except Exception:
                    pass
                try:
                    self.browser.driver.execute_script(
                        "arguments[0].value = ''; arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
                        element
                    )
                except Exception:
                    pass
                print(f"   ✓ clear: {target}")
                return True
            else:
                print(f"   ✗ clear: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'highlight':
            element = self.browser._find_element(target)
            if element:
                # Im Test-Modus kürzer highlighten
                duration = 0.5 if test_mode else action.get('duration', 2)
                self.browser.highlight(target, duration)
                print(f"   ✓ highlight: {target}")
                return True
            else:
                print(f"   ✗ highlight: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'drag':
            from_el = self.browser._find_element(action.get('from'))
            to_el = self.browser._find_element(action.get('to'))
            if from_el and to_el:
                self.browser.drag(action.get('from'), action.get('to'))
                print(f"   ✓ drag: {action.get('from')} → {action.get('to')}")
                return True
            else:
                missing = []
                if not from_el:
                    missing.append(action.get('from'))
                if not to_el:
                    missing.append(action.get('to'))
                print(f"   ✗ drag: {', '.join(missing)} (NICHT GEFUNDEN)")
                return False

        elif do == 'upload':
            self.browser.upload(
                action.get('file'),
                wait_for_processing=action.get('wait_for_processing', True)
            )
            print(f"   ✓ upload: {action.get('file')}")
            return True
        elif do == 'set_text_from_file':
            result = self.browser.set_text_from_file(
                target,
                action.get('file')
            )
            return result

        elif do == 'paste':
            element = self.browser._find_element(target)
            if element:
                text = _resolve_env_placeholders(action.get('text', ''))
                # Click to focus
                try:
                    element.click()
                except Exception:
                    self.browser.driver.execute_script("arguments[0].click()", element)
                time.sleep(0.1)
                # Set value via JS using native setter (works with Vue/Vuetify reactivity)
                try:
                    self.browser.driver.execute_script("""
                        var el = arguments[0];
                        var val = arguments[1];
                        // Use native setter to properly trigger Vue/Vuetify reactivity
                        var nativeSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        )?.set || Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, 'value'
                        )?.set;
                        if (nativeSetter) {
                            nativeSetter.call(el, val);
                        } else {
                            el.value = val;
                        }
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    """, element, text)
                except Exception:
                    element.send_keys(text)
                masked = text[:4] + '...' if len(text) > 4 else text
                print(f"   ✓ paste: {target} ({masked})")
                return True
            else:
                print(f"   ✗ paste: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'wait':
            seconds = action.get('seconds', 1)
            # Im Test-Modus kürzere Wartezeiten, aber mindestens 1s für async content
            if test_mode:
                seconds = max(min(seconds, 1.5), 0.5)
            time.sleep(seconds)
            print(f"   ✓ wait: {seconds}s")
            return True

        elif do == 'wait_for':
            self.browser.wait_for(target, action.get('timeout', 10))
            print(f"   ✓ wait_for: {target}")
            return True

        elif do == 'wait_for_modal':
            self.browser.wait_for_modal()
            print(f"   ✓ wait_for_modal")
            return True

        elif do == 'dismiss_dialog':
            self.browser.dismiss_dialog()
            print(f"   ✓ dismiss_dialog")
            return True

        elif do == 'show_title':
            title = action.get('title', '')
            subtitle = action.get('subtitle', '')
            text = action.get('text', '')
            columns = action.get('columns', None)
            duration = action.get('duration', 0)
            self.browser.show_title(title, subtitle, text, columns=columns)
            if test_mode:
                time.sleep(0.3)  # Kurz anzeigen im Test
                if duration > 0:
                    time.sleep(0.5)
                    self.browser.hide_title()
                    time.sleep(0.3)
            else:
                time.sleep(0.5)  # Wait for fade-in
                if duration > 0:
                    time.sleep(duration)
                    self.browser.hide_title()
                    time.sleep(0.6)  # Wait for fade-out
            print(f"   ✓ show_title: {title}")
            return True

        elif do == 'hide_title':
            self.browser.hide_title()
            time.sleep(0.3 if test_mode else 0.6)  # Wait for fade-out
            print(f"   ✓ hide_title")
            return True

        elif do == 'show_pipeline':
            title = action.get('title', '')
            subtitle = action.get('subtitle', '')
            columns = action.get('columns', None)
            self.browser.show_pipeline(title=title, subtitle=subtitle, columns=columns)
            if test_mode:
                time.sleep(0.3)
            else:
                time.sleep(0.5)  # Wait for fade-in
            print(f"   ✓ show_pipeline")
            return True

        elif do == 'show_problem':
            self.browser.show_problem()
            if test_mode:
                time.sleep(0.3)
            else:
                time.sleep(0.5)  # Wait for fade-in
            print(f"   ✓ show_problem")
            return True

        elif do == 'merge_problem':
            self.browser.merge_problem()
            if test_mode:
                time.sleep(0.3)
            else:
                time.sleep(1.5)  # Wait for merge animation
            print(f"   ✓ merge_problem")
            return True

        elif do == 'show_data_preview':
            self.browser.show_data_preview()
            if test_mode:
                time.sleep(0.3)
            else:
                time.sleep(0.5)  # Wait for fade-in
            print(f"   ✓ show_data_preview")
            return True

        elif do == 'scroll_to':
            element = self.browser._find_element(target)
            if element:
                self.browser.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                print(f"   ✓ scroll_to: {target}")
                time.sleep(0.5)
                return True
            else:
                print(f"   ✗ scroll_to: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'scroll':
            element = self.browser._find_element(target)
            if element:
                amount = action.get('amount', 200)
                try:
                    amount = int(amount)
                except Exception:
                    amount = 200
                self.browser.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];",
                    element,
                    amount
                )
                print(f"   ✓ scroll: {target} ({amount}px)")
                time.sleep(0.3)
                return True
            else:
                print(f"   ✗ scroll: {target} (NICHT GEFUNDEN)")
                return False

        elif do == 'js_exec':
            # Execute JavaScript and print result
            js_code = action.get('code', '')
            try:
                result = self.browser.driver.execute_script(js_code)
                print(f"   🔍 js_exec: {result}")
            except Exception as e:
                print(f"   ⚠️ js_exec error: {e}")
            return True

        elif do == 'dismiss_overlays':
            # Remove stale Vuetify overlays from the DOM entirely
            try:
                result = self.browser.driver.execute_script("""
                    var removed = 0;
                    document.querySelectorAll('.v-overlay--active').forEach(function(overlay) {
                        var hasContent = overlay.querySelector('.v-card, .v-dialog__content, .l-floating-window');
                        if (!hasContent) {
                            overlay.remove();
                            removed++;
                        }
                    });
                    return removed;
                """)
                print(f"   🧹 Cleaned {result} stale overlay(s)")
                time.sleep(0.3)
            except Exception as e:
                print(f"   ⚠️ dismiss_overlays error: {e}")
            return True

        elif do == 'js_click':
            # Click element via JavaScript, bypassing overlay interception
            js_selector = action.get('selector', '')
            try:
                result = self.browser.driver.execute_script(f"""
                    var el = document.querySelector('{js_selector}');
                    if (el) {{ el.click(); return true; }}
                    return false;
                """)
                if result:
                    print(f"   ✓ js_click: {js_selector}")
                else:
                    print(f"   ✗ js_click: {js_selector} (NICHT GEFUNDEN)")
                return result
            except Exception as e:
                print(f"   ⚠️ js_click error: {e}")
                return False

        elif do == 'close_file_dialog':
            self.browser.close_file_dialog()
            return True

        # =====================================================================
        # COLLAB-AKTIONEN - Zweiter Browser für Echtzeit-Kollaboration
        # =====================================================================

        elif do == 'collab_open':
            username = action.get('user', 'researcher')
            password = action.get('password', 'admin123')
            self.browser.collab_open(username, password)
            print(f"   ✓ collab_open: {username}")
            return True

        elif do == 'collab_goto':
            path = action.get('url', action.get('path', '/'))
            self.browser.collab_goto(path)
            print(f"   ✓ collab_goto: {path}")
            return True

        elif do == 'collab_click':
            self.browser.collab_click(target)
            print(f"   ✓ collab_click: {target}")
            return True

        elif do == 'collab_type':
            text = action.get('text', '')
            delay = action.get('delay', 0.08)
            cursor = action.get('cursor', 'end')
            if test_mode:
                delay = 0.02  # Schneller tippen im Test
            self.browser.collab_type(target, text, delay, cursor=cursor)
            print(f"   ✓ collab_type: {target}")
            return True

        elif do == 'collab_focus':
            self.browser.collab_focus_editor()
            print(f"   ✓ collab_focus")
            return True

        elif do == 'collab_close':
            self.browser.collab_close()
            print(f"   ✓ collab_close")
            return True

        else:
            print(f"   ? Unbekannte Aktion: {do}")
            return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Lars Demo Video Runner - Produktionssystem',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                         PRODUKTIONS-WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SKRIPT PRÜFEN
   python run.py --list                    # Alle Schritte anzeigen
   python run.py --preview                 # Detaillierte Vorschau

2. AUDIO GENERIEREN
   python run.py --smart                   # Nur geänderte Sections neu generieren (EMPFOHLEN)
   python run.py --smart --sections INTRO  # Nur bestimmte Sections
   python run.py --audio                   # Alle Audio-Dateien generieren
   python run.py --audio --force           # Audio NEU generieren (Cache ignorieren)
   python run.py --audio --only intro_1    # Nur bestimmte Steps

3. AUDIO TESTEN
   python run.py --play intro_1            # Audio für Step abspielen
   python run.py --play all                # Alle Audios abspielen

4. ELEMENT-TEST (ohne Aufnahme)
   python run.py --test                    # Nur prüfen ob Elemente gefunden werden
   python run.py --test --from prompt_eng_1  # Ab bestimmtem Step testen

5. VIDEO AUFNEHMEN
   python run.py                           # Vollständige Aufnahme mit Audio
   python run.py --silent                  # Aufnahme OHNE Audio-Wiedergabe
   python run.py --from prompt_eng_1       # Ab bestimmtem Step aufnehmen

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                         TYPISCHE WORKFLOWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Narration geändert:     python run.py --smart && python run.py  # EMPFOHLEN
Section geändert:       python run.py --smart --sections INTRO  # Nur bestimmte Section
Actions geändert:       python run.py --test && python run.py
Alles neu:              python run.py --audio --force && python run.py
Quick Test:             python run.py --test --from prompt_eng_1
        """
    )

    # === INFO & PREVIEW ===
    parser.add_argument('--list', '-l', action='store_true',
                        help='Liste aller Schritte mit IDs')
    parser.add_argument('--preview', '-p', action='store_true',
                        help='Detaillierte Skript-Vorschau')

    # === AUDIO ===
    parser.add_argument('--audio', '-a', action='store_true',
                        help='Nur Audio generieren (kein Browser/Video)')
    parser.add_argument('--smart', action='store_true',
                        help='Intelligente Audio-Generierung: Nur geänderte Sections neu generieren')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Audio-Cache ignorieren, alles neu generieren')
    parser.add_argument('--only', nargs='+', metavar='STEP_ID',
                        help='Nur bestimmte Steps (mit --audio)')
    parser.add_argument('--sections', nargs='+', metavar='SECTION',
                        help='Nur bestimmte Sections neu generieren (mit --smart)')
    parser.add_argument('--play', nargs='?', const='all', metavar='STEP_ID',
                        help='Audio abspielen (einzeln oder "all")')

    # === TEST ===
    parser.add_argument('--test', '-t', action='store_true',
                        help='Element-Test ohne Aufnahme/Audio')

    # === AUFNAHME ===
    parser.add_argument('--silent', '-s', action='store_true',
                        help='Aufnahme ohne Audio-Wiedergabe')
    parser.add_argument('--from', dest='from_step', metavar='STEP_ID',
                        help='Ab diesem Schritt starten (ID oder Nummer)')
    parser.add_argument('--no-record', action='store_true',
                        help='Browser-Automation ohne Video-Aufnahme')

    # === SONSTIGES ===
    parser.add_argument('--script', default=SCRIPT_FILE,
                        help='Alternatives Skript verwenden')
    parser.add_argument('--model', '-m', choices=['small', 'large', 'design', 'custom', 'custom-small'],
                        help='TTS-Modell: custom/custom-small (vordefinierte Stimmen, EMPFOHLEN), design (Voice Design), small/large (Voice Cloning)')
    parser.add_argument('--voice-clone', action='store_true',
                        help='Voice Cloning aktivieren (SEHR langsam auf CPU! Nur für finale Produktion)')

    args = parser.parse_args()
    runner = ScriptRunner(args.script)

    # TTS-Modell überschreiben wenn Flag gesetzt
    if args.model:
        runner.tts_model_override = args.model
    if args.voice_clone:
        runner.use_voice_cloning = True

    # === MODUS-AUSWAHL ===

    if args.list:
        # Kurze Liste aller Steps
        runner.list_steps()

    elif args.preview:
        # Detaillierte Vorschau
        runner.preview()

    elif args.play:
        # Audio abspielen
        runner.play_audio(args.play)

    elif args.smart:
        # Intelligente Audio-Generierung (nur geänderte Sections)
        runner.generate_audio_smart(force_sections=args.sections)

    elif args.audio:
        # Audio generieren
        runner.generate_audio(force=args.force, only_steps=args.only)

    elif args.test:
        # Element-Test
        start_step = runner.resolve_step(args.from_step) if args.from_step else 0
        runner.run(start_step=start_step, record=False, pregenerate=False, silent=True, test_mode=True)

    else:
        # Vollständige Aufnahme
        start_step = runner.resolve_step(args.from_step) if args.from_step else 0
        runner.run(
            start_step=start_step,
            record=not args.no_record,
            pregenerate=True,
            silent=args.silent
        )


if __name__ == '__main__':
    main()
