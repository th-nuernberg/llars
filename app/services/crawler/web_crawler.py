# web_crawler.py
"""
Intelligent Website Crawler for RAG Collections.

Features:
- Respects robots.txt
- Rate limiting to be friendly
- Extracts clean text from HTML
- Follows internal links (same domain)
- Configurable depth and max pages
- Sitemap.xml support
"""

import os
import re
import uuid
import time
import hashlib
import logging
import requests
import threading
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    Intelligent web crawler that extracts text content from websites.
    Designed to be polite and respect website policies.
    """

    USER_AGENT = "LLARSBot/1.0 (+https://github.com/llars; friendly-crawler)"

    def __init__(
        self,
        base_url: str,
        max_pages: int = 50,
        max_depth: int = 3,
        delay_seconds: float = 1.0,
        timeout: int = 30,
        follow_external: bool = False,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        """
        Initialize the web crawler.

        Args:
            base_url: Starting URL to crawl
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum link depth from base URL
            delay_seconds: Delay between requests (politeness)
            timeout: Request timeout in seconds
            follow_external: Whether to follow links to other domains
            include_patterns: URL patterns to include (regex)
            exclude_patterns: URL patterns to exclude (regex)
        """
        self.base_url = self._normalize_url(base_url)
        self.base_domain = urlparse(self.base_url).netloc
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay_seconds = delay_seconds
        self.timeout = timeout
        self.follow_external = follow_external

        # URL filtering patterns
        self.include_patterns = [re.compile(p) for p in (include_patterns or [])]
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or [
            r'\.pdf$', r'\.zip$', r'\.exe$', r'\.dmg$',
            r'\.jpg$', r'\.jpeg$', r'\.png$', r'\.gif$', r'\.svg$',
            r'\.mp3$', r'\.mp4$', r'\.avi$', r'\.mov$',
            r'/login', r'/logout', r'/signin', r'/signup',
            r'/cart', r'/checkout', r'/account',
            r'\?.*utm_', r'#'
        ])]

        # State tracking
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[Dict] = []
        self.robots_parser: Optional[RobotFileParser] = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_skipped': 0,
            'errors': 0,
            'total_bytes': 0,
            'start_time': None,
            'end_time': None
        }

    def _normalize_url(self, url: str) -> str:
        """Normalize URL for consistent comparison."""
        parsed = urlparse(url)
        # Ensure scheme
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        # Remove trailing slash and fragments
        path = parsed.path.rstrip('/') or '/'
        return urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            path,
            '', '', ''
        ))

    def _is_same_domain(self, url: str) -> bool:
        """Check if URL belongs to the same domain."""
        return urlparse(url).netloc.lower() == self.base_domain.lower()

    def _should_crawl(self, url: str) -> bool:
        """Determine if a URL should be crawled."""
        # Already visited
        if url in self.visited_urls:
            return False

        # Check domain
        if not self.follow_external and not self._is_same_domain(url):
            return False

        # Check robots.txt
        if self.robots_parser and not self.robots_parser.can_fetch(self.USER_AGENT, url):
            logger.debug(f"Robots.txt disallows: {url}")
            return False

        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern.search(url):
                logger.debug(f"Excluded by pattern: {url}")
                return False

        # Check include patterns (if any specified, URL must match at least one)
        if self.include_patterns:
            if not any(p.search(url) for p in self.include_patterns):
                return False

        return True

    def _load_robots_txt(self):
        """Load and parse robots.txt."""
        try:
            robots_url = urljoin(self.base_url, '/robots.txt')
            self.robots_parser = RobotFileParser()
            self.robots_parser.set_url(robots_url)
            self.robots_parser.read()
            logger.info(f"Loaded robots.txt from {robots_url}")

            # Try to get crawl delay from robots.txt
            crawl_delay = self.robots_parser.crawl_delay(self.USER_AGENT)
            if crawl_delay:
                self.delay_seconds = max(self.delay_seconds, crawl_delay)
                logger.info(f"Using crawl delay from robots.txt: {self.delay_seconds}s")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}")
            self.robots_parser = None

    def _extract_text(self, html: str, url: str) -> Tuple[str, Dict]:
        """
        Extract clean text content from HTML.

        Returns:
            Tuple of (text_content, metadata)
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract metadata
        metadata = {
            'url': url,
            'title': '',
            'description': '',
            'keywords': '',
            'language': 'de',
            'author': ''
        }

        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)

        # Meta tags
        for meta in soup.find_all('meta'):
            name = (meta.get('name') or meta.get('property') or '').lower()
            content = meta.get('content', '')

            if name in ['description', 'og:description']:
                metadata['description'] = content
            elif name == 'keywords':
                metadata['keywords'] = content
            elif name == 'author':
                metadata['author'] = content
            elif name in ['language', 'og:locale']:
                metadata['language'] = content[:2] if content else 'de'

        # Remove unwanted elements
        for element in soup.find_all([
            'script', 'style', 'nav', 'header', 'footer',
            'aside', 'form', 'button', 'iframe', 'noscript',
            'svg', 'img', 'video', 'audio'
        ]):
            element.decompose()

        # Remove elements by class/id that typically contain non-content
        for selector in [
            '[class*="nav"]', '[class*="menu"]', '[class*="sidebar"]',
            '[class*="footer"]', '[class*="header"]', '[class*="cookie"]',
            '[class*="popup"]', '[class*="modal"]', '[class*="ad-"]',
            '[id*="nav"]', '[id*="menu"]', '[id*="sidebar"]',
            '[id*="footer"]', '[id*="header"]', '[id*="cookie"]'
        ]:
            for element in soup.select(selector):
                element.decompose()

        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('[role="main"]') or
            soup.find(class_=re.compile(r'content|article|post|entry')) or
            soup.find('body')
        )

        if not main_content:
            main_content = soup

        # Extract text with structure
        text_parts = []

        # Add title as header
        if metadata['title']:
            text_parts.append(f"# {metadata['title']}\n")

        # Process headings and paragraphs
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th']):
            text = element.get_text(separator=' ', strip=True)
            if text and len(text) > 10:  # Skip very short content
                tag = element.name
                if tag.startswith('h'):
                    level = int(tag[1])
                    text_parts.append(f"\n{'#' * level} {text}\n")
                elif tag == 'li':
                    text_parts.append(f"- {text}")
                else:
                    text_parts.append(text)

        # Clean up and join
        text = '\n'.join(text_parts)

        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Add source information
        text += f"\n\n---\nQuelle: {url}\n"

        return text.strip(), metadata

    def _extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract and normalize all links from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        links = []

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip javascript, mailto, tel links
            if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)

            if normalized not in links:
                links.append(normalized)

        return links

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch a single page with error handling."""
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()

            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                logger.debug(f"Skipping non-HTML content: {url}")
                return None

            self.stats['total_bytes'] += len(response.content)
            return response.text

        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching {url}")
            self.stats['errors'] += 1
        except requests.exceptions.HTTPError as e:
            logger.warning(f"HTTP error {e.response.status_code} for {url}")
            self.stats['errors'] += 1
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for {url}: {e}")
            self.stats['errors'] += 1

        return None

    def crawl(self, progress_callback=None) -> List[Dict]:
        """
        Execute the crawl starting from base_url.

        Args:
            progress_callback: Optional callback function(current, total, url)

        Returns:
            List of crawled pages with content and metadata
        """
        self.stats['start_time'] = datetime.now()
        logger.info(f"Starting crawl of {self.base_url} (max {self.max_pages} pages, depth {self.max_depth})")

        # Load robots.txt
        self._load_robots_txt()

        # Queue: (url, depth)
        queue = [(self.base_url, 0)]

        while queue and len(self.crawled_pages) < self.max_pages:
            url, depth = queue.pop(0)

            if url in self.visited_urls:
                continue

            if depth > self.max_depth:
                continue

            if not self._should_crawl(url):
                self.stats['pages_skipped'] += 1
                continue

            # Mark as visited
            self.visited_urls.add(url)

            # Fetch page
            logger.info(f"Crawling [{len(self.crawled_pages)+1}/{self.max_pages}]: {url}")
            html = self._fetch_page(url)

            if html:
                # Extract content
                text, metadata = self._extract_text(html, url)

                if text and len(text) > 100:  # Minimum content threshold
                    page_data = {
                        'url': url,
                        'depth': depth,
                        'content': text,
                        'content_length': len(text),
                        'content_hash': hashlib.sha256(text.encode()).hexdigest(),
                        'metadata': metadata,
                        'crawled_at': datetime.now().isoformat()
                    }
                    self.crawled_pages.append(page_data)
                    self.stats['pages_crawled'] += 1

                    # Extract and queue links
                    if depth < self.max_depth:
                        links = self._extract_links(html, url)
                        for link in links:
                            if link not in self.visited_urls:
                                queue.append((link, depth + 1))

                    if progress_callback:
                        progress_callback(
                            len(self.crawled_pages),
                            self.max_pages,
                            url
                        )
                else:
                    logger.debug(f"Skipping page with insufficient content: {url}")
                    self.stats['pages_skipped'] += 1

            # Polite delay
            time.sleep(self.delay_seconds)

        self.stats['end_time'] = datetime.now()
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()

        logger.info(f"Crawl complete: {self.stats['pages_crawled']} pages in {duration:.1f}s")
        logger.info(f"Stats: {self.stats}")

        return self.crawled_pages

    def get_stats(self) -> Dict:
        """Return crawl statistics."""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        return stats


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
                # Track seen hashes within this crawl to avoid duplicates
                seen_hashes = set()

                for page in pages:
                    try:
                        # Skip duplicate content (same hash)
                        content_hash = page['content_hash']
                        if content_hash in seen_hashes:
                            logger.debug(f"Skipping duplicate content for {page['url']}")
                            continue
                        seen_hashes.add(content_hash)

                        # Check if hash already exists in database
                        existing_doc = RAGDocument.query.filter_by(file_hash=content_hash).first()
                        if existing_doc:
                            logger.debug(f"Content already exists in DB for {page['url']}")
                            continue

                        # Generate unique filename
                        filename = f"webcrawl_{job_id[:8]}_{uuid.uuid4().hex[:8]}.md"
                        file_path = os.path.join(self.RAG_DOCS_PATH, filename)

                        # Ensure directory exists
                        os.makedirs(self.RAG_DOCS_PATH, exist_ok=True)

                        # Write content to file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(page['content'])

                        # Create document record
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

                        # Queue for processing
                        queue_entry = RAGProcessingQueue(
                            document_id=doc.id,
                            priority=5,
                            status='queued',
                            created_at=datetime.now()
                        )
                        db.session.add(queue_entry)
                        db.session.commit()  # Commit each document individually

                        self.active_crawls[job_id]['documents_created'] += 1

                    except Exception as e:
                        logger.error(f"Error creating document for {page['url']}: {e}")
                        db.session.rollback()  # Rollback on error, continue with next
                        self.active_crawls[job_id]['errors'].append({
                            'url': page['url'],
                            'error': str(e)
                        })

            # Update collection stats - re-fetch collection to avoid detached instance
            try:
                collection = RAGCollection.query.get(collection_id)
                if collection:
                    collection.document_count = self.active_crawls[job_id]['documents_created']
                    db.session.commit()
            except Exception as e:
                logger.warning(f"Could not update collection stats: {e}")

            self.active_crawls[job_id]['status'] = 'completed'
            self.active_crawls[job_id]['completed_at'] = datetime.now().isoformat()

            logger.info(f"[Job {job_id}] Crawl completed: {total_pages} pages, {self.active_crawls[job_id]['documents_created']} documents")

            # Emit completion event via WebSocket
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
            # Emit error event via WebSocket
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
        app=None
    ) -> str:
        """
        Start a crawl job in the background (continues even if user leaves).

        Returns:
            job_id: The ID of the started crawl job
        """
        from db.db import db
        from db.tables import RAGCollection

        job_id = str(uuid.uuid4())

        # Pre-create job entry immediately
        self.active_crawls[job_id] = {
            'status': 'queued',
            'urls': urls,
            'collection_name': collection_name,
            'pages_crawled': 0,
            'documents_created': 0,
            'errors': [],
            'queued_at': datetime.now().isoformat()
        }

        def run_crawl_with_context():
            """Run crawl in background thread with Flask app context."""
            if app:
                with app.app_context():
                    self._run_background_crawl(
                        job_id, urls, collection_name, collection_description,
                        max_pages_per_site, max_depth, created_by
                    )
            else:
                self._run_background_crawl(
                    job_id, urls, collection_name, collection_description,
                    max_pages_per_site, max_depth, created_by
                )

        # Start background thread
        thread = threading.Thread(target=run_crawl_with_context, daemon=True)
        thread.start()
        self._background_threads[job_id] = thread

        logger.info(f"[Job {job_id}] Background crawl started for {len(urls)} URLs")

        return job_id

    def _run_background_crawl(
        self,
        job_id: str,
        urls: List[str],
        collection_name: str,
        collection_description: str,
        max_pages_per_site: int,
        max_depth: int,
        created_by: str
    ):
        """Internal method to run crawl in background."""
        from db.db import db
        from db.tables import RAGCollection, RAGDocument, RAGProcessingQueue

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
            self.active_crawls[job_id]['collection_id'] = collection_id

            total_pages = 0

            for url_index, url in enumerate(urls):
                logger.info(f"[Job {job_id}] Crawling URL {url_index + 1}/{len(urls)}: {url}")

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
                        'current_url_index': url_index + 1,
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
                # Track seen hashes within this crawl to avoid duplicates
                seen_hashes = set()

                for page in pages:
                    try:
                        # Skip duplicate content (same hash)
                        content_hash = page['content_hash']
                        if content_hash in seen_hashes:
                            logger.debug(f"Skipping duplicate content for {page['url']}")
                            continue
                        seen_hashes.add(content_hash)

                        # Check if hash already exists in database
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
                        db.session.commit()  # Commit each document individually

                        self.active_crawls[job_id]['documents_created'] += 1

                    except Exception as e:
                        logger.error(f"Error creating document for {page['url']}: {e}")
                        db.session.rollback()  # Rollback on error, continue with next
                        self.active_crawls[job_id]['errors'].append({
                            'url': page['url'],
                            'error': str(e)
                        })

            # Update collection stats - re-fetch collection to avoid detached instance
            try:
                collection = RAGCollection.query.get(collection_id)
                if collection:
                    collection.document_count = self.active_crawls[job_id]['documents_created']
                    db.session.commit()
            except Exception as e:
                logger.warning(f"Could not update collection stats: {e}")

            self.active_crawls[job_id]['status'] = 'completed'
            self.active_crawls[job_id]['completed_at'] = datetime.now().isoformat()

            logger.info(f"[Job {job_id}] Background crawl completed: {total_pages} pages")

            # Emit completion event
            self._emit_complete(job_id, {
                'status': 'completed',
                'collection_id': collection_id,
                'pages_crawled': total_pages,
                'documents_created': self.active_crawls[job_id]['documents_created'],
                'errors_count': len(self.active_crawls[job_id]['errors'])
            })

        except Exception as e:
            logger.error(f"[Job {job_id}] Background crawl failed: {e}")
            self.active_crawls[job_id]['status'] = 'failed'
            self.active_crawls[job_id]['error'] = str(e)
            try:
                db.session.rollback()
            except:
                pass
            self._emit_error(job_id, str(e))

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a crawl job."""
        return self.active_crawls.get(job_id)

    def list_jobs(self) -> List[Dict]:
        """List all crawl jobs."""
        return [
            {'job_id': job_id, **status}
            for job_id, status in self.active_crawls.items()
        ]

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running crawl job (marks as cancelled, thread continues until next check)."""
        if job_id in self.active_crawls:
            self.active_crawls[job_id]['status'] = 'cancelled'
            return True
        return False


# Singleton instance
crawler_service = CrawlerService()
