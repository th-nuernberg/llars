"""
Zotero Integration Routes

Provides:
- OAuth 1.0a flow for connecting Zotero accounts
- Manual API key connection (alternative to OAuth)
- Library and collection management
- Workspace library linking and sync
"""

import logging
import os
from datetime import datetime
from typing import Tuple, Optional

from flask import Blueprint, request, jsonify, redirect, session, g, url_for
from requests_oauthlib import OAuth1Session

from auth.decorators import authentik_required
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError

from db.db import db
from db.models import (
    User,
    ZoteroConnection,
    WorkspaceZoteroLibrary,
    ZoteroLibraryType,
    ZoteroSyncLog,
    LatexWorkspace,
    LatexDocument,
)
from services.zotero import (
    ZoteroAPIService,
    ZoteroSyncService,
    encrypt_api_key,
    decrypt_api_key,
)
from services.zotero.zotero_api_service import ZoteroAPIError

logger = logging.getLogger(__name__)

zotero_bp = Blueprint("zotero", __name__, url_prefix="/api/zotero")

# Zotero OAuth 1.0a URLs
ZOTERO_REQUEST_TOKEN_URL = "https://www.zotero.org/oauth/request"
ZOTERO_AUTHORIZE_URL = "https://www.zotero.org/oauth/authorize"
ZOTERO_ACCESS_TOKEN_URL = "https://www.zotero.org/oauth/access"


def _get_base_url() -> str:
    """Get the base URL for OAuth callbacks."""
    return os.environ.get("PROJECT_URL", "http://localhost:55080")


def _get_oauth_credentials() -> Tuple[Optional[str], Optional[str], bool, str]:
    """
    Get Zotero OAuth credentials. Checks environment variables first,
    falls back to database (SystemSettings) if not found in env.

    Returns:
        Tuple of (client_key, client_secret, is_available, source)
        source is 'env', 'database', or 'none'
    """
    # 1. Check environment variables first (priority)
    env_key = os.environ.get("ZOTERO_CLIENT_KEY", "").strip()
    env_secret = os.environ.get("ZOTERO_CLIENT_SECRET", "").strip()

    if env_key and env_secret:
        return env_key, env_secret, True, "env"

    # 2. Fallback to database
    try:
        from db.models.system_settings import SystemSettings
        settings = SystemSettings.query.get(1)
        if settings and settings.zotero_oauth_enabled:
            if settings.zotero_client_key and settings.zotero_client_secret_encrypted:
                client_secret = decrypt_api_key(settings.zotero_client_secret_encrypted)
                return settings.zotero_client_key, client_secret, True, "database"
    except Exception as e:
        logger.warning(f"Failed to get Zotero OAuth from database: {e}")

    return None, None, False, "none"


# ============================================================
# Account Connection Endpoints
# ============================================================


