from __future__ import annotations

import os
from functools import lru_cache
from threading import Lock
from time import time
from typing import Any

import redis


RUNTIME_WEB = "web"
RUNTIME_WORKER = "worker"
RUNTIME_STANDBY = "standby"


class _InMemoryRedis:
    """Minimal Redis substitute for tests without a live Redis service."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._values: dict[str, tuple[Any, float | None]] = {}
        self._sets: dict[str, tuple[set[str], float | None]] = {}

    def _purge_if_expired(self, key: str) -> None:
        now = time()
        value_entry = self._values.get(key)
        if value_entry is not None:
            _, expires_at = value_entry
            if expires_at is not None and expires_at <= now:
                self._values.pop(key, None)
        set_entry = self._sets.get(key)
        if set_entry is not None:
            _, expires_at = set_entry
            if expires_at is not None and expires_at <= now:
                self._sets.pop(key, None)

    @staticmethod
    def _expiry(ex: int | None) -> float | None:
        if ex is None:
            return None
        return time() + max(0, int(ex))

    def set(self, key: str, value: Any, ex: int | None = None, nx: bool = False) -> bool:
        with self._lock:
            self._purge_if_expired(key)
            if nx and (key in self._values or key in self._sets):
                return False
            self._values[key] = (value, self._expiry(ex))
            self._sets.pop(key, None)
            return True

    def setex(self, key: str, seconds: int, value: Any) -> bool:
        return self.set(key, value, ex=seconds)

    def get(self, key: str) -> Any:
        with self._lock:
            self._purge_if_expired(key)
            entry = self._values.get(key)
            return entry[0] if entry is not None else None

    def delete(self, *keys: str) -> int:
        deleted = 0
        with self._lock:
            for key in keys:
                self._purge_if_expired(key)
                if key in self._values:
                    self._values.pop(key, None)
                    deleted += 1
                if key in self._sets:
                    self._sets.pop(key, None)
                    deleted += 1
        return deleted

    def expire(self, key: str, seconds: int) -> bool:
        with self._lock:
            self._purge_if_expired(key)
            expires_at = self._expiry(seconds)
            if key in self._values:
                value, _ = self._values[key]
                self._values[key] = (value, expires_at)
                return True
            if key in self._sets:
                members, _ = self._sets[key]
                self._sets[key] = (members, expires_at)
                return True
            return False

    def sadd(self, key: str, *values: Any) -> int:
        with self._lock:
            self._purge_if_expired(key)
            members, expires_at = self._sets.get(key, (set(), None))
            added = 0
            for value in values:
                normalized = str(value)
                if normalized not in members:
                    members.add(normalized)
                    added += 1
            self._sets[key] = (members, expires_at)
            self._values.pop(key, None)
            return added

    def srem(self, key: str, *values: Any) -> int:
        with self._lock:
            self._purge_if_expired(key)
            entry = self._sets.get(key)
            if entry is None:
                return 0
            members, expires_at = entry
            removed = 0
            for value in values:
                normalized = str(value)
                if normalized in members:
                    members.remove(normalized)
                    removed += 1
            if members:
                self._sets[key] = (members, expires_at)
            else:
                self._sets.pop(key, None)
            return removed

    def scard(self, key: str) -> int:
        with self._lock:
            self._purge_if_expired(key)
            entry = self._sets.get(key)
            return len(entry[0]) if entry is not None else 0

    def smembers(self, key: str) -> set[str]:
        with self._lock:
            self._purge_if_expired(key)
            entry = self._sets.get(key)
            return set(entry[0]) if entry is not None else set()


_test_redis_client = _InMemoryRedis()


def get_runtime_role() -> str:
    role = str(os.environ.get("LLARS_RUNTIME_ROLE", RUNTIME_WEB)).strip().lower()
    if role in {RUNTIME_WEB, RUNTIME_WORKER, RUNTIME_STANDBY}:
        return role
    return RUNTIME_WEB


def is_web_runtime() -> bool:
    return get_runtime_role() == RUNTIME_WEB


def is_worker_runtime() -> bool:
    return get_runtime_role() == RUNTIME_WORKER


def is_standby_runtime() -> bool:
    return get_runtime_role() == RUNTIME_STANDBY


def get_redis_connection_kwargs(*, db_override: int | None = None) -> dict:
    is_testing = str(os.environ.get("TESTING", "")).lower() in {"1", "true", "yes", "on"}
    kwargs = {
        "host": os.environ.get("REDIS_HOST", "llars-redis"),
        "port": int(os.environ.get("REDIS_PORT", 6379)),
        "db": int(os.environ.get("REDIS_DB", 0)) if db_override is None else int(db_override),
        "password": os.environ.get("REDIS_PASSWORD", None),
        "decode_responses": True,
        "socket_connect_timeout": 0.1 if is_testing else 5,
        "socket_timeout": 0.1 if is_testing else 5,
        "retry_on_timeout": True,
    }
    return kwargs


def get_redis_url(*, db_override: int | None = None) -> str:
    kwargs = get_redis_connection_kwargs(db_override=db_override)
    password = kwargs["password"]
    auth = ""
    if password:
        auth = f":{password}@"
    return f"redis://{auth}{kwargs['host']}:{kwargs['port']}/{kwargs['db']}"


@lru_cache(maxsize=4)
def _build_redis_client(cache_key: tuple) -> redis.Redis:
    kwargs = dict(cache_key[1])
    return redis.Redis(**kwargs)


def get_redis_client(*, db_override: int | None = None) -> redis.Redis:
    is_testing = str(os.environ.get("TESTING", "")).lower() in {"1", "true", "yes", "on"}
    if is_testing and os.environ.get("LLARS_USE_REAL_REDIS_IN_TESTS", "").lower() not in {"1", "true", "yes", "on"}:
        return _test_redis_client
    kwargs = get_redis_connection_kwargs(db_override=db_override)
    cache_key = (db_override, tuple(sorted(kwargs.items())))
    return _build_redis_client(cache_key)
