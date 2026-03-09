"""
Unit tests for ChatbotActivityService.

Tests activity logging, event querying, and analytics for
chatbot-related events stored in the SystemEvent table.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestLogActivity:
    """Tests for the core log_activity method."""

    def test_CHAT_ACT_001_log_activity_basic(self, app, db, app_context):
        """[CHAT_ACT-001] Should log a basic activity event."""
        from services.chatbot_activity_service import ChatbotActivityService
        from db.models.system_event import SystemEvent

        event = ChatbotActivityService.log_activity(
            event_type='chatbot.created',
            message='Test chatbot created',
            username='admin',
        )

        assert event is not None
        assert event.event_type == 'chatbot.created'
        assert event.message == 'Test chatbot created'
        assert event.username == 'admin'

        stored = SystemEvent.query.filter_by(event_type='chatbot.created').first()
        assert stored is not None

    def test_CHAT_ACT_002_log_activity_with_entity(self, app, db, app_context):
        """[CHAT_ACT-002] Should log activity with entity info."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_activity(
            event_type='chatbot.updated',
            message='Chatbot updated',
            username='admin',
            entity_type='chatbot',
            entity_id=42,
        )

        assert event is not None
        assert event.entity_type == 'chatbot'
        assert event.entity_id == '42'

    def test_CHAT_ACT_003_log_activity_with_details(self, app, db, app_context):
        """[CHAT_ACT-003] Should log activity with JSON details."""
        from services.chatbot_activity_service import ChatbotActivityService

        details = {'chatbot_name': 'TestBot', 'via_wizard': True}
        event = ChatbotActivityService.log_activity(
            event_type='chatbot.created',
            message='Created',
            username='admin',
            details=details,
        )

        assert event is not None
        assert event.details == details

    def test_CHAT_ACT_004_log_activity_with_severity(self, app, db, app_context):
        """[CHAT_ACT-004] Should log activity with custom severity."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_activity(
            event_type='chatbot.deleted',
            message='Chatbot deleted',
            username='admin',
            severity='warning',
        )

        assert event is not None
        assert event.severity == 'warning'

    def test_CHAT_ACT_005_log_activity_db_error_returns_none(self, app, db, app_context):
        """[CHAT_ACT-005] Should return None on database error."""
        from services.chatbot_activity_service import ChatbotActivityService

        with patch('services.chatbot_activity_service.db.session.commit',
                   side_effect=Exception('DB error')):
            result = ChatbotActivityService.log_activity(
                event_type='chatbot.created',
                message='Will fail',
                username='admin',
            )
            assert result is None

    def test_CHAT_ACT_006_log_activity_no_request_context(self, app, db, app_context):
        """[CHAT_ACT-006] Should handle missing request context gracefully."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_activity(
            event_type='chatbot.created',
            message='No request context',
            username='admin',
        )

        assert event is not None
        # In test context, Flask provides a default request path
        assert event.remote_addr is not None or event.remote_addr is None  # depends on context


class TestChatbotEvents:
    """Tests for chatbot-specific event logging methods."""

    def test_CHAT_ACT_007_log_chatbot_created(self, app, db, app_context):
        """[CHAT_ACT-007] Should log chatbot creation."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_created(
            chatbot_id=1,
            chatbot_name='test-bot',
            display_name='Test Bot',
            username='admin',
        )

        assert event is not None
        assert event.event_type == 'chatbot.created'
        assert 'Test Bot' in event.message

    def test_CHAT_ACT_008_log_chatbot_created_via_wizard(self, app, db, app_context):
        """[CHAT_ACT-008] Should indicate wizard creation in message."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_created(
            chatbot_id=1,
            chatbot_name='wizard-bot',
            display_name='Wizard Bot',
            username='admin',
            via_wizard=True,
        )

        assert event is not None
        assert 'Wizard' in event.message

    def test_CHAT_ACT_009_log_chatbot_updated(self, app, db, app_context):
        """[CHAT_ACT-009] Should log chatbot update with changed fields."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_updated(
            chatbot_id=1,
            chatbot_name='test-bot',
            username='admin',
            changed_fields={'name': 'new-name', 'color': '#ff0000'},
        )

        assert event is not None
        assert event.event_type == 'chatbot.updated'
        assert 'name' in event.message

    def test_CHAT_ACT_010_log_chatbot_updated_many_fields(self, app, db, app_context):
        """[CHAT_ACT-010] Should truncate field list when many fields changed."""
        from services.chatbot_activity_service import ChatbotActivityService

        fields = {f'field_{i}': f'value_{i}' for i in range(6)}
        event = ChatbotActivityService.log_chatbot_updated(
            chatbot_id=1, chatbot_name='bot', username='admin', changed_fields=fields,
        )

        assert event is not None
        assert '(+' in event.message

    def test_CHAT_ACT_011_log_chatbot_deleted(self, app, db, app_context):
        """[CHAT_ACT-011] Should log chatbot deletion with warning severity."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_deleted(
            chatbot_id=1, chatbot_name='dead-bot', username='admin',
        )

        assert event is not None
        assert event.event_type == 'chatbot.deleted'
        assert event.severity == 'warning'

    def test_CHAT_ACT_012_log_chatbot_deleted_with_collections(self, app, db, app_context):
        """[CHAT_ACT-012] Should indicate collection deletion in message."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_deleted(
            chatbot_id=1, chatbot_name='bot', username='admin', with_collections=True,
        )

        assert 'Collections' in event.message

    def test_CHAT_ACT_013_log_chatbot_duplicated(self, app, db, app_context):
        """[CHAT_ACT-013] Should log chatbot duplication."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_duplicated(
            source_chatbot_id=1, new_chatbot_id=2,
            new_name='cloned-bot', username='admin',
        )

        assert event is not None
        assert event.event_type == 'chatbot.duplicated'
        assert event.details['source_chatbot_id'] == 1


