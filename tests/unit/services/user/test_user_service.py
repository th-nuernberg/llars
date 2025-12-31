"""
Unit Tests: User Service
========================

Tests for the user management service.

Test IDs:
- USER-001 to USER-015: Lookup Methods
- USER-020 to USER-030: API Key Validation
- USER-040 to USER-060: User Creation
- USER-070 to USER-090: Group Management
- USER-100 to USER-110: Utility Methods
- USER-120 to USER-130: Profile Helpers

Status: Implemented
"""

import pytest
from uuid import uuid4


class TestUserLookup:
    """
    Lookup Methods Tests

    Tests for user lookup by various identifiers.
    """

    def test_USER_001_get_user_by_api_key_found(self, app, db, app_context):
        """
        [USER-001] Get User by API Key - Gefunden

        User mit gültigem API Key sollte gefunden werden.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create group and user
        group = UserGroup(name='TestGroup001')
        db.session.add(group)
        db.session.commit()

        user = User(username='testuser001')
        user.set_password('password123')
        user.api_key = 'test-api-key-001'
        user.group = group
        db.session.add(user)
        db.session.commit()

        # Test lookup
        found_user = UserService.get_user_by_api_key('test-api-key-001')

        assert found_user is not None
        assert found_user.username == 'testuser001'

    def test_USER_002_get_user_by_api_key_not_found(self, app, db, app_context):
        """
        [USER-002] Get User by API Key - Nicht gefunden

        Ungültiger API Key sollte None zurückgeben.
        """
        from services.user_service import UserService

        found_user = UserService.get_user_by_api_key('nonexistent-key')

        assert found_user is None

    def test_USER_003_get_user_by_api_key_empty(self, app, db, app_context):
        """
        [USER-003] Get User by API Key - Leer

        Leerer API Key sollte None zurückgeben.
        """
        from services.user_service import UserService

        assert UserService.get_user_by_api_key('') is None
        assert UserService.get_user_by_api_key(None) is None

    def test_USER_004_get_user_by_username_found(self, app, db, app_context):
        """
        [USER-004] Get User by Username - Gefunden

        User mit gültigem Username sollte gefunden werden.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup004')
        db.session.add(group)
        db.session.commit()

        user = User(username='findme_user')
        user.set_password('password123')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        found_user = UserService.get_user_by_username('findme_user')

        assert found_user is not None
        assert found_user.username == 'findme_user'

    def test_USER_005_get_user_by_username_not_found(self, app, db, app_context):
        """
        [USER-005] Get User by Username - Nicht gefunden

        Unbekannter Username sollte None zurückgeben.
        """
        from services.user_service import UserService

        found_user = UserService.get_user_by_username('nonexistent_user')

        assert found_user is None

    def test_USER_006_get_user_by_username_empty(self, app, db, app_context):
        """
        [USER-006] Get User by Username - Leer

        Leerer Username sollte None zurückgeben.
        """
        from services.user_service import UserService

        assert UserService.get_user_by_username('') is None
        assert UserService.get_user_by_username(None) is None

    def test_USER_007_get_user_by_id_found(self, app, db, app_context):
        """
        [USER-007] Get User by ID - Gefunden

        User mit gültiger ID sollte gefunden werden.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup007')
        db.session.add(group)
        db.session.commit()

        user = User(username='user_by_id')
        user.set_password('password123')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        user_id = user.id
        found_user = UserService.get_user_by_id(user_id)

        assert found_user is not None
        assert found_user.id == user_id

    def test_USER_008_get_user_by_id_not_found(self, app, db, app_context):
        """
        [USER-008] Get User by ID - Nicht gefunden

        Ungültige ID sollte None zurückgeben.
        """
        from services.user_service import UserService

        found_user = UserService.get_user_by_id(99999)

        assert found_user is None

    def test_USER_009_get_user_by_id_empty(self, app, db, app_context):
        """
        [USER-009] Get User by ID - Leer/None

        Leere ID sollte None zurückgeben.
        """
        from services.user_service import UserService

        assert UserService.get_user_by_id(0) is None
        assert UserService.get_user_by_id(None) is None

    def test_USER_010_user_exists_true(self, app, db, app_context):
        """
        [USER-010] User Exists - True

        Existierender User sollte True zurückgeben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup010')
        db.session.add(group)
        db.session.commit()

        user = User(username='exists_user')
        user.set_password('password123')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        assert UserService.user_exists('exists_user') is True

    def test_USER_011_user_exists_false(self, app, db, app_context):
        """
        [USER-011] User Exists - False

        Nicht existierender User sollte False zurückgeben.
        """
        from services.user_service import UserService

        assert UserService.user_exists('nonexistent_user_011') is False


