"""LaTeX compilation helpers for LaTeX Collab."""

from __future__ import annotations

import os
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexDocument,
    LatexAsset,
    LatexCompileJob,
    LatexCommit,
    LatexNodeType,
)


class LatexCompileError(RuntimeError):
    pass


def _doc_path(doc_id: int, docs_by_id: dict[int, LatexDocument], cache: dict[int, str]) -> str:
    if doc_id in cache:
        return cache[doc_id]
    doc = docs_by_id.get(doc_id)
    if not doc:
        return ""
    if doc.parent_id:
        parent_path = _doc_path(doc.parent_id, docs_by_id, cache)
        path = f"{parent_path}/{doc.title}" if parent_path else doc.title
    else:
        path = doc.title
    cache[doc_id] = path
    return path


def _safe_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/").strip()
    normalized = os.path.normpath(normalized)
    if normalized.startswith("..") or os.path.isabs(normalized):
        raise LatexCompileError("Invalid path in workspace snapshot")
    return normalized


def build_workspace_snapshot(workspace_id: int) -> dict:
    workspace = LatexWorkspace.query.get(workspace_id)
    if not workspace:
        raise LatexCompileError("Workspace not found")

    docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .order_by(LatexDocument.parent_id.asc(), LatexDocument.order_index.asc(), LatexDocument.id.asc())
        .all()
    )
    docs_by_id = {d.id: d for d in docs}
    cache: dict[int, str] = {}

    nodes = []
    for doc in docs:
        node_type = doc.node_type.value if hasattr(doc.node_type, "value") else str(doc.node_type)
        path = _doc_path(doc.id, docs_by_id, cache)
        nodes.append({
            "id": doc.id,
            "path": path,
            "title": doc.title,
            "node_type": node_type,
            "asset_id": doc.asset_id,
            "content_text": doc.content_text,
        })

    return {
        "workspace_id": workspace_id,
        "main_document_id": workspace.main_document_id,
        "nodes": nodes,
        "created_at": datetime.utcnow().isoformat(),
    }


def _pick_main_tex(snapshot: dict) -> Optional[str]:
    nodes = snapshot.get("nodes") or []
    nodes_by_id = {n.get("id"): n for n in nodes}
    main_id = snapshot.get("main_document_id")
    if main_id:
        node = nodes_by_id.get(main_id)
        if node and node.get("node_type") == "file":
            path = node.get("path") or ""
            if path.lower().endswith(".tex"):
                return path

    # Fallback to main.tex if present
    for node in nodes:
        path = (node.get("path") or "").lower()
        if node.get("node_type") == "file" and path.endswith("/main.tex"):
            return node.get("path")
        if node.get("node_type") == "file" and path == "main.tex":
            return node.get("path")

    # Last fallback: first tex file
    for node in nodes:
        path = node.get("path") or ""
        if node.get("node_type") == "file" and path.lower().endswith(".tex"):
            return path

    return None


def _materialize_snapshot(snapshot: dict, base_dir: str) -> None:
    nodes = snapshot.get("nodes") or []
    for node in nodes:
        path = node.get("path") or ""
        if not path:
            continue
        rel_path = _safe_relative_path(path)
        target_path = Path(base_dir) / rel_path

        node_type = node.get("node_type")
        if node_type == "folder":
            target_path.mkdir(parents=True, exist_ok=True)
            continue

        target_path.parent.mkdir(parents=True, exist_ok=True)
        asset_id = node.get("asset_id")
        if asset_id:
            asset = LatexAsset.query.get(int(asset_id))
            if not asset:
                raise LatexCompileError(f"Asset {asset_id} missing for {path}")
            target_path.write_bytes(asset.data)
        else:
            content = node.get("content_text") or ""
            target_path.write_text(content, encoding="utf-8")


def _read_log(log_path: Path, fallback: str) -> str:
    if log_path.exists():
        try:
            return log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return fallback
    return fallback


def _clear_previous_pdfs(workspace_id: int, keep_job_id: int) -> None:
    (
        LatexCompileJob.query
        .filter(LatexCompileJob.workspace_id == workspace_id, LatexCompileJob.id != keep_job_id)
        .update({LatexCompileJob.pdf_blob: None, LatexCompileJob.synctex_blob: None})
    )