@zotero_bp.route("/oauth-available", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def check_oauth_available():
    """
    Check if Zotero OAuth is configured and available.

    Returns:
        Whether OAuth login is available for users
    """
    client_key, client_secret, is_available, source = _get_oauth_credentials()
    return jsonify({
        "success": True,
        "oauth_available": is_available,
    })


@zotero_bp.route("/status", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def get_connection_status():
    """
    Get current user's Zotero connection status.

    Returns:
        Connection status and info if connected
    """
    user = g.authentik_user
    connection = ZoteroConnection.query.filter_by(user_id=user.id).first()

    if not connection:
        return jsonify({
            "success": True,
            "connected": False,
            "connection": None,
        })

    return jsonify({
        "success": True,
        "connected": True,
        "connection": connection.to_dict(),
    })


@zotero_bp.route("/connect/oauth/start", methods=["POST"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def start_oauth():
    """
    Start OAuth 1.0a flow to connect Zotero account.

    Returns:
        Authorization URL to redirect user to
    """
    client_key, client_secret, is_available, source = _get_oauth_credentials()

    if not is_available:
        raise ValidationError(
            "Zotero OAuth ist nicht konfiguriert. Bitte API-Key verwenden oder Admin kontaktieren."
        )

    user = g.authentik_user

    # Check if already connected
    existing = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if existing:
        raise ConflictError("Zotero account already connected. Disconnect first to reconnect.")

    try:
        oauth = OAuth1Session(
            client_key=client_key,
            client_secret=client_secret,
            callback_uri=f"{_get_base_url()}/api/zotero/connect/oauth/callback",
        )

        # Fetch request token
        fetch_response = oauth.fetch_request_token(ZOTERO_REQUEST_TOKEN_URL)

        # Store tokens and user_id in session for callback
        # (callback comes as browser redirect without Bearer token)
        session["zotero_oauth_token"] = fetch_response.get("oauth_token")
        session["zotero_oauth_token_secret"] = fetch_response.get("oauth_token_secret")
        session["zotero_oauth_user_id"] = user.id

        # Get authorization URL
        authorization_url = oauth.authorization_url(ZOTERO_AUTHORIZE_URL)

        return jsonify({
            "success": True,
            "authorization_url": authorization_url,
        })

    except Exception as e:
        logger.exception("Failed to start Zotero OAuth flow")
        raise ValidationError(f"Failed to start OAuth: {str(e)}")


@zotero_bp.route("/connect/oauth/callback", methods=["GET"])
@handle_api_errors(logger_name="zotero")
def oauth_callback():
    """
    OAuth callback handler - exchanges tokens and saves connection.

    Note: No @authentik_required - callback comes as browser redirect from Zotero
    without Bearer token. User is identified via session (set in start_oauth).

    Redirects user back to frontend with status.
    """
    # Get user from session (stored during start_oauth)
    user_id = session.get("zotero_oauth_user_id")
    if not user_id:
        logger.warning("Zotero OAuth callback without user_id in session")
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_error=session_expired")

    user = User.query.get(user_id)
    if not user:
        logger.warning(f"Zotero OAuth callback: user {user_id} not found")
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_error=user_not_found")

    oauth_token = session.get("zotero_oauth_token")
    oauth_token_secret = session.get("zotero_oauth_token_secret")
    oauth_verifier = request.args.get("oauth_verifier")

    if not oauth_token or not oauth_token_secret or not oauth_verifier:
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_error=missing_tokens")

    client_key, client_secret, is_available, source = _get_oauth_credentials()
    if not is_available:
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_error=oauth_not_configured")

    try:
        oauth = OAuth1Session(
            client_key=client_key,
            client_secret=client_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
            verifier=oauth_verifier,
        )

        # Fetch access token
        tokens = oauth.fetch_access_token(ZOTERO_ACCESS_TOKEN_URL)

        # tokens contains: oauth_token (API key), userID, username
        api_key = tokens.get("oauth_token")
        zotero_user_id = str(tokens.get("userID", ""))
        zotero_username = tokens.get("username", "")

        if not api_key or not zotero_user_id:
            return redirect(f"{_get_base_url()}/LatexCollab?zotero_error=invalid_response")

        # Save connection
        connection = ZoteroConnection(
            user_id=user.id,
            zotero_user_id=zotero_user_id,
            zotero_username=zotero_username,
            api_key_encrypted=encrypt_api_key(api_key),
        )
        db.session.add(connection)
        db.session.commit()

        # Clear session tokens
        session.pop("zotero_oauth_token", None)
        session.pop("zotero_oauth_token_secret", None)
        session.pop("zotero_oauth_user_id", None)

        logger.info(f"User {user.username} connected Zotero account {zotero_username}")
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_connected=true")

    except Exception as e:
        logger.exception("Zotero OAuth callback failed")
        return redirect(f"{_get_base_url()}/LatexCollab?zotero_error={str(e)[:100]}")


@zotero_bp.route("/connect/api-key", methods=["POST"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def connect_with_api_key():
    """
    Connect Zotero account using a manually provided API key.

    This is an alternative to OAuth for users who prefer to generate
    their own API key from zotero.org/settings/keys

    Request body:
        {
            "api_key": "string"
        }
    """
    user = g.authentik_user
    data = request.get_json() or {}

    api_key = data.get("api_key", "").strip()
    if not api_key:
        raise ValidationError("API key is required")

    # Check if already connected
    existing = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if existing:
        raise ConflictError("Zotero account already connected. Disconnect first to reconnect.")

    # Verify the API key
    try:
        api_service = ZoteroAPIService(api_key)
        user_info = api_service.verify_connection()
    except ZoteroAPIError as e:
        raise ValidationError(f"Invalid API key: {str(e)}")

    # Save connection
    connection = ZoteroConnection(
        user_id=user.id,
        zotero_user_id=user_info["user_id"],
        zotero_username=user_info["username"],
        api_key_encrypted=encrypt_api_key(api_key),
    )
    db.session.add(connection)
    db.session.commit()

    logger.info(f"User {user.username} connected Zotero account {user_info['username']} via API key")

    return jsonify({
        "success": True,
        "message": "Zotero account connected successfully",
        "connection": connection.to_dict(),
    })


@zotero_bp.route("/disconnect", methods=["DELETE"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def disconnect():
    """
    Disconnect Zotero account.

    This will also unlink all workspace libraries but keep the .bib files.
    """
    user = g.authentik_user

    connection = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if not connection:
        raise NotFoundError("No Zotero account connected")

    # Delete connection (cascades to workspace libraries)
    db.session.delete(connection)
    db.session.commit()

    logger.info(f"User {user.username} disconnected Zotero account")

    return jsonify({
        "success": True,
        "message": "Zotero account disconnected",
    })


# ============================================================
# Library & Collection Endpoints
# ============================================================


@zotero_bp.route("/libraries", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def get_libraries():
    """
    Get all Zotero libraries accessible to the user.

    Returns:
        List of libraries (personal + groups)
    """
    user = g.authentik_user

    connection = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if not connection:
        raise NotFoundError("No Zotero account connected")

    try:
        api_key = decrypt_api_key(connection.api_key_encrypted)
        api_service = ZoteroAPIService(api_key)
        libraries = api_service.get_libraries(connection.zotero_user_id)

        return jsonify({
            "success": True,
            "libraries": [
                {
                    "library_type": lib.library_type,
                    "library_id": lib.library_id,
                    "name": lib.name,
                    "description": lib.description,
                    "is_owner": lib.is_owner,
                }
                for lib in libraries
            ],
        })
    except ZoteroAPIError as e:
        raise ValidationError(f"Failed to fetch libraries: {str(e)}")


@zotero_bp.route("/libraries/<library_type>/<library_id>/collections", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def get_collections(library_type: str, library_id: str):
    """
    Get collections in a Zotero library.

    Args:
        library_type: "user" or "group"
        library_id: User or group ID
    """
    user = g.authentik_user

    if library_type not in ("user", "group"):
        raise ValidationError("library_type must be 'user' or 'group'")

    connection = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if not connection:
        raise NotFoundError("No Zotero account connected")

    try:
        api_key = decrypt_api_key(connection.api_key_encrypted)
        api_service = ZoteroAPIService(api_key)
        collections = api_service.get_collections(library_type, library_id)

        return jsonify({
            "success": True,
            "collections": [
                {
                    "key": c.key,
                    "name": c.name,
                    "parent_key": c.parent_key,
                    "num_items": c.num_items,
                }
                for c in collections
            ],
        })
    except ZoteroAPIError as e:
        raise ValidationError(f"Failed to fetch collections: {str(e)}")


# ============================================================
# Workspace Library Management
# ============================================================


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def get_workspace_libraries(workspace_id: int):
    """
    Get Zotero libraries linked to a workspace.
    """
    user = g.authentik_user

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    # Check access (owner or member)
    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    libraries = WorkspaceZoteroLibrary.query.filter_by(workspace_id=workspace_id).all()

    return jsonify({
        "success": True,
        "libraries": [lib.to_dict() for lib in libraries],
    })


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries", methods=["POST"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def add_workspace_library(workspace_id: int):
    """
    Link a Zotero library/collection to a workspace.

    Request body:
        {
            "library_type": "user" | "group",
            "library_id": "string",
            "library_name": "string",
            "collection_key": "string" | null,
            "collection_name": "string" | null,
            "bib_filename": "string",
            "auto_sync_enabled": false,
            "auto_sync_interval_minutes": 30
        }
    """
    user = g.authentik_user
    data = request.get_json() or {}

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    # Check edit access
    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    # Get Zotero connection
    connection = ZoteroConnection.query.filter_by(user_id=user.id).first()
    if not connection:
        raise ValidationError("No Zotero account connected")

    # Validate input
    library_type = data.get("library_type")
    library_id = data.get("library_id")
    library_name = data.get("library_name", "")
    collection_key = data.get("collection_key")
    collection_name = data.get("collection_name")
    bib_filename = data.get("bib_filename", "").strip()

    if library_type not in ("user", "group"):
        raise ValidationError("library_type must be 'user' or 'group'")
    if not library_id:
        raise ValidationError("library_id is required")
    if not bib_filename:
        raise ValidationError("bib_filename is required")
    if not bib_filename.endswith(".bib"):
        bib_filename += ".bib"

    # Check for duplicate
    existing = WorkspaceZoteroLibrary.query.filter_by(
        workspace_id=workspace_id,
        library_id=library_id,
        collection_key=collection_key,
    ).first()
    if existing:
        raise ConflictError("This library/collection is already linked to the workspace")

    # Check filename conflict
    filename_exists = LatexDocument.query.filter_by(
        workspace_id=workspace_id,
        title=bib_filename,
    ).first()
    if filename_exists:
        raise ConflictError(f"A file named '{bib_filename}' already exists in the workspace")

    # Create the link
    workspace_library = WorkspaceZoteroLibrary(
        workspace_id=workspace_id,
        zotero_connection_id=connection.id,
        library_type=ZoteroLibraryType(library_type),
        library_id=library_id,
        library_name=library_name,
        collection_key=collection_key,
        collection_name=collection_name,
        bib_filename=bib_filename,
        auto_sync_enabled=data.get("auto_sync_enabled", False),
        auto_sync_interval_minutes=data.get("auto_sync_interval_minutes", 30),
    )
    db.session.add(workspace_library)
    db.session.commit()

    # Perform initial sync
    sync_service = ZoteroSyncService(workspace_library)
    success, message = sync_service.sync(
        triggered_by="manual",
        triggered_by_username=user.username,
    )

    if not success:
        logger.warning(f"Initial sync failed for workspace library {workspace_library.id}: {message}")

    # Reload to get updated data
    db.session.refresh(workspace_library)

    return jsonify({
        "success": True,
        "message": "Library linked and synced" if success else f"Library linked but sync failed: {message}",
        "library": workspace_library.to_dict(),
    }), 201


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries/<int:library_id>", methods=["DELETE"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def remove_workspace_library(workspace_id: int, library_id: int):
    """
    Unlink a Zotero library from a workspace.

    The .bib file will be kept in the workspace but no longer synced.
    """
    user = g.authentik_user

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    workspace_library = WorkspaceZoteroLibrary.query.filter_by(
        id=library_id,
        workspace_id=workspace_id,
    ).first()
    if not workspace_library:
        raise NotFoundError("Library link not found")

    # Keep the .bib document, just unlink it
    workspace_library.document_id = None

    db.session.delete(workspace_library)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Library unlinked from workspace",
    })


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries/<int:library_id>/sync", methods=["POST"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def sync_workspace_library(workspace_id: int, library_id: int):
    """
    Manually sync a Zotero library to update the .bib file.
    """
    user = g.authentik_user

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    workspace_library = WorkspaceZoteroLibrary.query.filter_by(
        id=library_id,
        workspace_id=workspace_id,
    ).first()
    if not workspace_library:
        raise NotFoundError("Library link not found")

    success, message = ZoteroSyncService.sync_library(
        workspace_library.id,
        triggered_by="manual",
        triggered_by_username=user.username,
    )

    # Reload to get updated data
    db.session.refresh(workspace_library)

    return jsonify({
        "success": success,
        "message": message,
        "library": workspace_library.to_dict(),
    })


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries/<int:library_id>/settings", methods=["PATCH"])
@authentik_required
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="zotero")
def update_library_settings(workspace_id: int, library_id: int):
    """
    Update library sync settings.

    Request body:
        {
            "auto_sync_enabled": boolean,
            "auto_sync_interval_minutes": number
        }
    """
    user = g.authentik_user
    data = request.get_json() or {}

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    workspace_library = WorkspaceZoteroLibrary.query.filter_by(
        id=library_id,
        workspace_id=workspace_id,
    ).first()
    if not workspace_library:
        raise NotFoundError("Library link not found")

    if "auto_sync_enabled" in data:
        workspace_library.auto_sync_enabled = bool(data["auto_sync_enabled"])

    if "auto_sync_interval_minutes" in data:
        interval = int(data["auto_sync_interval_minutes"])
        if interval < 5:
            raise ValidationError("Sync interval must be at least 5 minutes")
        workspace_library.auto_sync_interval_minutes = interval

    db.session.commit()

    return jsonify({
        "success": True,
        "library": workspace_library.to_dict(),
    })


@zotero_bp.route("/workspaces/<int:workspace_id>/libraries/<int:library_id>/logs", methods=["GET"])
@authentik_required
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="zotero")
def get_sync_logs(workspace_id: int, library_id: int):
    """
    Get sync history for a library.
    """
    user = g.authentik_user

    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise NotFoundError("Workspace not found")

    is_member = any(m.username == user.username for m in workspace.members)
    if workspace.owner_username != user.username and not is_member:
        raise NotFoundError("Workspace not found")

    workspace_library = WorkspaceZoteroLibrary.query.filter_by(
        id=library_id,
        workspace_id=workspace_id,
    ).first()
    if not workspace_library:
        raise NotFoundError("Library link not found")

    limit = request.args.get("limit", 20, type=int)
    logs = ZoteroSyncLog.query.filter_by(
        workspace_library_id=library_id,
    ).order_by(ZoteroSyncLog.created_at.desc()).limit(limit).all()

    return jsonify({
        "success": True,
        "logs": [log.to_dict() for log in logs],
    })
