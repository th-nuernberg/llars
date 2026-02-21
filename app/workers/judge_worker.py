"""
Background Worker for LLM-as-Judge Evaluations.

This worker processes the evaluation queue in the background,
allowing users to close their browser while evaluations continue.

Features:
- Thread-based background processing
- Live Socket.IO broadcasts
- Pause/Resume support
- Error handling and retry logic
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional

from flask import current_app

logger = logging.getLogger(__name__)

# Global worker registry
_workers: Dict[int, 'JudgeWorker'] = {}
_worker_lock = threading.Lock()


class JudgeWorker:
    """
    Background worker for processing Judge evaluations.

    Runs in a separate thread and processes the comparison queue
    for a specific session.
    """

    def __init__(self, session_id: int, app):
        """
        Initialize the worker.

        Args:
            session_id: ID of the session to process
            app: Flask application instance (for context)
        """
        self.session_id = session_id
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the worker in a background thread."""
        if self.running:
            logger.warning(f"[JudgeWorker:{self.session_id}] Already running")
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name=f"JudgeWorker-{self.session_id}",
            daemon=True
        )
        self.thread.start()
        logger.info(f"[JudgeWorker:{self.session_id}] Started")

    def stop(self):
        """Stop the worker gracefully."""
        logger.info(f"[JudgeWorker:{self.session_id}] Stopping...")
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)

        logger.info(f"[JudgeWorker:{self.session_id}] Stopped")

    def _run(self):
        """Main worker loop."""
        with self.app.app_context():
            try:
                self._process_queue()
            except Exception as e:
                logger.error(f"[JudgeWorker:{self.session_id}] Fatal error: {e}")
                self._mark_session_failed(str(e))
            finally:
                self.running = False

    def _process_queue(self):
        """Process the evaluation queue."""
        from db.database import db
        from db.tables import (
            JudgeSession, JudgeSessionStatus,
            JudgeComparison, JudgeComparisonStatus,
            JudgeEvaluation, JudgeWinner,
            PillarStatistics, Message
        )
        from services.judge.judge_service import JudgeService

        logger.info(f"[JudgeWorker:{self.session_id}] Processing queue...")

        # Initialize judge service
        try:
            judge_service = JudgeService()
        except Exception as e:
            logger.error(f"[JudgeWorker:{self.session_id}] Failed to init JudgeService: {e}")
            raise

        while self.running and not self._stop_event.is_set():
            # Check session status
            session = db.session.get(JudgeSession, self.session_id)
            if not session:
                logger.error(f"[JudgeWorker:{self.session_id}] Session not found")
                break

            if session.status != JudgeSessionStatus.RUNNING:
                logger.info(f"[JudgeWorker:{self.session_id}] Session status: {session.status.value}")
                break

            # Get next pending comparison
            comparison = JudgeComparison.query.filter_by(
                session_id=self.session_id,
                status=JudgeComparisonStatus.PENDING
            ).order_by(JudgeComparison.queue_position).first()

            if not comparison:
                # Queue empty - session complete
                logger.info(f"[JudgeWorker:{self.session_id}] Queue empty - completing session")
                session.status = JudgeSessionStatus.COMPLETED
                session.completed_at = datetime.now()
                session.current_comparison_id = None
                db.session.commit()
                self._broadcast_session_complete()
                break

            # Process this comparison
            try:
                self._process_comparison(comparison, session, judge_service)
            except Exception as e:
                logger.error(f"[JudgeWorker:{self.session_id}] Comparison {comparison.id} failed: {e}")
                comparison.status = JudgeComparisonStatus.FAILED
                db.session.commit()

            # Brief pause between comparisons
            time.sleep(1)

    def _process_comparison(self, comparison, session, judge_service):
        """Process a single comparison."""
        from db.database import db
        from db.tables import (
            JudgeComparisonStatus, JudgeEvaluation, JudgeWinner,
            PillarStatistics, Message
        )

        logger.info(
            f"[JudgeWorker:{self.session_id}] Processing comparison {comparison.id}: "
            f"Thread {comparison.thread_a_id} vs {comparison.thread_b_id}"
        )

        # Update status
        comparison.status = JudgeComparisonStatus.RUNNING
        comparison.started_at = datetime.now()
        session.current_comparison_id = comparison.id
        db.session.commit()

        # Broadcast start
        self._broadcast_comparison_start(comparison)

        # Load thread messages
        messages_a = self._load_messages(comparison.thread_a_id)
        messages_b = self._load_messages(comparison.thread_b_id)

        if not messages_a or not messages_b:
            logger.warning(f"[JudgeWorker:{self.session_id}] Empty messages for comparison {comparison.id}")
            comparison.status = JudgeComparisonStatus.FAILED
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
            logger.error(f"[JudgeWorker:{self.session_id}] Evaluation error: {e}")
            comparison.status = JudgeComparisonStatus.FAILED
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

        # Update statistics
        self._update_statistics(
            comparison.pillar_a,
            comparison.pillar_b,
            result.winner,
            result.confidence
        )

        # Update comparison status
        comparison.status = JudgeComparisonStatus.COMPLETED
        comparison.completed_at = datetime.now()

        # Update session progress
        session.completed_comparisons += 1
        db.session.commit()

        # Broadcast completion
        self._broadcast_comparison_complete(comparison, result)
        self._broadcast_progress(session)

        logger.info(
            f"[JudgeWorker:{self.session_id}] Comparison {comparison.id} complete: "
            f"winner={result.winner}, confidence={result.confidence:.2f}"
        )

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
        """Update pillar statistics."""
        from db.database import db
        from db.tables import PillarStatistics

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

    def _mark_session_failed(self, error: str):
        """Mark session as failed."""
        from db.database import db
        from db.tables import JudgeSession, JudgeSessionStatus

        try:
            session = db.session.get(JudgeSession, self.session_id)
            if session:
                session.status = JudgeSessionStatus.FAILED
                # Store error in config
                if session.config_json is None:
                    session.config_json = {}
                session.config_json['error'] = error
                db.session.commit()
        except Exception as e:
            logger.error(f"[JudgeWorker:{self.session_id}] Failed to mark session failed: {e}")

    # ========================================================================
    # Socket.IO Broadcasts
    # ========================================================================

    def _get_socketio(self):
        """Get SocketIO instance."""
        try:
            # Try different import paths depending on how the app is run
            try:
                from main import socketio
                logger.debug(f"[JudgeWorker:{self.session_id}] Got socketio from main")
                return socketio
            except ImportError:
                pass

            try:
                from app.main import socketio
                logger.debug(f"[JudgeWorker:{self.session_id}] Got socketio from app.main")
                return socketio
            except ImportError:
                pass

            # Last resort: try to get from flask's current_app
            from flask import current_app
            if hasattr(current_app, 'extensions') and 'socketio' in current_app.extensions:
                socketio = current_app.extensions['socketio']
                logger.debug(f"[JudgeWorker:{self.session_id}] Got socketio from current_app.extensions")
                return socketio

            logger.warning(f"[JudgeWorker:{self.session_id}] Could not find socketio instance")
            return None
        except Exception as e:
            logger.warning(f"[JudgeWorker:{self.session_id}] Failed to get socketio: {e}")
            return None

    def _broadcast_comparison_start(self, comparison):
        """Broadcast when a comparison starts."""
        socketio = self._get_socketio()
        if not socketio:
            logger.warning(f"[JudgeWorker:{self.session_id}] No socketio for comparison_start broadcast")
            return

        room = f"judge_session_{self.session_id}"
        logger.info(f"[JudgeWorker:{self.session_id}] Broadcasting comparison_start to room {room}")
        socketio.emit('judge:comparison_start', {
            'session_id': self.session_id,
            'comparison_id': comparison.id,
            'thread_a_id': comparison.thread_a_id,
            'thread_b_id': comparison.thread_b_id,
            'pillar_a': comparison.pillar_a,
            'pillar_b': comparison.pillar_b,
            'position_order': comparison.position_order
        }, room=room)

    def _broadcast_stream(self, chunk: str):
        """Broadcast LLM streaming chunk."""
        socketio = self._get_socketio()
        if not socketio:
            logger.warning(f"[JudgeWorker:{self.session_id}] No socketio for stream broadcast")
            return

        room = f"judge_session_{self.session_id}"
        # Log every 10th chunk to avoid log spam
        if len(chunk) > 0:
            logger.debug(f"[JudgeWorker:{self.session_id}] Stream chunk to room {room}: {chunk[:50]}...")
        socketio.emit('judge:llm_stream', {
            'session_id': self.session_id,
            'token': chunk,
            'content': chunk
        }, room=room)

    def _broadcast_comparison_complete(self, comparison, result):
        """Broadcast when a comparison completes."""
        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        socketio.emit('judge:comparison_complete', {
            'session_id': self.session_id,
            'comparison_id': comparison.id,
            'winner': result.winner,
            'confidence': result.confidence,
            'reasoning': result.final_justification
        }, room=room)

    def _broadcast_progress(self, session):
        """Broadcast session progress update."""
        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        progress = (session.completed_comparisons / session.total_comparisons * 100) \
            if session.total_comparisons > 0 else 0

        socketio.emit('judge:progress', {
            'completed': session.completed_comparisons,
            'total': session.total_comparisons,
            'percent': progress
        }, room=room)

    def _broadcast_session_complete(self):
        """Broadcast when session completes."""
        socketio = self._get_socketio()
        if not socketio:
            return

        room = f"judge_session_{self.session_id}"
        socketio.emit('judge:session_complete', {
            'session_id': self.session_id
        }, room=room)


