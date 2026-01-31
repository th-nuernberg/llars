import logging
from numbers import Number
from pyexpat.errors import messages
from unicodedata import category

from flask import Blueprint, jsonify, request, g, Response, current_app
from werkzeug.security import check_password_hash
from routes.auth import data_bp as data_blueprint, auth_bp as auth_blueprint
from auth.decorators import authentik_required, admin_required, roles_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, UnauthorizedError
)
from db.database import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating,  UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare, PromptCommit,
                       ConsultingCategoryType, UserConsultingCategorySelection)
from sqlalchemy import func
from uuid import uuid4
import uuid
from datetime import datetime
import json


def _emit_prompt_list_updates(owner_user_id, shared_user_ids=None):
    socketio = current_app.extensions.get('socketio')
    if not socketio:
        return
    try:
        from socketio_handlers.events_prompts import (
            emit_prompts_updated,
            emit_shared_prompts_updated
        )
        emit_prompts_updated(socketio, owner_user_id)
        if shared_user_ids:
            for user_id in set(shared_user_ids):
                emit_shared_prompts_updated(socketio, user_id)
    except Exception:
        # Do not fail the request if socket emission fails
        pass


@data_blueprint.route('/prompts', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def save_user_prompt():
    """
    Route zum Speichern eines neuen Prompts für den angemeldeten Benutzer.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    data = request.get_json()
    prompt_name = data.get('name')
    prompt_content = data.get('content')

    if not prompt_name or not prompt_content:
        raise ValidationError('Prompt name and content are required')

    # Prüfen, ob ein Prompt mit dem gleichen Namen bereits existiert
    existing_prompt = UserPrompt.query.filter_by(user_id=user.id, name=prompt_name).first()
    if existing_prompt:
        raise ConflictError(f'A prompt with the name "{prompt_name}" already exists')

    # Neuen Prompt speichern
    new_prompt = UserPrompt(
        user_id=user.id,
        name=prompt_name,
        content=prompt_content
    )
    db.session.add(new_prompt)
    db.session.commit()

    _emit_prompt_list_updates(user.id)

    return jsonify({
        'success': True,
        'message': 'Prompt saved successfully',
        'data': {
            'id': new_prompt.prompt_id,
            'name': new_prompt.name,
            'content': new_prompt.content,
            'created_at': new_prompt.created_at.isoformat(),
            'updated_at': new_prompt.updated_at.isoformat()
        }
    }), 201


@data_blueprint.route('/prompts', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_user_prompts():
    """
    Route zum Abrufen aller Prompts des angemeldeten Benutzers.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Alle Prompts des Benutzers abrufen inkl. Sharing-Informationen
    user_prompts = UserPrompt.query.filter_by(user_id=user.id).all()

    # Rückgabe der Prompts als JSON mit Sharing-Informationen
    prompts_data = []
    for prompt in user_prompts:
        # Sharing-Informationen abrufen
        shared_users = db.session.query(User.username) \
            .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id) \
            .filter(UserPromptShare.prompt_id == prompt.prompt_id) \
            .all()

        shared_with = [user[0] for user in shared_users]

        prompt_data = {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'created_at': prompt.created_at.isoformat(),
            'updated_at': prompt.updated_at.isoformat(),
            'shared_with': shared_with  # Liste der Benutzernamen
        }
        prompts_data.append(prompt_data)

    return jsonify({'success': True, 'data': prompts_data}), 200