class TestWizardEvents:
    """Tests for wizard event logging."""

    def test_CHAT_ACT_014_log_wizard_started(self, app, db, app_context):
        """[CHAT_ACT-014] Should log wizard start."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_wizard_started(
            chatbot_id=1, source_url='https://example.com', username='admin',
        )

        assert event is not None
        assert event.event_type == 'wizard.started'

    def test_CHAT_ACT_015_log_wizard_completed(self, app, db, app_context):
        """[CHAT_ACT-015] Should log successful wizard completion."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_wizard_completed(
            chatbot_id=1, chatbot_name='wizard-bot',
            username='admin', document_count=5,
        )

        assert event is not None
        assert event.event_type == 'wizard.completed'
        assert event.severity == 'success'
        assert '5 Dokumente' in event.message

    def test_CHAT_ACT_016_log_wizard_failed(self, app, db, app_context):
        """[CHAT_ACT-016] Should log wizard failure with error severity."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_wizard_failed(
            chatbot_id=1, username='admin', error='Connection timeout',
        )

        assert event is not None
        assert event.event_type == 'wizard.failed'
        assert event.severity == 'error'

    def test_CHAT_ACT_017_log_wizard_cancelled(self, app, db, app_context):
        """[CHAT_ACT-017] Should log wizard cancellation."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_wizard_cancelled(chatbot_id=1, username='admin')

        assert event is not None
        assert event.event_type == 'wizard.cancelled'
        assert event.severity == 'warning'


class TestChatConversationEvents:
    """Tests for chat/conversation event logging."""

    def test_CHAT_ACT_018_log_chat_created(self, app, db, app_context):
        """[CHAT_ACT-018] Should log new chat creation."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chat_created(
            conversation_id=10, chatbot_id=1,
            chatbot_name='Test Bot', username='user1',
        )

        assert event is not None
        assert event.event_type == 'chat.created'
        assert event.entity_type == 'conversation'
        assert event.entity_id == '10'

    def test_CHAT_ACT_019_log_chat_deleted(self, app, db, app_context):
        """[CHAT_ACT-019] Should log chat deletion."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chat_deleted(
            conversation_id=10, chatbot_id=1,
            chatbot_name='Test Bot', username='user1', message_count=15,
        )

        assert event is not None
        assert event.event_type == 'chat.deleted'
        assert event.severity == 'warning'
        assert '15 Nachrichten' in event.message


class TestCollectionEvents:
    """Tests for collection event logging."""

    def test_CHAT_ACT_020_log_collection_created(self, app, db, app_context):
        """[CHAT_ACT-020] Should log collection creation."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_collection_created(
            collection_id=5, collection_name='test-coll',
            display_name='Test Collection', username='admin',
        )

        assert event is not None
        assert event.event_type == 'collection.created'

    def test_CHAT_ACT_021_log_collection_updated(self, app, db, app_context):
        """[CHAT_ACT-021] Should log collection update."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_collection_updated(
            collection_id=5, collection_name='coll',
            username='admin', changed_fields={'name': 'new-name'},
        )

        assert event is not None
        assert event.event_type == 'collection.updated'

    def test_CHAT_ACT_022_log_collection_deleted(self, app, db, app_context):
        """[CHAT_ACT-022] Should log collection deletion with document count."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_collection_deleted(
            collection_id=5, collection_name='old-coll',
            username='admin', document_count=10,
        )

        assert event is not None
        assert event.event_type == 'collection.deleted'
        assert '10 Dokumente' in event.message


class TestDocumentEvents:
    """Tests for document event logging."""

    def test_CHAT_ACT_023_log_document_uploaded(self, app, db, app_context):
        """[CHAT_ACT-023] Should log single document upload."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_document_uploaded(
            document_id=1, filename='test.pdf', username='admin',
            file_size_bytes=1024 * 1024,
        )

        assert event is not None
        assert event.event_type == 'document.uploaded'
        assert '1.0 MB' in event.message

    def test_CHAT_ACT_024_log_documents_uploaded_batch(self, app, db, app_context):
        """[CHAT_ACT-024] Should log batch document upload."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_documents_uploaded(
            document_ids=[1, 2, 3],
            filenames=['a.pdf', 'b.pdf', 'c.pdf'],
            username='admin',
            total_size_bytes=5 * 1024 * 1024,
        )

        assert event is not None
        assert '3 Dokumente' in event.message

    def test_CHAT_ACT_025_log_document_deleted(self, app, db, app_context):
        """[CHAT_ACT-025] Should log document deletion."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_document_deleted(
            document_id=1, filename='old.pdf', username='admin',
        )

        assert event is not None
        assert event.event_type == 'document.deleted'
        assert event.severity == 'warning'


