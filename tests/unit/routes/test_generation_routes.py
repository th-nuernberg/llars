"""
Route Tests for Generation API
================================

Tests for app/routes/generation/generation_routes.py.
Covers: Job CRUD, job lifecycle (start, pause, cancel), auth checks.

Uses real blueprints with mocked OIDC token validation.
Service-layer calls are mocked since they depend on external LLM providers.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime


def _make_mock_job(job_id=1, name='Test Job', status='created', created_by='admin'):
    """Create a mock GenerationJob object."""
    job = MagicMock()
    job.id = job_id
    job.name = name
    job.status = status
    job.created_by = created_by
    job.to_dict.return_value = {
        'id': job_id,
        'name': name,
        'status': status,
        'created_by': created_by,
        'config': {},
        'created_at': datetime.utcnow().isoformat(),
    }
    return job


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------

class TestGenerationHealth:
    """Tests for GET /api/generation/health"""

    def test_ROUTE_GEN_HEALTH_001_public(self, rclient, rdb, rmock_token):
        """Health endpoint is public."""
        response = rclient.get('/api/generation/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['service'] == 'generation'


# ---------------------------------------------------------------------------
# Create Job
# ---------------------------------------------------------------------------

class TestCreateJob:
    """Tests for POST /api/generation/jobs"""

    def test_ROUTE_GEN_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/generation/jobs', json={
            'name': 'Test', 'config': {}
        })
        assert response.status_code == 401

    def test_ROUTE_GEN_CREATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/generation/jobs', json={
                'name': 'Test', 'config': {}
            })
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.start_job')
    @patch('services.generation.BatchGenerationService.create_job')
    def test_ROUTE_GEN_CREATE_003_missing_name(self, mock_create, mock_start,
                                                auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs', json={
                'config': {'sources': {}}
            })
            assert response.status_code == 400

    @patch('services.generation.BatchGenerationService.start_job')
    @patch('services.generation.BatchGenerationService.create_job')
    def test_ROUTE_GEN_CREATE_004_missing_config(self, mock_create, mock_start,
                                                  auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs', json={
                'name': 'Test Job'
            })
            assert response.status_code == 400

    @patch('services.generation.BatchGenerationService.start_job')
    @patch('services.generation.BatchGenerationService.create_job')
    def test_ROUTE_GEN_CREATE_005_success(self, mock_create, mock_start,
                                           auth_admin, real_app):
        mock_job = _make_mock_job()
        mock_create.return_value = mock_job
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs', json={
                'name': 'New Generation Job',
                'config': {'sources': {'type': 'scenario', 'scenario_id': 1}},
                'auto_start': False,
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['success'] is True
            assert data['job']['name'] == 'Test Job'

    @patch('services.generation.BatchGenerationService.start_job')
    @patch('services.generation.BatchGenerationService.create_job')
    def test_ROUTE_GEN_CREATE_006_no_auto_start(self, mock_create, mock_start,
                                                 auth_admin, real_app):
        """When auto_start=False, start_job should not be called."""
        mock_job = _make_mock_job()
        mock_create.return_value = mock_job
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs', json={
                'name': 'No Auto Start Job',
                'config': {'sources': {'type': 'scenario'}},
                'auto_start': False,
            })
            assert response.status_code == 201
            mock_start.assert_not_called()


# ---------------------------------------------------------------------------
# List Jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    """Tests for GET /api/generation/jobs"""

    def test_ROUTE_GEN_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/generation/jobs')
        assert response.status_code == 401

    def test_ROUTE_GEN_LIST_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/generation/jobs')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.get_jobs_for_user')
    def test_ROUTE_GEN_LIST_003_success(self, mock_list, auth_admin, real_app):
        mock_list.return_value = [
            {'id': 1, 'name': 'Job 1', 'status': 'completed'},
            {'id': 2, 'name': 'Job 2', 'status': 'running'},
        ]
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['total'] == 2

    @patch('services.generation.BatchGenerationService.get_jobs_for_user')
    def test_ROUTE_GEN_LIST_004_empty(self, mock_list, auth_admin, real_app):
        mock_list.return_value = []
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs')
            assert response.status_code == 200
            data = response.get_json()
            assert data['total'] == 0


# ---------------------------------------------------------------------------
# Get Job
# ---------------------------------------------------------------------------

class TestGetJob:
    """Tests for GET /api/generation/jobs/<id>"""

    def test_ROUTE_GEN_GET_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/generation/jobs/1')
        assert response.status_code == 401

    def test_ROUTE_GEN_GET_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/generation/jobs/1')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.get_job_status')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_GET_003_success(self, mock_owner, mock_status, auth_admin, real_app):
        mock_owner.return_value = None  # No exception = owner check passes
        mock_status.return_value = {
            'id': 1, 'name': 'Test Job', 'status': 'completed'
        }
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs/1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['job']['name'] == 'Test Job'

    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_GET_004_not_found(self, mock_owner, auth_admin, real_app):
        from decorators.error_handler import NotFoundError
        mock_owner.side_effect = NotFoundError("Job not found")
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs/99999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete Job
# ---------------------------------------------------------------------------

class TestDeleteJob:
    """Tests for DELETE /api/generation/jobs/<id>"""

    def test_ROUTE_GEN_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/generation/jobs/1')
        assert response.status_code == 401

    def test_ROUTE_GEN_DELETE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/generation/jobs/1')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.delete_job')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_DELETE_003_success(self, mock_owner, mock_delete, auth_admin, real_app):
        mock_owner.return_value = None
        mock_delete.return_value = None
        with real_app.app_context():
            response = auth_admin.delete('/api/generation/jobs/1')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True

    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_DELETE_004_not_found(self, mock_owner, auth_admin, real_app):
        from decorators.error_handler import NotFoundError
        mock_owner.side_effect = NotFoundError("Job not found")
        with real_app.app_context():
            response = auth_admin.delete('/api/generation/jobs/99999')
            assert response.status_code == 404


# ---------------------------------------------------------------------------
# Start Job
# ---------------------------------------------------------------------------

class TestStartJob:
    """Tests for POST /api/generation/jobs/<id>/start"""

    def test_ROUTE_GEN_START_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/generation/jobs/1/start')
        assert response.status_code == 401

    def test_ROUTE_GEN_START_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/generation/jobs/1/start')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.start_job')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_START_003_success(self, mock_owner, mock_start, auth_admin, real_app):
        import sys
        mock_main = MagicMock()
        mock_main.socketio = MagicMock()
        sys.modules['main'] = mock_main
        try:
            mock_owner.return_value = None
            mock_start.return_value = _make_mock_job(status='running')
            with real_app.app_context():
                response = auth_admin.post('/api/generation/jobs/1/start')
                assert response.status_code == 200
                data = response.get_json()
                assert data['success'] is True
        finally:
            del sys.modules['main']


# ---------------------------------------------------------------------------
# Pause Job
# ---------------------------------------------------------------------------

class TestPauseJob:
    """Tests for POST /api/generation/jobs/<id>/pause"""

    def test_ROUTE_GEN_PAUSE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/generation/jobs/1/pause')
        assert response.status_code == 401

    def test_ROUTE_GEN_PAUSE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/generation/jobs/1/pause')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.pause_job')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_PAUSE_003_success(self, mock_owner, mock_pause, auth_admin, real_app):
        mock_owner.return_value = None
        mock_pause.return_value = _make_mock_job(status='paused')
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs/1/pause')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Cancel Job
# ---------------------------------------------------------------------------

class TestCancelJob:
    """Tests for POST /api/generation/jobs/<id>/cancel"""

    def test_ROUTE_GEN_CANCEL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/generation/jobs/1/cancel')
        assert response.status_code == 401

    def test_ROUTE_GEN_CANCEL_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/generation/jobs/1/cancel')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.cancel_job')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_CANCEL_003_success(self, mock_owner, mock_cancel, auth_admin, real_app):
        mock_owner.return_value = None
        mock_cancel.return_value = _make_mock_job(status='cancelled')
        with real_app.app_context():
            response = auth_admin.post('/api/generation/jobs/1/cancel')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Job Outputs
# ---------------------------------------------------------------------------

class TestGetJobOutputs:
    """Tests for GET /api/generation/jobs/<id>/outputs"""

    def test_ROUTE_GEN_OUTPUTS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/generation/jobs/1/outputs')
        assert response.status_code == 401

    def test_ROUTE_GEN_OUTPUTS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/generation/jobs/1/outputs')
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.get_job_outputs')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_OUTPUTS_003_success(self, mock_owner, mock_outputs, auth_admin, real_app):
        mock_owner.return_value = None
        mock_outputs.return_value = {
            'outputs': [{'id': 1, 'status': 'completed'}],
            'total': 1,
            'page': 1,
            'per_page': 50,
        }
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs/1/outputs')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True


# ---------------------------------------------------------------------------
# Job Statistics
# ---------------------------------------------------------------------------

class TestGetJobStatistics:
    """Tests for GET /api/generation/jobs/<id>/statistics"""

    def test_ROUTE_GEN_STATS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/generation/jobs/1/statistics')
        assert response.status_code == 401

    def test_ROUTE_GEN_STATS_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/generation/jobs/1/statistics')
            assert response.status_code == 403

    @patch('services.generation.OutputExportService.get_job_statistics')
    @patch('auth.access_control.require_generation_job_owner')
    def test_ROUTE_GEN_STATS_003_success(self, mock_owner, mock_stats, auth_admin, real_app):
        mock_owner.return_value = None
        mock_stats.return_value = {
            'total_outputs': 10,
            'completed': 8,
            'failed': 2,
        }
        with real_app.app_context():
            response = auth_admin.get('/api/generation/jobs/1/statistics')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['statistics']['total_outputs'] == 10


# ---------------------------------------------------------------------------
# Cost Estimation
# ---------------------------------------------------------------------------

class TestEstimateCost:
    """Tests for POST /api/generation/estimate"""

    def test_ROUTE_GEN_ESTIMATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/generation/estimate',
                                json={'config': {}})
        assert response.status_code == 401

    def test_ROUTE_GEN_ESTIMATE_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/generation/estimate',
                                      json={'config': {}})
            assert response.status_code == 403

    @patch('services.generation.BatchGenerationService.estimate_cost')
    def test_ROUTE_GEN_ESTIMATE_003_missing_config(self, mock_est, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/generation/estimate', json={})
            assert response.status_code == 400

    @patch('services.generation.BatchGenerationService.estimate_cost')
    def test_ROUTE_GEN_ESTIMATE_004_success(self, mock_est, auth_admin, real_app):
        mock_est.return_value = {
            'total_cost': 0.50,
            'total_outputs': 10,
        }
        with real_app.app_context():
            response = auth_admin.post('/api/generation/estimate', json={
                'config': {'sources': {'type': 'scenario'}, 'llm_models': ['gpt-4']}
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['estimate']['total_cost'] == 0.50


# ---------------------------------------------------------------------------
# Max Parallel Settings
# ---------------------------------------------------------------------------

class TestGetMaxParallel:
    """Tests for GET /api/generation/settings/max-parallel"""

    def test_ROUTE_GEN_MAXPAR_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/generation/settings/max-parallel')
        assert response.status_code == 401

    def test_ROUTE_GEN_MAXPAR_002_forbidden_evaluator(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/generation/settings/max-parallel')
            assert response.status_code == 403

    def test_ROUTE_GEN_MAXPAR_003_success(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.get('/api/generation/settings/max-parallel')
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert isinstance(data['max_parallel'], int)
            assert 1 <= data['max_parallel'] <= 16
