"""
Admin routes for managing AI Field Prompt Templates.

Provides CRUD operations for configuring field-specific AI prompts
that power the AI-assist feature across forms.
"""

import logging
from flask import jsonify, request, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.ai_assist import FieldPromptService
from db.models import FieldPromptTemplate

logger = logging.getLogger(__name__)


@data_bp.get("/admin/field-prompts")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def list_field_prompts():
    """
    Get all field prompt templates.

    Returns:
        List of all field prompts (active and inactive)
    """
    templates = FieldPromptService.get_all()
    return jsonify({
        'success': True,
        'prompts': [t.to_dict() for t in templates]
    })


@data_bp.get("/admin/field-prompts/<field_key>")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def get_field_prompt(field_key: str):
    """
    Get a single field prompt template by field key.

    Args:
        field_key: The unique field key (e.g., 'scenario.settings.name')

    Returns:
        The prompt template details
    """
    # Handle URL-encoded field keys (dots might be encoded)
    field_key = field_key.replace('%2E', '.')

    template = FieldPromptTemplate.query.filter_by(field_key=field_key).first()
    if not template:
        raise NotFoundError(f"Field prompt not found: {field_key}")

    return jsonify({
        'success': True,
        'prompt': template.to_dict()
    })


@data_bp.post("/admin/field-prompts")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def create_field_prompt():
    """
    Create a new field prompt template.

    Body:
        field_key: Unique key (required)
        display_name: Human-readable name (required)
        system_prompt: System prompt for LLM (required)
        user_prompt_template: User prompt with {variables} (required)
        description: Help text (optional)
        context_variables: List of expected variables (optional)
        max_tokens: Maximum tokens (optional, default 200)
        temperature: LLM temperature (optional, default 0.7)

    Returns:
        The created prompt template
    """
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required_fields = ['field_key', 'display_name', 'system_prompt', 'user_prompt_template']
    for field in required_fields:
        if not data.get(field):
            raise ValidationError(f"Missing required field: {field}")

    # Check for duplicate field_key
    existing = FieldPromptTemplate.query.filter_by(field_key=data['field_key']).first()
    if existing:
        raise ValidationError(f"Field prompt already exists: {data['field_key']}")

    # Create the template
    template = FieldPromptService.create(
        field_key=data['field_key'],
        display_name=data['display_name'],
        system_prompt=data['system_prompt'],
        user_prompt_template=data['user_prompt_template'],
        description=data.get('description'),
        context_variables=data.get('context_variables', []),
        max_tokens=data.get('max_tokens', 200),
        temperature=data.get('temperature', 0.7),
    )

    logger.info(f"Created field prompt: {template.field_key} by {g.authentik_user.username}")

    return jsonify({
        'success': True,
        'prompt': template.to_dict()
    }), 201


@data_bp.put("/admin/field-prompts/<int:template_id>")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def update_field_prompt(template_id: int):
    """
    Update a field prompt template.

    Args:
        template_id: The prompt template ID

    Body:
        Any of: display_name, description, system_prompt, user_prompt_template,
                context_variables, max_tokens, temperature, is_active

    Returns:
        The updated prompt template
    """
    data = request.get_json(silent=True) or {}

    template = FieldPromptService.update(template_id, **data)
    if not template:
        raise NotFoundError(f"Field prompt not found: {template_id}")

    logger.info(f"Updated field prompt: {template.field_key} by {g.authentik_user.username}")

    return jsonify({
        'success': True,
        'prompt': template.to_dict()
    })


@data_bp.delete("/admin/field-prompts/<int:template_id>")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def delete_field_prompt(template_id: int):
    """
    Delete a field prompt template.

    Args:
        template_id: The prompt template ID

    Returns:
        Success status
    """
    template = FieldPromptTemplate.query.get(template_id)
    if not template:
        raise NotFoundError(f"Field prompt not found: {template_id}")

    field_key = template.field_key

    if not FieldPromptService.delete(template_id):
        raise NotFoundError(f"Field prompt not found: {template_id}")

    logger.info(f"Deleted field prompt: {field_key} by {g.authentik_user.username}")

    return jsonify({
        'success': True,
        'message': f"Deleted field prompt: {field_key}"
    })


@data_bp.post("/admin/field-prompts/<int:template_id>/test")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def test_field_prompt(template_id: int):
    """
    Test a field prompt with sample context.

    Args:
        template_id: The prompt template ID

    Body:
        context: Dictionary of context variables

    Returns:
        Generated value from the LLM
    """
    from services.llm.llm_client_factory import LLMClientFactory

    data = request.get_json(silent=True) or {}
    context = data.get('context', {})

    template = FieldPromptTemplate.query.get(template_id)
    if not template:
        raise NotFoundError(f"Field prompt not found: {template_id}")

    # Render the prompt
    rendered_prompt = FieldPromptService.render_prompt(template, context)

    # Call the LLM using admin-configured default model
    try:
        from db.models.llm_model import LLMModel
        client = LLMClientFactory.get_client_for_model(None)
        model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        if not model:
            raise ValidationError("No default LLM model configured")
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

        logger.info(f"Tested field prompt: {template.field_key} - {tokens_used} tokens")

        return jsonify({
            'success': True,
            'value': generated_value,
            'rendered_prompt': rendered_prompt,
            'tokens_used': tokens_used
        })

    except Exception as e:
        logger.error(f"Field prompt test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'rendered_prompt': rendered_prompt
        }), 500


@data_bp.post("/admin/field-prompts/seed-defaults")
@require_permission("admin:field_prompts:manage")
@handle_api_errors(logger_name='field_prompts')
def seed_default_prompts():
    """
    Seed default field prompts.

    Only creates prompts that don't exist yet.

    Returns:
        Number of prompts created
    """
    created = FieldPromptService.seed_defaults()

    return jsonify({
        'success': True,
        'created': created,
        'message': f"Created {created} default field prompts"
    })
