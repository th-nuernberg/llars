"""
Schema Validator for LLARS import data.

Validates that transformed data matches the expected LLARS schema.
"""

from typing import Any
from dataclasses import dataclass, field
import logging

from .adapters.base_adapter import TaskType, MessageRole

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of schema validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)


class SchemaValidator:
    """
    Validates data against the LLARS import schema.

    Ensures all required fields are present and correctly typed.
    """

    # Required fields for ImportItem
    REQUIRED_ITEM_FIELDS = {"id", "conversation"}

    # Required fields for Message
    REQUIRED_MESSAGE_FIELDS = {"role", "content"}

    # Valid task types
    VALID_TASK_TYPES = {t.value for t in TaskType}

    # Valid message roles
    VALID_ROLES = {r.value for r in MessageRole}

    def validate_item(self, item: dict[str, Any], index: int = 0) -> ValidationResult:
        """
        Validate a single import item.

        Args:
            item: Item dictionary to validate
            index: Item index for error messages

        Returns:
            ValidationResult with any errors/warnings
        """
        errors = []
        warnings = []

        # Check required fields
        for field_name in self.REQUIRED_ITEM_FIELDS:
            if field_name not in item:
                errors.append(f"Item {index}: Missing required field '{field_name}'")

        # Validate ID
        if "id" in item:
            if not isinstance(item["id"], (str, int)):
                errors.append(f"Item {index}: 'id' must be string or integer")
            elif not str(item["id"]).strip():
                errors.append(f"Item {index}: 'id' cannot be empty")

        # Validate conversation
        if "conversation" in item:
            conv = item["conversation"]
            if not isinstance(conv, list):
                errors.append(f"Item {index}: 'conversation' must be an array")
            elif not conv:
                warnings.append(f"Item {index}: 'conversation' is empty")
            else:
                for msg_idx, msg in enumerate(conv):
                    msg_errors, msg_warnings = self._validate_message(msg, index, msg_idx)
                    errors.extend(msg_errors)
                    warnings.extend(msg_warnings)

        # Validate features if present
        if "features" in item:
            features = item["features"]
            if not isinstance(features, list):
                errors.append(f"Item {index}: 'features' must be an array")
            else:
                for feat_idx, feat in enumerate(features):
                    feat_errors = self._validate_feature(feat, index, feat_idx)
                    errors.extend(feat_errors)

        # Validate metadata if present
        if "metadata" in item and not isinstance(item["metadata"], dict):
            errors.append(f"Item {index}: 'metadata' must be an object")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_message(
        self,
        message: Any,
        item_index: int,
        msg_index: int
    ) -> tuple[list[str], list[str]]:
        """Validate a single message."""
        errors = []
        warnings = []
        prefix = f"Item {item_index}, message {msg_index}"

        if not isinstance(message, dict):
            errors.append(f"{prefix}: Message must be an object")
            return errors, warnings

        # Check required fields
        for field_name in self.REQUIRED_MESSAGE_FIELDS:
            if field_name not in message:
                errors.append(f"{prefix}: Missing required field '{field_name}'")

        # Validate role
        if "role" in message:
            role = message["role"]
            if not isinstance(role, str):
                errors.append(f"{prefix}: 'role' must be a string")
            elif role not in self.VALID_ROLES:
                warnings.append(
                    f"{prefix}: Unknown role '{role}', expected one of {self.VALID_ROLES}"
                )

        # Validate content
        if "content" in message:
            content = message["content"]
            if not isinstance(content, str):
                errors.append(f"{prefix}: 'content' must be a string")
            elif not content.strip():
                warnings.append(f"{prefix}: 'content' is empty")

        return errors, warnings

    def _validate_feature(
        self,
        feature: Any,
        item_index: int,
        feat_index: int
    ) -> list[str]:
        """Validate a single feature."""
        errors = []
        prefix = f"Item {item_index}, feature {feat_index}"

        if not isinstance(feature, dict):
            errors.append(f"{prefix}: Feature must be an object")
            return errors

        if "type" not in feature:
            errors.append(f"{prefix}: Missing required field 'type'")
        elif not isinstance(feature["type"], str):
            errors.append(f"{prefix}: 'type' must be a string")

        if "content" not in feature:
            errors.append(f"{prefix}: Missing required field 'content'")
        elif not isinstance(feature["content"], str):
            errors.append(f"{prefix}: 'content' must be a string")

        return errors

    def validate_import_data(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate complete import data (with metadata and items).

        Args:
            data: Full import data dictionary

        Returns:
            ValidationResult with aggregate results
        """
        errors = []
        warnings = []
        stats = {
            "total_items": 0,
            "valid_items": 0,
            "total_messages": 0,
            "total_features": 0,
        }

        # Validate metadata
        if "metadata" in data:
            meta = data["metadata"]
            if not isinstance(meta, dict):
                errors.append("'metadata' must be an object")
            else:
                if "task_type" in meta:
                    if meta["task_type"] not in self.VALID_TASK_TYPES:
                        warnings.append(
                            f"Unknown task_type '{meta['task_type']}', "
                            f"expected one of {self.VALID_TASK_TYPES}"
                        )

        # Validate items
        if "items" not in data:
            errors.append("Missing required field 'items'")
        elif not isinstance(data["items"], list):
            errors.append("'items' must be an array")
        else:
            stats["total_items"] = len(data["items"])

            for idx, item in enumerate(data["items"]):
                result = self.validate_item(item, idx)
                errors.extend(result.errors)
                warnings.extend(result.warnings)

                if result.valid:
                    stats["valid_items"] += 1

                # Count messages and features
                if isinstance(item.get("conversation"), list):
                    stats["total_messages"] += len(item["conversation"])
                if isinstance(item.get("features"), list):
                    stats["total_features"] += len(item["features"])

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            stats=stats,
        )

    def validate_items_list(self, items: list[dict[str, Any]]) -> ValidationResult:
        """
        Validate a list of items (without wrapper).

        Args:
            items: List of item dictionaries

        Returns:
            ValidationResult with aggregate results
        """
        return self.validate_import_data({"items": items})
