# latex_helpers.py
"""
Helper functions for LaTeX Collab routes.

This module provides LaTeX-specific wrappers around the generic collab helpers,
plus LaTeX-only helpers like comment_to_dict.
"""

from typing import Optional

from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexComment,
    LatexWorkspaceMember,
)
from services.collab import (
    CollabAccessService,
    # Generic helpers
    is_admin,
    ensure_safe_title,
    document_to_dict as _generic_doc_to_dict,
    workspace_to_dict as _generic_workspace_to_dict,
    get_next_order_index as _generic_get_next_order_index,
    resequence_children as _generic_resequence_children,
    insert_into_parent as _generic_insert_into_parent,
    build_doc_path as _generic_build_doc_path,
)

# Re-export unchanged helpers
__all__ = [
    'is_admin',
    'ensure_safe_title',
    'require_workspace_access',
    'require_workspace_manage',
    'require_document_access',
    'doc_to_dict',
    'workspace_to_dict',
    'comment_to_dict',
    'get_next_order_index',
    'resequence_children',
    'insert_into_parent',
    'build_doc_path',
]


# ============================================================================
# Access Control Helpers (LaTeX-specific wrappers)
# ============================================================================

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


# ============================================================================
# Dict Conversion Helpers
# ============================================================================

def doc_to_dict(doc: LatexDocument) -> dict:
    """Convert LatexDocument to API response dict."""
    return _generic_doc_to_dict(doc, include_asset=True, include_zotero=True)


def workspace_to_dict(ws: LatexWorkspace) -> dict:
    """Convert LatexWorkspace to API response dict."""
    return _generic_workspace_to_dict(ws, include_compile=True)


def comment_to_dict(comment: LatexComment) -> dict:
    """Convert LatexComment to API response dict (LaTeX-only)."""
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
# Ordering Helpers (LaTeX-specific wrappers)
# ============================================================================

def get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    """Get the next order_index for a new document in a folder."""
    return _generic_get_next_order_index(LatexDocument, workspace_id, parent_id)


def resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    """Resequence all children of a folder to have consecutive order_index values."""
    _generic_resequence_children(LatexDocument, workspace_id, parent_id)


def insert_into_parent(node: LatexDocument, new_parent_id: Optional[int], new_index: int) -> None:
    """Insert a node into a new parent at a specific index, resequencing siblings."""
    _generic_insert_into_parent(LatexDocument, node, new_parent_id, new_index)


def build_doc_path(doc: LatexDocument) -> str:
    """Build full path for a document by traversing parents."""
    return _generic_build_doc_path(LatexDocument, doc)
