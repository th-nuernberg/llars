"""
OpenAI/ChatML Format Adapter.

Handles data in OpenAI Chat Completion API format.
This is the most common format for LLM conversations.
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


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI/ChatML conversation format."""

    FORMAT_ID = "openai"
    FORMAT_NAME = "OpenAI/ChatML"
    FORMAT_DESCRIPTION = "OpenAI Chat Completion API format with messages array"
    SUPPORTED_EXTENSIONS = [".json", ".jsonl"]

    # Known role mappings
    ROLE_MAPPING = {
        "user": MessageRole.USER,
        "human": MessageRole.USER,
        "customer": MessageRole.USER,
        "client": MessageRole.USER,
        "klient": MessageRole.USER,
        "assistant": MessageRole.ASSISTANT,
        "bot": MessageRole.ASSISTANT,
        "ai": MessageRole.ASSISTANT,
        "gpt": MessageRole.ASSISTANT,
        "model": MessageRole.ASSISTANT,
        "berater": MessageRole.ASSISTANT,
        "counsellor": MessageRole.ASSISTANT,
        "counselor": MessageRole.ASSISTANT,
        "system": MessageRole.SYSTEM,
    }

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """Check if data is in OpenAI/ChatML format."""
        # Handle single conversation
        if isinstance(data, dict):
            return self._check_single_conversation(data)

        # Handle list of conversations
        if isinstance(data, list) and data:
            # Check first few items
            matches = 0
            check_count = min(3, len(data))

            for item in data[:check_count]:
                if isinstance(item, dict):
                    can_handle, _ = self._check_single_conversation(item)
                    if can_handle:
                        matches += 1

            if matches == check_count:
                return True, 0.95
            elif matches > 0:
                return True, 0.7

        return False, 0.0

    def _check_single_conversation(self, item: dict[str, Any]) -> tuple[bool, float]:
        """Check if a single item is an OpenAI conversation."""
        # Direct messages array
        if "messages" in item and isinstance(item["messages"], list):
            messages = item["messages"]
            if messages and isinstance(messages[0], dict):
                first_msg = messages[0]
                if "role" in first_msg and "content" in first_msg:
                    return True, 0.95
                # Just content without role
                if "content" in first_msg:
                    return True, 0.7

        # Alternative: conversation field
        if "conversation" in item and isinstance(item["conversation"], list):
            conv = item["conversation"]
            if conv and isinstance(conv[0], dict):
                first_msg = conv[0]
                if "role" in first_msg or "content" in first_msg:
                    return True, 0.8

        # Alternative: turns field
        if "turns" in item and isinstance(item["turns"], list):
            return True, 0.6

        return False, 0.0

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze OpenAI format structure."""
        structure = {
            "format": self.FORMAT_ID,
            "is_array": isinstance(data, list),
            "item_count": 0,
            "message_field": None,
            "has_id": False,
            "has_metadata": False,
            "detected_roles": set(),
            "avg_messages": 0,
        }

        items = data if isinstance(data, list) else [data]
        structure["item_count"] = len(items)

        if not items:
            return structure

        # Detect message field name
        first_item = items[0]
        for field_name in ["messages", "conversation", "turns", "chat"]:
            if field_name in first_item:
                structure["message_field"] = field_name
                break

        structure["has_id"] = any(
            k in first_item for k in ["id", "conversation_id", "thread_id", "chat_id"]
        )
        structure["has_metadata"] = "metadata" in first_item

        # Analyze messages
        total_messages = 0
        roles = set()

        for item in items[:10]:  # Sample first 10
            msg_field = structure["message_field"]
            if msg_field and msg_field in item:
                messages = item[msg_field]
                total_messages += len(messages)
                for msg in messages:
                    if isinstance(msg, dict) and "role" in msg:
                        roles.add(msg["role"])

        structure["detected_roles"] = list(roles)
        structure["avg_messages"] = total_messages / min(10, len(items)) if items else 0

        return structure

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform OpenAI format to LLARS ImportItems."""
        self.clear_messages()
        options = options or {}
        items: list[ImportItem] = []

        # Normalize to list
        raw_items = data if isinstance(data, list) else [data]

        # Detect message field
        message_field = options.get("message_field")
        if not message_field:
            for field_name in ["messages", "conversation", "turns", "chat"]:
                if raw_items and field_name in raw_items[0]:
                    message_field = field_name
                    break

        if not message_field:
            return AdapterResult(
                success=False,
                errors=["Could not detect message field (expected: messages, conversation, turns)"]
            )

        # Process items
        for idx, raw_item in enumerate(raw_items):
            try:
                item = self._parse_item(raw_item, idx, message_field, options)
                if item:
                    items.append(item)
            except Exception as e:
                self.add_error(f"Error parsing item {idx}: {str(e)}")

        # Suggest task type based on structure
        suggested_type = TaskType.MAIL_RATING  # Default for conversations

        return AdapterResult(
            success=len(items) > 0,
            items=items,
            errors=self._errors,
            warnings=self._warnings,
            suggested_task_type=suggested_type,
            stats={
                "total_items": len(raw_items),
                "successfully_parsed": len(items),
                "failed": len(raw_items) - len(items),
                "message_field_used": message_field,
            }
        )

    def _parse_item(
        self,
        raw_item: dict[str, Any],
        index: int,
        message_field: str,
        options: dict[str, Any]
    ) -> ImportItem | None:
        """Parse a single OpenAI conversation."""
        # Get ID
        item_id = None
        for id_field in ["id", "conversation_id", "thread_id", "chat_id"]:
            if id_field in raw_item:
                item_id = str(raw_item[id_field])
                break

        if not item_id:
            # Generate ID from content hash
            content = str(raw_item.get(message_field, []))
            item_id = hashlib.md5(content.encode()).hexdigest()[:12]

        # Parse messages
        raw_messages = raw_item.get(message_field, [])
        messages: list[Message] = []

        for msg_idx, raw_msg in enumerate(raw_messages):
            if not isinstance(raw_msg, dict):
                self.add_warning(f"Item {item_id}, message {msg_idx}: not a dict")
                continue

            # Get content
            content = raw_msg.get("content", "")
            if not content:
                # Try alternative fields
                content = raw_msg.get("text", raw_msg.get("message", ""))

            if not content:
                continue

            # Get role
            role_str = raw_msg.get("role", "user")
            role = self.ROLE_MAPPING.get(role_str.lower(), MessageRole.USER)

            # Get timestamp
            timestamp = raw_msg.get("timestamp", raw_msg.get("created_at"))

            messages.append(Message(
                role=role,
                content=content,
                timestamp=timestamp,
            ))

        if not messages:
            self.add_warning(f"Item {item_id} has no valid messages")
            return None

        # Get subject if available
        subject = raw_item.get("subject", raw_item.get("title"))

        # Get metadata
        metadata = raw_item.get("metadata", {})

        # Include model info if present
        if "model" in raw_item:
            metadata["model"] = raw_item["model"]

        return ImportItem(
            id=item_id,
            conversation=messages,
            subject=subject,
            metadata=metadata,
        )
