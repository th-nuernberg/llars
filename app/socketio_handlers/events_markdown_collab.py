"""
Socket.IO events for Markdown Collab real-time updates.

Events:
    Client → Server:
        - markdown_collab:subscribe: Subscribe to workspace list updates for a user
        - markdown_collab:unsubscribe: Unsubscribe from workspace list updates
        - markdown_collab:subscribe_document: Subscribe to commit updates for a document
        - markdown_collab:unsubscribe_document: Unsubscribe from commit updates

    Server → Client:
        - markdown_collab:workspace_shared: A workspace was shared with the user
        - markdown_collab:commit_created: A new commit was created for a document
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

from socketio_handlers.socket_auth import socket_user, socket_authorize

logger = logging.getLogger(__name__)

WORKSPACE_ROOM_PREFIX = "markdown_collab_user_"
DOCUMENT_ROOM_PREFIX = "markdown_collab_doc_"


def get_workspace_room(user_id: int) -> str:
    return f"{WORKSPACE_ROOM_PREFIX}{user_id}"


def get_document_room(document_id: int) -> str:
    return f"{DOCUMENT_ROOM_PREFIX}{document_id}"


def register_markdown_collab_events(socketio):
    """Register Socket.IO events for Markdown Collab real-time updates."""

    @socketio.on('markdown_collab:subscribe')
    def handle_subscribe_workspaces(data=None):
        if data is None:
            data = {}

        user_id = data.get('user_id')
        if not user_id:
            emit('markdown_collab:error', {'error': 'user_id is required'})
            return

        # AuthN + AuthZ: only subscribe to your OWN workspace-update room (or admin).
        user = socket_user('markdown_collab:error')
        if user is None:
            return
        from decorators.permission_decorator import has_role
        if str(user_id) != str(getattr(user, 'id', '')) and not has_role(user, 'admin'):
            emit('markdown_collab:error', {'error': 'Forbidden'})
            return

        room = get_workspace_room(user_id)
        join_room(room)
        logger.info(f"[Markdown Collab] Client {request.sid} subscribed to workspace updates for user {user_id}")
        emit('markdown_collab:subscribed', {'user_id': user_id, 'room': room})

    @socketio.on('markdown_collab:unsubscribe')
    def handle_unsubscribe_workspaces(data=None):
        if data is None:
            data = {}

        user_id = data.get('user_id')
        if not user_id:
            return

        room = get_workspace_room(user_id)
        leave_room(room)
        logger.info(f"[Markdown Collab] Client {request.sid} unsubscribed from workspace updates for user {user_id}")

    @socketio.on('markdown_collab:subscribe_document')
    def handle_subscribe_document(data=None):
        if data is None:
            data = {}

        document_id = data.get('document_id')
        if not document_id:
            emit('markdown_collab:error', {'error': 'document_id is required'})
            return

        # AuthN + AuthZ: only users with access to the document's workspace may
        # subscribe to its commit stream (same check as the HTTP routes).
        user = socket_user('markdown_collab:error')
        if user is None:
            return
        from db.tables import MarkdownDocument
        from routes.markdown_collab.markdown_collab_helpers import _require_document_access
        document = MarkdownDocument.query.get(document_id)
        if not document:
            emit('markdown_collab:error', {'error': 'Forbidden'})
            return
        if not socket_authorize(_require_document_access, document, user.username, error_event='markdown_collab:error'):
            return

        room = get_document_room(document_id)
        join_room(room)
        logger.info(f"[Markdown Collab] Client {request.sid} subscribed to commit updates for document {document_id}")
        emit('markdown_collab:subscribed_document', {'document_id': document_id, 'room': room})

    @socketio.on('markdown_collab:unsubscribe_document')
    def handle_unsubscribe_document(data=None):
        if data is None:
            data = {}

        document_id = data.get('document_id')
        if not document_id:
            return

        room = get_document_room(document_id)
        leave_room(room)
        logger.info(f"[Markdown Collab] Client {request.sid} unsubscribed from commit updates for document {document_id}")

    logger.info("[Markdown Collab] Socket events registered")


def emit_workspace_shared(socketio, user_id: int, workspace: dict):
    """Emit a workspace-shared event to the user."""
    try:
        room = get_workspace_room(user_id)
        socketio.emit('markdown_collab:workspace_shared', {'workspace': workspace}, room=room)
    except Exception as exc:
        logger.error(f"[Markdown Collab] Failed to emit workspace_shared to user {user_id}: {exc}")


def emit_commit_created(socketio, document_id: int, commit: dict):
    """Emit a commit-created event to all subscribers of a document."""
    try:
        room = get_document_room(document_id)
        socketio.emit('markdown_collab:commit_created', {'document_id': document_id, 'commit': commit}, room=room)
    except Exception as exc:
        logger.error(f"[Markdown Collab] Failed to emit commit_created for document {document_id}: {exc}")
