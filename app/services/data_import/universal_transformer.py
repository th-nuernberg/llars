"""
Universal Transformer for AI-assisted data import.

Transforms arbitrary JSON structures into LLARS format using AI-generated field mappings.
This is the core of the "conversational import" feature - users describe their data
and intent, the AI analyzes it, and this transformer applies the mappings.
"""

from typing import Any
from dataclasses import dataclass, field
import logging
import hashlib
import re

from .adapters.base_adapter import (
    ImportItem, Message, MessageRole, ItemType, TaskType, AdapterResult, Feature
)

logger = logging.getLogger(__name__)


@dataclass
class TransformConfig:
    """Configuration for universal transformation."""
    task_type: TaskType = TaskType.MAIL_RATING

    # Field mappings (source -> target)
    field_mapping: dict[str, str] = field(default_factory=dict)

    # Role mappings for conversations
    role_mapping: dict[str, str] = field(default_factory=dict)

    # Paths to important fields (JSONPath-like)
    id_path: str | None = None
    messages_path: str | None = None
    content_path: str | None = None
    role_path: str | None = None
    subject_path: str | None = None
    label_path: str | None = None
    metadata_paths: list[str] = field(default_factory=list)

    # Evaluation criteria (for rating tasks)
    evaluation_criteria: list[str] = field(default_factory=list)

    @classmethod
    def from_ai_analysis(cls, analysis: dict[str, Any]) -> "TransformConfig":
        """Create config from AI analysis result."""
        task_type_str = analysis.get("task_type", "mail_rating")
        try:
            task_type = TaskType(task_type_str)
        except ValueError:
            task_type = TaskType.MAIL_RATING

        return cls(
            task_type=task_type,
            field_mapping=analysis.get("field_mapping", {}),
            role_mapping=analysis.get("role_mapping", {}),
            evaluation_criteria=analysis.get("evaluation_criteria", []),
        )


