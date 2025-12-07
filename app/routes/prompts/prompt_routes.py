import logging
from numbers import Number
from pyexpat.errors import messages
from unicodedata import category

from flask import Blueprint, jsonify, request, g, Response
from werkzeug.security import check_password_hash
from . import data_blueprint
from . import auth_blueprint
from auth.decorators import authentik_required, admin_required, roles_required
from decorators.error_handler import (
    handle_api_errors, NotFoundError, ValidationError, ConflictError, UnauthorizedError
)
from db.db import db
from db.tables import (User, EmailThread, Message, Feature, FeatureType, LLM, UserFeatureRanking,
                       FeatureFunctionType, UserFeatureRating,  UserGroup,ConsultingCategoryType, UserConsultingCategorySelection,
                       FeatureFunctionType, UserFeatureRating, UserMessageRating,
                       UserGroup, UserPrompt, UserPromptShare,
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
