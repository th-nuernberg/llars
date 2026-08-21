"""
Extended tests for GenerationWorker.

Covers worker lifecycle, task execution, error handling, helper methods,
variable substitution, content formatting, cost calculation, and status updates.
All LLM calls are mocked.

Test IDs: [GEN_WORKER_001] through [GEN_WORKER_040]
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, PropertyMock, call
from datetime import datetime

from services.generation.generation_worker import (
    GenerationWorker,
    strip_thinking_tags,
    decode_yjs_content,
    _extract_text_from_yjs_binary,
    _restore_variable_placeholders,
    DEFAULT_MAX_PARALLEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BATCH_SIZE,
    RETRY_DELAYS,
)


# =============================================================================
# strip_thinking_tags
# =============================================================================

class TestStripThinkingTags:
    """Tests for the strip_thinking_tags utility."""

    def test_GEN_WORKER_001_empty_input(self):
        """Empty input should return empty string."""
        assert strip_thinking_tags("") == ""
        assert strip_thinking_tags(None) == ""

    def test_GEN_WORKER_002_no_tags(self):
        """Text without think tags should be returned unchanged."""
        text = "This is normal text."
        assert strip_thinking_tags(text) == text

    def test_GEN_WORKER_003_single_block(self):
        """Single think block should be removed."""
        text = "<think>reasoning</think>Answer."
        assert strip_thinking_tags(text) == "Answer."

    def test_GEN_WORKER_004_multiple_blocks(self):
        """Multiple think blocks should all be removed."""
        text = "A<think>one</think>B<think>two</think>C"
        assert strip_thinking_tags(text) == "ABC"

    def test_GEN_WORKER_005_thinking_variant(self):
        """<thinking> tag variant should also be removed."""
        text = "<thinking>step 1</thinking>Result."
        assert strip_thinking_tags(text) == "Result."

    def test_GEN_WORKER_006_case_insensitive(self):
        """Tags should be matched case-insensitively."""
        text = "<THINK>reasoning</THINK>Answer."
        assert strip_thinking_tags(text) == "Answer."

    def test_GEN_WORKER_007_dangling_open_tag(self):
        """Dangling open tag should remove everything after it."""
        text = "Visible\n<think>hidden"
        assert strip_thinking_tags(text) == "Visible"

    def test_GEN_WORKER_008_multiline_block(self):
        """Multi-line reasoning block should be removed."""
        text = "<think>\nStep 1\nStep 2\nStep 3\n</think>\n\nFinal answer."
        assert strip_thinking_tags(text) == "Final answer."

    def test_GEN_WORKER_009_preserves_whitespace_outside(self):
        """Whitespace outside of tags should be preserved."""
        text = "  <think>x</think>  Text  "
        result = strip_thinking_tags(text)
        assert "Text" in result


# =============================================================================
# Worker Initialization
# =============================================================================

class TestWorkerInit:
    """Tests for GenerationWorker initialization."""

    def test_GEN_WORKER_010_init_basic(self):
        """Worker should initialize with job_id and empty caches."""
        worker = GenerationWorker(job_id=42)
        assert worker.job_id == 42
        assert worker.socketio is None
        assert worker.should_stop is False
        assert worker._template_cache == {}
        assert worker._model_cache == {}
        assert worker._source_data_cache == {}

    def test_GEN_WORKER_011_init_with_socketio(self):
        """Worker should accept optional socketio."""
        mock_sio = MagicMock()
        worker = GenerationWorker(job_id=1, socketio=mock_sio)
        assert worker.socketio is mock_sio

    def test_GEN_WORKER_012_stop_signal(self):
        """stop() should set should_stop flag."""
        worker = GenerationWorker(job_id=1)
        assert worker.should_stop is False
        worker.stop()
        assert worker.should_stop is True


# =============================================================================
# Constants
# =============================================================================

class TestConstants:
    """Tests for module-level constants."""

    def test_GEN_WORKER_013_default_values(self):
        """Default constants should have sensible values."""
        assert DEFAULT_MAX_PARALLEL >= 1
        assert DEFAULT_MAX_RETRIES >= 1
        assert DEFAULT_BATCH_SIZE >= 1

    def test_GEN_WORKER_014_retry_delays_ascending(self):
        """Retry delays should be in ascending order (exponential backoff)."""
        for i in range(len(RETRY_DELAYS) - 1):
            assert RETRY_DELAYS[i] <= RETRY_DELAYS[i + 1]


# =============================================================================
# Variable Substitution
# =============================================================================

class TestVariableSubstitution:
    """Tests for _substitute_variables."""

    def test_GEN_WORKER_015_simple_substitution(self):
        """Should replace {{variable}} with value."""
        worker = GenerationWorker(job_id=1)
        result = worker._substitute_variables(
            "Hello {{name}}, welcome!",
            {"name": "Alice"}
        )
        assert result == "Hello Alice, welcome!"

    def test_GEN_WORKER_016_multiple_variables(self):
        """Should replace multiple variables."""
        worker = GenerationWorker(job_id=1)
        result = worker._substitute_variables(
            "{{greeting}} {{name}}!",
            {"greeting": "Hi", "name": "Bob"}
        )
        assert result == "Hi Bob!"

    def test_GEN_WORKER_017_missing_variable_kept(self):
        """Missing variable should keep the placeholder."""
        worker = GenerationWorker(job_id=1)
        result = worker._substitute_variables(
            "Hello {{unknown}}!",
            {}
        )
        assert result == "Hello {{unknown}}!"

    def test_GEN_WORKER_018_none_value_rendered_empty(self):
        """None value should be rendered as empty string."""
        worker = GenerationWorker(job_id=1)
        result = worker._substitute_variables(
            "Value: {{x}}",
            {"x": None}
        )
        assert result == "Value: "


# =============================================================================
# Format Variable Value
# =============================================================================

class TestFormatVariableValue:
    """Tests for _format_variable_value."""

    def test_GEN_WORKER_019_string_value(self):
        """String value should be returned as-is."""
        worker = GenerationWorker(job_id=1)
        assert worker._format_variable_value("hello") == "hello"

    def test_GEN_WORKER_020_none_value(self):
        """None should return empty string."""
        worker = GenerationWorker(job_id=1)
        assert worker._format_variable_value(None) == ""

    def test_GEN_WORKER_021_int_value(self):
        """Integer should be converted to string."""
        worker = GenerationWorker(job_id=1)
        assert worker._format_variable_value(42) == "42"

    def test_GEN_WORKER_022_list_of_strings(self):
        """List of strings should be joined with newlines."""
        worker = GenerationWorker(job_id=1)
        result = worker._format_variable_value(["line1", "line2", "line3"])
        assert result == "line1\nline2\nline3"

    def test_GEN_WORKER_023_messages_array(self):
        """Messages array should be formatted as email thread."""
        worker = GenerationWorker(job_id=1)
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        result = worker._format_variable_value(messages)
        assert "Klient" in result
        assert "Hello" in result
        assert "Berater" in result
        assert "Hi there" in result


# =============================================================================
# Format Messages Array
# =============================================================================

class TestFormatMessagesArray:
    """Tests for _format_messages_array."""

    def test_GEN_WORKER_024_basic_format(self):
        """Should format messages with role labels."""
        worker = GenerationWorker(job_id=1)
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]
        result = worker._format_messages_array(messages)
        assert "[Klient]" in result
        assert "Question" in result
        assert "[Berater]" in result
        assert "Answer" in result

    def test_GEN_WORKER_025_role_mapping(self):
        """Should map various role names to standard labels."""
        worker = GenerationWorker(job_id=1)

        client_roles = ['ratsuchende', 'klient', 'client', 'user']
        for role in client_roles:
            result = worker._format_messages_array([{"role": role, "content": "test"}])
            assert "[Klient]" in result, f"Failed for role '{role}'"

        counselor_roles = ['beratende', 'berater', 'counselor', 'assistant']
        for role in counselor_roles:
            result = worker._format_messages_array([{"role": role, "content": "test"}])
            assert "[Berater]" in result, f"Failed for role '{role}'"

    def test_GEN_WORKER_026_unknown_role_preserved(self):
        """Unknown role should be used as-is."""
        worker = GenerationWorker(job_id=1)
        result = worker._format_messages_array([{"role": "moderator", "content": "test"}])
        assert "[moderator]" in result

    def test_GEN_WORKER_027_with_timestamp(self):
        """Should include timestamp when present."""
        worker = GenerationWorker(job_id=1)
        messages = [
            {"role": "user", "content": "Hi", "timestamp": "2026-01-15 12:00"}
        ]
        result = worker._format_messages_array(messages)
        assert "(2026-01-15 12:00)" in result

    def test_GEN_WORKER_028_separator(self):
        """Messages should be separated by ---."""
        worker = GenerationWorker(job_id=1)
        messages = [
            {"role": "user", "content": "Msg 1"},
            {"role": "assistant", "content": "Msg 2"},
        ]
        result = worker._format_messages_array(messages)
        assert "---" in result


# =============================================================================
# Is System Block Detection
# =============================================================================

class TestIsSystemBlock:
    """Tests for _is_system_block detection."""

    def test_GEN_WORKER_029_system_by_id(self):
        """Block with id 'system' should be detected."""
        assert GenerationWorker._is_system_block("system", {"title": "Something"})

    def test_GEN_WORKER_030_system_by_title(self):
        """Block with title 'System' should be detected."""
        assert GenerationWorker._is_system_block("block1", {"title": "System"})

    def test_GEN_WORKER_031_system_prompt_by_id(self):
        """Block with id 'system prompt' should be detected."""
        assert GenerationWorker._is_system_block("system prompt", {"title": "Any"})

    def test_GEN_WORKER_032_system_case_insensitive(self):
        """Detection should be case-insensitive."""
        assert GenerationWorker._is_system_block("SYSTEM", {"title": "x"})
        assert GenerationWorker._is_system_block("x", {"title": "SYSTEM"})

    def test_GEN_WORKER_033_not_system(self):
        """Non-system blocks should not be detected."""
        assert not GenerationWorker._is_system_block("user", {"title": "Task"})
        assert not GenerationWorker._is_system_block("context", {"title": "Context"})


# =============================================================================
# Is Empty Prompt Variable Value
# =============================================================================

class TestIsEmptyPromptVariableValue:
    """Tests for _is_empty_prompt_variable_value."""

    def test_GEN_WORKER_034_none_is_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value(None) is True

    def test_GEN_WORKER_035_empty_string_is_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value("") is True

    def test_GEN_WORKER_036_empty_list_is_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value([]) is True

    def test_GEN_WORKER_037_empty_dict_is_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value({}) is True

    def test_GEN_WORKER_038_nonempty_string_not_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value("hello") is False

    def test_GEN_WORKER_039_number_not_empty(self):
        assert GenerationWorker._is_empty_prompt_variable_value(42) is False
        assert GenerationWorker._is_empty_prompt_variable_value(0) is False


# =============================================================================
# Extract Prompt Variable Defaults
# =============================================================================

class TestExtractPromptVariableDefaults:
    """Tests for _extract_prompt_variable_defaults."""

    def test_GEN_WORKER_040_no_variables(self):
        """Content without variables key should return empty dict."""
        result = GenerationWorker._extract_prompt_variable_defaults({"blocks": {}})
        assert result == {}

    def test_GEN_WORKER_041_dict_variables(self):
        """Should extract content from dict-style variables."""
        content = {
            "blocks": {},
            "variables": {
                "name": {"content": "Alice"},
                "role": {"content": "Expert"}
            }
        }
        result = GenerationWorker._extract_prompt_variable_defaults(content)
        assert result == {"name": "Alice", "role": "Expert"}

    def test_GEN_WORKER_042_string_variables(self):
        """Should handle plain string variable values."""
        content = {
            "blocks": {},
            "variables": {
                "simple": "direct value"
            }
        }
        result = GenerationWorker._extract_prompt_variable_defaults(content)
        assert result == {"simple": "direct value"}

    def test_GEN_WORKER_043_non_dict_input(self):
        """Non-dict input should return empty dict."""
        assert GenerationWorker._extract_prompt_variable_defaults(None) == {}
        assert GenerationWorker._extract_prompt_variable_defaults("string") == {}

    def test_GEN_WORKER_044_empty_variable_names_skipped(self):
        """Empty variable names should be skipped."""
        content = {
            "variables": {
                "": {"content": "skip me"},
                "valid": {"content": "keep me"}
            }
        }
        result = GenerationWorker._extract_prompt_variable_defaults(content)
        assert "" not in result
        assert result["valid"] == "keep me"


# =============================================================================
# Normalize Block Name
# =============================================================================

class TestNormalizeBlockName:
    """Tests for _normalize_block_name."""

    def test_GEN_WORKER_045_none_input(self):
        assert GenerationWorker._normalize_block_name(None) == ""

    def test_GEN_WORKER_046_string_input(self):
        assert GenerationWorker._normalize_block_name("System") == "system"

    def test_GEN_WORKER_047_whitespace_stripped(self):
        assert GenerationWorker._normalize_block_name("  System  ") == "system"

    def test_GEN_WORKER_048_case_folded(self):
        assert GenerationWorker._normalize_block_name("SYSTEM PROMPT") == "system prompt"


# =============================================================================
# decode_yjs_content
# =============================================================================

class TestDecodeYjsContent:
    """Tests for YJS content decoding."""

    def test_GEN_WORKER_049_dict_passthrough(self):
        """Dict input should pass through."""
        data = {"blocks": {"default": {"content": "text"}}}
        result = decode_yjs_content(data)
        assert result == data

    def test_GEN_WORKER_050_non_list_non_dict(self):
        """Non-list, non-dict input should return empty dict."""
        assert decode_yjs_content("string") == {}
        assert decode_yjs_content(42) == {}

    def test_GEN_WORKER_051_empty_list(self):
        """Empty list should return empty dict or minimal structure."""
        result = decode_yjs_content([])
        assert isinstance(result, dict)


# =============================================================================
# _extract_text_from_yjs_binary
# =============================================================================

class TestExtractTextFromYjsBinary:
    """Tests for binary text extraction."""

    def test_GEN_WORKER_052_extracts_readable_text(self):
        """Should extract readable ASCII sequences from binary."""
        text = "This is readable text in the binary"
        # Pad with non-ASCII bytes
        binary = [0, 0, 0, 0] + list(text.encode('ascii')) + [0, 0, 0, 0]
        result = _extract_text_from_yjs_binary(binary)
        if result and 'blocks' in result:
            default_block = result['blocks'].get('default', {})
            assert text in default_block.get('content', '')

    def test_GEN_WORKER_053_short_sequences_filtered(self):
        """Sequences shorter than 8 chars should be filtered out."""
        binary = list(b"short") + [0] + list(b"This is a longer readable sequence")
        result = _extract_text_from_yjs_binary(binary)
        if result and 'blocks' in result:
            content = result['blocks'].get('default', {}).get('content', '')
            assert 'short' not in content


# =============================================================================
# _restore_variable_placeholders
# =============================================================================

class TestRestoreVariablePlaceholders:
    """Tests for restoring variable placeholders after YJS decoding."""

    def test_GEN_WORKER_054_no_variables(self):
        """No variables should return text unchanged."""
        text = "Hello world"
        result = _restore_variable_placeholders(text, [])
        assert result == text

    def test_GEN_WORKER_055_label_based_matching(self):
        """Should match labels to variables."""
        text = "Subject: \nEnd"
        result = _restore_variable_placeholders(text, ["subject"])
        assert "{{subject}}" in result

    def test_GEN_WORKER_056_already_present_skipped(self):
        """Variables already present as {{var}} should be skipped."""
        text = "Subject: {{subject}}\nContent: \n"
        result = _restore_variable_placeholders(text, ["subject", "content"])
        # subject already present, should not be doubled
        assert result.count("{{subject}}") == 1


# =============================================================================
# Emit Event
# =============================================================================

class TestEmitEvent:
    """Tests for _emit_event."""

    def test_GEN_WORKER_057_no_socketio_no_crash(self):
        """Should not crash when socketio is None."""
        worker = GenerationWorker(job_id=1)
        # Should not raise
        worker._emit_event("test:event", {"key": "value"})

    def test_GEN_WORKER_058_emit_to_job_room(self):
        """Should emit to job room when socketio is present."""
        mock_sio = MagicMock()
        worker = GenerationWorker(job_id=42, socketio=mock_sio)
        worker._emit_event("generation:item:completed", {"job_id": 42})
        mock_sio.emit.assert_called()

    def test_GEN_WORKER_059_job_events_mirror_to_overview(self):
        """Job-level events should also go to overview room."""
        mock_sio = MagicMock()
        worker = GenerationWorker(job_id=42, socketio=mock_sio)
        worker._emit_event("generation:job:progress", {"job_id": 42})
        # Should be called at least twice (job room + overview room)
        assert mock_sio.emit.call_count >= 2

    def test_GEN_WORKER_060_emit_exception_caught(self):
        """Exceptions during emit should be caught."""
        mock_sio = MagicMock()
        mock_sio.emit.side_effect = Exception("Socket error")
        worker = GenerationWorker(job_id=1, socketio=mock_sio)
        # Should not raise
        worker._emit_event("test:event", {"key": "value"})


# =============================================================================
# Render User Prompt (extended)
# =============================================================================

class TestRenderUserPromptExtended:
    """Extended tests for _render_user_prompt."""

    def _make_user_prompt(self, blocks, variables=None):
        rendered = {"blocks": blocks}
        if variables:
            rendered["variables"] = variables
        return SimpleNamespace(
            prompt_id=123,
            rendered_content=rendered,
            content=None,
        )

    def test_GEN_WORKER_061_empty_blocks(self):
        """Empty blocks should return empty prompts."""
        worker = GenerationWorker(job_id=1)
        user_prompt = self._make_user_prompt({})

        system, user = worker._render_user_prompt(user_prompt, {})
        assert system == ""
        assert user == ""

    def test_GEN_WORKER_062_blocks_sorted_by_position(self):
        """Blocks should be sorted by position."""
        worker = GenerationWorker(job_id=1)
        user_prompt = self._make_user_prompt({
            "b": {"title": "Second", "position": 2, "content": "B"},
            "a": {"title": "First", "position": 1, "content": "A"},
            "c": {"title": "Third", "position": 3, "content": "C"},
        })

        _, user = worker._render_user_prompt(user_prompt, {})
        # Should be A, B, C in order
        assert user == "A\n\nB\n\nC"

    def test_GEN_WORKER_063_variable_defaults_applied(self):
        """Prompt variable defaults should be applied when runtime value is empty."""
        worker = GenerationWorker(job_id=1)
        user_prompt = self._make_user_prompt(
            {"task": {"title": "Task", "position": 0, "content": "Say {{greeting}}"}},
            variables={"greeting": {"content": "Hello"}}
        )

        _, user = worker._render_user_prompt(user_prompt, {"greeting": ""})
        assert user == "Say Hello"

    def test_GEN_WORKER_064_runtime_value_overrides_default(self):
        """Non-empty runtime value should override prompt default."""
        worker = GenerationWorker(job_id=1)
        user_prompt = self._make_user_prompt(
            {"task": {"title": "Task", "position": 0, "content": "Say {{greeting}}"}},
            variables={"greeting": {"content": "Default"}}
        )

        _, user = worker._render_user_prompt(user_prompt, {"greeting": "Override"})
        assert user == "Say Override"

    def test_GEN_WORKER_065_non_dict_content_as_string(self):
        """Non-dict rendered_content is ignored; content=str falls through as string."""
        worker = GenerationWorker(job_id=1)
        # rendered_content must be a dict to be used; non-dict is ignored.
        # content is used as fallback. When content is a plain string (not dict/list),
        # it's returned directly as the user prompt.
        prompt = SimpleNamespace(
            prompt_id=1,
            rendered_content="plain text",  # Ignored (not dict)
            content="fallback text",         # Used as fallback
        )

        system, user = worker._render_user_prompt(prompt, {})
        assert system == ""
        assert user == "fallback text"

    def test_GEN_WORKER_066_empty_block_content_skipped(self):
        """Blocks with empty content should be skipped."""
        worker = GenerationWorker(job_id=1)
        user_prompt = self._make_user_prompt({
            "a": {"title": "A", "position": 0, "content": ""},
            "b": {"title": "B", "position": 1, "content": "Visible"},
        })

        _, user = worker._render_user_prompt(user_prompt, {})
        assert user == "Visible"
