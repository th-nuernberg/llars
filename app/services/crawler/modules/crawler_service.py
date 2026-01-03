# crawler_service.py
"""
CrawlerService - Main orchestration class for web crawling.

This is the main entry point for all crawl operations. It coordinates:
- Background crawl job management
- Collection creation and updates
- URL discovery and processing
- WebSocket progress updates
- Embedding pipeline integration

The actual implementation is distributed across specialized modules:
- crawler_constants.py: Configuration and utilities
- crawler_events.py: WebSocket event emission
- crawler_collection.py: Collection management
- crawler_document.py: Document creation/linking
- crawler_processing.py: URL processing strategies
- crawler_jobs.py: Job status management

Usage:
    from services.crawler.modules.crawler_service import crawler_service

    # Start a background crawl
    job_id = crawler_service.start_crawl_background(
        urls=["https://example.com"],
        collection_name="Example Site",
        app=current_app._get_current_object()
    )

    # Check status
    status = crawler_service.get_job_status(job_id)
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from datetime import datetime
from typing import List, Dict, Optional

# Import from specialized modules
from .crawler_constants import (
    RAG_DOCS_PATH,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_ICON,
    DEFAULT_COLOR,
)
from .crawler_events import (
    emit_progress,
    emit_page_crawled,
    emit_complete,
    emit_error,
    emit_jobs_updated,
)
from .crawler_collection import (
    create_crawl_collection,
    update_collection_for_crawl,
    update_collection_stats,
)
from .crawler_jobs import (
    get_job_status,
    get_all_jobs,
    list_jobs,
    cancel_job,
    create_job_entry,
    update_job_started,
    update_job_completed,
    update_job_failed,
)
from .crawler_processing import (
    process_urls_basic,
    process_urls_playwright,
)
from .crawler_core import WebCrawler

logger = logging.getLogger(__name__)

# =============================================================================
# PLAYWRIGHT AVAILABILITY CHECK
# =============================================================================

PLAYWRIGHT_AVAILABLE = False
try:
    from .playwright_crawler import PlaywrightCrawler
    PLAYWRIGHT_AVAILABLE = True
    logger.info("[CrawlerService] Playwright crawler available")
except ImportError as e:
    logger.warning(f"[CrawlerService] Playwright not available: {e}")


# =============================================================================
# CRAWLER SERVICE CLASS
# =============================================================================

class CrawlerService:
    """
    Main service class for managing web crawls and RAG collection creation.

    Supports both synchronous and background crawling with real-time
    WebSocket progress updates. Integrates with the RAG embedding pipeline
    for automatic document indexing.

    Attributes:
        active_crawls: Dict mapping job_id to job status
        _socketio: Flask-SocketIO instance for WebSocket events
        _background_threads: Dict of background crawl threads

    Class Constants (re-exported from crawler_constants):
        RAG_DOCS_PATH: Storage path for crawled documents
        DEFAULT_CHUNK_SIZE: Default chunk size for RAG
        DEFAULT_CHUNK_OVERLAP: Default chunk overlap
        DEFAULT_ICON: Default collection icon
        DEFAULT_COLOR: Default collection color
    """

    # Re-export constants for backward compatibility
    RAG_DOCS_PATH = RAG_DOCS_PATH
    DEFAULT_CHUNK_SIZE = DEFAULT_CHUNK_SIZE
    DEFAULT_CHUNK_OVERLAP = DEFAULT_CHUNK_OVERLAP
    DEFAULT_ICON = DEFAULT_ICON
    DEFAULT_COLOR = DEFAULT_COLOR

    def __init__(self):
        """Initialize the crawler service."""
        self.active_crawls: Dict[str, Dict] = {}
        self._socketio = None
        self._background_threads: Dict[str, threading.Thread] = {}

    # =========================================================================
    # SOCKETIO CONFIGURATION
    # =========================================================================

    def set_socketio(self, socketio) -> None:
        """
        Set the SocketIO instance for live progress updates.

        Must be called during app initialization to enable WebSocket events.

        Args:
            socketio: Flask-SocketIO instance
        """
        self._socketio = socketio

    # =========================================================================
    # JOB STATUS METHODS (Delegated to crawler_jobs)
    # =========================================================================

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a crawl job. See crawler_jobs.get_job_status()."""
        return get_job_status(job_id, self.active_crawls)

    def get_all_jobs(self) -> List[Dict]:
        """Get all crawl jobs. See crawler_jobs.get_all_jobs()."""
        return get_all_jobs(self.active_crawls)

    def list_jobs(self) -> List[Dict]:
        """List all crawl jobs. See crawler_jobs.list_jobs()."""
        return list_jobs(self.active_crawls)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job. See crawler_jobs.cancel_job()."""
        return cancel_job(job_id, self.active_crawls)

    # =========================================================================
    # BACKGROUND CRAWL (Main Entry Point)
    # =========================================================================

    def start_crawl_background(
        self,
        urls: List[str],
        collection_name: str,
        collection_description: str = '',
        max_pages_per_site: int = 50,
        max_depth: int = 3,
        created_by: str = 'web_crawler',
        app=None,
        existing_collection_id: Optional[int] = None,
        use_playwright: bool = True,
        use_vision_llm: bool = True,
        take_screenshots: bool = True,
        chatbot_id: Optional[int] = None
    ) -> str:
        """
        Start a crawl job in the background.

        This is the main entry point for crawling. The crawl runs in a
        background thread and continues even if the user leaves the page.
        Progress updates are sent via WebSocket.

        Args:
            urls: List of URLs to crawl
            collection_name: Display name for the collection
            collection_description: Description text
            max_pages_per_site: Maximum pages to crawl per URL
            max_depth: Maximum link depth to follow
            created_by: Username of requester
            app: Flask app instance (for background context)
            existing_collection_id: Add to existing collection instead of creating new
            use_playwright: Use Playwright for JS rendering (default: True)
            use_vision_llm: Use Vision-LLM for extraction (default: True)
            take_screenshots: Capture screenshots (default: True)
            chatbot_id: Associated chatbot ID (for wizard integration)

        Returns:
            job_id: UUID string for tracking the crawl job

        Raises:
            RuntimeError: If collection creation fails
        """
        job_id = str(uuid.uuid4())

        # Resolve actual Playwright availability
        actual_use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        if use_playwright and not PLAYWRIGHT_AVAILABLE:
            logger.warning(
                f"[Job {job_id}] Playwright requested but not available, "
                "falling back to basic crawler"
            )

        actual_take_screenshots = bool(take_screenshots) and actual_use_playwright
        actual_use_vision_llm = bool(use_vision_llm) and actual_take_screenshots

        # Create job entry
        self.active_crawls[job_id] = create_job_entry(
            job_id=job_id,
            urls=urls,
            collection_name=collection_name,
            existing_collection_id=existing_collection_id,
            chatbot_id=chatbot_id,
            max_pages_per_site=max_pages_per_site,
            use_playwright=actual_use_playwright,
            use_vision_llm=actual_use_vision_llm,
            take_screenshots=actual_take_screenshots
        )

        # Pre-create collection (so frontend gets ID immediately)
        if not existing_collection_id:
            existing_collection_id = self._create_collection_for_job(
                job_id=job_id,
                urls=urls,
                collection_name=collection_name,
                collection_description=collection_description,
                created_by=created_by,
                app=app
            )

        # Notify clients about new job
        emit_jobs_updated(self._socketio, self.get_all_jobs())

        # Start background thread
        def run_crawl_with_context():
            if app:
                with app.app_context():
                    self._run_background_crawl(
                        job_id, urls, collection_name, collection_description,
                        max_pages_per_site, max_depth, created_by,
                        existing_collection_id, actual_use_playwright,
                        actual_use_vision_llm, actual_take_screenshots
                    )
            else:
                self._run_background_crawl(
                    job_id, urls, collection_name, collection_description,
                    max_pages_per_site, max_depth, created_by,
                    existing_collection_id, actual_use_playwright,
                    actual_use_vision_llm, actual_take_screenshots
                )

        thread = threading.Thread(target=run_crawl_with_context, daemon=True)
        thread.start()
        self._background_threads[job_id] = thread

        crawler_type = "Playwright" if actual_use_playwright else "Basic"
        vision_status = "with Vision-LLM" if actual_use_vision_llm else "without Vision-LLM"
        logger.info(
            f"[Job {job_id}] Background crawl started ({crawler_type}, {vision_status}) "
            f"for {len(urls)} URLs"
        )

        return job_id

    def _create_collection_for_job(
        self,
        job_id: str,
        urls: List[str],
        collection_name: str,
        collection_description: str,
        created_by: str,
        app
    ) -> int:
        """Create a collection for a new crawl job."""
        try:
            new_collection_id = None

            if app:
                with app.app_context():
                    collection = create_crawl_collection(
                        urls=urls,
                        display_name=collection_name,
                        description=collection_description,
                        created_by=created_by,
                        job_id=job_id
                    )
                    from db.db import db
                    db.session.commit()
                    new_collection_id = collection.id
            else:
                collection = create_crawl_collection(
                    urls=urls,
                    display_name=collection_name,
                    description=collection_description,
                    created_by=created_by,
                    job_id=job_id
                )
                from db.db import db
                db.session.commit()
                new_collection_id = collection.id

            if not new_collection_id:
                raise RuntimeError("Collection creation returned no ID")

            self.active_crawls[job_id]['collection_id'] = new_collection_id
            self.active_crawls[job_id]['existing_collection_id'] = new_collection_id
            logger.info(f"[Job {job_id}] Pre-created crawl collection {new_collection_id}")

            return new_collection_id

        except Exception as e:
            logger.error(f"[Job {job_id}] Could not create collection: {e}")
            self.active_crawls[job_id]['status'] = 'failed'
            self.active_crawls[job_id]['error'] = str(e)
            emit_error(self._socketio, job_id, str(e))
            emit_jobs_updated(self._socketio, self.get_all_jobs())
            raise

    # =========================================================================
    # BACKGROUND CRAWL EXECUTION
    # =========================================================================

    def _run_background_crawl(
        self,
        job_id: str,
        urls: List[str],
        collection_name: str,
        collection_description: str,
        max_pages_per_site: int,
        max_depth: int,
        created_by: str,
        existing_collection_id: Optional[int],
        use_playwright: bool,
        use_vision_llm: bool,
        take_screenshots: bool
    ) -> None:
        """
        Execute the crawl in the background thread.

        This method runs the complete crawl workflow:
        1. Initialize collection
        2. Start embedding pipeline
        3. Discover URLs
        4. Process URLs (basic or Playwright)
        5. Update collection stats
        6. Emit completion event
        """
        from db.db import db
        from db.tables import RAGCollection
        from services.rag.collection_embedding_service import get_collection_embedding_service

        update_job_started(job_id, self.active_crawls)
        crawler_type = "Playwright" if use_playwright else "Basic"

        # Wait for frontend to subscribe to room
        time.sleep(1.5)

        # Emit initial planning status
        emit_progress(self._socketio, job_id, {
            'status': 'planning',
            'stage': 'planning',
            'pages_crawled': 0,
            'max_pages': max_pages_per_site * len(urls),
            'urls_total': 0,
            'urls_completed': 0,
            'message': f'Crawl gestartet ({crawler_type})...',
            'crawler_type': crawler_type,
            'use_vision_llm': use_vision_llm
        }, self.active_crawls)

        try:
            # Get or create collection
            collection_id = self._initialize_collection(
                job_id, urls, collection_name, collection_description,
                created_by, existing_collection_id
            )

            # Start embedding early
            self._start_early_embedding(job_id, collection_id)

            # Phase 1: URL Discovery
            discovered_urls = self._discover_urls(
                job_id, urls, max_pages_per_site, max_depth, crawler_type
            )

            # Phase 2: URL Processing
            total_pages = self._process_discovered_urls(
                job_id, discovered_urls, collection_id, created_by,
                use_playwright, use_vision_llm, take_screenshots, crawler_type
            )

            # Update collection stats
            brand_color = self.active_crawls[job_id].get('brand_color')
            update_collection_stats(collection_id, brand_color)

            # Mark job completed
            update_job_completed(job_id, self.active_crawls)

            # Emit completion
            self._emit_crawl_complete(job_id, collection_id, total_pages, crawler_type)

        except Exception as e:
            logger.error(f"[Job {job_id}] Background crawl failed: {e}")
            update_job_failed(job_id, str(e), self.active_crawls)
            try:
                db.session.rollback()
            except Exception:
                pass
            emit_error(self._socketio, job_id, str(e))
            emit_jobs_updated(self._socketio, self.get_all_jobs())

    def _initialize_collection(
        self,
        job_id: str,
        urls: List[str],
        collection_name: str,
        collection_description: str,
        created_by: str,
        existing_collection_id: Optional[int]
    ) -> int:
        """Initialize or get the collection for crawling."""
        from db.db import db
        from db.tables import RAGCollection

        if existing_collection_id:
            collection = RAGCollection.query.get(existing_collection_id)
            if not collection:
                raise ValueError(f"Collection with ID {existing_collection_id} not found")

            update_collection_for_crawl(
                collection_id=existing_collection_id,
                job_id=job_id,
                source_url=urls[0] if urls else None
            )

            logger.info(
                f"[Job {job_id}] Adding to existing collection: "
                f"{collection.display_name} (ID: {existing_collection_id})"
            )
            collection_id = existing_collection_id
        else:
            # Create new collection (fallback if not pre-created)
            collection = create_crawl_collection(
                urls=urls,
                display_name=collection_name,
                description=collection_description,
                created_by=created_by,
                job_id=job_id
            )
            collection_id = collection.id
            logger.info(
                f"[Job {job_id}] Created new collection: "
                f"{collection.display_name} (ID: {collection_id})"
            )

        self.active_crawls[job_id]['collection_id'] = collection_id
        self.active_crawls[job_id]['documents_linked'] = 0
        self.active_crawls[job_id]['urls_total'] = 0
        self.active_crawls[job_id]['urls_completed'] = 0
        self.active_crawls[job_id]['images_extracted'] = 0

        return collection_id

    def _start_early_embedding(self, job_id: str, collection_id: int) -> None:
        """Start embedding pipeline early for live indexing."""
        try:
            from services.rag.collection_embedding_service import get_collection_embedding_service
            embedding_service = get_collection_embedding_service()
            embedding_service.start_embedding(
                collection_id,
                wait_for_more=True,
                source_job_id=job_id
            )
            logger.info(
                f"[Job {job_id}] Embedding started in live mode for collection {collection_id}"
            )
        except Exception as e:
            logger.warning(f"[Job {job_id}] Could not start early embedding: {e}")

    def _discover_urls(
        self,
        job_id: str,
        urls: List[str],
        max_pages_per_site: int,
        max_depth: int,
        crawler_type: str
    ) -> List[str]:
        """Discover all URLs to crawl."""
        emit_progress(self._socketio, job_id, {
            'status': 'planning',
            'stage': 'planning',
            'pages_crawled': 0,
            'max_pages': max_pages_per_site * len(urls),
            'urls_total': 0,
            'urls_completed': 0,
            'current_url': urls[0] if urls else '',
            'crawler_type': crawler_type,
            'message': 'URL-Erkundung gestartet...'
        }, self.active_crawls)

        discovered_urls: List[str] = []
        last_emit_time = [0]

        def discovery_progress_callback(count: int, current_url: str):
            now = time.time()
            if now - last_emit_time[0] < 0.25:
                return
            last_emit_time[0] = now

            self.active_crawls[job_id]['urls_total'] = count
            self.active_crawls[job_id]['current_url'] = current_url

            emit_progress(self._socketio, job_id, {
                'status': 'planning',
                'stage': 'planning',
                'pages_crawled': 0,
                'max_pages': max(count, max_pages_per_site * len(urls)),
                'urls_total': count,
                'urls_completed': 0,
                'current_url': current_url,
                'crawler_type': crawler_type,
                'message': f'{count} URLs gefunden...'
            }, self.active_crawls)

        for url_index, url in enumerate(urls):
            logger.info(f"[Job {job_id}] Discovery URL {url_index + 1}/{len(urls)}: {url}")
            crawler = WebCrawler(
                base_url=url,
                max_pages=max_pages_per_site,
                max_depth=max_depth,
                delay_seconds=0.1
            )
            discovered_urls.extend(
                crawler.discover_urls(
                    max_pages_per_site,
                    max_depth,
                    progress_callback=discovery_progress_callback
                )
            )

        # Deduplicate
        discovered_urls = list(dict.fromkeys(discovered_urls))
        self.active_crawls[job_id]['urls_total'] = len(discovered_urls)

        logger.info(f"[Job {job_id}] Discovery complete: {len(discovered_urls)} unique URLs")

        emit_progress(self._socketio, job_id, {
            'status': 'running',
            'stage': 'planning_done',
            'pages_crawled': 0,
            'max_pages': len(discovered_urls),
            'urls_total': len(discovered_urls),
            'urls_completed': 0,
            'crawler_type': crawler_type,
            'message': f'{len(discovered_urls)} URLs gefunden, Crawling startet...'
        }, self.active_crawls)

        return discovered_urls

    def _process_discovered_urls(
        self,
        job_id: str,
        discovered_urls: List[str],
        collection_id: int,
        created_by: str,
        use_playwright: bool,
        use_vision_llm: bool,
        take_screenshots: bool,
        crawler_type: str
    ) -> int:
        """Process discovered URLs with appropriate crawler."""
        seen_hashes_global: set = set()

        if use_playwright and PLAYWRIGHT_AVAILABLE:
            return process_urls_playwright(
                job_id=job_id,
                urls=discovered_urls,
                collection_id=collection_id,
                created_by=created_by,
                seen_hashes_global=seen_hashes_global,
                use_vision_llm=use_vision_llm,
                take_screenshots=take_screenshots,
                crawler_type=crawler_type,
                active_crawls=self.active_crawls,
                socketio=self._socketio
            )
        else:
            return process_urls_basic(
                job_id=job_id,
                urls=discovered_urls,
                collection_id=collection_id,
                created_by=created_by,
                seen_hashes_global=seen_hashes_global,
                crawler_type=crawler_type,
                active_crawls=self.active_crawls,
                socketio=self._socketio
            )

    def _emit_crawl_complete(
        self,
        job_id: str,
        collection_id: int,
        total_pages: int,
        crawler_type: str
    ) -> None:
        """Emit completion event and update job list."""
        job = self.active_crawls[job_id]
        docs_created = job['documents_created']
        docs_linked = job['documents_linked']
        screenshots = job.get('screenshots_taken', 0)
        vision_extractions = job.get('vision_extractions', 0)
        brand_color = job.get('brand_color')

        logger.info(
            f"[Job {job_id}] Background crawl completed: {total_pages} pages, "
            f"{docs_created} documents neu, {docs_linked} documents verlinkt"
        )

        if crawler_type == 'Playwright':
            logger.info(
                f"[Job {job_id}] Playwright stats: {screenshots} screenshots, "
                f"{vision_extractions} vision extractions"
            )

        emit_complete(self._socketio, job_id, {
            'status': 'completed',
            'stage': 'completed',
            'collection_id': collection_id,
            'pages_crawled': total_pages,
            'documents_created': docs_created,
            'documents_linked': docs_linked,
            'screenshots_taken': screenshots,
            'vision_extractions': vision_extractions,
            'errors_count': len(job['errors']),
            'crawler_type': crawler_type,
            'brand_color': brand_color
        })

        emit_jobs_updated(self._socketio, self.get_all_jobs())


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

crawler_service = CrawlerService()
