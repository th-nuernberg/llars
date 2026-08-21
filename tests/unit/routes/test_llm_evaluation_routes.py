"""
Route Tests for LLM Evaluation API
====================================

Tests for app/routes/llm/llm_evaluation_routes.py which provides endpoints
for LLM evaluation progress tracking, result retrieval, start/retry,
error listing, and stop functionality.

Covers all 5 endpoints:
- GET  /api/evaluation/llm/<scenario_id>/progress
- GET  /api/evaluation/llm/result/<result_id>
- POST /api/evaluation/llm/<scenario_id>/start
- GET  /api/evaluation/llm/<scenario_id>/errors
- POST /api/evaluation/llm/<scenario_id>/stop

Uses real blueprints with mocked OIDC token validation.
Prefix: LLM_EVAL
"""

import pytest
from datetime import datetime
from unittest.mock import patch


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_active_locks():
    """
    Clear LLMAITaskRunner._active_locks before and after each test.

    The runner uses an in-memory set to track active (scenario, model) pairs.
    Leaked locks from one test would cause false 'running' status in the next,
    so we reset the set on both sides of the test boundary.
    """
    from services.llm.llm_ai_task_runner import LLMAITaskRunner
    LLMAITaskRunner._active_locks.clear()
    yield
    LLMAITaskRunner._active_locks.clear()


@pytest.fixture
def create_llm_scenario(rdb, real_app, seed_function_types):
    """
    Factory fixture that creates a scenario with evaluation items and optional LLMTaskResult rows.

    Returns a dict with scenario, items, and results for easy access in tests.

    Args (via kwargs):
        name: Scenario name (default 'Test LLM Scenario')
        config_json: Scenario config dict (default includes one LLM evaluator)
        item_count: Number of EvaluationItem rows to create (default 3)
        results: List of dicts describing LLMTaskResult rows to seed, each with keys:
            - item_index: Index into the created items list
            - model_id: Model identifier string
            - task_type: Task type string (default 'evaluation')
            - payload_json: Result payload (None means no success result)
            - error: Error string (None means no error)
    """
    from db.models.scenario import (
        RatingScenarios, EvaluationItem, ScenarioItems, FeatureFunctionType
    )
    from db.models.llm_task_result import LLMTaskResult

    def _factory(
        name='Test LLM Scenario',
        config_json=None,
        item_count=3,
        results=None,
    ):
        with real_app.app_context():
            if config_json is None:
                config_json = {'llm_evaluators': ['test-model-1']}

            scenario = RatingScenarios(
                scenario_name=name,
                function_type_id=2,  # rating
                config_json=config_json,
                begin=datetime.utcnow(),
                end=datetime.utcnow(),
            )
            rdb.session.add(scenario)
            rdb.session.commit()
            scenario_id = scenario.id

            # Create evaluation items and link them to the scenario
            item_ids = []
            for i in range(item_count):
                item = EvaluationItem(
                    subject=f'Test Item {i + 1}',
                    function_type_id=2,
                )
                rdb.session.add(item)
                rdb.session.flush()  # Get item_id before creating ScenarioItems
                item_ids.append(item.item_id)

                link = ScenarioItems(
                    scenario_id=scenario_id,
                    item_id=item.item_id,
                )
                rdb.session.add(link)

            rdb.session.commit()

            # Seed LLMTaskResult rows if requested.
            # IMPORTANT: Only set payload_json/error when explicitly provided.
            # SQLite's JSON type serializes Python None to the string 'null'
            # instead of SQL NULL, which breaks isnot(None) filters.
            result_ids = []
            if results:
                for r in results:
                    idx = r.get('item_index', 0)
                    kwargs = {
                        'scenario_id': scenario_id,
                        'item_id': item_ids[idx],
                        'model_id': r.get('model_id', 'test-model-1'),
                        'task_type': r.get('task_type', 'evaluation'),
                    }
                    if 'payload_json' in r and r['payload_json'] is not None:
                        kwargs['payload_json'] = r['payload_json']
                    if 'error' in r and r['error'] is not None:
                        kwargs['error'] = r['error']
                    result_row = LLMTaskResult(**kwargs)
                    rdb.session.add(result_row)
                    rdb.session.flush()
                    result_ids.append(result_row.id)
                rdb.session.commit()

            # Return plain IDs to avoid DetachedInstanceError
            return {
                'scenario_id': scenario_id,
                'item_ids': item_ids,
                'result_ids': result_ids,
            }

    return _factory


# ===========================================================================
# GET /api/evaluation/llm/<scenario_id>/progress
# ===========================================================================