class TestAPIKeyValidation:
    """
    API Key Validation Tests

    Tests for API key validation.
    """

    def test_USER_020_validate_api_key_valid(self, app, db, app_context):
        """
        [USER-020] Validate API Key - Gültig

        Gültiger API Key sollte (True, user, None) zurückgeben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup020')
        db.session.add(group)
        db.session.commit()

        user = User(username='validate_user')
        user.set_password('password123')
        user.api_key = 'valid-api-key-020'
        user.group = group
        db.session.add(user)
        db.session.commit()

        is_valid, found_user, error = UserService.validate_api_key('valid-api-key-020')

        assert is_valid is True
        assert found_user is not None
        assert found_user.username == 'validate_user'
        assert error is None

    def test_USER_021_validate_api_key_invalid(self, app, db, app_context):
        """
        [USER-021] Validate API Key - Ungültig

        Ungültiger API Key sollte (False, None, error) zurückgeben.
        """
        from services.user_service import UserService

        is_valid, found_user, error = UserService.validate_api_key('invalid-key-021')

        assert is_valid is False
        assert found_user is None
        assert error == "Invalid API key"

    def test_USER_022_validate_api_key_empty(self, app, db, app_context):
        """
        [USER-022] Validate API Key - Leer

        Leerer API Key sollte (False, None, error) zurückgeben.
        """
        from services.user_service import UserService

        is_valid, found_user, error = UserService.validate_api_key('')

        assert is_valid is False
        assert found_user is None
        assert error == "API key is missing"

    def test_USER_023_validate_api_key_none(self, app, db, app_context):
        """
        [USER-023] Validate API Key - None

        None API Key sollte (False, None, error) zurückgeben.
        """
        from services.user_service import UserService

        is_valid, found_user, error = UserService.validate_api_key(None)

        assert is_valid is False
        assert found_user is None
        assert error == "API key is missing"


class TestUserCreation:
    """
    User Creation Tests

    Tests for user creation functionality.
    """

    def test_USER_040_create_user_success(self, app, db, app_context):
        """
        [USER-040] Create User - Erfolgreich

        User sollte erfolgreich erstellt werden.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_040',
            password='secure_password'
        )

        assert success is True
        assert user is not None
        assert user.username == 'new_user_040'
        assert user.api_key is not None
        assert user.group is not None
        assert error is None

    def test_USER_041_create_user_with_api_key(self, app, db, app_context):
        """
        [USER-041] Create User - Mit API Key

        User mit explizitem API Key sollte erstellt werden.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_041',
            password='secure_password',
            api_key='explicit-api-key-041'
        )

        assert success is True
        assert user.api_key == 'explicit-api-key-041'

    def test_USER_042_create_user_with_group(self, app, db, app_context):
        """
        [USER-042] Create User - Mit Gruppe

        User mit spezifischer Gruppe sollte erstellt werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Create group first
        group = UserGroup(name='CustomGroup042')
        db.session.add(group)
        db.session.commit()

        success, user, error = UserService.create_user(
            username='new_user_042',
            password='secure_password',
            group_name='CustomGroup042'
        )

        assert success is True
        assert user.group.name == 'CustomGroup042'

    def test_USER_043_create_user_with_collab_color(self, app, db, app_context):
        """
        [USER-043] Create User - Mit Collab Color

        User mit gültiger Collab Color sollte erstellt werden.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_043',
            password='secure_password',
            collab_color='#FF5733'
        )

        assert success is True
        assert user.collab_color == '#FF5733'

    def test_USER_044_create_user_invalid_collab_color(self, app, db, app_context):
        """
        [USER-044] Create User - Ungültige Collab Color

        User mit ungültiger Collab Color sollte fehlschlagen.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_044',
            password='secure_password',
            collab_color='not-a-color'
        )

        assert success is False
        assert user is None
        assert "Invalid collab color" in error

    def test_USER_045_create_user_with_avatar_seed(self, app, db, app_context):
        """
        [USER-045] Create User - Mit Avatar Seed

        User mit Avatar Seed sollte erstellt werden.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_045',
            password='secure_password',
            avatar_seed='custom_seed_123'
        )

        assert success is True
        assert user.avatar_seed == 'custom_seed_123'

    def test_USER_046_create_user_avatar_seed_too_long(self, app, db, app_context):
        """
        [USER-046] Create User - Avatar Seed zu lang

        Avatar Seed > 32 Zeichen sollte fehlschlagen.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='new_user_046',
            password='secure_password',
            avatar_seed='x' * 33
        )

        assert success is False
        assert user is None
        assert "Avatar seed must be <= 32 characters" in error

    def test_USER_047_create_user_duplicate_username(self, app, db, app_context):
        """
        [USER-047] Create User - Doppelter Username

        Doppelter Username sollte fehlschlagen.
        """
        from services.user_service import UserService

        # Create first user
        success1, _, _ = UserService.create_user(
            username='duplicate_user',
            password='password1'
        )
        assert success1 is True

        # Try to create duplicate
        success2, user2, error2 = UserService.create_user(
            username='duplicate_user',
            password='password2'
        )

        assert success2 is False
        assert user2 is None
        assert "Username already exists" in error2

    def test_USER_048_create_user_missing_username(self, app, db, app_context):
        """
        [USER-048] Create User - Fehlender Username

        Fehlender Username sollte fehlschlagen.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='',
            password='password'
        )

        assert success is False
        assert user is None
        assert "Username and password are required" in error

    def test_USER_049_create_user_missing_password(self, app, db, app_context):
        """
        [USER-049] Create User - Fehlendes Passwort

        Fehlendes Passwort sollte fehlschlagen.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='user_no_password',
            password=''
        )

        assert success is False
        assert user is None
        assert "Username and password are required" in error

    def test_USER_050_create_user_auto_generates_api_key(self, app, db, app_context):
        """
        [USER-050] Create User - Auto API Key

        API Key sollte automatisch generiert werden.
        """
        from services.user_service import UserService

        success, user, error = UserService.create_user(
            username='auto_key_user',
            password='password'
        )

        assert success is True
        assert user.api_key is not None
        assert len(user.api_key) == 36  # UUID format

    def test_USER_051_create_user_new_group_created(self, app, db, app_context):
        """
        [USER-051] Create User - Neue Gruppe erstellt

        Nicht existierende Gruppe sollte erstellt werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Ensure group doesn't exist
        assert UserGroup.query.filter_by(name='BrandNewGroup').first() is None

        success, user, error = UserService.create_user(
            username='new_group_user',
            password='password',
            group_name='BrandNewGroup'
        )

        assert success is True
        assert user.group.name == 'BrandNewGroup'
        # Verify group was created
        assert UserGroup.query.filter_by(name='BrandNewGroup').first() is not None


class TestGroupManagement:
    """
    Group Management Tests

    Tests for user group management.
    """

    def test_USER_070_get_or_create_default_group(self, app, db, app_context):
        """
        [USER-070] Get or Create Default Group

        Default Group "Standard" sollte erstellt werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Clear existing Standard group if any
        UserGroup.query.filter_by(name='Standard').delete()
        db.session.commit()

        group = UserService.get_or_create_default_group()

        assert group is not None
        assert group.name == 'Standard'

    def test_USER_071_get_or_create_default_group_existing(self, app, db, app_context):
        """
        [USER-071] Get or Create Default Group - Existiert

        Existierende Default Group sollte zurückgegeben werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Create Standard group
        existing_group = UserGroup(name='Standard')
        db.session.add(existing_group)
        db.session.commit()
        existing_id = existing_group.id

        group = UserService.get_or_create_default_group()

        assert group is not None
        assert group.id == existing_id

    def test_USER_072_get_or_create_group_new(self, app, db, app_context):
        """
        [USER-072] Get or Create Group - Neu

        Neue Gruppe sollte erstellt werden.
        """
        from services.user_service import UserService

        group = UserService.get_or_create_group('NewTestGroup072')

        assert group is not None
        assert group.name == 'NewTestGroup072'

    def test_USER_073_get_or_create_group_existing(self, app, db, app_context):
        """
        [USER-073] Get or Create Group - Existiert

        Existierende Gruppe sollte zurückgegeben werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Create group first
        existing = UserGroup(name='ExistingGroup073')
        db.session.add(existing)
        db.session.commit()
        existing_id = existing.id

        group = UserService.get_or_create_group('ExistingGroup073')

        assert group is not None
        assert group.id == existing_id

    def test_USER_074_get_group_by_name_found(self, app, db, app_context):
        """
        [USER-074] Get Group by Name - Gefunden

        Existierende Gruppe sollte gefunden werden.
        """
        from services.user_service import UserService
        from db.models import UserGroup

        # Create group
        group = UserGroup(name='FindableGroup')
        db.session.add(group)
        db.session.commit()

        found = UserService.get_group_by_name('FindableGroup')

        assert found is not None
        assert found.name == 'FindableGroup'

    def test_USER_075_get_group_by_name_not_found(self, app, db, app_context):
        """
        [USER-075] Get Group by Name - Nicht gefunden

        Nicht existierende Gruppe sollte None zurückgeben.
        """
        from services.user_service import UserService

        found = UserService.get_group_by_name('NonexistentGroup')

        assert found is None

    def test_USER_080_change_user_group_success(self, app, db, app_context):
        """
        [USER-080] Change User Group - Erfolgreich

        Admin sollte User-Gruppe ändern können.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create groups
        admin_group = UserGroup(name='Admin')
        user_group = UserGroup(name='Users')
        new_group = UserGroup(name='NewGroup080')
        db.session.add_all([admin_group, user_group, new_group])
        db.session.commit()

        # Create admin user
        admin = User(username='admin_080')
        admin.set_password('password')
        admin.api_key = str(uuid4())
        admin.group = admin_group
        db.session.add(admin)

        # Create target user
        target = User(username='target_080')
        target.set_password('password')
        target.api_key = str(uuid4())
        target.group = user_group
        db.session.add(target)
        db.session.commit()

        success, error = UserService.change_user_group('target_080', 'NewGroup080', admin)

        assert success is True
        assert error is None

        # Verify change
        updated_user = UserService.get_user_by_username('target_080')
        assert updated_user.group.name == 'NewGroup080'

    def test_USER_081_change_user_group_not_admin(self, app, db, app_context):
        """
        [USER-081] Change User Group - Kein Admin

        Nicht-Admin sollte keine Berechtigung haben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create groups
        user_group = UserGroup(name='Users081')
        target_group = UserGroup(name='Target081')
        db.session.add_all([user_group, target_group])
        db.session.commit()

        # Create non-admin user
        non_admin = User(username='nonadmin_081')
        non_admin.set_password('password')
        non_admin.api_key = str(uuid4())
        non_admin.group = user_group
        db.session.add(non_admin)

        # Create target user
        target = User(username='target_081')
        target.set_password('password')
        target.api_key = str(uuid4())
        target.group = user_group
        db.session.add(target)
        db.session.commit()

        success, error = UserService.change_user_group('target_081', 'Target081', non_admin)

        assert success is False
        assert "permission" in error.lower()

    def test_USER_082_change_user_group_user_not_found(self, app, db, app_context):
        """
        [USER-082] Change User Group - User nicht gefunden

        Nicht existierender User sollte Fehler geben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create admin group and admin
        admin_group = UserGroup(name='Admin082')
        db.session.add(admin_group)
        db.session.commit()

        admin = User(username='admin_082')
        admin.set_password('password')
        admin.api_key = str(uuid4())
        admin.group = admin_group
        admin.group.name = 'Admin'  # Must be 'Admin' to have permission
        db.session.add(admin)
        db.session.commit()

        success, error = UserService.change_user_group('nonexistent_user', 'SomeGroup', admin)

        assert success is False
        assert "User not found" in error

    def test_USER_083_change_user_group_group_not_found(self, app, db, app_context):
        """
        [USER-083] Change User Group - Gruppe nicht gefunden

        Nicht existierende Gruppe sollte Fehler geben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create admin group
        admin_group = UserGroup(name='Admin')
        user_group = UserGroup(name='Users083')
        db.session.add_all([admin_group, user_group])
        db.session.commit()

        # Create admin
        admin = User(username='admin_083')
        admin.set_password('password')
        admin.api_key = str(uuid4())
        admin.group = admin_group
        db.session.add(admin)

        # Create target user
        target = User(username='target_083')
        target.set_password('password')
        target.api_key = str(uuid4())
        target.group = user_group
        db.session.add(target)
        db.session.commit()

        success, error = UserService.change_user_group('target_083', 'NonexistentGroup', admin)

        assert success is False
        assert "does not exist" in error


