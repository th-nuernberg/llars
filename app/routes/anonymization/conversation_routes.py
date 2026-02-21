"""API routes for anonymization conversation management."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.db import db
from db.models import (
    AnonymizationConversation,
    AnonymizationMessage,
    AnonymizationMessageVersion,
)

logger = logging.getLogger(__name__)
# Create sub-blueprint (no url_prefix - parent handles that)
conversation_bp = Blueprint("anonymization_conversations", __name__)


# Import blueprint at module level to avoid circular imports


@conversation_bp.route("/conversations", methods=["GET"])
@authentik_required
@require_permission("feature:anonymization-pipeline:view")
@handle_api_errors(logger_name="anonymization")
def list_conversations():
    """
    List all conversations with optional filtering.

    Query params:
        status: Filter by status (pending|in_progress|completed|error)
        search: Search in title
        limit: Page size (default: 50, max: 100)
        offset: Pagination offset (default: 0)

    Returns:
        {
            "success": true,
            "conversations": [...],
            "total": 123,
            "limit": 50,
            "offset": 0
        }
    """
    status = request.args.get("status")
    search = request.args.get("search", "").strip()
    quality_filter = request.args.get("quality_filter")  # "all", "included", "excluded"
    limit = int(request.args.get("limit", 50))
    if limit < 0:
        limit = 999999  # Fetch all
    else:
        limit = min(limit, 100)
    offset = int(request.args.get("offset", 0))

    query = AnonymizationConversation.query

    # Filter by status
    if status:
        if status not in ["pending", "in_progress", "completed", "error"]:
            raise ValidationError(f"Invalid status: {status}")
        query = query.filter_by(status=status)

    # Filter by quality/export status
    if quality_filter == "included":
        query = query.filter_by(exclude_from_export=False)
    elif quality_filter == "excluded":
        query = query.filter_by(exclude_from_export=True)

    # Search in title
    if search:
        query = query.filter(AnonymizationConversation.title.ilike(f"%{search}%"))

    # Get total count
    total = query.count()

    # Paginate
    conversations = query.order_by(AnonymizationConversation.imported_at.desc()).limit(limit).offset(offset).all()

    return jsonify(
        {
            "success": True,
            "conversations": [c.to_dict() for c in conversations],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    )


@conversation_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
@authentik_required
@require_permission("feature:anonymization-pipeline:view")
@handle_api_errors(logger_name="anonymization")
def get_conversation(conversation_id: int):
    """
    Get conversation details with messages and entities.

    Returns:
        {
            "success": true,
            "conversation": {
                "id": 1,
                "title": "...",
                "status": "pending",
                "messages": [
                    {
                        "id": 1,
                        "message_number": 1,
                        "author": "user",
                        "original_content": "...",
                        "anonymized_content": "...",
                        "entities": [...]
                    }
                ]
            }
        }
    """
    conversation = AnonymizationConversation.query.get(conversation_id)
    if not conversation:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    return jsonify({"success": True, "conversation": conversation.to_dict(include_messages=True)})


@conversation_bp.route("/conversations/<int:conversation_id>/status", methods=["PATCH"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def update_conversation_status(conversation_id: int):
    """
    Update conversation status.

    Request body:
        {
            "status": "in_progress" | "completed" | "error",
            "error_message": "..." (optional, for error status)
        }

    Returns:
        {
            "success": true,
            "conversation": {...}
        }
    """
    conversation = AnonymizationConversation.query.get(conversation_id)
    if not conversation:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    data = request.get_json()
    new_status = data.get("status")

    if not new_status:
        raise ValidationError("status is required")

    if new_status not in ["in_progress", "completed", "error"]:
        raise ValidationError(f"Invalid status: {new_status}")

    conversation.status = new_status
    conversation.updated_by = g.authentik_user.id
    conversation.updated_at = datetime.utcnow()

    if new_status == "completed":
        conversation.completed_at = datetime.utcnow()

    if new_status == "error":
        conversation.error_message = data.get("error_message")

    db.session.commit()

    logger.info(f"Conversation {conversation_id} status updated to {new_status} by user {g.authentik_user.id}")

    return jsonify({"success": True, "conversation": conversation.to_dict()})


@conversation_bp.route("/conversations/<int:conversation_id>/quality", methods=["PATCH"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def update_conversation_quality(conversation_id: int):
    """
    Update conversation quality rating and export status.

    Request body:
        {
            "quality_rating": 1-5 (optional),
            "exclude_from_export": boolean (optional),
            "quality_notes": "..." (optional)
        }

    Returns:
        {
            "success": true,
            "conversation": {...}
        }
    """
    conversation = AnonymizationConversation.query.get(conversation_id)
    if not conversation:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    data = request.get_json()

    # Update quality rating (1-5 or null)
    if "quality_rating" in data:
        rating = data["quality_rating"]
        if rating is not None and (rating < 1 or rating > 5):
            raise ValidationError("quality_rating must be between 1 and 5")
        conversation.quality_rating = rating

    # Update export exclusion flag
    if "exclude_from_export" in data:
        conversation.exclude_from_export = bool(data["exclude_from_export"])

    # Update quality notes
    if "quality_notes" in data:
        conversation.quality_notes = data["quality_notes"]

    # Set review metadata
    conversation.quality_reviewed_at = datetime.utcnow()
    conversation.quality_reviewed_by = g.authentik_user.id
    conversation.updated_at = datetime.utcnow()
    conversation.updated_by = g.authentik_user.id

    db.session.commit()

    logger.info(f"Conversation {conversation_id} quality updated by user {g.authentik_user.id}")

    return jsonify({"success": True, "conversation": conversation.to_dict()})


@conversation_bp.route("/messages/<int:message_id>", methods=["PATCH"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def update_message(message_id: int):
    """
    Edit message content and create version history.

    Request body:
        {
            "anonymized_content": "Edited text...",
            "change_description": "Fixed typo in anonymization"
        }

    Returns:
        {
            "success": true,
            "message": {...},
            "version": {...}
        }
    """
    message = AnonymizationMessage.query.get(message_id)
    if not message:
        raise NotFoundError(f"Message {message_id} not found")

    data = request.get_json()
    new_content = data.get("anonymized_content", "").strip()

    if not new_content:
        raise ValidationError("anonymized_content is required")

    if new_content == message.anonymized_content:
        raise ValidationError("Content unchanged")

    # Create version record for old content
    version = AnonymizationMessageVersion(
        message_id=message.id,
        version_number=message.current_version,
        content=message.anonymized_content,
        change_description=data.get("change_description", ""),
        changed_by=g.authentik_user.id,
    )
    db.session.add(version)

    # Update message
    message.anonymized_content = new_content
    message.current_version += 1
    message.is_manually_edited = True
    message.updated_at = datetime.utcnow()

    db.session.commit()

    logger.info(f"Message {message_id} updated to version {message.current_version} by user {g.authentik_user.id}")

    return jsonify({"success": True, "message": message.to_dict(include_entities=True), "version": version.to_dict()})


@conversation_bp.route("/messages/<int:message_id>/versions", methods=["GET"])
@authentik_required
@require_permission("feature:anonymization-pipeline:view")
@handle_api_errors(logger_name="anonymization")
def get_message_versions(message_id: int):
    """
    Get version history for a message.

    Returns:
        {
            "success": true,
            "message": {...},
            "versions": [...]
        }
    """
    message = AnonymizationMessage.query.get(message_id)
    if not message:
        raise NotFoundError(f"Message {message_id} not found")

    return jsonify({"success": True, "message": message.to_dict(), "versions": [v.to_dict() for v in message.versions]})
