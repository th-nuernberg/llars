# crawler_processing.py
"""
URL processing strategies for the crawler service.

This module implements two crawling strategies:
1. Basic Crawler: Fast, parallel HTTP requests with BeautifulSoup parsing
2. Playwright Crawler: JavaScript-rendered pages with screenshots and Vision-LLM

Both strategies share the same document processing pipeline but differ in
how they fetch and extract content from web pages.

Used by: crawler_service.py
Depends on: crawler_document.py, crawler_events.py, crawler_core.py, playwright_crawler.py
"""

from __future__ import annotations

import os
import asyncio
import logging
import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Set

from .crawler_document import process_crawled_page
from .crawler_events import emit_progress, emit_page_crawled

logger = logging.getLogger(__name__)


# =============================================================================
# BASIC CRAWLER PROCESSING
# =============================================================================

def process_urls_basic(
    job_id: str,
    urls: List[str],
    collection_id: int,
    created_by: str,
    seen_hashes_global: Set[str],
    crawler_type: str,
    active_crawls: Dict[str, Dict],
    socketio: Any
) -> int:
    """
    Fetch URLs in parallel using the basic crawler (requests + BeautifulSoup).

    Uses a thread pool to fetch multiple URLs concurrently for speed.
    Each URL is fetched independently, and results are processed as
    they complete.

    Args:
        job_id: UUID of the crawl job
        urls: List of URLs to fetch
        collection_id: Target collection ID
        created_by: Username
        seen_hashes_global: Set of content hashes for deduplication
        crawler_type: 'Basic' (for progress display)
        active_crawls: Active jobs dict (for stats and progress)
        socketio: Flask-SocketIO instance for progress events

    Returns:
        Total number of pages successfully crawled

    Performance:
        - Uses 2-8 worker threads depending on URL count
        - 50ms delay between requests (configured in WebCrawler)
        - Parallel fetching significantly speeds up multi-page crawls
    """
    from .crawler_core import WebCrawler

    if not urls:
        return 0

    # Scale workers with URL count (min 2, max 8)
    fetch_workers = max(2, min(8, len(urls)))

    def fetch_single(target_url: str) -> Dict:
        """Fetch a single URL using the basic crawler."""
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
        # Submit all fetch tasks
        future_map = {executor.submit(fetch_single, u): u for u in urls}

        # Process results as they complete (not in order)
        for future in as_completed(future_map):
            url = future_map[future]

            try:
                page_data = future.result()
            except Exception as e:
                logger.error(f"[Job {job_id}] Fetch failed for {url}: {e}")
                active_crawls[job_id]['errors'].append({'url': url, 'error': str(e)})
                active_crawls[job_id]['urls_completed'] += 1
                continue

            active_crawls[job_id]['urls_completed'] += 1

            # Process the crawled page (create/link document)
            doc_update = None
            if page_data:
                total_pages += 1
                active_crawls[job_id]['pages_crawled'] = active_crawls[job_id]['urls_completed']
                doc_update = process_crawled_page(
                    job_id=job_id,
                    page=page_data,
                    collection_id=collection_id,
                    created_by=created_by,
                    seen_hashes=seen_hashes_global,
                    active_crawls=active_crawls
                )

            # Emit progress update via WebSocket
            _emit_basic_progress(
                job_id=job_id,
                url=url,
                urls=urls,
                crawler_type=crawler_type,
                active_crawls=active_crawls,
                socketio=socketio,
                collection_id=collection_id,
                doc_update=doc_update
            )

    return total_pages


def _emit_basic_progress(
    job_id: str,
    url: str,
    urls: List[str],
    crawler_type: str,
    active_crawls: Dict[str, Dict],
    socketio: Any,
    collection_id: int,
    doc_update: Dict
) -> None:
    """Emit progress events for basic crawler."""
    emit_progress(socketio, job_id, {
        'status': 'running',
        'stage': 'crawling',
        'pages_crawled': active_crawls[job_id]['urls_completed'],
        'max_pages': len(urls),
        'current_url': url,
        'urls_total': len(urls),
        'urls_completed': active_crawls[job_id]['urls_completed'],
        'images_extracted': active_crawls[job_id].get('images_extracted', 0),
        'crawler_type': crawler_type
    }, active_crawls)

    page_payload = {
        'url': url,
        'page_number': active_crawls[job_id]['urls_completed'],
        'documents_created': active_crawls[job_id]['documents_created'],
        'documents_linked': active_crawls[job_id]['documents_linked'],
        'images_extracted': active_crawls[job_id].get('images_extracted', 0)
    }
    if doc_update:
        page_payload.update({
            'collection_id': collection_id,
            'document_action': doc_update.get('action'),
            'document': doc_update.get('document')
        })
    emit_page_crawled(socketio, job_id, page_payload)


# =============================================================================
# PLAYWRIGHT CRAWLER PROCESSING
# =============================================================================

