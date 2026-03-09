"""Local Whisper STT provider (self-hosted)."""

import io
import logging
import tempfile

from services.stt.stt_base import STTBase, TranscriptResult, TranscriptSegment

logger = logging.getLogger(__name__)


class LocalWhisperProvider(STTBase):
    """STT provider using locally-installed Whisper model."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model_name = config.get("model_name", "base")
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                import whisper

                self._model = whisper.load_model(self.model_name)
                logger.info("Loaded local Whisper model: %s", self.model_name)
            except ImportError:
                raise ImportError(
                    "openai-whisper package not installed. Install with: pip install openai-whisper"
                )
        return self._model

    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        try:
            model = self._get_model()

            # Write audio to temp file (whisper requires file path)
            with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=True) as tmp:
                tmp.write(audio_data)
                tmp.flush()

                result = model.transcribe(
                    tmp.name,
                    language=language,
                    verbose=False,
                )

            segments = []
            for seg in result.get("segments", []):
                segments.append(
                    TranscriptSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"].strip(),
                    )
                )

            return TranscriptResult(
                text=result.get("text", "").strip(),
                segments=segments,
                language=result.get("language", language),
            )

        except Exception as e:
            logger.error("Local Whisper transcription failed: %s", e)
            raise
