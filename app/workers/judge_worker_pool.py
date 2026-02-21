# judge_worker_pool.py
"""
Worker Pool for parallel LLM-as-Judge Evaluations.

DEPRECATED: This file is kept for backward compatibility.
The implementation has been moved to workers/pool/ module.

Import from workers.pool instead:
    from workers.pool import (
        JudgeWorkerPool,
        PooledJudgeWorker,
        trigger_judge_worker_pool,
        stop_judge_worker_pool,
        get_pool_status,
        get_worker_streams
    )

Or use the legacy imports (still supported):
    from workers.judge_worker_pool import trigger_judge_worker_pool

Module Structure (workers/pool/):
    - worker_pool_constants.py: Configuration and global registry
    - worker_pool_events.py: Socket.IO broadcast functions
    - worker_pool_recovery.py: Stale comparison recovery
    - worker_pool_comparison.py: Comparison claiming and processing
    - worker_pool_statistics.py: Statistics updates and session completion
    - judge_worker_pool.py: Main pool and worker classes

Author: LLARS Team
Date: November 2025 (refactored January 2026)
"""

# Re-export everything from the new module location for backward compatibility
from .pool.judge_worker_pool import (
    JudgeWorkerPool,
    PooledJudgeWorker,
    trigger_judge_worker_pool,
    stop_judge_worker_pool,
    get_pool_status,
    get_worker_streams,
)

# Re-export constants for any code that might reference them
from .pool.worker_pool_constants import (
    MAX_WORKERS,
    MAX_ATTEMPTS,
    BACKOFF_BASE,
    HEARTBEAT_INTERVAL,
    STALE_TIMEOUT,
    _pools,
    _pool_lock,
)

__all__ = [
    # Main classes
    'JudgeWorkerPool',
    'PooledJudgeWorker',

    # Pool management functions
    'trigger_judge_worker_pool',
    'stop_judge_worker_pool',
    'get_pool_status',
    'get_worker_streams',

    # Constants (for advanced usage)
    'MAX_WORKERS',
    'MAX_ATTEMPTS',
    'BACKOFF_BASE',
    'HEARTBEAT_INTERVAL',
    'STALE_TIMEOUT',

    # Global registry (for advanced usage)
    '_pools',
    '_pool_lock',
]
