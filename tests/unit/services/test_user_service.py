"""
Unit Tests: User Service (Extended)
=====================================

Additional comprehensive tests for user_service.py covering areas
not fully tested in the existing tests/unit/services/user/test_user_service.py.

Test IDs: USR_SVC-001 to USR_SVC-030

Key areas:
- Soft delete / inactive user lookups
- Edge cases for create_user
- change_user_group with None admin_user
- get_all_users includes deleted/inactive
- validate_api_key with inactive user
- get_or_create_group error handling
"""

import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_group(db, name):
    from db.models import UserGroup
    group = UserGroup(name=name)
    db.session.add(group)
    db.session.commit()
    return group


def _make_user(db, username, *, group_name='USR_SVC_Group', active=True, deleted=False, api_key=None):
    from db.models import User, UserGroup

    group = UserGroup.query.filter_by(name=group_name).first()
    if not group:
        group = _make_group(db, group_name)

    user = User(username=username)
    user.set_password('password')
    user.api_key = api_key or f'usr-svc-key-{username}'
    user.group = group
    user.is_active = active
    if deleted:
        user.deleted_at = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


# ===========================================================================
# Lookup edge cases
# ===========================================================================

class TestUserLookupExtended:
    """Extended lookup tests."""

    def test_USR_SVC_001_get_by_username_returns_deleted_user(self, app, db, app_context):
        """[USR_SVC-001] get_user_by_username returns a soft-deleted user (no filter)."""
        from services.user_service import UserService

        _make_user(db, 'deleted_lookup_001', deleted=True)
        user = UserService.get_user_by_username('deleted_lookup_001')
        # The service does NOT filter deleted users in lookups
        assert user is not None
        assert user.deleted_at is not None

    def test_USR_SVC_002_get_by_username_returns_inactive_user(self, app, db, app_context):
        """[USR_SVC-002] get_user_by_username returns an inactive user."""
        from services.user_service import UserService

        _make_user(db, 'inactive_lookup_002', active=False)
        user = UserService.get_user_by_username('inactive_lookup_002')
        assert user is not None
        assert user.is_active is False

    def test_USR_SVC_003_get_by_id_zero_returns_none(self, app, db, app_context):
        """[USR_SVC-003] get_user_by_id with 0 returns None."""
        from services.user_service import UserService

        assert UserService.get_user_by_id(0) is None

    def test_USR_SVC_004_user_exists_with_deleted_user(self, app, db, app_context):
        """[USR_SVC-004] user_exists returns True even for deleted users."""
        from services.user_service import UserService

        _make_user(db, 'exists_deleted_004', deleted=True)
        assert UserService.user_exists('exists_deleted_004') is True


# ===========================================================================
# API Key Validation edge cases
# ===========================================================================

class TestAPIKeyValidationExtended:
    """Extended API key tests."""

    def test_USR_SVC_005_validate_api_key_inactive_user(self, app, db, app_context):
        """[USR_SVC-005] validate_api_key succeeds for inactive user (no active check)."""
        from services.user_service import UserService

        _make_user(db, 'inactive_key_005', active=False, api_key='inactive-key-005')
        is_valid, user, error = UserService.validate_api_key('inactive-key-005')
        # The service doesn't check is_active during key validation
        assert is_valid is True
        assert user is not None

    def test_USR_SVC_006_validate_api_key_deleted_user(self, app, db, app_context):
        """[USR_SVC-006] validate_api_key succeeds for deleted user (no delete check)."""
        from services.user_service import UserService

        _make_user(db, 'deleted_key_006', deleted=True, api_key='deleted-key-006')
        is_valid, user, error = UserService.validate_api_key('deleted-key-006')
        assert is_valid is True


# ===========================================================================
# Create user edge cases
# ===========================================================================

