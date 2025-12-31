"""
Completion Service for AI Writing Assistant

Provides ghost text completion functionality for the editor.
"""

import logging
from typing import Optional, List, Dict, Any

from llm.litellm_client import LiteLLMClient
from .prompts import COMPLETION_SYSTEM_PROMPT, COMPLETION_USER_PROMPT

logger = logging.getLogger(__name__)


class CompletionService:
    """Service for generating text completions (ghost text)."""

    # Default settings
    DEFAULT_MAX_TOKENS = 100
    DEFAULT_TEMPERATURE = 0.3
    MAX_CONTEXT_LENGTH = 2000  # Characters before/after cursor

    def __init__(self, model: Optional[str] = None):
        """
        Initialize completion service.

        Args:
            model: Optional model override
        """
        self.llm_client = LiteLLMClient(model=model)

    def complete(
        self,
        context: str,
        cursor_position: int,
        document_type: str = "latex",
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> Dict[str, Any]:
        """
        Generate a text completion at the cursor position.

        Args:
            context: Text around the cursor (before + after)
            cursor_position: Position of cursor within context
            document_type: "latex" or "markdown"
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with completion, confidence, and alternatives
        """
        try:
            # Insert cursor marker
            context_with_cursor = (
                context[:cursor_position] +
                "[CURSOR]" +
                context[cursor_position:]
            )

            # Build messages
            messages = [
                {"role": "system", "content": COMPLETION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": COMPLETION_USER_PROMPT.format(context=context_with_cursor)
                }
            ]

            # Generate completion
            completion = self.llm_client.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not completion:
                return {
                    "completion": "",
                    "confidence": 0.0,
                    "alternatives": []
                }

            # Clean up completion (remove quotes, etc.)
            completion = self._clean_completion(completion)

            return {
                "completion": completion,
                "confidence": 0.8,  # Could be enhanced with actual confidence scoring
                "alternatives": []  # Could generate multiple alternatives
            }

        except Exception as e:
            logger.error(f"[CompletionService] Error generating completion: {e}")
            return {
                "completion": "",
                "confidence": 0.0,
                "alternatives": [],
                "error": str(e)
            }

    def complete_multiple(
        self,
        context: str,
        cursor_position: int,
        num_alternatives: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate multiple completion alternatives.

        Args:
            context: Text around cursor
            cursor_position: Cursor position in context
            num_alternatives: Number of alternatives to generate
            **kwargs: Additional arguments for complete()

        Returns:
            Dict with primary completion and alternatives
        """
        # Generate primary completion
        result = self.complete(context, cursor_position, **kwargs)

        if num_alternatives <= 1:
            return result

        # Generate alternatives with higher temperature
        alternatives = []
        for i in range(num_alternatives - 1):
            alt_result = self.complete(
                context,
                cursor_position,
                temperature=kwargs.get('temperature', 0.3) + 0.2 * (i + 1),
                **{k: v for k, v in kwargs.items() if k != 'temperature'}
            )
            if alt_result.get('completion'):
                alternatives.append(alt_result['completion'])

        result['alternatives'] = alternatives
        return result

    def _clean_completion(self, text: str) -> str:
        """
        Clean up completion text.

        Args:
            text: Raw completion from LLM

        Returns:
            Cleaned completion text
        """
        # Remove surrounding quotes
        text = text.strip()
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]

        # Remove any instruction text that might have leaked
        prefixes_to_remove = [
            "Vervollständigung:",
            "Completion:",
            "Hier ist die Vervollständigung:",
            "Der Text wird wie folgt fortgesetzt:",
        ]
        for prefix in prefixes_to_remove:
            if text.lower().startswith(prefix.lower()):
                text = text[len(prefix):].strip()

        return text


# Singleton instance
_completion_service: Optional[CompletionService] = None


def get_completion_service() -> CompletionService:
    """Get or create singleton CompletionService instance."""
    global _completion_service
    if _completion_service is None:
        _completion_service = CompletionService()
    return _completion_service
