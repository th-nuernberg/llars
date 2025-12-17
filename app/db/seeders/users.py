"""
User-related Seeders

Seeds user groups, bootstrap admin user, and related data.
"""
import os
import uuid


def seed_user_groups(db):
    """
    Seed default user groups (Standard, Admin).

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import UserGroup

    # Check if the groups already exist
    if not UserGroup.query.filter_by(name='Standard').first():
        standard_group = UserGroup(name='Standard')
        db.session.add(standard_group)
    if not UserGroup.query.filter_by(name='Admin').first():
        admin_group = UserGroup(name='Admin')
        db.session.add(admin_group)

    db.session.commit()
    print("User groups seeded successfully.")


def seed_bootstrap_admin(db):
    """
    Create the bootstrap admin user from environment variables.
    This runs on every startup but only creates the user if it doesn't exist.

    The admin user is created with:
    - Username: 'admin' (fixed, used by SYSTEM_ADMIN_API_KEY)
    - API Key: from SYSTEM_ADMIN_API_KEY env var
    - Group: Admin group

    The admin role assignment happens separately in permissions.py

    Args:
        db: SQLAlchemy database instance
    """
    # Lazy import to avoid circular dependencies
    from ..tables import User, UserGroup

    # Check if admin user already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        # Update API key if it changed
        system_api_key = os.getenv('SYSTEM_ADMIN_API_KEY')
        if system_api_key and existing_admin.api_key != system_api_key:
            existing_admin.api_key = system_api_key
            db.session.commit()
            print("Updated admin user API key from environment.")
        else:
            print("Bootstrap admin user already exists.")
        return

    # Get or create Admin group
    admin_group = UserGroup.query.filter_by(name='Admin').first()
    if not admin_group:
        admin_group = UserGroup(name='Admin')
        db.session.add(admin_group)
        db.session.flush()

    # Get API key from environment (or generate one)
    api_key = os.getenv('SYSTEM_ADMIN_API_KEY') or str(uuid.uuid4())

    # Create admin user
    admin_user = User(
        username='admin',
        password_hash='',  # Auth via Authentik, no local password
        api_key=api_key,
        group_id=admin_group.id
    )
    db.session.add(admin_user)
    db.session.commit()

    print(f"Created bootstrap admin user with API key from environment.")
    print(f"  Username: admin")
    print(f"  API Key: {api_key[:8]}...{api_key[-4:]}")


def seed_avatar_seeds(db) -> None:
    """
    Ensure all users have a stable avatar seed.

    This prevents per-request generation and keeps avatars consistent across sessions.
    """
    # Lazy import to avoid circular dependencies
    from ..tables import User

    users_missing_seed = User.query.filter(User.avatar_seed.is_(None)).all()
    if not users_missing_seed:
        return

    changed = False
    for user in users_missing_seed:
        if hasattr(user, "get_avatar_seed"):
            user.get_avatar_seed()
            changed = True

    if changed:
        db.session.commit()
        print("✅ Avatar seeds backfilled")