class TestUtilityMethods:
    """
    Utility Methods Tests

    Tests for utility methods.
    """

    def test_USER_100_get_all_users(self, app, db, app_context):
        """
        [USER-100] Get All Users

        Sollte alle User zurückgeben.
        """
        from services.user_service import UserService
        from db.models import User, UserGroup

        # Create group and users
        group = UserGroup(name='TestGroup100')
        db.session.add(group)
        db.session.commit()

        for i in range(3):
            user = User(username=f'all_users_test_{i}')
            user.set_password('password')
            user.api_key = str(uuid4())
            user.group = group
            db.session.add(user)
        db.session.commit()

        users = UserService.get_all_users()

        assert len(users) >= 3
        usernames = [u.username for u in users]
        assert 'all_users_test_0' in usernames
        assert 'all_users_test_1' in usernames
        assert 'all_users_test_2' in usernames

    def test_USER_101_get_all_users_empty(self, app, db, app_context):
        """
        [USER-101] Get All Users - Leer

        Leere DB sollte leere Liste zurückgeben.
        """
        from services.user_service import UserService
        from db.models import User

        # Clear all users
        User.query.delete()
        db.session.commit()

        users = UserService.get_all_users()

        assert users == []

    def test_USER_102_validate_uuid_valid(self, app, app_context):
        """
        [USER-102] Validate UUID - Gültig

        Gültige UUID sollte True zurückgeben.
        """
        from services.user_service import UserService

        valid_uuid = str(uuid4())
        result = UserService.validate_uuid(valid_uuid)

        assert result is True

    def test_USER_103_validate_uuid_invalid(self, app, app_context):
        """
        [USER-103] Validate UUID - Ungültig

        Ungültige UUID sollte False zurückgeben.
        """
        from services.user_service import UserService

        assert UserService.validate_uuid('not-a-uuid') is False
        assert UserService.validate_uuid('12345') is False
        assert UserService.validate_uuid('') is False

    def test_USER_104_validate_uuid_version(self, app, app_context):
        """
        [USER-104] Validate UUID - Version

        UUID Version sollte geprüft werden.
        """
        from services.user_service import UserService
        import uuid

        # UUID v4
        uuid_v4 = str(uuid.uuid4())
        assert UserService.validate_uuid(uuid_v4, version=4) is True

        # UUID v1
        uuid_v1 = str(uuid.uuid1())
        assert UserService.validate_uuid(uuid_v1, version=1) is True
        # v1 UUID validated as v4 should fail
        assert UserService.validate_uuid(uuid_v1, version=4) is False


