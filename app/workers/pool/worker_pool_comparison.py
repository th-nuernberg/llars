# worker_pool_comparison.py
"""
Comparison claiming and processing for the Judge Worker Pool.

This module handles the core comparison processing logic:
- Atomic comparison claiming with database-level locking
- Heartbeat mechanism during processing
- Retry logic with exponential backoff
- Message loading for evaluation

The claiming mechanism uses SQL FOR UPDATE SKIP LOCKED to ensure
thread-safe job distribution without race conditions.

Used by: judge_worker_pool.py (PooledJudgeWorker class)
Depends on: worker_pool_constants.py, worker_pool_events.py
"""

from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable

from .worker_pool_constants import MAX_ATTEMPTS, BACKOFF_BASE, HEARTBEAT_INTERVAL

logger = logging.getLogger(__name__)


# =============================================================================
# COMPARISON CLAIMING
# =============================================================================

def claim_next_comparison(
    session_id: int,
    worker_id: int
) -> Optional[Any]:
    """
    Atomically claim the next pending comparison.

    Uses a single UPDATE statement with subquery to atomically claim
    the next available job. This is more robust than SELECT FOR UPDATE
    followed by a separate UPDATE.

    The SQL uses FOR UPDATE SKIP LOCKED to:
    1. Lock only the row being claimed
    2. Skip rows already locked by other workers
    3. Prevent thundering herd on high-contention scenarios

    Args:
        session_id: ID of the session to get work from
        worker_id: ID of the claiming worker

    Returns:
        JudgeComparison object if claimed, None if no work available

    Database Effects:
        - Sets status to RUNNING
        - Sets worker_id to claiming worker
        - Sets started_at and last_heartbeat to NOW()
        - Commits the claim
    """
    from db.database import db
    from db.tables import JudgeComparison, JudgeComparisonStatus
    from sqlalchemy import text

    try:
        # Atomic claim using UPDATE with subquery
        result = db.session.execute(
            text("""
                UPDATE judge_comparisons
                SET status = 'running',
                    worker_id = :worker_id,
                    started_at = NOW(),
                    last_heartbeat = NOW()
                WHERE id = (
                    SELECT id FROM judge_comparisons
                    WHERE session_id = :session_id
                    AND status = 'pending'
                    ORDER BY queue_position
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
            """),
            {'session_id': session_id, 'worker_id': worker_id}
        )
        db.session.commit()

        if result.rowcount == 0:
            # No job claimed - add jitter before retry
            jitter = random.uniform(0.1, 0.5)
            time.sleep(jitter)
            return None

        # Fetch the comparison we just claimed
        comparison = JudgeComparison.query.filter_by(
            session_id=session_id,
            worker_id=worker_id,
            status=JudgeComparisonStatus.RUNNING
        ).order_by(JudgeComparison.started_at.desc()).first()

        if comparison:
            logger.debug(
                f"[JudgeWorker:{session_id}:{worker_id}] "
                f"Claimed comparison {comparison.id}"
            )
            return comparison

        return None

    except Exception as e:
        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Error claiming comparison: {e}"
        )
        db.session.rollback()
        return None


# =============================================================================
# HEARTBEAT MECHANISM
# =============================================================================

def start_heartbeat_thread(
    app,
    session_id: int,
    worker_id: int,
    comparison_id: int
) -> tuple[threading.Thread, threading.Event]:
    """
    Start a heartbeat thread for a comparison.

    The heartbeat thread updates last_heartbeat every HEARTBEAT_INTERVAL
    seconds while the comparison is being processed. This allows the
    recovery system to detect stuck comparisons.

    Args:
        app: Flask app instance (for app context)
        session_id: Session ID for logging
        worker_id: Worker ID for logging
        comparison_id: ID of the comparison being processed

    Returns:
        Tuple of (thread, stop_event) - caller must set stop_event
        when processing completes and join the thread.

    Example:
        thread, stop_event = start_heartbeat_thread(app, sid, wid, cid)
        try:
            process_comparison(...)
        finally:
            stop_event.set()
            thread.join(timeout=2.0)
    """
    stop_event = threading.Event()

    def heartbeat_loop():
        """Send heartbeat every HEARTBEAT_INTERVAL seconds."""
        while not stop_event.wait(timeout=HEARTBEAT_INTERVAL):
            try:
                with app.app_context():
                    from db.database import db
                    from db.tables import JudgeComparison

                    comparison = db.session.get(JudgeComparison, comparison_id)
                    if comparison:
                        comparison.last_heartbeat = datetime.now()
                        db.session.commit()
                        logger.debug(
                            f"[JudgeWorker:{session_id}:{worker_id}] "
                            f"Heartbeat for comparison {comparison_id}"
                        )
            except Exception as e:
                logger.warning(
                    f"[JudgeWorker:{session_id}:{worker_id}] "
                    f"Heartbeat update failed: {e}"
                )

    thread = threading.Thread(
        target=heartbeat_loop,
        daemon=True,
        name=f"Heartbeat-{session_id}-{worker_id}-{comparison_id}"
    )
    thread.start()

    return thread, stop_event


