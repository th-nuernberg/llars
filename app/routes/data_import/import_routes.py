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
"""

from flask import request, jsonify, g
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
            "source_name": "My Dataset"
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

    session = import_service.execute_import(
        session_id=session_id,
        task_type=task_type,
        source_name=source_name
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
