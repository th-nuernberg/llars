"""
Unit tests for ReferralService.

Tests referral campaign management, link generation/validation,
registration tracking, and analytics.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestCampaignCRUD:
    """Tests for campaign creation, reading, updating, and deletion."""

    def test_REF_001_create_campaign(self, app, db, app_context):
        """[REF-001] Should create a campaign with all fields."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaign

        campaign = ReferralService.create_campaign(
            name='Test Campaign',
            created_by='admin',
            description='A test campaign',
            max_registrations=100,
        )

        assert campaign is not None
        assert campaign.id is not None
        assert campaign.name == 'Test Campaign'
        assert campaign.created_by == 'admin'
        assert campaign.description == 'A test campaign'
        assert campaign.max_registrations == 100
        assert campaign.status == 'draft'

        # Verify in DB
        stored = ReferralCampaign.query.get(campaign.id)
        assert stored is not None
        assert stored.name == 'Test Campaign'

    def test_REF_002_create_campaign_minimal(self, app, db, app_context):
        """[REF-002] Should create a campaign with only required fields."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(
            name='Minimal Campaign',
            created_by='admin',
        )

        assert campaign is not None
        assert campaign.name == 'Minimal Campaign'
        assert campaign.description is None
        assert campaign.max_registrations is None
        assert campaign.start_date is None
        assert campaign.end_date is None

    def test_REF_003_get_campaign(self, app, db, app_context):
        """[REF-003] Should retrieve a campaign by ID."""
        from services.referral_service import ReferralService

        created = ReferralService.create_campaign(name='Get Test', created_by='admin')
        fetched = ReferralService.get_campaign(created.id)

        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == 'Get Test'

    def test_REF_004_get_campaign_not_found(self, app, db, app_context):
        """[REF-004] Should return None for non-existent campaign."""
        from services.referral_service import ReferralService

        result = ReferralService.get_campaign(99999)
        assert result is None

    def test_REF_005_list_campaigns(self, app, db, app_context):
        """[REF-005] Should list all non-archived campaigns."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        ReferralService.create_campaign(name='Active', created_by='admin')
        ReferralService.create_campaign(name='Draft', created_by='admin')

        # Create an archived campaign
        archived = ReferralService.create_campaign(name='Archived', created_by='admin')
        ReferralService.update_campaign_status(archived.id, ReferralCampaignStatus.ARCHIVED)

        campaigns = ReferralService.list_campaigns(include_archived=False)
        names = [c.name for c in campaigns]
        assert 'Active' in names
        assert 'Draft' in names
        assert 'Archived' not in names

    def test_REF_006_list_campaigns_include_archived(self, app, db, app_context):
        """[REF-006] Should include archived campaigns when requested."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        ReferralService.create_campaign(name='Active', created_by='admin')
        archived = ReferralService.create_campaign(name='Archived', created_by='admin')
        ReferralService.update_campaign_status(archived.id, ReferralCampaignStatus.ARCHIVED)

        campaigns = ReferralService.list_campaigns(include_archived=True)
        names = [c.name for c in campaigns]
        assert 'Active' in names
        assert 'Archived' in names

    def test_REF_007_update_campaign(self, app, db, app_context):
        """[REF-007] Should update campaign fields."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='Original', created_by='admin')

        updated = ReferralService.update_campaign(
            campaign.id,
            name='Updated Name',
            description='New description',
            max_registrations=50,
        )

        assert updated is not None
        assert updated.name == 'Updated Name'
        assert updated.description == 'New description'
        assert updated.max_registrations == 50

    def test_REF_008_update_campaign_not_found(self, app, db, app_context):
        """[REF-008] Should return None when updating non-existent campaign."""
        from services.referral_service import ReferralService

        result = ReferralService.update_campaign(99999, name='Nope')
        assert result is None

    def test_REF_009_update_campaign_status(self, app, db, app_context):
        """[REF-009] Should update campaign status."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        campaign = ReferralService.create_campaign(name='Status Test', created_by='admin')
        assert campaign.status == 'draft'

        result = ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
        assert result is True

        refreshed = ReferralService.get_campaign(campaign.id)
        assert refreshed.status == 'active'

    def test_REF_010_update_campaign_status_not_found(self, app, db, app_context):
        """[REF-010] Should return False for non-existent campaign status update."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        result = ReferralService.update_campaign_status(99999, ReferralCampaignStatus.ACTIVE)
        assert result is False

    def test_REF_011_delete_campaign(self, app, db, app_context):
        """[REF-011] Should delete a campaign."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='To Delete', created_by='admin')
        result = ReferralService.delete_campaign(campaign.id)
        assert result is True

        fetched = ReferralService.get_campaign(campaign.id)
        assert fetched is None

    def test_REF_012_delete_campaign_not_found(self, app, db, app_context):
        """[REF-012] Should return False when deleting non-existent campaign."""
        from services.referral_service import ReferralService

        result = ReferralService.delete_campaign(99999)
        assert result is False


class TestLinkManagement:
    """Tests for referral link creation, retrieval, and management."""

    def _create_campaign(self, ReferralService):
        """Helper to create a test campaign."""
        return ReferralService.create_campaign(name='Link Test Campaign', created_by='admin')

    def test_REF_013_create_link(self, app, db, app_context):
        """[REF-013] Should create a referral link for a campaign."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            role_name='evaluator',
            label='Test Link',
        )

        assert link is not None
        assert link.campaign_id == campaign.id
        assert link.role_name == 'evaluator'
        assert link.label == 'Test Link'
        assert link.code is not None
        assert link.is_active is True

    def test_REF_014_create_link_with_slug(self, app, db, app_context):
        """[REF-014] Should create a link with a custom slug."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            slug='my-custom-slug',
        )

        assert link.slug == 'my-custom-slug'

    def test_REF_015_create_link_duplicate_slug_raises(self, app, db, app_context):
        """[REF-015] Should raise ConflictError for duplicate slugs."""
        from services.referral_service import ReferralService
        from decorators.error_handler import ConflictError

        campaign = self._create_campaign(ReferralService)
        ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            slug='unique-slug',
        )

        with pytest.raises(ConflictError):
            ReferralService.create_link(
                campaign_id=campaign.id,
                created_by='admin',
                slug='unique-slug',
            )

    def test_REF_016_create_link_invalid_campaign_raises(self, app, db, app_context):
        """[REF-016] Should raise ValidationError for non-existent campaign."""
        from services.referral_service import ReferralService
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            ReferralService.create_link(
                campaign_id=99999,
                created_by='admin',
            )

    @patch('services.referral_service.get_setting', return_value='researcher')
    def test_REF_017_create_link_default_role(self, mock_setting, app, db, app_context):
        """[REF-017] Should use system default role when none specified."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
        )

        assert link.role_name == 'researcher'

    def test_REF_018_get_link_by_code(self, app, db, app_context):
        """[REF-018] Should retrieve a link by code."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        fetched = ReferralService.get_link_by_code(link.code)
        assert fetched is not None
        assert fetched.id == link.id

    def test_REF_019_get_link_by_slug(self, app, db, app_context):
        """[REF-019] Should retrieve a link by slug."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            slug='test-slug',
        )

        fetched = ReferralService.get_link_by_slug('test-slug')
        assert fetched is not None
        assert fetched.id == link.id

    def test_REF_020_list_campaign_links(self, app, db, app_context):
        """[REF-020] Should list all links for a campaign."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        ReferralService.create_link(campaign_id=campaign.id, created_by='admin', label='Link 1')
        ReferralService.create_link(campaign_id=campaign.id, created_by='admin', label='Link 2')

        links = ReferralService.list_campaign_links(campaign.id)
        assert len(links) == 2

    def test_REF_021_update_link(self, app, db, app_context):
        """[REF-021] Should update link fields."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        updated = ReferralService.update_link(
            link.id,
            label='Updated Label',
            role_name='admin',
            max_uses=10,
        )

        assert updated is not None
        assert updated.label == 'Updated Label'
        assert updated.role_name == 'admin'
        assert updated.max_uses == 10

    def test_REF_022_update_link_not_found(self, app, db, app_context):
        """[REF-022] Should return None for non-existent link update."""
        from services.referral_service import ReferralService

        result = ReferralService.update_link(99999, label='Nope')
        assert result is None

    def test_REF_023_deactivate_link(self, app, db, app_context):
        """[REF-023] Should deactivate a link."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')
        assert link.is_active is True

        result = ReferralService.deactivate_link(link.id)
        assert result is True

        refreshed = ReferralService.get_link(link.id)
        assert refreshed.is_active is False

    def test_REF_024_deactivate_link_not_found(self, app, db, app_context):
        """[REF-024] Should return False for non-existent link deactivation."""
        from services.referral_service import ReferralService

        result = ReferralService.deactivate_link(99999)
        assert result is False

    def test_REF_025_delete_link(self, app, db, app_context):
        """[REF-025] Should delete a link."""
        from services.referral_service import ReferralService

        campaign = self._create_campaign(ReferralService)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        result = ReferralService.delete_link(link.id)
        assert result is True

        fetched = ReferralService.get_link(link.id)
        assert fetched is None

    def test_REF_026_delete_link_not_found(self, app, db, app_context):
        """[REF-026] Should return False for non-existent link deletion."""
        from services.referral_service import ReferralService

        result = ReferralService.delete_link(99999)
        assert result is False


class TestLinkValidation:
    """Tests for referral link validation logic."""

    def _create_active_campaign_with_link(self, ReferralService):
        """Helper to create an active campaign with an active link."""
        from db.models.referral import ReferralCampaignStatus

        campaign = ReferralService.create_campaign(name='Validation Test', created_by='admin')
        ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            slug='valid-link',
        )
        return campaign, link

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_027_validate_valid_link(self, mock_setting, app, db, app_context):
        """[REF-027] Should validate a valid active link."""
        from services.referral_service import ReferralService

        campaign, link = self._create_active_campaign_with_link(ReferralService)

        is_valid, found_link, error = ReferralService.validate_link(link.code)
        assert is_valid is True
        assert found_link is not None
        assert found_link.id == link.id
        assert error is None

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_028_validate_link_by_slug(self, mock_setting, app, db, app_context):
        """[REF-028] Should validate a link by slug."""
        from services.referral_service import ReferralService

        campaign, link = self._create_active_campaign_with_link(ReferralService)

        is_valid, found_link, error = ReferralService.validate_link('valid-link')
        assert is_valid is True
        assert found_link is not None

    @patch('services.referral_service.get_setting', return_value=False)
    def test_REF_029_validate_disabled_referral_system(self, mock_setting, app, db, app_context):
        """[REF-029] Should reject when referral system is disabled."""
        from services.referral_service import ReferralService

        is_valid, found_link, error = ReferralService.validate_link('any-code')
        assert is_valid is False
        assert error is not None

    @patch('services.referral_service.get_setting', side_effect=lambda key, default=None: {
        'referral_system_enabled': True,
        'self_registration_enabled': True,
    }.get(key, default))
    def test_REF_030_validate_invalid_code(self, mock_setting, app, db, app_context):
        """[REF-030] Should reject an invalid code."""
        from services.referral_service import ReferralService

        is_valid, found_link, error = ReferralService.validate_link('nonexistent-code')
        assert is_valid is False
        assert 'Ungültig' in error

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_031_validate_inactive_link(self, mock_setting, app, db, app_context):
        """[REF-031] Should reject an inactive link."""
        from services.referral_service import ReferralService

        campaign, link = self._create_active_campaign_with_link(ReferralService)
        ReferralService.deactivate_link(link.id)

        is_valid, found_link, error = ReferralService.validate_link(link.code)
        assert is_valid is False
        assert 'nicht mehr aktiv' in error

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_032_validate_inactive_campaign(self, mock_setting, app, db, app_context):
        """[REF-032] Should reject link when campaign is not active."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        campaign = ReferralService.create_campaign(name='Paused', created_by='admin')
        ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.PAUSED)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        is_valid, found_link, error = ReferralService.validate_link(link.code)
        assert is_valid is False
        assert 'nicht aktiv' in error

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_033_validate_expired_link(self, mock_setting, app, db, app_context):
        """[REF-033] Should reject an expired link."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        campaign, link = self._create_active_campaign_with_link(ReferralService)
        ReferralService.update_link(link.id, expires_at=datetime.now() - timedelta(hours=1))

        is_valid, found_link, error = ReferralService.validate_link(link.code)
        assert is_valid is False
        assert 'abgelaufen' in error

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_034_validate_max_uses_reached(self, mock_setting, app, db, app_context):
        """[REF-034] Should reject link when max uses reached."""
        from services.referral_service import ReferralService

        campaign, link = self._create_active_campaign_with_link(ReferralService)
        ReferralService.update_link(link.id, max_uses=1)

        # Register one user
        ReferralService.register_user(link, 'user1')

        is_valid, found_link, error = ReferralService.validate_link(link.code)
        assert is_valid is False
        assert 'Nutzungslimit' in error


class TestRegistration:
    """Tests for user registration tracking."""

    def test_REF_035_register_user(self, app, db, app_context):
        """[REF-035] Should record a user registration."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='Reg Test', created_by='admin')
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        reg = ReferralService.register_user(
            link=link,
            username='newuser',
            ip_address='127.0.0.1',
            user_agent='TestBrowser/1.0',
        )

        assert reg is not None
        assert reg.username == 'newuser'
        assert reg.link_id == link.id
        assert reg.ip_address == '127.0.0.1'

    def test_REF_036_register_user_truncates_user_agent(self, app, db, app_context):
        """[REF-036] Should truncate long user agents to 512 characters."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='UA Test', created_by='admin')
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        long_ua = 'A' * 1000
        reg = ReferralService.register_user(link=link, username='user2', user_agent=long_ua)

        assert len(reg.user_agent) == 512

    def test_REF_037_get_registration_by_username(self, app, db, app_context):
        """[REF-037] Should find registration by username."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='Lookup Test', created_by='admin')
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')
        ReferralService.register_user(link=link, username='findme')

        found = ReferralService.get_registration_by_username('findme')
        assert found is not None
        assert found.username == 'findme'

    def test_REF_038_get_registration_not_found(self, app, db, app_context):
        """[REF-038] Should return None for non-existent username."""
        from services.referral_service import ReferralService

        result = ReferralService.get_registration_by_username('ghost')
        assert result is None


class TestAnalytics:
    """Tests for campaign and link statistics."""

    def test_REF_039_campaign_stats(self, app, db, app_context):
        """[REF-039] Should return campaign statistics."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        campaign = ReferralService.create_campaign(name='Stats Test', created_by='admin')
        ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
        link1 = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')
        link2 = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')

        ReferralService.register_user(link1, 'user_a')
        ReferralService.register_user(link1, 'user_b')
        ReferralService.register_user(link2, 'user_c')

        stats = ReferralService.get_campaign_stats(campaign.id)

        assert stats['campaign_id'] == campaign.id
        assert stats['total_links'] == 2
        assert stats['total_registrations'] == 3

    def test_REF_040_campaign_stats_not_found(self, app, db, app_context):
        """[REF-040] Should return empty dict for non-existent campaign."""
        from services.referral_service import ReferralService

        stats = ReferralService.get_campaign_stats(99999)
        assert stats == {}

    def test_REF_041_link_stats(self, app, db, app_context):
        """[REF-041] Should return link statistics."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='Link Stats', created_by='admin')
        link = ReferralService.create_link(
            campaign_id=campaign.id,
            created_by='admin',
            max_uses=5,
            slug='stats-link',
        )
        ReferralService.register_user(link, 'user_x')
        ReferralService.register_user(link, 'user_y')

        stats = ReferralService.get_link_stats(link.id)

        assert stats['link_id'] == link.id
        assert stats['registrations'] == 2
        assert stats['remaining_uses'] == 3
        assert stats['slug'] == 'stats-link'

    def test_REF_042_link_stats_not_found(self, app, db, app_context):
        """[REF-042] Should return empty dict for non-existent link."""
        from services.referral_service import ReferralService

        stats = ReferralService.get_link_stats(99999)
        assert stats == {}

    def test_REF_043_system_overview(self, app, db, app_context):
        """[REF-043] Should return system-wide overview statistics."""
        from services.referral_service import ReferralService
        from db.models.referral import ReferralCampaignStatus

        campaign = ReferralService.create_campaign(name='Overview', created_by='admin')
        ReferralService.update_campaign_status(campaign.id, ReferralCampaignStatus.ACTIVE)
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')
        ReferralService.register_user(link, 'overview_user')

        with patch('services.referral_service.get_setting', return_value=True):
            overview = ReferralService.get_system_overview()

        assert overview['total_campaigns'] >= 1
        assert overview['active_campaigns'] >= 1
        assert overview['total_links'] >= 1
        assert overview['total_registrations'] >= 1

    def test_REF_044_list_registrations(self, app, db, app_context):
        """[REF-044] Should list registrations with pagination."""
        from services.referral_service import ReferralService

        campaign = ReferralService.create_campaign(name='List Regs', created_by='admin')
        link = ReferralService.create_link(campaign_id=campaign.id, created_by='admin')
        for i in range(5):
            ReferralService.register_user(link, f'list_user_{i}')

        result, total = ReferralService.list_registrations(limit=3, offset=0)

        assert total == 5
        assert len(result) == 3

    def test_REF_045_list_registrations_by_campaign(self, app, db, app_context):
        """[REF-045] Should filter registrations by campaign."""
        from services.referral_service import ReferralService

        campaign1 = ReferralService.create_campaign(name='C1', created_by='admin')
        campaign2 = ReferralService.create_campaign(name='C2', created_by='admin')
        link1 = ReferralService.create_link(campaign_id=campaign1.id, created_by='admin')
        link2 = ReferralService.create_link(campaign_id=campaign2.id, created_by='admin')

        ReferralService.register_user(link1, 'c1_user')
        ReferralService.register_user(link2, 'c2_user')

        result, total = ReferralService.list_registrations(campaign_id=campaign1.id)
        assert total == 1
        assert result[0]['username'] == 'c1_user'


class TestSystemSettings:
    """Tests for referral system setting checks."""

    @patch('services.referral_service.get_setting', return_value=True)
    def test_REF_046_is_referral_enabled_true(self, mock_get, app, db, app_context):
        """[REF-046] Should return True when referral system is enabled."""
        from services.referral_service import ReferralService

        assert ReferralService.is_referral_enabled() is True

    @patch('services.referral_service.get_setting', return_value=False)
    def test_REF_047_is_referral_enabled_false(self, mock_get, app, db, app_context):
        """[REF-047] Should return False when referral system is disabled."""
        from services.referral_service import ReferralService

        assert ReferralService.is_referral_enabled() is False

    @patch('services.referral_service.get_setting', return_value='evaluator')
    def test_REF_048_get_default_role(self, mock_get, app, db, app_context):
        """[REF-048] Should return configured default role."""
        from services.referral_service import ReferralService

        assert ReferralService.get_default_role() == 'evaluator'
