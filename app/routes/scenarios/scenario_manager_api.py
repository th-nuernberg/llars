"""
Scenario Manager API
User-facing API for creating, managing and monitoring evaluation scenarios.

This module provides a simplified API for users to:
- Create and manage their own scenarios
- View scenarios they're invited to
- Track progress and statistics
- Start/stop LLM evaluations

SCHEMA GROUND TRUTH:
-------------------
This module uses the unified EvaluationData schemas for evaluation types:
- Backend: app/schemas/evaluation_data_schemas.py (EvaluationType enum)
- Frontend: llars-frontend/src/schemas/evaluationSchemas.js
- Dokumentation: .claude/plans/evaluation-data-schemas.md
"""

import json
import logging
from datetime import datetime
from flask import jsonify, request, g, current_app
from auth.decorators import authentik_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ForbiddenError
)
from decorators.permission_decorator import require_permission, has_role
from db.database import db
from db.tables import (
    RatingScenarios, FeatureFunctionType, ScenarioUsers,
    EmailThread, Message, ScenarioThreads, ScenarioRoles, User,
    ScenarioThreadDistribution, InvitationStatus, MembershipStatus,
    UserFeatureRanking, UserFeatureRating, Feature,
    UserMailHistoryRating, UserConsultingCategorySelection,
    ComparisonSession, ItemDimensionRating
)
from db.models.authenticity import UserAuthenticityVote
from db.models.llm_task_result import LLMTaskResult
from schemas.evaluation_data_schemas import EvaluationType
from services.scenario_stats_service import get_progress_stats, get_authenticity_stats, get_scenario_stats_payload
from services.user_profile_service import serialize_user_brief
from .. import data_blueprint
from .scenario_utils import is_scenario_owner, check_scenario_ownership

logger = logging.getLogger(__name__)


def _normalize_llm_evaluators(config):
    if not isinstance(config, dict):
        return []

    if config.get('enable_llm_evaluation') is False:
        return []

    raw_llm_evaluators = config.get('llm_evaluators')
    if raw_llm_evaluators is None:
        raw_llm_evaluators = config.get('selected_llms')

    if isinstance(raw_llm_evaluators, str):
        raw_llm_evaluators = [raw_llm_evaluators]
    if raw_llm_evaluators is None:
        raw_llm_evaluators = []
    if not isinstance(raw_llm_evaluators, list):
        return []

    llm_evaluators = []
    for model in raw_llm_evaluators:
        if isinstance(model, str):
            mid = model.strip()
        elif isinstance(model, dict):
            mid = str(model.get('model_id') or '').strip()
        else:
            continue
        if mid and mid not in llm_evaluators:
            llm_evaluators.append(mid)
    return llm_evaluators


def _emit_scenario_stats_update(scenario_id: int) -> None:
    """Emit WebSocket event when scenario stats change (e.g., config updated)."""
    socketio = current_app.extensions.get('socketio')
    if not socketio:
        return
    try:
        from socketio_handlers.events_scenarios import emit_scenario_stats_updated
        emit_scenario_stats_updated(socketio, scenario_id)
        logger.debug(f"Emitted scenario stats update for scenario {scenario_id}")
    except Exception as e:
        logger.warning(f"Failed to emit scenario stats update: {e}")


def get_user_scenarios(user, invitation_filter=None):
    """
    Get all scenarios a user has access to.
    Includes owned scenarios and scenarios they're invited to.

    Args:
        user: The authenticated user
        invitation_filter: Optional filter for invitation status:
            - 'owned': Only scenarios created by the user
            - 'accepted': Only accepted invitations
            - 'rejected': Only rejected invitations
            - 'pending': Only pending invitations
            - None: All scenarios (owned + accepted invitations)
    """
    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')

    if is_admin and not invitation_filter:
        # Admins see all scenarios (unless filtering)
        return RatingScenarios.query.all(), {}

    # Get scenarios user created
    owned = RatingScenarios.query.filter_by(created_by=username).all()
    owned_ids = {s.id for s in owned}

    # Build invitation status map for user
    invitation_map = {}  # scenario_id -> invitation_status

    if user_id:
        # Get all scenario_users records for this user (only ACTIVE memberships)
        scenario_users = ScenarioUsers.query.filter(
            ScenarioUsers.user_id == user_id,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        ).all()

        for su in scenario_users:
            invitation_map[su.scenario_id] = {
                'status': su.invitation_status.value if su.invitation_status else 'accepted',
                'role': su.role.value if su.role else 'EVALUATOR',
                'invited_at': su.invited_at.isoformat() if su.invited_at else None,
                'invited_by': su.invited_by
            }

    # Apply filters
    if invitation_filter == 'owned':
        return owned, {}

    if invitation_filter == 'rejected':
        # Only rejected invitations
        rejected_ids = [
            sid for sid, info in invitation_map.items()
            if info['status'] == 'rejected' and sid not in owned_ids
        ]
        scenarios = RatingScenarios.query.filter(
            RatingScenarios.id.in_(rejected_ids)
        ).all() if rejected_ids else []
        return scenarios, invitation_map

    if invitation_filter == 'pending':
        # Only pending invitations
        pending_ids = [
            sid for sid, info in invitation_map.items()
            if info['status'] == 'pending' and sid not in owned_ids
        ]
        scenarios = RatingScenarios.query.filter(
            RatingScenarios.id.in_(pending_ids)
        ).all() if pending_ids else []
        return scenarios, invitation_map

    if invitation_filter == 'accepted':
        # Only accepted invitations (not owned)
        accepted_ids = [
            sid for sid, info in invitation_map.items()
            if info['status'] == 'accepted' and sid not in owned_ids
        ]
        scenarios = RatingScenarios.query.filter(
            RatingScenarios.id.in_(accepted_ids)
        ).all() if accepted_ids else []
        return scenarios, invitation_map

    # Default: owned + accepted invitations (hide rejected)
    accepted_ids = [
        sid for sid, info in invitation_map.items()
        if info['status'] == 'accepted' and sid not in owned_ids
    ]
    invited = RatingScenarios.query.filter(
        RatingScenarios.id.in_(accepted_ids)
    ).all() if accepted_ids else []

    return owned + invited, invitation_map


def format_scenario_for_api(scenario, user, invitation_map=None, include_detailed_stats=False):
    """
    Format a scenario for the API response with computed fields.

    Args:
        scenario: The RatingScenarios object
        user: The authenticated user
        invitation_map: Optional dict of invitation info by scenario_id
        include_detailed_stats: If True, calculate detailed progress stats (slower)
    """
    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', str(user))

    # Determine ownership
    is_owner = (scenario.created_by == username) or has_role(user, 'admin')

    # Get function type name
    func_type = FeatureFunctionType.query.filter_by(
        function_type_id=scenario.function_type_id
    ).first()
    func_type_name = func_type.name if func_type else None

    # Count threads/sessions and users (only count accepted users for user_count display)
    # For comparison scenarios, count ComparisonSession instead of ScenarioThreads
    if func_type_name == 'comparison':
        thread_count = ComparisonSession.query.filter_by(scenario_id=scenario.id).count()
    else:
        thread_count = ScenarioThreads.query.filter_by(scenario_id=scenario.id).count()
    user_count = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario.id,
        ScenarioUsers.invitation_status == InvitationStatus.ACCEPTED,
        ScenarioUsers.membership_status == MembershipStatus.ACTIVE
    ).count()

    # Compute status based on dates if not explicitly set
    # Status can be in config_json or as direct attribute
    config = scenario.config_json or {}
    status = config.get('status') or getattr(scenario, 'status', None)
    if not status:
        current_time = datetime.utcnow()
        if scenario.begin and scenario.end:
            if current_time < scenario.begin:
                status = 'draft'
            elif current_time > scenario.end:
                status = 'completed'
            else:
                status = 'evaluating'
        else:
            status = 'draft'

    # Get owner info
    owner_name = scenario.created_by

    # Compute stats and user progress
    user_progress = {'completed': 0, 'progressing': 0, 'total': thread_count}

    if include_detailed_stats and thread_count > 0:
        # Calculate detailed progress stats from actual evaluations
        try:
            progress_data = get_progress_stats(scenario.id)
            rater_stats = progress_data.get('rater_stats', [])
            evaluator_stats = progress_data.get('evaluator_stats', [])

            # Find current user's progress (check both raters and evaluators)
            all_user_stats = rater_stats + [e for e in evaluator_stats if not e.get('is_llm')]
            user_found = False
            for user_stat in all_user_stats:
                if user_stat.get('username') == username:
                    user_progress = {
                        'completed': user_stat.get('done_threads', 0),
                        'progressing': user_stat.get('progressing_threads', 0),
                        'total': user_stat.get('total_threads', thread_count)
                    }
                    user_found = True
                    break

            # Fallback for owners not in ScenarioUsers: calculate progress directly
            if not user_found and is_owner:
                from db.models import ItemDimensionRating, ProgressionStatus
                from db.models import ScenarioThreads as ST, UserMailHistoryRating
                scenario_thread_ids = [
                    st.thread_id for st in ST.query.filter_by(scenario_id=scenario.id).all()
                ]
                if scenario_thread_ids:
                    # Check ItemDimensionRating for this user's progress
                    user_ratings = ItemDimensionRating.query.filter(
                        ItemDimensionRating.user_id == user_id,
                        ItemDimensionRating.scenario_id == scenario.id,
                        ItemDimensionRating.item_id.in_(scenario_thread_ids)
                    ).all()

                    completed = sum(1 for r in user_ratings if r.status == ProgressionStatus.DONE)
                    progressing = sum(1 for r in user_ratings if r.status == ProgressionStatus.PROGRESSING)

                    # Also check mail_rating if function_type is mail_rating (3)
                    if scenario.function_type_id == 3:
                        mail_ratings = UserMailHistoryRating.query.filter(
                            UserMailHistoryRating.user_id == user_id,
                            UserMailHistoryRating.thread_id.in_(scenario_thread_ids)
                        ).all()
                        completed = sum(1 for r in mail_ratings if r.status == ProgressionStatus.DONE)
                        progressing = sum(1 for r in mail_ratings if r.status == ProgressionStatus.PROGRESSING)

                    user_progress = {
                        'completed': completed,
                        'progressing': progressing,
                        'total': thread_count
                    }

            # Aggregate human evaluator stats
            human_stats = rater_stats + [e for e in evaluator_stats if not e.get('is_llm')]
            human_done = sum(u.get('done_threads', 0) for u in human_stats)
            human_total = sum(u.get('total_threads', 0) for u in human_stats)

            # Aggregate LLM evaluator stats
            llm_stats = [e for e in evaluator_stats if e.get('is_llm')]
            llm_done = sum(u.get('done_threads', 0) for u in llm_stats)
            llm_total = sum(u.get('total_threads', 0) for u in llm_stats)

            # Count users who are fully done
            raters_done = len([u for u in rater_stats if u.get('done_threads', 0) == u.get('total_threads', 0) and u.get('total_threads', 0) > 0])

            # Total evaluations = sum of expected evaluations from all evaluators
            # This ensures progress calculation is correct (completed/total <= 100%)
            total_expected = human_total + llm_total
            stats = {
                'total': total_expected if total_expected > 0 else thread_count,
                'completed': human_done + llm_done,
                'human_total': human_total,
                'human_completed': human_done,
                'llm_total': llm_total,
                'llm_completed': llm_done,
                'raters_done': raters_done,
                'total_raters': len(rater_stats)
            }
        except Exception as e:
            logger.warning(f"Failed to calculate detailed stats for scenario {scenario.id}: {e}")
            stats = {
                'total': thread_count,
                'completed': 0,
                'human_total': thread_count * user_count if user_count else 0,
                'human_completed': 0,
                'llm_total': 0,
                'llm_completed': 0
            }
    else:
        # Basic stats for list view (no expensive queries)
        stats = {
            'total': thread_count,
            'completed': 0,
            'human_total': thread_count * user_count if user_count else 0,
            'human_completed': 0,
            'llm_total': 0,
            'llm_completed': 0
        }

    # Get config - parse JSON string if needed
    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    llm_evaluators = _normalize_llm_evaluators(config)
    if llm_evaluators:
        config['llm_evaluators'] = llm_evaluators

    # Get invitation info for current user
    invitation_info = None
    if invitation_map and scenario.id in invitation_map:
        invitation_info = invitation_map[scenario.id]
    elif user_id and not is_owner:
        # Fetch invitation info if not provided
        su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            user_id=user_id
        ).first()
        if su:
            invitation_info = {
                'status': su.invitation_status.value if su.invitation_status else 'accepted',
                'role': su.role.value if su.role else 'EVALUATOR',
                'invited_at': su.invited_at.isoformat() if su.invited_at else None,
                'invited_by': su.invited_by
            }

    return {
        'id': scenario.id,
        'scenario_name': scenario.scenario_name,
        'description': getattr(scenario, 'description', None),
        'function_type_id': scenario.function_type_id,
        'function_type_name': func_type_name,
        'begin': scenario.begin.isoformat() if scenario.begin else None,
        'end': scenario.end.isoformat() if scenario.end else None,
        'created_at': scenario.begin.isoformat() if scenario.begin else None,  # Using begin as proxy
        'status': status,
        'visibility': getattr(scenario, 'visibility', 'private'),
        'is_owner': is_owner,
        'owner_name': owner_name,
        'thread_count': thread_count,
        'user_count': user_count,
        'llm_evaluator_count': len(llm_evaluators),
        'config_json': config,
        'stats': stats,
        'user_progress': user_progress,  # Current user's evaluation progress
        'invitation': invitation_info  # New: invitation status for current user
    }


