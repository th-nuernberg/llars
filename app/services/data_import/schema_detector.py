"""
Deterministic schema detection for evaluation data.

Determines evaluation type based on field names/structure, NOT AI.
This ensures consistent, predictable type detection based on LLARS conventions.

Priority Order:
1. authenticity - is_human, is_fake, synthetic fields
2. comparison - response_a/response_b pairs, winner field
3. ranking - summary_a/b/c or 3+ variant columns
4. labeling - category/label/sentiment + text content
5. mail_rating - messages[] array (conversation)
6. rating - question/response pairs (fallback)
"""

from typing import Optional, Dict, Any, Set, List, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EvaluationType(Enum):
    """Supported evaluation types in LLARS."""
    AUTHENTICITY = 'authenticity'
    COMPARISON = 'comparison'
    RANKING = 'ranking'
    LABELING = 'labeling'
    MAIL_RATING = 'mail_rating'
    RATING = 'rating'


@dataclass
class DetectionResult:
    """Result of schema detection."""
    eval_type: Optional[EvaluationType]
    confidence: str  # 'definite', 'likely', 'uncertain'
    matched_fields: List[str]
    reason: str
    all_fields: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'eval_type': self.eval_type.value if self.eval_type else None,
            'confidence': self.confidence,
            'matched_fields': self.matched_fields,
            'reason': self.reason,
            'all_fields': self.all_fields or []
        }


