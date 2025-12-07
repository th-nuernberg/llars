"""
CrawlerService Module

Service for managing web crawls and creating RAG collections from crawled content.
Supports background crawling with WebSocket live updates.
"""

import os
import uuid
import logging
import threading
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

from .crawler_core import WebCrawler

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

    RAG_DOCS_PATH = '/app/rag_docs'

    def __init__(self):
        self.active_crawls: Dict[str, Dict] = {}
        self._socketio = None
        self._background_threads: Dict[str, threading.Thread] = {}

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
        from db.tables import RAGCollection, RAGDocument, RAGProcessingQueue

        job_id = str(uuid.uuid4())

        # Create collection
        collection = RAGCollection(
            name=f"crawl_{collection_name.lower().replace(' ', '_')}_{job_id[:8]}",
            display_name=collection_name,
            description=collection_description or f"Webcrawl von: {', '.join(urls)}",
            icon='mdi-web',
            color='#2196F3',
            embedding_model='sentence-transformers/all-MiniLM-L6-v2',
            chunk_size=1000,
            chunk_overlap=200,
            is_active=True,
            created_by=created_by,
            created_at=datetime.now()
        )
        db.session.add(collection)
        db.session.flush()

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
        from db.tables import RAGCollection, RAGDocument, RAGProcessingQueue, CollectionDocumentLink

        self.active_crawls[job_id]['status'] = 'running'
        self.active_crawls[job_id]['started_at'] = datetime.now().isoformat()

        crawler_type = "Playwright" if use_playwright else "Basic"

        # Emit started event
        self._emit_progress(job_id, {
            'status': 'running',
            'pages_crawled': 0,
            'max_pages': max_pages_per_site * len(urls),
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
            else:
                # Create new collection
                collection = RAGCollection(
                    name=f"crawl_{collection_name.lower().replace(' ', '_')}_{job_id[:8]}",
                    display_name=collection_name,
                    description=collection_description or f"Webcrawl von: {', '.join(urls)}",
                    icon='mdi-web',
                    color='#2196F3',
                    embedding_model='sentence-transformers/all-MiniLM-L6-v2',
                    chunk_size=1000,
                    chunk_overlap=200,
                    is_active=True,
                    created_by=created_by,
                    created_at=datetime.now()
                )
                db.session.add(collection)
                db.session.flush()
                collection_id = collection.id
                logger.info(f"[Job {job_id}] Created new collection: {collection.display_name} (ID: {collection_id})")

            self.active_crawls[job_id]['collection_id'] = collection_id
            self.active_crawls[job_id]['documents_linked'] = 0

            total_pages = 0

            for url_index, url in enumerate(urls):
                logger.info(f"[Job {job_id}] Crawling URL {url_index + 1}/{len(urls)}: {url} (using {crawler_type})")

                # Track seen hashes for deduplication during this crawl
                seen_hashes_in_crawl = set()

                # Choose crawler based on use_playwright flag
                if use_playwright and PLAYWRIGHT_AVAILABLE:
                    # Use Playwright crawler with Vision-LLM support
                    crawler = PlaywrightCrawler(
                        base_url=url,
                        max_pages=max_pages_per_site,
                        max_depth=max_depth,
                        delay_seconds=1.5,
                        use_vision_llm=use_vision_llm
                    )
                else:
                    # Fallback to basic WebCrawler
                    crawler = WebCrawler(
                        base_url=url,
                        max_pages=max_pages_per_site,
                        max_depth=max_depth,
                        delay_seconds=1.0
                    )

                def progress_callback(current, total, page_url):
                    self.active_crawls[job_id]['pages_crawled'] = total_pages + current
                    self.active_crawls[job_id]['current_url'] = page_url
                    docs_created = self.active_crawls[job_id]['documents_created']
                    docs_linked = self.active_crawls[job_id]['documents_linked']
                    screenshots = self.active_crawls[job_id].get('screenshots_taken', 0)
                    vision_extractions = self.active_crawls[job_id].get('vision_extractions', 0)
                    self._emit_progress(job_id, {
                        'status': 'running',
                        'pages_crawled': total_pages + current,
                        'max_pages': max_pages_per_site * len(urls),
                        'current_url': page_url,
                        'current_url_index': url_index + 1,
                        'total_urls': len(urls),
                        'documents_created': docs_created,
                        'documents_linked': docs_linked,
                        'screenshots_taken': screenshots,
                        'vision_extractions': vision_extractions,
                        'crawler_type': crawler_type
                    })
                    self._emit_page_crawled(job_id, {
                        'url': page_url,
                        'page_number': total_pages + current,
                        'documents_created': docs_created,
                        'documents_linked': docs_linked
                    })

                def page_callback(page_data):
                    """Process each page immediately as it's crawled."""
                    # Update stats from Playwright crawler
                    if page_data.get('screenshot'):
                        self.active_crawls[job_id]['screenshots_taken'] = \
                            self.active_crawls[job_id].get('screenshots_taken', 0) + 1
                    if page_data.get('structured_data') and page_data.get('crawler_type') == 'playwright':
                        # Check if vision extraction was used (non-empty structured data)
                        if any(v for v in page_data.get('structured_data', {}).values() if v):
                            self.active_crawls[job_id]['vision_extractions'] = \
                                self.active_crawls[job_id].get('vision_extractions', 0) + 1

                    self._process_crawled_page(
                        job_id, page_data, collection_id, created_by,
                        seen_hashes_in_crawl
                    )

                pages = crawler.crawl(progress_callback=progress_callback, page_callback=page_callback)
                total_pages += len(pages)
                # Pages are already processed via page_callback during crawling

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
                return
            seen_hashes.add(content_hash)

            existing_doc = RAGDocument.query.filter_by(file_hash=content_hash).first()

            if existing_doc:
                existing_link = CollectionDocumentLink.query.filter_by(
                    collection_id=collection_id,
                    document_id=existing_doc.id
                ).first()

                if existing_link:
                    logger.debug(f"Document already linked to collection for {page['url']}")
                    return

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

                # Store screenshot as a special chunk (for Vision-LLM queries)
                if screenshot_data and screenshot_path:
                    screenshot_chunk = RAGDocumentChunk(
                        document_id=doc.id,
                        chunk_index=99999,  # Special index for page screenshot
                        content=f"[Screenshot der Webseite: {page['url']}]",
                        has_image=True,
                        image_path=screenshot_path,
                        image_url=page['url'],
                        image_alt_text=f"Screenshot von {page['metadata'].get('title', page['url'])}",
                        image_mime_type='image/png',
                        embedding_status='completed'
                    )
                    db.session.add(screenshot_chunk)
                    logger.info(f"[Job {job_id}] Stored screenshot for document {doc.id}")

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
                crawler_type = page.get('crawler_type', 'basic')
                logger.info(f"[Job {job_id}] Created new document {doc.id} for {page['url']} (crawler: {crawler_type})")

        except Exception as e:
            logger.error(f"Error processing document for {page['url']}: {e}")
            db.session.rollback()
            self.active_crawls[job_id]['errors'].append({
                'url': page['url'],
                'error': str(e)
            })


# Singleton instance
crawler_service = CrawlerService()
