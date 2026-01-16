"""
Scenario Manager API
User-facing API for creating, managing and monitoring evaluation scenarios.

This module provides a simplified API for users to:
- Create and manage their own scenarios
- View scenarios they're invited to
- Track progress and statistics
- Start/stop LLM evaluations
"""

import json
import logging
from datetime import datetime
from flask import jsonify, request, g
from auth.decorators import authentik_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ForbiddenError
)
from decorators.permission_decorator import require_permission, has_role
from db.database import db
from db.tables import (
    RatingScenarios, FeatureFunctionType, ScenarioUsers,
    EmailThread, Message, ScenarioThreads, ScenarioRoles, User,
    ScenarioThreadDistribution, InvitationStatus,
    UserFeatureRanking, UserFeatureRating, Feature,
    UserMailHistoryRating, UserConsultingCategorySelection
)
from db.models.authenticity import UserAuthenticityVote
from db.models.llm_task_result import LLMTaskResult
from services.scenario_stats_service import get_progress_stats
from .. import data_blueprint
from .scenario_utils import is_scenario_owner, check_scenario_ownership

logger = logging.getLogger(__name__)


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
        # Get all scenario_users records for this user
        scenario_users = ScenarioUsers.query.filter(
            ScenarioUsers.user_id == user_id
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

    # Count threads and users (only count accepted users for user_count display)
    thread_count = ScenarioThreads.query.filter_by(scenario_id=scenario.id).count()
    user_count = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario.id,
        ScenarioUsers.invitation_status == InvitationStatus.ACCEPTED
    ).count()

    # Compute status based on dates if not explicitly set
    status = getattr(scenario, 'status', None)
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

    # Compute stats
    if include_detailed_stats and thread_count > 0:
        # Calculate detailed progress stats from actual evaluations
        try:
            progress_data = get_progress_stats(scenario.id)
            rater_stats = progress_data.get('rater_stats', [])
            evaluator_stats = progress_data.get('evaluator_stats', [])

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

            stats = {
                'total': thread_count,
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
        'llm_evaluator_count': len(config.get('llm_evaluators', [])),
        'config_json': config,
        'stats': stats,
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

    Returns:
        - Scenarios created by the user
        - Scenarios the user is invited to (filtered by invitation status)
    """
    user = g.authentik_user
    invitation_filter = request.args.get('filter', None)

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

    formatted = [format_scenario_for_api(s, user, invitation_map) for s in scenarios]

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

    # Add users list with real progress
    scenario_users = ScenarioUsers.query.filter_by(scenario_id=scenario_id).all()
    users_list = []
    for su in scenario_users:
        db_user = User.query.get(su.user_id)
        if db_user:
            user_progress = user_stats_map.get(db_user.username, {})
            users_list.append({
                'user_id': su.user_id,
                'username': db_user.username,
                'display_name': getattr(db_user, 'display_name', db_user.username),
                'role': su.role.value if hasattr(su.role, 'value') else str(su.role),
                'completed': user_progress.get('done', 0),
                'total': user_progress.get('total', result['thread_count'])
            })
    result['users'] = users_list

    # Add LLM evaluators from config
    config = scenario.config_json or {}
    result['llm_evaluators'] = config.get('llm_evaluators', [])

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

    # Build response
    threads = []
    for scenario_thread, email_thread in query.all():
        # Count messages in thread
        message_count = len(email_thread.messages) if email_thread.messages else 0

        # Get first message sender and date
        first_message = None
        if email_thread.messages:
            first_message = min(email_thread.messages, key=lambda m: m.timestamp if m.timestamp else datetime.max)

        threads.append({
            'thread_id': email_thread.thread_id,
            'scenario_thread_id': scenario_thread.id,
            'subject': email_thread.subject,
            'sender': first_message.sender if first_message else email_thread.sender,
            'message_count': message_count,
            'created_at': first_message.timestamp.isoformat() if first_message and first_message.timestamp else None,
            'chat_id': email_thread.chat_id,
            'institut_id': email_thread.institut_id,
            'status': 'pending'  # TODO: Calculate from evaluations
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

    return jsonify({
        'message': f'Successfully added {len(validated_threads)} threads',
        'added_count': len(validated_threads),
        'failed_threads': failed_threads
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
    if not config.get('distribution_mode'):
        config['distribution_mode'] = 'all'
    if not config.get('order_mode'):
        config['order_mode'] = 'random'

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

    # Delete related records
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
    """
    user = g.authentik_user
    scenario = RatingScenarios.query.get(scenario_id)

    if not scenario:
        raise NotFoundError(f'Scenario {scenario_id} not found')

    thread_count = ScenarioThreads.query.filter_by(scenario_id=scenario_id).count()
    user_count = ScenarioUsers.query.filter_by(scenario_id=scenario_id).count()

    # Get detailed progress stats
    try:
        progress_data = get_progress_stats(scenario_id)
        rater_stats = progress_data.get('rater_stats', [])
        evaluator_stats = progress_data.get('evaluator_stats', [])

        # Aggregate human evaluator stats
        human_stats = rater_stats + [e for e in evaluator_stats if not e.get('is_llm')]
        human_done = sum(u.get('done_threads', 0) for u in human_stats)
        human_total = sum(u.get('total_threads', 0) for u in human_stats)

        # Aggregate LLM evaluator stats
        llm_stats = [e for e in evaluator_stats if e.get('is_llm')]
        llm_done = sum(u.get('done_threads', 0) for u in llm_stats)
        llm_total = sum(u.get('total_threads', 0) for u in llm_stats)

        # Total evaluations
        total_evaluations = human_total + llm_total
        completed_evaluations = human_done + llm_done
        pending_evaluations = total_evaluations - completed_evaluations

        response = {
            'scenario_id': scenario_id,
            'total_threads': thread_count,
            'total_evaluators': user_count + len(llm_stats),
            'human_evaluators': len(human_stats),
            'llm_evaluators': len(llm_stats),
            'total_evaluations': total_evaluations,
            'completed_evaluations': completed_evaluations,
            'pending_evaluations': pending_evaluations,
            'rater_stats': rater_stats,
            'evaluator_stats': evaluator_stats,
            'agreement_metrics': {
                'kappa': None,
                'alpha': None,
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
        - role: EVALUATOR or RATER (default: EVALUATOR)

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
    role = data.get('role', 'EVALUATOR')

    if not user_ids:
        raise ValidationError('user_ids is required')

    added = 0
    reinvited = 0
    for uid in user_ids:
        # Check if already added
        existing = ScenarioUsers.query.filter_by(
            scenario_id=scenario_id,
            user_id=uid
        ).first()

        if not existing:
            su = ScenarioUsers(
                scenario_id=scenario_id,
                user_id=uid,
                role=role,
                invitation_status=InvitationStatus.ACCEPTED,  # Auto-accept new invitations
                invited_at=datetime.utcnow(),
                invited_by=username
            )
            db.session.add(su)
            added += 1
        elif existing.invitation_status == InvitationStatus.REJECTED:
            # Re-invite a rejected user
            existing.invitation_status = InvitationStatus.ACCEPTED
            existing.invited_at = datetime.utcnow()
            existing.invited_by = username
            existing.responded_at = None
            reinvited += 1

    db.session.commit()

    logger.info(f"User {username} invited {added} users (reinvited {reinvited}) to scenario {scenario_id}")

    return jsonify({
        'message': f'Added {added} users to scenario' + (f', reinvited {reinvited}' if reinvited else ''),
        'added': added,
        'reinvited': reinvited
    }), 200


@data_blueprint.route('/scenarios/<int:scenario_id>/users/<int:user_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='scenario_manager')
def sm_remove_user(scenario_id, user_id):
    """
    Remove a user from a scenario.
    """
    user = g.authentik_user
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

    db.session.delete(su)
    db.session.commit()

    return jsonify({'message': 'User removed from scenario'}), 200


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
        # Export feature rankings
        # Get features for these threads
        features = Feature.query.filter(Feature.thread_id.in_(scenario_thread_ids)).all()
        feature_ids = [f.feature_id for f in features]

        rankings = UserFeatureRanking.query.filter(
            UserFeatureRanking.user_id.in_(scenario_user_ids),
            UserFeatureRanking.feature_id.in_(feature_ids)
        ).all()

        for ranking in rankings:
            user_info = user_map.get(ranking.user_id, {})
            feature = Feature.query.get(ranking.feature_id)
            thread_info = thread_map.get(feature.thread_id, {}) if feature else {}
            results.append({
                'type': 'ranking',
                'user_id': ranking.user_id,
                'username': user_info.get('username'),
                'thread_id': feature.thread_id if feature else None,
                'thread_subject': thread_info.get('subject'),
                'feature_id': ranking.feature_id,
                'feature_content': feature.feature_content if feature else None,
                'ranking_value': ranking.ranking_content,
                'bucket': ranking.bucket
            })

    elif func_type_name == 'rating':
        # Export feature ratings
        features = Feature.query.filter(Feature.thread_id.in_(scenario_thread_ids)).all()
        feature_ids = [f.feature_id for f in features]

        ratings = UserFeatureRating.query.filter(
            UserFeatureRating.user_id.in_(scenario_user_ids),
            UserFeatureRating.feature_id.in_(feature_ids)
        ).all()

        for rating in ratings:
            user_info = user_map.get(rating.user_id, {})
            feature = Feature.query.get(rating.feature_id)
            thread_info = thread_map.get(feature.thread_id, {}) if feature else {}
            results.append({
                'type': 'rating',
                'user_id': rating.user_id,
                'username': user_info.get('username'),
                'thread_id': feature.thread_id if feature else None,
                'thread_subject': thread_info.get('subject'),
                'feature_id': rating.feature_id,
                'feature_content': feature.feature_content if feature else None,
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
                'rating': rating.rating,
                'comment': rating.comment,
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
                'category_id': selection.category_id,
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

    scenario_users = ScenarioUsers.query.filter_by(scenario_id=scenario_id).all()

    team = []
    for su in scenario_users:
        db_user = User.query.get(su.user_id)
        if db_user:
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
                'avatar_seed': getattr(db_user, 'avatar_seed', None),
                'collab_color': getattr(db_user, 'collab_color', None)
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
    user_count = ScenarioUsers.query.filter_by(scenario_id=scenario_id).count()

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
