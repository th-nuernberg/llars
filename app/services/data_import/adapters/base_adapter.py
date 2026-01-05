"""
Base Adapter for data import transformations.

All format-specific adapters inherit from this class.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class TaskType(str, Enum):
    """Supported evaluation task types."""
    RATING = "rating"
    RANKING = "ranking"
    MAIL_RATING = "mail_rating"
    COMPARISON = "comparison"
    AUTHENTICITY = "authenticity"
    JUDGE = "judge"
    TEXT_CLASSIFICATION = "text_classification"
    TEXT_RATING = "text_rating"


class ItemType(str, Enum):
    """Type of data item being imported."""
    CONVERSATION = "conversation"      # Multi-turn chat/email
    SINGLE_TEXT = "single_text"        # Single text to evaluate
    QA_PAIR = "qa_pair"                # Question + Answer
    TEXT_PAIR = "text_pair"            # Two texts for comparison (A/B)
    DOCUMENT = "document"              # Long-form document
    CUSTOM = "custom"                  # Custom structure


class MessageRole(str, Enum):
    """Standard message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """A single message in a conversation."""
    role: MessageRole
    content: str
    timestamp: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.timestamp:
            result["timestamp"] = self.timestamp
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class Feature:
    """An LLM-generated feature for a conversation."""
    type: str
    content: str
    generated_by: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "type": self.type,
            "content": self.content,
        }
        if self.generated_by:
            result["generated_by"] = self.generated_by
        return result


@dataclass
class ImportItem:
    """
    A single item to be imported.

    Supports multiple data types:
    - CONVERSATION: Multi-turn chat (uses `conversation` field)
    - SINGLE_TEXT: Single text to evaluate (uses `content` field)
    - QA_PAIR: Question + Answer (uses `question` + `answer` fields)
    - TEXT_PAIR: Two texts for comparison (uses `text_a` + `text_b` fields)
    - DOCUMENT: Long-form document (uses `content` field)
    """
    id: str
    item_type: ItemType = ItemType.CONVERSATION

    # For CONVERSATION type
    conversation: list[Message] = field(default_factory=list)

    # For SINGLE_TEXT and DOCUMENT types
    content: str | None = None

    # For QA_PAIR type
    question: str | None = None
    answer: str | None = None

    # For TEXT_PAIR type (A/B comparison)
    text_a: str | None = None
    text_b: str | None = None
    label_a: str | None = None  # e.g., "GPT-4", "Human", "Version A"
    label_b: str | None = None

    # Common fields
    subject: str | None = None
    title: str | None = None
    category: str | None = None
    label: str | None = None  # Ground truth label if available
    features: list[Feature] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "id": self.id,
            "item_type": self.item_type.value,
        }

        # Add type-specific fields
        if self.item_type == ItemType.CONVERSATION and self.conversation:
            result["conversation"] = [msg.to_dict() for msg in self.conversation]
        if self.content:
            result["content"] = self.content
        if self.question:
            result["question"] = self.question
        if self.answer:
            result["answer"] = self.answer
        if self.text_a:
            result["text_a"] = self.text_a
        if self.text_b:
            result["text_b"] = self.text_b
        if self.label_a:
            result["label_a"] = self.label_a
        if self.label_b:
            result["label_b"] = self.label_b

        # Common fields
        if self.subject:
            result["subject"] = self.subject
        if self.title:
            result["title"] = self.title
        if self.category:
            result["category"] = self.category
        if self.label:
            result["label"] = self.label
        if self.features:
            result["features"] = [f.to_dict() for f in self.features]
        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def get_display_content(self) -> str:
        """Get the primary content for display/preview."""
        if self.item_type == ItemType.CONVERSATION and self.conversation:
            # Return first message content
            return self.conversation[0].content[:200] if self.conversation else ""
        if self.content:
            return self.content[:200]
        if self.question:
            return self.question[:200]
        if self.text_a:
            return self.text_a[:200]
        return ""

    @classmethod
    def from_single_text(cls, id: str, content: str, **kwargs) -> "ImportItem":
        """Create an item from a single text."""
        return cls(
            id=id,
            item_type=ItemType.SINGLE_TEXT,
            content=content,
            **kwargs
        )

    @classmethod
    def from_qa_pair(cls, id: str, question: str, answer: str, **kwargs) -> "ImportItem":
        """Create an item from a Q&A pair."""
        return cls(
            id=id,
            item_type=ItemType.QA_PAIR,
            question=question,
            answer=answer,
            **kwargs
        )

    @classmethod
    def from_text_pair(
        cls, id: str, text_a: str, text_b: str,
        label_a: str = "A", label_b: str = "B", **kwargs
    ) -> "ImportItem":
        """Create an item from two texts for comparison."""
        return cls(
            id=id,
            item_type=ItemType.TEXT_PAIR,
            text_a=text_a,
            text_b=text_b,
            label_a=label_a,
            label_b=label_b,
            **kwargs
        )

    @classmethod
    def from_conversation(cls, id: str, messages: list[Message], **kwargs) -> "ImportItem":
        """Create an item from a conversation."""
        return cls(
            id=id,
            item_type=ItemType.CONVERSATION,
            conversation=messages,
            **kwargs
        )


