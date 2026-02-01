#!/usr/bin/env python3
"""
LLARS Demo Video - Runner
=========================

Führt SCRIPT.json automatisch aus:
- Öffnet Chrome
- Navigiert zu LLARS
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

# Element-Mapping: Lesbare Namen → CSS Selektoren
# LLARS nutzt eine Home-Seite mit Feature-Karten, keine Sidebar
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

    # Prompt Engineering - Sidebar Actions (in .sidebar .actions-grid)
    # Note: Uses lowercase "block" as per en.json translation "New block"
    "New Block": ".actions-grid .l-btn, .sidebar .l-btn:first-child, .v-btn:contains('block'), .v-btn:contains('Block')",
    "Preview": ".v-btn:contains('Preview')",
    "Test": ".v-btn:contains('Test'), .sidebar .v-btn:contains('Test')",
    "Manage Variables": ".v-btn:contains('Variables')",

    # Inputs (Vuetify Text Fields) - In Dialogs
    "Name Input": ".v-dialog .v-text-field input, .v-dialog input[type='text']",
    "Prompt Name Input": ".v-dialog .v-text-field input",
    "Block Name Input": ".v-dialog .v-text-field input",
    "Job Name": ".v-text-field input, input[placeholder*='Name']",
    "Scenario Name": ".v-text-field input, input[placeholder*='Name']",
    "Budget Limit": "input[type='number'], .v-text-field input",

    # Prompt Editor Blocks (LLARS uses generic blocks + Quill editor)
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
    "Test Prompt Dialog": ".test-prompt-card, .v-dialog:contains('Test')",
    "Model Select": ".config-select, .llm-model-select, .v-select",
    "Regenerate": ".v-btn:contains('Regenerate'), .dialog-actions .v-btn:contains('Regenerate')",
    "Response Output": ".response-content, .response-text",
    "Close": ".v-dialog .v-btn:contains('Close'), .wizard-header .v-btn, .v-btn:contains('Close'), button:contains('Close')",
    "Cancel": ".v-btn:contains('Cancel'), button:contains('Cancel')",
    "Dialog Create Button": ".v-dialog .l-btn:contains('Create'), .v-dialog .v-btn:contains('Create'), .v-dialog button:contains('Create')",
    "Block Create Button": ".v-dialog--active .l-btn:contains('Create'), .v-overlay--active .l-btn:contains('Create')",
    "Prompt Card": ".prompt-card, .v-card:contains('News Summary')",

    # =============================================
    # BATCH GENERATION - Wizard Steps
    # =============================================

    # Hub Buttons
    "New Job": ".header-actions .v-btn:contains('New Job'), .v-btn:contains('New Job')",
    "Create First Job": ".empty-state .v-btn:contains('Create')",

    # Wizard Navigation (inside dialog)
    "Next": ".generation-wizard .v-btn:contains('Next'), .v-dialog .v-btn:contains('Next')",
    "Back": ".generation-wizard .v-btn:contains('Back'), .v-dialog .v-btn:contains('Back')",
    "Create Job": ".generation-wizard .v-btn:contains('Create'), .v-dialog .v-btn:contains('Create Job')",

    # Step 1: Source Selection (inside wizard)
    "Source Scenario": ".generation-wizard .source-card:contains('Scenario'), .source-card:contains('Scenario')",
    "Source Upload": ".generation-wizard .source-card:contains('Upload'), .source-card:contains('Upload')",
    "Source Prompt Only": ".generation-wizard .source-card:contains('Prompt'), .source-card:contains('Prompt')",
    "Upload Zone": ".upload-zone",
    "File Input": ".upload-zone input[type='file'], input[type='file']",

    # Step 2: Prompt Templates (click to select, inside wizard/dialog)
    "Prompt Item": ".v-dialog .selection-item, .generation-wizard .selection-item",
    "First Prompt": ".v-dialog .prompts-selection .selection-item:first-child, .prompts-selection .selection-item:first-child",
    "News Summary Prompt Item": ".v-dialog .selection-item:contains('News Summary'), .selection-item:contains('News Summary')",

    # Step 3: Models (click to select, inside wizard/dialog)
    "Model Item": ".v-dialog .selection-item, .generation-wizard .selection-item",
    "First Model": ".v-dialog .models-selection .selection-item:first-child, .models-selection .selection-item:first-child",
    "Mistral Model": ".v-dialog .selection-item:contains('mistral'), .selection-item:contains('Mistral')",
    "GPT-4 Model": ".v-dialog .selection-item:contains('gpt-4'), .selection-item:contains('GPT')",
    "Claude Model": ".v-dialog .selection-item:contains('claude'), .selection-item:contains('Claude')",

    # Step 4: Configuration (inside wizard/dialog)
    "Job Name Field": ".v-dialog .config-form .v-text-field input, .config-form .v-text-field input",
    "Temperature Slider": ".v-dialog .config-form .v-slider, .config-form .v-slider",
    "Max Tokens Field": ".v-dialog .config-form input[type='number']",
    "Budget Field": ".v-dialog .config-form .v-text-field input",

    # Step 5: Review (inside wizard/dialog)
    "Matrix Preview": ".v-dialog .matrix-preview, .matrix-preview",
    "Cost Estimate": ".v-dialog .cost-estimate, .v-dialog .cost-value, .cost-estimate",
    "Review Summary": ".v-dialog .review-summary, .review-summary",

    # Job Detail View
    "Start Job": ".header-actions .v-btn:contains('Start'), .v-btn:contains('Start')",
    "Pause Job": ".v-btn:contains('Pause')",
    "Cancel Job": ".v-btn:contains('Cancel')",
    "Progress Bar": ".v-progress-linear, .progress-fill, .card-progress-bar",
    "Outputs List": ".outputs-list",
    "Output Item": ".output-item",

    # Job Cards
    "Job Card": ".job-card",
    "Active Job Card": ".job-card.is-active",
    "News Summary Prompt": ".v-list-item:contains('News'), .prompt-item:contains('News')",

    # Evaluation Types
    "Ranking": ".v-list-item:contains('Ranking'), .v-radio:contains('Ranking'), label:contains('Ranking')",
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
    "Best Bucket": ".bucket-best, .bucket:contains('Best'), .v-card:contains('Best')",
    "Acceptable Bucket": ".bucket-acceptable, .bucket:contains('Accept')",
    "Poor Bucket": ".bucket-poor, .bucket:contains('Poor')",

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
    "Variable Name Input": ".variable-input input, .v-text-field input",
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
    "Completed Scenario": ".scenario-card:contains('Complete'), .scenario-card.completed",
    "Demo Scenario": ".scenario-card:contains('Demo'), .scenario-card:contains('News')",
    "Scenario Stats": ".scenario-stats, .stats-card",
    "Open Scenario": ".v-btn:contains('Open'), .scenario-card .v-btn",

    # Scenario Wizard (Button text is "Scenario Wizard")
    "Wizard Button": ".v-btn:contains('Scenario Wizard'), .v-btn:contains('Wizard')",
    "Scenario Wizard": ".v-btn:contains('Scenario Wizard')",
    "Wizard Dialog": ".wizard-dialog, .scenario-wizard, .v-dialog",
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
}


# =============================================================================
# TTS
# =============================================================================

class TTS:
    """TTS-Wrapper mit Sprecher-Unterstützung"""

    # Default Sprecher-Konfigurationen
    DEFAULT_SPEAKERS = {
        "host": {"name": "Alex", "macos_voice": "Daniel", "macos_rate": 175},
        "narrator": {"name": "David", "macos_voice": "Daniel", "macos_rate": 155},
        "default": {"name": "Default", "macos_voice": "Daniel", "macos_rate": 180},
    }

    def __init__(self, model_size: str = "small", speakers: dict = None):
        self.model_size = model_size
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
        if engine != "fallback":
            engine._load_model()

        self._loaded = True
        print("\n✓ TTS-Modell geladen und bereit!\n")

    def _get_engine(self):
        if self._engine is None:
            try:
                from src.tts import QwenTTS
                self._engine = QwenTTS(
                    model_size=self.model_size,
                    cache_dir=AUDIO_DIR,
                    speakers=self.speakers
                )
            except Exception as e:
                print(f"⚠️ TTS Fehler: {e}")
                self._engine = "fallback"
        return self._engine

    def speak(self, text: str, step_id: str, speaker: str = "default"):
        """Spricht Text (blockierend)"""
        audio_file = f"{AUDIO_DIR}/{step_id}.wav"

        if not os.path.exists(audio_file):
            engine = self._get_engine()
            if engine == "fallback":
                self._generate_fallback(text, audio_file, speaker)
            else:
                engine.generate(text, audio_file, speaker=speaker)

        # Abspielen
        self._play(audio_file)

    def _generate_fallback(self, text: str, output_path: str, speaker: str = "default"):
        """macOS say als Fallback mit Sprecher-Unterstützung"""
        import platform
        if platform.system() == 'Darwin':
            config = self.get_speaker_config(speaker)
            voice = config.get('macos_voice', 'Daniel')
            rate = config.get('macos_rate', 180)

            temp = output_path.replace('.wav', '.aiff')
            subprocess.run(['say', '-v', voice, '-r', str(rate), '-o', temp, text], capture_output=True)
            subprocess.run(['ffmpeg', '-y', '-i', temp, '-ar', '24000', output_path], capture_output=True)
            if os.path.exists(temp):
                os.remove(temp)

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

    def __init__(self, output_file: str):
        # Verhindere doppeltes output/
        if output_file.startswith('output/'):
            output_file = output_file[7:]
        self.output_file = output_file
        self.process = None
        self.start_time = None
        self.timestamps = []  # [(relative_time, audio_file), ...]
        Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    def start(self):
        """Startet Aufnahme (ohne Audio)"""
        import platform

        # Raw video (ohne Audio)
        self.raw_video = os.path.join(OUTPUT_DIR, "raw_" + self.output_file)
        self.final_output = os.path.join(OUTPUT_DIR, self.output_file)

        if platform.system() == 'Darwin':
            cmd = [
                'ffmpeg', '-y',
                '-f', 'avfoundation',
                '-framerate', '30',
                '-capture_cursor', '1',
                '-i', '1:none',
                '-vf', 'scale=1920:1080',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '18',  # Bessere Qualität
                '-pix_fmt', 'yuv420p',
                self.raw_video
            ]
        else:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'x11grab',
                '-framerate', '30',
                '-video_size', '1920x1080',
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

        # Alle Audio-Streams mixen
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(self.timestamps))])
        filter_parts.append(f"{mix_inputs}amix=inputs={len(self.timestamps)}:duration=longest[aout]")

        filter_complex = ';'.join(filter_parts)

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

    def open(self, username: str = "admin", password: str = "admin123", language: str = "en"):
        """Öffnet Chrome"""
        options = Options()
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        print(f"🌐 Chrome geöffnet")

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

            # 3. Warten und prüfen
            time.sleep(3)
            page = self._detect_page()

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

        # SQL zum Löschen von Demo-Daten (News Summary)
        cleanup_sql = """
        -- Prompts löschen
        DELETE FROM user_prompts WHERE name LIKE '%News Summary%';
        -- Scenarios löschen (mit Foreign Keys)
        DELETE FROM scenario_users WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%News Summary%');
        DELETE FROM scenario_threads WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%News Summary%');
        DELETE FROM item_dimension_ratings WHERE scenario_id IN (SELECT id FROM scenarios WHERE name LIKE '%News Summary%');
        DELETE FROM scenarios WHERE name LIKE '%News Summary%';
        -- Generation Jobs löschen
        DELETE FROM generation_outputs WHERE job_id IN (SELECT id FROM generation_jobs WHERE name LIKE '%News Summary%');
        DELETE FROM generation_jobs WHERE name LIKE '%News Summary%';
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

        try:
            # Finde Language Toggle Button (innerhalb des Wrappers)
            toggle = self.driver.find_element(By.CSS_SELECTOR,
                "[data-testid='language-toggle'] .language-toggle-btn, "
                ".language-toggle-wrapper .language-toggle-btn, "
                ".language-toggle-btn")

            # Klicke um Dropdown zu öffnen
            toggle.click()
            time.sleep(0.5)

            # Wähle die richtige Sprache
            lang_text = "English" if language == "en" else "Deutsch"

            # Suche in der Sprachauswahl-Liste
            lang_option = self.driver.find_element(By.XPATH,
                f"//button[contains(@class, 'language-option') and contains(., '{lang_text}')]")
            lang_option.click()
            time.sleep(0.5)

            print(f"   ✓ Sprache auf {lang_text} gesetzt")
        except Exception as e:
            print(f"   ⚠️ Sprache konnte nicht über UI gesetzt werden: {e}")
            # Fallback: Direkt localStorage setzen (zuverlässiger)
            try:
                self.driver.execute_script(f"localStorage.setItem('llars-language', '{language}')")
                self.driver.refresh()
                time.sleep(1)
                print(f"   ✓ Sprache via localStorage gesetzt")
            except Exception:
                pass

    def _do_login_on_login_page(self, username: str, password: str):
        """Login auf der LLARS /login Seite"""
        print(f"   🔐 Login als: {username}")

        try:
            # Username eingeben
            username_field = self.driver.find_element(By.CSS_SELECTOR,
                "[data-testid='username-input'] input, #username, input[name='username']")
            username_field.clear()
            username_field.send_keys(username)
            print("   ✓ Username eingegeben")

            time.sleep(0.3)

            # Password eingeben
            password_field = self.driver.find_element(By.CSS_SELECTOR,
                "[data-testid='password-input'] input, #password, input[name='password'], input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            print("   ✓ Passwort eingegeben")

            time.sleep(0.3)

            # Login Button klicken
            login_btn = self.driver.find_element(By.CSS_SELECTOR,
                "[data-testid='login-btn'], button[type='submit'], .login-button")
            login_btn.click()
            print("   ✓ Login-Button geklickt")

            time.sleep(2)

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

            # Geschwindigkeit
            delay = {"slow": 0.08, "medium": 0.04, "fast": 0.02}[speed]

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

    def drag(self, source: str, target: str):
        """Drag & Drop"""
        src = self._find_element(source)
        tgt = self._find_element(target)
        if src and tgt:
            ActionChains(self.driver).drag_and_drop(src, tgt).perform()
            print(f"   ↔️ Drag: {source} → {target}")
            time.sleep(0.3)

    def upload(self, file_path: str):
        """Lädt Datei hoch"""
        abs_path = str(Path(file_path).resolve())
        file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(abs_path)
        print(f"   📁 Upload: {file_path}")
        time.sleep(1)

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

    def close(self):
        """Schließt Browser"""
        if self.driver:
            self.driver.quit()


# =============================================================================
# SCRIPT RUNNER
# =============================================================================

class ScriptRunner:
    """Führt SCRIPT.json aus"""

    def __init__(self, script_path: str = SCRIPT_FILE):
        self.script_path = script_path
        self.script = None
        self.browser = None
        self.tts = None
        self.recorder = None
        self.force_consistent_voices = False  # Für 100% konsistente Stimmen (macOS)

    def load_script(self):
        """Lädt Skript"""
        with open(self.script_path) as f:
            self.script = json.load(f)
        print(f"✓ Skript geladen: {len(self.script['steps'])} Schritte")

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
        """Generiert Audio-Dateien mit Sprecher-Unterstützung"""
        self.load_script()

        config = self.script.get('config', {})
        speakers_config = config.get('speakers', {})

        # Konsistente Stimmen: macOS TTS statt Qwen3
        if self.force_consistent_voices:
            tts_model = 'fallback'
            print("🎯 Verwende macOS TTS für konsistente Stimmen")
            print("   Host (Alex): Fred (US)")
            print("   Narrator (David): Daniel (UK)")
        else:
            tts_model = config.get('tts_model', 'small')

        self.tts = TTS(model_size=tts_model, speakers=speakers_config)

        # Modell laden (bei fallback kein Laden nötig)
        if tts_model != 'fallback':
            self.tts.preload()

        # Steps filtern
        if only_steps:
            steps = [s for s in self.script['steps']
                     if s.get('narration') and s['id'] in only_steps]
        else:
            steps = [s for s in self.script['steps'] if s.get('narration')]

        total = len(steps)

        if force:
            print(f"\n🎤 Generiere {total} Audio-Dateien NEU (Cache wird ignoriert)...")
        else:
            print(f"\n🎤 Generiere {total} Audio-Dateien...")
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
                if force and os.path.exists(audio_file):
                    os.remove(audio_file)
                print(f"   [{i+1}/{total}] 🎤 {step_id} [{speaker_name}]")
                engine = self.tts._get_engine()
                if engine != "fallback":
                    engine.generate(narration, audio_file, speaker=speaker)
                else:
                    self.tts._generate_fallback(narration, audio_file, speaker)
                generated += 1

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

        tts_model = self.script.get('config', {}).get('tts_model', 'small')
        self.tts = TTS(model_size=tts_model)

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
            audio_file = f"{AUDIO_DIR}/{step_id}.wav"

            if os.path.exists(audio_file):
                print(f"   [{i+1}/{total}] ♻️ Cache: {step_id}")
            else:
                print(f"   [{i+1}/{total}] 🎤 Generiere: {step_id}")
                engine = self.tts._get_engine()
                if engine != "fallback":
                    engine.generate(narration, audio_file)
                else:
                    self.tts._speak_fallback(narration, audio_file)

        print("="*60)
        print(f"✓ Alle {total} Audio-Dateien bereit!\n")

    def run(self, start_step: int = 0, record: bool = True, pregenerate: bool = True,
            silent: bool = False, test_mode: bool = False):
        """Führt Skript aus"""
        self.load_script()

        config = self.script.get('config', {})
        url = config.get('url', 'http://localhost:55080')
        output_file = config.get('output_file', 'demo.mp4')
        tts_model = config.get('tts_model', 'small')
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
        self.tts = TTS(model_size=tts_model)

        if record:
            self.recorder = Recorder(output_file)

        try:
            # === PHASE 1: AUDIO PRÜFEN / GENERIEREN ===
            if pregenerate and not test_mode:
                steps_with_narration = [s for s in self.script['steps'] if s.get('narration')]
                total = len(steps_with_narration)

                # Prüfe welche Audio-Dateien fehlen
                missing_audio = []
                for step in steps_with_narration:
                    audio_file = f"{AUDIO_DIR}/{step['id']}.wav"
                    if not os.path.exists(audio_file):
                        missing_audio.append(step)

                if missing_audio:
                    # Nur TTS laden wenn Audio fehlt
                    print(f"\n🎤 {len(missing_audio)} Audio-Dateien müssen generiert werden...")
                    self.tts.preload()

                    for i, step in enumerate(steps_with_narration):
                        step_id = step['id']
                        narration = step['narration']
                        audio_file = f"{AUDIO_DIR}/{step_id}.wav"

                        if os.path.exists(audio_file):
                            print(f"   [{i+1}/{total}] ♻️ {step_id} (cached)")
                        else:
                            print(f"   [{i+1}/{total}] 🎤 {step_id}")
                            engine = self.tts._get_engine()
                            if engine != "fallback":
                                engine.generate(narration, audio_file)
                            else:
                                self.tts._speak_fallback(narration, audio_file)
                else:
                    print(f"\n✓ Alle {total} Audio-Dateien bereits vorhanden (TTS nicht benötigt)")

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
                print("\n🎬 Starte Aufnahme in 3 Sekunden...")
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

        elif do == 'type':
            element = self.browser._find_element(target)
            if element:
                # Im Test-Modus schneller tippen
                speed = 'fast' if test_mode else action.get('speed', 'fast')
                self.browser.type(target, action.get('text', ''), speed)
                print(f"   ✓ type: {target}")
                return True
            else:
                print(f"   ✗ type: {target} (NICHT GEFUNDEN)")
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
            self.browser.upload(action.get('file'))
            print(f"   ✓ upload: {action.get('file')}")
            return True

        elif do == 'wait':
            seconds = action.get('seconds', 1)
            # Im Test-Modus kürzere Wartezeiten
            if test_mode:
                seconds = min(seconds, 0.5)
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

        else:
            print(f"   ? Unbekannte Aktion: {do}")
            return True


# =============================================================================
# MAIN
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='LLARS Demo Video Runner - Produktionssystem',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                         PRODUKTIONS-WORKFLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. SKRIPT PRÜFEN
   python run.py --list                    # Alle Schritte anzeigen
   python run.py --preview                 # Detaillierte Vorschau

2. AUDIO GENERIEREN
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

Narration geändert:     python run.py --audio --force && python run.py
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
    parser.add_argument('--force', '-f', action='store_true',
                        help='Audio-Cache ignorieren, alles neu generieren')
    parser.add_argument('--only', nargs='+', metavar='STEP_ID',
                        help='Nur bestimmte Steps (mit --audio)')
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
    parser.add_argument('--consistent', '-c', action='store_true',
                        help='Konsistente Stimmen (macOS TTS statt Qwen3)')

    args = parser.parse_args()
    runner = ScriptRunner(args.script)

    # Konsistente Stimmen: Überschreibe TTS-Modell
    if args.consistent:
        runner.force_consistent_voices = True
        print("🎯 Konsistente Stimmen aktiviert (macOS TTS)")

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
