from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db.database import db
from db.models import ScenarioStatsJob

logger = logging.getLogger(__name__)


class ScenarioStatsJobService:
    LEASE_SECONDS = 120
    POLL_INTERVAL_SECONDS = 2

    @staticmethod
    def enqueue_recompute(scenario_id: int, *, priority: int = 0) -> ScenarioStatsJob:
        now = datetime.utcnow()
        job = ScenarioStatsJob.query.filter_by(scenario_id=scenario_id).first()
        if job is None:
            job = ScenarioStatsJob(
                scenario_id=scenario_id,
                status=ScenarioStatsJob.STATUS_QUEUED,
                priority=int(priority),
                request_token=1,
                last_requested_at=now,
            )
            db.session.add(job)
        else:
            job.priority = max(int(job.priority or 0), int(priority))
            job.request_token = int(job.request_token or 0) + 1
            job.last_requested_at = now
            if job.status in (ScenarioStatsJob.STATUS_IDLE, ScenarioStatsJob.STATUS_FAILED):
                job.status = ScenarioStatsJob.STATUS_QUEUED
                job.last_error = None
        db.session.commit()
        return job

    @staticmethod
    def _claim_candidate_sql() -> str:
        return """
            SELECT id
            FROM scenario_stats_jobs
            WHERE (
                status = 'queued'
                OR (
                    status = 'running'
                    AND lease_expires_at IS NOT NULL
                    AND lease_expires_at < UTC_TIMESTAMP()
                )
            )
            ORDER BY priority DESC, COALESCE(last_requested_at, created_at), id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """

    @staticmethod
    def claim_next_job(worker_id: str, *, lease_seconds: Optional[int] = None) -> Optional[ScenarioStatsJob]:
        lease_seconds = int(lease_seconds or ScenarioStatsJobService.LEASE_SECONDS)
        bind = db.session.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
        if dialect_name != "sqlite":
            try:
                row = db.session.execute(text(ScenarioStatsJobService._claim_candidate_sql())).first()
            except SQLAlchemyError:
                db.session.rollback()
                row = None
            if row:
                job = ScenarioStatsJob.query.get(int(row[0]))
            else:
                job = None
        else:
            job = None

        if job is None:
            now = datetime.utcnow()
            job = (
                ScenarioStatsJob.query
                .filter(
                    or_(
                        ScenarioStatsJob.status == ScenarioStatsJob.STATUS_QUEUED,
                        (
                            (ScenarioStatsJob.status == ScenarioStatsJob.STATUS_RUNNING)
                            & ScenarioStatsJob.lease_expires_at.isnot(None)
                            & (ScenarioStatsJob.lease_expires_at < now)
                        ),
                    )
                )
                .order_by(
                    ScenarioStatsJob.priority.desc(),
                    ScenarioStatsJob.last_requested_at.asc(),
                    ScenarioStatsJob.created_at.asc(),
                    ScenarioStatsJob.id.asc(),
                )
                .first()
            )
            if not job:
                db.session.rollback()
                return None

        now = datetime.utcnow()
        job.status = ScenarioStatsJob.STATUS_RUNNING
        job.worker_id = worker_id
        job.processing_token = int(job.request_token or 0)
        job.started_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        job.last_heartbeat_at = now
        job.last_error = None
        db.session.commit()
        return job

    @staticmethod
    def heartbeat(job_id: int, worker_id: str, *, lease_seconds: Optional[int] = None) -> None:
        lease_seconds = int(lease_seconds or ScenarioStatsJobService.LEASE_SECONDS)
        job = ScenarioStatsJob.query.get(job_id)
        if not job or job.worker_id != worker_id or job.status != ScenarioStatsJob.STATUS_RUNNING:
            return
        now = datetime.utcnow()
        job.last_heartbeat_at = now
        job.lease_expires_at = now + timedelta(seconds=lease_seconds)
        db.session.commit()

    @staticmethod
    def finish_job(job_id: int, *, processing_token: int, error: Optional[str] = None) -> None:
        job = ScenarioStatsJob.query.get(job_id)
        if not job:
            db.session.rollback()
            return

        has_new_request = int(job.request_token or 0) != int(processing_token or 0)
        job.worker_id = None
        job.lease_expires_at = None
        job.last_heartbeat_at = datetime.utcnow()
        job.completed_at = datetime.utcnow()
        job.priority = 0

        if error:
            job.last_error = error
            job.status = ScenarioStatsJob.STATUS_QUEUED if has_new_request else ScenarioStatsJob.STATUS_FAILED
        elif has_new_request:
            job.status = ScenarioStatsJob.STATUS_QUEUED
        else:
            job.status = ScenarioStatsJob.STATUS_IDLE
            job.last_error = None

        db.session.commit()
