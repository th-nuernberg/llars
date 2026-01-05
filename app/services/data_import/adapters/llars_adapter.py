"""
LLARS Native Format Adapter.

Handles data already in LLARS import schema format.
"""

from typing import Any
import logging

from .base_adapter import (
    BaseAdapter,
    AdapterResult,
    ImportItem,
    Message,
    Feature,
    MessageRole,
    TaskType,
)

logger = logging.getLogger(__name__)


class LLARSAdapter(BaseAdapter):
    """Adapter for LLARS native import format."""

    FORMAT_ID = "llars"
    FORMAT_NAME = "LLARS Native"
    FORMAT_DESCRIPTION = "Native LLARS import format with full schema support"
    SUPPORTED_EXTENSIONS = [".json"]

    # Schema version
    CURRENT_SCHEMA_VERSION = "llars-import-v1"

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """Check if data is in LLARS native format."""
        if not isinstance(data, dict):
            return False, 0.0

        # Check for schema identifier
        if data.get("$schema") == self.CURRENT_SCHEMA_VERSION:
            return True, 1.0

        # Check for LLARS structure without explicit schema
        has_metadata = "metadata" in data and isinstance(data["metadata"], dict)
        has_items = "items" in data and isinstance(data["items"], list)

        if has_metadata and has_items:
            # Check if items have expected structure
            if data["items"]:
                first_item = data["items"][0]
                has_conversation = "conversation" in first_item
                has_id = "id" in first_item
                if has_conversation and has_id:
                    return True, 0.9

        return False, 0.0

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze LLARS format structure."""
        structure = {
            "format": self.FORMAT_ID,
            "schema_version": data.get("$schema", "unknown"),
            "has_metadata": "metadata" in data,
            "item_count": 0,
            "fields": [],
            "task_type": None,
        }

        if "metadata" in data:
            metadata = data["metadata"]
            structure["task_type"] = metadata.get("task_type")
            structure["source"] = metadata.get("source")
            structure["name"] = metadata.get("name")

        if "items" in data and data["items"]:
            structure["item_count"] = len(data["items"])
            first_item = data["items"][0]
            structure["fields"] = list(first_item.keys())

            # Analyze conversation structure
            if "conversation" in first_item:
                conv = first_item["conversation"]
                if conv:
                    structure["message_fields"] = list(conv[0].keys()) if conv else []
                    structure["avg_messages"] = sum(
                        len(item.get("conversation", [])) for item in data["items"]
                    ) / len(data["items"])

            # Check for features
            if "features" in first_item:
                structure["has_features"] = True
                structure["feature_types"] = list(set(
                    f.get("type") for item in data["items"]
                    for f in item.get("features", [])
                    if f.get("type")
                ))

        return structure

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform LLARS native format (mostly validation and normalization)."""
        self.clear_messages()
        items: list[ImportItem] = []

        if not isinstance(data, dict):
            return AdapterResult(
                success=False,
                errors=["Data must be a dictionary/object"]
            )

        if "items" not in data:
            return AdapterResult(
                success=False,
                errors=["Missing 'items' array in data"]
            )

        # Determine task type
        task_type = None
        if "metadata" in data and "task_type" in data["metadata"]:
            try:
                task_type = TaskType(data["metadata"]["task_type"])
            except ValueError:
                self.add_warning(f"Unknown task_type: {data['metadata']['task_type']}")

        # Process each item
        for idx, raw_item in enumerate(data["items"]):
            try:
                item = self._parse_item(raw_item, idx)
                if item:
                    items.append(item)
            except Exception as e:
                self.add_error(f"Error parsing item {idx}: {str(e)}")

        return AdapterResult(
            success=len(items) > 0,
            items=items,
            errors=self._errors,
            warnings=self._warnings,
            suggested_task_type=task_type,
            stats={
                "total_items": len(data["items"]),
                "successfully_parsed": len(items),
                "failed": len(data["items"]) - len(items),
            }
        )

    def _parse_item(self, raw_item: dict[str, Any], index: int) -> ImportItem | None:
        """Parse a single item from raw data."""
        # Get ID
        item_id = str(raw_item.get("id", f"item-{index}"))

        # Parse conversation
        raw_conversation = raw_item.get("conversation", [])
        messages: list[Message] = []

        for msg_idx, raw_msg in enumerate(raw_conversation):
            try:
                role_str = raw_msg.get("role", "user")
                try:
                    role = MessageRole(role_str)
                except ValueError:
                    # Map common alternatives
                    role_mapping = {
                        "human": MessageRole.USER,
                        "bot": MessageRole.ASSISTANT,
                        "ai": MessageRole.ASSISTANT,
                        "client": MessageRole.USER,
                        "klient": MessageRole.USER,
                        "berater": MessageRole.ASSISTANT,
                        "counsellor": MessageRole.ASSISTANT,
                        "counselor": MessageRole.ASSISTANT,
                    }
                    role = role_mapping.get(role_str.lower(), MessageRole.USER)

                message = Message(
                    role=role,
                    content=raw_msg.get("content", ""),
                    timestamp=raw_msg.get("timestamp"),
                    metadata=raw_msg.get("metadata", {}),
                )
                messages.append(message)
            except Exception as e:
                self.add_warning(f"Item {item_id}, message {msg_idx}: {str(e)}")

        if not messages:
            self.add_warning(f"Item {item_id} has no valid messages")
            return None

        # Parse features
        features: list[Feature] = []
        for raw_feature in raw_item.get("features", []):
            features.append(Feature(
                type=raw_feature.get("type", "unknown"),
                content=raw_feature.get("content", ""),
                generated_by=raw_feature.get("generated_by"),
            ))

        return ImportItem(
            id=item_id,
            conversation=messages,
            subject=raw_item.get("subject"),
            features=features,
            metadata=raw_item.get("metadata", {}),
        )