class TestCreateUserExtended:
    """Extended user creation tests."""

    def test_USR_SVC_010_create_user_whitespace_collab_color(self, app, db, app_context):
        """[USR_SVC-010] Whitespace-only collab_color treated as None."""
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='whitespace_color_010',
            password='password',
            collab_color='   '
        )
        assert success is True
        # Should get a default color, not whitespace
        assert user.collab_color is not None
        assert user.collab_color.strip() != ''

    def test_USR_SVC_011_create_user_whitespace_avatar_seed(self, app, db, app_context):
        """[USR_SVC-011] Whitespace-only avatar_seed treated as None."""
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='whitespace_seed_011',
            password='password',
            avatar_seed='   '
        )
        assert success is True
        # Should auto-generate an avatar seed
        assert user.avatar_seed is not None

    def test_USR_SVC_012_create_user_generates_collab_color(self, app, db, app_context):
        """[USR_SVC-012] collab_color is auto-assigned when not provided."""
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='auto_color_012',
            password='password'
        )
        assert success is True
        assert user.collab_color is not None
        assert user.collab_color.startswith('#')


# ===========================================================================
# Change user group edge cases
# ===========================================================================

class TestChangeUserGroupExtended:
    """Extended group change tests."""

    def test_USR_SVC_015_change_group_none_admin(self, app, db, app_context):
        """[USR_SVC-015] change_user_group with None admin returns error."""
        from services.user_service import UserService

        _make_user(db, 'target_015')
        success, error = UserService.change_user_group('target_015', 'SomeGroup', None)
        assert success is False
        assert 'permission' in error.lower()

    def test_USR_SVC_016_change_group_admin_without_username_attr(self, app, db, app_context):
        """[USR_SVC-016] change_user_group with admin missing username returns error."""
        from services.user_service import UserService

        _make_user(db, 'target_016')
        fake_admin = MagicMock(spec=[])  # No username attribute
        success, error = UserService.change_user_group('target_016', 'SomeGroup', fake_admin)
        assert success is False


# ===========================================================================
# get_or_create_group
# ===========================================================================

class TestGroupManagementExtended:
    """Extended group management tests."""

    def test_USR_SVC_020_get_or_create_group_idempotent(self, app, db, app_context):
        """[USR_SVC-020] get_or_create_group called twice returns same group."""
        from services.user_service import UserService

        g1 = UserService.get_or_create_group('Idempotent020')
        g2 = UserService.get_or_create_group('Idempotent020')
        assert g1.id == g2.id

    def test_USR_SVC_021_get_group_by_name_none_input(self, app, db, app_context):
        """[USR_SVC-021] get_group_by_name with None returns None."""
        from services.user_service import UserService

        result = UserService.get_group_by_name(None)
        assert result is None


# ===========================================================================
# get_all_users
# ===========================================================================

class TestGetAllUsersExtended:
    """Extended get_all_users tests."""

    def test_USR_SVC_025_get_all_users_includes_inactive(self, app, db, app_context):
        """[USR_SVC-025] get_all_users includes inactive users."""
        from services.user_service import UserService

        _make_user(db, 'inactive_all_025', active=False)
        _make_user(db, 'active_all_025', active=True)

        users = UserService.get_all_users()
        usernames = [u.username for u in users]
        assert 'inactive_all_025' in usernames
        assert 'active_all_025' in usernames

    def test_USR_SVC_026_get_all_users_includes_deleted(self, app, db, app_context):
        """[USR_SVC-026] get_all_users includes soft-deleted users."""
        from services.user_service import UserService

        _make_user(db, 'deleted_all_026', deleted=True)

        users = UserService.get_all_users()
        usernames = [u.username for u in users]
        assert 'deleted_all_026' in usernames


# ===========================================================================
# validate_uuid
# ===========================================================================

class TestValidateUuidExtended:
    """Extended UUID validation tests."""

    def test_USR_SVC_028_validate_uuid_with_uppercase(self, app, app_context):
        """[USR_SVC-028] UUID with uppercase hex is invalid (strict)."""
        from services.user_service import UserService

        upper_uuid = str(uuid4()).upper()
        # Python uuid4() produces lowercase; uppercase should fail strict equality
        result = UserService.validate_uuid(upper_uuid)
        assert result is False

    def test_USR_SVC_029_validate_uuid_none_input(self, app, app_context):
        """[USR_SVC-029] None input raises TypeError (uuid.UUID doesn't accept None)."""
        from services.user_service import UserService

        with pytest.raises(TypeError):
            UserService.validate_uuid(None)

    def test_USR_SVC_030_validate_uuid_correct_v4(self, app, app_context):
        """[USR_SVC-030] Properly formatted v4 UUID passes."""
        from services.user_service import UserService
        import uuid

        valid = str(uuid.uuid4())
        assert UserService.validate_uuid(valid, version=4) is True
