"""
Socket.IO room helpers for batch generation.
"""

from __future__ import annotations

GENERATION_OVERVIEW_ROOM = "generation_overview"


def generation_job_room(job_id: int) -> str:
    """Return the Socket.IO room name for a generation job."""
    return f"generation_job_{int(job_id)}"

