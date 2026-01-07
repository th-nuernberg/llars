"""
User Settings API

Self-service endpoints for users to manage their own settings.
"""

import io
import uuid
from datetime import date, datetime
from pathlib import Path

from flask import g, jsonify, request, send_file
from PIL import Image

from auth.decorators import authentik_required, public_endpoint
from decorators.error_handler import NotFoundError, ValidationError, handle_api_errors
from db.database import db
from db.models.user import generate_avatar_seed
from routes.auth import data_bp
from services.user_profile_service import build_avatar_url, is_valid_collab_color, pick_collab_color


MAX_AVATAR_CHANGES_PER_DAY = 3
MAX_AVATAR_FILE_BYTES = 5 * 1024 * 1024
MAX_AVATAR_DIMENSION = 512
ALLOWED_AVATAR_MIME = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


def _get_avatar_storage_dir() -> Path:
    base_dir = Path(__file__).resolve().parents[2] / "storage" / "avatars"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def _current_avatar_change_count(user) -> int:
    if user.avatar_change_date != date.today():
        return 0
    return int(user.avatar_change_count or 0)


def _avatar_changes_left(user) -> int:
    return max(0, MAX_AVATAR_CHANGES_PER_DAY - _current_avatar_change_count(user))


def _ensure_avatar_change_available(user) -> None:
    if _avatar_changes_left(user) <= 0:
        raise ValidationError("Profilbild kann nur 3x pro Tag geaendert werden")


def _consume_avatar_change(user) -> None:
    today = date.today()
    if user.avatar_change_date != today:
        user.avatar_change_date = today
        user.avatar_change_count = 0

    if user.avatar_change_count >= MAX_AVATAR_CHANGES_PER_DAY:
        raise ValidationError("Profilbild kann nur 3x pro Tag geaendert werden")

    user.avatar_change_count = int(user.avatar_change_count or 0) + 1


def _remove_avatar_file(user) -> None:
    if not user.avatar_file:
        return

    path = _get_avatar_storage_dir() / user.avatar_file
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def _process_avatar_image(file_storage) -> bytes:
    if not file_storage or not file_storage.filename:
        raise ValidationError("No avatar file provided")

    if file_storage.mimetype not in ALLOWED_AVATAR_MIME:
        raise ValidationError("Unsupported image type. Allowed: PNG, JPEG, WEBP")

    file_storage.stream.seek(0)
    file_bytes = file_storage.read() or b""
    if not file_bytes:
        raise ValidationError("Uploaded file is empty")
    if len(file_bytes) > MAX_AVATAR_FILE_BYTES:
        raise ValidationError("Avatar image is too large (max 5MB)")

    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValidationError("Invalid image file") from exc

    if image.format not in {"PNG", "JPEG", "JPG", "WEBP"}:
        raise ValidationError("Unsupported image format")

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    image.thumbnail((MAX_AVATAR_DIMENSION, MAX_AVATAR_DIMENSION), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output.read()


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
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None,
        "avatar_url": build_avatar_url(user),
        "avatar_changes_left": _avatar_changes_left(user)
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
        if not color:
            user.collab_color = pick_collab_color()
        else:
            if not is_valid_collab_color(color):
                raise ValidationError("collab_color must be a valid hex color (#RRGGBB format)")
            user.collab_color = color

    db.session.commit()

    return jsonify({
        "success": True,
        "collab_color": user.collab_color,
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None,
        "avatar_url": build_avatar_url(user),
        "avatar_changes_left": _avatar_changes_left(user)
    })


@data_bp.route("/users/me/avatar", methods=["POST"])
@authentik_required
@handle_api_errors(logger_name="user_settings")
def upload_user_avatar():
    user = g.authentik_user
    if "file" not in request.files:
        raise ValidationError("Missing file field 'file'")

    _ensure_avatar_change_available(user)
    avatar_bytes = _process_avatar_image(request.files["file"])

    avatar_dir = _get_avatar_storage_dir()
    avatar_id = uuid.uuid4().hex
    filename = f"avatar_{user.id}_{avatar_id}.png"
    path = avatar_dir / filename
    path.write_bytes(avatar_bytes)

    _remove_avatar_file(user)

    _consume_avatar_change(user)
    user.avatar_file = filename
    user.avatar_public_id = avatar_id
    user.avatar_mime_type = "image/png"
    user.avatar_updated_at = datetime.utcnow()
    if hasattr(user, "get_avatar_seed"):
        user.get_avatar_seed()

    db.session.commit()

    return jsonify({
        "success": True,
        "avatar_url": build_avatar_url(user),
        "avatar_seed": user.avatar_seed,
        "avatar_changes_left": _avatar_changes_left(user)
    })


@data_bp.route("/users/me/avatar", methods=["PATCH"])
@authentik_required
@handle_api_errors(logger_name="user_settings")
def regenerate_user_avatar():
    user = g.authentik_user
    data = request.get_json() or {}
    avatar_seed = (data.get("avatar_seed") or "").strip() or None
    if avatar_seed and len(avatar_seed) > 32:
        raise ValidationError("avatar_seed must be <= 32 characters")

    _ensure_avatar_change_available(user)
    _remove_avatar_file(user)

    _consume_avatar_change(user)
    user.avatar_file = None
    user.avatar_public_id = None
    user.avatar_mime_type = None
    user.avatar_updated_at = datetime.utcnow()
    user.avatar_seed = avatar_seed or generate_avatar_seed()

    db.session.commit()

    return jsonify({
        "success": True,
        "avatar_url": build_avatar_url(user),
        "avatar_seed": user.avatar_seed,
        "avatar_changes_left": _avatar_changes_left(user)
    })


@data_bp.route("/users/me/avatar", methods=["DELETE"])
@authentik_required
@handle_api_errors(logger_name="user_settings")
def reset_user_avatar():
    user = g.authentik_user

    if not user.avatar_file:
        return jsonify({
            "success": True,
            "avatar_url": build_avatar_url(user),
            "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None,
            "avatar_changes_left": _avatar_changes_left(user)
        })

    _ensure_avatar_change_available(user)
    _remove_avatar_file(user)

    _consume_avatar_change(user)
    user.avatar_file = None
    user.avatar_public_id = None
    user.avatar_mime_type = None
    user.avatar_updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "success": True,
        "avatar_url": build_avatar_url(user),
        "avatar_seed": user.get_avatar_seed() if hasattr(user, "get_avatar_seed") else None,
        "avatar_changes_left": _avatar_changes_left(user)
    })


@data_bp.route("/users/avatar/<avatar_id>", methods=["GET"])
@public_endpoint
@handle_api_errors(logger_name="user_settings")
def get_user_avatar(avatar_id: str):
    from db.models import User

    user = User.query.filter_by(avatar_public_id=avatar_id).first()
    if not user or not user.avatar_file:
        raise NotFoundError("Avatar not found")

    path = _get_avatar_storage_dir() / user.avatar_file
    if not path.exists():
        raise NotFoundError("Avatar file not found on disk")

    return send_file(
        path,
        mimetype=user.avatar_mime_type or "image/png",
        conditional=True
    )
