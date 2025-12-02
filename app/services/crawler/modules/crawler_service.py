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
            except:
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
        existing_collection_id: Optional[int] = None
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

        Returns:
            job_id: The ID of the started crawl job
        """
        job_id = str(uuid.uuid4())

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
            'errors': [],
            'queued_at': datetime.now().isoformat()
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
                        existing_collection_id
                    )
            else:
                self._run_background_crawl(
                    job_id, urls, collection_name, collection_description,
                    max_pages_per_site, max_depth, created_by,
                    existing_collection_id
                )

        # Start background thread
        thread = threading.Thread(target=run_crawl_with_context, daemon=True)
        thread.start()
        self._background_threads[job_id] = thread

        logger.info(f"[Job {job_id}] Background crawl started for {len(urls)} URLs (existing_collection_id={existing_collection_id})")

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
        existing_collection_id: Optional[int] = None
    ):
        """
        Internal method to run crawl in background.

        Implements document linking logic:
        - If a document with the same content hash already exists, it is LINKED to the collection
        - If the document is new, it is created and linked
        - Documents can exist in multiple collections via CollectionDocumentLink
        """
        from db.db import db
        from db.tables import RAGCollection, RAGDocument, RAGProcessingQueue, CollectionDocumentLink

        self.active_crawls[job_id]['status'] = 'running'
        self.active_crawls[job_id]['started_at'] = datetime.now().isoformat()

        # Emit started event
        self._emit_progress(job_id, {
            'status': 'running',
            'pages_crawled': 0,
            'max_pages': max_pages_per_site * len(urls),
            'message': 'Crawl gestartet...'
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
                logger.info(f"[Job {job_id}] Crawling URL {url_index + 1}/{len(urls)}: {url}")

                crawler = WebCrawler(
                    base_url=url,
                    max_pages=max_pages_per_site,
                    max_depth=max_depth,
                    delay_seconds=1.0
                )

                # Track seen hashes for deduplication during this crawl
                seen_hashes_in_crawl = set()

                def progress_callback(current, total, page_url):
                    self.active_crawls[job_id]['pages_crawled'] = total_pages + current
                    self.active_crawls[job_id]['current_url'] = page_url
                    docs_created = self.active_crawls[job_id]['documents_created']
                    docs_linked = self.active_crawls[job_id]['documents_linked']
                    self._emit_progress(job_id, {
                        'status': 'running',
                        'pages_crawled': total_pages + current,
                        'max_pages': max_pages_per_site * len(urls),
                        'current_url': page_url,
                        'current_url_index': url_index + 1,
                        'total_urls': len(urls),
                        'documents_created': docs_created,
                        'documents_linked': docs_linked
                    })
                    self._emit_page_crawled(job_id, {
                        'url': page_url,
                        'page_number': total_pages + current,
                        'documents_created': docs_created,
                        'documents_linked': docs_linked
                    })

                def page_callback(page_data):
                    """Process each page immediately as it's crawled."""
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

            logger.info(f"[Job {job_id}] Background crawl completed: {total_pages} pages, {docs_created} documents neu, {docs_linked} documents verlinkt")

            self._emit_complete(job_id, {
                'status': 'completed',
                'collection_id': collection_id,
                'pages_crawled': total_pages,
                'documents_created': docs_created,
                'documents_linked': docs_linked,
                'errors_count': len(self.active_crawls[job_id]['errors'])
            })

            self._emit_jobs_updated()

        except Exception as e:
            logger.error(f"[Job {job_id}] Background crawl failed: {e}")
            self.active_crawls[job_id]['status'] = 'failed'
            self.active_crawls[job_id]['error'] = str(e)
            try:
                db.session.rollback()
            except:
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
        """
        from db.db import db
        from db.tables import RAGDocument, RAGProcessingQueue, CollectionDocumentLink

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
                logger.info(f"[Job {job_id}] Created new document {doc.id} for {page['url']}")

        except Exception as e:
            logger.error(f"Error processing document for {page['url']}: {e}")
            db.session.rollback()
            self.active_crawls[job_id]['errors'].append({
                'url': page['url'],
                'error': str(e)
            })


# Singleton instance
crawler_service = CrawlerService()
