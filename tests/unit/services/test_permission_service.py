"""
Unit Tests: Permission Service (Extended)
==========================================

Comprehensive tests for permission_service.py covering areas NOT tested
in the existing tests/unit/services/permission/test_permission_service.py.

Test IDs: PERM_SVC-001 to PERM_SVC-060

Key areas:
- grant_permission / revoke_permission
- assign_role / unassign_role
- get_all_permissions / get_all_roles
- create_role / set_role_permissions
- get_all_users_with_roles
- user_has_role
- _resolve_role
- Edge cases (empty/None inputs)
- Audit logging
"""

import pytest
from datetime import datetime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_user(db, username, *, active=True, deleted=False):
    from db.models import User, UserGroup

    group = UserGroup.query.first()
    if not group:
        group = UserGroup(name='PermTestGroup')
        db.session.add(group)
        db.session.commit()

    user = User(username=username)
    user.set_password('password')
    user.api_key = f'perm-svc-key-{username}'
    user.group = group
    user.is_active = active
    if deleted:
        user.deleted_at = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def _assign_role(db, username, role_name):
    from db.models import Role, UserRole

    role = Role.query.filter_by(role_name=role_name).first()
    if role:
        db.session.add(UserRole(
            username=username,
            role_id=role.id,
            assigned_by='test',
            assigned_at=datetime.utcnow()
        ))
        db.session.commit()


# ===========================================================================
# Grant / Revoke Permission
# ===========================================================================

class TestGrantPermission:
    """Tests for PermissionService.grant_permission."""

    def test_PERM_SVC_001_grant_permission_new(self, app, db, app_context):
        """[PERM_SVC-001] Grant a new direct permission to a user."""
        from services.permission_service import PermissionService
        from db.models import UserPermission, Permission

        user = _create_user(db, 'grant_new_001')
        perm = Permission.query.filter_by(permission_key='admin:users:manage').first()

        result = PermissionService.grant_permission(
            username='grant_new_001',
            permission_key='admin:users:manage',
            admin_username='test_admin'
        )

        assert result is True
        up = UserPermission.query.filter_by(
            username='grant_new_001', permission_id=perm.id
        ).first()
        assert up is not None
        assert up.granted is True

    def test_PERM_SVC_002_grant_permission_updates_existing_deny(self, app, db, app_context):
        """[PERM_SVC-002] Grant overwrites an existing deny."""
        from services.permission_service import PermissionService
        from db.models import UserPermission, Permission

        user = _create_user(db, 'grant_update_002')
        perm = Permission.query.filter_by(permission_key='feature:ranking:view').first()

        # First deny
        up = UserPermission(
            username='grant_update_002',
            permission_id=perm.id,
            granted=False,
            granted_by='setup'
        )
        db.session.add(up)
        db.session.commit()

        # Now grant
        result = PermissionService.grant_permission(
            'grant_update_002', 'feature:ranking:view', 'test_admin'
        )
        assert result is True

        up_updated = UserPermission.query.filter_by(
            username='grant_update_002', permission_id=perm.id
        ).first()
        assert up_updated.granted is True

    def test_PERM_SVC_003_grant_permission_nonexistent_key(self, app, db, app_context):
        """[PERM_SVC-003] Grant returns False for unknown permission key."""
        from services.permission_service import PermissionService

        _create_user(db, 'grant_bad_003')
        result = PermissionService.grant_permission(
            'grant_bad_003', 'nonexistent:perm:key', 'admin'
        )
        assert result is False

    def test_PERM_SVC_004_grant_permission_creates_audit_log(self, app, db, app_context):
        """[PERM_SVC-004] Grant creates an audit log entry."""
        from services.permission_service import PermissionService
        from db.models import PermissionAuditLog

        _create_user(db, 'grant_audit_004')
        PermissionService.grant_permission(
            'grant_audit_004', 'feature:ranking:view', 'admin_audit'
        )

        log = PermissionAuditLog.query.filter_by(
            action='GRANT',
            target_username='grant_audit_004',
            admin_username='admin_audit'
        ).first()
        assert log is not None
        assert log.permission_key == 'feature:ranking:view'


