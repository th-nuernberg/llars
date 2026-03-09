"""
Route Tests for Judge (LLM-as-Judge) API
==========================================

Tests for app/routes/judge/ (session_routes.py, session_control_routes.py,
comparison_routes.py, statistics_routes.py).
Covers: Session CRUD, start/pause/delete, comparison modes, statistics.

Uses real blueprints with mocked OIDC token validation.
Prefix: ROUTE_JUDGE
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers: seed comparison permissions
# ---------------------------------------------------------------------------

@pytest.fixture
def seed_comparison_perms(rdb, real_app):
    """Seed comparison-related permissions needed by judge routes."""
    from db.models.permission import Permission, Role, RolePermission

    with real_app.app_context():
        perms_data = [
            ('feature:comparison:view', 'View Comparisons', 'feature'),
            ('feature:comparison:edit', 'Edit Comparisons', 'feature'),
        ]
        for perm_key, display, category in perms_data:
            perm = Permission.query.filter_by(permission_key=perm_key).first()
            if not perm:
                perm = Permission(
                    permission_key=perm_key,
                    display_name=display,
                    category=category,
                    description=display
                )
                rdb.session.add(perm)
        rdb.session.commit()

        # Grant to admin
        admin_role = Role.query.filter_by(role_name='admin').first()
        if admin_role:
            for perm_key in ('feature:comparison:view', 'feature:comparison:edit'):
                perm = Permission.query.filter_by(permission_key=perm_key).first()
                existing = RolePermission.query.filter_by(
                    role_id=admin_role.id, permission_id=perm.id
                ).first()
                if not existing:
                    rdb.session.add(RolePermission(role_id=admin_role.id, permission_id=perm.id))
        rdb.session.commit()


# ---------------------------------------------------------------------------
# GET /api/judge/comparison-modes
# ---------------------------------------------------------------------------

class TestComparisonModes:
    """Tests for GET /api/judge/comparison-modes"""

    def test_ROUTE_JUDGE_MODES_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/comparison-modes')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_MODES_002_forbidden_evaluator(self, auth_user, real_app,
                                                        seed_comparison_perms):
        with real_app.app_context():
            response = auth_user.get('/api/judge/comparison-modes')
            assert response.status_code == 403

    def test_ROUTE_JUDGE_MODES_003_admin_success(self, auth_admin, real_app,
                                                  seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.get('/api/judge/comparison-modes')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 3
            mode_ids = [m['id'] for m in data]
            assert 'pillar_sample' in mode_ids
            assert 'round_robin' in mode_ids
            assert 'free_for_all' in mode_ids


# ---------------------------------------------------------------------------
# GET /api/judge/sessions (List sessions)
# ---------------------------------------------------------------------------

class TestListSessions:
    """Tests for GET /api/judge/sessions"""

    def test_ROUTE_JUDGE_LIST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/sessions')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_LIST_002_forbidden_evaluator(self, auth_user, real_app,
                                                       seed_comparison_perms):
        with real_app.app_context():
            response = auth_user.get('/api/judge/sessions')
            assert response.status_code == 403

    def test_ROUTE_JUDGE_LIST_003_admin_empty(self, auth_admin, real_app,
                                               seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.get('/api/judge/sessions')
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 0


# ---------------------------------------------------------------------------
# POST /api/judge/sessions (Create session)
# ---------------------------------------------------------------------------

class TestCreateSession:
    """Tests for POST /api/judge/sessions"""

    def test_ROUTE_JUDGE_CREATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/judge/sessions', json={'name': 'Test'})
        assert response.status_code == 401

    def test_ROUTE_JUDGE_CREATE_002_forbidden_evaluator(self, auth_user, real_app,
                                                         seed_comparison_perms):
        with real_app.app_context():
            response = auth_user.post('/api/judge/sessions', json={'name': 'Test'})
            assert response.status_code == 403

    def test_ROUTE_JUDGE_CREATE_003_admin_success(self, auth_admin, real_app,
                                                   seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/sessions', json={
                'session_name': 'Test Session',
                'pillar_ids': [],
                'comparison_mode': 'pillar_sample'
            })
            assert response.status_code == 201
            data = response.get_json()
            assert 'session_id' in data
            assert data['name'] == 'Test Session'
            assert data['status'] == 'created'

    def test_ROUTE_JUDGE_CREATE_004_default_name(self, auth_admin, real_app,
                                                  seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/sessions', json={})
            assert response.status_code == 201
            data = response.get_json()
            assert 'Evaluation' in data['name']

    def test_ROUTE_JUDGE_CREATE_005_with_config(self, auth_admin, real_app,
                                                 seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/sessions', json={
                'name': 'Config Session',
                'comparison_mode': 'free_for_all',
                'position_swap': False,
                'worker_count': 3,
                'repetitions_per_pair': 2,
            })
            assert response.status_code == 201
            data = response.get_json()
            assert data['comparison_mode'] == 'free_for_all'


# ---------------------------------------------------------------------------
# GET /api/judge/sessions/<id> (Get session)
# ---------------------------------------------------------------------------

class TestGetSession:
    """Tests for GET /api/judge/sessions/<session_id>"""

    def test_ROUTE_JUDGE_GETSESS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/sessions/1')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_GETSESS_002_not_found(self, auth_admin, real_app,
                                                 seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.get('/api/judge/sessions/99999')
            assert response.status_code == 404

    def test_ROUTE_JUDGE_GETSESS_003_success(self, auth_admin, real_app,
                                              seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Get Session Test',
                config_json={'pillars': [1, 2]},
                status=JudgeSessionStatus.CREATED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.get(f'/api/judge/sessions/{session.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['name'] == 'Get Session Test'
            assert data['status'] == 'created'


# ---------------------------------------------------------------------------
# DELETE /api/judge/sessions/<id> (Delete session)
# ---------------------------------------------------------------------------

class TestDeleteSession:
    """Tests for DELETE /api/judge/sessions/<session_id>"""

    def test_ROUTE_JUDGE_DEL_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/judge/sessions/1')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_DEL_002_not_found(self, auth_admin, real_app,
                                            seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.delete('/api/judge/sessions/99999')
            assert response.status_code == 404

    def test_ROUTE_JUDGE_DEL_003_success(self, auth_admin, real_app,
                                          seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Delete Test',
                config_json={},
                status=JudgeSessionStatus.CREATED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()
            sid = session.id

            response = auth_admin.delete(f'/api/judge/sessions/{sid}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['session_id'] == sid

            assert JudgeSession.query.get(sid) is None


# ---------------------------------------------------------------------------
# POST /api/judge/sessions/<id>/pause (Pause session)
# ---------------------------------------------------------------------------

class TestPauseSession:
    """Tests for POST /api/judge/sessions/<session_id>/pause"""

    def test_ROUTE_JUDGE_PAUSE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/judge/sessions/1/pause')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_PAUSE_002_not_found(self, auth_admin, real_app,
                                              seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/sessions/99999/pause')
            assert response.status_code == 404

    @patch('workers.judge_worker_pool.stop_judge_worker_pool')
    def test_ROUTE_JUDGE_PAUSE_003_not_running(self, mock_stop, auth_admin, real_app,
                                                seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Pause Test',
                config_json={},
                status=JudgeSessionStatus.CREATED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.post(f'/api/judge/sessions/{session.id}/pause')
            assert response.status_code == 400

    @patch('workers.judge_worker_pool.stop_judge_worker_pool')
    def test_ROUTE_JUDGE_PAUSE_004_success(self, mock_stop, auth_admin, real_app,
                                            seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Pause Success',
                config_json={},
                status=JudgeSessionStatus.RUNNING,
                total_comparisons=10,
                completed_comparisons=3,
                started_at=datetime.utcnow(),
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.post(f'/api/judge/sessions/{session.id}/pause')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'paused'


# ---------------------------------------------------------------------------
# POST /api/judge/sessions/<id>/start (Start session)
# ---------------------------------------------------------------------------

class TestStartSession:
    """Tests for POST /api/judge/sessions/<session_id>/start"""

    def test_ROUTE_JUDGE_START_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/judge/sessions/1/start')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_START_002_not_found(self, auth_admin, real_app,
                                              seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/sessions/99999/start')
            assert response.status_code == 404

    @patch('workers.judge_worker_pool.trigger_judge_worker_pool')
    def test_ROUTE_JUDGE_START_003_wrong_status(self, mock_trigger, auth_admin, real_app,
                                                 seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Start Wrong Status',
                config_json={},
                status=JudgeSessionStatus.COMPLETED,
                total_comparisons=10,
                completed_comparisons=10,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.post(f'/api/judge/sessions/{session.id}/start')
            assert response.status_code == 400

    @patch('workers.judge_worker_pool.trigger_judge_worker_pool')
    def test_ROUTE_JUDGE_START_004_success(self, mock_trigger, auth_admin, real_app,
                                            seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Start Test',
                config_json={'worker_count': 2},
                status=JudgeSessionStatus.QUEUED,
                total_comparisons=5,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.post(f'/api/judge/sessions/{session.id}/start')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'running'
            assert data['worker_count'] == 2


# ---------------------------------------------------------------------------
# GET /api/judge/sessions/<id>/results (Session results)
# ---------------------------------------------------------------------------

class TestSessionResults:
    """Tests for GET /api/judge/sessions/<session_id>/results"""

    def test_ROUTE_JUDGE_RESULTS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/sessions/1/results')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_RESULTS_002_not_found(self, auth_admin, real_app,
                                                seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.get('/api/judge/sessions/99999/results')
            # get_or_404 raises werkzeug NotFound, error handler maps to 500
            assert response.status_code in (404, 500)

    def test_ROUTE_JUDGE_RESULTS_003_success_empty(self, auth_admin, real_app,
                                                    seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Results Test',
                config_json={},
                status=JudgeSessionStatus.COMPLETED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.get(f'/api/judge/sessions/{session.id}/results')
            assert response.status_code == 200
            data = response.get_json()
            assert data['session_id'] == session.id
            assert 'pillar_metrics' in data
            assert 'win_matrix' in data


# ---------------------------------------------------------------------------
# GET /api/judge/sessions/<id>/statistics (Pillar statistics)
# ---------------------------------------------------------------------------

class TestPillarStatistics:
    """Tests for GET /api/judge/sessions/<session_id>/statistics"""

    def test_ROUTE_JUDGE_STATS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/sessions/1/statistics')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_STATS_002_success(self, auth_admin, real_app,
                                            seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Stats Test',
                config_json={},
                status=JudgeSessionStatus.COMPLETED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.get(f'/api/judge/sessions/{session.id}/statistics')
            assert response.status_code == 200
            data = response.get_json()
            assert 'matrix' in data
            assert 'overall' in data
            assert 'pillar_ranking' in data


# ---------------------------------------------------------------------------
# GET /api/judge/sessions/<id>/queue (Session queue)
# ---------------------------------------------------------------------------

class TestSessionQueue:
    """Tests for GET /api/judge/sessions/<session_id>/queue"""

    def test_ROUTE_JUDGE_QUEUE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/judge/sessions/1/queue')
        assert response.status_code == 401

    def test_ROUTE_JUDGE_QUEUE_002_not_found(self, auth_admin, real_app,
                                              seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.get('/api/judge/sessions/99999/queue')
            assert response.status_code == 404

    def test_ROUTE_JUDGE_QUEUE_003_success(self, auth_admin, real_app,
                                            seed_comparison_perms):
        with real_app.app_context():
            from db.database import db
            from db.tables import JudgeSession, JudgeSessionStatus

            session = JudgeSession(
                user_id='admin',
                name='Queue Test',
                config_json={},
                status=JudgeSessionStatus.QUEUED,
                total_comparisons=0,
                completed_comparisons=0,
            )
            db.session.add(session)
            db.session.commit()

            response = auth_admin.get(f'/api/judge/sessions/{session.id}/queue')
            assert response.status_code == 200
            data = response.get_json()
            assert 'running' in data
            assert 'pending' in data
            assert 'stats' in data


# ---------------------------------------------------------------------------
# POST /api/judge/estimate (Estimate comparisons)
# ---------------------------------------------------------------------------

class TestEstimateComparisons:
    """Tests for POST /api/judge/estimate"""

    def test_ROUTE_JUDGE_EST_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/judge/estimate', json={'pillar_ids': [1, 2]})
        assert response.status_code == 401

    def test_ROUTE_JUDGE_EST_002_no_pillars(self, auth_admin, real_app,
                                             seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/estimate', json={'pillar_ids': []})
            assert response.status_code == 400

    def test_ROUTE_JUDGE_EST_003_no_threads(self, auth_admin, real_app,
                                             seed_comparison_perms):
        with real_app.app_context():
            response = auth_admin.post('/api/judge/estimate', json={
                'pillar_ids': [1, 2],
                'comparison_mode': 'pillar_sample'
            })
            assert response.status_code == 200
            data = response.get_json()
            assert data['total_comparisons'] == 0
