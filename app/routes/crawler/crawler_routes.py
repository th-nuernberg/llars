# crawler_routes.py
"""
API routes for web crawler management.
Supports background crawling with WebSocket live updates.
"""

import logging
import threading
from flask import Blueprint, request, jsonify, g, current_app
from decorators.permission_decorator import require_permission
from decorators.error_handler import handle_api_errors, NotFoundError, ValidationError, ConflictError
from services.crawler.web_crawler import crawler_service, WebCrawler
from auth.auth_utils import AuthUtils

logger = logging.getLogger(__name__)

crawler_blueprint = Blueprint('crawler', __name__, url_prefix='/api/crawler')


def init_crawler_socketio(socketio):
    """Initialize crawler service with SocketIO for live updates."""
    crawler_service.set_socketio(socketio)
    logger.info("[Crawler] WebSocket integration initialized")


# ============================================================================
# CRAWLER JOB ROUTES
# ============================================================================

@crawler_blueprint.route('/start', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='crawler')
def start_crawl():
    """
    Start a new web crawl job in background with WebSocket live updates.

    Request body:
    {
        "urls": ["https://example.com"],
        "collection_name": "My Website Docs",           // Name for new collection (ignored if existing_collection_id is set)
        "collection_description": "Crawled documentation",
        "max_pages_per_site": 50,
        "max_depth": 3,
        "existing_collection_id": null,                 // If set, add documents to existing collection
        "use_playwright": true,                         // Use headless browser for JS rendering (default: true)
        "use_vision_llm": true                          // Use Vision-LLM for intelligent data extraction (default: true)
    }

    Collection modes:
    - New collection: Omit existing_collection_id, provide collection_name
    - Existing collection: Set existing_collection_id, collection_name is optional

    Document handling:
    - If content hash already exists: Document is LINKED to collection (no duplicate)
    - If content is new: Document is created and LINKED

    Crawler modes:
    - Playwright (default): Uses headless Chromium browser for full JS rendering
      - Takes screenshots of each page
      - Supports Vision-LLM for intelligent data extraction from screenshots
      - Better for modern JavaScript-heavy websites
    - Basic: Uses simple HTTP requests (faster, no JS support)
      - Falls back to regex-based data extraction
      - Better for static HTML websites

    Returns immediately with job_id. Connect via WebSocket to crawler:{job_id}
    room for live progress updates.
    """
    data = request.get_json()
    if not data:
        raise ValidationError('No data provided')

    urls = data.get('urls', [])
    if not urls:
        raise ValidationError('No URLs provided')

    # Validate URLs
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            raise ValidationError(f'Invalid URL format: {url}')

    # Collection mode: existing or new
    existing_collection_id = data.get('existing_collection_id')

    collection_name = data.get('collection_name')
    if not collection_name and not existing_collection_id:
        # Generate name from first URL domain
        from urllib.parse import urlparse
        domain = urlparse(urls[0]).netloc
        collection_name = f"Webcrawl: {domain}"

    username = AuthUtils.extract_username_without_validation() or 'unknown'

    # Crawler options
    use_playwright = data.get('use_playwright', True)
    use_vision_llm = data.get('use_vision_llm', True)

    # Start background crawl with WebSocket support
    job_id = crawler_service.start_crawl_background(
        urls=urls,
        collection_name=collection_name or '',
        collection_description=data.get('collection_description', ''),
        max_pages_per_site=data.get('max_pages_per_site', 50),
        max_depth=data.get('max_depth', 3),
        created_by=username,
        app=current_app._get_current_object(),
        existing_collection_id=existing_collection_id,
        use_playwright=use_playwright,
        use_vision_llm=use_vision_llm
    )

    # Return immediately with job info
    response_data = {
        'success': True,
        'message': 'Crawl job started',
        'job_id': job_id,
        'urls': urls,
        'websocket_room': f'crawler_{job_id}',
        'crawler_config': {
            'use_playwright': use_playwright,
            'use_vision_llm': use_vision_llm
        }
    }

    # If collection was pre-created, expose its ID immediately
    job_status = crawler_service.get_job_status(job_id) or {}
    if job_status.get('collection_id'):
        response_data['collection_id'] = job_status['collection_id']

    if existing_collection_id:
        response_data['mode'] = 'add_to_existing'
        response_data['existing_collection_id'] = existing_collection_id
    else:
        response_data['mode'] = 'new_collection'
        response_data['collection_name'] = collection_name

    return jsonify(response_data), 202


