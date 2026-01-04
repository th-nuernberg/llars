# latex_document_routes.py
"""
LaTeX Collab Document/Node API Routes.
Handles document tree, CRUD operations, and main document selection.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexAsset,
    LatexNodeType,
    LatexCommit,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_workspace_access,
    require_document_access,
    ensure_safe_title,
    doc_to_dict,
    workspace_to_dict,
    get_next_order_index,
    resequence_children,
    insert_into_parent,
)

latex_document_bp = Blueprint("latex_document", __name__, url_prefix="/api/latex-collab")


# ============================================================================
# Workspace Tree
# ============================================================================

@latex_document_bp.route("/workspaces/<int:workspace_id>/tree", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_workspace_tree(workspace_id: int):
    """Get the full document tree for a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(LatexDocument.deleted_at.is_(None))  # Exclude soft-deleted documents
        .order_by(LatexDocument.parent_id.asc(), LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )

    return jsonify({
        "success": True,
        "workspace": workspace_to_dict(ws),
        "nodes": [doc_to_dict(d) for d in docs],
    }), 200


@latex_document_bp.route("/workspaces/<int:workspace_id>/main", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def set_main_document(workspace_id: int):
    """Set the main document for compilation."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    data = request.get_json() or {}
    document_id = data.get("document_id")
    if not document_id:
        raise ValidationError("document_id is required")

    doc = LatexDocument.query.get(int(document_id))
    if not doc or doc.workspace_id != ws.id:
        raise ValidationError("Invalid document_id")
    if (doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type)) != "file":
        raise ValidationError("document_id must reference a file")

    ws.main_document_id = doc.id
    ws.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"success": True, "workspace": workspace_to_dict(ws)}), 200


# ============================================================================
# Document CRUD
# ============================================================================

@latex_document_bp.route("/documents", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_document():
    """Create a new document or folder."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    data = request.get_json() or {}
    workspace_id = data.get("workspace_id")
    parent_id = data.get("parent_id")
    title = (data.get("title") or "").strip()
    node_type = (data.get("type") or data.get("node_type") or "file").strip().lower()
    asset_id = data.get("asset_id")
    initial_content = data.get("initial_content")

    if not workspace_id:
        raise ValidationError("workspace_id is required")
    if not title:
        raise ValidationError("title is required")
    if node_type not in {"file", "folder"}:
        raise ValidationError("type must be file|folder")
    ensure_safe_title(title)

    ws = LatexWorkspace.query.get(int(workspace_id))
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    if parent_id is not None:
        parent_id = int(parent_id)
        parent = LatexDocument.query.get(parent_id)
        if not parent or parent.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")

    existing = LatexDocument.query.filter_by(workspace_id=ws.id, parent_id=parent_id, title=title).first()
    if existing:
        raise ValidationError("A node with this title already exists in the selected folder")

    asset_ref = None
    if asset_id:
        asset_ref = LatexAsset.query.get(int(asset_id))
        if not asset_ref or asset_ref.workspace_id != ws.id:
            raise ValidationError("Invalid asset_id")

    doc = LatexDocument(
        workspace_id=ws.id,
        parent_id=parent_id,
        node_type=LatexNodeType.folder if node_type == "folder" else LatexNodeType.file,
        title=title,
        order_index=get_next_order_index(ws.id, parent_id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    if asset_ref:
        doc.asset_id = asset_ref.id
    if isinstance(initial_content, str) and node_type == "file" and not asset_ref:
        doc.content_text = initial_content

    db.session.add(doc)
    db.session.flush()

    if node_type == "file" and not asset_ref:
        doc.yjs_doc_id = f"latex_{doc.id}"

    db.session.commit()
    return jsonify({"success": True, "node": doc_to_dict(doc)}), 201


@latex_document_bp.route("/documents/<int:document_id>", methods=["PATCH"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def update_document(document_id: int):
    """Update a document's title, parent, or order."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    new_title = data.get("title")
    new_parent_id = data.get("parent_id", doc.parent_id)
    new_order_index = data.get("order_index")

    if new_parent_id is not None:
        new_parent_id = int(new_parent_id)

    if new_title is not None:
        new_title = str(new_title).strip()
        if not new_title:
            raise ValidationError("title cannot be empty")
        ensure_safe_title(new_title)
        existing = LatexDocument.query.filter_by(
            workspace_id=doc.workspace_id,
            parent_id=new_parent_id,
            title=new_title,
        ).filter(LatexDocument.id != doc.id).first()
        if existing:
            raise ValidationError("A node with this title already exists in the selected folder")
        doc.title = new_title

    old_parent_id = doc.parent_id
    if new_parent_id is not None:
        parent = LatexDocument.query.get(int(new_parent_id))
        if not parent or parent.workspace_id != doc.workspace_id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")
        if parent.id == doc.id:
            raise ValidationError("A node cannot be its own parent")

        cursor = parent
        while cursor and cursor.parent_id is not None:
            if cursor.parent_id == doc.id:
                raise ValidationError("Cannot move a node into its own subtree")
            cursor = LatexDocument.query.get(cursor.parent_id)

    if new_order_index is None:
        if new_parent_id != old_parent_id:
            doc.parent_id = new_parent_id
            doc.order_index = get_next_order_index(doc.workspace_id, new_parent_id)
            resequence_children(doc.workspace_id, old_parent_id)
            resequence_children(doc.workspace_id, new_parent_id)
    else:
        insert_into_parent(doc, new_parent_id, int(new_order_index))
        if new_parent_id != old_parent_id:
            resequence_children(doc.workspace_id, old_parent_id)

    doc.updated_at = datetime.utcnow()
    doc.last_editor_username = username
    db.session.commit()
    return jsonify({"success": True, "node": doc_to_dict(doc)}), 200


@latex_document_bp.route("/documents/<int:document_id>", methods=["DELETE"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def delete_document(document_id: int):
    """Delete a document or folder.

    For files with commits: soft-delete (set deleted_at) to allow restore via git panel.
    For folders or files without commits: hard-delete.
    """
    from datetime import datetime, timezone

    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    workspace_id = doc.workspace_id
    parent_id = doc.parent_id

    # Check if this is a file with commits (can be soft-deleted)
    is_file = doc.node_type == LatexNodeType.file
    has_commits = LatexCommit.query.filter_by(document_id=doc.id).first() is not None

    if is_file and has_commits:
        # Soft-delete: mark as deleted but keep in DB for restore
        doc.deleted_at = datetime.now(timezone.utc)
        # Clear main_document reference if needed
        if doc.workspace and doc.workspace.main_document_id == doc.id:
            doc.workspace.main_document_id = None
        db.session.commit()
        return jsonify({"success": True, "soft_deleted": True}), 200

    # Hard-delete for folders or files without commits
    if doc.workspace and doc.workspace.main_document_id == doc.id:
        doc.workspace.main_document_id = None

    db.session.delete(doc)
    db.session.flush()

    resequence_children(workspace_id, parent_id)
    db.session.commit()
    return jsonify({"success": True}), 200
