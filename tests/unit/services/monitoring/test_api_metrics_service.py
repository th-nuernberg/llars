"""
Tests for ApiMetricsService - API performance metrics collection.

Covers:
- Path normalization and exclusion
- Request recording
- Stats aggregation by time window
- Percentile calculations
- Error tracking
- Throughput history
- Snapshot generation
- Middleware creation
"""

import time
from collections import deque
from unittest.mock import MagicMock, patch

import pytest

from services.api_metrics_service import (
    ApiMetricsService,
    RequestMetric,
    EndpointStats,
    create_metrics_middleware,
)


class TestPathNormalization:
    """Test path normalization logic."""

    def test_API_METRICS_001_normalizes_numeric_ids(self):
        """API_METRICS_001: Replaces numeric path segments with <id>."""
        result = ApiMetricsService._normalize_path('/api/scenarios/123/items/456')
        assert result == '/api/scenarios/<id>/items/<id>'

    def test_API_METRICS_002_normalizes_uuids(self):
        """API_METRICS_002: Replaces UUID segments with <uuid>."""
        result = ApiMetricsService._normalize_path(
            '/api/items/a1b2c3d4-e5f6-7890-abcd-ef1234567890'
        )
        assert '<uuid>' in result

    def test_API_METRICS_003_strips_query_string(self):
        """API_METRICS_003: Removes query string before normalization."""
        result = ApiMetricsService._normalize_path('/api/items?page=1&limit=20')
        assert '?' not in result
        assert result == '/api/items'

    def test_API_METRICS_004_preserves_static_paths(self):
        """API_METRICS_004: Static paths are not modified."""
        result = ApiMetricsService._normalize_path('/api/health')
        assert result == '/api/health'


class TestShouldTrack:
    """Test path exclusion logic."""

    def test_API_METRICS_010_excludes_health_endpoint(self):
        """API_METRICS_010: /api/health is excluded."""
        assert ApiMetricsService._should_track('/api/health') is False

    def test_API_METRICS_011_excludes_socket_io(self):
        """API_METRICS_011: /socket.io/ is excluded."""
        assert ApiMetricsService._should_track('/socket.io/poll') is False

    def test_API_METRICS_012_excludes_analytics(self):
        """API_METRICS_012: /analytics/ paths are excluded."""
        assert ApiMetricsService._should_track('/analytics/track') is False

    def test_API_METRICS_013_excludes_event_stream(self):
        """API_METRICS_013: Event stream endpoint is excluded."""
        assert ApiMetricsService._should_track('/api/admin/system/events/stream') is False

    def test_API_METRICS_014_tracks_normal_api_paths(self):
        """API_METRICS_014: Normal API paths are tracked."""
        assert ApiMetricsService._should_track('/api/scenarios') is True
        assert ApiMetricsService._should_track('/api/users/me') is True


class TestRecordRequest:
    """Test request recording."""

    def setup_method(self):
        """Clear metrics between tests."""
        ApiMetricsService._requests.clear()
        ApiMetricsService._recent_errors.clear()

    def test_API_METRICS_020_records_request_metric(self):
        """API_METRICS_020: Records valid request metric."""
        ApiMetricsService.record_request(
            method='GET', path='/api/scenarios',
            status_code=200, latency_ms=15.5
        )

        assert len(ApiMetricsService._requests) == 1
        metric = ApiMetricsService._requests[0]
        assert metric.method == 'GET'
        assert metric.status_code == 200
        assert metric.latency_ms == 15.5

    def test_API_METRICS_021_skips_excluded_paths(self):
        """API_METRICS_021: Does not record excluded paths."""
        ApiMetricsService.record_request(
            method='GET', path='/api/health',
            status_code=200, latency_ms=1.0
        )

        assert len(ApiMetricsService._requests) == 0

    def test_API_METRICS_022_tracks_errors_separately(self):
        """API_METRICS_022: Status >= 400 recorded in both deques."""
        ApiMetricsService.record_request(
            method='POST', path='/api/items',
            status_code=500, latency_ms=200.0,
            error='Internal error'
        )

        assert len(ApiMetricsService._requests) == 1
        assert len(ApiMetricsService._recent_errors) == 1
        assert ApiMetricsService._recent_errors[0].error == 'Internal error'

    def test_API_METRICS_023_uppercases_method(self):
        """API_METRICS_023: Method is uppercased."""
        ApiMetricsService.record_request(
            method='post', path='/api/items',
            status_code=201, latency_ms=5.0
        )

        assert ApiMetricsService._requests[0].method == 'POST'

    def test_API_METRICS_024_rounds_latency(self):
        """API_METRICS_024: Latency is rounded to 2 decimal places."""
        ApiMetricsService.record_request(
            method='GET', path='/api/items',
            status_code=200, latency_ms=15.5678
        )

        assert ApiMetricsService._requests[0].latency_ms == 15.57


