"""
User LLM Provider Routes.

Manages user-owned LLM API keys and sharing.
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime

from auth.decorators import authentik_required
from decorators.error_handler import (
    handle_api_errors, ValidationError, NotFoundError
)
from services.user_llm_provider_service import UserLLMProviderService

user_provider_bp = Blueprint('providers', __name__, url_prefix='/providers')


# ============================================================================
# Provider CRUD
# ============================================================================

@user_provider_bp.route('', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def list_providers():
    """List current user's LLM providers."""
    user = g.authentik_user
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    providers = UserLLMProviderService.get_user_providers(
        user_id=user.id,
        include_inactive=include_inactive
    )

    return jsonify({
        'success': True,
        'providers': [p.to_dict(include_shares=True) for p in providers]
    })


@user_provider_bp.route('/available', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def list_available_providers():
    """List all providers available to user (own + shared)."""
    user = g.authentik_user

    # Get user roles from PermissionService
    from services.permission_service import PermissionService
    user_roles_data = PermissionService.get_user_roles(user.username)
    roles = [r['role_name'] for r in user_roles_data] if user_roles_data else []

    providers = UserLLMProviderService.get_available_providers_for_user(
        user_id=user.id,
        username=user.username,
        user_roles=roles
    )

    return jsonify({
        'success': True,
        'providers': providers
    })


@user_provider_bp.route('', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def create_provider():
    """Create a new LLM provider."""
    user = g.authentik_user
    data = request.get_json() or {}

    # Validate required fields
    provider_type = (data.get('provider_type') or '').strip()
    name = (data.get('name') or '').strip()

    if not provider_type:
        raise ValidationError("Provider-Typ ist erforderlich")
    if not name:
        raise ValidationError("Name ist erforderlich")

    valid_types = ['openai', 'anthropic', 'gemini', 'azure', 'ollama', 'litellm', 'custom']
    if provider_type not in valid_types:
        raise ValidationError(f"Ungültiger Provider-Typ. Erlaubt: {', '.join(valid_types)}")

    provider = UserLLMProviderService.create_provider(
        user_id=user.id,
        provider_type=provider_type,
        name=name,
        api_key=data.get('api_key'),
        base_url=data.get('base_url'),
        config=data.get('config'),
        is_default=data.get('is_default', False),
        priority=data.get('priority', 0)
    )

    return jsonify({
        'success': True,
        'provider': provider.to_dict()
    }), 201


@user_provider_bp.route('/<int:provider_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def get_provider(provider_id: int):
    """Get a specific provider."""
    user = g.authentik_user

    provider = UserLLMProviderService.get_provider(provider_id)
    if not provider or provider.user_id != user.id:
        raise NotFoundError("Provider nicht gefunden")

    return jsonify({
        'success': True,
        'provider': provider.to_dict(include_shares=True)
    })


@user_provider_bp.route('/<int:provider_id>', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def update_provider(provider_id: int):
    """Update a provider."""
    user = g.authentik_user
    data = request.get_json() or {}

    provider = UserLLMProviderService.update_provider(
        provider_id=provider_id,
        user_id=user.id,
        name=data.get('name'),
        api_key=data.get('api_key'),
        base_url=data.get('base_url'),
        config=data.get('config'),
        is_active=data.get('is_active'),
        is_default=data.get('is_default'),
        priority=data.get('priority')
    )

    if not provider:
        raise NotFoundError("Provider nicht gefunden")

    return jsonify({
        'success': True,
        'provider': provider.to_dict()
    })


@user_provider_bp.route('/<int:provider_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def delete_provider(provider_id: int):
    """Delete a provider."""
    user = g.authentik_user

    success = UserLLMProviderService.delete_provider(
        provider_id=provider_id,
        user_id=user.id
    )

    if not success:
        raise NotFoundError("Provider nicht gefunden")

    return jsonify({'success': True})


@user_provider_bp.route('/<int:provider_id>/test', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def test_provider(provider_id: int):
    """Test provider connection."""
    user = g.authentik_user

    success, message = UserLLMProviderService.test_provider(
        provider_id=provider_id,
        user_id=user.id
    )

    return jsonify({
        'success': success,
        'message': message
    })


@user_provider_bp.route('/models', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def fetch_provider_models():
    """Fetch available models for a provider (OpenAI + OpenAI-compatible)."""
    user = g.authentik_user
    data = request.get_json() or {}

    provider_id = data.get('provider_id')
    provider_type = (data.get('provider_type') or '').strip().lower()
    api_key = data.get('api_key')
    base_url = data.get('base_url')
    config = data.get('config')

    if provider_id:
        provider = UserLLMProviderService.get_provider(int(provider_id))
        if not provider or provider.user_id != user.id:
            raise NotFoundError("Provider nicht gefunden")
        provider_type = provider.provider_type
        base_url = base_url or provider.base_url
        config = config or provider.config_json
        if not api_key:
            api_key = UserLLMProviderService._decrypt_api_key(provider.api_key_encrypted)

    if not provider_type:
        raise ValidationError("Provider-Typ ist erforderlich")

    models = UserLLMProviderService.fetch_models(
        provider_type=provider_type,
        api_key=api_key,
        base_url=base_url,
        config=config
    )

    return jsonify({
        'success': True,
        'models': models
    })


# ============================================================================
# Provider Sharing
# ============================================================================

@user_provider_bp.route('/<int:provider_id>/shares', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def list_shares(provider_id: int):
    """List shares for a provider."""
    user = g.authentik_user

    shares = UserLLMProviderService.get_provider_shares(
        provider_id=provider_id,
        user_id=user.id
    )

    return jsonify({
        'success': True,
        'shares': [s.to_dict() for s in shares]
    })


@user_provider_bp.route('/<int:provider_id>/shares', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def create_share(provider_id: int):
    """Share a provider with another user or role."""
    user = g.authentik_user
    data = request.get_json() or {}

    share_type = (data.get('share_type') or '').strip()
    target = (data.get('target_identifier') or '').strip()

    if not share_type or not target:
        raise ValidationError("share_type und target_identifier sind erforderlich")

    # Parse expires_at if provided
    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(
                data['expires_at'].replace('Z', '+00:00')
            )
        except ValueError:
            raise ValidationError("Ungültiges Ablaufdatum")

    share = UserLLMProviderService.share_provider(
        provider_id=provider_id,
        user_id=user.id,
        share_type=share_type,
        target_identifier=target,
        usage_limit_tokens=data.get('usage_limit_tokens'),
        expires_at=expires_at
    )

    return jsonify({
        'success': True,
        'share': share.to_dict()
    }), 201


@user_provider_bp.route('/<int:provider_id>/shares/<int:share_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def delete_share(provider_id: int, share_id: int):
    """Remove a provider share."""
    user = g.authentik_user

    success = UserLLMProviderService.unshare_provider(
        share_id=share_id,
        user_id=user.id
    )

    if not success:
        raise NotFoundError("Share nicht gefunden")

    return jsonify({'success': True})


@user_provider_bp.route('/<int:provider_id>/share-all', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def toggle_share_all(provider_id: int):
    """Toggle sharing with all users."""
    user = g.authentik_user
    data = request.get_json() or {}

    share_with_all = data.get('share_with_all', False)

    success = UserLLMProviderService.toggle_share_with_all(
        provider_id=provider_id,
        user_id=user.id,
        share_with_all=share_with_all
    )

    if not success:
        raise NotFoundError("Provider nicht gefunden")

    return jsonify({'success': True, 'share_with_all': share_with_all})


# ============================================================================
# Provider Types Info
# ============================================================================

@user_provider_bp.route('/types', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_providers')
def get_provider_types():
    """Get available provider types with configuration info."""
    types = [
        {
            'id': 'openai',
            'name': 'OpenAI',
            'description': 'GPT-4, GPT-3.5 und andere OpenAI Modelle',
            'requires_api_key': True,
            'supports_base_url': True,
            'default_base_url': 'https://api.openai.com/v1',
            'config_schema': {
                'organization': {'type': 'string', 'label': 'Organization ID (optional)'}
            }
        },
        {
            'id': 'anthropic',
            'name': 'Anthropic',
            'description': 'Claude Modelle',
            'requires_api_key': True,
            'supports_base_url': True,
            'default_base_url': 'https://api.anthropic.com',
            'config_schema': {}
        },
        {
            'id': 'gemini',
            'name': 'Google Gemini',
            'description': 'Gemini Pro und Ultra',
            'requires_api_key': True,
            'supports_base_url': False,
            'config_schema': {}
        },
        {
            'id': 'azure',
            'name': 'Azure OpenAI',
            'description': 'Azure-gehostete OpenAI Modelle',
            'requires_api_key': True,
            'supports_base_url': True,
            'config_schema': {
                'deployment_name': {'type': 'string', 'label': 'Deployment Name', 'required': True},
                'api_version': {'type': 'string', 'label': 'API Version', 'default': '2024-02-15-preview'}
            }
        },
        {
            'id': 'ollama',
            'name': 'Ollama',
            'description': 'Lokale Ollama Installation',
            'requires_api_key': False,
            'supports_base_url': True,
            'default_base_url': 'http://localhost:11434',
            'config_schema': {}
        },
        {
            'id': 'litellm',
            'name': 'LiteLLM',
            'description': 'LiteLLM Proxy für mehrere Provider',
            'requires_api_key': True,
            'supports_base_url': True,
            'config_schema': {}
        },
        {
            'id': 'custom',
            'name': 'Custom (OpenAI-kompatibel)',
            'description': 'Eigener OpenAI-kompatibler Endpunkt',
            'requires_api_key': True,
            'supports_base_url': True,
            'config_schema': {
                'model_list': {'type': 'array', 'label': 'Verfügbare Modelle'}
            }
        }
    ]

    return jsonify({
        'success': True,
        'types': types
    })
