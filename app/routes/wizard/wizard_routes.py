"""
Wizard API Routes

REST API for programmatic Scenario Wizard access.

Endpoints:
- POST   /api/wizard/sessions              - Create new session
- GET    /api/wizard/sessions/{id}         - Get session status
- DELETE /api/wizard/sessions/{id}         - Delete session
- POST   /api/wizard/sessions/{id}/files   - Upload file(s)
- POST   /api/wizard/sessions/{id}/analyze - Run AI analysis
- PUT    /api/wizard/sessions/{id}/config  - Update configuration
- POST   /api/wizard/sessions/{id}/preview - Get preview of items
- POST   /api/wizard/sessions/{id}/create  - Create scenario

Authentication:
- X-API-Key header with a valid UserApiKey (wizard or admin scope)
- Authorization: Bearer <key>
"""

from flask import request, jsonify, g, current_app
from functools import wraps
import logging
import os

from . import bp
from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError
from services.wizard import get_scenario_wizard_service

logger = logging.getLogger(__name__)


# =============================================================================
# Authentication
# =============================================================================

def require_wizard_api_key(f):
    """
    Decorator to require API key authentication for Wizard API.

    Checks for API key in:
    1. X-API-Key header
    2. Authorization: Bearer <key> header

    Validates against UserApiKey table. Keys must have 'wizard' or 'admin' scope.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from db.models import UserApiKey
        from db import db

        # Get API key from request
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]

        if not api_key:
            logger.warning(f"Wizard API: No API key provided from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'API key required. Use X-API-Key header or Authorization: Bearer <key>'
            }), 401

        # Validate against UserApiKey table
        user_api_key = UserApiKey.find_by_key(api_key)
        if not user_api_key:
            logger.warning(f"Wizard API: Invalid API key from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401

        # Check if key has wizard scope
        scopes = user_api_key.scopes.split(',') if user_api_key.scopes else []
        if not ('wizard' in scopes or 'admin' in scopes):
            logger.warning(f"Wizard API: Key lacks wizard scope from {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'API key lacks wizard scope. Create a key with wizard or admin scope.'
            }), 403

        # Update last used timestamp
        user_api_key.update_last_used()
        db.session.commit()

        # Store user in g for potential later use
        g.wizard_user = user_api_key.user
        g.wizard_api_key = user_api_key
        logger.info(f"Wizard API: Authenticated as {user_api_key.user.username}")

        return f(*args, **kwargs)

    return decorated


def log_wizard_request():
    """Log wizard API request for audit."""
    api_key = request.headers.get('X-API-Key', '')
    key_prefix = api_key[:8] + '...' if len(api_key) > 8 else api_key
    logger.info(f"Wizard API: {request.method} {request.path} "
                f"from {request.remote_addr} key_prefix={key_prefix}")


# =============================================================================
# Session Management
# =============================================================================

@bp.route('/sessions', methods=['POST'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def create_session():
    """
    Create a new wizard session.

    Returns:
        {
            "success": true,
            "data": {
                "session_id": "wiz_abc123",
                "status": "initialized",
                ...
            },
            "next_step": "upload",
            "available_actions": ["upload", "delete"]
        }
    """
    log_wizard_request()

    service = get_scenario_wizard_service()
    session = service.create_session()

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'next_step': session.get_next_step(),
        'available_actions': session.get_available_actions(),
    }), 201


@bp.route('/sessions/<session_id>', methods=['GET'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def get_session(session_id: str):
    """
    Get session status and details.

    Returns:
        Session data with current status and available actions
    """
    log_wizard_request()

    service = get_scenario_wizard_service()
    session = service.get_session(session_id)

    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'next_step': session.get_next_step(),
        'available_actions': session.get_available_actions(),
    })


@bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def delete_session(session_id: str):
    """
    Delete a wizard session.

    Returns:
        {"success": true, "deleted": true}
    """
    log_wizard_request()

    service = get_scenario_wizard_service()
    deleted = service.delete_session(session_id)

    if not deleted:
        raise NotFoundError(f"Session not found: {session_id}")

    return jsonify({
        'success': True,
        'deleted': True,
        'session_id': session_id,
    })


# =============================================================================
# File Upload
# =============================================================================

@bp.route('/sessions/<session_id>/files', methods=['POST'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def upload_file(session_id: str):
    """
    Upload a file to the wizard session.

    Supports two modes:
    1. Base64: {"filename": "data.csv", "content_base64": "..."}
    2. Local:  {"file_path": "/path/to/file.csv", "mode": "local"}

    Local mode is only available in development!

    Returns:
        Updated session with file info
    """
    log_wizard_request()

    service = get_scenario_wizard_service()

    # Check if session exists
    session = service.get_session(session_id)
    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No data provided")

    # Mode: Local file path (development only)
    if data.get('mode') == 'local':
        file_path = data.get('file_path')
        if not file_path:
            raise ValidationError("file_path is required for local mode")

        # Security: Only allow in development mode
        is_dev = current_app.debug or os.environ.get('FLASK_ENV') == 'development'
        if not is_dev:
            raise ValidationError("Local file access is only available in development mode")

        # Security: Check if path is within allowed directories
        allowed_dirs = [
            os.path.abspath(current_app.config.get('DATA_DIR', '/app/data')),
            os.path.abspath('/Users'),  # macOS
            os.path.abspath('/home'),   # Linux
        ]

        abs_path = os.path.abspath(file_path)
        if not any(abs_path.startswith(d) for d in allowed_dirs):
            raise ValidationError(f"File path not in allowed directory: {file_path}")

        session = service.upload_file_local(session_id, file_path)

    # Mode: Base64 encoded content
    elif 'content_base64' in data:
        filename = data.get('filename')
        content_base64 = data.get('content_base64')

        if not filename:
            raise ValidationError("filename is required")
        if not content_base64:
            raise ValidationError("content_base64 is required")

        session = service.upload_file_base64(session_id, filename, content_base64)

    else:
        raise ValidationError("Either 'file_path' with 'mode: local' or 'content_base64' is required")

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'next_step': session.get_next_step(),
        'available_actions': session.get_available_actions(),
    })


# =============================================================================
# Analysis
# =============================================================================

@bp.route('/sessions/<session_id>/analyze', methods=['POST'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def analyze_session(session_id: str):
    """
    Run AI analysis on uploaded data.

    Optional request body:
        {"user_intent": "I want to rank LLM outputs"}

    Returns:
        Session with analysis results including:
        - detected_type: Evaluation type (ranking, rating, etc.)
        - field_mapping: Detected field mappings
        - analysis: Full AI analysis result
        - config: Suggested configuration
    """
    log_wizard_request()

    service = get_scenario_wizard_service()

    # Check if session exists
    session = service.get_session(session_id)
    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    data = request.get_json(silent=True) or {}
    user_intent = data.get('user_intent')

    session = service.analyze(session_id, user_intent=user_intent)

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'next_step': session.get_next_step(),
        'available_actions': session.get_available_actions(),
    })


# =============================================================================
# Configuration
# =============================================================================

@bp.route('/sessions/<session_id>/config', methods=['PUT'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def update_config(session_id: str):
    """
    Update session configuration.

    Request body (all fields optional):
        {
            "scenario_name": "My Scenario",
            "eval_type": "ranking",
            "preset": "buckets-3",
            "dimensions": [...],
            "labels": [...],
            "buckets": [...],
            "scale": {"min": 1, "max": 5},
            "owner_id": 1,
            "evaluator_ids": [2, 3]
        }

    Returns:
        Updated session with new configuration
    """
    log_wizard_request()

    service = get_scenario_wizard_service()

    # Check if session exists
    session = service.get_session(session_id)
    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    data = request.get_json(silent=True)
    if not data:
        raise ValidationError("No configuration provided")

    session = service.configure(session_id, data)

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'next_step': session.get_next_step(),
        'available_actions': session.get_available_actions(),
    })


# =============================================================================
# Preview
# =============================================================================

@bp.route('/sessions/<session_id>/preview', methods=['POST'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def get_preview(session_id: str):
    """
    Get preview of transformed items.

    Optional request body:
        {"count": 5}

    Returns:
        {
            "items": [...],
            "total_count": 100,
            "eval_type": "ranking"
        }
    """
    log_wizard_request()

    service = get_scenario_wizard_service()

    # Check if session exists
    session = service.get_session(session_id)
    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    data = request.get_json(silent=True) or {}
    count = data.get('count', 5)

    preview = service.get_preview(session_id, count=count)

    return jsonify({
        'success': True,
        'data': preview,
    })


# =============================================================================
# Create Scenario
# =============================================================================

@bp.route('/sessions/<session_id>/create', methods=['POST'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def create_scenario(session_id: str):
    """
    Create the scenario from session data.

    Returns:
        {
            "success": true,
            "data": {
                "scenario_id": 18,
                "scenario_url": "/scenarios/18/evaluate",
                ...
            }
        }
    """
    log_wizard_request()

    service = get_scenario_wizard_service()

    # Check if session exists
    session = service.get_session(session_id)
    if not session:
        raise NotFoundError(f"Session not found: {session_id}")

    session = service.create_scenario(session_id)

    return jsonify({
        'success': True,
        'data': session.to_dict(),
        'message': f"Scenario created successfully: {session.config.scenario_name}",
        'scenario_id': session.scenario_id,
        'scenario_url': session.scenario_url,
    })


# =============================================================================
# Health & Info
# =============================================================================

@bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint (no auth required).

    Returns:
        {"status": "ok", "service": "wizard-api"}
    """
    return jsonify({
        'status': 'ok',
        'service': 'wizard-api',
        'version': '1.0',
    })


