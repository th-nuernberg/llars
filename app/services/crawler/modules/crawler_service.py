"""
CrawlerService Module

Service for managing web crawls and creating RAG collections from crawled content.
Supports background crawling with WebSocket live updates.
"""

import os
import uuid
import logging
import threading
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

from .crawler_core import WebCrawler
from services.rag.collection_embedding_service import get_collection_embedding_service

logger = logging.getLogger(__name__)

# Flag to check if Playwright is available
PLAYWRIGHT_AVAILABLE = False
try:
    from .playwright_crawler import PlaywrightCrawler
    PLAYWRIGHT_AVAILABLE = True
    logger.info("[CrawlerService] Playwright crawler available")
except ImportError as e:
    logger.warning(f"[CrawlerService] Playwright not available: {e}")


class CrawlerService:
    """
    Service for managing web crawls and creating RAG collections from crawled content.
    Supports background crawling with WebSocket live updates.
    """

    RAG_DOCS_PATH = '/app/data/rag/crawls'
    DEFAULT_EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    DEFAULT_CHUNK_SIZE = 1000
    DEFAULT_CHUNK_OVERLAP = 200
    DEFAULT_ICON = 'mdi-web'
    DEFAULT_COLOR = '#2196F3'

    def __init__(self):
        self.active_crawls: Dict[str, Dict] = {}
        self._socketio = None
        self._background_threads: Dict[str, threading.Thread] = {}

    def _slugify(self, value: str, max_length: int = 200) -> str:
        """Create a safe slug for internal collection names."""
        value = (value or '').strip().lower()
        value = re.sub(r'[^a-z0-9]+', '_', value)
        value = value.strip('_')
        if not value:
            value = 'site'
        return value[:max_length].rstrip('_')

    def _build_crawl_collection_name(self, urls: List[str], display_name: str, job_id: str) -> str:
        """Build a unique, safe internal name for crawl collections."""
        domain = ''
        if urls:
            try:
                domain = urlparse(urls[0]).netloc
            except Exception:
                domain = ''
        base = domain or display_name or 'site'
        slug = self._slugify(base, max_length=180)
        return f"crawl_{slug}_{job_id[:8]}"

    def _create_crawl_collection(
        self,
        urls: List[str],
        display_name: str,
        description: str,
        created_by: str,
        job_id: str
    ):
        """Create and persist a new RAGCollection for a crawl."""
        from db.db import db
        from db.tables import RAGCollection

        internal_name = self._build_crawl_collection_name(urls, display_name, job_id)

        collection = RAGCollection(
            name=internal_name,
            display_name=display_name,
            description=description or (f"Webcrawl von: {', '.join(urls)}" if urls else ''),
            icon=self.DEFAULT_ICON,
            color=self.DEFAULT_COLOR,
            embedding_model=self.DEFAULT_EMBEDDING_MODEL,
            chunk_size=self.DEFAULT_CHUNK_SIZE,
            chunk_overlap=self.DEFAULT_CHUNK_OVERLAP,
            is_active=True,
            is_public=True,
            created_by=created_by,
            created_at=datetime.now(),
            source_type='crawler',
            source_url=urls[0] if urls else None,
            crawl_job_id=job_id
        )
        db.session.add(collection)
        db.session.flush()
        return collection

    def set_socketio(self, socketio):
        """Set the SocketIO instance for live updates."""
        self._socketio = socketio

    def _emit_progress(self, session_id: str, data: dict):
        """Emit progress update via WebSocket."""
        if self._socketio:
            from socketio_handlers.events_crawler import emit_crawler_progress
            emit_crawler_progress(self._socketio, session_id, data)

    def _emit_page_crawled(self, session_id: str, data: dict):
        """Emit page crawled event via WebSocket."""
        if self._socketio:
            from socketio_handlers.events_crawler import emit_crawler_page_crawled
            emit_crawler_page_crawled(self._socketio, session_id, data)

    def _emit_complete(self, session_id: str, data: dict):
        """Emit completion event via WebSocket."""
        if self._socketio:
            from socketio_handlers.events_crawler import emit_crawler_complete
            emit_crawler_complete(self._socketio, session_id, data)

    def _emit_error(self, session_id: str, error: str):
        """Emit error event via WebSocket."""
        if self._socketio:
            from socketio_handlers.events_crawler import emit_crawler_error
            emit_crawler_error(self._socketio, session_id, error)

    def _emit_jobs_updated(self):
        """Emit global job list update to all subscribed clients."""
        if self._socketio:
            from socketio_handlers.events_crawler import emit_crawler_jobs_updated
            emit_crawler_jobs_updated(self._socketio, self.get_all_jobs())

    def start_crawl(
        self,
        urls: List[str],
        collection_name: str,
        collection_description: str = '',
        max_pages_per_site: int = 50,
        max_depth: int = 3,
        created_by: str = 'web_crawler'
    ) -> Dict:
        """
        Start a crawl job for one or more URLs and create a RAG collection.

        Args:
            urls: List of base URLs to crawl
            collection_name: Name for the new collection
            collection_description: Description for the collection
            max_pages_per_site: Max pages to crawl per URL
            max_depth: Max link depth
            created_by: Username of requester

        Returns:
            Dict with job_id and status
        """
        from db.db import db
        from db.tables import RAGDocument, RAGProcessingQueue

        job_id = str(uuid.uuid4())

        # Create collection (synchronous mode)
        collection = self._create_crawl_collection(
            urls=urls,
            display_name=collection_name,
            description=collection_description,
            created_by=created_by,
            job_id=job_id
        )

        collection_id = collection.id

        # Track job
        self.active_crawls[job_id] = {
            'status': 'running',
            'collection_id': collection_id,
            'urls': urls,
            'pages_crawled': 0,
            'documents_created': 0,
            'errors': [],
            'started_at': datetime.now().isoformat()
        }

        try:
            total_pages = 0

            for url in urls:
                logger.info(f"[Job {job_id}] Starting crawl of {url}")

                crawler = WebCrawler(
                    base_url=url,
                    max_pages=max_pages_per_site,
                    max_depth=max_depth,
                    delay_seconds=1.0
                )

                def progress_callback(current, total, page_url):
                    self.active_crawls[job_id]['pages_crawled'] = total_pages + current
                    self.active_crawls[job_id]['current_url'] = page_url
                    # Emit WebSocket progress update
                    self._emit_progress(job_id, {
                        'status': 'running',
                        'stage': 'crawling',
                        'pages_crawled': total_pages + current,
                        'max_pages': max_pages_per_site * len(urls),
                        'current_url': page_url,
                        'current_url_index': urls.index(url) + 1,
                        'total_urls': len(urls)
                    })
                    # Emit page crawled event
                    self._emit_page_crawled(job_id, {
                        'url': page_url,
                        'page_number': total_pages + current
                    })

                pages = crawler.crawl(progress_callback=progress_callback)
                total_pages += len(pages)

                # Create documents from crawled pages
                seen_hashes = set()

                for page in pages:
                    try:
                        content_hash = page['content_hash']
                        if content_hash in seen_hashes:
                            logger.debug(f"Skipping duplicate content for {page['url']}")
                            continue
                        seen_hashes.add(content_hash)

                        existing_doc = RAGDocument.query.filter_by(file_hash=content_hash).first()
                        if existing_doc:
                            logger.debug(f"Content already exists in DB for {page['url']}")
                            continue

                        filename = f"webcrawl_{job_id[:8]}_{uuid.uuid4().hex[:8]}.md"
                        file_path = os.path.join(self.RAG_DOCS_PATH, filename)

                        os.makedirs(self.RAG_DOCS_PATH, exist_ok=True)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(page['content'])

                        doc = RAGDocument(
                            filename=filename,
                            original_filename=page['metadata'].get('title', page['url'])[:255],
                            file_path=file_path,
                            file_size_bytes=len(page['content'].encode('utf-8')),
                            mime_type='text/markdown',
                            file_hash=content_hash,
                            title=page['metadata'].get('title', '')[:255],
                            description=page['metadata'].get('description', '')[:500],
                            author=urlparse(page['url']).netloc,
                            language=page['metadata'].get('language', 'de'),
                            keywords=page['metadata'].get('keywords', ''),
                            status='pending',
                            collection_id=collection_id,
                            is_public=True,
                            uploaded_by=created_by,
                            uploaded_at=datetime.now()
                        )
                        db.session.add(doc)
                        db.session.flush()

                        queue_entry = RAGProcessingQueue(
                            document_id=doc.id,
                            priority=5,
                            status='queued',
                            created_at=datetime.now()
                        )
                        db.session.add(queue_entry)
                        db.session.commit()

                        self.active_crawls[job_id]['documents_created'] += 1

                    except Exception as e:
                        logger.error(f"Error creating document for {page['url']}: {e}")
                        db.session.rollback()
                        self.active_crawls[job_id]['errors'].append({
                            'url': page['url'],
                            'error': str(e)
                        })

            # Update collection stats
            try:
                collection = RAGCollection.query.get(collection_id)
                if collection:
                    actual_count = RAGDocument.query.filter_by(collection_id=collection_id).count()
                    collection.document_count = actual_count
                    db.session.commit()
            except Exception as e:
                logger.warning(f"Could not update collection stats: {e}")

            self.active_crawls[job_id]['status'] = 'completed'
            self.active_crawls[job_id]['completed_at'] = datetime.now().isoformat()

            logger.info(f"[Job {job_id}] Crawl completed: {total_pages} pages, {self.active_crawls[job_id]['documents_created']} documents")

            self._emit_complete(job_id, {
                'status': 'completed',
                'collection_id': collection_id,
                'pages_crawled': total_pages,
                'documents_created': self.active_crawls[job_id]['documents_created'],
                'errors_count': len(self.active_crawls[job_id]['errors'])
            })

        except Exception as e:
            logger.error(f"[Job {job_id}] Crawl failed: {e}")
            self.active_crawls[job_id]['status'] = 'failed'
            self.active_crawls[job_id]['error'] = str(e)
            try:
                db.session.rollback()
            except Exception:
                pass
            self._emit_error(job_id, str(e))

        return {
            'job_id': job_id,
            'collection_id': collection_id,
            'status': self.active_crawls[job_id]['status'],
            'pages_crawled': self.active_crawls[job_id]['pages_crawled'],
            'documents_created': self.active_crawls[job_id]['documents_created']
        }

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
        use_vision_llm: bool = True
    ) -> str:
        """
        Start a crawl job in the background (continues even if user leaves).

        Args:
            urls: List of URLs to crawl
            collection_name: Name for new collection (ignored if existing_collection_id is set)
            collection_description: Description for new collection
            max_pages_per_site: Max pages to crawl per URL
            max_depth: Max link depth
            created_by: Username of requester
            app: Flask app instance for context
            existing_collection_id: If set, add documents to this existing collection instead of creating new one
            use_playwright: Use Playwright headless browser for JavaScript rendering (default: True)
            use_vision_llm: Use Vision-LLM for intelligent data extraction from screenshots (default: True)

        Returns:
            job_id: The ID of the started crawl job
        """
        job_id = str(uuid.uuid4())

        # Check if Playwright is requested but not available
        actual_use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        if use_playwright and not PLAYWRIGHT_AVAILABLE:
            logger.warning(f"[Job {job_id}] Playwright requested but not available, falling back to basic crawler")

        # Pre-create job entry immediately
        self.active_crawls[job_id] = {
            'status': 'queued',
            'urls': urls,
            'collection_name': collection_name,
            'existing_collection_id': existing_collection_id,
            'collection_id': existing_collection_id,
            'max_pages': max_pages_per_site * len(urls),
            'pages_crawled': 0,
            'documents_created': 0,
            'documents_linked': 0,
            'screenshots_taken': 0,
            'vision_extractions': 0,
            'errors': [],
            'queued_at': datetime.now().isoformat(),
            'use_playwright': actual_use_playwright,
            'use_vision_llm': use_vision_llm
        }

        # Create collection synchronously when starting a new crawl (so frontend gets ID immediately)
        if not existing_collection_id:
            try:
                new_collection_id = None
                if app:
                    with app.app_context():
                        collection = self._create_crawl_collection(
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
                    collection = self._create_crawl_collection(
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

                existing_collection_id = new_collection_id
                self.active_crawls[job_id]['collection_id'] = new_collection_id
                self.active_crawls[job_id]['existing_collection_id'] = new_collection_id
                logger.info(f"[Job {job_id}] Pre-created crawl collection {new_collection_id}")
            except Exception as e:
                logger.error(f"[Job {job_id}] Could not create collection: {e}")
                self.active_crawls[job_id]['status'] = 'failed'
                self.active_crawls[job_id]['error'] = str(e)
                self._emit_error(job_id, str(e))
                self._emit_jobs_updated()
                raise

        # Notify all clients about new job
        self._emit_jobs_updated()

        def run_crawl_with_context():
            """Run crawl in background thread with Flask app context."""
            if app:
                with app.app_context():
                    self._run_background_crawl(
                        job_id, urls, collection_name, collection_description,
                        max_pages_per_site, max_depth, created_by,
                        existing_collection_id, actual_use_playwright, use_vision_llm
                    )
            else:
                self._run_background_crawl(
                    job_id, urls, collection_name, collection_description,
                    max_pages_per_site, max_depth, created_by,
                    existing_collection_id, actual_use_playwright, use_vision_llm
                )

        # Start background thread
        thread = threading.Thread(target=run_crawl_with_context, daemon=True)
        thread.start()
        self._background_threads[job_id] = thread

        crawler_type = "Playwright" if actual_use_playwright else "Basic"
        vision_status = "with Vision-LLM" if use_vision_llm and actual_use_playwright else "without Vision-LLM"
        logger.info(f"[Job {job_id}] Background crawl started ({crawler_type}, {vision_status}) for {len(urls)} URLs")

        return job_id

    def _run_background_crawl(
        self,
        job_id: str,
        urls: List[str],
        collection_name: str,
        collection_description: str,
        max_pages_per_site: int,
        max_depth: int,
        created_by: str,
        existing_collection_id: Optional[int] = None,
        use_playwright: bool = True,
        use_vision_llm: bool = True
    ):
        """
        Internal method to run crawl in background.

        Implements document linking logic:
        - If a document with the same content hash already exists, it is LINKED to the collection
        - If the document is new, it is created and linked
        - Documents can exist in multiple collections via CollectionDocumentLink

        Args:
            job_id: Unique job identifier
            urls: List of URLs to crawl
            collection_name: Name for the collection
            collection_description: Description for the collection
            max_pages_per_site: Max pages per URL
            max_depth: Max link depth
            created_by: Username
            existing_collection_id: Optional existing collection ID
            use_playwright: Use Playwright headless browser (default: True)
            use_vision_llm: Use Vision-LLM for extraction (default: True)
        """
        from db.db import db
        from db.tables import RAGCollection, RAGDocument, RAGProcessingQueue, CollectionDocumentLink, RAGDocumentChunk

        self.active_crawls[job_id]['status'] = 'running'
        self.active_crawls[job_id]['started_at'] = datetime.now().isoformat()

        crawler_type = "Playwright" if use_playwright else "Basic"

        # Wait a moment for frontend to subscribe to the room
        # This prevents race condition where events are emitted before client joins
        import time
        time.sleep(1.5)

        # Emit started event - use 'planning' stage since discovery starts first
        self._emit_progress(job_id, {
            'status': 'planning',
            'stage': 'planning',
            'pages_crawled': 0,
            'max_pages': max_pages_per_site * len(urls),
            'urls_total': 0,
            'urls_completed': 0,
            'message': f'Crawl gestartet ({crawler_type})...',
            'crawler_type': crawler_type,
            'use_vision_llm': use_vision_llm
        })

        try:
            # Either use existing collection or create new one
            if existing_collection_id:
                collection = RAGCollection.query.get(existing_collection_id)
                if not collection:
                    raise ValueError(f"Collection with ID {existing_collection_id} not found")
                collection_id = collection.id
                logger.info(f"[Job {job_id}] Adding to existing collection: {collection.display_name} (ID: {collection_id})")

                # Update source metadata for existing collections
                collection.crawl_job_id = job_id
                if collection.source_type == 'upload':
                    collection.source_type = 'mixed'
                if not collection.source_url and urls:
                    collection.source_url = urls[0]
                db.session.commit()
            else:
                # Create new collection (fallback if not pre-created)
                collection = self._create_crawl_collection(
                    urls=urls,
                    display_name=collection_name,
                    description=collection_description,
                    created_by=created_by,
                    job_id=job_id
                )
                collection_id = collection.id
                logger.info(f"[Job {job_id}] Created new collection: {collection.display_name} (ID: {collection_id})")

            self.active_crawls[job_id]['collection_id'] = collection_id
            self.active_crawls[job_id]['documents_linked'] = 0
            self.active_crawls[job_id]['urls_total'] = 0
            self.active_crawls[job_id]['urls_completed'] = 0
            self.active_crawls[job_id]['images_extracted'] = 0

            # Start embedding early so chunks are indexed while crawling continues
            try:
                embedding_service = get_collection_embedding_service()
                embedding_service.start_embedding(
                    collection_id,
                    wait_for_more=True,
                    source_job_id=job_id
                )
                logger.info(f"[Job {job_id}] Embedding started in live mode for collection {collection_id}")
            except Exception as e:
                logger.warning(f"[Job {job_id}] Could not start early embedding: {e}")

            total_pages = 0
            seen_hashes_global = set()

            # ---------- Phase 1: Discovery ----------
            # Emit initial planning status
            self._emit_progress(job_id, {
                'status': 'planning',
                'stage': 'planning',
                'pages_crawled': 0,
                'max_pages': max_pages_per_site * len(urls),
                'urls_total': 0,
                'urls_completed': 0,
                'current_url': urls[0] if urls else '',
                'crawler_type': crawler_type,
                'message': 'URL-Erkundung gestartet...'
            })

            discovered_urls: List[str] = []
            last_emit_time = [0]  # Use list for closure mutability

            def discovery_progress_callback(count: int, current_url: str):
                """Callback to emit progress during discovery."""
                import time
                now = time.time()
                # Throttle emissions to max 4 per second for responsive UI
                if now - last_emit_time[0] < 0.25:
                    return
                last_emit_time[0] = now

                self.active_crawls[job_id]['urls_total'] = count
                self.active_crawls[job_id]['current_url'] = current_url

                self._emit_progress(job_id, {
                    'status': 'planning',
                    'stage': 'planning',
                    'pages_crawled': 0,
                    'max_pages': max(count, max_pages_per_site * len(urls)),
                    'urls_total': count,
                    'urls_completed': 0,
                    'current_url': current_url,
                    'crawler_type': crawler_type,
                    'message': f'{count} URLs gefunden...'
                })

            for url_index, url in enumerate(urls):
                logger.info(f"[Job {job_id}] Discovery URL {url_index + 1}/{len(urls)}: {url}")
                crawler = WebCrawler(
                    base_url=url,
                    max_pages=max_pages_per_site,
                    max_depth=max_depth,
                    delay_seconds=0.1  # Faster for discovery
                )
                discovered_urls.extend(
                    crawler.discover_urls(
                        max_pages_per_site,
                        max_depth,
                        progress_callback=discovery_progress_callback
                    )
                )

            # De-duplicate URLs
            discovered_urls = list(dict.fromkeys(discovered_urls))
            self.active_crawls[job_id]['urls_total'] = len(discovered_urls)

            logger.info(f"[Job {job_id}] Discovery complete: {len(discovered_urls)} unique URLs found")

            self._emit_progress(job_id, {
                'status': 'running',
                'stage': 'planning_done',
                'pages_crawled': 0,
                'max_pages': len(discovered_urls),
                'urls_total': len(discovered_urls),
                'urls_completed': 0,
                'crawler_type': crawler_type,
                'message': f'{len(discovered_urls)} URLs gefunden, Crawling startet...'
            })

            if use_playwright and PLAYWRIGHT_AVAILABLE:
                total_pages = self._process_urls_playwright(
                    job_id,
                    discovered_urls,
                    collection_id,
                    created_by,
                    seen_hashes_global,
                    use_vision_llm,
                    crawler_type
                )
            else:
                total_pages = self._process_urls_basic(
                    job_id,
                    discovered_urls,
                    collection_id,
                    created_by,
                    seen_hashes_global,
                    crawler_type
                )

            # Update collection stats
            try:
                collection = RAGCollection.query.get(collection_id)
                if collection:
                    link_count = CollectionDocumentLink.query.filter_by(collection_id=collection_id).count()
                    collection.document_count = link_count
                    db.session.commit()
            except Exception as e:
                logger.warning(f"Could not update collection stats: {e}")

            self.active_crawls[job_id]['status'] = 'completed'
            self.active_crawls[job_id]['completed_at'] = datetime.now().isoformat()

            docs_created = self.active_crawls[job_id]['documents_created']
            docs_linked = self.active_crawls[job_id]['documents_linked']
            screenshots = self.active_crawls[job_id].get('screenshots_taken', 0)
            vision_extractions = self.active_crawls[job_id].get('vision_extractions', 0)

            logger.info(f"[Job {job_id}] Background crawl completed: {total_pages} pages, {docs_created} documents neu, {docs_linked} documents verlinkt")
            if use_playwright:
                logger.info(f"[Job {job_id}] Playwright stats: {screenshots} screenshots, {vision_extractions} vision extractions")

            self._emit_complete(job_id, {
                'status': 'completed',
                'stage': 'completed',
                'collection_id': collection_id,
                'pages_crawled': total_pages,
                'documents_created': docs_created,
                'documents_linked': docs_linked,
                'screenshots_taken': screenshots,
                'vision_extractions': vision_extractions,
                'errors_count': len(self.active_crawls[job_id]['errors']),
                'crawler_type': crawler_type
            })

            self._emit_jobs_updated()

        except Exception as e:
            logger.error(f"[Job {job_id}] Background crawl failed: {e}")
            self.active_crawls[job_id]['status'] = 'failed'
            self.active_crawls[job_id]['error'] = str(e)
            try:
                db.session.rollback()
            except Exception:
                pass
            self._emit_error(job_id, str(e))
            self._emit_jobs_updated()

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a crawl job."""
        return self.active_crawls.get(job_id)

    def get_all_jobs(self) -> List[Dict]:
        """Get all crawl jobs (for WebSocket subscription)."""
        jobs = []
        for job_id, status in self.active_crawls.items():
            jobs.append({'job_id': job_id, **status})
        jobs.sort(key=lambda x: x.get('started_at') or x.get('queued_at') or '', reverse=True)
        return jobs

    def list_jobs(self) -> List[Dict]:
        """List all crawl jobs."""
        return self.get_all_jobs()

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running crawl job (marks as cancelled, thread continues until next check)."""
        if job_id in self.active_crawls:
            self.active_crawls[job_id]['status'] = 'cancelled'
            return True
        return False

    def _process_crawled_page(
        self,
        job_id: str,
        page: Dict,
        collection_id: int,
        created_by: str,
        seen_hashes: set
    ):
        """
        Process a single crawled page immediately.
        Creates document or links existing document to collection.
        Also stores extracted images and screenshots as RAGDocumentChunks.
        """
        from db.db import db
        from db.tables import RAGDocument, RAGDocumentChunk, RAGProcessingQueue, CollectionDocumentLink

        try:
            content_hash = page['content_hash']

            if content_hash in seen_hashes:
                logger.debug(f"Skipping duplicate content within crawl for {page['url']}")
                return None
            seen_hashes.add(content_hash)

            existing_doc = RAGDocument.query.filter_by(file_hash=content_hash).first()

            if existing_doc:
                existing_link = CollectionDocumentLink.query.filter_by(
                    collection_id=collection_id,
                    document_id=existing_doc.id
                ).first()

                if existing_link:
                    logger.debug(f"Document already linked to collection for {page['url']}")
                    return None

                link = CollectionDocumentLink(
                    collection_id=collection_id,
                    document_id=existing_doc.id,
                    link_type='linked',
                    source_url=page['url'],
                    crawl_job_id=job_id,
                    linked_at=datetime.now(),
                    linked_by=created_by
                )
                db.session.add(link)
                db.session.commit()

                self.active_crawls[job_id]['documents_linked'] += 1
                logger.info(f"[Job {job_id}] Linked existing document {existing_doc.id} to collection {collection_id}")

                try:
                    from services.rag.document_service import DocumentService
                    return {
                        'action': 'linked',
                        'document': DocumentService.serialize_document(existing_doc)
                    }
                except Exception:
                    return None

            else:
                filename = f"webcrawl_{job_id[:8]}_{uuid.uuid4().hex[:8]}.md"
                file_path = os.path.join(self.RAG_DOCS_PATH, filename)
                os.makedirs(self.RAG_DOCS_PATH, exist_ok=True)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(page['content'])

                # Extract screenshot data if available (from Playwright crawler)
                screenshot_data = page.get('screenshot')
                screenshot_path = screenshot_data.get('screenshot_path') if screenshot_data else None

                doc = RAGDocument(
                    filename=filename,
                    original_filename=page['metadata'].get('title', page['url'])[:255],
                    file_path=file_path,
                    file_size_bytes=len(page['content'].encode('utf-8')),
                    mime_type='text/markdown',
                    file_hash=content_hash,
                    title=page['metadata'].get('title', '')[:255],
                    description=page['metadata'].get('description', '')[:500],
                    author=urlparse(page['url']).netloc,
                    language=page['metadata'].get('language', 'de'),
                    keywords=page['metadata'].get('keywords', ''),
                    status='pending',
                    collection_id=collection_id,
                    is_public=True,
                    uploaded_by=created_by,
                    uploaded_at=datetime.now(),
                    # New fields for Playwright/Vision-LLM support
                    screenshot_path=screenshot_path,
                    source_url=page['url']
                )
                db.session.add(doc)
                db.session.flush()

                # Persist an API URL so UIs (and chats) can fetch the screenshot with auth
                if screenshot_path and not getattr(doc, 'screenshot_url', None):
                    doc.screenshot_url = f"/api/rag/documents/{doc.id}/screenshot"

                # Store extracted images as chunks
                images = page.get('images', [])
                if images:
                    for idx, img in enumerate(images):
                        image_chunk = RAGDocumentChunk(
                            document_id=doc.id,
                            chunk_index=10000 + idx,  # High index to avoid collision with text chunks
                            content=f"[Bild: {img.get('alt_text', 'Bild ohne Beschreibung')}]",
                            has_image=True,
                            image_path=img.get('image_path'),
                            image_url=img.get('source_url'),
                            image_alt_text=img.get('alt_text'),
                            image_mime_type=img.get('mime_type', 'image/jpeg'),
                            embedding_status='completed'  # Images don't need text embedding
                        )
                    db.session.add(image_chunk)
                logger.info(f"[Job {job_id}] Stored {len(images)} images for document {doc.id}")

                # Store screenshot(s) as special chunks (for Vision-LLM queries and UI inspection)
                if screenshot_data:
                    screenshot_entries = screenshot_data.get('screenshots') or []
                    if not screenshot_entries and screenshot_path:
                        screenshot_entries = [{'screenshot_path': screenshot_path}]

                    stored = 0
                    for idx, shot in enumerate(screenshot_entries):
                        shot_path = (shot or {}).get('screenshot_path')
                        if not shot_path:
                            continue

                        screenshot_chunk = RAGDocumentChunk(
                            document_id=doc.id,
                            chunk_index=99999 + idx,  # Keep legacy index for first screenshot
                            content=f"[Screenshot der Webseite: {page['url']}]",
                            has_image=True,
                            image_path=shot_path,
                            image_url=page['url'],
                            image_alt_text=f"Screenshot von {page['metadata'].get('title', page['url'])}",
                            image_mime_type='image/png',
                            embedding_status='completed'
                        )
                        db.session.add(screenshot_chunk)
                        stored += 1

                    if stored:
                        logger.info(f"[Job {job_id}] Stored {stored} screenshot(s) for document {doc.id}")

                link = CollectionDocumentLink(
                    collection_id=collection_id,
                    document_id=doc.id,
                    link_type='new',
                    source_url=page['url'],
                    crawl_job_id=job_id,
                    linked_at=datetime.now(),
                    linked_by=created_by
                )
                db.session.add(link)

                queue_entry = RAGProcessingQueue(
                    document_id=doc.id,
                    priority=5,
                    status='queued',
                    created_at=datetime.now()
                )
                db.session.add(queue_entry)
                db.session.commit()

                self.active_crawls[job_id]['documents_created'] += 1
                if images:
                    self.active_crawls[job_id]['images_extracted'] = self.active_crawls[job_id].get('images_extracted', 0) + len(images)
                if screenshot_data and screenshot_path:
                    self.active_crawls[job_id]['screenshots_taken'] = self.active_crawls[job_id].get('screenshots_taken', 0) + screenshot_data.get('screenshot_count', 1)
                crawler_type = page.get('crawler_type', 'basic')
                logger.info(f"[Job {job_id}] Created new document {doc.id} for {page['url']} (crawler: {crawler_type})")

                try:
                    from services.rag.document_service import DocumentService
                    return {
                        'action': 'new',
                        'document': DocumentService.serialize_document(doc)
                    }
                except Exception:
                    return None

            return None

        except Exception as e:
            logger.error(f"Error processing document for {page['url']}: {e}")
            db.session.rollback()
            self.active_crawls[job_id]['errors'].append({
                'url': page['url'],
                'error': str(e)
            })
            return None

    def _process_urls_basic(
        self,
        job_id: str,
        urls: List[str],
        collection_id: int,
        created_by: str,
        seen_hashes_global: set,
        crawler_type: str
    ) -> int:
        """
        Fetch URLs in parallel using the basic crawler (requests + BeautifulSoup).
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        if not urls:
            return 0

        fetch_workers = max(2, min(8, len(urls)))

        def fetch_single(target_url: str):
            worker = WebCrawler(
                base_url=target_url,
                max_pages=1,
                max_depth=0,
                delay_seconds=0.05,
                extract_images=True
            )
            return worker.fetch_page_content(target_url)

        total_pages = 0
        with ThreadPoolExecutor(max_workers=fetch_workers) as executor:
            future_map = {executor.submit(fetch_single, u): u for u in urls}
            for future in as_completed(future_map):
                url = future_map[future]
                try:
                    page_data = future.result()
                except Exception as e:
                    logger.error(f"[Job {job_id}] Fetch failed for {url}: {e}")
                    self.active_crawls[job_id]['errors'].append({'url': url, 'error': str(e)})
                    self.active_crawls[job_id]['urls_completed'] += 1
                    continue

                self.active_crawls[job_id]['urls_completed'] += 1

                doc_update = None
                if page_data:
                    total_pages += 1
                    self.active_crawls[job_id]['pages_crawled'] = self.active_crawls[job_id]['urls_completed']
                    doc_update = self._process_crawled_page(
                        job_id,
                        page_data,
                        collection_id,
                        created_by,
                        seen_hashes_global
                    )

                # Emit progress after each processed page (even on failures)
                self._emit_progress(job_id, {
                    'status': 'running',
                    'stage': 'crawling',
                    'pages_crawled': self.active_crawls[job_id]['urls_completed'],
                    'max_pages': len(urls),
                    'current_url': url,
                    'urls_total': len(urls),
                    'urls_completed': self.active_crawls[job_id]['urls_completed'],
                    'images_extracted': self.active_crawls[job_id].get('images_extracted', 0),
                    'crawler_type': crawler_type
                })
                page_payload = {
                    'url': url,
                    'page_number': self.active_crawls[job_id]['urls_completed'],
                    'documents_created': self.active_crawls[job_id]['documents_created'],
                    'documents_linked': self.active_crawls[job_id]['documents_linked'],
                    'images_extracted': self.active_crawls[job_id].get('images_extracted', 0)
                }
                if doc_update:
                    page_payload.update({
                        'collection_id': collection_id,
                        'document_action': doc_update.get('action'),
                        'document': doc_update.get('document')
                    })
                self._emit_page_crawled(job_id, page_payload)

        return total_pages

    def _process_urls_playwright(
        self,
        job_id: str,
        urls: List[str],
        collection_id: int,
        created_by: str,
        seen_hashes_global: set,
        use_vision_llm: bool,
        crawler_type: str
    ) -> int:
        """
        Fetch URLs with Playwright (screenshots + vision) using a bounded async worker pool.
        Emits progress updates in real-time as each URL is processed.
        """
        if not urls:
            return 0

        total_pages = 0
        total_urls = len(urls)

        # Use a queue to collect results and process them with progress updates
        from queue import Queue
        import threading

        result_queue = Queue()
        processing_complete = threading.Event()

        async def run():
            from .playwright_crawler import PlaywrightCrawler

            max_workers = min(4, max(1, len(urls)))
            sem = asyncio.Semaphore(max_workers)

            async def fetch_url(target_url: str):
                async with sem:
                    try:
                        crawler = PlaywrightCrawler(
                            base_url=target_url,
                            max_pages=1,
                            max_depth=0,
                            delay_seconds=0.5,
                            extract_images=True,
                            use_vision_llm=use_vision_llm,
                            litellm_base_url=os.environ.get('LITELLM_BASE_URL'),
                            litellm_api_key=os.environ.get('LITELLM_API_KEY')
                        )
                        pages = await crawler.crawl_async()
                        page = pages[0] if pages else None
                        return target_url, page, crawler.stats
                    except Exception as e:
                        logger.error(f"[Job {job_id}] Playwright fetch failed for {target_url}: {e}")
                        return target_url, None, {'screenshots_taken': 0, 'vision_extractions': 0}

            tasks = [fetch_url(u) for u in urls]
            for coro in asyncio.as_completed(tasks):
                result = await coro
                result_queue.put(result)

            processing_complete.set()

        # Start async crawling in a separate thread
        def run_async():
            asyncio.run(run())

        async_thread = threading.Thread(target=run_async, daemon=True)
        async_thread.start()

        # Process results as they come in (this runs in the main thread)
        processed_count = 0
        while processed_count < total_urls:
            try:
                # Wait for next result with timeout
                result = result_queue.get(timeout=120)
                url, page_data, stats = result
                processed_count += 1

                self.active_crawls[job_id]['urls_completed'] = processed_count

                doc_update = None
                if page_data:
                    total_pages += 1
                    self.active_crawls[job_id]['pages_crawled'] = total_pages
                    doc_update = self._process_crawled_page(
                        job_id,
                        page_data,
                        collection_id,
                        created_by,
                        seen_hashes_global
                    )

                # Aggregate Playwright-specific stats
                self.active_crawls[job_id]['screenshots_taken'] = self.active_crawls[job_id].get('screenshots_taken', 0) + stats.get('screenshots_taken', 0)
                self.active_crawls[job_id]['vision_extractions'] = self.active_crawls[job_id].get('vision_extractions', 0) + stats.get('vision_extractions', 0)

                # Emit progress update immediately
                self._emit_progress(job_id, {
                    'status': 'running',
                    'stage': 'crawling',
                    'pages_crawled': total_pages,
                    'max_pages': total_urls,
                    'current_url': url,
                    'urls_total': total_urls,
                    'urls_completed': processed_count,
                    'documents_created': self.active_crawls[job_id]['documents_created'],
                    'documents_linked': self.active_crawls[job_id]['documents_linked'],
                    'images_extracted': self.active_crawls[job_id].get('images_extracted', 0),
                    'screenshots_taken': self.active_crawls[job_id].get('screenshots_taken', 0),
                    'crawler_type': crawler_type
                })
                page_payload = {
                    'url': url,
                    'page_number': processed_count,
                    'documents_created': self.active_crawls[job_id]['documents_created'],
                    'documents_linked': self.active_crawls[job_id]['documents_linked'],
                    'images_extracted': self.active_crawls[job_id].get('images_extracted', 0),
                    'screenshots_taken': self.active_crawls[job_id].get('screenshots_taken', 0)
                }
                if doc_update:
                    page_payload.update({
                        'collection_id': collection_id,
                        'document_action': doc_update.get('action'),
                        'document': doc_update.get('document')
                    })
                self._emit_page_crawled(job_id, page_payload)

            except Exception as e:
                if processing_complete.is_set() and result_queue.empty():
                    break
                logger.warning(f"[Job {job_id}] Error processing result: {e}")
                continue

        # Wait for async thread to finish
        async_thread.join(timeout=10)

        return total_pages


# Singleton instance
crawler_service = CrawlerService()
