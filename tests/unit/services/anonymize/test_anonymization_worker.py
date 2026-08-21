"""
Unit Tests: Anonymization Worker
=================================

Tests for the background NER worker that processes conversations
and emits Socket.IO events for real-time progress tracking.

Test IDs:
- ANON_WRK_001: Worker processes single conversation successfully
- ANON_WRK_002: Worker processes multiple conversations sequentially
- ANON_WRK_003: Worker emits batch-level socket events
- ANON_WRK_004: Worker emits conversation-level socket events
- ANON_WRK_005: Worker handles conversation not found
- ANON_WRK_006: Worker handles NER failure gracefully per conversation
- ANON_WRK_007: Worker force mode clears manual edits
- ANON_WRK_008: Worker runs without socketio (silent mode)
- ANON_WRK_009: Worker sets correct status after success
- ANON_WRK_010: Worker marks failed conversation as error
- ANON_WRK_011: Worker entity building normalizes labels
"""

import pytest
from unittest.mock import patch, MagicMock, call


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _import_conversation(db, title="Test Conv", messages=None):
    """Create a conversation in the DB for testing."""
    from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

    if messages is None:
        messages = [
            {"message_number": 1, "content": "Mein Name ist Max Mustermann.", "author": "user"},
            {"message_number": 2, "content": "Guten Tag, Herr Mustermann.", "author": "counselor"},
        ]

    payload = {"title": title, "messages": messages}
    result = AnonymizationPipelineService.import_conversations(
        payload=payload,
        source_file_path=f"test://{title}.json",
        user_id=1,
        run_ner=False,
    )
    db.session.commit()
    return result["imported_conversations"][0]


def _mock_pseudonymize_result(output_text="Anonymized", entities=None, groups=None):
    """Build a mock pseudonymize return value."""
    return {
        "input_text": "original",
        "output_text": output_text,
        "entities": entities or [
            {
                "label": "PER", "text": "Max Mustermann", "replacement": "Anna Schmid",
                "start": 16, "end": 31, "output_start": 16, "output_end": 27,
                "group_id": "PER:Max Mustermann",
            }
        ],
        "groups": groups or [
            {
                "group_id": "PER:Max Mustermann", "label": "PER",
                "original": "Max Mustermann", "replacement": "Anna Schmid",
                "mode": "auto", "db_hit": True,
            }
        ],
        "date_shift_days": -30,
    }


# ---------------------------------------------------------------------------
# Worker Processing Tests
# ---------------------------------------------------------------------------

class TestAnonymizationWorkerProcessing:

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_001_processes_single_conversation(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-001] Worker processes a single conversation, stores entities, sets status."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationConversation, AnonymizationEntity

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        worker = AnonymizationWorker(
            conversation_ids=[conv.id],
            user_id=1,
            socketio=None,
            force=True,
        )
        worker.run()

        refreshed = AnonymizationConversation.query.get(conv.id)
        assert refreshed.status == "pending"  # pending = NER done, awaiting review
        assert refreshed.entity_count > 0

        entities = AnonymizationEntity.query.all()
        assert len(entities) > 0
        assert entities[0].label == "PER"

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_002_processes_multiple_conversations(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-002] Worker processes multiple conversations sequentially."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationConversation

        conv1 = _import_conversation(db, title="Conv A")
        conv2 = _import_conversation(db, title="Conv B")
        conv3 = _import_conversation(db, title="Conv C")

        mock_pseudo.return_value = _mock_pseudonymize_result()

        worker = AnonymizationWorker(
            conversation_ids=[conv1.id, conv2.id, conv3.id],
            user_id=1,
            socketio=None,
            force=True,
        )
        worker.run()

        for cid in [conv1.id, conv2.id, conv3.id]:
            c = AnonymizationConversation.query.get(cid)
            assert c.status == "pending"
            assert c.entity_count > 0

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_009_sets_correct_status_after_success(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-009] After successful NER, status is 'pending' (awaiting review)."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationConversation

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        worker = AnonymizationWorker(conversation_ids=[conv.id], user_id=1, force=True)
        worker.run()

        refreshed = AnonymizationConversation.query.get(conv.id)
        assert refreshed.status == "pending"
        assert refreshed.error_message is None