# ============================================================================
# Worker Management Functions
# ============================================================================

def trigger_judge_worker(session_id: int):
    """
    Start a worker for a session.

    If a worker is already running for this session, it will be stopped first.

    Args:
        session_id: ID of the session to process
    """
    from flask import current_app

    with _worker_lock:
        # Stop existing worker if any
        if session_id in _workers:
            _workers[session_id].stop()
            del _workers[session_id]

        # Create and start new worker
        worker = JudgeWorker(session_id, current_app._get_current_object())
        _workers[session_id] = worker
        worker.start()

    logger.info(f"[JudgeWorker] Triggered worker for session {session_id}")


def stop_judge_worker(session_id: int):
    """
    Stop the worker for a session.

    Args:
        session_id: ID of the session
    """
    with _worker_lock:
        if session_id in _workers:
            _workers[session_id].stop()
            del _workers[session_id]
            logger.info(f"[JudgeWorker] Stopped worker for session {session_id}")
        else:
            logger.warning(f"[JudgeWorker] No worker found for session {session_id}")


def get_worker_status(session_id: int) -> Optional[dict]:
    """
    Get the status of a worker.

    Args:
        session_id: ID of the session

    Returns:
        Dict with worker status or None if no worker exists
    """
    with _worker_lock:
        if session_id in _workers:
            worker = _workers[session_id]
            return {
                'session_id': session_id,
                'running': worker.running,
                'thread_alive': worker.thread.is_alive() if worker.thread else False
            }
        return None