class TestEndpointStats:
    """Test EndpointStats dataclass."""

    def test_API_METRICS_030_avg_latency_calculation(self):
        """API_METRICS_030: avg_latency_ms computed correctly."""
        stats = EndpointStats(method='GET', path='/api/test')
        stats.count = 3
        stats.total_latency_ms = 30.0

        assert stats.avg_latency_ms == 10.0

    def test_API_METRICS_031_avg_latency_zero_count(self):
        """API_METRICS_031: avg_latency_ms returns 0 for zero count."""
        stats = EndpointStats(method='GET', path='/api/test')
        assert stats.avg_latency_ms == 0.0

    def test_API_METRICS_032_error_rate_calculation(self):
        """API_METRICS_032: error_rate computed as percentage."""
        stats = EndpointStats(method='GET', path='/api/test')
        stats.count = 10
        stats.error_count = 2

        assert stats.error_rate == 20.0

    def test_API_METRICS_033_percentile_calculation(self):
        """API_METRICS_033: Percentile computes correctly."""
        stats = EndpointStats(method='GET', path='/api/test')
        stats.latencies = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        p50 = stats.percentile(50)
        assert 5.0 <= p50 <= 6.0

        p95 = stats.percentile(95)
        assert p95 >= 9.0

    def test_API_METRICS_034_percentile_empty_latencies(self):
        """API_METRICS_034: Percentile returns 0 for empty latencies."""
        stats = EndpointStats(method='GET', path='/api/test')
        assert stats.percentile(95) == 0.0


class TestGetStats:
    """Test stats aggregation."""

    def setup_method(self):
        """Clear metrics between tests."""
        ApiMetricsService._requests.clear()
        ApiMetricsService._recent_errors.clear()

    def test_API_METRICS_040_empty_stats(self):
        """API_METRICS_040: Returns zeros when no requests recorded."""
        stats = ApiMetricsService.get_stats("5min")

        assert stats['request_count'] == 0
        assert stats['avg_latency_ms'] == 0.0
        assert stats['error_count'] == 0
        assert stats['endpoints'] == []

    def test_API_METRICS_041_stats_with_requests(self):
        """API_METRICS_041: Computes correct stats for recorded requests."""
        now = time.time()
        ApiMetricsService._requests.extend([
            RequestMetric(timestamp=now - 10, method='GET', path='/api/a', status_code=200, latency_ms=10.0),
            RequestMetric(timestamp=now - 5, method='GET', path='/api/a', status_code=200, latency_ms=20.0),
            RequestMetric(timestamp=now - 1, method='POST', path='/api/b', status_code=500, latency_ms=100.0, error='fail'),
        ])

        stats = ApiMetricsService.get_stats("5min")

        assert stats['request_count'] == 3
        assert stats['avg_latency_ms'] == pytest.approx(43.33, abs=0.1)
        assert stats['min_latency_ms'] == 10.0
        assert stats['max_latency_ms'] == 100.0
        assert stats['error_count'] == 1
        assert '5xx' in stats['status_codes'] or '2xx' in stats['status_codes']

    def test_API_METRICS_042_stats_respects_window(self):
        """API_METRICS_042: Only includes requests within time window."""
        now = time.time()
        ApiMetricsService._requests.extend([
            RequestMetric(timestamp=now - 3700, method='GET', path='/api/old', status_code=200, latency_ms=5.0),
            RequestMetric(timestamp=now - 10, method='GET', path='/api/new', status_code=200, latency_ms=15.0),
        ])

        stats = ApiMetricsService.get_stats("1hour")
        assert stats['request_count'] == 1

    def test_API_METRICS_043_stats_endpoints_sorted_by_latency(self):
        """API_METRICS_043: Endpoints are sorted by avg latency (desc)."""
        now = time.time()
        ApiMetricsService._requests.extend([
            RequestMetric(timestamp=now, method='GET', path='/api/fast', status_code=200, latency_ms=5.0),
            RequestMetric(timestamp=now, method='GET', path='/api/slow', status_code=200, latency_ms=500.0),
        ])

        stats = ApiMetricsService.get_stats("5min")
        if len(stats['endpoints']) >= 2:
            assert stats['endpoints'][0]['avg_latency_ms'] >= stats['endpoints'][1]['avg_latency_ms']


