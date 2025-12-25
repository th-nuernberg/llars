"""API performance metrics service.

Collects request latency, throughput, and error statistics via Flask middleware.
Uses a ring buffer for efficient memory usage.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple


@dataclass
class RequestMetric:
    """Single request metric entry."""
    timestamp: float
    method: str
    path: str
    status_code: int
    latency_ms: float
    error: Optional[str] = None


@dataclass
class EndpointStats:
    """Aggregated stats for a single endpoint."""
    method: str
    path: str
    count: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0
    error_count: int = 0
    latencies: List[float] = field(default_factory=list)

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.count if self.count > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return (self.error_count / self.count * 100) if self.count > 0 else 0.0

    def percentile(self, p: int) -> float:
        """Calculate percentile from stored latencies."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * p / 100)
        idx = min(idx, len(sorted_latencies) - 1)
        return sorted_latencies[idx]


class ApiMetricsService:
    """Collect and aggregate API performance metrics."""

    # Ring buffer size (store last N requests)
    MAX_REQUESTS = 10000

    # Time windows for aggregation (in seconds)
    WINDOWS = {
        "1min": 60,
        "5min": 300,
        "15min": 900,
        "1hour": 3600,
    }

    _lock = threading.Lock()
    _requests: Deque[RequestMetric] = deque(maxlen=MAX_REQUESTS)
    _recent_errors: Deque[RequestMetric] = deque(maxlen=100)

    # Paths to exclude from metrics
    EXCLUDE_PATHS = {
        '/api/health',
        '/api/admin/system/events/stream',
        '/metrics.php',
        '/metrics.js',
        '/analytics/',
        '/socket.io/',
    }

    # Path patterns to normalize (replace IDs with placeholders)
    PATH_PATTERNS = [
        (r'/\d+', '/<id>'),
        (r'/[a-f0-9-]{36}', '/<uuid>'),
    ]

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        """Normalize path by replacing dynamic segments."""
        import re

        # Remove query string
        path = path.split('?')[0]

        # Apply patterns
        for pattern, replacement in cls.PATH_PATTERNS:
            path = re.sub(pattern, replacement, path)

        return path

    @classmethod
    def _should_track(cls, path: str) -> bool:
        """Check if path should be tracked."""
        for exclude in cls.EXCLUDE_PATHS:
            if path.startswith(exclude):
                return False
        return True

    @classmethod
    def record_request(
        cls,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        error: Optional[str] = None,
    ) -> None:
        """Record a single request metric."""
        if not cls._should_track(path):
            return

        normalized_path = cls._normalize_path(path)

        metric = RequestMetric(
            timestamp=time.time(),
            method=method.upper(),
            path=normalized_path,
            status_code=status_code,
            latency_ms=round(latency_ms, 2),
            error=error,
        )

        with cls._lock:
            cls._requests.append(metric)

            # Track errors separately for quick access
            if status_code >= 400:
                cls._recent_errors.append(metric)

    @classmethod
    def get_stats(cls, window: str = "5min") -> Dict[str, Any]:
        """Get aggregated stats for a time window."""
        window_seconds = cls.WINDOWS.get(window, 300)
        cutoff = time.time() - window_seconds

        with cls._lock:
            requests = [r for r in cls._requests if r.timestamp >= cutoff]

        if not requests:
            return {
                "window": window,
                "window_seconds": window_seconds,
                "request_count": 0,
                "requests_per_sec": 0.0,
                "avg_latency_ms": 0.0,
                "min_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "error_count": 0,
                "error_rate": 0.0,
                "status_codes": {},
                "endpoints": [],
            }

        # Calculate overall stats
        total_count = len(requests)
        latencies = [r.latency_ms for r in requests]
        sorted_latencies = sorted(latencies)

        error_count = sum(1 for r in requests if r.status_code >= 400)

        # Status code distribution
        status_codes: Dict[str, int] = defaultdict(int)
        for r in requests:
            category = f"{r.status_code // 100}xx"
            status_codes[category] += 1

        # Calculate time span for rate calculation
        if len(requests) > 1:
            time_span = requests[-1].timestamp - requests[0].timestamp
            requests_per_sec = total_count / time_span if time_span > 0 else 0.0
        else:
            requests_per_sec = total_count / window_seconds

        # Per-endpoint stats
        endpoint_map: Dict[Tuple[str, str], EndpointStats] = {}
        for r in requests:
            key = (r.method, r.path)
            if key not in endpoint_map:
                endpoint_map[key] = EndpointStats(method=r.method, path=r.path)

            stats = endpoint_map[key]
            stats.count += 1
            stats.total_latency_ms += r.latency_ms
            stats.min_latency_ms = min(stats.min_latency_ms, r.latency_ms)
            stats.max_latency_ms = max(stats.max_latency_ms, r.latency_ms)
            stats.latencies.append(r.latency_ms)
            if r.status_code >= 400:
                stats.error_count += 1

        # Sort endpoints by average latency (descending)
        endpoints = sorted(
            endpoint_map.values(),
            key=lambda e: e.avg_latency_ms,
            reverse=True,
        )[:20]  # Top 20

        def percentile(arr: List[float], p: int) -> float:
            if not arr:
                return 0.0
            idx = int(len(arr) * p / 100)
            idx = min(idx, len(arr) - 1)
            return arr[idx]

        return {
            "window": window,
            "window_seconds": window_seconds,
            "request_count": total_count,
            "requests_per_sec": round(requests_per_sec, 2),
            "avg_latency_ms": round(sum(latencies) / total_count, 2),
            "min_latency_ms": round(min(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "p50_latency_ms": round(percentile(sorted_latencies, 50), 2),
            "p95_latency_ms": round(percentile(sorted_latencies, 95), 2),
            "p99_latency_ms": round(percentile(sorted_latencies, 99), 2),
            "error_count": error_count,
            "error_rate": round(error_count / total_count * 100, 2),
            "status_codes": dict(status_codes),
            "endpoints": [
                {
                    "method": e.method,
                    "path": e.path,
                    "count": e.count,
                    "avg_latency_ms": round(e.avg_latency_ms, 2),
                    "min_latency_ms": round(e.min_latency_ms, 2) if e.min_latency_ms != float('inf') else 0.0,
                    "max_latency_ms": round(e.max_latency_ms, 2),
                    "p95_latency_ms": round(e.percentile(95), 2),
                    "error_count": e.error_count,
                    "error_rate": round(e.error_rate, 2),
                }
                for e in endpoints
            ],
        }

    @classmethod
    def get_recent_errors(cls, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent error requests."""
        with cls._lock:
            errors = list(cls._recent_errors)[-limit:]

        return [
            {
                "timestamp": e.timestamp,
                "method": e.method,
                "path": e.path,
                "status_code": e.status_code,
                "latency_ms": e.latency_ms,
                "error": e.error,
                "age_seconds": round(time.time() - e.timestamp, 1),
            }
            for e in reversed(errors)
        ]

    @classmethod
    def get_throughput_history(cls, window: str = "5min", buckets: int = 60) -> List[Dict[str, Any]]:
        """Get throughput history as time series data for charts."""
        window_seconds = cls.WINDOWS.get(window, 300)
        bucket_size = window_seconds / buckets
        cutoff = time.time() - window_seconds

        with cls._lock:
            requests = [r for r in cls._requests if r.timestamp >= cutoff]

        if not requests:
            return []

        # Initialize buckets
        now = time.time()
        history: List[Dict[str, Any]] = []

        for i in range(buckets):
            bucket_start = now - window_seconds + (i * bucket_size)
            bucket_end = bucket_start + bucket_size

            bucket_requests = [
                r for r in requests
                if bucket_start <= r.timestamp < bucket_end
            ]

            count = len(bucket_requests)
            latencies = [r.latency_ms for r in bucket_requests]
            errors = sum(1 for r in bucket_requests if r.status_code >= 400)

            history.append({
                "timestamp": bucket_start,
                "requests": count,
                "requests_per_sec": round(count / bucket_size, 2) if bucket_size > 0 else 0,
                "avg_latency_ms": round(sum(latencies) / count, 2) if latencies else 0,
                "errors": errors,
            })

        return history

    @classmethod
    def get_snapshot(cls) -> Dict[str, Any]:
        """Get a complete snapshot of API metrics."""
        return {
            "ok": True,
            "timestamp": time.time(),
            "stats": cls.get_stats("5min"),
            "recent_errors": cls.get_recent_errors(10),
            "history": cls.get_throughput_history("5min", 60),
        }


def create_metrics_middleware(app):
    """Create Flask middleware for API metrics collection."""

    @app.before_request
    def before_request():
        from flask import g, request as flask_request
        g.request_start_time = time.time()

    @app.after_request
    def after_request(response):
        from flask import g, request as flask_request

        start_time = getattr(g, 'request_start_time', None)
        if start_time is None:
            return response

        latency_ms = (time.time() - start_time) * 1000

        # Determine error message if applicable
        error = None
        if response.status_code >= 400:
            try:
                data = response.get_json(silent=True)
                if data and isinstance(data, dict):
                    error = data.get('error') or data.get('message')
            except Exception:
                pass

        ApiMetricsService.record_request(
            method=flask_request.method,
            path=flask_request.path,
            status_code=response.status_code,
            latency_ms=latency_ms,
            error=error,
        )

        return response

    return app