class TestRevokePermission:
    """Tests for PermissionService.revoke_permission."""

    def test_PERM_SVC_005_revoke_permission_new_deny(self, app, db, app_context):
        """[PERM_SVC-005] Revoke creates an explicit deny entry."""
        from services.permission_service import PermissionService
        from db.models import UserPermission, Permission

        user = _create_user(db, 'revoke_005')
        result = PermissionService.revoke_permission(
            'revoke_005', 'feature:ranking:view', 'admin'
        )
        assert result is True

        perm = Permission.query.filter_by(permission_key='feature:ranking:view').first()
        up = UserPermission.query.filter_by(
            username='revoke_005', permission_id=perm.id
        ).first()
        assert up is not None
        assert up.granted is False

    def test_PERM_SVC_006_revoke_permission_flips_grant_to_deny(self, app, db, app_context):
        """[PERM_SVC-006] Revoke flips an existing grant to deny."""
        from services.permission_service import PermissionService
        from db.models import UserPermission, Permission

        user = _create_user(db, 'revoke_flip_006')
        perm = Permission.query.filter_by(permission_key='feature:ranking:view').first()

        db.session.add(UserPermission(
            username='revoke_flip_006', permission_id=perm.id,
            granted=True, granted_by='setup'
        ))
        db.session.commit()

        result = PermissionService.revoke_permission(
            'revoke_flip_006', 'feature:ranking:view', 'admin'
        )
        assert result is True

        up = UserPermission.query.filter_by(
            username='revoke_flip_006', permission_id=perm.id
        ).first()
        assert up.granted is False

    def test_PERM_SVC_007_revoke_nonexistent_key(self, app, db, app_context):
        """[PERM_SVC-007] Revoke returns False for unknown key."""
        from services.permission_service import PermissionService

        _create_user(db, 'revoke_bad_007')
        result = PermissionService.revoke_permission(
            'revoke_bad_007', 'nonexistent:key', 'admin'
        )
        assert result is False

    def test_PERM_SVC_008_revoke_overrides_role_permission(self, app, db, app_context):
        """[PERM_SVC-008] Revoke blocks a permission even if role grants it."""
        from services.permission_service import PermissionService

        user = _create_user(db, 'revoke_role_008')
        _assign_role(db, 'revoke_role_008', 'researcher')

        # Researcher has feature:ranking:view via role
        assert PermissionService.check_permission('revoke_role_008', 'feature:ranking:view') is True

        PermissionService.revoke_permission(
            'revoke_role_008', 'feature:ranking:view', 'admin'
        )
        assert PermissionService.check_permission('revoke_role_008', 'feature:ranking:view') is False


# ===========================================================================
# Assign / Unassign Role
# ===========================================================================

