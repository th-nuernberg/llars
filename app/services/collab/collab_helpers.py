# collab_helpers.py
"""
Generic helper functions for collaborative document workspaces (LaTeX/Markdown).
Provides access control, dict conversion, and ordering utilities.

This module provides parametrized functions that work with both LaTeX and Markdown
collab systems by accepting model classes as parameters.
"""

from __future__ import annotations

from typing import Optional, Type, TypeVar, Any

from db.database import db
from decorators.error_handler import ValidationError
# Import directly from submodule to avoid circular import with __init__.py
from services.collab.collab_access_service import CollabAccessService


# Type vars for generic model parameters
TWorkspace = TypeVar('TWorkspace')
TDocument = TypeVar('TDocument')
TMember = TypeVar('TMember')


# ============================================================================
# Access Control Helpers (delegate to CollabAccessService)
# ============================================================================

def is_admin(username: Optional[str]) -> bool:
    """Check if user has admin privileges."""
    return CollabAccessService.is_admin(username)


def require_workspace_access(
    workspace: TWorkspace,
    username: str,
    member_model: Type[TMember]
) -> None:
    """Verify user has access to workspace (owner, member, or admin)."""
    CollabAccessService.require_workspace_access(
        workspace, username, member_model=member_model
    )


def require_workspace_manage(workspace: TWorkspace, username: str) -> None:
    """Verify user can manage workspace (owner or admin only)."""
    CollabAccessService.require_workspace_manage(workspace, username)


def require_document_access(
    document: TDocument,
    username: str,
    member_model: Type[TMember]
) -> None:
    """Verify user has access to document via its workspace."""
    CollabAccessService.require_document_access(
        document, username, member_model=member_model
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

def document_to_dict(
    doc: TDocument,
    include_asset: bool = False,
    include_zotero: bool = False
) -> dict:
    """
    Convert a document model to API response dict.

    Works with both LatexDocument and MarkdownDocument.

    Args:
        doc: Document model instance
        include_asset: Include asset_id field (LaTeX only)
        include_zotero: Include is_zotero_managed field (LaTeX only)

    Returns:
        Dict representation for API response
    """
    result = {
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

    # LaTeX-specific fields
    if include_asset and hasattr(doc, "asset_id"):
        result["asset_id"] = doc.asset_id

    if include_zotero and hasattr(doc, "zotero_library_link"):
        result["is_zotero_managed"] = doc.zotero_library_link is not None

    return result


def workspace_to_dict(
    ws: TWorkspace,
    include_compile: bool = False
) -> dict:
    """
    Convert a workspace model to API response dict.

    Works with both LatexWorkspace and MarkdownWorkspace.

    Args:
        ws: Workspace model instance
        include_compile: Include compile-related fields (LaTeX only)

    Returns:
        Dict representation for API response
    """
    result = {
        "id": ws.id,
        "name": ws.name,
        "owner_username": ws.owner_username,
        "visibility": ws.visibility.value if hasattr(ws.visibility, "value") else str(ws.visibility),
        "updated_at": ws.updated_at.isoformat() if ws.updated_at else None,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }

    # LaTeX-specific fields
    if include_compile:
        if hasattr(ws, "main_document_id"):
            result["main_document_id"] = ws.main_document_id
        if hasattr(ws, "latest_compile_job_id"):
            result["latest_compile_job_id"] = ws.latest_compile_job_id

    return result


# ============================================================================
# Ordering Helpers
# ============================================================================

def get_next_order_index(
    document_model: Type[TDocument],
    workspace_id: int,
    parent_id: Optional[int]
) -> int:
    """
    Get the next order_index for a new document in a folder.

    Args:
        document_model: The document model class (LatexDocument or MarkdownDocument)
        workspace_id: Workspace ID
        parent_id: Parent folder ID (None for root)

    Returns:
        Next available order_index
    """
    q = document_model.query.filter_by(workspace_id=workspace_id, parent_id=parent_id)
    max_idx = q.with_entities(db.func.max(document_model.order_index)).scalar()
    return int(max_idx + 1) if max_idx is not None else 0


def resequence_children(
    document_model: Type[TDocument],
    workspace_id: int,
    parent_id: Optional[int]
) -> None:
    """
    Resequence all children of a folder to have consecutive order_index values.

    Args:
        document_model: The document model class
        workspace_id: Workspace ID
        parent_id: Parent folder ID
    """
    siblings = (
        document_model.query
        .filter_by(workspace_id=workspace_id, parent_id=parent_id)
        .order_by(document_model.order_index.asc(), document_model.id.asc())
        .all()
    )
    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx


def insert_into_parent(
    document_model: Type[TDocument],
    node: TDocument,
    new_parent_id: Optional[int],
    new_index: int
) -> None:
    """
    Insert a node into a new parent at a specific index, resequencing siblings.

    Args:
        document_model: The document model class
        node: Document to move
        new_parent_id: Target parent folder ID
        new_index: Target position index
    """
    siblings = (
        document_model.query
        .filter(
            document_model.workspace_id == node.workspace_id,
            document_model.parent_id == new_parent_id,
            document_model.id != node.id,
        )
        .order_by(document_model.order_index.asc(), document_model.id.asc())
        .all()
    )

    new_index = max(0, min(int(new_index), len(siblings)))
    siblings.insert(new_index, node)

    for idx, sibling in enumerate(siblings):
        sibling.order_index = idx
        if sibling.id == node.id:
            sibling.parent_id = new_parent_id


def build_doc_path(
    document_model: Type[TDocument],
    doc: TDocument
) -> str:
    """
    Build full path for a document by traversing parents.

    Args:
        document_model: The document model class
        doc: Document to build path for

    Returns:
        Full path string (e.g., "folder/subfolder/document.tex")
    """
    parts = [doc.title]
    current = doc
    while current.parent_id:
        parent = document_model.query.get(current.parent_id)
        if not parent:
            break
        parts.insert(0, parent.title)
        current = parent
    return "/".join(parts)