class TestGetRecentErrors:
    """Test recent error retrieval."""

    def setup_method(self):
        ApiMetricsService._recent_errors.clear()

    def test_API_METRICS_050_returns_recent_errors(self):
        """API_METRICS_050: Returns recent errors with age calculation."""
        now = time.time()
        ApiMetricsService._recent_errors.append(
            RequestMetric(timestamp=now - 30, method='POST', path='/api/fail',
                         status_code=500, latency_ms=200.0, error='Server error')
        )

        errors = ApiMetricsService.get_recent_errors(limit=5)

        assert len(errors) == 1
        assert errors[0]['status_code'] == 500
        assert errors[0]['error'] == 'Server error'
        assert errors[0]['age_seconds'] >= 29.0

    def test_API_METRICS_051_respects_limit(self):
        """API_METRICS_051: Limits number of returned errors."""
        now = time.time()
        for i in range(10):
            ApiMetricsService._recent_errors.append(
                RequestMetric(timestamp=now - i, method='GET', path=f'/api/{i}',
                             status_code=500, latency_ms=100.0)
            )

        errors = ApiMetricsService.get_recent_errors(limit=3)
        assert len(errors) == 3


class TestGetThroughputHistory:
    """Test throughput history generation."""

    def setup_method(self):
        ApiMetricsService._requests.clear()

    def test_API_METRICS_060_empty_history(self):
        """API_METRICS_060: Returns empty list when no requests."""
        history = ApiMetricsService.get_throughput_history("5min", buckets=10)
        assert history == []

    def test_API_METRICS_061_generates_buckets(self):
        """API_METRICS_061: Generates correct number of time buckets."""
        now = time.time()
        ApiMetricsService._requests.append(
            RequestMetric(timestamp=now - 1, method='GET', path='/api/test',
                         status_code=200, latency_ms=10.0)
        )

        history = ApiMetricsService.get_throughput_history("5min", buckets=10)

        assert len(history) == 10
        total_requests = sum(h['requests'] for h in history)
        assert total_requests == 1


class TestGetSnapshot:
    """Test complete snapshot."""

    def setup_method(self):
        ApiMetricsService._requests.clear()
        ApiMetricsService._recent_errors.clear()

    def test_API_METRICS_070_snapshot_contains_all_sections(self):
        """API_METRICS_070: Snapshot includes stats, errors, and history."""
        snapshot = ApiMetricsService.get_snapshot()

        assert snapshot['ok'] is True
        assert 'timestamp' in snapshot
        assert 'stats' in snapshot
        assert 'recent_errors' in snapshot
        assert 'history' in snapshot


class TestMetricsMiddleware:
    """Test Flask middleware creation."""

    def test_API_METRICS_080_middleware_registers_hooks(self):
        """API_METRICS_080: Middleware registers before/after request hooks."""
        mock_app = MagicMock()

        create_metrics_middleware(mock_app)

        mock_app.before_request.assert_called_once()
        mock_app.after_request.assert_called_once()
