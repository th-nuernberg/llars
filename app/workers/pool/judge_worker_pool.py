# judge_worker_pool.py
"""
Worker Pool for parallel LLM-as-Judge Evaluations.

This module provides the main classes and entry points for the worker pool:
- JudgeWorkerPool: Manages multiple parallel workers
- PooledJudgeWorker: Individual worker within a pool
- Pool management functions (trigger, stop, status)

The implementation is distributed across specialized modules:
- worker_pool_constants: Configuration and global registry
- worker_pool_events: Socket.IO broadcast functions
- worker_pool_recovery: Stale comparison recovery
- worker_pool_comparison: Comparison claiming and processing
- worker_pool_statistics: Statistics updates and session completion

Usage:
    from workers.pool import trigger_judge_worker_pool, stop_judge_worker_pool

    # Start a pool with 3 workers
    trigger_judge_worker_pool(session_id=123, worker_count=3)

    # Stop the pool
    stop_judge_worker_pool(session_id=123)

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

from __future__ import annotations

import logging
import random
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

# Import from specialized modules
from .worker_pool_constants import (
    MAX_WORKERS,
    MAX_ATTEMPTS,
    HEARTBEAT_INTERVAL,
    get_pool,
    register_pool,
    unregister_pool,
    _pool_lock,
    _pools,
)
from .worker_pool_events import (
    get_socketio,
    broadcast_comparison_start,
    broadcast_stream_chunk,
    broadcast_comparison_complete,
    broadcast_progress_atomic,
    broadcast_session_complete,
)
from .worker_pool_recovery import recover_stale_comparisons
from .worker_pool_comparison import (
    claim_next_comparison,
    start_heartbeat_thread,
    handle_comparison_failure,
    increment_attempt_count,
    load_thread_messages,
    get_queue_counts,
)
from .worker_pool_statistics import (
    update_pillar_statistics,
    atomic_increment_progress,
    try_complete_session,
    get_session_total,
)

logger = logging.getLogger(__name__)


# =============================================================================
# JUDGE WORKER POOL CLASS
# =============================================================================

class JudgeWorkerPool:
    """
    Manages multiple parallel workers for a Judge session.

    The pool spawns 1-5 worker threads that process comparisons from
    the queue concurrently. Each worker claims jobs atomically using
    database-level locking to prevent race conditions.

    Features:
        - Spawns 1-5 worker threads
        - Thread-safe comparison assignment via FOR UPDATE SKIP LOCKED
        - Graceful shutdown support
        - Live Socket.IO broadcasts with worker_id

    Attributes:
        session_id: ID of the session being processed
        worker_count: Number of parallel workers (1-5)
        app: Flask application instance
        workers: List of PooledJudgeWorker instances
        running: Whether the pool is active
    """

    MAX_WORKERS = MAX_WORKERS

    def __init__(self, session_id: int, worker_count: int, app):
        """
        Initialize the worker pool.

        Args:
            session_id: ID of the session to process
            worker_count: Number of parallel workers (1-5)
            app: Flask application instance (for context)
        """
        self.session_id = session_id
        self.worker_count = min(max(worker_count, 1), self.MAX_WORKERS)
        self.app = app
        self.workers: List[PooledJudgeWorker] = []
        self.running = False
        self._stop_event = threading.Event()

        logger.info(
            f"[JudgeWorkerPool:{session_id}] Initialized with {self.worker_count} workers"
        )

    def start(self) -> None:
        """Start all workers in the pool."""
        if self.running:
            logger.warning(f"[JudgeWorkerPool:{self.session_id}] Already running")
            return

        self.running = True
        self._stop_event.clear()

        # Spawn worker threads
        for worker_id in range(self.worker_count):
            worker = PooledJudgeWorker(
                session_id=self.session_id,
                worker_id=worker_id,
                pool=self,
                app=self.app
            )
            self.workers.append(worker)
            worker.start()

        logger.info(
            f"[JudgeWorkerPool:{self.session_id}] Started {len(self.workers)} workers"
        )

    def stop(self) -> None:
        """Stop all workers gracefully."""
        logger.info(f"[JudgeWorkerPool:{self.session_id}] Stopping pool...")
        self.running = False
        self._stop_event.set()

        # Wait for all workers to finish
        for worker in self.workers:
            worker.stop()

        self.workers.clear()
        logger.info(f"[JudgeWorkerPool:{self.session_id}] Pool stopped")

    def is_running(self) -> bool:
        """Check if any worker is still running."""
        return any(w.running for w in self.workers)

    def get_status(self) -> Dict:
        """Get status of all workers in the pool."""
        return {
            'session_id': self.session_id,
            'worker_count': self.worker_count,
            'running': self.running,
            'workers': [
                {
                    'worker_id': w.worker_id,
                    'running': w.running,
                    'current_comparison_id': w.current_comparison_id
                }
                for w in self.workers
            ]
        }

    def get_worker_streams(self) -> Dict:
        """Get full stream state of all workers for reconnect support."""
        return {
            'session_id': self.session_id,
            'worker_count': self.worker_count,
            'running': self.running,
            'workers': [w.get_stream_state() for w in self.workers]
        }


# =============================================================================
# POOLED JUDGE WORKER CLASS
# =============================================================================

class PooledJudgeWorker:
    """
    Individual worker within a pool.

    Each worker runs in its own thread and fetches comparisons from
    the queue using database-level locking. Features include:
    - Heartbeat mechanism (updates every 30s during processing)
    - Retry logic with exponential backoff (max 3 attempts)
    - Stream state storage for reconnect support

    Attributes:
        session_id: ID of the session being processed
        worker_id: Unique ID within the pool (0 to N-1)
        pool: Reference to parent JudgeWorkerPool
        app: Flask application instance
        running: Whether this worker is active
        current_comparison_id: ID of comparison being processed (or None)
        stream_content: Accumulated LLM stream content
        is_streaming: Whether currently streaming
    """

    def __init__(self, session_id: int, worker_id: int, pool: JudgeWorkerPool, app):
        """Initialize the worker."""
        self.session_id = session_id
        self.worker_id = worker_id
        self.pool = pool
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.current_comparison_id: Optional[int] = None
        self._stop_event = threading.Event()

        # Stream state storage for reconnect support
        self.stream_content: str = ""
        self.comparison_data: Optional[Dict] = None
        self.is_streaming: bool = False

    def get_stream_state(self) -> Dict:
        """Get current stream state for reconnect support."""
        return {
            'worker_id': self.worker_id,
            'running': self.running,
            'is_streaming': self.is_streaming,
            'current_comparison_id': self.current_comparison_id,
            'comparison': self.comparison_data,
            'stream_content': self.stream_content,
            'stream_length': len(self.stream_content)
        }

    def start(self) -> None:
        """Start the worker thread."""
        if self.running:
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name=f"JudgeWorker-{self.session_id}-{self.worker_id}",
            daemon=True
        )
        self.thread.start()
        logger.info(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Started")

    def stop(self) -> None:
        """Stop the worker gracefully."""
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        logger.info(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Stopped")

    def _run(self) -> None:
        """Main worker loop."""
        with self.app.app_context():
            try:
                self._process_queue()
            except Exception as e:
                logger.error(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] Fatal error: {e}"
                )
            finally:
                self.running = False
                self.current_comparison_id = None

    def _process_queue(self) -> None:
        """Process comparisons from the queue."""
        from db.database import db
        from db.tables import JudgeSession, JudgeSessionStatus
        from services.judge.judge_service import JudgeService

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] Processing queue..."
        )

        # First, recover any stale comparisons (only worker 0)
        if self.worker_id == 0:
            recover_stale_comparisons(self.session_id, self.worker_id)

        # Initialize judge service
        try:
            judge_service = JudgeService()
        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Failed to init JudgeService: {e}"
            )
            return

        while self.running and not self._stop_event.is_set():
            # Check if pool is still running
            if not self.pool.running:
                logger.info(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Pool stopped, exiting"
                )
                break

            # Check session status
            session = db.session.get(JudgeSession, self.session_id)
            if not session:
                logger.error(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] Session not found"
                )
                break

            if session.status != JudgeSessionStatus.RUNNING:
                logger.info(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Session status: {session.status.value}"
                )
                break

            # Get next pending comparison
            comparison = claim_next_comparison(self.session_id, self.worker_id)

            if not comparison:
                # Handle empty queue
                if not self._handle_empty_queue(session):
                    break
                continue

            # Process this comparison
            self.current_comparison_id = comparison.id
            try:
                self._process_comparison_with_retry(comparison, session, judge_service)
            finally:
                self.current_comparison_id = None

            # Brief pause between comparisons
            time.sleep(0.5)

    def _handle_empty_queue(self, session) -> bool:
        """
        Handle when no comparison is available.

        Returns:
            True to continue processing, False to exit
        """
        counts = get_queue_counts(self.session_id)

        if counts['pending'] == 0 and counts['running'] == 0:
            # Queue truly empty - try to complete session
            logger.info(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Queue empty - completing session"
            )
            if try_complete_session(self.session_id, self.worker_id):
                total = get_session_total(self.session_id)
                broadcast_session_complete(self.session_id, self.worker_id, total)
            return False

        elif counts['pending'] == 0 and counts['running'] > 0:
            # Other workers might still be processing
            recover_stale_comparisons(self.session_id, self.worker_id)
            time.sleep(1.5 + random.uniform(0, 1))
            return True

        else:
            # Jobs exist but we missed the claim
            logger.debug(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Missed job claim, {counts['pending']} pending, retrying..."
            )
            time.sleep(random.uniform(0.2, 0.8))
            return True

    def _process_comparison_with_retry(self, comparison, session, judge_service) -> None:
        """Process a comparison with retry logic and heartbeat."""
        from db.database import db
        from db.tables import JudgeComparisonStatus

        # Increment attempt count
        attempt = increment_attempt_count(comparison)

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Processing comparison {comparison.id} (attempt {attempt}/{MAX_ATTEMPTS})"
        )

        # Start heartbeat thread
        heartbeat_thread, heartbeat_stop = start_heartbeat_thread(
            self.app, self.session_id, self.worker_id, comparison.id
        )

        try:
            self._process_comparison(comparison, session, judge_service)
        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Comparison {comparison.id} failed (attempt {attempt}): {e}"
            )
            handle_comparison_failure(
                comparison, self.session_id, self.worker_id, e, attempt
            )
        finally:
            # Stop heartbeat thread
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=2.0)

    def _process_comparison(self, comparison, session, judge_service) -> None:
        """Process a single comparison."""
        from db.database import db
        from db.tables import JudgeComparisonStatus, JudgeEvaluation, JudgeWinner

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Processing comparison {comparison.id}: "
            f"Thread {comparison.thread_a_id} vs {comparison.thread_b_id}"
        )

        # Reset stream state
        self.stream_content = ""
        self.is_streaming = True
        self.comparison_data = {
            'comparison_id': comparison.id,
            'thread_a_id': comparison.thread_a_id,
            'thread_b_id': comparison.thread_b_id,
            'pillar_a': comparison.pillar_a,
            'pillar_b': comparison.pillar_b,
            'position_order': comparison.position_order
        }

        # Broadcast start
        broadcast_comparison_start(
            self.session_id, self.worker_id, self.comparison_data
        )

        # Load thread messages
        messages_a = load_thread_messages(comparison.thread_a_id)
        messages_b = load_thread_messages(comparison.thread_b_id)

        if not messages_a or not messages_b:
            logger.warning(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Empty messages for comparison {comparison.id}"
            )
            comparison.status = JudgeComparisonStatus.FAILED
            comparison.worker_id = None
            db.session.commit()
            return

        # Stream callback that broadcasts and accumulates
        def stream_callback(chunk: str):
            self.stream_content += chunk
            broadcast_stream_chunk(
                self.session_id, self.worker_id, chunk, len(self.stream_content)
            )

        # Perform evaluation
        start_time = time.time()

        try:
            result, metadata = judge_service.evaluate_pair(
                thread_a_messages=messages_a,
                thread_b_messages=messages_b,
                pillar_a=comparison.pillar_a,
                pillar_b=comparison.pillar_b,
                stream_callback=stream_callback
            )
        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Evaluation error: {e}"
            )
            comparison.status = JudgeComparisonStatus.FAILED
            comparison.worker_id = None
            db.session.commit()
            return

        self.is_streaming = False
        latency_ms = int((time.time() - start_time) * 1000)

        # Map winner and create evaluation
        winner_map = {'A': JudgeWinner.A, 'B': JudgeWinner.B, 'TIE': JudgeWinner.TIE}

        evaluation = JudgeEvaluation(
            comparison_id=comparison.id,
            raw_response=result.model_dump_json(),
            evaluation_json=result.model_dump(),
            winner=winner_map.get(result.winner, JudgeWinner.TIE),
            counsellor_coherence_a=result.criteria_scores.counsellor_coherence.score_a,
            counsellor_coherence_b=result.criteria_scores.counsellor_coherence.score_b,
            client_coherence_a=result.criteria_scores.client_coherence.score_a,
            client_coherence_b=result.criteria_scores.client_coherence.score_b,
            quality_a=result.criteria_scores.quality.score_a,
            quality_b=result.criteria_scores.quality.score_b,
            empathy_a=result.criteria_scores.empathy.score_a,
            empathy_b=result.criteria_scores.empathy.score_b,
            authenticity_a=result.criteria_scores.authenticity.score_a,
            authenticity_b=result.criteria_scores.authenticity.score_b,
            solution_orientation_a=result.criteria_scores.solution_orientation.score_a,
            solution_orientation_b=result.criteria_scores.solution_orientation.score_b,
            reasoning=result.final_justification,
            confidence=result.confidence,
            position_variant=comparison.position_order,
            llm_latency_ms=latency_ms,
            token_count=metadata.get('token_count')
        )

        db.session.add(evaluation)

        # Update comparison status
        comparison.status = JudgeComparisonStatus.COMPLETED
        comparison.completed_at = datetime.now()
        db.session.commit()

        # Update statistics
        update_pillar_statistics(
            self.session_id, self.worker_id,
            comparison.pillar_a, comparison.pillar_b,
            result.winner, result.confidence
        )

        # Atomic progress increment
        new_completed = atomic_increment_progress(self.session_id, self.worker_id)

        # Broadcast completion
        broadcast_comparison_complete(
            self.session_id, self.worker_id, comparison.id,
            result, self.stream_content, new_completed, session.total_comparisons
        )
        broadcast_progress_atomic(
            self.session_id, self.worker_id, new_completed, session.total_comparisons
        )

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Comparison {comparison.id} complete: "
            f"winner={result.winner}, confidence={result.confidence:.2f}"
        )


# =============================================================================
# POOL MANAGEMENT FUNCTIONS
# =============================================================================

def trigger_judge_worker_pool(session_id: int, worker_count: int = 1) -> None:
    """
    Start a worker pool for a session.

    Args:
        session_id: ID of the session to process
        worker_count: Number of parallel workers (1-5)
    """
    from flask import current_app

    # Stop existing pool if any
    with _pool_lock:
        if session_id in _pools:
            _pools[session_id].stop()
            del _pools[session_id]

    # Create and start new pool
    pool = JudgeWorkerPool(
        session_id=session_id,
        worker_count=worker_count,
        app=current_app._get_current_object()
    )

    with _pool_lock:
        _pools[session_id] = pool

    pool.start()

    logger.info(
        f"[JudgeWorkerPool] Triggered pool for session {session_id} "
        f"with {worker_count} workers"
    )


def stop_judge_worker_pool(session_id: int) -> None:
    """Stop the worker pool for a session."""
    with _pool_lock:
        if session_id in _pools:
            _pools[session_id].stop()
            del _pools[session_id]
            logger.info(f"[JudgeWorkerPool] Stopped pool for session {session_id}")
        else:
            logger.warning(f"[JudgeWorkerPool] No pool found for session {session_id}")


def get_pool_status(session_id: int) -> Optional[Dict]:
    """Get the status of a worker pool."""
    with _pool_lock:
        if session_id in _pools:
            return _pools[session_id].get_status()
        return None


def get_worker_streams(session_id: int) -> Optional[Dict]:
    """
    Get full stream state of all workers for reconnect support.

    Returns accumulated stream content for each worker so clients
    can resume mid-stream without losing previous content.
    """
    with _pool_lock:
        if session_id in _pools:
            return _pools[session_id].get_worker_streams()
        return None
