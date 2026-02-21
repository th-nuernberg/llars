"""
Data Preprocessor for AI Scenario Analysis.

Provides intelligent preprocessing of uploaded data for LLM analysis:
- Recursive schema extraction (nested structures)
- Representative sample selection
- Smart truncation that preserves structure
- Statistics computation
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import Counter


class DataPreprocessor:
    """
    Preprocesses uploaded data for AI-powered scenario analysis.

    Extracts schema information, selects representative samples,
    and prepares data in a format optimal for LLM understanding.
    """

    # Max characters for content fields when truncating
    MAX_CONTENT_LENGTH = 300
    # Max items to analyze for schema detection
    MAX_ITEMS_FOR_SCHEMA = 50
    # Max sample items to include
    MAX_SAMPLE_ITEMS = 3

    @classmethod
    def preprocess(cls, items: List[Dict], filename: str = "data") -> Dict[str, Any]:
        """
        Main preprocessing entry point.

        Args:
            items: List of data items (dicts)
            filename: Original filename for context

        Returns:
            Preprocessed data structure for LLM prompt
        """
        if not items:
            return {
                "item_count": 0,
                "schema": {},
                "samples": [],
                "statistics": {},
                "detected_patterns": []
            }

        # 1. Extract recursive schema
        schema = cls.extract_schema(items[:cls.MAX_ITEMS_FOR_SCHEMA])

        # 2. Detect data patterns (comparison, conversation, labels, etc.)
        patterns = cls.detect_patterns(items[:cls.MAX_ITEMS_FOR_SCHEMA], schema)

        # 3. Select representative samples
        samples = cls.select_representative_samples(items, schema)

        # 4. Compute statistics
        statistics = cls.compute_statistics(items, schema)

        # 5. Truncate samples intelligently
        truncated_samples = [cls.truncate_item(s, schema) for s in samples]

        return {
            "item_count": len(items),
            "filename": filename,
            "schema": schema,
            "samples": truncated_samples,
            "statistics": statistics,
            "detected_patterns": patterns
        }

    @classmethod
    def extract_schema(cls, items: List[Dict]) -> Dict[str, Any]:
        """
        Recursively extract schema from items.

        Returns a schema dict like:
        {
            "field_name": {
                "type": "string|number|boolean|array|object|null|mixed",
                "nullable": True/False,
                "completeness": 0.0-1.0,
                "children": {...}  # For objects
                "items_schema": {...}  # For arrays
                "enum_values": [...]  # For detected enums
                "avg_length": N  # For strings
            }
        }
        """
        if not items:
            return {}

        schema = {}
        all_keys = set()

        # Collect all keys across items
        for item in items:
            if isinstance(item, dict):
                all_keys.update(item.keys())

        for key in all_keys:
            values = [item.get(key) for item in items if isinstance(item, dict)]
            schema[key] = cls._analyze_field(key, values, len(items))

        return schema

    @classmethod
    def _analyze_field(cls, field_name: str, values: List[Any], total_count: int) -> Dict[str, Any]:
        """Analyze a single field across all items."""
        non_null = [v for v in values if v is not None]

        if not non_null:
            return {
                "type": "null",
                "nullable": True,
                "completeness": 0.0
            }

        # Determine type(s)
        types = set()
        for v in non_null:
            types.add(cls._get_type(v))

        field_type = list(types)[0] if len(types) == 1 else "mixed"

        result = {
            "type": field_type,
            "nullable": len(non_null) < len(values),
            "completeness": round(len(non_null) / total_count, 2) if total_count > 0 else 0
        }

        # Type-specific analysis
        if field_type == "string":
            result.update(cls._analyze_string_field(non_null))
        elif field_type == "array":
            result.update(cls._analyze_array_field(non_null))
        elif field_type == "object":
            result.update(cls._analyze_object_field(non_null))
        elif field_type == "number":
            result.update(cls._analyze_number_field(non_null))
        elif field_type == "boolean":
            result["values"] = list(set(non_null))

        return result

    @classmethod
    def _get_type(cls, value: Any) -> str:
        """Get the type string for a value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, (int, float)):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"

    @classmethod
    def _analyze_string_field(cls, values: List[str]) -> Dict[str, Any]:
        """Analyze string field for patterns."""
        result = {}

        # Calculate average length
        lengths = [len(v) for v in values if isinstance(v, str)]
        if lengths:
            result["avg_length"] = round(sum(lengths) / len(lengths))
            result["max_length"] = max(lengths)
            result["min_length"] = min(lengths)

        # Check for enum pattern (few unique values)
        unique_values = list(set(v for v in values if isinstance(v, str)))
        if len(unique_values) <= 10 and len(unique_values) < len(values) * 0.3:
            result["enum_values"] = unique_values[:10]
        else:
            # Sample some values
            result["sample_values"] = unique_values[:3]

        return result

    @classmethod
    def _analyze_array_field(cls, values: List[List]) -> Dict[str, Any]:
        """Analyze array field structure."""
        result = {}

        # Get array lengths
        lengths = [len(v) for v in values if isinstance(v, list)]
        if lengths:
            result["avg_items"] = round(sum(lengths) / len(lengths), 1)
            result["max_items"] = max(lengths)
            result["min_items"] = min(lengths)

        # Analyze array item schema (from first few arrays)
        all_items = []
        for arr in values[:10]:
            if isinstance(arr, list):
                all_items.extend(arr[:5])  # First 5 items from each array

        if all_items:
            # Check if items are objects
            if all(isinstance(item, dict) for item in all_items[:10]):
                result["items_schema"] = cls.extract_schema(all_items[:20])
            else:
                # Primitive array
                item_types = set(cls._get_type(item) for item in all_items[:20])
                result["items_type"] = list(item_types)[0] if len(item_types) == 1 else "mixed"

        return result

    @classmethod
    def _analyze_object_field(cls, values: List[Dict]) -> Dict[str, Any]:
        """Analyze nested object field."""
        result = {}

        # Extract nested schema
        nested_items = [v for v in values if isinstance(v, dict)]
        if nested_items:
            result["children"] = cls.extract_schema(nested_items[:20])

        return result

    @classmethod
    def _analyze_number_field(cls, values: List[Union[int, float]]) -> Dict[str, Any]:
        """Analyze number field."""
        numbers = [v for v in values if isinstance(v, (int, float))]
        if not numbers:
            return {}

        return {
            "min": min(numbers),
            "max": max(numbers),
            "is_integer": all(isinstance(v, int) or v == int(v) for v in numbers)
        }

    @classmethod
    def detect_patterns(cls, items: List[Dict], schema: Dict) -> List[str]:
        """
        Detect common data patterns for evaluation type hints.

        Returns list of detected patterns like:
        - "comparison_pairs": Has answer_a/answer_b structure
        - "conversation": Has messages array with role/content
        - "labels": Has label/category/is_* fields
        - "rating_scores": Has numeric score/rating fields
        """
        patterns = []
        field_names = set(schema.keys())
        field_names_lower = {f.lower() for f in field_names}

        # Pattern: Comparison pairs (A vs B)
        comparison_indicators = [
            ('answer_a', 'answer_b'),
            ('text_a', 'text_b'),
            ('response_a', 'response_b'),
            ('conversation_a', 'conversation_b'),
            ('model_a', 'model_b'),
            ('output_a', 'output_b'),
        ]
        for a, b in comparison_indicators:
            if a in field_names_lower and b in field_names_lower:
                patterns.append(f"comparison_pairs:{a}/{b}")
                break

        # Pattern: Conversation/Messages
        for field, info in schema.items():
            if info.get("type") == "array":
                items_schema = info.get("items_schema", {})
                if "role" in items_schema and "content" in items_schema:
                    patterns.append(f"conversation:{field}")
                elif "role" in items_schema or "speaker" in items_schema:
                    patterns.append(f"dialogue:{field}")

        # Pattern: Labels/Categories
        label_fields = []
        for field in field_names:
            lower = field.lower()
            if lower in ('label', 'labels', 'category', 'categories', 'class', 'sentiment'):
                label_fields.append(field)
            elif lower.startswith('is_') or lower.startswith('has_'):
                label_fields.append(field)
        if label_fields:
            patterns.append(f"labels:{','.join(label_fields)}")

        # Pattern: Authenticity indicators
        auth_fields = {'is_human', 'is_fake', 'is_synthetic', 'is_ai', 'is_generated', 'human', 'synthetic'}
        if auth_fields & field_names_lower:
            patterns.append("authenticity_labels")

        # Pattern: Rating/Score fields
        score_fields = []
        for field, info in schema.items():
            lower = field.lower()
            if info.get("type") == "number":
                if any(kw in lower for kw in ['score', 'rating', 'rank', 'quality']):
                    score_fields.append(field)
        if score_fields:
            patterns.append(f"scores:{','.join(score_fields)}")

        # Pattern: Winner/Preference field
        winner_fields = {'winner', 'preference', 'chosen', 'selected', 'better'}
        if winner_fields & field_names_lower:
            patterns.append("winner_field")

        # Pattern: Email/Thread structure
        email_fields = {'subject', 'thread_id', 'email_id', 'mail_id'}
        if email_fields & field_names_lower:
            patterns.append("email_structure")

        return patterns

    @classmethod
    def select_representative_samples(cls, items: List[Dict], schema: Dict) -> List[Dict]:
        """
        Select representative samples from the data.

        Strategy:
        - 1 item with minimal complexity (shortest content)
        - 1 item with typical complexity (median)
        - 1 item with maximum complexity (longest content, most fields)
        """
        if not items:
            return []

        if len(items) <= cls.MAX_SAMPLE_ITEMS:
            return items.copy()

        # Calculate complexity score for each item
        scored_items = []
        for i, item in enumerate(items[:100]):  # Only score first 100 for performance
            score = cls._calculate_complexity(item)
            scored_items.append((i, score, item))

        scored_items.sort(key=lambda x: x[1])

        samples = []

        # Minimal complexity
        samples.append(scored_items[0][2])

        # Median complexity
        mid_idx = len(scored_items) // 2
        samples.append(scored_items[mid_idx][2])

        # Maximum complexity (but not extreme outliers)
        max_idx = min(len(scored_items) - 1, int(len(scored_items) * 0.9))
        if scored_items[max_idx][2] not in samples:
            samples.append(scored_items[max_idx][2])
        elif len(scored_items) > 2:
            # Pick another different one
            for i in range(len(scored_items) - 1, -1, -1):
                if scored_items[i][2] not in samples:
                    samples.append(scored_items[i][2])
                    break

        return samples[:cls.MAX_SAMPLE_ITEMS]

    @classmethod
    def _calculate_complexity(cls, item: Dict) -> int:
        """Calculate a complexity score for an item."""
        if not isinstance(item, dict):
            return 0

        score = len(item)  # Number of fields

        for value in item.values():
            if isinstance(value, str):
                score += len(value) // 100  # Add 1 per 100 chars
            elif isinstance(value, list):
                score += len(value) * 2  # Arrays add complexity
                for elem in value[:5]:
                    if isinstance(elem, dict):
                        score += len(elem)
            elif isinstance(value, dict):
                score += len(value) * 2

        return score

    @classmethod
    def truncate_item(cls, item: Dict, schema: Dict) -> Dict:
        """
        Intelligently truncate an item while preserving structure.

        - Truncates long strings with [...] marker
        - Limits array items but shows structure
        - Preserves all fields
        """
        return cls._truncate_value(item, schema, depth=0)

    @classmethod
    def _truncate_value(cls, value: Any, schema: Optional[Dict], depth: int = 0) -> Any:
        """Recursively truncate a value."""
        if depth > 5:  # Prevent infinite recursion
            return "..."

        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif isinstance(value, (int, float)):
            return value
        elif isinstance(value, str):
            if len(value) > cls.MAX_CONTENT_LENGTH:
                return value[:cls.MAX_CONTENT_LENGTH] + f" [...{len(value) - cls.MAX_CONTENT_LENGTH} mehr Zeichen]"
            return value
        elif isinstance(value, list):
            if not value:
                return []
            # Show first 2-3 items, indicate if more
            truncated = [cls._truncate_value(v, None, depth + 1) for v in value[:3]]
            if len(value) > 3:
                truncated.append(f"... (+{len(value) - 3} weitere)")
            return truncated
        elif isinstance(value, dict):
            return {
                k: cls._truncate_value(v, schema.get(k) if schema else None, depth + 1)
                for k, v in value.items()
            }
        else:
            return str(value)[:100]

    @classmethod
    def compute_statistics(cls, items: List[Dict], schema: Dict) -> Dict[str, Any]:
        """Compute useful statistics about the data."""
        if not items:
            return {}

        stats = {
            "total_items": len(items),
            "fields_always_present": [],
            "fields_sometimes_present": [],
            "fields_rarely_present": [],
        }

        # Categorize fields by completeness
        for field, info in schema.items():
            completeness = info.get("completeness", 0)
            if completeness >= 0.95:
                stats["fields_always_present"].append(field)
            elif completeness >= 0.5:
                stats["fields_sometimes_present"].append(field)
            else:
                stats["fields_rarely_present"].append(field)

        # Find content fields (long text fields)
        content_fields = []
        for field, info in schema.items():
            if info.get("type") == "string":
                avg_len = info.get("avg_length", 0)
                if avg_len > 100:
                    content_fields.append({"field": field, "avg_length": avg_len})
        if content_fields:
            stats["content_fields"] = sorted(content_fields, key=lambda x: -x["avg_length"])

        return stats

    @classmethod
    def format_for_prompt(cls, preprocessed: Dict) -> str:
        """
        Format preprocessed data as a string for the LLM prompt.

        Returns a structured, readable representation.
        """
        lines = []

        # Header
        lines.append(f"## DATENANALYSE")
        lines.append(f"")
        lines.append(f"**Datensätze:** {preprocessed['item_count']}")
        lines.append(f"**Datei:** {preprocessed.get('filename', 'unbekannt')}")
        lines.append(f"")

        # Detected patterns
        if preprocessed.get("detected_patterns"):
            lines.append(f"### Erkannte Muster")
            for pattern in preprocessed["detected_patterns"]:
                lines.append(f"- {pattern}")
            lines.append(f"")

        # Schema
        lines.append(f"### Datenstruktur (Schema)")
        lines.append("```json")
        lines.append(json.dumps(preprocessed["schema"], indent=2, ensure_ascii=False))
        lines.append("```")
        lines.append(f"")

        # Statistics
        stats = preprocessed.get("statistics", {})
        if stats:
            lines.append(f"### Statistiken")
            if stats.get("fields_always_present"):
                lines.append(f"- **Immer vorhanden:** {', '.join(stats['fields_always_present'])}")
            if stats.get("fields_sometimes_present"):
                lines.append(f"- **Teilweise vorhanden:** {', '.join(stats['fields_sometimes_present'])}")
            if stats.get("content_fields"):
                cf = stats["content_fields"][:3]
                content_field_strs = [f"{field['field']} (~{field['avg_length']} Zeichen)" for field in cf]
                lines.append(f"- **Haupt-Textfelder:** {', '.join(content_field_strs)}")
            lines.append(f"")

        # Sample data
        lines.append(f"### Beispieldaten ({len(preprocessed['samples'])} von {preprocessed['item_count']})")
        lines.append("```json")
        lines.append(json.dumps(preprocessed["samples"], indent=2, ensure_ascii=False))
        lines.append("```")

        return "\n".join(lines)
