"""
Stale Job Detection Service for LLM-as-Judge.

Periodically checks for stuck comparisons (in RUNNING state for too long)
and resets them for retry or marks them as failed.

Features:
- Thread-based background processing (5-minute interval)
- Heartbeat-based stale detection
- Automatic retry with max attempts
- Graceful shutdown
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Global detector instance
_detector: Optional['StaleJobDetector'] = None
_detector_lock = threading.Lock()

# Configuration
STALE_THRESHOLD_MINUTES = 10  # Comparison considered stale after 10 min
CHECK_INTERVAL_SECONDS = 300  # Check every 5 minutes
MAX_ATTEMPTS = 3  # Maximum retry attempts


class StaleJobDetector:
    """
    Background service that detects and resets stale comparisons.

    A comparison is considered stale if:
    1. Status is RUNNING
    2. last_heartbeat is older than STALE_THRESHOLD_MINUTES
    3. OR started_at is older than STALE_THRESHOLD_MINUTES (if no heartbeat)
    """

    def __init__(self, app):
        """
        Initialize the detector.

        Args:
            app: Flask application instance (for context)
        """
        self.app = app
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._total_recovered = 0
        self._last_check_time: Optional[datetime] = None

    def start(self):
        """Start the detector in a background thread."""
        if self.running:
            logger.warning("[StaleJobDetector] Already running")
            return

        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(
            target=self._run,
            name="StaleJobDetector",
            daemon=True
        )
        self.thread.start()
        logger.info("[StaleJobDetector] Started (check interval: %ds, stale threshold: %d min)",
                    CHECK_INTERVAL_SECONDS, STALE_THRESHOLD_MINUTES)

    def stop(self):
        """Stop the detector gracefully."""
        logger.info("[StaleJobDetector] Stopping...")
        self.running = False
        self._stop_event.set()

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=10.0)

        logger.info("[StaleJobDetector] Stopped")

    def get_stats(self) -> dict:
        """Get detector statistics."""
        return {
            'running': self.running,
            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
            'total_recovered': self._total_recovered,
            'check_interval_seconds': CHECK_INTERVAL_SECONDS,
            'stale_threshold_minutes': STALE_THRESHOLD_MINUTES
        }

    def _run(self):
        """Main detector loop."""
        with self.app.app_context():
            while self.running and not self._stop_event.is_set():
                try:
                    self._detect_and_reset_stale()
                    self._last_check_time = datetime.now()
                except Exception as e:
                    logger.error("[StaleJobDetector] Error during check: %s", e, exc_info=True)

                # Wait for next check interval
                self._stop_event.wait(timeout=CHECK_INTERVAL_SECONDS)

    def _detect_and_reset_stale(self):
        """Detect stale comparisons and reset them to PENDING or mark as FAILED."""
        from db.db import db
        from db.models.judge import (
            JudgeComparison, JudgeComparisonStatus,
            JudgeSession, JudgeSessionStatus
        )

        threshold = datetime.now() - timedelta(minutes=STALE_THRESHOLD_MINUTES)

        # Find stale comparisons:
        # - Status is RUNNING
        # - Either last_heartbeat is stale OR (no heartbeat AND started_at is stale)
        stale_comparisons = JudgeComparison.query.filter(
            JudgeComparison.status == JudgeComparisonStatus.RUNNING,
            db.or_(
                db.and_(
                    JudgeComparison.last_heartbeat.isnot(None),
                    JudgeComparison.last_heartbeat < threshold
                ),
                db.and_(
                    JudgeComparison.last_heartbeat.is_(None),
                    JudgeComparison.started_at.isnot(None),
                    JudgeComparison.started_at < threshold
                )
            )
        ).all()

        if not stale_comparisons:
            logger.debug("[StaleJobDetector] No stale comparisons found")
            return

        logger.info("[StaleJobDetector] Found %d stale comparisons", len(stale_comparisons))

        recovered_count = 0
        failed_count = 0

        for comparison in stale_comparisons:
            # Check if session is still supposed to be running
            session = db.session.get(JudgeSession, comparison.session_id)
            if not session or session.status != JudgeSessionStatus.RUNNING:
                logger.debug("[StaleJobDetector] Skipping comparison %d - session not running",
                            comparison.id)
                continue

            # Calculate how long it's been stuck
            stuck_since = comparison.last_heartbeat or comparison.started_at
            stuck_duration = datetime.now() - stuck_since if stuck_since else timedelta(0)

            # Check if under max attempts
            if comparison.attempt_count >= MAX_ATTEMPTS:
                comparison.status = JudgeComparisonStatus.FAILED
                comparison.error_message = f"Exceeded max attempts ({MAX_ATTEMPTS}) after stale detection"
                comparison.worker_id = None
                failed_count += 1
                logger.warning(
                    "[StaleJobDetector] Comparison %d marked FAILED (max attempts exceeded, stuck %s)",
                    comparison.id, stuck_duration
                )
            else:
                # Reset to pending for retry
                comparison.status = JudgeComparisonStatus.PENDING
                comparison.worker_id = None
                comparison.last_heartbeat = None
                comparison.started_at = None
                recovered_count += 1
                logger.info(
                    "[StaleJobDetector] Reset comparison %d to PENDING (attempt %d/%d, was stuck %s)",
                    comparison.id, comparison.attempt_count + 1, MAX_ATTEMPTS, stuck_duration
                )

        db.session.commit()

        if recovered_count > 0 or failed_count > 0:
            self._total_recovered += recovered_count
            logger.info(
                "[StaleJobDetector] Processed stale comparisons: %d recovered, %d failed",
                recovered_count, failed_count
            )


def start_stale_job_detector(app):
    """Start the global stale job detector."""
    global _detector

    with _detector_lock:
        if _detector is not None:
            logger.warning("[StaleJobDetector] Detector already exists")
            return _detector

        _detector = StaleJobDetector(app)
        _detector.start()
        logger.info("[StaleJobDetector] Global detector started")
        return _detector


def stop_stale_job_detector():
    """Stop the global stale job detector."""
    global _detector

    with _detector_lock:
        if _detector is None:
            return

        _detector.stop()
        _detector = None
        logger.info("[StaleJobDetector] Global detector stopped")


def get_stale_job_detector() -> Optional['StaleJobDetector']:
    """Get the global stale job detector instance."""
    return _detector