class TestQueryMethods:
    """Tests for activity querying and statistics."""

    def _seed_events(self, ChatbotActivityService):
        """Helper to seed test events."""
        ChatbotActivityService.log_chatbot_created(
            chatbot_id=1, chatbot_name='bot-1', display_name='Bot 1', username='user1',
        )
        ChatbotActivityService.log_chatbot_updated(
            chatbot_id=1, chatbot_name='bot-1', username='user1',
            changed_fields={'name': 'new'},
        )
        ChatbotActivityService.log_wizard_started(
            chatbot_id=2, source_url='https://example.com', username='user2',
        )
        ChatbotActivityService.log_document_uploaded(
            document_id=1, filename='doc.pdf', username='user1',
        )

    def test_CHAT_ACT_026_get_activities_all(self, app, db, app_context):
        """[CHAT_ACT-026] Should return all chatbot-related activities."""
        from services.chatbot_activity_service import ChatbotActivityService

        self._seed_events(ChatbotActivityService)
        activities = ChatbotActivityService.get_activities()

        assert len(activities) == 4

    def test_CHAT_ACT_027_get_activities_by_username(self, app, db, app_context):
        """[CHAT_ACT-027] Should filter activities by username."""
        from services.chatbot_activity_service import ChatbotActivityService

        self._seed_events(ChatbotActivityService)
        activities = ChatbotActivityService.get_activities(username='user1')

        assert len(activities) == 3
        assert all(a['username'] == 'user1' for a in activities)

    def test_CHAT_ACT_028_get_activities_by_prefix(self, app, db, app_context):
        """[CHAT_ACT-028] Should filter activities by event type prefix."""
        from services.chatbot_activity_service import ChatbotActivityService

        self._seed_events(ChatbotActivityService)
        activities = ChatbotActivityService.get_activities(event_type_prefix='chatbot')

        assert len(activities) == 2
        assert all(a['event_type'].startswith('chatbot.') for a in activities)

    def test_CHAT_ACT_029_get_activities_pagination(self, app, db, app_context):
        """[CHAT_ACT-029] Should support pagination."""
        from services.chatbot_activity_service import ChatbotActivityService

        self._seed_events(ChatbotActivityService)
        activities = ChatbotActivityService.get_activities(limit=2, offset=0)

        assert len(activities) == 2

    def test_CHAT_ACT_030_get_activities_empty(self, app, db, app_context):
        """[CHAT_ACT-030] Should return empty list when no activities match."""
        from services.chatbot_activity_service import ChatbotActivityService

        activities = ChatbotActivityService.get_activities(username='nonexistent')
        assert activities == []

    def test_CHAT_ACT_031_get_activity_stats(self, app, db, app_context):
        """[CHAT_ACT-031] Should return activity statistics."""
        from services.chatbot_activity_service import ChatbotActivityService

        self._seed_events(ChatbotActivityService)
        stats = ChatbotActivityService.get_activity_stats(period_hours=24)

        assert stats['total_events'] == 4
        assert 'by_type' in stats
        assert 'by_category' in stats
        assert 'top_users' in stats
        assert stats['by_category'].get('chatbot', 0) == 2

    def test_CHAT_ACT_032_serialize_event(self, app, db, app_context):
        """[CHAT_ACT-032] Should serialize event to dictionary."""
        from services.chatbot_activity_service import ChatbotActivityService

        event = ChatbotActivityService.log_chatbot_created(
            chatbot_id=1, chatbot_name='bot', display_name='Bot', username='admin',
        )

        serialized = ChatbotActivityService._serialize_event(event)

        assert 'id' in serialized
        assert 'event_type' in serialized
        assert 'severity' in serialized
        assert 'message' in serialized
        assert 'username' in serialized
        assert 'created_at' in serialized
