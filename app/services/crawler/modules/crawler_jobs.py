# crawler_jobs.py
"""
Job status management for the crawler service.

This module handles tracking and querying crawl job status:
- In-memory job status for active crawls
- Database recovery for jobs that outlived the service
- Job listing and cancellation

Job Lifecycle:
1. queued - Job created, waiting to start
2. running - Crawl in progress
3. completed - Crawl finished successfully
4. failed - Crawl encountered fatal error
5. cancelled - User cancelled the job

Used by: crawler_service.py
Depends on: db.tables
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# JOB STATUS RETRIEVAL
# =============================================================================

def get_job_status(
    job_id: str,
    active_crawls: Dict[str, Dict]
) -> Optional[Dict]:
    """
    Get the current status of a crawl job.

    First checks the in-memory active_crawls dict for running jobs,
    then falls back to database recovery for completed/historical jobs.

    Args:
        job_id: UUID of the crawl job
        active_crawls: Dict of currently active/recent jobs

    Returns:
        Job status dict containing:
            - status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled'
            - collection_id: Associated collection ID
            - pages_crawled: Number of pages processed
            - documents_created: New documents created
            - documents_linked: Existing documents linked
            - errors: List of error dicts
            - started_at: ISO timestamp
            - completed_at: ISO timestamp (if finished)
        Returns None if job not found
    """
    # First check in-memory status (for active/recent jobs)
    status = active_crawls.get(job_id)
    if status:
        return status

    # Fall back to database recovery (for historical jobs)
    return _get_persisted_job_status(job_id)


def _get_persisted_job_status(job_id: str) -> Optional[Dict]:
    """
    Reconstruct job status from database when in-memory session is missing.

    Called when a job ID is requested but not found in active_crawls.
    This can happen after a service restart or if the job completed
    and was evicted from memory.

    Args:
        job_id: UUID of the crawl job

    Returns:
        Reconstructed job status dict, or None if not found in DB

    Recovery Strategy:
        - Find collection by crawl_job_id
        - Count documents by link_type
        - Infer status from collection state
    """
    try:
        from db.tables import RAGCollection, CollectionDocumentLink

        # Find collection associated with this job
        collection = RAGCollection.query.filter_by(crawl_job_id=job_id).first()
        if not collection:
            return None

        # Count documents by type
        docs_created = CollectionDocumentLink.query.filter_by(
            crawl_job_id=job_id,
            link_type='new'
        ).count()

        docs_linked = CollectionDocumentLink.query.filter_by(
            crawl_job_id=job_id,
            link_type='linked'
        ).count()

        docs_total = docs_created + docs_linked

        # If no documents found, job may not have progressed far enough
        if docs_total == 0:
            return None

        # Infer completion status from collection state
        completed_at = collection.updated_at or collection.last_indexed_at
        status = 'completed' if collection.embedding_status != 'failed' else 'failed'

        return {
            'status': status,
            'stage': 'completed' if status == 'completed' else 'crawling',
            'collection_id': collection.id,
            'collection_name': collection.display_name or collection.name,
            'documents_created': docs_created,
            'documents_linked': docs_linked,
            'pages_crawled': docs_total,
            'max_pages': docs_total,
            'urls_total': docs_total,
            'urls_completed': docs_total,
            'completed_at': completed_at.isoformat() if completed_at else None,
            'recovered': True,  # Flag indicating this was recovered from DB
            'error': collection.embedding_error if status == 'failed' else None
        }

    except Exception as e:
        logger.warning(f"[CrawlerJobs] Could not recover status for job {job_id}: {e}")
        return None


# =============================================================================
# JOB LISTING
# =============================================================================

def get_all_jobs(active_crawls: Dict[str, Dict]) -> List[Dict]:
    """
    Get all crawl jobs for dashboard display.

    Returns a list of all jobs in memory, sorted by start time (newest first).
    Used for WebSocket subscriptions and admin dashboards.

    Args:
        active_crawls: Dict of currently active/recent jobs

    Returns:
        List of job dicts with job_id included in each entry
    """
    jobs = []
    for job_id, status in active_crawls.items():
        jobs.append({'job_id': job_id, **status})

    # Sort by start time, newest first
    jobs.sort(
        key=lambda x: x.get('started_at') or x.get('queued_at') or '',
        reverse=True
    )

    return jobs


def list_jobs(active_crawls: Dict[str, Dict]) -> List[Dict]:
    """
    Alias for get_all_jobs() for API compatibility.

    Args:
        active_crawls: Dict of currently active/recent jobs

    Returns:
        List of all job dicts
    """
    return get_all_jobs(active_crawls)


# =============================================================================
# JOB CONTROL
# =============================================================================

def cancel_job(job_id: str, active_crawls: Dict[str, Dict]) -> bool:
    """
    Cancel a running crawl job.

    Sets the job status to 'cancelled'. The crawl thread will check
    this status and stop at the next iteration.

    Note: This doesn't immediately stop the thread, it just marks
    the job for cancellation. The actual thread will exit cleanly.

    Args:
        job_id: UUID of the job to cancel
        active_crawls: Dict of currently active jobs

    Returns:
        True if job was found and marked for cancellation,
        False if job not found
    """
    if job_id in active_crawls:
        active_crawls[job_id]['status'] = 'cancelled'
        logger.info(f"[CrawlerJobs] Job {job_id} marked for cancellation")
        return True

    logger.warning(f"[CrawlerJobs] Cannot cancel job {job_id}: not found")
    return False


# =============================================================================
# JOB INITIALIZATION
# =============================================================================

def create_job_entry(
    job_id: str,
    urls: List[str],
    collection_name: str,
    existing_collection_id: Optional[int],
    chatbot_id: Optional[int],
    max_pages_per_site: int,
    use_playwright: bool,
    use_vision_llm: bool,
    take_screenshots: bool
) -> Dict:
    """
    Create the initial job entry for a new crawl.

    This is called when start_crawl_background begins, before
    the actual crawling starts. Initializes all tracking fields.

    Args:
        job_id: UUID for the new job
        urls: List of URLs to crawl
        collection_name: Display name for the collection
        existing_collection_id: ID of existing collection (or None)
        chatbot_id: Associated chatbot ID (for wizard integration)
        max_pages_per_site: Max pages per URL
        use_playwright: Whether Playwright is being used
        use_vision_llm: Whether Vision-LLM is enabled
        take_screenshots: Whether screenshots are enabled

    Returns:
        Initial job status dict
    """
    from datetime import datetime

    return {
        # Job identification
        'status': 'queued',
        'urls': urls,
        'collection_name': collection_name,
        'existing_collection_id': existing_collection_id,
        'collection_id': existing_collection_id,
        'chatbot_id': chatbot_id,

        # Progress tracking
        'max_pages': max_pages_per_site * len(urls),
        'pages_crawled': 0,
        'documents_created': 0,
        'documents_linked': 0,
        'screenshots_taken': 0,
        'vision_extractions': 0,
        'urls_total': 0,
        'urls_completed': 0,
        'images_extracted': 0,
        'errors': [],

        # Timestamps
        'queued_at': datetime.now().isoformat(),

        # Configuration
        'use_playwright': use_playwright,
        'use_vision_llm': use_vision_llm,
        'take_screenshots': take_screenshots
    }


def update_job_started(job_id: str, active_crawls: Dict[str, Dict]) -> None:
    """
    Mark a job as started (running).

    Called when the background thread begins actual crawling.

    Args:
        job_id: UUID of the job
        active_crawls: Dict of active jobs
    """
    from datetime import datetime

    if job_id in active_crawls:
        active_crawls[job_id]['status'] = 'running'
        active_crawls[job_id]['started_at'] = datetime.now().isoformat()


def update_job_completed(
    job_id: str,
    active_crawls: Dict[str, Dict]
) -> None:
    """
    Mark a job as completed.

    Called when crawling finishes successfully.

    Args:
        job_id: UUID of the job
        active_crawls: Dict of active jobs
    """
    from datetime import datetime

    if job_id in active_crawls:
        active_crawls[job_id]['status'] = 'completed'
        active_crawls[job_id]['completed_at'] = datetime.now().isoformat()


def update_job_failed(
    job_id: str,
    error: str,
    active_crawls: Dict[str, Dict]
) -> None:
    """
    Mark a job as failed.

    Called when crawling encounters a fatal error.

    Args:
        job_id: UUID of the job
        error: Error message
        active_crawls: Dict of active jobs
    """
    if job_id in active_crawls:
        active_crawls[job_id]['status'] = 'failed'
        active_crawls[job_id]['error'] = error
