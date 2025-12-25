"""Host system metrics service using psutil.

Provides CPU, memory, disk, and network statistics for the host machine.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class HostMetricsService:
    """Collect host system metrics via psutil."""

    _last_net_io: Optional[Dict[str, int]] = None
    _last_net_time: Optional[float] = None
    _last_disk_io: Optional[Dict[str, int]] = None
    _last_disk_time: Optional[float] = None

    @classmethod
    def is_available(cls) -> bool:
        """Check if psutil is available."""
        return PSUTIL_AVAILABLE

    @classmethod
    def get_cpu_metrics(cls) -> Dict[str, Any]:
        """Get CPU usage statistics."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            # Overall CPU percent (non-blocking with interval=None uses cached value)
            cpu_percent = psutil.cpu_percent(interval=None)

            # Per-CPU percentages
            per_cpu = psutil.cpu_percent(interval=None, percpu=True)

            # CPU times
            cpu_times = psutil.cpu_times_percent(interval=None)

            # CPU count
            cpu_count_logical = psutil.cpu_count(logical=True)
            cpu_count_physical = psutil.cpu_count(logical=False)

            # Load average (Unix only)
            try:
                load_avg = list(psutil.getloadavg())
            except (AttributeError, OSError):
                load_avg = [0.0, 0.0, 0.0]

            return {
                "percent": round(cpu_percent, 1),
                "per_cpu": [round(p, 1) for p in per_cpu],
                "count_logical": cpu_count_logical,
                "count_physical": cpu_count_physical or cpu_count_logical,
                "load_avg": {
                    "1min": round(load_avg[0], 2),
                    "5min": round(load_avg[1], 2),
                    "15min": round(load_avg[2], 2),
                },
                "times": {
                    "user": round(cpu_times.user, 1),
                    "system": round(cpu_times.system, 1),
                    "idle": round(cpu_times.idle, 1),
                    "iowait": round(getattr(cpu_times, 'iowait', 0), 1),
                },
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_memory_metrics(cls) -> Dict[str, Any]:
        """Get memory (RAM) and swap statistics."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "ram": {
                    "total": mem.total,
                    "available": mem.available,
                    "used": mem.used,
                    "percent": round(mem.percent, 1),
                    "cached": getattr(mem, 'cached', 0),
                    "buffers": getattr(mem, 'buffers', 0),
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": round(swap.percent, 1),
                },
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_disk_metrics(cls) -> Dict[str, Any]:
        """Get disk usage and I/O statistics."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            partitions: List[Dict[str, Any]] = []

            for part in psutil.disk_partitions(all=False):
                # Skip special filesystems
                if part.fstype in ('squashfs', 'tmpfs', 'devtmpfs', 'overlay'):
                    continue

                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round(usage.percent, 1),
                    })
                except (PermissionError, OSError):
                    continue

            # Disk I/O with rate calculation
            io_rate = {"read_bytes_sec": 0, "write_bytes_sec": 0}
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    current_time = time.time()
                    current_io = {
                        "read_bytes": disk_io.read_bytes,
                        "write_bytes": disk_io.write_bytes,
                    }

                    if cls._last_disk_io and cls._last_disk_time:
                        time_delta = current_time - cls._last_disk_time
                        if time_delta > 0:
                            io_rate["read_bytes_sec"] = int(
                                (current_io["read_bytes"] - cls._last_disk_io["read_bytes"]) / time_delta
                            )
                            io_rate["write_bytes_sec"] = int(
                                (current_io["write_bytes"] - cls._last_disk_io["write_bytes"]) / time_delta
                            )

                    cls._last_disk_io = current_io
                    cls._last_disk_time = current_time
            except Exception:
                pass

            return {
                "partitions": partitions,
                "io": io_rate,
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_network_metrics(cls) -> Dict[str, Any]:
        """Get network I/O statistics with rate calculation."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            net_io = psutil.net_io_counters()
            current_time = time.time()

            current = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
            }

            # Calculate rates
            rates = {
                "bytes_sent_sec": 0,
                "bytes_recv_sec": 0,
            }

            if cls._last_net_io and cls._last_net_time:
                time_delta = current_time - cls._last_net_time
                if time_delta > 0:
                    rates["bytes_sent_sec"] = int(
                        (current["bytes_sent"] - cls._last_net_io["bytes_sent"]) / time_delta
                    )
                    rates["bytes_recv_sec"] = int(
                        (current["bytes_recv"] - cls._last_net_io["bytes_recv"]) / time_delta
                    )

            cls._last_net_io = {
                "bytes_sent": current["bytes_sent"],
                "bytes_recv": current["bytes_recv"],
            }
            cls._last_net_time = current_time

            # Network interfaces
            interfaces: List[Dict[str, Any]] = []
            try:
                net_if_addrs = psutil.net_if_addrs()
                net_if_stats = psutil.net_if_stats()

                for iface_name, stats in net_if_stats.items():
                    if not stats.isup:
                        continue
                    # Skip loopback and virtual interfaces
                    if iface_name.startswith(('lo', 'docker', 'br-', 'veth')):
                        continue

                    addrs = net_if_addrs.get(iface_name, [])
                    ipv4 = next((a.address for a in addrs if a.family.name == 'AF_INET'), None)

                    interfaces.append({
                        "name": iface_name,
                        "ip": ipv4,
                        "speed": stats.speed,  # Mbps
                        "mtu": stats.mtu,
                    })
            except Exception:
                pass

            return {
                "totals": current,
                "rates": rates,
                "interfaces": interfaces,
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_system_info(cls) -> Dict[str, Any]:
        """Get general system information."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil not available"}

        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time

            # Convert uptime to days, hours, minutes
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)

            return {
                "boot_time": boot_time,
                "uptime_seconds": int(uptime_seconds),
                "uptime_formatted": f"{days}d {hours}h {minutes}m",
                "platform": {
                    "system": __import__('platform').system(),
                    "release": __import__('platform').release(),
                    "machine": __import__('platform').machine(),
                },
            }
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def get_snapshot(cls) -> Dict[str, Any]:
        """Get a complete snapshot of all host metrics."""
        if not PSUTIL_AVAILABLE:
            return {
                "ok": False,
                "error": "psutil not available",
                "cpu": {},
                "memory": {},
                "disk": {},
                "network": {},
                "system": {},
            }

        try:
            return {
                "ok": True,
                "timestamp": time.time(),
                "cpu": cls.get_cpu_metrics(),
                "memory": cls.get_memory_metrics(),
                "disk": cls.get_disk_metrics(),
                "network": cls.get_network_metrics(),
                "system": cls.get_system_info(),
            }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "cpu": {},
                "memory": {},
                "disk": {},
                "network": {},
                "system": {},
            }


# Initialize CPU percent calculation (first call is always 0)
if PSUTIL_AVAILABLE:
    try:
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(interval=None, percpu=True)
        psutil.cpu_times_percent(interval=None)
    except Exception:
        pass
