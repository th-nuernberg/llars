"""
User Service

Handles all user-related business logic including:
- User creation and management
- API key validation
- User group management
- User authentication helpers
"""

from typing import Optional, Tuple
from uuid import uuid4
from datetime import datetime

from db.db import db
from services.user_profile_service import is_valid_collab_color, pick_collab_color


class UserService:
    """
    Core service for user management.

    Provides methods for user CRUD operations, authentication,
    and API key management.
    """

    @staticmethod
    def get_user_by_api_key(api_key: str) -> Optional['User']:
        """
        Get user by API key.

        Args:
            api_key: The API key to look up

        Returns:
            User object if found, None otherwise
        """
        if not api_key:
            return None

        # Import here to avoid circular imports
        from db.models import User

        return User.query.filter_by(api_key=api_key).first()

    @staticmethod
    def get_user_by_username(username: str) -> Optional['User']:
        """
        Get user by username.

        Args:
            username: The username to look up

        Returns:
            User object if found, None otherwise
        """
        if not username:
            return None

        from db.models import User

        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional['User']:
        """
        Get user by ID.

        Args:
            user_id: The user ID to look up

        Returns:
            User object if found, None otherwise
        """
        if not user_id:
            return None

        from db.models import User

        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def user_exists(username: str) -> bool:
        """
        Check if a user exists.

        Args:
            username: The username to check

        Returns:
            True if user exists, False otherwise
        """
        return UserService.get_user_by_username(username) is not None

    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, Optional['User'], Optional[str]]:
        """
        Validate API key and return result.

        Args:
            api_key: The API key to validate

        Returns:
            Tuple of (is_valid, user, error_message)
            - is_valid: True if API key is valid
            - user: User object if valid, None otherwise
            - error_message: Error message if invalid, None otherwise
        """
        if not api_key:
            return False, None, "API key is missing"

        user = UserService.get_user_by_api_key(api_key)

        if not user:
            return False, None, "Invalid API key"

        return True, user, None

    @staticmethod
    def create_user(
        username: str,
        password: str,
        api_key: Optional[str] = None,
        group_name: Optional[str] = None,
        collab_color: Optional[str] = None,
        avatar_seed: Optional[str] = None
    ) -> Tuple[bool, Optional['User'], Optional[str]]:
        """
        Create a new user.

        Args:
            username: Username for the new user
            password: Password for the new user
            api_key: Optional API key (generated if not provided)
            group_name: Optional group name (defaults to "Standard")

        Returns:
            Tuple of (success, user, error_message)
            - success: True if user was created
            - user: Created user object if successful, None otherwise
            - error_message: Error message if failed, None otherwise
        """
        from db.models import User

        # Validate input
        if not username or not password:
            return False, None, "Username and password are required"

        # Check if user already exists
        if UserService.user_exists(username):
            return False, None, "Username already exists"

        # Validate optional collab color
        if collab_color is not None:
            collab_color = collab_color.strip() or None
            if collab_color and not is_valid_collab_color(collab_color):
                return False, None, "Invalid collab color (expected #RRGGBB)"

        # Normalize optional avatar seed
        if avatar_seed is not None:
            avatar_seed = avatar_seed.strip() or None
            if avatar_seed and len(avatar_seed) > 32:
                return False, None, "Avatar seed must be <= 32 characters"

        # Generate API key if not provided
        if not api_key:
            api_key = str(uuid4())

        try:
            # Create new user
            new_user = User(username=username)
            new_user.set_password(password)
            new_user.api_key = api_key

            # Assign group
            if group_name:
                group = UserService.get_or_create_group(group_name)
            else:
                group = UserService.get_or_create_default_group()

            new_user.group = group
            new_user.collab_color = collab_color or pick_collab_color()
            if avatar_seed:
                new_user.avatar_seed = avatar_seed
            else:
                if hasattr(new_user, "get_avatar_seed"):
                    new_user.get_avatar_seed()

            db.session.add(new_user)
            db.session.commit()

            return True, new_user, None

        except Exception as e:
            db.session.rollback()
            return False, None, f"Error creating user: {str(e)}"

    @staticmethod
    def get_or_create_default_group() -> 'UserGroup':
        """
        Get or create the default user group.

        Returns:
            UserGroup object for "Standard" group
        """
        from db.models import UserGroup

        default_group = UserGroup.query.filter_by(name="Standard").first()
        if not default_group:
            default_group = UserGroup(name="Standard")
            db.session.add(default_group)
            db.session.commit()
        return default_group

    @staticmethod
    def get_or_create_group(group_name: str) -> Optional['UserGroup']:
        """
        Get or create a user group.

        Args:
            group_name: Name of the group

        Returns:
            UserGroup object if found or created, None if error
        """
        from db.models import UserGroup

        group = UserGroup.query.filter_by(name=group_name).first()
        if not group:
            try:
                group = UserGroup(name=group_name)
                db.session.add(group)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                return None
        return group

    @staticmethod
    def get_group_by_name(group_name: str) -> Optional['UserGroup']:
        """
        Get a user group by name.

        Args:
            group_name: Name of the group

        Returns:
            UserGroup object if found, None otherwise
        """
        from db.models import UserGroup

        return UserGroup.query.filter_by(name=group_name).first()

    @staticmethod
    def change_user_group(
        username: str,
        new_group_name: str,
        admin_user: 'User'
    ) -> Tuple[bool, Optional[str]]:
        """
        Change a user's group.

        Args:
            username: Username of the user to change
            new_group_name: Name of the new group
            admin_user: Admin user performing the action

        Returns:
            Tuple of (success, error_message)
            - success: True if group was changed
            - error_message: Error message if failed, None otherwise
        """
        # Check admin permission
        if not admin_user or admin_user.group.name != 'Admin':
            return False, "You do not have permission to change user groups"

        # Find user
        user = UserService.get_user_by_username(username)
        if not user:
            return False, "User not found"

        # Find new group
        new_group = UserService.get_group_by_name(new_group_name)
        if not new_group:
            return False, f"Group '{new_group_name}' does not exist"

        try:
            # Update user's group
            user.group = new_group
            db.session.commit()
            return True, None

        except Exception as e:
            db.session.rollback()
            return False, f"Error changing user group: {str(e)}"

    @staticmethod
    def get_all_users() -> list:
        """
        Get all users.

        Returns:
            List of all User objects
        """
        from db.models import User

        return User.query.all()

    @staticmethod
    def validate_uuid(uuid_string: str, version: int = 4) -> bool:
        """
        Validate if a string is a valid UUID.

        Args:
            uuid_string: String to validate
            version: UUID version (default: 4)

        Returns:
            True if valid UUID, False otherwise
        """
        import uuid

        try:
            uuid_obj = uuid.UUID(uuid_string, version=version)
            return str(uuid_obj) == uuid_string
        except ValueError:
            return False
