"""
Scenario Utility Functions
Shared helpers for scenario operations to avoid circular imports.
"""

import logging
import random
from decorators.permission_decorator import has_role
from decorators.error_handler import ForbiddenError

logger = logging.getLogger(__name__)


def is_scenario_owner(scenario, username) -> bool:
    """Check if the user is the owner of the scenario (by created_by or OWNER access_level in ScenarioUsers)."""
    # Accept both username string and user object
    if not isinstance(username, str):
        username = getattr(username, 'username', str(username))

    if getattr(scenario, 'created_by', None) == username:
        return True

    # Check ScenarioUsers OWNER access_level (for seeded scenarios where created_by may be NULL)
    from db.models import ScenarioUsers, ScenarioRoles, User, AccessLevel
    # New model: check access_level='OWNER'
    owner_entry = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario.id,
        ScenarioUsers.access_level == AccessLevel.OWNER.value
    ).first()
    # Fallback to legacy role for rows not yet migrated
    if not owner_entry:
        owner_entry = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id,
            role=ScenarioRoles.OWNER
        ).first()
    if owner_entry:
        owner_user = User.query.get(owner_entry.user_id)
        if owner_user and owner_user.username == username:
            return True

    return False


def is_scenario_manager(scenario, username) -> bool:
    """Check if the user has MANAGER access_level for this scenario."""
    if not isinstance(username, str):
        username = getattr(username, 'username', str(username))

    from db.models import ScenarioUsers, ScenarioRoles, User, MembershipStatus, AccessLevel
    # New model: check access_level='MANAGER'
    manager_entries = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario.id,
        ScenarioUsers.access_level == AccessLevel.MANAGER.value,
        ScenarioUsers.membership_status == MembershipStatus.ACTIVE
    ).all()
    # Fallback to legacy role for rows not yet migrated
    if not manager_entries:
        manager_entries = ScenarioUsers.query.filter(
            ScenarioUsers.scenario_id == scenario.id,
            ScenarioUsers.role == ScenarioRoles.MANAGER,
            ScenarioUsers.membership_status == MembershipStatus.ACTIVE
        ).all()
    for entry in manager_entries:
        manager_user = User.query.get(entry.user_id)
        if manager_user and manager_user.username == username:
            return True
    return False


def check_scenario_ownership(scenario, user) -> bool:
    """
    Check if user is the scenario OWNER or admin.
    Used for owner-only actions (delete, remove owner).
    Raises ForbiddenError if not authorized.
    """
    username = getattr(user, 'username', str(user))

    # Admins can manage all scenarios
    if has_role(user, 'admin'):
        return True

    # Check if user is the owner
    if is_scenario_owner(scenario, username):
        return True

    raise ForbiddenError(f'Only the scenario owner or admin can perform this action')


def check_scenario_management_access(scenario, user) -> bool:
    """
    Check if user can manage this scenario (edit settings, invite users).
    Allowed for: Owner, Manager, Admin.
    Raises ForbiddenError if not authorized.
    """
    username = getattr(user, 'username', str(user))

    if has_role(user, 'admin'):
        return True

    if is_scenario_owner(scenario, username):
        return True

    if is_scenario_manager(scenario, username):
        return True

    raise ForbiddenError(f'Only the scenario owner, manager, or admin can perform this action')


def distribute_threads_to_users(thread_ids, user_ids):
    """
    Distribute threads to users in a round-robin fashion.

    Args:
        thread_ids: List of thread IDs to distribute
        user_ids: List of user IDs to receive threads

    Returns:
        Dictionary mapping user_id to list of thread_ids
    """
    if not thread_ids or not user_ids:
        return {}

    # Randomize the thread IDs to ensure a random distribution
    random.shuffle(thread_ids)
    random.shuffle(user_ids)

    # Create a dictionary to store the distribution
    user_threads = {user_id: [] for user_id in user_ids}

    # Distribute the threads round-robin style
    for i, thread_id in enumerate(thread_ids):
        user_id = user_ids[i % len(user_ids)]
        user_threads[user_id].append(thread_id)

    return user_threads


