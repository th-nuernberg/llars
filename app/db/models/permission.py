"""Permission and Role database models."""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from db import db


class Permission(db.Model):
    """Defines available permissions in the system"""
    __tablename__ = 'permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    permission_key: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(db.String(50), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)


class Role(db.Model):
    """Collection of permissions (e.g., 'researcher', 'admin')"""
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(db.String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)


class RolePermission(db.Model):
    """Maps permissions to roles"""
    __tablename__ = 'role_permissions'

    role_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    permission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), primary_key=True)

    role = db.relationship('Role', backref='permissions')
    permission = db.relationship('Permission')


class UserPermission(db.Model):
    """Direct user permissions (overrides role permissions)"""
    __tablename__ = 'user_permissions'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(db.String(255), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)
    granted: Mapped[bool] = mapped_column(db.Boolean, default=True)
    granted_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    granted_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    permission = db.relationship('Permission')

    __table_args__ = (
        db.UniqueConstraint('username', 'permission_id', name='unique_user_permission'),
    )


class UserRole(db.Model):
    """Maps users to roles"""
    __tablename__ = 'user_roles'

    username: Mapped[str] = mapped_column(db.String(255), primary_key=True)
    role_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), primary_key=True)
    assigned_by: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now)

    role = db.relationship('Role', backref='users')


class PermissionAuditLog(db.Model):
    """Audit trail for all permission changes"""
    __tablename__ = 'permission_audit_log'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True, autoincrement=True)
    action: Mapped[str] = mapped_column(db.String(50), nullable=False)
    admin_username: Mapped[str] = mapped_column(db.String(255), nullable=False)
    target_username: Mapped[Optional[str]] = mapped_column(db.String(255), nullable=True)
    permission_key: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    role_name: Mapped[Optional[str]] = mapped_column(db.String(100), nullable=True)
    details: Mapped[Optional[str]] = mapped_column(db.JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.now, index=True)
