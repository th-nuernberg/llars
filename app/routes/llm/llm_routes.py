"""
LLM Model API Routes

Endpoints for retrieving available LLM models and their configurations.
"""

from flask import jsonify, request
from db.models.llm_model import LLMModel
from db.models.llm_provider import LLMProvider
from db.database import db
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from decorators.permission_decorator import require_permission
from services.llm.llm_access_service import LLMAccessService
from services.llm.llm_provider_service import LLMProviderService
from services.llm.model_sync_service import LLMModelSyncService
from auth.auth_utils import AuthUtils

from routes.llm import llm_bp


@llm_bp.route('/models', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_models():
    """
    Get all available LLM models.

    Query params:
        - active_only: bool (default: true) - Only return active models
        - model_type: str (optional) - Filter by model type (llm/embedding/reranker)
        - vision_only: bool (default: false) - Only return vision-capable models
        - reasoning_only: bool (default: false) - Only return reasoning-capable models

    Returns:
        List of model configurations
    """
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    vision_only = request.args.get('vision_only', 'false').lower() == 'true'
    reasoning_only = request.args.get('reasoning_only', 'false').lower() == 'true'
    model_type = (request.args.get('model_type') or '').strip() or None

    query = LLMModel.query

    if active_only:
        query = query.filter_by(is_active=True)

    if model_type:
        query = query.filter_by(model_type=model_type)

    if vision_only:
        query = query.filter_by(supports_vision=True)

    if reasoning_only:
        query = query.filter_by(supports_reasoning=True)

    models = query.order_by(LLMModel.is_default.desc(), LLMModel.display_name).all()

    return jsonify({
        'success': True,
        'models': [m.to_dict() for m in models],
        'count': len(models)
    })


@llm_bp.route('/models/available', methods=['GET'])
@require_permission('feature:llm:view')
@handle_api_errors(logger_name='llm')
def get_available_models():
    """
    Get available LLM models for the current user.

    Query params:
        - active_only: bool (default: true) - Only return active models
        - model_type: str (optional) - Filter by model type (llm/embedding/reranker)
        - vision_only: bool (default: false) - Only return vision-capable models
        - reasoning_only: bool (default: false) - Only return reasoning-capable models
    """
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    vision_only = request.args.get('vision_only', 'false').lower() == 'true'
    reasoning_only = request.args.get('reasoning_only', 'false').lower() == 'true'
    model_type = (request.args.get('model_type') or '').strip() or None

    username = AuthUtils.extract_username_without_validation()
    models = LLMAccessService.get_accessible_models(
        username,
        active_only=active_only,
        model_type=model_type,
        vision_only=vision_only,
        reasoning_only=reasoning_only,
    )

    return jsonify({
        'success': True,
        'models': [m.to_dict() for m in models],
        'count': len(models)
    })


@llm_bp.route('/models/default', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_default_model():
    """Get the default LLM model."""
    model_type = (request.args.get('model_type') or '').strip() or None
    vision_only = request.args.get('vision_only', 'false').lower() == 'true'
    model = LLMModel.get_default_model(
        model_type=model_type,
        supports_vision=True if vision_only else None
    )

    if not model:
        raise NotFoundError('No default model configured')

    return jsonify({
        'success': True,
        'model': model.to_dict()
    })


@llm_bp.route('/models/<int:model_id>', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_model(model_id):
    """Get a specific LLM model by ID."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    return jsonify({
        'success': True,
        'model': model.to_dict()
    })


@llm_bp.route('/models/by-model-id/<path:model_id>', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_model_by_model_id(model_id):
    """Get a specific LLM model by its model_id string."""
    model = LLMModel.get_by_model_id(model_id)

    if not model:
        raise NotFoundError(f'Model "{model_id}" not found')

    return jsonify({
        'success': True,
        'model': model.to_dict()
    })


@llm_bp.route('/models/<int:model_id>/set-default', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def set_default_model(model_id):
    """Set a model as the default."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    if not model.is_active:
        raise ValidationError('Cannot set inactive model as default')

    # Unset current default
    LLMModel.query.filter_by(
        is_default=True,
        model_type=model.model_type
    ).update({'is_default': False})

    # Set new default
    model.is_default = True
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{model.display_name} is now the default model',
        'model': model.to_dict()
    })


@llm_bp.route('/models', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def create_model():
    """Create a new LLM model configuration."""
    data = request.get_json()

    if not data:
        raise ValidationError('No data provided')

    required_fields = ['model_id', 'display_name', 'provider', 'context_window', 'max_output_tokens']
    for field in required_fields:
        if field not in data:
            raise ValidationError(f'Missing required field: {field}')

    # Check if model_id already exists
    existing = LLMModel.get_by_model_id(data['model_id'])
    if existing:
        raise ConflictError(f'Model with ID "{data["model_id"]}" already exists')

    model_type = data.get('model_type') or LLMModel.MODEL_TYPE_LLM
    if not isinstance(model_type, str) or not model_type.strip():
        raise ValidationError('model_type must be a non-empty string')

    color = LLMModel.normalize_color(data.get('color'))
    if data.get('color') and not color:
        raise ValidationError('color must be a hex string like #RRGGBB')
    if not color:
        color = LLMModel.generate_color(data['model_id'])

    provider_id = data.get('provider_id')
    if provider_id is not None:
        try:
            provider_id = int(provider_id)
        except Exception:
            raise ValidationError('provider_id must be an integer')

    admin_username = AuthUtils.extract_username_without_validation()
    model = LLMModel(
        model_id=data['model_id'],
        display_name=data['display_name'],
        provider=data['provider'],
        description=data.get('description'),
        provider_id=provider_id,
        model_type=model_type.strip(),
        color=color,
        supports_vision=data.get('supports_vision', False),
        supports_reasoning=data.get('supports_reasoning', False),
        supports_function_calling=data.get('supports_function_calling', True),
        supports_streaming=data.get('supports_streaming', True),
        context_window=data['context_window'],
        max_output_tokens=data['max_output_tokens'],
        input_cost_per_million=data.get('input_cost_per_million', 0.0),
        output_cost_per_million=data.get('output_cost_per_million', 0.0),
        is_default=data.get('is_default', False),
        is_active=data.get('is_active', True),
        created_by=admin_username,
        updated_by=admin_username,
    )

    # If setting as default, unset current default
    if model.is_default:
        LLMModel.query.filter_by(
            is_default=True,
            model_type=model.model_type
        ).update({'is_default': False})

    db.session.add(model)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Model created successfully',
        'model': model.to_dict()
    }), 201


