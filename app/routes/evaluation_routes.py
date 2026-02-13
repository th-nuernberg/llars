"""
Evaluation API Routes.

Provides REST endpoints for evaluation metrics, results, and session management.
Includes:
- Agreement metrics calculation
- Evaluation session management (for rating, ranking, comparison, etc.)
- Feature rating endpoints

Separate from LLM-specific evaluation routes.
"""

import logging
from flask import Blueprint, jsonify, request, g

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError

logger = logging.getLogger(__name__)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')


@evaluation_bp.get('/<int:scenario_id>/agreement-metrics')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_agreement_metrics(scenario_id):
    """
    Get inter-rater agreement metrics for a scenario.

    Calculates and returns metrics including:
    - Krippendorff's Alpha
    - Cohen's Kappa (for 2 raters)
    - Fleiss' Kappa (for 3+ raters)
    - Kendall's Tau
    - Spearman's Rho
    - Percent Agreement

    Args:
        scenario_id: Scenario ID to analyze

    Query Parameters:
        include_llm: Include LLM evaluators (default: true)
        include_human: Include human evaluators (default: true)

    Returns:
        JSON with agreement metrics and interpretations
    """
    from flask import request
    from db.models import RatingScenarios
    from services.evaluation.agreement_metrics_service import AgreementMetricsService

    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Parse query parameters
    include_llm = request.args.get('include_llm', 'true').lower() == 'true'
    include_human = request.args.get('include_human', 'true').lower() == 'true'

    # Calculate metrics
    metrics = AgreementMetricsService.calculate_all_metrics(
        scenario_id=scenario_id,
        include_llm=include_llm,
        include_human=include_human,
    )

    # Check for errors
    if 'error' in metrics:
        return jsonify({
            'scenario_id': scenario_id,
            'error': metrics['error'],
            'metrics': {},
            'rater_count': 0,
            'item_count': 0,
        })

    return jsonify(metrics)


# =============================================================================
# Evaluation Session Routes
# =============================================================================