# ---------------------------------------------------------------------------
# Socket.IO Event Emission Tests
# ---------------------------------------------------------------------------

class TestAnonymizationWorkerSocketEvents:

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_003_emits_batch_events(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-003] Worker emits batch:started, batch:progress, batch:completed."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        emitted_events = [c[0][0] for c in mock_socketio.emit.call_args_list]

        assert "anonymization:batch:started" in emitted_events
        assert "anonymization:batch:progress" in emitted_events
        assert "anonymization:batch:completed" in emitted_events

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_004_emits_conversation_events(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-004] Worker emits conversation:ner_started, ner_progress, ner_completed."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        emitted_events = [c[0][0] for c in mock_socketio.emit.call_args_list]

        assert "anonymization:conversation:ner_started" in emitted_events
        assert "anonymization:conversation:ner_progress" in emitted_events
        assert "anonymization:conversation:ner_completed" in emitted_events

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_004b_conversation_events_contain_correct_data(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-004b] Conversation events contain conversation_id, progress percent, entity counts."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        # Find ner_completed event
        completed_calls = [
            c for c in mock_socketio.emit.call_args_list
            if c[0][0] == "anonymization:conversation:ner_completed"
        ]
        assert len(completed_calls) >= 1

        data = completed_calls[0][0][1]
        assert data["conversation_id"] == conv.id
        assert data["entity_count"] > 0
        assert data["message_count"] == 2
        assert data["status"] == "pending"

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_004c_progress_events_contain_percent(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-004c] Progress events contain percent, message_number, total_messages."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv = _import_conversation(db)
        mock_pseudo.return_value = _mock_pseudonymize_result()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        progress_calls = [
            c for c in mock_socketio.emit.call_args_list
            if c[0][0] == "anonymization:conversation:ner_progress"
        ]
        assert len(progress_calls) >= 1

        # Last progress event should be 100%
        last_progress = progress_calls[-1][0][1]
        assert last_progress["percent"] == 100
        assert last_progress["conversation_id"] == conv.id
        assert last_progress["total_messages"] == 2

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_003b_batch_completed_counts(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-003b] Batch completed event reports correct completed/failed counts."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv1 = _import_conversation(db, title="OK Conv")
        conv2 = _import_conversation(db, title="OK Conv 2")
        mock_pseudo.return_value = _mock_pseudonymize_result()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv1.id, conv2.id],
            user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        completed_calls = [
            c for c in mock_socketio.emit.call_args_list
            if c[0][0] == "anonymization:batch:completed"
        ]
        assert len(completed_calls) == 1
        data = completed_calls[0][0][1]
        assert data["completed"] == 2
        assert data["failed"] == 0
        assert data["total"] == 2


# ---------------------------------------------------------------------------
# Error Handling Tests
# ---------------------------------------------------------------------------

class TestAnonymizationWorkerErrors:

    def test_ANON_WRK_005_handles_conversation_not_found(self, app, db, app_context):
        """[ANON_WRK-005] Worker handles missing conversation gracefully."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[99999],  # non-existent
            user_id=1, socketio=mock_socketio, force=True,
        )
        # Should not raise
        worker.run()

        emitted_events = [c[0][0] for c in mock_socketio.emit.call_args_list]
        assert "anonymization:conversation:ner_failed" in emitted_events
        assert "anonymization:batch:completed" in emitted_events

        completed_data = [
            c[0][1] for c in mock_socketio.emit.call_args_list
            if c[0][0] == "anonymization:batch:completed"
        ][0]
        assert completed_data["failed"] == 1
        assert completed_data["completed"] == 0

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_006_handles_ner_failure_per_conversation(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-006] Worker continues processing after one conversation fails."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationConversation

        conv1 = _import_conversation(db, title="Will Fail")
        conv2 = _import_conversation(db, title="Will Succeed")

        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            # Fail on first conversation's first message
            if call_count[0] <= 2:  # conv1 has 2 messages
                raise RuntimeError("Model crashed")
            return _mock_pseudonymize_result()

        mock_pseudo.side_effect = side_effect

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv1.id, conv2.id],
            user_id=1, socketio=mock_socketio, force=True,
        )
        worker.run()

        # Conv1 should be error, conv2 should be pending (success)
        c1 = AnonymizationConversation.query.get(conv1.id)
        c2 = AnonymizationConversation.query.get(conv2.id)
        assert c1.status == "error"
        assert c2.status == "pending"

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_010_marks_failed_conversation_error(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-010] Worker sets conversation status to error with message on failure."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationConversation

        conv = _import_conversation(db)
        mock_pseudo.side_effect = RuntimeError("Flair model not loaded")

        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, force=True,
        )
        worker.run()

        refreshed = AnonymizationConversation.query.get(conv.id)
        assert refreshed.status == "error"
        assert "Flair model not loaded" in refreshed.error_message

    def test_ANON_WRK_008_runs_without_socketio(self, app, db, app_context):
        """[ANON_WRK-008] Worker runs silently when socketio is None."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        conv = _import_conversation(db)

        with patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize") as mock_pseudo:
            mock_pseudo.return_value = _mock_pseudonymize_result()

            worker = AnonymizationWorker(
                conversation_ids=[conv.id], user_id=1, socketio=None, force=True,
            )
            # Should not raise even without socketio
            worker.run()

        from db.models import AnonymizationConversation
        refreshed = AnonymizationConversation.query.get(conv.id)
        assert refreshed.status == "pending"


