"""
Socket.IO room helpers for the anonymization pipeline.
"""

from __future__ import annotations

ANONYMIZATION_OVERVIEW_ROOM = "anonymization_overview"


def anonymization_conversation_room(conversation_id: int) -> str:
    """Return the Socket.IO room name for a specific conversation."""
    return f"anonymization_conversation_{int(conversation_id)}"
