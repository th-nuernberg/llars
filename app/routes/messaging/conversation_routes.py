"""Messaging conversation endpoints (list, create, manage members)."""

import logging

from flask import Blueprint, g, jsonify, request

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

conversation_bp = Blueprint("messaging_conversations", __name__)


@conversation_bp.route("/conversations", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def list_conversations():
    """List conversations for the current user."""
    username = g.authentik_user.username
    limit = request.args.get("limit", 50, type=int)
    offset = request.args.get("offset", 0, type=int)

    conversations = MessagingService.get_conversations(username, limit, offset)
    return jsonify({"success": True, "conversations": conversations}), 200


@conversation_bp.route("/conversations/<int:conversation_id>", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def get_conversation(conversation_id):
    """Get a single conversation."""
    username = g.authentik_user.username
    conv = MessagingService.get_conversation(conversation_id, username)
    if not conv:
        raise NotFoundError(f"Conversation {conversation_id} not found")
    return jsonify({"success": True, "conversation": conv}), 200


@conversation_bp.route("/conversations/direct", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def create_direct_conversation():
    """Create or return existing 1:1 conversation."""
    data = request.get_json()
    if not data or not data.get("username"):
        raise ValidationError("username is required")

    username = g.authentik_user.username
    conv = MessagingService.create_direct_conversation(username, data["username"])
    return jsonify({"success": True, "conversation": conv}), 201


@conversation_bp.route("/conversations/group", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def create_group_conversation():
    """Create a new group conversation."""
    data = request.get_json()
    if not data or not data.get("name"):
        raise ValidationError("name is required")
    if not data.get("members") or len(data["members"]) < 1:
        raise ValidationError("At least one member is required")

    username = g.authentik_user.username
    conv = MessagingService.create_group_conversation(
        creator=username,
        name=data["name"],
        member_usernames=data["members"],
        description=data.get("description"),
    )
    return jsonify({"success": True, "conversation": conv}), 201


@conversation_bp.route("/conversations/<int:conversation_id>", methods=["PUT"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def update_group_info(conversation_id):
    """Update group name / description."""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")

    username = g.authentik_user.username
    conv = MessagingService.update_group_info(
        conversation_id,
        username,
        name=data.get("name"),
        description=data.get("description"),
    )
    if not conv:
        raise NotFoundError(f"Conversation {conversation_id} not found or insufficient permissions")
    return jsonify({"success": True, "conversation": conv}), 200


@conversation_bp.route("/conversations/<int:conversation_id>/members", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def add_member(conversation_id):
    """Add a member to a group conversation."""
    data = request.get_json()
    if not data or not data.get("username"):
        raise ValidationError("username is required")

    username = g.authentik_user.username
    result = MessagingService.add_group_member(conversation_id, data["username"], username)
    if not result:
        raise NotFoundError(f"Conversation {conversation_id} not found or insufficient permissions")
    return jsonify({"success": True, "conversation": result}), 200


@conversation_bp.route("/conversations/<int:conversation_id>/members/<member_username>", methods=["DELETE"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def remove_member(conversation_id, member_username):
    """Remove a member from a group conversation."""
    username = g.authentik_user.username
    success = MessagingService.remove_group_member(conversation_id, member_username, username)
    if not success:
        raise NotFoundError(f"Cannot remove member from conversation {conversation_id}")
    return jsonify({"success": True}), 200


@conversation_bp.route("/conversations/<int:conversation_id>/mute", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def mute_conversation(conversation_id):
    """Mute or unmute a conversation."""
    data = request.get_json() or {}
    username = g.authentik_user.username
    mute = data.get("mute", True)
    success = MessagingService.mute_conversation(conversation_id, username, mute)
    if not success:
        raise NotFoundError(f"Conversation {conversation_id} not found")
    return jsonify({"success": True, "is_muted": mute}), 200


@conversation_bp.route("/unread", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def get_unread_counts():
    """Get unread message counts for the current user."""
    username = g.authentik_user.username
    counts = MessagingService.get_unread_counts(username)
    return jsonify({"success": True, **counts}), 200
