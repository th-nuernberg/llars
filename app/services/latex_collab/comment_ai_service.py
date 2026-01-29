"""
LaTeX Collab Comment AI Service.

Provides AI-assisted comment resolution for LaTeX documents.
Uses LLM to analyze comments and suggest document changes.
Supports streaming for real-time token display.
"""

import logging
import threading
from dataclasses import dataclass
from typing import Optional, Tuple, Callable, Dict, Any

from db.database import db
from db.tables import LatexComment, LatexDocument
from services.llm.llm_client_factory import LLMClientFactory
from services.system_settings_service import get_setting
from llm.openai_utils import extract_message_text

logger = logging.getLogger(__name__)

# In-memory storage for active AI resolve streams (for reconnection support)
# Key: comment_id, Value: {"content": str, "status": str, "result": dict}
_active_streams: Dict[int, Dict[str, Any]] = {}
_streams_lock = threading.Lock()


@dataclass
class AIResolveResult:
    """Result of an AI comment resolution attempt."""
    success: bool
    new_text: Optional[str] = None
    old_text: Optional[str] = None
    ai_reply: Optional[str] = None
    error: Optional[str] = None


class CommentAIService:
    """Service for AI-assisted comment resolution in LaTeX Collab."""

    CONTEXT_CHARS = 1000  # Characters of context before/after the selected range

    @staticmethod
    def get_ai_settings() -> dict:
        """Get AI assistant settings from system settings."""
        return {
            'enabled': bool(get_setting('ai_assistant_enabled', True)),
            'color': get_setting('ai_assistant_color', '#9B59B6'),  # LLARS KI purple
            'username': get_setting('ai_assistant_username', 'LLARS KI'),
        }

    @staticmethod
    def resolve_comment(
        comment: LatexComment,
        document: LatexDocument,
        model_id: Optional[str] = None,
    ) -> AIResolveResult:
        """
        Use AI to resolve a comment by suggesting document changes.

        Args:
            comment: The comment to resolve
            document: The document containing the comment
            model_id: Optional specific model to use (defaults to system default)

        Returns:
            AIResolveResult with suggested changes or error
        """
        ai_settings = CommentAIService.get_ai_settings()
        if not ai_settings['enabled']:
            return AIResolveResult(
                success=False,
                error="AI assistant is disabled"
            )

        # Get document content (plain text cache)
        content = document.content_text if isinstance(document.content_text, str) else ""
        if not content and isinstance(document.content, str):
            content = document.content
        if not content:
            return AIResolveResult(
                success=False,
                error="Document has no content"
            )

        # Extract the selected text and context
        range_start = comment.range_start
        range_end = comment.range_end

        if range_start is None or range_end is None:
            return AIResolveResult(
                success=False,
                error="Comment has no text range"
            )

        # Clamp ranges to document bounds
        range_start = max(0, min(range_start, len(content)))
        range_end = max(range_start, min(range_end, len(content)))

        selected_text = content[range_start:range_end]
        if not selected_text.strip():
            return AIResolveResult(
                success=False,
                error="Selected text range is empty"
            )

        # Get surrounding context
        context_start = max(0, range_start - CommentAIService.CONTEXT_CHARS)
        context_end = min(len(content), range_end + CommentAIService.CONTEXT_CHARS)

        context_before = content[context_start:range_start]
        context_after = content[range_end:context_end]

        # Build the prompt
        system_prompt = CommentAIService._build_system_prompt()
        user_prompt = CommentAIService._build_user_prompt(
            comment_body=comment.body,
            selected_text=selected_text,
            context_before=context_before,
            context_after=context_after,
        )

        # Call LLM
        try:
            new_text, ai_reply = CommentAIService._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model_id=model_id,
            )

            return AIResolveResult(
                success=True,
                old_text=selected_text,
                new_text=new_text,
                ai_reply=ai_reply,
            )

        except Exception as e:
            logger.exception(f"AI resolve failed for comment {comment.id}: {e}")
            return AIResolveResult(
                success=False,
                error=str(e)
            )

    @staticmethod
    def _build_system_prompt() -> str:
        """Build the system prompt for the AI assistant."""
        return """Du bist ein hilfreicher Assistent für LaTeX-Dokumente.
Deine Aufgabe ist es, Kommentare und Anmerkungen von Benutzern umzusetzen.

Analysiere den Kommentar und den markierten Text, dann:
1. Setze die Anmerkung des Benutzers um
2. Gib den verbesserten/geänderten Text zurück
3. Erkläre kurz, was du geändert hast

Antworte im folgenden JSON-Format:
{
  "new_text": "Der verbesserte Text, der den markierten Abschnitt ersetzen soll",
  "reply": "Kurze Erklärung der Änderungen (1-2 Sätze)"
}

Wichtige Regeln:
- Behalte die LaTeX-Formatierung bei
- Füge nur sinnvolle Änderungen ein
- Bei unklaren Anmerkungen, versuche die wahrscheinlichste Interpretation
- Wenn keine Änderung nötig ist, gib den Originaltext zurück"""

    @staticmethod
    def _build_user_prompt(
        comment_body: str,
        selected_text: str,
        context_before: str,
        context_after: str,
    ) -> str:
        """Build the user prompt with comment and context."""
        return f"""Ein Benutzer hat folgenden Kommentar zu einem Textabschnitt hinterlassen:

---
Kommentar: {comment_body}
---

Der markierte Textabschnitt ist:
---
{selected_text}
---

Kontext davor:
---
{context_before}
---

Kontext danach:
---
{context_after}
---

Bitte setze die Anmerkung um und gib das Ergebnis im JSON-Format zurück."""

    @staticmethod
    def _call_llm(
        system_prompt: str,
        user_prompt: str,
        model_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Call the LLM and parse the response.

        Returns:
            Tuple of (new_text, ai_reply)
        """
        import json

        # Get a client (will use default model if model_id is None)
        client = LLMClientFactory.get_client_for_model(model_id)
        actual_model_id = model_id or LLMClientFactory.get_default_model_id()

        if not client or not actual_model_id:
            raise ValueError("No LLM client available")

        response = client.chat.completions.create(
            model=actual_model_id,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=2000,
            extra_body={"response_format": {"type": "json_object"}},
        )

        content = extract_message_text(response.choices[0].message) if response.choices else ""
        if not content:
            raise ValueError("Empty response from LLM")

        # Parse JSON response - handle LaTeX backslashes
        raw = content.strip()
        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        # Try standard JSON parsing first
        parsed = None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # LaTeX content may contain backslashes that break JSON parsing
            # Try to extract fields manually using regex
            import re

            # Extract new_text field (handles multiline content)
            new_text_match = re.search(
                r'"new_text"\s*:\s*"((?:[^"\\]|\\.|"(?=\s*,|\s*}))*)"',
                raw,
                re.DOTALL
            )
            # Extract reply field
            reply_match = re.search(
                r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"',
                raw
            )

            if new_text_match:
                extracted_new_text = new_text_match.group(1)
                # Unescape common JSON escapes while preserving LaTeX
                extracted_new_text = extracted_new_text.replace('\\"', '"')
                extracted_new_text = extracted_new_text.replace('\\n', '\n')
                extracted_new_text = extracted_new_text.replace('\\t', '\t')

                parsed = {
                    "new_text": extracted_new_text,
                    "reply": reply_match.group(1) if reply_match else "Änderung wurde umgesetzt."
                }
            else:
                # Last resort: try to fix common LaTeX escaping issues
                fixed_raw = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
                try:
                    parsed = json.loads(fixed_raw)
                except json.JSONDecodeError as e2:
                    raise ValueError(f"Could not parse LLM response as JSON: {e2}")

        if not parsed:
            raise ValueError("Could not extract response from LLM output")

        new_text = parsed.get("new_text", "")
        ai_reply = parsed.get("reply", "Änderung wurde umgesetzt.")

        if not new_text:
            raise ValueError("LLM returned empty new_text")

        return new_text, ai_reply

    # =========================================================================
    # Streaming Support
    # =========================================================================

    @staticmethod
    def get_active_stream(comment_id: int) -> Optional[Dict[str, Any]]:
        """Get the current state of an active AI resolve stream for reconnection."""
        with _streams_lock:
            return _active_streams.get(comment_id)

    @staticmethod
    def clear_stream(comment_id: int):
        """Clear a finished stream from memory."""
        with _streams_lock:
            _active_streams.pop(comment_id, None)

    @staticmethod
    def resolve_comment_streaming(
        comment: LatexComment,
        document: LatexDocument,
        on_token: Callable[[str], None],
        on_complete: Callable[[str, str], None],
        on_error: Callable[[str], None],
        model_id: Optional[str] = None,
    ) -> bool:
        """
        Use AI to resolve a comment with streaming support.
        Runs in a background thread and calls callbacks for each token.

        Args:
            comment: The comment to resolve
            document: The document containing the comment
            on_token: Callback for each streamed token
            on_complete: Callback when complete with (new_text, ai_reply)
            on_error: Callback on error with error message
            model_id: Optional specific model to use

        Returns:
            True if streaming started, False if error
        """
        ai_settings = CommentAIService.get_ai_settings()
        if not ai_settings['enabled']:
            on_error("AI assistant is disabled")
            return False

        # Get document content
        content = document.content_text if isinstance(document.content_text, str) else ""
        if not content and isinstance(document.content, str):
            content = document.content
        if not content:
            on_error("Document has no content")
            return False

        # Extract selected text and context
        range_start = comment.range_start
        range_end = comment.range_end

        if range_start is None or range_end is None:
            on_error("Comment has no text range")
            return False

        range_start = max(0, min(range_start, len(content)))
        range_end = max(range_start, min(range_end, len(content)))

        selected_text = content[range_start:range_end]
        if not selected_text.strip():
            on_error("Selected text range is empty")
            return False

        context_start = max(0, range_start - CommentAIService.CONTEXT_CHARS)
        context_end = min(len(content), range_end + CommentAIService.CONTEXT_CHARS)

        context_before = content[context_start:range_start]
        context_after = content[range_end:context_end]

        # Build prompts
        system_prompt = CommentAIService._build_system_prompt()
        user_prompt = CommentAIService._build_user_prompt(
            comment_body=comment.body,
            selected_text=selected_text,
            context_before=context_before,
            context_after=context_after,
        )

        # Get LLM client BEFORE starting background thread (requires app context)
        client = LLMClientFactory.get_client_for_model(model_id)
        actual_model_id = model_id or LLMClientFactory.get_default_model_id()

        if not client or not actual_model_id:
            on_error("No LLM client available")
            return False

        # Initialize stream state
        with _streams_lock:
            _active_streams[comment.id] = {
                "content": "",
                "status": "streaming",
                "result": None,
                "old_text": selected_text
            }

        def stream_worker():
            import json
            try:

                # Stream the response
                stream = client.chat.completions.create(
                    model=actual_model_id,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2000,
                    stream=True,
                )

                full_content = ""
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        token = chunk.choices[0].delta.content
                        full_content += token

                        # Update stream state
                        with _streams_lock:
                            if comment.id in _active_streams:
                                _active_streams[comment.id]["content"] = full_content

                        # Emit token
                        on_token(token)

                # Parse the complete response - handle LaTeX backslashes
                raw = full_content.strip()
                if raw.startswith("```"):
                    raw = raw.replace("```json", "").replace("```", "").strip()

                # Try standard JSON parsing first
                parsed = None
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    # LaTeX content may contain backslashes that break JSON parsing
                    # Try to extract fields manually using regex
                    logger.info("Standard JSON parsing failed, attempting regex extraction")
                    import re

                    # Extract new_text field (handles multiline content)
                    new_text_match = re.search(
                        r'"new_text"\s*:\s*"((?:[^"\\]|\\.|"(?=\s*,|\s*}))*)"',
                        raw,
                        re.DOTALL
                    )
                    # Extract reply field
                    reply_match = re.search(
                        r'"reply"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        raw
                    )

                    if new_text_match:
                        extracted_new_text = new_text_match.group(1)
                        # Unescape common JSON escapes while preserving LaTeX
                        extracted_new_text = extracted_new_text.replace('\\"', '"')
                        extracted_new_text = extracted_new_text.replace('\\n', '\n')
                        extracted_new_text = extracted_new_text.replace('\\t', '\t')

                        parsed = {
                            "new_text": extracted_new_text,
                            "reply": reply_match.group(1) if reply_match else "Änderung wurde umgesetzt."
                        }
                    else:
                        # Last resort: try to fix common LaTeX escaping issues
                        # Escape unescaped backslashes that aren't part of JSON escapes
                        fixed_raw = re.sub(
                            r'\\(?!["\\/bfnrtu])',
                            r'\\\\',
                            raw
                        )
                        try:
                            parsed = json.loads(fixed_raw)
                        except json.JSONDecodeError as e2:
                            raise ValueError(f"Could not parse LLM response as JSON: {e2}")

                if not parsed:
                    raise ValueError("Could not extract response from LLM output")

                new_text = parsed.get("new_text", "")
                ai_reply = parsed.get("reply", "Änderung wurde umgesetzt.")

                if not new_text:
                    raise ValueError("LLM returned empty new_text")

                # Update stream state
                with _streams_lock:
                    if comment.id in _active_streams:
                        _active_streams[comment.id]["status"] = "completed"
                        _active_streams[comment.id]["result"] = {
                            "new_text": new_text,
                            "ai_reply": ai_reply
                        }

                on_complete(new_text, ai_reply)

            except Exception as e:
                logger.exception(f"AI streaming failed for comment {comment.id}: {e}")
                with _streams_lock:
                    if comment.id in _active_streams:
                        _active_streams[comment.id]["status"] = "error"
                        _active_streams[comment.id]["error"] = str(e)
                on_error(str(e))

        # Start streaming in background thread
        thread = threading.Thread(target=stream_worker, daemon=True)
        thread.start()
        return True