@dataclass
class AdapterResult:
    """Result of an adapter transformation."""
    success: bool
    items: list[ImportItem] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggested_task_type: TaskType | None = None
    stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "success": self.success,
            "items": [item.to_dict() for item in self.items],
            "errors": self.errors,
            "warnings": self.warnings,
            "suggested_task_type": self.suggested_task_type.value if self.suggested_task_type else None,
            "stats": self.stats,
        }


class BaseAdapter(ABC):
    """
    Abstract base class for format adapters.

    Each adapter transforms a specific format into LLARS ImportItems.
    """

    # Format identifier
    FORMAT_ID: str = "base"
    FORMAT_NAME: str = "Base Format"
    FORMAT_DESCRIPTION: str = "Base adapter - not for direct use"

    # File extensions this adapter can handle
    SUPPORTED_EXTENSIONS: list[str] = []

    def __init__(self):
        """Initialize the adapter."""
        self._errors: list[str] = []
        self._warnings: list[str] = []

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self._errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self._warnings.append(message)

    def clear_messages(self) -> None:
        """Clear error and warning messages."""
        self._errors = []
        self._warnings = []

    @abstractmethod
    def can_handle(self, data: Any) -> tuple[bool, float]:
        """
        Check if this adapter can handle the given data.

        Args:
            data: The raw data to check

        Returns:
            Tuple of (can_handle, confidence) where confidence is 0.0-1.0
        """
        pass

    @abstractmethod
    def detect_structure(self, data: Any) -> dict[str, Any]:
        """
        Analyze the data structure and return detected fields.

        Args:
            data: The raw data to analyze

        Returns:
            Dictionary with detected structure information
        """
        pass

    @abstractmethod
    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """
        Transform the data into LLARS ImportItems.

        Args:
            data: The raw data to transform
            options: Optional transformation options (field mappings, etc.)

        Returns:
            AdapterResult with transformed items or errors
        """
        pass

    def get_sample(self, data: Any, count: int = 5) -> list[dict[str, Any]]:
        """
        Get a sample of items for preview.

        Args:
            data: The raw data
            count: Number of items to return

        Returns:
            List of sample items as dictionaries
        """
        result = self.transform(data)
        sample_items = result.items[:count]
        return [item.to_dict() for item in sample_items]

    @classmethod
    def get_info(cls) -> dict[str, Any]:
        """Get adapter information."""
        return {
            "format_id": cls.FORMAT_ID,
            "format_name": cls.FORMAT_NAME,
            "description": cls.FORMAT_DESCRIPTION,
            "extensions": cls.SUPPORTED_EXTENSIONS,
        }
