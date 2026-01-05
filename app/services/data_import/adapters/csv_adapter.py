"""
CSV Format Adapter.

Handles tabular data with columns for messages.
"""

from typing import Any
import logging
import hashlib

from .base_adapter import (
    BaseAdapter,
    AdapterResult,
    ImportItem,
    Message,
    MessageRole,
    TaskType,
)

logger = logging.getLogger(__name__)


class CSVAdapter(BaseAdapter):
    """Adapter for CSV/tabular data format."""

    FORMAT_ID = "csv"
    FORMAT_NAME = "CSV/Tabular"
    FORMAT_DESCRIPTION = "Tabular data with columns for ID, user message, assistant response"
    SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".tsv"]

    # Common column name patterns
    ID_COLUMNS = ["id", "conversation_id", "thread_id", "chat_id", "index", "row"]
    USER_COLUMNS = ["user", "user_message", "input", "prompt", "question", "human", "client"]
    ASSISTANT_COLUMNS = ["assistant", "response", "output", "answer", "bot", "ai", "model_response"]
    SUBJECT_COLUMNS = ["subject", "title", "topic", "category"]

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """Check if data is in CSV/tabular format."""
        if not isinstance(data, list) or not data:
            return False, 0.0

        # Check if it's a list of flat dictionaries (rows)
        first_row = data[0]
        if not isinstance(first_row, dict):
            return False, 0.0

        columns = set(first_row.keys())
        lower_columns = {c.lower() for c in columns}

        # Check for user/assistant column patterns
        has_user = any(
            any(pattern in col for pattern in self.USER_COLUMNS)
            for col in lower_columns
        )
        has_assistant = any(
            any(pattern in col for pattern in self.ASSISTANT_COLUMNS)
            for col in lower_columns
        )

        # Must have at least user or a single content column
        if has_user and has_assistant:
            return True, 0.9
        elif has_user or has_assistant:
            return True, 0.7
        elif "content" in lower_columns or "text" in lower_columns:
            return True, 0.5

        return False, 0.0

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze CSV structure."""
        if not data:
            return {"format": self.FORMAT_ID, "columns": [], "row_count": 0}

        columns = list(data[0].keys())
        lower_columns = {c.lower(): c for c in columns}

        structure = {
            "format": self.FORMAT_ID,
            "columns": columns,
            "row_count": len(data),
            "detected_mappings": {},
        }

        # Detect ID column
        for pattern in self.ID_COLUMNS:
            for lower, original in lower_columns.items():
                if pattern in lower:
                    structure["detected_mappings"]["id"] = original
                    break
            if "id" in structure["detected_mappings"]:
                break

        # Detect user column
        for pattern in self.USER_COLUMNS:
            for lower, original in lower_columns.items():
                if pattern in lower:
                    structure["detected_mappings"]["user"] = original
                    break
            if "user" in structure["detected_mappings"]:
                break

        # Detect assistant column
        for pattern in self.ASSISTANT_COLUMNS:
            for lower, original in lower_columns.items():
                if pattern in lower:
                    structure["detected_mappings"]["assistant"] = original
                    break
            if "assistant" in structure["detected_mappings"]:
                break

        # Detect subject column
        for pattern in self.SUBJECT_COLUMNS:
            for lower, original in lower_columns.items():
                if pattern in lower:
                    structure["detected_mappings"]["subject"] = original
                    break
            if "subject" in structure["detected_mappings"]:
                break

        return structure

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform CSV data to LLARS ImportItems."""
        self.clear_messages()
        options = options or {}
        items: list[ImportItem] = []

        if not data:
            return AdapterResult(success=False, errors=["Empty data"])

        # Get column mappings
        structure = self.detect_structure(data)
        mappings = options.get("mappings", structure["detected_mappings"])

        id_col = mappings.get("id")
        user_col = mappings.get("user")
        assistant_col = mappings.get("assistant")
        subject_col = mappings.get("subject")

        if not user_col and not assistant_col:
            return AdapterResult(
                success=False,
                errors=["Could not detect user or assistant columns"]
            )

        # Process rows
        for idx, row in enumerate(data):
            try:
                item = self._parse_row(
                    row, idx, id_col, user_col, assistant_col, subject_col
                )
                if item:
                    items.append(item)
            except Exception as e:
                self.add_error(f"Error parsing row {idx}: {str(e)}")

        return AdapterResult(
            success=len(items) > 0,
            items=items,
            errors=self._errors,
            warnings=self._warnings,
            suggested_task_type=TaskType.MAIL_RATING,
            stats={
                "total_rows": len(data),
                "successfully_parsed": len(items),
                "failed": len(data) - len(items),
                "column_mappings": mappings,
            }
        )

    def _parse_row(
        self,
        row: dict[str, Any],
        index: int,
        id_col: str | None,
        user_col: str | None,
        assistant_col: str | None,
        subject_col: str | None
    ) -> ImportItem | None:
        """Parse a single CSV row."""
        messages: list[Message] = []

        # Get user message
        if user_col and row.get(user_col):
            messages.append(Message(
                role=MessageRole.USER,
                content=str(row[user_col]),
            ))

        # Get assistant message
        if assistant_col and row.get(assistant_col):
            messages.append(Message(
                role=MessageRole.ASSISTANT,
                content=str(row[assistant_col]),
            ))

        if not messages:
            return None

        # Get ID
        if id_col and row.get(id_col):
            item_id = str(row[id_col])
        else:
            # Generate from content
            content = str(messages[0].content if messages else index)
            item_id = hashlib.md5(content.encode()).hexdigest()[:12]

        # Get subject
        subject = str(row[subject_col]) if subject_col and row.get(subject_col) else None

        # Collect remaining fields as metadata
        known_cols = {id_col, user_col, assistant_col, subject_col}
        metadata = {
            k: v for k, v in row.items()
            if k not in known_cols and v is not None
        }

        return ImportItem(
            id=item_id,
            conversation=messages,
            subject=subject,
            metadata=metadata,
        )
