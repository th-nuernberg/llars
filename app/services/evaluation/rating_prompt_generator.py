"""
Rating Prompt Generator Service.

Generates dynamic LLM prompts for multi-dimensional rating evaluation.
Supports variable Likert scales and configurable dimensions.
"""

import logging
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# System Prompt Templates
# =============================================================================

DIMENSIONAL_RATING_SYSTEM_TEMPLATE = """Du bist ein Experte für die mehrdimensionale Bewertung von {content_type}.

Deine Aufgabe ist es, den folgenden Inhalt auf {num_dimensions} Dimension(en) zu bewerten.
{scale_info}

**Bewertungsdimensionen:**
{dimensions_formatted}

**Wichtig:**
- Bewerte jede Dimension unabhängig voneinander
- Gib für jede Bewertung eine kurze Begründung
- Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format
- Sei objektiv und konsistent in deinen Bewertungen
- Achte auf die unterschiedlichen Skalen pro Dimension!
"""

DIMENSIONAL_RATING_SYSTEM_TEMPLATE_EN = """You are an expert in multi-dimensional evaluation of {content_type}.

Your task is to rate the following content on {num_dimensions} dimension(s).
{scale_info}

**Rating Dimensions:**
{dimensions_formatted}

**Important:**
- Rate each dimension independently
- Provide a brief justification for each rating
- Answer ONLY in the specified JSON format
- Be objective and consistent in your evaluations
- Pay attention to the different scales per dimension!
"""

# =============================================================================
# User Prompt Templates
# =============================================================================

DIMENSIONAL_RATING_USER_TEMPLATE = """Bewerte den folgenden Inhalt nach den oben genannten Kriterien.

**Inhalt zur Bewertung:**
{content}

**Antworte im folgenden JSON-Format:**
{{
  "ratings": {{
    {dimension_ratings_schema}
  }},
  "reasoning": {{
    {dimension_reasoning_schema}
  }},
  "overall_score": <gewichteter Durchschnitt, {min}-{max}>,
  "summary": "<Kurze Zusammenfassung der Bewertung>",
  "confidence": <0.0-1.0>
}}
"""

DIMENSIONAL_RATING_USER_TEMPLATE_EN = """Rate the following content according to the criteria above.

**Content to evaluate:**
{content}

**Answer in the following JSON format:**
{{
  "ratings": {{
    {dimension_ratings_schema}
  }},
  "reasoning": {{
    {dimension_reasoning_schema}
  }},
  "overall_score": <weighted average, {min}-{max}>,
  "summary": "<Brief summary of the evaluation>",
  "confidence": <0.0-1.0>
}}
"""


