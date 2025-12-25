"""
SocketIO event handlers for system health monitoring (admin-only).

Namespace: /admin

Client → Server:
    - host:subscribe         {}
    - host:unsubscribe       {}
    - api:subscribe          { window?: "1min"|"5min"|"15min"|"1hour" }
    - api:unsubscribe        {}
    - ws:subscribe           {}
    - ws:unsubscribe         {}

Server → Client:
    - host:stats             { ...snapshot }
    - api:stats              { ...snapshot }
    - ws:stats               { ...snapshot }
    - health:error           { message }
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Set

from flask import request
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)

ADMIN_NAMESPACE = "/admin"

# Rooms for system health subscriptions
ROOM_HOST_STATS = "host_stats"
ROOM_API_STATS = "api_stats"
ROOM_WS_STATS = "ws_stats"

# Subscriber tracking
_host_lock = threading.Lock()
_host_task_started = False
_host_stop = threading.Event()
_host_sids: Set[str] = set()

_api_lock = threading.Lock()
_api_task_started = False
_api_stop = threading.Event()
_api_sids: Set[str] = set()
_api_windows: Dict[str, str] = {}  # sid -> window

_ws_lock = threading.Lock()
_ws_task_started = False
_ws_stop = threading.Event()
_ws_sids: Set[str] = set()


def _is_authorized(auth_sids: Dict[str, str], sid: str) -> bool:
    """Check if SID is authorized (must be in auth_sids from docker_monitor)."""
    return sid in auth_sids


def _start_host_task(socketio, auth_sids: Dict[str, str]) -> None:
    """Start background task for host metrics polling."""
    global _host_task_started

    with _host_lock:
        if _host_task_started:
            return
        _host_task_started = True
        _host_stop.clear()

    def run():
        try:
            from services.host_metrics_service import HostMetricsService

            while not _host_stop.is_set():
                with _host_lock:
                    if not _host_sids:
                        break

                try:
                    snapshot = HostMetricsService.get_snapshot()
                    socketio.emit(
                        "host:stats",
                        snapshot,
                        room=ROOM_HOST_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )
                except Exception as exc:
                    logger.warning(f"[System Health] Host metrics error: {exc}")
                    socketio.emit(
                        "health:error",
                        {"message": f"Host metrics error: {exc}"},
                        room=ROOM_HOST_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )

                time.sleep(2.0)  # 2s polling interval
        finally:
            with _host_lock:
                global _host_task_started
                _host_task_started = False
                _host_stop.clear()

    socketio.start_background_task(run)


def _start_api_task(socketio, auth_sids: Dict[str, str]) -> None:
    """Start background task for API metrics polling."""
    global _api_task_started

    with _api_lock:
        if _api_task_started:
            return
        _api_task_started = True
        _api_stop.clear()

    def run():
        try:
            from services.api_metrics_service import ApiMetricsService

            while not _api_stop.is_set():
                with _api_lock:
                    if not _api_sids:
                        break

                try:
                    snapshot = ApiMetricsService.get_snapshot()
                    socketio.emit(
                        "api:stats",
                        snapshot,
                        room=ROOM_API_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )
                except Exception as exc:
                    logger.warning(f"[System Health] API metrics error: {exc}")
                    socketio.emit(
                        "health:error",
                        {"message": f"API metrics error: {exc}"},
                        room=ROOM_API_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )

                time.sleep(2.0)  # 2s polling interval
        finally:
            with _api_lock:
                global _api_task_started
                _api_task_started = False
                _api_stop.clear()

    socketio.start_background_task(run)


def _start_ws_task(socketio, auth_sids: Dict[str, str]) -> None:
    """Start background task for WebSocket metrics polling."""
    global _ws_task_started

    with _ws_lock:
        if _ws_task_started:
            return
        _ws_task_started = True
        _ws_stop.clear()

    def run():
        try:
            from services.websocket_metrics_service import WebSocketMetricsService

            while not _ws_stop.is_set():
                with _ws_lock:
                    if not _ws_sids:
                        break

                try:
                    snapshot = WebSocketMetricsService.get_snapshot()
                    socketio.emit(
                        "ws:stats",
                        snapshot,
                        room=ROOM_WS_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )
                except Exception as exc:
                    logger.warning(f"[System Health] WebSocket metrics error: {exc}")
                    socketio.emit(
                        "health:error",
                        {"message": f"WebSocket metrics error: {exc}"},
                        room=ROOM_WS_STATS,
                        namespace=ADMIN_NAMESPACE,
                    )

                time.sleep(2.0)  # 2s polling interval
        finally:
            with _ws_lock:
                global _ws_task_started
                _ws_task_started = False
                _ws_stop.clear()

    socketio.start_background_task(run)


def register_system_health_events(socketio, auth_sids: Dict[str, str]):
    """Register system health event handlers.

    Args:
        socketio: Flask-SocketIO instance
        auth_sids: Shared dict of authorized SIDs from docker_monitor events
    """

    @socketio.on("host:subscribe", namespace=ADMIN_NAMESPACE)
    def subscribe_host(data=None):
        sid = request.sid
        if not _is_authorized(auth_sids, sid):
            emit("health:error", {"message": "Unauthorized"}, namespace=ADMIN_NAMESPACE)
            return

        join_room(ROOM_HOST_STATS)
        with _host_lock:
            _host_sids.add(sid)

        _start_host_task(socketio, auth_sids)
        emit("host:subscribed", {}, namespace=ADMIN_NAMESPACE)

        # Send immediate snapshot
        try:
            from services.host_metrics_service import HostMetricsService
            snapshot = HostMetricsService.get_snapshot()
            emit("host:stats", snapshot, namespace=ADMIN_NAMESPACE)
        except Exception as exc:
            logger.warning(f"[System Health] Immediate host snapshot failed: {exc}")

    @socketio.on("host:unsubscribe", namespace=ADMIN_NAMESPACE)
    def unsubscribe_host(data=None):
        sid = request.sid
        leave_room(ROOM_HOST_STATS)
        with _host_lock:
            _host_sids.discard(sid)
            if not _host_sids:
                _host_stop.set()

    @socketio.on("api:subscribe", namespace=ADMIN_NAMESPACE)
    def subscribe_api(data=None):
        sid = request.sid
        if not _is_authorized(auth_sids, sid):
            emit("health:error", {"message": "Unauthorized"}, namespace=ADMIN_NAMESPACE)
            return

        data = data or {}
        window = str(data.get("window", "5min"))

        join_room(ROOM_API_STATS)
        with _api_lock:
            _api_sids.add(sid)
            _api_windows[sid] = window

        _start_api_task(socketio, auth_sids)
        emit("api:subscribed", {"window": window}, namespace=ADMIN_NAMESPACE)

        # Send immediate snapshot
        try:
            from services.api_metrics_service import ApiMetricsService
            snapshot = ApiMetricsService.get_snapshot()
            emit("api:stats", snapshot, namespace=ADMIN_NAMESPACE)
        except Exception as exc:
            logger.warning(f"[System Health] Immediate API snapshot failed: {exc}")

    @socketio.on("api:unsubscribe", namespace=ADMIN_NAMESPACE)
    def unsubscribe_api(data=None):
        sid = request.sid
        leave_room(ROOM_API_STATS)
        with _api_lock:
            _api_sids.discard(sid)
            _api_windows.pop(sid, None)
            if not _api_sids:
                _api_stop.set()

    @socketio.on("ws:subscribe", namespace=ADMIN_NAMESPACE)
    def subscribe_ws(data=None):
        sid = request.sid
        if not _is_authorized(auth_sids, sid):
            emit("health:error", {"message": "Unauthorized"}, namespace=ADMIN_NAMESPACE)
            return

        join_room(ROOM_WS_STATS)
        with _ws_lock:
            _ws_sids.add(sid)

        _start_ws_task(socketio, auth_sids)
        emit("ws:subscribed", {}, namespace=ADMIN_NAMESPACE)

        # Send immediate snapshot
        try:
            from services.websocket_metrics_service import WebSocketMetricsService
            snapshot = WebSocketMetricsService.get_snapshot()
            emit("ws:stats", snapshot, namespace=ADMIN_NAMESPACE)
        except Exception as exc:
            logger.warning(f"[System Health] Immediate WS snapshot failed: {exc}")

    @socketio.on("ws:unsubscribe", namespace=ADMIN_NAMESPACE)
    def unsubscribe_ws(data=None):
        sid = request.sid
        leave_room(ROOM_WS_STATS)
        with _ws_lock:
            _ws_sids.discard(sid)
            if not _ws_sids:
                _ws_stop.set()

    logger.info("[System Health] Event handlers registered")


def cleanup_system_health_subscriber(sid: str) -> None:
    """Clean up subscriptions when a client disconnects.

    Call this from the main disconnect handler in docker_monitor.
    """
    with _host_lock:
        _host_sids.discard(sid)
        if not _host_sids:
            _host_stop.set()

    with _api_lock:
        _api_sids.discard(sid)
        _api_windows.pop(sid, None)
        if not _api_sids:
            _api_stop.set()

    with _ws_lock:
        _ws_sids.discard(sid)
        if not _ws_sids:
            _ws_stop.set()
