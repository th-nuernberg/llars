# events_crawler.py
"""
SocketIO event handlers for Web Crawler live updates.
Provides real-time progress updates during crawling.

Events:
    Client → Server:
        - crawler:join_session: Join a specific crawler job session for live updates
        - crawler:leave_session: Leave a crawler job session
        - crawler:subscribe_jobs: Subscribe to global job list updates (replaces polling)
        - crawler:unsubscribe_jobs: Unsubscribe from global job updates
        - crawler:get_status: Request current status of a crawler job

    Server → Client:
        - crawler:joined: Confirmation of joining a session
        - crawler:jobs_list: Initial list of all crawler jobs
        - crawler:jobs_updated: Global job list has changed
        - crawler:progress: Progress update for a specific job
        - crawler:page_crawled: Notification when a page has been crawled
        - crawler:status: Current status of a requested job
        - crawler:complete: Crawl job has completed
        - crawler:error: Error occurred during crawling

Rooms:
    - crawler_{session_id}: Per-job room for detailed updates
    - crawler_jobs_global: Global room for job list updates
"""

import logging
from flask import request
from flask_socketio import join_room, leave_room, emit

logger = logging.getLogger(__name__)

# Global room for clients watching all jobs
CRAWLER_JOBS_ROOM = "crawler_jobs_global"


def register_crawler_events(socketio):
    """
    Register WebSocket events for crawler live updates.

    This replaces HTTP polling for crawler job status with real-time WebSocket updates.
    """

    @socketio.on('crawler:join_session')
    def handle_join_session(data):
        """Join a crawler session room for live updates."""
        session_id = data.get('session_id')
        if not session_id:
            emit('crawler:error', {'error': 'Missing session_id'})
            return

        room = f"crawler_{session_id}"
        join_room(room)
        logger.info(f"[Crawler Socket] Client joined session room: {room}")

        emit('crawler:joined', {
            'session_id': session_id,
            'message': 'Joined crawler session'
        })

    @socketio.on('crawler:subscribe_jobs')
    def handle_subscribe_jobs():
        """Subscribe to global job updates (replaces polling)."""
        join_room(CRAWLER_JOBS_ROOM)
        logger.info(f"[Crawler Socket] Client subscribed to global job updates")

        # Send current jobs list immediately
        from services.crawler.web_crawler import crawler_service
        jobs = crawler_service.get_all_jobs()
        emit('crawler:jobs_list', {'jobs': jobs})

    @socketio.on('crawler:unsubscribe_jobs')
    def handle_unsubscribe_jobs():
        """Unsubscribe from global job updates."""
        leave_room(CRAWLER_JOBS_ROOM)
        logger.info(f"[Crawler Socket] Client unsubscribed from global job updates")

    @socketio.on('crawler:leave_session')
    def handle_leave_session(data):
        """Leave a crawler session room."""
        session_id = data.get('session_id')
        if session_id:
            room = f"crawler_{session_id}"
            leave_room(room)
            logger.info(f"[Crawler Socket] Client left session room: {room}")

    @socketio.on('crawler:get_status')
    def handle_get_status(data):
        """Get current status of a crawler session."""
        session_id = data.get('session_id')
        if not session_id:
            emit('crawler:error', {'error': 'Missing session_id'})
            return

        from services.crawler.web_crawler import crawler_service
        status = crawler_service.get_job_status(session_id)

        if status:
            emit('crawler:status', {
                'session_id': session_id,
                **status
            })
        else:
            emit('crawler:error', {
                'session_id': session_id,
                'error': 'Session not found'
            })

    logger.info("[Crawler Socket] Event handlers registered")


def emit_crawler_progress(socketio, session_id: str, data: dict):
    """Emit progress update to all clients watching a session."""
    room = f"crawler_{session_id}"
    socketio.emit('crawler:progress', {
        'session_id': session_id,
        **data
    }, room=room)


def emit_crawler_page_crawled(socketio, session_id: str, data: dict):
    """Emit event when a page is crawled."""
    room = f"crawler_{session_id}"
    socketio.emit('crawler:page_crawled', {
        'session_id': session_id,
        **data
    }, room=room)


def emit_crawler_complete(socketio, session_id: str, data: dict):
    """Emit event when crawl is complete."""
    room = f"crawler_{session_id}"
    socketio.emit('crawler:complete', {
        'session_id': session_id,
        **data
    }, room=room)


def emit_crawler_error(socketio, session_id: str, error: str):
    """Emit error event."""
    room = f"crawler_{session_id}"
    socketio.emit('crawler:error', {
        'session_id': session_id,
        'error': error
    }, room=room)


def emit_crawler_jobs_updated(socketio, jobs: list = None):
    """
    Emit global job list update to all subscribed clients.
    Call this whenever jobs are created, updated, or completed.
    """
    if jobs is None:
        # Fetch current jobs if not provided
        from services.crawler.web_crawler import crawler_service
        jobs = crawler_service.get_all_jobs()

    socketio.emit('crawler:jobs_updated', {
        'jobs': jobs
    }, room=CRAWLER_JOBS_ROOM)
    logger.debug(f"[Crawler Socket] Emitted jobs update to global room ({len(jobs)} jobs)")