class TestAssignRole:
    """Tests for PermissionService.assign_role."""

    def test_PERM_SVC_010_assign_role_success(self, app, db, app_context):
        """[PERM_SVC-010] Assign a known role to a user."""
        from services.permission_service import PermissionService

        _create_user(db, 'assign_010')
        result = PermissionService.assign_role('assign_010', 'researcher', 'admin')
        assert result is True

        assert PermissionService.user_has_role('assign_010', 'researcher') is True

    def test_PERM_SVC_011_assign_role_already_assigned(self, app, db, app_context):
        """[PERM_SVC-011] Assigning same role twice returns True (idempotent)."""
        from services.permission_service import PermissionService

        _create_user(db, 'assign_twice_011')
        PermissionService.assign_role('assign_twice_011', 'evaluator', 'admin')
        result = PermissionService.assign_role('assign_twice_011', 'evaluator', 'admin')
        assert result is True

    def test_PERM_SVC_012_assign_role_nonexistent(self, app, db, app_context):
        """[PERM_SVC-012] Assigning a non-existent role returns False."""
        from services.permission_service import PermissionService

        _create_user(db, 'assign_bad_012')
        result = PermissionService.assign_role(
            'assign_bad_012', 'nonexistent_role_xyz', 'admin'
        )
        assert result is False

    def test_PERM_SVC_013_assign_role_empty_name(self, app, db, app_context):
        """[PERM_SVC-013] Empty role name returns False."""
        from services.permission_service import PermissionService

        _create_user(db, 'assign_empty_013')
        assert PermissionService.assign_role('assign_empty_013', '', 'admin') is False
        assert PermissionService.assign_role('assign_empty_013', '   ', 'admin') is False

    def test_PERM_SVC_014_assign_role_creates_audit_log(self, app, db, app_context):
        """[PERM_SVC-014] Role assignment creates audit log."""
        from services.permission_service import PermissionService
        from db.models import PermissionAuditLog

        _create_user(db, 'assign_audit_014')
        PermissionService.assign_role('assign_audit_014', 'admin', 'super_admin')

        log = PermissionAuditLog.query.filter_by(
            action='ROLE_ASSIGN',
            target_username='assign_audit_014',
            admin_username='super_admin'
        ).first()
        assert log is not None


class TestUnassignRole:
    """Tests for PermissionService.unassign_role."""

    def test_PERM_SVC_015_unassign_role_success(self, app, db, app_context):
        """[PERM_SVC-015] Unassign an assigned role."""
        from services.permission_service import PermissionService

        _create_user(db, 'unassign_015')
        PermissionService.assign_role('unassign_015', 'researcher', 'admin')
        assert PermissionService.user_has_role('unassign_015', 'researcher') is True

        result = PermissionService.unassign_role('unassign_015', 'researcher', 'admin')
        assert result is True
        assert PermissionService.user_has_role('unassign_015', 'researcher') is False

    def test_PERM_SVC_016_unassign_role_not_assigned(self, app, db, app_context):
        """[PERM_SVC-016] Unassigning a role not assigned returns True (no-op)."""
        from services.permission_service import PermissionService

        _create_user(db, 'unassign_noop_016')
        result = PermissionService.unassign_role('unassign_noop_016', 'admin', 'admin')
        assert result is True

    def test_PERM_SVC_017_unassign_role_nonexistent(self, app, db, app_context):
        """[PERM_SVC-017] Unassigning a nonexistent role returns False."""
        from services.permission_service import PermissionService

        _create_user(db, 'unassign_bad_017')
        result = PermissionService.unassign_role(
            'unassign_bad_017', 'nonexistent_xyz', 'admin'
        )
        assert result is False

    def test_PERM_SVC_018_unassign_role_empty(self, app, db, app_context):
        """[PERM_SVC-018] Empty role name returns False."""
        from services.permission_service import PermissionService

        _create_user(db, 'unassign_empty_018')
        assert PermissionService.unassign_role('unassign_empty_018', '', 'admin') is False


# ===========================================================================
# user_has_role
# ===========================================================================

class TestUserHasRole:
    """Tests for PermissionService.user_has_role."""

    def test_PERM_SVC_020_user_has_role_true(self, app, db, app_context):
        """[PERM_SVC-020] Returns True when user has the role."""
        from services.permission_service import PermissionService

        _create_user(db, 'has_role_020')
        _assign_role(db, 'has_role_020', 'admin')
        assert PermissionService.user_has_role('has_role_020', 'admin') is True

    def test_PERM_SVC_021_user_has_role_false(self, app, db, app_context):
        """[PERM_SVC-021] Returns False when user lacks the role."""
        from services.permission_service import PermissionService

        _create_user(db, 'no_role_021')
        assert PermissionService.user_has_role('no_role_021', 'admin') is False

    def test_PERM_SVC_022_user_has_role_empty_inputs(self, app, db, app_context):
        """[PERM_SVC-022] Returns False for empty username or role_name."""
        from services.permission_service import PermissionService

        assert PermissionService.user_has_role('', 'admin') is False
        assert PermissionService.user_has_role('someone', '') is False
        assert PermissionService.user_has_role(None, 'admin') is False
        assert PermissionService.user_has_role('someone', None) is False


