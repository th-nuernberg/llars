import logging
from numbers import Number
from pyexpat.errors import messages
from unicodedata import category

from flask import Blueprint, jsonify, request, g, Response
from werkzeug.security import check_password_hash
from routes.auth import data_bp as data_blueprint, auth_bp as auth_blueprint
from auth.decorators import authentik_required, admin_required, roles_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, UnauthorizedError
)
from db.db import db
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

    return jsonify({'success': True, 'message': f'Prompt sharing removed for "{unshare_with_username}" successfully'}), 200



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
    UserPromptShare.query.filter_by(prompt_id=prompt_id).delete()

    # Prompt löschen
    db.session.delete(prompt)
    db.session.commit()

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
