"""
Worker Pool for parallel LLM-as-Judge Evaluations.

Manages multiple JudgeWorker instances to process evaluations in parallel.
Each worker grabs comparisons from the queue using database-level locking
to prevent race conditions.

Author: LLARS Team
Date: November 2025
"""

import logging
import random
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Global pool registry
_pools: Dict[int, 'JudgeWorkerPool'] = {}
_pool_lock = threading.Lock()


class JudgeWorkerPool:
    """
    Manages multiple parallel workers for a Judge session.

    Features:
    - Spawns 1-5 worker threads
    - Thread-safe comparison assignment via FOR UPDATE SKIP LOCKED
    - Graceful shutdown support
    - Live Socket.IO broadcasts with worker_id
    """

    MAX_WORKERS = 5

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
        self.workers: List['PooledJudgeWorker'] = []
        self.running = False
        self._stop_event = threading.Event()

        logger.info(
            f"[JudgeWorkerPool:{session_id}] Initialized with {self.worker_count} workers"
        )

    def start(self):
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

    def stop(self):
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


class PooledJudgeWorker:
    """
    Individual worker within a pool.

    Each worker runs in its own thread and fetches comparisons
    from the queue using database-level locking.

    Features:
    - Heartbeat mechanism (updates every 30s during processing)
    - Retry logic with exponential backoff (max 3 attempts)
    """

    # Retry configuration
    MAX_ATTEMPTS = 3
    BACKOFF_BASE = 2  # seconds

    # Heartbeat configuration
    HEARTBEAT_INTERVAL = 30  # seconds
    STALE_TIMEOUT = 120  # seconds - comparisons without heartbeat for this long are considered stuck

    def __init__(self, session_id: int, worker_id: int, pool: JudgeWorkerPool, app):
        self.session_id = session_id
        self.worker_id = worker_id
        self.pool = pool
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.current_comparison_id: Optional[int] = None
        self._stop_event = threading.Event()

        # Stream state storage for reconnect support
        self.stream_content: str = ""  # Accumulated stream content
        self.comparison_data: Optional[Dict] = None  # Current comparison info
        self.is_streaming: bool = False  # Whether currently streaming

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

    def start(self):
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
        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] Started"
        )

    def stop(self):
        """Stop the worker gracefully."""
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] Stopped"
        )

    def _run(self):
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

    def _process_queue(self):
        """Process comparisons from the queue."""
        from db.db import db
        from db.tables import (
            JudgeSession, JudgeSessionStatus,
            JudgeComparison, JudgeComparisonStatus,
            JudgeEvaluation, JudgeWinner,
            PillarStatistics, Message
        )
        from services.judge.judge_service import JudgeService

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] Processing queue..."
        )

        # First, recover any stale comparisons (only worker 0 does this to avoid conflicts)
        if self.worker_id == 0:
            self._recover_stale_comparisons()

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
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Session not found"
                )
                break

            if session.status != JudgeSessionStatus.RUNNING:
                logger.info(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Session status: {session.status.value}"
                )
                break

            # Get next pending comparison using database-level lock
            comparison = self._get_next_comparison()

            if not comparison:
                # No more work - check if other workers might still be working
                pending_count = JudgeComparison.query.filter_by(
                    session_id=self.session_id,
                    status=JudgeComparisonStatus.PENDING
                ).count()

                running_count = JudgeComparison.query.filter_by(
                    session_id=self.session_id,
                    status=JudgeComparisonStatus.RUNNING
                ).count()

                if pending_count == 0 and running_count == 0:
                    # Queue truly empty - mark session complete (first worker to notice)
                    logger.info(
                        f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                        f"Queue empty - completing session"
                    )
                    self._try_complete_session(session)
                    break
                elif pending_count == 0 and running_count > 0:
                    # Other workers might still be processing, but also check for stale jobs
                    # This prevents infinite waiting if workers crashed
                    self._recover_stale_comparisons()
                    # Add jitter to prevent all workers polling at same time
                    time.sleep(1.5 + random.uniform(0, 1))
                    continue
                else:
                    # pending_count > 0 but we didn't get a job
                    # This means other workers grabbed them - retry with jitter
                    logger.debug(
                        f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                        f"Missed job claim, {pending_count} pending, retrying..."
                    )
                    time.sleep(random.uniform(0.2, 0.8))
                    continue

            # Process this comparison with retry logic
            self.current_comparison_id = comparison.id
            try:
                self._process_comparison_with_retry(comparison, session, judge_service)
            finally:
                self.current_comparison_id = None

            # Brief pause between comparisons
            time.sleep(0.5)

    def _recover_stale_comparisons(self):
        """
        Recover stale comparisons that have been RUNNING too long without heartbeat.

        This handles cases where:
        - A worker crashed mid-comparison
        - LLM request timed out without proper cleanup
        - Backend was restarted while comparisons were running
        """
        from db.db import db
        from db.tables import JudgeComparison, JudgeComparisonStatus
        from sqlalchemy import text

        try:
            stale_threshold = datetime.now() - timedelta(seconds=self.STALE_TIMEOUT)

            # Find stale RUNNING comparisons
            stale_comparisons = JudgeComparison.query.filter(
                JudgeComparison.session_id == self.session_id,
                JudgeComparison.status == JudgeComparisonStatus.RUNNING,
                db.or_(
                    JudgeComparison.last_heartbeat == None,
                    JudgeComparison.last_heartbeat < stale_threshold
                )
            ).all()

            if stale_comparisons:
                logger.warning(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Found {len(stale_comparisons)} stale comparisons, recovering..."
                )

                for comp in stale_comparisons:
                    # Check attempt count
                    if comp.attempt_count >= self.MAX_ATTEMPTS:
                        # Mark as failed
                        comp.status = JudgeComparisonStatus.FAILED
                        comp.error_message = f"Stale after {comp.attempt_count} attempts (no heartbeat)"
                        logger.warning(
                            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                            f"Comparison {comp.id} marked FAILED (stale, max attempts)"
                        )
                    else:
                        # Reset to pending for retry
                        comp.status = JudgeComparisonStatus.PENDING
                        comp.error_message = f"Reset from stale RUNNING (attempt {comp.attempt_count})"
                        logger.info(
                            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                            f"Comparison {comp.id} reset to PENDING (was stale)"
                        )

                    comp.worker_id = None
                    comp.started_at = None
                    comp.last_heartbeat = None

                db.session.commit()
                logger.info(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Recovered {len(stale_comparisons)} stale comparisons"
                )

        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Error recovering stale comparisons: {e}"
            )
            db.session.rollback()

    def _get_next_comparison(self):
        """
        Get next pending comparison with atomic claim.

        Uses a single UPDATE statement to atomically claim the next available job.
        This prevents race conditions better than SELECT FOR UPDATE + separate UPDATE.
        """
        from db.db import db
        from db.tables import JudgeComparison, JudgeComparisonStatus
        from sqlalchemy import text

        try:
            # Atomic claim: UPDATE with subquery to get next pending job
            # This is more robust than SELECT FOR UPDATE + separate UPDATE
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
                {'session_id': self.session_id, 'worker_id': self.worker_id}
            )
            db.session.commit()

            if result.rowcount == 0:
                # No job claimed - add jitter before retry to prevent thundering herd
                jitter = random.uniform(0.1, 0.5)
                time.sleep(jitter)
                return None

            # Fetch the comparison we just claimed
            comparison = JudgeComparison.query.filter_by(
                session_id=self.session_id,
                worker_id=self.worker_id,
                status=JudgeComparisonStatus.RUNNING
            ).order_by(JudgeComparison.started_at.desc()).first()

            if comparison:
                logger.debug(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Claimed comparison {comparison.id}"
                )
                return comparison

            return None

        except Exception as e:
            logger.warning(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Error getting next comparison: {e}"
            )
            db.session.rollback()
            return None

    def _process_comparison_with_retry(self, comparison, session, judge_service):
        """
        Process comparison with retry logic and heartbeat.

        - Increments attempt_count before processing
        - Spawns heartbeat thread during processing
        - On failure: Reset to PENDING if under max attempts, else mark FAILED
        - Uses exponential backoff between retries
        """
        from db.db import db
        from db.tables import JudgeComparisonStatus

        # Increment attempt count
        attempt = comparison.attempt_count + 1
        comparison.attempt_count = attempt
        comparison.last_heartbeat = datetime.now()
        db.session.commit()

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Processing comparison {comparison.id} (attempt {attempt}/{self.MAX_ATTEMPTS})"
        )

        # Start heartbeat thread
        heartbeat_stop = threading.Event()
        heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(comparison.id, heartbeat_stop),
            daemon=True
        )
        heartbeat_thread.start()

        try:
            self._process_comparison(comparison, session, judge_service)
        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Comparison {comparison.id} failed (attempt {attempt}): {e}"
            )

            if attempt >= self.MAX_ATTEMPTS:
                # Max retries exceeded - mark as failed
                comparison.status = JudgeComparisonStatus.FAILED
                comparison.error_message = f"Failed after {attempt} attempts: {str(e)[:400]}"
                comparison.worker_id = None
                db.session.commit()
                logger.warning(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Comparison {comparison.id} permanently FAILED after {attempt} attempts"
                )
            else:
                # Reset for retry
                comparison.status = JudgeComparisonStatus.PENDING
                comparison.worker_id = None
                comparison.started_at = None
                comparison.last_heartbeat = None
                comparison.error_message = f"Attempt {attempt} failed: {str(e)[:400]}"
                db.session.commit()

                # Exponential backoff
                backoff = self.BACKOFF_BASE ** attempt
                logger.info(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Comparison {comparison.id} will retry (backoff: {backoff}s)"
                )
                time.sleep(backoff)
        finally:
            # Stop heartbeat thread
            heartbeat_stop.set()
            heartbeat_thread.join(timeout=2.0)

    def _heartbeat_loop(self, comparison_id: int, stop_event: threading.Event):
        """
        Send heartbeat every HEARTBEAT_INTERVAL seconds while processing.

        Updates last_heartbeat timestamp in database to indicate the worker is alive.
        The stale job detector uses this to identify stuck comparisons.
        """
        while not stop_event.wait(timeout=self.HEARTBEAT_INTERVAL):
            try:
                with self.app.app_context():
                    from db.db import db
                    from db.tables import JudgeComparison
                    comparison = db.session.get(JudgeComparison, comparison_id)
                    if comparison:
                        comparison.last_heartbeat = datetime.now()
                        db.session.commit()
                        logger.debug(
                            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                            f"Heartbeat for comparison {comparison_id}"
                        )
            except Exception as e:
                logger.warning(
                    f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                    f"Heartbeat update failed: {e}"
                )

    def _process_comparison(self, comparison, session, judge_service):
        """Process a single comparison."""
        from db.db import db
        from db.tables import (
            JudgeComparison, JudgeComparisonStatus, JudgeEvaluation, JudgeWinner,
            PillarStatistics, Message
        )

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Processing comparison {comparison.id}: "
            f"Thread {comparison.thread_a_id} vs {comparison.thread_b_id}"
        )

        # Broadcast start
        self._broadcast_comparison_start(comparison)

        # Load thread messages
        messages_a = self._load_messages(comparison.thread_a_id)
        messages_b = self._load_messages(comparison.thread_b_id)

        if not messages_a or not messages_b:
            logger.warning(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Empty messages for comparison {comparison.id}"
            )
            comparison.status = JudgeComparisonStatus.FAILED
            comparison.worker_id = None
            db.session.commit()
            return

        # Perform evaluation
        start_time = time.time()

        try:
            result, metadata = judge_service.evaluate_pair(
                thread_a_messages=messages_a,
                thread_b_messages=messages_b,
                pillar_a=comparison.pillar_a,
                pillar_b=comparison.pillar_b,
                stream_callback=lambda chunk: self._broadcast_stream(chunk)
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

        latency_ms = int((time.time() - start_time) * 1000)

        # Map winner string to enum
        winner_map = {
            'A': JudgeWinner.A,
            'B': JudgeWinner.B,
            'TIE': JudgeWinner.TIE
        }

        # Create evaluation record
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

        # Update comparison status and commit evaluation together
        # IMPORTANT: Commit before _update_statistics because it may rollback on IntegrityError
        comparison.status = JudgeComparisonStatus.COMPLETED
        comparison.completed_at = datetime.now()
        db.session.commit()

        # Update statistics (has its own transaction handling with retry logic)
        self._update_statistics(
            comparison.pillar_a,
            comparison.pillar_b,
            result.winner,
            result.confidence
        )

        # Atomic increment of session progress (prevents race condition)
        # This returns the NEW value after increment
        new_completed = self._atomic_increment_progress()

        # Broadcast completion with the atomic count
        self._broadcast_comparison_complete(comparison, result, new_completed)
        self._broadcast_progress_atomic(new_completed, session.total_comparisons)

        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Comparison {comparison.id} complete: "
            f"winner={result.winner}, confidence={result.confidence:.2f}"
        )

    def _atomic_increment_progress(self):
        """
        Atomically increment session progress and return the NEW value.

        This prevents race conditions where multiple workers read/write
        completed_comparisons simultaneously and get inconsistent values.
        """
        from db.db import db
        from sqlalchemy import text

        try:
            # MariaDB atomic increment with result
            result = db.session.execute(
                text("""
                    UPDATE judge_sessions
                    SET completed_comparisons = completed_comparisons + 1
                    WHERE id = :session_id
                """),
                {'session_id': self.session_id}
            )
            db.session.commit()

            # Fetch the new value (MariaDB doesn't support RETURNING)
            new_value = db.session.execute(
                text("SELECT completed_comparisons FROM judge_sessions WHERE id = :session_id"),
                {'session_id': self.session_id}
            ).scalar()

            logger.debug(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Atomic increment: completed_comparisons = {new_value}"
            )
            return new_value or 0

        except Exception as e:
            logger.error(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Error in atomic increment: {e}"
            )
            db.session.rollback()
            return 0

    def _load_messages(self, thread_id: int):
        """Load messages for a thread."""
        from db.tables import Message

        messages = Message.query.filter_by(
            thread_id=thread_id
        ).order_by(Message.timestamp).all()

        return [{
            'content': msg.content,
            'is_counsellor': msg.is_counsellor if hasattr(msg, 'is_counsellor') else False,
            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None
        } for msg in messages]

    def _update_statistics(self, pillar_a: int, pillar_b: int, winner: str, confidence: float):
        """Update pillar statistics (thread-safe with retry on duplicate key)."""
        from db.db import db
        from db.tables import PillarStatistics
        from sqlalchemy.exc import IntegrityError

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Re-query in case another worker created it
                stat = PillarStatistics.query.filter_by(
                    session_id=self.session_id,
                    pillar_a=pillar_a,
                    pillar_b=pillar_b
                ).first()

                if not stat:
                    stat = PillarStatistics(
                        session_id=self.session_id,
                        pillar_a=pillar_a,
                        pillar_b=pillar_b,
                        wins_a=0,
                        wins_b=0,
                        ties=0
                    )
                    db.session.add(stat)
                    # Flush to catch duplicate key early
                    db.session.flush()

                if winner == 'A':
                    stat.wins_a += 1
                elif winner == 'B':
                    stat.wins_b += 1
                else:
                    stat.ties += 1

                # Update average confidence
                total = stat.wins_a + stat.wins_b + stat.ties
                if stat.avg_confidence is None:
                    stat.avg_confidence = confidence
                else:
                    stat.avg_confidence = (
                        (stat.avg_confidence * (total - 1) + confidence) / total
                    )

                stat.updated_at = datetime.now()
                return  # Success

            except IntegrityError:
                # Duplicate key - rollback and retry (another worker created it)
                db.session.rollback()
                if attempt < max_retries - 1:
                    logger.debug(
                        f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                        f"Statistics race condition, retry {attempt + 1}"
                    )
                    continue
                else:
                    logger.warning(
                        f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                        f"Failed to update statistics after {max_retries} retries"
                    )

    def _try_complete_session(self, session):
        """Try to mark session as complete (thread-safe)."""
        from db.db import db
        from db.tables import JudgeSessionStatus, JudgeComparison, JudgeComparisonStatus

        # Double-check under lock that session isn't already completed
        if session.status != JudgeSessionStatus.RUNNING:
            return

        # CRITICAL: Re-check that there are truly no pending or running comparisons
        # This prevents race conditions where another worker reset a comparison to PENDING
        pending_count = JudgeComparison.query.filter_by(
            session_id=self.session_id,
            status=JudgeComparisonStatus.PENDING
        ).count()

        running_count = JudgeComparison.query.filter_by(
            session_id=self.session_id,
            status=JudgeComparisonStatus.RUNNING
        ).count()

        if pending_count > 0 or running_count > 0:
            logger.info(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Cannot complete session - still has {pending_count} pending, {running_count} running"
            )
            return

        # All comparisons done - mark session complete
        session.status = JudgeSessionStatus.COMPLETED
        session.completed_at = datetime.now()
        session.current_comparison_id = None
        db.session.commit()
        logger.info(
            f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
            f"Session {self.session_id} marked as COMPLETED"
        )
        self._broadcast_session_complete()

    # ========================================================================
    # Socket.IO Broadcasts (with worker_id)
    # ========================================================================

    def _get_socketio(self):
        """Get SocketIO instance."""
        try:
            try:
                from main import socketio
                logger.debug(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Got socketio from main")
                return socketio
            except ImportError as e:
                logger.debug(f"[JudgeWorker:{self.session_id}:{self.worker_id}] main import failed: {e}")

            try:
                from app.main import socketio
                logger.debug(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Got socketio from app.main")
                return socketio
            except ImportError as e:
                logger.debug(f"[JudgeWorker:{self.session_id}:{self.worker_id}] app.main import failed: {e}")

            from flask import current_app
            if hasattr(current_app, 'extensions') and 'socketio' in current_app.extensions:
                logger.debug(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Got socketio from extensions")
                return current_app.extensions['socketio']

            logger.warning(f"[JudgeWorker:{self.session_id}:{self.worker_id}] No socketio instance found!")
            return None
        except Exception as e:
            logger.warning(
                f"[JudgeWorker:{self.session_id}:{self.worker_id}] "
                f"Failed to get socketio: {e}"
            )
            return None

    def _broadcast_comparison_start(self, comparison):
        """Broadcast when a comparison starts."""
        # Reset stream state for new comparison
        self.stream_content = ""
        self.is_streaming = True

        # Store comparison data for reconnect support
        self.comparison_data = {
            'comparison_id': comparison.id,
            'thread_a_id': comparison.thread_a_id,
            'thread_b_id': comparison.thread_b_id,
            'pillar_a': comparison.pillar_a,
            'pillar_b': comparison.pillar_b,
            'position_order': comparison.position_order
        }

        socketio = self._get_socketio()
        if not socketio:
            logger.warning(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Cannot broadcast - no socketio")
            return

        room = f"judge_session_{self.session_id}"
        logger.info(f"[JudgeWorker:{self.session_id}:{self.worker_id}] Broadcasting comparison_start to room {room}")
        socketio.emit('judge:comparison_start', {
            'session_id': self.session_id,
            'worker_id': self.worker_id,
            **self.comparison_data
        }, room=room)

    def _broadcast_stream(self, chunk: str):
        """Broadcast LLM streaming chunk and accumulate content."""
        # Accumulate stream content for reconnect support
        self.stream_content += chunk
        self.is_streaming = True

        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        socketio.emit('judge:llm_stream', {
            'session_id': self.session_id,
            'worker_id': self.worker_id,
            'token': chunk,
            'content': chunk,
            'accumulated_length': len(self.stream_content)  # For debugging
        }, room=room)

    def _broadcast_comparison_complete(self, comparison, result, atomic_completed=None):
        """Broadcast when a comparison completes."""
        from db.tables import JudgeSession

        # Mark streaming as complete (keep stream_content for late joiners to see final result)
        self.is_streaming = False

        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"

        # Use atomic count if provided, otherwise fall back to DB read
        session = JudgeSession.query.get(self.session_id)
        completed = atomic_completed if atomic_completed is not None else (session.completed_comparisons if session else 0)
        total = session.total_comparisons if session else 0

        event_data = {
            'session_id': self.session_id,
            'worker_id': self.worker_id,
            'comparison_id': comparison.id,
            'winner': result.winner,
            'confidence': result.confidence,
            'reasoning': result.final_justification,
            'final_stream_content': self.stream_content,  # Include final content for verification
            'completed': completed,  # Include for robust progress tracking
            'total': total  # Include for robust progress tracking
        }
        socketio.emit('judge:comparison_complete', event_data, room=room)
        # Also broadcast to overview room for live updates on overview page
        socketio.emit('judge:comparison_complete', event_data, room='judge_overview')

    def _broadcast_progress_atomic(self, completed, total):
        """Broadcast session progress update with atomic values (prevents race conditions)."""
        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        progress = (completed / total * 100) if total > 0 else 0

        event_data = {
            'session_id': self.session_id,
            'status': 'running',
            'completed': completed,
            'total': total,
            'percent': progress
        }
        socketio.emit('judge:progress', event_data, room=room)
        # Also broadcast to overview room for live updates on overview page
        socketio.emit('judge:progress', event_data, room='judge_overview')

    def _broadcast_progress(self, session):
        """Broadcast session progress update (legacy, use _broadcast_progress_atomic when possible)."""
        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        progress = (session.completed_comparisons / session.total_comparisons * 100) \
            if session.total_comparisons > 0 else 0

        event_data = {
            'session_id': self.session_id,
            'status': session.status.value if hasattr(session.status, 'value') else str(session.status),
            'completed': session.completed_comparisons,
            'total': session.total_comparisons,
            'percent': progress
        }
        socketio.emit('judge:progress', event_data, room=room)
        # Also broadcast to overview room for live updates on overview page
        socketio.emit('judge:progress', event_data, room='judge_overview')

    def _broadcast_session_complete(self):
        """Broadcast when session completes."""
        from db.tables import JudgeSession

        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"

        # Get total from session for robust frontend tracking (100% complete)
        session = JudgeSession.query.get(self.session_id)
        total = session.total_comparisons if session else 0

        event_data = {
            'session_id': self.session_id,
            'total': total,  # Include for robust progress tracking (100%)
            'completed': total  # Both should be equal when complete
        }
        socketio.emit('judge:session_complete', event_data, room=room)
        # Also broadcast to overview room for live updates on overview page
        socketio.emit('judge:session_complete', event_data, room='judge_overview')


# ============================================================================
# Pool Management Functions
# ============================================================================

def trigger_judge_worker_pool(session_id: int, worker_count: int = 1):
    """
    Start a worker pool for a session.

    Args:
        session_id: ID of the session to process
        worker_count: Number of parallel workers (1-5)
    """
    from flask import current_app

    with _pool_lock:
        # Stop existing pool if any
        if session_id in _pools:
            _pools[session_id].stop()
            del _pools[session_id]

        # Create and start new pool
        pool = JudgeWorkerPool(
            session_id=session_id,
            worker_count=worker_count,
            app=current_app._get_current_object()
        )
        _pools[session_id] = pool
        pool.start()

    logger.info(
        f"[JudgeWorkerPool] Triggered pool for session {session_id} "
        f"with {worker_count} workers"
    )


def stop_judge_worker_pool(session_id: int):
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