# ---------------------------------------------------------------------------
# Force Mode Tests
# ---------------------------------------------------------------------------

class TestAnonymizationWorkerForceMode:

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_007_force_clears_manual_edits(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-007] Worker with force=True resets manually edited messages."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationMessage

        conv = _import_conversation(db)

        # Mark message as manually edited
        msg = AnonymizationMessage.query.filter_by(conversation_id=conv.id).first()
        msg.is_manually_edited = True
        msg.anonymized_content = "Manually edited content"
        db.session.commit()

        mock_pseudo.return_value = _mock_pseudonymize_result()

        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, force=True,
        )
        worker.run()

        refreshed_msg = AnonymizationMessage.query.get(msg.id)
        assert refreshed_msg.is_manually_edited is False
        assert refreshed_msg.anonymized_content != "Manually edited content"

    @patch("services.anonymize.anonymize_service.AnonymizeService.pseudonymize")
    def test_ANON_WRK_007b_no_force_rejects_manual_edits(self, mock_pseudo, app, db, app_context):
        """[ANON_WRK-007b] Worker without force emits error for manually edited conversations."""
        from services.anonymize.anonymization_worker import AnonymizationWorker
        from db.models import AnonymizationMessage

        conv = _import_conversation(db)

        msg = AnonymizationMessage.query.filter_by(conversation_id=conv.id).first()
        msg.is_manually_edited = True
        db.session.commit()

        mock_socketio = MagicMock()
        worker = AnonymizationWorker(
            conversation_ids=[conv.id], user_id=1, socketio=mock_socketio, force=False,
        )
        worker.run()

        emitted_events = [c[0][0] for c in mock_socketio.emit.call_args_list]
        assert "anonymization:conversation:ner_failed" in emitted_events


# ---------------------------------------------------------------------------
# Entity Building Tests (Worker-level)
# ---------------------------------------------------------------------------

class TestAnonymizationWorkerEntityBuilding:

    def test_ANON_WRK_011_entity_label_normalization(self, app, app_context):
        """[ANON_WRK-011] Worker entity building normalizes labels via alias map."""
        from services.anonymize.anonymization_worker import AnonymizationWorker

        # Test alias mapping
        entity_email = {
            "label": "EMAIL", "text": "test@test.de", "replacement": "xxx",
            "start": 0, "end": 13, "output_start": 0, "output_end": 3,
            "group_id": "EMAIL:test@test.de",
        }
        result = AnonymizationWorker._build_entity_record(
            message_id=1, entity=entity_email, groups_by_id={},
        )
        assert result is not None
        assert result.label == "MAIL"

        # Test unknown label falls back to MISC
        entity_unknown = {
            "label": "FOOBAR", "text": "something", "replacement": "xxx",
            "start": 0, "end": 9, "output_start": 0, "output_end": 3,
            "group_id": "FOOBAR:something",
        }
        result = AnonymizationWorker._build_entity_record(
            message_id=1, entity=entity_unknown, groups_by_id={},
        )
        assert result is not None
        assert result.label == "MISC"