# ===========================================================================
# get_user_permissions (extended)
# ===========================================================================

class TestGetUserPermissionsExtended:
    """Extended tests for get_user_permissions."""

    def test_PERM_SVC_025_empty_username(self, app, db, app_context):
        """[PERM_SVC-025] Empty username returns empty list."""
        from services.permission_service import PermissionService

        assert PermissionService.get_user_permissions('') == []
        assert PermissionService.get_user_permissions(None) == []

    def test_PERM_SVC_026_combines_role_and_direct_grants(self, app, db, app_context):
        """[PERM_SVC-026] Merges role permissions with direct grants."""
        from services.permission_service import PermissionService

        _create_user(db, 'combined_026')
        _assign_role(db, 'combined_026', 'evaluator')

        # Evaluator gets feature:ranking:view via role.
        # Grant an additional admin permission directly.
        PermissionService.grant_permission(
            'combined_026', 'admin:users:manage', 'admin'
        )

        perms = PermissionService.get_user_permissions('combined_026')
        assert 'feature:ranking:view' in perms
        assert 'admin:users:manage' in perms

    def test_PERM_SVC_027_direct_deny_removes_role_permission(self, app, db, app_context):
        """[PERM_SVC-027] Direct deny removes a role-granted permission."""
        from services.permission_service import PermissionService

        _create_user(db, 'deny_remove_027')
        _assign_role(db, 'deny_remove_027', 'evaluator')

        PermissionService.revoke_permission(
            'deny_remove_027', 'feature:ranking:view', 'admin'
        )

        perms = PermissionService.get_user_permissions('deny_remove_027')
        assert 'feature:ranking:view' not in perms


# ===========================================================================
# check_permission edge cases
# ===========================================================================

class TestCheckPermissionEdgeCases:
    """Edge cases for check_permission."""

    def test_PERM_SVC_030_empty_username_denied(self, app, db, app_context):
        """[PERM_SVC-030] Empty username always returns False."""
        from services.permission_service import PermissionService

        assert PermissionService.check_permission('', 'feature:ranking:view') is False
        assert PermissionService.check_permission(None, 'feature:ranking:view') is False

    def test_PERM_SVC_031_empty_permission_key_denied(self, app, db, app_context):
        """[PERM_SVC-031] Empty permission key always returns False."""
        from services.permission_service import PermissionService

        _create_user(db, 'empty_perm_031')
        assert PermissionService.check_permission('empty_perm_031', '') is False
        assert PermissionService.check_permission('empty_perm_031', None) is False


# ===========================================================================
# get_all_permissions / get_all_roles
# ===========================================================================

class TestGetAllPermissionsAndRoles:
    """Tests for get_all_permissions and get_all_roles."""

    def test_PERM_SVC_035_get_all_permissions(self, app, db, app_context):
        """[PERM_SVC-035] Returns all seeded permissions."""
        from services.permission_service import PermissionService

        perms = PermissionService.get_all_permissions()
        assert isinstance(perms, list)
        assert len(perms) > 0
        assert all('permission_key' in p for p in perms)
        assert all('display_name' in p for p in perms)
        assert all('category' in p for p in perms)

    def test_PERM_SVC_036_get_all_roles(self, app, db, app_context):
        """[PERM_SVC-036] Returns all seeded roles with their permissions."""
        from services.permission_service import PermissionService

        roles = PermissionService.get_all_roles()
        assert isinstance(roles, list)
        assert len(roles) >= 3  # admin, researcher, evaluator at minimum
        role_names = [r['role_name'] for r in roles]
        assert 'admin' in role_names
        assert 'researcher' in role_names
        assert 'evaluator' in role_names
        # Each role dict should have permissions list
        admin_role = next(r for r in roles if r['role_name'] == 'admin')
        assert 'permissions' in admin_role
        assert len(admin_role['permissions']) > 0