# ==================== User-Facing Endpoints ====================

@data_blueprint.route('/scenarios', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def list_user_scenarios():
    """
    Get all scenarios accessible to the current user.

    Query params:
        - filter: 'owned', 'accepted', 'rejected', 'pending', 'all'
                  Default behavior excludes rejected invitations.
        - include_stats: 'true' to include detailed progress stats (slower but shows actual progress)

    Returns:
        - Scenarios created by the user
        - Scenarios the user is invited to (filtered by invitation status)
    """
    user = g.authentik_user
    invitation_filter = request.args.get('filter', None)
    include_stats = request.args.get('include_stats', 'false').lower() == 'true'

    # Special handling for 'all' - get everything including rejected
    if invitation_filter == 'all':
        # Get all scenarios (owned + all invitations)
        scenarios, invitation_map = get_user_scenarios(user, None)
        # Also get rejected ones
        rejected_scenarios, rejected_map = get_user_scenarios(user, 'rejected')
        invitation_map.update(rejected_map)
        # Combine, avoiding duplicates
        scenario_ids = {s.id for s in scenarios}
        for rs in rejected_scenarios:
            if rs.id not in scenario_ids:
                scenarios.append(rs)
    else:
        scenarios, invitation_map = get_user_scenarios(user, invitation_filter)

    formatted = [format_scenario_for_api(s, user, invitation_map, include_detailed_stats=include_stats) for s in scenarios]

    # Sort by status (active first) then by date
    status_order = {'evaluating': 0, 'data_collection': 1, 'draft': 2, 'completed': 3, 'archived': 4}
    formatted.sort(key=lambda x: (status_order.get(x['status'], 99), x['begin'] or ''))

    return jsonify({'scenarios': formatted}), 200


@data_blueprint.route('/scenarios/<int:scenario_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_scenario_detail(scenario_id):
    """
    Get detailed information about a specific scenario.

    Includes:
        - Basic scenario info
        - Thread list
        - User assignments
        - Progress statistics
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check access
    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')
    is_owner = scenario.created_by == username

    # Check if user is invited
    is_member = False
    if user_id:
        is_member = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first() is not None

    if not (is_admin or is_owner or is_member):
        raise ForbiddenError('You do not have access to this scenario')

    # Get detailed stats for detail view
    result = format_scenario_for_api(scenario, user, include_detailed_stats=True)

    # Get detailed user stats from progress service
    try:
        progress_data = get_progress_stats(scenario.id)
        user_stats_map = {}
        for rater in progress_data.get('rater_stats', []):
            user_stats_map[rater['username']] = {
                'done': rater.get('done_threads', 0),
                'total': rater.get('total_threads', 0)
            }
        for evaluator in progress_data.get('evaluator_stats', []):
            if not evaluator.get('is_llm'):
                user_stats_map[evaluator['username']] = {
                    'done': evaluator.get('done_threads', 0),
                    'total': evaluator.get('total_threads', 0)
                }
    except Exception:
        user_stats_map = {}

    # Add users list with real progress (only ACTIVE members)
    scenario_users = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        membership_status=MembershipStatus.ACTIVE
    ).all()
    users_list = []
    for su in scenario_users:
        db_user = User.query.get(su.user_id)
        if db_user:
            user_progress = user_stats_map.get(db_user.username, {})
            avatar = serialize_user_brief(db_user)
            users_list.append({
                'user_id': su.user_id,
                'username': db_user.username,
                'display_name': getattr(db_user, 'display_name', db_user.username),
                'role': su.role.value if hasattr(su.role, 'value') else str(su.role),
                'avatar_seed': avatar.get('avatar_seed'),
                'avatar_url': avatar.get('avatar_url'),
                'completed': user_progress.get('done', 0),
                'total': user_progress.get('total', result['thread_count'])
            })
    result['users'] = users_list

    # Add LLM evaluators from config
    config = scenario.config_json or {}
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}

    llm_evaluators = _normalize_llm_evaluators(config)
    if llm_evaluators:
        config['llm_evaluators'] = llm_evaluators
    result['llm_evaluators'] = llm_evaluators

    if llm_evaluators and (is_admin or is_owner) and result.get('thread_count', 0) > 0:
        try:
            # Get all item IDs for this scenario (threads or comparison sessions)
            function_type = FeatureFunctionType.query.filter_by(
                function_type_id=scenario.function_type_id
            ).first()
            function_name = function_type.name if function_type else None

            if function_name == "comparison":
                all_thread_ids = {session.id for session in ComparisonSession.query.filter_by(scenario_id=scenario.id).all()}
                id_label = "sessions"
            else:
                scenario_threads = ScenarioThreads.query.filter_by(scenario_id=scenario.id).all()
                all_thread_ids = {st.thread_id for st in scenario_threads}
                id_label = "threads"

            if all_thread_ids:
                # For each model, find which threads are missing evaluations
                from services.llm.llm_ai_task_runner import LLMAITaskRunner

                for model_id in llm_evaluators:
                    # Get threads that already have results for this model
                    completed_rows = db.session.query(LLMTaskResult.thread_id).filter(
                        LLMTaskResult.scenario_id == scenario.id,
                        LLMTaskResult.model_id == model_id,
                        LLMTaskResult.payload_json.isnot(None),
                        LLMTaskResult.error.is_(None),
                    ).all()
                    completed_thread_ids = {row[0] for row in completed_rows if row[0]}

                    # Find threads that need evaluation
                    pending_thread_ids = list(all_thread_ids - completed_thread_ids)

                    if pending_thread_ids:
                        logger.info(
                            "[LLM AI Runner] Auto-starting %s for scenario %s: %d/%d %s pending",
                            model_id,
                            scenario.id,
                            len(pending_thread_ids),
                            len(all_thread_ids),
                            id_label,
                        )
                        LLMAITaskRunner.run_for_scenario_async(
                            scenario.id,
                            model_ids=[model_id],
                            thread_ids=pending_thread_ids,
                        )
        except Exception as exc:
            logger.warning(
                "[LLM AI Runner] Auto-start failed for scenario %s: %s",
                scenario.id,
                exc,
            )

    return jsonify(result), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/threads', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_scenario_threads(scenario_id):
    """
    Get all threads associated with a scenario.

    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)
        - search: Search query for subject/sender

    Returns:
        - threads: List of thread objects with message counts
        - total: Total number of threads
        - page: Current page
        - per_page: Items per page
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check access
    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')
    is_owner = scenario.created_by == username

    # Check if user is invited
    is_member = False
    if user_id:
        is_member = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=user_id
        ).first() is not None

    if not (is_admin or is_owner or is_member):
        raise ForbiddenError('You do not have access to this scenario')

    # Query params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')

    # Get scenario threads with their email thread data
    query = (
        db.session.query(ScenarioThreads, EmailThread)
        .join(EmailThread, ScenarioThreads.thread_id == EmailThread.thread_id)
        .filter(ScenarioThreads.scenario_id == scenario_id)
    )

    # Apply search filter
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                EmailThread.subject.ilike(search_term),
                EmailThread.sender.ilike(search_term)
            )
        )

    # Get total count
    total = query.count()

    # Apply pagination and ordering
    query = query.order_by(EmailThread.thread_id.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Get all thread IDs for batch status lookup
    all_results = query.all()
    thread_ids = [et.thread_id for _, et in all_results]

    # Get function type name for type-specific status calculation
    func_type = FeatureFunctionType.query.filter_by(
        function_type_id=scenario.function_type_id
    ).first()
    func_type_name = func_type.name if func_type else None

    # Get evaluation status for current user (batch query for performance)
    # Uses different tables depending on scenario type
    user_status_map = {}

    if user_id and thread_ids:
        config = scenario.config_json or {}

        if func_type_name == 'rating':
            # Rating: use ItemDimensionRating
            ratings = ItemDimensionRating.query.filter(
                ItemDimensionRating.scenario_id == scenario_id,
                ItemDimensionRating.user_id == user_id,
                ItemDimensionRating.item_id.in_(thread_ids)
            ).all()

            required_dimensions = len(config.get('dimensions', []))
            if required_dimensions == 0:
                required_dimensions = 4  # Default fallback

            for r in ratings:
                dim_ratings = r.dimension_ratings or {}
                rated_count = sum(1 for v in dim_ratings.values() if v is not None)
                if rated_count >= required_dimensions:
                    user_status_map[r.item_id] = 'done'
                elif rated_count > 0:
                    user_status_map[r.item_id] = 'in_progress'

        elif func_type_name == 'mail_rating':
            # Mail rating: use UserMailHistoryRating
            mail_ratings = UserMailHistoryRating.query.filter(
                UserMailHistoryRating.user_id == user_id,
                UserMailHistoryRating.thread_id.in_(thread_ids)
            ).all()

            for rating in mail_ratings:
                # Check if rating is complete (has overall rating)
                if rating.status and rating.status.value == 'Done':
                    user_status_map[rating.thread_id] = 'done'
                elif (rating.overall_rating is not None or
                      rating.quality_rating is not None or
                      rating.counsellor_coherence_rating is not None or
                      rating.client_coherence_rating is not None):
                    user_status_map[rating.thread_id] = 'in_progress'

        elif func_type_name == 'ranking':
            # Ranking: check UserFeatureRanking for features in these threads
            features = Feature.query.filter(Feature.thread_id.in_(thread_ids)).all()
            feature_to_thread = {f.feature_id: f.thread_id for f in features}
            feature_ids = list(feature_to_thread.keys())

            if feature_ids:
                rankings = UserFeatureRanking.query.filter(
                    UserFeatureRanking.user_id == user_id,
                    UserFeatureRanking.feature_id.in_(feature_ids)
                ).all()

                # Group rankings by thread
                thread_ranked_features = {}
                for ranking in rankings:
                    tid = feature_to_thread.get(ranking.feature_id)
                    if tid:
                        if tid not in thread_ranked_features:
                            thread_ranked_features[tid] = set()
                        thread_ranked_features[tid].add(ranking.feature_id)

                # Count expected features per thread
                thread_feature_counts = {}
                for f in features:
                    thread_feature_counts[f.thread_id] = thread_feature_counts.get(f.thread_id, 0) + 1

                # Determine status per thread
                for tid in thread_ids:
                    expected = thread_feature_counts.get(tid, 0)
                    ranked = len(thread_ranked_features.get(tid, set()))
                    if expected > 0 and ranked >= expected:
                        user_status_map[tid] = 'done'
                    elif ranked > 0:
                        user_status_map[tid] = 'in_progress'

        elif func_type_name == 'authenticity':
            # Authenticity: check UserAuthenticityVote (uses item_id, not thread_id)
            votes = UserAuthenticityVote.query.filter(
                UserAuthenticityVote.user_id == user_id,
                UserAuthenticityVote.item_id.in_(thread_ids)
            ).all()

            for vote in votes:
                if vote.vote is not None:
                    user_status_map[vote.item_id] = 'done'

        elif func_type_name == 'labeling':
            # Labeling: check for label assignments (using ItemDimensionRating for now)
            ratings = ItemDimensionRating.query.filter(
                ItemDimensionRating.scenario_id == scenario_id,
                ItemDimensionRating.user_id == user_id,
                ItemDimensionRating.item_id.in_(thread_ids)
            ).all()

            for r in ratings:
                # For labeling, having any rating means done
                if r.dimension_ratings:
                    user_status_map[r.item_id] = 'done'

    # Also check for LLM evaluations (independent of user)
    # This ensures Data tab shows items as evaluated when LLMs have processed them
    if thread_ids and func_type_name:
        llm_task_type = func_type_name
        # Map function type to task type if different
        if func_type_name == 'authenticity':
            llm_task_type = 'authenticity'

        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.item_id.in_(thread_ids),
            LLMTaskResult.task_type == llm_task_type
        ).all()

        for result in llm_results:
            # If no human evaluation exists, mark as 'llm_done' to show LLM has evaluated
            if result.item_id not in user_status_map:
                user_status_map[result.item_id] = 'llm_done'

    # Build response
    threads = []
    for scenario_thread, email_thread in all_results:
        # Count messages in thread
        message_count = len(email_thread.messages) if email_thread.messages else 0

        # Get first message sender and date
        first_message = None
        if email_thread.messages:
            first_message = min(email_thread.messages, key=lambda m: m.timestamp if m.timestamp else datetime.max)

        # Get status from precomputed map
        status = user_status_map.get(email_thread.thread_id, 'pending')

        threads.append({
            'thread_id': email_thread.thread_id,
            'scenario_thread_id': scenario_thread.id,
            'subject': email_thread.subject,
            'sender': first_message.sender if first_message else email_thread.sender,
            'message_count': message_count,
            'created_at': first_message.timestamp.isoformat() if first_message and first_message.timestamp else None,
            'chat_id': email_thread.chat_id,
            'institut_id': email_thread.institut_id,
            'status': status
        })

    return jsonify({
        'threads': threads,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/available-threads', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_available_threads(scenario_id):
    """
    Get threads that can be added to a scenario.
    Returns threads matching the scenario's function_type that are NOT already in the scenario.

    Query params:
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)
        - search: Search query for subject/sender

    Returns:
        - threads: List of available threads
        - total: Total number of available threads
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership - only owner can add threads
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')
    is_owner = scenario.created_by == username

    if not (is_admin or is_owner):
        raise ForbiddenError('Only the owner can add threads to this scenario')

    # Query params
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')

    # Get thread IDs already in this scenario
    existing_thread_ids = db.session.query(ScenarioThreads.thread_id).filter(
        ScenarioThreads.scenario_id == scenario_id
    ).subquery()

    # Query threads with matching function_type but NOT in scenario
    query = EmailThread.query.filter(
        EmailThread.function_type_id == scenario.function_type_id,
        ~EmailThread.thread_id.in_(existing_thread_ids)
    )

    if search:
        query = query.filter(
            db.or_(
                EmailThread.subject.ilike(f'%{search}%'),
                EmailThread.sender.ilike(f'%{search}%')
            )
        )

    total = query.count()
    email_threads = query.order_by(EmailThread.thread_id.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    threads = []
    for thread in email_threads:
        # Get message count
        message_count = db.session.query(db.func.count()).filter(
            Message.thread_id == thread.thread_id
        ).scalar() or 0

        threads.append({
            'thread_id': thread.thread_id,
            'subject': thread.subject,
            'sender': thread.sender,
            'message_count': message_count,
            'chat_id': thread.chat_id,
            'institut_id': thread.institut_id
        })

    return jsonify({
        'threads': threads,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/threads', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def scenario_manager_add_threads(scenario_id):
    """
    Add existing threads to a scenario.

    Request body:
        - thread_ids: list of int (required)

    Returns:
        - message: Success message
        - added_count: Number of threads added
        - failed_threads: List of thread IDs that couldn't be added
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    username = getattr(user, 'username', str(user))
    is_admin = has_role(user, 'admin')
    is_owner = scenario.created_by == username

    if not (is_admin or is_owner):
        raise ForbiddenError('Only the owner can add threads to this scenario')

    data = request.get_json()
    thread_ids = data.get('thread_ids', [])

    if not thread_ids or not isinstance(thread_ids, list):
        raise ValidationError('thread_ids must be a non-empty list')

    validated_threads = []
    failed_threads = []

    for thread_id in thread_ids:
        if not isinstance(thread_id, int):
            failed_threads.append(thread_id)
            continue

        # Check thread exists and matches function_type
        thread = EmailThread.query.filter_by(
            thread_id=thread_id,
            function_type_id=scenario.function_type_id
        ).first()

        if not thread:
            failed_threads.append(thread_id)
            continue

        # Check if already in scenario
        existing = ScenarioThreads.query.filter_by(
            scenario_id=scenario_id,
            thread_id=thread_id
        ).first()

        if existing:
            continue  # Skip silently

        validated_threads.append(thread_id)

    # Add validated threads
    for thread_id in validated_threads:
        new_scenario_thread = ScenarioThreads(
            scenario_id=scenario_id,
            thread_id=thread_id
        )
        db.session.add(new_scenario_thread)

    db.session.commit()

    try:
        if validated_threads:
            config = scenario.config_json or {}
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except (json.JSONDecodeError, TypeError):
                    config = {}
            llm_evaluators = _normalize_llm_evaluators(config)
            if llm_evaluators:
                from services.llm.llm_ai_task_runner import LLMAITaskRunner
                LLMAITaskRunner.run_for_scenario_async(
                    scenario.id,
                    model_ids=llm_evaluators,
                    thread_ids=validated_threads,
                )
    except Exception as exc:
        logger.warning("[LLM AI Runner] Add threads trigger failed: %s", exc)

    return jsonify({
        'message': f'Successfully added {len(validated_threads)} threads',
        'added_count': len(validated_threads),
        'failed_threads': failed_threads
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/threads/<int:thread_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_scenario_thread_detail(scenario_id, thread_id):
    """
    Get detailed information about a specific thread in a scenario.

    Includes:
        - Thread metadata
        - All messages
        - Evaluation votes (human and LLM)

    Path params:
        - scenario_id: Scenario ID
        - thread_id: Thread ID

    Returns:
        - thread: Thread object with messages and votes
    """
    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Verify thread is in this scenario
    scenario_thread = ScenarioThreads.query.filter_by(
        scenario_id=scenario_id,
        thread_id=thread_id
    ).first()

    if not scenario_thread:
        raise NotFoundError(f'Thread {thread_id} is not part of scenario {scenario_id}')

    # Get email thread with messages
    email_thread = EmailThread.query.get(thread_id)
    if not email_thread:
        raise NotFoundError(f'Thread {thread_id} not found')

    # Get messages sorted by timestamp
    messages = sorted(email_thread.messages, key=lambda m: m.timestamp if m.timestamp else datetime.max)

    # Get function type to determine which votes to fetch
    func_type = FeatureFunctionType.query.get(scenario.function_type_id)
    func_type_name = func_type.name if func_type else 'unknown'

    # Collect votes based on function type
    votes = []

    if func_type_name == 'authenticity':
        from db.models.authenticity import UserAuthenticityVote
        human_votes = UserAuthenticityVote.query.filter_by(thread_id=thread_id).all()
        for vote in human_votes:
            user = User.query.get(vote.user_id)
            votes.append({
                'type': 'human',
                'user_id': vote.user_id,
                'username': user.username if user else 'Unknown',
                'vote': vote.vote,
                'confidence': vote.confidence,
                'created_at': vote.created_at.isoformat() if vote.created_at else None
            })

        # Get LLM votes
        llm_votes = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id,
            task_type='authenticity'
        ).all()
        for vote in llm_votes:
            payload = vote.payload_json or {}
            votes.append({
                'type': 'llm',
                'model_id': vote.model_id,
                'vote': payload.get('label') or payload.get('vote'),
                'confidence': payload.get('confidence'),
                'reasoning': payload.get('reasoning'),
                'created_at': vote.created_at.isoformat() if vote.created_at else None
            })

    elif func_type_name == 'rating':
        # Get human dimensional ratings from ItemDimensionRating table
        from db.models.scenario import ItemDimensionRating
        from collections import defaultdict
        human_ratings = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id
        ).all()

        # Group by user_id - dimension_ratings is a JSON column with all dimensions
        user_ratings_map = {}
        user_status_map = {}
        user_created_map = {}
        for rating in human_ratings:
            if rating.dimension_ratings:
                user_ratings_map[rating.user_id] = rating.dimension_ratings
            if rating.status:
                user_status_map[rating.user_id] = rating.status.value
            if rating.created_at:
                user_created_map[rating.user_id] = rating.created_at

        for user_id, ratings_dict in user_ratings_map.items():
            user = User.query.get(user_id)
            votes.append({
                'type': 'human',
                'user_id': user_id,
                'username': user.username if user else 'Unknown',
                'ratings': ratings_dict,
                'status': user_status_map.get(user_id),
                'created_at': user_created_map.get(user_id).isoformat() if user_created_map.get(user_id) else None
            })

        # Get LLM ratings
        llm_ratings = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id,
            task_type='rating'
        ).all()
        for rating in llm_ratings:
            payload = rating.payload_json or {}
            # Transform dimensional_ratings array to dict format
            ratings_dict = None
            if payload.get('dimensional_ratings'):
                ratings_dict = {
                    item.get('dimension'): item.get('rating')
                    for item in payload['dimensional_ratings']
                    if item.get('dimension') is not None
                }
            elif payload.get('ratings'):
                ratings_dict = payload['ratings']
            elif payload.get('dimensions'):
                ratings_dict = payload['dimensions']

            votes.append({
                'type': 'llm',
                'model_id': rating.model_id,
                'ratings': ratings_dict,
                'overall_score': payload.get('overall_rating') or payload.get('overall_score') or payload.get('score'),
                'reasoning': payload.get('justification') or payload.get('reasoning'),
                'created_at': rating.created_at.isoformat() if rating.created_at else None
            })

    elif func_type_name == 'mail_rating':
        # First check new ItemDimensionRating table (multi-dimensional ratings)
        from db.models.scenario import ItemDimensionRating
        from collections import defaultdict
        dim_ratings = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id
        ).all()

        if dim_ratings:
            # Group by user_id
            user_ratings_map = defaultdict(dict)
            user_status_map = {}
            user_created_map = {}
            for rating in dim_ratings:
                if rating.dimension_ratings:
                    user_ratings_map[rating.user_id] = rating.dimension_ratings
                if rating.status:
                    user_status_map[rating.user_id] = rating.status.value
                if rating.created_at:
                    user_created_map[rating.user_id] = rating.created_at

            for user_id, ratings_dict in user_ratings_map.items():
                user = User.query.get(user_id)
                votes.append({
                    'type': 'human',
                    'user_id': user_id,
                    'username': user.username if user else 'Unknown',
                    'ratings': ratings_dict,
                    'status': user_status_map.get(user_id),
                    'created_at': user_created_map.get(user_id).isoformat() if user_created_map.get(user_id) else None
                })
        else:
            # Fallback to legacy UserMailHistoryRating table
            mail_ratings = UserMailHistoryRating.query.filter_by(item_id=thread_id).all()
            for rating in mail_ratings:
                user = User.query.get(rating.user_id)
                votes.append({
                    'type': 'human',
                    'user_id': rating.user_id,
                    'username': user.username if user else 'Unknown',
                    'ratings': {
                        'overall_rating': rating.overall_rating,
                        'counsellor_coherence': rating.counsellor_coherence_rating,
                        'client_coherence': rating.client_coherence_rating,
                        'quality': rating.quality_rating
                    },
                    'feedback': rating.feedback,
                    'status': rating.status.value if rating.status else None,
                    'created_at': rating.timestamp.isoformat() if rating.timestamp else None
                })

        llm_ratings = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id,
            task_type='mail_rating'
        ).all()
        for rating in llm_ratings:
            payload = rating.payload_json or {}
            # Handle different payload formats:
            # 1. Simple format: {"rating": 4, "reasoning": "..."}
            # 2. Dimensional format: {"dimensional_ratings": [...], "reasoning": "..."}
            # 3. Dict format: {"ratings": {...}, "reasoning": "..."}
            ratings_dict = None
            overall_rating = None
            if payload.get('dimensional_ratings'):
                ratings_dict = {
                    item.get('dimension'): item.get('rating')
                    for item in payload['dimensional_ratings']
                    if item.get('dimension') is not None
                }
            elif payload.get('ratings'):
                ratings_dict = payload['ratings']
            elif payload.get('rating') is not None:
                # Simple single rating format
                overall_rating = payload.get('rating')

            votes.append({
                'type': 'llm',
                'model_id': rating.model_id,
                'ratings': ratings_dict,
                'overall_rating': overall_rating,
                'reasoning': payload.get('justification') or payload.get('reasoning'),
                'created_at': rating.created_at.isoformat() if rating.created_at else None
            })

    elif func_type_name == 'ranking':
        # Get features for this thread/item
        features = Feature.query.filter_by(item_id=thread_id).all()
        feature_ids = [f.feature_id for f in features]

        if feature_ids:
            # Get human rankings
            from collections import defaultdict
            human_rankings = UserFeatureRanking.query.filter(
                UserFeatureRanking.feature_id.in_(feature_ids)
            ).all()

            # Group rankings by user
            user_rankings_map = defaultdict(list)
            for ranking in human_rankings:
                user_rankings_map[ranking.user_id].append({
                    'feature_id': ranking.feature_id,
                    'bucket': ranking.bucket,
                    'ranking_content': ranking.ranking_content
                })

            for user_id, rankings_list in user_rankings_map.items():
                user = User.query.get(user_id)
                votes.append({
                    'type': 'human',
                    'user_id': user_id,
                    'username': user.username if user else 'Unknown',
                    'rankings': rankings_list,
                    'ranked_count': len(rankings_list),
                    'total_features': len(feature_ids)
                })

            # Get LLM rankings
            llm_rankings = LLMTaskResult.query.filter_by(
                scenario_id=scenario_id,
                item_id=thread_id,
                task_type='ranking'
            ).all()
            for ranking in llm_rankings:
                payload = ranking.payload_json or {}
                # Transform bucket-based format to list format
                # Payload format: {"gut": [id1, id2], "mittel": [id3], ...}
                rankings_list = []
                for bucket_name, feature_ids in payload.items():
                    if bucket_name not in ['reasoning', 'justification'] and isinstance(feature_ids, list):
                        for fid in feature_ids:
                            rankings_list.append({
                                'feature_id': fid,
                                'bucket': bucket_name
                            })
                votes.append({
                    'type': 'llm',
                    'model_id': ranking.model_id,
                    'rankings': rankings_list if rankings_list else None,
                    'ranked_count': len(rankings_list),
                    'total_features': len(feature_ids) if feature_ids else 0,
                    'reasoning': payload.get('reasoning') or payload.get('justification'),
                    'created_at': ranking.created_at.isoformat() if ranking.created_at else None
                })

    elif func_type_name == 'labeling':
        # Get human labelings from ItemDimensionRating table
        from db.models.scenario import ItemDimensionRating
        human_labels = ItemDimensionRating.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id
        ).all()

        for label in human_labels:
            user = User.query.get(label.user_id)
            votes.append({
                'type': 'human',
                'user_id': label.user_id,
                'username': user.username if user else 'Unknown',
                'label': label.dimension_ratings.get('label') if label.dimension_ratings else None,
                'status': label.status.value if label.status else None,
                'created_at': label.created_at.isoformat() if label.created_at else None
            })

        # Get LLM labelings
        llm_labels = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            item_id=thread_id,
            task_type='labeling'
        ).all()
        for label in llm_labels:
            payload = label.payload_json or {}
            votes.append({
                'type': 'llm',
                'model_id': label.model_id,
                'label': payload.get('label'),
                'confidence': payload.get('confidence'),
                'reasoning': payload.get('reasoning'),
                'created_at': label.created_at.isoformat() if label.created_at else None
            })

    return jsonify({
        'thread': {
            'thread_id': email_thread.thread_id,
            'subject': email_thread.subject,
            'sender': email_thread.sender,
            'chat_id': email_thread.chat_id,
            'messages': [{
                'id': m.message_id,
                'sender': m.sender,
                'content': m.content,
                'timestamp': m.timestamp.isoformat() if m.timestamp else None,
                'role': getattr(m, 'role', m.sender)  # Use sender as fallback for role
            } for m in messages],
            'votes': votes
        }
    })


