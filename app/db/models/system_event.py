"""System event log for the admin system monitor."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column

from db import db


class SystemEvent(db.Model):
    """Append-only system event log."""

    __tablename__ = "system_events"

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)

    # What happened
    event_type: Mapped[str] = mapped_column(db.String(120), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(db.String(16), index=True, default="info", nullable=False)
    message: Mapped[str] = mapped_column(db.Text, nullable=False)

    # Who/what caused it (optional)
    username: Mapped[Optional[str]] = mapped_column(db.String(255), index=True, nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(db.String(64), index=True, nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(db.String(128), index=True, nullable=True)

    # Request context (optional)
    request_path: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    remote_addr: Mapped[Optional[str]] = mapped_column(db.String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)

    # Extra info (sanitized)
    details: Mapped[Optional[dict]] = mapped_column(db.JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, index=True, nullable=False)

