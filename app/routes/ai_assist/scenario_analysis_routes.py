"""
AI-powered scenario data analysis routes.

Provides intelligent analysis of uploaded data to suggest
evaluation type, scenario name, description, and configuration.
Supports both standard and streaming (SSE) responses.
"""

import json
import logging
from flask import jsonify, request, g, Response

from auth.decorators import authentik_required, api_key_or_token_required
from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.ai_assist import FieldPromptService
from services.ai_assist.data_preprocessor import DataPreprocessor

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
@api_key_or_token_required
@require_permission('data:import')
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

    # Preprocess data: extract schema, select samples, detect patterns
    preprocessed = DataPreprocessor.preprocess(items, filename)
    preprocessed_text = DataPreprocessor.format_for_prompt(preprocessed)

    # Load prompt template from database (configurable via Admin Panel)
    template = FieldPromptService.get_by_field_key(SCENARIO_ANALYSIS_FIELD_KEY)
    if not template:
        raise NotFoundError(
            f"Prompt template '{SCENARIO_ANALYSIS_FIELD_KEY}' not found. "
            "Please seed defaults via Admin Panel or API."
        )

    # Build context for prompt rendering
    context = {
        "preprocessed_data": preprocessed_text,
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

        # Build response with preprocessed data summary
        schema = preprocessed.get('schema', {})
        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(schema.keys()),
                    'field_types': {k: v.get('type', 'unknown') for k, v in schema.items()},
                    'field_completeness': {k: v.get('completeness', 0) for k, v in schema.items()},
                    'sample_items': preprocessed.get('samples', [])[:3],
                    'detected_patterns': preprocessed.get('detected_patterns', [])
                },
                'suggestions': result.get('suggestions', {}),
                'data_quality': result.get('data_quality', {})
            },
            'tokens_used': tokens_used
        })

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        # Return partial result with local analysis only
        schema = preprocessed.get('schema', {})
        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(schema.keys()),
                    'field_types': {k: v.get('type', 'unknown') for k, v in schema.items()},
                    'field_completeness': {k: v.get('completeness', 0) for k, v in schema.items()},
                    'sample_items': preprocessed.get('samples', [])[:3],
                    'detected_patterns': preprocessed.get('detected_patterns', [])
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
        schema = preprocessed.get('schema', {})
        return jsonify({
            'success': True,
            'analysis': {
                'data_summary': {
                    'item_count': len(items),
                    'fields': list(schema.keys()),
                    'field_types': {k: v.get('type', 'unknown') for k, v in schema.items()},
                    'field_completeness': {k: v.get('completeness', 0) for k, v in schema.items()},
                    'sample_items': preprocessed.get('samples', [])[:3],
                    'detected_patterns': preprocessed.get('detected_patterns', [])
                },
                'suggestions': None,
                'data_quality': None,
                'ai_error': str(e)
            },
            'tokens_used': 0
        })


