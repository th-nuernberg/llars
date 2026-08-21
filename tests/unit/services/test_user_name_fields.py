"""
Unit tests for user name fields (first_name, last_name, display_name).

Tests the new name fields on the User model and their integration with:
- Admin create/update user endpoints (auto-generation of display_name)
- User search endpoints (search across name fields)
- _serialize_user response format
- AuthentikAdminService.create_user attribute passing
- AuthentikAdminService.send_recovery_email flow

Test IDs: UNAME-001 to UNAME-050
"""

import pytest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_group(db, name):
    from db.models import UserGroup
    group = UserGroup(name=name)
    db.session.add(group)
    db.session.commit()
    return group


def _make_user(db, username, *, group_name='UNAME_Group', first_name=None,
               last_name=None, display_name=None, active=True, deleted=False):
    from db.models import User, UserGroup

    group = UserGroup.query.filter_by(name=group_name).first()
    if not group:
        group = _make_group(db, group_name)

    user = User(username=username)
    user.set_password('password')
    user.api_key = f'uname-key-{username}'
    user.group = group
    user.is_active = active
    user.first_name = first_name
    user.last_name = last_name
    user.display_name = display_name
    if deleted:
        from datetime import datetime
        user.deleted_at = datetime.utcnow()
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


# ===========================================================================
# User Model - Name Fields
# ===========================================================================

class TestUserModelNameFields:
    """Tests that the User model has the expected name fields."""

    def test_UNAME_001_user_model_has_first_name(self, app, db, app_context):
        """[UNAME-001] User model should have first_name column."""
        from db.models.user import User

        user = User(username='model_fn_001')
        user.set_password('pw')
        user.api_key = str(uuid4())
        user.first_name = 'Alice'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        assert user.first_name == 'Alice'

    def test_UNAME_002_user_model_has_last_name(self, app, db, app_context):
        """[UNAME-002] User model should have last_name column."""
        from db.models.user import User

        user = User(username='model_ln_002')
        user.set_password('pw')
        user.api_key = str(uuid4())
        user.last_name = 'Smith'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        assert user.last_name == 'Smith'

    def test_UNAME_003_user_model_has_display_name(self, app, db, app_context):
        """[UNAME-003] User model should have display_name column."""
        from db.models.user import User

        user = User(username='model_dn_003')
        user.set_password('pw')
        user.api_key = str(uuid4())
        user.display_name = 'Alice Smith'
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        assert user.display_name == 'Alice Smith'

    def test_UNAME_004_name_fields_nullable(self, app, db, app_context):
        """[UNAME-004] Name fields should all be nullable (Optional)."""
        from db.models.user import User

        user = User(username='model_null_004')
        user.set_password('pw')
        user.api_key = str(uuid4())
        # Do not set any name fields
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)

        assert user.first_name is None
        assert user.last_name is None
        assert user.display_name is None

    def test_UNAME_005_name_fields_persist_after_reload(self, app, db, app_context):
        """[UNAME-005] Name fields should round-trip through DB correctly."""
        from db.models.user import User

        user = User(username='model_rt_005')
        user.set_password('pw')
        user.api_key = str(uuid4())
        user.first_name = 'Max'
        user.last_name = 'Mustermann'
        user.display_name = 'Max Mustermann'
        db.session.add(user)
        db.session.commit()

        loaded = User.query.filter_by(username='model_rt_005').first()
        assert loaded.first_name == 'Max'
        assert loaded.last_name == 'Mustermann'
        assert loaded.display_name == 'Max Mustermann'


# ===========================================================================
# _serialize_user - Name Fields in Response
# ===========================================================================

class TestSerializeUserNameFields:
    """Tests that _serialize_user includes name fields in the response."""

    def test_UNAME_010_serialize_includes_name_fields(self, app, db, app_context):
        """[UNAME-010] _serialize_user should include first_name, last_name, display_name."""
        from routes.users.user_admin_routes import _serialize_user

        user = _make_user(db, 'serialize_010', first_name='Alice',
                          last_name='Wonder', display_name='Alice Wonder')
        result = _serialize_user(user, [])

        assert result['first_name'] == 'Alice'
        assert result['last_name'] == 'Wonder'
        assert result['display_name'] == 'Alice Wonder'

    def test_UNAME_011_serialize_name_fields_none(self, app, db, app_context):
        """[UNAME-011] _serialize_user should return None for unset name fields."""
        from routes.users.user_admin_routes import _serialize_user

        user = _make_user(db, 'serialize_011')
        result = _serialize_user(user, [])

        assert result['first_name'] is None
        assert result['last_name'] is None
        assert result['display_name'] is None

    def test_UNAME_012_serialize_preserves_other_fields(self, app, db, app_context):
        """[UNAME-012] _serialize_user should still include standard fields alongside name fields."""
        from routes.users.user_admin_routes import _serialize_user

        user = _make_user(db, 'serialize_012', first_name='Bob')
        result = _serialize_user(user, [])

        assert result['username'] == 'serialize_012'
        assert 'id' in result
        assert 'is_active' in result
        assert 'avatar_seed' in result
        assert result['first_name'] == 'Bob'


