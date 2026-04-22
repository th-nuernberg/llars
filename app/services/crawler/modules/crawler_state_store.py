from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from services.runtime_config import get_redis_client

logger = logging.getLogger(__name__)


class CrawlerStateStore:
    """Redis-backed shared crawl job state for cross-worker visibility."""

    KEY_JOB = "crawler:job:{job_id}"
    KEY_INDEX = "crawler:jobs:index"
    TTL_JOB_SECONDS = int(os.environ.get("CRAWLER_JOB_STATE_TTL_SECONDS", "86400"))

    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()

    @classmethod
    def _job_key(cls, job_id: str) -> str:
        return cls.KEY_JOB.format(job_id=job_id)

    def persist_job(self, job_id: str, job_data: Dict) -> Dict:
        payload = dict(job_data or {})
        payload["job_id"] = job_id
        payload["last_updated_at"] = datetime.utcnow().isoformat()

        self.redis.setex(
            self._job_key(job_id),
            self.TTL_JOB_SECONDS,
            json.dumps(payload, default=str),
        )
        self.redis.sadd(self.KEY_INDEX, job_id)
        return payload

    def get_job(self, job_id: str, *, refresh_ttl: bool = True) -> Optional[Dict]:
        raw = self.redis.get(self._job_key(job_id))
        if not raw:
            return None

        if refresh_ttl:
            self.redis.expire(self._job_key(job_id), self.TTL_JOB_SECONDS)

        try:
            job = json.loads(raw)
        except Exception as exc:
            logger.warning(f"[CrawlerStateStore] Invalid job payload for {job_id}: {exc}")
            self.delete_job(job_id)
            return None

        if isinstance(job, dict) and "job_id" not in job:
            job["job_id"] = job_id
        return job if isinstance(job, dict) else None

    def list_jobs(self) -> List[Dict]:
        jobs: List[Dict] = []
        stale_job_ids: List[str] = []

        for job_id in self.redis.smembers(self.KEY_INDEX):
            job = self.get_job(str(job_id), refresh_ttl=False)
            if job:
                jobs.append(job)
            else:
                stale_job_ids.append(str(job_id))

        if stale_job_ids:
            self.redis.srem(self.KEY_INDEX, *stale_job_ids)

        jobs.sort(
            key=lambda x: x.get("started_at") or x.get("queued_at") or "",
            reverse=True,
        )
        return jobs

    def delete_job(self, job_id: str) -> None:
        self.redis.delete(self._job_key(job_id))
        self.redis.srem(self.KEY_INDEX, job_id)
