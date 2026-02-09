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

SCRIPT_FILE = "SCRIPT.json"
AUDIO_DIR = "audio"
OUTPUT_DIR = "output"

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

# Element-Mapping: Lesbare Namen → CSS Selektoren
# Lars nutzt eine Home-Seite mit Feature-Karten, keine Sidebar
ELEMENT_MAP = {
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
    "Settings": ".v-btn:contains('Settings'), .v-icon.mdi-cog, button:contains('Settings')",
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

    # Inputs (Vuetify Text Fields) - In Dialogs
    "Name Input": ".v-dialog .v-text-field input, .v-dialog input[type='text']",
    "Prompt Name Input": ".v-dialog .v-text-field input",
    "Block Name Input": ".v-dialog .v-text-field input",
    "Provider Name Input": ".v-dialog input[placeholder*='OpenAI'], .v-dialog input[aria-label='Name'], .v-dialog .v-text-field input[type='text']",
    "Provider API Key Input": ".v-dialog input[type='password'], .v-dialog input[aria-label='API Key']",
    "Provider Base URL Input": ".v-dialog input[placeholder*='Base URL'], .v-dialog input[aria-label*='Base URL']",
    "Provider Model Input": ".v-dialog .v-combobox input, .v-dialog .v-autocomplete input",
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
    "Response Output": ".response-content, .response-text",
    "Close": ".v-dialog .l-btn:contains('Close'), .v-dialog .v-btn:contains('Close'), .wizard-header .v-btn, .l-btn:contains('Close'), .v-btn:contains('Close'), button:contains('Close')",
    "Cancel": ".v-btn:contains('Cancel'), button:contains('Cancel')",
    "Dialog Create Button": ".v-dialog .l-btn:contains('Create'), .v-dialog .v-btn:contains('Create'), .v-dialog button:contains('Create')",
    "Block Create Button": ".v-dialog--active .l-btn:contains('Create'), .v-overlay--active .l-btn:contains('Create')",
    "Prompt Card": ".prompt-card, .v-card:contains('News Summary')",
    "Collaboration Color": ".color-presets, .color-preview",
    "Collab Color Preset": ".color-presets .color-preset",

    # Generation Wizard (Batch Generation)
    "Generation Wizard": ".generation-wizard, .v-dialog:contains('New Generation Job')",
    "First Model": ".generation-wizard .models-selection .selection-item:first-child, .models-selection .selection-item:first-child",
    "Second Model": ".generation-wizard .models-selection .selection-item:nth-child(2), .models-selection .selection-item:nth-child(2)",
    "Job Name Input": ".generation-wizard .v-text-field input",

    # Scenario Wizard
    "Scenario Wizard": ".l-btn:contains('Scenario Wizard'), button.l-btn:contains('Scenario Wizard'), .header-actions .l-btn:contains('Scenario Wizard'), .v-btn:contains('Scenario Wizard')",
    "Ranking": ".type-card:contains('Ranking'), .type-name:contains('Ranking'), .v-list-item:contains('Ranking'), .v-radio:contains('Ranking'), label:contains('Ranking')",
    "LLM List": ".llm-category .llm-item, .llm-list .llm-item",
    "First LLM Evaluator": ".llm-category .llm-item, .llm-list .llm-item, .llm-item",
    "Second LLM Evaluator": ".llm-category .llm-item:nth-child(2), .llm-list .llm-item:nth-child(2), .llm-item:nth-child(2)",
    "OpenAI Provider": ".llm-item--user:contains('OpenAI'), .llm-category .llm-item:contains('OpenAI')",
    "User List": ".user-list, .team-section .user-item",
    "Admin User": ".user-item:contains('admin'), .user-item:contains('Admin'), .user-name:contains('admin'), .user-name:contains('Admin')",
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
    "Prompt Item": ".v-overlay--active .selection-item, .prompts-selection .selection-item, .selection-item",
    "First Prompt": ".v-overlay--active .selection-item:first-child, .v-overlay--active .selectable-card:first-child, .prompts-selection .selection-item:first-child",
    "News Summary Prompt Item": ".v-overlay--active .selection-item:contains('News'), .prompts-selection .selection-item:contains('News'), .selection-item:contains('News Summary'), .item-name:contains('News')",
    "Analyst Summary Prompt Item": ".v-overlay--active .selection-item:contains('Analyst Summary'), .prompts-selection .selection-item:contains('Analyst Summary'), .selection-item:contains('Analyst Summary'), .item-name:contains('Analyst')",
    "News Summary Eval Item": ".v-overlay--active .selection-item:contains('News Summary Eval'), .prompts-selection .selection-item:contains('News Summary Eval'), .selection-item:contains('News Summary Eval'), .item-name:contains('News Summary Eval')",

    # Step 3: Models (click to select) - in wizard overlay
    "Model Item": ".v-overlay--active .selection-item, .models-selection .selection-item",
    "First Model": ".v-overlay--active .selection-item:first-child, .v-overlay--active .selectable-card:first-child, .models-selection .selection-item:first-child",
    "Second Model": ".v-overlay--active .selection-item:nth-child(2), .v-overlay--active .selectable-card:nth-child(2), .models-selection .selection-item:nth-child(2)",
    "Mistral Model": ".models-selection .selection-item:contains('mistral'), .models-selection .selection-item:contains('Mistral'), .item-name:contains('mistral')",
    "Magistral Model": ".models-selection .selection-item:contains('Magistral'), .models-selection .selection-item:contains('magistral'), .item-name:contains('Magistral')",
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
    "Matrix Total": ".matrix-item.total",

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
    "News Summary Prompt": ".v-list-item:contains('News'), .prompt-item:contains('News')",

    # Evaluation Types
    "Ranking": ".type-card:contains('Ranking'), .type-name:contains('Ranking'), .v-list-item:contains('Ranking'), .v-radio:contains('Ranking'), label:contains('Ranking')",
    "Bucket Config": ".v-btn:contains('Bucket'), button:contains('Bucket')",
    "3 Buckets": ".v-list-item:contains('3'), .v-radio:contains('3')",
    "Enable LLM Evaluation": ".v-checkbox:contains('LLM'), .v-switch:contains('LLM'), input[type='checkbox']",
    "GPT-4 as Judge": ".v-list-item:contains('GPT-4'), .v-checkbox:contains('GPT')",
    "Start LLM Evaluation": ".v-btn:contains('Start'), button:contains('Start')",

    # Dashboard Elements
    "Agreement Matrix": ".agreement-matrix, .v-card:contains('Agreement')",
    "Krippendorff Alpha": ".metric:contains('Alpha'), .v-card:contains('Krippendorff')",
    "Disagreement Tab": ".v-tab:contains('Disagreement'), button:contains('Disagreement')",
    "Disagreement Chart": ".chart, .v-card:contains('Disagreement')",
    "Correlation Chart": ".chart, .v-card:contains('Correlation')",

    # Drag & Drop Items
    "Summary 1": ".eval-item:nth-child(1), .v-card:nth-child(1)",
    "Summary 2": ".eval-item:nth-child(2), .v-card:nth-child(2)",
    "Summary 3": ".eval-item:nth-child(3), .v-card:nth-child(3)",
    "Best Bucket": ".ranking-interface .good-bucket, .bucket.good-bucket",
    "Acceptable Bucket": ".ranking-interface .moderate-bucket, .bucket.moderate-bucket",
    "Poor Bucket": ".ranking-interface .bad-bucket, .bucket.bad-bucket",

    # Misc
    "Test Output": ".test-result, .v-card:contains('Result'), .output",
    "Progress Bar": ".v-progress-linear, .progress-bar, .v-progress-circular",
    "Cost Estimate": ".cost-display, .v-card:contains('Cost')",
    "Import Dialog": ".v-dialog, .v-card.import",
    "Recommended: Ranking": ".recommendation, .v-chip:contains('Ranking')",
    "News Summary Evaluation": ".v-card:contains('News'), .scenario-card:contains('News')",

    # =============================================
    # ADDITIONAL ELEMENTS FOR DEMO VIDEO
    # =============================================

    # Prompt Engineering - Variable Management
    "Variables Button": ".v-btn:contains('Variables'), .actions-grid .v-btn:contains('Variables')",
    "Variable Dialog": ".v-dialog:contains('Variable'), .variables-dialog",
    "Add Variable": ".v-btn:contains('Add'), .v-dialog .v-btn:contains('Add')",
    "Variable Name Input": ".variable-manager-card .name-input input, .variable-input input, .v-text-field input",
    "Variable Content Input": ".variable-manager-card .content-input textarea, .variable-manager-card textarea",
    "Create Variable": ".variable-manager-card .l-btn:contains('Create Variable'), .variable-manager-card .v-btn:contains('Create Variable')",
    "Variable Dialog Close": ".variable-manager-card .dialog-header .v-btn",
    "Variable Save": ".v-btn:contains('Save'), .v-btn:contains('Done')",

    # Test Prompt Dialog - Enhanced
    "Run Test Button": ".v-btn:contains('Run'), .test-dialog .v-btn:contains('Generate'), .v-btn:contains('Generate')",
    "Test Response": ".response-content, .test-response, .response-text, .v-card-text",
    "Test Loading": ".v-progress-circular, .loading",

    # Batch Generation - Job List
    "Completed Job": ".job-card:contains('completed'), .job-card.status-completed, .job-item:contains('100%')",
    "Demo Job": ".job-card:contains('Demo'), .job-card:contains('News')",
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
    "News Summary Demo Scenario": ".scenario-card:contains('News Summary Demo Job'), .scenario-card:contains('News Summary')",
    "Completed Scenario": ".scenario-card:contains('Complete'), .scenario-card.completed",
    "Demo Scenario": ".scenario-card:contains('Demo'), .scenario-card:contains('News')",
    "Scenario Stats": ".scenario-stats, .stats-card",
    "Open Scenario": ".v-btn:contains('Open'), .scenario-card .v-btn",
    "Scenario Workspace": ".scenario-workspace",
    "Scenario Workspace Back": ".scenario-workspace .back-btn, .scenario-workspace .v-btn.back-btn",
    "Scenario Manager Title": ".scenario-manager .title, .page-header .title:contains('Scenario Manager'), h1.title:contains('Scenario Manager')",
    "Scenario Tabs": ".scenario-workspace .tab-navigation, .tab-navigation",
    "Scenario Tab Overview": ".tab-navigation .v-btn:contains('Overview'), .tab-navigation button:contains('Overview')",
    "Scenario Tab Data": ".tab-navigation .v-btn:contains('Data'), .tab-navigation button:contains('Data')",
    "Scenario Tab Evaluation": ".tab-navigation .v-btn:contains('Evaluation'), .tab-navigation button:contains('Evaluation')",
    "Scenario Tab Team": ".tab-navigation .v-btn:contains('Team'), .tab-navigation button:contains('Team')",
    "Scenario Live Badge": ".stats-bar .live-dot, .overview-tab .live-badge .live-dot, .overview-tab .live-dot",
    "Scenario LLM Progress": ".overview-tab .progress-fill.llm, .stats-bar .progress-mini, .progress-mini .progress-fill",
    "Evaluation Summary": ".evaluation-tab .summary-grid, .evaluation-tab .summary-card",
    "Evaluation Progress": ".evaluation-tab .progress-bar-track, .evaluation-tab .progress-bar-fill, .evaluation-tab .total-progress-section",
    "Evaluation Export": ".evaluation-tab .l-btn:contains('Export'), .evaluation-tab .v-btn:contains('Export')",
    "Export JSON": ".v-list-item:contains('JSON')",
    # Scenario Data Tab
    "Data Stats": ".data-tab .data-stats, .data-stats",
    "Data Threads Table": ".data-tab .threads-table, .threads-table, .threads-section",
    "Data Status Legend": ".data-tab .status-legend, .status-legend",
    # Scenario Team Tab
    "Team Members List": ".team-tab .members-list, .members-list",
    "Team Invite Button": ".team-tab .l-btn:contains('Invite'), .team-tab .l-btn:contains('Add'), .team-tab .v-btn:contains('Invite')",
    "Team Add LLM Button": ".team-tab .l-btn:contains('Add LLM'), .team-tab .l-btn:contains('LLM'), .team-tab .v-btn:contains('LLM')",
    "Team Member Menu": ".team-tab .member-actions .v-btn, .team-tab .member-actions button",
    "Scenario Wizard Close": ".scenario-wizard .wizard-header .v-btn",
    # Human Evaluation (Evaluation Hub + Ranking UI)
    "Evaluation Scenario Card": ".scenarios-grid .scenario-card:contains('News Summary'), .scenario-card:contains('News Summary'), .scenarios-grid .scenario-card:first-child, .scenario-card:first-child",
    "Evaluation Items Grid": ".items-grid, .items-content",
    "Evaluation Item Card": ".items-grid .item-card:first-child, .item-card:first-child",
    "Ranking Interface": ".ranking-interface",
    "Ranking Buckets": ".ranking-interface .buckets-row, .ranking-interface .bucket, .ranking-interface .neutral-bucket",
    "Ranking Content": ".ranking-interface .right-panel, .ranking-interface .content-text, .ranking-interface .message-list",
    "Ranking Item": ".ranking-interface .neutral-bucket .bucket-item:first-child, .ranking-interface .bucket-item:first-child",

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
    "News Summary Prompt": ".prompt-card:contains('News Summary'), .v-card:contains('News Summary Prompt'), .prompt-list-item:contains('News Summary')",
    "Analyst Summary Prompt": ".prompt-card:contains('Analyst Summary'), .v-card:contains('Analyst Summary')",

    # Prompt Engineering - Collaboration
    "Collab Indicator": ".collab-indicator, .user-presence, .collaboration-status, .yjs-status, .online-users",

    # Batch Generation - Existing Jobs (seeded by seed_demo_video_data)
    "News Summary Demo Job": ".job-card:contains('News Summary Demo'), .job-row:contains('News Summary Demo'), .v-list-item:contains('News Summary Demo')",
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
    # Documentation
    "Docs Hero": ".docs-hero, .docs-page .hero-title",
    "Docs Technical Section": ".docs-section.highlight",
    "Docs MkDocs Link": ".mkdocs-link, .mkdocs-link-container",
    "MkDocs Header": "header.md-header, .md-header",
    "MkDocs Sidebar": ".md-sidebar, .md-nav, .md-nav__list",
}


