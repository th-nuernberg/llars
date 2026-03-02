"""Azure Cognitive Services Speech STT provider."""

import logging

from services.stt.stt_base import STTBase, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class AzureSpeechProvider(STTBase):
    """STT provider using Azure Cognitive Services Speech."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.region = config.get("base_url", "westeurope")  # Reuse base_url field for region

    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=self.region,
            )
            speech_config.speech_recognition_language = self._map_language(language)

            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_stream.write(audio_data)
            audio_stream.close()

            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config,
                audio_config=audio_config,
            )

            result = recognizer.recognize_once()

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return TranscriptResult(
                    text=result.text,
                    language=language,
                    duration=result.duration / 10000000 if result.duration else None,
                )
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return TranscriptResult(text="", language=language)
            else:
                raise RuntimeError(f"Azure speech recognition failed: {result.reason}")

        except ImportError:
            raise ImportError(
                "azure-cognitiveservices-speech package not installed. "
                "Install with: pip install azure-cognitiveservices-speech"
            )
        except Exception as e:
            logger.error("Azure Speech transcription failed: %s", e)
            raise

    @staticmethod
    def _map_language(lang_code: str) -> str:
        """Map short language codes to Azure language identifiers."""
        lang_map = {
            "en": "en-US",
            "de": "de-DE",
            "fr": "fr-FR",
            "es": "es-ES",
            "it": "it-IT",
            "pt": "pt-BR",
            "ja": "ja-JP",
            "zh": "zh-CN",
            "ko": "ko-KR",
        }
        return lang_map.get(lang_code, lang_code)

    def test_connection(self) -> bool:
        try:
            import azure.cognitiveservices.speech as speechsdk

            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key,
                region=self.region,
            )
            return True
        except Exception as e:
            logger.error("Azure Speech connection test failed: %s", e)
            return False
