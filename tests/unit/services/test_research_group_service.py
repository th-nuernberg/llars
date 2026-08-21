"""
Unit tests for ResearchGroupService.

Tests research group CRUD, member management, access control,
access requests, and statistics.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock


class TestSlugify:
    """Tests for the _slugify helper function."""

    def test_RES_GRP_001_slugify_basic(self):
        """[RES_GRP-001] Should convert name to lowercase slug."""
        from services.research_group_service import _slugify

        assert _slugify('My Research Group') == 'my-research-group'

    def test_RES_GRP_002_slugify_special_chars(self):
        """[RES_GRP-002] Should remove special characters."""
        from services.research_group_service import _slugify

        assert _slugify('NLP & AI Research!') == 'nlp-ai-research'

    def test_RES_GRP_003_slugify_trim_hyphens(self):
        """[RES_GRP-003] Should trim leading/trailing hyphens."""
        from services.research_group_service import _slugify

        result = _slugify(' -Test Group- ')
        assert not result.startswith('-')
        assert not result.endswith('-')

    def test_RES_GRP_004_slugify_multiple_spaces(self):
        """[RES_GRP-004] Should collapse multiple spaces into single hyphen."""
        from services.research_group_service import _slugify

        result = _slugify('Multi   Spaced   Name')
        assert '--' not in result


class TestGroupCRUD:
    """Tests for group creation, retrieval, update, and deletion."""

    def test_RES_GRP_005_create_group(self, app, db, app_context, mock_user):
        """[RES_GRP-005] Should create a group with owner membership."""
        from services.research_group_service import ResearchGroupService

        data = {'name': 'NLP Lab', 'description': 'Natural Language Processing'}
        result = ResearchGroupService.create_group(data, 'testuser')

        assert result is not None
        assert result['name'] == 'NLP Lab'
        assert result['slug'] == 'nlp-lab'
        assert result['created_by'] == 'testuser'

    def test_RES_GRP_006_create_group_custom_slug(self, app, db, app_context, mock_user):
        """[RES_GRP-006] Should use custom slug when provided."""
        from services.research_group_service import ResearchGroupService

        data = {'name': 'AI Group', 'slug': 'custom-ai-slug'}
        result = ResearchGroupService.create_group(data, 'testuser')

        assert result['slug'] == 'custom-ai-slug'

    def test_RES_GRP_007_create_group_duplicate_slug(self, app, db, app_context, mock_user):
        """[RES_GRP-007] Should auto-increment slug for duplicates."""
        from services.research_group_service import ResearchGroupService

        ResearchGroupService.create_group({'name': 'Test Group'}, 'testuser')
        result = ResearchGroupService.create_group({'name': 'Test Group'}, 'testuser')

        assert result['slug'] == 'test-group-1'

    def test_RES_GRP_008_create_group_creator_as_owner(self, app, db, app_context, mock_user):
        """[RES_GRP-008] Should add creator as owner member."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.create_group({'name': 'Owner Test'}, 'testuser')
        members = ResearchGroupService.get_members(result['id'])

        assert len(members) == 1
        assert members[0]['role'] == 'owner'

    def test_RES_GRP_009_get_group(self, app, db, app_context, mock_user):
        """[RES_GRP-009] Should retrieve a group by ID."""
        from services.research_group_service import ResearchGroupService

        created = ResearchGroupService.create_group({'name': 'Get Test'}, 'testuser')
        fetched = ResearchGroupService.get_group(created['id'])

        assert fetched is not None
        assert fetched['id'] == created['id']

    def test_RES_GRP_010_get_group_not_found(self, app, db, app_context):
        """[RES_GRP-010] Should return None for non-existent group."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.get_group(99999)
        assert result is None

    def test_RES_GRP_011_list_groups(self, app, db, app_context, mock_user):
        """[RES_GRP-011] Should list all groups."""
        from services.research_group_service import ResearchGroupService

        ResearchGroupService.create_group({'name': 'Alpha Group'}, 'testuser')
        ResearchGroupService.create_group({'name': 'Beta Group'}, 'testuser')

        results = ResearchGroupService.list_groups()
        assert len(results) >= 2

    def test_RES_GRP_012_list_groups_search(self, app, db, app_context, mock_user):
        """[RES_GRP-012] Should search groups by name or slug."""
        from services.research_group_service import ResearchGroupService

        ResearchGroupService.create_group({'name': 'Findable Group'}, 'testuser')
        ResearchGroupService.create_group({'name': 'Other Group'}, 'testuser')

        results = ResearchGroupService.list_groups(search='findable')
        assert len(results) == 1
        assert results[0]['name'] == 'Findable Group'

    def test_RES_GRP_013_update_group(self, app, db, app_context, mock_user):
        """[RES_GRP-013] Should update group fields."""
        from services.research_group_service import ResearchGroupService

        created = ResearchGroupService.create_group({'name': 'Original'}, 'testuser')
        updated = ResearchGroupService.update_group(
            created['id'], {'name': 'Updated Name', 'description': 'New desc'}, 'testuser'
        )

        assert updated is not None
        assert updated['name'] == 'Updated Name'
        assert updated['description'] == 'New desc'

    def test_RES_GRP_014_update_group_not_found(self, app, db, app_context):
        """[RES_GRP-014] Should return None for non-existent group update."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.update_group(99999, {'name': 'Nope'}, 'admin')
        assert result is None

    def test_RES_GRP_015_update_group_slug(self, app, db, app_context, mock_user):
        """[RES_GRP-015] Should update slug when provided."""
        from services.research_group_service import ResearchGroupService

        created = ResearchGroupService.create_group({'name': 'Slug Test'}, 'testuser')
        updated = ResearchGroupService.update_group(
            created['id'], {'slug': 'new-slug'}, 'testuser'
        )

        assert updated is not None
        assert updated['slug'] == 'new-slug'

    def test_RES_GRP_016_update_group_duplicate_slug_ignored(self, app, db, app_context, mock_user):
        """[RES_GRP-016] Should not update slug if it would conflict."""
        from services.research_group_service import ResearchGroupService

        g1 = ResearchGroupService.create_group({'name': 'Group One'}, 'testuser')
        g2 = ResearchGroupService.create_group({'name': 'Group Two'}, 'testuser')

        updated = ResearchGroupService.update_group(
            g2['id'], {'slug': 'group-one'}, 'testuser'
        )

        # Slug should remain unchanged because 'group-one' is taken
        assert updated is not None
        assert updated['slug'] != 'group-one'

    def test_RES_GRP_017_delete_group(self, app, db, app_context, mock_user):
        """[RES_GRP-017] Should delete a group."""
        from services.research_group_service import ResearchGroupService

        created = ResearchGroupService.create_group({'name': 'Delete Me'}, 'testuser')
        result = ResearchGroupService.delete_group(created['id'])
        assert result is True

        fetched = ResearchGroupService.get_group(created['id'])
        assert fetched is None

    def test_RES_GRP_018_delete_group_not_found(self, app, db, app_context):
        """[RES_GRP-018] Should return False for non-existent group."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.delete_group(99999)
        assert result is False


class TestMembership:
    """Tests for group membership management."""

    def _create_group_with_user(self, ResearchGroupService, username='testuser'):
        """Helper to create a group."""
        return ResearchGroupService.create_group({'name': 'Member Test'}, username)

    def test_RES_GRP_019_get_members(self, app, db, app_context, mock_user):
        """[RES_GRP-019] Should list group members."""
        from services.research_group_service import ResearchGroupService

        group = self._create_group_with_user(ResearchGroupService)
        members = ResearchGroupService.get_members(group['id'])

        assert len(members) == 1
        assert members[0]['role'] == 'owner'

    def test_RES_GRP_020_add_member(self, app, db, app_context, mock_user):
        """[RES_GRP-020] Should add a new member to the group."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        # Create a second user
        user2 = User(username='member2', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = self._create_group_with_user(ResearchGroupService)
        result = ResearchGroupService.add_member(
            group['id'], user2.id, 'member', 'testuser'
        )

        assert result is not None
        assert result['role'] == 'member'

    def test_RES_GRP_021_add_member_already_exists(self, app, db, app_context, mock_user):
        """[RES_GRP-021] Should return existing membership if already a member."""
        from services.research_group_service import ResearchGroupService

        group = self._create_group_with_user(ResearchGroupService)
        # Try to add creator again (already owner)
        result = ResearchGroupService.add_member(
            group['id'], mock_user.id, 'member', 'testuser'
        )

        assert result is not None
        assert result['role'] == 'owner'  # still owner, not downgraded

    def test_RES_GRP_022_add_member_invalid_role(self, app, db, app_context, mock_user):
        """[RES_GRP-022] Should default to 'member' for invalid role."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='defaultrole', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = self._create_group_with_user(ResearchGroupService)
        result = ResearchGroupService.add_member(
            group['id'], user2.id, 'invalid_role', 'testuser'
        )

        assert result is not None
        assert result['role'] == 'member'

    def test_RES_GRP_023_add_member_group_not_found(self, app, db, app_context):
        """[RES_GRP-023] Should return None for non-existent group."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.add_member(99999, 1, 'member', 'admin')
        assert result is None

    def test_RES_GRP_024_update_member_role(self, app, db, app_context, mock_user):
        """[RES_GRP-024] Should update a member's role."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='rolechange', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = self._create_group_with_user(ResearchGroupService)
        member = ResearchGroupService.add_member(
            group['id'], user2.id, 'member', 'testuser'
        )

        updated = ResearchGroupService.update_member_role(member['id'], 'viewer', 'testuser')
        assert updated is not None
        assert updated['role'] == 'viewer'

    def test_RES_GRP_025_update_member_role_invalid(self, app, db, app_context, mock_user):
        """[RES_GRP-025] Should return None for invalid role."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='badrole', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = self._create_group_with_user(ResearchGroupService)
        member = ResearchGroupService.add_member(
            group['id'], user2.id, 'member', 'testuser'
        )

        result = ResearchGroupService.update_member_role(member['id'], 'superadmin', 'testuser')
        assert result is None

    def test_RES_GRP_026_update_member_role_not_found(self, app, db, app_context):
        """[RES_GRP-026] Should return None for non-existent member."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.update_member_role(99999, 'member', 'admin')
        assert result is None

    def test_RES_GRP_027_remove_member(self, app, db, app_context, mock_user):
        """[RES_GRP-027] Should remove a member from the group."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='removable', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = self._create_group_with_user(ResearchGroupService)
        member = ResearchGroupService.add_member(
            group['id'], user2.id, 'member', 'testuser'
        )

        result = ResearchGroupService.remove_member(member['id'], 'testuser')
        assert result is True

        members = ResearchGroupService.get_members(group['id'])
        assert len(members) == 1  # only owner remains

    def test_RES_GRP_028_remove_member_not_found(self, app, db, app_context):
        """[RES_GRP-028] Should return False for non-existent member."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.remove_member(99999, 'admin')
        assert result is False

    def test_RES_GRP_029_get_user_groups(self, app, db, app_context, mock_user):
        """[RES_GRP-029] Should list groups where user is a member."""
        from services.research_group_service import ResearchGroupService

        ResearchGroupService.create_group({'name': 'Group A'}, 'testuser')
        ResearchGroupService.create_group({'name': 'Group B'}, 'testuser')

        groups = ResearchGroupService.get_user_groups('testuser')
        assert len(groups) >= 2
        assert all('user_role' in g for g in groups)

    def test_RES_GRP_030_get_user_groups_not_found(self, app, db, app_context):
        """[RES_GRP-030] Should return empty list for non-existent user."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.get_user_groups('ghost')
        assert result == []


class TestAccessControl:
    """Tests for group access control checks."""

    def test_RES_GRP_031_get_user_role_in_group(self, app, db, app_context, mock_user):
        """[RES_GRP-031] Should return user's role in a group."""
        from services.research_group_service import ResearchGroupService

        group = ResearchGroupService.create_group({'name': 'Role Check'}, 'testuser')
        role = ResearchGroupService.get_user_role_in_group(group['id'], 'testuser')

        assert role == 'owner'

    def test_RES_GRP_032_get_user_role_not_member(self, app, db, app_context, mock_user):
        """[RES_GRP-032] Should return None when user is not a member."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='outsider', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Exclusive'}, 'testuser')
        role = ResearchGroupService.get_user_role_in_group(group['id'], 'outsider')

        assert role is None

    def test_RES_GRP_033_check_group_access_member(self, app, db, app_context, mock_user):
        """[RES_GRP-033] Should grant access to group members."""
        from services.research_group_service import ResearchGroupService

        group = ResearchGroupService.create_group({'name': 'Access Test'}, 'testuser')

        with patch('services.permission_service.PermissionService') as MockPS:
            MockPS.check_permission.return_value = False
            result = ResearchGroupService.check_group_access(group['id'], 'testuser')

        assert result is True

    def test_RES_GRP_034_check_group_access_non_member(self, app, db, app_context, mock_user):
        """[RES_GRP-034] Should deny access to non-members."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='noacccess', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'No Access'}, 'testuser')

        with patch('services.permission_service.PermissionService') as MockPS:
            MockPS.check_permission.return_value = False
            result = ResearchGroupService.check_group_access(group['id'], 'noacccess')

        assert result is False

    def test_RES_GRP_035_check_group_access_admin_override(self, app, db, app_context, mock_user):
        """[RES_GRP-035] Should grant access to admins regardless of membership."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='adminuser', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Admin Test'}, 'testuser')

        with patch('services.permission_service.PermissionService') as MockPS:
            MockPS.check_permission.return_value = True  # admin has permission
            result = ResearchGroupService.check_group_access(group['id'], 'adminuser')

        assert result is True

    def test_RES_GRP_036_check_group_access_viewer_write_denied(self, app, db, app_context, mock_user):
        """[RES_GRP-036] Should deny write access to viewers."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='viewer', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Viewer Test'}, 'testuser')
        ResearchGroupService.add_member(group['id'], user2.id, 'viewer', 'testuser')

        with patch('services.permission_service.PermissionService') as MockPS:
            MockPS.check_permission.return_value = False
            result = ResearchGroupService.check_group_access(
                group['id'], 'viewer', require_write=True
            )

        assert result is False

    def test_RES_GRP_037_check_group_access_unknown_user(self, app, db, app_context, mock_user):
        """[RES_GRP-037] Should deny access for unknown users."""
        from services.research_group_service import ResearchGroupService

        group = ResearchGroupService.create_group({'name': 'Unknown'}, 'testuser')
        result = ResearchGroupService.check_group_access(group['id'], 'nonexistent')

        assert result is False


class TestAccessRequests:
    """Tests for group access request management."""

    def test_RES_GRP_038_create_access_request(self, app, db, app_context, mock_user):
        """[RES_GRP-038] Should create an access request."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='requester', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Request Test'}, 'testuser')
        result = ResearchGroupService.create_access_request(
            group['id'], 'requester', message='Please let me in'
        )

        assert result is not None
        assert result['status'] == 'pending'

    def test_RES_GRP_039_create_access_request_already_member(self, app, db, app_context, mock_user):
        """[RES_GRP-039] Should return None if already a member."""
        from services.research_group_service import ResearchGroupService

        group = ResearchGroupService.create_group({'name': 'Already In'}, 'testuser')
        result = ResearchGroupService.create_access_request(group['id'], 'testuser')

        assert result is None

    def test_RES_GRP_040_create_access_request_pending_exists(self, app, db, app_context, mock_user):
        """[RES_GRP-040] Should return existing request if already pending."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='pending_req', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Pending Test'}, 'testuser')
        ResearchGroupService.create_access_request(group['id'], 'pending_req')

        result = ResearchGroupService.create_access_request(group['id'], 'pending_req')
        assert result is not None
        assert result['status'] == 'already_pending'

    def test_RES_GRP_041_create_access_request_group_not_found(self, app, db, app_context):
        """[RES_GRP-041] Should return None for non-existent group."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.create_access_request(99999, 'someone')
        assert result is None

    def test_RES_GRP_042_resolve_access_request_approve(self, app, db, app_context, mock_user):
        """[RES_GRP-042] Should approve an access request and add member."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='approved_user', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Approve Test'}, 'testuser')
        req = ResearchGroupService.create_access_request(group['id'], 'approved_user')

        result = ResearchGroupService.resolve_access_request(req['id'], 'approve', 'testuser')

        assert result is not None
        assert result['status'] == 'approved'
        assert result['action'] == 'approve'

        # Verify member was added
        members = ResearchGroupService.get_members(group['id'])
        usernames = [m.get('username') for m in members]
        assert 'approved_user' in usernames

    def test_RES_GRP_043_resolve_access_request_reject(self, app, db, app_context, mock_user):
        """[RES_GRP-043] Should reject an access request."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='rejected_user', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Reject Test'}, 'testuser')
        req = ResearchGroupService.create_access_request(group['id'], 'rejected_user')

        result = ResearchGroupService.resolve_access_request(req['id'], 'reject', 'testuser')

        assert result is not None
        assert result['status'] == 'rejected'

    def test_RES_GRP_044_resolve_access_request_invalid_action(self, app, db, app_context, mock_user):
        """[RES_GRP-044] Should return None for invalid action."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='invalid_action', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Invalid Action'}, 'testuser')
        req = ResearchGroupService.create_access_request(group['id'], 'invalid_action')

        result = ResearchGroupService.resolve_access_request(req['id'], 'maybe', 'testuser')
        assert result is None

    def test_RES_GRP_045_resolve_access_request_not_found(self, app, db, app_context):
        """[RES_GRP-045] Should return None for non-existent request."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.resolve_access_request(99999, 'approve', 'admin')
        assert result is None

    def test_RES_GRP_046_list_pending_requests(self, app, db, app_context, mock_user):
        """[RES_GRP-046] Should list pending requests for group owner."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='req_user', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'List Requests'}, 'testuser')
        ResearchGroupService.create_access_request(group['id'], 'req_user')

        requests = ResearchGroupService.list_pending_requests('testuser')
        assert len(requests) >= 1
        assert requests[0]['requester_username'] == 'req_user'

    def test_RES_GRP_047_list_pending_requests_no_groups(self, app, db, app_context):
        """[RES_GRP-047] Should return empty list for user with no groups."""
        from services.research_group_service import ResearchGroupService

        result = ResearchGroupService.list_pending_requests('nonexistent')
        assert result == []

    def test_RES_GRP_048_list_group_requests(self, app, db, app_context, mock_user):
        """[RES_GRP-048] Should list all requests for a specific group."""
        from services.research_group_service import ResearchGroupService
        from db.models.user import User

        user2 = User(username='grp_req_user', password_hash='hash', is_active=True, api_key=str(uuid4()))
        db.session.add(user2)
        db.session.commit()

        group = ResearchGroupService.create_group({'name': 'Group Requests'}, 'testuser')
        ResearchGroupService.create_access_request(group['id'], 'grp_req_user')

        requests = ResearchGroupService.list_group_requests(group['id'])
        assert len(requests) >= 1
        assert 'status' in requests[0]


class TestGroupStats:
    """Tests for group statistics."""

    def test_RES_GRP_049_get_group_stats(self, app, db, app_context, mock_user):
        """[RES_GRP-049] Should return group statistics."""
        from services.research_group_service import ResearchGroupService

        group = ResearchGroupService.create_group({'name': 'Stats Group'}, 'testuser')
        stats = ResearchGroupService.get_group_stats(group['id'])

        assert 'conferences' in stats
        assert 'papers' in stats
        assert 'members' in stats
        assert stats['members'] == 1  # just the owner

    def test_RES_GRP_050_get_group_stats_empty(self, app, db, app_context):
        """[RES_GRP-050] Should return zero counts for non-existent group."""
        from services.research_group_service import ResearchGroupService

        stats = ResearchGroupService.get_group_stats(99999)
        assert stats['conferences'] == 0
        assert stats['papers'] == 0
        assert stats['members'] == 0
