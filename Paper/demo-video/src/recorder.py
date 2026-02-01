#!/usr/bin/env python3
"""
LLARS Demo Video - Screen Recorder
===================================
Nimmt den Bildschirm auf mit separatem Audio-Track.

Features:
- ffmpeg-basiertes Recording für hohe Qualität
- Separater Audio-Track für TTS
- Snapshot-Funktion
- Automatische Segmentierung
"""

import subprocess
import threading
import time
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class RecorderConfig:
    output_dir: str = "output"
    resolution: tuple = (1920, 1080)
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 18  # Qualität (0-51, niedriger = besser)
    preset: str = "fast"


class ScreenRecorder:
    """
    Screen Recording mit ffmpeg.
    Unterstützt macOS (avfoundation) und Linux (x11grab).
    """

    def __init__(
        self,
        output_dir: str = "output",
        resolution: tuple = (1920, 1080),
        fps: int = 30
    ):
        self.config = RecorderConfig(
            output_dir=output_dir,
            resolution=resolution,
            fps=fps
        )
        self.process: Optional[subprocess.Popen] = None
        self.is_recording = False
        self.current_output: Optional[str] = None
        self.segment_count = 0

        # Output-Verzeichnis erstellen
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Plattform erkennen
        import platform
        self.platform = platform.system().lower()

        # ffmpeg prüfen
        self._check_ffmpeg()

    def _check_ffmpeg(self):
        """Prüft ob ffmpeg verfügbar ist"""
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            print("✓ ffmpeg gefunden")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "ffmpeg nicht gefunden! Installation:\n"
                "  macOS: brew install ffmpeg\n"
                "  Ubuntu: sudo apt install ffmpeg"
            )

    def _build_command(self, output_path: str) -> list:
        """Erstellt ffmpeg-Befehl basierend auf Plattform"""
        width, height = self.config.resolution

        if self.platform == 'darwin':  # macOS
            # Capture Display 1 (Hauptbildschirm)
            return [
                'ffmpeg',
                '-y',  # Überschreiben ohne Nachfrage
                '-f', 'avfoundation',
                '-framerate', str(self.config.fps),
                '-capture_cursor', '1',
                '-i', '1:none',  # Display 1, kein Audio
                '-vf', f'scale={width}:{height}',
                '-c:v', self.config.video_codec,
                '-preset', self.config.preset,
                '-crf', str(self.config.crf),
                '-pix_fmt', 'yuv420p',
                output_path
            ]

        elif self.platform == 'linux':
            return [
                'ffmpeg',
                '-y',
                '-f', 'x11grab',
                '-framerate', str(self.config.fps),
                '-video_size', f'{width}x{height}',
                '-i', ':0.0',
                '-c:v', self.config.video_codec,
                '-preset', self.config.preset,
                '-crf', str(self.config.crf),
                '-pix_fmt', 'yuv420p',
                output_path
            ]

        else:
            raise RuntimeError(f"Plattform nicht unterstützt: {self.platform}")

    def start(self, filename: Optional[str] = None):
        """Startet die Aufnahme"""
        if self.is_recording:
            print("⚠️ Aufnahme läuft bereits")
            return

        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.mp4"

        self.current_output = os.path.join(self.config.output_dir, filename)
        command = self._build_command(self.current_output)

        print(f"🎬 Starte Aufnahme: {self.current_output}")

        # ffmpeg starten
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        self.is_recording = True
        self.segment_count = 0

    def stop(self) -> Optional[str]:
        """Stoppt die Aufnahme"""
        if not self.is_recording or not self.process:
            return None

        print("⏹️ Stoppe Aufnahme...")

        # ffmpeg sauber beenden mit 'q'
        try:
            self.process.stdin.write(b'q')
            self.process.stdin.flush()
            self.process.wait(timeout=10)
        except Exception:
            self.process.terminate()
            self.process.wait(timeout=5)

        self.is_recording = False
        output = self.current_output
        self.current_output = None

        print(f"✓ Aufnahme gespeichert: {output}")
        return output

    def pause(self):
        """Pausiert die Aufnahme (stoppt und startet neues Segment)"""
        if not self.is_recording:
            return

        self.segment_count += 1
        current_segment = self.current_output

        # Stoppe aktuelles Segment
        self.stop()

        # Neues Segment starten
        base_name = Path(current_segment).stem
        new_name = f"{base_name}_segment{self.segment_count:03d}.mp4"
        self.start(new_name)

    def save_snapshot(self, output_path: str):
        """Speichert aktuellen Frame als Bild"""
        if self.platform == 'darwin':
            command = [
                'screencapture',
                '-x',  # Kein Sound
                output_path
            ]
        else:
            command = [
                'ffmpeg',
                '-y',
                '-f', 'x11grab',
                '-video_size', f'{self.config.resolution[0]}x{self.config.resolution[1]}',
                '-i', ':0.0',
                '-frames:v', '1',
                output_path
            ]

        subprocess.run(command, capture_output=True)
        print(f"📸 Snapshot: {output_path}")

    def merge_with_audio(
        self,
        video_path: str,
        audio_path: str,
        output_path: str
    ):
        """
        Fügt Video und Audio zusammen.

        Args:
            video_path: Pfad zum Video
            audio_path: Pfad zur Audio-Datei
            output_path: Ausgabepfad
        """
        command = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-i', audio_path,
            '-c:v', 'copy',
            '-c:a', self.config.audio_codec,
            '-shortest',
            output_path
        ]

        print(f"🎵 Merge Video + Audio: {output_path}")
        subprocess.run(command, capture_output=True, check=True)

    def merge_segments(self, segment_paths: list, output_path: str):
        """
        Fügt mehrere Video-Segmente zusammen.

        Args:
            segment_paths: Liste von Video-Pfaden
            output_path: Ausgabepfad
        """
        # Concat-Datei erstellen
        concat_file = os.path.join(self.config.output_dir, '_concat.txt')
        with open(concat_file, 'w') as f:
            for path in segment_paths:
                f.write(f"file '{os.path.abspath(path)}'\n")

        command = [
            'ffmpeg',
            '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]

        print(f"🔗 Merge Segments: {output_path}")
        subprocess.run(command, capture_output=True, check=True)

        # Cleanup
        os.remove(concat_file)


class AudioTrackRecorder:
    """
    Sammelt Audio-Segmente für späteres Merging.
    """

    def __init__(self, output_dir: str = "output/audio"):
        self.output_dir = output_dir
        self.segments: list = []
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def add_segment(self, audio_path: str, start_time: float, duration: float):
        """Fügt ein Audio-Segment hinzu"""
        self.segments.append({
            'path': audio_path,
            'start': start_time,
            'duration': duration
        })

    def build_track(self, output_path: str, total_duration: float):
        """
        Erstellt finale Audio-Spur aus Segmenten.

        Fügt Stille ein wo nötig.
        """
        if not self.segments:
            return

        # Filter-Complex für ffmpeg bauen
        filter_parts = []
        inputs = []

        for i, seg in enumerate(sorted(self.segments, key=lambda x: x['start'])):
            inputs.extend(['-i', seg['path']])

            # Delay für Startzeit
            delay_ms = int(seg['start'] * 1000)
            filter_parts.append(
                f"[{i}:a]adelay={delay_ms}|{delay_ms}[a{i}]"
            )

        # Alle Streams mixen
        mix_inputs = ''.join(f'[a{i}]' for i in range(len(self.segments)))
        filter_parts.append(
            f"{mix_inputs}amix=inputs={len(self.segments)}:duration=longest[aout]"
        )

        filter_complex = ';'.join(filter_parts)

        command = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', filter_complex,
            '-map', '[aout]',
            '-t', str(total_duration),
            output_path
        ]

        subprocess.run(command, capture_output=True, check=True)
        print(f"🎵 Audio Track erstellt: {output_path}")


# Test
if __name__ == '__main__':
    print("Testing Screen Recorder...")

    recorder = ScreenRecorder(output_dir="test_output")

    print("Starting 5 second test recording...")
    recorder.start("test_recording.mp4")
    time.sleep(5)
    output = recorder.stop()

    print(f"Test complete: {output}")
