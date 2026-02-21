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
            "include_all_completed": true   // export all completed conversations
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
    data = request.get_json()
    conversation_ids = data.get("conversation_ids", [])
    include_all_completed = data.get("include_all_completed", False)

    query = AnonymizationConversation.query

    if include_all_completed:
        query = query.filter_by(status="completed")
    elif conversation_ids:
        query = query.filter(AnonymizationConversation.id.in_(conversation_ids))
    else:
        raise ValidationError("Provide conversation_ids or set include_all_completed=true")

    conversations = query.all()

    if not conversations:
        raise NotFoundError("No conversations found to export")

    # Build export structure (only anonymized content)
    export_data = {
        "metadata": {
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "exported_by": g.authentik_user.username,
            "conversation_count": len(conversations),
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
