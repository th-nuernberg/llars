"""
AI-powered scenario data analysis routes.

Provides intelligent analysis of uploaded data to suggest
evaluation type, scenario name, description, and configuration.
"""

import json
import logging
from flask import jsonify, request, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError
from routes.auth import data_bp
from services.ai_assist import FieldPromptService

logger = logging.getLogger(__name__)

# Field key for scenario analysis prompt (configurable via Admin Panel)
SCENARIO_ANALYSIS_FIELD_KEY = "scenario.analysis"


def detect_field_types(items):
    """
    Detect field types from a list of data items.

    Args:
        items: List of dictionaries

    Returns:
        Dictionary with field names as keys and type info as values
    """
    if not items or not isinstance(items, list):
        return {}

    fields = {}
    sample_item = items[0] if items else {}

    for key in sample_item.keys():
        values = [item.get(key) for item in items[:100] if key in item]
        non_null_values = [v for v in values if v is not None]

        # Determine type
        field_type = "string"
        if non_null_values:
            sample = non_null_values[0]
            if isinstance(sample, bool):
                field_type = "boolean"
            elif isinstance(sample, (int, float)):
                field_type = "number"
            elif isinstance(sample, list):
                field_type = "array"
            elif isinstance(sample, dict):
                field_type = "object"

        # Calculate completeness
        completeness = len(non_null_values) / len(items) if items else 0

        # Get sample values (first 3 unique)
        sample_values = []
        seen = set()
        for v in non_null_values[:20]:
            str_v = str(v)[:100]  # Truncate long values
            if str_v not in seen:
                seen.add(str_v)
                sample_values.append(str_v)
                if len(sample_values) >= 3:
                    break

        fields[key] = {
            "type": field_type,
            "completeness": round(completeness, 2),
            "sample_values": sample_values
        }

    return fields


@data_bp.post("/ai-assist/analyze-scenario-data")
@authentik_required
@handle_api_errors(logger_name='ai_assist')
def analyze_scenario_data():
    """
    Analyze uploaded data and suggest scenario configuration using AI.

    Body:
        data: List of data items (required)
        filename: Original filename for context (optional)
        file_count: Number of files uploaded (optional)
        user_hint: User's description of what they want (optional)

    Returns:
        Analysis results with AI suggestions for eval type, name,
        description, and configuration.
    """
    from services.llm.llm_client_factory import LLMClientFactory

    data = request.get_json(silent=True) or {}

    # Validate input
    items = data.get('data', [])
    if not items:
        raise ValidationError("Missing required field: data")
    if not isinstance(items, list):
        raise ValidationError("Field 'data' must be an array")
    if len(items) == 0:
        raise ValidationError("Data array is empty")

    filename = data.get('filename', 'unknown')
    file_count = data.get('file_count', 1)
    user_hint = data.get('user_hint', '')

    # Extract sample items (max 5 for token efficiency)
    sample_items = items[:5]

    # Detect field types and info
    fields = detect_field_types(items)

    # Load prompt template from database (configurable via Admin Panel)
    template = FieldPromptService.get_by_field_key(SCENARIO_ANALYSIS_FIELD_KEY)
    if not template:
        raise NotFoundError(
            f"Prompt template '{SCENARIO_ANALYSIS_FIELD_KEY}' not found. "
            "Please seed defaults via Admin Panel or API."
        )

    # Build context for prompt rendering
    context = {
        "filename": filename,
        "file_count": file_count,
        "item_count": len(items),
        "fields_json": json.dumps(fields, ensure_ascii=False, indent=2),
        "sample_count": len(sample_items),
        "sample_data": json.dumps(sample_items, ensure_ascii=False, indent=2)[:3000],
        "user_hint_text": f'Benutzerhinweis: {user_hint}' if user_hint else ''
    }

    # Render user prompt from template
    user_prompt = FieldPromptService.render_prompt(template, context)

    try:
        # Get LLM client and admin-configured default model
        from db.models.llm_model import LLMModel
        client = LLMClientFactory.get_client_for_model(None)
        model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        if not model:
            raise ValidationError("No default LLM model configured")

        # Call LLM with structured output (using template's settings)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": template.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=template.max_tokens,
            temperature=template.temperature,
            extra_body={"response_format": {"type": "json_object"}}
        )

        # Parse response
        response_text = response.choices[0].message.content.strip()
        result = json.loads(response_text)
        tokens_used = response.usage.total_tokens if response.usage else 0

        logger.info(
            f"AI scenario analysis completed for {g.authentik_user.username}: "
            f"{len(items)} items, {tokens_used} tokens"
        )

        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(fields.keys()),
                    'field_types': {k: v['type'] for k, v in fields.items()},
                    'field_completeness': {k: v['completeness'] for k, v in fields.items()},
                    'sample_items': sample_items[:3]
                },
                'suggestions': result.get('suggestions', {}),
                'data_quality': result.get('data_quality', {})
            },
            'tokens_used': tokens_used
        })

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        # Return partial result with local analysis only
        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(fields.keys()),
                    'field_types': {k: v['type'] for k, v in fields.items()},
                    'field_completeness': {k: v['completeness'] for k, v in fields.items()},
                    'sample_items': sample_items[:3]
                },
                'suggestions': None,
                'data_quality': None,
                'ai_error': 'Failed to parse AI response'
            },
            'tokens_used': 0
        })

    except Exception as e:
        logger.error(f"AI scenario analysis failed: {e}")
        # Return local analysis as fallback
        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(fields.keys()),
                    'field_types': {k: v['type'] for k, v in fields.items()},
                    'field_completeness': {k: v['completeness'] for k, v in fields.items()},
                    'sample_items': sample_items[:3]
                },
                'suggestions': None,
                'data_quality': None,
                'ai_error': str(e)
            },
            'tokens_used': 0
        })
