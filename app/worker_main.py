from __future__ import annotations

import logging
import multiprocessing as mp
import os
import threading
import time
import uuid

from services.runtime_config import is_worker_runtime

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def _start_heartbeat_loop(callback, *, interval_seconds: int) -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()

    def _run():
        while not stop_event.wait(interval_seconds):
            try:
                callback()
            except Exception:
                logger.exception("Background worker heartbeat failed")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread, stop_event


def _run_stats_worker(worker_label: str) -> None:
    from main import app
    from db.database import db
    from services.background_jobs import ScenarioStatsJobService
    from services.scenario_stats_cache_service import recompute_stats_for_worker

    poll_interval = float(os.environ.get("SCENARIO_STATS_POLL_INTERVAL", ScenarioStatsJobService.POLL_INTERVAL_SECONDS))

    with app.app_context():
        while True:
            try:
                job = ScenarioStatsJobService.claim_next_job(worker_label)
                if not job:
                    time.sleep(poll_interval)
                    continue

                heartbeat_thread, stop_event = _start_heartbeat_loop(
                    lambda: ScenarioStatsJobService.heartbeat(job.id, worker_label),
                    interval_seconds=max(5, ScenarioStatsJobService.LEASE_SECONDS // 3),
                )
                try:
                    recompute_stats_for_worker(job.scenario_id)
                    ScenarioStatsJobService.finish_job(job.id, processing_token=job.processing_token)
                except Exception as exc:
                    logger.exception("[StatsWorker] Failed scenario %s", job.scenario_id)
                    db.session.rollback()
                    ScenarioStatsJobService.finish_job(job.id, processing_token=job.processing_token, error=str(exc))
                finally:
                    stop_event.set()
                    heartbeat_thread.join(timeout=1.0)
                    db.session.remove()
            except Exception:
                db.session.rollback()
                logger.exception("[StatsWorker] Loop failure")
                time.sleep(poll_interval)


def _run_llm_eval_worker(worker_label: str) -> None:
    from main import app
    from db.database import db
    from services.background_jobs import LLMEvalQueueService
    from services.llm.llm_ai_task_runner import LLMAITaskRunner

    poll_interval = float(os.environ.get("LLM_EVAL_POLL_INTERVAL", LLMEvalQueueService.POLL_INTERVAL_SECONDS))

    with app.app_context():
        while True:
            try:
                run = LLMEvalQueueService.claim_next_run(worker_label)
                if not run:
                    time.sleep(poll_interval)
                    continue

                target_ids = LLMEvalQueueService.resolve_target_ids(run)
                heartbeat_thread, stop_event = _start_heartbeat_loop(
                    lambda: LLMEvalQueueService.heartbeat(run.id, worker_label),
                    interval_seconds=max(5, LLMEvalQueueService.LEASE_SECONDS // 3),
                )
                try:
                    if target_ids:
                        LLMAITaskRunner.run_for_scenario(
                            run.scenario_id,
                            model_ids=[run.model_id],
                            thread_ids=target_ids,
                            use_process_lock=False,
                        )
                    LLMEvalQueueService.finish_run(run.id, processing_token=run.processing_token)
                except Exception as exc:
                    logger.exception(
                        "[LLMEvalWorker] Failed scenario=%s model=%s",
                        run.scenario_id,
                        run.model_id,
                    )
                    db.session.rollback()
                    LLMEvalQueueService.finish_run(run.id, processing_token=run.processing_token, error=str(exc))
                finally:
                    stop_event.set()
                    heartbeat_thread.join(timeout=1.0)
                    db.session.remove()
            except Exception:
                db.session.rollback()
                logger.exception("[LLMEvalWorker] Loop failure")
                time.sleep(poll_interval)


def _spawn_named_processes(kind: str, count: int, target) -> list[mp.Process]:
    processes: list[mp.Process] = []
    base_id = str(uuid.uuid4())[:8]
    for index in range(count):
        worker_label = f"{kind}-{base_id}-{index}"
        process = mp.Process(target=target, args=(worker_label,), daemon=False, name=worker_label)
        process.start()
        processes.append(process)
    return processes


def main() -> int:
    if not is_worker_runtime():
        logger.error("LLARS worker started without LLARS_RUNTIME_ROLE=worker")
        return 2

    from main import app
    from services.background_jobs import LLMEvalQueueService

    with app.app_context():
        resumed = LLMEvalQueueService.enqueue_pending_evaluations_from_scenarios()
        logger.info("[WorkerMain] Enqueued %s pending LLM evaluation runs on startup", resumed)

    stats_worker_processes = max(1, int(os.environ.get("STATS_WORKER_PROCESSES", 2)))
    llm_eval_worker_processes = max(1, int(os.environ.get("LLM_EVAL_WORKER_PROCESSES", 2)))

    processes = []
    processes.extend(_spawn_named_processes("stats", stats_worker_processes, _run_stats_worker))
    processes.extend(_spawn_named_processes("llm-eval", llm_eval_worker_processes, _run_llm_eval_worker))

    try:
        while True:
            for process in processes:
                process.join(timeout=1.0)
                if not process.is_alive():
                    logger.error("[WorkerMain] Child %s exited unexpectedly with code %s", process.name, process.exitcode)
                    return int(process.exitcode or 1)
    except KeyboardInterrupt:
        logger.info("[WorkerMain] Shutting down worker processes")
        for process in processes:
            if process.is_alive():
                process.terminate()
        for process in processes:
            process.join(timeout=5.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

