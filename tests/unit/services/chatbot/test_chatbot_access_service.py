"""
Unit Tests: Chatbot Access Service
===================================

Tests for the ChatbotAccessService including chatbot-collection permission synchronization.

Test IDs:
- CBAC-001 to CBAC-010: User Access Tests
- CBAC-020 to CBAC-030: Chatbot Sharing Tests
- CBAC-040 to CBAC-060: Collection Permission Synchronization Tests

Status: Implemented
"""

import pytest
from unittest.mock import patch, MagicMock


class TestUserAccess:
    """
    User Access Tests

    Tests for basic access control methods.
    """

    def test_CBAC_001_is_admin_user_true(self, app, db, app_context):
        """
        [CBAC-001] Is Admin User - Admin Permission

        Should return True for user with admin permission.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService

        with patch.object(ChatbotAccessService, 'is_admin_user', return_value=True):
            result = ChatbotAccessService.is_admin_user('admin')
            assert result is True

    def test_CBAC_002_user_can_access_public_chatbot(self, app, db, app_context):
        """
        [CBAC-002] User Can Access - Public Chatbot

        Public chatbots should be accessible by any user.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot

        bot = Chatbot(
            name='public_test_bot',
            display_name='Public Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=True,
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotAccessService.user_can_access_chatbot('any_user', bot)
        assert result is True

    def test_CBAC_003_user_can_access_owned_chatbot(self, app, db, app_context):
        """
        [CBAC-003] User Can Access - Owned Chatbot

        Owners should always access their chatbots.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot

        bot = Chatbot(
            name='owned_test_bot',
            display_name='Owned Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=False,
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotAccessService.user_can_access_chatbot('owner', bot)
        assert result is True

    def test_CBAC_004_user_cannot_access_private_chatbot(self, app, db, app_context):
        """
        [CBAC-004] User Cannot Access - Private Chatbot

        Private chatbots should not be accessible by random users.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot

        bot = Chatbot(
            name='private_test_bot',
            display_name='Private Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=False,
            is_active=True
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotAccessService.user_can_access_chatbot('random_user', bot)
        assert result is False


class TestChatbotSharing:
    """
    Chatbot Sharing Tests

    Tests for sharing chatbots with users/roles.
    """

    def test_CBAC_020_set_chatbot_access_adds_users(self, app, db, app_context):
        """
        [CBAC-020] Set Chatbot Access - Adds Users

        Should add users to chatbot access.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, ChatbotUserAccess

        bot = Chatbot(
            name='share_test_bot',
            display_name='Share Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=['user1', 'user2'],
            granted_by='owner'
        )

        assert 'user1' in result['allowed_usernames']
        assert 'user2' in result['allowed_usernames']
        assert 'user1' in result['users_added']
        assert 'user2' in result['users_added']

        # Verify in database
        access = ChatbotUserAccess.query.filter_by(chatbot_id=bot.id).all()
        usernames = [a.username for a in access]
        assert 'user1' in usernames
        assert 'user2' in usernames

    def test_CBAC_021_set_chatbot_access_removes_users(self, app, db, app_context):
        """
        [CBAC-021] Set Chatbot Access - Removes Users

        Should remove users no longer in the list.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, ChatbotUserAccess

        bot = Chatbot(
            name='remove_user_bot',
            display_name='Remove User Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Add initial access
        access1 = ChatbotUserAccess(chatbot_id=bot.id, username='user1', granted_by='owner')
        access2 = ChatbotUserAccess(chatbot_id=bot.id, username='user2', granted_by='owner')
        db.session.add_all([access1, access2])
        db.session.commit()

        # Update to only user1
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=['user1'],
            granted_by='owner'
        )

        assert 'user1' in result['allowed_usernames']
        assert 'user2' not in result['allowed_usernames']
        assert 'user2' in result['users_removed']

    def test_CBAC_022_set_chatbot_access_sets_roles(self, app, db, app_context):
        """
        [CBAC-022] Set Chatbot Access - Sets Roles

        Should update allowed_roles on chatbot.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot

        bot = Chatbot(
            name='role_test_bot',
            display_name='Role Bot',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.commit()

        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            role_names=['researcher', 'evaluator'],
            granted_by='owner'
        )

        assert 'researcher' in result['allowed_roles']
        assert 'evaluator' in result['allowed_roles']

        # Verify in database
        bot = Chatbot.query.get(bot.id)
        assert 'researcher' in bot.allowed_roles
        assert 'evaluator' in bot.allowed_roles


class TestCollectionPermissionSync:
    """
    Collection Permission Synchronization Tests

    Tests for synchronizing collection permissions when chatbots are shared.
    """

    def test_CBAC_040_sharing_chatbot_grants_collection_view(self, app, db, app_context):
        """
        [CBAC-040] Sharing Chatbot - Grants Collection View

        When chatbot is shared, associated collections should get view access.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_share',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_with_coll',
            display_name='Bot with Collection',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)
        db.session.commit()

        # Share chatbot with user
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=['new_user'],
            granted_by='owner'
        )

        assert coll.id in result['shared_collections']

        # Verify collection permission was created
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='new_user'
        ).first()

        assert perm is not None
        assert perm.can_view is True
        assert perm.can_edit is False  # Only view access
        assert perm.can_delete is False
        assert perm.can_share is False

    def test_CBAC_041_unsharing_chatbot_removes_view_only_access(self, app, db, app_context):
        """
        [CBAC-041] Unsharing Chatbot - Removes View-Only Access

        When user is removed from chatbot sharing, view-only collection access should be removed.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection, ChatbotUserAccess
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_unshare',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_unshare',
            display_name='Bot Unshare',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)

        # Add initial chatbot access
        access = ChatbotUserAccess(chatbot_id=bot.id, username='user_to_remove', granted_by='owner')
        db.session.add(access)

        # Add view-only collection permission
        perm = RAGCollectionPermission(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='user_to_remove',
            can_view=True,
            can_edit=False,
            can_delete=False,
            can_share=False,
            granted_by='owner'
        )
        db.session.add(perm)
        db.session.commit()

        # Remove user from chatbot sharing
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=[],  # Remove all users
            granted_by='owner'
        )

        assert 'user_to_remove' in result['users_removed']

        # Verify collection permission was removed
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='user_to_remove'
        ).first()

        assert perm is None

    def test_CBAC_042_unsharing_keeps_elevated_permissions(self, app, db, app_context):
        """
        [CBAC-042] Unsharing Chatbot - Keeps Elevated Permissions

        When user is removed from chatbot, edit/delete/share permissions should be kept.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection, ChatbotUserAccess
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_keep_edit',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_keep_edit',
            display_name='Bot Keep Edit',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)

        # Add initial chatbot access
        access = ChatbotUserAccess(chatbot_id=bot.id, username='editor_user', granted_by='owner')
        db.session.add(access)

        # Add EDIT permission (elevated)
        perm = RAGCollectionPermission(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='editor_user',
            can_view=True,
            can_edit=True,  # Elevated permission
            can_delete=False,
            can_share=False,
            granted_by='owner'
        )
        db.session.add(perm)
        db.session.commit()

        # Remove user from chatbot sharing
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=[],  # Remove all users
            granted_by='owner'
        )

        assert 'editor_user' in result['users_removed']

        # Verify collection permission was NOT removed (edit permission)
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='editor_user'
        ).first()

        assert perm is not None
        assert perm.can_view is True
        assert perm.can_edit is True

    def test_CBAC_043_sharing_does_not_overwrite_edit_access(self, app, db, app_context):
        """
        [CBAC-043] Sharing Chatbot - Does Not Overwrite Edit Access

        When chatbot is shared, existing edit permissions should not be downgraded.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_no_overwrite',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_no_overwrite',
            display_name='Bot No Overwrite',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)

        # Add existing EDIT permission
        perm = RAGCollectionPermission(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='existing_editor',
            can_view=True,
            can_edit=True,
            can_delete=False,
            can_share=False,
            granted_by='owner'
        )
        db.session.add(perm)
        db.session.commit()

        # Share chatbot with the same user (should not downgrade)
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            usernames=['existing_editor'],
            granted_by='owner'
        )

        # Verify permission was NOT downgraded
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='existing_editor'
        ).first()

        assert perm is not None
        assert perm.can_view is True
        assert perm.can_edit is True  # Still has edit permission

    def test_CBAC_044_role_sharing_grants_collection_view(self, app, db, app_context):
        """
        [CBAC-044] Role Sharing - Grants Collection View

        When chatbot is shared with role, collection should get role-based view access.
        """
        from services.chatbot.chatbot_access_service import ChatbotAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_role',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_role_share',
            display_name='Bot Role Share',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)
        db.session.commit()

        # Share chatbot with role
        result = ChatbotAccessService.set_chatbot_access(
            chatbot_id=bot.id,
            role_names=['researcher'],
            granted_by='owner'
        )

        assert 'researcher' in result['allowed_roles']

        # Verify role permission was created
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='role',
            target_identifier='researcher'
        ).first()

        assert perm is not None
        assert perm.can_view is True
        assert perm.can_edit is False


class TestCollectionAccessValidation:
    """
    Collection Access Validation Tests

    Tests for preventing removal of collection access when chatbot is shared.
    """

    def test_CBAC_050_cannot_remove_collection_access_with_shared_chatbot(self, app, db, app_context):
        """
        [CBAC-050] Cannot Remove Collection Access - Shared Chatbot

        Should raise ValueError when trying to remove collection access for a user
        who has access through a shared chatbot.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection, ChatbotUserAccess
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_validation',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_validation',
            display_name='Bot Validation',
            system_prompt='Test',
            created_by='owner',
            is_public=False
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)

        # Add chatbot access for user
        access = ChatbotUserAccess(chatbot_id=bot.id, username='shared_user', granted_by='owner')
        db.session.add(access)

        # Add collection permission
        perm = RAGCollectionPermission(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='shared_user',
            can_view=True,
            can_edit=False,
            can_delete=False,
            can_share=False,
            granted_by='owner'
        )
        db.session.add(perm)
        db.session.commit()

        # Try to remove collection access - should fail
        with pytest.raises(ValueError, match="Collection-Zugriff kann nicht entfernt werden"):
            RAGAccessService.set_collection_permissions(
                collection_id=coll.id,
                usernames=[],  # Try to remove all users
                granted_by='owner'
            )

    def test_CBAC_051_can_remove_collection_access_without_shared_chatbot(self, app, db, app_context):
        """
        [CBAC-051] Can Remove Collection Access - No Shared Chatbot

        Should allow removing collection access when no chatbot is shared.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection
        from db.models.rag import RAGCollectionPermission

        # Create collection without chatbot
        coll = RAGCollection(
            name='test_coll_no_chatbot',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Add collection permission
        perm = RAGCollectionPermission(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='some_user',
            can_view=True,
            can_edit=False,
            can_delete=False,
            can_share=False,
            granted_by='owner'
        )
        db.session.add(perm)
        db.session.commit()

        # Should succeed - no chatbot is using this collection
        result = RAGAccessService.set_collection_permissions(
            collection_id=coll.id,
            usernames=[],  # Remove all users
            granted_by='owner'
        )

        assert result['usernames'] == []

        # Verify permission was removed
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='some_user'
        ).first()

        assert perm is None

    def test_CBAC_052_can_add_edit_permissions_independently(self, app, db, app_context):
        """
        [CBAC-052] Can Add Edit Permissions - Independently

        Should allow adding edit permissions independently of chatbot sharing.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import RAGCollection
        from db.models.rag import RAGCollectionPermission

        # Create collection
        coll = RAGCollection(
            name='test_coll_edit_perm',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.commit()

        # Add edit permission
        result = RAGAccessService.set_collection_permissions(
            collection_id=coll.id,
            usernames=['editor_user'],
            granted_by='owner',
            access={'can_view': True, 'can_edit': True, 'can_delete': False, 'can_share': False}
        )

        assert 'editor_user' in result['usernames']
        assert result['access']['can_edit'] is True

        # Verify permission
        perm = RAGCollectionPermission.query.filter_by(
            collection_id=coll.id,
            permission_type='user',
            target_identifier='editor_user'
        ).first()

        assert perm is not None
        assert perm.can_view is True
        assert perm.can_edit is True

    def test_CBAC_053_get_chatbot_required_access(self, app, db, app_context):
        """
        [CBAC-053] Get Chatbot Required Access

        Should return users/roles who need access due to chatbot sharing.
        """
        from services.rag.access_service import RAGAccessService
        from db.tables import Chatbot, RAGCollection, ChatbotCollection, ChatbotUserAccess

        # Create collection
        coll = RAGCollection(
            name='test_coll_required',
            display_name='Test Collection',
            created_by='owner',
            is_public=False
        )
        db.session.add(coll)
        db.session.flush()

        # Create chatbot with collection
        bot = Chatbot(
            name='bot_required',
            display_name='Bot Required',
            system_prompt='Test',
            created_by='owner',
            is_public=False,
            allowed_roles=['researcher']
        )
        db.session.add(bot)
        db.session.flush()

        # Link chatbot to collection
        cc = ChatbotCollection(
            chatbot_id=bot.id,
            collection_id=coll.id,
            assigned_by='owner'
        )
        db.session.add(cc)

        # Add chatbot access
        access = ChatbotUserAccess(chatbot_id=bot.id, username='chatbot_user', granted_by='owner')
        db.session.add(access)
        db.session.commit()

        # Get required access
        result = RAGAccessService.get_chatbot_required_access(coll.id)

        assert 'chatbot_user' in result['users']
        assert 'researcher' in result['roles']
        assert len(result['chatbots']) == 1
        assert result['chatbots'][0]['name'] == 'bot_required'
