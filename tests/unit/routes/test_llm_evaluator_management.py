"""Route tests for adding/removing an LLM as a scenario assessor.

Covers app/routes/scenarios/scenario_crud.py:
- POST   /api/scenarios/<id>/llm-evaluators          (add + auto-start)
- DELETE /api/scenarios/<id>/llm-evaluators/<model>  (remove + result cleanup)

Prefix: ADDLLM
"""

from datetime import datetime
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _clear_locks():
    from services.llm.llm_ai_task_runner import LLMAITaskRunner
    LLMAITaskRunner._active_locks.clear()
    yield
    LLMAITaskRunner._active_locks.clear()


def _make_scenario(rdb, real_app, config=None):
    from db.models.scenario import RatingScenarios
    with real_app.app_context():
        s = RatingScenarios(
            scenario_name="LLM Assessor Test", function_type_id=7,
            config_json=config or {}, begin=datetime.utcnow(), end=datetime.utcnow(),
        )
        rdb.session.add(s)
        rdb.session.commit()
        return s.id


def _config_of(real_app, sid):
    from db.models.scenario import RatingScenarios
    with real_app.app_context():
        return dict(RatingScenarios.query.get(sid).config_json or {})


ACCESS = "services.llm.llm_access_service.LLMAccessService.user_can_access_model"
RUNNER = "routes.scenarios.scenario_crud.LLMAITaskRunner.run_for_scenario_async"


class TestAddLLMEvaluator:

    def test_ADDLLM_001_add_persists_and_enables(self, auth_admin, real_app, rdb, seed_function_types):
        sid = _make_scenario(rdb, real_app)
        with patch(ACCESS, return_value=True), patch(RUNNER):
            resp = auth_admin.post(
                f"/api/scenarios/{sid}/llm-evaluators",
                json={"model_id": "Global/Mistral/Mistral-Medium-3.5-128B", "autostart": False},
            )
        assert resp.status_code == 200
        cfg = _config_of(real_app, sid)
        assert cfg["llm_evaluators"] == ["Global/Mistral/Mistral-Medium-3.5-128B"]
        assert cfg["enable_llm_evaluation"] is True

    def test_ADDLLM_002_add_is_idempotent(self, auth_admin, real_app, rdb, seed_function_types):
        sid = _make_scenario(rdb, real_app, {"llm_evaluators": ["Global/X/M"]})
        with patch(ACCESS, return_value=True), patch(RUNNER):
            auth_admin.post(f"/api/scenarios/{sid}/llm-evaluators",
                            json={"model_id": "Global/X/M", "autostart": False})
        assert _config_of(real_app, sid)["llm_evaluators"] == ["Global/X/M"]

    def test_ADDLLM_003_no_access_is_forbidden(self, auth_admin, real_app, rdb, seed_function_types):
        sid = _make_scenario(rdb, real_app)
        with patch(ACCESS, return_value=False), patch(RUNNER):
            resp = auth_admin.post(f"/api/scenarios/{sid}/llm-evaluators",
                                   json={"model_id": "Global/X/M", "autostart": False})
        assert resp.status_code == 403
        assert "llm_evaluators" not in _config_of(real_app, sid)

    def test_ADDLLM_004_autostart_triggers_runner(self, auth_admin, real_app, rdb, seed_function_types):
        sid = _make_scenario(rdb, real_app)
        with patch(ACCESS, return_value=True), patch(RUNNER) as mock_run:
            resp = auth_admin.post(f"/api/scenarios/{sid}/llm-evaluators",
                                   json={"model_id": "Global/X/M", "autostart": True})
        assert resp.status_code == 200
        assert resp.get_json()["started"] is True
        mock_run.assert_called_once()
        # the managed runner is invoked for exactly the added model
        assert mock_run.call_args.kwargs.get("model_ids") == ["Global/X/M"]

    def test_ADDLLM_005_missing_model_id_is_400(self, auth_admin, real_app, rdb, seed_function_types):
        sid = _make_scenario(rdb, real_app)
        resp = auth_admin.post(f"/api/scenarios/{sid}/llm-evaluators", json={"autostart": False})
        assert resp.status_code == 400

    def test_ADDLLM_006_scenario_not_found(self, auth_admin, real_app, seed_function_types):
        with patch(ACCESS, return_value=True), patch(RUNNER):
            resp = auth_admin.post("/api/scenarios/999999/llm-evaluators",
                                   json={"model_id": "Global/X/M"})
        assert resp.status_code == 404


class TestRemoveLLMEvaluator:

    def test_ADDLLM_010_remove_drops_model_and_results(self, auth_admin, real_app, rdb, seed_function_types):
        from db.models.scenario import EvaluationItem, ScenarioItems
        from db.models.llm_task_result import LLMTaskResult
        model = "Global/Mistral/Mistral-Medium-3.5-128B"
        sid = _make_scenario(rdb, real_app, {"llm_evaluators": [model, "Global/Other/M"]})
        # seed a stored LLM result for the model we will remove
        with real_app.app_context():
            it = EvaluationItem(subject="x", function_type_id=7)
            rdb.session.add(it)
            rdb.session.flush()
            rdb.session.add(ScenarioItems(scenario_id=sid, item_id=it.item_id))
            rdb.session.add(LLMTaskResult(
                scenario_id=sid, item_id=it.item_id, model_id=model,
                task_type="labeling", payload_json={"label": "cat_x"},
            ))
            rdb.session.commit()

        resp = auth_admin.delete(f"/api/scenarios/{sid}/llm-evaluators/{model}")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["removed_results"] == 1
        assert body["llm_evaluators"] == ["Global/Other/M"]

        cfg = _config_of(real_app, sid)
        assert cfg["llm_evaluators"] == ["Global/Other/M"]
        with real_app.app_context():
            assert LLMTaskResult.query.filter_by(scenario_id=sid, model_id=model).count() == 0

    def test_ADDLLM_011_remove_last_clears_key(self, auth_admin, real_app, rdb, seed_function_types):
        model = "Global/X/M"
        sid = _make_scenario(rdb, real_app, {"llm_evaluators": [model]})
        resp = auth_admin.delete(f"/api/scenarios/{sid}/llm-evaluators/{model}")
        assert resp.status_code == 200
        cfg = _config_of(real_app, sid)
        assert "llm_evaluators" not in cfg
        # removing the last assessor turns LLM evaluation back off
        assert cfg.get("enable_llm_evaluation") is False
