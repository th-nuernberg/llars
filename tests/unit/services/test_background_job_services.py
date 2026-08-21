"""Unit tests for durable background job services."""

from __future__ import annotations

from db.models import EvaluationItem
from db.models.scenario import FeatureFunctionType, RatingScenarios, ScenarioThreads
from services.background_jobs import LLMEvalQueueService, ScenarioStatsJobService


def _ensure_function_type(db, function_type_id: int, name: str = "ranking") -> None:
    if FeatureFunctionType.query.filter_by(function_type_id=function_type_id).first():
        return
    db.session.add(FeatureFunctionType(function_type_id=function_type_id, name=name))
    db.session.commit()


def _create_scenario_with_threads(db, *, model_id: str = "mistral-small", function_type_id: int = 1):
    _ensure_function_type(db, function_type_id)
    scenario = RatingScenarios(
        scenario_name="Background Job Scenario",
        function_type_id=function_type_id,
        config_json={"llm_evaluators": [model_id]},
    )
    db.session.add(scenario)
    db.session.commit()

    items = []
    for index in range(2):
        item = EvaluationItem(subject=f"subject-{index}", content=f"content-{index}")
        db.session.add(item)
        db.session.flush()
        db.session.add(ScenarioThreads(scenario_id=scenario.id, thread_id=item.item_id))
        items.append(item)
    db.session.commit()
    return scenario, items


class TestLLMEvalQueueService:
    def test_BGJ_LLM_001_enqueue_claim_and_finish(self, app, db, app_context):
        """Queued LLM eval runs should be claimable and finish cleanly on SQLite tests."""
        scenario, _items = _create_scenario_with_threads(db)

        queued = LLMEvalQueueService.enqueue_for_scenario(scenario.id)
        assert len(queued) == 1
        assert queued[0].status == "queued"
        assert queued[0].requested_all is True

        claimed = LLMEvalQueueService.claim_next_run("worker-a")
        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.worker_id == "worker-a"

        LLMEvalQueueService.finish_run(claimed.id, processing_token=claimed.processing_token)

        refreshed = type(claimed).query.get(claimed.id)
        assert refreshed.status == "idle"
        assert refreshed.worker_id is None
        assert refreshed.requested_all is False

    def test_BGJ_LLM_002_finish_requeues_if_new_request_arrives(self, app, db, app_context):
        """A newer request token should keep the run queued after the worker finishes."""
        scenario, items = _create_scenario_with_threads(db)
        run = LLMEvalQueueService.enqueue_run(scenario.id, model_id="mistral-small", thread_ids=[items[0].item_id])
        claimed = LLMEvalQueueService.claim_next_run("worker-b")

        LLMEvalQueueService.enqueue_run(
            scenario.id,
            model_id="mistral-small",
            thread_ids=[items[1].item_id],
        )
        LLMEvalQueueService.finish_run(claimed.id, processing_token=claimed.processing_token)

        refreshed = type(run).query.get(run.id)
        assert refreshed.status == "queued"
        assert refreshed.request_token > claimed.processing_token


class TestScenarioStatsJobService:
    def test_BGJ_STATS_001_enqueue_claim_and_finish(self, app, db, app_context):
        """Stats recompute jobs should dedupe by scenario and be claimable on SQLite tests."""
        scenario, _items = _create_scenario_with_threads(db)

        job = ScenarioStatsJobService.enqueue_recompute(scenario.id, priority=1)
        job = ScenarioStatsJobService.enqueue_recompute(scenario.id, priority=3)
        assert job.status == "queued"
        assert job.priority == 3
        assert job.request_token == 2

        claimed = ScenarioStatsJobService.claim_next_job("stats-worker")
        assert claimed is not None
        assert claimed.status == "running"
        assert claimed.worker_id == "stats-worker"

        ScenarioStatsJobService.finish_job(claimed.id, processing_token=claimed.processing_token)

        refreshed = type(job).query.get(job.id)
        assert refreshed.status == "idle"
        assert refreshed.worker_id is None
        assert refreshed.priority == 0