class RatingPromptGenerator:
    """Generates dynamic prompts for LLM-based multi-dimensional rating."""

    @staticmethod
    def generate_system_prompt(
        dimensions: List[Dict],
        scale_config: Dict,
        locale: str = 'de',
        content_type: str = 'Text'
    ) -> str:
        """
        Generate system prompt for dimensional rating.

        Args:
            dimensions: List of dimension configurations
                Each dimension: {id, name: {de, en}, description: {de, en}, weight, prompt_hint?,
                               scale?: {min, max, step?, labels?}}
            scale_config: Default scale configuration {min, max, step, labels: {value: {de, en}}}
            locale: Language locale ('de' or 'en')
            content_type: Type of content being evaluated (for prompt context)

        Returns:
            Formatted system prompt string
        """
        template = (DIMENSIONAL_RATING_SYSTEM_TEMPLATE if locale == 'de'
                    else DIMENSIONAL_RATING_SYSTEM_TEMPLATE_EN)

        # Check if we have per-dimension scales
        has_per_dimension_scales = any(dim.get('scale') for dim in dimensions)

        # Format scale info (global or per-dimension)
        if has_per_dimension_scales:
            scale_info = RatingPromptGenerator._format_per_dimension_scale_info(
                dimensions, scale_config, locale
            )
        else:
            # Single global scale
            min_val = scale_config.get('min', 1)
            max_val = scale_config.get('max', 5)
            scale_labels = RatingPromptGenerator._format_scale_labels(scale_config, locale)
            if locale == 'de':
                scale_info = f"Verwende für alle Dimensionen eine Skala von {min_val} bis {max_val}.\n\n**Bewertungsskala:**\n{scale_labels}"
            else:
                scale_info = f"Use a scale from {min_val} to {max_val} for all dimensions.\n\n**Rating Scale:**\n{scale_labels}"

        # Format dimensions (with individual scales if present)
        dimensions_formatted = RatingPromptGenerator._format_dimensions_with_scales(
            dimensions, scale_config, locale
        )

        return template.format(
            content_type=content_type,
            num_dimensions=len(dimensions),
            scale_info=scale_info,
            dimensions_formatted=dimensions_formatted
        )

    @staticmethod
    def generate_user_prompt(
        dimensions: List[Dict],
        content: str,
        scale_config: Dict,
        locale: str = 'de'
    ) -> str:
        """
        Generate user prompt with content for dimensional rating.

        Args:
            dimensions: List of dimension configurations (may have per-dimension scales)
            content: The content to be evaluated
            scale_config: Default scale configuration
            locale: Language locale

        Returns:
            Formatted user prompt string
        """
        template = (DIMENSIONAL_RATING_USER_TEMPLATE if locale == 'de'
                    else DIMENSIONAL_RATING_USER_TEMPLATE_EN)

        # Generate dimension schemas (with per-dimension scales if present)
        schema = RatingPromptGenerator._generate_dimension_schema_with_scales(
            dimensions, scale_config, locale
        )

        # For overall score, use the average of all scales or global scale
        overall_min, overall_max = RatingPromptGenerator._get_overall_scale_range(
            dimensions, scale_config
        )

        return template.format(
            content=content,
            dimension_ratings_schema=schema['ratings'],
            dimension_reasoning_schema=schema['reasoning'],
            min=overall_min,
            max=overall_max
        )

    @staticmethod
    def generate_output_schema(dimensions: List[Dict], scale_config: Dict) -> Dict:
        """
        Generate JSON schema for structured LLM output.

        Args:
            dimensions: List of dimension configurations (may have per-dimension scales)
            scale_config: Default scale configuration

        Returns:
            JSON schema dict for validating LLM output
        """
        # Get overall scale range for overall_score
        overall_min, overall_max = RatingPromptGenerator._get_overall_scale_range(
            dimensions, scale_config
        )

        properties = {
            "ratings": {
                "type": "object",
                "properties": {},
                "required": [dim['id'] for dim in dimensions]
            },
            "reasoning": {
                "type": "object",
                "properties": {},
                "required": [dim['id'] for dim in dimensions]
            },
            "overall_score": {
                "type": "number",
                "minimum": overall_min,
                "maximum": overall_max
            },
            "summary": {
                "type": "string"
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0
            }
        }

        for dim in dimensions:
            # Get scale for this dimension (per-dimension or global)
            dim_scale = dim.get('scale', {})
            dim_min = dim_scale.get('min', scale_config.get('min', 1))
            dim_max = dim_scale.get('max', scale_config.get('max', 5))

            properties["ratings"]["properties"][dim['id']] = {
                "type": "number",
                "minimum": dim_min,
                "maximum": dim_max
            }
            properties["reasoning"]["properties"][dim['id']] = {
                "type": "string"
            }

        return {
            "type": "object",
            "properties": properties,
            "required": ["ratings", "reasoning", "overall_score", "confidence"]
        }

    @staticmethod
    def parse_llm_rating_response(
        response: str,
        dimensions: List[Dict],
        scale_config: Dict
    ) -> Dict:
        """
        Parse and validate LLM rating response.

        Args:
            response: Raw LLM response string
            dimensions: Expected dimensions (may have per-dimension scales)
            scale_config: Default scale configuration

        Returns:
            Parsed response dict with validation status
        """
        result = {
            'success': False,
            'ratings': {},
            'reasoning': {},
            'overall_score': None,
            'summary': None,
            'confidence': None,
            'errors': []
        }

        try:
            # Try to extract JSON from response
            json_str = RatingPromptGenerator._extract_json(response)
            if not json_str:
                result['errors'].append('No valid JSON found in response')
                return result

            data = json.loads(json_str)

            if 'ratings' in data:
                for dim in dimensions:
                    dim_id = dim['id']
                    # Get scale for this dimension (per-dimension or global)
                    dim_scale = dim.get('scale', {})
                    min_val = dim_scale.get('min', scale_config.get('min', 1))
                    max_val = dim_scale.get('max', scale_config.get('max', 5))

                    if dim_id in data['ratings']:
                        value = data['ratings'][dim_id]
                        if isinstance(value, (int, float)) and min_val <= value <= max_val:
                            result['ratings'][dim_id] = value
                        else:
                            result['errors'].append(
                                f"Invalid rating for {dim_id}: {value} "
                                f"(expected {min_val}-{max_val})"
                            )
                    else:
                        result['errors'].append(f"Missing rating for dimension: {dim_id}")

            # Extract reasoning
            if 'reasoning' in data:
                result['reasoning'] = data['reasoning']

            # Extract overall score (use overall scale range)
            if 'overall_score' in data:
                overall_min, overall_max = RatingPromptGenerator._get_overall_scale_range(
                    dimensions, scale_config
                )
                score = data['overall_score']
                if isinstance(score, (int, float)) and overall_min <= score <= overall_max:
                    result['overall_score'] = score

            # Extract summary and confidence
            result['summary'] = data.get('summary')
            result['confidence'] = data.get('confidence')

            # Mark as success if we have all ratings
            if len(result['ratings']) == len(dimensions):
                result['success'] = True

        except json.JSONDecodeError as e:
            result['errors'].append(f'JSON parsing error: {str(e)}')
        except Exception as e:
            logger.exception('Error parsing LLM rating response')
            result['errors'].append(f'Parsing error: {str(e)}')

        return result

    @staticmethod
    def generate_rating_prompt(
        dimensions: List[Dict],
        scale_config: Dict,
        content: str,
        locale: str = 'de',
        content_type: str = 'Text'
    ) -> Dict[str, str]:
        """
        Generate complete rating prompt (system + user).

        Convenience method that generates both prompts at once.

        Args:
            dimensions: List of dimension configurations
            scale_config: Scale configuration
            content: Content to evaluate
            locale: Language locale
            content_type: Type of content

        Returns:
            Dict with 'system_prompt' and 'user_prompt' keys
        """
        return {
            'system_prompt': RatingPromptGenerator.generate_system_prompt(
                dimensions, scale_config, locale, content_type
            ),
            'user_prompt': RatingPromptGenerator.generate_user_prompt(
                dimensions, content, scale_config, locale
            )
        }

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    @staticmethod
    def _format_scale_labels(scale_config: Dict, locale: str) -> str:
        """Format scale labels for prompt."""
        labels = scale_config.get('labels', {})
        min_val = scale_config.get('min', 1)
        max_val = scale_config.get('max', 5)
        step = scale_config.get('step', 1)

        lines = []
        value = min_val
        while value <= max_val:
            str_val = str(value)
            if str_val in labels:
                label_obj = labels[str_val]
                if isinstance(label_obj, dict):
                    label = label_obj.get(locale) or label_obj.get('de', str_val)
                else:
                    label = label_obj
                lines.append(f"- {value}: {label}")
            elif value in labels:
                label_obj = labels[value]
                if isinstance(label_obj, dict):
                    label = label_obj.get(locale) or label_obj.get('de', str(value))
                else:
                    label = label_obj
                lines.append(f"- {value}: {label}")
            else:
                # Generate default label based on position
                label = RatingPromptGenerator._generate_default_label(
                    value, min_val, max_val, locale
                )
                lines.append(f"- {value}: {label}")
            value += step

        return '\n'.join(lines)

    @staticmethod
    def _format_dimensions(dimensions: List[Dict], locale: str) -> str:
        """Format dimension descriptions for prompt."""
        lines = []
        for i, dim in enumerate(dimensions, 1):
            name = RatingPromptGenerator._get_localized(dim.get('name', ''), locale)
            description = RatingPromptGenerator._get_localized(
                dim.get('description', ''), locale
            )
            weight = dim.get('weight', 1.0)
            prompt_hint = dim.get('prompt_hint', '')

            line = f"{i}. **{name}** (Gewichtung: {weight * 100:.0f}%)"
            if description:
                line += f"\n   {description}"
            if prompt_hint:
                line += f"\n   *Hinweis: {prompt_hint}*"

            lines.append(line)

        return '\n'.join(lines)

    @staticmethod
    def _generate_dimension_schema(
        dimensions: List[Dict],
        scale_config: Dict,
        locale: str
    ) -> Dict[str, str]:
        """Generate JSON schema strings for dimensions."""
        min_val = scale_config.get('min', 1)
        max_val = scale_config.get('max', 5)

        ratings = []
        reasoning = []

        for dim in dimensions:
            dim_id = dim['id']
            dim_name = RatingPromptGenerator._get_localized(
                dim.get('name', dim_id), locale
            )

            ratings.append(f'"{dim_id}": <{min_val}-{max_val}>')

            if locale == 'de':
                reasoning.append(f'"{dim_id}": "<Begründung für {dim_name}>"')
            else:
                reasoning.append(f'"{dim_id}": "<Reasoning for {dim_name}>"')

        return {
            'ratings': ',\n    '.join(ratings),
            'reasoning': ',\n    '.join(reasoning)
        }

    @staticmethod
    def _format_per_dimension_scale_info(
        dimensions: List[Dict],
        default_scale: Dict,
        locale: str
    ) -> str:
        """Format scale information when dimensions have different scales."""
        if locale == 'de':
            intro = "Jede Dimension hat ihre eigene Bewertungsskala. Achte auf die unterschiedlichen Skalen!"
        else:
            intro = "Each dimension has its own rating scale. Pay attention to the different scales!"

        return intro

    @staticmethod
    def _format_dimensions_with_scales(
        dimensions: List[Dict],
        default_scale: Dict,
        locale: str
    ) -> str:
        """Format dimension descriptions with per-dimension scale information."""
        lines = []
        for i, dim in enumerate(dimensions, 1):
            name = RatingPromptGenerator._get_localized(dim.get('name', ''), locale)
            description = RatingPromptGenerator._get_localized(
                dim.get('description', ''), locale
            )
            weight = dim.get('weight', 1.0)
            prompt_hint = dim.get('prompt_hint', '')

            # Get scale for this dimension
            dim_scale = dim.get('scale', {})
            min_val = dim_scale.get('min', default_scale.get('min', 1))
            max_val = dim_scale.get('max', default_scale.get('max', 5))

            # Format scale labels for this dimension
            effective_scale = {
                'min': min_val,
                'max': max_val,
                'step': dim_scale.get('step', default_scale.get('step', 1)),
                'labels': dim_scale.get('labels', default_scale.get('labels', {}))
            }
            scale_labels = RatingPromptGenerator._format_scale_labels(effective_scale, locale)

            if locale == 'de':
                line = f"{i}. **{name}** (Gewichtung: {weight * 100:.0f}%, Skala: {min_val}-{max_val})"
            else:
                line = f"{i}. **{name}** (Weight: {weight * 100:.0f}%, Scale: {min_val}-{max_val})"

            if description:
                line += f"\n   {description}"
            if prompt_hint:
                if locale == 'de':
                    line += f"\n   *Hinweis: {prompt_hint}*"
                else:
                    line += f"\n   *Hint: {prompt_hint}*"

            # Add scale labels for this dimension
            if locale == 'de':
                line += f"\n   Skala:\n   {scale_labels.replace(chr(10), chr(10) + '   ')}"
            else:
                line += f"\n   Scale:\n   {scale_labels.replace(chr(10), chr(10) + '   ')}"

            lines.append(line)

        return '\n\n'.join(lines)

    @staticmethod
    def _generate_dimension_schema_with_scales(
        dimensions: List[Dict],
        default_scale: Dict,
        locale: str
    ) -> Dict[str, str]:
        """Generate JSON schema strings for dimensions with per-dimension scales."""
        ratings = []
        reasoning = []

        for dim in dimensions:
            dim_id = dim['id']
            dim_name = RatingPromptGenerator._get_localized(
                dim.get('name', dim_id), locale
            )

            # Get scale for this dimension
            dim_scale = dim.get('scale', {})
            min_val = dim_scale.get('min', default_scale.get('min', 1))
            max_val = dim_scale.get('max', default_scale.get('max', 5))

            ratings.append(f'"{dim_id}": <{min_val}-{max_val}>')

            if locale == 'de':
                reasoning.append(f'"{dim_id}": "<Begründung für {dim_name}>"')
            else:
                reasoning.append(f'"{dim_id}": "<Reasoning for {dim_name}>"')

        return {
            'ratings': ',\n    '.join(ratings),
            'reasoning': ',\n    '.join(reasoning)
        }

    @staticmethod
    def _get_overall_scale_range(
        dimensions: List[Dict],
        default_scale: Dict
    ) -> tuple:
        """Get the overall scale range for the overall_score field."""
        # If any dimension has a custom scale, use a normalized range
        # Otherwise use the global scale
        has_custom = any(dim.get('scale') for dim in dimensions)

        if not has_custom:
            return (default_scale.get('min', 1), default_scale.get('max', 5))

        # With mixed scales, we could normalize to 0-1 or use a common range
        # For simplicity, use 1-5 as a normalized overall score
        # The actual calculation should normalize each dimension's score
        return (1, 5)

    @staticmethod
    def _get_localized(value: Any, locale: str) -> str:
        """Get localized string value."""
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return value.get(locale) or value.get('de') or value.get('en', '')
        return str(value) if value else ''

    @staticmethod
    def _generate_default_label(
        value: int,
        min_val: int,
        max_val: int,
        locale: str
    ) -> str:
        """Generate default label based on position in scale."""
        if max_val == min_val:
            return str(value)

        position = (value - min_val) / (max_val - min_val)

        if locale == 'de':
            if position <= 0.2:
                return 'Sehr schlecht'
            elif position <= 0.4:
                return 'Schlecht'
            elif position <= 0.6:
                return 'Akzeptabel'
            elif position <= 0.8:
                return 'Gut'
            else:
                return 'Sehr gut'
        else:
            if position <= 0.2:
                return 'Very poor'
            elif position <= 0.4:
                return 'Poor'
            elif position <= 0.6:
                return 'Acceptable'
            elif position <= 0.8:
                return 'Good'
            else:
                return 'Very good'

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract JSON from text, handling common formats."""
        text = text.strip()

        # Try to find JSON in markdown code blocks
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            if end > start:
                return text[start:end].strip()

        if '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            if end > start:
                candidate = text[start:end].strip()
                if candidate.startswith('{'):
                    return candidate

        # Try to find JSON object directly
        if '{' in text:
            start = text.find('{')
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return text[start:i + 1]

        return None


# =============================================================================
# Scale Label Presets
# =============================================================================

SCALE_LABEL_PRESETS = {
    # 0-1 Binary scale
    '0-1': {
        'de': {0: 'Nein', 1: 'Ja'},
        'en': {0: 'No', 1: 'Yes'}
    },
    # 1-5 Standard Likert
    '1-5': {
        'de': {
            1: 'Sehr schlecht',
            2: 'Schlecht',
            3: 'Akzeptabel',
            4: 'Gut',
            5: 'Sehr gut'
        },
        'en': {
            1: 'Very poor',
            2: 'Poor',
            3: 'Acceptable',
            4: 'Good',
            5: 'Very good'
        }
    },
    # 0-4 Four-point scale
    '0-4': {
        'de': {
            0: 'Nicht vorhanden',
            1: 'Unzureichend',
            2: 'Befriedigend',
            3: 'Gut',
            4: 'Ausgezeichnet'
        },
        'en': {
            0: 'Not present',
            1: 'Insufficient',
            2: 'Satisfactory',
            3: 'Good',
            4: 'Excellent'
        }
    },
    # 1-7 Extended Likert
    '1-7': {
        'de': {
            1: 'Stimme gar nicht zu',
            2: 'Stimme nicht zu',
            3: 'Stimme eher nicht zu',
            4: 'Neutral',
            5: 'Stimme eher zu',
            6: 'Stimme zu',
            7: 'Stimme voll zu'
        },
        'en': {
            1: 'Strongly disagree',
            2: 'Disagree',
            3: 'Somewhat disagree',
            4: 'Neutral',
            5: 'Somewhat agree',
            6: 'Agree',
            7: 'Strongly agree'
        }
    },
    # 0-9 Ten-point scale (0-indexed)
    '0-9': {
        'de': {
            0: 'Völlig inakzeptabel',
            3: 'Unzureichend',
            5: 'Akzeptabel',
            7: 'Gut',
            9: 'Herausragend'
        },
        'en': {
            0: 'Completely unacceptable',
            3: 'Insufficient',
            5: 'Acceptable',
            7: 'Good',
            9: 'Outstanding'
        }
    },
    # 1-10 Ten-point scale (1-indexed)
    '1-10': {
        'de': {
            1: 'Völlig unzureichend',
            4: 'Unzureichend',
            5: 'Befriedigend',
            7: 'Gut',
            10: 'Ausgezeichnet'
        },
        'en': {
            1: 'Completely insufficient',
            4: 'Insufficient',
            5: 'Satisfactory',
            7: 'Good',
            10: 'Excellent'
        }
    }
}


def get_scale_labels_for_range(min_val: int, max_val: int, locale: str = 'de') -> Dict:
    """
    Get appropriate scale labels for a given range.

    Args:
        min_val: Minimum scale value
        max_val: Maximum scale value
        locale: Language locale

    Returns:
        Dictionary of labels for the scale
    """
    key = f'{min_val}-{max_val}'

    if key in SCALE_LABEL_PRESETS:
        return SCALE_LABEL_PRESETS[key].get(locale, SCALE_LABEL_PRESETS[key]['de'])

    # Generate default labels for unknown scales
    labels = {}
    range_size = max_val - min_val

    if range_size > 0:
        labels[min_val] = 'Sehr schlecht' if locale == 'de' else 'Very poor'
        labels[max_val] = 'Sehr gut' if locale == 'de' else 'Very good'

        # Add middle point if scale is large enough
        if range_size >= 2:
            mid = min_val + range_size // 2
            labels[mid] = 'Akzeptabel' if locale == 'de' else 'Acceptable'

    return labels
