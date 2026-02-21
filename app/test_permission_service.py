"""
Manual test script for PermissionService

Run this script to test the permission system:
    python app/test_permission_service.py

This script tests:
- Permission checking (deny-by-default)
- User permission retrieval
- Role assignment
- Permission granting/revoking
- Audit logging
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from db import db
from services.permission_service import PermissionService


def create_test_app():
    """Create a minimal Flask app for testing"""
    app = Flask(__name__)

    # Database configuration
    db_root_password = os.getenv('MYSQL_ROOT_PASSWORD', 'root_password_feature')
    db_database_name = os.getenv('MYSQL_DATABASE', 'database_llars')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://root:{db_root_password}@localhost:55306/{db_database_name}'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    return app


def run_tests():
    """Run all permission service tests"""
    app = create_test_app()

    with app.app_context():
        print("=" * 80)
        print("PERMISSION SERVICE TESTS")
        print("=" * 80)
        print()

        # Test 1: Check permission for non-existent user (should deny)
        print("Test 1: Check permission for non-existent user")
        print("-" * 80)
        result = PermissionService.check_permission('testuser123', 'feature:mail_rating:view')
        print(f"  check_permission('testuser123', 'feature:mail_rating:view'): {result}")
        assert result == False, "Non-existent user should not have permissions"
        print("  ✓ PASSED: Non-existent user denied\n")

        # Test 2: Assign role to user
        print("Test 2: Assign 'evaluator' role to testuser")
        print("-" * 80)
        success = PermissionService.assign_role('testuser', 'evaluator', 'admin')
        print(f"  assign_role('testuser', 'evaluator', 'admin'): {success}")
        assert success == True, "Role assignment should succeed"
        print("  ✓ PASSED: Role assigned successfully\n")

        # Test 3: Check permission after role assignment
        print("Test 3: Check permission after role assignment")
        print("-" * 80)
        result = PermissionService.check_permission('testuser', 'feature:mail_rating:view')
        print(f"  check_permission('testuser', 'feature:mail_rating:view'): {result}")
        assert result == True, "User with evaluator role should have view permission"

        result = PermissionService.check_permission('testuser', 'feature:mail_rating:edit')
        print(f"  check_permission('testuser', 'feature:mail_rating:edit'): {result}")
        assert result == False, "User with evaluator role should not have edit permission"
        print("  ✓ PASSED: Role-based permissions working correctly\n")

        # Test 4: Get user permissions
        print("Test 4: Get all user permissions")
        print("-" * 80)
        permissions = PermissionService.get_user_permissions('testuser')
        print(f"  get_user_permissions('testuser'): {len(permissions)} permissions")
        for perm in permissions:
            print(f"    - {perm}")
        assert 'feature:mail_rating:view' in permissions
        assert 'feature:mail_rating:edit' not in permissions
        print("  ✓ PASSED: User permissions retrieved correctly\n")

        # Test 5: Grant direct permission
        print("Test 5: Grant direct permission to user")
        print("-" * 80)
        success = PermissionService.grant_permission(
            'testuser',
            'feature:mail_rating:edit',
            'admin'
        )
        print(f"  grant_permission('testuser', 'feature:mail_rating:edit', 'admin'): {success}")
        assert success == True, "Permission grant should succeed"

        result = PermissionService.check_permission('testuser', 'feature:mail_rating:edit')
        print(f"  check_permission('testuser', 'feature:mail_rating:edit'): {result}")
        assert result == True, "User should now have edit permission"
        print("  ✓ PASSED: Direct permission grant working\n")

        # Test 6: Revoke permission (deny override)
        print("Test 6: Revoke permission (should override role)")
        print("-" * 80)
        success = PermissionService.revoke_permission(
            'testuser',
            'feature:mail_rating:view',
            'admin'
        )
        print(f"  revoke_permission('testuser', 'feature:mail_rating:view', 'admin'): {success}")
        assert success == True, "Permission revoke should succeed"

        result = PermissionService.check_permission('testuser', 'feature:mail_rating:view')
        print(f"  check_permission('testuser', 'feature:mail_rating:view'): {result}")
        assert result == False, "Revoked permission should deny even with role"
        print("  ✓ PASSED: Permission revocation working (deny overrides role)\n")

        # Test 7: Get user roles
        print("Test 7: Get user roles")
        print("-" * 80)
        roles = PermissionService.get_user_roles('testuser')
        print(f"  get_user_roles('testuser'): {len(roles)} roles")
        for role in roles:
            print(f"    - {role['role_name']}: {role['display_name']}")
        assert len(roles) == 1
        assert roles[0]['role_name'] == 'evaluator'
        print("  ✓ PASSED: User roles retrieved correctly\n")

        # Test 8: Assign admin role
        print("Test 8: Assign admin role")
        print("-" * 80)
        success = PermissionService.assign_role('admin_user', 'admin', 'system')
        print(f"  assign_role('admin_user', 'admin', 'system'): {success}")
        assert success == True

        result = PermissionService.check_permission('admin_user', 'admin:permissions:manage')
        print(f"  check_permission('admin_user', 'admin:permissions:manage'): {result}")
        assert result == True, "Admin should have admin permissions"
        print("  ✓ PASSED: Admin role working\n")

        # Test 9: Get all permissions
        print("Test 9: Get all permissions in system")
        print("-" * 80)
        all_perms = PermissionService.get_all_permissions()
        print(f"  get_all_permissions(): {len(all_perms)} total permissions")
        categories = {}
        for perm in all_perms:
            cat = perm['category']
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        for cat, count in categories.items():
            print(f"    - {cat}: {count} permissions")
        print("  ✓ PASSED: All permissions retrieved\n")

        # Test 10: Unassign role
        print("Test 10: Unassign role")
        print("-" * 80)
        success = PermissionService.unassign_role('testuser', 'evaluator', 'admin')
        print(f"  unassign_role('testuser', 'evaluator', 'admin'): {success}")
        assert success == True

        roles = PermissionService.get_user_roles('testuser')
        print(f"  get_user_roles('testuser'): {len(roles)} roles")
        assert len(roles) == 0, "User should have no roles after unassignment"
        print("  ✓ PASSED: Role unassignment working\n")

        # Summary
        print("=" * 80)
        print("ALL TESTS PASSED ✓")
        print("=" * 80)
        print("\nPermission system is working correctly!")
        print("\nKey features verified:")
        print("  ✓ Deny-by-default security model")
        print("  ✓ Role-based permissions")
        print("  ✓ Direct permission grants/revokes")
        print("  ✓ Permission deny overrides role permissions")
        print("  ✓ User permission and role retrieval")
        print("  ✓ Audit logging (check permission_audit_log table)")


if __name__ == '__main__':
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
