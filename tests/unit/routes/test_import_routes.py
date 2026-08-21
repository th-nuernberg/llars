"""
Route Tests for Data Import API
=================================

Tests for app/routes/data_import/import_routes.py (755 lines).
Covers: formats, upload, session, transform, validate, execute, from-data,
        delete-session, AI endpoints.

Uses real blueprints with mocked OIDC token validation.
"""

import io
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Formats
# ---------------------------------------------------------------------------

class TestGetFormats:
    """Tests for GET /api/import/formats"""

    def test_IMPORT_FORMATS_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/import/formats')
        assert response.status_code == 401

    def test_IMPORT_FORMATS_002_success(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.get('/api/import/formats')
            assert response.status_code == 200
            data = response.get_json()
            assert 'formats' in data
            assert 'task_types' in data
            assert isinstance(data['formats'], list)
            assert isinstance(data['task_types'], list)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class TestUploadFile:
    """Tests for POST /api/import/upload"""

    def test_IMPORT_UPLOAD_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/upload')
        assert response.status_code == 401

    def test_IMPORT_UPLOAD_002_evaluator_forbidden(self, auth_user, real_app):
        """Evaluators lack data:import permission."""
        with real_app.app_context():
            response = auth_user.post('/api/import/upload',
                                      data={},
                                      content_type='multipart/form-data')
            assert response.status_code == 403

    def test_IMPORT_UPLOAD_003_no_file(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/upload',
                                       data={},
                                       content_type='multipart/form-data')
            assert response.status_code == 400

    def test_IMPORT_UPLOAD_004_empty_filename(self, auth_admin, real_app):
        with real_app.app_context():
            data = {'file': (io.BytesIO(b''), '')}
            response = auth_admin.post('/api/import/upload',
                                       data=data,
                                       content_type='multipart/form-data')
            assert response.status_code == 400

    @patch('routes.data_import.import_routes.import_service')
    def test_IMPORT_UPLOAD_005_success(self, mock_svc, auth_admin, real_app):
        with real_app.app_context():
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {
                'session_id': 'test-123',
                'status': 'analyzed',
                'detected_format': 'csv',
                'item_count': 5,
            }
            mock_svc.create_session.return_value = mock_session
            mock_svc.analyze_file.return_value = mock_session

            csv_content = b'id,text\n1,hello\n2,world'
            data = {'file': (io.BytesIO(csv_content), 'test.csv')}
            response = auth_admin.post('/api/import/upload',
                                       data=data,
                                       content_type='multipart/form-data')
            assert response.status_code == 201
            result = response.get_json()
            assert result['session_id'] == 'test-123'


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class TestGetSession:
    """Tests for GET /api/import/session/<id>"""

    def test_IMPORT_SESSION_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/import/session/abc123')
        assert response.status_code == 401

    @patch('routes.data_import.import_routes.import_service')
    def test_IMPORT_SESSION_002_not_found(self, mock_svc, auth_user, real_app):
        with real_app.app_context():
            mock_svc.get_session.return_value = None
            response = auth_user.get('/api/import/session/nonexistent')
            assert response.status_code == 400

    @patch('routes.data_import.import_routes.import_service')
    def test_IMPORT_SESSION_003_success(self, mock_svc, auth_user, real_app):
        with real_app.app_context():
            mock_session = MagicMock()
            mock_session.to_dict.return_value = {
                'session_id': 'sess-123',
                'status': 'analyzed',
                'detected_format': 'json',
            }
            mock_svc.get_session.return_value = mock_session

            response = auth_user.get('/api/import/session/sess-123')
            assert response.status_code == 200
            data = response.get_json()
            assert data['session_id'] == 'sess-123'


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

class TestTransformData:
    """Tests for POST /api/import/transform"""

    def test_IMPORT_TRANSFORM_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/transform',
                                json={'session_id': 'x'})
        assert response.status_code == 401

    def test_IMPORT_TRANSFORM_002_evaluator_forbidden(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/import/transform',
                                      json={'session_id': 'x'})
            assert response.status_code == 403

    def test_IMPORT_TRANSFORM_003_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/transform',
                                       data='',
                                       content_type='application/json')
            # Empty JSON body causes BadRequest (400) or server error (500) via error handler
            assert response.status_code in (400, 500)

    def test_IMPORT_TRANSFORM_004_missing_session_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/transform',
                                       json={'options': {}})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

