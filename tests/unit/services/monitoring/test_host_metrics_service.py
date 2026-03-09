"""
Tests for HostMetricsService - host system metrics via psutil.

Covers:
- is_available check
- CPU metrics collection
- Memory metrics collection
- Disk metrics with I/O rate calculation
- Network metrics with rate calculation
- System info (uptime, platform)
- Complete snapshot
- Graceful handling when psutil is unavailable
"""

import time
from unittest.mock import MagicMock, patch, PropertyMock

import pytest


class TestIsAvailable:
    """Test psutil availability check."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    def test_HOST_001_available_when_psutil_present(self):
        """HOST_001: Returns True when psutil is installed."""
        from services.host_metrics_service import HostMetricsService
        assert HostMetricsService.is_available() is True

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_002_unavailable_when_psutil_missing(self):
        """HOST_002: Returns False when psutil is not installed."""
        from services.host_metrics_service import HostMetricsService
        assert HostMetricsService.is_available() is False


class TestGetCpuMetrics:
    """Test CPU metrics collection."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_010_cpu_returns_error_without_psutil(self):
        """HOST_010: Returns error dict when psutil unavailable."""
        from services.host_metrics_service import HostMetricsService
        result = HostMetricsService.get_cpu_metrics()
        assert result == {"error": "psutil not available"}

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_011_cpu_returns_valid_metrics(self, mock_psutil):
        """HOST_011: Returns CPU metrics with correct structure."""
        from services.host_metrics_service import HostMetricsService

        # cpu_percent is called with different kwargs: interval=None and percpu=True
        def cpu_percent_side_effect(interval=None, percpu=False):
            if percpu:
                return [40.0, 50.0, 45.0, 46.0]
            return 45.2

        mock_psutil.cpu_percent.side_effect = cpu_percent_side_effect
        mock_psutil.cpu_count.side_effect = [8, 4]  # logical, physical
        mock_psutil.getloadavg.return_value = (1.5, 2.0, 1.8)

        mock_times = MagicMock()
        mock_times.user = 30.0
        mock_times.system = 10.0
        mock_times.idle = 60.0
        mock_times.iowait = 0.5
        mock_psutil.cpu_times_percent.return_value = mock_times

        result = HostMetricsService.get_cpu_metrics()

        assert result['percent'] == 45.2
        assert result['count_logical'] == 8
        assert result['count_physical'] == 4
        assert result['load_avg']['1min'] == 1.5
        assert result['times']['user'] == 30.0

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_012_cpu_handles_exception(self, mock_psutil):
        """HOST_012: Returns error dict on exception."""
        from services.host_metrics_service import HostMetricsService

        mock_psutil.cpu_percent.side_effect = RuntimeError("CPU error")

        result = HostMetricsService.get_cpu_metrics()
        assert 'error' in result


class TestGetMemoryMetrics:
    """Test memory metrics collection."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_020_memory_returns_error_without_psutil(self):
        """HOST_020: Returns error when psutil unavailable."""
        from services.host_metrics_service import HostMetricsService
        result = HostMetricsService.get_memory_metrics()
        assert result == {"error": "psutil not available"}

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_021_memory_returns_ram_and_swap(self, mock_psutil):
        """HOST_021: Returns both RAM and swap metrics."""
        from services.host_metrics_service import HostMetricsService

        mock_mem = MagicMock()
        mock_mem.total = 16_000_000_000
        mock_mem.available = 8_000_000_000
        mock_mem.used = 8_000_000_000
        mock_mem.percent = 50.0
        mock_mem.cached = 2_000_000_000
        mock_mem.buffers = 500_000_000
        mock_psutil.virtual_memory.return_value = mock_mem

        mock_swap = MagicMock()
        mock_swap.total = 4_000_000_000
        mock_swap.used = 1_000_000_000
        mock_swap.free = 3_000_000_000
        mock_swap.percent = 25.0
        mock_psutil.swap_memory.return_value = mock_swap

        result = HostMetricsService.get_memory_metrics()

        assert result['ram']['total'] == 16_000_000_000
        assert result['ram']['percent'] == 50.0
        assert result['swap']['total'] == 4_000_000_000
        assert result['swap']['percent'] == 25.0


class TestGetDiskMetrics:
    """Test disk metrics collection."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_030_disk_returns_error_without_psutil(self):
        """HOST_030: Returns error when psutil unavailable."""
        from services.host_metrics_service import HostMetricsService
        result = HostMetricsService.get_disk_metrics()
        assert result == {"error": "psutil not available"}

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_031_disk_returns_partitions(self, mock_psutil):
        """HOST_031: Returns partition info with usage."""
        from services.host_metrics_service import HostMetricsService
        # Reset class state
        HostMetricsService._last_disk_io = None
        HostMetricsService._last_disk_time = None

        mock_part = MagicMock()
        mock_part.device = '/dev/sda1'
        mock_part.mountpoint = '/'
        mock_part.fstype = 'ext4'
        mock_psutil.disk_partitions.return_value = [mock_part]

        mock_usage = MagicMock()
        mock_usage.total = 100_000_000_000
        mock_usage.used = 60_000_000_000
        mock_usage.free = 40_000_000_000
        mock_usage.percent = 60.0
        mock_psutil.disk_usage.return_value = mock_usage

        mock_io = MagicMock()
        mock_io.read_bytes = 1_000_000
        mock_io.write_bytes = 500_000
        mock_psutil.disk_io_counters.return_value = mock_io

        result = HostMetricsService.get_disk_metrics()

        assert len(result['partitions']) == 1
        assert result['partitions'][0]['device'] == '/dev/sda1'
        assert result['partitions'][0]['percent'] == 60.0
        assert 'io' in result

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_032_disk_skips_special_filesystems(self, mock_psutil):
        """HOST_032: Skips tmpfs, squashfs, etc."""
        from services.host_metrics_service import HostMetricsService
        HostMetricsService._last_disk_io = None
        HostMetricsService._last_disk_time = None

        mock_part = MagicMock()
        mock_part.device = 'tmpfs'
        mock_part.mountpoint = '/tmp'
        mock_part.fstype = 'tmpfs'
        mock_psutil.disk_partitions.return_value = [mock_part]
        mock_psutil.disk_io_counters.return_value = None

        result = HostMetricsService.get_disk_metrics()
        assert result['partitions'] == []


