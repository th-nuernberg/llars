"""Messaging encryption key management endpoints."""

import logging

from flask import Blueprint, g, jsonify, request

from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from services.messaging_service import MessagingService

logger = logging.getLogger(__name__)

encryption_bp = Blueprint("messaging_encryption", __name__)


@encryption_bp.route("/keys", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def store_key_bundle():
    """Store or update the current user's encryption key bundle."""
    data = request.get_json()
    if not data:
        raise ValidationError("Request body is required")
    if not data.get("identity_public_key"):
        raise ValidationError("identity_public_key is required")
    if not data.get("signed_prekey_public"):
        raise ValidationError("signed_prekey_public is required")

    username = g.authentik_user.username
    bundle = MessagingService.store_key_bundle(username, data)
    return jsonify({"success": True, "key_bundle": bundle}), 200


@encryption_bp.route("/keys/<target_username>", methods=["GET"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def get_key_bundle(target_username):
    """Get a user's encryption key bundle."""
    bundle = MessagingService.get_key_bundle(target_username)
    if not bundle:
        raise NotFoundError(f"Key bundle for {target_username} not found")
    return jsonify({"success": True, "key_bundle": bundle}), 200


@encryption_bp.route("/keys/bulk", methods=["POST"])
@require_permission("feature:communication:access")
@handle_api_errors(logger_name="messaging")
def get_key_bundles_bulk():
    """Get key bundles for multiple users."""
    data = request.get_json()
    if not data or not data.get("usernames"):
        raise ValidationError("usernames list is required")

    bundles = MessagingService.get_key_bundles(data["usernames"])
    return jsonify({"success": True, "key_bundles": bundles}), 200
