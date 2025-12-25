from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Response, jsonify, request, stream_with_context
from sqlalchemy import or_

from db.db import db
from db.models.system_event import SystemEvent
from decorators.permission_decorator import require_permission
from routes.auth import data_bp
from services.chatbot_activity_service import ChatbotActivityService


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


# ============================================================================
# CHATBOT ACTIVITY ENDPOINTS
# ============================================================================

@data_bp.get("/admin/chatbot-activity")
@require_permission("admin:system:configure")
def list_chatbot_activities():
    """
    Get chatbot-related activities (chatbots, chats, collections, documents, wizard).

    Query Parameters:
        - limit: Max number of results (default 100, max 500)
        - offset: Pagination offset (default 0)
        - period: Time period filter (24h, 7d, 30d)
        - username: Filter by username
        - type: Filter by event type prefix (chatbot, wizard, chat, collection, document)
        - chatbot_id: Filter by chatbot ID
    """
    limit_raw = request.args.get("limit", "100")
    offset_raw = request.args.get("offset", "0")
    period = request.args.get("period", "").strip()
    username_filter = request.args.get("username", "").strip()
    event_type_prefix = request.args.get("type", "").strip()
    chatbot_id_raw = request.args.get("chatbot_id", "")

    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 100
    limit = max(1, min(500, limit))

    try:
        offset = int(offset_raw)
    except ValueError:
        offset = 0
    offset = max(0, offset)

    # Parse period to datetime
    since = None
    if period:
        period_hours = {
            "1h": 1,
            "24h": 24,
            "7d": 24 * 7,
            "30d": 24 * 30,
        }.get(period.lower())
        if period_hours:
            since = datetime.utcnow() - timedelta(hours=period_hours)

    # Parse chatbot_id
    chatbot_id = None
    if chatbot_id_raw:
        try:
            chatbot_id = int(chatbot_id_raw)
        except ValueError:
            pass

    activities = ChatbotActivityService.get_activities(
        limit=limit,
        offset=offset,
        username=username_filter if username_filter else None,
        event_type_prefix=event_type_prefix if event_type_prefix else None,
        chatbot_id=chatbot_id,
        since=since
    )

    return jsonify({
        "success": True,
        "activities": activities,
        "count": len(activities),
        "limit": limit,
        "offset": offset
    }), 200


@data_bp.get("/admin/chatbot-activity/stats")
@require_permission("admin:system:configure")
def get_chatbot_activity_stats():
    """
    Get chatbot activity statistics.

    Query Parameters:
        - period: Time period in hours (default 24)
    """
    period_raw = request.args.get("period", "24")
    try:
        period_hours = int(period_raw)
    except ValueError:
        period_hours = 24
    period_hours = max(1, min(720, period_hours))  # 1 hour to 30 days

    stats = ChatbotActivityService.get_activity_stats(period_hours=period_hours)

    return jsonify({
        "success": True,
        "stats": stats
    }), 200


@data_bp.get("/admin/chatbot-activity/stream")
@require_permission("admin:system:configure")
def stream_chatbot_activities():
    """
    Stream chatbot activities via Server-Sent Events.

    Query Parameters:
        - after_id: Start streaming from this event ID
    """
    after_id_raw = request.args.get("after_id") or request.headers.get("Last-Event-ID") or "0"
    try:
        after_id = int(after_id_raw)
    except ValueError:
        after_id = 0

    # Define the tracked prefixes for chatbot activities
    tracked_prefixes = ChatbotActivityService.TRACKED_PREFIXES

    def _sse(event_id: Optional[int], data: Dict[str, Any]) -> str:
        lines = []
        if event_id is not None:
            lines.append(f"id: {event_id}")
        lines.append("event: chatbot_activity")
        lines.append(f"data: {json.dumps(data, separators=(',', ':'))}")
        return "\n".join(lines) + "\n\n"

    @stream_with_context
    def generate():
        last_id = after_id

        # Hint for browsers to retry quickly
        yield "retry: 2000\n\n"

        while True:
            try:
                # Build filter for chatbot-related events
                prefix_filters = [
                    SystemEvent.event_type.like(f"{prefix}.%")
                    for prefix in tracked_prefixes
                ]

                rows: List[SystemEvent] = (
                    SystemEvent.query.filter(
                        SystemEvent.id > last_id,
                        or_(*prefix_filters)
                    )
                    .order_by(SystemEvent.id.asc())
                    .limit(100)
                    .all()
                )

                for row in rows:
                    last_id = int(row.id)
                    yield _sse(last_id, _serialize_event(row))

                # Keep-alive ping
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
