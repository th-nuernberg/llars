# chat_title_service.py
"""
Service for generating and managing chat conversation titles.
Supports LLM-based smart title generation with streaming.
"""

import re
import logging
from typing import Optional, Callable

from llm.openai_utils import extract_delta_text, extract_message_text
from services.llm.llm_client_factory import LLMClientFactory
from db.models.llm_model import LLMModel

logger = logging.getLogger(__name__)


class ChatTitleService:
    """Service for generating and managing conversation titles."""

    _TOKEN_RE = re.compile(r"[\wäöüÄÖÜß]+", re.UNICODE)
    _PLACEHOLDER_TITLES = {"neuer chat", "new chat"}
    _TITLE_MAX_CHARS = 50
    _TITLE_MAX_WORDS = 8

    @classmethod
    def normalize_title(cls, title: Optional[str]) -> str:
        """Normalize a title for comparison (lowercase, trimmed, collapsed whitespace)."""
        return re.sub(r"\s+", " ", str(title or "")).strip().lower()

    @classmethod
    def is_placeholder_title(cls, title: Optional[str]) -> bool:
        """Check if a title is a placeholder (empty or default)."""
        normalized = cls.normalize_title(title)
        if not normalized:
            return True
        return normalized in cls._PLACEHOLDER_TITLES

    @classmethod
    def build_title_from_message(cls, message: Optional[str]) -> Optional[str]:
        """
        Build a simple title from the first line of a message.
        Truncates to max words/chars and adds ellipsis if needed.
        """
        text = str(message or "").strip()
        if not text:
            return None
        first_line = text.splitlines()[0].strip()
        if not first_line:
            return None
        collapsed = re.sub(r"\s+", " ", first_line)
        words = collapsed.split(" ")
        title = " ".join(words[:cls._TITLE_MAX_WORDS])
        truncated_by_words = len(words) > cls._TITLE_MAX_WORDS
        truncated_by_chars = len(title) > cls._TITLE_MAX_CHARS
        if truncated_by_chars:
            title = title[:cls._TITLE_MAX_CHARS]
        if truncated_by_words or truncated_by_chars:
            title = title.rstrip(" .,:;!?-")
            max_len = cls._TITLE_MAX_CHARS - 3
            if max_len > 0 and len(title) > max_len:
                title = title[:max_len].rstrip(" .,:;!?-")
            title = f"{title}..."
        return title

    @classmethod
    def generate_smart_title(
        cls,
        message: Optional[str],
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[str]:
        """
        Generate an intelligent short title using LLM.
        Falls back to simple truncation on error.

        Args:
            message: User message to generate title from
            stream_callback: Optional callback function(delta: str) for streaming title chars

        Returns:
            Generated title or None
        """
        text = str(message or "").strip()
        if not text:
            return None

        try:
            # Always use fast model for title generation
            model = 'LiteLLM/mistralai/Mistral-Small-3.2-24B-Instruct-2506'
            if not LLMModel.get_by_model_id(model):
                default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
                if default_model_id:
                    model = default_model_id
            client, effective_model = LLMClientFactory.resolve_client_and_model_id(model)

            messages = [
                {
                    "role": "system",
                    "content": "Generiere einen sehr kurzen Titel (2-4 Wörter) für diese Chat-Anfrage. "
                               "Antworte NUR mit dem Titel, keine Anführungszeichen, keine Erklärung. "
                               "Beispiele: Öffnungszeiten, Kontaktdaten, Preisanfrage, Technischer Support, Firmeninhaber"
                },
                {
                    "role": "user",
                    "content": text[:500]  # Limit input length
                }
            ]

            logger.debug(f"Generating title with model: {model}")

            # Stream if callback provided
            if stream_callback:
                title = ""
                stream = client.chat.completions.create(
                    model=effective_model,
                    messages=messages,
                    max_tokens=20,
                    temperature=0.3,
                    timeout=10.0,
                    stream=True
                )
                for chunk in stream:
                    choice = chunk.choices[0] if chunk.choices else None
                    delta = getattr(choice, "delta", None) if choice else None
                    delta_text = extract_delta_text(delta)
                    if delta_text:
                        title += delta_text
                        stream_callback(delta_text)
            else:
                response = client.chat.completions.create(
                    model=effective_model,
                    messages=messages,
                    max_tokens=20,
                    temperature=0.3,
                    timeout=10.0
                )
                title = extract_message_text(response.choices[0].message).strip()

            # Clean up: remove quotes, limit length
            title = title.strip('"\'„"»«')
            title = re.sub(r'[.!?:;,]+$', '', title)
            if len(title) > cls._TITLE_MAX_CHARS:
                title = title[:cls._TITLE_MAX_CHARS - 3].rstrip(" .,:;!?-") + "..."

            if title:
                logger.info(f"Generated smart title: '{title}' for message: '{text[:50]}...'")
                return title
            else:
                logger.warning(f"Smart title generation returned empty result, using fallback for: '{text[:50]}...'")

        except Exception as e:
            logger.warning(f"Smart title generation failed, using fallback: {e}")

        # Fallback to simple title extraction
        return cls.build_title_from_message(message)

    @classmethod
    def maybe_update_conversation_title(
        cls,
        conversation,
        message: Optional[str],
        stream_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """
        Update conversation title if it's a placeholder.

        Args:
            conversation: ChatbotConversation object
            message: User message to generate title from
            stream_callback: Optional callback for streaming title generation

        Returns:
            True if title was updated, False otherwise
        """
        if not cls.is_placeholder_title(conversation.title):
            return False
        title = cls.generate_smart_title(message, stream_callback)
        if not title:
            return False
        conversation.title = title
        return True
