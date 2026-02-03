#!/usr/bin/env python3
"""
LLARS Demo Video - Text-to-Speech mit Qwen3-TTS Voice Cloning
==============================================================
Lokales TTS mit Qwen3-TTS (Alibaba Cloud, Januar 2026).

WICHTIG: Für konsistente Stimmen wird VOICE CLONING verwendet!
- Jeder Sprecher hat eine Referenz-Audio-Datei (3-15 Sekunden)
- Alle Generierungen für diesen Sprecher klingen identisch

Modelle:
- Qwen3-TTS-12Hz-1.7B-Base: Beste Qualität, Voice Cloning
- Qwen3-TTS-12Hz-0.6B-Base: Leichtgewicht, Voice Cloning

Installation:
    pip install qwen-tts soundfile
"""

import os
import hashlib
import subprocess
import warnings
from pathlib import Path
from typing import Optional, Dict, Tuple, Any

# Flash Attention Warnung unterdrücken (nicht verfügbar auf Mac/MPS)
os.environ["TRANSFORMERS_NO_FLASH_ATTENTION"] = "1"
warnings.filterwarnings("ignore", message=".*flash-attn.*")
warnings.filterwarnings("ignore", message=".*Flash attention.*")


# =============================================================================
# SPRECHER-DEFINITIONEN MIT REFERENZ-AUDIO
# =============================================================================

SPEAKERS = {
    # Host - freundlich, amerikanisch, professionell
    "host": {
        "name": "Alex",
        "ref_audio": "voices/alex_reference.wav",
        "ref_text": "Hello, I'm Alex. Welcome to this demonstration of LLARS, the LLM Assisted Rating System.",
        "description": "A friendly professional American male voice, clear and articulate.",
        "custom_voice": "Aiden",  # Für CustomVoice-Modell: Sunny American male
    },

    # Narrator - britisch, Attenborough-Stil
    "narrator": {
        "name": "David",
        "ref_audio": "voices/david_reference.wav",
        "ref_text": "In the world of artificial intelligence, we observe remarkable developments. Let me guide you through this fascinating journey.",
        "description": "A distinguished elderly British male voice, calm and authoritative, like a documentary narrator.",
        "custom_voice": "Ryan",  # Für CustomVoice-Modell: Dynamic male with rhythmic drive
    },

    # Technischer Experte
    "expert": {
        "name": "Dr. Chen",
        "ref_audio": "voices/chen_reference.wav",
        "ref_text": "From a technical perspective, this architecture demonstrates several key innovations.",
        "description": "A clear, precise female voice with technical expertise.",
        "custom_voice": "Vivian",  # Für CustomVoice-Modell: Bright young female
    },

    # Default
    "default": {
        "name": "Default",
        "ref_audio": None,
        "ref_text": None,
        "description": "A calm professional male voice, clear and articulate.",
        "custom_voice": "Ryan",  # Fallback
    }
}


