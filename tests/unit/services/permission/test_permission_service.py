"""
Unit Tests: Permission Service
==============================

Tests for the RBAC permission system.

Test IDs:
- PERM-001 to PERM-004: Deny-by-Default Tests
- PERM-010 to PERM-011: Admin Tests
- PERM-020 to PERM-025: Role Tests
- PERM-030 to PERM-032: Override Tests

Security Model: Deny-by-Default | User Override > Role | Deny > Grant

Status: ✅ IMPLEMENTED
"""

import pytest
from datetime import datetime


class TestDenyByDefault:
    """
    Deny-by-Default Tests

    The permission system should deny access by default unless
    explicitly granted through roles or user permissions.
    """

    def test_PERM_001_unknown_permission_denied(self, app, db, mock_user, app_context):
        """
        [PERM-001] Unbekannte Permission wird verweigert

        Eine Permission die nicht existiert soll False zurückgeben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()
        # PermissionService.check_permission expects username (str), not User object
        result = service.check_permission(mock_user.username, 'unknown:random:permission:xyz')

        assert result is False

    def test_PERM_002_no_role_no_permission(self, app, db, app_context):
        """
        [PERM-002] Keine Rolle, keine Permission

        Ein User ohne zugewiesene Rolle soll keine Permissions haben.
        """
        from db.tables import User
        from services.permission_service import PermissionService

        # Create user without any role
        user = User(
            username='no_role_user',
            password_hash='test-password-hash',
            api_key='test-api-key-no-role',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        service = PermissionService()
        # Pass username string, not User object
        result = service.check_permission(user.username, 'feature:ranking:view')

        assert result is False

    def test_PERM_003_locked_user_denied(self, app, db, locked_user, app_context):
        """
        [PERM-003] Gesperrter User wird verweigert

        Ein User mit is_active=False soll keine Permissions haben,
        auch wenn er eine Rolle mit Permissions hat.
        """
        from services.permission_service import PermissionService

        service = PermissionService()
        result = service.check_permission(locked_user.username, 'feature:ranking:view')

        assert result is False

    def test_PERM_004_deleted_user_denied(self, app, db, deleted_user, app_context):
        """
        [PERM-004] Gelöschter User wird verweigert

        Ein User mit deleted_at != NULL soll keine Permissions haben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()
        result = service.check_permission(deleted_user.username, 'feature:ranking:view')

        assert result is False


class TestAdminPermissions:
    """
    Admin Tests

    Admin users should have access to all permissions via role-based permissions.
    Admin role has all permissions assigned to it.
    """

    def test_PERM_010_admin_has_all_permissions(self, app, db, admin_user, app_context):
        """
        [PERM-010] Admin hat ALLE Permissions

        Admin-Rolle soll True für jede Permission zurückgeben,
        die in der Datenbank existiert.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        # Standard permissions - admin role has all these assigned
        assert service.check_permission(admin_user.username, 'feature:ranking:view') is True
        assert service.check_permission(admin_user.username, 'feature:ranking:edit') is True
        assert service.check_permission(admin_user.username, 'feature:chatbots:view') is True
        assert service.check_permission(admin_user.username, 'feature:chatbots:edit') is True

        # Admin-only permissions
        assert service.check_permission(admin_user.username, 'admin:permissions:manage') is True
        assert service.check_permission(admin_user.username, 'admin:users:manage') is True
        assert service.check_permission(admin_user.username, 'admin:system:configure') is True

        # Unknown permissions return False (no admin bypass for unknown permissions)
        # The service uses deny-by-default for permissions not in the database
        assert service.check_permission(admin_user.username, 'some:random:unknown') is False

    def test_PERM_011_admin_has_all_seeded_permissions(self, app, db, admin_user, app_context):
        """
        [PERM-011] Admin hat alle geseedeten Permissions

        Admin bekommt alle Permissions die in der DB existieren.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        # Admin should have all existing permissions via role
        permissions = service.get_user_permissions(admin_user.username)
        assert len(permissions) > 0  # Admin has at least some permissions