@evaluation_bp.get('/session/<int:scenario_id>')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_session_data(scenario_id):
    """
    Get evaluation session data for a scenario.

    Returns scenario info, configuration, and items to evaluate.
    Items include their evaluation status for the current user.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with scenario, config, and items
    """
    from services.evaluation.session_service import EvaluationSessionService

    user = g.authentik_user
    data = EvaluationSessionService.get_session_data(scenario_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.get('/session/<int:scenario_id>/threads/<int:thread_id>/features')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_thread_features(scenario_id, thread_id):
    """
    Get features for a specific thread in evaluation session.

    Returns messages and features with their evaluation status.

    Args:
        scenario_id: Scenario ID (for access control)
        thread_id: Thread ID

    Returns:
        JSON with messages, features, and feature types
    """
    from services.evaluation.session_service import EvaluationSessionService

    user = g.authentik_user
    data = EvaluationSessionService.get_thread_features(scenario_id, thread_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.post('/session/<int:scenario_id>/features/<int:feature_id>/rate')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def rate_feature(scenario_id, feature_id):
    """
    Rate a feature in an evaluation session.

    Request body:
        rating: Rating value (required)
        edited_content: Optional corrected text
        comment: Optional comment
        thread_id: Thread ID for context

    Args:
        scenario_id: Scenario ID
        feature_id: Feature ID to rate

    Returns:
        JSON with result status and evaluation data
    """
    from services.evaluation.session_service import (
        EvaluationSessionService, emit_evaluation_update
    )
    from services.scenario_stats_service import get_scenario_ids_for_thread
    from flask import current_app

    user = g.authentik_user
    data = request.get_json()

    if not data:
        raise ValidationError('Request body is required')

    rating = data.get('rating')
    if rating is None:
        raise ValidationError('Rating is required')

    thread_id = data.get('thread_id')
    edited_content = data.get('edited_content')
    comment = data.get('comment')

    result = EvaluationSessionService.save_feature_rating(
        scenario_id=scenario_id,
        feature_id=feature_id,
        user_id=user.id,
        rating=rating,
        thread_id=thread_id,
        edited_content=edited_content,
        comment=comment
    )

    if 'error' in result:
        raise ValidationError(result['error'])

    # Emit real-time update
    emit_evaluation_update(scenario_id, feature_id, user.id)

    # Emit scenario stats update
    if thread_id:
        socketio = current_app.extensions.get('socketio')
        if socketio:
            try:
                from socketio_handlers.events_scenarios import emit_scenario_stats_updated
                for sid in get_scenario_ids_for_thread(thread_id):
                    emit_scenario_stats_updated(socketio, sid)
            except Exception:
                pass

    return jsonify(result)


@evaluation_bp.post('/session/<int:scenario_id>/items/<int:item_id>/evaluate')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def submit_evaluation(scenario_id, item_id):
    """
    Submit/mark an item (thread) as evaluated.

    This is called when all features of a thread have been rated,
    or for simple evaluation types that rate the thread directly.

    Request body:
        function_type: Type of evaluation (labeling, comparison, etc.)
        category_id: For labeling - selected category
        is_unsure: For labeling - whether user is unsure
        feedback: Optional feedback text
        choice: For comparison - selected option (A, B, tie)

    Args:
        scenario_id: Scenario ID
        item_id: Item ID (thread_id)

    Returns:
        JSON with result status
    """
    from services.evaluation.session_service import (
        EvaluationSessionService, emit_evaluation_update
    )
    from db.models.scenario import ItemLabelingEvaluation
    from db import db
    from routes.HelperFunctions import user_can_evaluate

    user = g.authentik_user

    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot submit evaluations')

    data = request.get_json() or {}
    function_type = data.get('function_type')

    # Handle labeling evaluations
    if function_type == 'labeling':
        category_id = data.get('category_id')
        is_unsure = data.get('is_unsure', False)
        feedback = data.get('feedback')

        # Find or create labeling evaluation
        evaluation = ItemLabelingEvaluation.query.filter_by(
            user_id=user.id,
            item_id=item_id,
            scenario_id=scenario_id
        ).first()

        if evaluation:
            # Update existing
            evaluation.category_id = category_id
            evaluation.is_unsure = is_unsure
            evaluation.feedback = feedback
        else:
            # Create new
            evaluation = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item_id,
                scenario_id=scenario_id,
                category_id=category_id,
                is_unsure=is_unsure,
                feedback=feedback
            )
            db.session.add(evaluation)

        db.session.commit()

        result = {
            'success': True,
            'evaluation': evaluation.to_dict(),
            'status': 'completed'
        }
    else:
        # Default behavior for other types
        result = EvaluationSessionService.mark_thread_complete(
            scenario_id=scenario_id,
            thread_id=item_id,
            user_id=user.id
        )

    if 'error' in result:
        raise ValidationError(result['error'])

    # Emit real-time update
    emit_evaluation_update(scenario_id, item_id, user.id)

    return jsonify(result)


# =============================================================================
# Dimensional Rating Routes (New Multi-Dimensional Rating System)
# =============================================================================


@evaluation_bp.get('/rating/<int:scenario_id>/config')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_config(scenario_id):
    """
    Get the rating configuration for a scenario.

    Returns the dimension definitions, scale settings, and labels
    for multi-dimensional rating.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with rating configuration including dimensions
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService

    config = DimensionalRatingService.get_scenario_config(scenario_id)

    if 'error' in config:
        raise NotFoundError(config['error'])

    return jsonify({'config': config, 'scenario_id': scenario_id})


@evaluation_bp.get('/rating/<int:scenario_id>/items')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_items(scenario_id):
    """
    Get all items assigned to the current user for rating.

    Returns items with their evaluation status and overall scores.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with list of items and their status
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService

    user = g.authentik_user
    items = DimensionalRatingService.get_items_for_user(scenario_id, user.id)

    return jsonify({
        'scenario_id': scenario_id,
        'items': items,
        'total': len(items)
    })


@evaluation_bp.get('/rating/<int:scenario_id>/items/<int:item_id>')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_item_content(scenario_id, item_id):
    """
    Get item content with messages for dimensional rating.

    Returns the item content, messages, existing rating, and
    the configuration for displaying the rating interface.

    Args:
        scenario_id: Scenario ID
        item_id: Item ID

    Returns:
        JSON with item, messages, content, existing_rating, and config
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService

    user = g.authentik_user
    data = DimensionalRatingService.get_item_with_content(scenario_id, item_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.post('/rating/<int:scenario_id>/items/<int:item_id>/rate')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def submit_dimensional_rating(scenario_id, item_id):
    """
    Submit multi-dimensional rating for an item.

    Request body:
        dimension_ratings: Dict mapping dimension_id to score
                          e.g., {"coherence": 4, "fluency": 5}
        feedback: Optional user feedback text
        auto_complete: Auto-mark as DONE if all dimensions rated (default: true)

    Args:
        scenario_id: Scenario ID
        item_id: Item ID

    Returns:
        JSON with saved rating and status
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService
    from services.scenario_stats_service import get_scenario_ids_for_thread
    from routes.HelperFunctions import user_can_evaluate
    from flask import current_app

    user = g.authentik_user

    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot submit evaluations')

    data = request.get_json()

    if not data:
        raise ValidationError('Request body is required')

    dimension_ratings = data.get('dimension_ratings')
    if not dimension_ratings or not isinstance(dimension_ratings, dict):
        raise ValidationError('dimension_ratings is required and must be an object')

    feedback = data.get('feedback')
    auto_complete = data.get('auto_complete', True)

    result = DimensionalRatingService.save_dimensional_rating(
        scenario_id=scenario_id,
        item_id=item_id,
        user_id=user.id,
        dimension_ratings=dimension_ratings,
        feedback=feedback,
        auto_complete=auto_complete
    )

    if 'error' in result:
        raise ValidationError(result['error'])

    # Emit scenario stats update
    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_scenarios import emit_scenario_stats_updated
            for sid in get_scenario_ids_for_thread(item_id):
                emit_scenario_stats_updated(socketio, sid)
        except Exception:
            pass

    return jsonify(result)


@evaluation_bp.get('/rating/<int:scenario_id>/progress')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_progress(scenario_id):
    """
    Get the current user's progress for a rating scenario.

    Returns completion statistics including total, completed,
    in_progress, and percentage.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with progress statistics
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService

    user = g.authentik_user
    progress = DimensionalRatingService.get_user_progress(scenario_id, user.id)

    return jsonify({
        'scenario_id': scenario_id,
        'progress': progress
    })


@evaluation_bp.get('/rating/<int:scenario_id>/statistics')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_statistics(scenario_id):
    """
    Get statistics for a scenario's dimensional ratings.

    Returns aggregated statistics including total ratings,
    average scores, and dimension-wise averages.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with rating statistics
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService

    stats = DimensionalRatingService.get_scenario_statistics(scenario_id)

    if 'error' in stats:
        raise NotFoundError(stats['error'])

    return jsonify({
        'scenario_id': scenario_id,
        'statistics': stats
    })


# =============================================================================
# LLM Evaluation Routes
# =============================================================================


@evaluation_bp.post('/rating/<int:scenario_id>/items/<int:item_id>/llm-evaluate')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def trigger_llm_evaluation(scenario_id, item_id):
    """
    Trigger LLM evaluation for a specific item.

    Uses the scenario's dimension configuration and scale settings
    to generate prompts and evaluate the item using an LLM.

    Request body:
        model_id: The LLM model ID to use for evaluation (required)
        save_rating: Whether to save the rating (default: false)
        locale: Language for prompts ('de' or 'en', default: 'de')

    Args:
        scenario_id: Scenario ID
        item_id: Item ID to evaluate

    Returns:
        JSON with LLM evaluation results including ratings and reasoning
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService
    from db.models import RatingScenarios

    user = g.authentik_user
    data = request.get_json() or {}

    model_id = data.get('model_id')
    if not model_id:
        raise ValidationError('model_id is required')

    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    save_rating = data.get('save_rating', False)
    locale = data.get('locale', 'de')

    # Determine user ID for saving (use current user if saving)
    llm_user_id = user.id if save_rating else None

    result = DimensionalRatingService.trigger_llm_evaluation(
        scenario_id=scenario_id,
        item_id=item_id,
        model_id=model_id,
        llm_user_id=llm_user_id,
        locale=locale
    )

    if 'error' in result:
        raise ValidationError(result['error'])

    return jsonify(result)


@evaluation_bp.get('/rating/<int:scenario_id>/llm-evaluations')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_llm_evaluations(scenario_id):
    """
    Get all LLM evaluations for a scenario.

    Returns evaluations that were created by LLM evaluators.

    Args:
        scenario_id: Scenario ID

    Returns:
        JSON with list of LLM evaluations
    """
    from services.evaluation.dimensional_rating_service import DimensionalRatingService
    from db.models import RatingScenarios

    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    evaluations = DimensionalRatingService.get_llm_evaluations(scenario_id)

    return jsonify({
        'scenario_id': scenario_id,
        'evaluations': evaluations,
        'count': len(evaluations)
    })


# =============================================================================
# Rating Preset Routes
# =============================================================================


@evaluation_bp.get('/rating/presets')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_presets():
    """
    Get all available rating presets.

    Returns presets organized by category including:
    - Standard presets (Likert scales)
    - LLM-as-Judge presets (multi-dimensional)
    - Mail/Counseling presets (LLARS-specific)

    Query Parameters:
        category: Filter by category ('standard', 'llm-judge', 'mail', 'all')

    Returns:
        JSON with available presets
    """
    from services.evaluation.rating_preset_service import RatingPresetService

    category = request.args.get('category', 'all')

    if category == 'all':
        presets = RatingPresetService.get_all_presets()
    else:
        presets = RatingPresetService.get_presets_by_category(category)

    return jsonify({
        'presets': presets,
        'categories': RatingPresetService.get_categories()
    })


@evaluation_bp.get('/rating/presets/<preset_id>')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_rating_preset(preset_id):
    """
    Get a specific rating preset by ID.

    Args:
        preset_id: Preset ID

    Returns:
        JSON with preset configuration
    """
    from services.evaluation.rating_preset_service import RatingPresetService

    preset = RatingPresetService.get_preset(preset_id)

    if not preset:
        raise NotFoundError(f'Preset {preset_id} not found')

    return jsonify({'preset': preset})


@evaluation_bp.get('/rating/scale-labels/<scale_range>')
@authentik_required
@handle_api_errors(logger_name='evaluation')
def get_scale_labels(scale_range):
    """
    Get default labels for a scale range.

    Args:
        scale_range: Scale range in format 'min-max' (e.g., '1-5', '0-4')

    Query Parameters:
        locale: Language ('de' or 'en', default: 'de')

    Returns:
        JSON with scale labels
    """
    from services.evaluation.rating_prompt_generator import get_scale_labels_for_range

    locale = request.args.get('locale', 'de')

    try:
        parts = scale_range.split('-')
        min_val = int(parts[0])
        max_val = int(parts[1])
    except (ValueError, IndexError):
        raise ValidationError('Invalid scale range format. Expected: min-max (e.g., 1-5)')

    labels = get_scale_labels_for_range(min_val, max_val, locale)

    # Convert to localized format expected by frontend
    labels_formatted = {}
    for value, label in labels.items():
        labels_formatted[str(value)] = {'de': label, 'en': label}

    return jsonify({
        'scale_range': scale_range,
        'min': min_val,
        'max': max_val,
        'labels': labels_formatted
    })
