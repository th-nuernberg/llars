#!/usr/bin/env python3
"""
LLARS Demo Video - Text-to-Speech mit Qwen3-TTS
================================================
Lokales TTS mit Qwen3-TTS (Alibaba Cloud, Januar 2026).

Features:
- Mehrere Sprecher mit unterschiedlichen Stimmen
- VoiceDesign für Stimm-Beschreibung
- Voice Cloning für Referenz-Audio

Modelle:
- Qwen3-TTS-12Hz-1.7B-VoiceDesign: Beste Qualität, Voice Design
- Qwen3-TTS-12Hz-0.6B-Base: Leichtgewicht

Installation:
    pip install qwen-tts
    brew install sox  # macOS
"""

import os
import hashlib
import subprocess
import warnings
from pathlib import Path
from typing import Optional, Dict

# Flash Attention Warnung unterdrücken (nicht verfügbar auf Mac/MPS)
os.environ["TRANSFORMERS_NO_FLASH_ATTENTION"] = "1"
warnings.filterwarnings("ignore", message=".*flash-attn.*")
warnings.filterwarnings("ignore", message=".*Flash attention.*")


# =============================================================================
# SPRECHER-DEFINITIONEN
# =============================================================================

SPEAKERS = {
    # Standard Host - freundlich, klar, professionell
    "host": {
        "name": "Alex",
        "description": "A friendly professional male voice, clear and articulate, with a warm tone. "
                      "Natural pacing, enthusiastic but not over the top. "
                      "Suitable for software demonstrations and tutorials.",
        "macos_voice": "Daniel",
        "macos_rate": 175,
    },

    # Sir David Attenborough Stil - ruhig, weise, fesselnd
    "narrator": {
        "name": "David",
        "description": "A distinguished elderly British male voice, deep and resonant, "
                      "with the calm authority of a nature documentary narrator. "
                      "Thoughtful pauses, gentle intonation, warm and wise. "
                      "Speaking as if revealing the wonders of the natural world. "
                      "Similar to Sir David Attenborough's iconic narration style.",
        "macos_voice": "Daniel",  # Beste britische Stimme auf macOS
        "macos_rate": 155,  # Langsamer für den Attenborough-Effekt
    },

    # Technischer Experte - präzise, sachlich
    "expert": {
        "name": "Dr. Chen",
        "description": "A clear, precise female voice with a slight technical accent. "
                      "Confident and knowledgeable, speaking with authority on technical matters. "
                      "Well-paced for explaining complex concepts.",
        "macos_voice": "Samantha",
        "macos_rate": 170,
    },

    # Default fallback
    "default": {
        "name": "Default",
        "description": "A calm professional male voice, clear and articulate, "
                      "suitable for technical presentations.",
        "macos_voice": "Daniel",
        "macos_rate": 180,
    }
}


