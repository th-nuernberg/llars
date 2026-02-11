"""
REST API Routes for LLARS Data Importer.

Endpoints:
- POST /api/import/upload - Upload and analyze file
- GET /api/import/session/{id} - Get session status
- POST /api/import/transform - Transform data
- POST /api/import/validate - Validate transformed data
- POST /api/import/execute - Execute import
- GET /api/import/formats - List supported formats
- POST /api/import/ai/analyze - AI-assisted analysis
- POST /api/import/ai/transform - AI-generated transform script
- POST /api/import/ai/chat-stream - Streaming chat for config refinement
"""

from flask import request, jsonify, g, Response
import json
import logging

from . import bp
from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, ValidationError

from services.data_import import ImportService
from services.data_import.ai_analyzer import AIAnalyzer
from services.data_import.adapters.base_adapter import TaskType

logger = logging.getLogger(__name__)

# Service instances
import_service = ImportService()
_ai_analyzer = None


def get_ai_analyzer():
    """Lazy initialization of AIAnalyzer to avoid app context issues."""
    global _ai_analyzer
    if _ai_analyzer is None:
        _ai_analyzer = AIAnalyzer()
    return _ai_analyzer


@bp.route('/formats', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='import')
def get_formats():
    """Get list of supported import formats."""
    formats = import_service.get_available_formats()
    return jsonify({
        "formats": formats,
        "task_types": [t.value for t in TaskType],
    })


