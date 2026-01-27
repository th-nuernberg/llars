"""
API Key Management Routes.

Endpoints for users to manage their personal API keys.
"""

import logging
import secrets

from flask import Blueprint, g, jsonify

from auth.decorators import authentik_required
from db import db
from decorators.error_handler import handle_api_errors

logger = logging.getLogger(__name__)

api_key_bp = Blueprint('api_key', __name__, url_prefix='/api/auth')


@api_key_bp.route('/api-key', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def get_api_key():
    """
    Get the current user's API key.

    Returns:
        200: API key (partially masked for security)
    """
    user = g.authentik_user

    # Ensure user has an API key
    if not user.api_key:
        user.api_key = secrets.token_urlsafe(32)
        db.session.commit()

    # Return full key (user can only see their own)
    return jsonify({
        'success': True,
        'api_key': user.api_key,
        'username': user.username,
        'usage': {
            'header': 'X-API-Key: <your-api-key>',
            'query': '?api_key=<your-api-key>',
            'example': f'curl -H "X-API-Key: {user.api_key}" http://localhost:55080/api/...'
        }
    })


@api_key_bp.route('/api-key/regenerate', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def regenerate_api_key():
    """
    Regenerate the current user's API key.

    This invalidates the old key immediately.

    Returns:
        200: New API key
    """
    user = g.authentik_user

    # Generate new key
    old_key_prefix = user.api_key[:8] if user.api_key else None
    user.api_key = secrets.token_urlsafe(32)
    db.session.commit()

    logger.info(f"[ApiKey] User {user.username} regenerated API key (old prefix: {old_key_prefix})")

    return jsonify({
        'success': True,
        'api_key': user.api_key,
        'message': 'API key regenerated. Old key is now invalid.',
        'username': user.username,
    })


@api_key_bp.route('/api-key/verify', methods=['GET'])
@handle_api_errors(logger_name='api_key')
def verify_api_key():
    """
    Verify an API key without full authentication.

    Send the API key via X-API-Key header or api_key query param.

    Returns:
        200: Key is valid with user info
        401: Invalid key
    """
    from flask import request
    from db.models import User

    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

    if not api_key:
        return jsonify({
            'success': False,
            'valid': False,
            'error': 'No API key provided',
        }), 401

    user = User.query.filter_by(api_key=api_key).first()

    if not user:
        return jsonify({
            'success': False,
            'valid': False,
            'error': 'Invalid API key',
        }), 401

    if not user.is_active:
        return jsonify({
            'success': False,
            'valid': False,
            'error': 'Account is disabled',
        }), 403

    return jsonify({
        'success': True,
        'valid': True,
        'username': user.username,
        'user_id': user.id,
    })