def process_urls_playwright(
    job_id: str,
    urls: List[str],
    collection_id: int,
    created_by: str,
    seen_hashes_global: Set[str],
    use_vision_llm: bool,
    take_screenshots: bool,
    crawler_type: str,
    active_crawls: Dict[str, Dict],
    socketio: Any
) -> int:
    """
    Fetch URLs with Playwright (screenshots + vision) using async worker pool.

    Uses Playwright's headless browser for JavaScript-heavy sites.
    Optionally captures screenshots and uses Vision-LLM for content extraction.
    Emits progress updates in real-time as each URL is processed.

    Args:
        job_id: UUID of the crawl job
        urls: List of URLs to fetch
        collection_id: Target collection ID
        created_by: Username
        seen_hashes_global: Set of content hashes for deduplication
        use_vision_llm: Whether to use Vision-LLM for extraction
        take_screenshots: Whether to capture screenshots
        crawler_type: 'Playwright' (for progress display)
        active_crawls: Active jobs dict (for stats and progress)
        socketio: Flask-SocketIO instance for progress events

    Returns:
        Total number of pages successfully crawled

    Architecture:
        - Runs async Playwright in a background thread
        - Uses semaphore to limit concurrent browsers (max 4)
        - Results are queued and processed in the main thread
        - Progress events emitted as URLs start and complete
    """
    if not urls:
        return 0

    total_pages = 0
    total_urls = len(urls)

    # Queues for inter-thread communication
    result_queue = Queue()     # Completed URL results
    start_queue = Queue()      # "Starting URL" notifications
    processing_complete = threading.Event()

    # Validate vision model if needed
    effective_use_vision_llm = use_vision_llm and take_screenshots
    vision_model_id = None

    if effective_use_vision_llm:
        vision_model_id = _get_vision_model_id()

    # =================================================================
    # ASYNC CRAWLING COROUTINE
    # =================================================================
    async def run():
        """Run Playwright crawling asynchronously."""
        from .playwright_crawler import PlaywrightCrawler

        # Limit concurrent browser instances
        max_workers = min(4, max(1, len(urls)))
        sem = asyncio.Semaphore(max_workers)

        async def fetch_url(target_url: str, url_index: int):
            """Fetch a single URL with Playwright."""
            async with sem:
                # Signal that we're starting this URL
                start_queue.put(('start', target_url, url_index))

                try:
                    crawler = PlaywrightCrawler(
                        base_url=target_url,
                        max_pages=1,
                        max_depth=0,
                        delay_seconds=0.3,           # Faster than default
                        extract_images=True,
                        use_vision_llm=effective_use_vision_llm,
                        vision_llm_model=vision_model_id,
                        litellm_base_url=os.environ.get('LITELLM_BASE_URL'),
                        litellm_api_key=os.environ.get('LITELLM_API_KEY'),
                        take_screenshots=take_screenshots,
                        fast_mode=False
                    )
                    pages = await crawler.crawl_async()
                    page = pages[0] if pages else None
                    return target_url, page, crawler.stats

                except Exception as e:
                    logger.error(f"[Job {job_id}] Playwright fetch failed for {target_url}: {e}")
                    return target_url, None, {'screenshots_taken': 0, 'vision_extractions': 0}

        # Create tasks for all URLs
        tasks = [fetch_url(u, i) for i, u in enumerate(urls)]

        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            result_queue.put(result)

        processing_complete.set()

    # =================================================================
    # START ASYNC THREAD
    # =================================================================
    def run_async():
        """Wrapper to run async code in a thread."""
        asyncio.run(run())

    async_thread = threading.Thread(target=run_async, daemon=True)
    async_thread.start()

    # =================================================================
    # PROCESS RESULTS IN MAIN THREAD
    # =================================================================
    processed_count = 0
    active_urls = set()  # Track URLs currently being crawled

    while processed_count < total_urls:
        # Process "starting URL" events (non-blocking)
        _process_start_events(
            start_queue=start_queue,
            active_urls=active_urls,
            job_id=job_id,
            processed_count=processed_count,
            total_urls=total_urls,
            crawler_type=crawler_type,
            active_crawls=active_crawls,
            socketio=socketio
        )

        # Wait for next result (with timeout to check start_queue)
        try:
            result = result_queue.get(timeout=0.5)
            url, page_data, stats = result
            processed_count += 1
            active_urls.discard(url)

            active_crawls[job_id]['urls_completed'] = processed_count

            # Process the crawled page
            doc_update = None
            if page_data:
                total_pages += 1
                active_crawls[job_id]['pages_crawled'] = total_pages
                doc_update = process_crawled_page(
                    job_id=job_id,
                    page=page_data,
                    collection_id=collection_id,
                    created_by=created_by,
                    seen_hashes=seen_hashes_global,
                    active_crawls=active_crawls
                )

            # Aggregate Playwright-specific stats
            _update_playwright_stats(job_id, stats, active_crawls)

            # Emit progress events
            _emit_playwright_progress(
                job_id=job_id,
                url=url,
                total_pages=total_pages,
                total_urls=total_urls,
                processed_count=processed_count,
                crawler_type=crawler_type,
                active_crawls=active_crawls,
                socketio=socketio,
                collection_id=collection_id,
                doc_update=doc_update
            )

        except Exception as e:
            if processing_complete.is_set() and result_queue.empty():
                break
            # Timeout is expected when waiting for results
            if 'Empty' not in str(type(e).__name__):
                logger.warning(f"[Job {job_id}] Error processing result: {e}")
            continue

    # Wait for async thread to finish
    async_thread.join(timeout=10)

    return total_pages


