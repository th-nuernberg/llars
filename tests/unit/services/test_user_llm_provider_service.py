"""
Unit Tests: User LLM Provider Service
=======================================

Comprehensive tests for user_llm_provider_service.py.

Test IDs: ULP-001 to ULP-060

Key areas:
- CRUD operations for user providers
- Provider sharing (user-share, role-share, share-all)
- Available providers query
- Provider testing/validation
- Provider deletion
- get_provider_for_use access checks
- record_usage
- fetch_models
- Default base URL resolution
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(db, username, *, group_name='ULP_Group'):
    from db.models import User, UserGroup

    group = UserGroup.query.filter_by(name=group_name).first()
    if not group:
        group = UserGroup(name=group_name)
        db.session.add(group)
        db.session.commit()

    user = User(username=username)
    user.set_password('password')
    user.api_key = f'ulp-key-{username}'
    user.group = group
    user.is_active = True
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def _create_provider(db, user_id, name, provider_type='openai', *, api_key='sk-test', active=True):
    """Create a provider directly in DB for test setup."""
    from db.models.user_llm_provider import UserLLMProvider

    provider = UserLLMProvider(
        user_id=user_id,
        provider_type=provider_type,
        name=name,
        api_key_encrypted='encrypted_placeholder' if api_key else None,
        is_active=active,
        config_json={}
    )
    db.session.add(provider)
    db.session.commit()
    db.session.refresh(provider)
    return provider


# ===========================================================================
# Create Provider
# ===========================================================================

class TestCreateProvider:
    """Tests for UserLLMProviderService.create_provider."""

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='encrypted_key')
    def test_ULP_001_create_provider_success(self, mock_enc, app, db, app_context):
        """[ULP-001] Create a new provider successfully."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_create_001')
        provider = UserLLMProviderService.create_provider(
            user_id=user.id,
            provider_type='openai',
            name='My OpenAI',
            api_key='sk-test123',
            base_url='https://api.openai.com/v1'
        )

        assert provider is not None
        assert provider.name == 'My OpenAI'
        assert provider.provider_type == 'openai'
        assert provider.user_id == user.id
        assert provider.is_active is True
        mock_enc.assert_called_once_with('sk-test123')

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='enc')
    def test_ULP_002_create_provider_duplicate_name_fails(self, mock_enc, app, db, app_context):
        """[ULP-002] Duplicate name for same user raises ConflictError."""
        from services.user_llm_provider_service import UserLLMProviderService
        from decorators.error_handler import ConflictError

        user = _make_user(db, 'ulp_dup_002')
        UserLLMProviderService.create_provider(
            user_id=user.id, provider_type='openai', name='DupName', api_key='k'
        )

        with pytest.raises(ConflictError):
            UserLLMProviderService.create_provider(
                user_id=user.id, provider_type='openai', name='DupName', api_key='k'
            )

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='enc')
    def test_ULP_003_create_provider_is_default_unsets_others(self, mock_enc, app, db, app_context):
        """[ULP-003] Setting is_default unsets other defaults."""
        from services.user_llm_provider_service import UserLLMProviderService
        from db.models.user_llm_provider import UserLLMProvider

        user = _make_user(db, 'ulp_def_003')
        p1 = UserLLMProviderService.create_provider(
            user_id=user.id, provider_type='openai', name='First',
            api_key='k', is_default=True
        )
        p2 = UserLLMProviderService.create_provider(
            user_id=user.id, provider_type='openai', name='Second',
            api_key='k', is_default=True
        )

        # Refresh p1
        db.session.refresh(p1)
        assert p1.is_default is False
        assert p2.is_default is True

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='enc')
    def test_ULP_004_create_provider_no_api_key(self, mock_enc, app, db, app_context):
        """[ULP-004] Provider without API key (e.g., Ollama local)."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_nokey_004')
        provider = UserLLMProviderService.create_provider(
            user_id=user.id, provider_type='ollama', name='Local Ollama'
        )

        assert provider.api_key_encrypted is None
        mock_enc.assert_not_called()

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='enc')
    def test_ULP_005_create_provider_normalizes_type(self, mock_enc, app, db, app_context):
        """[ULP-005] Provider type is lowercased and stripped."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_norm_005')
        provider = UserLLMProviderService.create_provider(
            user_id=user.id, provider_type='  OpenAI  ', name='Normalized',
            api_key='k'
        )

        assert provider.provider_type == 'openai'


# ===========================================================================
# Get Provider
# ===========================================================================