# =============================================================================
# RETRY LOGIC
# =============================================================================

def handle_comparison_failure(
    comparison,
    session_id: int,
    worker_id: int,
    error: Exception,
    attempt: int
) -> None:
    """
    Handle a failed comparison attempt.

    If under MAX_ATTEMPTS, resets to PENDING for retry with exponential
    backoff. If at or over MAX_ATTEMPTS, marks as permanently FAILED.

    Args:
        comparison: JudgeComparison object that failed
        session_id: Session ID for logging
        worker_id: Worker ID for logging
        error: The exception that caused the failure
        attempt: Current attempt number (1-based)

    Database Effects:
        - Updates status to PENDING or FAILED
        - Clears worker_id, started_at, last_heartbeat (if PENDING)
        - Sets error_message
        - Commits changes

    Side Effects:
        - Sleeps for exponential backoff time if resetting to PENDING
    """
    from db.database import db
    from db.tables import JudgeComparisonStatus

    error_msg = str(error)[:400]  # Truncate long errors

    if attempt >= MAX_ATTEMPTS:
        # Max retries exceeded - mark as permanently failed
        comparison.status = JudgeComparisonStatus.FAILED
        comparison.error_message = f"Failed after {attempt} attempts: {error_msg}"
        comparison.worker_id = None
        db.session.commit()

        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Comparison {comparison.id} permanently FAILED after {attempt} attempts"
        )
    else:
        # Reset for retry
        comparison.status = JudgeComparisonStatus.PENDING
        comparison.worker_id = None
        comparison.started_at = None
        comparison.last_heartbeat = None
        comparison.error_message = f"Attempt {attempt} failed: {error_msg}"
        db.session.commit()

        # Exponential backoff before next attempt
        backoff = BACKOFF_BASE ** attempt
        logger.info(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Comparison {comparison.id} will retry (backoff: {backoff}s)"
        )
        time.sleep(backoff)


def increment_attempt_count(comparison) -> int:
    """
    Increment and return the attempt count for a comparison.

    Args:
        comparison: JudgeComparison object

    Returns:
        New attempt count (1-based)

    Database Effects:
        - Increments attempt_count
        - Updates last_heartbeat
        - Commits changes
    """
    from db.database import db

    new_attempt = comparison.attempt_count + 1
    comparison.attempt_count = new_attempt
    comparison.last_heartbeat = datetime.now()
    db.session.commit()

    return new_attempt


# =============================================================================
# MESSAGE LOADING
# =============================================================================

def load_thread_messages(thread_id: int) -> List[Dict[str, Any]]:
    """
    Load messages for a thread in chronological order.

    Retrieves all messages for the given thread and formats them
    for the judge evaluation.

    Args:
        thread_id: ID of the thread to load messages from

    Returns:
        List of message dicts with:
            - content: Message text
            - is_counsellor: Boolean indicating if from counsellor
            - timestamp: ISO format timestamp (or None)

    Note:
        Returns empty list if thread has no messages, which will
        cause the comparison to be marked as failed.
    """
    from db.tables import Message

    messages = Message.query.filter_by(
        thread_id=thread_id
    ).order_by(Message.timestamp).all()

    return [{
        'content': msg.content,
        'is_counsellor': msg.is_counsellor if hasattr(msg, 'is_counsellor') else False,
        'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
    } for msg in messages]


# =============================================================================
# QUEUE STATUS UTILITIES
# =============================================================================

def get_queue_counts(session_id: int) -> Dict[str, int]:
    """
    Get counts of comparisons by status for a session.

    Useful for determining if the queue is truly empty or if
    other workers are still processing.

    Args:
        session_id: ID of the session to check

    Returns:
        Dict with 'pending', 'running', 'completed', 'failed' counts
    """
    from db.tables import JudgeComparison, JudgeComparisonStatus

    pending = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.PENDING
    ).count()

    running = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.RUNNING
    ).count()

    completed = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.COMPLETED
    ).count()

    failed = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.FAILED
    ).count()

    return {
        'pending': pending,
        'running': running,
        'completed': completed,
        'failed': failed
    }


def is_queue_empty(session_id: int) -> bool:
    """
    Check if the queue is completely empty (no pending or running).

    Args:
        session_id: ID of the session to check

    Returns:
        True if no pending or running comparisons
    """
    counts = get_queue_counts(session_id)
    return counts['pending'] == 0 and counts['running'] == 0
