"""
User Settings Routes.

Personal settings management (theme, avatar, collab color, etc.)
"""

from flask import Blueprint, jsonify, request, g
from datetime import datetime

from auth.decorators import authentik_required
from decorators.error_handler import handle_api_errors, ValidationError

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='user_settings')
def get_user_settings():
    """Get current user's settings."""
    user = g.authentik_user

    return jsonify({
        'success': True,
        'settings': {
            'collab_color': user.collab_color,
            'avatar_seed': user.avatar_seed,
            'avatar_file': user.avatar_file,
            'avatar_public_id': user.avatar_public_id,
            'preferences': user.settings_json or {},
            'last_seen_at': user.last_seen_at.isoformat() if user.last_seen_at else None
        }
    })


@settings_bp.route('', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='user_settings')
def update_user_settings():
    """Update current user's settings."""
    from db.database import db

    user = g.authentik_user
    data = request.get_json() or {}

    # Update collab color
    if 'collab_color' in data:
        color = data['collab_color']
        if color and not (color.startswith('#') and len(color) == 7):
            raise ValidationError("Ungültiges Farbformat (erwartet: #RRGGBB)")
        user.collab_color = color

    # Update avatar seed (for generated avatars)
    if 'avatar_seed' in data:
        user.avatar_seed = data['avatar_seed']

    # Update preferences JSON
    if 'preferences' in data:
        current = user.settings_json or {}
        current.update(data['preferences'])
        user.settings_json = current

    db.session.commit()

    return jsonify({
        'success': True,
        'settings': {
            'collab_color': user.collab_color,
            'avatar_seed': user.avatar_seed,
            'preferences': user.settings_json or {}
        }
    })


@settings_bp.route('/avatar', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='user_settings')
def upload_avatar():
    """
    Upload a custom avatar image.

    Expects multipart/form-data with 'avatar' file field.
    Max size: 2MB. Formats: PNG, JPG, GIF, WebP.
    """
    import os
    import uuid
    from werkzeug.utils import secure_filename
    from db.database import db

    user = g.authentik_user

    if 'avatar' not in request.files:
        raise ValidationError("Keine Datei hochgeladen")

    file = request.files['avatar']
    if not file.filename:
        raise ValidationError("Keine Datei ausgewählt")

    # Check file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        raise ValidationError(f"Ungültiger Dateityp. Erlaubt: {', '.join(allowed_extensions)}")

    # Check file size (2MB max)
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > 2 * 1024 * 1024:
        raise ValidationError("Datei zu groß (max 2MB)")

    # Check rate limit (3 changes per day)
    today = datetime.now().date()
    if user.avatar_change_date == today:
        if user.avatar_change_count >= 3:
            raise ValidationError("Avatar-Änderungslimit erreicht (max 3 pro Tag)")
    else:
        user.avatar_change_date = today
        user.avatar_change_count = 0

    # Generate unique filename
    public_id = uuid.uuid4().hex[:16]
    filename = f"avatar_{user.id}_{public_id}.{ext}"

    # Save file
    upload_dir = os.path.join(os.getcwd(), 'uploads', 'avatars')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    # Delete old avatar if exists
    if user.avatar_file:
        old_path = os.path.join(upload_dir, user.avatar_file)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    file.save(filepath)

    # Update user record
    user.avatar_file = filename
    user.avatar_public_id = public_id
    user.avatar_mime_type = file.content_type
    user.avatar_updated_at = datetime.now()
    user.avatar_change_count += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'avatar': {
            'public_id': public_id,
            'url': f"/api/user/settings/avatar/{public_id}"
        }
    })


@settings_bp.route('/avatar/<public_id>', methods=['GET'])
@handle_api_errors(logger_name='user_settings')
def get_avatar(public_id: str):
    """
    Get an avatar image by public ID.

    Public endpoint - no auth required.
    """
    import os
    from flask import send_file
    from db.models.user import User

    user = User.query.filter_by(avatar_public_id=public_id).first()
    if not user or not user.avatar_file:
        # Return default avatar
        return jsonify({'success': False, 'error': 'Avatar nicht gefunden'}), 404

    upload_dir = os.path.join(os.getcwd(), 'uploads', 'avatars')
    filepath = os.path.join(upload_dir, user.avatar_file)

    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Avatar-Datei nicht gefunden'}), 404

    return send_file(
        filepath,
        mimetype=user.avatar_mime_type or 'image/png'
    )


@settings_bp.route('/avatar', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='user_settings')
def delete_avatar():
    """Delete user's custom avatar."""
    import os
    from db.database import db

    user = g.authentik_user

    if user.avatar_file:
        upload_dir = os.path.join(os.getcwd(), 'uploads', 'avatars')
        filepath = os.path.join(upload_dir, user.avatar_file)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    user.avatar_file = None
    user.avatar_public_id = None
    user.avatar_mime_type = None
    user.avatar_updated_at = None

    db.session.commit()

    return jsonify({'success': True})
