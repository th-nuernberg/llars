"""
Format Detector for automatic data format recognition.

Analyzes uploaded data and determines the best adapter to use.
"""

from typing import Any
import json
import csv
import io
import logging

from .adapters import (
    BaseAdapter,
    LLARSAdapter,
    OpenAIAdapter,
    JSONLAdapter,
    CSVAdapter,
    LMSYSAdapter,
    GenericAdapter,
)

logger = logging.getLogger(__name__)


class FormatDetector:
    """
    Automatic format detection for uploaded data.

    Tests data against all registered adapters and returns
    the best match with confidence score.
    """

    def __init__(self):
        """Initialize with all available adapters."""
        self._adapters: list[BaseAdapter] = [
            LLARSAdapter(),
            LMSYSAdapter(),  # Check before OpenAI (more specific)
            OpenAIAdapter(),
            JSONLAdapter(),
            CSVAdapter(),
            GenericAdapter(),  # Fallback adapter for text-based data
        ]

    @property
    def available_formats(self) -> list[dict[str, Any]]:
        """Get list of all available format adapters."""
        return [adapter.get_info() for adapter in self._adapters]

    def detect(self, data: Any) -> dict[str, Any]:
        """
        Detect the format of the given data.

        Args:
            data: Parsed data (dict, list, or raw string)

        Returns:
            Dictionary with detection results
        """
        results: list[dict[str, Any]] = []

        for adapter in self._adapters:
            try:
                can_handle, confidence = adapter.can_handle(data)
                if can_handle:
                    results.append({
                        "format_id": adapter.FORMAT_ID,
                        "format_name": adapter.FORMAT_NAME,
                        "confidence": confidence,
                        "adapter": adapter,
                    })
            except Exception as e:
                logger.warning(f"Error checking adapter {adapter.FORMAT_ID}: {e}")

        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)

        if not results:
            return {
                "detected": False,
                "format_id": None,
                "format_name": None,
                "confidence": 0.0,
                "alternatives": [],
                "message": "Could not detect data format",
            }

        best = results[0]
        return {
            "detected": True,
            "format_id": best["format_id"],
            "format_name": best["format_name"],
            "confidence": best["confidence"],
            "alternatives": [
                {
                    "format_id": r["format_id"],
                    "format_name": r["format_name"],
                    "confidence": r["confidence"],
                }
                for r in results[1:3]  # Top 3 alternatives
            ],
            "adapter": best["adapter"],
        }

    def detect_from_file(
        self,
        content: str | bytes,
        filename: str,
        content_type: str | None = None
    ) -> dict[str, Any]:
        """
        Detect format from file content.

        Args:
            content: File content as string or bytes
            filename: Original filename
            content_type: MIME type if known

        Returns:
            Detection result with parsed data
        """
        # Decode bytes if needed
        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                content = content.decode('latin-1')

        # Determine file type from extension
        ext = filename.lower().split('.')[-1] if '.' in filename else ''

        parsed_data = None
        parse_error = None

        # Try parsing based on extension
        if ext in ['json']:
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError as e:
                parse_error = f"JSON parse error: {str(e)}"

        elif ext in ['jsonl', 'ndjson']:
            try:
                lines = content.strip().split('\n')
                parsed_data = [json.loads(line) for line in lines if line.strip()]
            except json.JSONDecodeError as e:
                parse_error = f"JSONL parse error: {str(e)}"

        elif ext in ['csv']:
            try:
                reader = csv.DictReader(io.StringIO(content))
                parsed_data = list(reader)
            except Exception as e:
                parse_error = f"CSV parse error: {str(e)}"

        elif ext in ['tsv']:
            try:
                reader = csv.DictReader(io.StringIO(content), delimiter='\t')
                parsed_data = list(reader)
            except Exception as e:
                parse_error = f"TSV parse error: {str(e)}"

        else:
            # Try JSON first, then JSONL
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                try:
                    lines = content.strip().split('\n')
                    if len(lines) > 1:
                        parsed_data = [json.loads(line) for line in lines if line.strip()]
                    else:
                        parse_error = "Could not parse as JSON or JSONL"
                except json.JSONDecodeError:
                    parse_error = "Could not parse file content"

        if parse_error:
            return {
                "detected": False,
                "parse_error": parse_error,
                "filename": filename,
            }

        # Now detect format
        result = self.detect(parsed_data)
        result["filename"] = filename
        result["extension"] = ext
        result["data"] = parsed_data

        # Add structure analysis if detection succeeded
        if result["detected"] and "adapter" in result:
            adapter = result["adapter"]
            result["structure"] = adapter.detect_structure(parsed_data)
            # Don't include adapter in response (not serializable)
            del result["adapter"]

        return result

    def get_adapter(self, format_id: str) -> BaseAdapter | None:
        """Get adapter by format ID."""
        for adapter in self._adapters:
            if adapter.FORMAT_ID == format_id:
                return adapter
        return None

    def get_adapter_for_data(self, data: Any) -> BaseAdapter | None:
        """Get the best adapter for the given data."""
        result = self.detect(data)
        if result["detected"]:
            return result.get("adapter")
        return None
