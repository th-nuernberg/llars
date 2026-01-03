# markdown_collab_helpers.py
"""
Shared helper functions for Markdown Collab routes.
"""

from __future__ import annotations

from typing import Optional

from db.db import db
from db.tables import (
    MarkdownWorkspace,
    MarkdownWorkspaceMember,
    MarkdownDocument,
)
from services.collab import CollabAccessService


# ============================================================================
# Access Control Helpers (delegate to CollabAccessService)
# ============================================================================

def _is_admin(username: Optional[str]) -> bool:
    """Check if user has admin privileges."""
    return CollabAccessService.is_admin(username)


def _require_workspace_access(workspace: MarkdownWorkspace, username: str) -> None:
    """Verify user has access to workspace (owner, member, or admin)."""
    CollabAccessService.require_workspace_access(
        workspace, username, member_model=MarkdownWorkspaceMember
    )


def _require_workspace_manage(workspace: MarkdownWorkspace, username: str) -> None:
    """Verify user can manage workspace (owner or admin only)."""
    CollabAccessService.require_workspace_manage(workspace, username)


def _require_document_access(document: MarkdownDocument, username: str) -> None:
    """Verify user has access to document via its workspace."""
    CollabAccessService.require_document_access(
        document, username, member_model=MarkdownWorkspaceMember
    )


# ============================================================================
# Serialization Helpers
# ============================================================================

def _doc_to_dict(doc: MarkdownDocument) -> dict:
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "parent_id": doc.parent_id,
        "type": doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type),
        "title": doc.title,
        "slug": doc.slug,
        "order_index": doc.order_index,
        "yjs_doc_id": doc.yjs_doc_id,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _workspace_to_dict(ws: MarkdownWorkspace) -> dict:
    return {
        "id": ws.id,
        "name": ws.name,
        "owner_username": ws.owner_username,
        "visibility": ws.visibility.value if hasattr(ws.visibility, "value") else str(ws.visibility),
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


# ============================================================================
# Document Tree Helpers
# ============================================================================

def _get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    q = MarkdownDocument.query.filter_by(workspace_id=workspace_id, parent_id=parent_id)
    max_idx = q.with_entities(db.func.max(MarkdownDocument.order_index)).scalar()
    return int(max_idx + 1) if max_idx is not None else 0


def _resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    siblings = (
        MarkdownDocument.query
        .filter_by(workspace_id=workspace_id, parent_id=parent_id)
        .order_by(MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )
    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx


def _insert_into_parent(node: MarkdownDocument, new_parent_id: Optional[int], new_index: int) -> None:
    siblings = (
        MarkdownDocument.query
        .filter(
            MarkdownDocument.workspace_id == node.workspace_id,
            MarkdownDocument.parent_id == new_parent_id,
            MarkdownDocument.id != node.id,
        )
        .order_by(MarkdownDocument.order_index.asc(), MarkdownDocument.id.asc())
        .all()
    )

    new_index = max(0, min(int(new_index), len(siblings)))
    siblings.insert(new_index, node)

    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx
        if sibling.id == node.id:
            sibling.parent_id = new_parent_id