class QwenTTS:
    """
    Text-to-Speech mit Qwen3-TTS Voice Cloning.

    Verwendet Referenz-Audio für 100% konsistente Stimmen!
    """

    MODELS = {
        'large': 'Qwen/Qwen3-TTS-12Hz-1.7B-Base',  # Voice Cloning - beste Qualität
        'small': 'Qwen/Qwen3-TTS-12Hz-0.6B-Base',  # Voice Cloning - schneller
        'design': 'Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign',  # Voice Design (weniger konsistent)
        'custom': 'Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice',  # Vordefinierte Stimmen (Ryan, Aiden)
        'custom-small': 'Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice',  # Vordefinierte Stimmen (kleiner)
    }

    # Vordefinierte Sprecher für CustomVoice Modelle
    CUSTOM_SPEAKERS = {
        'Ryan': 'Dynamic male voice with strong rhythmic drive (English)',
        'Aiden': 'Sunny American male voice with clear midrange (English)',
        'Vivian': 'Bright, slightly edgy young female voice (Chinese)',
        'Serena': 'Warm, gentle young female voice (Chinese)',
    }

    def __init__(
        self,
        model_size: str = "large",
        cache_dir: str = "audio/cache",
        device: str = "auto",
        language: str = "English",
        speakers: Optional[Dict] = None,
        voices_dir: str = "voices",
        use_voice_cloning: bool = False  # Voice Cloning ist SEHR langsam auf CPU!
    ):
        self.model_size = model_size
        self.model_id = self.MODELS.get(model_size, self.MODELS['large'])
        self.cache_dir = cache_dir
        self.device = device
        self.language = language
        self.voices_dir = voices_dir
        self.use_voice_cloning = use_voice_cloning

        # Sprecher-Konfiguration
        self.speakers = {**SPEAKERS}
        if speakers:
            for speaker_id, config in speakers.items():
                if speaker_id in self.speakers:
                    self.speakers[speaker_id].update(config)
                else:
                    self.speakers[speaker_id] = config

        self._model = None
        self._voice_prompts = {}  # Cache für Voice Clone Prompts
        self._current_speaker = "default"

        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        Path(voices_dir).mkdir(parents=True, exist_ok=True)

        print(f"🎤 Qwen3-TTS initialisiert (Model: {model_size})")
        print(f"   Sprecher: {', '.join(self.speakers.keys())}")
        if use_voice_cloning:
            print(f"   Modus: Voice Cloning (konsistent, LANGSAM)")
        else:
            print(f"   Modus: Voice Design (schnell, weniger konsistent)")

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
        """Lädt das Qwen3-TTS Modell (lazy loading)"""
        if self._model is not None:
            return

        import sys
        print(f"⏳ Lade Qwen3-TTS: {self.model_id}", flush=True)
        print("   (Erster Start kann einige Minuten dauern...)", flush=True)

        import torch
        from qwen_tts import Qwen3TTSModel

        # Device bestimmen
        # HINWEIS: MPS (Apple Silicon) hängt bei generate_voice_clone()
        # Daher wird CPU verwendet bis Qwen3-TTS MPS-Support verbessert
        if self.device == "auto":
            if torch.cuda.is_available():
                device = "cuda:0"
                dtype = torch.bfloat16
            else:
                device = "cpu"
                dtype = torch.float32
        else:
            device = self.device
            dtype = torch.float32 if device == "cpu" else torch.bfloat16

        print(f"   Device: {device}, dtype: {dtype}", flush=True)

        self._model = Qwen3TTSModel.from_pretrained(
            self.model_id,
            device_map=device,
            dtype=dtype,
        )
        self._device = device

        print(f"✓ Modell geladen auf {device}", flush=True)
        sys.stdout.flush()

    def _get_voice_prompt(self, speaker_id: str):
        """
        Erstellt oder cached einen Voice Clone Prompt für einen Sprecher.

        Der Voice Prompt enthält die Speaker-Embedding aus der Referenz-Audio
        und wird für alle Generierungen dieses Sprechers wiederverwendet.
        """
        if speaker_id in self._voice_prompts:
            return self._voice_prompts[speaker_id]

        config = self.get_speaker_config(speaker_id)
        ref_audio = config.get('ref_audio')
        ref_text = config.get('ref_text')

        if not ref_audio or not ref_text:
            print(f"   ⚠️ Keine Referenz-Audio für {speaker_id}, verwende Voice Design")
            return None

        # Pfad zur Referenz-Audio
        ref_path = os.path.join(self.voices_dir, os.path.basename(ref_audio))
        if not os.path.exists(ref_path):
            # Versuche relativen Pfad
            ref_path = ref_audio
            if not os.path.exists(ref_path):
                print(f"   ⚠️ Referenz-Audio nicht gefunden: {ref_audio}")
                print(f"      Bitte erstelle: {ref_path}")
                return None

        print(f"   🎯 Lade Voice Prompt für {config.get('name', speaker_id)}...", flush=True)
        print(f"      Referenz: {ref_path}", flush=True)

        try:
            # Voice Clone Prompt erstellen
            import time
            start = time.time()
            print(f"      Starte create_voice_clone_prompt()...", flush=True)
            prompt = self._model.create_voice_clone_prompt(
                ref_audio=ref_path,
                ref_text=ref_text,
            )
            print(f"      create_voice_clone_prompt() fertig in {time.time()-start:.1f}s", flush=True)
            self._voice_prompts[speaker_id] = prompt
            print(f"   ✓ Voice Prompt gecached", flush=True)
            return prompt

        except Exception as e:
            print(f"   ⚠️ Voice Prompt Fehler: {e}", flush=True)
            return None

    def _cache_key(self, text: str, speaker_id: str) -> str:
        """Generiert Cache-Key"""
        config = self.get_speaker_config(speaker_id)
        # Inkludiere Referenz-Audio im Key für Konsistenz
        ref_audio = config.get('ref_audio', '')
        content = f"{text}|{self.model_id}|{self.language}|{ref_audio}"
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
        Generiert Audio mit Voice Cloning für konsistente Stimmen.

        Args:
            text: Zu sprechender Text
            output_path: Optionaler Ausgabepfad
            speaker: Sprecher-ID

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

        # Generieren mit Qwen3-TTS
        return self._generate_qwen(text, final_path, speaker_id)

    def _generate_qwen(self, text: str, output_path: str, speaker_id: str) -> str:
        """Generiert mit Qwen3-TTS Voice Cloning"""
        import sys
        config = self.get_speaker_config(speaker_id)
        speaker_name = config.get('name', speaker_id)

        print(f"🎤 Generiere [{speaker_name}]: {text[:50]}...", flush=True)

        try:
            import soundfile as sf

            # Voice Prompt für konsistente Stimme holen
            print(f"   Hole Voice Prompt für {speaker_id}...", flush=True)
            voice_prompt = self._get_voice_prompt(speaker_id)
            print(f"   Voice Prompt: {'vorhanden' if voice_prompt else 'nicht vorhanden'}", flush=True)

            import time
            start = time.time()

            if 'CustomVoice' in (self.model_id or ''):
                # CustomVoice Model - vordefinierte Stimmen (Ryan, Aiden, etc.)
                custom_speaker = config.get('custom_voice', 'Ryan')
                print(f"   Starte CustomVoice [{custom_speaker}]...", flush=True)
                wavs, sr = self._model.generate_custom_voice(
                    text=text,
                    language=self.language,
                    speaker=custom_speaker,
                )
            elif voice_prompt is not None and self.use_voice_cloning:
                # Voice Cloning (konsistent aber SEHR langsam auf CPU!)
                print(f"   Starte Voice Cloning...", flush=True)
                wavs, sr = self._model.generate_voice_clone(
                    text=text,
                    language=self.language,
                    voice_clone_prompt=voice_prompt,
                )
            elif 'VoiceDesign' in (self.model_id or ''):
                # VoiceDesign Model - nutze generate_voice_design
                voice_desc = config.get('description', SPEAKERS['default']['description'])
                print(f"   Starte Voice Design...", flush=True)
                wavs, sr = self._model.generate_voice_design(
                    text=text,
                    language=self.language,
                    instruct=voice_desc,
                )
            else:
                # Fallback für Base Model ohne Voice Cloning
                print(f"   ⚠️ Base Model ohne Voice Cloning - nutze Voice Design Fallback", flush=True)
                voice_desc = config.get('description', SPEAKERS['default']['description'])
                wavs, sr = self._model.generate_voice_design(
                    text=text,
                    language=self.language,
                    instruct=voice_desc,
                )

            print(f"   Generierung abgeschlossen! ({time.time()-start:.1f}s)", flush=True)

            # Speichern
            sf.write(output_path, wavs[0], sr)

            # Cache
            cache_path = self._get_cache_path(text, speaker_id)
            if output_path != cache_path:
                import shutil
                shutil.copy(output_path, cache_path)

            return output_path

        except Exception as e:
            print(f"⚠️ Qwen TTS Fehler: {e}")
            raise RuntimeError(f"Audio-Generierung fehlgeschlagen: {e}")

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
        print("="*70)
        for speaker_id, config in self.speakers.items():
            name = config.get('name', speaker_id)
            ref = config.get('ref_audio', 'keine')
            has_ref = "✓" if ref and os.path.exists(os.path.join(self.voices_dir, os.path.basename(ref))) else "✗"
            print(f"  {speaker_id:12} | {name:15} | Ref: {has_ref} {ref or '-'}")
        print("="*70)


