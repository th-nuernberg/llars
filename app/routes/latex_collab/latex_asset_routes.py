# latex_asset_routes.py
"""
LaTeX Collab Asset API Routes.
Handles binary file uploads (images, PDFs, etc.) for LaTeX documents.
"""

from datetime import datetime
import hashlib
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexAsset,
    LatexNodeType,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_workspace_access,
    ensure_safe_title,
    doc_to_dict,
    get_next_order_index,
)

latex_asset_bp = Blueprint("latex_asset", __name__, url_prefix="/api/latex-collab")


@latex_asset_bp.route("/workspaces/<int:workspace_id>/assets", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def upload_asset(workspace_id: int):
    """Upload a binary asset (image, PDF, etc.) to a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    file = request.files.get("file")
    if not file:
        raise ValidationError("file is required")

    parent_id = request.form.get("parent_id")
    if parent_id is not None:
        parent_id = int(parent_id)
        parent = LatexDocument.query.get(parent_id)
        if not parent or parent.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if (parent.node_type.value if hasattr(parent.node_type, "value") else str(parent.node_type)) != "folder":
            raise ValidationError("parent_id must reference a folder")

    filename = (file.filename or "").strip()
    if not filename:
        raise ValidationError("filename is required")
    ensure_safe_title(filename)

    existing = LatexDocument.query.filter_by(workspace_id=ws.id, parent_id=parent_id, title=filename).first()
    if existing:
        raise ValidationError("A node with this title already exists in the selected folder")

    data = file.read()
    sha256 = hashlib.sha256(data).hexdigest() if data else None
    asset = LatexAsset(
        workspace_id=ws.id,
        filename=filename,
        mime_type=file.mimetype,
        file_size_bytes=len(data),
        sha256=sha256,
        data=data,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(asset)
    db.session.flush()

    doc = LatexDocument(
        workspace_id=ws.id,
        parent_id=parent_id,
        node_type=LatexNodeType.file,
        title=filename,
        order_index=get_next_order_index(ws.id, parent_id),
        asset_id=asset.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({"success": True, "asset_id": asset.id, "node": doc_to_dict(doc)}), 201


@latex_asset_bp.route("/assets/<int:asset_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_asset(asset_id: int):
    """Download a binary asset."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    asset = LatexAsset.query.get(asset_id)
    if not asset:
        raise NotFoundError("Asset not found")

    ws = LatexWorkspace.query.get(asset.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    return send_file(
        BytesIO(asset.data),
        mimetype=asset.mime_type or "application/octet-stream",
        download_name=asset.filename,
        as_attachment=False,
    )
