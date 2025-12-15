"""
Permission Service

Handles all permission-related business logic including:
- Permission checking (deny-by-default)
- User permission retrieval
- Role management
- Permission granting/revoking
- Audit logging

Performance optimizations with caching will be added in later phases.
"""

import re
from typing import List, Optional, Set, Dict, Any
from datetime import datetime
from sqlalchemy import select, and_, or_
from db.db import db
from db.tables import (
    Permission,
    Role,
    RolePermission,
    UserPermission,
    UserRole,
    PermissionAuditLog
)


class PermissionService:
    """
    Core service for permission management and checking.

    Implements a deny-by-default security model where:
    1. User must have explicit permission (via role or direct grant)
    2. Direct user permissions override role permissions
    3. Deny takes precedence over grant
    """

    @staticmethod
    def check_permission(username: str, permission_key: str) -> bool:
        """
        Check if a user has a specific permission.

        Logic:
        1. Check direct user permissions first (granted=False denies)
        2. If no direct permission, check role-based permissions
        3. Default to deny if no permission found

        Args:
            username: The username to check
            permission_key: The permission key (e.g., 'feature:mail_rating:view')

        Returns:
            True if permission is granted, False otherwise
        """
        if not username or not permission_key:
            return False

        # Get the permission ID
        permission = db.session.execute(
            select(Permission).where(Permission.permission_key == permission_key)
        ).scalar_one_or_none()

        if not permission:
            # Permission doesn't exist in system
            return False

        # 1. Check direct user permissions (highest priority)
        user_perm = db.session.execute(
            select(UserPermission).where(
                and_(
                    UserPermission.username == username,
                    UserPermission.permission_id == permission.id
                )
            )
        ).scalar_one_or_none()

        if user_perm is not None:
            # Direct permission exists - use its granted value
            return user_perm.granted

        # 2. Check role-based permissions
        # Get all roles for this user
        user_roles = db.session.execute(
            select(UserRole).where(UserRole.username == username)
        ).scalars().all()

        if not user_roles:
            # No roles assigned, no direct permission -> deny
            return False

        # Check if any of the user's roles have this permission
        role_ids = [ur.role_id for ur in user_roles]

        role_perm = db.session.execute(
            select(RolePermission).where(
                and_(
                    RolePermission.role_id.in_(role_ids),
                    RolePermission.permission_id == permission.id
                )
            )
        ).scalar_one_or_none()

        # If role has permission, grant it; otherwise deny
        return role_perm is not None

    @staticmethod
    def get_user_permissions(username: str) -> List[str]:
        """
        Get all effective permissions for a user.

        Combines:
        1. Permissions from all assigned roles
        2. Direct user permissions (granted=True)
        3. Removes permissions where direct user permission is granted=False

        Args:
            username: The username

        Returns:
            List of permission keys the user has
        """
        if not username:
            return []

        # Get role-based permissions
        role_permissions_query = (
            select(Permission.permission_key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(UserRole, UserRole.role_id == RolePermission.role_id)
            .where(UserRole.username == username)
        )

        role_perms = db.session.execute(role_permissions_query).scalars().all()
        role_perm_set = set(role_perms)

        # Get direct user permissions
        user_permissions_query = (
            select(Permission.permission_key, UserPermission.granted)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.username == username)
        )

        user_perms = db.session.execute(user_permissions_query).all()

        # Build final permission set
        final_permissions = role_perm_set.copy()

        for perm_key, granted in user_perms:
            if granted:
                # Add granted permission
                final_permissions.add(perm_key)
            else:
                # Remove denied permission
                final_permissions.discard(perm_key)

        return sorted(list(final_permissions))

    @staticmethod
    def get_user_roles(username: str) -> List[dict]:
        """
        Get all roles assigned to a user.

        Args:
            username: The username

        Returns:
            List of role dictionaries with id, role_name, and display_name
        """
        if not username:
            return []

        roles_query = (
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.username == username)
        )

        roles = db.session.execute(roles_query).scalars().all()

        return [
            {
                'id': role.id,
                'role_name': role.role_name,
                'display_name': role.display_name,
                'description': role.description
            }
            for role in roles
        ]

    @staticmethod
    def grant_permission(
        username: str,
        permission_key: str,
        admin_username: str
    ) -> bool:
        """
        Grant a permission directly to a user.

        Args:
            username: Target user
            permission_key: Permission to grant
            admin_username: Admin performing the action (for audit log)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get permission
            permission = db.session.execute(
                select(Permission).where(Permission.permission_key == permission_key)
            ).scalar_one_or_none()

            if not permission:
                return False

            # Check if user permission already exists
            user_perm = db.session.execute(
                select(UserPermission).where(
                    and_(
                        UserPermission.username == username,
                        UserPermission.permission_id == permission.id
                    )
                )
            ).scalar_one_or_none()

            if user_perm:
                # Update existing permission
                user_perm.granted = True
                user_perm.granted_at = datetime.now()
                user_perm.granted_by = admin_username
            else:
                # Create new permission
                user_perm = UserPermission(
                    username=username,
                    permission_id=permission.id,
                    granted=True,
                    granted_by=admin_username,
                    granted_at=datetime.now()
                )
                db.session.add(user_perm)

            # Log the action
            PermissionService._log_permission_change(
                action='GRANT',
                admin_username=admin_username,
                target_username=username,
                permission_key=permission_key,
                details={'permission_id': permission.id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error granting permission: {e}")
            return False

    @staticmethod
    def revoke_permission(
        username: str,
        permission_key: str,
        admin_username: str
    ) -> bool:
        """
        Revoke a permission from a user (set granted=False).

        This creates an explicit deny that overrides role permissions.

        Args:
            username: Target user
            permission_key: Permission to revoke
            admin_username: Admin performing the action

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get permission
            permission = db.session.execute(
                select(Permission).where(Permission.permission_key == permission_key)
            ).scalar_one_or_none()

            if not permission:
                return False

            # Check if user permission already exists
            user_perm = db.session.execute(
                select(UserPermission).where(
                    and_(
                        UserPermission.username == username,
                        UserPermission.permission_id == permission.id
                    )
                )
            ).scalar_one_or_none()

            if user_perm:
                # Update to deny
                user_perm.granted = False
                user_perm.granted_at = datetime.now()
                user_perm.granted_by = admin_username
            else:
                # Create explicit deny
                user_perm = UserPermission(
                    username=username,
                    permission_id=permission.id,
                    granted=False,
                    granted_by=admin_username,
                    granted_at=datetime.now()
                )
                db.session.add(user_perm)

            # Log the action
            PermissionService._log_permission_change(
                action='REVOKE',
                admin_username=admin_username,
                target_username=username,
                permission_key=permission_key,
                details={'permission_id': permission.id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error revoking permission: {e}")
            return False

    @staticmethod
    def assign_role(
        username: str,
        role_name: str,
        admin_username: str
    ) -> bool:
        """
        Assign a role to a user.

        Args:
            username: Target user
            role_name: Role to assign
            admin_username: Admin performing the action

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get role
            role = db.session.execute(
                select(Role).where(Role.role_name == role_name)
            ).scalar_one_or_none()

            if not role:
                return False

            # Check if already assigned
            existing = db.session.execute(
                select(UserRole).where(
                    and_(
                        UserRole.username == username,
                        UserRole.role_id == role.id
                    )
                )
            ).scalar_one_or_none()

            if existing:
                # Already assigned
                return True

            # Create assignment
            user_role = UserRole(
                username=username,
                role_id=role.id,
                assigned_at=datetime.now(),
                assigned_by=admin_username
            )
            db.session.add(user_role)

            # Log the action
            PermissionService._log_permission_change(
                action='ROLE_ASSIGN',
                admin_username=admin_username,
                target_username=username,
                permission_key=None,
                details={'role_name': role_name, 'role_id': role.id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error assigning role: {e}")
            return False

    @staticmethod
    def unassign_role(
        username: str,
        role_name: str,
        admin_username: str
    ) -> bool:
        """
        Remove a role from a user.

        Args:
            username: Target user
            role_name: Role to remove
            admin_username: Admin performing the action

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get role
            role = db.session.execute(
                select(Role).where(Role.role_name == role_name)
            ).scalar_one_or_none()

            if not role:
                return False

            # Find assignment
            user_role = db.session.execute(
                select(UserRole).where(
                    and_(
                        UserRole.username == username,
                        UserRole.role_id == role.id
                    )
                )
            ).scalar_one_or_none()

            if not user_role:
                # Not assigned
                return True

            # Remove assignment
            db.session.delete(user_role)

            # Log the action
            PermissionService._log_permission_change(
                action='ROLE_UNASSIGN',
                admin_username=admin_username,
                target_username=username,
                permission_key=None,
                details={'role_name': role_name, 'role_id': role.id}
            )

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error unassigning role: {e}")
            return False

    @staticmethod
    def _log_permission_change(
        action: str,
        admin_username: str,
        target_username: Optional[str] = None,
        permission_key: Optional[str] = None,
        role_name: Optional[str] = None,
        details: Optional[dict] = None
    ) -> None:
        """
        Internal method to log permission changes.

        Args:
            action: Type of action (GRANT, REVOKE, ROLE_ASSIGN, ROLE_UNASSIGN)
            admin_username: Who performed the action
            target_username: User affected by the action
            permission_key: Permission involved (if applicable)
            details: Additional details as JSON
        """
        try:
            log_entry = PermissionAuditLog(
                action=action,
                admin_username=admin_username,
                target_username=target_username,
                permission_key=permission_key,
                role_name=role_name,
                details=details,
                created_at=datetime.now()
            )
            db.session.add(log_entry)
            # Note: Commit is handled by calling method
        except Exception as e:
            print(f"Error logging permission change: {e}")

    @staticmethod
    def get_all_permissions() -> List[dict]:
        """
        Get all available permissions in the system.

        Returns:
            List of permission dictionaries
        """
        permissions = db.session.execute(
            select(Permission).order_by(Permission.category, Permission.permission_key)
        ).scalars().all()

        return [
            {
                'id': p.id,
                'permission_key': p.permission_key,
                'display_name': p.display_name,
                'category': p.category,
                'description': p.description
            }
            for p in permissions
        ]

    @staticmethod
    def get_all_roles() -> List[dict]:
        """
        Get all available roles in the system.

        Returns:
            List of role dictionaries
        """
        roles = db.session.execute(select(Role).order_by(Role.role_name)).scalars().all()

        role_ids = [r.id for r in roles]
        permissions_by_role_id: Dict[int, List[str]] = {rid: [] for rid in role_ids}

        if role_ids:
            rows = db.session.execute(
                select(RolePermission.role_id, Permission.permission_key)
                .join(Permission, Permission.id == RolePermission.permission_id)
                .where(RolePermission.role_id.in_(role_ids))
                .order_by(RolePermission.role_id, Permission.permission_key)
            ).all()

            for rid, perm_key in rows:
                permissions_by_role_id.setdefault(rid, []).append(perm_key)

        return [
            {
                'id': r.id,
                'role_name': r.role_name,
                'display_name': r.display_name,
                'description': r.description,
                'permissions': permissions_by_role_id.get(r.id, []),
            }
            for r in roles
        ]

    @staticmethod
    def create_role(
        role_name: str,
        display_name: str,
        description: Optional[str],
        permission_keys: Optional[List[str]],
        admin_username: str,
    ) -> dict:
        """Create a new role and optionally assign permissions."""
        from decorators.error_handler import ValidationError, ConflictError

        name = (role_name or '').strip().lower()
        disp = (display_name or '').strip()
        desc = (description or '').strip() or None

        if not name:
            raise ValidationError('role_name is required')
        if not disp:
            raise ValidationError('display_name is required')
        if not re.match(r'^[a-z0-9][a-z0-9_-]{0,99}$', name):
            raise ValidationError('role_name must match ^[a-z0-9][a-z0-9_-]{0,99}$')

        existing = db.session.execute(select(Role).where(Role.role_name == name)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Role '{name}' already exists")

        normalized_keys = sorted({(k or '').strip() for k in (permission_keys or []) if (k or '').strip()})
        perms = []
        if normalized_keys:
            perms = db.session.execute(
                select(Permission).where(Permission.permission_key.in_(normalized_keys))
            ).scalars().all()
            found = {p.permission_key for p in perms}
            missing = [k for k in normalized_keys if k not in found]
            if missing:
                raise ValidationError('Unknown permission keys', details={'missing': missing})

        try:
            role = Role(role_name=name, display_name=disp, description=desc, created_at=datetime.now())
            db.session.add(role)
            db.session.flush()

            for p in perms:
                db.session.add(RolePermission(role_id=role.id, permission_id=p.id))

            PermissionService._log_permission_change(
                action='ROLE_CREATE',
                admin_username=admin_username,
                role_name=name,
                details={'display_name': disp, 'permission_count': len(normalized_keys)},
            )

            db.session.commit()
            return {
                'id': role.id,
                'role_name': role.role_name,
                'display_name': role.display_name,
                'description': role.description,
                'permissions': normalized_keys,
            }
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def set_role_permissions(
        role_name: str,
        permission_keys: List[str],
        admin_username: str,
    ) -> dict:
        """Replace permissions assigned to a role."""
        from decorators.error_handler import ValidationError, NotFoundError

        name = (role_name or '').strip().lower()
        if not name:
            raise ValidationError('role_name is required')

        role = db.session.execute(select(Role).where(Role.role_name == name)).scalar_one_or_none()
        if not role:
            raise NotFoundError(f"Role '{name}' not found")

        normalized_keys = sorted({(k or '').strip() for k in (permission_keys or []) if (k or '').strip()})

        perms = []
        if normalized_keys:
            perms = db.session.execute(
                select(Permission).where(Permission.permission_key.in_(normalized_keys))
            ).scalars().all()
            found = {p.permission_key for p in perms}
            missing = [k for k in normalized_keys if k not in found]
            if missing:
                raise ValidationError('Unknown permission keys', details={'missing': missing})

        desired_perm_ids = {p.id for p in perms}

        existing = db.session.execute(
            select(RolePermission).where(RolePermission.role_id == role.id)
        ).scalars().all()
        existing_perm_ids = {rp.permission_id for rp in existing}

        to_add_ids = desired_perm_ids - existing_perm_ids
        to_remove_ids = existing_perm_ids - desired_perm_ids

        if to_remove_ids:
            db.session.execute(
                RolePermission.__table__.delete().where(
                    and_(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id.in_(to_remove_ids),
                    )
                )
            )

        if to_add_ids:
            for pid in sorted(to_add_ids):
                db.session.add(RolePermission(role_id=role.id, permission_id=pid))

        PermissionService._log_permission_change(
            action='ROLE_PERMISSIONS_SET',
            admin_username=admin_username,
            role_name=name,
            details={
                'granted': sorted([p.permission_key for p in perms if p.id in to_add_ids]),
                'revoked': sorted([
                    row[0]
                    for row in db.session.execute(
                        select(Permission.permission_key).where(Permission.id.in_(to_remove_ids))
                    ).all()
                ]),
                'permission_count': len(normalized_keys),
            },
        )
        try:
            db.session.commit()
            return {
                'id': role.id,
                'role_name': role.role_name,
                'display_name': role.display_name,
                'description': role.description,
                'permissions': normalized_keys,
            }
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def get_all_users_with_roles() -> List[dict]:
        """
        Get all users that have at least one role assigned.

        Returns:
            List of user dictionaries with username and their roles
        """
        # Get all unique usernames from user_roles
        user_roles = db.session.execute(
            select(UserRole.username, Role.id, Role.role_name, Role.display_name)
            .join(Role, Role.id == UserRole.role_id)
            .order_by(UserRole.username)
        ).all()

        # Group by username
        users_dict = {}
        for username, role_id, role_name, display_name in user_roles:
            if username not in users_dict:
                users_dict[username] = {
                    'username': username,
                    'roles': []
                }
            users_dict[username]['roles'].append({
                'id': role_id,
                'role_name': role_name,
                'display_name': display_name
            })

        return list(users_dict.values())
