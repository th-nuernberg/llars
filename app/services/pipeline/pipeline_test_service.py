"""
Pipeline Test Service.

Idempotent service for setting up test data and creating test pipeline runs.
Used by the admin API for E2E testing of the complete pipeline loop.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from db import db

logger = logging.getLogger(__name__)

# Default test configuration for Magistral-based pipeline runs
DEFAULT_TEST_CONFIG = {
    "task_spec": (
        "Fasse den folgenden Nachrichtenartikel in 2-3 präzisen Sätzen zusammen. "
        "Die Zusammenfassung soll die wichtigsten Fakten enthalten und neutral formuliert sein."
    ),
    "meta_model_id": "Global/Mistral/Magistral-Small-2509",
    "eval_model_id": "Global/Mistral/Magistral-Small-2509",
    "num_prompt_variants": 2,
    "evaluation_type": "rating",
    "eval_config": {
        "type": "multi-dimensional",
        "min": 1,
        "max": 5,
        "step": 1,
        "dimensions": [
            {"id": "coherence", "name": {"de": "Kohärenz", "en": "Coherence"}, "weight": 0.25},
            {"id": "fluency", "name": {"de": "Flüssigkeit", "en": "Fluency"}, "weight": 0.25},
            {"id": "relevance", "name": {"de": "Relevanz", "en": "Relevance"}, "weight": 0.25},
            {"id": "consistency", "name": {"de": "Konsistenz", "en": "Consistency"}, "weight": 0.25},
        ],
    },
    "generation_params": {"temperature": 0.3, "max_tokens": 300},
    "thresholds": {
        "global_threshold": 3.5,
        "dimension_thresholds": {
            "coherence": 3.5,
            "fluency": 3.5,
            "relevance": 3.5,
            "consistency": 3.5,
        },
        "convergence_epsilon": 0.1,
        "max_plateau_iterations": 2,
    },
}

# Marker name prefix for test scenarios/runs
TEST_PREFIX = "[Pipeline-Test]"


class PipelineTestService:
    """Service for creating test data and pipeline runs for E2E testing."""

    @classmethod
    def ensure_test_data(cls) -> Dict[str, Any]:
        """
        Ensure test news articles exist as an evaluation scenario.
        Idempotent — returns existing scenario if already present.

        Returns:
            Dict with 'scenario_id', 'item_count', 'created' (bool)
        """
        from db.models.scenario import RatingScenarios, ScenarioItems, EvaluationItem

        # Check if test scenario already exists
        existing = RatingScenarios.query.filter(
            RatingScenarios.scenario_name.like(f"{TEST_PREFIX}%"),
        ).first()

        if existing:
            item_count = ScenarioItems.query.filter_by(scenario_id=existing.id).count()
            logger.info("[PipelineTest] Test scenario %d already exists (%d items)", existing.id, item_count)
            return {
                "scenario_id": existing.id,
                "item_count": item_count,
                "created": False,
            }

        # Load news articles from data file
        articles = cls._load_news_articles()
        if not articles:
            raise RuntimeError("No news articles found in data/news_articles_sample.json")

        # Create scenario
        scenario = RatingScenarios(
            scenario_name=f"{TEST_PREFIX} News Summarization",
            function_type_id=2,  # rating
            created_by="admin",
        )
        db.session.add(scenario)
        db.session.flush()

        # Create evaluation items from articles
        for article in articles:
            item = EvaluationItem(
                subject=article.get("content", article.get("subject", "")),
            )
            db.session.add(item)
            db.session.flush()

            link = ScenarioItems(
                scenario_id=scenario.id,
                item_id=item.item_id,
            )
            db.session.add(link)

        db.session.commit()

        logger.info("[PipelineTest] Created test scenario %d with %d items", scenario.id, len(articles))
        return {
            "scenario_id": scenario.id,
            "item_count": len(articles),
            "created": True,
        }

    @classmethod
    def create_test_run(
        cls,
        *,
        name: Optional[str] = None,
        task_spec: Optional[str] = None,
        candidate_models: Optional[List[str]] = None,
        eval_model_id: Optional[str] = None,
        meta_model_id: Optional[str] = None,
        max_iterations: int = 3,
        budget_tokens_total: int = 200000,
        auto_start: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a test pipeline run with sensible defaults.

        Ensures test data exists, then creates and optionally starts the run.

        Returns:
            Dict with 'run' (serialized), 'scenario' info, 'started' (bool)
        """
        from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService

        # Step 1: Ensure test data
        data_info = cls.ensure_test_data()

        # Step 2: Build config with overrides
        config = dict(DEFAULT_TEST_CONFIG)
        if task_spec:
            config["task_spec"] = task_spec
        if eval_model_id:
            config["eval_model_id"] = eval_model_id
        if meta_model_id:
            config["meta_model_id"] = meta_model_id

        config["sources"] = {
            "type": "scenario",
            "scenario_id": data_info["scenario_id"],
        }

        # Step 3: Create the pipeline run
        models = candidate_models or ["Global/Mistral/Magistral-Small-2509"]
        run_name = name or f"{TEST_PREFIX} Magistral E2E"

        run = PipelineOrchestratorService.create_run(
            name=run_name,
            config=config,
            candidate_models=models,
            created_by="admin",
            description="Auto-created by Pipeline Admin API for E2E testing",
            scenario_type="greenfield",
            source_scenario_id=data_info["scenario_id"],
            max_iterations=max_iterations,
            budget_tokens_total=budget_tokens_total,
        )

        # Step 4: Optionally start
        started = False
        if auto_start:
            PipelineOrchestratorService.start_run(run.id)
            started = True

        logger.info(
            "[PipelineTest] Created test run %d (started=%s, scenario=%d)",
            run.id, started, data_info["scenario_id"],
        )

        return {
            "run": run.to_dict(),
            "scenario": data_info,
            "started": started,
        }

    @classmethod
    def cleanup_test_data(cls) -> Dict[str, Any]:
        """
        Delete all test pipeline runs and test scenarios.

        Returns:
            Dict with counts of deleted items.
        """
        from db.models.pipeline import PipelineRun, PipelineStatus

        # Cancel any running test runs first
        test_runs = PipelineRun.query.filter(
            PipelineRun.name.like(f"{TEST_PREFIX}%"),
        ).all()

        cancelled = 0
        for run in test_runs:
            if run.status == PipelineStatus.RUNNING:
                try:
                    from services.pipeline.pipeline_orchestrator_service import PipelineOrchestratorService
                    PipelineOrchestratorService.cancel_run(run.id)
                    cancelled += 1
                except Exception as e:
                    logger.warning("[PipelineTest] Could not cancel run %d: %s", run.id, e)

        # Delete test runs (cascade deletes iterations)
        deleted_runs = PipelineRun.query.filter(
            PipelineRun.name.like(f"{TEST_PREFIX}%"),
        ).delete(synchronize_session='fetch')

        # Delete test scenarios
        from db.models.scenario import RatingScenarios
        deleted_scenarios = RatingScenarios.query.filter(
            RatingScenarios.scenario_name.like(f"{TEST_PREFIX}%"),
        ).delete(synchronize_session='fetch')

        db.session.commit()

        logger.info(
            "[PipelineTest] Cleanup: %d runs deleted (%d cancelled), %d scenarios deleted",
            deleted_runs, cancelled, deleted_scenarios,
        )

        return {
            "deleted_runs": deleted_runs,
            "cancelled_runs": cancelled,
            "deleted_scenarios": deleted_scenarios,
        }

    @classmethod
    def _load_news_articles(cls) -> List[Dict[str, Any]]:
        """Load news articles from data/news_articles_sample.json."""
        # Try relative to app directory first, then project root
        candidates = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "news_articles_sample.json"),
            os.path.join(os.getcwd(), "data", "news_articles_sample.json"),
            "/app/data/news_articles_sample.json",  # Docker path
        ]

        for path in candidates:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)

        logger.error("[PipelineTest] news_articles_sample.json not found in: %s", candidates)
        return []
