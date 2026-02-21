# latex_commit_routes.py
"""
LaTeX Collab Commit API Routes.
Handles version control: commits, baselines, rollback, and change tracking.
"""

from datetime import datetime, timezone
from difflib import SequenceMatcher, unified_diff
import logging

from flask import Blueprint, jsonify, request, current_app

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexCommit,
    LatexNodeType,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_workspace_access,
    require_document_access,
    build_doc_path,
)
from services.latex_compile_service import build_workspace_snapshot

logger = logging.getLogger(__name__)

latex_commit_bp = Blueprint("latex_commit", __name__, url_prefix="/api/latex-collab")


def calculate_char_diff(baseline: str, current: str) -> tuple[int, int]:
    """
    Calculate the number of inserted and deleted characters between two strings.

    Uses SequenceMatcher to find matching blocks and calculates the actual
    character-level insertions and deletions.

    Returns:
        tuple: (insertions, deletions) - number of characters added/removed
    """
    if baseline == current:
        return 0, 0

    matcher = SequenceMatcher(None, baseline, current, autojunk=False)
    insertions = 0
    deletions = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            deletions += i2 - i1
            insertions += j2 - j1
        elif tag == 'delete':
            deletions += i2 - i1
        elif tag == 'insert':
            insertions += j2 - j1
        # 'equal' tags don't contribute to changes

    return insertions, deletions


# ============================================================================
# Document Commits
# ============================================================================

