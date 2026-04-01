"""
API Key Management Routes.

Endpoints for users to manage their personal API keys.
Supports multiple keys per user with labels.

Endpoints:
- GET    /api/auth/api-keys         - List all user's API keys
- POST   /api/auth/api-keys         - Create new API key
- GET    /api/auth/api-keys/{id}    - Get specific API key
- DELETE /api/auth/api-keys/{id}    - Delete API key
- PUT    /api/auth/api-keys/{id}    - Update API key (name, active status)
- GET    /api/auth/api-keys/verify  - Verify an API key
"""

import logging

from flask import Blueprint, g, jsonify, request

from auth.decorators import authentik_required
from db import db
from db.models import User, UserApiKey
from decorators.error_handler import handle_api_errors, ValidationError, NotFoundError

logger = logging.getLogger(__name__)

api_key_bp = Blueprint('api_key', __name__, url_prefix='/api/auth')


@api_key_bp.route('/api-keys', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def list_api_keys():
    """
    List all API keys for the current user.

    Returns:
        200: List of API keys (without the actual key values)
    """
    user = g.authentik_user
    keys = UserApiKey.query.filter_by(user_id=user.id).order_by(UserApiKey.created_at.desc()).all()

    return jsonify({
        'success': True,
        'api_keys': [key.to_dict() for key in keys],
        'count': len(keys),
    })


@api_key_bp.route('/api-keys', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def create_api_key():
    """
    Create a new API key.

    Request body:
        {
            "name": "My API Key",
            "scopes": "wizard,read"  (optional)
        }

    Returns:
        201: New API key with the full key value (only shown once!)
    """
    user = g.authentik_user
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    if not name:
        raise ValidationError("Name is required")

    if len(name) > 100:
        raise ValidationError("Name must be 100 characters or less")

    # Check key limit (max 10 per user)
    existing_count = UserApiKey.query.filter_by(user_id=user.id).count()
    if existing_count >= 10:
        raise ValidationError("Maximum of 10 API keys per user")

    # Generate new key
    full_key, key_hash, key_prefix = UserApiKey.generate_key()

    api_key = UserApiKey(
        user_id=user.id,
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        scopes=data.get('scopes'),
    )
    db.session.add(api_key)
    db.session.commit()

    logger.info(f"[ApiKey] User {user.username} created API key: {name} ({key_prefix}...)")

    return jsonify({
        'success': True,
        'api_key': api_key.to_dict(include_key=True, full_key=full_key),
        'message': 'API key created. Save this key - it will not be shown again!',
    }), 201


@api_key_bp.route('/api-keys/<int:key_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def get_api_key(key_id: int):
    """
    Get a specific API key by ID.

    Returns:
        200: API key details (without the actual key value)
    """
    user = g.authentik_user

    api_key = UserApiKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not api_key:
        raise NotFoundError(f"API key not found: {key_id}")

    return jsonify({
        'success': True,
        'api_key': api_key.to_dict(),
    })


@api_key_bp.route('/api-keys/<int:key_id>', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def update_api_key(key_id: int):
    """
    Update an API key (name or active status).

    Request body:
        {
            "name": "New Name",
            "is_active": false
        }

    Returns:
        200: Updated API key
    """
    user = g.authentik_user
    data = request.get_json() or {}

    api_key = UserApiKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not api_key:
        raise NotFoundError(f"API key not found: {key_id}")

    # System keys can only be deactivated, not renamed
    if api_key.is_system_key and 'name' in data:
        raise ValidationError("System API keys cannot be renamed")

    if 'name' in data:
        name = data['name'].strip()
        if not name:
            raise ValidationError("Name cannot be empty")
        if len(name) > 100:
            raise ValidationError("Name must be 100 characters or less")
        api_key.name = name

    if 'is_active' in data:
        api_key.is_active = bool(data['is_active'])

    db.session.commit()

    logger.info(f"[ApiKey] User {user.username} updated API key: {api_key.name}")

    return jsonify({
        'success': True,
        'api_key': api_key.to_dict(),
    })


@api_key_bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def delete_api_key(key_id: int):
    """
    Delete an API key.

    System keys (from .env) cannot be deleted.

    Returns:
        200: Deletion confirmed
    """
    user = g.authentik_user

    api_key = UserApiKey.query.filter_by(id=key_id, user_id=user.id).first()
    if not api_key:
        raise NotFoundError(f"API key not found: {key_id}")

    if api_key.is_system_key:
        raise ValidationError("System API keys cannot be deleted")

    key_name = api_key.name
    key_prefix = api_key.key_prefix

    db.session.delete(api_key)
    db.session.commit()

    logger.info(f"[ApiKey] User {user.username} deleted API key: {key_name} ({key_prefix}...)")

    return jsonify({
        'success': True,
        'deleted': True,
        'message': f'API key "{key_name}" deleted',
    })


@api_key_bp.route('/api-keys/verify', methods=['GET'])
@handle_api_errors(logger_name='api_key')
def verify_api_key():
    """
    Verify an API key without full authentication.

    Send the API key via X-API-Key header only.

    Returns:
        200: Key is valid with user info
        401: Invalid key
    """
    api_key_value = request.headers.get('X-API-Key') or ''

    if not api_key_value:
        return jsonify({
            'success': False,
            'valid': False,
            'error': 'No API key provided',
        }), 401

    # Find key in new UserApiKey table
    api_key = UserApiKey.find_by_key(api_key_value)

    if api_key:
        # Update last used
        api_key.update_last_used()
        db.session.commit()

        user = api_key.user
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
            'key_name': api_key.name,
            'scopes': api_key.scopes.split(',') if api_key.scopes else [],
        })

    # Fallback: Check legacy api_key field on User (argon2 hash, then plaintext)
    user = User.find_by_api_key_hash(api_key_value)
    if not user:
        user = User.query.filter_by(api_key=api_key_value).first()

    if user:
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
            'key_name': 'Legacy API Key',
            'scopes': [],
        })

    return jsonify({
        'success': False,
        'valid': False,
        'error': 'Invalid API key',
    }), 401


