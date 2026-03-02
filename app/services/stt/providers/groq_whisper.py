"""Groq Whisper STT provider (fast, cheap cloud)."""

import io
import logging

from services.stt.stt_base import STTBase, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class GroqWhisperProvider(STTBase):
    """STT provider using Groq's Whisper API."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model_name", "whisper-large-v3")
        self.base_url = config.get("base_url", "https://api.groq.com/openai/v1")

    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        try:
            from openai import OpenAI

            # Groq uses OpenAI-compatible API
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
            logger.error("Groq Whisper transcription failed: %s", e)
            raise
