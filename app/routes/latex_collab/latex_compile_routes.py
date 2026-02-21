# latex_compile_routes.py
"""
LaTeX Collab Compile API Routes.
Handles LaTeX compilation, PDF generation, and SyncTeX bidirectional sync.
"""

from datetime import datetime
from io import BytesIO

from flask import Blueprint, jsonify, request, current_app, send_file

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexCommit,
    LatexCompileJob,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import require_workspace_access
from services.latex_compile_service import (
    run_compile_job,
    synctex_forward_search,
    synctex_inverse_search,
    LatexCompileError,
)

latex_compile_bp = Blueprint("latex_compile", __name__, url_prefix="/api/latex-collab")


# ============================================================================
# Compilation
# ============================================================================

@latex_compile_bp.route("/workspaces/<int:workspace_id>/compile", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def compile_workspace(workspace_id: int):
    """Start a compilation job for a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    data = request.get_json() or {}
    commit_id = data.get("commit_id")
    if commit_id:
        commit = LatexCommit.query.get(int(commit_id))
        if not commit or commit.workspace_id != ws.id:
            raise ValidationError("Invalid commit_id")

    job = LatexCompileJob(
        workspace_id=ws.id,
        commit_id=int(commit_id) if commit_id else None,
        status="queued",
        created_at=datetime.utcnow(),
    )
    db.session.add(job)
    db.session.flush()

    ws.latest_compile_job_id = job.id
    ws.updated_at = datetime.utcnow()
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        app = current_app._get_current_object()
        socketio.start_background_task(_run_compile_background, app, job.id)
    else:
        run_compile_job(job.id)

    return jsonify({
        "success": True,
        "job": {
            "id": job.id,
            "workspace_id": job.workspace_id,
            "commit_id": job.commit_id,
            "status": job.status,
        },
    }), 202


def _run_compile_background(app, job_id: int) -> None:
    """Run compilation in background task."""
    with app.app_context():
        run_compile_job(job_id)


@latex_compile_bp.route("/compile/<int:job_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_compile_job(job_id: int):
    """Get the status of a compile job."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    return jsonify({
        "success": True,
        "job": {
            "id": job.id,
            "workspace_id": job.workspace_id,
            "commit_id": job.commit_id,
            "status": job.status,
            "error_message": job.error_message,
            "log_text": job.log_text,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
            "has_pdf": job.pdf_blob is not None,
            "has_synctex": job.synctex_blob is not None,
        },
    }), 200


# ============================================================================
# SyncTeX (Bidirectional Source/PDF Sync)
# ============================================================================

@latex_compile_bp.route("/compile/<int:job_id>/synctex/forward", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def synctex_forward(job_id: int):
    """
    Forward sync: Source position -> PDF position.
    Given a document, line, and column, find the corresponding PDF page/position.
    """
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    data = request.get_json() or {}
    document_id = data.get("document_id")
    line = data.get("line")
    column = data.get("column", 1)

    if not document_id:
        raise ValidationError("document_id is required")
    if not isinstance(line, int) or line <= 0:
        raise ValidationError("line must be a positive integer")
    if not isinstance(column, int) or column <= 0:
        raise ValidationError("column must be a positive integer")

    if job.status != "success" or not job.pdf_blob or not job.synctex_blob:
        return jsonify({"success": False, "location": None, "error": "SyncTeX data not available"}), 200

    try:
        location = synctex_forward_search(job_id, int(document_id), line, column)
    except LatexCompileError as exc:
        msg = str(exc)
        if "no location" in msg.lower():
            return jsonify({"success": False, "location": None, "error": msg}), 200
        raise ValidationError(msg) from exc

    return jsonify({"success": True, "location": location}), 200


@latex_compile_bp.route("/compile/<int:job_id>/synctex/inverse", methods=["POST"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def synctex_inverse(job_id: int):
    """
    Inverse sync: PDF position -> Source position.
    Given a PDF page and coordinates, find the corresponding source line.
    """
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise NotFoundError("Compile job not found")

    ws = LatexWorkspace.query.get(job.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    data = request.get_json() or {}
    page = data.get("page")
    x = data.get("x")
    y = data.get("y")

    if not isinstance(page, int) or page <= 0:
        raise ValidationError("page must be a positive integer")
    if x is None or y is None:
        raise ValidationError("x and y are required")

    if job.status != "success" or not job.pdf_blob or not job.synctex_blob:
        return jsonify({"success": False, "location": None, "error": "SyncTeX data not available"}), 200

    try:
        location = synctex_inverse_search(job_id, int(page), float(x), float(y))
    except LatexCompileError as exc:
        msg = str(exc)
        if "no source location" in msg.lower() or "no location" in msg.lower():
            return jsonify({"success": False, "location": None, "error": msg}), 200
        raise ValidationError(msg) from exc

    return jsonify({"success": True, "location": location}), 200


# ============================================================================
# PDF Download
# ============================================================================

@latex_compile_bp.route("/workspaces/<int:workspace_id>/pdf", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_latest_pdf(workspace_id: int):
    """Get the latest compiled PDF for a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    job_id = request.args.get("job_id")
    if job_id:
        job = LatexCompileJob.query.get(int(job_id))
        if not job or job.workspace_id != ws.id:
            raise NotFoundError("Compile job not found")
    else:
        job = (
            LatexCompileJob.query
            .filter_by(workspace_id=ws.id)
            .filter(LatexCompileJob.pdf_blob.isnot(None))
            .order_by(LatexCompileJob.finished_at.desc(), LatexCompileJob.id.desc())
            .first()
        )

    if not job or not job.pdf_blob:
        raise NotFoundError("No compiled PDF available")

    return send_file(
        BytesIO(job.pdf_blob),
        mimetype="application/pdf",
        download_name=f"workspace_{ws.id}.pdf",
        as_attachment=False,
    )
