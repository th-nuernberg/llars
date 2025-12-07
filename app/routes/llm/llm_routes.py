"""
LLM Model API Routes

Endpoints for retrieving available LLM models and their configurations.
"""

from flask import jsonify, request
from db.models.llm_model import LLMModel
from db.db import db
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError

from routes.llm import llm_bp


@llm_bp.route('/models', methods=['GET'])
@handle_api_errors(logger_name='llm')
def get_models():
    """
    Get all available LLM models.

    Query params:
        - active_only: bool (default: true) - Only return active models
        - vision_only: bool (default: false) - Only return vision-capable models
        - reasoning_only: bool (default: false) - Only return reasoning-capable models

    Returns:
        List of model configurations
    """
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    vision_only = request.args.get('vision_only', 'false').lower() == 'true'
    reasoning_only = request.args.get('reasoning_only', 'false').lower() == 'true'

    query = LLMModel.query

    if active_only:
        query = query.filter_by(is_active=True)

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


@llm_bp.route('/models/default', methods=['GET'])
@handle_api_errors(logger_name='llm')
def get_default_model():
    """Get the default LLM model."""
    model = LLMModel.get_default_model()

    if not model:
        raise NotFoundError('No default model configured')

    return jsonify({
        'success': True,
        'model': model.to_dict()
    })


@llm_bp.route('/models/<int:model_id>', methods=['GET'])
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
@handle_api_errors(logger_name='llm')
def set_default_model(model_id):
    """Set a model as the default."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    if not model.is_active:
        raise ValidationError('Cannot set inactive model as default')

    # Unset current default
    LLMModel.query.filter_by(is_default=True).update({'is_default': False})

    # Set new default
    model.is_default = True
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{model.display_name} is now the default model',
        'model': model.to_dict()
    })


@llm_bp.route('/models', methods=['POST'])
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

    model = LLMModel(
        model_id=data['model_id'],
        display_name=data['display_name'],
        provider=data['provider'],
        description=data.get('description'),
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
        recommended_for=data.get('recommended_for'),
    )

    # If setting as default, unset current default
    if model.is_default:
        LLMModel.query.filter_by(is_default=True).update({'is_default': False})

    db.session.add(model)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Model created successfully',
        'model': model.to_dict()
    }), 201


@llm_bp.route('/models/<int:model_id>', methods=['PUT'])
@handle_api_errors(logger_name='llm')
def update_model(model_id):
    """Update an existing LLM model configuration."""
    model = LLMModel.query.get(model_id)

    if not model:
        raise NotFoundError(f'Model with ID {model_id} not found')

    data = request.get_json()
    if not data:
        raise ValidationError('No data provided')

    # Update allowed fields
    updatable_fields = [
        'display_name', 'description', 'supports_vision', 'supports_reasoning',
        'supports_function_calling', 'supports_streaming', 'context_window',
        'max_output_tokens', 'input_cost_per_million', 'output_cost_per_million',
        'is_active', 'recommended_for'
    ]

    for field in updatable_fields:
        if field in data:
            setattr(model, field, data[field])

    # Handle is_default separately
    if data.get('is_default') and not model.is_default:
        LLMModel.query.filter_by(is_default=True).update({'is_default': False})
        model.is_default = True

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Model updated successfully',
        'model': model.to_dict()
    })


@llm_bp.route('/models/<int:model_id>', methods=['DELETE'])
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
