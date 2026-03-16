# diff_cache_service.py
"""
In-memory cache for character-level diff results in LaTeX documents.

Avoids blocking the gevent worker with O(n²) SequenceMatcher on large documents.
Instead, diffs are computed in a background task and cached by content hash.

Cache-Key: (document_id, baseline_hash, current_hash)
- Invalidation is automatic via content hash mismatch — if content changes,
  the old key simply won't match anymore.
- Explicit invalidation on commit/rollback via invalidate_document().

Thread-safe: uses threading.Lock() for cache dict access.
Background computation: uses socketio.start_background_task() (gevent-compatible).
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Cached result of a character-level diff computation."""
    insertions: int
    deletions: int
    computed_at: float


# Module-level state
_diff_cache: dict[tuple, DiffResult] = {}
_computing: set[tuple] = set()  # Keys currently being computed
_lock = threading.Lock()

# Stats for debugging
_hits = 0
_misses = 0


def _content_hash(content: str) -> str:
    """Fast hash for cache key derivation."""
    return hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()


def get_or_compute(doc_id: int, baseline: str, current: str, socketio) -> DiffResult | None:
    """
    Return cached diff if available, otherwise start background computation.

    Returns:
        DiffResult if cache hit, None if computation was started (caller should
        return diff_status="computing" to the client).
    """
    global _hits, _misses

    baseline_hash = _content_hash(baseline)
    current_hash = _content_hash(current)
    cache_key = (doc_id, baseline_hash, current_hash)

    with _lock:
        cached = _diff_cache.get(cache_key)
        if cached is not None:
            _hits += 1
            return cached

        # Already being computed — don't start a duplicate task
        if cache_key in _computing:
            _misses += 1
            return None

        _computing.add(cache_key)
        _misses += 1

    # Start background computation via gevent-compatible task
    socketio.start_background_task(
        _compute_in_background, cache_key, baseline, current
    )
    return None


def _compute_in_background(cache_key: tuple, baseline: str, current: str):
    """
    Compute char diff and store result in cache.

    Runs in a gevent greenlet spawned by socketio.start_background_task().
    No Flask app context needed — pure computation, no DB access.
    """
    from routes.latex_collab.latex_commit_routes import calculate_char_diff

    try:
        insertions, deletions = calculate_char_diff(baseline, current)
        result = DiffResult(
            insertions=insertions,
            deletions=deletions,
            computed_at=time.time()
        )

        with _lock:
            _diff_cache[cache_key] = result
            _computing.discard(cache_key)

        doc_id = cache_key[0]
        logger.debug(
            f"[DiffCache] Computed diff for doc {doc_id}: "
            f"+{insertions} -{deletions}"
        )
    except Exception:
        logger.exception(f"[DiffCache] Failed to compute diff for key {cache_key[0]}")
        with _lock:
            _computing.discard(cache_key)


def invalidate_document(doc_id: int):
    """
    Remove all cached diffs for a document.

    Called after commit or rollback to ensure fresh computation on next request.
    """
    with _lock:
        keys_to_remove = [k for k in _diff_cache if k[0] == doc_id]
        for key in keys_to_remove:
            del _diff_cache[key]

    if keys_to_remove:
        logger.debug(f"[DiffCache] Invalidated {len(keys_to_remove)} entries for doc {doc_id}")


def get_stats() -> dict:
    """Return cache statistics for debugging."""
    with _lock:
        return {
            "cache_size": len(_diff_cache),
            "computing": len(_computing),
            "hits": _hits,
            "misses": _misses,
            "hit_rate": round(_hits / max(_hits + _misses, 1) * 100, 1),
        }