@llm_bp.route('/models/<int:model_id>', methods=['PUT'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def update_model(model_id):
    """Update an existing LLM model configuration."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    data = request.get_json()
    if not data:
        raise ValidationError('No data provided')

    old_model_type = model.model_type

    admin_username = AuthUtils.extract_username_without_validation()

    # Update allowed fields
    updatable_fields = [
        'display_name', 'description', 'model_type', 'supports_vision', 'supports_reasoning',
        'supports_function_calling', 'supports_streaming', 'context_window',
        'max_output_tokens', 'input_cost_per_million', 'output_cost_per_million',
        'is_active', 'color'
    ]

    for field in updatable_fields:
        if field in data:
            if field == "model_type":
                if not isinstance(data[field], str) or not data[field].strip():
                    raise ValidationError('model_type must be a non-empty string')
                setattr(model, field, data[field].strip())
            elif field == "color":
                normalized = LLMModel.normalize_color(data[field])
                if data[field] and not normalized:
                    raise ValidationError('color must be a hex string like #RRGGBB')
                model.color = normalized
            else:
                setattr(model, field, data[field])

    if 'provider_id' in data:
        provider_id = data.get('provider_id')
        if provider_id is None:
            model.provider_id = None
        else:
            try:
                model.provider_id = int(provider_id)
            except Exception:
                raise ValidationError('provider_id must be an integer')

    # Handle is_default separately
    if data.get('is_default') and not model.is_default:
        LLMModel.query.filter_by(
            is_default=True,
            model_type=model.model_type
        ).update({'is_default': False})
        model.is_default = True
    elif model.is_default and old_model_type != model.model_type:
        LLMModel.query.filter_by(
            is_default=True,
            model_type=model.model_type
        ).filter(LLMModel.id != model.id).update({'is_default': False})

    if admin_username:
        model.updated_by = admin_username

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Model updated successfully',
        'model': model.to_dict()
    })


@llm_bp.route('/models/<int:model_id>', methods=['DELETE'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def delete_model(model_id):
    """Delete an LLM model configuration."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    if model.is_default:
        raise ValidationError('Cannot delete the default model. Set another model as default first.')

    db.session.delete(model)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Model "{model.display_name}" deleted successfully'
    })