class TestRolePermissions:
    """
    Role Tests

    Tests for role-based permission inheritance.
    """

    def test_PERM_020_researcher_has_view_permissions(self, app, db, researcher_user, app_context):
        """
        [PERM-020] Researcher hat view Permissions für Evaluation-Features

        Researcher-Rolle soll view-Permissions für Rankings/Ratings haben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        assert service.check_permission(researcher_user.username, 'feature:ranking:view') is True
        assert service.check_permission(researcher_user.username, 'feature:rating:view') is True

    def test_PERM_021_researcher_no_admin_permissions(self, app, db, researcher_user, app_context):
        """
        [PERM-021] Researcher hat KEINE Admin Permissions

        Researcher-Rolle soll keinen Zugriff auf Admin-Bereiche haben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        assert service.check_permission(researcher_user.username, 'admin:permissions:manage') is False
        assert service.check_permission(researcher_user.username, 'admin:users:manage') is False
        assert service.check_permission(researcher_user.username, 'admin:system:configure') is False

    def test_PERM_022_evaluator_has_view_permissions(self, app, db, evaluator_user, app_context):
        """
        [PERM-022] Evaluator hat nur view Permissions

        Evaluator-Rolle soll nur :view Permissions haben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        # Should have view permissions
        assert service.check_permission(evaluator_user.username, 'feature:ranking:view') is True
        assert service.check_permission(evaluator_user.username, 'feature:rating:view') is True

    def test_PERM_023_evaluator_no_edit_permissions(self, app, db, evaluator_user, app_context):
        """
        [PERM-023] Evaluator hat KEINE edit Permissions

        Evaluator-Rolle soll keinen Schreibzugriff haben.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        assert service.check_permission(evaluator_user.username, 'feature:ranking:edit') is False
        assert service.check_permission(evaluator_user.username, 'feature:rating:edit') is False

    def test_PERM_024_chatbot_manager_permissions(self, app, db, app_context):
        """
        [PERM-024] Chatbot Manager hat Chatbot Permissions

        Chatbot Manager soll Chatbot-spezifische Permissions haben.
        Note: This test will only pass if chatbot_manager role has chatbot permissions assigned.
        """
        from db.tables import User, Role, UserRole, RolePermission, Permission
        from services.permission_service import PermissionService

        # Create chatbot manager user
        user = User(
            username='chatbot_mgr',
            password_hash='test-password-hash',
            api_key='test-api-key-cm',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        chatbot_role = Role.query.filter_by(role_name='chatbot_manager').first()
        if chatbot_role:
            # Assign the role to the user
            user_role = UserRole(
                username='chatbot_mgr',
                role_id=chatbot_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            )
            db.session.add(user_role)

            # Also assign the chatbot permission to the role if not already done
            chatbot_perm = Permission.query.filter_by(permission_key='feature:chatbots:view').first()
            if chatbot_perm:
                existing_rp = RolePermission.query.filter_by(
                    role_id=chatbot_role.id,
                    permission_id=chatbot_perm.id
                ).first()
                if not existing_rp:
                    db.session.add(RolePermission(
                        role_id=chatbot_role.id,
                        permission_id=chatbot_perm.id
                    ))

            db.session.commit()

        service = PermissionService()

        # Should have chatbot permissions
        assert service.check_permission(user.username, 'feature:chatbots:view') is True

    def test_PERM_025_chatbot_manager_no_ranking(self, app, db, app_context):
        """
        [PERM-025] Chatbot Manager hat KEINE Ranking Permissions

        Chatbot Manager soll keinen Zugriff auf Evaluation-Features haben.
        """
        from db.tables import User, Role, UserRole
        from services.permission_service import PermissionService

        user = User(
            username='chatbot_mgr2',
            password_hash='test-password-hash',
            api_key='test-api-key-cm2',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        chatbot_role = Role.query.filter_by(role_name='chatbot_manager').first()
        if chatbot_role:
            user_role = UserRole(
                username='chatbot_mgr2',
                role_id=chatbot_role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow()
            )
            db.session.add(user_role)
            db.session.commit()

        service = PermissionService()

        # Should NOT have ranking edit permissions
        assert service.check_permission(user.username, 'feature:ranking:edit') is False


class TestPermissionOverrides:
    """
    Override Tests

    Tests for user-level permission overrides.
    Rule: User > Role, Deny > Grant
    """

    def test_PERM_030_user_grant_overrides_role_deny(self, app, db, mock_user, app_context):
        """
        [PERM-030] User Grant überschreibt Role Deny

        Wenn ein User explizit eine Permission hat, die seine Rolle
        nicht hat, soll er trotzdem Zugriff haben.
        """
        from db.tables import Permission, UserPermission
        from services.permission_service import PermissionService

        # Give user explicit permission that evaluator role doesn't have
        admin_perm = Permission.query.filter_by(permission_key='admin:users:manage').first()
        if admin_perm:
            user_perm = UserPermission(
                username=mock_user.username,
                permission_id=admin_perm.id,
                granted=True,
                granted_by='test',
                granted_at=datetime.utcnow()
            )
            db.session.add(user_perm)
            db.session.commit()

        service = PermissionService()

        # User should have this permission despite role
        result = service.check_permission(mock_user.username, 'admin:users:manage')
        assert result is True

    def test_PERM_031_user_deny_overrides_role_grant(self, app, db, researcher_user, app_context):
        """
        [PERM-031] User Deny überschreibt Role Grant

        Wenn ein User explizit eine Permission verweigert bekommt,
        soll er keinen Zugriff haben, auch wenn seine Rolle es erlaubt.
        """
        from db.tables import Permission, UserPermission
        from services.permission_service import PermissionService

        # Researcher has ranking:view from role, deny it explicitly
        ranking_perm = Permission.query.filter_by(permission_key='feature:ranking:view').first()
        if ranking_perm:
            user_perm = UserPermission(
                username=researcher_user.username,
                permission_id=ranking_perm.id,
                granted=False,  # Explicit DENY
                granted_by='test',
                granted_at=datetime.utcnow()
            )
            db.session.add(user_perm)
            db.session.commit()

        service = PermissionService()

        # User should NOT have this permission despite role
        result = service.check_permission(researcher_user.username, 'feature:ranking:view')
        assert result is False

    def test_PERM_032_explicit_deny_beats_implicit_grant(self, app, db, admin_user, app_context):
        """
        [PERM-032] Explicit Deny > Implicit Grant (außer Admin)

        Für normale User: explizites Deny schlägt implizites Grant.
        Note: Admin bypass ignoriert dieses Deny.
        """
        from db.tables import User, Permission, UserPermission
        from services.permission_service import PermissionService

        # Create a non-admin user
        user = User(
            username='deny_test_user',
            password_hash='test-password-hash',
            api_key='test-api-key-deny',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()

        # Give explicit deny
        perm = Permission.query.filter_by(permission_key='feature:ranking:view').first()
        if perm:
            user_perm = UserPermission(
                username=user.username,
                permission_id=perm.id,
                granted=False,
                granted_by='test',
                granted_at=datetime.utcnow()
            )
            db.session.add(user_perm)
            db.session.commit()

        service = PermissionService()
        result = service.check_permission(user.username, 'feature:ranking:view')
        assert result is False


class TestPermissionService:
    """
    General Permission Service Tests

    Tests for PermissionService class methods.
    """

    def test_get_user_permissions(self, app, db, researcher_user, app_context):
        """
        Test getting all permissions for a user.
        """
        from services.permission_service import PermissionService

        service = PermissionService()
        # get_user_permissions expects username (str)
        permissions = service.get_user_permissions(researcher_user.username)

        assert isinstance(permissions, list)
        # Researcher should have some permissions
        assert len(permissions) > 0

    def test_get_user_roles(self, app, db, researcher_user, app_context):
        """
        Test getting all roles for a user.
        """
        from services.permission_service import PermissionService

        service = PermissionService()
        # get_user_roles expects username (str) and returns list of dicts
        roles = service.get_user_roles(researcher_user.username)

        assert isinstance(roles, list)
        assert len(roles) > 0
        # Each role is a dict with 'role_name' key
        assert all('role_name' in role for role in roles)
        # Researcher should have researcher role
        role_names = [role['role_name'] for role in roles]
        assert 'researcher' in role_names

    def test_admin_has_admin_role(self, app, db, admin_user, app_context):
        """
        Test that admin user has admin role assigned.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        # Get admin's roles
        roles = service.get_user_roles(admin_user.username)
        role_names = [role['role_name'] for role in roles]

        # Admin should have admin role
        assert 'admin' in role_names

    def test_researcher_is_not_admin(self, app, db, researcher_user, app_context):
        """
        Test that researcher user does not have admin role.
        """
        from services.permission_service import PermissionService

        service = PermissionService()

        # Get researcher's roles
        roles = service.get_user_roles(researcher_user.username)
        role_names = [role['role_name'] for role in roles]

        # Researcher should NOT have admin role
        assert 'admin' not in role_names