class QwenTTS:
    """
    Text-to-Speech mit Qwen3-TTS (lokal).

    Unterstützt mehrere Sprecher mit unterschiedlichen Stimm-Charakteristiken.
    """

    MODELS = {
        'large': 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',
        'small': 'Qwen/Qwen3-TTS-12Hz-0.6B-Base',
        'fallback': None,  # Nur macOS say verwenden
    }

    def __init__(
        self,
        model_size: str = "small",
        cache_dir: str = "audio/cache",
        device: str = "auto",
        language: str = "English",
        speakers: Optional[Dict] = None
    ):
        self.model_size = model_size
        self.model_id = self.MODELS.get(model_size, self.MODELS['small'])
        self.cache_dir = cache_dir
        self.device = device
        self.language = language

        # Sprecher-Konfiguration (kann von SCRIPT.json überschrieben werden)
        self.speakers = {**SPEAKERS}
        if speakers:
            for speaker_id, config in speakers.items():
                if speaker_id in self.speakers:
                    self.speakers[speaker_id].update(config)
                else:
                    self.speakers[speaker_id] = config

        self._model = None
        self._current_speaker = "default"

        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        print(f"🎤 Qwen3-TTS initialisiert (Model: {model_size})")
        print(f"   Sprecher: {', '.join(self.speakers.keys())}")

    def set_speaker(self, speaker_id: str):
        """Setzt den aktiven Sprecher"""
        if speaker_id in self.speakers:
            self._current_speaker = speaker_id
            speaker = self.speakers[speaker_id]
            print(f"   🎭 Sprecher: {speaker.get('name', speaker_id)}")
        else:
            print(f"   ⚠️ Unbekannter Sprecher: {speaker_id}, verwende 'default'")
            self._current_speaker = "default"

    def get_speaker_config(self, speaker_id: Optional[str] = None) -> dict:
        """Gibt Sprecher-Konfiguration zurück"""
        sid = speaker_id or self._current_speaker
        return self.speakers.get(sid, self.speakers["default"])

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

    def _cache_key(self, text: str, speaker_id: str) -> str:
        """Generiert Cache-Key (inkl. Sprecher)"""
        speaker_config = self.get_speaker_config(speaker_id)
        content = f"{text}|{self.model_id}|{self.language}|{speaker_config.get('description', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_path(self, text: str, speaker_id: str) -> str:
        """Cache-Pfad für Text + Sprecher"""
        key = self._cache_key(text, speaker_id)
        return os.path.join(self.cache_dir, f"{key}.wav")

    def generate(
        self,
        text: str,
        output_path: Optional[str] = None,
        speaker: Optional[str] = None
    ) -> str:
        """
        Generiert Audio für Text mit optionalem Sprecher.

        Args:
            text: Zu sprechender Text
            output_path: Optionaler Ausgabepfad
            speaker: Sprecher-ID (default: aktueller Sprecher)

        Returns:
            Pfad zur Audio-Datei
        """
        speaker_id = speaker or self._current_speaker

        # Cache prüfen
        cache_path = self._get_cache_path(text, speaker_id)
        if os.path.exists(cache_path):
            speaker_name = self.get_speaker_config(speaker_id).get('name', speaker_id)
            print(f"♻️ Cache [{speaker_name}]: {text[:40]}...")
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
            return self._generate_fallback(text, final_path, speaker_id)
        else:
            return self._generate_qwen(text, final_path, speaker_id)

    def _generate_qwen(self, text: str, output_path: str, speaker_id: str) -> str:
        """Generiert mit Qwen3-TTS"""
        speaker_config = self.get_speaker_config(speaker_id)
        speaker_name = speaker_config.get('name', speaker_id)
        voice_description = speaker_config.get('description', SPEAKERS['default']['description'])

        print(f"🎤 Generiere [{speaker_name}]: {text[:50]}...")

        try:
            import soundfile as sf

            # Voice Design für konsistente Stimme pro Sprecher
            if 'VoiceDesign' in self.model_id:
                wavs, sr = self._model.generate_voice_design(
                    text=text,
                    language=self.language,
                    instruct=voice_description,
                )
            else:
                # Base model - einfache Generierung (keine Stimm-Kontrolle)
                wavs, sr = self._model.generate(
                    text=text,
                    language=self.language,
                )

            # Speichern
            sf.write(output_path, wavs[0], sr)

            # Cache
            cache_path = self._get_cache_path(text, speaker_id)
            if output_path != cache_path:
                import shutil
                shutil.copy(output_path, cache_path)

            return output_path

        except Exception as e:
            print(f"⚠️ Qwen Fehler: {e}")
            return self._generate_fallback(text, output_path, speaker_id)

    def _generate_fallback(self, text: str, output_path: str, speaker_id: str) -> str:
        """Fallback: macOS say mit sprecher-spezifischer Stimme"""
        speaker_config = self.get_speaker_config(speaker_id)
        speaker_name = speaker_config.get('name', speaker_id)
        voice = speaker_config.get('macos_voice', 'Daniel')
        rate = speaker_config.get('macos_rate', 180)

        print(f"🎤 macOS TTS [{speaker_name}]: {text[:50]}...")

        import platform
        if platform.system() != 'Darwin':
            print("⚠️ Fallback nur auf macOS verfügbar")
            Path(output_path).touch()
            return output_path

        # macOS say -> AIFF -> WAV
        temp_aiff = output_path.replace('.wav', '.aiff')

        subprocess.run([
            'say',
            '-v', voice,
            '-r', str(rate),
            '-o', temp_aiff,
            text
        ], capture_output=True)

        # Konvertieren zu WAV
        subprocess.run([
            'ffmpeg', '-y', '-i', temp_aiff,
            '-ar', '24000',
            '-ac', '1',
            output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)

        # Cache
        cache_path = self._get_cache_path(text, speaker_id)
        if output_path != cache_path and os.path.exists(output_path):
            import shutil
            shutil.copy(output_path, cache_path)

        return output_path

    def speak(self, text: str, speaker: Optional[str] = None):
        """Spricht Text (blockierend)"""
        audio_path = self.generate(text, speaker=speaker)
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

    def list_speakers(self):
        """Zeigt verfügbare Sprecher"""
        print("\n🎭 Verfügbare Sprecher:")
        print("="*60)
        for speaker_id, config in self.speakers.items():
            name = config.get('name', speaker_id)
            desc = config.get('description', '')[:60]
            print(f"  {speaker_id:12} | {name:15} | {desc}...")
        print("="*60)


# Alias
TTSEngine = QwenTTS


if __name__ == '__main__':
    print("Testing Qwen3-TTS Multi-Speaker...")
    tts = QwenTTS(model_size="fallback")  # Fallback für schnellen Test

    tts.list_speakers()

    # Test Host
    print("\n--- Host ---")
    tts.generate(
        "Welcome to LLARS, a platform for evaluating LLM outputs.",
        "test_host.wav",
        speaker="host"
    )
    tts.play("test_host.wav")

    # Test Narrator (Attenborough-Stil)
    print("\n--- Narrator (Attenborough) ---")
    tts.generate(
        "And here we observe... the remarkable process of prompt engineering. "
        "A delicate dance between human expertise and artificial intelligence.",
        "test_narrator.wav",
        speaker="narrator"
    )
    tts.play("test_narrator.wav")

    print("\n✓ Test abgeschlossen")