@data_blueprint.route('/prompts/<int:prompt_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_user_prompt(prompt_id):
    """
    Route zum Abrufen eines einzelnen Prompts für den Benutzer.
    Berücksichtigt sowohl eigene als auch geteilte Prompts.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Prompt abrufen (eigene und geteilte)
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |  # Eigene Prompts
         (UserPrompt.prompt_id.in_(  # Geteilte Prompts
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()

    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to view it')

    # Überprüfen, ob es ein geteiltes Prompt ist
    is_shared = prompt.user_id != user.id

    # Besitzer-Informationen hinzufügen
    owner = prompt.user.username

    # Hole alle User mit denen das Prompt geteilt wurde
    shared_users = db.session.query(User.username)\
        .join(UserPromptShare, User.id == UserPromptShare.shared_with_user_id)\
        .filter(UserPromptShare.prompt_id == prompt_id)\
        .all()
    shared_with = [user[0] for user in shared_users]

    # Bestimme ob der aktuelle User Zugriff auf die shared_with Liste haben soll
    should_see_shared_with = (prompt.user_id == user.id) or (user.username in shared_with)

    return jsonify({
        'success': True,
        'data': {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'created_at': prompt.created_at.isoformat(),
            'updated_at': prompt.updated_at.isoformat(),
            'is_shared': is_shared,
            'owner': owner,
            'shared_with': shared_with if should_see_shared_with else []  # Nur ausgeben wenn berechtigt
        }
    }), 200

@data_blueprint.route('/prompts/<int:prompt_id>', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def update_user_prompt(prompt_id):
    """
    Route zum Aktualisieren eines Prompts für den Benutzer.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Prompt abrufen und prüfen, ob der Benutzer Zugriff hat
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |  # Eigene Prompts
         (UserPrompt.prompt_id.in_(  # Geteilte Prompts
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()

    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to edit it')

    data = request.get_json()
    content = data.get('content')

    if not isinstance(content, dict):
        raise ValidationError('Content must be a valid JSON object')

    # Prompt-Inhalt aktualisieren
    prompt.content = content
    prompt.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Prompt updated successfully',
        'data': {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'updated_at': prompt.updated_at.isoformat(),
        }
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/share', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def share_prompt(prompt_id):
    """
    Route zum Freigeben eines Prompts für einen anderen Benutzer.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    data = request.get_json()
    shared_with_username = data.get('shared_with')

    if not shared_with_username:
        raise ValidationError('Username to share with is required')

    # Prüfen, ob der Benutzer versucht, das Prompt mit sich selbst zu teilen
    if shared_with_username == user.username:
        raise ValidationError('You cannot share a prompt with yourself')

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to share it')

    # Zielbenutzer abrufen
    shared_with_user = User.query.filter_by(username=shared_with_username).first()
    if not shared_with_user:
        raise NotFoundError(f'User "{shared_with_username}" not found')

    # Prüfen, ob das Prompt bereits freigegeben wurde
    existing_share = UserPromptShare.query.filter_by(prompt_id=prompt_id, shared_with_user_id=shared_with_user.id).first()
    if existing_share:
        raise ConflictError(f'Prompt is already shared with "{shared_with_username}"')

    # Freigabe erstellen
    new_share = UserPromptShare(prompt_id=prompt_id, shared_with_user_id=shared_with_user.id)
    db.session.add(new_share)
    db.session.commit()

    _emit_prompt_list_updates(user.id, [shared_with_user.id])

    return jsonify({'success': True, 'message': f'Prompt shared with "{shared_with_username}" successfully'}), 201


@data_blueprint.route('/prompts/<int:prompt_id>/unshare', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def unshare_prompt(prompt_id):
    """
    Route zum Entfernen der Freigabe eines Prompts für einen Benutzer.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    data = request.get_json()
    unshare_with_username = data.get('unshare_with')

    if not unshare_with_username:
        raise ValidationError('Username to unshare with is required')

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to unshare it')

    # Zielbenutzer abrufen
    unshare_with_user = User.query.filter_by(username=unshare_with_username).first()
    if not unshare_with_user:
        raise NotFoundError(f'User "{unshare_with_username}" not found')

    # Freigabe entfernen
    share = UserPromptShare.query.filter_by(
        prompt_id=prompt_id,
        shared_with_user_id=unshare_with_user.id
    ).first()

    if not share:
        raise NotFoundError(f'Prompt is not shared with "{unshare_with_username}"')

    db.session.delete(share)
    db.session.commit()

    _emit_prompt_list_updates(user.id, [unshare_with_user.id])

    return jsonify({'success': True, 'message': f'Prompt sharing removed for "{unshare_with_username}" successfully'}), 200



@data_blueprint.route('/prompts/templates', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_templates():
    """
    Get all prompts as templates for the Generation module.
    Returns prompts with assembled text content for preview.
    Includes both own and shared prompts.
    """
    user = g.authentik_user

    # Get own prompts
    own_prompts = UserPrompt.query.filter_by(user_id=user.id).all()

    # Get shared prompts
    shared_prompts = db.session.query(UserPrompt).join(
        UserPromptShare, UserPrompt.prompt_id == UserPromptShare.prompt_id
    ).filter(
        UserPromptShare.shared_with_user_id == user.id
    ).all()

    def assemble_prompt_text(content):
        """Assemble prompt text from blocks structure."""
        if not isinstance(content, dict):
            return str(content) if content else ''

        # Handle YJS binary format (array of numbers) - return empty for now
        if isinstance(content, list):
            return '[YJS Content - Open in Prompt Engineering to view]'

        blocks = content.get('blocks', {})
        if not blocks:
            return ''

        # Sort blocks by position and concatenate content
        sorted_blocks = sorted(
            blocks.items(),
            key=lambda x: x[1].get('position', 0) if isinstance(x[1], dict) else 0
        )

        text_parts = []
        for block_id, block_data in sorted_blocks:
            if isinstance(block_data, dict):
                block_content = block_data.get('content', '')
                if block_content:
                    text_parts.append(block_content)

        return '\n\n'.join(text_parts)

    templates = []

    # Add own prompts
    for prompt in own_prompts:
        templates.append({
            'id': prompt.prompt_id,
            'name': prompt.name,
            'preview': assemble_prompt_text(prompt.content)[:500],  # First 500 chars
            'full_text': assemble_prompt_text(prompt.content),
            'owner': user.username,
            'is_own': True,
            'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None
        })

    # Add shared prompts
    for prompt in shared_prompts:
        templates.append({
            'id': prompt.prompt_id,
            'name': prompt.name,
            'preview': assemble_prompt_text(prompt.content)[:500],
            'full_text': assemble_prompt_text(prompt.content),
            'owner': prompt.user.username if prompt.user else 'Unknown',
            'is_own': False,
            'updated_at': prompt.updated_at.isoformat() if prompt.updated_at else None
        })

    return jsonify({
        'success': True,
        'templates': templates
    }), 200


@data_blueprint.route('/prompts/shared', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_shared_prompts():
    """
    Route zum Abrufen aller für den Benutzer freigegebenen Prompts.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Freigegebene Prompts mit Sharing-Zeitstempel abrufen
    shared_prompts = db.session.query(
        UserPrompt, UserPromptShare.created_at.label('shared_at')
    ).join(
        UserPromptShare, UserPrompt.prompt_id == UserPromptShare.prompt_id
    ).filter(
        UserPromptShare.shared_with_user_id == user.id
    ).all()

    # Freigegebene Prompts formatieren
    prompts_data = [
        {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'content': prompt.content,
            'owner': prompt.user.username,
            'shared_at': shared_at.isoformat() if shared_at else None
        }
        for prompt, shared_at in shared_prompts
    ]

    return jsonify({'success': True, 'data': prompts_data}), 200


@data_blueprint.route('/prompts/<int:prompt_id>/download', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def download_prompt_json(prompt_id):
    """
    Route zum Herunterladen eines Prompts als formatierte JSON-Datei.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Prompt abrufen und prüfen, ob der Benutzer Zugriff hat
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |
         (UserPrompt.prompt_id.in_(
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()

    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to access it')

    # Formatierte JSON erstellen
    formatted_content = {}

    if isinstance(prompt.content, dict) and 'blocks' in prompt.content:
        # Sortiere die Blöcke nach ihrer Position
        blocks_sorted = sorted(
            prompt.content['blocks'].items(),
            key=lambda x: x[1].get('position', float('inf'))
        )

        # Erstelle das formatierte Dictionary
        formatted_content = {
            block_name: block_data['content']
            for block_name, block_data in blocks_sorted
        }

    # JSON-Response mit Download-Header
    response = Response(
        json.dumps(formatted_content, indent=4, ensure_ascii=False),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=prompt_{prompt.name}.json'
        }
    )

    return response


@data_blueprint.route('/prompts/<int:prompt_id>/rename', methods=['PUT'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def rename_prompt(prompt_id):
    """
    Route zum Umbenennen eines Prompts.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to rename it')

    data = request.get_json()
    new_name = data.get('name')

    if not new_name:
        raise ValidationError('New name is required')

    # Prüfen, ob bereits ein Prompt mit diesem Namen existiert
    existing_prompt = UserPrompt.query.filter_by(user_id=user.id, name=new_name).first()
    if existing_prompt and existing_prompt.prompt_id != prompt_id:
        raise ConflictError(f'A prompt with the name "{new_name}" already exists')

    # Prompt umbenennen
    prompt.name = new_name
    prompt.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Prompt renamed successfully',
        'data': {
            'id': prompt.prompt_id,
            'name': prompt.name,
            'updated_at': prompt.updated_at.isoformat()
        }
    }), 200

@data_blueprint.route('/prompts/<int:prompt_id>', methods=['DELETE'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def delete_prompt(prompt_id):
    """
    Route zum Löschen eines Prompts.
    """
    # Authorization handled by @authentik_required decorator
    user = g.authentik_user

    # Prompt abrufen und prüfen, ob es dem Benutzer gehört
    prompt = UserPrompt.query.filter_by(prompt_id=prompt_id, user_id=user.id).first()
    if not prompt:
        raise NotFoundError('Prompt not found or you do not have permission to delete it')

    # Freigaben für das Prompt entfernen
    shared_user_ids = [
        row.shared_with_user_id
        for row in UserPromptShare.query.filter_by(prompt_id=prompt_id).all()
    ]
    UserPromptShare.query.filter_by(prompt_id=prompt_id).delete()

    # Prompt löschen
    db.session.delete(prompt)
    db.session.commit()

    _emit_prompt_list_updates(user.id, shared_user_ids)

    return jsonify({'success': True, 'message': 'Prompt deleted successfully'}), 200


# ============================================================
# User Search Endpoints (for prompt sharing)
# ============================================================

@data_blueprint.route('/users/search', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def search_users_for_sharing():
    """
    Route zum Suchen von Benutzern für Autocomplete.
    Query-Parameter: q (Suchbegriff), limit (max. Ergebnisse, default 10)
    """
    current_user = g.authentik_user
    query = request.args.get('q', '').strip()
    limit = min(int(request.args.get('limit', 10)), 50)

    if len(query) < 2:
        return jsonify({'success': True, 'users': [], 'message': 'Search query must be at least 2 characters'}), 200

    users = User.query.filter(
        User.username.ilike(f'%{query}%'),
        User.id != current_user.id,
        User.deleted_at.is_(None),  # Exclude deleted users
        User.is_active == True  # Only active users
    ).limit(limit).all()

    return jsonify({
        'success': True,
        'users': [{'id': u.id, 'username': u.username, 'avatar_seed': u.get_avatar_seed() if hasattr(u, 'get_avatar_seed') else None} for u in users]
    }), 200


# ============================================================
# Prompt Git Versioning Endpoints
# ============================================================

def _check_prompt_access(prompt_id, user):
    """Helper to check if user has access to a prompt (owner or shared)."""
    prompt = UserPrompt.query.filter(
        (UserPrompt.prompt_id == prompt_id) &
        ((UserPrompt.user_id == user.id) |
         (UserPrompt.prompt_id.in_(
             db.session.query(UserPromptShare.prompt_id)
             .filter_by(shared_with_user_id=user.id)
         )))
    ).first()
    return prompt


@data_blueprint.route('/prompts/<int:prompt_id>/baseline', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_baseline(prompt_id):
    """
    Get the latest commit snapshot for diff comparison.
    Returns the content_snapshot of the most recent commit.
    """
    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    # Get the most recent commit
    latest_commit = PromptCommit.query.filter_by(prompt_id=prompt_id) \
        .order_by(PromptCommit.created_at.desc()) \
        .first()

    if not latest_commit:
        return jsonify({
            'success': True,
            'baseline': None,
            'message': 'No commits yet'
        }), 200

    return jsonify({
        'success': True,
        'baseline': {
            'commit_id': latest_commit.id,
            'content_snapshot': latest_commit.content_snapshot,
            'created_at': latest_commit.created_at.isoformat(),
            'author': latest_commit.author_username,
            'message': latest_commit.message
        }
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/commits', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_commits(prompt_id):
    """
    Get all commits for a prompt (max 200, reverse chronological order).
    """
    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    commits = PromptCommit.query.filter_by(prompt_id=prompt_id) \
        .order_by(PromptCommit.created_at.desc()) \
        .limit(200) \
        .all()

    return jsonify({
        'success': True,
        'commits': [{
            'id': c.id,
            'author': c.author_username,
            'message': c.message,
            'diff_summary': c.diff_summary,
            'created_at': c.created_at.isoformat()
        } for c in commits]
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/commits/<int:commit_id>', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_commit(prompt_id, commit_id):
    """
    Get a single commit with full content snapshot.
    """
    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    commit = PromptCommit.query.filter_by(id=commit_id, prompt_id=prompt_id).first()

    if not commit:
        raise NotFoundError('Commit not found')

    return jsonify({
        'success': True,
        'commit': {
            'id': commit.id,
            'author': commit.author_username,
            'message': commit.message,
            'diff_summary': commit.diff_summary,
            'content_snapshot': commit.content_snapshot,
            'created_at': commit.created_at.isoformat()
        }
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/commit', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def create_prompt_commit(prompt_id):
    """
    Create a new commit for the prompt.
    Requires: message, content_snapshot
    Optional: diff_summary (JSON with user contributions)
    """
    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    data = request.get_json()
    message = data.get('message', '').strip()
    content_snapshot = data.get('content_snapshot')
    diff_summary = data.get('diff_summary')

    if not message:
        raise ValidationError('Commit message is required')

    if content_snapshot is None:
        raise ValidationError('Content snapshot is required')

    # Create the commit
    new_commit = PromptCommit(
        prompt_id=prompt_id,
        author_username=user.username,
        message=message,
        content_snapshot=content_snapshot,
        diff_summary=diff_summary
    )
    db.session.add(new_commit)
    db.session.commit()

    commit_data = {
        'id': new_commit.id,
        'author': new_commit.author_username,
        'message': new_commit.message,
        'diff_summary': new_commit.diff_summary,
        'created_at': new_commit.created_at.isoformat()
    }

    # Broadcast to Socket.IO subscribers (if socketio is available)
    try:
        from main import socketio
        socketio.emit('prompt:commit_created', {
            'prompt_id': prompt_id,
            'commit': commit_data
        }, room=f'prompt_{prompt_id}')
    except Exception as e:
        logging.warning(f"Could not broadcast commit event: {e}")

    return jsonify({
        'success': True,
        'message': 'Commit created successfully',
        'commit': commit_data
    }), 201


@data_blueprint.route('/prompts/<int:prompt_id>/changes', methods=['GET', 'POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_changes(prompt_id):
    """
    Get block-level changes between current content and baseline.
    Returns per-block status (M/A/D), insertions, deletions.

    For POST requests, accepts current_content in body (JSON string with block titles as keys).
    This allows comparing real-time YJS state with baseline.
    """
    import difflib

    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    # Get the most recent commit as baseline
    latest_commit = PromptCommit.query.filter_by(prompt_id=prompt_id) \
        .order_by(PromptCommit.created_at.desc()) \
        .first()

    # Parse baseline blocks
    baseline_blocks = {}
    if latest_commit and latest_commit.content_snapshot:
        try:
            if isinstance(latest_commit.content_snapshot, str):
                baseline_blocks = json.loads(latest_commit.content_snapshot)
            else:
                baseline_blocks = latest_commit.content_snapshot
        except (json.JSONDecodeError, TypeError):
            baseline_blocks = {}

    # Parse current blocks - prefer POST body, fallback to prompt.content
    current_blocks = {}

    if request.method == 'POST':
        # Current content sent from frontend (real-time YJS state)
        data = request.get_json() or {}
        current_content = data.get('current_content')
        if current_content:
            try:
                if isinstance(current_content, str):
                    current_blocks = json.loads(current_content)
                elif isinstance(current_content, dict):
                    current_blocks = current_content
            except (json.JSONDecodeError, TypeError):
                current_blocks = {}

    # Fallback to prompt.content if no current_content provided
    if not current_blocks and prompt.content and isinstance(prompt.content, dict):
        blocks_data = prompt.content.get('blocks', {})
        for block_id, block_info in blocks_data.items():
            if isinstance(block_info, dict):
                title = block_info.get('title', block_id)
                content = block_info.get('content', '')
                current_blocks[title] = content

    # Compare blocks
    changed_blocks = []
    all_block_titles = set(baseline_blocks.keys()) | set(current_blocks.keys())

    for title in sorted(all_block_titles):
        baseline_content = baseline_blocks.get(title, None)
        current_content = current_blocks.get(title, None)

        if baseline_content is None and current_content is not None:
            # New block (Added)
            insertions = len(current_content.split('\n')) if current_content else 0
            changed_blocks.append({
                'id': title,
                'title': title,
                'status': 'A',
                'insertions': insertions,
                'deletions': 0,
                'has_baseline': False
            })
        elif baseline_content is not None and current_content is None:
            # Deleted block
            deletions = len(baseline_content.split('\n')) if baseline_content else 0
            changed_blocks.append({
                'id': title,
                'title': title,
                'status': 'D',
                'insertions': 0,
                'deletions': deletions,
                'has_baseline': True
            })
        elif baseline_content != current_content:
            # Modified block
            baseline_lines = (baseline_content or '').split('\n')
            current_lines = (current_content or '').split('\n')

            # Use difflib to get line-level changes
            diff = list(difflib.unified_diff(baseline_lines, current_lines, lineterm=''))
            insertions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

            changed_blocks.append({
                'id': title,
                'title': title,
                'status': 'M',
                'insertions': insertions,
                'deletions': deletions,
                'has_baseline': True
            })

    return jsonify({
        'success': True,
        'changed_blocks': changed_blocks,
        'total_changes': len(changed_blocks),
        'baseline_commit_id': latest_commit.id if latest_commit else None
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/blocks/<path:block_id>/diff', methods=['GET', 'POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_prompt_block_diff(prompt_id, block_id):
    """
    Get unified diff for a single block.
    block_id is the block title (URL-encoded).

    For POST requests, accepts current_content in body (JSON string with block titles as keys).
    """
    import difflib

    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    # Get the most recent commit as baseline
    latest_commit = PromptCommit.query.filter_by(prompt_id=prompt_id) \
        .order_by(PromptCommit.created_at.desc()) \
        .first()

    # Parse baseline blocks
    baseline_blocks = {}
    if latest_commit and latest_commit.content_snapshot:
        try:
            if isinstance(latest_commit.content_snapshot, str):
                baseline_blocks = json.loads(latest_commit.content_snapshot)
            else:
                baseline_blocks = latest_commit.content_snapshot
        except (json.JSONDecodeError, TypeError):
            baseline_blocks = {}

    # Parse current blocks - prefer POST body, fallback to prompt.content
    current_blocks = {}

    if request.method == 'POST':
        data = request.get_json() or {}
        current_content_data = data.get('current_content')
        if current_content_data:
            try:
                if isinstance(current_content_data, str):
                    current_blocks = json.loads(current_content_data)
                elif isinstance(current_content_data, dict):
                    current_blocks = current_content_data
            except (json.JSONDecodeError, TypeError):
                current_blocks = {}

    # Fallback to prompt.content
    if not current_blocks and prompt.content and isinstance(prompt.content, dict):
        blocks_data = prompt.content.get('blocks', {})
        for bid, block_info in blocks_data.items():
            if isinstance(block_info, dict):
                title = block_info.get('title', bid)
                content = block_info.get('content', '')
                current_blocks[title] = content

    baseline_content = baseline_blocks.get(block_id, '')
    current_content = current_blocks.get(block_id, '')

    # Generate unified diff
    baseline_lines = (baseline_content or '').split('\n')
    current_lines = (current_content or '').split('\n')

    diff_lines = list(difflib.unified_diff(
        baseline_lines,
        current_lines,
        fromfile=f'baseline/{block_id}',
        tofile=f'current/{block_id}',
        lineterm=''
    ))

    return jsonify({
        'success': True,
        'block_id': block_id,
        'baseline_text': baseline_content or '',
        'current_text': current_content or '',
        'diff': '\n'.join(diff_lines),
        'baseline_commit_id': latest_commit.id if latest_commit else None
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/commits/<int:commit_id>/diff', methods=['GET'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def get_commit_diff(prompt_id, commit_id):
    """
    Get the diff for a specific commit.
    Shows what changed between this commit and the previous commit (or initial state).
    Returns block-level changes with before/after content.
    """
    import difflib

    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    # Get the specified commit
    target_commit = PromptCommit.query.filter_by(
        prompt_id=prompt_id,
        id=commit_id
    ).first()

    if not target_commit:
        raise NotFoundError('Commit not found')

    # Get the previous commit (the one before target_commit)
    previous_commit = PromptCommit.query.filter(
        PromptCommit.prompt_id == prompt_id,
        PromptCommit.created_at < target_commit.created_at
    ).order_by(PromptCommit.created_at.desc()).first()

    # Parse target commit content (the "after" state)
    after_blocks = {}
    if target_commit.content_snapshot:
        try:
            if isinstance(target_commit.content_snapshot, str):
                after_blocks = json.loads(target_commit.content_snapshot)
            else:
                after_blocks = target_commit.content_snapshot
        except (json.JSONDecodeError, TypeError):
            after_blocks = {}

    # Parse previous commit content (the "before" state)
    before_blocks = {}
    if previous_commit and previous_commit.content_snapshot:
        try:
            if isinstance(previous_commit.content_snapshot, str):
                before_blocks = json.loads(previous_commit.content_snapshot)
            else:
                before_blocks = previous_commit.content_snapshot
        except (json.JSONDecodeError, TypeError):
            before_blocks = {}

    # Compare blocks
    changed_blocks = []
    all_block_titles = set(before_blocks.keys()) | set(after_blocks.keys())

    for title in sorted(all_block_titles):
        before_content = before_blocks.get(title, None)
        after_content = after_blocks.get(title, None)

        if before_content is None and after_content is not None:
            # New block (Added)
            insertions = len(after_content.split('\n')) if after_content else 0
            changed_blocks.append({
                'title': title,
                'status': 'A',
                'insertions': insertions,
                'deletions': 0,
                'before': '',
                'after': after_content or ''
            })
        elif before_content is not None and after_content is None:
            # Deleted block
            deletions = len(before_content.split('\n')) if before_content else 0
            changed_blocks.append({
                'title': title,
                'status': 'D',
                'insertions': 0,
                'deletions': deletions,
                'before': before_content or '',
                'after': ''
            })
        elif before_content != after_content:
            # Modified block
            before_lines = (before_content or '').split('\n')
            after_lines = (after_content or '').split('\n')

            diff = list(difflib.unified_diff(before_lines, after_lines, lineterm=''))
            insertions = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
            deletions = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

            changed_blocks.append({
                'title': title,
                'status': 'M',
                'insertions': insertions,
                'deletions': deletions,
                'before': before_content or '',
                'after': after_content or ''
            })

    return jsonify({
        'success': True,
        'commit_id': commit_id,
        'previous_commit_id': previous_commit.id if previous_commit else None,
        'changed_blocks': changed_blocks,
        'total_changes': len(changed_blocks)
    }), 200


@data_blueprint.route('/prompts/<int:prompt_id>/rollback', methods=['POST'])
@authentik_required
@handle_api_errors(logger_name='prompts')
def rollback_prompt(prompt_id):
    """
    Rollback prompt content to the last baseline (most recent commit).
    Optionally can rollback a single block.
    """
    user = g.authentik_user
    prompt = _check_prompt_access(prompt_id, user)

    if not prompt:
        raise NotFoundError('Prompt not found or access denied')

    data = request.get_json() or {}
    block_id = data.get('block_id')  # Optional: rollback single block

    # Get the most recent commit as baseline
    latest_commit = PromptCommit.query.filter_by(prompt_id=prompt_id) \
        .order_by(PromptCommit.created_at.desc()) \
        .first()

    if not latest_commit:
        raise NotFoundError('No commits found - cannot rollback')

    # Parse baseline content
    baseline_content = {}
    if latest_commit.content_snapshot:
        try:
            if isinstance(latest_commit.content_snapshot, str):
                baseline_content = json.loads(latest_commit.content_snapshot)
            else:
                baseline_content = latest_commit.content_snapshot
        except (json.JSONDecodeError, TypeError):
            raise ValidationError('Invalid baseline snapshot format')

    if block_id:
        # Rollback single block
        if block_id not in baseline_content:
            raise NotFoundError(f'Block "{block_id}" not found in baseline')

        # Update only the specified block in prompt.content
        if prompt.content and isinstance(prompt.content, dict):
            blocks = prompt.content.get('blocks', {})
            # Find the block by title
            for bid, block_info in blocks.items():
                if isinstance(block_info, dict) and block_info.get('title') == block_id:
                    block_info['content'] = baseline_content[block_id]
                    break
            prompt.content = dict(prompt.content)  # Trigger change detection
            db.session.commit()
    else:
        # Full rollback - rebuild content from baseline
        new_blocks = {}
        position = 0
        for title, content in baseline_content.items():
            block_uuid = str(uuid.uuid4())
            new_blocks[block_uuid] = {
                'title': title,
                'content': content,
                'position': position
            }
            position += 1

        prompt.content = {'blocks': new_blocks}
        prompt.updated_at = datetime.utcnow()
        db.session.commit()

    # Broadcast rollback event
    try:
        from main import socketio
        socketio.emit('prompt:rollback', {
            'prompt_id': prompt_id,
            'block_id': block_id,
            'baseline_commit_id': latest_commit.id
        }, room=f'prompt_{prompt_id}')
    except Exception as e:
        logging.warning(f"Could not broadcast rollback event: {e}")

    return jsonify({
        'success': True,
        'message': f'Rolled back {"block " + block_id if block_id else "all content"} to baseline',
        'baseline_commit_id': latest_commit.id,
        'baseline_content': baseline_content if not block_id else {block_id: baseline_content[block_id]}
    }), 200
