"""Export routes for anonymization conversations."""

from __future__ import annotations

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from db.models import AnonymizationConversation
export_bp = Blueprint("anonymization_export", __name__)

logger = logging.getLogger(__name__)


@export_bp.route("/export", methods=["POST"])
@authentik_required
@require_permission("data:export")
@handle_api_errors(logger_name="anonymization")
def export_conversations():
    """
    Export completed conversations as JSON.

    Request body:
        {
            "conversation_ids": [1, 2, 3],  // optional - export specific IDs
            "include_all_completed": true,  // export all completed conversations
            "min_quality_rating": 3         // optional, default 3
        }

    Returns:
        {
            "success": true,
            "export": {
                "metadata": {
                    "exported_at": "2025-02-01T10:00:00Z",
                    "exported_by": "admin",
                    "conversation_count": 3
                },
                "conversations": [...]
            }
        }
    """
    data = request.get_json() or {}
    conversation_ids = data.get("conversation_ids", [])
    include_all_completed = data.get("include_all_completed", False)
    min_quality_rating = data.get("min_quality_rating", 3)

    try:
        min_quality_rating = int(min_quality_rating)
    except (TypeError, ValueError):
        raise ValidationError("min_quality_rating must be an integer between 1 and 5")

    if min_quality_rating < 1 or min_quality_rating > 5:
        raise ValidationError("min_quality_rating must be between 1 and 5")

    # Finished dataset export should only contain fully reviewed conversations.
    query = AnonymizationConversation.query.filter_by(status="completed")

    if include_all_completed:
        pass
    elif conversation_ids:
        query = query.filter(AnonymizationConversation.id.in_(conversation_ids))
    else:
        raise ValidationError("Provide conversation_ids or set include_all_completed=true")

    # Export only high-quality conversations:
    # - explicitly not excluded
    # - quality rating at/above threshold
    query = query.filter(
        AnonymizationConversation.exclude_from_export.is_(False),
        AnonymizationConversation.quality_rating.isnot(None),
        AnonymizationConversation.quality_rating >= min_quality_rating,
    )

    conversations = query.all()

    if not conversations:
        raise NotFoundError(
            f"No high-quality conversations found to export (min_quality_rating={min_quality_rating})"
        )

    # Build export structure (only anonymized content)
    export_data = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "exported_by": g.authentik_user.username,
            "conversation_count": len(conversations),
            "quality_filter": {
                "min_quality_rating": min_quality_rating,
                "exclude_from_export": True,
                "requires_rating": True,
            },
        },
        "conversations": [],
    }

    for conv in conversations:
        conv_data = {
            "id": conv.original_chat_id or str(conv.id),
            "title": conv.title,
            "messages": [],
            "persona": conv.persona_json,
            "created_at": conv.original_created_at.isoformat() + "Z" if conv.original_created_at else None,
            "metadata": {
                "entity_count": conv.entity_count,
                "manually_edited_messages": sum(1 for msg in conv.messages if msg.is_manually_edited),
                "quality_rating": conv.quality_rating,
                "quality_notes": conv.quality_notes,
                "quality_reviewed_at": (
                    conv.quality_reviewed_at.isoformat() + "Z" if conv.quality_reviewed_at else None
                ),
                "quality_reviewed_by": conv.quality_reviewed_by,
            },
        }

        for msg in conv.messages:
            conv_data["messages"].append(
                {
                    "message_number": msg.message_number,
                    "author": msg.author,
                    "content": msg.anonymized_content,  # ONLY anonymized content
                    "version": msg.current_version,
                    "is_manually_edited": msg.is_manually_edited,
                }
            )

        export_data["conversations"].append(conv_data)

    logger.info(f"Exported {len(conversations)} conversations by user {g.authentik_user.id}")

    return jsonify({"success": True, "export": export_data})