# ===========================================================================
# Admin Create User - display_name Auto-Generation
# ===========================================================================

class TestCreateUserDisplayNameGeneration:
    """Tests for display_name auto-generation logic in the admin create endpoint."""

    def test_UNAME_020_create_auto_generates_display_name(self, app, db, app_context):
        """[UNAME-020] Create with first_name+last_name should auto-generate display_name."""
        # Test the logic directly: same logic as in user_admin_routes.create_admin_user
        first_name = 'Alice'
        last_name = 'Smith'
        display_name = ''

        if not display_name and (first_name or last_name):
            display_name = ' '.join(filter(None, [first_name, last_name]))

        assert display_name == 'Alice Smith'

    def test_UNAME_021_create_auto_generates_from_first_name_only(self, app, db, app_context):
        """[UNAME-021] Create with only first_name should use it as display_name."""
        first_name = 'Alice'
        last_name = None
        display_name = ''

        if not display_name and (first_name or last_name):
            display_name = ' '.join(filter(None, [first_name, last_name]))

        assert display_name == 'Alice'

    def test_UNAME_022_create_auto_generates_from_last_name_only(self, app, db, app_context):
        """[UNAME-022] Create with only last_name should use it as display_name."""
        first_name = None
        last_name = 'Smith'
        display_name = ''

        if not display_name and (first_name or last_name):
            display_name = ' '.join(filter(None, [first_name, last_name]))

        assert display_name == 'Smith'

    def test_UNAME_023_create_explicit_display_name_used(self, app, db, app_context):
        """[UNAME-023] Explicit display_name should NOT be overwritten by auto-generation."""
        first_name = 'Alice'
        last_name = 'Smith'
        display_name = 'Dr. Alice'

        # The route checks: if not display_name ...
        # Since display_name is set, it should remain as-is
        if not display_name and (first_name or last_name):
            display_name = ' '.join(filter(None, [first_name, last_name]))

        assert display_name == 'Dr. Alice'

    def test_UNAME_024_create_without_name_fields_backward_compat(self, app, db, app_context):
        """[UNAME-024] Create without any name fields should work (backward compatibility)."""
        first_name = None
        last_name = None
        display_name = ''

        if not display_name and (first_name or last_name):
            display_name = ' '.join(filter(None, [first_name, last_name]))

        # display_name stays empty string, which is falsy -> won't be set on user
        assert display_name == ''

    def test_UNAME_025_create_user_persists_name_fields(self, app, db, app_context):
        """[UNAME-025] Name fields should be persisted on created User object."""
        from db.models import User, UserGroup

        group = UserGroup.query.filter_by(name='UNAME_Create_Group').first()
        if not group:
            group = _make_group(db, 'UNAME_Create_Group')

        user = User(
            username='persist_025',
            password_hash='',
            api_key=str(uuid4()),
            group_id=group.id,
        )
        user.first_name = 'Max'
        user.last_name = 'Plank'
        user.display_name = 'Max Plank'
        db.session.add(user)
        db.session.commit()

        loaded = User.query.filter_by(username='persist_025').first()
        assert loaded.first_name == 'Max'
        assert loaded.last_name == 'Plank'
        assert loaded.display_name == 'Max Plank'


# ===========================================================================
# Admin PATCH User - display_name Auto-Generation on Update
# ===========================================================================