class TestGetProvider:
    """Tests for get_provider and get_user_providers."""

    def test_ULP_010_get_provider_found(self, app, db, app_context):
        """[ULP-010] Get provider by ID."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_get_010')
        p = _create_provider(db, user.id, 'GetTest')

        result = UserLLMProviderService.get_provider(p.id)
        assert result is not None
        assert result.name == 'GetTest'

    def test_ULP_011_get_provider_not_found(self, app, db, app_context):
        """[ULP-011] Get non-existent provider returns None."""
        from services.user_llm_provider_service import UserLLMProviderService

        assert UserLLMProviderService.get_provider(99999) is None

    def test_ULP_012_get_user_providers_filters_inactive(self, app, db, app_context):
        """[ULP-012] get_user_providers excludes inactive by default."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_inactive_012')
        _create_provider(db, user.id, 'Active012', active=True)
        _create_provider(db, user.id, 'Inactive012', active=False)

        providers = UserLLMProviderService.get_user_providers(user.id)
        names = [p.name for p in providers]
        assert 'Active012' in names
        assert 'Inactive012' not in names

    def test_ULP_013_get_user_providers_include_inactive(self, app, db, app_context):
        """[ULP-013] get_user_providers with include_inactive=True returns all."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_all_013')
        _create_provider(db, user.id, 'Active013', active=True)
        _create_provider(db, user.id, 'Inactive013', active=False)

        providers = UserLLMProviderService.get_user_providers(
            user.id, include_inactive=True
        )
        names = [p.name for p in providers]
        assert 'Active013' in names
        assert 'Inactive013' in names

    def test_ULP_014_get_user_providers_filter_by_type(self, app, db, app_context):
        """[ULP-014] get_user_providers filters by provider_type."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_type_014')
        _create_provider(db, user.id, 'OAI014', provider_type='openai')
        _create_provider(db, user.id, 'Ollama014', provider_type='ollama')

        providers = UserLLMProviderService.get_user_providers(
            user.id, provider_type='openai'
        )
        assert all(p.provider_type == 'openai' for p in providers)
        assert len(providers) == 1


# ===========================================================================
# Update Provider
# ===========================================================================

class TestUpdateProvider:
    """Tests for update_provider."""

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='new_enc')
    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_020_update_provider_name(self, mock_cache, mock_enc, app, db, app_context):
        """[ULP-020] Update provider name."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_upd_020')
        p = _create_provider(db, user.id, 'OldName020')

        result = UserLLMProviderService.update_provider(
            p.id, user.id, name='NewName020'
        )

        assert result is not None
        assert result.name == 'NewName020'

    @patch('services.user_llm_provider_service.encrypt_api_key', return_value='new_enc')
    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_021_update_provider_clear_api_key(self, mock_cache, mock_enc, app, db, app_context):
        """[ULP-021] Empty string API key clears the stored key."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_clear_021')
        p = _create_provider(db, user.id, 'ClearKey021')

        result = UserLLMProviderService.update_provider(
            p.id, user.id, api_key=''
        )

        assert result.api_key_encrypted is None

    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_022_update_provider_wrong_user(self, mock_cache, app, db, app_context):
        """[ULP-022] Update by wrong user returns None."""
        from services.user_llm_provider_service import UserLLMProviderService

        user1 = _make_user(db, 'ulp_own_022a')
        user2 = _make_user(db, 'ulp_own_022b')
        p = _create_provider(db, user1.id, 'OwnedBy022a')

        result = UserLLMProviderService.update_provider(
            p.id, user2.id, name='Stolen'
        )
        assert result is None


# ===========================================================================
# Delete Provider
# ===========================================================================

