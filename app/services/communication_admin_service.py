"""
Communication Admin Service.

Provides admin functionality for managing communication (messaging) features:
- Global toggle via SystemSettings
- Per-user granular permission management (6 levels)
- Privacy-respecting statistics (counts only, never content)
"""

import logging
from datetime import datetime

from sqlalchemy import text, func

from db.database import db
from db.models.permission import Permission, UserPermission
from db.models.user import User
from services.system_settings_service import is_communication_enabled

logger = logging.getLogger(__name__)

COMMUNICATION_PERMISSIONS = [
    'feature:communication:access',
    'feature:communication:chat',
    'feature:communication:voice',
    'feature:communication:video',
    'feature:communication:transcription',
    'feature:communication:ai',
]


def get_all_users_communication_permissions():
    """
    Get all users with their communication permission states.

    Returns list of dicts with username and boolean for each permission.
    """
    # Get all active users
    users = User.query.filter(
        User.is_active.is_(True),
        User.deleted_at.is_(None),
        User.is_ai.is_(False),
    ).order_by(User.username).all()

    # Get permission IDs for communication permissions
    perm_rows = Permission.query.filter(
        Permission.permission_key.in_(COMMUNICATION_PERMISSIONS)
    ).all()
    perm_id_map = {p.permission_key: p.id for p in perm_rows}

    # Get all user_permissions for communication in one query
    user_perms = UserPermission.query.filter(
        UserPermission.permission_id.in_(perm_id_map.values())
    ).all()

    # Build lookup: (username, permission_id) -> granted
    perm_lookup = {}
    for up in user_perms:
        perm_lookup[(up.username, up.permission_id)] = up.granted

    result = []
    for user in users:
        perms = {}
        for perm_key in COMMUNICATION_PERMISSIONS:
            pid = perm_id_map.get(perm_key)
            if pid:
                entry = perm_lookup.get((user.username, pid))
                perms[perm_key] = entry if entry is not None else False
            else:
                perms[perm_key] = False
        avatar_url = None
        if user.avatar_public_id:
            avatar_url = f"/api/users/avatar/{user.avatar_public_id}"

        result.append({
            'username': user.username,
            'avatar_seed': user.avatar_seed,
            'avatar_url': avatar_url,
            'permissions': perms,
        })

    return result


def set_user_communication_permissions(username, perms_dict, admin_username):
    """
    Set communication permissions for a single user.

    Args:
        username: Target username
        perms_dict: Dict of permission_key -> bool (True=grant, False=revoke)
        admin_username: Admin performing the action

    Returns:
        Dict of updated permission keys
    """
    perm_rows = Permission.query.filter(
        Permission.permission_key.in_(COMMUNICATION_PERMISSIONS)
    ).all()
    perm_id_map = {p.permission_key: p.id for p in perm_rows}

    updated = []
    for perm_key, granted in perms_dict.items():
        if perm_key not in COMMUNICATION_PERMISSIONS:
            continue
        pid = perm_id_map.get(perm_key)
        if not pid:
            continue

        existing = UserPermission.query.filter_by(
            username=username,
            permission_id=pid,
        ).first()

        if granted:
            if existing:
                if not existing.granted:
                    existing.granted = True
                    existing.granted_by = admin_username
                    existing.granted_at = datetime.now()
                    updated.append(perm_key)
            else:
                up = UserPermission(
                    username=username,
                    permission_id=pid,
                    granted=True,
                    granted_by=admin_username,
                    granted_at=datetime.now(),
                )
                db.session.add(up)
                updated.append(perm_key)
        else:
            if existing:
                db.session.delete(existing)
                updated.append(perm_key)

    db.session.commit()
    return updated


def bulk_set_permissions(usernames, perms_dict, admin_username):
    """
    Set communication permissions for multiple users at once.

    Args:
        usernames: List of target usernames
        perms_dict: Dict of permission_key -> bool
        admin_username: Admin performing the action

    Returns:
        Dict with count of updated users
    """
    updated_count = 0
    for username in usernames:
        result = set_user_communication_permissions(username, perms_dict, admin_username)
        if result:
            updated_count += 1

    return {'updated_users': updated_count}


def get_communication_stats():
    """
    Get aggregate communication statistics (privacy-safe, no content).

    Returns dict with total conversations, messages, calls, active users.
    """
    stats = {
        'total_conversations': 0,
        'total_messages': 0,
        'total_calls': 0,
        'active_users': 0,
    }

    try:
        # Total conversations
        result = db.session.execute(text("SELECT COUNT(*) FROM messaging_conversations"))
        stats['total_conversations'] = result.scalar() or 0

        # Total messages
        result = db.session.execute(text(
            "SELECT COUNT(*) FROM messaging_messages WHERE is_deleted = 0"
        ))
        stats['total_messages'] = result.scalar() or 0

        # Total calls
        result = db.session.execute(text("SELECT COUNT(*) FROM messaging_calls"))
        stats['total_calls'] = result.scalar() or 0

        # Active users (users who sent at least one message)
        result = db.session.execute(text(
            "SELECT COUNT(DISTINCT sender_username) FROM messaging_messages WHERE is_deleted = 0"
        ))
        stats['active_users'] = result.scalar() or 0

    except Exception as e:
        logger.warning(f"Failed to fetch communication stats: {e}")

    return stats


def get_user_stats():
    """
    Get per-user communication statistics (privacy-safe, no content).

    Returns list of dicts with username, conversation_count, message_count,
    last_active, unread_count.
    """
    users_stats = []

    try:
        # Get per-user message counts and last activity via SQL aggregation
        rows = db.session.execute(text("""
            SELECT
                p.username,
                COUNT(DISTINCT p.conversation_id) AS conversation_count,
                COALESCE(msg.message_count, 0) AS message_count,
                msg.last_active,
                COALESCE(unread.unread_count, 0) AS unread_count,
                u.avatar_seed,
                u.avatar_public_id
            FROM messaging_participants p
            LEFT JOIN users u ON u.username = p.username
            LEFT JOIN (
                SELECT sender_username,
                       COUNT(*) AS message_count,
                       MAX(created_at) AS last_active
                FROM messaging_messages
                WHERE is_deleted = 0
                GROUP BY sender_username
            ) msg ON msg.sender_username = p.username
            LEFT JOIN (
                SELECT p2.username,
                       SUM(p2.unread_count) AS unread_count
                FROM messaging_participants p2
                WHERE p2.is_active = 1
                GROUP BY p2.username
            ) unread ON unread.username = p.username
            GROUP BY p.username, u.avatar_seed, u.avatar_public_id
            ORDER BY msg.last_active DESC
        """)).fetchall()

        for row in rows:
            avatar_url = f"/api/users/avatar/{row[6]}" if row[6] else None
            users_stats.append({
                'username': row[0],
                'conversation_count': row[1],
                'message_count': row[2],
                'last_active': row[3].isoformat() if row[3] else None,
                'unread_count': row[4],
                'avatar_seed': row[5],
                'avatar_url': avatar_url,
            })

    except Exception as e:
        logger.warning(f"Failed to fetch user communication stats: {e}")

    return users_stats