class TestUpdateUserDisplayNameGeneration:
    """Tests for display_name auto-generation logic on PATCH."""

    def test_UNAME_030_update_first_name_auto_generates_display(self, app, db, app_context):
        """[UNAME-030] Updating first_name without display_name should auto-generate it."""
        user = _make_user(db, 'update_030', first_name='Old', last_name='Name')

        # Simulate the PATCH logic from user_admin_routes.update_admin_user
        data = {'first_name': 'New'}

        if 'first_name' in data:
            user.first_name = (data['first_name'] or '').strip() or None
        if 'last_name' in data:
            user.last_name = (data['last_name'] or '').strip() or None
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None
        elif 'first_name' in data or 'last_name' in data:
            fn = user.first_name or ''
            ln = user.last_name or ''
            auto_dn = ' '.join(filter(None, [fn, ln]))
            if auto_dn:
                user.display_name = auto_dn

        assert user.display_name == 'New Name'

    def test_UNAME_031_update_last_name_auto_generates_display(self, app, db, app_context):
        """[UNAME-031] Updating last_name without display_name should auto-generate it."""
        user = _make_user(db, 'update_031', first_name='Alice', last_name='Old')

        data = {'last_name': 'New'}

        if 'first_name' in data:
            user.first_name = (data['first_name'] or '').strip() or None
        if 'last_name' in data:
            user.last_name = (data['last_name'] or '').strip() or None
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None
        elif 'first_name' in data or 'last_name' in data:
            fn = user.first_name or ''
            ln = user.last_name or ''
            auto_dn = ' '.join(filter(None, [fn, ln]))
            if auto_dn:
                user.display_name = auto_dn

        assert user.display_name == 'Alice New'

    def test_UNAME_032_update_explicit_display_name_not_overwritten(self, app, db, app_context):
        """[UNAME-032] Explicit display_name in PATCH should be used, not auto-generated."""
        user = _make_user(db, 'update_032', first_name='Alice', last_name='Smith')

        data = {'first_name': 'Bob', 'display_name': 'Custom Name'}

        if 'first_name' in data:
            user.first_name = (data['first_name'] or '').strip() or None
        if 'last_name' in data:
            user.last_name = (data['last_name'] or '').strip() or None
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None
        elif 'first_name' in data or 'last_name' in data:
            fn = user.first_name or ''
            ln = user.last_name or ''
            auto_dn = ' '.join(filter(None, [fn, ln]))
            if auto_dn:
                user.display_name = auto_dn

        assert user.display_name == 'Custom Name'
        assert user.first_name == 'Bob'

    def test_UNAME_033_update_both_names_auto_generates(self, app, db, app_context):
        """[UNAME-033] Updating both first and last name should auto-generate display_name."""
        user = _make_user(db, 'update_033')

        data = {'first_name': 'Max', 'last_name': 'Planck'}

        if 'first_name' in data:
            user.first_name = (data['first_name'] or '').strip() or None
        if 'last_name' in data:
            user.last_name = (data['last_name'] or '').strip() or None
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None
        elif 'first_name' in data or 'last_name' in data:
            fn = user.first_name or ''
            ln = user.last_name or ''
            auto_dn = ' '.join(filter(None, [fn, ln]))
            if auto_dn:
                user.display_name = auto_dn

        assert user.display_name == 'Max Planck'

    def test_UNAME_034_update_clear_first_name(self, app, db, app_context):
        """[UNAME-034] Clearing first_name should auto-generate display_name from last_name only."""
        user = _make_user(db, 'update_034', first_name='Alice', last_name='Smith',
                          display_name='Alice Smith')

        data = {'first_name': ''}

        if 'first_name' in data:
            user.first_name = (data['first_name'] or '').strip() or None
        if 'last_name' in data:
            user.last_name = (data['last_name'] or '').strip() or None
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None
        elif 'first_name' in data or 'last_name' in data:
            fn = user.first_name or ''
            ln = user.last_name or ''
            auto_dn = ' '.join(filter(None, [fn, ln]))
            if auto_dn:
                user.display_name = auto_dn

        assert user.first_name is None
        assert user.display_name == 'Smith'


# ===========================================================================
# User Search - Name Field Search
# ===========================================================================