class SchemaDetector:
    """
    Detects evaluation type from data structure.

    Uses deterministic field matching to identify the evaluation type.
    Only falls back to AI when structure is ambiguous.
    """

    # Priority 1: Authenticity - Binary human/AI classification
    AUTHENTICITY_FIELDS = {
        'is_human', 'is_fake', 'synthetic', 'is_ai',
        'is_generated', 'human_written', 'ai_generated',
        'is_authentic', 'is_real', 'is_machine_generated'
    }

    # Priority 2: Comparison - A/B comparison pairs
    COMPARISON_PAIRS = [
        ('response_a', 'response_b'),
        ('conversation_a', 'conversation_b'),
        ('answer_a', 'answer_b'),
        ('output_a', 'output_b'),
        ('text_a', 'text_b'),
        ('model_a_response', 'model_b_response'),
    ]
    COMPARISON_INDICATORS = {'winner', 'preferred', 'chosen', 'better', 'preference'}

    # Priority 4: Labeling - Category/classification fields
    LABELING_FIELDS = {
        'category', 'label', 'sentiment', 'topic',
        'class', 'tag', 'classification', 'category_id',
        'intent', 'emotion', 'type'
    }
    LABELING_CONTENT_FIELDS = {
        'text', 'content', 'message', 'document',
        'input', 'sentence', 'paragraph', 'review'
    }

    # Priority 6: Rating - Question/response pairs
    RATING_PAIRS = [
        ('question', 'response'),
        ('question', 'answer'),
        ('prompt', 'completion'),
        ('prompt', 'response'),
        ('input', 'output'),
        ('query', 'response'),
        ('instruction', 'response'),
    ]
    RATING_CONTENT_FIELDS = {
        'text', 'content', 'response', 'answer',
        'output', 'completion', 'generated_text'
    }

    def detect(self, data: Any, filename: str = None) -> DetectionResult:
        """
        Main detection entry point.

        Args:
            data: Parsed data (dict, list of dicts, or list of lists for CSV)
            filename: Original filename (used as hint)

        Returns:
            DetectionResult with eval_type, confidence, and matched fields
        """
        # Normalize data to get a sample item
        sample, all_fields = self._normalize_data(data)

        if sample is None:
            return DetectionResult(
                eval_type=None,
                confidence='uncertain',
                matched_fields=[],
                reason='Could not parse data structure',
                all_fields=[]
            )

        fields = set(str(k).lower() for k in sample.keys())
        all_fields_list = list(fields)

        logger.info(f"SchemaDetector analyzing fields: {fields}")
        if filename:
            logger.info(f"Filename hint: {filename}")

        # Priority-ordered checks
        # NOTE: Rating comes BEFORE Labeling because Q&A structure (question+response)
        # is more specific than category/label fields (which could be metadata)
        checks = [
            (self._check_authenticity, EvaluationType.AUTHENTICITY, "authenticity fields (is_human, is_fake, etc.)"),
            (self._check_comparison, EvaluationType.COMPARISON, "comparison pairs (response_a/b, winner)"),
            (self._check_ranking, EvaluationType.RANKING, "ranking variants (summary_a/b/c)"),
            (self._check_mail_rating, EvaluationType.MAIL_RATING, "conversation structure (messages array)"),
            (self._check_rating, EvaluationType.RATING, "rating pairs (question/response)"),
            (self._check_labeling, EvaluationType.LABELING, "labeling fields (category, sentiment, label)"),
        ]

        for check_fn, eval_type, description in checks:
            matched = check_fn(fields, sample)
            if matched:
                reason = f"Detected {eval_type.value} based on {description}: {matched}"
                logger.info(f"SchemaDetector: {reason}")
                return DetectionResult(
                    eval_type=eval_type,
                    confidence='definite',
                    matched_fields=matched,
                    reason=reason,
                    all_fields=all_fields_list
                )

        # No clear pattern matched
        logger.info(f"SchemaDetector: No definite pattern matched for fields: {fields}")
        return DetectionResult(
            eval_type=None,
            confidence='uncertain',
            matched_fields=[],
            reason=f'No clear pattern matched. Available fields: {list(fields)[:10]}',
            all_fields=all_fields_list
        )

    def _normalize_data(self, data: Any) -> tuple[Optional[Dict], List[str]]:
        """
        Normalize various data formats to extract a sample item.

        Supports:
        - Single dict
        - List of dicts
        - List of lists (CSV with headers)
        """
        if isinstance(data, dict):
            # Single object or nested structure
            if 'items' in data and isinstance(data['items'], list) and data['items']:
                # Nested items array
                return data['items'][0], list(data['items'][0].keys()) if isinstance(data['items'][0], dict) else []
            return data, list(data.keys())

        elif isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first, list(first.keys())
            elif isinstance(first, list):
                # CSV format: first row is headers
                headers = [str(h).lower().strip() for h in first]
                # Create dict from headers for analysis
                return {h: None for h in headers}, headers

        return None, []

    def _check_authenticity(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for authenticity pattern (Priority 1).

        Authenticity is identified by presence of is_human, is_fake, etc.
        This has HIGHEST priority - even if messages[] exists.
        """
        matched = fields & self.AUTHENTICITY_FIELDS
        return list(matched) if matched else None

    def _check_comparison(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for comparison pattern (Priority 2).

        Comparison requires paired responses (a/b) or winner field.
        """
        # Check for paired fields
        for a, b in self.COMPARISON_PAIRS:
            if a in fields and b in fields:
                result = [a, b]
                # Also include winner if present
                indicators = fields & self.COMPARISON_INDICATORS
                if indicators:
                    result.extend(list(indicators))
                return result

        # Check for winner/preference indicators with multiple responses
        indicators = fields & self.COMPARISON_INDICATORS
        if indicators:
            # Must have some response fields too
            response_fields = [f for f in fields if 'response' in f or 'answer' in f or 'output' in f]
            if response_fields:
                return list(indicators) + response_fields[:2]

        return None

    def _check_ranking(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for ranking pattern (Priority 3).

        Ranking requires 3+ variants of the same field (summary_a, summary_b, summary_c).
        """
        # Check for explicit summary_* pattern
        summary_fields = sorted([f for f in fields if f.startswith('summary_')])
        if len(summary_fields) >= 2:
            return summary_fields

        # Check for generic _a, _b, _c or _1, _2, _3 pattern
        suffixes = ['_a', '_b', '_c', '_d', '_1', '_2', '_3', '_4']
        prefixes: Dict[str, List[str]] = {}

        for field in fields:
            for suffix in suffixes:
                if field.endswith(suffix):
                    prefix = field[:-len(suffix)]
                    if prefix and len(prefix) > 0:  # Avoid empty prefix
                        if prefix not in prefixes:
                            prefixes[prefix] = []
                        prefixes[prefix].append(field)
                    break

        # Need at least 3 variants of the same field for ranking
        for prefix, matched in prefixes.items():
            if len(matched) >= 3:
                return sorted(matched)

        # Also check for 2 variants (still valid ranking)
        for prefix, matched in prefixes.items():
            if len(matched) >= 2:
                return sorted(matched)

        return None

    def _check_labeling(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for labeling pattern (Priority 4).

        Labeling requires a label/category field AND content to classify.
        """
        label_fields = fields & self.LABELING_FIELDS
        content_fields = fields & self.LABELING_CONTENT_FIELDS

        if label_fields and content_fields:
            return sorted(list(label_fields) + list(content_fields))

        # Also check if there's a label field with any text-like content
        if label_fields:
            # Check if sample has substantial text content in any field
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 50:
                    return sorted(list(label_fields) + [key.lower()])

        return None

    def _check_mail_rating(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for mail_rating pattern (Priority 5).

        Mail rating requires a messages array with conversation structure.
        NOTE: If authenticity fields exist, this returns None (authenticity wins).
        """
        # Already checked authenticity first, but double-check
        if fields & self.AUTHENTICITY_FIELDS:
            return None

        if 'messages' not in sample:
            return None

        messages = sample.get('messages', [])
        if not isinstance(messages, list) or len(messages) < 2:
            return None

        # Check first message for conversation structure
        first_msg = messages[0] if messages else {}
        if isinstance(first_msg, dict):
            conversation_fields = {'role', 'sender', 'from', 'author', 'speaker'}
            if any(k.lower() in conversation_fields for k in first_msg.keys()):
                result = ['messages']
                # Include subject if present
                if 'subject' in fields:
                    result.append('subject')
                return result

        return None

    def _check_rating(self, fields: Set[str], sample: dict) -> Optional[List[str]]:
        """
        Check for rating pattern (Priority 6 - Fallback).

        Rating is the default for question/response pairs or single text items.
        """
        # Check for question/response pairs
        for q, a in self.RATING_PAIRS:
            if q in fields and a in fields:
                return [q, a]

        # Fallback: any substantial content field
        content = fields & self.RATING_CONTENT_FIELDS
        if content:
            return sorted(list(content))

        return None

    def detect_from_csv_headers(self, headers: List[str]) -> DetectionResult:
        """
        Convenience method for CSV files.

        Args:
            headers: List of column headers from CSV

        Returns:
            DetectionResult
        """
        # Convert headers to dict format
        sample = {h.lower().strip(): None for h in headers}
        return self.detect(sample)

    def get_field_documentation(self) -> Dict[str, Dict[str, Any]]:
        """
        Return documentation of which fields trigger which evaluation type.

        Useful for UI to show users the "magic fields".
        """
        return {
            'authenticity': {
                'priority': 1,
                'fields': sorted(list(self.AUTHENTICITY_FIELDS)),
                'description': 'Binary classification: human vs. AI-generated content',
                'example': {'text': '...', 'is_human': True}
            },
            'comparison': {
                'priority': 2,
                'fields': [f"{a}/{b}" for a, b in self.COMPARISON_PAIRS] + sorted(list(self.COMPARISON_INDICATORS)),
                'description': 'A/B comparison of two responses',
                'example': {'prompt': '...', 'response_a': '...', 'response_b': '...', 'winner': 'a'}
            },
            'ranking': {
                'priority': 3,
                'fields': ['*_a, *_b, *_c', 'summary_a, summary_b, summary_c'],
                'description': 'Rank/sort multiple variants of the same content',
                'example': {'source': '...', 'summary_a': '...', 'summary_b': '...', 'summary_c': '...'}
            },
            'labeling': {
                'priority': 4,
                'fields': sorted(list(self.LABELING_FIELDS)),
                'description': 'Assign categories/labels to content',
                'example': {'text': '...', 'category': 'positive'}
            },
            'mail_rating': {
                'priority': 5,
                'fields': ['messages[]'],
                'description': 'Rate conversation/email thread quality',
                'example': {'subject': '...', 'messages': [{'role': 'user', 'content': '...'}]}
            },
            'rating': {
                'priority': 6,
                'fields': [f"{q}/{a}" for q, a in self.RATING_PAIRS],
                'description': 'Rate single responses on quality dimensions',
                'example': {'question': '...', 'response': '...'}
            }
        }


# Singleton instance for convenience
_detector_instance = None


def get_schema_detector() -> SchemaDetector:
    """Get or create singleton SchemaDetector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SchemaDetector()
    return _detector_instance


def detect_evaluation_type(data: Any, filename: str = None) -> DetectionResult:
    """
    Convenience function for quick detection.

    Args:
        data: Parsed data
        filename: Optional filename hint

    Returns:
        DetectionResult
    """
    return get_schema_detector().detect(data, filename)
