"""
LMSYS Pairwise Comparison Format Adapter.

Handles data in LMSYS Chatbot Arena format for pairwise comparisons.
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


class LMSYSAdapter(BaseAdapter):
    """Adapter for LMSYS pairwise comparison format."""

    FORMAT_ID = "lmsys"
    FORMAT_NAME = "LMSYS Pairwise"
    FORMAT_DESCRIPTION = "Pairwise comparison format (prompt + response_a + response_b)"
    SUPPORTED_EXTENSIONS = [".json", ".jsonl"]

    # Field name patterns for LMSYS format
    PROMPT_FIELDS = ["prompt", "instruction", "input", "question"]
    RESPONSE_A_FIELDS = ["response_a", "output_a", "answer_a", "model_a_response", "chosen"]
    RESPONSE_B_FIELDS = ["response_b", "output_b", "answer_b", "model_b_response", "rejected"]
    MODEL_A_FIELDS = ["model_a", "model_name_a", "model_1"]
    MODEL_B_FIELDS = ["model_b", "model_name_b", "model_2"]
    VOTE_FIELDS = ["winner", "vote", "preference", "label"]

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """Check if data is in LMSYS pairwise format."""
        items = data if isinstance(data, list) else [data]

        if not items or not isinstance(items[0], dict):
            return False, 0.0

        first_item = items[0]
        lower_keys = {k.lower(): k for k in first_item.keys()}

        # Check for pairwise structure
        has_prompt = any(p in lower_keys for p in self.PROMPT_FIELDS)
        has_response_a = any(p in lower_keys for p in self.RESPONSE_A_FIELDS)
        has_response_b = any(p in lower_keys for p in self.RESPONSE_B_FIELDS)

        if has_prompt and has_response_a and has_response_b:
            return True, 0.95

        # Alternative: conversation_a/conversation_b structure
        if "conversation_a" in lower_keys and "conversation_b" in lower_keys:
            return True, 0.9

        # DPO format: chosen/rejected
        if "chosen" in lower_keys and "rejected" in lower_keys:
            return True, 0.85

        return False, 0.0

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze LMSYS format structure."""
        items = data if isinstance(data, list) else [data]

        structure = {
            "format": self.FORMAT_ID,
            "item_count": len(items),
            "detected_fields": {},
            "has_model_names": False,
            "has_votes": False,
        }

        if not items:
            return structure

        first_item = items[0]
        lower_keys = {k.lower(): k for k in first_item.keys()}

        # Detect field mappings
        for pattern in self.PROMPT_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["prompt"] = lower_keys[pattern]
                break

        for pattern in self.RESPONSE_A_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["response_a"] = lower_keys[pattern]
                break

        for pattern in self.RESPONSE_B_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["response_b"] = lower_keys[pattern]
                break

        for pattern in self.MODEL_A_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["model_a"] = lower_keys[pattern]
                structure["has_model_names"] = True
                break

        for pattern in self.MODEL_B_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["model_b"] = lower_keys[pattern]
                break

        for pattern in self.VOTE_FIELDS:
            if pattern in lower_keys:
                structure["detected_fields"]["vote"] = lower_keys[pattern]
                structure["has_votes"] = True
                break

        return structure

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform LMSYS format to LLARS ImportItems."""
        self.clear_messages()
        options = options or {}
        items: list[ImportItem] = []

        raw_items = data if isinstance(data, list) else [data]

        # Get field mappings
        structure = self.detect_structure(data)
        mappings = options.get("mappings", structure["detected_fields"])

        prompt_field = mappings.get("prompt")
        response_a_field = mappings.get("response_a")
        response_b_field = mappings.get("response_b")
        model_a_field = mappings.get("model_a")
        model_b_field = mappings.get("model_b")
        vote_field = mappings.get("vote")

        if not prompt_field or not response_a_field or not response_b_field:
            return AdapterResult(
                success=False,
                errors=["Missing required fields: prompt, response_a, response_b"]
            )

        # Process items - create TWO items per comparison (one for each response)
        for idx, raw_item in enumerate(raw_items):
            try:
                pair = self._parse_comparison(
                    raw_item, idx,
                    prompt_field, response_a_field, response_b_field,
                    model_a_field, model_b_field, vote_field
                )
                if pair:
                    items.extend(pair)
            except Exception as e:
                self.add_error(f"Error parsing item {idx}: {str(e)}")

        return AdapterResult(
            success=len(items) > 0,
            items=items,
            errors=self._errors,
            warnings=self._warnings,
            suggested_task_type=TaskType.COMPARISON,
            stats={
                "total_comparisons": len(raw_items),
                "total_items": len(items),
                "items_per_comparison": 2,
                "has_model_names": structure["has_model_names"],
                "has_votes": structure["has_votes"],
            }
        )

    def _parse_comparison(
        self,
        raw_item: dict[str, Any],
        index: int,
        prompt_field: str,
        response_a_field: str,
        response_b_field: str,
        model_a_field: str | None,
        model_b_field: str | None,
        vote_field: str | None
    ) -> list[ImportItem] | None:
        """Parse a single pairwise comparison into two ImportItems."""
        prompt = raw_item.get(prompt_field, "")
        response_a = raw_item.get(response_a_field, "")
        response_b = raw_item.get(response_b_field, "")

        if not prompt or (not response_a and not response_b):
            self.add_warning(f"Item {index}: Missing prompt or responses")
            return None

        # Get model names
        model_a = raw_item.get(model_a_field, "Model A") if model_a_field else "Model A"
        model_b = raw_item.get(model_b_field, "Model B") if model_b_field else "Model B"

        # Get vote if present
        vote = raw_item.get(vote_field) if vote_field else None

        # Generate base ID
        base_id = hashlib.md5(f"{prompt}{response_a}{response_b}".encode()).hexdigest()[:12]

        items = []

        # Create Item A
        if response_a:
            item_a = ImportItem(
                id=f"{base_id}_a",
                conversation=[
                    Message(role=MessageRole.USER, content=prompt),
                    Message(role=MessageRole.ASSISTANT, content=response_a),
                ],
                subject=f"Comparison {index + 1} - {model_a}",
                metadata={
                    "comparison_id": base_id,
                    "comparison_side": "a",
                    "model": model_a,
                    "vote": vote,
                    "original_index": index,
                }
            )
            items.append(item_a)

        # Create Item B
        if response_b:
            item_b = ImportItem(
                id=f"{base_id}_b",
                conversation=[
                    Message(role=MessageRole.USER, content=prompt),
                    Message(role=MessageRole.ASSISTANT, content=response_b),
                ],
                subject=f"Comparison {index + 1} - {model_b}",
                metadata={
                    "comparison_id": base_id,
                    "comparison_side": "b",
                    "model": model_b,
                    "vote": vote,
                    "original_index": index,
                }
            )
            items.append(item_b)

        return items