# ===========================================================================
# create_role
# ===========================================================================

class TestCreateRole:
    """Tests for PermissionService.create_role."""

    def test_PERM_SVC_040_create_role_success(self, app, db, app_context):
        """[PERM_SVC-040] Create a new role with permissions."""
        from services.permission_service import PermissionService

        result = PermissionService.create_role(
            role_name='custom-test-role',
            display_name='Custom Test Role',
            description='A test role',
            permission_keys=['feature:ranking:view'],
            admin_username='admin'
        )

        assert result['role_name'] == 'custom-test-role'
        assert result['display_name'] == 'Custom Test Role'
        assert 'feature:ranking:view' in result['permissions']

    def test_PERM_SVC_041_create_role_empty_name_fails(self, app, db, app_context):
        """[PERM_SVC-041] Empty role_name raises ValidationError."""
        from services.permission_service import PermissionService
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            PermissionService.create_role(
                role_name='',
                display_name='Empty',
                description=None,
                permission_keys=None,
                admin_username='admin'
            )

    def test_PERM_SVC_042_create_role_duplicate_fails(self, app, db, app_context):
        """[PERM_SVC-042] Duplicate role name raises ConflictError."""
        from services.permission_service import PermissionService
        from decorators.error_handler import ConflictError

        with pytest.raises(ConflictError):
            PermissionService.create_role(
                role_name='admin',
                display_name='Admin Duplicate',
                description=None,
                permission_keys=None,
                admin_username='admin'
            )

    def test_PERM_SVC_043_create_role_invalid_name_format(self, app, db, app_context):
        """[PERM_SVC-043] Invalid role name format raises ValidationError."""
        from services.permission_service import PermissionService
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            PermissionService.create_role(
                role_name='INVALID NAME!',
                display_name='Bad Name',
                description=None,
                permission_keys=None,
                admin_username='admin'
            )

    def test_PERM_SVC_044_create_role_unknown_permission_keys(self, app, db, app_context):
        """[PERM_SVC-044] Unknown permission keys raise ValidationError."""
        from services.permission_service import PermissionService
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError):
            PermissionService.create_role(
                role_name='role-with-bad-perms',
                display_name='Bad Perms',
                description=None,
                permission_keys=['nonexistent:perm:xyz'],
                admin_username='admin'
            )

    def test_PERM_SVC_045_create_role_no_permissions(self, app, db, app_context):
        """[PERM_SVC-045] Create role with no permissions succeeds."""
        from services.permission_service import PermissionService

        result = PermissionService.create_role(
            role_name='empty-perms-role',
            display_name='No Perms',
            description='Role without permissions',
            permission_keys=None,
            admin_username='admin'
        )

        assert result['role_name'] == 'empty-perms-role'
        assert result['permissions'] == []


# ===========================================================================
# set_role_permissions
# ===========================================================================

class TestSetRolePermissions:
    """Tests for PermissionService.set_role_permissions."""

    def test_PERM_SVC_050_set_role_permissions_replace(self, app, db, app_context):
        """[PERM_SVC-050] Replace permissions on a role."""
        from services.permission_service import PermissionService

        # Create a custom role first
        PermissionService.create_role(
            role_name='settable-role',
            display_name='Settable',
            description=None,
            permission_keys=['feature:ranking:view'],
            admin_username='admin'
        )

        result = PermissionService.set_role_permissions(
            role_name='settable-role',
            permission_keys=['feature:rating:view', 'feature:rating:edit'],
            admin_username='admin'
        )

        assert 'feature:rating:view' in result['permissions']
        assert 'feature:rating:edit' in result['permissions']
        assert 'feature:ranking:view' not in result['permissions']

    def test_PERM_SVC_051_set_role_permissions_not_found(self, app, db, app_context):
        """[PERM_SVC-051] Non-existent role raises NotFoundError."""
        from services.permission_service import PermissionService
        from decorators.error_handler import NotFoundError

        with pytest.raises(NotFoundError):
            PermissionService.set_role_permissions(
                role_name='nonexistent-role-xyz',
                permission_keys=[],
                admin_username='admin'
            )

    def test_PERM_SVC_052_set_role_permissions_empty_clears(self, app, db, app_context):
        """[PERM_SVC-052] Setting empty permissions list clears all."""
        from services.permission_service import PermissionService

        PermissionService.create_role(
            role_name='clearable-role',
            display_name='Clearable',
            description=None,
            permission_keys=['feature:ranking:view', 'feature:ranking:edit'],
            admin_username='admin'
        )

        result = PermissionService.set_role_permissions(
            role_name='clearable-role',
            permission_keys=[],
            admin_username='admin'
        )

        assert result['permissions'] == []