class TestDeleteProvider:
    """Tests for delete_provider."""

    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_025_delete_provider_success(self, mock_cache, app, db, app_context):
        """[ULP-025] Delete own provider."""
        from services.user_llm_provider_service import UserLLMProviderService
        from db.models.user_llm_provider import UserLLMProvider

        user = _make_user(db, 'ulp_del_025')
        p = _create_provider(db, user.id, 'DeleteMe025')
        pid = p.id

        result = UserLLMProviderService.delete_provider(pid, user.id)
        assert result is True
        assert UserLLMProvider.query.get(pid) is None

    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_026_delete_provider_wrong_user(self, mock_cache, app, db, app_context):
        """[ULP-026] Cannot delete another user's provider."""
        from services.user_llm_provider_service import UserLLMProviderService

        user1 = _make_user(db, 'ulp_del_026a')
        user2 = _make_user(db, 'ulp_del_026b')
        p = _create_provider(db, user1.id, 'NotYours026')

        result = UserLLMProviderService.delete_provider(p.id, user2.id)
        assert result is False

    @patch('services.llm.llm_client_factory.LLMClientFactory.clear_cache')
    def test_ULP_027_delete_nonexistent_provider(self, mock_cache, app, db, app_context):
        """[ULP-027] Deleting non-existent provider returns False."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_del_027')
        result = UserLLMProviderService.delete_provider(99999, user.id)
        assert result is False


# ===========================================================================
# Provider Sharing
# ===========================================================================

class TestProviderSharing:
    """Tests for share/unshare operations."""

    def test_ULP_030_share_with_user(self, app, db, app_context):
        """[ULP-030] Share provider with a specific user."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_share_030a')
        target = _make_user(db, 'ulp_share_030b')
        p = _create_provider(db, owner.id, 'Shared030')

        share = UserLLMProviderService.share_provider(
            provider_id=p.id,
            user_id=owner.id,
            share_type='user',
            target_identifier=target.username
        )

        assert share is not None
        assert share.share_type == 'user'
        assert share.target_identifier == target.username

        # Provider should be marked as shared
        db.session.refresh(p)
        assert p.is_shared is True

    def test_ULP_031_share_with_role(self, app, db, app_context):
        """[ULP-031] Share provider with a role."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_share_031')
        p = _create_provider(db, owner.id, 'SharedRole031')

        share = UserLLMProviderService.share_provider(
            provider_id=p.id,
            user_id=owner.id,
            share_type='role',
            target_identifier='researcher'
        )

        assert share.share_type == 'role'
        assert share.target_identifier == 'researcher'

    def test_ULP_032_share_duplicate_fails(self, app, db, app_context):
        """[ULP-032] Duplicate share raises ConflictError."""
        from services.user_llm_provider_service import UserLLMProviderService
        from decorators.error_handler import ConflictError

        owner = _make_user(db, 'ulp_dup_032a')
        target = _make_user(db, 'ulp_dup_032b')
        p = _create_provider(db, owner.id, 'DupShare032')

        UserLLMProviderService.share_provider(
            p.id, owner.id, 'user', target.username
        )

        with pytest.raises(ConflictError):
            UserLLMProviderService.share_provider(
                p.id, owner.id, 'user', target.username
            )

    def test_ULP_033_share_invalid_type_fails(self, app, db, app_context):
        """[ULP-033] Invalid share_type raises ValidationError."""
        from services.user_llm_provider_service import UserLLMProviderService
        from decorators.error_handler import ValidationError

        owner = _make_user(db, 'ulp_bad_033')
        p = _create_provider(db, owner.id, 'BadType033')

        with pytest.raises(ValidationError):
            UserLLMProviderService.share_provider(
                p.id, owner.id, 'invalid_type', 'someone'
            )

    def test_ULP_034_share_nonexistent_user_fails(self, app, db, app_context):
        """[ULP-034] Sharing with non-existent user raises ValidationError."""
        from services.user_llm_provider_service import UserLLMProviderService
        from decorators.error_handler import ValidationError

        owner = _make_user(db, 'ulp_nouser_034')
        p = _create_provider(db, owner.id, 'NoUser034')

        with pytest.raises(ValidationError):
            UserLLMProviderService.share_provider(
                p.id, owner.id, 'user', 'nonexistent_user_xyz'
            )

    def test_ULP_035_share_not_owner_fails(self, app, db, app_context):
        """[ULP-035] Non-owner cannot share provider."""
        from services.user_llm_provider_service import UserLLMProviderService
        from decorators.error_handler import NotFoundError

        owner = _make_user(db, 'ulp_notowner_035a')
        other = _make_user(db, 'ulp_notowner_035b')
        p = _create_provider(db, owner.id, 'NotYours035')

        with pytest.raises(NotFoundError):
            UserLLMProviderService.share_provider(
                p.id, other.id, 'role', 'researcher'
            )

    def test_ULP_036_share_with_token_limit(self, app, db, app_context):
        """[ULP-036] Share with usage_limit_tokens."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_limit_036a')
        target = _make_user(db, 'ulp_limit_036b')
        p = _create_provider(db, owner.id, 'Limited036')

        share = UserLLMProviderService.share_provider(
            p.id, owner.id, 'user', target.username,
            usage_limit_tokens=10000
        )

        assert share.usage_limit_tokens == 10000


# ===========================================================================
# Unshare Provider
# ===========================================================================

class TestUnshareProvider:
    """Tests for unshare_provider."""

    def test_ULP_038_unshare_success(self, app, db, app_context):
        """[ULP-038] Unshare removes the share entry."""
        from services.user_llm_provider_service import UserLLMProviderService
        from db.models.user_llm_provider import UserLLMProviderShare

        owner = _make_user(db, 'ulp_unshare_038a')
        target = _make_user(db, 'ulp_unshare_038b')
        p = _create_provider(db, owner.id, 'Unshare038')

        share = UserLLMProviderService.share_provider(
            p.id, owner.id, 'user', target.username
        )

        result = UserLLMProviderService.unshare_provider(share.id, owner.id)
        assert result is True

        assert UserLLMProviderShare.query.get(share.id) is None
        db.session.refresh(p)
        assert p.is_shared is False

    def test_ULP_039_unshare_wrong_owner(self, app, db, app_context):
        """[ULP-039] Non-owner cannot unshare."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_uns_039a')
        other = _make_user(db, 'ulp_uns_039b')
        target = _make_user(db, 'ulp_uns_039c')
        p = _create_provider(db, owner.id, 'WrongUnshare039')

        share = UserLLMProviderService.share_provider(
            p.id, owner.id, 'user', target.username
        )

        result = UserLLMProviderService.unshare_provider(share.id, other.id)
        assert result is False

    def test_ULP_040_unshare_nonexistent(self, app, db, app_context):
        """[ULP-040] Unsharing non-existent share returns False."""
        from services.user_llm_provider_service import UserLLMProviderService

        _make_user(db, 'ulp_uns_040')
        result = UserLLMProviderService.unshare_provider(99999, 1)
        assert result is False


# ===========================================================================
# Toggle Share With All
# ===========================================================================

class TestToggleShareWithAll:
    """Tests for toggle_share_with_all."""

    def test_ULP_042_toggle_share_all_on(self, app, db, app_context):
        """[ULP-042] Enable share_with_all."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_all_042')
        p = _create_provider(db, owner.id, 'ShareAll042')

        result = UserLLMProviderService.toggle_share_with_all(p.id, owner.id, True)
        assert result is True

        db.session.refresh(p)
        assert p.share_with_all is True
        assert p.is_shared is True

    def test_ULP_043_toggle_share_all_off(self, app, db, app_context):
        """[ULP-043] Disable share_with_all."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_all_043')
        p = _create_provider(db, owner.id, 'ShareAllOff043')
        p.share_with_all = True
        p.is_shared = True
        db.session.commit()

        result = UserLLMProviderService.toggle_share_with_all(p.id, owner.id, False)
        assert result is True

        db.session.refresh(p)
        assert p.share_with_all is False

    def test_ULP_044_toggle_share_all_wrong_user(self, app, db, app_context):
        """[ULP-044] Non-owner cannot toggle share_with_all."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_all_044a')
        other = _make_user(db, 'ulp_all_044b')
        p = _create_provider(db, owner.id, 'NotYourToggle044')

        result = UserLLMProviderService.toggle_share_with_all(p.id, other.id, True)
        assert result is False


# ===========================================================================
# Available Providers for User
# ===========================================================================