def _get_vision_model_id() -> str:
    """Get the default vision-capable LLM model ID."""
    from db.models.llm_model import LLMModel
    vision_model_id = LLMModel.get_default_model_id(
        model_type=LLMModel.MODEL_TYPE_LLM,
        supports_vision=True
    )
    if not vision_model_id:
        raise ValueError("No vision-capable LLM model configured in llm_models")
    return vision_model_id


def _process_start_events(
    start_queue: Queue,
    active_urls: Set[str],
    job_id: str,
    processed_count: int,
    total_urls: int,
    crawler_type: str,
    active_crawls: Dict[str, Dict],
    socketio: Any
) -> None:
    """Process 'starting URL' events from the async thread."""
    while not start_queue.empty():
        try:
            event_type, start_url, url_index = start_queue.get_nowait()
            if event_type == 'start':
                active_urls.add(start_url)
                active_crawls[job_id]['current_url'] = start_url

                # Emit progress immediately when starting a URL
                emit_progress(socketio, job_id, {
                    'status': 'running',
                    'stage': 'crawling',
                    'pages_crawled': processed_count,
                    'max_pages': total_urls,
                    'current_url': start_url,
                    'urls_total': total_urls,
                    'urls_completed': processed_count,
                    'documents_created': active_crawls[job_id]['documents_created'],
                    'documents_linked': active_crawls[job_id]['documents_linked'],
                    'images_extracted': active_crawls[job_id].get('images_extracted', 0),
                    'screenshots_taken': active_crawls[job_id].get('screenshots_taken', 0),
                    'crawler_type': crawler_type,
                    'message': 'Crawle Seite...'
                }, active_crawls)
        except Exception:
            break


def _update_playwright_stats(
    job_id: str,
    stats: Dict,
    active_crawls: Dict[str, Dict]
) -> None:
    """Aggregate Playwright-specific statistics."""
    active_crawls[job_id]['screenshots_taken'] = (
        active_crawls[job_id].get('screenshots_taken', 0) +
        stats.get('screenshots_taken', 0)
    )
    active_crawls[job_id]['vision_extractions'] = (
        active_crawls[job_id].get('vision_extractions', 0) +
        stats.get('vision_extractions', 0)
    )

    # Capture brand color from first page (homepage)
    if stats.get('brand_color') and not active_crawls[job_id].get('brand_color'):
        active_crawls[job_id]['brand_color'] = stats.get('brand_color')
        logger.info(f"[Job {job_id}] Captured brand color: {stats.get('brand_color')}")


def _emit_playwright_progress(
    job_id: str,
    url: str,
    total_pages: int,
    total_urls: int,
    processed_count: int,
    crawler_type: str,
    active_crawls: Dict[str, Dict],
    socketio: Any,
    collection_id: int,
    doc_update: Dict
) -> None:
    """Emit progress events for Playwright crawler."""
    emit_progress(socketio, job_id, {
        'status': 'running',
        'stage': 'crawling',
        'pages_crawled': total_pages,
        'max_pages': total_urls,
        'current_url': url,
        'urls_total': total_urls,
        'urls_completed': processed_count,
        'documents_created': active_crawls[job_id]['documents_created'],
        'documents_linked': active_crawls[job_id]['documents_linked'],
        'images_extracted': active_crawls[job_id].get('images_extracted', 0),
        'screenshots_taken': active_crawls[job_id].get('screenshots_taken', 0),
        'crawler_type': crawler_type
    }, active_crawls)

    page_payload = {
        'url': url,
        'page_number': processed_count,
        'documents_created': active_crawls[job_id]['documents_created'],
        'documents_linked': active_crawls[job_id]['documents_linked'],
        'images_extracted': active_crawls[job_id].get('images_extracted', 0),
        'screenshots_taken': active_crawls[job_id].get('screenshots_taken', 0)
    }
    if doc_update:
        page_payload.update({
            'collection_id': collection_id,
            'document_action': doc_update.get('action'),
            'document': doc_update.get('document')
        })
    emit_page_crawled(socketio, job_id, page_payload)
