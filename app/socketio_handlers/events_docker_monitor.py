"""
SocketIO event handlers for Docker container monitoring (admin-only).

Namespace: /admin

Client → Server:
    - docker:subscribe_stats      { scope?: "project"|"all" }
    - docker:unsubscribe_stats    { scope?: "project"|"all" }
    - docker:subscribe_logs       { scope?: "project"|"all", container_id?: str, mode?: "container"|"system", tail?: int }
    - docker:unsubscribe_logs

Server → Client:
    - docker:stats                { ...snapshot }
    - docker:log_line             { container_id, container_name, line }
    - docker:error                { message }
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Dict, Optional, Set

from flask import request
from flask_socketio import disconnect, emit, join_room, leave_room

from auth.oidc_validator import get_username, validate_token
from services.permission_service import PermissionService
from services.docker_monitor_service import DockerMonitorService
from services.db_explorer_service import DbExplorerService

logger = logging.getLogger(__name__)

ADMIN_NAMESPACE = "/admin"
ROOM_STATS_PROJECT = "docker_stats_project"
ROOM_STATS_ALL = "docker_stats_all"

_auth_sids: Dict[str, str] = {}

_stats_lock = threading.Lock()
_stats_task_started = False
_stats_stop = threading.Event()
_stats_project_sids: Set[str] = set()
_stats_all_sids: Set[str] = set()

_log_tasks: Dict[str, Dict[str, object]] = {}

ROOM_DB_TABLE_PREFIX = "db_table__"
_db_lock = threading.Lock()
_db_task_started = False
_db_stop = threading.Event()
_db_tables: Dict[str, Set[str]] = {}
_db_table_limits: Dict[str, int] = {}


def _is_authorized_sid(sid: str) -> bool:
    return sid in _auth_sids


def _require_authorized() -> Optional[str]:
    sid = request.sid
    username = _auth_sids.get(sid)
    if not username:
        emit("docker:error", {"message": "Unauthorized"}, namespace=ADMIN_NAMESPACE)
        disconnect(namespace=ADMIN_NAMESPACE)
        return None
    return username


def _start_stats_task(socketio) -> None:
    global _stats_task_started

    with _stats_lock:
        if _stats_task_started:
            return
        _stats_task_started = True
        _stats_stop.clear()

    def run():
        try:
            while not _stats_stop.is_set():
                with _stats_lock:
                    want_project = bool(_stats_project_sids)
                    want_all = bool(_stats_all_sids)

                if not want_project and not want_all:
                    break

                if not DockerMonitorService.ping():
                    if want_project:
                        socketio.emit(
                            "docker:error",
                            {"message": "Docker engine not reachable (is /var/run/docker.sock mounted?)"},
                            room=ROOM_STATS_PROJECT,
                            namespace=ADMIN_NAMESPACE,
                        )
                    if want_all:
                        socketio.emit(
                            "docker:error",
                            {"message": "Docker engine not reachable (is /var/run/docker.sock mounted?)"},
                            room=ROOM_STATS_ALL,
                            namespace=ADMIN_NAMESPACE,
                        )
                    time.sleep(2.0)
                    continue

                snapshot_all = None
                if want_all:
                    snapshot_all = DockerMonitorService.get_snapshot(scope="all")
                    socketio.emit(
                        "docker:stats",
                        snapshot_all,
                        room=ROOM_STATS_ALL,
                        namespace=ADMIN_NAMESPACE,
                    )

                if want_project:
                    if snapshot_all and snapshot_all.get("ok"):
                        prefix = DockerMonitorService.PROJECT_PREFIX
                        containers = [
                            c for c in (snapshot_all.get("containers") or [])
                            if str(c.get("name", "")).startswith(prefix)
                        ]

                        summary = snapshot_all.get("summary") or {}
                        project_summary = {
                            "total": len(containers),
                            "running": sum(1 for c in containers if c.get("state") == "running"),
                            "exited": sum(1 for c in containers if c.get("state") == "exited"),
                            "restarting": sum(1 for c in containers if c.get("state") == "restarting"),
                            "paused": sum(1 for c in containers if c.get("state") == "paused"),
                            "healthy": sum(1 for c in containers if c.get("health") == "healthy"),
                            "unhealthy": sum(1 for c in containers if c.get("health") == "unhealthy"),
                            "starting": sum(1 for c in containers if c.get("health") == "starting"),
                            "no_healthcheck": sum(1 for c in containers if c.get("health") is None),
                            "cpu_total_percent": round(sum(float(c.get("cpu_percent") or 0) for c in containers), 2),
                            "mem_total_bytes": int(sum(int(c.get("mem_usage") or 0) for c in containers)),
                        }

                        socketio.emit(
                            "docker:stats",
                            {
                                "ok": True,
                                "scope": "project",
                                "containers": containers,
                                "summary": project_summary,
                                "error": None,
                            },
                            room=ROOM_STATS_PROJECT,
                            namespace=ADMIN_NAMESPACE,
                        )
                    else:
                        snapshot_project = DockerMonitorService.get_snapshot(scope="project")
                        socketio.emit(
                            "docker:stats",
                            snapshot_project,
                            room=ROOM_STATS_PROJECT,
                            namespace=ADMIN_NAMESPACE,
                        )

                time.sleep(1.0)
        finally:
            with _stats_lock:
                global _stats_task_started
                _stats_task_started = False
                _stats_stop.clear()

    socketio.start_background_task(run)


def _stop_logs_for_sid(sid: str) -> None:
    task = _log_tasks.pop(sid, None)
    if not task:
        return
    stop_event = task.get("stop_event")
    if isinstance(stop_event, threading.Event):
        stop_event.set()


def register_docker_monitor_events(socketio):
    @socketio.on("connect", namespace=ADMIN_NAMESPACE)
    def handle_admin_connect():
        token = request.args.get("token") or ""
        payload = validate_token(token) if token else None
        if not payload:
            return False

        username = get_username(payload)
        if not username:
            return False

        if not PermissionService.check_permission(username, "admin:system:configure"):
            return False

        _auth_sids[request.sid] = username
        emit("docker:connected", {"username": username}, namespace=ADMIN_NAMESPACE)
        logger.info(f"[Docker Monitor] Admin socket connected: {username} ({request.sid})")

    @socketio.on("disconnect", namespace=ADMIN_NAMESPACE)
    def handle_admin_disconnect():
        sid = request.sid
        username = _auth_sids.pop(sid, None)
        _stop_logs_for_sid(sid)
        with _stats_lock:
            _stats_project_sids.discard(sid)
            _stats_all_sids.discard(sid)
            if not _stats_project_sids and not _stats_all_sids:
                _stats_stop.set()
        with _db_lock:
            to_delete = []
            for table, sids in _db_tables.items():
                sids.discard(sid)
                if not sids:
                    to_delete.append(table)
            for table in to_delete:
                _db_tables.pop(table, None)
                _db_table_limits.pop(table, None)
            if not _db_tables:
                _db_stop.set()
        logger.info(f"[Docker Monitor] Admin socket disconnected: {username or sid}")

    @socketio.on("docker:subscribe_stats", namespace=ADMIN_NAMESPACE)
    def subscribe_stats(data=None):
        username = _require_authorized()
        if not username:
            return

        data = data or {}
        scope = str(data.get("scope") or "project").strip().lower()
        sid = request.sid

        if scope == "all":
            join_room(ROOM_STATS_ALL)
            with _stats_lock:
                _stats_all_sids.add(sid)
        else:
            join_room(ROOM_STATS_PROJECT)
            with _stats_lock:
                _stats_project_sids.add(sid)

        _start_stats_task(socketio)
        emit("docker:subscribed", {"scope": scope}, namespace=ADMIN_NAMESPACE)

    @socketio.on("docker:unsubscribe_stats", namespace=ADMIN_NAMESPACE)
    def unsubscribe_stats(data=None):
        username = _require_authorized()
        if not username:
            return

        data = data or {}
        scope = str(data.get("scope") or "project").strip().lower()
        sid = request.sid

        if scope == "all":
            leave_room(ROOM_STATS_ALL)
            with _stats_lock:
                _stats_all_sids.discard(sid)
        else:
            leave_room(ROOM_STATS_PROJECT)
            with _stats_lock:
                _stats_project_sids.discard(sid)

        with _stats_lock:
            if not _stats_project_sids and not _stats_all_sids:
                _stats_stop.set()

    @socketio.on("docker:subscribe_logs", namespace=ADMIN_NAMESPACE)
    def subscribe_logs(data=None):
        username = _require_authorized()
        if not username:
            return

        if not DockerMonitorService.ping():
            emit(
                "docker:error",
                {"message": "Docker engine not reachable (is /var/run/docker.sock mounted?)"},
                namespace=ADMIN_NAMESPACE,
            )
            return

        data = data or {}
        mode = str(data.get("mode") or "container").strip().lower()
        scope = str(data.get("scope") or "project").strip().lower()
        tail = int(data.get("tail") or 200)
        tail = max(0, min(5000, tail))
        container_id = str(data.get("container_id") or "").strip()

        sid = request.sid
        _stop_logs_for_sid(sid)
        stop_event = threading.Event()
        _log_tasks[sid] = {"stop_event": stop_event}

        def emit_line(cid_short: str, cname: str, line: str):
            socketio.emit(
                "docker:log_line",
                {"container_id": cid_short, "container_name": cname, "line": line},
                room=sid,
                namespace=ADMIN_NAMESPACE,
            )

        def stream_container(cid_full: str, cid_short: str, cname: str):
            try:
                for raw in DockerMonitorService.stream_logs(container_id=cid_full, tail=tail, timestamps=True):
                    if stop_event.is_set():
                        break
                    try:
                        text = raw.decode("utf-8", errors="replace").rstrip("\n")
                    except Exception:
                        text = str(raw)
                    emit_line(cid_short, cname, text)
            except Exception as exc:
                socketio.emit(
                    "docker:error",
                    {"message": f"Log stream failed for {cname}: {exc}"},
                    room=sid,
                    namespace=ADMIN_NAMESPACE,
                )

        def run():
            try:
                if mode == "system":
                    containers = DockerMonitorService.list_containers(scope=scope)
                    for c in containers:
                        if stop_event.is_set():
                            break
                        names = c.get("Names") or []
                        cid_full = str(c.get("Id") or "")
                        cid_short = cid_full[:12]
                        cname = names[0].lstrip("/") if names else cid_short
                        socketio.start_background_task(stream_container, cid_full, cid_short, cname)
                    # keep task alive until stop
                    while not stop_event.is_set():
                        time.sleep(0.5)
                else:
                    if not container_id:
                        emit(
                            "docker:error",
                            {"message": "Missing container_id"},
                            namespace=ADMIN_NAMESPACE,
                        )
                        return
                    # Resolve name (best-effort)
                    cname = container_id
                    cid_short = container_id[:12]
                    try:
                        containers = DockerMonitorService.list_containers(scope="all")
                        for c in containers:
                            cid_full = str(c.get("Id") or "")
                            cid = cid_full[:12]
                            if cid == container_id or cid_full == container_id or cid_full.startswith(container_id):
                                names = c.get("Names") or []
                                cname = names[0].lstrip("/") if names else cid
                                cid_short = cid
                                container_id_resolved = cid_full
                                break
                        else:
                            container_id_resolved = container_id
                    except Exception:
                        container_id_resolved = container_id

                    stream_container(container_id_resolved, cid_short, cname)
            finally:
                pass

        socketio.start_background_task(run)
        emit("docker:logs_subscribed", {"mode": mode, "scope": scope, "container_id": container_id}, namespace=ADMIN_NAMESPACE)

    @socketio.on("docker:unsubscribe_logs", namespace=ADMIN_NAMESPACE)
    def unsubscribe_logs():
        username = _require_authorized()
        if not username:
            return
        _stop_logs_for_sid(request.sid)

    def _start_db_task() -> None:
        global _db_task_started

        with _db_lock:
            if _db_task_started:
                return
            _db_task_started = True
            _db_stop.clear()

        try:
            from flask import current_app

            app = current_app._get_current_object()
        except Exception:
            app = None

        def run():
            try:
                if app:
                    with app.app_context():
                        _run_loop()
                else:
                    _run_loop()
            finally:
                with _db_lock:
                    global _db_task_started
                    _db_task_started = False
                    _db_stop.clear()

        def _run_loop():
            while not _db_stop.is_set():
                with _db_lock:
                    items = list(_db_tables.items())
                    limits = dict(_db_table_limits)

                if not items:
                    break

                for table, _sids in items:
                    room = f"{ROOM_DB_TABLE_PREFIX}{table}"
                    limit = int(limits.get(table) or 50)
                    try:
                        snapshot = DbExplorerService.get_table_snapshot(table=table, limit=limit)
                        snapshot["polled_at"] = time.time()
                        socketio.emit("db:table", snapshot, room=room, namespace=ADMIN_NAMESPACE)
                    except Exception as exc:
                        socketio.emit(
                            "db:error",
                            {"message": f"DB snapshot failed for {table}: {exc}", "table": table},
                            room=room,
                            namespace=ADMIN_NAMESPACE,
                        )
                time.sleep(1.5)

        socketio.start_background_task(run)

    @socketio.on("db:get_tables", namespace=ADMIN_NAMESPACE)
    def db_get_tables():
        username = _require_authorized()
        if not username:
            return
        try:
            tables = DbExplorerService.list_tables()
            emit("db:tables", {"tables": tables}, namespace=ADMIN_NAMESPACE)
        except Exception as exc:
            emit("db:error", {"message": f"Failed to list tables: {exc}"}, namespace=ADMIN_NAMESPACE)

    @socketio.on("db:subscribe_table", namespace=ADMIN_NAMESPACE)
    def db_subscribe_table(data=None):
        username = _require_authorized()
        if not username:
            return

        data = data or {}
        table = str(data.get("table") or "").strip()
        limit = int(data.get("limit") or 50)
        limit = max(1, min(200, limit))

        try:
            # validate early
            DbExplorerService._validate_table(table)
        except Exception as exc:
            emit("db:error", {"message": str(exc) or "Invalid table"}, namespace=ADMIN_NAMESPACE)
            return

        room = f"{ROOM_DB_TABLE_PREFIX}{table}"
        join_room(room)

        sid = request.sid
        with _db_lock:
            _db_tables.setdefault(table, set()).add(sid)
            _db_table_limits[table] = limit
        _start_db_task()

        emit("db:subscribed", {"table": table, "limit": limit}, namespace=ADMIN_NAMESPACE)

    @socketio.on("db:unsubscribe_table", namespace=ADMIN_NAMESPACE)
    def db_unsubscribe_table(data=None):
        username = _require_authorized()
        if not username:
            return

        data = data or {}
        table = str(data.get("table") or "").strip()
        if not table:
            return

        room = f"{ROOM_DB_TABLE_PREFIX}{table}"
        leave_room(room)

        sid = request.sid
        with _db_lock:
            sids = _db_tables.get(table)
            if sids:
                sids.discard(sid)
                if not sids:
                    _db_tables.pop(table, None)
                    _db_table_limits.pop(table, None)
            if not _db_tables:
                _db_stop.set()

    logger.info("[Docker Monitor] Event handlers registered")
