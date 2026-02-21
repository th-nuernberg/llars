# worker_pool_statistics.py
"""
Statistics updates and session management for the Judge Worker Pool.

This module handles:
- Pillar statistics updates (wins, ties, confidence)
- Atomic session progress increments
- Session completion detection and marking

The statistics update uses retry logic to handle race conditions
when multiple workers try to create the same pillar pair statistics.

Used by: judge_worker_pool.py (PooledJudgeWorker class)
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# =============================================================================
# PILLAR STATISTICS
# =============================================================================

def update_pillar_statistics(
    session_id: int,
    worker_id: int,
    pillar_a: int,
    pillar_b: int,
    winner: str,
    confidence: float
) -> bool:
    """
    Update pillar pair statistics with retry logic.

    Records the result of a comparison between two pillars.
    Handles race conditions where multiple workers might try to
    create the same pillar pair statistics simultaneously.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the worker (for logging)
        pillar_a: First pillar ID in the comparison
        pillar_b: Second pillar ID in the comparison
        winner: Result string ('A', 'B', or 'TIE')
        confidence: Confidence score (0.0 to 1.0)

    Returns:
        True if update succeeded, False if failed after retries

    Database Effects:
        - Creates or updates PillarStatistics record
        - Increments wins_a, wins_b, or ties based on winner
        - Updates avg_confidence using running average
        - Commits changes (or rolls back on error)
    """
    from db.database import db
    from db.tables import PillarStatistics
    from sqlalchemy.exc import IntegrityError

    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Re-query in case another worker created it
            stat = PillarStatistics.query.filter_by(
                session_id=session_id,
                pillar_a=pillar_a,
                pillar_b=pillar_b
            ).first()

            if not stat:
                # Create new statistics record
                stat = PillarStatistics(
                    session_id=session_id,
                    pillar_a=pillar_a,
                    pillar_b=pillar_b,
                    wins_a=0,
                    wins_b=0,
                    ties=0
                )
                db.session.add(stat)
                # Flush to catch duplicate key early
                db.session.flush()

            # Update win/tie counts
            if winner == 'A':
                stat.wins_a += 1
            elif winner == 'B':
                stat.wins_b += 1
            else:
                stat.ties += 1

            # Update running average confidence
            total = stat.wins_a + stat.wins_b + stat.ties
            if stat.avg_confidence is None:
                stat.avg_confidence = confidence
            else:
                # Running average: ((old_avg * (n-1)) + new_value) / n
                stat.avg_confidence = (
                    (stat.avg_confidence * (total - 1) + confidence) / total
                )

            stat.updated_at = datetime.now()
            db.session.commit()

            return True

        except IntegrityError:
            # Duplicate key - another worker created it first
            db.session.rollback()

            if attempt < max_retries - 1:
                logger.debug(
                    f"[JudgeWorker:{session_id}:{worker_id}] "
                    f"Statistics race condition, retry {attempt + 1}"
                )
                continue
            else:
                logger.warning(
                    f"[JudgeWorker:{session_id}:{worker_id}] "
                    f"Failed to update statistics after {max_retries} retries"
                )
                return False

    return False


# =============================================================================
# SESSION PROGRESS
# =============================================================================

def atomic_increment_progress(session_id: int, worker_id: int) -> int:
    """
    Atomically increment session progress and return the new value.

    Uses SQL UPDATE to atomically increment completed_comparisons.
    This prevents race conditions where multiple workers read/write
    the same value simultaneously.

    Args:
        session_id: ID of the judge session
        worker_id: ID of the worker (for logging)

    Returns:
        New value of completed_comparisons after increment,
        or 0 if the update failed

    Note:
        MariaDB doesn't support RETURNING clause, so we execute
        a separate SELECT after the UPDATE.
    """
    from db.database import db
    from sqlalchemy import text

    try:
        # Atomic increment
        db.session.execute(
            text("""
                UPDATE judge_sessions
                SET completed_comparisons = completed_comparisons + 1
                WHERE id = :session_id
            """),
            {'session_id': session_id}
        )
        db.session.commit()

        # Fetch the new value (MariaDB doesn't support RETURNING)
        new_value = db.session.execute(
            text("""
                SELECT completed_comparisons
                FROM judge_sessions
                WHERE id = :session_id
            """),
            {'session_id': session_id}
        ).scalar()

        logger.debug(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Atomic increment: completed_comparisons = {new_value}"
        )

        return new_value or 0

    except Exception as e:
        logger.error(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Error in atomic increment: {e}"
        )
        db.session.rollback()
        return 0


# =============================================================================
# SESSION COMPLETION
# =============================================================================

def try_complete_session(
    session_id: int,
    worker_id: int
) -> bool:
    """
    Try to mark a session as complete (thread-safe).

    Checks if all comparisons are done and marks the session as COMPLETED.
    Uses double-checking to prevent race conditions where another worker
    might have reset a comparison to PENDING.

    Args:
        session_id: ID of the session to potentially complete
        worker_id: ID of the worker attempting completion (for logging)

    Returns:
        True if session was marked complete, False otherwise

    Database Effects:
        - Updates session status to COMPLETED
        - Sets completed_at timestamp
        - Clears current_comparison_id
        - Commits changes
    """
    from db.database import db
    from db.tables import (
        JudgeSession, JudgeSessionStatus,
        JudgeComparison, JudgeComparisonStatus
    )

    # Get session
    session = db.session.get(JudgeSession, session_id)
    if not session:
        logger.error(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Session not found for completion"
        )
        return False

    # Check if already completed
    if session.status != JudgeSessionStatus.RUNNING:
        logger.debug(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Session already in status {session.status.value}"
        )
        return False

    # CRITICAL: Re-check that there are truly no pending or running comparisons
    # This prevents race conditions where another worker reset a comparison
    pending_count = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.PENDING
    ).count()

    running_count = JudgeComparison.query.filter_by(
        session_id=session_id,
        status=JudgeComparisonStatus.RUNNING
    ).count()

    if pending_count > 0 or running_count > 0:
        logger.info(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Cannot complete session - still has {pending_count} pending, "
            f"{running_count} running"
        )
        return False

    # All comparisons done - mark session complete
    session.status = JudgeSessionStatus.COMPLETED
    session.completed_at = datetime.now()
    session.current_comparison_id = None
    db.session.commit()

    logger.info(
        f"[JudgeWorker:{session_id}:{worker_id}] "
        f"Session {session_id} marked as COMPLETED"
    )

    return True


def get_session_total(session_id: int) -> int:
    """
    Get the total number of comparisons in a session.

    Args:
        session_id: ID of the session

    Returns:
        Total comparison count, or 0 if session not found
    """
    from db.tables import JudgeSession

    session = JudgeSession.query.get(session_id)
    return session.total_comparisons if session else 0
