# latex_zip_routes.py
"""
LaTeX Collab ZIP Import/Export API Routes.
Handles workspace export as ZIP and project import from ZIP.
"""

import hashlib
import logging
import os
import zipfile
from datetime import datetime
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file

from auth.auth_utils import AuthUtils
from db.database import db
from db.tables import (
    LatexWorkspace,
    LatexWorkspaceMember,
    LatexDocument,
    LatexAsset,
    LatexNodeType,
    LatexWorkspaceVisibility,
)
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError
from decorators.permission_decorator import require_permission
from routes.latex_collab.latex_helpers import (
    require_workspace_access,
    build_doc_path,
    ensure_safe_title,
    get_next_order_index,
)

logger = logging.getLogger(__name__)

latex_zip_bp = Blueprint("latex_zip", __name__, url_prefix="/api/latex-collab")

# Binary file extensions that should be treated as assets
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
    '.pdf', '.eps', '.ps',
    '.ttf', '.otf', '.woff', '.woff2',
    '.zip', '.tar', '.gz', '.bz2',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.mp3', '.mp4', '.wav', '.avi', '.mov',
}

# Maximum allowed ZIP file size (100 MB)
MAX_ZIP_SIZE = 100 * 1024 * 1024

# Maximum number of files allowed in a ZIP
MAX_ZIP_FILES = 1000


def _is_binary_file(filename: str) -> bool:
    """Check if a file should be treated as binary based on extension."""
    _, ext = os.path.splitext(filename.lower())
    return ext in BINARY_EXTENSIONS


def _guess_mime_type(filename: str) -> str:
    """Guess MIME type from filename extension."""
    ext = os.path.splitext(filename.lower())[1]
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.pdf': 'application/pdf',
        '.eps': 'application/postscript',
        '.ttf': 'font/ttf',
        '.otf': 'font/otf',
        '.woff': 'font/woff',
        '.woff2': 'font/woff2',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.mp3': 'audio/mpeg',
        '.mp4': 'video/mp4',
        '.wav': 'audio/wav',
    }
    return mime_types.get(ext, 'application/octet-stream')


# ============================================================================
# ZIP Export (Download)
# ============================================================================

@latex_zip_bp.route("/workspaces/<int:workspace_id>/export", methods=["GET"])
@require_permission("feature:latex_collab:view")
@handle_api_errors(logger_name="latex_collab")
def export_workspace_zip(workspace_id: int):
    """
    Export a workspace as a ZIP file.

    Downloads the entire workspace structure including all documents and assets.
    The folder structure is preserved in the ZIP file.
    """
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    ws = LatexWorkspace.query.get(workspace_id)
    if not ws:
        raise NotFoundError("Workspace not found")
    require_workspace_access(ws, username)

    # Get all non-deleted documents
    docs = (
        LatexDocument.query
        .filter_by(workspace_id=workspace_id)
        .filter(LatexDocument.deleted_at.is_(None))
        .order_by(LatexDocument.parent_id.asc(), LatexDocument.order_index.asc())
        .all()
    )

    # Build ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for doc in docs:
            if doc.node_type == LatexNodeType.folder:
                # Create empty folder entry
                folder_path = build_doc_path(doc)
                if folder_path:
                    zf.writestr(folder_path + '/', '')
            else:
                # File
                file_path = build_doc_path(doc)
                if not file_path:
                    continue

                if doc.asset_id and doc.asset:
                    # Binary file - use asset data
                    zf.writestr(file_path, doc.asset.data)
                elif doc.content_text is not None:
                    # Text file - use content_text
                    zf.writestr(file_path, doc.content_text.encode('utf-8'))
                else:
                    # Empty text file
                    zf.writestr(file_path, b'')

    zip_buffer.seek(0)

    # Generate filename
    safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in ws.name)
    filename = f"{safe_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        download_name=filename,
        as_attachment=True,
    )


# ============================================================================
# ZIP Import (Upload)
# ============================================================================