def run_compile_job(job_id: int) -> None:
    job = LatexCompileJob.query.get(job_id)
    if not job:
        return

    workspace = LatexWorkspace.query.get(job.workspace_id)
    if not workspace:
        job.status = "failed"
        job.error_message = "Workspace not found"
        job.finished_at = datetime.utcnow()
        db.session.commit()
        return

    job.status = "running"
    job.started_at = datetime.utcnow()
    job.error_message = None
    db.session.commit()

    snapshot = None
    if job.commit_id:
        commit = LatexCommit.query.get(job.commit_id)
        if commit and commit.workspace_snapshot:
            snapshot = commit.workspace_snapshot
    if not snapshot:
        try:
            snapshot = build_workspace_snapshot(workspace.id)
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            job.finished_at = datetime.utcnow()
            db.session.commit()
            return

    main_path = _pick_main_tex(snapshot)
    if not main_path:
        job.status = "failed"
        job.error_message = "No main .tex file found"
        job.finished_at = datetime.utcnow()
        db.session.commit()
        return

    try:
        with tempfile.TemporaryDirectory(prefix=f"latex_ws_{workspace.id}_") as tmpdir:
            _materialize_snapshot(snapshot, tmpdir)

            rel_main = _safe_relative_path(main_path)
            cmd = [
                "latexmk",
                "-pdf",
                "-bibtex",
                "-interaction=nonstopmode",
                "-file-line-error",
                "-synctex=1",
                rel_main,
            ]

            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )

            main_stem = os.path.splitext(rel_main)[0]
            pdf_path = Path(tmpdir) / f"{main_stem}.pdf"
            synctex_path = Path(tmpdir) / f"{main_stem}.synctex.gz"
            log_path = Path(tmpdir) / f"{main_stem}.log"

            output = proc.stdout or ""
            job.log_text = _read_log(log_path, output)

            # Check if PDF was created - latexmk may return non-zero for warnings
            if not pdf_path.exists():
                job.status = "failed"
                job.error_message = "LaTeX compile failed - no PDF generated"
                job.finished_at = datetime.utcnow()
                db.session.commit()
                return

            job.pdf_blob = pdf_path.read_bytes()
            job.synctex_blob = synctex_path.read_bytes() if synctex_path.exists() else None
            job.status = "success"
            job.finished_at = datetime.utcnow()
            db.session.commit()

            _clear_previous_pdfs(workspace.id, job.id)
            workspace.latest_compile_job_id = job.id
            db.session.commit()

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.finished_at = datetime.utcnow()
        db.session.commit()


def _snapshot_for_job(job: LatexCompileJob) -> dict:
    if job.commit_id:
        commit = LatexCommit.query.get(job.commit_id)
        if commit and commit.workspace_snapshot:
            return commit.workspace_snapshot
    return build_workspace_snapshot(job.workspace_id)


def _normalize_path(path: str) -> str:
    if not path:
        return ""
    normalized = path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def _parse_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_synctex_view(output: str) -> dict:
    page = None
    x_val = None
    y_val = None
    h_val = None
    v_val = None
    width = None
    height = None

    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Page:"):
            try:
                page = int(line.split(":", 1)[1].strip())
            except ValueError:
                page = None
            continue
        if line.startswith("x:"):
            x_val = _parse_float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("y:"):
            y_val = _parse_float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("h:"):
            h_val = _parse_float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("v:"):
            v_val = _parse_float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("W:") or line.lower().startswith("width:"):
            width = _parse_float(line.split(":", 1)[1].strip())
            continue
        if line.startswith("H:") or line.lower().startswith("height:"):
            height = _parse_float(line.split(":", 1)[1].strip())
            continue

    if x_val is None and h_val is not None:
        x_val = h_val
    if y_val is None and v_val is not None:
        y_val = v_val

    if page is None or x_val is None or y_val is None:
        raise LatexCompileError("SyncTeX view produced no location")

    return {
        "page": page,
        "x": x_val,
        "y": y_val,
        "h": h_val,
        "v": v_val,
        "width": width,
        "height": height,
    }


def _parse_synctex_edit(output: str) -> dict:
    for raw in output.splitlines():
        line = raw.strip()
        if not line.startswith("Input:"):
            continue
        payload = line[len("Input:"):].strip()
        parts = payload.split(":", 2)
        if len(parts) < 3:
            continue
        try:
            line_no = int(parts[0])
        except ValueError:
            line_no = None
        try:
            column_no = int(parts[1])
        except ValueError:
            column_no = None
        path = parts[2].strip()
        return {
            "line": line_no,
            "column": column_no,
            "path": path,
        }
    raise LatexCompileError("SyncTeX edit produced no source location")


