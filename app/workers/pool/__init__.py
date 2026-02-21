# pool/__init__.py
"""
Judge Worker Pool Module.

This package contains the worker pool system for parallel LLM-as-Judge evaluations.

Modules:
    - worker_pool_constants: Configuration and global registry
    - worker_pool_events: Socket.IO broadcast functions
    - worker_pool_recovery: Stale comparison recovery
    - worker_pool_comparison: Comparison processing logic
    - worker_pool_statistics: Statistics updates and session completion
    - judge_worker_pool: Main pool and worker classes

Usage:
    from workers.pool import (
        trigger_judge_worker_pool,
        stop_judge_worker_pool,
        get_pool_status,
        get_worker_streams
    )
"""

from .judge_worker_pool import (
    JudgeWorkerPool,
    PooledJudgeWorker,
    trigger_judge_worker_pool,
    stop_judge_worker_pool,
    get_pool_status,
    get_worker_streams,
)

__all__ = [
    'JudgeWorkerPool',
    'PooledJudgeWorker',
    'trigger_judge_worker_pool',
    'stop_judge_worker_pool',
    'get_pool_status',
    'get_worker_streams',
]