@bp.route('/info', methods=['GET'])
@require_wizard_api_key
@handle_api_errors(logger_name='wizard')
def get_info():
    """
    Get API information and available presets.

    Returns:
        API capabilities and configuration options
    """
    log_wizard_request()

    return jsonify({
        'success': True,
        'data': {
            'version': '1.0',
            'eval_types': [
                {'id': 'ranking', 'name': 'Ranking', 'description': 'Rank/sort multiple items'},
                {'id': 'rating', 'name': 'Rating', 'description': 'Rate items on a scale'},
                {'id': 'comparison', 'name': 'Comparison', 'description': 'Compare two items A/B'},
                {'id': 'authenticity', 'name': 'Authenticity', 'description': 'Human vs AI classification'},
                {'id': 'labeling', 'name': 'Labeling', 'description': 'Assign categories/labels'},
                {'id': 'mail_rating', 'name': 'Mail Rating', 'description': 'Rate conversation quality'},
            ],
            'presets': {
                'ranking': ['buckets-3', 'buckets-5', 'simple-rank'],
                'rating': ['llm-judge-standard', 'summeval', 'response-quality'],
                'labeling': ['binary-authentic', 'sentiment-3', 'multi-label'],
                'comparison': ['pairwise', 'multicriteria'],
            },
            'supported_formats': ['csv', 'json', 'jsonl'],
            'endpoints': [
                'POST /api/wizard/sessions',
                'GET /api/wizard/sessions/{id}',
                'DELETE /api/wizard/sessions/{id}',
                'POST /api/wizard/sessions/{id}/files',
                'POST /api/wizard/sessions/{id}/analyze',
                'PUT /api/wizard/sessions/{id}/config',
                'POST /api/wizard/sessions/{id}/preview',
                'POST /api/wizard/sessions/{id}/create',
            ],
        },
    })
