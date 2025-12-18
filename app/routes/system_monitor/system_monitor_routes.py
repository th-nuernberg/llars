from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from flask import Response, jsonify, request, stream_with_context

from db.db import db
from db.models.system_event import SystemEvent
from decorators.permission_decorator import require_permission
from routes.auth import data_bp


def _serialize_event(event: SystemEvent) -> Dict[str, Any]:
    return {
        "id": int(event.id),
        "event_type": event.event_type,
        "severity": event.severity,
        "message": event.message,
        "username": event.username,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "request_path": event.request_path,
        "remote_addr": event.remote_addr,
        "created_at": event.created_at.isoformat() + "Z",
        "details": event.details or None,
    }


@data_bp.get("/admin/system/events")
@require_permission("admin:system:configure")
def list_system_events():
    limit_raw = request.args.get("limit", "200")
    before_id_raw = request.args.get("before_id")
    severity = (request.args.get("severity") or "").strip().lower()
    event_type = (request.args.get("event_type") or "").strip()

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 200
    limit = max(1, min(1000, limit))

    query = SystemEvent.query
    if before_id_raw:
        try:
            before_id = int(before_id_raw)
            query = query.filter(SystemEvent.id < before_id)
        except ValueError:
            pass

    if severity:
        query = query.filter(SystemEvent.severity == severity)
    if event_type:
        query = query.filter(SystemEvent.event_type.like(f"{event_type}%"))

    events = query.order_by(SystemEvent.id.desc()).limit(limit).all()
    payload = [_serialize_event(e) for e in events]
    return jsonify({"events": payload}), 200


@data_bp.get("/admin/system/events/stream")
@require_permission("admin:system:configure")
def stream_system_events():
    after_id_raw = request.args.get("after_id") or request.headers.get("Last-Event-ID") or "0"
    try:
        after_id = int(after_id_raw)
    except ValueError:
        after_id = 0

    def _sse(event_id: Optional[int], data: Dict[str, Any]) -> str:
        lines = []
        if event_id is not None:
            lines.append(f"id: {event_id}")
        lines.append("event: system_event")
        lines.append(f"data: {json.dumps(data, separators=(',', ':'))}")
        return "\n".join(lines) + "\n\n"

    @stream_with_context
    def generate():
        last_id = after_id

        # Hint for browsers to retry quickly
        yield "retry: 2000\n\n"

        while True:
            try:
                rows: List[SystemEvent] = (
                    SystemEvent.query.filter(SystemEvent.id > last_id)
                    .order_by(SystemEvent.id.asc())
                    .limit(200)
                    .all()
                )

                for row in rows:
                    last_id = int(row.id)
                    yield _sse(last_id, _serialize_event(row))

                # Keep-alive ping to prevent proxies from closing the connection
                if not rows:
                    yield "event: ping\ndata: {}\n\n"

                db.session.remove()
                time.sleep(1.0)
            except GeneratorExit:
                break
            except Exception:
                db.session.remove()
                time.sleep(2.0)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return Response(generate(), headers=headers)