@data_bp.post("/ai-assist/analyze-scenario-data/stream")
@api_key_or_token_required
@require_permission('data:import')
@handle_api_errors(logger_name='ai_assist')
def analyze_scenario_data_stream():
    """
    Stream AI analysis of uploaded data using Server-Sent Events (SSE).

    Emits events:
        data_summary: Immediate local analysis (fields, types, counts)
        thinking: AI is processing the data
        chunk: Streaming token from LLM
        suggestions: Parsed AI suggestions (eval_type, name, description)
        data_quality: Data quality assessment
        done: Analysis complete
        error: Error occurred

    Body:
        data: List of data items (required)
        filename: Original filename for context (optional)
        file_count: Number of files uploaded (optional)
        user_hint: User's description of what they want (optional)
    """
    from services.llm.llm_client_factory import LLMClientFactory
    from db.models.llm_model import LLMModel

    data = request.get_json(silent=True) or {}

    # Validate input
    items = data.get('data', [])
    if not items:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'Missing required field: data'})}\n\n",
            mimetype='text/event-stream'
        )
    if not isinstance(items, list) or len(items) == 0:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'Field data must be a non-empty array'})}\n\n",
            mimetype='text/event-stream'
        )

    filename = data.get('filename', 'unknown')
    file_count = data.get('file_count', 1)
    user_hint = data.get('user_hint', '')

    # PRE-FETCH all context-dependent data BEFORE the generator starts
    # (generator runs outside Flask request context)
    username = g.authentik_user.username if g.authentik_user else 'unknown'

    # Load prompt template (requires app context)
    template = FieldPromptService.get_by_field_key(SCENARIO_ANALYSIS_FIELD_KEY)
    if not template:
        return Response(
            f"event: error\ndata: {json.dumps({'error': f'Prompt template {SCENARIO_ANALYSIS_FIELD_KEY} not found'})}\n\n",
            mimetype='text/event-stream'
        )

    # Get LLM model (requires app context)
    model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
    if not model_id:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'No default LLM model configured'})}\n\n",
            mimetype='text/event-stream'
        )

    # Get LLM client (requires app context for config lookup)
    client = LLMClientFactory.get_client_for_model(None)

    # Extract template settings for use in generator
    system_prompt = template.system_prompt
    max_tokens = template.max_tokens
    temperature = template.temperature

    # Preprocess data: extract schema, select samples, detect patterns
    preprocessed = DataPreprocessor.preprocess(items, filename)
    preprocessed_text = DataPreprocessor.format_for_prompt(preprocessed)

    # Build context for prompt
    context = {
        "preprocessed_data": preprocessed_text,
        "user_hint_text": f'Benutzerhinweis: {user_hint}' if user_hint else ''
    }
    user_prompt = FieldPromptService.render_prompt(template, context)

    # Extract schema for data_summary event
    schema = preprocessed.get('schema', {})

    def generate():
        """
        Generator function for SSE streaming.
        NOTE: This runs OUTSIDE Flask request context.
        All Flask-dependent data must be pre-fetched above.
        """
        try:
            # Step 1: Emit immediate local analysis with preprocessed data
            data_summary = {
                'item_count': len(items),
                'fields': list(schema.keys()),
                'field_types': {k: v.get('type', 'unknown') for k, v in schema.items()},
                'field_completeness': {k: v.get('completeness', 0) for k, v in schema.items()},
                'sample_items': preprocessed.get('samples', [])[:3],
                'detected_patterns': preprocessed.get('detected_patterns', [])
            }
            yield f"event: data_summary\ndata: {json.dumps(data_summary)}\n\n"

            # Step 2: Signal AI is thinking
            yield f"event: thinking\ndata: {json.dumps({'status': 'analyzing', 'message': 'KI analysiert die Daten...'})}\n\n"

            # Step 3: Stream LLM response (client already created with context)
            response_text = ""
            tokens_used = 0

            stream = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                extra_body={"response_format": {"type": "json_object"}}
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    response_text += content
                    yield f"event: chunk\ndata: {json.dumps({'content': content})}\n\n"

                # Capture usage from final chunk if available
                if hasattr(chunk, 'usage') and chunk.usage:
                    tokens_used = chunk.usage.total_tokens

            # Step 4: Parse and emit structured suggestions
            try:
                result = json.loads(response_text)
                suggestions = result.get('suggestions', {})
                data_quality = result.get('data_quality', {})

                yield f"event: suggestions\ndata: {json.dumps(suggestions)}\n\n"
                yield f"event: data_quality\ndata: {json.dumps(data_quality)}\n\n"

            except json.JSONDecodeError as e:
                # Log without Flask context (use print as fallback)
                print(f"Failed to parse LLM response as JSON: {e}")
                yield f"event: suggestions\ndata: {json.dumps({'parse_error': True})}\n\n"

            # Step 5: Done
            yield f"event: done\ndata: {json.dumps({'tokens_used': tokens_used, 'success': True})}\n\n"

            # Log completion (username captured before generator)
            print(f"AI scenario analysis stream completed for {username}: {len(items)} items, {tokens_used} tokens")

        except Exception as e:
            print(f"AI scenario analysis stream failed: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


@data_bp.post("/ai-assist/scenario-chat/stream")
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='ai_assist')
def scenario_chat_stream():
    """
    Streaming chat for scenario configuration refinement.

    Unlike /api/import/ai/chat-stream, this endpoint accepts data directly
    rather than requiring an import session. Used by the Scenario Wizard.

    Body:
        data: Sample data items (required)
        messages: Chat history [{role, content}] (required)
        current_config: Current configuration to refine (optional)
        filename: Original filename for context (optional)

    SSE Events:
        thinking: AI is processing
        config_update: Configuration change (field + value)
        chunk: Text chunk from LLM
        done: Chat complete
        error: Error occurred
    """
    from services.data_import.ai_analyzer import AIAnalyzer

    request_data = request.get_json(silent=True) or {}

    # Validate input
    data = request_data.get('data', [])
    messages = request_data.get('messages', [])

    if not messages:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'messages array is required'})}\n\n",
            mimetype='text/event-stream'
        )

    current_config = request_data.get('current_config', {})
    filename = request_data.get('filename', 'data')

    # Pre-fetch user info before generator
    username = g.authentik_user.username if g.authentik_user else 'unknown'

    # Initialize AI analyzer
    ai_analyzer = AIAnalyzer()

    def generate():
        """Generator for SSE streaming - runs outside Flask context."""
        try:
            for event in ai_analyzer.chat_refine_streaming(
                data=data,
                messages=messages,
                current_config=current_config,
                filename=filename
            ):
                event_type = event.get('type', 'chunk')

                if event_type == 'thinking':
                    yield f"event: thinking\ndata: {json.dumps({'message': event.get('message', '')})}\n\n"
                elif event_type == 'config':
                    yield f"event: config_update\ndata: {json.dumps({'field': event.get('field'), 'value': event.get('value')})}\n\n"
                elif event_type == 'chunk':
                    yield f"event: chunk\ndata: {json.dumps({'content': event.get('content', '')})}\n\n"
                elif event_type == 'done':
                    yield f"event: done\ndata: {json.dumps({'config': event.get('config', {}), 'response': event.get('response', '')})}\n\n"
                elif event_type == 'error':
                    yield f"event: error\ndata: {json.dumps({'error': event.get('error', 'Unknown error')})}\n\n"

            print(f"Scenario chat stream completed for {username}")

        except Exception as e:
            print(f"Scenario chat stream failed: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )
