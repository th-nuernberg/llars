"""
Tests for KIASyncService.

Covers GitLab API interaction, pillar availability checking,
file fetching, pillar sync, and sync status reporting.
All HTTP calls are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestKIASyncServiceInit:
    """Tests for KIASyncService initialization."""

    def test_KIAS_001_init_with_token(self, app, app_context):
        """[KIAS-001] Initializes with provided token."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token='test-token')
        assert service.gitlab_token == 'test-token'
        assert service.project_id is None

    def test_KIAS_002_init_from_env(self, app, app_context):
        """[KIAS-002] Falls back to env variable for token."""
        from services.judge.kia_sync_service import KIASyncService
        with patch.dict('os.environ', {'GITLAB_TOKEN': 'env-token'}):
            service = KIASyncService()
            assert service.gitlab_token == 'env-token'

    def test_KIAS_003_init_no_token(self, app, app_context):
        """[KIAS-003] Works without token (public repos)."""
        from services.judge.kia_sync_service import KIASyncService
        with patch.dict('os.environ', {}, clear=True):
            service = KIASyncService()
            assert service.gitlab_token is None

    def test_KIAS_004_base_url_constructed(self, app, app_context):
        """[KIAS-004] Base URL is properly constructed."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token='test')
        assert 'git.informatik.fh-nuernberg.de' in service.base_url
        assert 'v4' in service.base_url


class TestGetHeaders:
    """Tests for KIASyncService._get_headers."""

    def test_KIAS_010_headers_with_token(self, app, app_context):
        """[KIAS-010] Headers include token when provided."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token='my-token')
        headers = service._get_headers()
        assert headers['PRIVATE-TOKEN'] == 'my-token'
        assert 'Content-Type' in headers

    def test_KIAS_011_headers_without_token(self, app, app_context):
        """[KIAS-011] Headers omit token when not provided."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token=None)
        headers = service._get_headers()
        assert 'PRIVATE-TOKEN' not in headers


class TestGetProjectId:
    """Tests for KIASyncService._get_project_id."""

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_020_project_id_success(self, mock_get, app, app_context):
        """[KIAS-020] Successfully fetches project ID."""
        from services.judge.kia_sync_service import KIASyncService
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {'id': 12345}
        mock_get.return_value = mock_resp

        service = KIASyncService(gitlab_token='token')
        pid = service._get_project_id()
        assert pid == 12345

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_021_project_id_cached(self, mock_get, app, app_context):
        """[KIAS-021] Project ID is cached after first fetch."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token='token')
        service.project_id = 999

        pid = service._get_project_id()
        assert pid == 999
        mock_get.assert_not_called()

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_022_project_id_auth_failure(self, mock_get, app, app_context):
        """[KIAS-022] Returns None on auth failure."""
        from services.judge.kia_sync_service import KIASyncService
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        service = KIASyncService(gitlab_token='bad-token')
        assert service._get_project_id() is None

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_023_project_id_not_found(self, mock_get, app, app_context):
        """[KIAS-023] Returns None on 404."""
        from services.judge.kia_sync_service import KIASyncService
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        service = KIASyncService(gitlab_token='token')
        assert service._get_project_id() is None

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_024_project_id_network_error(self, mock_get, app, app_context):
        """[KIAS-024] Returns None on network error."""
        import requests
        from services.judge.kia_sync_service import KIASyncService
        mock_get.side_effect = requests.RequestException('Connection failed')

        service = KIASyncService(gitlab_token='token')
        assert service._get_project_id() is None


class TestCheckPillarAvailability:
    """Tests for KIASyncService.check_pillar_availability."""

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_030_all_pillars_checked(self, mock_get, app, app_context):
        """[KIAS-030] All 5 pillars are checked."""
        from services.judge.kia_sync_service import KIASyncService, SyncStatus

        # First call = project ID, subsequent = pillar checks
        project_resp = MagicMock()
        project_resp.status_code = 200
        project_resp.json.return_value = {'id': 100}

        pillar_resp = MagicMock()
        pillar_resp.status_code = 200
        pillar_resp.json.return_value = [{'name': 'file.json'}]

        # Second page (empty to terminate)
        empty_resp = MagicMock()
        empty_resp.status_code = 200
        empty_resp.json.return_value = []

        mock_get.side_effect = [project_resp] + [pillar_resp, empty_resp] * 5

        service = KIASyncService(gitlab_token='token')
        result = service.check_pillar_availability()

        assert len(result) == 5
        for pillar_num in range(1, 6):
            assert pillar_num in result

    @patch.object(
        __import__('services.judge.kia_sync_service', fromlist=['KIASyncService']).KIASyncService,
        '_get_project_id', return_value=None
    )
    def test_KIAS_031_no_project_id_returns_error(self, mock_pid, app, app_context):
        """[KIAS-031] Returns error status when project ID unavailable."""
        from services.judge.kia_sync_service import KIASyncService, SyncStatus

        service = KIASyncService(gitlab_token='token')
        result = service.check_pillar_availability()

        for status in result.values():
            assert status.status == SyncStatus.ERROR


