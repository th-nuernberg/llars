# worker_pool_recovery.py
"""
Stale comparison recovery for the Judge Worker Pool.

This module handles detection and recovery of stuck/abandoned comparisons:
- Detects comparisons that have been RUNNING too long without heartbeat
- Resets them to PENDING for retry (if under max attempts)
- Marks them as FAILED (if max attempts exceeded)

Recovery scenarios handled:
1. Worker crashed mid-comparison
2. LLM request timed out without proper cleanup
3. Backend was restarted while comparisons were running
4. Network issues caused worker to become unresponsive

Used by: judge_worker_pool.py (PooledJudgeWorker class)
Depends on: worker_pool_constants.py
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from .worker_pool_constants import STALE_TIMEOUT, MAX_ATTEMPTS

logger = logging.getLogger(__name__)


# =============================================================================
# STALE COMPARISON RECOVERY
# =============================================================================

def recover_stale_comparisons(session_id: int, worker_id: int) -> int:
    """
    Recover stale comparisons that have been RUNNING too long without heartbeat.

    Scans for comparisons in RUNNING status whose last_heartbeat is older
    than STALE_TIMEOUT seconds. These are considered abandoned and are either:
    - Reset to PENDING for retry (if attempt_count < MAX_ATTEMPTS)
    - Marked as FAILED (if attempt_count >= MAX_ATTEMPTS)

    Args:
        session_id: ID of the session to scan
        worker_id: ID of the worker performing recovery (for logging)

    Returns:
        Number of comparisons recovered

    Database Effects:
        - Updates status to PENDING or FAILED
        - Clears worker_id, started_at, last_heartbeat
        - Sets error_message explaining the recovery
        - Commits changes

    Note:
        Only worker 0 should call this to avoid conflicting recovery attempts.
        The main worker loop handles this coordination.
    """
    from db.db import db
    from db.tables import JudgeComparison, JudgeComparisonStatus

    try:
        stale_threshold = datetime.now() - timedelta(seconds=STALE_TIMEOUT)

        # Find stale RUNNING comparisons
        # A comparison is stale if:
        # 1. Status is RUNNING
        # 2. last_heartbeat is NULL (never received heartbeat) OR
        #    last_heartbeat < stale_threshold (no recent heartbeat)
        stale_comparisons = JudgeComparison.query.filter(
            JudgeComparison.session_id == session_id,
            JudgeComparison.status == JudgeComparisonStatus.RUNNING,
            db.or_(
                JudgeComparison.last_heartbeat == None,
                JudgeComparison.last_heartbeat < stale_threshold
            )
        ).all()

        if not stale_comparisons:
            return 0

        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Found {len(stale_comparisons)} stale comparisons, recovering..."
        )

        recovered_count = 0
        for comp in stale_comparisons:
            recovered_count += _recover_single_comparison(
                comp, session_id, worker_id
            )

        db.session.commit()

        logger.info(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Recovered {recovered_count} stale comparisons"
        )

        return recovered_count

    except Exception as e:
        logger.error(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Error recovering stale comparisons: {e}"
        )
        from db.db import db
        db.session.rollback()
        return 0


def _recover_single_comparison(
    comparison,
    session_id: int,
    worker_id: int
) -> int:
    """
    Recover a single stale comparison.

    Determines whether to reset to PENDING or mark as FAILED based on
    the attempt_count.

    Args:
        comparison: JudgeComparison object to recover
        session_id: Session ID for logging
        worker_id: Worker ID for logging

    Returns:
        1 if recovered, 0 if skipped

    Side Effects:
        - Modifies comparison object (status, worker_id, etc.)
        - Does NOT commit - caller is responsible for commit
    """
    from db.tables import JudgeComparisonStatus

    if comparison.attempt_count >= MAX_ATTEMPTS:
        # Max retries exceeded - mark as permanently failed
        comparison.status = JudgeComparisonStatus.FAILED
        comparison.error_message = (
            f"Stale after {comparison.attempt_count} attempts (no heartbeat)"
        )
        logger.warning(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Comparison {comparison.id} marked FAILED (stale, max attempts)"
        )
    else:
        # Reset to pending for retry
        comparison.status = JudgeComparisonStatus.PENDING
        comparison.error_message = (
            f"Reset from stale RUNNING (attempt {comparison.attempt_count})"
        )
        logger.info(
            f"[JudgeWorker:{session_id}:{worker_id}] "
            f"Comparison {comparison.id} reset to PENDING (was stale)"
        )

    # Clear worker assignment
    comparison.worker_id = None
    comparison.started_at = None
    comparison.last_heartbeat = None

    return 1


# =============================================================================
# HEALTH CHECK UTILITIES
# =============================================================================

def get_stale_comparison_count(session_id: int) -> int:
    """
    Count how many comparisons are potentially stale.

    Useful for monitoring and debugging without actually recovering.

    Args:
        session_id: ID of the session to check

    Returns:
        Number of comparisons that would be recovered
    """
    from db.db import db
    from db.tables import JudgeComparison, JudgeComparisonStatus

    stale_threshold = datetime.now() - timedelta(seconds=STALE_TIMEOUT)

    return JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.RUNNING,
        db.or_(
            JudgeComparison.last_heartbeat == None,
            JudgeComparison.last_heartbeat < stale_threshold
        )
    ).count()


def get_running_comparison_ages(session_id: int) -> list[dict]:
    """
    Get age information for all RUNNING comparisons.

    Useful for debugging to see which comparisons might become stale.

    Args:
        session_id: ID of the session to check

    Returns:
        List of dicts with comparison_id, worker_id, age_seconds, is_stale
    """
    from db.tables import JudgeComparison, JudgeComparisonStatus

    comparisons = JudgeComparison.query.filter(
        JudgeComparison.session_id == session_id,
        JudgeComparison.status == JudgeComparisonStatus.RUNNING
    ).all()

    now = datetime.now()
    result = []

    for comp in comparisons:
        if comp.last_heartbeat:
            age = (now - comp.last_heartbeat).total_seconds()
        elif comp.started_at:
            age = (now - comp.started_at).total_seconds()
        else:
            age = float('inf')

        result.append({
            'comparison_id': comp.id,
            'worker_id': comp.worker_id,
            'age_seconds': age,
            'is_stale': age > STALE_TIMEOUT,
            'attempt_count': comp.attempt_count
        })

    return result
