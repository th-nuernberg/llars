"""API routes for anonymization conversation management."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.database import db, escape_like
from db.models import (
    AnonymizationConversation,
    AnonymizationMessage,
    AnonymizationMessageVersion,
)
from services.anonymize import AnonymizationPipelineService
from services.anonymize.anonymization_worker import AnonymizationWorker

logger = logging.getLogger(__name__)
# Create sub-blueprint (no url_prefix - parent handles that)
conversation_bp = Blueprint("anonymization_conversations", __name__)
NO_MODEL_FILTER_VALUE = "__NO_MODEL__"


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
        model: Filter by metadata model (case-insensitive, partial match)
               use "__NO_MODEL__" for human-human conversations without model metadata
        course: Filter by metadata course (case-insensitive, partial match)
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
    model_filter = request.args.get("model", "").strip()
    course_filter = request.args.get("course", "").strip()
    quality_filter = request.args.get("quality_filter")  # "all", "included", "excluded"
    raw_limit = int(request.args.get("limit", 50))
    fetch_all = raw_limit < 0
    if fetch_all:
        limit = 999999  # Backwards-compatible response value for "all"
    else:
        limit = min(max(raw_limit, 1), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

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
        query = query.filter(AnonymizationConversation.title.ilike(f"%{escape_like(search)}%"))

    # Load candidate set first so metadata-based filtering can run in Python.
    candidates = query.order_by(AnonymizationConversation.imported_at.desc()).all()

    def _matches_metadata_filter(values: list[str], filter_value: str) -> bool:
        if not filter_value:
            return True
        needle = filter_value.lower()
        return any(needle in str(value).lower() for value in values)

    available_models: set[str] = set()
    available_courses: set[str] = set()
    has_conversations_without_model = False
    filtered_conversations: list[AnonymizationConversation] = []

    for conversation in candidates:
        summary = AnonymizationConversation._build_metadata_summary(conversation.metadata_json)
        models = summary.get("models") or []
        courses = summary.get("courses") or []
        if not models:
            has_conversations_without_model = True

        available_models.update(str(model) for model in models if str(model).strip())
        available_courses.update(str(course) for course in courses if str(course).strip())

        if model_filter == NO_MODEL_FILTER_VALUE:
            if models:
                continue
        elif not _matches_metadata_filter(models, model_filter):
            continue
        if not _matches_metadata_filter(courses, course_filter):
            continue
        filtered_conversations.append(conversation)

    total = len(filtered_conversations)
    if fetch_all:
        conversations = filtered_conversations[offset:]
    else:
        conversations = filtered_conversations[offset : offset + limit]

    return jsonify(
        {
            "success": True,
            "conversations": [c.to_dict() for c in conversations],
            "total": total,
            "limit": limit,
            "offset": offset,
            "available_models": sorted(available_models),
            "available_courses": sorted(available_courses),
            "has_conversations_without_model": has_conversations_without_model,
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

    return jsonify(
        {"success": True, "conversation": conversation.to_dict(include_messages=True, include_metadata=True)}
    )


@conversation_bp.route("/import", methods=["POST"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def import_conversations():
    """
    Import one or multiple conversations from uploaded JSON file.

    Form-data:
        file: .json file containing a conversation object or array of conversations
        run_ner: true|false (optional, default false) - run NER immediately after import

    Returns:
        {
            "success": true,
            "imported_count": 3,
            "failed_count": 0,
            "conversations": [...]
        }
    """
    if "file" not in request.files:
        raise ValidationError("No file provided")

    upload_file = request.files["file"]
    if not upload_file or not upload_file.filename:
        raise ValidationError("Filename is required")

    if not upload_file.filename.lower().endswith(".json"):
        raise ValidationError("Only JSON files are supported")

    content_bytes = upload_file.read()
    if not content_bytes:
        raise ValidationError("Uploaded file is empty")

    try:
        payload = json.loads(content_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValidationError(f"File encoding must be UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON: {exc}") from exc

    run_ner = str(request.form.get("run_ner", "false")).lower() in {"1", "true", "yes", "on"}
    filename = secure_filename(upload_file.filename) or "conversations.json"
    source_path = f"upload://{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"

    # Import without running NER synchronously - we'll do it async if requested
    result = AnonymizationPipelineService.import_conversations(
        payload=payload,
        source_file_path=source_path,
        user_id=g.authentik_user.id,
        run_ner=False,
    )

    db.session.commit()

    logger.info(
        "Imported %s conversation(s) from %s by user %s",
        result["imported_count"],
        upload_file.filename,
        g.authentik_user.id,
    )

    # Auto-start NER in background if requested
    ner_started = False
    if run_ner and result["imported_conversations"]:
        imported_ids = [c.id for c in result["imported_conversations"]]

        # Mark as in_progress
        for conv in result["imported_conversations"]:
            conv.status = "in_progress"
            conv.error_message = None
        db.session.commit()

        try:
            from main import socketio
        except ImportError:
            socketio = None

        AnonymizationWorker.start_async(
            conversation_ids=imported_ids,
            user_id=g.authentik_user.id,
            socketio=socketio,
            force=True,
        )
        ner_started = True

    return (
        jsonify(
            {
                "success": True,
                "imported_count": result["imported_count"],
                "failed_count": result["failed_count"],
                "failed": result["failed"],
                "conversations": [c.to_dict() for c in result["imported_conversations"]],
                "ner_started": ner_started,
            }
        ),
        201,
    )


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


@conversation_bp.route("/conversations/<int:conversation_id>/run-ner", methods=["POST"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def run_conversation_ner(conversation_id: int):
    """
    Run NER/pseudonymization for all messages in a conversation (async with live updates).

    Request body (optional):
        {
            "force": false  # if true, overwrite manually edited messages
        }

    Returns:
        {
            "success": true,
            "conversation": {...},
            "started": true
        }
    """
    conversation = AnonymizationConversation.query.get(conversation_id)
    if not conversation:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))

    # Validate before starting async
    if not force and conversation.messages:
        if any(msg.is_manually_edited for msg in conversation.messages):
            raise ValidationError(
                "Conversation contains manually edited messages. Use force=true to re-run NER."
            )

    # Mark as in_progress immediately
    conversation.status = "in_progress"
    conversation.error_message = None
    conversation.updated_by = g.authentik_user.id
    conversation.updated_at = datetime.utcnow()
    db.session.commit()

    # Start async worker
    try:
        from main import socketio
    except ImportError:
        socketio = None

    AnonymizationWorker.start_async(
        conversation_ids=[conversation_id],
        user_id=g.authentik_user.id,
        socketio=socketio,
        force=force,
    )

    logger.info(
        "NER started async for conversation %s by user %s",
        conversation_id,
        g.authentik_user.id,
    )

    return jsonify(
        {
            "success": True,
            "conversation": conversation.to_dict(),
            "started": True,
        }
    )


@conversation_bp.route("/batch-ner", methods=["POST"])
@authentik_required
@require_permission("feature:anonymization-pipeline:edit")
@handle_api_errors(logger_name="anonymization")
def batch_run_ner():
    """
    Run NER for multiple conversations at once (async with live updates).

    Request body:
        {
            "conversation_ids": [1, 2, 3],  # optional - if omitted, runs for all pending
            "force": false
        }

    Returns:
        {
            "success": true,
            "conversation_ids": [1, 2, 3],
            "started": true
        }
    """
    data = request.get_json(silent=True) or {}
    force = bool(data.get("force", False))
    conversation_ids = data.get("conversation_ids")

    if conversation_ids:
        if not isinstance(conversation_ids, list):
            raise ValidationError("conversation_ids must be a list")
        conversations = AnonymizationConversation.query.filter(
            AnonymizationConversation.id.in_(conversation_ids)
        ).all()
    else:
        # Run NER for all pending conversations
        conversations = AnonymizationConversation.query.filter_by(status="pending").all()

    if not conversations:
        raise ValidationError("No conversations found to process")

    ids = [c.id for c in conversations]

    # Mark all as in_progress
    for conv in conversations:
        conv.status = "in_progress"
        conv.error_message = None
        conv.updated_by = g.authentik_user.id
        conv.updated_at = datetime.utcnow()
    db.session.commit()

    try:
        from main import socketio
    except ImportError:
        socketio = None

    AnonymizationWorker.start_async(
        conversation_ids=ids,
        user_id=g.authentik_user.id,
        socketio=socketio,
        force=force,
    )

    logger.info(
        "Batch NER started for %d conversations by user %s",
        len(ids),
        g.authentik_user.id,
    )

    return jsonify(
        {
            "success": True,
            "conversation_ids": ids,
            "count": len(ids),
            "started": True,
        }
    )


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
