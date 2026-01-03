# latex_helpers.py
"""
Helper functions for LaTeX Collab routes.
Provides access control, dict conversion, and ordering utilities.
"""

from datetime import datetime
from typing import Optional

from db.db import db
from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexComment,
    LatexWorkspaceMember,
)
from decorators.error_handler import ValidationError
from services.collab import CollabAccessService


# ============================================================================
# Access Control Helpers (delegate to CollabAccessService)
# ============================================================================

def is_admin(username: Optional[str]) -> bool:
    """Check if user has admin privileges."""
    return CollabAccessService.is_admin(username)


def require_workspace_access(workspace: LatexWorkspace, username: str) -> None:
    """Verify user has access to workspace (owner, member, or admin)."""
    CollabAccessService.require_workspace_access(
        workspace, username, member_model=LatexWorkspaceMember
    )


def require_workspace_manage(workspace: LatexWorkspace, username: str) -> None:
    """Verify user can manage workspace (owner or admin only)."""
    CollabAccessService.require_workspace_manage(workspace, username)


def require_document_access(document: LatexDocument, username: str) -> None:
    """Verify user has access to document via its workspace."""
    CollabAccessService.require_document_access(
        document, username, member_model=LatexWorkspaceMember
    )


def ensure_safe_title(title: str) -> None:
    """Validate title doesn't contain path traversal characters."""
    if "/" in title or "\\" in title:
        raise ValidationError("Dateiname darf keine Pfad-Trenner enthalten")
    if ".." in title:
        raise ValidationError("Dateiname darf keine relativen Pfade enthalten")


# ============================================================================
# Dict Conversion Helpers
# ============================================================================

def doc_to_dict(doc: LatexDocument) -> dict:
    """Convert LatexDocument to API response dict."""
    # Check if this document is managed by Zotero (linked as .bib file)
    is_zotero_managed = hasattr(doc, "zotero_library_link") and doc.zotero_library_link is not None
    return {
        "id": doc.id,
        "workspace_id": doc.workspace_id,
        "parent_id": doc.parent_id,
        "type": doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type),
        "title": doc.title,
        "slug": doc.slug,
        "order_index": doc.order_index,
        "yjs_doc_id": doc.yjs_doc_id,
        "asset_id": doc.asset_id,
        "is_zotero_managed": is_zotero_managed,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def workspace_to_dict(ws: LatexWorkspace) -> dict:
    """Convert LatexWorkspace to API response dict."""
    return {
        "id": ws.id,
        "name": ws.name,
        "owner_username": ws.owner_username,
        "visibility": ws.visibility.value if hasattr(ws.visibility, "value") else str(ws.visibility),
        "main_document_id": ws.main_document_id,
        "latest_compile_job_id": ws.latest_compile_job_id,
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


def comment_to_dict(comment: LatexComment) -> dict:
    """Convert LatexComment to API response dict."""
    return {
        "id": comment.id,
        "document_id": comment.document_id,
        "author_username": comment.author_username,
        "range_start": comment.range_start,
        "range_end": comment.range_end,
        "body": comment.body,
        "resolved_at": comment.resolved_at.isoformat() if comment.resolved_at else None,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


# ============================================================================
# Ordering Helpers
# ============================================================================

def get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    """Get the next order_index for a new document in a folder."""
    q = LatexDocument.query.filter_by(workspace_id=workspace_id, parent_id=parent_id)
    max_idx = q.with_entities(db.func.max(LatexDocument.order_index)).scalar()
    return int(max_idx + 1) if max_idx is not None else 0


def resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    """Resequence all children of a folder to have consecutive order_index values."""
    siblings = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id, parent_id=parent_id)
        .order_by(LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )
    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx


def insert_into_parent(node: LatexDocument, new_parent_id: Optional[int], new_index: int) -> None:
    """Insert a node into a new parent at a specific index, resequencing siblings."""
    siblings = (
        LatexDocument.query
        .filter(
            LatexDocument.workspace_id == node.workspace_id,
            LatexDocument.parent_id == new_parent_id,
            LatexDocument.id != node.id,
        )
        .order_by(LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )

    new_index = max(0, min(int(new_index), len(siblings)))
    siblings.insert(new_index, node)

    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx
        if sibling.id == node.id:
            sibling.parent_id = new_parent_id


def build_doc_path(doc: LatexDocument) -> str:
    """Build full path for a document by traversing parents."""
    parts = [doc.title]
    current = doc
    while current.parent_id:
        parent = LatexDocument.query.get(current.parent_id)
        if not parent:
            break
        parts.insert(0, parent.title)
        current = parent
    return "/".join(parts)