# ===========================================================================
# get_all_users_with_roles
# ===========================================================================

class TestGetAllUsersWithRoles:
    """Tests for PermissionService.get_all_users_with_roles."""

    def test_PERM_SVC_055_users_with_roles(self, app, db, app_context):
        """[PERM_SVC-055] Returns users that have roles assigned."""
        from services.permission_service import PermissionService

        user = _create_user(db, 'with_roles_055')
        _assign_role(db, 'with_roles_055', 'researcher')

        users = PermissionService.get_all_users_with_roles()
        assert isinstance(users, list)
        usernames = [u['username'] for u in users]
        assert 'with_roles_055' in usernames

        user_entry = next(u for u in users if u['username'] == 'with_roles_055')
        role_names = [r['role_name'] for r in user_entry['roles']]
        assert 'researcher' in role_names

    def test_PERM_SVC_056_user_without_roles_not_listed(self, app, db, app_context):
        """[PERM_SVC-056] Users without roles are not in the result."""
        from services.permission_service import PermissionService

        _create_user(db, 'no_roles_056')

        users = PermissionService.get_all_users_with_roles()
        usernames = [u['username'] for u in users]
        assert 'no_roles_056' not in usernames


# ===========================================================================
# get_user_roles (extended)
# ===========================================================================

class TestGetUserRolesExtended:
    """Extended tests for get_user_roles."""

    def test_PERM_SVC_058_empty_username_returns_empty(self, app, db, app_context):
        """[PERM_SVC-058] Empty username returns empty list."""
        from services.permission_service import PermissionService

        assert PermissionService.get_user_roles('') == []
        assert PermissionService.get_user_roles(None) == []

    def test_PERM_SVC_059_multiple_roles(self, app, db, app_context):
        """[PERM_SVC-059] User with multiple roles gets all returned."""
        from services.permission_service import PermissionService

        _create_user(db, 'multi_role_059')
        PermissionService.assign_role('multi_role_059', 'researcher', 'admin')
        PermissionService.assign_role('multi_role_059', 'evaluator', 'admin')

        roles = PermissionService.get_user_roles('multi_role_059')
        role_names = [r['role_name'] for r in roles]
        assert 'researcher' in role_names
        assert 'evaluator' in role_names

    def test_PERM_SVC_060_viewer_normalized_to_evaluator(self, app, db, app_context):
        """[PERM_SVC-060] 'viewer' role_name is normalized to 'evaluator' in output."""
        from services.permission_service import PermissionService
        from db.models import Role, UserRole

        _create_user(db, 'viewer_norm_060')

        # Create a 'viewer' role if it does not exist
        viewer = Role.query.filter_by(role_name='viewer').first()
        if not viewer:
            viewer = Role(role_name='viewer', display_name='Viewer', description='Viewer')
            db.session.add(viewer)
            db.session.commit()

        db.session.add(UserRole(
            username='viewer_norm_060',
            role_id=viewer.id,
            assigned_by='test',
            assigned_at=datetime.utcnow()
        ))
        db.session.commit()

        roles = PermissionService.get_user_roles('viewer_norm_060')
        role_names = [r['role_name'] for r in roles]
        assert 'evaluator' in role_names
        assert 'viewer' not in role_names
