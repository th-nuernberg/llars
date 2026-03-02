"""Messaging AI feature endpoints (key grants, summarization)."""

import logging

from flask import Blueprint, g, jsonify, request

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

ai_bp = Blueprint("messaging_ai", __name__)


@ai_bp.route("/conversations/<int:conversation_id>/ai-access", methods=["POST"])
@require_permission("feature:communication:ai")
@handle_api_errors(logger_name="messaging")
def grant_ai_access(conversation_id):
    """Grant AI access to E2E conversation keys."""
    data = request.get_json()
    if not data or not data.get("encrypted_key"):
        raise ValidationError("encrypted_key is required")

    username = g.authentik_user.username
    success = MessagingService.grant_ai_access(
        username, conversation_id, data["encrypted_key"]
    )
    if not success:
        raise NotFoundError(f"Conversation {conversation_id} not found or access denied")
    return jsonify({"success": True}), 200


@ai_bp.route("/conversations/<int:conversation_id>/ai-access", methods=["DELETE"])
@require_permission("feature:communication:ai")
@handle_api_errors(logger_name="messaging")
def revoke_ai_access(conversation_id):
    """Revoke AI access to E2E conversation keys."""
    username = g.authentik_user.username
    success = MessagingService.revoke_ai_access(username, conversation_id)
    if not success:
        raise NotFoundError(f"No AI access grant found for conversation {conversation_id}")
    return jsonify({"success": True}), 200


@ai_bp.route("/conversations/<int:conversation_id>/summarize", methods=["POST"])
@require_permission("feature:communication:ai")
@handle_api_errors(logger_name="messaging")
def summarize_conversation(conversation_id):
    """Summarize recent messages in a conversation using LLM."""
    data = request.get_json() or {}
    username = g.authentik_user.username
    limit = data.get("message_count", 50)

    # Verify access
    conv = MessagingService.get_conversation(conversation_id, username)
    if not conv:
        raise NotFoundError(f"Conversation {conversation_id} not found")

    messages = MessagingService.get_messages(conversation_id, username, limit=limit)
    if not messages:
        return jsonify({"success": True, "summary": "No messages to summarize."}), 200

    # Build transcript for summarization
    transcript_lines = []
    for msg in messages:
        if msg.get("is_deleted") or msg.get("message_type") == "system":
            continue
        sender = msg.get("sender_username", "Unknown")
        content = msg.get("content", "")
        transcript_lines.append(f"{sender}: {content}")

    if not transcript_lines:
        return jsonify({"success": True, "summary": "No messages to summarize."}), 200

    transcript = "\n".join(transcript_lines)

    try:
        from services.llm.llm_client_factory import LLMClientFactory

        model_id = data.get("model_id")
        client = LLMClientFactory.create(model_id=model_id, username=username)

        prompt = (
            "Summarize the following chat conversation concisely. "
            "Include key decisions, action items, and important points.\n\n"
            f"{transcript}"
        )

        response = client.chat([{"role": "user", "content": prompt}])
        summary = response.get("content", "") if isinstance(response, dict) else str(response)

        return jsonify({"success": True, "summary": summary}), 200

    except ImportError:
        logger.warning("LLMClientFactory not available for summarization")
        return jsonify({"success": False, "error": "LLM service not available"}), 503
    except Exception as e:
        logger.error("Summarization failed: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@ai_bp.route("/calls/transcript-chunk", methods=["POST"])
@handle_api_errors(logger_name="messaging")
def receive_transcript_chunk():
    """Receive a transcript chunk from the LiveKit transcription agent."""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    room_name = data.get("room_name")
    speaker = data.get("speaker", "Unknown")
    text = data.get("text", "")
    timestamp = data.get("timestamp", 0)

    if not room_name or not text:
        raise ValidationError("room_name and text are required")

    from services.call_transcription_service import CallTranscriptionService

    chunk = CallTranscriptionService.receive_transcript_chunk(
        room_name, speaker, text, timestamp
    )

    # Broadcast via Socket.IO to the conversation room
    try:
        from db.models.messaging import MessagingCall
        call = MessagingCall.query.filter_by(livekit_room_name=room_name).first()
        if call:
            from app import socketio
            socketio.emit("messaging:transcript_update", {
                "call_id": call.id,
                "conversation_id": call.conversation_id,
                **chunk,
            }, room=f"messaging_conv_{call.conversation_id}")
    except Exception as e:
        logger.warning("Failed to broadcast transcript chunk: %s", e)

    return jsonify({"success": True}), 200


@ai_bp.route("/calls/<int:call_id>/summary", methods=["GET"])
@require_permission("feature:communication:ai")
@handle_api_errors(logger_name="messaging")
def get_call_summary(call_id):
    """Get transcript and summary for a call."""
    from services.call_transcription_service import CallTranscriptionService

    result = CallTranscriptionService.get_transcript(call_id)
    if not result:
        raise NotFoundError(f"Call {call_id} not found")
    return jsonify({"success": True, **result}), 200