# =============================================================================
# TTS
# =============================================================================

class TTS:
    """TTS-Wrapper mit Sprecher-Unterstützung"""

    # Default Sprecher-Konfigurationen für Qwen3-TTS Voice Cloning
    DEFAULT_SPEAKERS = {
        "moderator": {"name": "Alex", "ref_audio": "voices/alex_reference.wav"},
        "guest": {"name": "David", "ref_audio": "voices/david_reference.wav"},
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

    def start(self):
        """Startet Aufnahme (ohne Audio)

        Wenn window_bounds gesetzt ist, wird nur dieser Bereich aufgenommen.
        Ansonsten wird der gesamte Bildschirm aufgenommen und auf Zielgröße skaliert.
        """
        import platform

        # Raw video (ohne Audio)
        self.raw_video = os.path.join(OUTPUT_DIR, "raw_" + self.output_file)
        self.final_output = os.path.join(OUTPUT_DIR, self.output_file)

        if platform.system() == 'Darwin':
            # macOS: avfoundation unterstützt kein direktes Fenster-Capture
            # Lösung: Gesamten Bildschirm aufnehmen und dann croppen

            if self.window_bounds:
                x, y, w, h = self.window_bounds
                # Crop-Filter: crop=width:height:x:y, dann scale auf Zielgröße
                video_filter = f"crop={w}:{h}:{x}:{y},scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"
                print(f"   📐 Crop: {w}x{h} at ({x},{y})")
            else:
                video_filter = f"scale={self.TARGET_WIDTH}:{self.TARGET_HEIGHT}"

            cmd = [
                'ffmpeg', '-y',
                '-f', 'avfoundation',
                '-framerate', '30',
                '-capture_cursor', '1',
                '-i', '1:none',  # Screen capture (device 1)
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

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.start_time = time.time()
        print(f"🎬 Aufnahme gestartet: {self.raw_video}")

    def mark_audio(self, audio_file: str):
        """Markiert Zeitpunkt für Audio-Einfügung"""
        if self.start_time:
            relative_time = time.time() - self.start_time
            self.timestamps.append((relative_time, audio_file))

    def stop(self):
        """Stoppt Aufnahme"""
        if self.process:
            try:
                self.process.stdin.write(b'q')
                self.process.stdin.flush()
                self.process.wait(timeout=10)
            except (BrokenPipeError, OSError):
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except Exception:
                    pass
            print("⏹️ Aufnahme gestoppt")

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
    """

    def __init__(self, url: str = "http://localhost:55080"):
        self.base_url = url
        self.driver = None
        self.window_bounds = None  # (x, y, width, height)
        self.collab_driver = None  # Zweiter Browser für Collab-Demo

    def open(self, username: str = "admin", password: str = "admin123", language: str = "en"):
        """Öffnet Chrome mit exakter Fenstergröße und Position"""
        options = Options()
        # Starte mit kleinem Fenster, setzen die exakte Größe danach
        options.add_argument('--window-size=1280,800')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # Kiosk-Modus entfernt UI-Elemente für saubere Aufnahme
        # options.add_argument('--kiosk')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Fenster an Position (0,0) setzen und exakte Größe einstellen
        self.driver.set_window_position(0, 0)

        # Berechne Fenster-Dekoration (Titelleiste etc.)
        # Chrome hat typisch ~74px Toolbar oben (Tab-Bar + Adressleiste)
        # Wir wollen dass der VIEWPORT 1920x1080 ist
        self.driver.set_window_size(self.TARGET_WIDTH, self.TARGET_HEIGHT + 100)

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

    def setup(self, username: str = "admin", password: str = "admin123", language: str = "en"):
        """
        SETUP PHASE - Vor der Aufnahme:
        1. Prüft ob auf /login oder /Home
        2. Stellt Sprache auf Englisch
        3. Führt Login durch falls nötig
        4. Navigiert zu /Home
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
            # Sprache prüfen und ggf. ändern (für eingeloggte User)
            # self._ensure_language(language)

        elif page == "authentik":
            # Authentik 2-Step Login
            self._do_authentik_login(username, password)
            time.sleep(3)

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
        """Löscht alte Demo-Daten via Docker/MariaDB"""
        print("   🧹 Räume alte Demo-Daten auf...")

        # SQL zum Löschen von Demo-Daten (nur Scenarios, NICHT die geseedeten Prompts/Jobs!)
        # Der "News Summary Demo Job" und die Prompts werden vom Seeder erstellt und sollen bleiben
        cleanup_sql = """
        -- Scenarios löschen (mit Foreign Keys) - Diese werden während der Aufnahme erstellt
        DELETE FROM scenario_item_distribution WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM scenario_items WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM scenario_users WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM item_dimension_ratings WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM item_labeling_evaluations WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM comparison_evaluations WHERE message_id IN (
            SELECT id FROM comparison_messages WHERE session_id IN (
                SELECT id FROM comparison_sessions WHERE scenario_id IN (
                    SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
                )
            )
        );
        DELETE FROM comparison_messages WHERE session_id IN (
            SELECT id FROM comparison_sessions WHERE scenario_id IN (
                SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
            )
        );
        DELETE FROM comparison_sessions WHERE scenario_id IN (
            SELECT id FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%'
        );
        DELETE FROM rating_scenarios WHERE scenario_name LIKE '%News Summary%' OR scenario_name LIKE '%Demo%Evaluation%';
        -- Alte Generation Jobs aus der Video-Entwicklung entfernen (Seeded Demo Job bleibt)
        DELETE FROM generated_outputs WHERE job_id IN (
            SELECT id FROM generation_jobs WHERE created_by = 'admin' AND name <> 'News Summary Demo Job'
        );
        DELETE FROM generation_jobs WHERE created_by = 'admin' AND name <> 'News Summary Demo Job';
        -- Prompt aus der Live-Demo entfernen (wird im Skript neu erstellt)
        DELETE FROM prompt_commits WHERE prompt_id IN (
            SELECT prompt_id FROM user_prompts
            WHERE LOWER(TRIM(name)) LIKE 'analyst summary prompt%'
               OR LOWER(TRIM(name)) LIKE 'live collab prompt%'
        );
        DELETE FROM user_prompt_shares WHERE prompt_id IN (
            SELECT prompt_id FROM user_prompts
            WHERE LOWER(TRIM(name)) LIKE 'analyst summary prompt%'
               OR LOWER(TRIM(name)) LIKE 'live collab prompt%'
        );
        DELETE FROM user_prompts
        WHERE LOWER(TRIM(name)) LIKE 'analyst summary prompt%'
           OR LOWER(TRIM(name)) LIKE 'live collab prompt%';
        -- HINWEIS: Seeder-Daten (Prompts + Demo-Job) bleiben erhalten.
        -- Nur der im Skript neu erstellte Job "Live Collab Batch Job" und der Prompt
        -- "Analyst Summary Prompt" werden entfernt.
        """

        try:
            # Via Docker exec MariaDB aufrufen
            result = subprocess.run([
                'docker', 'exec', 'llars_db_service',
                'mariadb', '-u', 'dev_user', '-pdev_password_change_me', 'database_llars',
                '-e', cleanup_sql
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                print(f"   ✓ Demo-Daten gelöscht")
            else:
                # Fallback: Ignoriere Fehler (z.B. wenn Tabellen nicht existieren)
                print(f"   ✓ Cleanup abgeschlossen")
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ Cleanup Timeout (ignoriert)")
        except FileNotFoundError:
            print(f"   ⚠️ Docker nicht verfügbar (ignoriert)")
        except Exception as e:
            print(f"   ⚠️ Cleanup-Fehler (ignoriert): {str(e)[:50]}")

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
                            return el
                else:
                    el = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if el:
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
        """Klickt auf Element"""
        element = self._find_element(target)
        if element:
            # Scroll to element
            self.driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'})",
                element
            )
            time.sleep(0.3)

            # Highlight
            self.driver.execute_script(
                "arguments[0].classList.add('llars-highlight')",
                element
            )
            time.sleep(0.2)

            # Click
            try:
                element.click()
            except StaleElementReferenceException:
                # Re-find and retry once if DOM changed
                element = self._find_element(target)
                if element:
                    try:
                        element.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click()", element)
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

    def type(self, target: str, text: str, speed: str = "fast"):
        """Tippt Text in Element (inkl. contenteditable für Quill Editor)"""
        element = self._find_element(target)
        if element:
            # Click to focus
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click()", element)
            time.sleep(0.1)

            # Check if it's a contenteditable element (Quill editor)
            is_contenteditable = element.get_attribute('contenteditable') == 'true'

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
            delay = {"slow": 0.08, "medium": 0.04, "fast": 0.02}.get(speed, 0.02)

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

    def highlight(self, target: str, duration: float = 2):
        """Hebt Element hervor"""
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
                self.driver.execute_script(
                    "arguments[0].classList.remove('llars-highlight')",
                    element
                )
            except Exception as e:
                # Stale element or page changed - just continue
                print(f"   ⚠️ Highlight fehlgeschlagen: {str(e)[:50]}")

    def drag(self, source: str, target: str):
        """Drag & Drop"""
        src = self._find_element(source)
        tgt = self._find_element(target)
        if src and tgt:
            ActionChains(self.driver).drag_and_drop(src, tgt).perform()
            print(f"   ↔️ Drag: {source} → {target}")
            time.sleep(0.3)

    def upload(self, file_path: str, wait_for_processing: bool = True):
        """Lädt Datei hoch und wartet optional auf Verarbeitung"""
        abs_path = str(Path(file_path).resolve())

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
        abs_path = Path(file_path).resolve()
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
        selectors = ELEMENT_MAP.get(target, target).split(', ')[0]
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selectors))
            )
        except Exception:
            print(f"⚠️ Timeout: {target}")

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

    def collab_open(self, username: str = "researcher", password: str = "admin123"):
        """
        Öffnet einen zweiten Browser für die Kollaborations-Demo.
        Der zweite Browser wird kleiner und außerhalb des sichtbaren Bereichs positioniert,
        sodass nur der Hauptbrowser aufgenommen wird, aber der Collab-Cursor im Editor sichtbar ist.
        """
        print(f"   👥 Öffne Collab-Browser als '{username}'...")

        options = Options()
        options.add_argument('--window-size=800,600')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        service = Service(ChromeDriverManager().install())
        self.collab_driver = webdriver.Chrome(service=service, options=options)

        # Fenster außerhalb des sichtbaren Bereichs positionieren (rechts vom Hauptfenster)
        self.collab_driver.set_window_position(2000, 100)
        self.collab_driver.set_window_size(800, 600)

        # Zur Login-Seite navigieren
        self.collab_driver.get(self.base_url)
        time.sleep(2)

        # Sprache für Collab-User auf Englisch setzen
        self._set_language_for_driver(self.collab_driver, "en")

        # Login mit Dev Quick Login Button
        try:
            dev_btn_selector = f"[data-testid='dev-login-btn-{username}']"
            dev_btn = self.collab_driver.find_element(By.CSS_SELECTOR, dev_btn_selector)
            if dev_btn and dev_btn.is_displayed():
                self.collab_driver.execute_script("arguments[0].click()", dev_btn)
                print(f"   ✓ Collab-User '{username}' eingeloggt")
                time.sleep(2)
            else:
                print(f"   ⚠️ Dev-Login-Button für '{username}' nicht gefunden")
        except Exception as e:
            print(f"   ⚠️ Collab-Login fehlgeschlagen: {e}")

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
                            return el
                else:
                    el = driver.find_element(By.CSS_SELECTOR, selector)
                    if el:
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

    def collab_type(self, target: str, text: str, delay: float = 0.08):
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
            self.collab_driver.execute_script("arguments[0].click()", element)
            time.sleep(0.3)

            # Tippe jeden Buchstaben einzeln für sichtbaren Effekt
            print(f"   👥 Collab tippt in '{target}': {text[:30]}...")
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
        """Schließt den Collab-Browser"""
        if self.collab_driver:
            print("   👥 Collab-Browser geschlossen")
            self.collab_driver.quit()
            self.collab_driver = None

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
        with open(self.script_path) as f:
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

            # === PHASE 2: BROWSER ÖFFNEN + SETUP ===
            self.browser.open()
            self.browser.setup(username=username, password=password, language=language)

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

                    for action in actions:
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
                            self.browser.highlight(target, highlight_before)
                            print(f"   ✨ highlight: {target} ({highlight_before}s)")

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

                time.sleep(0.1 if test_mode else 0.5)

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
            username = action.get('username', 'admin')
            password = action.get('password', 'admin123')
            if self.browser._needs_login():
                self.browser._do_login(username, password)
            print(f"   ✓ login")
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

        elif do == 'show_title':
            title = action.get('title', '')
            subtitle = action.get('subtitle', '')
            print(f"   ✓ show_title: {title} - {subtitle}")
            if not test_mode:
                time.sleep(2)
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

        elif do == 'close_file_dialog':
            self.browser.close_file_dialog()
            return True

        # =====================================================================
        # COLLAB-AKTIONEN - Zweiter Browser für Echtzeit-Kollaboration
        # =====================================================================

        elif do == 'collab_open':
            username = action.get('user', 'researcher')
            password = action.get('password', 'admin123')
            if test_mode:
                print(f"   ✓ collab_open: {username} (skip in test)")
            else:
                self.browser.collab_open(username, password)
            return True

        elif do == 'collab_goto':
            path = action.get('url', action.get('path', '/'))
            if test_mode:
                print(f"   ✓ collab_goto: {path} (skip in test)")
            else:
                self.browser.collab_goto(path)
            return True

        elif do == 'collab_click':
            if test_mode:
                print(f"   ✓ collab_click: {target} (skip in test)")
            else:
                self.browser.collab_click(target)
            return True

        elif do == 'collab_type':
            text = action.get('text', '')
            delay = action.get('delay', 0.08)
            if test_mode:
                print(f"   ✓ collab_type: {target} (skip in test)")
            else:
                self.browser.collab_type(target, text, delay)
            return True

        elif do == 'collab_focus':
            if test_mode:
                print(f"   ✓ collab_focus (skip in test)")
            else:
                self.browser.collab_focus_editor()
            return True

        elif do == 'collab_close':
            if test_mode:
                print(f"   ✓ collab_close (skip in test)")
            else:
                self.browser.collab_close()
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
