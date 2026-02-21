"""
Presence Service

Tracks online/active users via Redis-backed Socket.IO signals and persists
last_seen_at/last_active_at in MariaDB for admin visibility.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from db.database import db
from db.models.user import User


_presence_service = None


def get_presence_service():
    """Get singleton PresenceService instance."""
    global _presence_service
    if _presence_service is None:
        from main import redis_client

        _presence_service = PresenceService(redis_client)
    return _presence_service


class PresenceService:
    """Redis-backed presence tracking with DB persistence."""

    KEY_USER_LAST_SEEN = "presence:user:last_seen"
    KEY_USER_LAST_ACTIVE = "presence:user:last_active"
    KEY_USER_SOCKETS = "presence:user:sockets:{user_id}"
    KEY_SOCKET_USER = "presence:socket:user:{sid}"
    KEY_LAST_DB_SEEN = "presence:last_db_seen:{user_id}"
    KEY_LAST_DB_ACTIVE = "presence:last_db_active:{user_id}"

    ONLINE_TIMEOUT_SECONDS = int(os.getenv("PRESENCE_ONLINE_TIMEOUT", "90"))
    ACTIVE_WINDOW_SECONDS = int(os.getenv("PRESENCE_ACTIVE_WINDOW", "120"))
    DB_WRITE_THROTTLE_SECONDS = int(os.getenv("PRESENCE_DB_WRITE_THROTTLE", "120"))
    SOCKET_TTL_SECONDS = int(os.getenv("PRESENCE_SOCKET_TTL", "300"))

    def __init__(self, redis_client):
        self.redis = redis_client

    def record_seen(self, user: User, socket_id: Optional[str], force_db: bool = False) -> Dict[str, Any]:
        """Record a heartbeat/seen signal for a user."""
        now = datetime.utcnow()
        now_ts = now.timestamp()
        user_id = str(user.id)

        self.redis.zadd(self.KEY_USER_LAST_SEEN, {user_id: now_ts})
        sockets_key = self.KEY_USER_SOCKETS.format(user_id=user_id)

        if socket_id:
            self.redis.zadd(sockets_key, {socket_id: now_ts})
            self.redis.setex(self.KEY_SOCKET_USER.format(sid=socket_id), self.SOCKET_TTL_SECONDS, user_id)
            self.redis.expire(sockets_key, self.SOCKET_TTL_SECONDS)

        self._purge_stale_sockets(sockets_key, now_ts)
        self._maybe_update_db(user.id, last_seen_at=now, force=force_db)

        return self.build_user_payload(user, now_ts=now_ts)

    def record_active(self, user: User, socket_id: Optional[str]) -> Dict[str, Any]:
        """Record a user activity signal."""
        now = datetime.utcnow()
        now_ts = now.timestamp()
        user_id = str(user.id)

        self.redis.zadd(self.KEY_USER_LAST_SEEN, {user_id: now_ts})
        self.redis.zadd(self.KEY_USER_LAST_ACTIVE, {user_id: now_ts})

        sockets_key = self.KEY_USER_SOCKETS.format(user_id=user_id)
        if socket_id:
            self.redis.zadd(sockets_key, {socket_id: now_ts})
            self.redis.setex(self.KEY_SOCKET_USER.format(sid=socket_id), self.SOCKET_TTL_SECONDS, user_id)
            self.redis.expire(sockets_key, self.SOCKET_TTL_SECONDS)

        self._purge_stale_sockets(sockets_key, now_ts)
        self._maybe_update_db(user.id, last_seen_at=now, last_active_at=now)

        return self.build_user_payload(user, now_ts=now_ts)

    def remove_socket(self, socket_id: str) -> Optional[Dict[str, Any]]:
        """Remove a socket association and mark user as seen at disconnect."""
        if not socket_id:
            return None

        user_id = self.redis.get(self.KEY_SOCKET_USER.format(sid=socket_id))
        if not user_id:
            return None

        sockets_key = self.KEY_USER_SOCKETS.format(user_id=user_id)
        self.redis.zrem(sockets_key, socket_id)
        self.redis.delete(self.KEY_SOCKET_USER.format(sid=socket_id))

        now = datetime.utcnow()
        now_ts = now.timestamp()
        self.redis.zadd(self.KEY_USER_LAST_SEEN, {user_id: now_ts})
        self._maybe_update_db(int(user_id), last_seen_at=now, force=True)

        user = db.session.get(User, int(user_id))
        if not user:
            return None

        return self.build_user_payload(user, now_ts=now_ts)

    def build_user_payload(self, user: User, now_ts: Optional[float] = None) -> Dict[str, Any]:
        """Build payload for admin presence UI."""
        now_ts = now_ts or datetime.utcnow().timestamp()
        user_id = str(user.id)

        redis_seen = self.redis.zscore(self.KEY_USER_LAST_SEEN, user_id)
        redis_active = self.redis.zscore(self.KEY_USER_LAST_ACTIVE, user_id)

        last_seen_ts = self._coalesce_timestamp(redis_seen, user.last_seen_at)
        last_active_ts = self._coalesce_timestamp(redis_active, user.last_active_at)

        online_socket_count = self._count_online_sockets(user_id, now_ts)
        status = self._compute_status(online_socket_count, last_seen_ts, last_active_ts, now_ts)

        return {
            "user_id": int(user.id),
            "username": user.username,
            "status": status,
            "last_seen_at": self._format_iso(last_seen_ts),
            "last_active_at": self._format_iso(last_active_ts),
        }

    def list_users(self) -> List[Dict[str, Any]]:
        """Return presence payloads for all users."""
        now_ts = datetime.utcnow().timestamp()
        users = (
            db.session.query(User)
            .filter(User.deleted_at.is_(None))
            .filter(User.is_active.is_(True))
            .order_by(User.username.asc())
            .all()
        )
        return [self.build_user_payload(user, now_ts=now_ts) for user in users]

    def _count_online_sockets(self, user_id: str, now_ts: float) -> int:
        sockets_key = self.KEY_USER_SOCKETS.format(user_id=user_id)
        threshold = now_ts - self.ONLINE_TIMEOUT_SECONDS
        return int(self.redis.zcount(sockets_key, threshold, "+inf"))

    def _purge_stale_sockets(self, sockets_key: str, now_ts: float) -> None:
        threshold = now_ts - (self.ONLINE_TIMEOUT_SECONDS * 2)
        try:
            self.redis.zremrangebyscore(sockets_key, 0, threshold)
        except Exception:
            pass

    def _maybe_update_db(
        self,
        user_id: int,
        last_seen_at: Optional[datetime] = None,
        last_active_at: Optional[datetime] = None,
        force: bool = False,
    ) -> None:
        updates: Dict[str, Any] = {}

        if last_seen_at and (force or self._should_write_db(self.KEY_LAST_DB_SEEN.format(user_id=user_id))):
            updates["last_seen_at"] = last_seen_at

        if last_active_at and (force or self._should_write_db(self.KEY_LAST_DB_ACTIVE.format(user_id=user_id))):
            updates["last_active_at"] = last_active_at

        if not updates:
            return

        try:
            db.session.query(User).filter_by(id=user_id).update(updates)
            db.session.commit()
        except Exception:
            db.session.rollback()

    def _should_write_db(self, key: str) -> bool:
        now_ts = datetime.utcnow().timestamp()
        last_raw = self.redis.get(key)
        try:
            last_ts = float(last_raw) if last_raw else None
        except (TypeError, ValueError):
            last_ts = None

        if last_ts is not None and (now_ts - last_ts) < self.DB_WRITE_THROTTLE_SECONDS:
            return False

        self.redis.setex(key, self.DB_WRITE_THROTTLE_SECONDS * 2, str(now_ts))
        return True

    @staticmethod
    def _coalesce_timestamp(redis_ts: Optional[float], db_dt: Optional[datetime]) -> Optional[float]:
        db_ts = db_dt.timestamp() if db_dt else None
        if redis_ts is None and db_ts is None:
            return None
        if redis_ts is None:
            return db_ts
        if db_ts is None:
            return float(redis_ts)
        return float(max(redis_ts, db_ts))

    @staticmethod
    def _format_iso(ts: Optional[float]) -> Optional[str]:
        if not ts:
            return None
        return datetime.utcfromtimestamp(float(ts)).isoformat() + "Z"

    def _compute_status(
        self,
        online_socket_count: int,
        last_seen_ts: Optional[float],
        last_active_ts: Optional[float],
        now_ts: float,
    ) -> str:
        if online_socket_count <= 0:
            return "offline"

        if last_seen_ts is None or (now_ts - last_seen_ts) > self.ONLINE_TIMEOUT_SECONDS:
            return "offline"

        if last_active_ts is not None and (now_ts - last_active_ts) <= self.ACTIVE_WINDOW_SECONDS:
            return "active"

        return "online"
