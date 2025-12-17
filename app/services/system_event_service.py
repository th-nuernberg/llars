"""System event logging service."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from flask import current_app, has_request_context, request


_THROTTLE_STATE: Dict[str, float] = {}


class SystemEventService:
    """Write-only service for system events (admin monitor)."""

    @staticmethod
    def log_event(
        *,
        event_type: str,
        message: str,
        severity: str = "info",
        username: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        dedupe: bool = False,
        throttle_key: Optional[str] = None,
        throttle_seconds: Optional[int] = None,
    ) -> None:
        """
        Persist an event to the DB.

        This method is best-effort: it never raises.
        """
        if not event_type or not message:
            return

        if throttle_key and throttle_seconds:
            now = time.monotonic()
            last = _THROTTLE_STATE.get(throttle_key)
            if last is not None and (now - last) < float(throttle_seconds):
                return
            _THROTTLE_STATE[throttle_key] = now

        severity_normalized = (severity or "info").strip().lower()
        if severity_normalized not in {"debug", "info", "warning", "error", "critical", "success"}:
            severity_normalized = "info"

        try:
            from db.db import db
            from db.models.system_event import SystemEvent

            request_path = None
            remote_addr = None
            user_agent = None
            if has_request_context():
                request_path = request.path
                remote_addr = request.headers.get("X-Real-IP") or request.remote_addr
                user_agent = (request.headers.get("User-Agent") or "")[:255] or None

            if dedupe:
                existing = (
                    SystemEvent.query.filter_by(
                        event_type=event_type,
                        username=username,
                        entity_type=entity_type,
                        entity_id=str(entity_id) if entity_id is not None else None,
                    )
                    .order_by(SystemEvent.id.desc())
                    .first()
                )
                if existing is not None:
                    return

            event = SystemEvent(
                event_type=event_type,
                severity=severity_normalized,
                message=message,
                username=username,
                entity_type=entity_type,
                entity_id=str(entity_id) if entity_id is not None else None,
                request_path=request_path,
                remote_addr=remote_addr,
                user_agent=user_agent,
                details=details or None,
            )

            db.session.add(event)
            db.session.commit()
        except Exception as exc:
            try:
                current_app.logger.debug(f"SystemEventService failed: {exc}")
            except Exception:
                pass

