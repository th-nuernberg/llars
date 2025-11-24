#!/usr/bin/env python3
from app.db.tables import UserRole, Role
from app.db import db
from app.main import app

with app.app_context():
    # Check admin user roles
    admin_roles = UserRole.query.filter_by(username='admin').all()
    print('Admin User Roles:')
    if admin_roles:
        for ur in admin_roles:
            role = Role.query.get(ur.role_id)
            print(f'  - Role: {role.role_name} (ID: {role.id})')
    else:
        print('  NO ROLES ASSIGNED!')

    # Check admin role permissions
    admin_role = Role.query.filter_by(role_name='admin').first()
    if admin_role:
        print(f'\nAdmin Role has {len(admin_role.permissions)} permissions')
        for perm in admin_role.permissions[:5]:
            print(f'  - {perm.permission_key}')
    else:
        print('Admin role not found!')
