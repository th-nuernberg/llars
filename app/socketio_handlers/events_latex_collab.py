"""
Socket.IO events for LaTeX Collab real-time updates.

Events:
    Client → Server:
        - latex_collab:subscribe: Subscribe to workspace list updates for a user
        - latex_collab:unsubscribe: Unsubscribe from workspace list updates
        - latex_collab:subscribe_document: Subscribe to document updates (commits, comments)
        - latex_collab:unsubscribe_document: Unsubscribe from document updates
        - latex_collab:subscribe_workspace: Subscribe to workspace-level updates (compile)
        - latex_collab:unsubscribe_workspace: Unsubscribe from workspace-level updates

    Server → Client:
        - latex_collab:workspace_shared: A workspace was shared with the user
        - latex_collab:commit_created: A new commit was created for a document
        - latex_collab:comment_changed: A comment was created, updated, or deleted
        - latex_collab:compile_status: Compile job status update
"""

import logging
from flask_socketio import emit, join_room, leave_room
from flask import request

logger = logging.getLogger(__name__)

WORKSPACE_ROOM_PREFIX = "latex_collab_user_"
DOCUMENT_ROOM_PREFIX = "latex_collab_doc_"
WORKSPACE_UPDATES_ROOM_PREFIX = "latex_collab_workspace_"


def get_workspace_room(user_id: int) -> str:
    return f"{WORKSPACE_ROOM_PREFIX}{user_id}"


def get_document_room(document_id: int) -> str:
    return f"{DOCUMENT_ROOM_PREFIX}{document_id}"


def get_workspace_updates_room(workspace_id: int) -> str:
    return f"{WORKSPACE_UPDATES_ROOM_PREFIX}{workspace_id}"


def register_latex_collab_events(socketio):
    """Register Socket.IO events for LaTeX Collab real-time updates."""

    @socketio.on('latex_collab:subscribe')
    def handle_subscribe_workspaces(data=None):
        if data is None:
            data = {}

        user_id = data.get('user_id')
        if not user_id:
            emit('latex_collab:error', {'error': 'user_id is required'})
            return

        room = get_workspace_room(user_id)
        join_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} subscribed to workspace updates for user {user_id}")
        emit('latex_collab:subscribed', {'user_id': user_id, 'room': room})

    @socketio.on('latex_collab:unsubscribe')
    def handle_unsubscribe_workspaces(data=None):
        if data is None:
            data = {}

        user_id = data.get('user_id')
        if not user_id:
            return

        room = get_workspace_room(user_id)
        leave_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} unsubscribed from workspace updates for user {user_id}")

    @socketio.on('latex_collab:subscribe_document')
    def handle_subscribe_document(data=None):
        if data is None:
            data = {}

        document_id = data.get('document_id')
        if not document_id:
            emit('latex_collab:error', {'error': 'document_id is required'})
            return

        room = get_document_room(document_id)
        join_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} subscribed to commit updates for document {document_id}")
        emit('latex_collab:subscribed_document', {'document_id': document_id, 'room': room})

    @socketio.on('latex_collab:unsubscribe_document')
    def handle_unsubscribe_document(data=None):
        if data is None:
            data = {}

        document_id = data.get('document_id')
        if not document_id:
            return

        room = get_document_room(document_id)
        leave_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} unsubscribed from commit updates for document {document_id}")

    @socketio.on('latex_collab:subscribe_workspace')
    def handle_subscribe_workspace(data=None):
        if data is None:
            data = {}

        workspace_id = data.get('workspace_id')
        if not workspace_id:
            emit('latex_collab:error', {'error': 'workspace_id is required'})
            return

        room = get_workspace_updates_room(workspace_id)
        join_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} subscribed to workspace updates for workspace {workspace_id}")
        emit('latex_collab:subscribed_workspace', {'workspace_id': workspace_id, 'room': room})

    @socketio.on('latex_collab:unsubscribe_workspace')
    def handle_unsubscribe_workspace(data=None):
        if data is None:
            data = {}

        workspace_id = data.get('workspace_id')
        if not workspace_id:
            return

        room = get_workspace_updates_room(workspace_id)
        leave_room(room)
        logger.info(f"[LaTeX Collab] Client {request.sid} unsubscribed from workspace updates for workspace {workspace_id}")

    logger.info("[LaTeX Collab] Socket events registered")


def emit_workspace_shared(socketio, user_id: int, workspace: dict):
    """Emit a workspace-shared event to the user."""
    try:
        room = get_workspace_room(user_id)
        socketio.emit('latex_collab:workspace_shared', {'workspace': workspace}, room=room)
    except Exception as exc:
        logger.error(f"[LaTeX Collab] Failed to emit workspace_shared to user {user_id}: {exc}")


def emit_commit_created(socketio, document_id: int, commit: dict):
    """Emit a commit-created event to all subscribers of a document."""
    try:
        room = get_document_room(document_id)
        socketio.emit('latex_collab:commit_created', {'document_id': document_id, 'commit': commit}, room=room)
    except Exception as exc:
        logger.error(f"[LaTeX Collab] Failed to emit commit_created for document {document_id}: {exc}")


def emit_compile_status(socketio, workspace_id: int, job: dict):
    """Emit a compile status update to all subscribers of a workspace."""
    try:
        room = get_workspace_updates_room(workspace_id)
        socketio.emit('latex_collab:compile_status', {'workspace_id': workspace_id, 'job': job}, room=room)
        logger.debug(f"[LaTeX Collab] Emitted compile_status for workspace {workspace_id}: {job.get('status')}")
    except Exception as exc:
        logger.error(f"[LaTeX Collab] Failed to emit compile_status for workspace {workspace_id}: {exc}")


def emit_comment_changed(socketio, document_id: int, action: str, comment: dict = None):
    """
    Emit a comment-changed event to all subscribers of a document.

    Args:
        socketio: SocketIO instance
        document_id: The document ID
        action: 'created', 'updated', or 'deleted'
        comment: Comment data dict (optional for 'deleted')
    """
    try:
        room = get_document_room(document_id)
        payload = {
            'document_id': document_id,
            'action': action
        }
        if comment:
            payload['comment'] = comment
        socketio.emit('latex_collab:comment_changed', payload, room=room)
        logger.debug(f"[LaTeX Collab] Emitted comment_changed ({action}) for document {document_id}")
    except Exception as exc:
        logger.error(f"[LaTeX Collab] Failed to emit comment_changed for document {document_id}: {exc}")


def emit_workspace_comment_changed(socketio, workspace_id: int, action: str, comment: dict = None):
    """
    Emit a comment-changed event to all subscribers of a workspace.

    Used for global/workspace-wide comments panel.

    Args:
        socketio: SocketIO instance
        workspace_id: The workspace ID
        action: 'created', 'updated', 'deleted', or 'reply_created'
        comment: Comment data dict (optional for 'deleted')
    """
    try:
        room = get_workspace_updates_room(workspace_id)
        payload = {
            'workspace_id': workspace_id,
            'action': action
        }
        if comment:
            payload['comment'] = comment
        socketio.emit('latex_collab:workspace_comment_changed', payload, room=room)
        logger.debug(f"[LaTeX Collab] Emitted workspace_comment_changed ({action}) for workspace {workspace_id}")
    except Exception as exc:
        logger.error(f"[LaTeX Collab] Failed to emit workspace_comment_changed for workspace {workspace_id}: {exc}")