class TestAvailableProviders:
    """Tests for get_available_providers_for_user."""

    def test_ULP_045_own_providers_listed(self, app, db, app_context):
        """[ULP-045] Own active providers appear with source='own'."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_avail_045')
        _create_provider(db, user.id, 'OwnProvider045')

        result = UserLLMProviderService.get_available_providers_for_user(
            user.id, user.username, ['evaluator']
        )

        own = [p for p in result if p['source'] == 'own']
        assert len(own) >= 1
        assert any(p['name'] == 'OwnProvider045' for p in own)

    def test_ULP_046_shared_with_all_visible(self, app, db, app_context):
        """[ULP-046] Providers shared with all appear for any user."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_avail_046a')
        other = _make_user(db, 'ulp_avail_046b')
        p = _create_provider(db, owner.id, 'SharedAll046')
        p.share_with_all = True
        p.is_active = True
        db.session.commit()

        result = UserLLMProviderService.get_available_providers_for_user(
            other.id, other.username, ['evaluator']
        )

        shared_all = [r for r in result if r.get('source') == 'shared_all']
        assert any(r['name'] == 'SharedAll046' for r in shared_all)

    def test_ULP_047_inactive_own_excluded(self, app, db, app_context):
        """[ULP-047] Inactive own providers are excluded."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_avail_047')
        _create_provider(db, user.id, 'Inactive047', active=False)

        result = UserLLMProviderService.get_available_providers_for_user(
            user.id, user.username, []
        )

        names = [p['name'] for p in result]
        assert 'Inactive047' not in names


# ===========================================================================
# Get Provider for Use (access checks)
# ===========================================================================

class TestGetProviderForUse:
    """Tests for get_provider_for_use with access control."""

    @patch('services.user_llm_provider_service.decrypt_api_key', return_value='sk-decrypted')
    def test_ULP_050_own_provider_accessible(self, mock_dec, app, db, app_context):
        """[ULP-050] Owner can use own provider."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_use_050')
        p = _create_provider(db, user.id, 'UseProv050')

        provider, key = UserLLMProviderService.get_provider_for_use(
            p.id, user.id, user.username, ['evaluator']
        )

        assert provider is not None
        assert key == 'sk-decrypted'

    def test_ULP_051_nonowner_no_share_denied(self, app, db, app_context):
        """[ULP-051] Non-owner without share cannot use provider."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_use_051a')
        other = _make_user(db, 'ulp_use_051b')
        p = _create_provider(db, owner.id, 'Denied051')

        provider, key = UserLLMProviderService.get_provider_for_use(
            p.id, other.id, other.username, ['evaluator']
        )

        assert provider is None
        assert key is None

    @patch('services.user_llm_provider_service.decrypt_api_key', return_value='sk-shared')
    def test_ULP_052_shared_with_all_accessible(self, mock_dec, app, db, app_context):
        """[ULP-052] Provider shared with all is accessible by any user."""
        from services.user_llm_provider_service import UserLLMProviderService

        owner = _make_user(db, 'ulp_use_052a')
        other = _make_user(db, 'ulp_use_052b')
        p = _create_provider(db, owner.id, 'SharedAll052')
        p.share_with_all = True
        db.session.commit()

        provider, key = UserLLMProviderService.get_provider_for_use(
            p.id, other.id, other.username, []
        )

        assert provider is not None

    def test_ULP_053_inactive_provider_denied(self, app, db, app_context):
        """[ULP-053] Inactive provider returns None even for owner."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_use_053')
        p = _create_provider(db, user.id, 'Inactive053', active=False)

        provider, key = UserLLMProviderService.get_provider_for_use(
            p.id, user.id, user.username, []
        )

        assert provider is None


# ===========================================================================
# Record Usage
# ===========================================================================

class TestRecordUsage:
    """Tests for record_usage."""

    def test_ULP_055_record_usage_increments(self, app, db, app_context):
        """[ULP-055] Record usage increments counters."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_usage_055')
        p = _create_provider(db, user.id, 'Usage055')
        initial_requests = p.total_requests
        initial_tokens = p.total_tokens

        UserLLMProviderService.record_usage(p.id, tokens=500)

        db.session.refresh(p)
        assert p.total_requests == initial_requests + 1
        assert p.total_tokens == initial_tokens + 500
        assert p.last_used_at is not None

    def test_ULP_056_record_usage_with_error(self, app, db, app_context):
        """[ULP-056] Record usage with error stores the error message."""
        from services.user_llm_provider_service import UserLLMProviderService

        user = _make_user(db, 'ulp_usage_056')
        p = _create_provider(db, user.id, 'UsageErr056')

        UserLLMProviderService.record_usage(p.id, tokens=0, error='Rate limited')

        db.session.refresh(p)
        assert p.last_error == 'Rate limited'

    def test_ULP_057_record_usage_nonexistent_provider(self, app, db, app_context):
        """[ULP-057] Record usage for non-existent provider does nothing."""
        from services.user_llm_provider_service import UserLLMProviderService

        # Should not raise
        UserLLMProviderService.record_usage(99999, tokens=100)


# ===========================================================================
# Default Base URL
# ===========================================================================

class TestDefaultBaseUrl:
    """Tests for _default_base_url."""

    def test_ULP_058_default_urls(self, app, db, app_context):
        """[ULP-058] Known provider types return correct default URLs."""
        from services.user_llm_provider_service import UserLLMProviderService

        assert UserLLMProviderService._default_base_url('openai') == 'https://api.openai.com/v1'
        assert UserLLMProviderService._default_base_url('ollama') == 'http://localhost:11434'
        assert UserLLMProviderService._default_base_url('mistral') == 'https://api.mistral.ai/v1'

    def test_ULP_059_default_url_unknown(self, app, db, app_context):
        """[ULP-059] Unknown provider type returns None."""
        from services.user_llm_provider_service import UserLLMProviderService

        assert UserLLMProviderService._default_base_url('unknown_xyz') is None

    def test_ULP_060_default_url_none_input(self, app, db, app_context):
        """[ULP-060] None provider type returns None."""
        from services.user_llm_provider_service import UserLLMProviderService

        assert UserLLMProviderService._default_base_url(None) is None
        assert UserLLMProviderService._default_base_url('') is None
