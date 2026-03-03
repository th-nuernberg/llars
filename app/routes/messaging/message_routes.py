"""Messaging message endpoints (list, send, edit, delete, read receipts, attachments)."""

import logging

from flask import Blueprint, g, jsonify, request, send_file
from io import BytesIO

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

message_bp = Blueprint("messaging_messages", __name__)


@message_bp.route("/conversations/<int:conversation_id>/messages", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def list_messages(conversation_id):
    """Get messages for a conversation (cursor-based pagination)."""
    username = g.authentik_user.username
    limit = request.args.get("limit", 50, type=int)
    before_id = request.args.get("before_id", None, type=int)

    messages = MessagingService.get_messages(conversation_id, username, limit, before_id)
    return jsonify({"success": True, "messages": messages}), 200


@message_bp.route("/conversations/<int:conversation_id>/messages", methods=["POST"])
@require_permission("feature:communication:chat")
@handle_api_errors(logger_name="messaging")
def send_message(conversation_id):
    """Send a message (REST fallback, prefer Socket.IO)."""
    data = request.get_json()
    if not data or not data.get("content"):
        raise ValidationError("content is required")

    username = g.authentik_user.username
    msg = MessagingService.send_message(
        conversation_id=conversation_id,
        sender=username,
        content=data["content"],
        message_type=data.get("message_type", "text"),
        reply_to_id=data.get("reply_to_id"),
        encryption_metadata=data.get("encryption_metadata"),
    )
    if not msg:
        raise NotFoundError(f"Conversation {conversation_id} not found or access denied")

    # Trigger link preview fetch in background (REST fallback)
    msg_id = msg.get("id")
    is_encrypted = msg.get("is_encrypted", False)
    if msg_id and not is_encrypted:
        try:
            from main import socketio
            from socketio_handlers.events_messaging import _fetch_link_previews
            socketio.start_background_task(_fetch_link_previews, socketio, msg_id, conversation_id)
        except Exception:
            pass  # Non-critical: previews will be missing but message is sent

    return jsonify({"success": True, "message": msg}), 201


@message_bp.route("/messages/<int:message_id>", methods=["PUT"])
@require_permission("feature:communication:chat")
@handle_api_errors(logger_name="messaging")
def edit_message(message_id):
    """Edit a message (sender only)."""
    data = request.get_json()
    if not data or not data.get("content"):
        raise ValidationError("content is required")

    username = g.authentik_user.username
    msg = MessagingService.edit_message(message_id, username, data["content"])
    if not msg:
        raise NotFoundError(f"Message {message_id} not found or access denied")
    return jsonify({"success": True, "message": msg}), 200


@message_bp.route("/messages/<int:message_id>", methods=["DELETE"])
@require_permission("feature:communication:chat")
@handle_api_errors(logger_name="messaging")
def delete_message(message_id):
    """Soft-delete a message."""
    username = g.authentik_user.username
    success = MessagingService.delete_message(message_id, username)
    if not success:
        raise NotFoundError(f"Message {message_id} not found or access denied")
    return jsonify({"success": True}), 200


@message_bp.route("/conversations/<int:conversation_id>/read", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def mark_as_read(conversation_id):
    """Mark messages as read up to a given message ID."""
    data = request.get_json()
    if not data or not data.get("up_to_message_id"):
        raise ValidationError("up_to_message_id is required")

    username = g.authentik_user.username
    success = MessagingService.mark_as_read(conversation_id, username, data["up_to_message_id"])
    if not success:
        raise NotFoundError(f"Conversation {conversation_id} not found")
    return jsonify({"success": True}), 200


@message_bp.route("/messages/<int:message_id>/attachments", methods=["POST"])
@require_permission("feature:communication:chat")
@handle_api_errors(logger_name="messaging")
def upload_attachment(message_id):
    """Upload a file attachment to a message."""
    if "file" not in request.files:
        raise ValidationError("file is required")

    file = request.files["file"]
    if not file.filename:
        raise ValidationError("filename is required")

    username = g.authentik_user.username
    file_data = file.read()

    attachment = MessagingService.add_attachment(
        message_id=message_id,
        username=username,
        filename=file.filename,
        mime_type=file.content_type,
        file_data=file_data,
    )
    if not attachment:
        raise NotFoundError(f"Message {message_id} not found or access denied")
    return jsonify({"success": True, "attachment": attachment}), 201


@message_bp.route("/link-preview", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def get_link_preview():
    """Fetch Open Graph preview for a URL (used by ChatInput compose area)."""
    url = request.args.get("url", "").strip()
    if not url:
        raise ValidationError("url query parameter is required")

    from services.link_preview_service import _is_safe_url, fetch_and_cache_preview

    if not _is_safe_url(url):
        return jsonify({"success": True, "preview": None}), 200

    preview = fetch_and_cache_preview(url)
    return jsonify({"success": True, "preview": preview}), 200


@message_bp.route("/link-preview/image", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def proxy_preview_image():
    """Proxy an external image to avoid CORS issues with OG preview images."""
    import requests as ext_requests
    from services.link_preview_service import _is_safe_url

    image_url = request.args.get("url", "").strip()
    if not image_url:
        raise ValidationError("url query parameter is required")

    if not _is_safe_url(image_url):
        raise ValidationError("URL not allowed")

    try:
        resp = ext_requests.get(
            image_url,
            timeout=5,
            headers={"User-Agent": "LLARS-LinkPreview/1.0"},
            stream=True,
        )
        content_type = resp.headers.get("Content-Type", "image/jpeg")
        if not content_type.startswith("image/"):
            raise ValidationError("URL does not point to an image")

        image_data = resp.raw.read(2 * 1024 * 1024)  # 2MB max
        resp.close()

        return send_file(
            BytesIO(image_data),
            mimetype=content_type,
        )
    except ext_requests.RequestException:
        raise NotFoundError("Could not fetch image")


@message_bp.route("/attachments/<int:attachment_id>", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def download_attachment(attachment_id):
    """Download an attachment."""
    username = g.authentik_user.username
    attachment = MessagingService.get_attachment(attachment_id, username)
    if not attachment:
        raise NotFoundError(f"Attachment {attachment_id} not found")

    return send_file(
        BytesIO(attachment.content),
        mimetype=attachment.mime_type or "application/octet-stream",
        as_attachment=True,
        download_name=attachment.filename,
    )
