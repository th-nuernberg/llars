"""
Zotero Sync Service

Handles synchronization of Zotero libraries to workspace .bib files.
"""

import logging
import time
from datetime import datetime
from typing import Optional, Tuple

from db.db import db
from db.models import (
    ZoteroConnection,
    WorkspaceZoteroLibrary,
    ZoteroSyncLog,
    LatexDocument,
    LatexWorkspace,
    LatexNodeType,
)
from services.zotero.zotero_api_service import ZoteroAPIService, ZoteroAPIError
from services.zotero.encryption import decrypt_api_key

logger = logging.getLogger(__name__)


class ZoteroSyncError(Exception):
    """Exception for Zotero sync errors."""
    pass


class ZoteroSyncService:
    """
    Service for synchronizing Zotero libraries with LaTeX workspace .bib files.

    This service:
    - Fetches BibTeX content from Zotero API
    - Creates or updates the .bib document in the workspace
    - Tracks sync history and errors
    """

    def __init__(self, workspace_library: WorkspaceZoteroLibrary):
        """
        Initialize the sync service.

        Args:
            workspace_library: The workspace-zotero library link to sync
        """
        self.workspace_library = workspace_library
        self.connection = workspace_library.zotero_connection
        self._api_service: Optional[ZoteroAPIService] = None

    @property
    def api_service(self) -> ZoteroAPIService:
        """Lazy-load the API service with decrypted key."""
        if self._api_service is None:
            api_key = decrypt_api_key(self.connection.api_key_encrypted)
            self._api_service = ZoteroAPIService(api_key)
        return self._api_service

    def sync(
        self,
        triggered_by: str = "manual",
        triggered_by_username: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Perform a sync operation.

        Args:
            triggered_by: "manual", "auto", or "system"
            triggered_by_username: Username of user who triggered sync

        Returns:
            Tuple of (success, message)
        """
        start_time = time.time()
        log_entry = ZoteroSyncLog(
            workspace_library_id=self.workspace_library.id,
            triggered_by=triggered_by,
            triggered_by_username=triggered_by_username,
            status="running",
        )
        db.session.add(log_entry)
        db.session.commit()

        try:
            # Fetch BibTeX from Zotero
            bibtex_content, item_count = self.api_service.get_bibtex(
                library_type=self.workspace_library.library_type.value,
                library_id=self.workspace_library.library_id,
                collection_key=self.workspace_library.collection_key,
            )

            # Get or create the .bib document
            document = self._ensure_bib_document()

            # Check if content changed
            old_content = document.content_text or ""
            content_changed = old_content != bibtex_content

            # Update document content
            document.content_text = bibtex_content
            document.updated_at = datetime.utcnow()
            document.last_editor_username = triggered_by_username or "zotero-sync"

            # Update library metadata
            self.workspace_library.item_count = item_count
            self.workspace_library.last_synced_at = datetime.utcnow()
            self.workspace_library.last_sync_error = None
            self.workspace_library.document_id = document.id

            # Update connection's last sync time
            self.connection.last_sync_at = datetime.utcnow()

            # Update sync log
            duration_ms = int((time.time() - start_time) * 1000)
            log_entry.status = "success"
            log_entry.items_fetched = item_count
            log_entry.items_updated = item_count if content_changed else 0
            log_entry.duration_ms = duration_ms

            db.session.commit()

            message = f"Synced {item_count} items from Zotero"
            if content_changed:
                message += " (content updated)"
            else:
                message += " (no changes)"

            logger.info(f"Zotero sync success for library {self.workspace_library.id}: {message}")
            return True, message

        except ZoteroAPIError as e:
            return self._handle_sync_error(log_entry, start_time, f"Zotero API error: {str(e)}")
        except Exception as e:
            logger.exception(f"Zotero sync failed for library {self.workspace_library.id}")
            return self._handle_sync_error(log_entry, start_time, f"Sync failed: {str(e)}")

    def _handle_sync_error(
        self,
        log_entry: ZoteroSyncLog,
        start_time: float,
        error_message: str,
    ) -> Tuple[bool, str]:
        """Handle a sync error by updating logs and library state."""
        duration_ms = int((time.time() - start_time) * 1000)

        log_entry.status = "failed"
        log_entry.error_message = error_message
        log_entry.duration_ms = duration_ms

        self.workspace_library.last_sync_error = error_message

        db.session.commit()

        logger.error(f"Zotero sync failed for library {self.workspace_library.id}: {error_message}")
        return False, error_message

    def _ensure_bib_document(self) -> LatexDocument:
        """
        Ensure the .bib document exists in the workspace.

        Creates a new document if needed, or returns the existing one.
        """
        # Check if document already exists
        if self.workspace_library.document_id:
            document = LatexDocument.query.get(self.workspace_library.document_id)
            if document:
                return document

        # Check if a document with this filename already exists
        existing = LatexDocument.query.filter_by(
            workspace_id=self.workspace_library.workspace_id,
            title=self.workspace_library.bib_filename,
            node_type=LatexNodeType.file,
        ).first()

        if existing:
            return existing

        # Create new document
        # Find the maximum order_index for root-level files
        max_order = db.session.query(db.func.max(LatexDocument.order_index)).filter(
            LatexDocument.workspace_id == self.workspace_library.workspace_id,
            LatexDocument.parent_id == None,
        ).scalar() or 0

        document = LatexDocument(
            workspace_id=self.workspace_library.workspace_id,
            parent_id=None,  # Root level
            node_type=LatexNodeType.file,
            title=self.workspace_library.bib_filename,
            order_index=max_order + 1,
            content_text="",  # Will be filled by sync
            yjs_doc_id=None,  # Zotero bib files don't need collaborative editing
        )

        db.session.add(document)
        db.session.flush()  # Get the ID

        return document

    @staticmethod
    def sync_library(
        workspace_library_id: int,
        triggered_by: str = "manual",
        triggered_by_username: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Static helper to sync a library by ID.

        Args:
            workspace_library_id: ID of the WorkspaceZoteroLibrary
            triggered_by: "manual", "auto", or "system"
            triggered_by_username: Username of user who triggered sync

        Returns:
            Tuple of (success, message)
        """
        library = WorkspaceZoteroLibrary.query.get(workspace_library_id)
        if not library:
            return False, "Library not found"

        service = ZoteroSyncService(library)
        return service.sync(triggered_by, triggered_by_username)

    @staticmethod
    def sync_all_auto_sync_libraries() -> int:
        """
        Sync all libraries that have auto-sync enabled and are due.

        Returns:
            Number of libraries synced
        """
        from datetime import timedelta

        now = datetime.utcnow()
        synced_count = 0

        libraries = WorkspaceZoteroLibrary.query.filter_by(
            auto_sync_enabled=True,
        ).all()

        for library in libraries:
            # Check if sync is due
            if library.last_synced_at:
                next_sync = library.last_synced_at + timedelta(minutes=library.auto_sync_interval_minutes)
                if now < next_sync:
                    continue

            try:
                success, _ = ZoteroSyncService.sync_library(
                    library.id,
                    triggered_by="auto",
                )
                if success:
                    synced_count += 1
            except Exception as e:
                logger.error(f"Auto-sync failed for library {library.id}: {e}")

        return synced_count
