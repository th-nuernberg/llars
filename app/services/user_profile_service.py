"""
User Profile Helpers

Shared helpers for collab colors and avatar URLs.
"""

import random
import re
from typing import Optional, Set, Dict, Any

from db import db
from db.models.user import DEFAULT_COLLAB_COLORS


HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


def is_valid_collab_color(color: str) -> bool:
    return bool(HEX_COLOR_PATTERN.match(color))


def pick_collab_color(used_colors: Optional[Set[str]] = None) -> str:
    if used_colors is None:
        from db.models import User

        with db.session.no_autoflush:
            used_colors = set(
                u.collab_color for u in User.query.with_entities(User.collab_color).all()
                if u.collab_color
            )

    available = [c for c in DEFAULT_COLLAB_COLORS if c not in used_colors]
    return random.choice(available) if available else random.choice(DEFAULT_COLLAB_COLORS)


def build_avatar_url(user) -> Optional[str]:
    public_id = getattr(user, "avatar_public_id", None)
    avatar_file = getattr(user, "avatar_file", None)
    if not public_id or not avatar_file:
        return None
    return f"/api/users/avatar/{public_id}"


def serialize_user_brief(user) -> Dict[str, Any]:
    """Canonical avatar payload for frontend user badges/avatars."""
    if not user:
        return {"username": None, "avatar_seed": None, "avatar_url": None}

    return {
        "username": getattr(user, "username", None),
        "avatar_seed": getattr(user, "avatar_seed", None),
        "avatar_url": build_avatar_url(user),
    }
