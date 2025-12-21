"""
User Settings API

Self-service endpoints for users to manage their own settings.
"""

import re
from flask import g, jsonify, request

from auth.decorators import authentik_required
from decorators.error_handler import ValidationError, handle_api_errors
from db.db import db
from routes.auth import data_bp


# Valid hex color pattern
HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


@data_bp.route("/users/me/settings", methods=["GET"])
@authentik_required
@handle_api_errors(logger_name="user_settings")
def get_user_settings():
    """
    Get current user's settings (collab_color, avatar_seed).
    """
    user = g.authentik_user
    return jsonify({
        "success": True,
        "collab_color": user.collab_color,
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None
    })


@data_bp.route("/users/me/settings", methods=["PATCH"])
@authentik_required
@handle_api_errors(logger_name="user_settings")
def update_user_settings():
    """
    Update current user's settings.

    Supported fields:
    - collab_color: Hex color string (#RRGGBB format)
    """
    user = g.authentik_user
    data = request.get_json() or {}

    if "collab_color" in data:
        color = data["collab_color"]
        if color is not None:
            # Validate hex color format
            if not HEX_COLOR_PATTERN.match(color):
                raise ValidationError("collab_color must be a valid hex color (#RRGGBB format)")
        user.collab_color = color

    db.session.commit()

    return jsonify({
        "success": True,
        "collab_color": user.collab_color,
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None
    })
