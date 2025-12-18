"""Docker monitoring helpers (containers, stats, logs)."""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional, Tuple


class DockerMonitorService:
    """Access Docker engine data via the Docker API."""

    PROJECT_PREFIX = os.getenv("LLARS_DOCKER_PROJECT_PREFIX", "llars_")

    _api = None

    @classmethod
    def _get_api(cls):
        if cls._api is not None:
            return cls._api

        import docker

        client = docker.from_env()
        cls._api = client.api
        return cls._api

    @classmethod
    def ping(cls) -> bool:
        try:
            api = cls._get_api()
            api.ping()
            return True
        except Exception:
            return False

    @classmethod
    def list_containers(cls, scope: str = "project") -> List[Dict[str, Any]]:
        api = cls._get_api()
        containers = api.containers(all=True)

        if scope == "all":
            return containers

        prefix = cls.PROJECT_PREFIX
        filtered = []
        for c in containers:
            names = c.get("Names") or []
            name = names[0].lstrip("/") if names else ""
            if name.startswith(prefix):
                filtered.append(c)
        return filtered

    @staticmethod
    def _infer_health(status_text: str) -> Optional[str]:
        if not status_text:
            return None
        s = status_text.lower()
        if "(healthy)" in s:
            return "healthy"
        if "(unhealthy)" in s:
            return "unhealthy"
        if "health: starting" in s:
            return "starting"
        return None

    @staticmethod
    def _cpu_percent(stats: Dict[str, Any]) -> float:
        try:
            cpu_total = stats["cpu_stats"]["cpu_usage"]["total_usage"]
            pre_cpu_total = stats.get("precpu_stats", {}).get("cpu_usage", {}).get("total_usage", 0)
            cpu_delta = cpu_total - pre_cpu_total

            system_total = stats["cpu_stats"]["system_cpu_usage"]
            pre_system_total = stats.get("precpu_stats", {}).get("system_cpu_usage", 0)
            system_delta = system_total - pre_system_total

            online_cpus = stats["cpu_stats"].get("online_cpus")
            if not online_cpus:
                percpu = stats["cpu_stats"]["cpu_usage"].get("percpu_usage") or []
                online_cpus = max(1, len(percpu))

            if system_delta > 0 and cpu_delta > 0:
                return float(cpu_delta) / float(system_delta) * float(online_cpus) * 100.0
        except Exception:
            return 0.0
        return 0.0

    @staticmethod
    def _memory(stats: Dict[str, Any]) -> Tuple[int, int, float]:
        try:
            mem_usage = int(stats.get("memory_stats", {}).get("usage") or 0)
            mem_limit = int(stats.get("memory_stats", {}).get("limit") or 0)
            mem_percent = 0.0
            if mem_limit > 0:
                mem_percent = float(mem_usage) / float(mem_limit) * 100.0
            return mem_usage, mem_limit, mem_percent
        except Exception:
            return 0, 0, 0.0

    @classmethod
    def get_snapshot(cls, scope: str = "project") -> Dict[str, Any]:
        """
        Return a snapshot of container state + computed CPU/memory stats.

        Shape:
            {
              "ok": bool,
              "scope": "project"|"all",
              "containers": [...],
              "summary": {...},
              "error": str|None,
            }
        """
        try:
            api = cls._get_api()
            raw = cls.list_containers(scope=scope)

            containers: List[Dict[str, Any]] = []
            for c in raw:
                container_id_full = str(c.get("Id") or "")
                container_id = container_id_full[:12]
                names = c.get("Names") or []
                name = names[0].lstrip("/") if names else container_id
                image = c.get("Image") or ""
                state = c.get("State") or ""
                status_text = c.get("Status") or ""
                health = cls._infer_health(status_text)

                cpu_percent = 0.0
                mem_usage = 0
                mem_limit = 0
                mem_percent = 0.0

                if state == "running":
                    try:
                        stats = api.stats(container=container_id_full, stream=False)
                        cpu_percent = cls._cpu_percent(stats)
                        mem_usage, mem_limit, mem_percent = cls._memory(stats)
                    except Exception:
                        cpu_percent = 0.0
                        mem_usage = 0
                        mem_limit = 0
                        mem_percent = 0.0

                containers.append(
                    {
                        "id": container_id,
                        "id_full": container_id_full,
                        "name": name,
                        "image": image,
                        "state": state,
                        "status": status_text,
                        "health": health,
                        "cpu_percent": round(float(cpu_percent), 2),
                        "mem_usage": int(mem_usage),
                        "mem_limit": int(mem_limit),
                        "mem_percent": round(float(mem_percent), 2),
                    }
                )

            total = len(containers)
            running = sum(1 for c in containers if c["state"] == "running")
            exited = sum(1 for c in containers if c["state"] == "exited")
            restarting = sum(1 for c in containers if c["state"] == "restarting")
            paused = sum(1 for c in containers if c["state"] == "paused")

            healthy = sum(1 for c in containers if c["health"] == "healthy")
            unhealthy = sum(1 for c in containers if c["health"] == "unhealthy")
            starting = sum(1 for c in containers if c["health"] == "starting")
            with_health = sum(1 for c in containers if c["health"] is not None)
            no_healthcheck = total - with_health

            cpu_total = round(sum(float(c["cpu_percent"]) for c in containers), 2)
            mem_total = int(sum(int(c["mem_usage"]) for c in containers))

            return {
                "ok": True,
                "scope": scope,
                "containers": containers,
                "summary": {
                    "total": total,
                    "running": running,
                    "exited": exited,
                    "restarting": restarting,
                    "paused": paused,
                    "healthy": healthy,
                    "unhealthy": unhealthy,
                    "starting": starting,
                    "no_healthcheck": no_healthcheck,
                    "cpu_total_percent": cpu_total,
                    "mem_total_bytes": mem_total,
                },
                "error": None,
            }
        except Exception as exc:
            return {
                "ok": False,
                "scope": scope,
                "containers": [],
                "summary": {
                    "total": 0,
                    "running": 0,
                    "exited": 0,
                    "restarting": 0,
                    "paused": 0,
                    "healthy": 0,
                    "unhealthy": 0,
                    "starting": 0,
                    "no_healthcheck": 0,
                    "cpu_total_percent": 0.0,
                    "mem_total_bytes": 0,
                },
                "error": str(exc),
            }

    @classmethod
    def stream_logs(
        cls,
        *,
        container_id: str,
        tail: int = 200,
        timestamps: bool = True,
    ) -> Iterable[bytes]:
        api = cls._get_api()
        return api.logs(
            container=container_id,
            stream=True,
            follow=True,
            tail=max(0, int(tail)),
            timestamps=bool(timestamps),
        )
