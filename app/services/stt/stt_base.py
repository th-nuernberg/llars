"""Base class for STT (Speech-to-Text) providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional


@dataclass
class TranscriptSegment:
    """A segment of transcribed audio."""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


@dataclass
class TranscriptResult:
    """Result from a transcription operation."""
    text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class TranscriptChunk:
    """A chunk of live transcription (streaming)."""
    text: str
    is_final: bool = False
    speaker: Optional[str] = None
    timestamp: Optional[float] = None


class STTBase(ABC):
    """Abstract base class for STT providers."""

    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def transcribe(
        self,
        audio_data: bytes,
        language: str = "en",
        audio_format: str = "wav",
    ) -> TranscriptResult:
        """
        Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., 'en', 'de')
            audio_format: Audio format ('wav', 'mp3', 'webm', etc.)

        Returns:
            TranscriptResult with text and segments
        """
        pass

    def transcribe_stream(
        self,
        audio_stream,
        language: str = "en",
    ) -> AsyncIterator[TranscriptChunk]:
        """
        Stream transcription for live audio.
        Override in providers that support streaming.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Language code

        Yields:
            TranscriptChunk objects
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support streaming transcription"
        )

    def test_connection(self) -> bool:
        """Test if the provider connection works."""
        try:
            # Try transcribing a tiny silent audio
            silence = b'\x00' * 1000
            self.transcribe(silence, language="en", audio_format="wav")
            return True
        except Exception:
            return False
