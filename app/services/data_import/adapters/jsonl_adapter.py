"""
JSONL (JSON Lines) Format Adapter.

Handles data where each line is a separate JSON object.
"""

from typing import Any
import logging

from .base_adapter import (
    BaseAdapter,
    AdapterResult,
    ImportItem,
    TaskType,
)
from .openai_adapter import OpenAIAdapter

logger = logging.getLogger(__name__)


class JSONLAdapter(BaseAdapter):
    """Adapter for JSONL format (JSON Lines)."""

    FORMAT_ID = "jsonl"
    FORMAT_NAME = "JSONL (JSON Lines)"
    FORMAT_DESCRIPTION = "One JSON object per line, commonly used for large datasets"
    SUPPORTED_EXTENSIONS = [".jsonl", ".ndjson"]

    def __init__(self):
        """Initialize the adapter."""
        super().__init__()
        # Delegate to OpenAI adapter for actual parsing
        self._openai_adapter = OpenAIAdapter()

    def can_handle(self, data: Any) -> tuple[bool, float]:
        """
        Check if data is in JSONL format.

        Note: By the time data reaches here, it should already be parsed
        into a list of objects (one per line).
        """
        if isinstance(data, list) and data:
            # JSONL is just a list of objects
            if all(isinstance(item, dict) for item in data[:5]):
                # Check if it looks like conversations
                can_handle, confidence = self._openai_adapter.can_handle(data)
                if can_handle:
                    return True, confidence * 0.9  # Slightly lower than pure OpenAI
        return False, 0.0

    def detect_structure(self, data: Any) -> dict[str, Any]:
        """Analyze JSONL structure."""
        base_structure = self._openai_adapter.detect_structure(data)
        base_structure["format"] = self.FORMAT_ID
        base_structure["line_count"] = len(data) if isinstance(data, list) else 0
        return base_structure

    def transform(self, data: Any, options: dict[str, Any] | None = None) -> AdapterResult:
        """Transform JSONL to LLARS ImportItems."""
        # Delegate to OpenAI adapter
        result = self._openai_adapter.transform(data, options)

        # Update stats
        result.stats["source_format"] = self.FORMAT_ID

        return result