# ============================================================================
# Legacy endpoints for backwards compatibility
# ============================================================================

@api_key_bp.route('/api-key', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def get_legacy_api_key():
    """
    Get the current user's legacy API key.

    DEPRECATED: Use /api-keys instead.
    Since keys are now hashed, the stored key cannot be retrieved.
    Users must use /api-keys to create new managed keys or /api-key/regenerate
    to get a new legacy key.
    """
    user = g.authentik_user

    # If user still has a plaintext key (not yet migrated), return it
    if user.api_key:
        return jsonify({
            'success': True,
            'api_key': user.api_key,
            'username': user.username,
            'deprecated': True,
            'message': 'This endpoint is deprecated. Use /api/auth/api-keys instead.',
            'usage': {
                'header': 'X-API-Key: <your-api-key>',
            }
        })

    # Key is hashed — cannot be retrieved. Inform user to regenerate or use new system.
    return jsonify({
        'success': True,
        'api_key': None,
        'api_key_exists': user.api_key_hash is not None,
        'username': user.username,
        'deprecated': True,
        'message': 'API key is hashed and cannot be retrieved. '
                   'Use POST /api/auth/api-key/regenerate to get a new key, '
                   'or use /api/auth/api-keys for better key management.',
        'usage': {
            'header': 'X-API-Key: <your-api-key>',
        }
    })


@api_key_bp.route('/api-key/regenerate', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='api_key')
def regenerate_legacy_api_key():
    """
    Regenerate the current user's legacy API key.

    DEPRECATED: Use /api-keys to create new keys instead.
    Returns the new key once — it is stored hashed and cannot be retrieved later.
    """
    import secrets
    user = g.authentik_user

    new_key = secrets.token_urlsafe(32)
    user.set_api_key_hashed(new_key)
    db.session.commit()

    logger.info(f"[ApiKey] User {user.username} regenerated legacy API key (now hashed)")

    return jsonify({
        'success': True,
        'api_key': new_key,
        'message': 'Legacy API key regenerated (stored hashed). '
                   'Save this key — it cannot be retrieved later. '
                   'Consider using /api/auth/api-keys for better key management.',
        'deprecated': True,
        'username': user.username,
    })
