"""OpenAI Whisper STT provider."""

import io
import logging
from typing import Optional

from services.stt.stt_base import STTBase, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class OpenAIWhisperProvider(STTBase):
    """STT provider using OpenAI's Whisper API."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model_name", "whisper-1")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")

    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"

            response = client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                response_format="verbose_json",
            )

            segments = []
            if hasattr(response, "segments"):
                for seg in response.segments:
                    segments.append(
                        TranscriptSegment(
                            start=seg.get("start", 0),
                            end=seg.get("end", 0),
                            text=seg.get("text", ""),
                        )
                    )

            return TranscriptResult(
                text=response.text,
                segments=segments,
                language=language,
                duration=getattr(response, "duration", None),
            )

        except Exception as e:
            logger.error("OpenAI Whisper transcription failed: %s", e)
            raise

    def test_connection(self) -> bool:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            client.models.list()
            return True
        except Exception as e:
            logger.error("OpenAI Whisper connection test failed: %s", e)
            return False