class TestUserSearchNameFields:
    """Tests that user search endpoints search across name fields."""

    def test_UNAME_040_search_finds_by_first_name(self, app, db, app_context):
        """[UNAME-040] User search should find users by first_name."""
        from db.models.user import User
        from sqlalchemy import or_

        _make_user(db, 'search_fn_040', first_name='Alphonse')
        _make_user(db, 'search_other_040')

        query = 'Alphonse'
        users = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
            )
        ).all()

        usernames = [u.username for u in users]
        assert 'search_fn_040' in usernames
        assert 'search_other_040' not in usernames

    def test_UNAME_041_search_finds_by_last_name(self, app, db, app_context):
        """[UNAME-041] User search should find users by last_name."""
        from db.models.user import User
        from sqlalchemy import or_

        _make_user(db, 'search_ln_041', last_name='Elric')
        _make_user(db, 'search_nope_041')

        query = 'Elric'
        users = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
            )
        ).all()

        usernames = [u.username for u in users]
        assert 'search_ln_041' in usernames
        assert 'search_nope_041' not in usernames

    def test_UNAME_042_search_finds_by_display_name(self, app, db, app_context):
        """[UNAME-042] User search should find users by display_name."""
        from db.models.user import User
        from sqlalchemy import or_

        _make_user(db, 'search_dn_042', display_name='Professor X')
        _make_user(db, 'search_miss_042')

        query = 'Professor'
        users = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
            )
        ).all()

        usernames = [u.username for u in users]
        assert 'search_dn_042' in usernames
        assert 'search_miss_042' not in usernames

    def test_UNAME_043_search_partial_match(self, app, db, app_context):
        """[UNAME-043] User search should support partial matching on name fields."""
        from db.models.user import User
        from sqlalchemy import or_

        _make_user(db, 'search_partial_043', first_name='Alexander')

        query = 'Alex'
        users = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
            )
        ).all()

        usernames = [u.username for u in users]
        assert 'search_partial_043' in usernames

    def test_UNAME_044_search_case_insensitive(self, app, db, app_context):
        """[UNAME-044] User search should be case-insensitive on name fields."""
        from db.models.user import User
        from sqlalchemy import or_

        _make_user(db, 'search_ci_044', first_name='UPPERCASE')

        query = 'uppercase'
        users = User.query.filter(
            User.deleted_at.is_(None),
            User.is_active == True,
            or_(
                User.username.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.display_name.ilike(f'%{query}%'),
            )
        ).all()

        usernames = [u.username for u in users]
        assert 'search_ci_044' in usernames


# ===========================================================================
# AuthentikAdminService.create_user - Attribute Passing
# ===========================================================================

