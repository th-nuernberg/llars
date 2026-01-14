"""
Collaboration Services Module

Provides shared services for LaTeX and Markdown collaboration features.
"""

from .collab_access_service import CollabAccessService
from .collab_helpers import (
    is_admin,
    require_workspace_access,
    require_workspace_manage,
    require_document_access,
    ensure_safe_title,
    document_to_dict,
    workspace_to_dict,
    get_next_order_index,
    resequence_children,
    insert_into_parent,
    build_doc_path,
)

__all__ = [
    'CollabAccessService',
    # Generic helpers
    'is_admin',
    'require_workspace_access',
    'require_workspace_manage',
    'require_document_access',
    'ensure_safe_title',
    'document_to_dict',
    'workspace_to_dict',
    'get_next_order_index',
    'resequence_children',
    'insert_into_parent',
    'build_doc_path',
]