# Alias
TTSEngine = QwenTTS


def create_reference_audio():
    """
    Hilfsfunktion zum Erstellen von Referenz-Audio-Dateien.

    Nutzt macOS TTS um initiale Referenz-Dateien zu erstellen,
    die dann für Voice Cloning verwendet werden.
    """
    import platform
    if platform.system() != 'Darwin':
        print("Diese Funktion ist nur auf macOS verfügbar")
        return

    voices_dir = Path("voices")
    voices_dir.mkdir(exist_ok=True)

    references = {
        "alex_reference.wav": {
            "voice": "Fred",
            "rate": 175,
            "text": "Hello, I'm Alex. Welcome to this demonstration of LLARS, "
                   "the LLM Assisted Rating System. Let me show you how it works."
        },
        "david_reference.wav": {
            "voice": "Daniel",
            "rate": 150,
            "text": "In the world of artificial intelligence, we observe remarkable developments. "
                   "Let me guide you through this fascinating journey of discovery."
        },
        "chen_reference.wav": {
            "voice": "Samantha",
            "rate": 170,
            "text": "From a technical perspective, this architecture demonstrates several key innovations "
                   "that enable scalable and efficient processing."
        }
    }

    print("\n🎙️ Erstelle Referenz-Audio-Dateien...")
    print("="*60)

    for filename, config in references.items():
        output_path = voices_dir / filename
        temp_aiff = str(output_path).replace('.wav', '.aiff')

        print(f"   Erstelle: {filename}")
        print(f"   Stimme: {config['voice']}, Rate: {config['rate']}")

        subprocess.run([
            'say',
            '-v', config['voice'],
            '-r', str(config['rate']),
            '-o', temp_aiff,
            config['text']
        ], capture_output=True)

        subprocess.run([
            'ffmpeg', '-y', '-i', temp_aiff,
            '-ar', '24000',
            '-ac', '1',
            str(output_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(temp_aiff):
            os.remove(temp_aiff)

        print(f"   ✓ {output_path}")

    print("="*60)
    print("\n✓ Referenz-Dateien erstellt!")
    print("  Du kannst diese durch eigene Aufnahmen ersetzen für bessere Qualität.")
    print("  Jede Datei sollte 3-15 Sekunden lang sein.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--create-refs':
        create_reference_audio()
    else:
        print("Testing Qwen3-TTS Voice Cloning...")

        # Erst Referenz-Dateien erstellen falls nicht vorhanden
        if not os.path.exists("voices/alex_reference.wav"):
            print("\n⚠️ Keine Referenz-Dateien gefunden!")
            print("   Erstelle mit: python src/tts.py --create-refs")
            create_reference_audio()

        tts = QwenTTS(model_size="large")
        tts.list_speakers()

        # Test Host
        print("\n--- Host (Alex) ---")
        tts.generate(
            "Welcome to LLARS, a platform for evaluating LLM outputs.",
            "test_host.wav",
            speaker="host"
        )
        tts.play("test_host.wav")

        # Test Narrator
        print("\n--- Narrator (David) ---")
        tts.generate(
            "And here we observe the remarkable process of prompt engineering.",
            "test_narrator.wav",
            speaker="narrator"
        )
        tts.play("test_narrator.wav")

        print("\n✓ Test abgeschlossen")
