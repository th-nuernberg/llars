"""
Tests for auth/access_control.py - IDOR prevention helpers.

Tests cover:
- Admin bypass for all 5 functions
- Owner/member access grants
- Forbidden access for unauthorized users
- NotFoundError for missing resources
"""

import pytest
from unittest.mock import MagicMock, patch

from decorators.error_handler import ForbiddenError, NotFoundError


class MockUser:
    """Minimal user mock."""
    def __init__(self, username='testuser', user_id=42, groups=None):
        self.username = username
        self.id = user_id
        self.groups = groups or []


# =============================================================================
# require_scenario_membership
# =============================================================================


class TestRequireScenarioMembership:

    @patch('decorators.permission_decorator.has_role', return_value=True)
    def test_AC_S01_admin_bypass(self, mock_has_role):
        from auth.access_control import require_scenario_membership
        user = MockUser()
        require_scenario_membership(999, user)
        mock_has_role.assert_called_once_with(user, 'admin')

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_S02_creator_access(self, mock_role):
        from auth.access_control import require_scenario_membership
        scenario = MagicMock()
        scenario.created_by = 'testuser'
        with patch('db.models.RatingScenarios') as mock_scenarios:
            mock_scenarios.query.get.return_value = scenario
            user = MockUser(username='testuser')
            require_scenario_membership(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_S03_member_access(self, mock_role):
        from auth.access_control import require_scenario_membership
        scenario = MagicMock()
        scenario.created_by = 'other_user'
        with patch('db.models.RatingScenarios') as mock_scenarios, \
             patch('db.models.ScenarioUsers') as mock_su:
            mock_scenarios.query.get.return_value = scenario
            mock_su.query.filter_by.return_value.first.return_value = MagicMock()
            user = MockUser(username='testuser')
            require_scenario_membership(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_S04_forbidden(self, mock_role):
        from auth.access_control import require_scenario_membership
        scenario = MagicMock()
        scenario.created_by = 'other_user'
        with patch('db.models.RatingScenarios') as mock_scenarios, \
             patch('db.models.ScenarioUsers') as mock_su:
            mock_scenarios.query.get.return_value = scenario
            mock_su.query.filter_by.return_value.first.return_value = None
            user = MockUser(username='testuser')
            with pytest.raises(ForbiddenError):
                require_scenario_membership(1, user)


# =============================================================================
# require_generation_job_owner
# =============================================================================


class TestRequireGenerationJobOwner:

    @patch('decorators.permission_decorator.has_role', return_value=True)
    def test_AC_G01_admin_bypass(self, mock_has_role):
        from auth.access_control import require_generation_job_owner
        user = MockUser()
        require_generation_job_owner(999, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_G02_owner_access(self, mock_role):
        from auth.access_control import require_generation_job_owner
        job = MagicMock()
        job.created_by = 'testuser'
        with patch('db.models.GenerationJob') as mock_job_cls:
            mock_job_cls.query.get.return_value = job
            user = MockUser(username='testuser')
            require_generation_job_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_G03_forbidden(self, mock_role):
        from auth.access_control import require_generation_job_owner
        job = MagicMock()
        job.created_by = 'other_user'
        with patch('db.models.GenerationJob') as mock_job_cls:
            mock_job_cls.query.get.return_value = job
            user = MockUser(username='testuser')
            with pytest.raises(ForbiddenError):
                require_generation_job_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_G04_not_found(self, mock_role):
        from auth.access_control import require_generation_job_owner
        with patch('db.models.GenerationJob') as mock_job_cls:
            mock_job_cls.query.get.return_value = None
            user = MockUser(username='testuser')
            with pytest.raises(NotFoundError):
                require_generation_job_owner(999, user)


# =============================================================================
# require_judge_session_owner
# =============================================================================


class TestRequireJudgeSessionOwner:

    @patch('decorators.permission_decorator.has_role', return_value=True)
    def test_AC_J01_admin_bypass(self, mock_has_role):
        from auth.access_control import require_judge_session_owner
        user = MockUser()
        require_judge_session_owner(999, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_J02_owner_access(self, mock_role):
        from auth.access_control import require_judge_session_owner
        session = MagicMock()
        session.user_id = 'testuser'
        with patch('db.tables.JudgeSession') as mock_session_cls:
            mock_session_cls.query.get.return_value = session
            user = MockUser(username='testuser')
            require_judge_session_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_J03_forbidden(self, mock_role):
        from auth.access_control import require_judge_session_owner
        session = MagicMock()
        session.user_id = 'other_user'
        with patch('db.tables.JudgeSession') as mock_session_cls:
            mock_session_cls.query.get.return_value = session
            user = MockUser(username='testuser')
            with pytest.raises(ForbiddenError):
                require_judge_session_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_J04_not_found(self, mock_role):
        from auth.access_control import require_judge_session_owner
        with patch('db.tables.JudgeSession') as mock_session_cls:
            mock_session_cls.query.get.return_value = None
            user = MockUser(username='testuser')
            with pytest.raises(NotFoundError):
                require_judge_session_owner(999, user)


# =============================================================================
# require_pipeline_run_owner
# =============================================================================


class TestRequirePipelineRunOwner:

    @patch('decorators.permission_decorator.has_role', return_value=True)
    def test_AC_P01_admin_bypass(self, mock_has_role):
        from auth.access_control import require_pipeline_run_owner
        user = MockUser()
        require_pipeline_run_owner(999, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_P02_owner_access(self, mock_role):
        from auth.access_control import require_pipeline_run_owner
        run = MagicMock()
        run.created_by = 'testuser'
        with patch('db.models.pipeline.PipelineRun') as mock_run_cls:
            mock_run_cls.query.get.return_value = run
            user = MockUser(username='testuser')
            require_pipeline_run_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_P03_forbidden(self, mock_role):
        from auth.access_control import require_pipeline_run_owner
        run = MagicMock()
        run.created_by = 'other_user'
        with patch('db.models.pipeline.PipelineRun') as mock_run_cls:
            mock_run_cls.query.get.return_value = run
            user = MockUser(username='testuser')
            with pytest.raises(ForbiddenError):
                require_pipeline_run_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_P04_not_found(self, mock_role):
        from auth.access_control import require_pipeline_run_owner
        with patch('db.models.pipeline.PipelineRun') as mock_run_cls:
            mock_run_cls.query.get.return_value = None
            user = MockUser(username='testuser')
            with pytest.raises(NotFoundError):
                require_pipeline_run_owner(999, user)


# =============================================================================
# require_oncoco_analysis_owner
# =============================================================================


class TestRequireOncocoAnalysisOwner:

    @patch('decorators.permission_decorator.has_role', return_value=True)
    def test_AC_O01_admin_bypass(self, mock_has_role):
        from auth.access_control import require_oncoco_analysis_owner
        user = MockUser()
        require_oncoco_analysis_owner(999, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_O02_owner_access(self, mock_role):
        from auth.access_control import require_oncoco_analysis_owner
        analysis = MagicMock()
        analysis.user_id = 'testuser'
        with patch('db.tables.OnCoCoAnalysis') as mock_analysis_cls:
            mock_analysis_cls.query.get.return_value = analysis
            user = MockUser(username='testuser')
            require_oncoco_analysis_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_O03_forbidden(self, mock_role):
        from auth.access_control import require_oncoco_analysis_owner
        analysis = MagicMock()
        analysis.user_id = 'other_user'
        with patch('db.tables.OnCoCoAnalysis') as mock_analysis_cls:
            mock_analysis_cls.query.get.return_value = analysis
            user = MockUser(username='testuser')
            with pytest.raises(ForbiddenError):
                require_oncoco_analysis_owner(1, user)

    @patch('decorators.permission_decorator.has_role', return_value=False)
    def test_AC_O04_not_found(self, mock_role):
        from auth.access_control import require_oncoco_analysis_owner
        with patch('db.tables.OnCoCoAnalysis') as mock_analysis_cls:
            mock_analysis_cls.query.get.return_value = None
            user = MockUser(username='testuser')
            with pytest.raises(NotFoundError):
                require_oncoco_analysis_owner(999, user)
