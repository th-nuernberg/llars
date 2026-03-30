from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from sqlalchemy import or_
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db.database import db
from db.models import ComparisonSession, FeatureFunctionType, LLMEvalRun, LLMTaskResult, RatingScenarios, ScenarioThreads

logger = logging.getLogger(__name__)


class LLMEvalQueueService:
    LEASE_SECONDS = 120
    POLL_INTERVAL_SECONDS = 2

    @staticmethod
    def _normalize_thread_ids(thread_ids: Optional[Iterable[int]]) -> list[int]:
        if thread_ids is None:
            return []
        normalized: list[int] = []
        seen = set()
        for value in thread_ids:
            try:
                item_id = int(value)
            except (TypeError, ValueError):
                continue
            if item_id in seen:
                continue
            seen.add(item_id)
            normalized.append(item_id)
        return normalized

    @staticmethod
    def enqueue_run(
        scenario_id: int,
        *,
        model_id: str,
        thread_ids: Optional[Iterable[int]] = None,
        requested_all: bool = False,
        task_type: Optional[str] = None,
    ) -> LLMEvalRun:
        now = datetime.utcnow()
        requested_ids = LLMEvalQueueService._normalize_thread_ids(thread_ids)
        run = LLMEvalRun.query.filter_by(scenario_id=scenario_id, model_id=model_id).first()
        if run is None:
            run = LLMEvalRun(
                scenario_id=scenario_id,
                model_id=model_id,
                task_type=task_type,
                status=LLMEvalRun.STATUS_QUEUED,
                requested_all=bool(requested_all or not requested_ids),
                thread_ids_json=requested_ids or None,
                request_token=1,
                last_requested_at=now,
            )
            db.session.add(run)
        else:
            existing_ids = LLMEvalQueueService._normalize_thread_ids(run.thread_ids_json or [])
            merged_ids = list(dict.fromkeys(existing_ids + requested_ids))
            run.task_type = task_type or run.task_type
            run.requested_all = bool(run.requested_all or requested_all or not requested_ids)
            run.thread_ids_json = None if run.requested_all else (merged_ids or None)
            run.request_token = int(run.request_token or 0) + 1
            run.last_requested_at = now
            if run.status in (LLMEvalRun.STATUS_IDLE, LLMEvalRun.STATUS_FAILED):
                run.status = LLMEvalRun.STATUS_QUEUED
                run.last_error = None
            elif run.status == LLMEvalRun.STATUS_QUEUED:
                run.last_error = None
        db.session.commit()
        return run

    @staticmethod
    def enqueue_for_scenario(
        scenario_id: int,
        *,
        model_ids: Optional[Iterable[str]] = None,
        thread_ids: Optional[Iterable[int]] = None,
    ) -> list[LLMEvalRun]:
        scenario = RatingScenarios.query.get(scenario_id)
        if not scenario:
            return []

        if model_ids is None:
            config = scenario.config_json
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except (TypeError, ValueError, json.JSONDecodeError):
                    config = {}
            if not isinstance(config, dict):
                config = {}
            selected = config.get("llm_evaluators") or config.get("selected_llms") or []
        else:
            selected = list(model_ids)

        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        task_type = function_type.name if function_type else None

        queued: list[LLMEvalRun] = []
        for model_id in selected:
            if not isinstance(model_id, str) or not model_id.strip():
                continue
            queued.append(
                LLMEvalQueueService.enqueue_run(
                    scenario_id,
                    model_id=model_id.strip(),
                    thread_ids=thread_ids,
                    requested_all=thread_ids is None,
                    task_type=task_type,
                )
            )
        return queued

    @staticmethod
    def is_active(scenario_id: int, model_id: str) -> bool:
        run = LLMEvalRun.query.filter_by(scenario_id=scenario_id, model_id=model_id).first()
        if run is None:
            return False
        if run.status == LLMEvalRun.STATUS_QUEUED:
            return True
        if run.status != LLMEvalRun.STATUS_RUNNING:
            return False
        if run.lease_expires_at is None:
            return False
        return run.lease_expires_at >= datetime.utcnow()

    @staticmethod
    def _claim_candidate_sql() -> str:
        return """
            SELECT id
            FROM llm_eval_runs
            WHERE (
                status = 'queued'
                OR (
                    status = 'running'
                    AND lease_expires_at IS NOT NULL
                    AND lease_expires_at < UTC_TIMESTAMP()
                )
            )
            ORDER BY COALESCE(last_requested_at, created_at), id
            LIMIT 1
            FOR UPDATE SKIP LOCKED
        """

    @staticmethod
    def claim_next_run(worker_id: str, *, lease_seconds: Optional[int] = None) -> Optional[LLMEvalRun]:
        lease_seconds = int(lease_seconds or LLMEvalQueueService.LEASE_SECONDS)
        bind = db.session.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
        if dialect_name != "sqlite":
            try:
                row = db.session.execute(text(LLMEvalQueueService._claim_candidate_sql())).first()
            except SQLAlchemyError:
                db.session.rollback()
                row = None
            if row:
                run = LLMEvalRun.query.get(int(row[0]))
            else:
                run = None
        else:
            run = None

        if run is None:
            now = datetime.utcnow()
            run = (
                LLMEvalRun.query
                .filter(
                    or_(
                        LLMEvalRun.status == LLMEvalRun.STATUS_QUEUED,
                        (
                            (LLMEvalRun.status == LLMEvalRun.STATUS_RUNNING)
                            & LLMEvalRun.lease_expires_at.isnot(None)
                            & (LLMEvalRun.lease_expires_at < now)
                        ),
                    )
                )
                .order_by(
                    LLMEvalRun.last_requested_at.asc(),
                    LLMEvalRun.created_at.asc(),
                    LLMEvalRun.id.asc(),
                )
                .first()
            )
            if not run:
                db.session.rollback()
                return None

        now = datetime.utcnow()
        run.status = LLMEvalRun.STATUS_RUNNING
        run.worker_id = worker_id
        run.processing_token = int(run.request_token or 0)
        run.started_at = now
        run.lease_expires_at = now + timedelta(seconds=lease_seconds)
        run.last_heartbeat_at = now
        run.last_error = None
        db.session.commit()
        return run

    @staticmethod
    def heartbeat(run_id: int, worker_id: str, *, lease_seconds: Optional[int] = None) -> None:
        lease_seconds = int(lease_seconds or LLMEvalQueueService.LEASE_SECONDS)
        run = LLMEvalRun.query.get(run_id)
        if not run or run.worker_id != worker_id or run.status != LLMEvalRun.STATUS_RUNNING:
            return
        now = datetime.utcnow()
        run.last_heartbeat_at = now
        run.lease_expires_at = now + timedelta(seconds=lease_seconds)
        db.session.commit()

    @staticmethod
    def finish_run(run_id: int, *, processing_token: int, error: Optional[str] = None) -> None:
        run = LLMEvalRun.query.get(run_id)
        if not run:
            db.session.rollback()
            return

        has_new_request = int(run.request_token or 0) != int(processing_token or 0)
        run.worker_id = None
        run.lease_expires_at = None
        run.last_heartbeat_at = datetime.utcnow()
        run.completed_at = datetime.utcnow()

        if error:
            run.last_error = error
            run.status = LLMEvalRun.STATUS_QUEUED if has_new_request else LLMEvalRun.STATUS_FAILED
        elif has_new_request:
            run.status = LLMEvalRun.STATUS_QUEUED
        else:
            run.status = LLMEvalRun.STATUS_IDLE
            run.requested_all = False
            run.thread_ids_json = None
            run.last_error = None

        db.session.commit()

    @staticmethod
    def resolve_target_ids(run: LLMEvalRun) -> list[int]:
        scenario = RatingScenarios.query.get(run.scenario_id)
        if not scenario:
            return []

        function_type = FeatureFunctionType.query.filter_by(
            function_type_id=scenario.function_type_id
        ).first()
        function_name = function_type.name if function_type else None

        if function_name == "comparison":
            available_ids = [session.id for session in ComparisonSession.query.filter_by(scenario_id=scenario.id).all()]
        else:
            available_ids = [row.thread_id for row in ScenarioThreads.query.filter_by(scenario_id=scenario.id).all()]

        if run.requested_all:
            return available_ids

        requested_ids = LLMEvalQueueService._normalize_thread_ids(run.thread_ids_json or [])
        requested_set = set(requested_ids)
        return [item_id for item_id in available_ids if item_id in requested_set]

    @staticmethod
    def enqueue_pending_evaluations_from_scenarios() -> int:
        from services.llm.llm_ai_task_runner import LLMAITaskRunner

        started = 0
        scenarios = RatingScenarios.query.filter(RatingScenarios.config_json.isnot(None)).all()
        for scenario in scenarios:
            config = scenario.config_json
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except (TypeError, ValueError, json.JSONDecodeError):
                    config = {}
            if not isinstance(config, dict):
                continue

            llm_evaluators = config.get("llm_evaluators") or config.get("selected_llms") or []
            if not llm_evaluators:
                continue

            function_type = FeatureFunctionType.query.filter_by(
                function_type_id=scenario.function_type_id
            ).first()
            function_name = function_type.name if function_type else None

            if function_name == "comparison":
                all_ids = {session.id for session in ComparisonSession.query.filter_by(scenario_id=scenario.id).all()}
            else:
                all_ids = {row.thread_id for row in ScenarioThreads.query.filter_by(scenario_id=scenario.id).all()}

            if not all_ids:
                continue

            for model_id in llm_evaluators:
                permanent_failures = db.session.query(LLMTaskResult).filter(
                    LLMTaskResult.scenario_id == scenario.id,
                    LLMTaskResult.model_id == model_id,
                    LLMTaskResult.error.isnot(None),
                ).limit(5).all()
                has_permanent = any(
                    LLMAITaskRunner._is_permanent_failure(row.error)
                    for row in permanent_failures if row.error
                )
                if has_permanent:
                    continue

                cooldown_cutoff = datetime.utcnow() - timedelta(minutes=30)
                recent_errors = db.session.query(db.func.count()).filter(
                    LLMTaskResult.scenario_id == scenario.id,
                    LLMTaskResult.model_id == model_id,
                    LLMTaskResult.error.isnot(None),
                    LLMTaskResult.updated_at >= cooldown_cutoff,
                ).scalar() or 0
                if recent_errors >= 3:
                    continue

                completed_rows = db.session.query(LLMTaskResult.thread_id).filter(
                    LLMTaskResult.scenario_id == scenario.id,
                    LLMTaskResult.model_id == model_id,
                    LLMTaskResult.payload_json.isnot(None),
                    LLMTaskResult.error.is_(None),
                ).all()
                completed_ids = {row[0] for row in completed_rows if row[0]}

                errored_rows = db.session.query(LLMTaskResult.thread_id).filter(
                    LLMTaskResult.scenario_id == scenario.id,
                    LLMTaskResult.model_id == model_id,
                    LLMTaskResult.error.isnot(None),
                ).all()
                errored_ids = {row[0] for row in errored_rows if row[0]}

                pending_ids = list(all_ids - completed_ids - errored_ids)
                if not pending_ids:
                    continue

                LLMEvalQueueService.enqueue_run(
                    scenario.id,
                    model_id=str(model_id),
                    thread_ids=pending_ids,
                    requested_all=False,
                    task_type=function_name,
                )
                started += 1
        return started
