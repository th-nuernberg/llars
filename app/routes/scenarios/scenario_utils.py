"""
Scenario Utility Functions
Shared helpers for scenario operations to avoid circular imports.
"""

import random
from decorators.permission_decorator import has_role
from decorators.error_handler import ForbiddenError


def is_scenario_owner(scenario, username) -> bool:
    """Check if the user is the owner of the scenario (by created_by or OWNER role in ScenarioUsers)."""
    # Accept both username string and user object
    if not isinstance(username, str):
        username = getattr(username, 'username', str(username))

    if getattr(scenario, 'created_by', None) == username:
        return True

    # Also check ScenarioUsers OWNER role (for seeded scenarios where created_by may be NULL)
    from db.models import ScenarioUsers, ScenarioRoles, Users
    owner_entry = ScenarioUsers.query.filter_by(
        scenario_id=scenario.id,
        role=ScenarioRoles.OWNER.value
    ).first()
    if owner_entry:
        owner_user = Users.query.get(owner_entry.user_id)
        if owner_user and owner_user.username == username:
            return True

    return False


def check_scenario_ownership(scenario, user) -> bool:
    """
    Check if user can manage this scenario.
    Returns True if user is admin or scenario owner.
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