class TestGetNetworkMetrics:
    """Test network metrics collection."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_040_network_returns_error_without_psutil(self):
        """HOST_040: Returns error when psutil unavailable."""
        from services.host_metrics_service import HostMetricsService
        result = HostMetricsService.get_network_metrics()
        assert result == {"error": "psutil not available"}

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_041_network_returns_totals_and_rates(self, mock_psutil):
        """HOST_041: Returns network totals with rate calculation."""
        from services.host_metrics_service import HostMetricsService
        # Reset state
        HostMetricsService._last_net_io = None
        HostMetricsService._last_net_time = None

        mock_io = MagicMock()
        mock_io.bytes_sent = 1_000_000
        mock_io.bytes_recv = 2_000_000
        mock_io.packets_sent = 100
        mock_io.packets_recv = 200
        mock_io.errin = 0
        mock_io.errout = 0
        mock_io.dropin = 0
        mock_io.dropout = 0
        mock_psutil.net_io_counters.return_value = mock_io

        mock_psutil.net_if_addrs.return_value = {}
        mock_psutil.net_if_stats.return_value = {}

        result = HostMetricsService.get_network_metrics()

        assert result['totals']['bytes_sent'] == 1_000_000
        assert result['totals']['bytes_recv'] == 2_000_000
        assert 'rates' in result

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_042_network_calculates_rates_on_second_call(self, mock_psutil):
        """HOST_042: Calculates byte rates after first call."""
        from services.host_metrics_service import HostMetricsService

        # Set up previous state
        HostMetricsService._last_net_io = {
            'bytes_sent': 900_000,
            'bytes_recv': 1_800_000,
        }
        HostMetricsService._last_net_time = time.time() - 10  # 10 seconds ago

        mock_io = MagicMock()
        mock_io.bytes_sent = 1_000_000
        mock_io.bytes_recv = 2_000_000
        mock_io.packets_sent = 100
        mock_io.packets_recv = 200
        mock_io.errin = 0
        mock_io.errout = 0
        mock_io.dropin = 0
        mock_io.dropout = 0
        mock_psutil.net_io_counters.return_value = mock_io
        mock_psutil.net_if_addrs.return_value = {}
        mock_psutil.net_if_stats.return_value = {}

        result = HostMetricsService.get_network_metrics()

        # 100_000 bytes / 10 seconds = ~10_000 bytes/sec
        assert result['rates']['bytes_sent_sec'] > 0
        assert result['rates']['bytes_recv_sec'] > 0


class TestGetSystemInfo:
    """Test system info retrieval."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_050_system_returns_error_without_psutil(self):
        """HOST_050: Returns error when psutil unavailable."""
        from services.host_metrics_service import HostMetricsService
        result = HostMetricsService.get_system_info()
        assert result == {"error": "psutil not available"}

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    @patch('services.host_metrics_service.psutil')
    def test_HOST_051_system_returns_uptime_info(self, mock_psutil):
        """HOST_051: Returns boot time and formatted uptime."""
        from services.host_metrics_service import HostMetricsService

        mock_psutil.boot_time.return_value = time.time() - 86400  # 1 day ago

        result = HostMetricsService.get_system_info()

        assert 'boot_time' in result
        assert 'uptime_seconds' in result
        assert 'uptime_formatted' in result
        assert result['uptime_seconds'] >= 86399  # ~1 day
        assert '1d' in result['uptime_formatted']
        assert 'platform' in result


class TestGetSnapshot:
    """Test complete snapshot."""

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', False)
    def test_HOST_060_snapshot_without_psutil(self):
        """HOST_060: Snapshot returns error structure without psutil."""
        from services.host_metrics_service import HostMetricsService

        result = HostMetricsService.get_snapshot()

        assert result['ok'] is False
        assert result['error'] == 'psutil not available'

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    def test_HOST_061_snapshot_with_psutil(self):
        """HOST_061: Snapshot returns all metric sections."""
        from services.host_metrics_service import HostMetricsService

        with patch.object(HostMetricsService, 'get_cpu_metrics', return_value={'percent': 10}):
            with patch.object(HostMetricsService, 'get_memory_metrics', return_value={'ram': {}}):
                with patch.object(HostMetricsService, 'get_disk_metrics', return_value={'partitions': []}):
                    with patch.object(HostMetricsService, 'get_network_metrics', return_value={'totals': {}}):
                        with patch.object(HostMetricsService, 'get_system_info', return_value={'uptime_seconds': 1000}):
                            result = HostMetricsService.get_snapshot()

        assert result['ok'] is True
        assert 'cpu' in result
        assert 'memory' in result
        assert 'disk' in result
        assert 'network' in result
        assert 'system' in result

    @patch('services.host_metrics_service.PSUTIL_AVAILABLE', True)
    def test_HOST_062_snapshot_handles_exception(self):
        """HOST_062: Snapshot returns error on unexpected exception."""
        from services.host_metrics_service import HostMetricsService

        with patch.object(HostMetricsService, 'get_cpu_metrics', side_effect=RuntimeError("boom")):
            result = HostMetricsService.get_snapshot()

        assert result['ok'] is False
        assert 'boom' in result['error']