class TestGetPillarFiles:
    """Tests for KIASyncService.get_pillar_files."""

    def test_KIAS_040_invalid_pillar_returns_empty(self, app, app_context):
        """[KIAS-040] Invalid pillar number returns empty list."""
        from services.judge.kia_sync_service import KIASyncService
        service = KIASyncService(gitlab_token='token')
        assert service.get_pillar_files(99) == []

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_041_no_project_id_returns_empty(self, mock_get, app, app_context):
        """[KIAS-041] No project ID returns empty list."""
        from services.judge.kia_sync_service import KIASyncService
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        service = KIASyncService(gitlab_token='token')
        assert service.get_pillar_files(1) == []


class TestFetchFileContent:
    """Tests for KIASyncService.fetch_file_content."""

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_050_fetch_success(self, mock_get, app, app_context):
        """[KIAS-050] Successfully fetches JSON content."""
        from services.judge.kia_sync_service import KIASyncService

        project_resp = MagicMock()
        project_resp.status_code = 200
        project_resp.json.return_value = {'id': 100}

        file_resp = MagicMock()
        file_resp.status_code = 200
        file_resp.json.return_value = {'conversation_id': 1, 'messages': []}

        mock_get.side_effect = [project_resp, file_resp]

        service = KIASyncService(gitlab_token='token')
        result = service.fetch_file_content('data/file.json')
        assert result is not None
        assert result['conversation_id'] == 1

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_051_fetch_not_found_tries_master(self, mock_get, app, app_context):
        """[KIAS-051] Tries master branch when main returns 404."""
        from services.judge.kia_sync_service import KIASyncService

        project_resp = MagicMock()
        project_resp.status_code = 200
        project_resp.json.return_value = {'id': 100}

        not_found_resp = MagicMock()
        not_found_resp.status_code = 404

        master_resp = MagicMock()
        master_resp.status_code = 200
        master_resp.json.return_value = {'data': 'from master'}

        mock_get.side_effect = [project_resp, not_found_resp, master_resp]

        service = KIASyncService(gitlab_token='token')
        result = service.fetch_file_content('data/file.json')
        assert result is not None

    @patch('services.judge.kia_sync_service.requests.get')
    def test_KIAS_052_fetch_invalid_json(self, mock_get, app, app_context):
        """[KIAS-052] Returns None for invalid JSON."""
        import json
        from services.judge.kia_sync_service import KIASyncService

        project_resp = MagicMock()
        project_resp.status_code = 200
        project_resp.json.return_value = {'id': 100}

        bad_resp = MagicMock()
        bad_resp.status_code = 200
        bad_resp.json.side_effect = json.JSONDecodeError('', '', 0)

        mock_get.side_effect = [project_resp, bad_resp]

        service = KIASyncService(gitlab_token='token')
        assert service.fetch_file_content('bad.json') is None


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_KIAS_060_sync_result_defaults(self, app, app_context):
        """[KIAS-060] SyncResult has correct defaults."""
        from services.judge.kia_sync_service import SyncResult
        result = SyncResult(success=False, pillar_number=1)
        assert result.files_processed == 0
        assert result.threads_created == 0
        assert result.errors == []

    def test_KIAS_061_pillar_status_defaults(self, app, app_context):
        """[KIAS-061] PillarStatus has correct defaults."""
        from services.judge.kia_sync_service import PillarStatus, SyncStatus
        status = PillarStatus(pillar_number=1, pillar_name='Test', status=SyncStatus.AVAILABLE)
        assert status.file_count == 0
        assert status.thread_count == 0
        assert status.last_sync is None


class TestPillarConfig:
    """Tests for PILLAR_CONFIG constant."""

    def test_KIAS_070_all_pillars_defined(self, app, app_context):
        """[KIAS-070] All 5 pillars are configured."""
        from services.judge.kia_sync_service import PILLAR_CONFIG
        assert len(PILLAR_CONFIG) == 5
        for i in range(1, 6):
            assert i in PILLAR_CONFIG
            assert 'name' in PILLAR_CONFIG[i]
            assert 'path' in PILLAR_CONFIG[i]


class TestGetKiaSyncService:
    """Tests for singleton factory."""

    def test_KIAS_080_singleton_creation(self, app, app_context):
        """[KIAS-080] Creates singleton instance."""
        from services.judge import kia_sync_service
        # Reset singleton
        kia_sync_service._sync_service = None

        service = kia_sync_service.get_kia_sync_service('test-token')
        assert service is not None
        assert service.gitlab_token == 'test-token'

        # Cleanup
        kia_sync_service._sync_service = None

    def test_KIAS_081_singleton_reuse(self, app, app_context):
        """[KIAS-081] Returns same instance on repeated calls."""
        from services.judge import kia_sync_service
        kia_sync_service._sync_service = None

        svc1 = kia_sync_service.get_kia_sync_service('token')
        svc2 = kia_sync_service.get_kia_sync_service()
        assert svc1 is svc2

        # Cleanup
        kia_sync_service._sync_service = None
