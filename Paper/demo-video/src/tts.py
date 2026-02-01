#!/usr/bin/env python3
"""
LLARS Demo Video - Text-to-Speech mit Qwen3-TTS
================================================
Lokales TTS mit Qwen3-TTS (Alibaba Cloud, Januar 2026).

Modelle:
- Qwen3-TTS-12Hz-1.7B: Beste Qualität, ~6GB VRAM
- Qwen3-TTS-12Hz-0.6B: Leichtgewicht, ~4GB VRAM

Installation:
    pip install qwen-tts
    brew install sox  # macOS
"""

import os
import hashlib
import subprocess
import warnings
from pathlib import Path
from typing import Optional

# Flash Attention Warnung unterdrücken (nicht verfügbar auf Mac/MPS)
os.environ["TRANSFORMERS_NO_FLASH_ATTENTION"] = "1"
warnings.filterwarnings("ignore", message=".*flash-attn.*")
warnings.filterwarnings("ignore", message=".*Flash attention.*")


class QwenTTS:
    """
    Text-to-Speech mit Qwen3-TTS (lokal).

    Verwendet die VoiceDesign-Variante für konsistente Stimme.
    """

    MODELS = {
        'large': 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',
        'small': 'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
        'fallback': None,  # Nur macOS say verwenden
    }

    # Deutsche männliche Stimme für Demo
    VOICE_DESCRIPTION = "A calm professional male voice, clear and articulate, suitable for technical presentations."

    def __init__(
        self,
        model_size: str = "small",
        cache_dir: str = "audio/cache",
        device: str = "auto",
        language: str = "English"
    ):
        self.model_size = model_size
        self.model_id = self.MODELS.get(model_size, self.MODELS['small'])
        self.cache_dir = cache_dir
        self.device = device
        self.language = language

        self._model = None

        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        print(f"🎤 Qwen3-TTS initialisiert (Model: {model_size})")

    def _load_model(self):
        """Lädt das Modell (lazy loading)"""
        if self._model is not None:
            return

        # Fallback-Modus: Kein Modell laden, direkt macOS say nutzen
        if self.model_id is None:
            print("🎤 Verwende macOS TTS (say) als Fallback")
            self._model = "fallback"
            return

        print(f"⏳ Lade Qwen3-TTS: {self.model_id}")
        print("   (Erster Start kann einige Minuten dauern...)")

        try:
            import torch
            from qwen_tts import Qwen3TTSModel

            # Device bestimmen
            if self.device == "auto":
                if torch.cuda.is_available():
                    device = "cuda:0"
                    dtype = torch.bfloat16
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device = "mps"
                    dtype = torch.float32  # MPS braucht float32
                else:
                    device = "cpu"
                    dtype = torch.float32
            else:
                device = self.device
                dtype = torch.float32 if device == "mps" else torch.bfloat16

            self._model = Qwen3TTSModel.from_pretrained(
                self.model_id,
                device_map=device,
                dtype=dtype,
            )
            self._device = device

            print(f"✓ Modell geladen auf {device}")

        except Exception as e:
            print(f"⚠️ Fehler beim Laden: {e}")
            print("   Fallback zu macOS TTS...")
            self._model = "fallback"

    def _cache_key(self, text: str) -> str:
        """Generiert Cache-Key"""
        content = f"{text}|{self.model_id}|{self.language}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, text: str) -> str:
        """Cache-Pfad für Text"""
        key = self._cache_key(text)
        return os.path.join(self.cache_dir, f"{key}.wav")

    def generate(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Generiert Audio für Text.

        Args:
            text: Zu sprechender Text
            output_path: Optionaler Ausgabepfad

        Returns:
            Pfad zur Audio-Datei
        """
        # Cache prüfen
        cache_path = self._get_cache_path(text)
        if os.path.exists(cache_path):
            print(f"♻️ Cache: {text[:40]}...")
            if output_path and output_path != cache_path:
                import shutil
                shutil.copy(cache_path, output_path)
                return output_path
            return cache_path

        # Modell laden
        self._load_model()

        final_path = output_path or cache_path

        # Generieren
        if self._model == "fallback":
            return self._generate_fallback(text, final_path)
        else:
            return self._generate_qwen(text, final_path)

    def _generate_qwen(self, text: str, output_path: str) -> str:
        """Generiert mit Qwen3-TTS"""
        print(f"🎤 Generiere: {text[:50]}...")

        try:
            import soundfile as sf

            # Voice Design für konsistente Stimme
            if 'VoiceDesign' in self.model_id:
                wavs, sr = self._model.generate_voice_design(
                    text=text,
                    language=self.language,
                    instruct=self.VOICE_DESCRIPTION,
                )
            else:
                # Base model - einfache Generierung
                wavs, sr = self._model.generate(
                    text=text,
                    language=self.language,
                )

            # Speichern
            sf.write(output_path, wavs[0], sr)

            # Cache
            cache_path = self._get_cache_path(text)
            if output_path != cache_path:
                import shutil
                shutil.copy(output_path, cache_path)

            return output_path

        except Exception as e:
            print(f"⚠️ Qwen Fehler: {e}")
            return self._generate_fallback(text, output_path)

    def _generate_fallback(self, text: str, output_path: str) -> str:
        """Fallback: macOS say"""
        print(f"🎤 macOS TTS: {text[:50]}...")

        import platform
        if platform.system() != 'Darwin':
            print("⚠️ Fallback nur auf macOS verfügbar")
            # Leere Datei erstellen
            Path(output_path).touch()
            return output_path

        # macOS say -> AIFF -> WAV
        temp_aiff = output_path.replace('.wav', '.aiff')

        subprocess.run([
            'say',
            '-v', 'Daniel',  # Gute englische Stimme
            '-r', '180',     # Sprechgeschwindigkeit
            '-o', temp_aiff,
            text
        ], capture_output=True)

        # Konvertieren zu WAV
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_aiff,
            '-ar', '24000',
            '-ac', '1',
            output_path
        ], capture_output=True, stderr=subprocess.DEVNULL)

        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)

        # Cache
        cache_path = self._get_cache_path(text)
        if output_path != cache_path and os.path.exists(output_path):
            import shutil
            shutil.copy(output_path, cache_path)

        return output_path

    def speak(self, text: str):
        """Spricht Text (blockierend)"""
        audio_path = self.generate(text)
        self.play(audio_path)

    def play(self, audio_path: str):
        """Spielt Audio ab"""
        import platform
        if platform.system() == 'Darwin':
            subprocess.run(['afplay', audio_path], capture_output=True)
        else:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', audio_path],
                           capture_output=True, stderr=subprocess.DEVNULL)

    def get_duration(self, audio_path: str) -> float:
        """Dauer in Sekunden"""
        result = subprocess.run([
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ], capture_output=True, text=True)

        try:
            return float(result.stdout.strip())
        except ValueError:
            return 5.0


# Alias
TTSEngine = QwenTTS


if __name__ == '__main__':
    print("Testing Qwen3-TTS...")
    tts = QwenTTS(model_size="small")

    test = "Welcome to LLARS, a platform for evaluating LLM outputs with human and machine evaluators."
    audio = tts.generate(test, "test_audio.wav")

    print(f"Generated: {audio}")
    print("Playing...")
    tts.play(audio)