def assign_items_to_new_assessor(scenario_id, scenario, new_scenario_user_id):
    """Assign proportional share of undone items to a newly added assessor.

    Only applies to round_robin distribution mode. In 'all' mode every user
    sees every item, so no distribution records are needed.

    Takes undone items from existing assessors and gives a fair share to the
    new user. Already started/completed items stay with their current owner.
    """
    from db.database import db
    from db.models import (
        ScenarioUsers, ScenarioItems, ScenarioItemDistribution,
        MembershipStatus, ProgressionStatus, EmailThread,
    )
    from routes.HelperFunctions import get_thread_progression_state

    config = getattr(scenario, 'config_json', None) or {}
    distribution_mode = config.get('distribution_mode', 'all')

    if distribution_mode != 'round_robin':
        return

    # All scenario_items for this scenario
    scenario_items = ScenarioItems.query.filter_by(scenario_id=scenario_id).all()
    if not scenario_items:
        return

    # Active assessors EXCLUDING the new one (they already have distributions)
    existing_assessors = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario_id,
        ScenarioUsers.is_assessor.is_(True),
        ScenarioUsers.membership_status == MembershipStatus.ACTIVE,
        ScenarioUsers.id != new_scenario_user_id,
    ).all()

    if not existing_assessors:
        # First assessor — assign all items
        for si in scenario_items:
            db.session.add(ScenarioItemDistribution(
                scenario_id=scenario_id,
                scenario_user_id=new_scenario_user_id,
                scenario_item_id=si.id,
            ))
        return

    # Collect undone items per existing assessor.
    # An item is "undone" for a user if their progression is NOT_STARTED.
    undone_by_assessor = {}  # {scenario_user_id: [scenario_item_id, ...]}
    for su in existing_assessors:
        dists = ScenarioItemDistribution.query.filter_by(
            scenario_id=scenario_id,
            scenario_user_id=su.id,
        ).all()
        undone = []
        for dist in dists:
            si = dist.scenario_item
            if not si:
                continue
            thread = EmailThread.query.get(si.item_id)
            if not thread:
                continue
            try:
                status = get_thread_progression_state(
                    thread, su.user_id, scenario.function_type_id
                )
                if status == ProgressionStatus.NOT_STARTED:
                    undone.append(dist)
            except Exception:
                # If progression check fails, treat as undone to be safe
                undone.append(dist)
        undone_by_assessor[su.id] = undone

    # Total undone items available for redistribution
    total_undone = sum(len(items) for items in undone_by_assessor.values())
    if total_undone == 0:
        return

    # Fair share for the new assessor: total_undone / (existing_assessors + 1)
    num_assessors = len(existing_assessors) + 1
    new_user_share = total_undone // num_assessors
    if new_user_share == 0:
        new_user_share = 1  # Give at least 1 item

    # Collect items to reassign, round-robin from each existing assessor
    items_to_reassign = []
    # Sort assessors by number of undone items (most first) for fair redistribution
    sorted_assessors = sorted(undone_by_assessor.items(), key=lambda x: len(x[1]), reverse=True)

    idx = 0
    while len(items_to_reassign) < new_user_share:
        took_any = False
        for su_id, undone_list in sorted_assessors:
            if len(items_to_reassign) >= new_user_share:
                break
            if idx < len(undone_list):
                items_to_reassign.append(undone_list[idx])
                took_any = True
        idx += 1
        if not took_any:
            break

    # Reassign: update scenario_user_id to new assessor
    for dist in items_to_reassign:
        dist.scenario_user_id = new_scenario_user_id

    logger.info(
        "Assigned %d items to new assessor (su_id=%d) in scenario %d "
        "(from %d existing assessors, %d undone total)",
        len(items_to_reassign), new_scenario_user_id, scenario_id,
        len(existing_assessors), total_undone,
    )


def reassign_items_from_user(scenario_id, scenario, removed_scenario_user_id):
    """Reassign undone items from a user who lost assessor status to remaining assessors.

    Only applies to round_robin distribution mode. Distributes undone items
    evenly among remaining active assessors.
    """
    from db.database import db
    from db.models import (
        ScenarioUsers, ScenarioItemDistribution,
        MembershipStatus, ProgressionStatus, EmailThread,
    )
    from routes.HelperFunctions import get_thread_progression_state

    config = getattr(scenario, 'config_json', None) or {}
    distribution_mode = config.get('distribution_mode', 'all')

    if distribution_mode != 'round_robin':
        return

    # Get the user being removed to check progression
    removed_su = ScenarioUsers.query.get(removed_scenario_user_id)
    if not removed_su:
        return

    # Find remaining active assessors
    remaining_assessors = ScenarioUsers.query.filter(
        ScenarioUsers.scenario_id == scenario_id,
        ScenarioUsers.is_assessor.is_(True),
        ScenarioUsers.membership_status == MembershipStatus.ACTIVE,
        ScenarioUsers.id != removed_scenario_user_id,
    ).all()

    if not remaining_assessors:
        # No remaining assessors — just remove the distributions
        ScenarioItemDistribution.query.filter_by(
            scenario_id=scenario_id,
            scenario_user_id=removed_scenario_user_id,
        ).delete()
        return

    # Find undone items for the removed user
    dists = ScenarioItemDistribution.query.filter_by(
        scenario_id=scenario_id,
        scenario_user_id=removed_scenario_user_id,
    ).all()

    undone_dists = []
    for dist in dists:
        si = dist.scenario_item
        if not si:
            continue
        thread = EmailThread.query.get(si.item_id)
        if not thread:
            continue
        try:
            status = get_thread_progression_state(
                thread, removed_su.user_id, scenario.function_type_id
            )
            if status == ProgressionStatus.NOT_STARTED:
                undone_dists.append(dist)
        except Exception:
            undone_dists.append(dist)

    if not undone_dists:
        return

    # Distribute undone items round-robin among remaining assessors
    remaining_ids = [su.id for su in remaining_assessors]
    random.shuffle(remaining_ids)

    for i, dist in enumerate(undone_dists):
        dist.scenario_user_id = remaining_ids[i % len(remaining_ids)]

    logger.info(
        "Reassigned %d undone items from su_id=%d to %d remaining assessors in scenario %d",
        len(undone_dists), removed_scenario_user_id, len(remaining_assessors), scenario_id,
    )
