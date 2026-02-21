"""
In-memory stream state for generation outputs.

Used to serve reconnecting clients the latest partial content immediately,
without waiting for periodic DB writes.
"""

from __future__ import annotations

from threading import RLock
from typing import Dict, Optional

_lock = RLock()
_partial_by_output_id: Dict[int, str] = {}


def set_partial_content(output_id: int, content: str) -> None:
    """Store latest partial content for an output."""
    if output_id is None:
        return
    with _lock:
        _partial_by_output_id[int(output_id)] = content or ""


def get_partial_content(output_id: int) -> Optional[str]:
    """Get latest in-memory partial content for an output."""
    if output_id is None:
        return None
    with _lock:
        return _partial_by_output_id.get(int(output_id))


def clear_partial_content(output_id: int) -> None:
    """Remove partial content for an output."""
    if output_id is None:
        return
    with _lock:
        _partial_by_output_id.pop(int(output_id), None)
