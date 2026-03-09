"""
Unit Tests: Anonymization Pipeline Service
===========================================

Tests for conversation import, NER processing, entity building,
and entity consistency across messages.

Test IDs:
- ANON_SVC_001: Import single conversation creates DB records
- ANON_SVC_002: Import multiple conversations from array
- ANON_SVC_003: Import with nested 'conversations' key
- ANON_SVC_004: Import fails with empty payload
- ANON_SVC_005: Import fails with no messages
- ANON_SVC_006: rerun_ner detects entities and stores them
- ANON_SVC_007: rerun_ner maintains entity consistency across messages
- ANON_SVC_008: rerun_ner refuses manually edited without force
- ANON_SVC_009: rerun_ner with force overwrites manual edits
- ANON_SVC_010: rerun_ner sets status=error on processing failure
- ANON_SVC_011: rerun_ner handles empty message text
- ANON_SVC_012: Entity label normalization (aliases)
- ANON_SVC_013: Entity building skips invalid spans
- ANON_SVC_014: Import with run_ner=False does not run NER
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conversation_payload(title="Test Conversation", messages=None):
    """Build a minimal conversation JSON payload."""
    if messages is None:
        messages = [
            {"message_number": 1, "content": "Hallo, mein Name ist Max Mustermann.", "author": "user"},
            {"message_number": 2, "content": "Guten Tag, Herr Mustermann.", "author": "counselor"},
        ]
    return {"title": title, "messages": messages}


def _make_pseudonymize_result(input_text="", output_text="Anonymisiert", entities=None, groups=None):
    """Build a mock AnonymizeService.pseudonymize() result."""
    return {
        "input_text": input_text,
        "output_text": output_text,
        "entities": entities or [],
        "groups": groups or [],
        "date_shift_days": -30,
    }


def _make_entity(label="PER", text="Max Mustermann", replacement="Anna Schmid",
                 start=0, end=15, output_start=0, output_end=11, group_id=None):
    """Build a single entity dict as returned by AnonymizeService."""
    return {
        "label": label,
        "text": text,
        "replacement": replacement,
        "start": start,
        "end": end,
        "output_start": output_start,
        "output_end": output_end,
        "group_id": group_id or f"{label}:{text}",
        "can_randomize": True,
    }


def _make_group(label="PER", original="Max Mustermann", replacement="Anna Schmid",
                mode="auto", db_hit=True, group_id=None):
    """Build a single group dict as returned by AnonymizeService."""
    return {
        "group_id": group_id or f"{label}:{original}",
        "label": label,
        "original": original,
        "replacement": replacement,
        "mode": mode,
        "db_hit": db_hit,
        "count": 1,
    }


# ---------------------------------------------------------------------------
# Import Tests
# ---------------------------------------------------------------------------

class TestImportConversations:

    def test_ANON_SVC_001_import_single_conversation(self, app, db, app_context):
        """[ANON_SVC-001] Import single conversation creates conversation + messages in DB."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation, AnonymizationMessage

        payload = _make_conversation_payload(title="Single Conv")

        result = AnonymizationPipelineService.import_conversations(
            payload=payload,
            source_file_path="test://single.json",
            user_id=1,
            run_ner=False,
        )
        db.session.commit()

        assert result["imported_count"] == 1
        assert result["failed_count"] == 0

        conv = AnonymizationConversation.query.first()
        assert conv is not None
        assert conv.title == "Single Conv"
        assert conv.status == "pending"
        assert conv.message_count == 2

        messages = AnonymizationMessage.query.filter_by(conversation_id=conv.id).all()
        assert len(messages) == 2
        assert messages[0].author == "user"
        assert messages[1].author == "counselor"

    def test_ANON_SVC_002_import_multiple_conversations(self, app, db, app_context):
        """[ANON_SVC-002] Import array of conversations creates multiple records."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation

        payload = [
            _make_conversation_payload(title="Conv 1"),
            _make_conversation_payload(title="Conv 2"),
            _make_conversation_payload(title="Conv 3"),
        ]

        result = AnonymizationPipelineService.import_conversations(
            payload=payload,
            source_file_path="test://multi.json",
            user_id=1,
        )
        db.session.commit()

        assert result["imported_count"] == 3
        conversations = AnonymizationConversation.query.all()
        assert len(conversations) == 3
        titles = {c.title for c in conversations}
        assert titles == {"Conv 1", "Conv 2", "Conv 3"}

    def test_ANON_SVC_003_import_nested_conversations_key(self, app, db, app_context):
        """[ANON_SVC-003] Import with wrapper object {'conversations': [...]} works."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation

        payload = {
            "conversations": [
                _make_conversation_payload(title="Nested 1"),
                _make_conversation_payload(title="Nested 2"),
            ]
        }

        result = AnonymizationPipelineService.import_conversations(
            payload=payload,
            source_file_path="test://nested.json",
            user_id=1,
        )
        db.session.commit()

        assert result["imported_count"] == 2

    def test_ANON_SVC_004_import_empty_payload_fails(self, app, db, app_context):
        """[ANON_SVC-004] Import with empty list raises ValidationError."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from decorators.error_handler import ValidationError

        with pytest.raises(ValidationError, match="No conversation objects found"):
            AnonymizationPipelineService.import_conversations(
                payload=[],
                source_file_path="test://empty.json",
                user_id=1,
            )

    def test_ANON_SVC_005_import_no_messages_fails(self, app, db, app_context):
        """[ANON_SVC-005] Import conversation without messages raises ValidationError."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from decorators.error_handler import ValidationError

        payload = {"title": "No Messages", "messages": []}

        with pytest.raises(ValidationError, match="Import failed"):
            AnonymizationPipelineService.import_conversations(
                payload=payload,
                source_file_path="test://empty-msg.json",
                user_id=1,
            )

    def test_ANON_SVC_014_import_without_run_ner(self, app, db, app_context):
        """[ANON_SVC-014] Import with run_ner=False leaves status=pending, no entities."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation, AnonymizationEntity

        payload = _make_conversation_payload()

        AnonymizationPipelineService.import_conversations(
            payload=payload,
            source_file_path="test://no-ner.json",
            user_id=1,
            run_ner=False,
        )
        db.session.commit()

        conv = AnonymizationConversation.query.first()
        assert conv.status == "pending"
        assert conv.entity_count == 0
        assert AnonymizationEntity.query.count() == 0


# ---------------------------------------------------------------------------
# NER Processing Tests
# ---------------------------------------------------------------------------

class TestRerunNer:

    @patch("services.anonymize.anonymization_pipeline_service.AnonymizeService.pseudonymize")
    def test_ANON_SVC_006_rerun_ner_detects_and_stores_entities(self, mock_pseudo, app, db, app_context):
        """[ANON_SVC-006] rerun_ner calls pseudonymize per message and stores entities."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation, AnonymizationEntity

        # Setup: import a conversation first
        payload = _make_conversation_payload()
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://ner.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        # Mock pseudonymize to return entities
        entity = _make_entity(label="PER", text="Max Mustermann", replacement="Anna Schmid",
                              start=22, end=37, output_start=22, output_end=33)
        group = _make_group(label="PER", original="Max Mustermann", replacement="Anna Schmid")

        mock_pseudo.return_value = _make_pseudonymize_result(
            output_text="Hallo, mein Name ist Anna Schmid.",
            entities=[entity],
            groups=[group],
        )

        # Run NER
        ner_result = AnonymizationPipelineService.rerun_ner(
            conversation=conv, user_id=1, force=True,
        )
        db.session.commit()

        assert ner_result["entity_count"] > 0
        assert len(ner_result["errors"]) == 0

        entities = AnonymizationEntity.query.all()
        assert len(entities) > 0
        assert entities[0].label == "PER"
        assert entities[0].replacement_text == "Anna Schmid"

    @patch("services.anonymize.anonymization_pipeline_service.AnonymizeService.pseudonymize")
    def test_ANON_SVC_007_rerun_ner_entity_consistency(self, mock_pseudo, app, db, app_context):
        """[ANON_SVC-007] rerun_ner passes group overrides to maintain consistency across messages."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

        payload = _make_conversation_payload(messages=[
            {"message_number": 1, "content": "Ich bin Max Mustermann aus Zürich.", "author": "user"},
            {"message_number": 2, "content": "Herr Max Mustermann, willkommen.", "author": "counselor"},
        ])
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://consistency.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        entity = _make_entity(label="PER", text="Max Mustermann", replacement="Anna Schmid")
        group = _make_group(label="PER", original="Max Mustermann", replacement="Anna Schmid")

        mock_pseudo.return_value = _make_pseudonymize_result(
            output_text="Anonymized text",
            entities=[entity],
            groups=[group],
        )

        AnonymizationPipelineService.rerun_ner(conversation=conv, user_id=1, force=True)
        db.session.commit()

        # Verify group_overrides were passed to second call with first call's mappings
        assert mock_pseudo.call_count == 2
        second_call_kwargs = mock_pseudo.call_args_list[1]
        group_overrides = second_call_kwargs[1].get("group_overrides", {}) if second_call_kwargs[1] else {}
        assert "PER:Max Mustermann" in group_overrides
        assert group_overrides["PER:Max Mustermann"]["replacement"] == "Anna Schmid"

    def test_ANON_SVC_008_rerun_ner_refuses_manual_edits(self, app, db, app_context):
        """[ANON_SVC-008] rerun_ner raises ValidationError if messages are manually edited."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationMessage
        from decorators.error_handler import ValidationError

        payload = _make_conversation_payload()
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://manual.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        # Mark first message as manually edited
        msg = AnonymizationMessage.query.filter_by(conversation_id=conv.id).first()
        msg.is_manually_edited = True
        db.session.commit()

        with pytest.raises(ValidationError, match="manually edited"):
            AnonymizationPipelineService.rerun_ner(conversation=conv, user_id=1, force=False)

    @patch("services.anonymize.anonymization_pipeline_service.AnonymizeService.pseudonymize")
    def test_ANON_SVC_009_rerun_ner_force_overwrites(self, mock_pseudo, app, db, app_context):
        """[ANON_SVC-009] rerun_ner with force=True clears manual edits and re-processes."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationMessage

        payload = _make_conversation_payload()
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://force.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        # Mark as manually edited
        msg = AnonymizationMessage.query.filter_by(conversation_id=conv.id).first()
        msg.is_manually_edited = True
        db.session.commit()

        mock_pseudo.return_value = _make_pseudonymize_result(output_text="Forced result")

        ner_result = AnonymizationPipelineService.rerun_ner(
            conversation=conv, user_id=1, force=True,
        )
        db.session.commit()

        assert len(ner_result["errors"]) == 0
        # Verify manual edit flag was cleared
        msg = AnonymizationMessage.query.filter_by(conversation_id=conv.id).first()
        assert msg.is_manually_edited is False

    @patch("services.anonymize.anonymization_pipeline_service.AnonymizeService.pseudonymize")
    def test_ANON_SVC_010_rerun_ner_error_status(self, mock_pseudo, app, db, app_context):
        """[ANON_SVC-010] rerun_ner sets status=error when processing fails."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService
        from db.models import AnonymizationConversation

        payload = _make_conversation_payload()
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://error.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        mock_pseudo.side_effect = RuntimeError("NER model not loaded")

        ner_result = AnonymizationPipelineService.rerun_ner(
            conversation=conv, user_id=1, force=True,
        )
        db.session.commit()

        assert len(ner_result["errors"]) > 0
        refreshed = AnonymizationConversation.query.get(conv.id)
        assert refreshed.status == "error"
        assert "NER model not loaded" in refreshed.error_message

    @patch("services.anonymize.anonymization_pipeline_service.AnonymizeService.pseudonymize")
    def test_ANON_SVC_011_rerun_ner_empty_messages(self, mock_pseudo, app, db, app_context):
        """[ANON_SVC-011] rerun_ner skips empty messages without calling pseudonymize."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

        payload = _make_conversation_payload(messages=[
            {"message_number": 1, "content": "", "author": "user"},
            {"message_number": 2, "content": "  ", "author": "counselor"},
            {"message_number": 3, "content": "Real content here.", "author": "user"},
        ])
        result = AnonymizationPipelineService.import_conversations(
            payload=payload, source_file_path="test://empty-msg.json", user_id=1, run_ner=False,
        )
        db.session.commit()
        conv = result["imported_conversations"][0]

        mock_pseudo.return_value = _make_pseudonymize_result(output_text="Processed content")

        AnonymizationPipelineService.rerun_ner(conversation=conv, user_id=1, force=True)
        db.session.commit()

        # Only the non-empty message should trigger pseudonymize
        assert mock_pseudo.call_count == 1


# ---------------------------------------------------------------------------
# Entity Building Tests
# ---------------------------------------------------------------------------

class TestEntityBuilding:

    def test_ANON_SVC_012_entity_label_normalization(self, app, app_context):
        """[ANON_SVC-012] Entity labels are normalized through alias mapping."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

        assert AnonymizationPipelineService._normalize_entity_label("PER") == "PER"
        assert AnonymizationPipelineService._normalize_entity_label("PERSON") == "PER"
        assert AnonymizationPipelineService._normalize_entity_label("NAME") == "PER"
        assert AnonymizationPipelineService._normalize_entity_label("LOCATION") == "LOC"
        assert AnonymizationPipelineService._normalize_entity_label("EMAIL") == "MAIL"
        assert AnonymizationPipelineService._normalize_entity_label("POSTAL_CODE") == "PLZ"
        assert AnonymizationPipelineService._normalize_entity_label("UNKNOWN_LABEL") == "MISC"
        assert AnonymizationPipelineService._normalize_entity_label(None) == "MISC"
        assert AnonymizationPipelineService._normalize_entity_label("") == "MISC"

    def test_ANON_SVC_013_entity_building_skips_invalid_spans(self, app, app_context):
        """[ANON_SVC-013] Entities with end_pos <= start_pos are skipped."""
        from services.anonymize.anonymization_pipeline_service import AnonymizationPipelineService

        # Zero-length span
        result = AnonymizationPipelineService._build_entity_record(
            message_id=1,
            entity={"label": "PER", "text": "Test", "start": 5, "end": 5,
                     "output_start": 5, "output_end": 5, "group_id": "PER:Test"},
            groups_by_id={},
        )
        assert result is None

        # Reversed span
        result = AnonymizationPipelineService._build_entity_record(
            message_id=1,
            entity={"label": "PER", "text": "Test", "start": 10, "end": 5,
                     "output_start": 10, "output_end": 5, "group_id": "PER:Test"},
            groups_by_id={},
        )
        assert result is None

        # Valid span
        result = AnonymizationPipelineService._build_entity_record(
            message_id=1,
            entity={"label": "PER", "text": "Max", "replacement": "Anna",
                     "start": 0, "end": 3, "output_start": 0, "output_end": 4,
                     "group_id": "PER:Max"},
            groups_by_id={"PER:Max": {"mode": "auto", "db_hit": True}},
        )
        assert result is not None
        assert result.label == "PER"
        assert result.original_text == "Max"
        assert result.replacement_text == "Anna"
        assert result.group_mode == "auto"
        assert result.db_hit is True