@data_blueprint.route('/scenarios/<int:scenario_id>/threads/<int:thread_id>', methods=['DELETE'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenario_manager')
def remove_thread_from_scenario(scenario_id, thread_id):
    """
    Remove a thread from a scenario.

    This only removes the association between the scenario and thread,
    it does not delete the actual thread or its data.

    Path params:
        - scenario_id: Scenario ID
        - thread_id: Thread ID to remove

    Returns:
        - message: Success message
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))

    # Verify scenario exists
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Verify ownership
    if not is_scenario_owner(scenario, user):
        raise ValidationError('Only scenario owner can remove threads')

    # Find the scenario-thread association
    scenario_thread = ScenarioThreads.query.filter_by(
        scenario_id=scenario_id,
        thread_id=thread_id
    ).first()

    if not scenario_thread:
        raise NotFoundError(f'Thread {thread_id} is not part of scenario {scenario_id}')

    # Remove associated thread distributions (assignments to users)
    ScenarioThreadDistribution.query.filter_by(
        scenario_id=scenario_id,
        thread_id=thread_id
    ).delete()

    # Remove the scenario-thread association
    db.session.delete(scenario_thread)
    db.session.commit()

    logger.info(f"User {username} removed thread {thread_id} from scenario {scenario_id}")

    return jsonify({
        'message': f'Thread {thread_id} removed from scenario successfully'
    }), 200


@data_blueprint.route('/scenarios', methods=['POST'])
@require_permission('data:manage_scenarios')
@handle_api_errors(logger_name='scenario_manager')
def sm_create_scenario():
    """
    Create a new scenario.

    Request body:
        - scenario_name: str (required)
        - function_type_id: int (required)
        - description: str (optional)
        - begin: date string (optional)
        - end: date string (optional)
        - config_json: dict (optional)
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    data = request.get_json()

    if not data:
        raise ValidationError('Request body is required')

    scenario_name = data.get('scenario_name')
    function_type_id = data.get('function_type_id')

    if not scenario_name:
        raise ValidationError('scenario_name is required')
    if not function_type_id:
        raise ValidationError('function_type_id is required')

    # Validate function type
    func_type = FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first()
    if not func_type:
        raise ValidationError(f'Invalid function_type_id: {function_type_id}')

    # Parse dates
    begin = None
    end = None
    if data.get('begin'):
        begin = datetime.fromisoformat(data['begin'].replace('Z', '+00:00'))
    else:
        begin = datetime.utcnow()

    if data.get('end'):
        end = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    else:
        # Default to 30 days from now
        from datetime import timedelta
        end = datetime.utcnow() + timedelta(days=30)

    # Build config
    config = data.get('config_json', {})
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    if not isinstance(config, dict):
        config = {}
    if not config.get('distribution_mode'):
        config['distribution_mode'] = 'all'
    if not config.get('order_mode'):
        config['order_mode'] = 'random'

    # Resolve LLM evaluators (supports legacy selected_llms from older frontends)
    raw_llm_evaluators = data.get('llm_evaluators')
    if raw_llm_evaluators is None:
        raw_llm_evaluators = config.get('llm_evaluators')
    if raw_llm_evaluators is None:
        raw_llm_evaluators = config.get('selected_llms')

    if isinstance(raw_llm_evaluators, str):
        raw_llm_evaluators = [raw_llm_evaluators]
    if raw_llm_evaluators is None:
        raw_llm_evaluators = []
    if not isinstance(raw_llm_evaluators, list):
        raise ValidationError('llm_evaluators must be a list of model IDs')

    llm_evaluators = []
    for model in raw_llm_evaluators:
        if isinstance(model, str):
            mid = model.strip()
        elif isinstance(model, dict):
            mid = str(model.get('model_id') or '').strip()
        else:
            continue
        if mid and mid not in llm_evaluators:
            llm_evaluators.append(mid)

    enable_llm = bool(config.get('enable_llm_evaluation', False))
    if enable_llm and llm_evaluators:
        from services.llm.llm_access_service import LLMAccessService
        unauthorized = [
            model_id
            for model_id in llm_evaluators
            if not LLMAccessService.user_can_access_model(username, model_id)
        ]
        if unauthorized:
            raise ForbiddenError('No access to LLM models: ' + ', '.join(unauthorized))
        config['llm_evaluators'] = llm_evaluators
    else:
        config.pop('llm_evaluators', None)

    # Create scenario
    new_scenario = RatingScenarios(
        scenario_name=scenario_name,
        function_type_id=function_type_id,
        begin=begin,
        end=end,
        created_by=username,
        config_json=config
    )

    # Set optional fields if model supports them
    if hasattr(new_scenario, 'description'):
        new_scenario.description = data.get('description', '')
    if hasattr(new_scenario, 'status'):
        new_scenario.status = 'draft'
    if hasattr(new_scenario, 'visibility'):
        new_scenario.visibility = data.get('visibility', 'private')

    db.session.add(new_scenario)
    db.session.commit()

    logger.info(f"User {username} created scenario {new_scenario.id}: {scenario_name}")

    if enable_llm and config.get('llm_evaluators'):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        LLMAITaskRunner.run_for_scenario_async(
            new_scenario.id,
            model_ids=config.get('llm_evaluators'),
        )

    return jsonify({
        'message': 'Scenario created successfully',
        'scenario': format_scenario_for_api(new_scenario, user)
    }), 201


@data_blueprint.route('/scenarios/<int:scenario_id>', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def update_scenario(scenario_id):
    """
    Update an existing scenario.

    Only the owner or admin can update a scenario.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    # Update allowed fields
    if 'scenario_name' in data:
        scenario.scenario_name = data['scenario_name']
    if 'begin' in data and data['begin']:
        scenario.begin = datetime.fromisoformat(data['begin'].replace('Z', '+00:00'))
    if 'end' in data and data['end']:
        scenario.end = datetime.fromisoformat(data['end'].replace('Z', '+00:00'))
    if 'config_json' in data:
        scenario.config_json = data['config_json']

    # Optional fields
    if hasattr(scenario, 'description') and 'description' in data:
        scenario.description = data['description']
    if hasattr(scenario, 'status') and 'status' in data:
        scenario.status = data['status']
    if hasattr(scenario, 'visibility') and 'visibility' in data:
        scenario.visibility = data['visibility']

    db.session.commit()

    # Emit WebSocket event for live updates (especially for config/LLM evaluator changes)
    _emit_scenario_stats_update(scenario_id)

    logger.info(f"User {username} updated scenario {scenario_id}")

    return jsonify({
        'message': 'Scenario updated successfully',
        'scenario': format_scenario_for_api(scenario, user)
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_delete_scenario(scenario_id):
    """
    Delete a scenario.

    Only the owner or admin can delete a scenario.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    # Delete related records (order matters for FK constraints)
    # First delete comparison sessions (for comparison scenarios)
    ComparisonSession.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioThreadDistribution.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioThreads.query.filter_by(scenario_id=scenario_id).delete()
    ScenarioUsers.query.filter_by(scenario_id=scenario_id).delete()

    db.session.delete(scenario)
    db.session.commit()

    logger.info(f"User {username} deleted scenario {scenario_id}")

    return jsonify({'message': 'Scenario deleted successfully'}), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/stats', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_scenario_stats(scenario_id):
    """
    Get detailed statistics for a scenario.

    Uses the unified stats payload which routes to the appropriate
    stats function based on scenario type (authenticity vs progress).
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    thread_count = ScenarioThreads.query.filter_by(scenario_id=scenario_id).count()
    user_count = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        membership_status=MembershipStatus.ACTIVE
    ).count()

    # Use unified stats payload which handles both authenticity and progress scenarios
    try:
        stats_payload = get_scenario_stats_payload(scenario_id)
        stats_data = stats_payload.get('stats', {})
        function_type = stats_payload.get('function_type')
        kind = stats_payload.get('kind')

        # For authenticity scenarios, data is structured differently
        if kind == 'authenticity':
            user_stats = stats_data.get('user_stats', [])
            # EVALUATOR role can interact (rate/evaluate), VIEWER is read-only
            rater_stats = [u for u in user_stats if u.get('role') == 'Evaluator' and not u.get('is_llm')]
            evaluator_stats = [u for u in user_stats if u.get('role') in ('Viewer', 'Owner') or u.get('is_llm')]

            # Map authenticity fields to standard progress fields
            for stat in rater_stats + evaluator_stats:
                stat['done_threads'] = stat.get('voted_count', 0)
                stat['not_started_threads'] = stat.get('pending_count', 0)

            human_stats = [u for u in user_stats if not u.get('is_llm')]
            llm_stats_list = [u for u in user_stats if u.get('is_llm')]

            human_done = sum(u.get('voted_count', 0) for u in human_stats)
            human_total = sum(u.get('total_threads', 0) for u in human_stats)
            llm_done = sum(u.get('voted_count', 0) for u in llm_stats_list)
            llm_total = sum(u.get('total_threads', 0) for u in llm_stats_list)

            response = {
                'scenario_id': scenario_id,
                'function_type': function_type,
                'kind': kind,
                'total_threads': thread_count,
                'total_evaluators': len(user_stats),
                'human_evaluators': len(human_stats),
                'llm_evaluators': len(llm_stats_list),
                'total_evaluations': human_total + llm_total,
                'completed_evaluations': human_done + llm_done,
                'pending_evaluations': (human_total + llm_total) - (human_done + llm_done),
                'rater_stats': rater_stats,
                'evaluator_stats': evaluator_stats,
                'user_stats': user_stats,  # Include for authenticity
                'agreement_metrics': {
                    'kappa': None,
                    'alpha': stats_data.get('krippendorff_alpha'),
                    'interpretation': stats_data.get('alpha_interpretation'),
                    'fleiss': None,
                    'accuracy': stats_data.get('overall_accuracy')
                },
                'vote_distribution': stats_data.get('vote_distribution'),
                'overall_accuracy': stats_data.get('overall_accuracy'),
                'ground_truth_stats': stats_data.get('ground_truth_stats')
            }
        else:
            # Standard progress scenarios (ranking, rating, mail_rating, etc.)
            rater_stats = stats_data.get('rater_stats', [])
            evaluator_stats = stats_data.get('evaluator_stats', [])

            human_stats = rater_stats + [e for e in evaluator_stats if not e.get('is_llm')]
            llm_stats_list = [e for e in evaluator_stats if e.get('is_llm')]

            human_done = sum(u.get('done_threads', 0) for u in human_stats)
            human_total = sum(u.get('total_threads', 0) for u in human_stats)
            llm_done = sum(u.get('done_threads', 0) for u in llm_stats_list)
            llm_total = sum(u.get('total_threads', 0) for u in llm_stats_list)

            response = {
                'scenario_id': scenario_id,
                'function_type': function_type,
                'kind': kind,
                'total_threads': thread_count,
                'total_evaluators': user_count + len(llm_stats_list),
                'human_evaluators': len(human_stats),
                'llm_evaluators': len(llm_stats_list),
                'total_evaluations': human_total + llm_total,
                'completed_evaluations': human_done + llm_done,
                'pending_evaluations': (human_total + llm_total) - (human_done + llm_done),
                'rater_stats': rater_stats,
                'evaluator_stats': evaluator_stats,
                'rating_distribution': stats_data.get('rating_distribution', []),
                'rating_alpha': stats_data.get('rating_alpha'),  # Krippendorff's Alpha split by evaluator type
                'dimension_averages': stats_data.get('dimension_averages'),
                'pairwise_agreement': stats_data.get('pairwise_agreement'),
                # Ranking-specific stats
                'bucket_distribution': stats_data.get('bucket_distribution'),
                'ranking_agreement': stats_data.get('ranking_agreement'),
                'agreement_metrics': {
                    'kappa': None,
                    'alpha': stats_data.get('krippendorff_alpha'),
                    'interpretation': stats_data.get('alpha_interpretation'),
                    'fleiss': None
                }
            }
    except Exception as e:
        logger.warning(f"Failed to get stats for scenario {scenario_id}: {e}")
        response = {
            'scenario_id': scenario_id,
            'total_threads': thread_count,
            'total_evaluators': user_count,
            'human_evaluators': user_count,
            'llm_evaluators': 0,
            'total_evaluations': 0,
            'completed_evaluations': 0,
            'pending_evaluations': 0,
            'agreement_metrics': {
                'kappa': None,
                'alpha': None,
                'fleiss': None
            }
        }

    return jsonify(response), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/invite', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_invite_users(scenario_id):
    """
    Invite users to a scenario.

    Request body:
        - user_ids: list of user IDs
        - role: EVALUATOR (can interact) or VIEWER (read-only) (default: EVALUATOR)

    Invitations are auto-accepted by default. Users can later reject them.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    data = request.get_json()
    user_ids = data.get('user_ids', [])
    role_str = data.get('role', 'EVALUATOR').lower()

    # Map role string to enum
    if role_str in ('evaluator', 'rater'):  # Accept 'rater' for backwards compatibility
        role_enum = ScenarioRoles.EVALUATOR
    elif role_str == 'viewer':
        role_enum = ScenarioRoles.VIEWER
    else:
        raise ValidationError(f'Invalid role: {role_str}. Must be EVALUATOR or VIEWER.')

    if not user_ids:
        raise ValidationError('user_ids is required')

    added = 0
    reinvited = 0
    restored = 0
    for uid in user_ids:
        # Check if already added (including archived users)
        existing = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=uid
        ).first()

        if not existing:
            su = ScenarioUsers(
                scenario_id=scenario_id,
                user_id=uid,
                role=role_enum,
                invitation_status=InvitationStatus.ACCEPTED,  # Auto-accept new invitations
                invited_at=datetime.utcnow(),
                invited_by=username,
                membership_status=MembershipStatus.ACTIVE
            )
            db.session.add(su)
            added += 1
        elif existing.membership_status == MembershipStatus.ARCHIVED:
            # Restore archived user - their evaluations are preserved
            # Role is set to the new requested role (EVALUATOR can continue, VIEWER is read-only)
            existing.membership_status = MembershipStatus.ACTIVE
            existing.role = role_enum
            existing.invitation_status = InvitationStatus.ACCEPTED
            existing.invited_at = datetime.utcnow()
            existing.invited_by = username
            existing.archived_at = None
            existing.archived_by = None
            restored += 1
        elif existing.invitation_status == InvitationStatus.REJECTED:
            # Re-invite a rejected user
            existing.invitation_status = InvitationStatus.ACCEPTED
            existing.invited_at = datetime.utcnow()
            existing.invited_by = username
            existing.responded_at = None
            reinvited += 1

    db.session.commit()

    logger.info(f"User {username} invited {added} users (reinvited {reinvited}, restored {restored}) to scenario {scenario_id}")

    msg_parts = []
    if added:
        msg_parts.append(f'Added {added} users')
    if reinvited:
        msg_parts.append(f'reinvited {reinvited}')
    if restored:
        msg_parts.append(f'restored {restored}')

    return jsonify({
        'message': ', '.join(msg_parts) if msg_parts else 'No changes made',
        'added': added,
        'reinvited': reinvited,
        'restored': restored
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/users/<int:user_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_remove_user(scenario_id, user_id):
    """
    Archive a user from a scenario (soft-delete).

    The user is hidden from the frontend but their evaluations are preserved.
    If they are re-invited as EVALUATOR, their progress will be restored.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    su = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        user_id=user_id
    ).first()

    if not su:
        raise NotFoundError('User not found in scenario')

    # Cannot archive the owner
    if su.role == ScenarioRoles.OWNER:
        raise ValidationError('Cannot remove the scenario owner')

    # Archive instead of delete - preserves evaluations for potential restoration
    su.membership_status = MembershipStatus.ARCHIVED
    su.archived_at = datetime.utcnow()
    su.archived_by = username
    db.session.commit()

    logger.info(f"User {username} archived user {user_id} from scenario {scenario_id}")

    return jsonify({'message': 'User removed from scenario'}), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/users/<int:user_id>/role', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_update_user_role(scenario_id, user_id):
    """
    Update a user's role in a scenario.

    Request body:
        - role: EVALUATOR (can interact) or VIEWER (read-only)

    Cannot change the OWNER role.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not
    target_user = User.query.get(user_id)
    is_target_owner = bool(
        target_user
        and scenario.created_by
        and target_user.username == scenario.created_by
    )

    su = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        user_id=user_id
    ).first()

    if not su:
        # Owner fallback: older/generated scenarios can miss owner membership rows.
        # Create a baseline VIEWER row so the owner can self-switch to EVALUATOR.
        if not is_target_owner:
            raise NotFoundError('User not found in scenario')

        su = ScenarioUsers(
            scenario_id=scenario_id,
            user_id=user_id,
            role=ScenarioRoles.VIEWER,
            invitation_status=InvitationStatus.ACCEPTED,
            membership_status=MembershipStatus.ACTIVE,
            invited_by=scenario.created_by
        )
        db.session.add(su)
        db.session.flush()

    # Legacy safety: OWNER rows can only be changed for the actual scenario owner.
    if su.role == ScenarioRoles.OWNER and not is_target_owner:
        raise ValidationError('Cannot change the role of the scenario owner')

    data = request.get_json()
    role_str = data.get('role', '').lower()

    # Map role string to enum
    if role_str in ('evaluator', 'rater'):  # Accept 'rater' for backwards compatibility
        role_enum = ScenarioRoles.EVALUATOR
    elif role_str == 'viewer':
        role_enum = ScenarioRoles.VIEWER
    else:
        raise ValidationError(f'Invalid role: {role_str}. Must be EVALUATOR or VIEWER.')

    old_role = su.role.value
    su.role = role_enum

    # Role changes should always reactivate membership for active collaboration.
    su.membership_status = MembershipStatus.ACTIVE
    su.archived_at = None
    su.archived_by = None
    su.invitation_status = InvitationStatus.ACCEPTED
    su.responded_at = None

    db.session.commit()

    logger.info(f"User {username} changed role of user {user_id} from {old_role} to {role_enum.value} in scenario {scenario_id}")

    return jsonify({
        'message': 'Role updated successfully',
        'user_id': user_id,
        'old_role': old_role,
        'new_role': role_enum.value
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/available-users', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_get_available_users(scenario_id):
    """
    Get list of users that can be invited to a scenario.
    """
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Get users already in scenario
    existing_ids = {su.user_id for su in ScenarioUsers.query.filter_by(scenario_id=scenario_id).all()}

    # Get all users not in scenario
    all_users = User.query.filter(~User.id.in_(existing_ids)).all()

    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'display_name': getattr(u, 'display_name', u.username)
        } for u in all_users]
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/export', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def export_scenario_results(scenario_id):
    """
    Export scenario results in various formats.

    Query params:
        - format: json, csv (default: json)

    Returns structured data based on function_type:
        - ranking (1): Feature rankings by user
        - rating (2): Feature ratings by user
        - authenticity (4): Authenticity votes by user
        - comparison (5): Pairwise comparisons
        - labeling (6): Multi-class classification
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    export_format = request.args.get('format', 'json')

    # Get function type
    func_type = FeatureFunctionType.query.filter_by(
        function_type_id=scenario.function_type_id
    ).first()
    func_type_name = func_type.name if func_type else 'unknown'

    # Get scenario threads
    scenario_thread_ids = [
        st.thread_id for st in ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    ]

    # Get scenario users
    scenario_user_ids = [
        su.user_id for su in ScenarioUsers.query.filter_by(scenario_id=scenario_id).all()
    ]

    # Get user info map
    users = User.query.filter(User.id.in_(scenario_user_ids)).all()
    user_map = {u.id: {'username': u.username, 'display_name': getattr(u, 'display_name', u.username)} for u in users}

    # Get thread info map
    threads = EmailThread.query.filter(EmailThread.thread_id.in_(scenario_thread_ids)).all()
    thread_map = {t.thread_id: {'subject': t.subject, 'chat_id': t.chat_id} for t in threads}

    results = []

    # Export based on function type
    if func_type_name == 'ranking':
        # Export feature rankings (human evaluators)
        # Get features for these threads
        features = Feature.query.filter(Feature.thread_id.in_(scenario_thread_ids)).all()
        feature_ids = [f.feature_id for f in features]
        feature_map = {f.feature_id: f for f in features}

        rankings = UserFeatureRanking.query.filter(
            UserFeatureRanking.user_id.in_(scenario_user_ids),
            UserFeatureRanking.feature_id.in_(feature_ids)
        ).all()

        for ranking in rankings:
            user_info = user_map.get(ranking.user_id, {})
            feature = feature_map.get(ranking.feature_id)
            thread_info = thread_map.get(feature.thread_id, {}) if feature else {}
            results.append({
                'type': 'ranking',
                'user_id': ranking.user_id,
                'username': user_info.get('username'),
                'item_id': feature.thread_id if feature else None,
                'item_subject': thread_info.get('subject'),
                'feature_id': ranking.feature_id,
                'feature_content': feature.content if feature else None,
                'ranking_value': ranking.ranking_content,
                'bucket': ranking.bucket
            })

        # Also include LLM rankings from llm_task_results
        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.task_type == 'ranking',
            LLMTaskResult.thread_id.in_(scenario_thread_ids)
        ).all()

        for result in llm_results:
            thread_info = thread_map.get(result.thread_id, {})
            payload = result.payload_json or {}
            results.append({
                'type': 'ranking_llm',
                'model_id': result.model_id,
                'item_id': result.thread_id,
                'item_subject': thread_info.get('subject'),
                'gut': payload.get('gut', []),
                'mittel': payload.get('mittel', []),
                'schlecht': payload.get('schlecht', []),
                'neutral': payload.get('neutral', []),
                'error': result.error,
                'timestamp': result.created_at.isoformat() if result.created_at else None
            })

    elif func_type_name == 'rating':
        # Export dimensional ratings (new system - ItemDimensionRating)
        dimensional_ratings = ItemDimensionRating.query.filter(
            ItemDimensionRating.scenario_id == scenario_id,
            ItemDimensionRating.item_id.in_(scenario_thread_ids)
        ).all()

        for rating in dimensional_ratings:
            user_info = user_map.get(rating.user_id, {})
            thread_info = thread_map.get(rating.item_id, {})
            results.append({
                'type': 'dimensional_rating',
                'user_id': rating.user_id,
                'username': user_info.get('username'),
                'item_id': rating.item_id,
                'item_subject': thread_info.get('subject'),
                'dimension_ratings': rating.dimension_ratings,
                'overall_score': rating.overall_score,
                'feedback': rating.feedback,
                'status': rating.status.value if rating.status else None,
                'timestamp': rating.created_at.isoformat() if rating.created_at else None
            })

        # Also include LLM evaluations from llm_task_results
        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.task_type == 'rating',
            LLMTaskResult.thread_id.in_(scenario_thread_ids)
        ).all()

        for result in llm_results:
            thread_info = thread_map.get(result.thread_id, {})
            payload = result.payload_json or {}
            # Handle both dimensional and simple rating formats
            if payload.get('type') == 'dimensional' and 'dimensional_ratings' in payload:
                dim_ratings = {dr.get('dimension'): dr.get('rating') for dr in payload.get('dimensional_ratings', [])}
                overall = payload.get('overall_rating')
            else:
                dim_ratings = payload
                overall = payload.get('overall_rating') or payload.get('rating')
            results.append({
                'type': 'rating_llm',
                'model_id': result.model_id,
                'item_id': result.thread_id,
                'item_subject': thread_info.get('subject'),
                'dimension_ratings': dim_ratings,
                'overall_rating': overall,
                'reasoning': payload.get('reasoning'),
                'error': result.error,
                'timestamp': result.created_at.isoformat() if result.created_at else None
            })

        # Fallback: also check legacy UserFeatureRating if no dimensional ratings found
        if not dimensional_ratings and not llm_results:
            features = Feature.query.filter(Feature.thread_id.in_(scenario_thread_ids)).all()
            feature_ids = [f.feature_id for f in features]
            feature_map = {f.feature_id: f for f in features}

            old_ratings = UserFeatureRating.query.filter(
                UserFeatureRating.user_id.in_(scenario_user_ids),
                UserFeatureRating.feature_id.in_(feature_ids)
            ).all()

            for rating in old_ratings:
                user_info = user_map.get(rating.user_id, {})
                feature = feature_map.get(rating.feature_id)
                thread_info = thread_map.get(feature.thread_id, {}) if feature else {}
                results.append({
                    'type': 'rating_legacy',
                    'user_id': rating.user_id,
                    'username': user_info.get('username'),
                    'item_id': feature.thread_id if feature else None,
                    'item_subject': thread_info.get('subject'),
                    'feature_id': rating.feature_id,
                    'feature_content': feature.content if feature else None,
                    'rating_value': rating.rating_content,
                    'edited_feature': rating.edited_feature
                })

    elif func_type_name == 'authenticity':
        # Export authenticity votes
        votes = UserAuthenticityVote.query.filter(
            UserAuthenticityVote.user_id.in_(scenario_user_ids),
            UserAuthenticityVote.thread_id.in_(scenario_thread_ids)
        ).all()

        for vote in votes:
            user_info = user_map.get(vote.user_id, {})
            thread_info = thread_map.get(vote.thread_id, {})
            results.append({
                'type': 'authenticity',
                'user_id': vote.user_id,
                'username': user_info.get('username'),
                'thread_id': vote.thread_id,
                'thread_subject': thread_info.get('subject'),
                'vote': vote.vote,
                'confidence': vote.confidence,
                'timestamp': vote.timestamp.isoformat() if vote.timestamp else None
            })

        # Also include LLM evaluations if any
        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.task_type == 'authenticity',
            LLMTaskResult.thread_id.in_(scenario_thread_ids)
        ).all()

        for result in llm_results:
            thread_info = thread_map.get(result.thread_id, {})
            payload = result.payload_json or {}
            results.append({
                'type': 'authenticity_llm',
                'model_id': result.model_id,
                'thread_id': result.thread_id,
                'thread_subject': thread_info.get('subject'),
                'vote': payload.get('vote'),
                'confidence': payload.get('confidence'),
                'reasoning': payload.get('reasoning'),
                'error': result.error,
                'timestamp': result.created_at.isoformat() if result.created_at else None
            })

    elif func_type_name == 'mail_rating':
        # Export mail history ratings
        mail_ratings = UserMailHistoryRating.query.filter(
            UserMailHistoryRating.user_id.in_(scenario_user_ids),
            UserMailHistoryRating.thread_id.in_(scenario_thread_ids)
        ).all()

        for rating in mail_ratings:
            user_info = user_map.get(rating.user_id, {})
            thread_info = thread_map.get(rating.thread_id, {})
            results.append({
                'type': 'mail_rating',
                'user_id': rating.user_id,
                'username': user_info.get('username'),
                'thread_id': rating.thread_id,
                'thread_subject': thread_info.get('subject'),
                'overall_rating': rating.overall_rating,
                'counsellor_coherence_rating': rating.counsellor_coherence_rating,
                'client_coherence_rating': rating.client_coherence_rating,
                'quality_rating': rating.quality_rating,
                'feedback': rating.feedback,
                'status': rating.status.value if rating.status else None,
                'timestamp': rating.timestamp.isoformat() if rating.timestamp else None
            })

        # Also include consulting category selections
        category_selections = UserConsultingCategorySelection.query.filter(
            UserConsultingCategorySelection.user_id.in_(scenario_user_ids),
            UserConsultingCategorySelection.thread_id.in_(scenario_thread_ids)
        ).all()

        for selection in category_selections:
            user_info = user_map.get(selection.user_id, {})
            thread_info = thread_map.get(selection.thread_id, {})
            results.append({
                'type': 'consulting_category',
                'user_id': selection.user_id,
                'username': user_info.get('username'),
                'thread_id': selection.thread_id,
                'thread_subject': thread_info.get('subject'),
                'consulting_category_type_id': selection.consulting_category_type_id,
                'notes': selection.notes,
                'timestamp': selection.timestamp.isoformat() if selection.timestamp else None
            })

        # Also include LLM evaluations if any
        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.task_type == 'mail_rating',
            LLMTaskResult.thread_id.in_(scenario_thread_ids)
        ).all()

        for result in llm_results:
            thread_info = thread_map.get(result.thread_id, {})
            payload = result.payload_json or {}
            results.append({
                'type': 'mail_rating_llm',
                'model_id': result.model_id,
                'thread_id': result.thread_id,
                'thread_subject': thread_info.get('subject'),
                'rating': payload.get('rating'),
                'reasoning': payload.get('reasoning'),
                'error': result.error,
                'timestamp': result.created_at.isoformat() if result.created_at else None
            })

    else:
        # Generic export - try to get any LLM task results
        llm_results = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario_id,
            LLMTaskResult.thread_id.in_(scenario_thread_ids)
        ).all()

        for result in llm_results:
            thread_info = thread_map.get(result.thread_id, {})
            results.append({
                'type': f'llm_{result.task_type}',
                'model_id': result.model_id,
                'thread_id': result.thread_id,
                'thread_subject': thread_info.get('subject'),
                'payload': result.payload_json,
                'error': result.error,
                'timestamp': result.created_at.isoformat() if result.created_at else None
            })

    if export_format == 'json':
        return jsonify({
            'scenario_id': scenario_id,
            'scenario_name': scenario.scenario_name,
            'function_type': func_type_name,
            'total_results': len(results),
            'results': results,
            'exported_at': datetime.utcnow().isoformat()
        }), 200

    elif export_format == 'csv':
        import csv
        import io

        if not results:
            return jsonify({
                'scenario_id': scenario_id,
                'scenario_name': scenario.scenario_name,
                'error': 'No results to export',
                'exported_at': datetime.utcnow().isoformat()
            }), 200

        # Create CSV
        output = io.StringIO()
        fieldnames = list(results[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=scenario_{scenario_id}_export.csv'
            }
        )

    else:
        raise ValidationError(f'Format {export_format} not supported. Use json or csv.')


# ==================== Invitation Management Endpoints ====================

@data_blueprint.route('/scenarios/<int:scenario_id>/respond', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def respond_to_invitation(scenario_id):
    """
    Respond to a scenario invitation (accept or reject).

    Request body:
        - action: 'accept' or 'reject'

    Users can reject invitations to hide scenarios from their evaluation list.
    They can later accept again to restore access.
    """
    user = g.authentik_user
    user_id = getattr(user, 'id', None)
    username = getattr(user, 'username', str(user))

    if not user_id:
        raise ValidationError('User ID not found')

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check if user is invited to this scenario
    su = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        user_id=user_id
    ).first()

    if not su:
        raise NotFoundError('You are not invited to this scenario')

    # Don't allow owners to reject their own scenarios
    if scenario.created_by == username:
        raise ValidationError('Owners cannot reject their own scenarios')

    data = request.get_json()
    action = data.get('action', '').lower()

    if action not in ('accept', 'reject'):
        raise ValidationError("action must be 'accept' or 'reject'")

    if action == 'accept':
        su.invitation_status = InvitationStatus.ACCEPTED
    else:
        su.invitation_status = InvitationStatus.REJECTED

    su.responded_at = datetime.utcnow()
    db.session.commit()

    logger.info(f"User {username} {action}ed invitation to scenario {scenario_id}")

    return jsonify({
        'message': f'Invitation {action}ed successfully',
        'scenario_id': scenario_id,
        'status': su.invitation_status.value
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/reinvite/<int:target_user_id>', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def reinvite_user(scenario_id, target_user_id):
    """
    Re-invite a user who previously rejected an invitation.

    Only the scenario owner can reinvite users.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))

    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    # Find the user's invitation record
    su = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        user_id=target_user_id
    ).first()

    if not su:
        raise NotFoundError('User was never invited to this scenario')

    if su.invitation_status == InvitationStatus.ACCEPTED:
        return jsonify({
            'message': 'User has already accepted the invitation',
            'status': 'accepted'
        }), 200

    # Reset invitation status
    su.invitation_status = InvitationStatus.ACCEPTED
    su.invited_at = datetime.utcnow()
    su.invited_by = username
    su.responded_at = None

    db.session.commit()

    target_user = User.query.get(target_user_id)
    target_username = target_user.username if target_user else f'user_{target_user_id}'

    logger.info(f"User {username} reinvited {target_username} to scenario {scenario_id}")

    return jsonify({
        'message': f'User {target_username} has been reinvited',
        'status': 'accepted'
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/team', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def get_scenario_team(scenario_id):
    """
    Get detailed team information including invitation status.

    This endpoint returns all users associated with a scenario,
    including their invitation status (accepted, rejected, pending).
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check access (owner or admin)
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    # Only show active members in team view
    scenario_users = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        membership_status=MembershipStatus.ACTIVE
    ).all()

    team = []
    existing_user_ids = set()

    for su in scenario_users:
        db_user = User.query.get(su.user_id)
        if not db_user:
            continue

        existing_user_ids.add(db_user.id)
        avatar = serialize_user_brief(db_user)
        team.append({
            'user_id': su.user_id,
            'username': db_user.username,
            'display_name': getattr(db_user, 'display_name', db_user.username),
            'role': su.role.value if su.role else 'EVALUATOR',
            'invitation_status': su.invitation_status.value if su.invitation_status else 'accepted',
            'invited_at': su.invited_at.isoformat() if su.invited_at else None,
            'invited_by': su.invited_by,
            'responded_at': su.responded_at.isoformat() if su.responded_at else None,
            'is_ai': getattr(db_user, 'is_ai', False),
            'avatar_seed': avatar.get('avatar_seed'),
            'avatar_url': avatar.get('avatar_url'),
            'collab_color': getattr(db_user, 'collab_color', None)
        })

    # Owner fallback for legacy/generated scenarios without a ScenarioUsers row.
    owner_user = None
    if scenario.created_by:
        owner_user = User.query.filter_by(username=scenario.created_by).first()

    if owner_user and owner_user.id not in existing_user_ids:
        avatar = serialize_user_brief(owner_user)
        team.append({
            'user_id': owner_user.id,
            'username': owner_user.username,
            'display_name': getattr(owner_user, 'display_name', owner_user.username),
            'role': ScenarioRoles.VIEWER.value,
            'invitation_status': InvitationStatus.ACCEPTED.value,
            'invited_at': None,
            'invited_by': scenario.created_by,
            'responded_at': None,
            'is_ai': getattr(owner_user, 'is_ai', False),
            'avatar_seed': avatar.get('avatar_seed'),
            'avatar_url': avatar.get('avatar_url'),
            'collab_color': getattr(owner_user, 'collab_color', None)
        })

    # Count by status
    status_counts = {
        'accepted': sum(1 for t in team if t['invitation_status'] == 'accepted'),
        'rejected': sum(1 for t in team if t['invitation_status'] == 'rejected'),
        'pending': sum(1 for t in team if t['invitation_status'] == 'pending')
    }

    return jsonify({
        'team': team,
        'counts': status_counts,
        'total': len(team)
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/duplicate', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def duplicate_scenario(scenario_id):
    """
    Duplicate an existing scenario.

    Creates a copy of the scenario with all its threads but without
    users, evaluations, or results. The new scenario starts as 'draft'.

    Request body (optional):
        - scenario_name: str (default: original name + " (Copy)")
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    data = request.get_json() or {}

    # Create new scenario name
    new_name = data.get('scenario_name', f"{scenario.scenario_name} (Kopie)")

    # Copy config but reset LLM evaluators
    new_config = dict(scenario.config_json or {})
    new_config['llm_evaluators'] = []  # Reset LLM evaluators for fresh start

    # Create the duplicate scenario
    from datetime import timedelta
    new_scenario = RatingScenarios(
        scenario_name=new_name,
        function_type_id=scenario.function_type_id,
        begin=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(days=30),
        created_by=username,
        config_json=new_config
    )

    # Copy optional fields
    if hasattr(scenario, 'description') and hasattr(new_scenario, 'description'):
        new_scenario.description = scenario.description
    if hasattr(new_scenario, 'status'):
        new_scenario.status = 'draft'
    if hasattr(scenario, 'visibility') and hasattr(new_scenario, 'visibility'):
        new_scenario.visibility = scenario.visibility

    db.session.add(new_scenario)
    db.session.flush()  # Get the new ID

    # Copy all threads from original scenario
    original_threads = ScenarioThreads.query.filter_by(scenario_id=scenario_id).all()
    for st in original_threads:
        new_thread_link = ScenarioThreads(
            scenario_id=new_scenario.id,
            thread_id=st.thread_id
        )
        db.session.add(new_thread_link)

    db.session.commit()

    logger.info(f"User {username} duplicated scenario {scenario_id} -> {new_scenario.id}")

    return jsonify({
        'message': 'Scenario duplicated successfully',
        'scenario': format_scenario_for_api(new_scenario, user)
    }), 201


@data_blueprint.route('/scenarios/<int:scenario_id>/archive', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def archive_scenario(scenario_id):
    """
    Archive a scenario.

    Sets the scenario status to 'archived'. Archived scenarios are
    read-only and hidden from the default scenario list.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    # Check if already archived
    current_status = getattr(scenario, 'status', None)
    if current_status == 'archived':
        raise ValidationError('Scenario is already archived')

    # Archive the scenario
    if hasattr(scenario, 'status'):
        scenario.status = 'archived'
    else:
        raise ValidationError('Scenario model does not support archiving')

    db.session.commit()

    logger.info(f"User {username} archived scenario {scenario_id}")

    return jsonify({
        'message': 'Scenario archived successfully',
        'scenario': format_scenario_for_api(scenario, user)
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/unarchive', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def unarchive_scenario(scenario_id):
    """
    Unarchive a scenario.

    Sets the scenario status back to 'completed' or 'draft' depending on
    whether it has evaluations.
    """
    user = g.authentik_user
    username = getattr(user, 'username', str(user))
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    # Check ownership
    check_scenario_ownership(scenario, user)  # Verifies user is owner or admin, raises ForbiddenError if not

    # Check if actually archived
    current_status = getattr(scenario, 'status', None)
    if current_status != 'archived':
        raise ValidationError('Scenario is not archived')

    # Determine new status based on progress
    thread_count = ScenarioThreads.query.filter_by(scenario_id=scenario_id).count()
    user_count = ScenarioUsers.query.filter_by(
        scenario_id=scenario_id,
        membership_status=MembershipStatus.ACTIVE
    ).count()

    if thread_count > 0 and user_count > 0:
        scenario.status = 'evaluating'
    elif thread_count > 0:
        scenario.status = 'data_collection'
    else:
        scenario.status = 'draft'

    db.session.commit()

    logger.info(f"User {username} unarchived scenario {scenario_id}")

    return jsonify({
        'message': 'Scenario unarchived successfully',
        'scenario': format_scenario_for_api(scenario, user)
    }), 200
