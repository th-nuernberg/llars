"""
Tests for DockerMonitorService - Docker container monitoring.

Covers:
- Docker API connection (ping)
- Container listing with project scope filtering
- Health status inference
- CPU percentage calculation
- Memory usage calculation
- Network I/O extraction
- Complete snapshot generation
- Log streaming
- Error handling when Docker unavailable
"""

from unittest.mock import MagicMock, patch

import pytest


class TestDockerApiConnection:
    """Test Docker API connection."""

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_001_ping_returns_true_when_connected(self, mock_get_api):
        """DOCKER_001: ping() returns True when Docker is reachable."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        assert DockerMonitorService.ping() is True
        mock_api.ping.assert_called_once()

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_002_ping_returns_false_on_error(self, mock_get_api):
        """DOCKER_002: ping() returns False when Docker unavailable."""
        from services.docker_monitor_service import DockerMonitorService

        mock_get_api.side_effect = Exception("Docker not running")

        assert DockerMonitorService.ping() is False

    def test_DOCKER_003_get_api_creates_client(self):
        """DOCKER_003: _get_api creates Docker client from environment."""
        from services.docker_monitor_service import DockerMonitorService

        DockerMonitorService._api = None  # Reset
        mock_client = MagicMock()

        # docker is imported inside _get_api, so patch at import point
        with patch.dict('sys.modules', {'docker': MagicMock(from_env=MagicMock(return_value=mock_client))}):
            import importlib
            # Force re-import to pick up patched docker
            api = DockerMonitorService._get_api()

        assert api is mock_client.api
        DockerMonitorService._api = None  # Cleanup

    def test_DOCKER_004_get_api_returns_cached(self):
        """DOCKER_004: _get_api returns cached client on second call."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        DockerMonitorService._api = mock_api

        result = DockerMonitorService._get_api()
        assert result is mock_api

        DockerMonitorService._api = None  # Cleanup


class TestListContainers:
    """Test container listing."""

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_010_list_all_returns_everything(self, mock_get_api):
        """DOCKER_010: scope='all' returns all containers."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_api.containers.return_value = [
            {'Names': ['/llars_flask'], 'State': 'running'},
            {'Names': ['/other_service'], 'State': 'running'},
        ]
        mock_get_api.return_value = mock_api

        result = DockerMonitorService.list_containers(scope="all")
        assert len(result) == 2

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_011_list_project_filters_by_prefix(self, mock_get_api):
        """DOCKER_011: scope='project' filters by LLARS prefix."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_api.containers.return_value = [
            {'Names': ['/llars_flask_service'], 'State': 'running'},
            {'Names': ['/llars_db_service'], 'State': 'running'},
            {'Names': ['/other_service'], 'State': 'running'},
        ]
        mock_get_api.return_value = mock_api

        result = DockerMonitorService.list_containers(scope="project")
        assert len(result) == 2


class TestInferHealth:
    """Test health status inference."""

    def test_DOCKER_020_infer_healthy(self):
        """DOCKER_020: Infers 'healthy' from status text."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._infer_health("Up 2 hours (healthy)") == "healthy"

    def test_DOCKER_021_infer_unhealthy(self):
        """DOCKER_021: Infers 'unhealthy' from status text."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._infer_health("Up 1 hour (unhealthy)") == "unhealthy"

    def test_DOCKER_022_infer_starting(self):
        """DOCKER_022: Infers 'starting' from status text."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._infer_health("Up 5 seconds (health: starting)") == "starting"

    def test_DOCKER_023_infer_none_for_no_health(self):
        """DOCKER_023: Returns None when no health info in status."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._infer_health("Up 2 hours") is None

    def test_DOCKER_024_infer_none_for_empty_status(self):
        """DOCKER_024: Returns None for empty status string."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._infer_health("") is None


class TestCpuPercent:
    """Test CPU percentage calculation."""

    def test_DOCKER_030_cpu_percent_basic_calculation(self):
        """DOCKER_030: Calculates CPU percentage from Docker stats."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'cpu_stats': {
                'cpu_usage': {'total_usage': 200_000_000},
                'system_cpu_usage': 1_000_000_000,
                'online_cpus': 4,
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 100_000_000},
                'system_cpu_usage': 500_000_000,
            },
        }

        result = DockerMonitorService._cpu_percent(stats)

        # cpu_delta = 100M, system_delta = 500M
        # (100M / 500M) * 4 * 100 = 80.0
        assert result == pytest.approx(80.0, abs=0.1)

    def test_DOCKER_031_cpu_percent_zero_delta(self):
        """DOCKER_031: Returns 0 when no CPU delta."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'cpu_stats': {
                'cpu_usage': {'total_usage': 100},
                'system_cpu_usage': 100,
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 100},
                'system_cpu_usage': 100,
            },
        }

        assert DockerMonitorService._cpu_percent(stats) == 0.0

    def test_DOCKER_032_cpu_percent_empty_stats(self):
        """DOCKER_032: Returns 0 for empty stats."""
        from services.docker_monitor_service import DockerMonitorService

        assert DockerMonitorService._cpu_percent({}) == 0.0

    def test_DOCKER_033_cpu_percent_uses_percpu_fallback(self):
        """DOCKER_033: Falls back to percpu_usage count when online_cpus missing."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'cpu_stats': {
                'cpu_usage': {
                    'total_usage': 200_000_000,
                    'percpu_usage': [50_000_000, 50_000_000, 50_000_000, 50_000_000],
                },
                'system_cpu_usage': 1_000_000_000,
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 100_000_000},
                'system_cpu_usage': 500_000_000,
            },
        }

        result = DockerMonitorService._cpu_percent(stats)
        assert result > 0