@crawler_blueprint.route('/start-sync', methods=['POST'])
@require_permission('feature:rag:edit')
@handle_api_errors(logger_name='crawler')
def start_crawl_sync():
    """
    Start a synchronous web crawl (waits for completion).
    Use this for smaller crawls or testing.
    """
    data = request.get_json()
    if not data:
        raise ValidationError('No data provided')

    urls = data.get('urls', [])
    if not urls:
        raise ValidationError('No URLs provided')

    collection_name = data.get('collection_name')
    if not collection_name:
        from urllib.parse import urlparse
        domain = urlparse(urls[0]).netloc
        collection_name = f"Webcrawl: {domain}"

    username = AuthUtils.extract_username_without_validation() or 'unknown'

    result = crawler_service.start_crawl(
        urls=urls,
        collection_name=collection_name,
        collection_description=data.get('collection_description', ''),
        max_pages_per_site=data.get('max_pages_per_site', 20),
        max_depth=data.get('max_depth', 2),
        created_by=username
    )

    return jsonify({
        'success': True,
        'result': result
    })


@crawler_blueprint.route('/jobs', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='crawler')
def list_jobs():
    """List all crawl jobs."""
    jobs = crawler_service.list_jobs()
    return jsonify({
        'success': True,
        'jobs': jobs,
        'count': len(jobs)
    })


@crawler_blueprint.route('/jobs/<job_id>', methods=['GET'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='crawler')
def get_job_status(job_id):
    """Get status of a specific crawl job."""
    job = crawler_service.get_job_status(job_id)
    if not job:
        raise NotFoundError('Job not found')

    return jsonify({
        'success': True,
        'job': {'job_id': job_id, **job}
    })


# ============================================================================
# CRAWLER PREVIEW / TEST ROUTES
# ============================================================================

@crawler_blueprint.route('/preview', methods=['POST'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='crawler')
def preview_crawl():
    """
    Preview what would be crawled without actually crawling.
    Fetches the first page and extracts links.
    """
    data = request.get_json()
    url = data.get('url')

    if not url:
        raise ValidationError('URL is required')

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    crawler = WebCrawler(
        base_url=url,
        max_pages=1,
        max_depth=0
    )

    # Just fetch the first page
    html = crawler._fetch_page(url)
    if not html:
        raise ValidationError('Could not fetch URL')

    # Extract content preview
    text, metadata = crawler._extract_text(html, url)

    # Extract links
    links = crawler._extract_links(html, url)
    internal_links = [l for l in links if crawler._is_same_domain(l)]

    return jsonify({
        'success': True,
        'preview': {
            'url': url,
            'title': metadata.get('title', ''),
            'description': metadata.get('description', ''),
            'content_preview': text[:1000] + '...' if len(text) > 1000 else text,
            'content_length': len(text),
            'internal_links_count': len(internal_links),
            'internal_links_sample': internal_links[:10],
            'total_links_count': len(links)
        }
    })


@crawler_blueprint.route('/test-fetch', methods=['POST'])
@require_permission('feature:rag:view')
@handle_api_errors(logger_name='crawler')
def test_fetch():
    """
    Test fetching a single URL and return extracted content.
    Useful for debugging and testing the crawler.
    """
    data = request.get_json()
    url = data.get('url')

    if not url:
        raise ValidationError('URL is required')

    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    crawler = WebCrawler(base_url=url, max_pages=1)

    # Fetch page
    html = crawler._fetch_page(url)
    if not html:
        raise ValidationError('Could not fetch URL')

    # Extract content
    text, metadata = crawler._extract_text(html, url)

    return jsonify({
        'success': True,
        'result': {
            'url': url,
            'metadata': metadata,
            'content': text,
            'content_length': len(text),
            'html_length': len(html)
        }
    })


# ============================================================================
# CHATBOT INTEGRATION ROUTES
# ============================================================================

@crawler_blueprint.route('/crawl-for-chatbot', methods=['POST'])
@require_permission('feature:chatbots:edit')
@handle_api_errors(logger_name='crawler')
def crawl_for_chatbot():
    """
    Crawl URLs and create a collection for a chatbot.
    Returns the collection_id for assignment.
    """
    data = request.get_json()
    if not data:
        raise ValidationError('No data provided')

    urls = data.get('urls', [])
    chatbot_name = data.get('chatbot_name', 'Chatbot')

    if not urls:
        raise ValidationError('No URLs provided')

    username = AuthUtils.extract_username_without_validation() or 'unknown'

    # Generate collection name
    from urllib.parse import urlparse
    domains = [urlparse(u).netloc for u in urls[:3]]
    collection_name = f"{chatbot_name} - Web: {', '.join(domains)}"

    # Run crawl synchronously (smaller scope for chatbot)
    result = crawler_service.start_crawl(
        urls=urls,
        collection_name=collection_name,
        collection_description=f"Automatisch gecrawlt für Chatbot '{chatbot_name}'",
        max_pages_per_site=data.get('max_pages', 30),
        max_depth=data.get('max_depth', 2),
        created_by=username
    )

    if result['status'] == 'completed':
        return jsonify({
            'success': True,
            'collection_id': result['collection_id'],
            'pages_crawled': result['pages_crawled'],
            'documents_created': result['documents_created'],
            'message': f"Collection '{collection_name}' erstellt mit {result['documents_created']} Dokumenten"
        })
    else:
        raise ValidationError('Crawl failed', details=result)
