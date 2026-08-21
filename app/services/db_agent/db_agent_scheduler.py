"""Deutsche Bahn Agent Scheduler - runs periodic price scans in a background thread."""

import logging
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

_scheduler_thread = None
_scheduler_running = False
_scan_interval = 6 * 60 * 60  # 6 hours in seconds
_scan_lock = threading.Lock()  # ensures only one scan runs at a time

# Status tracking
_status = {
    'running': False,
    'last_scan_at': None,
    'last_scan_result': None,
    'next_scan_at': None,
    'scan_count': 0,
    'is_scanning': False,
}


def get_status() -> dict:
    return dict(_status)


def _run_scan(app):
    """Execute a scan within Flask app context. Guarded by lock — only one at a time."""
    global _status

    if not _scan_lock.acquire(blocking=False):
        logger.info('DB Agent scan skipped — another scan is already running')
        return

    _status['is_scanning'] = True
    try:
        with app.app_context():
            from services.db_agent.db_price_scanner import run_full_scan
            result = run_full_scan(days_ahead=180)
            _status['last_scan_at'] = datetime.utcnow().isoformat()
            _status['last_scan_result'] = result
            _status['scan_count'] += 1
            logger.info(f'DB Agent scan #{_status["scan_count"]} completed: {result.get("dates_scanned")} dates scanned')
    except Exception as e:
        logger.error(f'DB Agent scan failed: {e}')
        _status['last_scan_result'] = {'error': str(e)}
    finally:
        _status['is_scanning'] = False
        _scan_lock.release()


def _scheduler_loop(app):
    """Background thread that runs scans at regular intervals."""
    global _scheduler_running, _status
    logger.info(f'DB Agent scheduler started (interval: {_scan_interval}s)')

    while _scheduler_running:
        _run_scan(app)

        # Calculate next scan time
        next_time = datetime.utcnow().timestamp() + _scan_interval
        _status['next_scan_at'] = datetime.fromtimestamp(next_time).isoformat()

        # Sleep in small increments so we can stop quickly
        elapsed = 0
        while elapsed < _scan_interval and _scheduler_running:
            time.sleep(10)
            elapsed += 10

    logger.info('DB Agent scheduler stopped')


def start_scheduler(app) -> bool:
    """Start the background scheduler. Returns True if started, False if already running."""
    global _scheduler_thread, _scheduler_running, _status

    if _scheduler_running:
        return False

    _scheduler_running = True
    _status['running'] = True
    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        args=(app,),
        daemon=True,
        name='db-agent-scheduler'
    )
    _scheduler_thread.start()
    return True


def stop_scheduler() -> bool:
    """Stop the background scheduler."""
    global _scheduler_running, _status

    if not _scheduler_running:
        return False

    _scheduler_running = False
    _status['running'] = False
    _status['next_scan_at'] = None
    return True


def trigger_manual_scan(app) -> dict:
    """Trigger a one-off scan in a background thread. Returns immediately."""
    if _status.get('is_scanning'):
        return {'status': 'already_scanning', 'message': 'A scan is already in progress.'}

    thread = threading.Thread(
        target=_run_scan,
        args=(app,),
        daemon=True,
        name='db-agent-manual-scan'
    )
    thread.start()
    return {'status': 'started', 'message': 'Manual scan started in background.'}
