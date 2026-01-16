"""
AI Assist routes for field generation.

Provides the generation endpoint used by LAIFieldButton components
across the frontend to generate content for form fields.
"""

import logging
from flask import jsonify, request, g, Response, stream_with_context

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.ai_assist import FieldPromptService
from db.models import FieldPromptTemplate

logger = logging.getLogger(__name__)


@data_bp.post("/ai-assist/generate")
@authentik_required
@handle_api_errors(logger_name='ai_assist')
def generate_field_value():
    """
    Generate a value for a form field using AI.

    Body:
        field_key: The field key (e.g., 'scenario.settings.name')
        context: Dictionary of context variables
        stream: Whether to stream the response (optional, default false)

    Returns:
        Generated value from the LLM
    """
    from services.llm.llm_client_factory import LLMClientFactory

    data = request.get_json(silent=True) or {}

    field_key = data.get('field_key')
    if not field_key:
        raise ValidationError("Missing required field: field_key")

    context = data.get('context', {})
    stream = data.get('stream', False)

    # Get the prompt template
    template = FieldPromptService.get_by_field_key(field_key)
    if not template:
        raise NotFoundError(f"No prompt template found for field: {field_key}")

    # Render the prompt
    rendered_prompt = FieldPromptService.render_prompt(template, context)

    # Get LLM client and admin-configured default model
    try:
        from db.models.llm_model import LLMModel
        client = LLMClientFactory.get_client_for_model(None)
        # Use admin-configured default model
        model = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        if not model:
            raise ValidationError("No default LLM model configured")
    except Exception as e:
        logger.error(f"Failed to get LLM client: {e}")
        raise ValidationError("LLM service unavailable")

    if stream:
        return _generate_streaming(client, model, template, rendered_prompt)
    else:
        return _generate_direct(client, model, template, rendered_prompt, field_key)


def _generate_direct(client, model, template, rendered_prompt, field_key):
    """Generate content directly (non-streaming)."""
    try:
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

        logger.info(f"AI assist generated: {field_key} - {tokens_used} tokens for {g.authentik_user.username}")

        return jsonify({
            'success': True,
            'value': generated_value,
            'field_key': field_key,
            'tokens_used': tokens_used
        })

    except Exception as e:
        logger.error(f"AI assist generation failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _generate_streaming(client, model, template, rendered_prompt):
    """Generate content with streaming."""
    import json

    def generate():
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": template.system_prompt},
                    {"role": "user", "content": rendered_prompt}
                ],
                max_tokens=template.max_tokens,
                temperature=template.temperature,
                stream=True,
            )

            full_content = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_content += delta
                    yield f"data: {json.dumps({'delta': delta})}\n\n"

            yield f"data: {json.dumps({'done': True, 'value': full_content})}\n\n"

        except Exception as e:
            logger.error(f"Streaming generation failed: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@data_bp.get("/ai-assist/prompts")
@authentik_required
@handle_api_errors(logger_name='ai_assist')
def list_available_prompts():
    """
    List all available field prompts for the current user.

    Returns only active prompts with basic info (no full prompt content).
    Used by frontend to show which fields have AI assist available.
    """
    templates = FieldPromptService.get_all_active()

    return jsonify({
        'success': True,
        'prompts': [
            {
                'field_key': t.field_key,
                'display_name': t.display_name,
                'description': t.description,
            }
            for t in templates
        ]
    })
