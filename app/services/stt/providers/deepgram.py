"""Deepgram STT provider (streaming capable)."""

import logging

from services.stt.stt_base import STTBase, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class DeepgramProvider(STTBase):
    """STT provider using Deepgram Nova-2 API."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.model = config.get("model_name", "nova-2")
        self.base_url = config.get("base_url", "https://api.deepgram.com/v1")

    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        try:
            import requests

            mime_map = {
                "wav": "audio/wav",
                "mp3": "audio/mpeg",
                "webm": "audio/webm",
                "ogg": "audio/ogg",
                "flac": "audio/flac",
            }
            content_type = mime_map.get(audio_format, "audio/wav")

            response = requests.post(
                f"{self.base_url}/listen",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": content_type,
                },
                params={
                    "model": self.model,
                    "language": language,
                    "smart_format": "true",
                    "diarize": "true",
                },
                data=audio_data,
                timeout=120,
            )
            response.raise_for_status()
            result = response.json()

            # Parse Deepgram response
            channel = result.get("results", {}).get("channels", [{}])[0]
            alternative = channel.get("alternatives", [{}])[0]
            text = alternative.get("transcript", "")

            segments = []
            for word in alternative.get("words", []):
                segments.append(
                    TranscriptSegment(
                        start=word.get("start", 0),
                        end=word.get("end", 0),
                        text=word.get("word", ""),
                        speaker=str(word.get("speaker", "")),
                        confidence=word.get("confidence"),
                    )
                )

            duration = result.get("metadata", {}).get("duration")

            return TranscriptResult(
                text=text,
                segments=segments,
                language=language,
                duration=duration,
            )

        except Exception as e:
            logger.error("Deepgram transcription failed: %s", e)
            raise

    def test_connection(self) -> bool:
        try:
            import requests

            response = requests.get(
                "https://api.deepgram.com/v1/projects",
                headers={"Authorization": f"Token {self.api_key}"},
                timeout=10,
            )
            return response.status_code == 200
        except Exception as e:
            logger.error("Deepgram connection test failed: %s", e)
            return False
