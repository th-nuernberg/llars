#!/usr/bin/env python3
"""
Lars Demo Video Orchestrator
=============================
Koordiniert Autoclicker, Screen Recording und TTS für automatisierte Demo-Videos.

Interaktive Steuerung:
- SPACE: Pause/Resume
- R: Aktuelle Szene wiederholen
- E: Skript editieren
- S: Snapshot speichern
- Q: Beenden mit Checkpoint
- N: Nächste Szene überspringen

Nutzung:
    python orchestrator.py --script scripts/full_script.json --output output/demo.mp4
    python orchestrator.py --resume checkpoint.json  # Fortsetzen nach Pause
"""

import json
import time
import threading
import subprocess
import sys
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum
import queue

# Abhängigkeiten
try:
    import keyboard
except ImportError:
    print("Installing keyboard...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])
    import keyboard


class RecordingState(Enum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINT = "checkpoint"


@dataclass
class Checkpoint:
    """Speichert den aktuellen Zustand für Resume"""
    scene_index: int
    segment_index: int
    timestamp: float
    script_path: str
    output_path: str

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.__dict__, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'Checkpoint':
        with open(path) as f:
            return cls(**json.load(f))


@dataclass
class OrchestratorConfig:
    script_path: str
    output_dir: str = "output"
    resolution: tuple = (1920, 1080)
    fps: int = 30
    tts_voice: str = "alloy"  # OpenAI TTS voice
    browser_url: str = "http://localhost:55080"
    checkpoint_dir: str = "checkpoints"
    preview_enabled: bool = True


class DemoOrchestrator:
    """
    Hauptklasse für die Video-Produktion.
    Koordiniert alle Komponenten und bietet interaktive Steuerung.
    """

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.state = RecordingState.STOPPED
        self.script = None
        self.current_scene = 0
        self.current_segment = 0
        self.command_queue = queue.Queue()

        # Komponenten (werden lazy initialisiert)
        self._autoclicker = None
        self._recorder = None
        self._tts = None

        # Event für Pause/Resume
        self._pause_event = threading.Event()
        self._pause_event.set()  # Nicht pausiert

        # Output-Verzeichnisse erstellen
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.checkpoint_dir).mkdir(parents=True, exist_ok=True)

    def load_script(self):
        """Lädt das Video-Skript"""
        with open(self.config.script_path) as f:
            self.script = json.load(f)
        print(f"✓ Skript geladen: {len(self.script['scenes'])} Szenen")
        return self.script

    @property
    def autoclicker(self):
        """Lazy-Loading für Autoclicker"""
        if self._autoclicker is None:
            from autoclicker import AutoClicker
            self._autoclicker = AutoClicker(
                browser_url=self.config.browser_url,
                highlight_clicks=True
            )
        return self._autoclicker

    @property
    def recorder(self):
        """Lazy-Loading für Recorder"""
        if self._recorder is None:
            from recorder import ScreenRecorder
            self._recorder = ScreenRecorder(
                output_dir=self.config.output_dir,
                resolution=self.config.resolution,
                fps=self.config.fps
            )
        return self._recorder

    @property
    def tts(self):
        """Lazy-Loading für TTS"""
        if self._tts is None:
            from tts import TTSEngine
            self._tts = TTSEngine(voice=self.config.tts_voice)
        return self._tts

    def setup_hotkeys(self):
        """Registriert Tastatur-Shortcuts"""
        keyboard.on_press_key('space', lambda _: self.toggle_pause())
        keyboard.on_press_key('r', lambda _: self.redo_segment())
        keyboard.on_press_key('e', lambda _: self.edit_script())
        keyboard.on_press_key('s', lambda _: self.save_snapshot())
        keyboard.on_press_key('q', lambda _: self.quit_with_checkpoint())
        keyboard.on_press_key('n', lambda _: self.skip_segment())
        print("✓ Hotkeys registriert: SPACE=Pause, R=Redo, E=Edit, S=Snapshot, Q=Quit, N=Skip")

    def toggle_pause(self):
        """Pausiert oder setzt die Aufnahme fort"""
        if self.state == RecordingState.RUNNING:
            self.state = RecordingState.PAUSED
            self._pause_event.clear()
            print("\n⏸  PAUSIERT - SPACE zum Fortsetzen")
        elif self.state == RecordingState.PAUSED:
            self.state = RecordingState.RUNNING
            self._pause_event.set()
            print("\n▶  FORTGESETZT")

    def redo_segment(self):
        """Wiederholt das aktuelle Segment"""
        self.command_queue.put(('redo', None))
        print("\n🔄 Segment wird wiederholt...")

    def edit_script(self):
        """Öffnet das Skript im Editor"""
        self.toggle_pause()  # Automatisch pausieren
        print(f"\n✏️  Skript öffnen: {self.config.script_path}")
        print("   Nach Bearbeitung: SPACE zum Fortsetzen")
        # Editor öffnen (VS Code, falls verfügbar)
        try:
            subprocess.Popen(['code', self.config.script_path])
        except FileNotFoundError:
            subprocess.Popen(['open', self.config.script_path])  # macOS Fallback

    def save_snapshot(self):
        """Speichert aktuellen Frame als Bild"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        snapshot_path = f"{self.config.output_dir}/snapshot_{timestamp}.png"
        self.recorder.save_snapshot(snapshot_path)
        print(f"\n📸 Snapshot gespeichert: {snapshot_path}")

    def quit_with_checkpoint(self):
        """Beendet mit Checkpoint für späteren Resume"""
        checkpoint = Checkpoint(
            scene_index=self.current_scene,
            segment_index=self.current_segment,
            timestamp=time.time(),
            script_path=self.config.script_path,
            output_path=self.config.output_dir
        )
        checkpoint_path = f"{self.config.checkpoint_dir}/checkpoint_{int(time.time())}.json"
        checkpoint.save(checkpoint_path)
        print(f"\n💾 Checkpoint gespeichert: {checkpoint_path}")
        self.state = RecordingState.STOPPED

    def skip_segment(self):
        """Überspringt zum nächsten Segment"""
        self.command_queue.put(('skip', None))
        print("\n⏭  Segment übersprungen")

    def wait_with_pause_check(self, duration: float, check_interval: float = 0.1):
        """Wartet mit Pause-Unterstützung"""
        elapsed = 0
        while elapsed < duration:
            self._pause_event.wait()  # Blockiert wenn pausiert
            if self.state == RecordingState.STOPPED:
                return False
            time.sleep(min(check_interval, duration - elapsed))
            elapsed += check_interval
        return True

    def run_segment(self, segment: dict) -> bool:
        """
        Führt ein einzelnes Segment aus.
        Returns: True wenn erfolgreich, False wenn abgebrochen/wiederholt
        """
        segment_id = segment.get('id', 'unknown')
        narration = segment.get('narration', '')
        actions = segment.get('actions', [])
        duration = segment.get('duration', 5)

        print(f"\n{'='*60}")
        print(f"Segment: {segment_id}")
        print(f"Narration: {narration[:80]}...")
        print(f"Actions: {len(actions)}")
        print(f"{'='*60}")

        # TTS starten (async)
        if narration:
            audio_thread = threading.Thread(
                target=self.tts.speak,
                args=(narration,)
            )
            audio_thread.start()

        # Aktionen ausführen
        for action in actions:
            # Prüfe auf Commands
            try:
                cmd, _ = self.command_queue.get_nowait()
                if cmd == 'redo':
                    return False  # Segment wiederholen
                elif cmd == 'skip':
                    return True  # Zum nächsten
            except queue.Empty:
                pass

            # Warte wenn pausiert
            self._pause_event.wait()
            if self.state == RecordingState.STOPPED:
                return False

            # Aktion ausführen
            self.execute_action(action)

        # Warte auf TTS Ende
        if narration:
            audio_thread.join()

        return True

    def execute_action(self, action: dict):
        """Führt eine einzelne UI-Aktion aus"""
        action_type = action.get('type')

        if action_type == 'click':
            selector = action.get('selector')
            self.autoclicker.click(selector)

        elif action_type == 'type':
            selector = action.get('selector')
            text = action.get('text')
            delay = action.get('delay', 50)
            self.autoclicker.type_text(selector, text, delay)

        elif action_type == 'navigate':
            url = action.get('url')
            self.autoclicker.navigate(url)

        elif action_type == 'wait':
            duration = action.get('duration', 1000) / 1000
            self.wait_with_pause_check(duration)

        elif action_type == 'wait_for':
            selector = action.get('selector')
            timeout = action.get('timeout', 5000) / 1000
            self.autoclicker.wait_for_element(selector, timeout)

        elif action_type == 'highlight':
            selector = action.get('selector')
            duration = action.get('duration', 2000) / 1000
            self.autoclicker.highlight(selector, duration)

        elif action_type == 'drag_drop':
            source = action.get('source')
            target = action.get('target')
            self.autoclicker.drag_drop(source, target)

        elif action_type == 'scroll':
            selector = action.get('selector')
            direction = action.get('direction', 'down')
            amount = action.get('amount', 100)
            self.autoclicker.scroll(selector, direction, amount)

        elif action_type == 'switch_window':
            window = action.get('window', 1)
            self.autoclicker.switch_window(window)

        elif action_type == 'upload_file':
            selector = action.get('selector')
            file_path = action.get('file')
            self.autoclicker.upload_file(selector, file_path)

        elif action_type == 'clear':
            selector = action.get('selector')
            self.autoclicker.clear(selector)

    def run_scene(self, scene: dict) -> bool:
        """Führt eine komplette Szene aus"""
        scene_name = scene.get('name', 'Unknown')
        segments = scene.get('segments', [])

        print(f"\n{'#'*70}")
        print(f"# SZENE: {scene_name}")
        print(f"# Segments: {len(segments)}")
        print(f"{'#'*70}")

        for i, segment in enumerate(segments):
            self.current_segment = i

            success = self.run_segment(segment)
            while not success:
                # Segment wurde abgebrochen, wiederholen
                success = self.run_segment(segment)

            if self.state == RecordingState.STOPPED:
                return False

        return True

    def run(self, resume_from: Optional[Checkpoint] = None):
        """
        Hauptschleife - führt das komplette Skript aus.

        Args:
            resume_from: Optional Checkpoint zum Fortsetzen
        """
        self.load_script()
        self.setup_hotkeys()

        # Start-Position
        start_scene = 0
        start_segment = 0
        if resume_from:
            start_scene = resume_from.scene_index
            start_segment = resume_from.segment_index
            print(f"📂 Fortsetzen von Szene {start_scene}, Segment {start_segment}")

        # Recording starten
        print("\n🎬 AUFNAHME STARTET IN 3 SEKUNDEN...")
        time.sleep(3)

        self.state = RecordingState.RUNNING
        self.recorder.start()

        try:
            scenes = self.script['scenes']
            for i in range(start_scene, len(scenes)):
                self.current_scene = i
                scene = scenes[i]

                if not self.run_scene(scene):
                    break

                # Checkpoint nach jeder Szene
                if self.state == RecordingState.RUNNING:
                    self._auto_checkpoint()

        except KeyboardInterrupt:
            print("\n⚠️  Unterbrochen durch Benutzer")
        finally:
            self.recorder.stop()
            self.state = RecordingState.STOPPED
            keyboard.unhook_all()

        print("\n✅ AUFNAHME BEENDET")
        print(f"   Output: {self.config.output_dir}")

    def _auto_checkpoint(self):
        """Automatischer Checkpoint nach jeder Szene"""
        checkpoint = Checkpoint(
            scene_index=self.current_scene + 1,
            segment_index=0,
            timestamp=time.time(),
            script_path=self.config.script_path,
            output_path=self.config.output_dir
        )
        path = f"{self.config.checkpoint_dir}/auto_checkpoint.json"
        checkpoint.save(path)

    def preview_script(self):
        """Zeigt eine Vorschau des Skripts ohne Aufnahme"""
        self.load_script()

        print("\n📋 SKRIPT-VORSCHAU")
        print("="*70)

        total_duration = 0
        for scene in self.script['scenes']:
            scene_duration = scene.get('duration_seconds', 0)
            total_duration += scene_duration

            print(f"\n🎬 {scene['name']} ({scene_duration}s)")
            for segment in scene.get('segments', []):
                narration = segment.get('narration', '')[:60]
                actions = len(segment.get('actions', []))
                print(f"   • {segment['id']}: {narration}... [{actions} actions]")

        print(f"\n{'='*70}")
        print(f"Gesamtdauer: {total_duration}s ({total_duration/60:.1f} min)")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Lars Demo Video Orchestrator')
    parser.add_argument('--script', default='scripts/full_script.json',
                        help='Pfad zum Skript')
    parser.add_argument('--output', default='output',
                        help='Output-Verzeichnis')
    parser.add_argument('--resume', help='Checkpoint-Datei zum Fortsetzen')
    parser.add_argument('--preview', action='store_true',
                        help='Nur Vorschau zeigen')
    parser.add_argument('--url', default='http://localhost:55080',
                        help='Lars URL')

    args = parser.parse_args()

    config = OrchestratorConfig(
        script_path=args.script,
        output_dir=args.output,
        browser_url=args.url
    )

    orchestrator = DemoOrchestrator(config)

    if args.preview:
        orchestrator.preview_script()
    elif args.resume:
        checkpoint = Checkpoint.load(args.resume)
        orchestrator.run(resume_from=checkpoint)
    else:
        orchestrator.run()


if __name__ == '__main__':
    main()