def _write_job_artifacts(tmpdir: str, main_path: str, job: LatexCompileJob) -> tuple[str, str]:
    rel_main = _safe_relative_path(main_path)
    main_stem = os.path.splitext(rel_main)[0]
    pdf_path = Path(tmpdir) / f"{main_stem}.pdf"
    synctex_path = Path(tmpdir) / f"{main_stem}.synctex.gz"

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    if not job.pdf_blob or not job.synctex_blob:
        raise LatexCompileError("Compile job has no PDF or SyncTeX data")

    pdf_path.write_bytes(job.pdf_blob)
    synctex_path.write_bytes(job.synctex_blob)

    rel_pdf = f"{main_stem}.pdf"
    return rel_main, rel_pdf


def _find_node(snapshot: dict, document_id: int) -> Optional[dict]:
    for node in snapshot.get("nodes", []):
        if node.get("id") == document_id:
            return node
    return None


def _find_node_by_path(snapshot: dict, path: str) -> Optional[dict]:
    normalized = _normalize_path(path)
    if not normalized:
        return None
    for node in snapshot.get("nodes", []):
        node_path = _normalize_path(node.get("path") or "")
        if node_path == normalized:
            return node
    return None


def synctex_forward_search(job_id: int, document_id: int, line: int, column: int = 1) -> dict:
    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise LatexCompileError("Compile job not found")

    snapshot = _snapshot_for_job(job)
    node = _find_node(snapshot, document_id)
    if not node:
        raise LatexCompileError("Document not found in snapshot")
    if node.get("node_type") != "file" or node.get("asset_id"):
        raise LatexCompileError("Document is not a text file")

    doc_path = node.get("path")
    if not doc_path:
        raise LatexCompileError("Document path missing")

    main_path = _pick_main_tex(snapshot)
    if not main_path:
        raise LatexCompileError("No main tex file found for SyncTeX")

    with tempfile.TemporaryDirectory(prefix=f"latex_synctex_{job.workspace_id}_") as tmpdir:
        _materialize_snapshot(snapshot, tmpdir)
        _write_job_artifacts(tmpdir, main_path, job)

        rel_doc = _safe_relative_path(doc_path)
        rel_main = _safe_relative_path(main_path)
        rel_pdf = f"{os.path.splitext(rel_main)[0]}.pdf"

        cmd = [
            "synctex",
            "view",
            "-i",
            f"{line}:{column}:{rel_doc}",
            "-o",
            rel_pdf,
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=6,
            )
        except FileNotFoundError as exc:
            raise LatexCompileError("synctex is not available") from exc

        output = proc.stdout or ""
        if proc.returncode != 0:
            raise LatexCompileError(output.strip() or "SyncTeX forward search failed")

        return _parse_synctex_view(output)


def synctex_inverse_search(job_id: int, page: int, x: float, y: float) -> dict:
    job = LatexCompileJob.query.get(job_id)
    if not job:
        raise LatexCompileError("Compile job not found")

    snapshot = _snapshot_for_job(job)
    main_path = _pick_main_tex(snapshot)
    if not main_path:
        raise LatexCompileError("No main tex file found for SyncTeX")

    with tempfile.TemporaryDirectory(prefix=f"latex_synctex_{job.workspace_id}_") as tmpdir:
        _materialize_snapshot(snapshot, tmpdir)
        _write_job_artifacts(tmpdir, main_path, job)

        rel_main = _safe_relative_path(main_path)
        rel_pdf = f"{os.path.splitext(rel_main)[0]}.pdf"

        cmd = [
            "synctex",
            "edit",
            "-o",
            f"{page}:{x}:{y}:{rel_pdf}",
        ]

        try:
            proc = subprocess.run(
                cmd,
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=6,
            )
        except FileNotFoundError as exc:
            raise LatexCompileError("synctex is not available") from exc

        output = proc.stdout or ""
        if proc.returncode != 0:
            raise LatexCompileError(output.strip() or "SyncTeX inverse search failed")

        result = _parse_synctex_edit(output)
        path = result.get("path") or ""
        normalized = path.replace("\\", "/")
        if os.path.isabs(normalized):
            try:
                normalized = os.path.relpath(normalized, tmpdir)
            except ValueError:
                normalized = normalized
        normalized = _normalize_path(normalized)

        node = _find_node_by_path(snapshot, normalized)
        if not node:
            result["document_id"] = None
        else:
            result["document_id"] = node.get("id")
        result["path"] = normalized
        return result
