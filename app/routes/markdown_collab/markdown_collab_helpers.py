# markdown_collab_helpers.py
"""
Helper functions for Markdown Collab routes.

This module provides Markdown-specific wrappers around the generic collab helpers.
"""

from __future__ import annotations

from typing import Optional

from db.tables import (
    MarkdownWorkspace,
    MarkdownWorkspaceMember,
    MarkdownDocument,
)
from services.collab import (
    CollabAccessService,
    # Generic helpers
    is_admin,
    document_to_dict as _generic_doc_to_dict,
    workspace_to_dict as _generic_workspace_to_dict,
    get_next_order_index as _generic_get_next_order_index,
    resequence_children as _generic_resequence_children,
    insert_into_parent as _generic_insert_into_parent,
)


# ============================================================================
# Access Control Helpers (Markdown-specific wrappers)
# ============================================================================

def _is_admin(username: Optional[str]) -> bool:
    """Check if user has admin privileges."""
    return is_admin(username)


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
    """Convert MarkdownDocument to API response dict."""
    return _generic_doc_to_dict(doc, include_asset=False, include_zotero=False)


def _workspace_to_dict(ws: MarkdownWorkspace) -> dict:
    """Convert MarkdownWorkspace to API response dict."""
    return _generic_workspace_to_dict(ws, include_compile=False)


# ============================================================================
# Document Tree Helpers (Markdown-specific wrappers)
# ============================================================================

def _get_next_order_index(workspace_id: int, parent_id: Optional[int]) -> int:
    """Get the next order_index for a new document in a folder."""
    return _generic_get_next_order_index(MarkdownDocument, workspace_id, parent_id)


def _resequence_children(workspace_id: int, parent_id: Optional[int]) -> None:
    """Resequence all children of a folder to have consecutive order_index values."""
    _generic_resequence_children(MarkdownDocument, workspace_id, parent_id)


def _insert_into_parent(node: MarkdownDocument, new_parent_id: Optional[int], new_index: int) -> None:
    """Insert a node into a new parent at a specific index, resequencing siblings."""
    _generic_insert_into_parent(MarkdownDocument, node, new_parent_id, new_index)