class TestGetEvaluationProgress:
    """Tests for the evaluation progress endpoint.

    Validates status calculation, per-model progress, and auth requirements.
    The endpoint aggregates LLMTaskResult counts to determine overall and
    per-model status (idle, pending, running, completed, failed, stopped).
    """

    def test_LLM_EVAL_PROG_001_unauthenticated(self, rclient, rdb, rmock_token):
        """Unauthenticated requests must be rejected with 401."""
        response = rclient.get('/api/evaluation/llm/1/progress')
        assert response.status_code == 401

    def test_LLM_EVAL_PROG_002_scenario_not_found(self, auth_admin, real_app):
        """Non-existent scenario returns 404."""
        with real_app.app_context():
            response = auth_admin.get('/api/evaluation/llm/99999/progress')
            assert response.status_code == 404

    def test_LLM_EVAL_PROG_003_empty_scenario_idle(self, auth_admin, real_app,
                                                     create_llm_scenario):
        """Scenario with no configured LLMs returns idle status."""
        with real_app.app_context():
            data = create_llm_scenario(config_json={}, item_count=0)
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()
            assert body['status'] == 'idle'
            assert body['progress']['total'] == 0

    def test_LLM_EVAL_PROG_004_configured_llms_model_progress(self, auth_admin, real_app,
                                                                create_llm_scenario):
        """Configured LLM evaluators appear in model_progress with correct totals."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['model-a', 'model-b']},
                item_count=2,
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            assert 'model-a' in body['model_progress']
            assert 'model-b' in body['model_progress']
            assert body['model_progress']['model-a']['total'] == 2
            assert body['model_progress']['model-b']['total'] == 2
            assert body['total_threads'] == 2

    def test_LLM_EVAL_PROG_005_completed_items_progress_percent(self, auth_admin, real_app,
                                                                  create_llm_scenario):
        """Completed items produce correct progress_percent in model_progress."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=4,
                results=[
                    {'item_index': 0, 'payload_json': {'rating': 3}},
                    {'item_index': 1, 'payload_json': {'rating': 4}},
                ],
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            mp = body['model_progress']['test-model-1']
            assert mp['completed'] == 2
            assert mp['total'] == 4
            assert mp['progress_percent'] == pytest.approx(50.0)

    def test_LLM_EVAL_PROG_006_error_items_failed_count(self, auth_admin, real_app,
                                                          create_llm_scenario):
        """Error results are counted as 'errors' in model_progress."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=3,
                results=[
                    {'item_index': 0, 'error': 'API key invalid (401)'},
                    {'item_index': 1, 'error': 'Rate limit exceeded'},
                ],
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            mp = body['model_progress']['test-model-1']
            assert mp['errors'] == 2
            assert body['progress']['failed'] == 2

    def test_LLM_EVAL_PROG_007_status_completed(self, auth_admin, real_app,
                                                  create_llm_scenario):
        """Status is 'completed' when all items have successful results."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=2,
                results=[
                    {'item_index': 0, 'payload_json': {'rating': 5}},
                    {'item_index': 1, 'payload_json': {'rating': 4}},
                ],
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            assert body['model_progress']['test-model-1']['status'] == 'completed'

    def test_LLM_EVAL_PROG_008_status_failed(self, auth_admin, real_app,
                                               create_llm_scenario):
        """Status is 'failed' when all items attempted but some have errors and none completed."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=2,
                results=[
                    {'item_index': 0, 'error': 'Auth error 401'},
                    {'item_index': 1, 'error': 'Auth error 401'},
                ],
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            mp = body['model_progress']['test-model-1']
            # errors == total_threads and completed + errors >= total → 'failed'
            assert mp['status'] == 'failed'

    def test_LLM_EVAL_PROG_009_status_pending(self, auth_admin, real_app,
                                                create_llm_scenario):
        """Status is 'pending' when no results exist and no runner is active."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=3,
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            assert body['model_progress']['test-model-1']['status'] == 'pending'

    @patch('services.llm.llm_ai_task_runner.LLMAITaskRunner.is_running', return_value=True)
    def test_LLM_EVAL_PROG_010_status_running_with_active_lock(self, mock_is_running,
                                                                 auth_admin, real_app,
                                                                 create_llm_scenario):
        """Status is 'running' when is_running returns True (lock is held)."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['test-model-1']},
                item_count=3,
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/progress')
            assert response.status_code == 200
            body = response.get_json()

            assert body['model_progress']['test-model-1']['status'] == 'running'


# ===========================================================================
# GET /api/evaluation/llm/result/<result_id>
# ===========================================================================

class TestGetEvaluationResult:
    """Tests for single result retrieval.

    Validates auth, 404 handling, and correct JSON structure from to_dict().
    """

    def test_LLM_EVAL_RES_001_unauthenticated(self, rclient, rdb, rmock_token):
        """Unauthenticated requests must be rejected with 401."""
        response = rclient.get('/api/evaluation/llm/result/1')
        assert response.status_code == 401

    def test_LLM_EVAL_RES_002_not_found(self, auth_admin, real_app, rdb):
        """Non-existent result returns 404."""
        with real_app.app_context():
            response = auth_admin.get('/api/evaluation/llm/result/99999')
            assert response.status_code == 404

    def test_LLM_EVAL_RES_003_valid_result(self, auth_admin, real_app,
                                             create_llm_scenario):
        """Valid result returns correct JSON structure from LLMTaskResult.to_dict()."""
        with real_app.app_context():
            data = create_llm_scenario(
                item_count=1,
                results=[{
                    'item_index': 0,
                    'model_id': 'test-model-1',
                    'task_type': 'evaluation',
                    'payload_json': {'rating': 4, 'reasoning': 'Good quality'},
                }],
            )
            result_id = data['result_ids'][0]

            response = auth_admin.get(f'/api/evaluation/llm/result/{result_id}')
            assert response.status_code == 200
            body = response.get_json()

            # Verify core fields from to_dict(include_raw=False)
            assert body['id'] == result_id
            assert body['model_id'] == 'test-model-1'
            assert body['task_type'] == 'evaluation'
            assert body['payload_json'] == {'rating': 4, 'reasoning': 'Good quality'}
            assert body['error'] is None
            assert 'raw_response' not in body  # include_raw=False
            assert 'created_at' in body
            assert 'updated_at' in body


# ===========================================================================
# POST /api/evaluation/llm/<scenario_id>/start
# ===========================================================================

class TestStartEvaluation:
    """Tests for manual start/retry of LLM evaluations.

    This endpoint is the ONLY path that retries permanent failures by clearing
    error records first. Tests verify auth, error deletion, and async dispatch.
    """

    def test_LLM_EVAL_START_001_unauthenticated(self, rclient, rdb, rmock_token):
        """Unauthenticated requests must be rejected with 401."""
        response = rclient.post('/api/evaluation/llm/1/start')
        assert response.status_code == 401

    def test_LLM_EVAL_START_002_scenario_not_found(self, auth_admin, real_app, rdb):
        """Non-existent scenario returns 404."""
        with real_app.app_context():
            response = auth_admin.post('/api/evaluation/llm/99999/start')
            assert response.status_code == 404

    @patch('services.llm.llm_ai_task_runner.LLMAITaskRunner.run_for_scenario_async')
    @patch('services.llm.llm_access_service.LLMAccessService.user_can_access_model', return_value=True)
    def test_LLM_EVAL_START_003_successful_start(self, mock_access, mock_run,
                                                   auth_admin, real_app,
                                                   create_llm_scenario):
        """Successful start returns success=True and dispatches async runner."""
        with real_app.app_context():
            data = create_llm_scenario()
            sid = data['scenario_id']

            response = auth_admin.post(
                f'/api/evaluation/llm/{sid}/start',
                json={'model_id': 'test-model-1'},
            )
            assert response.status_code == 200
            body = response.get_json()
            assert body['success'] is True
            assert body['scenario_id'] == sid
            assert body['model_id'] == 'test-model-1'

            # Verify the runner was dispatched with correct args
            mock_run.assert_called_once_with(sid, model_ids=['test-model-1'])

    @patch('services.llm.llm_ai_task_runner.LLMAITaskRunner.run_for_scenario_async')
    def test_LLM_EVAL_START_004_error_records_deleted(self, mock_run, auth_admin, real_app,
                                                        create_llm_scenario):
        """Error records are deleted before starting so runner treats items as pending."""
        from db.models.llm_task_result import LLMTaskResult

        with real_app.app_context():
            data = create_llm_scenario(
                item_count=3,
                results=[
                    {'item_index': 0, 'error': 'API key invalid'},
                    {'item_index': 1, 'error': 'Rate limit'},
                    {'item_index': 2, 'payload_json': {'rating': 5}},  # success - should remain
                ],
            )
            sid = data['scenario_id']

            # Confirm error records exist before start
            errors_before = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == sid,
                LLMTaskResult.error.isnot(None),
            ).count()
            assert errors_before == 2

            response = auth_admin.post(f'/api/evaluation/llm/{sid}/start')
            assert response.status_code == 200

            # Error records should be deleted, success record should remain
            errors_after = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == sid,
                LLMTaskResult.error.isnot(None),
            ).count()
            assert errors_after == 0

            success_count = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == sid,
                LLMTaskResult.payload_json.isnot(None),
            ).count()
            assert success_count == 1

    @patch('services.llm.llm_ai_task_runner.LLMAITaskRunner.run_for_scenario_async')
    @patch('services.llm.llm_access_service.LLMAccessService.user_can_access_model', return_value=True)
    def test_LLM_EVAL_START_005_model_id_filters_error_deletion(self, mock_access,
                                                                  mock_run,
                                                                  auth_admin, real_app,
                                                                  create_llm_scenario):
        """When model_id is specified, only errors for THAT model are deleted."""
        from db.models.llm_task_result import LLMTaskResult

        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['model-a', 'model-b']},
                item_count=2,
                results=[
                    {'item_index': 0, 'model_id': 'model-a', 'error': 'Auth error'},
                    {'item_index': 0, 'model_id': 'model-b', 'error': 'Timeout'},
                ],
            )
            sid = data['scenario_id']

            # Start only for model-a
            response = auth_admin.post(
                f'/api/evaluation/llm/{sid}/start',
                json={'model_id': 'model-a'},
            )
            assert response.status_code == 200

            # model-a errors deleted, model-b error remains
            model_a_errors = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == sid,
                LLMTaskResult.model_id == 'model-a',
                LLMTaskResult.error.isnot(None),
            ).count()
            assert model_a_errors == 0

            model_b_errors = LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == sid,
                LLMTaskResult.model_id == 'model-b',
                LLMTaskResult.error.isnot(None),
            ).count()
            assert model_b_errors == 1


# ===========================================================================
# GET /api/evaluation/llm/<scenario_id>/errors
# ===========================================================================

class TestGetEvaluationErrors:
    """Tests for error listing endpoint.

    Returns error details for failed LLM evaluations with optional model_id filter.
    """

    def test_LLM_EVAL_ERR_001_unauthenticated(self, rclient, rdb, rmock_token):
        """Unauthenticated requests must be rejected with 401."""
        response = rclient.get('/api/evaluation/llm/1/errors')
        assert response.status_code == 401

    def test_LLM_EVAL_ERR_002_scenario_not_found(self, auth_admin, real_app, rdb):
        """Non-existent scenario returns 404."""
        with real_app.app_context():
            response = auth_admin.get('/api/evaluation/llm/99999/errors')
            assert response.status_code == 404

    def test_LLM_EVAL_ERR_003_empty_error_list(self, auth_admin, real_app,
                                                 create_llm_scenario):
        """Scenario with no errors returns empty error list."""
        with real_app.app_context():
            data = create_llm_scenario(
                item_count=2,
                results=[
                    {'item_index': 0, 'payload_json': {'rating': 3}},
                    {'item_index': 1, 'payload_json': {'rating': 4}},
                ],
            )
            sid = data['scenario_id']

            response = auth_admin.get(f'/api/evaluation/llm/{sid}/errors')
            assert response.status_code == 200
            body = response.get_json()
            assert body['total_errors'] == 0
            assert body['errors'] == []

    def test_LLM_EVAL_ERR_004_errors_with_model_filter(self, auth_admin, real_app,
                                                         create_llm_scenario):
        """Errors filtered by model_id only return errors for that model."""
        with real_app.app_context():
            data = create_llm_scenario(
                config_json={'llm_evaluators': ['model-a', 'model-b']},
                item_count=2,
                results=[
                    {'item_index': 0, 'model_id': 'model-a', 'error': 'Auth error'},
                    {'item_index': 1, 'model_id': 'model-a', 'error': 'Timeout'},
                    {'item_index': 0, 'model_id': 'model-b', 'error': 'Rate limit'},
                ],
            )
            sid = data['scenario_id']

            # Without filter: all 3 errors
            response_all = auth_admin.get(f'/api/evaluation/llm/{sid}/errors')
            assert response_all.status_code == 200
            assert response_all.get_json()['total_errors'] == 3

            # With filter: only model-a errors
            response_filtered = auth_admin.get(
                f'/api/evaluation/llm/{sid}/errors?model_id=model-a'
            )
            assert response_filtered.status_code == 200
            body = response_filtered.get_json()
            assert body['total_errors'] == 2
            assert body['model_id'] == 'model-a'
            assert all(e['model_id'] == 'model-a' for e in body['errors'])

            # Verify error structure
            err = body['errors'][0]
            assert 'id' in err
            assert 'thread_id' in err
            assert 'item_label' in err
            assert 'error' in err
            assert 'updated_at' in err


# ===========================================================================
# POST /api/evaluation/llm/<scenario_id>/stop
# ===========================================================================

class TestStopEvaluation:
    """Tests for the stop evaluation endpoint.

    Currently a stub (TODO in route), but auth and 404 checks still apply.
    """

    def test_LLM_EVAL_STOP_001_unauthenticated(self, rclient, rdb, rmock_token):
        """Unauthenticated requests must be rejected with 401."""
        response = rclient.post('/api/evaluation/llm/1/stop')
        assert response.status_code == 401

    def test_LLM_EVAL_STOP_002_scenario_not_found(self, auth_admin, real_app, rdb):
        """Non-existent scenario returns 404."""
        with real_app.app_context():
            response = auth_admin.post('/api/evaluation/llm/99999/stop')
            assert response.status_code == 404
