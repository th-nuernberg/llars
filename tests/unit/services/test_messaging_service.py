"""
Unit tests for MessagingService.

Tests conversation management, message sending/receiving,
read status tracking, encryption keys, and AI key grants.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestDirectConversations:
    """Tests for direct (1:1) conversation creation and retrieval."""

    def test_MSG_001_create_direct_conversation(self, app, db, app_context):
        """[MSG-001] Should create a direct conversation between two users."""
        from services.messaging_service import MessagingService

        result = MessagingService.create_direct_conversation('alice', 'bob')

        assert result is not None
        assert result['conversation_type'] == 'direct'
        assert result['created_by'] == 'alice'
        participants = result['participants']
        usernames = {p['username'] for p in participants}
        assert usernames == {'alice', 'bob'}

    def test_MSG_002_create_direct_conversation_self_raises(self, app, db, app_context):
        """[MSG-002] Should raise ValueError when creating conversation with self."""
        from services.messaging_service import MessagingService

        with pytest.raises(ValueError, match="yourself"):
            MessagingService.create_direct_conversation('alice', 'alice')

    def test_MSG_003_create_direct_conversation_returns_existing(self, app, db, app_context):
        """[MSG-003] Should return existing conversation instead of creating duplicate."""
        from services.messaging_service import MessagingService

        conv1 = MessagingService.create_direct_conversation('alice', 'bob')
        conv2 = MessagingService.create_direct_conversation('alice', 'bob')

        assert conv1['id'] == conv2['id']

    def test_MSG_004_get_conversation(self, app, db, app_context):
        """[MSG-004] Should retrieve a conversation by ID for a participant."""
        from services.messaging_service import MessagingService

        created = MessagingService.create_direct_conversation('alice', 'bob')
        fetched = MessagingService.get_conversation(created['id'], 'alice')

        assert fetched is not None
        assert fetched['id'] == created['id']

    def test_MSG_005_get_conversation_non_participant(self, app, db, app_context):
        """[MSG-005] Should return None for non-participant access."""
        from services.messaging_service import MessagingService

        created = MessagingService.create_direct_conversation('alice', 'bob')
        fetched = MessagingService.get_conversation(created['id'], 'charlie')

        assert fetched is None

    def test_MSG_006_get_conversation_not_found(self, app, db, app_context):
        """[MSG-006] Should return None for non-existent conversation."""
        from services.messaging_service import MessagingService

        result = MessagingService.get_conversation(99999, 'alice')
        assert result is None

    def test_MSG_007_get_conversations_list(self, app, db, app_context):
        """[MSG-007] Should list user conversations ordered by last message."""
        from services.messaging_service import MessagingService

        MessagingService.create_direct_conversation('alice', 'bob')
        MessagingService.create_direct_conversation('alice', 'charlie')

        convs = MessagingService.get_conversations('alice')
        assert len(convs) == 2


class TestGroupConversations:
    """Tests for group conversation management."""

    def test_MSG_008_create_group_conversation(self, app, db, app_context):
        """[MSG-008] Should create a group conversation."""
        from services.messaging_service import MessagingService

        result = MessagingService.create_group_conversation(
            creator='alice',
            name='Test Group',
            member_usernames=['bob', 'charlie'],
            description='A test group',
        )

        assert result is not None
        assert result['conversation_type'] == 'group'
        assert result['name'] == 'Test Group'
        assert result['description'] == 'A test group'
        usernames = {p['username'] for p in result['participants']}
        assert 'alice' in usernames
        assert 'bob' in usernames
        assert 'charlie' in usernames

    def test_MSG_009_create_group_empty_name_raises(self, app, db, app_context):
        """[MSG-009] Should raise ValueError for empty group name."""
        from services.messaging_service import MessagingService

        with pytest.raises(ValueError, match="Group name"):
            MessagingService.create_group_conversation(
                creator='alice',
                name='',
                member_usernames=['bob'],
            )

    def test_MSG_010_create_group_adds_creator(self, app, db, app_context):
        """[MSG-010] Should auto-add creator as member if not in list."""
        from services.messaging_service import MessagingService

        result = MessagingService.create_group_conversation(
            creator='alice',
            name='Auto Creator',
            member_usernames=['bob'],
        )

        usernames = {p['username'] for p in result['participants']}
        assert 'alice' in usernames

    def test_MSG_011_update_group_info(self, app, db, app_context):
        """[MSG-011] Should update group name and description."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Original', member_usernames=['bob'],
        )

        updated = MessagingService.update_group_info(
            conv['id'], 'alice', name='Updated', description='New desc',
        )

        assert updated is not None
        assert updated['name'] == 'Updated'
        assert updated['description'] == 'New desc'

    def test_MSG_012_update_group_info_non_admin_fails(self, app, db, app_context):
        """[MSG-012] Should return None when non-admin tries to update group."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Protected', member_usernames=['bob'],
        )

        result = MessagingService.update_group_info(conv['id'], 'bob', name='Hacked')
        assert result is None

    def test_MSG_013_add_group_member(self, app, db, app_context):
        """[MSG-013] Should add a new member to the group."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Add Test', member_usernames=['bob'],
        )

        result = MessagingService.add_group_member(conv['id'], 'charlie', 'alice')
        assert result is not None
        usernames = {p['username'] for p in result['participants']}
        assert 'charlie' in usernames

    def test_MSG_014_add_group_member_non_admin_fails(self, app, db, app_context):
        """[MSG-014] Should return None when non-admin tries to add member."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Permission Test', member_usernames=['bob'],
        )

        result = MessagingService.add_group_member(conv['id'], 'charlie', 'bob')
        assert result is None

    def test_MSG_015_remove_group_member(self, app, db, app_context):
        """[MSG-015] Should remove a member from the group."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Remove Test', member_usernames=['bob', 'charlie'],
        )

        result = MessagingService.remove_group_member(conv['id'], 'charlie', 'alice')
        assert result is True

    def test_MSG_016_remove_group_owner_fails(self, app, db, app_context):
        """[MSG-016] Should not allow removing the group owner."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Owner Test', member_usernames=['bob'],
        )

        result = MessagingService.remove_group_member(conv['id'], 'alice', 'alice')
        assert result is False

    def test_MSG_017_self_leave_group(self, app, db, app_context):
        """[MSG-017] Should allow non-owner to leave group."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_group_conversation(
            creator='alice', name='Leave Test', member_usernames=['bob'],
        )

        result = MessagingService.remove_group_member(conv['id'], 'bob', 'bob')
        assert result is True

    def test_MSG_018_mute_conversation(self, app, db, app_context):
        """[MSG-018] Should mute/unmute a conversation for a user."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')

        result = MessagingService.mute_conversation(conv['id'], 'alice', True)
        assert result is True

        result = MessagingService.mute_conversation(conv['id'], 'alice', False)
        assert result is True

    def test_MSG_019_mute_non_participant_fails(self, app, db, app_context):
        """[MSG-019] Should return False when non-participant tries to mute."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        result = MessagingService.mute_conversation(conv['id'], 'charlie', True)
        assert result is False