@llm_bp.route('/models/sync', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def sync_models():
    """
    Sync LLM models from the configured LiteLLM/OpenAI-compatible endpoint.

    Uses:
      - LITELLM_BASE_URL
      - LITELLM_API_KEY (optional depending on gateway)
    """
    admin_username = AuthUtils.extract_username_without_validation()
    provider = LLMProviderService.get_default_provider()
    if provider:
        result = LLMModelSyncService.sync_from_provider(provider, synced_by=admin_username)
    else:
        result = LLMModelSyncService.sync_from_litellm(synced_by=admin_username)
    return jsonify(result), 200 if result.get('success') else 400


@llm_bp.route('/providers', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def list_providers():
    include_inactive = request.args.get('include_inactive', 'true').lower() == 'true'
    providers = LLMProviderService.list_providers(include_inactive=include_inactive)
    return jsonify({
        'success': True,
        'providers': [p.to_dict() for p in providers],
        'count': len(providers)
    })


@llm_bp.route('/providers', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def create_provider():
    data = request.get_json() or {}
    provider = LLMProviderService.create_provider(data)

    sync_models_flag = bool(data.get('sync_models'))
    model_ids = data.get('model_ids') or []
    model_metadata = data.get('model_metadata') or {}
    sync_result = None
    if sync_models_flag or model_ids:
        admin_username = AuthUtils.extract_username_without_validation()
        sync_result = LLMProviderService.sync_models(
            provider,
            model_ids=model_ids or None,
            model_metadata=model_metadata or None,
            synced_by=admin_username,
        )

    return jsonify({
        'success': True,
        'provider': provider.to_dict(),
        'sync_result': sync_result,
    }), 201


@llm_bp.route('/providers/test-connection', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def test_provider_connection():
    """
    Test a provider connection without saving it.

    Request body:
        - provider_type: str (required) - Type of provider (openai, anthropic, ollama, etc.)
        - base_url: str (optional) - Base URL for the provider API
        - api_key: str (optional) - API key
        - config: dict (optional) - Additional configuration

    Returns:
        - success: bool
        - message or error: str
    """
    data = request.get_json() or {}
    result = LLMProviderService.test_connection(
        provider_type=data.get('provider_type'),
        base_url=data.get('base_url'),
        api_key=data.get('api_key'),
        config=data.get('config'),
    )
    return jsonify(result), 200 if result.get('success') else 400


@llm_bp.route('/providers/<int:provider_id>', methods=['PUT'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def update_provider(provider_id: int):
    data = request.get_json() or {}
    provider = LLMProviderService.update_provider(provider_id, data)
    model_ids = data.get('model_ids') or []
    if isinstance(model_ids, str):
        model_ids = [m.strip() for m in model_ids.split(',') if m.strip()]
    sync_models_flag = bool(data.get('sync_models'))
    sync_result = None
    if sync_models_flag or model_ids:
        admin_username = AuthUtils.extract_username_without_validation()
        sync_result = LLMProviderService.sync_models(
            provider,
            model_ids=model_ids or None,
            synced_by=admin_username,
        )
    return jsonify({'success': True, 'provider': provider.to_dict(), 'sync_result': sync_result})


@llm_bp.route('/providers/<int:provider_id>', methods=['DELETE'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def delete_provider(provider_id: int):
    provider = LLMProvider.query.get(provider_id)
    if not provider:
        raise NotFoundError('Provider not found')
    provider.is_active = False
    provider.is_default = False
    db.session.commit()
    return jsonify({'success': True})


@llm_bp.route('/providers/<int:provider_id>/test', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def test_provider(provider_id: int):
    provider = LLMProvider.query.get(provider_id)
    if not provider:
        raise NotFoundError('Provider not found')
    result = LLMProviderService.test_provider(provider)
    return jsonify(result), 200 if result.get('success') else 400


@llm_bp.route('/providers/<int:provider_id>/sync-models', methods=['POST'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def sync_provider_models(provider_id: int):
    provider = LLMProvider.query.get(provider_id)
    if not provider:
        raise NotFoundError('Provider not found')
    data = request.get_json() or {}
    model_ids = data.get('model_ids') or []
    admin_username = AuthUtils.extract_username_without_validation()
    result = LLMProviderService.sync_models(
        provider,
        model_ids=model_ids or None,
        synced_by=admin_username,
    )
    return jsonify(result), 200 if result.get('success') else 400


@llm_bp.route('/models/access/overview', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_llm_access_overview():
    """Get an overview of LLM model access assignments (admin only)."""
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

    query = LLMModel.query
    if not include_inactive:
        query = query.filter(LLMModel.is_active == True)

    models = query.order_by(LLMModel.is_default.desc(), LLMModel.display_name).all()
    provider_ids = {m.provider_id for m in models if m.provider_id}
    providers = {}
    if provider_ids:
        rows = LLMProvider.query.filter(LLMProvider.id.in_(provider_ids)).all()
        providers = {p.id: p for p in rows}
    payload = []
    for model in models:
        allowed_usernames = LLMAccessService.get_allowed_usernames(model.id)
        allowed_roles = LLMAccessService.get_allowed_roles(model.id)
        provider = providers.get(model.provider_id) if model.provider_id else None
        provider_label = None
        provider_type = None
        provider_base_url = None
        if provider:
            provider_label = provider.name
            provider_type = provider.provider_type
            provider_base_url = provider.base_url
        payload.append({
            'id': model.id,
            'model_id': model.model_id,
            'display_name': model.display_name,
            'provider': model.provider,
            'provider_id': model.provider_id,
            'provider_label': provider_label,
            'provider_type': provider_type,
            'provider_base_url': provider_base_url,
            'model_type': model.model_type,
            'supports_vision': model.supports_vision,
            'supports_reasoning': model.supports_reasoning,
            'is_active': model.is_active,
            'is_default': model.is_default,
            'created_by': model.created_by,
            'updated_by': model.updated_by,
            'allowed_usernames': allowed_usernames,
            'allowed_roles': allowed_roles,
            'is_restricted': bool(allowed_usernames or allowed_roles),
        })

    return jsonify({'success': True, 'models': payload, 'count': len(payload)})


@llm_bp.route('/models/<int:model_id>/access', methods=['GET'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def get_llm_model_access(model_id: int):
    """Get access allowlist for a specific LLM model (admin only)."""
    model = LLMModel.query.get(model_id)
    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    return jsonify({
        'success': True,
        'model_id': model_id,
        'allowed_usernames': LLMAccessService.get_allowed_usernames(model_id),
        'allowed_roles': LLMAccessService.get_allowed_roles(model_id),
    })


@llm_bp.route('/models/<int:model_id>/access', methods=['PUT'])
@require_permission('admin:system:configure')
@handle_api_errors(logger_name='llm')
def set_llm_model_access(model_id: int):
    """Replace access allowlist for a specific LLM model (admin only)."""
    data = request.get_json() or {}
    usernames = data.get('usernames', data.get('allowed_usernames', [])) or []
    role_names = (
        data.get('role_names')
        or data.get('roles')
        or data.get('allowed_roles')
        or []
    )

    admin_username = AuthUtils.extract_username_without_validation()
    access = LLMAccessService.set_model_access(
        model_id=model_id,
        usernames=usernames,
        role_names=role_names,
        granted_by=admin_username,
    )

    return jsonify({
        'success': True,
        'model_id': model_id,
        'allowed_usernames': access.get('allowed_usernames', []),
        'allowed_roles': access.get('allowed_roles', []),
    })