class TestProfileHelpers:
    """
    Profile Helpers Tests

    Tests for user profile helper functions.
    """

    def test_USER_120_is_valid_collab_color_valid(self, app, app_context):
        """
        [USER-120] Is Valid Collab Color - Gültig

        Gültige Hex-Farben sollten True zurückgeben.
        """
        from services.user_profile_service import is_valid_collab_color

        assert is_valid_collab_color('#FF5733') is True
        assert is_valid_collab_color('#000000') is True
        assert is_valid_collab_color('#FFFFFF') is True
        assert is_valid_collab_color('#aabbcc') is True

    def test_USER_121_is_valid_collab_color_invalid(self, app, app_context):
        """
        [USER-121] Is Valid Collab Color - Ungültig

        Ungültige Farben sollten False zurückgeben.
        """
        from services.user_profile_service import is_valid_collab_color

        assert is_valid_collab_color('red') is False
        assert is_valid_collab_color('#FFF') is False  # Too short
        assert is_valid_collab_color('#FFFFFFF') is False  # Too long
        assert is_valid_collab_color('FF5733') is False  # Missing #
        assert is_valid_collab_color('#GGGGGG') is False  # Invalid hex

    def test_USER_122_pick_collab_color_unique(self, app, db, app_context):
        """
        [USER-122] Pick Collab Color - Unique

        Sollte eine nicht verwendete Farbe wählen wenn möglich.
        """
        from services.user_profile_service import pick_collab_color

        used_colors = {'#FF6B6B', '#4ECDC4'}
        color = pick_collab_color(used_colors)

        assert color is not None
        assert color.startswith('#')
        assert len(color) == 7

    def test_USER_123_pick_collab_color_all_used(self, app, db, app_context):
        """
        [USER-123] Pick Collab Color - Alle verwendet

        Sollte trotzdem eine Farbe zurückgeben wenn alle verwendet.
        """
        from services.user_profile_service import pick_collab_color
        from db.models.user import DEFAULT_COLLAB_COLORS

        # All colors used
        all_used = set(DEFAULT_COLLAB_COLORS)
        color = pick_collab_color(all_used)

        # Should still return a color (from the list)
        assert color is not None
        assert color in DEFAULT_COLLAB_COLORS

    def test_USER_124_build_avatar_url_with_public_id(self, app, app_context):
        """
        [USER-124] Build Avatar URL - Mit Public ID

        Sollte korrekte URL bauen.
        """
        from services.user_profile_service import build_avatar_url

        class MockUser:
            avatar_public_id = 'abc123'
            avatar_file = 'avatar.png'

        url = build_avatar_url(MockUser())

        assert url == '/api/users/avatar/abc123'

    def test_USER_125_build_avatar_url_no_public_id(self, app, app_context):
        """
        [USER-125] Build Avatar URL - Keine Public ID

        Ohne Public ID sollte None zurückgeben.
        """
        from services.user_profile_service import build_avatar_url

        class MockUser:
            avatar_public_id = None
            avatar_file = 'avatar.png'

        url = build_avatar_url(MockUser())

        assert url is None

    def test_USER_126_build_avatar_url_no_file(self, app, app_context):
        """
        [USER-126] Build Avatar URL - Keine Datei

        Ohne Avatar-Datei sollte None zurückgeben.
        """
        from services.user_profile_service import build_avatar_url

        class MockUser:
            avatar_public_id = 'abc123'
            avatar_file = None

        url = build_avatar_url(MockUser())

        assert url is None