class TestMessages:
    """Tests for sending, editing, and deleting messages."""

    def _create_conv(self, MessagingService):
        """Helper to create a direct conversation."""
        return MessagingService.create_direct_conversation('alice', 'bob')

    def test_MSG_020_send_message(self, app, db, app_context):
        """[MSG-020] Should send a text message."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Hello Bob!')

        assert msg is not None
        assert msg['content'] == 'Hello Bob!'
        assert msg['sender_username'] == 'alice'
        assert msg['message_type'] == 'text'

    def test_MSG_021_send_message_non_participant_fails(self, app, db, app_context):
        """[MSG-021] Should return None when non-participant sends message."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        result = MessagingService.send_message(conv['id'], 'charlie', 'Intruder!')

        assert result is None

    def test_MSG_022_send_message_updates_last_message(self, app, db, app_context):
        """[MSG-022] Should update conversation's last_message_at and preview."""
        from services.messaging_service import MessagingService
        from db.models.messaging import MessagingConversation

        conv = self._create_conv(MessagingService)
        MessagingService.send_message(conv['id'], 'alice', 'Latest message')

        updated_conv = MessagingConversation.query.get(conv['id'])
        assert updated_conv.last_message_at is not None
        assert updated_conv.last_message_preview == 'Latest message'

    def test_MSG_023_send_encrypted_message(self, app, db, app_context):
        """[MSG-023] Should handle encrypted message preview."""
        from services.messaging_service import MessagingService
        from db.models.messaging import MessagingConversation

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(
            conv['id'], 'alice', 'encrypted-content',
            encryption_metadata={'algorithm': 'aes-256'},
        )

        assert msg is not None
        assert msg['is_encrypted'] is True

        updated_conv = MessagingConversation.query.get(conv['id'])
        assert updated_conv.last_message_preview == '[Encrypted]'

    def test_MSG_024_send_message_increments_unread(self, app, db, app_context):
        """[MSG-024] Should increment unread count for other participants."""
        from services.messaging_service import MessagingService
        from db.models.messaging import MessagingParticipant

        conv = self._create_conv(MessagingService)
        MessagingService.send_message(conv['id'], 'alice', 'Read me')

        bob_participant = MessagingParticipant.query.filter_by(
            conversation_id=conv['id'], username='bob'
        ).first()
        assert bob_participant.unread_count == 1

    def test_MSG_025_get_messages(self, app, db, app_context):
        """[MSG-025] Should retrieve messages for a conversation."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        MessagingService.send_message(conv['id'], 'alice', 'Msg 1')
        MessagingService.send_message(conv['id'], 'bob', 'Msg 2')

        messages = MessagingService.get_messages(conv['id'], 'alice')
        assert len(messages) == 2

    def test_MSG_026_get_messages_non_participant_empty(self, app, db, app_context):
        """[MSG-026] Should return empty list for non-participants."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        MessagingService.send_message(conv['id'], 'alice', 'Secret')

        messages = MessagingService.get_messages(conv['id'], 'charlie')
        assert messages == []

    def test_MSG_027_get_messages_pagination(self, app, db, app_context):
        """[MSG-027] Should support cursor-based pagination."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        for i in range(5):
            MessagingService.send_message(conv['id'], 'alice', f'Msg {i}')

        messages = MessagingService.get_messages(conv['id'], 'alice', limit=3)
        assert len(messages) == 3

    def test_MSG_028_edit_message(self, app, db, app_context):
        """[MSG-028] Should allow sender to edit their message."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Typo')

        edited = MessagingService.edit_message(msg['id'], 'alice', 'Fixed')
        assert edited is not None
        assert edited['content'] == 'Fixed'
        assert edited['is_edited'] is True

    def test_MSG_029_edit_message_not_sender_fails(self, app, db, app_context):
        """[MSG-029] Should reject edits from non-sender."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Original')

        result = MessagingService.edit_message(msg['id'], 'bob', 'Hacked')
        assert result is None

    def test_MSG_030_delete_message(self, app, db, app_context):
        """[MSG-030] Should soft-delete a message."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Delete me')

        result = MessagingService.delete_message(msg['id'], 'alice')
        assert result is True

    def test_MSG_031_delete_message_non_sender_non_admin_fails(self, app, db, app_context):
        """[MSG-031] Should reject deletion from non-sender without admin role."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Protected')

        result = MessagingService.delete_message(msg['id'], 'bob')
        assert result is False

    def test_MSG_032_delete_already_deleted(self, app, db, app_context):
        """[MSG-032] Should return False for already deleted message."""
        from services.messaging_service import MessagingService

        conv = self._create_conv(MessagingService)
        msg = MessagingService.send_message(conv['id'], 'alice', 'Gone')

        MessagingService.delete_message(msg['id'], 'alice')
        result = MessagingService.delete_message(msg['id'], 'alice')
        assert result is False


class TestReadStatus:
    """Tests for read receipts and unread counts."""

    def test_MSG_033_mark_as_read(self, app, db, app_context):
        """[MSG-033] Should mark messages as read and reset unread count."""
        from services.messaging_service import MessagingService
        from db.models.messaging import MessagingParticipant

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        msg = MessagingService.send_message(conv['id'], 'alice', 'Read this')

        result = MessagingService.mark_as_read(conv['id'], 'bob', msg['id'])
        assert result is True

        bob_p = MessagingParticipant.query.filter_by(
            conversation_id=conv['id'], username='bob'
        ).first()
        assert bob_p.unread_count == 0

    def test_MSG_034_mark_as_read_non_participant(self, app, db, app_context):
        """[MSG-034] Should return False for non-participant."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        result = MessagingService.mark_as_read(conv['id'], 'charlie', 1)
        assert result is False

    def test_MSG_035_get_unread_counts(self, app, db, app_context):
        """[MSG-035] Should return per-conversation unread counts."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        MessagingService.send_message(conv['id'], 'alice', 'Msg 1')
        MessagingService.send_message(conv['id'], 'alice', 'Msg 2')

        counts = MessagingService.get_unread_counts('bob')
        assert counts['total'] == 2
        assert str(conv['id']) in counts['per_conversation']


class TestEncryptionKeys:
    """Tests for encryption key bundle management."""

    def test_MSG_036_store_key_bundle(self, app, db, app_context):
        """[MSG-036] Should store a new key bundle."""
        from services.messaging_service import MessagingService

        key_data = {
            'identity_public_key': 'pub-key-123',
            'signed_prekey_public': 'prekey-456',
            'signed_prekey_id': 1,
            'one_time_prekeys': ['otk-1', 'otk-2'],
        }

        result = MessagingService.store_key_bundle('alice', key_data)
        assert result is not None
        assert result['identity_public_key'] == 'pub-key-123'
        assert result['signed_prekey_public'] == 'prekey-456'

    def test_MSG_037_update_key_bundle(self, app, db, app_context):
        """[MSG-037] Should update an existing key bundle."""
        from services.messaging_service import MessagingService

        key_data = {
            'identity_public_key': 'old-key',
            'signed_prekey_public': 'old-prekey',
        }
        MessagingService.store_key_bundle('alice', key_data)

        updated_data = {
            'identity_public_key': 'new-key',
            'signed_prekey_public': 'new-prekey',
        }
        result = MessagingService.store_key_bundle('alice', updated_data)
        assert result['identity_public_key'] == 'new-key'

    def test_MSG_038_get_key_bundle(self, app, db, app_context):
        """[MSG-038] Should retrieve a key bundle."""
        from services.messaging_service import MessagingService

        key_data = {
            'identity_public_key': 'pub-key',
            'signed_prekey_public': 'prekey',
        }
        MessagingService.store_key_bundle('alice', key_data)

        result = MessagingService.get_key_bundle('alice')
        assert result is not None
        assert result['identity_public_key'] == 'pub-key'

    def test_MSG_039_get_key_bundle_not_found(self, app, db, app_context):
        """[MSG-039] Should return None for user without key bundle."""
        from services.messaging_service import MessagingService

        result = MessagingService.get_key_bundle('ghost')
        assert result is None

    def test_MSG_040_get_key_bundles_multiple(self, app, db, app_context):
        """[MSG-040] Should retrieve key bundles for multiple users."""
        from services.messaging_service import MessagingService

        MessagingService.store_key_bundle('alice', {
            'identity_public_key': 'alice-key',
            'signed_prekey_public': 'alice-prekey',
        })
        MessagingService.store_key_bundle('bob', {
            'identity_public_key': 'bob-key',
            'signed_prekey_public': 'bob-prekey',
        })

        bundles = MessagingService.get_key_bundles(['alice', 'bob'])
        assert 'alice' in bundles
        assert 'bob' in bundles
        assert bundles['alice']['identity_public_key'] == 'alice-key'


class TestAIKeyGrants:
    """Tests for AI key grant management."""

    def test_MSG_041_grant_ai_access(self, app, db, app_context):
        """[MSG-041] Should grant AI access to a conversation."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        result = MessagingService.grant_ai_access('alice', conv['id'], 'encrypted-key-data')

        assert result is True

    def test_MSG_042_grant_ai_access_non_participant_fails(self, app, db, app_context):
        """[MSG-042] Should return False for non-participant."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        result = MessagingService.grant_ai_access('charlie', conv['id'], 'encrypted-key')

        assert result is False

    def test_MSG_043_grant_ai_access_update_existing(self, app, db, app_context):
        """[MSG-043] Should update existing AI access grant."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        MessagingService.grant_ai_access('alice', conv['id'], 'old-key')
        result = MessagingService.grant_ai_access('alice', conv['id'], 'new-key')

        assert result is True

    def test_MSG_044_revoke_ai_access(self, app, db, app_context):
        """[MSG-044] Should revoke AI access."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        MessagingService.grant_ai_access('alice', conv['id'], 'encrypted-key')

        result = MessagingService.revoke_ai_access('alice', conv['id'])
        assert result is True

    def test_MSG_045_revoke_ai_access_not_found(self, app, db, app_context):
        """[MSG-045] Should return False when revoking non-existent grant."""
        from services.messaging_service import MessagingService

        result = MessagingService.revoke_ai_access('ghost', 99999)
        assert result is False


class TestAttachments:
    """Tests for message attachments."""

    def test_MSG_046_add_attachment(self, app, db, app_context):
        """[MSG-046] Should add an attachment to a message."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        msg = MessagingService.send_message(conv['id'], 'alice', 'See attached')

        result = MessagingService.add_attachment(
            msg['id'], 'alice', 'test.pdf', 'application/pdf', b'pdf-content'
        )

        assert result is not None
        assert result['filename'] == 'test.pdf'
        assert result['mime_type'] == 'application/pdf'

    def test_MSG_047_add_attachment_non_sender_fails(self, app, db, app_context):
        """[MSG-047] Should reject attachment from non-sender."""
        from services.messaging_service import MessagingService

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        msg = MessagingService.send_message(conv['id'], 'alice', 'My msg')

        result = MessagingService.add_attachment(
            msg['id'], 'bob', 'hack.pdf', 'application/pdf', b'data'
        )
        assert result is None

    def test_MSG_048_add_attachment_too_large_raises(self, app, db, app_context):
        """[MSG-048] Should raise ValueError for oversized attachment."""
        from services.messaging_service import MessagingService, MAX_ATTACHMENT_SIZE

        conv = MessagingService.create_direct_conversation('alice', 'bob')
        msg = MessagingService.send_message(conv['id'], 'alice', 'Big file')

        large_data = b'x' * (MAX_ATTACHMENT_SIZE + 1)
        with pytest.raises(ValueError, match="maximum size"):
            MessagingService.add_attachment(
                msg['id'], 'alice', 'large.bin', 'application/octet-stream', large_data
            )
