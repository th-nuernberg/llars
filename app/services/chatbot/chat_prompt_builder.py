# chat_prompt_builder.py
"""
Service for building chat prompts, RAG context formatting, and citation instructions.
"""

from typing import List, Dict, Any, Optional

from db.models.chatbot import (
    DEFAULT_RAG_CITATION_INSTRUCTIONS,
    DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE,
    DEFAULT_RAG_CONTEXT_PREFIX,
    DEFAULT_RAG_UNKNOWN_ANSWER,
)


class ChatPromptBuilder:
    """Builder for chat prompts with RAG context and citation support."""

    def __init__(self, chatbot):
        """
        Initialize the prompt builder.

        Args:
            chatbot: Chatbot model instance
        """
        self.chatbot = chatbot

    def _get_prompt_settings(self):
        """Get prompt settings from chatbot."""
        return getattr(self.chatbot, 'prompt_settings', None)

    def get_unknown_answer(self) -> str:
        """Get the configured 'unknown answer' response for RAG."""
        settings = self._get_prompt_settings()
        unknown = getattr(settings, 'rag_unknown_answer', None) if settings else None
        if unknown is None or str(unknown).strip() == "":
            return DEFAULT_RAG_UNKNOWN_ANSWER
        return str(unknown)

    def requires_sources(self) -> bool:
        """Check if the chatbot requires RAG sources for responses."""
        if not (self.chatbot.rag_enabled and self.chatbot.collections):
            return False
        settings = self._get_prompt_settings()
        require_citations = bool(getattr(settings, 'rag_require_citations', True))
        if not require_citations:
            return False
        # Allow the default LLARS assistant to answer system questions without RAG sources.
        if self.chatbot.name == 'standard_admin':
            return False
        return True

    def build_citation_instructions(self) -> str:
        """Build citation instructions to append to system prompt."""
        settings = self._get_prompt_settings()
        template = getattr(settings, 'rag_citation_instructions', None) if settings else None
        if template is None or str(template).strip() == "":
            template = DEFAULT_RAG_CITATION_INSTRUCTIONS

        unknown_answer = self.get_unknown_answer()
        rendered = (
            str(template)
            .replace("{{UNKNOWN_ANSWER}}", unknown_answer)
            .replace("{UNKNOWN_ANSWER}", unknown_answer)
        )

        return "\n\n" + rendered.strip() + "\n"

    def build_numbered_context(self, sources: List[Dict[str, Any]]) -> str:
        """
        Build numbered context string from sources for LLM consumption.

        Args:
            sources: List of source dicts with footnote_id, title, excerpt, etc.

        Returns:
            Formatted context string with numbered sources
        """
        if not sources:
            return ""

        settings = self._get_prompt_settings()
        prefix = getattr(settings, 'rag_context_prefix', None) if settings else None
        item_template = getattr(settings, 'rag_context_item_template', None) if settings else None

        if prefix is None or str(prefix).strip() == "":
            prefix = DEFAULT_RAG_CONTEXT_PREFIX
        if item_template is None or str(item_template).strip() == "":
            item_template = DEFAULT_RAG_CONTEXT_ITEM_TEMPLATE

        parts = [f"{str(prefix).strip()}\n"]
        for idx, source in enumerate(sources):
            footnote_id = source.get("footnote_id") or (idx + 1)
            title = source.get("title") or source.get("filename") or "Unbekannt"
            excerpt = source.get("excerpt") or ""

            mapping = {
                "id": footnote_id,
                "title": title,
                "filename": source.get("filename") or "",
                "collection_name": source.get("collection_name") or "",
                "page_number": source.get("page_number") or "",
                "chunk_index": source.get("chunk_index") if source.get("chunk_index") is not None else "",
                "relevance": source.get("relevance") if source.get("relevance") is not None else "",
                "document_id": source.get("document_id") or "",
                "url": source.get("url") or "",
                "excerpt": excerpt,
            }

            parts.append(self._render_placeholders(str(item_template), mapping).strip())
            parts.append("")  # spacing

        return "\n".join(parts).strip()

    @staticmethod
    def _render_placeholders(template: str, mapping: Dict[str, Any]) -> str:
        """Render template placeholders with values from mapping."""
        rendered = template or ""
        # Convert literal \n to actual newlines (from DB storage)
        rendered = rendered.replace('\\n', '\n')
        for key, value in mapping.items():
            placeholder = f"{{{{{key}}}}}"
            rendered = rendered.replace(placeholder, "" if value is None else str(value))
        return rendered

    def get_require_citations(self) -> bool:
        """Check if citations are required for this chatbot."""
        settings = self._get_prompt_settings()
        return bool(getattr(settings, 'rag_require_citations', True))