class TestMemory:
    """Test memory usage calculation."""

    def test_DOCKER_040_memory_basic_calculation(self):
        """DOCKER_040: Calculates memory usage subtracting cache."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'memory_stats': {
                'usage': 500_000_000,
                'limit': 2_000_000_000,
                'stats': {'cache': 100_000_000},
            },
        }

        usage, limit, percent = DockerMonitorService._memory(stats)

        assert usage == 400_000_000  # 500M - 100M cache
        assert limit == 2_000_000_000
        assert percent == pytest.approx(20.0, abs=0.1)

    def test_DOCKER_041_memory_empty_stats(self):
        """DOCKER_041: Returns zeros for empty stats."""
        from services.docker_monitor_service import DockerMonitorService

        usage, limit, percent = DockerMonitorService._memory({})

        assert usage == 0
        assert limit == 0
        assert percent == 0.0

    def test_DOCKER_042_memory_no_cache(self):
        """DOCKER_042: Works without cache field."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'memory_stats': {
                'usage': 500_000_000,
                'limit': 2_000_000_000,
                'stats': {},
            },
        }

        usage, limit, percent = DockerMonitorService._memory(stats)
        assert usage == 500_000_000


class TestNetwork:
    """Test network I/O extraction."""

    def test_DOCKER_050_network_aggregates_interfaces(self):
        """DOCKER_050: Aggregates rx/tx bytes across interfaces."""
        from services.docker_monitor_service import DockerMonitorService

        stats = {
            'networks': {
                'eth0': {'rx_bytes': 1000, 'tx_bytes': 500},
                'eth1': {'rx_bytes': 2000, 'tx_bytes': 1000},
            },
        }

        result = DockerMonitorService._network(stats)

        assert result['rx_bytes'] == 3000
        assert result['tx_bytes'] == 1500

    def test_DOCKER_051_network_empty_stats(self):
        """DOCKER_051: Returns zeros for empty network stats."""
        from services.docker_monitor_service import DockerMonitorService

        result = DockerMonitorService._network({})
        assert result == {'rx_bytes': 0, 'tx_bytes': 0}


class TestGetSnapshot:
    """Test complete snapshot generation."""

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    @patch('services.docker_monitor_service.DockerMonitorService.list_containers')
    def test_DOCKER_060_snapshot_running_container(self, mock_list, mock_get_api):
        """DOCKER_060: Snapshot includes stats for running containers."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        mock_list.return_value = [
            {
                'Id': 'abc123def456',
                'Names': ['/llars_flask_service'],
                'Image': 'llars:latest',
                'State': 'running',
                'Status': 'Up 2 hours (healthy)',
            },
        ]

        mock_api.stats.return_value = {
            'cpu_stats': {
                'cpu_usage': {'total_usage': 200_000_000},
                'system_cpu_usage': 1_000_000_000,
                'online_cpus': 4,
            },
            'precpu_stats': {
                'cpu_usage': {'total_usage': 100_000_000},
                'system_cpu_usage': 500_000_000,
            },
            'memory_stats': {
                'usage': 380_000_000,
                'limit': 2_000_000_000,
                'stats': {'cache': 0},
            },
            'networks': {
                'eth0': {'rx_bytes': 1000, 'tx_bytes': 500},
            },
        }

        result = DockerMonitorService.get_snapshot(scope="project")

        assert result['ok'] is True
        assert len(result['containers']) == 1
        container = result['containers'][0]
        assert container['name'] == 'llars_flask_service'
        assert container['health'] == 'healthy'
        assert container['cpu_percent'] > 0
        assert result['summary']['running'] == 1
        assert result['summary']['healthy'] == 1

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    @patch('services.docker_monitor_service.DockerMonitorService.list_containers')
    def test_DOCKER_061_snapshot_exited_container(self, mock_list, mock_get_api):
        """DOCKER_061: Exited containers have zero stats."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        mock_list.return_value = [
            {
                'Id': 'abc123',
                'Names': ['/llars_stopped'],
                'Image': 'llars:latest',
                'State': 'exited',
                'Status': 'Exited (0) 1 hour ago',
            },
        ]

        result = DockerMonitorService.get_snapshot()

        container = result['containers'][0]
        assert container['cpu_percent'] == 0.0
        assert container['mem_usage'] == 0
        assert result['summary']['exited'] == 1

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_062_snapshot_handles_error(self, mock_get_api):
        """DOCKER_062: Snapshot returns error structure on exception."""
        from services.docker_monitor_service import DockerMonitorService

        mock_get_api.side_effect = RuntimeError("Docker down")

        result = DockerMonitorService.get_snapshot()

        assert result['ok'] is False
        assert 'Docker down' in result['error']
        assert result['summary']['total'] == 0


class TestStreamLogs:
    """Test log streaming."""

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_070_stream_logs_calls_api(self, mock_get_api):
        """DOCKER_070: stream_logs calls Docker API with correct params."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_api.logs.return_value = iter([b"log line 1\n", b"log line 2\n"])
        mock_get_api.return_value = mock_api

        result = DockerMonitorService.stream_logs(
            container_id='abc123',
            tail=100,
            timestamps=True,
        )

        mock_api.logs.assert_called_once_with(
            container='abc123',
            stream=True,
            follow=True,
            tail=100,
            timestamps=True,
        )

    @patch('services.docker_monitor_service.DockerMonitorService._get_api')
    def test_DOCKER_071_stream_logs_clamps_negative_tail(self, mock_get_api):
        """DOCKER_071: Negative tail is clamped to 0."""
        from services.docker_monitor_service import DockerMonitorService

        mock_api = MagicMock()
        mock_get_api.return_value = mock_api

        DockerMonitorService.stream_logs(container_id='abc', tail=-5)

        call_kwargs = mock_api.logs.call_args[1]
        assert call_kwargs['tail'] == 0