class TestUserModel:
    """
    User Model Tests

    Tests for User model methods.
    """

    def test_USER_130_user_set_password(self, app, db, app_context):
        """
        [USER-130] User Set Password

        Passwort sollte gehasht gespeichert werden.
        """
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup130')
        db.session.add(group)
        db.session.commit()

        user = User(username='pwd_test_user')
        user.set_password('my_password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        assert user.password_hash is not None
        assert user.password_hash != 'my_password'

    def test_USER_131_user_check_password_correct(self, app, db, app_context):
        """
        [USER-131] User Check Password - Korrekt

        Korrektes Passwort sollte True zurückgeben.
        """
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup131')
        db.session.add(group)
        db.session.commit()

        user = User(username='check_pwd_user')
        user.set_password('correct_password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        assert user.check_password('correct_password') is True

    def test_USER_132_user_check_password_wrong(self, app, db, app_context):
        """
        [USER-132] User Check Password - Falsch

        Falsches Passwort sollte False zurückgeben.
        """
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup132')
        db.session.add(group)
        db.session.commit()

        user = User(username='wrong_pwd_user')
        user.set_password('correct_password')
        user.api_key = str(uuid4())
        user.group = group
        db.session.add(user)
        db.session.commit()

        assert user.check_password('wrong_password') is False

    def test_USER_133_user_get_avatar_seed(self, app, db, app_context):
        """
        [USER-133] User Get Avatar Seed

        Avatar Seed sollte generiert werden wenn nicht vorhanden.
        """
        from db.models import User, UserGroup

        group = UserGroup(name='TestGroup133')
        db.session.add(group)
        db.session.commit()

        user = User(username='avatar_seed_user')
        user.set_password('password')
        user.api_key = str(uuid4())
        user.group = group
        user.avatar_seed = None  # Explicitly set to None
        db.session.add(user)
        db.session.commit()

        seed = user.get_avatar_seed()

        assert seed is not None
        assert len(seed) == 16  # token_hex(8) = 16 chars
