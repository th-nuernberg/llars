"""
Unit tests for the chatbot citation-vs-general-knowledge branching (2026-06-13).

Goal being verified:
- relevant sources present  -> base prompt (+ citation instructions when the
  bot requires citations) so the model grounds + cites.
- no relevant sources on a RAG bot -> "general mode" instructions appended:
  answer generic questions from general knowledge WITHOUT citations, but be
  honest about LLARS-specific gaps.
- non-RAG bot, no sources -> plain base prompt (no general-mode noise).

These exercise pure prompt logic — no DB / LLM client needed.

Test IDs: CHAT-GENMODE-001..010.
"""

from __future__ import annotations

import types

from services.chatbot.chat_prompt_builder import ChatPromptBuilder
from services.chatbot.chat_service import ChatService
from db.models.chatbot import (
    DEFAULT_RAG_GENERAL_MODE_INSTRUCTIONS,
    DEFAULT_RAG_CITATION_INSTRUCTIONS,
)


def _bot(**attrs):
    """Lightweight stand-in for a Chatbot row (only the attrs we read)."""
    return types.SimpleNamespace(**attrs)


# --------------------------------------------------------------------------- #
# ChatPromptBuilder.build_general_mode_instructions
# --------------------------------------------------------------------------- #
class TestGeneralModeInstructions:
    def test_chat_genmode_001_default_when_no_settings(self):
        pb = ChatPromptBuilder(_bot(prompt_settings=None))
        out = pb.build_general_mode_instructions()
        # First line of the default text should be present.
        assert DEFAULT_RAG_GENERAL_MODE_INSTRUCTIONS.splitlines()[0] in out

    def test_chat_genmode_002_per_bot_override(self):
        settings = _bot(rag_general_mode_instructions="NUR ALLGEMEINWISSEN, KEINE QUELLEN")
        pb = ChatPromptBuilder(_bot(prompt_settings=settings))
        assert "NUR ALLGEMEINWISSEN" in pb.build_general_mode_instructions()

    def test_chat_genmode_003_blank_override_falls_back(self):
        settings = _bot(rag_general_mode_instructions="   ")
        pb = ChatPromptBuilder(_bot(prompt_settings=settings))
        assert DEFAULT_RAG_GENERAL_MODE_INSTRUCTIONS.splitlines()[0] in pb.build_general_mode_instructions()


# --------------------------------------------------------------------------- #
# ChatService._compose_system_prompt branching (called unbound with a fake self)
# --------------------------------------------------------------------------- #
class _PB:
    def __init__(self, require_citations):
        self._require = require_citations

    def get_require_citations(self):
        return self._require


class _FakeService:
    """Minimal duck-typed `self` for ChatService._compose_system_prompt."""

    def __init__(self, require_citations=True, rag_enabled=True, collections=("c",)):
        self.prompt_builder = _PB(require_citations)
        self.chatbot = _bot(rag_enabled=rag_enabled, collections=list(collections))

    def _get_system_prompt_with_urls(self):
        return "BASE_PROMPT"

    def _build_citation_instructions(self):
        return "\n[CITE]"

    def _build_general_mode_instructions(self):
        return "\n[GENERAL]"


_compose = ChatService._compose_system_prompt


class TestComposeSystemPrompt:
    def test_chat_genmode_004_sources_with_citations_required(self):
        # Guidance is always appended for RAG bots; citation formatting too.
        out = _compose(_FakeService(require_citations=True), [{"id": 1}])
        assert "[CITE]" in out
        assert "[GENERAL]" in out

    def test_chat_genmode_005_sources_without_citations_required(self):
        # No citation formatting, but guidance still present.
        out = _compose(_FakeService(require_citations=False), [{"id": 1}])
        assert "[CITE]" not in out
        assert "[GENERAL]" in out

    def test_chat_genmode_006_no_sources_rag_bot_gets_general_mode(self):
        out = _compose(_FakeService(), [])
        assert "[GENERAL]" in out
        assert "[CITE]" not in out

    def test_chat_genmode_007_no_sources_non_rag_bot_plain(self):
        out = _compose(_FakeService(rag_enabled=False, collections=()), [])
        assert out == "BASE_PROMPT"
        assert "[GENERAL]" not in out and "[CITE]" not in out

    def test_chat_genmode_008_no_sources_rag_enabled_but_no_collections_plain(self):
        # RAG flag on but no collections bound -> nothing to ground against.
        out = _compose(_FakeService(rag_enabled=True, collections=()), [])
        assert out == "BASE_PROMPT"
        assert "[GENERAL]" not in out
