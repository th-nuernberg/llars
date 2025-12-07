# crawler_routes.py
"""
API routes for web crawler management.
Supports background crawling with WebSocket live updates.
"""

import logging
import threading
from flask import Blueprint, request, jsonify, g, current_app
from decorators.permission_decorator import require_permission
from services.crawler.web_crawler import crawler_service, WebCrawler
import jwt

logger = logging.getLogger(__name__)

crawler_blueprint = Blueprint('crawler', __name__, url_prefix='/api/crawler')


def init_crawler_socketio(socketio):
    """Initialize crawler service with SocketIO for live updates."""
    crawler_service.set_socketio(socketio)
    logger.info("[Crawler] WebSocket integration initialized")


def get_username_from_token():
    """Extract username from JWT token."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            return decoded.get('preferred_username', 'unknown')
        except:
            pass
    return 'unknown'


# ============================================================================
# CRAWLER JOB ROUTES
# ============================================================================

@crawler_blueprint.route('/start', methods=['POST'])
@require_permission('feature:rag:edit')
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
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        urls = data.get('urls', [])
        if not urls:
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400

        # Validate URLs
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                return jsonify({
                    'success': False,
                    'error': f'Invalid URL format: {url}'
                }), 400

        # Collection mode: existing or new
        existing_collection_id = data.get('existing_collection_id')

        collection_name = data.get('collection_name')
        if not collection_name and not existing_collection_id:
            # Generate name from first URL domain
            from urllib.parse import urlparse
            domain = urlparse(urls[0]).netloc
            collection_name = f"Webcrawl: {domain}"

        username = get_username_from_token()

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

        if existing_collection_id:
            response_data['mode'] = 'add_to_existing'
            response_data['existing_collection_id'] = existing_collection_id
        else:
            response_data['mode'] = 'new_collection'
            response_data['collection_name'] = collection_name

        return jsonify(response_data), 202

    except Exception as e:
        logger.error(f"Error starting crawl: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crawler_blueprint.route('/start-sync', methods=['POST'])
@require_permission('feature:rag:edit')
def start_crawl_sync():
    """
    Start a synchronous web crawl (waits for completion).
    Use this for smaller crawls or testing.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        urls = data.get('urls', [])
        if not urls:
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400

        collection_name = data.get('collection_name')
        if not collection_name:
            from urllib.parse import urlparse
            domain = urlparse(urls[0]).netloc
            collection_name = f"Webcrawl: {domain}"

        username = get_username_from_token()

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

    except Exception as e:
        logger.error(f"Error in sync crawl: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crawler_blueprint.route('/jobs', methods=['GET'])
@require_permission('feature:rag:view')
def list_jobs():
    """List all crawl jobs."""
    try:
        jobs = crawler_service.list_jobs()
        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        })
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crawler_blueprint.route('/jobs/<job_id>', methods=['GET'])
@require_permission('feature:rag:view')
def get_job_status(job_id):
    """Get status of a specific crawl job."""
    try:
        job = crawler_service.get_job_status(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        return jsonify({
            'success': True,
            'job': {'job_id': job_id, **job}
        })
    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CRAWLER PREVIEW / TEST ROUTES
# ============================================================================

@crawler_blueprint.route('/preview', methods=['POST'])
@require_permission('feature:rag:view')
def preview_crawl():
    """
    Preview what would be crawled without actually crawling.
    Fetches the first page and extracts links.
    """
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

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
            return jsonify({
                'success': False,
                'error': 'Could not fetch URL'
            }), 400

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

    except Exception as e:
        logger.error(f"Error in preview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@crawler_blueprint.route('/test-fetch', methods=['POST'])
@require_permission('feature:rag:view')
def test_fetch():
    """
    Test fetching a single URL and return extracted content.
    Useful for debugging and testing the crawler.
    """
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        crawler = WebCrawler(base_url=url, max_pages=1)

        # Fetch page
        html = crawler._fetch_page(url)
        if not html:
            return jsonify({
                'success': False,
                'error': 'Could not fetch URL'
            }), 400

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

    except Exception as e:
        logger.error(f"Error in test fetch: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CHATBOT INTEGRATION ROUTES
# ============================================================================

@crawler_blueprint.route('/crawl-for-chatbot', methods=['POST'])
@require_permission('feature:chatbots:edit')
def crawl_for_chatbot():
    """
    Crawl URLs and create a collection for a chatbot.
    Returns the collection_id for assignment.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        urls = data.get('urls', [])
        chatbot_name = data.get('chatbot_name', 'Chatbot')

        if not urls:
            return jsonify({'success': False, 'error': 'No URLs provided'}), 400

        username = get_username_from_token()

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
            return jsonify({
                'success': False,
                'error': 'Crawl failed',
                'details': result
            }), 500

    except Exception as e:
        logger.error(f"Error in crawl for chatbot: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
