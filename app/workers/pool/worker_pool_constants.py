# worker_pool_constants.py
"""
Constants and global registry for the Judge Worker Pool.

This module provides centralized configuration for the worker pool system:
- Worker configuration (max workers, retry attempts, timeouts)
- Heartbeat settings for stale job detection
- Thread-safe global pool registry

The global registry `_pools` maintains references to all active worker pools,
allowing external code to query status and stop pools when needed.

Used by: judge_worker_pool.py, worker_pool_recovery.py
"""

from __future__ import annotations

import threading
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .judge_worker_pool import JudgeWorkerPool


# =============================================================================
# WORKER CONFIGURATION
# =============================================================================

# Maximum number of parallel workers per session
MAX_WORKERS = 5

# Retry configuration for failed comparisons
MAX_ATTEMPTS = 3          # Maximum retry attempts per comparison
BACKOFF_BASE = 2          # Base seconds for exponential backoff (2^attempt)


# =============================================================================
# HEARTBEAT CONFIGURATION
# =============================================================================

# Heartbeat interval during comparison processing
# Workers update last_heartbeat every HEARTBEAT_INTERVAL seconds
HEARTBEAT_INTERVAL = 30   # seconds

# Stale timeout for detecting stuck comparisons
# Comparisons without heartbeat for STALE_TIMEOUT are considered abandoned
STALE_TIMEOUT = 120       # seconds


# =============================================================================
# GLOBAL POOL REGISTRY
# =============================================================================

# Thread-safe registry of active worker pools
# Maps session_id -> JudgeWorkerPool instance
_pools: Dict[int, 'JudgeWorkerPool'] = {}

# Lock for thread-safe access to the pool registry
_pool_lock = threading.Lock()


def get_pool(session_id: int) -> 'JudgeWorkerPool | None':
    """
    Get an active pool by session ID (thread-safe).

    Args:
        session_id: ID of the session

    Returns:
        JudgeWorkerPool instance if exists, None otherwise
    """
    with _pool_lock:
        return _pools.get(session_id)


def register_pool(session_id: int, pool: 'JudgeWorkerPool') -> None:
    """
    Register a new pool in the global registry (thread-safe).

    If a pool already exists for this session, it will be stopped first.

    Args:
        session_id: ID of the session
        pool: JudgeWorkerPool instance to register
    """
    with _pool_lock:
        # Stop existing pool if any
        if session_id in _pools:
            _pools[session_id].stop()
        _pools[session_id] = pool


def unregister_pool(session_id: int) -> bool:
    """
    Remove a pool from the global registry (thread-safe).

    Args:
        session_id: ID of the session

    Returns:
        True if pool was found and removed, False if not found
    """
    with _pool_lock:
        if session_id in _pools:
            del _pools[session_id]
            return True
        return False


def get_all_pool_ids() -> list[int]:
    """
    Get all active pool session IDs (thread-safe).

    Returns:
        List of session IDs with active pools
    """
    with _pool_lock:
        return list(_pools.keys())