class UniversalTransformer:
    """
    Transforms arbitrary data structures into LLARS ImportItems.

    Uses AI-generated field mappings to extract and transform data.
    Supports multiple data patterns:
    - Conversations with messages arrays
    - Single text items
    - Q&A pairs
    - Comparison pairs
    """

    # Common role variations to normalize
    ROLE_NORMALIZATIONS = {
        # User roles
        "user": MessageRole.USER,
        "human": MessageRole.USER,
        "client": MessageRole.USER,
        "klient": MessageRole.USER,
        "kunde": MessageRole.USER,
        "ratsuchende": MessageRole.USER,
        "ratsuchender": MessageRole.USER,
        "question": MessageRole.USER,
        "input": MessageRole.USER,

        # Assistant roles
        "assistant": MessageRole.ASSISTANT,
        "bot": MessageRole.ASSISTANT,
        "ai": MessageRole.ASSISTANT,
        "berater": MessageRole.ASSISTANT,
        "beratende": MessageRole.ASSISTANT,
        "beratender": MessageRole.ASSISTANT,
        "agent": MessageRole.ASSISTANT,
        "response": MessageRole.ASSISTANT,
        "answer": MessageRole.ASSISTANT,
        "output": MessageRole.ASSISTANT,

        # System roles
        "system": MessageRole.SYSTEM,
        "instruction": MessageRole.SYSTEM,
    }

    def __init__(self):
        """Initialize the transformer."""
        self._errors: list[str] = []
        self._warnings: list[str] = []

    @staticmethod
    def _to_bool(value: Any) -> bool:
        """Parse bool-like values from JSON payloads safely."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    def transform(
        self,
        data: Any,
        config: TransformConfig | None = None,
        ai_analysis: dict[str, Any] | None = None
    ) -> AdapterResult:
        """
        Transform data into LLARS ImportItems.

        Args:
            data: Raw data (list of items or single item)
            config: Transformation configuration
            ai_analysis: AI analysis result (used if config not provided)

        Returns:
            AdapterResult with transformed items
        """
        self._errors = []
        self._warnings = []

        # Build config from AI analysis if not provided
        if config is None and ai_analysis:
            config = TransformConfig.from_ai_analysis(ai_analysis)
        elif config is None:
            config = TransformConfig()

        items: list[ImportItem] = []

        # Handle different input structures
        if isinstance(data, list):
            for idx, item_data in enumerate(data):
                try:
                    import_item = self._transform_item(item_data, config, idx)
                    if import_item:
                        items.append(import_item)
                except Exception as e:
                    self._warnings.append(f"Failed to transform item {idx}: {str(e)}")
        elif isinstance(data, dict):
            # Check if it's a wrapper with items array
            items_key = self._find_items_key(data)
            if items_key:
                for idx, item_data in enumerate(data[items_key]):
                    try:
                        import_item = self._transform_item(item_data, config, idx)
                        if import_item:
                            items.append(import_item)
                    except Exception as e:
                        self._warnings.append(f"Failed to transform item {idx}: {str(e)}")
            else:
                # Single item
                try:
                    import_item = self._transform_item(data, config, 0)
                    if import_item:
                        items.append(import_item)
                except Exception as e:
                    self._errors.append(f"Failed to transform data: {str(e)}")

        success = len(items) > 0 and len(self._errors) == 0

        return AdapterResult(
            success=success,
            items=items,
            errors=self._errors,
            warnings=self._warnings,
            suggested_task_type=config.task_type,
            stats={
                "total_items": len(items),
                "task_type": config.task_type.value,
            }
        )

    def _transform_item(
        self,
        data: dict[str, Any],
        config: TransformConfig,
        index: int
    ) -> ImportItem | None:
        """Transform a single data item."""
        if not isinstance(data, dict):
            self._warnings.append(f"Item {index} is not a dict, skipping")
            return None

        # Extract ID
        item_id = self._extract_id(data, config, index)

        # Check for ranking with features (source_text + summary_a/b/c pattern)
        if self._is_ranking_with_features(data, config):
            return self._transform_ranking_item(data, config, index, item_id)

        # Determine item type based on data structure and task type
        item_type = self._determine_item_type(data, config)

        # Extract common fields
        subject = self._extract_field(data, ["subject", "title", "topic", "betreff"])
        label = self._extract_field(data, ["label", "class", "category", "ground_truth"])

        # Extract metadata
        metadata = self._extract_metadata(data, config)

        # Create item based on type
        if item_type == ItemType.CONVERSATION:
            messages = self._extract_messages(data, config)
            if not messages:
                self._warnings.append(f"Item {index}: No messages found, using content fallback")
                content = self._extract_content(data)
                if content:
                    return ImportItem(
                        id=item_id,
                        item_type=ItemType.SINGLE_TEXT,
                        content=content,
                        subject=subject,
                        label=str(label) if label is not None else None,
                        metadata=metadata,
                    )
                return None

            return ImportItem(
                id=item_id,
                item_type=ItemType.CONVERSATION,
                conversation=messages,
                subject=subject,
                label=str(label) if label is not None else None,
                metadata=metadata,
            )

        elif item_type == ItemType.SINGLE_TEXT:
            content = self._extract_content(data)
            if not content:
                self._warnings.append(f"Item {index}: No content found")
                return None

            return ImportItem(
                id=item_id,
                item_type=ItemType.SINGLE_TEXT,
                content=content,
                subject=subject,
                label=str(label) if label is not None else None,
                metadata=metadata,
            )

        elif item_type == ItemType.TEXT_PAIR:
            text_a, text_b, label_a, label_b = self._extract_text_pair(data)
            if not text_a or not text_b:
                self._warnings.append(f"Item {index}: Missing text pair")
                return None

            return ImportItem(
                id=item_id,
                item_type=ItemType.TEXT_PAIR,
                text_a=text_a,
                text_b=text_b,
                label_a=label_a,
                label_b=label_b,
                subject=subject,
                label=str(label) if label is not None else None,
                metadata=metadata,
            )

        elif item_type == ItemType.QA_PAIR:
            question, answer = self._extract_qa_pair(data)
            if not question and not answer:
                self._warnings.append(f"Item {index}: No Q&A content found")
                return None

            return ImportItem(
                id=item_id,
                item_type=ItemType.QA_PAIR,
                question=question,
                answer=answer,
                subject=subject,
                label=str(label) if label is not None else None,
                metadata=metadata,
            )

        # Fallback: try to extract any content
        content = self._extract_content(data)
        if content:
            return ImportItem(
                id=item_id,
                item_type=ItemType.CUSTOM,
                content=content,
                subject=subject,
                label=str(label) if label is not None else None,
                metadata=metadata,
            )

        return None

    def _extract_id(
        self,
        data: dict[str, Any],
        config: TransformConfig,
        index: int
    ) -> str:
        """Extract or generate a unique ID."""
        # Try common ID fields
        id_fields = ["id", "conversation_id", "sample_id", "item_id", "uuid", "_id"]

        for field_name in id_fields:
            if field_name in data:
                return str(data[field_name])

        # Check metadata
        if "metadata" in data and isinstance(data["metadata"], dict):
            for field_name in id_fields:
                if field_name in data["metadata"]:
                    return str(data["metadata"][field_name])

            # Create composite ID from metadata
            meta = data["metadata"]
            if "conversation_id" in meta and "sample_id" in meta:
                return f"conv{meta['conversation_id']}_sample{meta['sample_id']}"

        # Generate from content hash
        content_str = str(data)[:500]
        hash_id = hashlib.md5(content_str.encode()).hexdigest()[:12]
        return f"item_{index}_{hash_id}"

    def _determine_item_type(
        self,
        data: dict[str, Any],
        config: TransformConfig
    ) -> ItemType:
        """Determine the item type based on data structure and task type."""
        # Check for messages array (conversation)
        messages_keys = ["messages", "conversation", "turns", "dialogue", "chat"]
        for key in messages_keys:
            if key in data and isinstance(data[key], list):
                return ItemType.CONVERSATION

        # Check task type hints
        if config.task_type in [TaskType.COMPARISON]:
            # Look for comparison structure
            if any(k in data for k in ["text_a", "text_b", "response_a", "response_b", "chosen", "rejected"]):
                return ItemType.TEXT_PAIR

        if config.task_type in [TaskType.AUTHENTICITY, TaskType.MAIL_RATING]:
            # These usually work with conversations
            for key in messages_keys:
                if key in data:
                    return ItemType.CONVERSATION

        # Check for Q&A structure
        if any(k in data for k in ["question", "query", "prompt"]) and any(k in data for k in ["answer", "response", "output"]):
            return ItemType.QA_PAIR

        # Check for text pair structure
        if any(k in data for k in ["text_a", "text_b", "chosen", "rejected"]):
            return ItemType.TEXT_PAIR

        # Default based on task type
        task_type_defaults = {
            TaskType.MAIL_RATING: ItemType.CONVERSATION,
            TaskType.RATING: ItemType.SINGLE_TEXT,
            TaskType.RANKING: ItemType.SINGLE_TEXT,
            TaskType.COMPARISON: ItemType.TEXT_PAIR,
            TaskType.AUTHENTICITY: ItemType.CONVERSATION,
            TaskType.LABELING: ItemType.SINGLE_TEXT,
            TaskType.TEXT_CLASSIFICATION: ItemType.SINGLE_TEXT,  # legacy alias
            TaskType.TEXT_RATING: ItemType.SINGLE_TEXT,  # legacy alias
        }

        return task_type_defaults.get(config.task_type, ItemType.CONVERSATION)

    def _extract_messages(
        self,
        data: dict[str, Any],
        config: TransformConfig
    ) -> list[Message]:
        """Extract messages from conversation data."""
        messages: list[Message] = []

        # Find messages array
        messages_keys = ["messages", "conversation", "turns", "dialogue", "chat"]
        raw_messages = None

        for key in messages_keys:
            if key in data and isinstance(data[key], list):
                raw_messages = data[key]
                break

        if not raw_messages:
            return messages

        for msg in raw_messages:
            if not isinstance(msg, dict):
                continue

            # Extract role
            role = self._extract_message_role(msg, config)

            # Extract content
            content = self._extract_field(msg, ["content", "text", "message", "body"])
            if not content:
                continue

            # Extract timestamp
            timestamp = self._extract_field(msg, ["timestamp", "created_at", "time", "date"])

            # Build metadata from remaining fields
            msg_metadata = {}
            for key in ["is_synthetic", "generated_by", "message_id", "type"]:
                if key in msg:
                    msg_metadata[key] = msg[key]

            messages.append(Message(
                role=role,
                content=str(content),
                timestamp=str(timestamp) if timestamp else None,
                metadata=msg_metadata if msg_metadata else {},
            ))

        return messages

    def _extract_message_role(
        self,
        msg: dict[str, Any],
        config: TransformConfig
    ) -> MessageRole:
        """Extract and normalize message role."""
        # Find role field
        role_value = self._extract_field(msg, ["role", "sender", "from", "author", "type"])

        if not role_value:
            return MessageRole.USER

        role_str = str(role_value).lower().strip()

        # Check custom role mapping first
        if config.role_mapping:
            for source, target in config.role_mapping.items():
                if role_str == source.lower():
                    target_lower = target.lower()
                    if target_lower in self.ROLE_NORMALIZATIONS:
                        return self.ROLE_NORMALIZATIONS[target_lower]

        # Check standard normalizations
        if role_str in self.ROLE_NORMALIZATIONS:
            return self.ROLE_NORMALIZATIONS[role_str]

        # Heuristics for German roles
        if "rat" in role_str or "such" in role_str or "kund" in role_str:
            return MessageRole.USER
        if "berat" in role_str or "agent" in role_str:
            return MessageRole.ASSISTANT

        # Default to USER for unknown roles
        return MessageRole.USER

    def _extract_content(self, data: dict[str, Any]) -> str | None:
        """Extract main content from data."""
        content_keys = ["content", "text", "body", "message", "document", "input", "output"]

        for key in content_keys:
            if key in data and data[key]:
                return str(data[key])

        # Try nested conversation content
        if "messages" in data and isinstance(data["messages"], list) and data["messages"]:
            # Concatenate all messages
            parts = []
            for msg in data["messages"]:
                if isinstance(msg, dict):
                    content = self._extract_field(msg, ["content", "text", "message"])
                    if content:
                        role = self._extract_field(msg, ["role", "sender"])
                        if role:
                            parts.append(f"[{role}]: {content}")
                        else:
                            parts.append(str(content))
            if parts:
                return "\n\n".join(parts)

        return None

    def _extract_text_pair(
        self,
        data: dict[str, Any]
    ) -> tuple[str | None, str | None, str | None, str | None]:
        """Extract text pair for comparison."""
        # Try standard A/B naming
        text_a = self._extract_field(data, ["text_a", "response_a", "output_a", "chosen", "preferred"])
        text_b = self._extract_field(data, ["text_b", "response_b", "output_b", "rejected", "dispreferred"])

        label_a = "A"
        label_b = "B"

        # Check for model names as labels
        if "model_a" in data:
            label_a = str(data["model_a"])
        if "model_b" in data:
            label_b = str(data["model_b"])

        # Handle chosen/rejected format
        if text_a and "chosen" in str(data.keys()).lower():
            label_a = "Chosen"
            label_b = "Rejected"

        return str(text_a) if text_a else None, str(text_b) if text_b else None, label_a, label_b

    def _extract_qa_pair(
        self,
        data: dict[str, Any]
    ) -> tuple[str | None, str | None]:
        """Extract question-answer pair."""
        question = self._extract_field(data, ["question", "query", "prompt", "input", "instruction"])
        answer = self._extract_field(data, ["answer", "response", "output", "completion", "reply"])

        return str(question) if question else None, str(answer) if answer else None

    def _extract_field(
        self,
        data: dict[str, Any],
        field_names: list[str]
    ) -> Any | None:
        """Extract first matching field from data."""
        for name in field_names:
            # Direct field access
            if name in data:
                return data[name]

            # Case-insensitive search
            for key in data.keys():
                if key.lower() == name.lower():
                    return data[key]

        return None

    def _extract_metadata(
        self,
        data: dict[str, Any],
        config: TransformConfig
    ) -> dict[str, Any]:
        """Extract metadata from data."""
        metadata: dict[str, Any] = {}

        # Extract from explicit metadata field
        if "metadata" in data and isinstance(data["metadata"], dict):
            metadata.update(data["metadata"])

        # Extract specific fields that should be preserved
        preserve_fields = [
            "is_synthetic", "augmentation_type", "model", "model_short",
            "generated_at", "format_version", "saeule", "split",
            "source_conversation_id", "num_replacements", "replaced_positions"
        ]

        for field_name in preserve_fields:
            if field_name in data:
                metadata[field_name] = data[field_name]

        return metadata

    def _find_items_key(self, data: dict[str, Any]) -> str | None:
        """Find the key containing the items array."""
        items_keys = ["items", "data", "records", "rows", "samples", "examples"]

        for key in items_keys:
            if key in data and isinstance(data[key], list):
                return key

        return None

    def _detect_ranking_features(
        self,
        data: dict[str, Any],
        split_by_prompt: bool = False
    ) -> tuple[str | None, list[Feature]]:
        """
        Detect ranking format with reference text and multiple features to rank.

        Supports patterns like:
        - source_text + summary_a/b/c
        - reference + response_1/2/3
        - article + text_a/b/c
        - original + summary_1/summary_2/summary_3

        Returns:
            Tuple of (reference_text, list of Features)
        """
        # Reference field patterns (the context/source shown on right side)
        reference_patterns = [
            "source_text", "source", "reference", "article", "original",
            "document", "context", "input_text", "text"
        ]

        # Find reference text
        reference_text = None
        for pattern in reference_patterns:
            if pattern in data and data[pattern]:
                reference_text = str(data[pattern])
                break
            # Case-insensitive
            for key in data.keys():
                if key.lower() == pattern.lower() and data[key]:
                    reference_text = str(data[key])
                    break
            if reference_text:
                break

        # Feature field patterns (items to rank, shown on left side)
        # Pattern: prefix + suffix (e.g., summary_a, response_1)
        feature_prefixes = [
            "summary", "response", "output", "text", "answer",
            "generation", "completion", "result"
        ]
        feature_suffixes = ["_a", "_b", "_c", "_d", "_e", "_1", "_2", "_3", "_4", "_5"]

        features: list[Feature] = []
        found_keys: set[str] = set()

        # Search for pattern-based features
        for prefix in feature_prefixes:
            for suffix in feature_suffixes:
                key_patterns = [
                    f"{prefix}{suffix}",           # summary_a
                    f"{prefix.title()}{suffix}",   # Summary_a
                    f"{prefix.upper()}{suffix}",   # SUMMARY_a
                ]

                for key_pattern in key_patterns:
                    # Direct match
                    if key_pattern in data and data[key_pattern] and key_pattern not in found_keys:
                        # Generate a label from suffix (A, B, C or 1, 2, 3)
                        label_char = suffix[-1].upper()
                        features.append(Feature(
                            type="Summary",
                            content=str(data[key_pattern]),
                            generated_by=f"Model_{label_char}"
                        ))
                        found_keys.add(key_pattern)
                        break

                    # Case-insensitive search
                    for actual_key in data.keys():
                        if actual_key.lower() == key_pattern.lower() and actual_key not in found_keys:
                            if data[actual_key]:
                                label_char = suffix[-1].upper()
                                features.append(Feature(
                                    type="Summary",
                                    content=str(data[actual_key]),
                                    generated_by=f"Model_{label_char}"
                                ))
                                found_keys.add(actual_key)
                                break

        # Also check for numbered/lettered items array (summaries: [...])
        array_keys = ["summaries", "responses", "outputs", "items", "texts"]
        for array_key in array_keys:
            if array_key in data and isinstance(data[array_key], list):
                for idx, item in enumerate(data[array_key]):
                    if item:
                        label_char = chr(65 + idx)  # A, B, C, ...
                        content = str(item) if isinstance(item, str) else item.get("content", item.get("text", str(item)))
                        generated_by = item.get("model", item.get("source", f"Model_{label_char}")) if isinstance(item, dict) else f"Model_{label_char}"
                        features.append(Feature(
                            type="Summary",
                            content=content,
                            generated_by=generated_by
                        ))

        # Enrich with actual model names (and optional prompt-based feature types) from metadata.
        if "metadata" in data and isinstance(data["metadata"], dict):
            metadata = data["metadata"]
            for i, feature in enumerate(features):
                suffix = chr(97 + i)  # a, b, c, d, ...
                model_key = f"model_{suffix}"
                if model_key in metadata and metadata[model_key]:
                    feature.generated_by = str(metadata[model_key])

                if split_by_prompt:
                    prompt_key = f"prompt_{suffix}"
                    prompt_label = metadata.get(prompt_key)
                    if prompt_label:
                        feature.type = str(prompt_label).strip() or feature.type

        logger.info(
            f"Ranking features detected: {len(features)} features, "
            f"keys={list(found_keys)}, reference={'found' if reference_text else 'missing'}, "
            f"split_by_prompt={split_by_prompt}"
        )

        return reference_text, features

    def _is_ranking_with_features(self, data: dict[str, Any], config: TransformConfig) -> bool:
        """
        Check if data has ranking format with multiple features.

        Returns True if:
        - task_type is RANKING
        - Data has reference + multiple feature fields (summary_a/b/c, etc.)
        """
        if config.task_type != TaskType.RANKING:
            return False

        split_by_prompt = self._to_bool((config.field_mapping or {}).get("split_by_prompt"))
        reference_text, features = self._detect_ranking_features(
            data,
            split_by_prompt=split_by_prompt
        )
        return reference_text is not None and len(features) >= 2

    def _transform_ranking_item(
        self,
        data: dict[str, Any],
        config: TransformConfig,
        index: int,
        item_id: str
    ) -> ImportItem | None:
        """
        Transform ranking data with reference text and multiple features.

        Creates an ImportItem with:
        - content: The reference/source text (shown on right side)
        - features: List of Feature objects to rank (shown on left side)
        """
        split_by_prompt = self._to_bool((config.field_mapping or {}).get("split_by_prompt"))
        reference_text, features = self._detect_ranking_features(
            data,
            split_by_prompt=split_by_prompt
        )

        if not reference_text:
            self._warnings.append(f"Item {index}: No reference text found for ranking")
            return None

        if len(features) < 2:
            self._warnings.append(f"Item {index}: Need at least 2 features for ranking, found {len(features)}")
            return None

        # Extract common fields
        subject = self._extract_field(data, ["subject", "title", "topic", "betreff"])
        label = self._extract_field(data, ["label", "class", "category", "ground_truth"])
        metadata = self._extract_metadata(data, config)

        # Add ranking-specific metadata
        metadata["ranking_features_count"] = len(features)
        metadata["has_reference"] = True

        logger.info(f"Item {index}: Created ranking item with {len(features)} features")

        return ImportItem(
            id=item_id,
            item_type=ItemType.SINGLE_TEXT,  # Reference is single text
            content=reference_text,
            features=features,
            subject=subject,
            label=str(label) if label is not None else None,
            metadata=metadata,
        )


def transform_with_ai_analysis(
    data: Any,
    ai_analysis: dict[str, Any]
) -> AdapterResult:
    """
    Convenience function to transform data using AI analysis.

    Args:
        data: Raw data to transform
        ai_analysis: Result from AIAnalyzer.analyze_intent()

    Returns:
        AdapterResult with transformed items
    """
    transformer = UniversalTransformer()
    return transformer.transform(data, ai_analysis=ai_analysis)
