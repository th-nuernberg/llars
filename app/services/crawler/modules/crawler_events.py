# crawler_events.py
"""
WebSocket event emission for the crawler service.

This module handles all real-time communication during crawl jobs:
- Progress updates (pages crawled, current URL, etc.)
- Page completion notifications
- Job completion/error events
- Global job list updates for dashboard

Events are emitted via Socket.IO to connected clients who have
joined the appropriate rooms (job-specific or global crawler room).

Used by: crawler_service.py
Depends on: socketio_handlers/events_crawler.py, services/wizard
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


# =============================================================================
# PROGRESS EVENTS
# =============================================================================

def emit_progress(
    socketio: Any,
    session_id: str,
    data: dict,
    active_crawls: Dict[str, Dict]
) -> None:
    """
    Emit crawl progress update via WebSocket.

    This is the primary progress notification mechanism, called frequently
    during crawling to update the UI in real-time. Also handles special
    case of chatbot builder wizard integration.

    Args:
        socketio: Flask-SocketIO instance
        session_id: The crawl job ID (UUID string)
        data: Progress data dict containing:
            - status: 'planning' | 'running' | 'completed' | 'failed'
            - stage: Current crawl stage
            - pages_crawled: Number of pages processed
            - max_pages: Total pages to crawl
            - current_url: URL currently being processed
            - urls_total: Total URLs discovered
            - urls_completed: URLs finished processing
            - crawler_type: 'Basic' | 'Playwright'
            - message: Human-readable status message
        active_crawls: Reference to active jobs dict (for wizard integration)

    Side Effects:
        - Emits 'crawler:progress' event to job room
        - If chatbot_id present, also updates wizard session progress
    """
    if socketio:
        from socketio_handlers.events_crawler import emit_crawler_progress
        emit_crawler_progress(socketio, session_id, data)

    # Special handling for Chatbot Builder Wizard integration
    # When a crawl is started from the wizard, we also update the wizard's progress tracker
    job = active_crawls.get(session_id)
    if job and job.get('chatbot_id'):
        _update_wizard_progress(socketio, job, data)


def _update_wizard_progress(socketio: Any, job: Dict, data: dict) -> None:
    """
    Update the Chatbot Builder Wizard with crawl progress.

    When a crawl is initiated from the wizard, this function keeps the
    wizard's progress UI in sync with the crawl status.

    Args:
        socketio: Flask-SocketIO instance
        job: The active crawl job dict (must have 'chatbot_id')
        data: Progress data from the crawl
    """
    try:
        from services.wizard import get_wizard_session_service
        from socketio_handlers.events_wizard import emit_wizard_progress

        wizard_service = get_wizard_session_service()

        # Map crawl progress to wizard progress format
        wizard_service.update_crawl_progress(job['chatbot_id'], {
            'crawl_stage': data.get('stage', 'crawling'),
            'urls_total': data.get('urls_total', 0),
            'urls_completed': data.get('urls_completed', data.get('pages_crawled', 0)),
            'documents_created': job.get('documents_created', 0),
            'current_url': data.get('current_url', ''),
        })

        # Emit wizard-specific progress event
        if socketio:
            emit_wizard_progress(
                socketio,
                job['chatbot_id'],
                wizard_service.get_progress(job['chatbot_id'])
            )

    except Exception as e:
        logger.warning(f"[CrawlerEvents] Failed to update wizard session: {e}")


# =============================================================================
# PAGE EVENTS
# =============================================================================

def emit_page_crawled(socketio: Any, session_id: str, data: dict) -> None:
    """
    Emit notification when a single page has been crawled.

    Sent after each page is processed, allowing UIs to show
    real-time page-by-page progress with document details.

    Args:
        socketio: Flask-SocketIO instance
        session_id: The crawl job ID
        data: Page data dict containing:
            - url: The URL that was crawled
            - page_number: Sequential page number
            - documents_created: Total new documents so far
            - documents_linked: Total linked documents so far
            - document_action: 'new' | 'linked' (if document was processed)
            - document: Serialized document object (if available)
    """
    if socketio:
        from socketio_handlers.events_crawler import emit_crawler_page_crawled
        emit_crawler_page_crawled(socketio, session_id, data)


# =============================================================================
# COMPLETION EVENTS
# =============================================================================

def emit_complete(socketio: Any, session_id: str, data: dict) -> None:
    """
    Emit crawl job completion event.

    Sent when a crawl job finishes successfully. Includes final
    statistics and results summary.

    Args:
        socketio: Flask-SocketIO instance
        session_id: The crawl job ID
        data: Completion data dict containing:
            - status: 'completed'
            - stage: 'completed'
            - collection_id: ID of the created/updated collection
            - pages_crawled: Total pages processed
            - documents_created: New documents created
            - documents_linked: Existing documents linked
            - screenshots_taken: Number of screenshots (Playwright only)
            - vision_extractions: Vision-LLM extractions (Playwright only)
            - errors_count: Number of errors encountered
            - crawler_type: 'Basic' | 'Playwright'
            - brand_color: Extracted brand color (if any)
    """
    if socketio:
        from socketio_handlers.events_crawler import emit_crawler_complete
        emit_crawler_complete(socketio, session_id, data)


def emit_error(socketio: Any, session_id: str, error: str) -> None:
    """
    Emit crawl job error event.

    Sent when a crawl job fails with an unrecoverable error.
    The error message is logged and displayed to the user.

    Args:
        socketio: Flask-SocketIO instance
        session_id: The crawl job ID
        error: Error message string describing what went wrong
    """
    if socketio:
        from socketio_handlers.events_crawler import emit_crawler_error
        emit_crawler_error(socketio, session_id, error)


# =============================================================================
# GLOBAL EVENTS
# =============================================================================

def emit_jobs_updated(socketio: Any, jobs: List[Dict]) -> None:
    """
    Emit global job list update to all subscribed clients.

    Sent when the overall job list changes (job started, completed, etc.).
    Allows dashboard UIs to show current crawl activity across all jobs.

    Args:
        socketio: Flask-SocketIO instance
        jobs: List of all active/recent job dicts with status info
    """
    if socketio:
        from socketio_handlers.events_crawler import emit_crawler_jobs_updated
        emit_crawler_jobs_updated(socketio, jobs)