@bp.route('/upload', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def upload_file():
    """
    Upload a file and analyze its format.

    Expects multipart form data with 'file' field.

    Returns:
        Session object with detection results
    """
    if 'file' not in request.files:
        raise ValidationError("No file provided")

    file = request.files['file']
    if not file.filename:
        raise ValidationError("Empty filename")

    # Read content
    content = file.read()
    filename = file.filename

    # Create session
    session = import_service.create_session(
        filename=filename,
        file_size=len(content)
    )

    # Analyze file
    session = import_service.analyze_file(
        session_id=session.session_id,
        content=content,
        filename=filename
    )

    return jsonify(session.to_dict()), 201


@bp.route('/session/<session_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='import')
def get_session(session_id: str):
    """Get session status and details."""
    session = import_service.get_session(session_id)
    if not session:
        raise ValidationError(f"Session not found: {session_id}")

    return jsonify(session.to_dict())


@bp.route('/session/<session_id>/sample', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='import')
def get_sample(session_id: str):
    """Get sample of transformed items for preview."""
    count = request.args.get('count', 5, type=int)
    sample = import_service.get_sample(session_id, count)

    return jsonify({
        "session_id": session_id,
        "sample": sample,
        "count": len(sample),
    })


@bp.route('/transform', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def transform_data():
    """
    Transform raw data using detected or specified format.

    Request body:
        {
            "session_id": "...",
            "options": {
                "mappings": {...},
                "format_override": "openai"
            }
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    options = data.get('options', {})

    # Apply format override if specified
    if 'format_override' in options:
        session = import_service.get_session(session_id)
        if session:
            session.detected_format = options['format_override']

    session = import_service.transform(session_id, options)

    return jsonify(session.to_dict())


@bp.route('/validate', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def validate_data():
    """
    Validate transformed data.

    Request body:
        {
            "session_id": "..."
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    session = import_service.validate(session_id)

    return jsonify(session.to_dict())


@bp.route('/execute', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def execute_import():
    """
    Execute the import and create database records.

    Request body:
        {
            "session_id": "...",
            "task_type": "rating",
            "source_name": "My Dataset",
            "create_scenario": true,
            "scenario_id": 123,  (optional, existing scenario to import into)
            "ai_analysis": {...}  (optional, from ai/analyze-intent)
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    # Get optional parameters
    task_type = None
    if 'task_type' in data:
        try:
            task_type = TaskType(data['task_type'])
        except ValueError:
            raise ValidationError(f"Invalid task_type: {data['task_type']}")

    source_name = data.get('source_name')
    create_scenario = data.get('create_scenario', True)  # Default to True
    scenario_id = data.get('scenario_id')  # Existing scenario to import into
    ai_analysis = data.get('ai_analysis')

    # Get username from authenticated user
    created_by = None
    if hasattr(g, 'authentik_user') and g.authentik_user:
        created_by = g.authentik_user.username if hasattr(g.authentik_user, 'username') else str(g.authentik_user)

    session = import_service.execute_import(
        session_id=session_id,
        task_type=task_type,
        source_name=source_name,
        create_scenario=create_scenario,
        scenario_id=scenario_id,
        created_by=created_by,
        ai_analysis=ai_analysis
    )

    return jsonify(session.to_dict())


@bp.route('/session/<session_id>', methods=['DELETE'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def delete_session(session_id: str):
    """Delete an import session."""
    deleted = import_service.delete_session(session_id)

    if not deleted:
        raise ValidationError(f"Session not found: {session_id}")

    return jsonify({"deleted": True, "session_id": session_id})


@bp.route('/from-data', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def import_from_data():
    """
    Import data directly from parsed JSON (without file upload).

    Used by ScenarioWizard which parses files client-side.

    Request body:
        {
            "data": [...],           // Array of items to import
            "scenario_id": 123,      // Existing scenario to import into
            "task_type": "authenticity",
            "source_name": "Wizard Import",
            "field_mapping": {       // Optional: AI-suggested field mappings
                "id_field": "chat_id",
                "content_field": "messages",
                "label_field": "subject",
                "reference_field": null
            }
        }

    Returns:
        {
            "success": true,
            "imported_count": 5,
            "thread_ids": [1, 2, 3, 4, 5]
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    items = data.get('data')
    if not items or not isinstance(items, list):
        raise ValidationError("'data' must be a non-empty array")

    scenario_id = data.get('scenario_id')
    if not scenario_id:
        raise ValidationError("scenario_id is required")

    # Get task type
    task_type = None
    if 'task_type' in data:
        try:
            task_type = TaskType(data['task_type'])
        except ValueError:
            raise ValidationError(f"Invalid task_type: {data['task_type']}")

    source_name = data.get('source_name', 'Wizard Import')

    # Get AI-suggested field mappings (optional)
    field_mapping = data.get('field_mapping')

    # Get filename for context (helps AI detect Long-Format patterns)
    filename = data.get('filename', source_name)

    # =========================================================================
    # Long-Format Detection & Transformation
    # =========================================================================
    # Long-Format: Same ID appears multiple times with different variants
    # Example: CSV with rows [S001,gpt4,output1], [S001,claude,output2], etc.
    # This needs to be transformed to LLARS ranking format before import.
    #
    # KEY HEURISTIC:
    # - 1 Reference → N Outputs = RANKING (compare/sort outputs)
    # - 1 Reference → 1 Output = RATING (rate single output quality)
    # =========================================================================
    # Skip long-format detection if data was already transformed by frontend
    # (e.g., generation data transformed to wide-format for ranking)
    skip_long_format = (
        field_mapping
        and field_mapping.get('from_generation')
    )

    ai_analyzer = get_ai_analyzer()

    if not skip_long_format and ai_analyzer._detect_long_format(items):
        logger.info(f"Long-Format detected for {filename}, generating field mapping...")

        # Generate field mapping for Long-Format data
        long_format_mapping = ai_analyzer.generate_field_mapping(
            data=items,
            detected_type=task_type.value if task_type else 'ranking',
            detected_format='long',
            filename=filename
        )

        if long_format_mapping.get('success') and long_format_mapping.get('format') == 'long':
            logger.info(f"Long-Format mapping: grouping={long_format_mapping.get('grouping_field')}, "
                       f"variant={long_format_mapping.get('variant_field')}, "
                       f"output={long_format_mapping.get('output_field')}")

            # KEY HEURISTIC: Long-Format with multiple outputs per reference = RANKING
            # This overrides any previous task_type detection because:
            # - Multiple outputs for same input = comparison task = ranking
            variants_per_group = long_format_mapping.get('variants_per_group', 0)
            if variants_per_group > 1:
                logger.info(f"Long-Format has {variants_per_group} variants per group -> forcing RANKING type")
                task_type = TaskType.RANKING

            # Transform Long-Format to LLARS ranking format
            items = ai_analyzer.transform_long_format_to_ranking(items, long_format_mapping)
            logger.info(f"Long-Format transformation complete: {len(items)} ranking items")

            # Update field mapping with Long-Format info
            if not field_mapping:
                field_mapping = {}
            field_mapping['long_format'] = True
            field_mapping['original_mapping'] = long_format_mapping
        else:
            logger.warning(f"Long-Format mapping failed: {long_format_mapping.get('error', 'unknown')}")

    # Create session from (potentially transformed) data
    session = import_service.create_session_from_data(
        data=items,
        task_type=task_type,
        filename=source_name
    )

    # Build AI analysis object for UniversalTransformer
    # This ensures ranking feature detection works correctly
    ai_analysis = {
        'task_type': task_type.value if task_type else 'mail_rating',
        'field_mapping': field_mapping or {},
        'role_mapping': {'user': 'Klient', 'assistant': 'Berater'},
        'evaluation_criteria': []
    }

    if field_mapping:
        logger.info(f"Using AI-provided field mappings: {field_mapping}")

    # Use transform_with_ai to leverage UniversalTransformer
    # This enables ranking feature detection (source_text + summary_a/b/c)
    session = import_service.transform_with_ai(session.session_id, ai_analysis=ai_analysis)

    if session.status == "error":
        raise ValidationError(f"Transform failed: {session.errors}")

    # Execute import into existing scenario
    # force_new_threads: generation data uses generic IDs ("0","1","2") that
    # would collide with existing threads via chat_id hash dedup.
    session = import_service.execute_import(
        session_id=session.session_id,
        task_type=task_type,
        source_name=source_name,
        create_scenario=False,
        scenario_id=scenario_id,
        force_new_threads=skip_long_format  # True when from_generation
    )

    if session.status == "error":
        raise ValidationError(f"Import failed: {session.errors}")

    # Clean up session
    import_service.delete_session(session.session_id)

    return jsonify({
        "success": True,
        "imported_count": session.imported_count,
        "scenario_id": scenario_id,
        "warnings": session.warnings
    })


# ============================================================================
# AI-Assisted Endpoints
# ============================================================================

@bp.route('/ai/analyze', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def ai_analyze():
    """
    Use AI to analyze data structure.

    Request body:
        {
            "session_id": "...",
        }
        OR
        {
            "data": {...},
            "filename": "..."
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    # Get data from session or direct input
    if 'session_id' in data:
        session = import_service.get_session(data['session_id'])
        if not session:
            raise ValidationError(f"Session not found: {data['session_id']}")
        raw_data = session.raw_data
        filename = session.filename
    elif 'data' in data:
        raw_data = data['data']
        filename = data.get('filename')
    else:
        raise ValidationError("Either session_id or data is required")

    # Run AI analysis
    result = get_ai_analyzer().analyze_structure(raw_data, filename)

    return jsonify(result)


@bp.route('/ai/analyze-intent', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def ai_analyze_intent():
    """
    Analyze user intent together with data structure.

    This is the main endpoint for the new "conversational" import wizard.
    The user describes what they want to do in natural language, and
    the AI extracts: task type, field mapping, evaluation criteria.

    Request body:
        {
            "session_id": "...",
            "user_intent": "Ich möchte die Qualität der Berater-Antworten bewerten...",
            "file_count": 523
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    user_intent = data.get('user_intent', '')
    if not user_intent or len(user_intent) < 10:
        raise ValidationError("user_intent must be at least 10 characters")

    file_count = data.get('file_count', 1)

    session = import_service.get_session(session_id)
    if not session:
        raise ValidationError(f"Session not found: {session_id}")

    # Run AI analysis with user intent
    result = get_ai_analyzer().analyze_intent(
        data=session.raw_data,
        user_intent=user_intent,
        filename=session.filename,
        file_count=file_count,
        detected_structure=session.structure
    )

    return jsonify(result)


@bp.route('/ai/transform', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def ai_transform():
    """
    Transform data using AI-generated field mappings.

    This is the main endpoint for the "conversational import" workflow.
    Uses the UniversalTransformer to apply AI-analyzed mappings.

    Request body:
        {
            "session_id": "...",
            "ai_analysis": {
                "task_type": "authenticity",
                "field_mapping": {...},
                "role_mapping": {...},
                "evaluation_criteria": [...]
            }
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    ai_analysis = data.get('ai_analysis')
    if not ai_analysis:
        raise ValidationError("ai_analysis is required")

    session = import_service.transform_with_ai(session_id, ai_analysis)

    return jsonify(session.to_dict())


@bp.route('/ai/transform-script', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def ai_transform_script():
    """
    Generate a transformation script using AI.

    Request body:
        {
            "session_id": "...",
            "field_hints": {
                "id_field": "conversation_id",
                "messages_field": "turns"
            }
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    # Get data from session
    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    session = import_service.get_session(session_id)
    if not session:
        raise ValidationError(f"Session not found: {session_id}")

    field_hints = data.get('field_hints', {})

    # Generate script
    result = get_ai_analyzer().generate_transform_script(
        data=session.raw_data,
        field_hints=field_hints
    )

    return jsonify(result)


@bp.route('/ai/suggest', methods=['POST'])
@authentik_required
@require_permission('data:import')
@handle_api_errors(logger_name='import')
def ai_suggest():
    """
    Get AI suggestions for improving field mapping.

    Request body:
        {
            "session_id": "...",
            "current_mapping": {...}
        }
    """
    data = request.get_json()
    if not data:
        raise ValidationError("No data provided")

    session_id = data.get('session_id')
    if not session_id:
        raise ValidationError("session_id is required")

    session = import_service.get_session(session_id)
    if not session:
        raise ValidationError(f"Session not found: {session_id}")

    current_mapping = data.get('current_mapping', session.structure.get('detected_mappings', {}))

    result = get_ai_analyzer().suggest_improvements(
        data=session.raw_data,
        current_mapping=current_mapping
    )

    return jsonify(result)


@bp.route('/ai/chat-stream', methods=['POST'])
@authentik_required
@require_permission('data:import')
def ai_chat_stream():
    """
    SSE streaming chat for scenario configuration refinement.

    Enables conversational refinement of scenario configuration.
    The AI extracts structured config updates (labels, buckets, scales)
    during streaming and emits them as SSE events.

    Request body:
        {
            "session_id": "...",
            "messages": [
                {"role": "user", "content": "Ich möchte 3 Labels..."}
            ],
            "current_config": {
                "task_type": "authenticity",
                "labels": [...]
            }
        }

    SSE Events:
        - thinking: KI verarbeitet ({"message": "..."})
        - config: Konfigurationsupdate ({"field": "labels", "value": [...]})
        - chunk: Text-Chunk ({"content": "..."})
        - done: Fertig ({"config": {...}, "response": "..."})
        - error: Fehler ({"error": "..."})
    """
    data = request.get_json(silent=True) or {}

    # Validate input
    session_id = data.get('session_id')
    if not session_id:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'session_id is required'})}\n\n",
            mimetype='text/event-stream'
        )

    messages = data.get('messages', [])
    if not messages:
        return Response(
            f"event: error\ndata: {json.dumps({'error': 'messages array is required'})}\n\n",
            mimetype='text/event-stream'
        )

    current_config = data.get('current_config', {})

    # Get session
    session = import_service.get_session(session_id)
    if not session:
        return Response(
            f"event: error\ndata: {json.dumps({'error': f'Session not found: {session_id}'})}\n\n",
            mimetype='text/event-stream'
        )

    # Pre-fetch context-dependent data before generator starts
    username = g.authentik_user.username if g.authentik_user else 'unknown'
    raw_data = session.raw_data
    filename = session.filename

    # Get AI analyzer instance
    ai_analyzer = get_ai_analyzer()

    def generate():
        """
        Generator function for SSE streaming.
        NOTE: This runs OUTSIDE Flask request context.
        """
        try:
            for event in ai_analyzer.chat_refine_streaming(
                data=raw_data,
                messages=messages,
                current_config=current_config,
                filename=filename
            ):
                event_type = event.get('type', 'chunk')

                if event_type == 'thinking':
                    yield f"event: thinking\ndata: {json.dumps({'message': event.get('message', '')})}\n\n"
                elif event_type == 'config':
                    yield f"event: config\ndata: {json.dumps({'field': event.get('field'), 'value': event.get('value')})}\n\n"
                elif event_type == 'chunk':
                    yield f"event: chunk\ndata: {json.dumps({'content': event.get('content', '')})}\n\n"
                elif event_type == 'done':
                    yield f"event: done\ndata: {json.dumps({'config': event.get('config', {}), 'response': event.get('response', '')})}\n\n"
                elif event_type == 'error':
                    yield f"event: error\ndata: {json.dumps({'error': event.get('error', 'Unknown error')})}\n\n"

            logger.info(f"AI chat stream completed for {username}, session {session_id}")

        except Exception as e:
            logger.exception(f"AI chat stream failed: {e}")
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
