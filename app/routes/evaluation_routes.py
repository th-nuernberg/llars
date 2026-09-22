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
import json
from flask import Blueprint, jsonify, request, g

from auth.decorators import authentik_required
from auth.access_control import require_scenario_membership, require_item_in_scenario
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ForbiddenError
from decorators.permission_decorator import require_permission
from services.evaluation.labeling_types import (
    LABELING_STATUS_DONE,
    is_labeling_type,
    labeling_row_status,
)

logger = logging.getLogger(__name__)

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/api/evaluation')


@evaluation_bp.get('/<int:scenario_id>/agreement-metrics')
@require_permission('feature:ranking:view')
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

    require_scenario_membership(scenario_id, g.authentik_user)

    # Parse query parameters
    include_llm = request.args.get('include_llm', 'true').lower() == 'true'
    include_human = request.args.get('include_human', 'true').lower() == 'true'
    # Labeling co-pilot filter: 'with' | 'without' (anchoring analysis view)
    copilot_filter = request.args.get('copilot') or None
    if copilot_filter not in (None, 'with', 'without'):
        raise ValidationError("copilot must be 'with' or 'without'")
    # Scenario parts filter: restrict units to one part (IRR per calibration
    # phase); combinable with the copilot filter. Unknown ids error in the
    # service (it knows the configured part ids).
    part_filter = request.args.get('part') or None

    # For large scenarios, return cached alpha from stats cache to avoid
    # blocking the gevent worker with expensive Krippendorff computation.
    # Cached values cover all raters (no filter) — when the caller asks for a
    # filtered view (humans-only or LLMs-only) we have to recompute live, even
    # though that is slower, because the cache cannot answer the question.
    from db.models import ScenarioItems, Feature
    item_count = ScenarioItems.query.filter_by(scenario_id=scenario_id).count()
    # The unit of analysis for ranking IRR is the FEATURE, not the item — a
    # scenario with few items can still carry thousands of features. Gating on
    # item_count alone let large-feature/low-item ranking scenarios slip past the
    # cache and recompute Krippendorff live on the gevent worker (blocking it).
    # Gate on the actual unit count (features under this scenario's items).
    _item_ids = [
        row[0] for row in ScenarioItems.query
        .filter_by(scenario_id=scenario_id)
        .with_entities(ScenarioItems.item_id).all()
    ]
    feature_count = (
        Feature.query.filter(Feature.item_id.in_(_item_ids)).count() if _item_ids else 0
    )
    is_filtered = (
        not (include_llm and include_human)
        or copilot_filter is not None
        or part_filter is not None
    )
    if (item_count > 200 or feature_count > 1000) and not is_filtered:
        from services.scenario_stats_cache_service import get_cached_stats
        cached = get_cached_stats(scenario_id)
        alpha = cached.get('krippendorff_alpha')
        pairwise = cached.get('pairwise_agreement') or {}
        return jsonify({
            'scenario_id': scenario_id,
            'item_count': item_count,
            'metrics': {
                'krippendorff_alpha': {
                    'value': alpha,
                    'interpretation': cached.get('alpha_interpretation', 'N/A'),
                },
            },
            'pairwise_agreement': pairwise,
            'note': 'Detailed metrics unavailable for large scenarios (>200 items). '
                    'Krippendorff Alpha from cached stats.',
        })

    # Calculate metrics
    metrics = AgreementMetricsService.calculate_all_metrics(
        scenario_id=scenario_id,
        include_llm=include_llm,
        include_human=include_human,
        copilot_filter=copilot_filter,
        part_filter=part_filter,
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
@require_permission('feature:ranking:view')
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
    require_scenario_membership(scenario_id, user)
    data = EvaluationSessionService.get_session_data(scenario_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.post('/session/<int:scenario_id>/items/<int:item_id>/spans/split')
@require_permission('feature:ranking:edit')
@handle_api_errors(logger_name='evaluation')
def split_item_span(scenario_id, item_id):
    """Split one span of a conversation-labeling item into two.

    The unitizing is frozen at import time on purpose — a wrong boundary is
    normally reported through a label card rather than re-cut, because
    re-segmenting mid-study would make the units incomparable between raters.
    This endpoint is the sanctioned exception for spans that plainly carry two
    intents, and it is deliberately not surfaced as a primary control.

    Body: ``{"span_id": "...", "offset": <absolute char offset>}``

    The offset is absolute within the MESSAGE (the same coordinate system the
    span's start/end use), not relative to the span — the client already has
    those coordinates, and converting on one side only invites off-by-one bugs.

    Any existing vote on the original span is deleted: a decision about the
    whole span is not a decision about either half, and carrying it over would
    fabricate study data.
    """
    from db import db
    from db.models import EvaluationItem, RatingScenarios
    from db.models.scenario import ItemLabelingEvaluation
    from routes.HelperFunctions import user_can_evaluate
    from services.evaluation.labeling_types import (
        CONVERSATION_LABELING_FUNCTION_TYPE_ID,
    )
    from services.evaluation.span_progress_service import (
        CONVERSATION_LABELING_META_KEY,
        split_span,
    )

    user = g.authentik_user
    require_scenario_membership(scenario_id, user)
    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot modify spans')
    require_item_in_scenario(scenario_id, item_id)

    scenario = RatingScenarios.query.get(scenario_id)
    if scenario is None or scenario.function_type_id != CONVERSATION_LABELING_FUNCTION_TYPE_ID:
        raise ValidationError('Span splitting is only available for conversation labeling')

    data = request.get_json() or {}
    span_id = str(data.get('span_id') or '')
    if not span_id:
        raise ValidationError('span_id is required')
    try:
        offset = int(data.get('offset'))
    except (TypeError, ValueError):
        raise ValidationError('offset must be an integer')

    item = EvaluationItem.query.get(item_id)
    if item is None:
        raise NotFoundError(f'Item {item_id} not found')

    try:
        result = split_span(item, span_id, offset)
    except ValueError as exc:
        raise ValidationError(str(exc))

    # Reassign the whole blob: SQLAlchemy does not track in-place mutation of a
    # JSON column, so editing the nested dict would never be written back.
    meta = dict(item.metadata_json or {})
    block = dict(meta.get(CONVERSATION_LABELING_META_KEY) or {})
    block['spans'] = result['spans']
    meta[CONVERSATION_LABELING_META_KEY] = block
    item.metadata_json = meta

    # Drop votes on the span that no longer exists — for EVERY rater, not just
    # the caller: the unit is gone for all of them.
    removed = ItemLabelingEvaluation.query.filter_by(
        scenario_id=scenario_id, item_id=item_id, span_id=span_id
    ).delete()

    # The measurements attached to that span go with it, for the same reason
    # the vote does: they describe a unit that no longer exists. Leaving them
    # would keep counting a phantom case — inflating the co-pilot denominators
    # (shown/accepted rates) and the per-rater timing statistics.
    from db.models import LabelingCopilotLog
    from db.models.evaluation_item_timing import EvaluationItemTiming
    LabelingCopilotLog.query.filter_by(
        scenario_id=scenario_id, item_id=item_id, span_id=span_id
    ).delete()
    EvaluationItemTiming.query.filter_by(
        scenario_id=scenario_id, item_id=item_id, span_id=span_id
    ).delete()

    db.session.commit()

    logger.info(
        'Span %s of item %s split at %s -> %s (%s votes dropped)',
        span_id, item_id, offset, result['new_ids'], removed,
    )

    return jsonify({
        'success': True,
        'new_span_ids': list(result['new_ids']),
        'votes_removed': removed,
        'spans': result['spans'],
    })



def _message_text_for_spans(item, span_ids):
    """Content of the message the given spans belong to, or None.

    Reading order is message_id ascending, matching how the importer and the
    co-pilot runner index messages — ordering by timestamp would be wrong,
    because the importer stamps "now" when the payload carries none.
    """
    from db.models import Message
    from services.evaluation.span_progress_service import (
        CONVERSATION_LABELING_META_KEY,
    )

    block = ((item.metadata_json or {}).get(CONVERSATION_LABELING_META_KEY) or {})
    wanted = set(str(sid) for sid in span_ids)
    indexes = {
        s.get('message_index')
        for s in (block.get('spans') or [])
        if str(s.get('span_id')) in wanted
    }
    if len(indexes) != 1:
        return None                      # spans span messages; merge_spans rejects
    message_index = indexes.pop()
    if not isinstance(message_index, int):
        return None

    messages = (
        Message.query.filter_by(thread_id=item.item_id)
        .order_by(Message.message_id.asc())
        .all()
    )
    if 0 <= message_index < len(messages):
        return messages[message_index].content or ''
    return None

@evaluation_bp.post('/session/<int:scenario_id>/items/<int:item_id>/spans/merge')
@require_permission('feature:ranking:edit')
@handle_api_errors(logger_name='evaluation')
def merge_item_spans(scenario_id, item_id):
    """Merge two adjacent spans of a conversation-labeling item into one.

    The counterpart to the split endpoint: a rater who cut by mistake, or who
    finds two neighbouring units that are really one speech act, can put them
    back together. Same guarantees as split — the change is recorded in the
    item's own span index, so from then on every rater sees the same units.

    Body: ``{"span_ids": ["...", "..."]}`` — two or more, order does not
    matter, the service sorts them into reading order itself.

    Every existing vote on them is deleted for EVERY rater: decisions about the
    parts are not a decision about the whole, and keeping one of them would
    invent an opinion nobody expressed.
    """
    from db import db
    from db.models import EvaluationItem, RatingScenarios
    from db.models.scenario import ItemLabelingEvaluation
    from routes.HelperFunctions import user_can_evaluate
    from services.evaluation.labeling_types import (
        CONVERSATION_LABELING_FUNCTION_TYPE_ID,
    )
    from services.evaluation.span_progress_service import (
        CONVERSATION_LABELING_META_KEY,
        merge_spans,
    )

    user = g.authentik_user
    require_scenario_membership(scenario_id, user)
    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot modify spans')
    require_item_in_scenario(scenario_id, item_id)

    scenario = RatingScenarios.query.get(scenario_id)
    if scenario is None or scenario.function_type_id != CONVERSATION_LABELING_FUNCTION_TYPE_ID:
        raise ValidationError('Span merging is only available for conversation labeling')

    data = request.get_json() or {}
    span_ids = data.get('span_ids')
    if not isinstance(span_ids, list) or len(span_ids) < 2:
        raise ValidationError('span_ids must be a list of at least two span ids')
    span_ids = [str(sid) for sid in span_ids if sid]

    item = EvaluationItem.query.get(item_id)
    if item is None:
        raise NotFoundError(f'Item {item_id} not found')

    try:
        # The message text lets the service tell a separator (one space between
        # sentence spans — the normal case in a real segmentation) from actual
        # words nobody decided about.
        message_text = _message_text_for_spans(item, span_ids)
        result = merge_spans(item, span_ids, message_text=message_text)
    except ValueError as exc:
        raise ValidationError(str(exc))

    # Reassign the whole blob: SQLAlchemy does not track in-place mutation of a
    # JSON column, so editing the nested dict would never be written back.
    meta = dict(item.metadata_json or {})
    block = dict(meta.get(CONVERSATION_LABELING_META_KEY) or {})
    block['spans'] = result['spans']
    meta[CONVERSATION_LABELING_META_KEY] = block
    item.metadata_json = meta

    # Same cleanup as split, for the same reason: the two units are gone, so the
    # votes and everything measured against them describe something that no
    # longer exists.
    from db.models import LabelingCopilotLog
    from db.models.evaluation_item_timing import EvaluationItemTiming
    removed = 0
    for gone in result['removed_ids']:
        removed += ItemLabelingEvaluation.query.filter_by(
            scenario_id=scenario_id, item_id=item_id, span_id=gone
        ).delete()
        LabelingCopilotLog.query.filter_by(
            scenario_id=scenario_id, item_id=item_id, span_id=gone
        ).delete()
        EvaluationItemTiming.query.filter_by(
            scenario_id=scenario_id, item_id=item_id, span_id=gone
        ).delete()

    db.session.commit()

    logger.info(
        'Spans %s of item %s merged -> %s (%s votes dropped)',
        result['removed_ids'], item_id, result['new_id'], removed,
    )

    return jsonify({
        'success': True,
        'new_span_id': result['new_id'],
        'votes_removed': removed,
        'spans': result['spans'],
    })


@evaluation_bp.get('/session/<int:scenario_id>/threads/<int:thread_id>/features')
@require_permission('feature:ranking:view')
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
    require_scenario_membership(scenario_id, user)
    require_item_in_scenario(scenario_id, thread_id)  # block cross-scenario item IDOR
    data = EvaluationSessionService.get_thread_features(scenario_id, thread_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.post('/session/<int:scenario_id>/features/<int:feature_id>/rate')
@require_permission('feature:ranking:edit')
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
    require_scenario_membership(scenario_id, user)
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

    # Mark stats dirty for background recompute
    if thread_id:
        try:
            from services.scenario_stats_cache_service import mark_dirty
            for sid in get_scenario_ids_for_thread(thread_id):
                mark_dirty(sid)
        except Exception:
            pass

    return jsonify(result)


@evaluation_bp.post('/session/<int:scenario_id>/items/<int:item_id>/evaluate')
@require_permission('feature:ranking:edit')
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
    require_scenario_membership(scenario_id, user)

    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot submit evaluations')

    require_item_in_scenario(scenario_id, item_id)  # block cross-scenario write IDOR

    data = request.get_json() or {}
    function_type = data.get('function_type')

    # Handle labeling evaluations (classic type 7 and conversation type 9)
    if is_labeling_type(function_type):
        # A partial save (question-first labeling) legitimately arrives with
        # category_id null — the row is upserted exactly like a full save, it
        # just does not count as done yet. Normalise '' to None so an "no label
        # chosen yet" placeholder from a client can never masquerade as a
        # decision in labeling_row_status / the export / the IRR.
        category_id = data.get('category_id')
        if isinstance(category_id, str) and not category_id.strip():
            category_id = None
        # NOT NULL in the DB, so coerce: a client sending null must not blow up
        # the insert mid-study.
        is_unsure = bool(data.get('is_unsure', False))
        feedback = data.get('feedback')
        # Conversation labeling addresses ONE SPAN of the item; classic
        # labeling addresses the whole item and sends no span_id. The empty
        # string is the stored representation of "whole item" — see
        # ItemLabelingEvaluation.span_id.
        span_id = str(data.get('span_id') or '')
        if len(span_id) > 64:
            raise ValidationError('span_id must be at most 64 characters')

        # Second choice ("Platz 2") — optional, never the same as the label,
        # and never a label on its own (a second choice without a first is
        # meaningless for the IRR analysis).
        second_choice_id = data.get('second_choice_id')
        second_choice_id = str(second_choice_id).strip() if second_choice_id else None
        if second_choice_id and (len(second_choice_id) > 255 or second_choice_id == category_id
                                 or not category_id):
            second_choice_id = None

        # Answers to the decision questions (question-first labeling). Kept
        # as an opaque dict with a size cap so a client bug can't bloat rows.
        answers_json = data.get('answers_json')
        if not isinstance(answers_json, dict) or not answers_json:
            answers_json = None
        elif len(json.dumps(answers_json)) > 4096:
            raise ValidationError('answers_json must be at most 4096 bytes')

        # Find or create labeling evaluation
        evaluation = ItemLabelingEvaluation.query.filter_by(
            user_id=user.id,
            item_id=item_id,
            scenario_id=scenario_id,
            span_id=span_id
        ).first()

        if evaluation:
            # Update existing
            evaluation.category_id = category_id
            evaluation.is_unsure = is_unsure
            evaluation.feedback = feedback
            evaluation.second_choice_id = second_choice_id
            evaluation.answers_json = answers_json
        else:
            # Create new
            evaluation = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item_id,
                scenario_id=scenario_id,
                span_id=span_id,
                category_id=category_id,
                is_unsure=is_unsure,
                feedback=feedback,
                second_choice_id=second_choice_id,
                answers_json=answers_json,
            )
            db.session.add(evaluation)

        db.session.commit()

        # Three-way status of the row we just wrote. Question-first labeling
        # persists EVERY click, so this save may well be a partial one
        # (answered questions, no label yet) — the interface needs to know
        # which, and so does everything below. Single source of truth:
        # labeling_types.labeling_row_status.
        row_status = labeling_row_status(evaluation)
        row_is_done = row_status == LABELING_STATUS_DONE

        # Co-pilot study logging (no-op unless the scenario has an enabled
        # copilot). Client only contributes timing + helpful flag; shown/
        # suggestions/acceptance are derived server-side. Must NEVER block
        # the labeling save itself.
        #
        # ONLY on a done row: the log is the study record of a labeling
        # decision (was a suggestion shown, was it accepted, how long did the
        # case take). Writing it on the first partial save would snapshot
        # "accepted=None" plus the time to the first question click and — the
        # log being first-write-only for the duration — freeze that as the
        # case duration forever.
        if row_is_done:
            try:
                from services.evaluation.labeling_copilot_service import LabelingCopilotService
                from db.models import RatingScenarios
                scenario = RatingScenarios.query.get(scenario_id)
                if scenario is not None:
                    copilot_data = data.get('copilot') or {}
                    log = LabelingCopilotService.record_label_event(
                        scenario,
                        user.id,
                        item_id,
                        category_id,
                        time_on_item_ms=copilot_data.get('time_on_item_ms'),
                        helpful=copilot_data.get('helpful'),
                        span_id=span_id,
                    )
                    if log is not None:
                        db.session.commit()
            except Exception:
                db.session.rollback()
                import logging
                logging.getLogger('evaluation').warning(
                    'Copilot log upsert failed for scenario %s item %s', scenario_id, item_id,
                    exc_info=True,
                )

        result = {
            'success': True,
            'evaluation': evaluation.to_dict(),
            # 'done' | 'in_progress' | 'pending' for the saved row — NOT the
            # old constant 'completed', which could not express a partial save.
            'status': row_status,
            # Gate for the timing block below; not part of the response.
            '_record_timing': row_is_done,
        }

    elif function_type == 'comparison':
        from db.models.scenario import ItemComparisonEvaluation

        choice = data.get('choice')
        if not choice or choice not in ('A', 'B', 'tie'):
            raise ValidationError('Choice must be A, B, or tie')

        notes = data.get('notes')

        # Find or create comparison evaluation
        evaluation = ItemComparisonEvaluation.query.filter_by(
            user_id=user.id,
            item_id=item_id,
            scenario_id=scenario_id
        ).first()

        if evaluation:
            evaluation.choice = choice
            evaluation.notes = notes
        else:
            evaluation = ItemComparisonEvaluation(
                user_id=user.id,
                item_id=item_id,
                scenario_id=scenario_id,
                choice=choice,
                notes=notes
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

    # Per-case timing. All types routed here (labeling, comparison, …) capture
    # into EvaluationItemTiming so every export carries a uniform time-on-case.
    # Labeling additionally rides in the co-pilot log above; extract_from_payload
    # reads the top-level value OR labeling's nested copilot.time_on_item_ms.
    # Best-effort: a bad/missing timing value must never fail the evaluation.
    #
    # Labeling gate: the timing column means "item shown -> DECISION", and the
    # row is first-write-only. A question-first save fires on the very first
    # question click, so recording it here would permanently stamp the case
    # with the time to that click instead of the time to the label. The
    # labeling branch therefore only asks for a timing write once the row is
    # done; every other type has no partial save and always records.
    record_timing = result.pop('_record_timing', True)
    try:
        from services.evaluation.item_timing_service import ItemTimingService
        ms = ItemTimingService.extract_from_payload(data) if record_timing else None
        if ms is not None:
            ItemTimingService.record_item_timing(
                scenario_id, user.id, item_id, ms, function_type=function_type,
                # Conversation labeling times each SPAN separately; every other
                # type sends no span_id and keeps one row per item.
                span_id=str(data.get('span_id') or ''),
            )
            db.session.commit()
    except Exception:
        db.session.rollback()
        import logging
        logging.getLogger('evaluation').warning(
            'Timing record failed for scenario %s item %s', scenario_id, item_id,
            exc_info=True,
        )

    # Emit real-time update
    emit_evaluation_update(scenario_id, item_id, user.id)

    # Invalidate the cached scenario-stats payload. Without this, the
    # `/evaluation` hub keeps showing stale "0/N" progress because the
    # cache was populated before the user's first comparison/labeling
    # submit. The other submission paths (rating/ranking) already do this
    # via `submit_individual_rating`; we mirror the call here for the
    # comparison + labeling flow.
    try:
        from services.scenario_stats_cache_service import mark_dirty
        mark_dirty(scenario_id)
    except Exception:
        pass

    return jsonify(result)


@evaluation_bp.get('/session/<int:scenario_id>/comparison/preferences')
@require_permission('feature:ranking:view')
@handle_api_errors(logger_name='evaluation')
def get_comparison_preferences(scenario_id):
    """
    Return the current user's pairwise preference patterns for a Comparison
    scenario. Powers the gamification reward popup and the per-user history
    drawer in ComparisonInterface.

    The payload aggregates choices across four orthogonal axes (human vs
    LLM, trained vs base, larger vs smaller, closed vs open) and includes a
    per-item history list for the drawer. See
    `services.evaluation.comparison_preference_stats_service` for the exact
    bucketing rules.
    """
    from db.models.scenario import RatingScenarios
    from services.evaluation.comparison_preference_stats_service import (
        get_user_preference_stats,
    )

    user = g.authentik_user
    require_scenario_membership(scenario_id, user)

    scenario = RatingScenarios.query.get(scenario_id)
    if scenario is None:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Endpoint is restricted to comparison-style scenarios that share the
    # ItemComparisonEvaluation persistence: classic Comparison (=4) and
    # Communication-Comparison (=8). Other types have no A/B provenance,
    # so the payload would be meaningless.
    if scenario.function_type_id not in (4, 8):
        raise ValidationError(
            'Preference stats are only available for comparison scenarios'
        )

    payload = get_user_preference_stats(scenario_id, user.id)
    return jsonify(payload)


# =============================================================================
# Dimensional Rating Routes (New Multi-Dimensional Rating System)
# =============================================================================


@evaluation_bp.get('/rating/<int:scenario_id>/config')
@require_permission('feature:ranking:view')
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

    require_scenario_membership(scenario_id, g.authentik_user)
    config = DimensionalRatingService.get_scenario_config(scenario_id)

    if 'error' in config:
        raise NotFoundError(config['error'])

    return jsonify({'config': config, 'scenario_id': scenario_id})


@evaluation_bp.get('/rating/<int:scenario_id>/items')
@require_permission('feature:ranking:view')
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
    require_scenario_membership(scenario_id, user)
    items = DimensionalRatingService.get_items_for_user(scenario_id, user.id)

    return jsonify({
        'scenario_id': scenario_id,
        'items': items,
        'total': len(items)
    })


@evaluation_bp.get('/rating/<int:scenario_id>/items/<int:item_id>')
@require_permission('feature:ranking:view')
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
    require_scenario_membership(scenario_id, user)
    require_item_in_scenario(scenario_id, item_id)  # block cross-scenario item IDOR
    data = DimensionalRatingService.get_item_with_content(scenario_id, item_id, user.id)

    if 'error' in data:
        raise NotFoundError(data['error'])

    return jsonify(data)


@evaluation_bp.post('/rating/<int:scenario_id>/items/<int:item_id>/rate')
@require_permission('feature:ranking:edit')
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
    require_scenario_membership(scenario_id, user)

    if not user_can_evaluate(user.id, scenario_id):
        raise ForbiddenError('VIEWER role cannot submit evaluations')

    require_item_in_scenario(scenario_id, item_id)  # block cross-scenario write IDOR

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

    # Per-case timing (rating + mail_rating share this endpoint). Best-effort so
    # a bad timing value never fails the rating save.
    try:
        from services.evaluation.item_timing_service import ItemTimingService
        from db import db
        ms = ItemTimingService.extract_from_payload(data)
        if ms is not None:
            ItemTimingService.record_item_timing(
                scenario_id, user.id, item_id, ms,
                function_type=data.get('function_type'),
            )
            db.session.commit()
    except Exception:
        from db import db
        db.session.rollback()
        current_app.logger.warning(
            'Timing record failed for scenario %s item %s', scenario_id, item_id,
            exc_info=True,
        )

    # Mark stats dirty for background recompute
    try:
        from services.scenario_stats_cache_service import mark_dirty
        for sid in get_scenario_ids_for_thread(item_id):
            mark_dirty(sid)
    except Exception:
        pass

    return jsonify(result)


@evaluation_bp.get('/rating/<int:scenario_id>/progress')
@require_permission('feature:ranking:view')
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
    require_scenario_membership(scenario_id, user)
    progress = DimensionalRatingService.get_user_progress(scenario_id, user.id)

    return jsonify({
        'scenario_id': scenario_id,
        'progress': progress
    })


@evaluation_bp.get('/rating/<int:scenario_id>/statistics')
@require_permission('feature:ranking:view')
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

    require_scenario_membership(scenario_id, g.authentik_user)
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
@require_permission('feature:ranking:edit')
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

    require_scenario_membership(scenario_id, user)

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
@require_permission('feature:ranking:view')
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

    require_scenario_membership(scenario_id, g.authentik_user)

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
@require_permission('feature:ranking:view')
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
@require_permission('feature:ranking:view')
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
@require_permission('feature:ranking:view')
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
