"""
Generic Format Adapter.

Handles various text-based data formats that don't fit specific patterns.
Attempts to intelligently detect the data structure and create appropriate items.
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
    ItemType,
)

logger = logging.getLogger(__name__)


class GenericAdapter(BaseAdapter):
    """
    Adapter for generic text data formats.

    Detects and handles:
    - Single text items (reviews, documents, etc.)
    - Q&A pairs
    - Text pairs for comparison
    - Simple key-value structures
    """

    FORMAT_ID = "generic"
    FORMAT_NAME = "Generic Text Data"
    FORMAT_DESCRIPTION = "Flexible adapter for various text-based data structures"
    SUPPORTED_EXTENSIONS = [".json", ".jsonl", ".csv"]

    # Field patterns for detection - expanded for common public datasets
    TEXT_FIELDS = [
        "text", "content", "body", "message", "description", "review", "comment",
        "input", "output", "sentence", "document", "passage", "context", "article",
        "premise", "hypothesis", "source", "summary", "highlights", "abstract",
        "comment_text", "post", "tweet", "utterance"
    ]
    QUESTION_FIELDS = [
        "question", "query", "prompt", "input", "instruction", "ask"
    ]
    ANSWER_FIELDS = [
        "answer", "response", "output", "completion", "reply", "target",
        "long_answer", "short_answer", "gold_answer", "reference",
        "canonical_solution", "solution", "expected_output", "best_answer"
    ]
    LABEL_FIELDS = [
        "label", "class", "category", "tag", "sentiment", "rating", "score",
        "toxic", "hate", "offensive", "spam", "newsgroup", "topic", "intent"
    ]
    ID_FIELDS = [
        "id", "idx", "index", "item_id", "doc_id", "row_id", "uid", "guid"
    ]
    TITLE_FIELDS = [
        "title", "subject", "headline", "name", "header"
    ]
    # Text pair fields for NLI, paraphrase, translation
    TEXT_PAIR_A_FIELDS = [
        "text_a", "text_1", "sentence1", "sentence_1", "premise", "source",
        "text1", "sent1", "s1", "original", "en", "src"
    ]
    TEXT_PAIR_B_FIELDS = [
        "text_b", "text_2", "sentence2", "sentence_2", "hypothesis", "target",
        "text2", "sent2", "s2", "translation", "de", "fr", "es", "tgt", "mt"
    ]

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """Check if this adapter can handle the data."""
        # This is a fallback adapter - it can handle almost anything
        if isinstance(data, list) and data:
            if all(isinstance(item, dict) for item in data[:5]):
                first_item = data[0]
                # Check for text-like fields
                has_text = any(
                    self._find_field(first_item, patterns)
                    for patterns in [
                        self.TEXT_FIELDS, self.QUESTION_FIELDS, self.ANSWER_FIELDS,
                        self.TEXT_PAIR_A_FIELDS, self.TEXT_PAIR_B_FIELDS
                    ]
                )
                if has_text:
                    return True, 0.5  # Lower confidence than specific adapters
        elif isinstance(data, dict):
            if "items" in data or "data" in data or "rows" in data:
                return True, 0.4
        return False, 0.0

    def _find_field(self, item: dict, patterns: list[str]) -> str | None:
        """Find a field matching any of the patterns."""
        for key in item.keys():
            key_lower = key.lower()
            for pattern in patterns:
                if pattern in key_lower:
                    return key
        return None

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze the data structure."""
        items = self._normalize_to_list(data)

        structure = {
            "format": self.FORMAT_ID,
            "item_count": len(items),
            "detected_item_type": None,
            "detected_fields": {},
            "sample_values": {},
        }

        if not items:
            return structure

        first_item = items[0]

        # Detect field mappings
        structure["detected_fields"] = {
            "id": self._find_field(first_item, self.ID_FIELDS),
            "text": self._find_field(first_item, self.TEXT_FIELDS),
            "question": self._find_field(first_item, self.QUESTION_FIELDS),
            "answer": self._find_field(first_item, self.ANSWER_FIELDS),
            "label": self._find_field(first_item, self.LABEL_FIELDS),
            "title": self._find_field(first_item, self.TITLE_FIELDS),
            "text_a": self._find_field(first_item, self.TEXT_PAIR_A_FIELDS),
            "text_b": self._find_field(first_item, self.TEXT_PAIR_B_FIELDS),
        }

        # Determine item type based on detected fields
        fields = structure["detected_fields"]
        if fields["text_a"] and fields["text_b"]:
            # Text pair (NLI, paraphrase, translation)
            structure["detected_item_type"] = ItemType.TEXT_PAIR.value
        elif fields["question"] and fields["answer"]:
            structure["detected_item_type"] = ItemType.QA_PAIR.value
        elif fields["text"]:
            structure["detected_item_type"] = ItemType.SINGLE_TEXT.value
        else:
            structure["detected_item_type"] = ItemType.CUSTOM.value

        # Get sample values
        for field_type, field_name in fields.items():
            if field_name and field_name in first_item:
                value = first_item[field_name]
                if isinstance(value, str):
                    structure["sample_values"][field_type] = value[:100]

        # List all fields
        structure["all_fields"] = list(first_item.keys())

        return structure

    def _normalize_to_list(self, data: Any) -> list[dict]:
        """Normalize data to a list of dictionaries."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ["items", "data", "rows", "records", "entries"]:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # Single item
            return [data]
        return []

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform generic data to ImportItems."""
        self.clear_messages()
        options = options or {}
        items: list[ImportItem] = []

        raw_items = self._normalize_to_list(data)

        if not raw_items:
            return AdapterResult(
                success=False,
                errors=["No items found in data"]
            )

        # Detect or use provided mappings
        structure = self.detect_structure(data)
        field_mappings = options.get("mappings", structure["detected_fields"])

        # Detect item type
        item_type_str = options.get("item_type", structure.get("detected_item_type"))
        try:
            item_type = ItemType(item_type_str) if item_type_str else ItemType.SINGLE_TEXT
        except ValueError:
            item_type = ItemType.SINGLE_TEXT

        # Process items
        for idx, raw_item in enumerate(raw_items):
            try:
                item = self._parse_item(raw_item, idx, item_type, field_mappings)
                if item:
                    items.append(item)
            except Exception as e:
                self.add_error(f"Error parsing item {idx}: {str(e)}")

        # Suggest task type based on item type
        task_type_mapping = {
            ItemType.SINGLE_TEXT: TaskType.RATING,
            ItemType.QA_PAIR: TaskType.RATING,
            ItemType.TEXT_PAIR: TaskType.COMPARISON,
            ItemType.CONVERSATION: TaskType.MAIL_RATING,
        }
        suggested_type = task_type_mapping.get(item_type, TaskType.RATING)

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
                "detected_item_type": item_type.value,
                "field_mappings": field_mappings,
            }
        )

    def _parse_item(
        self,
        raw_item: dict[str, Any],
        index: int,
        item_type: ItemType,
        mappings: dict[str, str | None]
    ) -> ImportItem | None:
        """Parse a single item based on detected type."""
        # Get ID
        id_field = mappings.get("id")
        if id_field and id_field in raw_item:
            item_id = str(raw_item[id_field])
        else:
            # Generate from content
            content_for_hash = str(raw_item)[:200]
            item_id = hashlib.md5(content_for_hash.encode()).hexdigest()[:12]

        # Get common fields
        title_field = mappings.get("title")
        title = str(raw_item[title_field]) if title_field and title_field in raw_item else None

        label_field = mappings.get("label")
        label = str(raw_item[label_field]) if label_field and label_field in raw_item else None

        # Collect remaining fields as metadata
        known_fields = set(v for v in mappings.values() if v)
        metadata = {
            k: v for k, v in raw_item.items()
            if k not in known_fields and v is not None
        }

        # Create item based on type
        if item_type == ItemType.QA_PAIR:
            q_field = mappings.get("question")
            a_field = mappings.get("answer")

            question = str(raw_item.get(q_field, "")) if q_field else ""
            answer = str(raw_item.get(a_field, "")) if a_field else ""

            if not question and not answer:
                return None

            return ImportItem.from_qa_pair(
                id=item_id,
                question=question,
                answer=answer,
                title=title,
                label=label,
                metadata=metadata,
            )

        elif item_type == ItemType.SINGLE_TEXT:
            text_field = mappings.get("text")
            content = str(raw_item.get(text_field, "")) if text_field else ""

            # If no text field found, try to use first string field
            if not content:
                for key, value in raw_item.items():
                    if isinstance(value, str) and len(value) > 20:
                        content = value
                        break

            if not content:
                return None

            return ImportItem.from_single_text(
                id=item_id,
                content=content,
                title=title,
                label=label,
                metadata=metadata,
            )

        elif item_type == ItemType.TEXT_PAIR:
            # Use detected mappings for text pairs
            text_a_field = mappings.get("text_a")
            text_b_field = mappings.get("text_b")

            text_a = str(raw_item.get(text_a_field, "")) if text_a_field else None
            text_b = str(raw_item.get(text_b_field, "")) if text_b_field else None

            # Fallback: try common field patterns if mappings didn't work
            if not text_a:
                for key in ["text_a", "text_1", "sentence1", "premise", "source", "en", "original"]:
                    if key in raw_item:
                        text_a = str(raw_item[key])
                        break

            if not text_b:
                for key in ["text_b", "text_2", "sentence2", "hypothesis", "target", "de", "translation"]:
                    if key in raw_item:
                        text_b = str(raw_item[key])
                        break

            if not text_a or not text_b:
                return None

            # Determine labels from field names if available
            label_a = text_a_field.replace("_", " ").title() if text_a_field else "Text A"
            label_b = text_b_field.replace("_", " ").title() if text_b_field else "Text B"

            return ImportItem.from_text_pair(
                id=item_id,
                text_a=text_a,
                text_b=text_b,
                label_a=label_a,
                label_b=label_b,
                title=title,
                label=label,
                metadata=metadata,
            )

        else:
            # Default: try to create single text
            content = None
            for key, value in raw_item.items():
                if isinstance(value, str) and len(value) > 20:
                    content = value
                    break

            if content:
                return ImportItem.from_single_text(
                    id=item_id,
                    content=content,
                    title=title,
                    label=label,
                    metadata=metadata,
                )

        return None