@latex_commit_bp.route("/documents/<int:document_id>/commits", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def list_commits(document_id: int):
    """List commits for a document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    commits = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .limit(200)
        .all()
    )

    return jsonify({
        "success": True,
        "commits": [
            {
                "id": c.id,
                "document_id": c.document_id,
                "workspace_id": c.workspace_id,
                "author_username": c.author_username,
                "message": c.message,
                "diff_summary": c.diff_summary,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in commits
        ],
    }), 200


@latex_commit_bp.route("/documents/<int:document_id>/commits/<int:commit_id>", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_commit(document_id: int, commit_id: int):
    """Get a specific commit with full content snapshot."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    commit = LatexCommit.query.filter_by(document_id=document_id, id=commit_id).first()
    if not commit:
        raise NotFoundError("Commit not found")

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "workspace_id": commit.workspace_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 200


@latex_commit_bp.route("/documents/<int:document_id>/commit", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_commit(document_id: int):
    """Create a commit for a single document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    diff_summary = data.get("diff_summary")
    content_snapshot = data.get("content_snapshot")
    workspace_snapshot = data.get("workspace_snapshot")

    if not message:
        raise ValidationError("message is required")

    if not workspace_snapshot:
        workspace_snapshot = build_workspace_snapshot(doc.workspace_id)
    if isinstance(content_snapshot, str) and workspace_snapshot:
        for node in workspace_snapshot.get("nodes", []):
            if node.get("id") == doc.id and node.get("node_type") == "file" and not node.get("asset_id"):
                node["content_text"] = content_snapshot
                break

    commit = LatexCommit(
        workspace_id=doc.workspace_id,
        document_id=doc.id,
        author_username=username,
        message=message,
        diff_summary=diff_summary,
        content_snapshot=content_snapshot,
        workspace_snapshot=workspace_snapshot,
        created_at=datetime.utcnow(),
    )
    db.session.add(commit)
    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_latex_collab import emit_commit_created
            emit_commit_created(socketio, document_id, {
                "id": commit.id,
                "document_id": commit.document_id,
                "workspace_id": commit.workspace_id,
                "author_username": commit.author_username,
                "message": commit.message,
                "diff_summary": commit.diff_summary,
                "content_snapshot": commit.content_snapshot,
                "created_at": commit.created_at.isoformat() if commit.created_at else None,
            })
        except Exception:
            pass

    return jsonify({
        "success": True,
        "commit": {
            "id": commit.id,
            "document_id": commit.document_id,
            "workspace_id": commit.workspace_id,
            "author_username": commit.author_username,
            "message": commit.message,
            "diff_summary": commit.diff_summary,
            "content_snapshot": commit.content_snapshot,
            "created_at": commit.created_at.isoformat() if commit.created_at else None,
        },
    }), 201


# ============================================================================
# Baseline and Rollback
# ============================================================================

@latex_commit_bp.route("/documents/<int:document_id>/baseline", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_baseline(document_id: int):
    """Get the baseline (last committed content) for a document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    latest_commit = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .filter(LatexCommit.content_snapshot.isnot(None))
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )

    if not latest_commit:
        return jsonify({
            "success": True,
            "baseline": None,
            "commit_id": None,
            "message": "No commits with content snapshot found",
        }), 200

    current_content = doc.content_text or ""
    baseline_commit = latest_commit
    if (latest_commit.content_snapshot or "") == "":
        non_empty_commit = (
            LatexCommit.query
            .filter_by(document_id=document_id)
            .filter(LatexCommit.content_snapshot.isnot(None))
            .filter(LatexCommit.content_snapshot != "")
            .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
            .first()
        )
        if non_empty_commit and current_content == (non_empty_commit.content_snapshot or ""):
            baseline_commit = non_empty_commit

    return jsonify({
        "success": True,
        "baseline": baseline_commit.content_snapshot,
        "commit_id": baseline_commit.id,
        "commit_message": baseline_commit.message,
        "commit_author": baseline_commit.author_username,
        "commit_date": baseline_commit.created_at.isoformat() if baseline_commit.created_at else None,
    }), 200


@latex_commit_bp.route("/documents/<int:document_id>/rollback", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def rollback_document(document_id: int):
    """Rollback a document to its last committed state."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")
    require_document_access(doc, username)

    latest_commit = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .filter(LatexCommit.content_snapshot.isnot(None))
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )

    if not latest_commit:
        raise NotFoundError("No commits found for this document - nothing to rollback to")

    data = request.get_json() or {}
    force = bool(data.get("force"))
    non_empty_commit = (
        LatexCommit.query
        .filter_by(document_id=document_id)
        .filter(LatexCommit.content_snapshot.isnot(None))
        .filter(LatexCommit.content_snapshot != "")
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )
    target_commit = latest_commit
    if not force and (latest_commit.content_snapshot or "") == "" and non_empty_commit:
        target_commit = non_empty_commit

    baseline_content = target_commit.content_snapshot or ""
    current_content = doc.content_text or ""

    if baseline_content == "" and current_content and not force:
        raise ConflictError(
            "Rollback baseline is empty. Set force=true to confirm clearing the document.",
            details={
                "requires_force": True,
                "baseline_empty": True,
                "commit_id": target_commit.id,
                "commit_message": target_commit.message,
            },
        )

    if current_content == baseline_content:
        return jsonify({
            "success": True,
            "message": "Document already matches baseline - no rollback needed",
            "rolled_back": False,
        }), 200

    logger.info(f"[LatexCollab] ROLLBACK START - Document {document_id}")
    logger.info(f"[LatexCollab] ROLLBACK - current_content length: {len(current_content)}, preview: {current_content[:100]!r}...")
    logger.info(f"[LatexCollab] ROLLBACK - baseline_content length: {len(baseline_content)}, preview: {baseline_content[:100]!r}...")

    doc.content_text = baseline_content
    # Clear cached Yjs JSON so server reload uses the new baseline text.
    doc.content = None
    doc.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    # Verify the commit worked
    db.session.refresh(doc)
    logger.info(f"[LatexCollab] ROLLBACK COMMITTED - new content_text length: {len(doc.content_text or '')}, content is None: {doc.content is None}")

    logger.info(f"[LatexCollab] Document {document_id} rolled back by {username}")

    return jsonify({
        "success": True,
        "message": "Document rolled back to last committed state",
        "rolled_back": True,
        "commit_id": target_commit.id,
        "commit_message": target_commit.message,
        "commit_author": target_commit.author_username,
        "baseline": baseline_content,
    }), 200


@latex_commit_bp.route("/documents/<int:document_id>/restore", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def restore_document(document_id: int):
    """Restore a soft-deleted document."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")

    if doc.deleted_at is None:
        return jsonify({
            "success": True,
            "message": "Document is not deleted - nothing to restore",
            "restored": False,
        }), 200

    require_document_access(doc, username)

    # Restore the document
    doc.deleted_at = None
    doc.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info(f"[LatexCollab] Document {document_id} restored by {username}")

    return jsonify({
        "success": True,
        "message": "Document restored successfully",
        "restored": True,
        "document": {
            "id": doc.id,
            "title": doc.title,
            "workspace_id": doc.workspace_id,
        },
    }), 200


# ============================================================================
# Workspace-level Changes and Commits
# ============================================================================

@latex_commit_bp.route("/workspaces/<int:workspace_id>/changes", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_workspace_changes(workspace_id: int):
    """Get list of all changed and deleted files in a workspace."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    # Get the latest workspace snapshot to detect renames/moves
    latest_workspace_commit = (
        LatexCommit.query
        .filter_by(workspace_id=workspace_id)
        .filter(LatexCommit.workspace_snapshot.isnot(None))
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )

    # Build lookup from snapshot: doc_id -> {title, path, parent_id}
    snapshot_by_id = {}
    if latest_workspace_commit and latest_workspace_commit.workspace_snapshot:
        snapshot = latest_workspace_commit.workspace_snapshot
        if isinstance(snapshot, dict):
            for node in snapshot.get("nodes", []):
                node_id = node.get("id")
                if node_id:
                    snapshot_by_id[node_id] = {
                        "title": node.get("title"),
                        "path": node.get("path"),
                    }

    # Get all non-deleted text files (no asset_id)
    docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(LatexDocument.node_type == LatexNodeType.file)
        .filter(LatexDocument.asset_id.is_(None))
        .filter(LatexDocument.deleted_at.is_(None))
        .all()
    )

    changed_files = []
    for doc in docs:
        current_content = doc.content_text or ""
        current_path = build_doc_path(doc)

        latest_commit = (
            LatexCommit.query
            .filter_by(document_id=doc.id)
            .filter(LatexCommit.content_snapshot.isnot(None))
            .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
            .first()
        )

        baseline_commit = latest_commit
        if latest_commit and (latest_commit.content_snapshot or "") == "":
            non_empty_commit = (
                LatexCommit.query
                .filter_by(document_id=doc.id)
                .filter(LatexCommit.content_snapshot.isnot(None))
                .filter(LatexCommit.content_snapshot != "")
                .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
                .first()
            )
            if non_empty_commit and current_content == (non_empty_commit.content_snapshot or ""):
                baseline_commit = non_empty_commit

        baseline = baseline_commit.content_snapshot if baseline_commit else ""

        # Check for content changes
        content_changed = current_content != baseline

        # Check for rename/move by comparing with snapshot
        snapshot_info = snapshot_by_id.get(doc.id, {})
        old_title = snapshot_info.get("title")
        old_path = snapshot_info.get("path")

        is_renamed = old_title and old_title != doc.title
        is_moved = old_path and old_path != current_path and not is_renamed

        # Determine status
        # Status codes: M=Modified, A=Added, R=Renamed, V=Moved (German: Verschoben)
        if content_changed or is_renamed or is_moved:
            char_insertions, char_deletions = calculate_char_diff(baseline or "", current_content or "") if content_changed else (0, 0)

            status = "M"  # Default: Modified
            if not baseline_commit:
                status = "A"  # Added (new file)
            elif is_renamed and is_moved:
                status = "RV"  # Renamed and Moved
            elif is_renamed:
                status = "R"  # Renamed
            elif is_moved:
                status = "V"  # Moved (Verschoben)

            changed_files.append({
                "id": doc.id,
                "title": doc.title,
                "path": current_path,
                "insertions": char_insertions,
                "deletions": char_deletions,
                "has_baseline": baseline_commit is not None,
                "baseline_commit_id": baseline_commit.id if baseline_commit else None,
                "status": status,
                "old_title": old_title if is_renamed else None,
                "old_path": old_path if is_moved else None,
            })

    # Get deleted files (soft-deleted with commits)
    deleted_docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(LatexDocument.node_type == LatexNodeType.file)
        .filter(LatexDocument.deleted_at.isnot(None))
        .all()
    )

    deleted_files = []
    for doc in deleted_docs:
        latest_commit = (
            LatexCommit.query
            .filter_by(document_id=doc.id)
            .filter(LatexCommit.content_snapshot.isnot(None))
            .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
            .first()
        )

        baseline_commit = latest_commit
        if latest_commit and (latest_commit.content_snapshot or "") == "":
            non_empty_commit = (
                LatexCommit.query
                .filter_by(document_id=doc.id)
                .filter(LatexCommit.content_snapshot.isnot(None))
                .filter(LatexCommit.content_snapshot != "")
                .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
                .first()
            )
            if non_empty_commit:
                baseline_commit = non_empty_commit

        if baseline_commit:
            # Count characters in the deleted content
            baseline_content = baseline_commit.content_snapshot or ""
            deleted_files.append({
                "id": doc.id,
                "title": doc.title,
                "path": build_doc_path(doc),
                "insertions": 0,
                "deletions": len(baseline_content),
                "has_baseline": True,
                "baseline_commit_id": baseline_commit.id,
                "status": "D",  # Deleted
                "deleted_at": doc.deleted_at.isoformat() if doc.deleted_at else None,
            })

    return jsonify({
        "success": True,
        "changed_files": changed_files,
        "deleted_files": deleted_files,
        "total_changed": len(changed_files),
        "total_deleted": len(deleted_files),
    }), 200


@latex_commit_bp.route("/workspaces/<int:workspace_id>/commit", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def create_workspace_commit(workspace_id: int):
    """Create commits for multiple files at once."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    data = request.get_json() or {}
    message = (data.get("message") or "").strip()
    document_ids = data.get("document_ids", [])

    if not message:
        raise ValidationError("message is required")
    if not document_ids:
        raise ValidationError("document_ids is required (at least one document must be committed)")

    doc_ids = [int(doc_id) for doc_id in document_ids]
    docs = LatexDocument.query.filter(
        LatexDocument.id.in_(doc_ids),
        LatexDocument.workspace_id == workspace_id,
        LatexDocument.node_type == LatexNodeType.file,
        LatexDocument.asset_id.is_(None)
    ).all()

    valid_doc_ids = {d.id for d in docs}
    invalid_ids = [doc_id for doc_id in doc_ids if doc_id not in valid_doc_ids]
    if invalid_ids:
        raise ValidationError(f"Invalid document IDs: {invalid_ids}")

    workspace_snapshot = build_workspace_snapshot(workspace_id)

    created_commits = []
    for doc in docs:
        content_snapshot = doc.content_text or ""

        latest_commit = (
            LatexCommit.query
            .filter_by(document_id=doc.id)
            .filter(LatexCommit.content_snapshot.isnot(None))
            .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
            .first()
        )
        baseline = latest_commit.content_snapshot if latest_commit else ""

        # Calculate character-level diff for commit summary
        insertions, deletions = calculate_char_diff(baseline or "", content_snapshot or "")

        diff_summary = {
            "insertions": insertions,
            "deletions": deletions
        }

        commit = LatexCommit(
            workspace_id=workspace_id,
            document_id=doc.id,
            author_username=username,
            message=message,
            diff_summary=diff_summary,
            content_snapshot=content_snapshot,
            workspace_snapshot=workspace_snapshot,
            created_at=datetime.utcnow(),
        )
        db.session.add(commit)
        created_commits.append((doc.id, commit))

    db.session.commit()

    socketio = current_app.extensions.get('socketio')
    if socketio:
        try:
            from socketio_handlers.events_latex_collab import emit_commit_created
            for doc_id, commit in created_commits:
                emit_commit_created(socketio, doc_id, {
                    "id": commit.id,
                    "document_id": commit.document_id,
                    "workspace_id": commit.workspace_id,
                    "author_username": commit.author_username,
                    "message": commit.message,
                    "diff_summary": commit.diff_summary,
                    "content_snapshot": commit.content_snapshot,
                    "created_at": commit.created_at.isoformat() if commit.created_at else None,
                })
        except Exception:
            pass

    return jsonify({
        "success": True,
        "commits": [
            {
                "id": commit.id,
                "document_id": commit.document_id,
                "message": commit.message,
            }
            for _, commit in created_commits
        ],
        "total_committed": len(created_commits),
    }), 201


# ============================================================================
# Document Diff
# ============================================================================

@latex_commit_bp.route("/documents/<int:document_id>/diff", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def get_document_diff(document_id: int):
    """Get unified diff for a single document comparing current content to baseline."""
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    doc = LatexDocument.query.get(document_id)
    if not doc:
        raise NotFoundError("Document not found")

    ws = LatexWorkspace.query.get(doc.workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    current_content = doc.content_text or ""
    current_path = build_doc_path(doc)

    # Get baseline from latest commit
    latest_commit = (
        LatexCommit.query
        .filter_by(document_id=doc.id)
        .filter(LatexCommit.content_snapshot.isnot(None))
        .order_by(LatexCommit.created_at.desc(), LatexCommit.id.desc())
        .first()
    )

    baseline = latest_commit.content_snapshot if latest_commit else ""

    # Generate unified diff
    baseline_lines = (baseline or "").splitlines(keepends=True)
    current_lines = current_content.splitlines(keepends=True)

    # Ensure lines end with newline for proper diff formatting
    if baseline_lines and not baseline_lines[-1].endswith('\n'):
        baseline_lines[-1] += '\n'
    if current_lines and not current_lines[-1].endswith('\n'):
        current_lines[-1] += '\n'

    diff_lines = list(unified_diff(
        baseline_lines,
        current_lines,
        fromfile=f"a/{current_path}",
        tofile=f"b/{current_path}",
        lineterm=''
    ))

    # Calculate stats
    insertions, deletions = calculate_char_diff(baseline or "", current_content)

    # Parse diff into structured format for frontend
    hunks = []
    current_hunk = None

    for line in diff_lines:
        if line.startswith('@@'):
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = {
                'header': line,
                'lines': []
            }
        elif current_hunk is not None:
            line_type = 'context'
            if line.startswith('+') and not line.startswith('+++'):
                line_type = 'addition'
            elif line.startswith('-') and not line.startswith('---'):
                line_type = 'deletion'
            elif line.startswith('\\'):
                line_type = 'info'

            current_hunk['lines'].append({
                'type': line_type,
                'content': line
            })

    if current_hunk:
        hunks.append(current_hunk)

    return jsonify({
        "success": True,
        "document_id": document_id,
        "title": doc.title,
        "path": current_path,
        "has_changes": current_content != baseline,
        "insertions": insertions,
        "deletions": deletions,
        "baseline_commit_id": latest_commit.id if latest_commit else None,
        "baseline_text": baseline or "",
        "current_text": current_content,
        "diff": {
            "raw": ''.join(diff_lines),
            "hunks": hunks
        }
    }), 200