@latex_zip_bp.route("/workspaces/import", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def import_workspace_zip():
    """
    Create a new workspace from an uploaded ZIP file.

    The ZIP file structure becomes the document tree.
    Text files (.tex, .bib, .sty, .cls, .txt, etc.) are stored as editable documents.
    Binary files (images, PDFs, etc.) are stored as assets.

    Request:
        - file: ZIP file (multipart/form-data)
        - name: Optional workspace name (defaults to ZIP filename)
        - visibility: Optional visibility (private|team|org, defaults to private)

    Returns:
        - workspace: Created workspace object
    """
    username = AuthUtils.extract_username_without_validation()
    if not username:
        raise ValidationError("Invalid token")

    file = request.files.get("file")
    if not file:
        raise ValidationError("file is required")

    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise ValidationError("File must be a ZIP archive")

    # Read file into memory
    zip_data = file.read()
    if len(zip_data) > MAX_ZIP_SIZE:
        raise ValidationError(f"ZIP file too large (max {MAX_ZIP_SIZE // (1024*1024)} MB)")

    # Parse optional parameters
    name = (request.form.get("name") or "").strip()
    if not name:
        # Use ZIP filename without extension
        name = os.path.splitext(file.filename)[0]
    name = name[:255]  # Limit length

    visibility = (request.form.get("visibility") or "private").strip().lower()
    if visibility not in {"private", "team", "org"}:
        visibility = "private"

    # Open ZIP file
    try:
        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Security check: no absolute paths or parent traversal
            for zip_info in zf.infolist():
                if zip_info.filename.startswith('/') or '..' in zip_info.filename:
                    raise ValidationError("Invalid ZIP structure: contains unsafe paths")

            file_list = [zi for zi in zf.infolist() if not zi.filename.startswith('__MACOSX')]
            if len(file_list) > MAX_ZIP_FILES:
                raise ValidationError(f"ZIP contains too many files (max {MAX_ZIP_FILES})")

            # Create workspace
            ws = LatexWorkspace(
                name=name,
                owner_username=username,
                visibility=LatexWorkspaceVisibility(visibility),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.session.add(ws)
            db.session.flush()

            # Track created folders for parent_id lookup
            folder_map = {}  # path -> document_id

            # First pass: create all folders
            for zip_info in sorted(file_list, key=lambda x: x.filename):
                if zip_info.is_dir():
                    folder_path = zip_info.filename.rstrip('/')
                    _create_folder_recursive(ws.id, folder_path, folder_map)

            # Second pass: create all files
            main_doc_id = None
            for zip_info in file_list:
                if zip_info.is_dir():
                    continue

                file_path = zip_info.filename
                if not file_path or file_path.endswith('/'):
                    continue

                # Get parent folder
                parent_path = os.path.dirname(file_path)
                parent_id = folder_map.get(parent_path) if parent_path else None

                # Ensure parent folders exist (in case ZIP has files without folder entries)
                if parent_path and parent_path not in folder_map:
                    _create_folder_recursive(ws.id, parent_path, folder_map)
                    parent_id = folder_map.get(parent_path)

                # Get filename
                filename = os.path.basename(file_path)
                if not filename:
                    continue

                try:
                    ensure_safe_title(filename)
                except ValidationError:
                    logger.warning(f"Skipping file with invalid name: {filename}")
                    continue

                # Check for duplicates
                existing = LatexDocument.query.filter_by(
                    workspace_id=ws.id, parent_id=parent_id, title=filename
                ).first()
                if existing:
                    logger.warning(f"Skipping duplicate file: {file_path}")
                    continue

                # Read file content
                try:
                    file_data = zf.read(zip_info.filename)
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    continue

                # Create document
                doc = LatexDocument(
                    workspace_id=ws.id,
                    parent_id=parent_id,
                    node_type=LatexNodeType.file,
                    title=filename,
                    order_index=get_next_order_index(ws.id, parent_id),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                if _is_binary_file(filename):
                    # Binary file - create asset
                    sha256 = hashlib.sha256(file_data).hexdigest() if file_data else None
                    asset = LatexAsset(
                        workspace_id=ws.id,
                        filename=filename,
                        mime_type=_guess_mime_type(filename),
                        file_size_bytes=len(file_data),
                        sha256=sha256,
                        data=file_data,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.session.add(asset)
                    db.session.flush()
                    doc.asset_id = asset.id
                else:
                    # Text file - try to decode as UTF-8
                    try:
                        doc.content_text = file_data.decode('utf-8')
                    except UnicodeDecodeError:
                        # Try latin-1 as fallback
                        try:
                            doc.content_text = file_data.decode('latin-1')
                        except UnicodeDecodeError:
                            doc.content_text = ""

                db.session.add(doc)
                db.session.flush()

                # Set yjs_doc_id for text files
                if not doc.asset_id:
                    doc.yjs_doc_id = f"latex_{doc.id}"

                # Track main.tex as main document
                if filename.lower() == 'main.tex' and parent_id is None:
                    main_doc_id = doc.id

            # Set main document
            if main_doc_id:
                ws.main_document_id = main_doc_id
            else:
                # Look for any .tex file at root level
                root_tex = LatexDocument.query.filter_by(
                    workspace_id=ws.id, parent_id=None
                ).filter(
                    LatexDocument.title.like('%.tex'),
                    LatexDocument.asset_id.is_(None)
                ).first()
                if root_tex:
                    ws.main_document_id = root_tex.id

            db.session.commit()

            return jsonify({
                "success": True,
                "workspace": {
                    "id": ws.id,
                    "name": ws.name,
                    "owner_username": ws.owner_username,
                    "visibility": ws.visibility.value,
                    "main_document_id": ws.main_document_id,
                    "created_at": ws.created_at.isoformat(),
                    "updated_at": ws.updated_at.isoformat(),
                }
            }), 201

    except zipfile.BadZipFile:
        raise ValidationError("Invalid ZIP file")


def _create_folder_recursive(workspace_id: int, folder_path: str, folder_map: dict) -> int:
    """Create a folder and all parent folders if they don't exist.

    Args:
        workspace_id: The workspace ID
        folder_path: Full path like "folder1/folder2/folder3"
        folder_map: Dict mapping paths to document IDs (updated in place)

    Returns:
        Document ID of the created/existing folder
    """
    if folder_path in folder_map:
        return folder_map[folder_path]

    parts = folder_path.split('/')
    current_path = ""
    parent_id = None

    for part in parts:
        if not part:
            continue

        current_path = f"{current_path}/{part}".lstrip('/')

        if current_path in folder_map:
            parent_id = folder_map[current_path]
            continue

        # Check if already exists
        existing = LatexDocument.query.filter_by(
            workspace_id=workspace_id,
            parent_id=parent_id,
            title=part,
            node_type=LatexNodeType.folder
        ).first()

        if existing:
            folder_map[current_path] = existing.id
            parent_id = existing.id
            continue

        # Create folder
        try:
            ensure_safe_title(part)
        except ValidationError:
            logger.warning(f"Skipping folder with invalid name: {part}")
            return parent_id

        folder = LatexDocument(
            workspace_id=workspace_id,
            parent_id=parent_id,
            node_type=LatexNodeType.folder,
            title=part,
            order_index=get_next_order_index(workspace_id, parent_id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(folder)
        db.session.flush()

        folder_map[current_path] = folder.id
        parent_id = folder.id

    return parent_id


@latex_zip_bp.route("/workspaces/<int:workspace_id>/import", methods=["POST"])
@require_permission("feature:latex_collab:edit")
@handle_api_errors(logger_name="latex_collab")
def import_to_workspace_zip(workspace_id: int):
    """
    Import a ZIP file into an existing workspace.

    Adds files from the ZIP to the workspace. Existing files with the same path
    are NOT overwritten - they are skipped.

    Request:
        - file: ZIP file (multipart/form-data)
        - parent_id: Optional parent folder ID (import into subfolder)

    Returns:
        - imported_count: Number of files imported
        - skipped_count: Number of files skipped (already exist)
    """
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

    if not file.filename or not file.filename.lower().endswith('.zip'):
        raise ValidationError("File must be a ZIP archive")

    # Optional parent folder
    parent_id = request.form.get("parent_id")
    base_parent_id = None
    if parent_id:
        base_parent_id = int(parent_id)
        parent_doc = LatexDocument.query.get(base_parent_id)
        if not parent_doc or parent_doc.workspace_id != ws.id:
            raise ValidationError("Invalid parent_id")
        if parent_doc.node_type != LatexNodeType.folder:
            raise ValidationError("parent_id must be a folder")

    # Read file into memory
    zip_data = file.read()
    if len(zip_data) > MAX_ZIP_SIZE:
        raise ValidationError(f"ZIP file too large (max {MAX_ZIP_SIZE // (1024*1024)} MB)")

    imported_count = 0
    skipped_count = 0

    try:
        zip_buffer = BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zf:
            # Security check
            for zip_info in zf.infolist():
                if zip_info.filename.startswith('/') or '..' in zip_info.filename:
                    raise ValidationError("Invalid ZIP structure: contains unsafe paths")

            file_list = [zi for zi in zf.infolist() if not zi.filename.startswith('__MACOSX')]
            if len(file_list) > MAX_ZIP_FILES:
                raise ValidationError(f"ZIP contains too many files (max {MAX_ZIP_FILES})")

            # Track created folders for parent_id lookup
            # Initialize with base_parent_id if provided
            folder_map = {}

            # First pass: create folders
            for zip_info in sorted(file_list, key=lambda x: x.filename):
                if zip_info.is_dir():
                    folder_path = zip_info.filename.rstrip('/')
                    _create_folder_recursive_with_base(
                        ws.id, folder_path, folder_map, base_parent_id
                    )

            # Second pass: create files
            for zip_info in file_list:
                if zip_info.is_dir():
                    continue

                file_path = zip_info.filename
                if not file_path or file_path.endswith('/'):
                    continue

                # Get parent folder
                parent_path = os.path.dirname(file_path)
                parent_id_for_file = folder_map.get(parent_path, base_parent_id) if parent_path else base_parent_id

                # Ensure parent folders exist
                if parent_path and parent_path not in folder_map:
                    _create_folder_recursive_with_base(ws.id, parent_path, folder_map, base_parent_id)
                    parent_id_for_file = folder_map.get(parent_path, base_parent_id)

                filename = os.path.basename(file_path)
                if not filename:
                    continue

                try:
                    ensure_safe_title(filename)
                except ValidationError:
                    skipped_count += 1
                    continue

                # Check for duplicates
                existing = LatexDocument.query.filter_by(
                    workspace_id=ws.id, parent_id=parent_id_for_file, title=filename
                ).first()
                if existing:
                    skipped_count += 1
                    continue

                # Read file content
                try:
                    file_data = zf.read(zip_info.filename)
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    skipped_count += 1
                    continue

                # Create document
                doc = LatexDocument(
                    workspace_id=ws.id,
                    parent_id=parent_id_for_file,
                    node_type=LatexNodeType.file,
                    title=filename,
                    order_index=get_next_order_index(ws.id, parent_id_for_file),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                if _is_binary_file(filename):
                    sha256 = hashlib.sha256(file_data).hexdigest() if file_data else None
                    asset = LatexAsset(
                        workspace_id=ws.id,
                        filename=filename,
                        mime_type=_guess_mime_type(filename),
                        file_size_bytes=len(file_data),
                        sha256=sha256,
                        data=file_data,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )
                    db.session.add(asset)
                    db.session.flush()
                    doc.asset_id = asset.id
                else:
                    try:
                        doc.content_text = file_data.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            doc.content_text = file_data.decode('latin-1')
                        except UnicodeDecodeError:
                            doc.content_text = ""

                db.session.add(doc)
                db.session.flush()

                if not doc.asset_id:
                    doc.yjs_doc_id = f"latex_{doc.id}"

                imported_count += 1

            db.session.commit()

            return jsonify({
                "success": True,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
            }), 200

    except zipfile.BadZipFile:
        raise ValidationError("Invalid ZIP file")


def _create_folder_recursive_with_base(
    workspace_id: int, folder_path: str, folder_map: dict, base_parent_id: int = None
) -> int:
    """Create a folder and all parent folders, with optional base parent.

    Args:
        workspace_id: The workspace ID
        folder_path: Full path like "folder1/folder2/folder3"
        folder_map: Dict mapping paths to document IDs (updated in place)
        base_parent_id: Optional base parent ID for all top-level folders

    Returns:
        Document ID of the created/existing folder
    """
    if folder_path in folder_map:
        return folder_map[folder_path]

    parts = folder_path.split('/')
    current_path = ""
    parent_id = base_parent_id

    for part in parts:
        if not part:
            continue

        current_path = f"{current_path}/{part}".lstrip('/')

        if current_path in folder_map:
            parent_id = folder_map[current_path]
            continue

        # Check if already exists
        existing = LatexDocument.query.filter_by(
            workspace_id=workspace_id,
            parent_id=parent_id,
            title=part,
            node_type=LatexNodeType.folder
        ).first()

        if existing:
            folder_map[current_path] = existing.id
            parent_id = existing.id
            continue

        try:
            ensure_safe_title(part)
        except ValidationError:
            logger.warning(f"Skipping folder with invalid name: {part}")
            return parent_id

        folder = LatexDocument(
            workspace_id=workspace_id,
            parent_id=parent_id,
            node_type=LatexNodeType.folder,
            title=part,
            order_index=get_next_order_index(workspace_id, parent_id),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(folder)
        db.session.flush()

        folder_map[current_path] = folder.id
        parent_id = folder.id

    return parent_id