class TestValidateData:
    """Tests for POST /api/import/validate"""

    def test_IMPORT_VALIDATE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/validate',
                                json={'session_id': 'x'})
        assert response.status_code == 401

    def test_IMPORT_VALIDATE_002_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/validate',
                                       data='',
                                       content_type='application/json')
            assert response.status_code in (400, 500)

    def test_IMPORT_VALIDATE_003_missing_session_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/validate',
                                       json={'options': {}})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Execute Import
# ---------------------------------------------------------------------------

class TestExecuteImport:
    """Tests for POST /api/import/execute"""

    def test_IMPORT_EXECUTE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/execute',
                                json={'session_id': 'x'})
        assert response.status_code == 401

    def test_IMPORT_EXECUTE_002_evaluator_forbidden(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/import/execute',
                                      json={'session_id': 'x'})
            assert response.status_code == 403

    def test_IMPORT_EXECUTE_003_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/execute',
                                       data='',
                                       content_type='application/json')
            assert response.status_code in (400, 500)

    def test_IMPORT_EXECUTE_004_missing_session_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/execute',
                                       json={'task_type': 'rating'})
            assert response.status_code == 400

    def test_IMPORT_EXECUTE_005_invalid_task_type(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/execute',
                                       json={'session_id': 'x', 'task_type': 'invalid_type'})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# Delete Session
# ---------------------------------------------------------------------------

class TestDeleteSession:
    """Tests for DELETE /api/import/session/<id>"""

    def test_IMPORT_DELETE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.delete('/api/import/session/abc123')
        assert response.status_code == 401

    def test_IMPORT_DELETE_002_evaluator_forbidden(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.delete('/api/import/session/abc123')
            assert response.status_code == 403

    @patch('routes.data_import.import_routes.import_service')
    def test_IMPORT_DELETE_003_not_found(self, mock_svc, auth_admin, real_app):
        with real_app.app_context():
            mock_svc.delete_session.return_value = False
            response = auth_admin.delete('/api/import/session/nonexistent')
            assert response.status_code == 400

    @patch('routes.data_import.import_routes.import_service')
    def test_IMPORT_DELETE_004_success(self, mock_svc, auth_admin, real_app):
        with real_app.app_context():
            mock_svc.delete_session.return_value = True
            response = auth_admin.delete('/api/import/session/sess-123')
            assert response.status_code == 200
            data = response.get_json()
            assert data['deleted'] is True


# ---------------------------------------------------------------------------
# Import from Data
# ---------------------------------------------------------------------------

class TestImportFromData:
    """Tests for POST /api/import/from-data"""

    def test_IMPORT_FROMDATA_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/from-data',
                                json={'data': [{'text': 'hello'}]})
        assert response.status_code == 401

    def test_IMPORT_FROMDATA_002_evaluator_forbidden(self, auth_user, real_app):
        with real_app.app_context():
            response = auth_user.post('/api/import/from-data',
                                      json={'data': [{'text': 'hello'}]})
            assert response.status_code == 403

    def test_IMPORT_FROMDATA_003_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/from-data',
                                       data='',
                                       content_type='application/json')
            assert response.status_code in (400, 500)

    def test_IMPORT_FROMDATA_004_missing_data(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/from-data',
                                       json={'scenario_id': 1})
            assert response.status_code == 400

    def test_IMPORT_FROMDATA_005_empty_data_array(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/from-data',
                                       json={'data': []})
            assert response.status_code == 400

    def test_IMPORT_FROMDATA_006_missing_scenario_id(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/from-data',
                                       json={'data': [{'text': 'hello'}]})
            assert response.status_code == 400


# ---------------------------------------------------------------------------
# AI Analyze
# ---------------------------------------------------------------------------

class TestAIAnalyze:
    """Tests for POST /api/import/ai/analyze"""

    def test_IMPORT_AI_ANALYZE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.post('/api/import/ai/analyze',
                                json={'session_id': 'x'})
        assert response.status_code == 401

    def test_IMPORT_AI_ANALYZE_002_empty_body(self, auth_admin, real_app):
        with real_app.app_context():
            response = auth_admin.post('/api/import/ai/analyze',
                                       data='',
                                       content_type='application/json')
            assert response.status_code in (400, 500)


# ---------------------------------------------------------------------------
# Sample
# ---------------------------------------------------------------------------

class TestGetSample:
    """Tests for GET /api/import/session/<id>/sample"""

    def test_IMPORT_SAMPLE_001_unauthenticated(self, rclient, rdb, rmock_token):
        response = rclient.get('/api/import/session/abc123/sample')
        assert response.status_code == 401