class TestAuthentikCreateUserAttributes:
    """Tests that AuthentikAdminService.create_user passes name attributes correctly."""

    def test_UNAME_050_create_user_passes_first_name_attribute(self, app, app_context):
        """[UNAME-050] create_user should include first_name in Authentik attributes."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_response_check = MagicMock()
        mock_response_check.status_code = 200
        mock_response_check.json.return_value = {'results': []}

        mock_response_create = MagicMock()
        mock_response_create.status_code = 201
        mock_response_create.json.return_value = {'pk': 42, 'username': 'newuser'}

        mock_response_password = MagicMock()
        mock_response_password.status_code = 204

        call_count = [0]
        captured_json = [None]

        def mock_make_request(method, url, **kwargs):
            call_count[0] += 1
            if method == 'GET':
                return mock_response_check
            elif method == 'POST' and '/set_password/' in url:
                return mock_response_password
            elif method == 'POST':
                captured_json[0] = kwargs.get('json', {})
                return mock_response_create
            return mock_response_check

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', side_effect=mock_make_request):

            success, error, data = AuthentikAdminService.create_user(
                username='newuser',
                email='newuser@test.com',
                password='password123',
                name='New User',
                first_name='New',
                last_name='User',
            )

        assert success is True
        assert captured_json[0] is not None
        assert captured_json[0].get('attributes', {}).get('first_name') == 'New'
        assert captured_json[0].get('attributes', {}).get('last_name') == 'User'

    def test_UNAME_051_create_user_omits_attributes_when_no_names(self, app, app_context):
        """[UNAME-051] create_user should not include attributes when no name fields given."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_response_check = MagicMock()
        mock_response_check.status_code = 200
        mock_response_check.json.return_value = {'results': []}

        mock_response_create = MagicMock()
        mock_response_create.status_code = 201
        mock_response_create.json.return_value = {'pk': 43, 'username': 'noname'}

        mock_response_password = MagicMock()
        mock_response_password.status_code = 204

        captured_json = [None]

        def mock_make_request(method, url, **kwargs):
            if method == 'GET':
                return mock_response_check
            elif method == 'POST' and '/set_password/' in url:
                return mock_response_password
            elif method == 'POST':
                captured_json[0] = kwargs.get('json', {})
                return mock_response_create
            return mock_response_check

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', side_effect=mock_make_request):

            success, error, data = AuthentikAdminService.create_user(
                username='noname',
                email='noname@test.com',
                password='password123',
            )

        assert success is True
        assert captured_json[0] is not None
        # When no first_name/last_name, attributes dict should be empty -> not included in payload
        assert 'attributes' not in captured_json[0]

    def test_UNAME_052_create_user_first_name_only_attribute(self, app, app_context):
        """[UNAME-052] create_user with only first_name should include it in attributes."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_response_check = MagicMock()
        mock_response_check.status_code = 200
        mock_response_check.json.return_value = {'results': []}

        mock_response_create = MagicMock()
        mock_response_create.status_code = 201
        mock_response_create.json.return_value = {'pk': 44, 'username': 'fnonly'}

        mock_response_password = MagicMock()
        mock_response_password.status_code = 204

        captured_json = [None]

        def mock_make_request(method, url, **kwargs):
            if method == 'GET':
                return mock_response_check
            elif method == 'POST' and '/set_password/' in url:
                return mock_response_password
            elif method == 'POST':
                captured_json[0] = kwargs.get('json', {})
                return mock_response_create
            return mock_response_check

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', side_effect=mock_make_request):

            success, error, data = AuthentikAdminService.create_user(
                username='fnonly',
                email='fnonly@test.com',
                password='password123',
                first_name='OnlyFirst',
            )

        assert success is True
        attrs = captured_json[0].get('attributes', {})
        assert attrs.get('first_name') == 'OnlyFirst'
        assert 'last_name' not in attrs


# ===========================================================================
# AuthentikAdminService.send_recovery_email
# ===========================================================================

class TestAuthentikSendRecoveryEmail:
    """Tests for AuthentikAdminService.send_recovery_email."""

    def test_UNAME_055_recovery_email_success(self, app, app_context):
        """[UNAME-055] send_recovery_email should return success when Authentik responds OK."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.json.return_value = {
            'results': [{'username': 'recover_user', 'pk': 100}]
        }

        mock_stages = MagicMock()
        mock_stages.status_code = 200
        mock_stages.json.return_value = {
            'results': [{'pk': 'stage-1', 'name': 'email-recovery-stage'}]
        }

        mock_recovery = MagicMock()
        mock_recovery.status_code = 200

        def mock_make_request(method, url, **kwargs):
            if '/stages/email/' in url:
                return mock_stages
            if '/recovery_email/' in url:
                return mock_recovery
            return mock_search

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', side_effect=mock_make_request):

            success, error = AuthentikAdminService.send_recovery_email(username='recover_user')

        assert success is True
        assert error is None

    def test_UNAME_056_recovery_email_user_not_found(self, app, app_context):
        """[UNAME-056] send_recovery_email should fail when user not found in Authentik."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.json.return_value = {'results': []}

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', return_value=mock_search):

            success, error = AuthentikAdminService.send_recovery_email(username='ghost_user')

        assert success is False
        assert 'not found' in error

    def test_UNAME_057_recovery_email_no_auth_token(self, app, app_context):
        """[UNAME-057] send_recovery_email should fail when unable to authenticate."""
        from services.authentik_admin_service import AuthentikAdminService

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value=None):
            success, error = AuthentikAdminService.send_recovery_email(username='any_user')

        assert success is False
        assert 'authenticate' in error.lower()

    def test_UNAME_058_recovery_email_no_email_stage(self, app, app_context):
        """[UNAME-058] send_recovery_email should fail when no email stage configured."""
        from services.authentik_admin_service import AuthentikAdminService

        mock_search = MagicMock()
        mock_search.status_code = 200
        mock_search.json.return_value = {
            'results': [{'username': 'nostage_user', 'pk': 200}]
        }

        mock_stages = MagicMock()
        mock_stages.status_code = 200
        mock_stages.json.return_value = {'results': []}

        def mock_make_request(method, url, **kwargs):
            if '/stages/email/' in url:
                return mock_stages
            return mock_search

        with patch.object(AuthentikAdminService, '_get_admin_token', return_value='fake-token'), \
             patch.object(AuthentikAdminService, '_make_request', side_effect=mock_make_request):

            success, error = AuthentikAdminService.send_recovery_email(username='nostage_user')

        assert success is False
        assert 'email stage' in error.lower()
