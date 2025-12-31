"""
Rewrite Service for AI Writing Assistant

Provides text rewriting, expansion, and summarization.
"""

import logging
from typing import Optional, Dict, Any, List

from llm.litellm_client import LiteLLMClient
from .prompts import (
    REWRITE_SYSTEM_PROMPT,
    REWRITE_STYLE_INSTRUCTIONS,
    REWRITE_USER_PROMPT,
    SUMMARIZE_SYSTEM_PROMPT,
    ABSTRACT_SYSTEM_PROMPT,
    TITLE_SYSTEM_PROMPT,
    FIX_LATEX_SYSTEM_PROMPT
)

logger = logging.getLogger(__name__)


class RewriteService:
    """Service for text rewriting and transformation."""

    VALID_STYLES = ['academic', 'concise', 'expanded', 'simplified']
    DEFAULT_TEMPERATURE = 0.5
    DEFAULT_MAX_TOKENS = 500

    def __init__(self, model: Optional[str] = None):
        """
        Initialize rewrite service.

        Args:
            model: Optional model override
        """
        self.llm_client = LiteLLMClient(model=model)

    def rewrite(
        self,
        text: str,
        style: str = 'academic',
        context: str = "",
        preserve_meaning: bool = True,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE
    ) -> Dict[str, Any]:
        """
        Rewrite text in the specified style.

        Args:
            text: Text to rewrite
            style: Target style (academic, concise, expanded, simplified)
            context: Surrounding context for consistency
            preserve_meaning: Whether to preserve original meaning
            max_tokens: Maximum tokens for output
            temperature: Sampling temperature

        Returns:
            Dict with result and detected changes
        """
        try:
            if style not in self.VALID_STYLES:
                style = 'academic'

            style_instruction = REWRITE_STYLE_INSTRUCTIONS.get(style, '')

            messages = [
                {"role": "system", "content": REWRITE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": REWRITE_USER_PROMPT.format(
                        style_instruction=style_instruction,
                        text=text,
                        context=context[:500] if context else "(kein Kontext)"
                    )
                }
            ]

            result = self.llm_client.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            if not result:
                return {
                    "result": text,
                    "changes": [],
                    "error": "No response from LLM"
                }

            # Detect changes (simplified - could use diff library)
            changes = self._detect_changes(text, result)

            return {
                "result": result.strip(),
                "changes": changes
            }

        except Exception as e:
            logger.error(f"[RewriteService] Error rewriting: {e}")
            return {
                "result": text,
                "changes": [],
                "error": str(e)
            }

    def expand(
        self,
        text: str,
        context: str = "",
        max_tokens: int = 800
    ) -> Dict[str, Any]:
        """
        Expand text with more details.

        Args:
            text: Text to expand
            context: Surrounding context
            max_tokens: Maximum tokens

        Returns:
            Dict with expanded result
        """
        return self.rewrite(
            text=text,
            style='expanded',
            context=context,
            max_tokens=max_tokens,
            temperature=0.6
        )

    def summarize(
        self,
        text: str,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Summarize text.

        Args:
            text: Text to summarize
            max_tokens: Maximum tokens

        Returns:
            Dict with summarized result
        """
        try:
            messages = [
                {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
                {"role": "user", "content": text}
            ]

            result = self.llm_client.complete(
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens
            )

            return {
                "result": result.strip() if result else "",
                "original_length": len(text),
                "summary_length": len(result) if result else 0
            }

        except Exception as e:
            logger.error(f"[RewriteService] Error summarizing: {e}")
            return {"result": "", "error": str(e)}

    def generate_abstract(
        self,
        document_content: str,
        max_tokens: int = 400
    ) -> Dict[str, Any]:
        """
        Generate an abstract for a document.

        Args:
            document_content: Full document content
            max_tokens: Maximum tokens

        Returns:
            Dict with generated abstract
        """
        try:
            # Truncate if too long
            content = document_content[:8000]

            messages = [
                {"role": "system", "content": ABSTRACT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Dokument:\n{content}"}
            ]

            result = self.llm_client.complete(
                messages=messages,
                temperature=0.4,
                max_tokens=max_tokens
            )

            return {
                "abstract": result.strip() if result else "",
                "word_count": len(result.split()) if result else 0
            }

        except Exception as e:
            logger.error(f"[RewriteService] Error generating abstract: {e}")
            return {"abstract": "", "error": str(e)}

    def suggest_titles(
        self,
        document_content: str,
        num_suggestions: int = 5
    ) -> Dict[str, Any]:
        """
        Suggest titles for a document.

        Args:
            document_content: Full document content
            num_suggestions: Number of title suggestions

        Returns:
            Dict with suggested titles
        """
        try:
            # Truncate if too long
            content = document_content[:6000]

            messages = [
                {"role": "system", "content": TITLE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Dokument:\n{content}"}
            ]

            result = self.llm_client.complete(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            if not result:
                return {"titles": [], "error": "No response"}

            # Parse numbered list
            titles = []
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering
                    title = line.lstrip('0123456789.-) ').strip()
                    if title:
                        titles.append(title)

            return {
                "titles": titles[:num_suggestions]
            }

        except Exception as e:
            logger.error(f"[RewriteService] Error suggesting titles: {e}")
            return {"titles": [], "error": str(e)}

    def fix_latex(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Analyze and fix LaTeX errors.

        Args:
            content: LaTeX content to fix

        Returns:
            Dict with errors and suggestions
        """
        try:
            messages = [
                {"role": "system", "content": FIX_LATEX_SYSTEM_PROMPT},
                {"role": "user", "content": content}
            ]

            result = self.llm_client.complete(
                messages=messages,
                temperature=0.2,
                max_tokens=1000
            )

            if not result:
                return {"errors": [], "suggestions": []}

            # Try to parse JSON response
            import json
            try:
                # Find JSON in response
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    data = json.loads(result[json_start:json_end])
                    return {
                        "errors": data.get("errors", []),
                        "suggestions": data.get("suggestions", [])
                    }
            except json.JSONDecodeError:
                pass

            # Fallback: return as suggestion
            return {
                "errors": [],
                "suggestions": [result]
            }

        except Exception as e:
            logger.error(f"[RewriteService] Error fixing LaTeX: {e}")
            return {"errors": [], "suggestions": [], "error": str(e)}

    def _detect_changes(
        self,
        original: str,
        rewritten: str
    ) -> List[Dict[str, str]]:
        """
        Detect changes between original and rewritten text.

        Args:
            original: Original text
            rewritten: Rewritten text

        Returns:
            List of detected changes
        """
        # Simplified change detection
        # In production, use difflib or similar
        if original.strip() != rewritten.strip():
            return [{
                "type": "replaced",
                "original": original,
                "new": rewritten
            }]
        return []


# Singleton instance
_rewrite_service: Optional[RewriteService] = None


def get_rewrite_service() -> RewriteService:
    """Get or create singleton RewriteService instance."""
    global _rewrite_service
    if _rewrite_service is None:
        _rewrite_service = RewriteService()
    return _rewrite_service
