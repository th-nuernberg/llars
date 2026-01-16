"""
Test routes for AI-Assist features (development only).

Provides unauthenticated endpoints for testing AI-assist functionality.
Only available when FLASK_ENV=development.
"""

import os
import json
import logging
from flask import jsonify, request

from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError
from routes.auth import data_bp
from services.ai_assist import FieldPromptService

logger = logging.getLogger(__name__)


def _check_dev_mode():
    """Ensure we're in development mode."""
    if os.environ.get('FLASK_ENV') != 'development':
        raise ValidationError("Test routes only available in development mode")


@data_bp.get("/ai-assist/test/prompts")
@handle_api_errors(logger_name='ai_assist_test')
def test_list_prompts():
    """List all field prompts (dev only)."""
    _check_dev_mode()

    templates = FieldPromptService.get_all()
    return jsonify({
        'success': True,
        'count': len(templates),
        'prompts': [
            {
                'id': t.id,
                'field_key': t.field_key,
                'display_name': t.display_name,
                'description': t.description,
                'is_active': t.is_active,
                'max_tokens': t.max_tokens,
                'temperature': t.temperature,
                'context_variables': t.context_variables,
            }
            for t in templates
        ]
    })


@data_bp.get("/ai-assist/test/prompt/<field_key>")
@handle_api_errors(logger_name='ai_assist_test')
def test_get_prompt(field_key: str):
    """Get a specific field prompt by key (dev only)."""
    _check_dev_mode()

    # Handle URL-encoded field keys
    field_key = field_key.replace('%2E', '.')

    template = FieldPromptService.get_by_field_key(field_key)
    if not template:
        raise NotFoundError(f"Prompt not found: {field_key}")

    return jsonify({
        'success': True,
        'prompt': template.to_dict()
    })


@data_bp.post("/ai-assist/test/generate")
@handle_api_errors(logger_name='ai_assist_test')
def test_generate():
    """
    Test AI generation without authentication (dev only).

    Body:
        field_key: The field key (e.g., 'scenario.settings.name')
        context: Dictionary of context variables
    """
    _check_dev_mode()

    from services.llm.llm_client_factory import LLMClientFactory
    from db.models.llm_model import LLMModel

    data = request.get_json(silent=True) or {}

    field_key = data.get('field_key')
    if not field_key:
        raise ValidationError("Missing required field: field_key")

    context = data.get('context', {})

    # Get the prompt template
    template = FieldPromptService.get_by_field_key(field_key)
    if not template:
        raise NotFoundError(f"No prompt template found for field: {field_key}")

    # Render the prompt
    rendered_prompt = FieldPromptService.render_prompt(template, context)

    # Get LLM client and admin-configured default model
    client = LLMClientFactory.get_client_for_model(None)
    model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    if not model:
        raise ValidationError("No default LLM model configured")

    # Call LLM
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": rendered_prompt}
        ],
        max_tokens=template.max_tokens,
        temperature=template.temperature,
    )

    generated_value = response.choices[0].message.content.strip()
    tokens_used = response.usage.total_tokens if response.usage else 0

    logger.info(f"Test AI generation: {field_key} - {tokens_used} tokens")

    return jsonify({
        'success': True,
        'value': generated_value,
        'field_key': field_key,
        'model_used': model,
        'tokens_used': tokens_used,
        'rendered_prompt': rendered_prompt,
        'system_prompt_preview': template.system_prompt[:200] + '...'
    })


@data_bp.post("/ai-assist/test/analyze-scenario")
@handle_api_errors(logger_name='ai_assist_test')
def test_analyze_scenario():
    """
    Test scenario data analysis without authentication (dev only).

    Body:
        data: List of data items (required)
        filename: Original filename for context (optional)
    """
    _check_dev_mode()

    from services.llm.llm_client_factory import LLMClientFactory
    from db.models.llm_model import LLMModel

    data = request.get_json(silent=True) or {}

    items = data.get('data', [])
    if not items:
        raise ValidationError("Missing required field: data")

    filename = data.get('filename', 'test.json')
    file_count = data.get('file_count', 1)
    user_hint = data.get('user_hint', '')

    # Load prompt template
    template = FieldPromptService.get_by_field_key('scenario.analysis')
    if not template:
        raise NotFoundError("Prompt template 'scenario.analysis' not found")

    # Detect field types
    from routes.ai_assist.scenario_analysis_routes import detect_field_types
    fields = detect_field_types(items)
    sample_items = items[:5]

    # Build context
    context = {
        "filename": filename,
        "file_count": file_count,
        "item_count": len(items),
        "fields_json": json.dumps(fields, ensure_ascii=False, indent=2),
        "sample_count": len(sample_items),
        "sample_data": json.dumps(sample_items, ensure_ascii=False, indent=2)[:3000],
        "user_hint_text": f'Benutzerhinweis: {user_hint}' if user_hint else ''
    }

    # Render prompt
    rendered_prompt = FieldPromptService.render_prompt(template, context)

    # Get LLM
    client = LLMClientFactory.get_client_for_model(None)
    model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    if not model:
        raise ValidationError("No default LLM model configured")

    # Call LLM
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": template.system_prompt},
            {"role": "user", "content": rendered_prompt}
        ],
        max_tokens=template.max_tokens,
        temperature=template.temperature,
        extra_body={"response_format": {"type": "json_object"}}
    )

    response_text = response.choices[0].message.content.strip()
    result = json.loads(response_text)
    tokens_used = response.usage.total_tokens if response.usage else 0

    logger.info(f"Test scenario analysis: {len(items)} items, {tokens_used} tokens")

    return jsonify({
        'success': True,
        'analysis': result,
        'model_used': model,
        'tokens_used': tokens_used,
        'template_info': {
            'id': template.id,
            'field_key': template.field_key,
            'max_tokens': template.max_tokens,
            'temperature': template.temperature
        }
    })
