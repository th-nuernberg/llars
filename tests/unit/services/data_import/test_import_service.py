"""
Tests for ImportService.

Covers session management, file analysis, transformation,
validation, task type mapping, chat_id generation, thread creation,
message creation, scenario creation, and sample retrieval.
"""

import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4


class TestSessionManagement:
    """Tests for ImportService session CRUD."""

    def test_IMP_001_create_session(self, app, app_context):
        """[IMP-001] Creates new session with unique ID."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session(filename='test.csv', file_size=1024)

        assert session.session_id is not None
        assert session.filename == 'test.csv'
        assert session.file_size == 1024
        assert session.status == 'pending'

    def test_IMP_002_get_session(self, app, app_context):
        """[IMP-002] Gets existing session by ID."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        created = service.create_session(filename='test.csv')
        fetched = service.get_session(created.session_id)
        assert fetched is not None
        assert fetched.session_id == created.session_id

    def test_IMP_003_get_nonexistent_session(self, app, app_context):
        """[IMP-003] Returns None for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        assert service.get_session('nonexistent-id') is None

    def test_IMP_004_delete_session(self, app, app_context):
        """[IMP-004] Deletes session and returns True."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        assert service.delete_session(session.session_id) is True
        assert service.get_session(session.session_id) is None

    def test_IMP_005_delete_nonexistent_session(self, app, app_context):
        """[IMP-005] Returns False for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        assert service.delete_session('nonexistent') is False


class TestImportSessionToDict:
    """Tests for ImportSession.to_dict."""

    def test_IMP_010_to_dict_basic(self, app, app_context):
        """[IMP-010] to_dict includes all required fields."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session(filename='test.json', file_size=512)

        d = session.to_dict()
        assert d['session_id'] == session.session_id
        assert d['filename'] == 'test.json'
        assert d['file_size'] == 512
        assert d['status'] == 'pending'
        assert d['item_count'] == 0
        assert d['imported_count'] == 0

    def test_IMP_011_to_dict_with_scenario(self, app, app_context):
        """[IMP-011] to_dict includes scenario info when present."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        session.options['scenario_id'] = 42
        session.options['scenario_name'] = 'Test Scenario'

        d = session.to_dict()
        assert d['scenario']['id'] == 42
        assert d['scenario']['name'] == 'Test Scenario'


class TestGetFunctionTypeId:
    """Tests for ImportService._get_function_type_id."""

    def test_IMP_020_ranking_type(self, app, app_context):
        """[IMP-020] RANKING maps to 1."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.RANKING) == 1

    def test_IMP_021_rating_type(self, app, app_context):
        """[IMP-021] RATING maps to 2."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.RATING) == 2

    def test_IMP_022_mail_rating_type(self, app, app_context):
        """[IMP-022] MAIL_RATING maps to 3."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.MAIL_RATING) == 3

    def test_IMP_023_comparison_type(self, app, app_context):
        """[IMP-023] COMPARISON maps to 4."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.COMPARISON) == 4

    def test_IMP_024_authenticity_type(self, app, app_context):
        """[IMP-024] AUTHENTICITY maps to 5."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.AUTHENTICITY) == 5

    def test_IMP_025_labeling_type(self, app, app_context):
        """[IMP-025] LABELING maps to 7."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.LABELING) == 7

    def test_IMP_026_text_classification_alias(self, app, app_context):
        """[IMP-026] TEXT_CLASSIFICATION legacy alias maps to 7."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        assert ImportService._get_function_type_id(TaskType.TEXT_CLASSIFICATION) == 7


class TestGenerateChatId:
    """Tests for ImportService._generate_chat_id."""

    def test_IMP_030_deterministic(self, app, app_context):
        """[IMP-030] Same input produces same ID."""
        from services.data_import.import_service import ImportService
        id1 = ImportService._generate_chat_id('test-item-1')
        id2 = ImportService._generate_chat_id('test-item-1')
        assert id1 == id2

    def test_IMP_031_different_inputs_different_ids(self, app, app_context):
        """[IMP-031] Different inputs produce different IDs."""
        from services.data_import.import_service import ImportService
        id1 = ImportService._generate_chat_id('item-a')
        id2 = ImportService._generate_chat_id('item-b')
        assert id1 != id2

    def test_IMP_032_within_int_range(self, app, app_context):
        """[IMP-032] Generated ID fits in signed INT."""
        from services.data_import.import_service import ImportService
        for i in range(100):
            chat_id = ImportService._generate_chat_id(f'test-{i}')
            assert 0 <= chat_id < 2147483647


class TestMapRoleToSender:
    """Tests for ImportService._map_role_to_sender."""

    def test_IMP_040_user_role(self, app, app_context):
        """[IMP-040] USER role maps to Klient."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import MessageRole
        service = ImportService()
        assert service._map_role_to_sender(MessageRole.USER) == 'Klient'

    def test_IMP_041_assistant_role(self, app, app_context):
        """[IMP-041] ASSISTANT role maps to Berater."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import MessageRole
        service = ImportService()
        assert service._map_role_to_sender(MessageRole.ASSISTANT) == 'Berater'

    def test_IMP_042_system_role(self, app, app_context):
        """[IMP-042] SYSTEM role maps to System."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import MessageRole
        service = ImportService()
        assert service._map_role_to_sender(MessageRole.SYSTEM) == 'System'


class TestCreateSessionFromData:
    """Tests for ImportService.create_session_from_data."""

    def test_IMP_050_from_list_of_dicts(self, app, app_context):
        """[IMP-050] Creates session from list of dicts."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import TaskType
        service = ImportService()

        data = [
            {'question': 'Q1', 'answer': 'A1'},
            {'question': 'Q2', 'answer': 'A2'},
        ]
        session = service.create_session_from_data(data, task_type=TaskType.RATING)

        assert session.status == 'analyzed'
        assert session.detected_format == 'generic'
        assert session.format_confidence == 1.0
        assert session.task_type == TaskType.RATING
        assert session.raw_data == data
        assert session.structure['item_count'] == 2
        assert 'question' in session.structure['fields']

    def test_IMP_051_from_empty_data(self, app, app_context):
        """[IMP-051] Handles empty data gracefully."""
        from services.data_import.import_service import ImportService
        service = ImportService()

        session = service.create_session_from_data([])
        assert session.status == 'analyzed'
        assert session.raw_data == []


class TestAnalyzeFile:
    """Tests for ImportService.analyze_file."""

    def test_IMP_060_session_not_found(self, app, app_context):
        """[IMP-060] Raises for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        with pytest.raises(ValueError, match='Session not found'):
            service.analyze_file('nonexistent', '{}', 'test.json')

    @patch.object(
        __import__('services.data_import.import_service', fromlist=['ImportService']).ImportService,
        '__init__', lambda self: None
    )
    def test_IMP_061_analyze_sets_status(self, app, app_context):
        """[IMP-061] Analysis sets correct status on success."""
        from services.data_import.import_service import ImportService, ImportSession
        from datetime import datetime

        service = ImportService.__new__(ImportService)
        service._sessions = {}

        # Create mock detector
        mock_detector = MagicMock()
        mock_detector.detect_from_file.return_value = {
            'detected': True,
            'format_id': 'json',
            'confidence': 0.9,
            'structure': {'fields': ['a', 'b']},
            'data': [{'a': 1}],
        }
        service.detector = mock_detector
        service.validator = MagicMock()
        service.universal_transformer = MagicMock()

        session = ImportSession(
            session_id='test-sess',
            created_at=datetime.now(),
        )
        service._sessions['test-sess'] = session

        result = service.analyze_file('test-sess', '{"a":1}', 'test.json')
        assert result.status == 'analyzed'
        assert result.detected_format == 'json'


class TestTransform:
    """Tests for ImportService.transform."""

    def test_IMP_070_session_not_found(self, app, app_context):
        """[IMP-070] Raises for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        with pytest.raises(ValueError, match='Session not found'):
            service.transform('nonexistent')

    def test_IMP_071_no_raw_data(self, app, app_context):
        """[IMP-071] Error when no raw data."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        result = service.transform(session.session_id)
        assert 'No data to transform' in result.errors


class TestValidate:
    """Tests for ImportService.validate."""

    def test_IMP_080_session_not_found(self, app, app_context):
        """[IMP-080] Raises for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        with pytest.raises(ValueError, match='Session not found'):
            service.validate('nonexistent')

    def test_IMP_081_no_items(self, app, app_context):
        """[IMP-081] Error when no items to validate."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        result = service.validate(session.session_id)
        assert 'No items to validate' in result.errors


class TestGetSample:
    """Tests for ImportService.get_sample."""

    def test_IMP_090_empty_session(self, app, app_context):
        """[IMP-090] Returns empty list for empty session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        assert service.get_sample(session.session_id) == []

    def test_IMP_091_nonexistent_session(self, app, app_context):
        """[IMP-091] Returns empty list for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        assert service.get_sample('nonexistent') == []

    def test_IMP_092_returns_limited_items(self, app, app_context):
        """[IMP-092] Returns up to count items."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import ImportItem, ItemType
        service = ImportService()
        session = service.create_session()

        # Add test items
        for i in range(10):
            session.transformed_items.append(
                ImportItem(id=f'item-{i}', item_type=ItemType.SINGLE_TEXT, content=f'Content {i}')
            )

        sample = service.get_sample(session.session_id, count=3)
        assert len(sample) == 3


class TestExecuteImport:
    """Tests for ImportService.execute_import."""

    def test_IMP_100_no_items_error(self, app, db, app_context):
        """[IMP-100] Error when no items to import."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        session = service.create_session()
        result = service.execute_import(session.session_id)
        assert result.status == 'error'
        assert 'No items to import' in result.errors

    def test_IMP_101_session_not_found(self, app, db, app_context):
        """[IMP-101] Raises for nonexistent session."""
        from services.data_import.import_service import ImportService
        service = ImportService()
        with pytest.raises(ValueError, match='Session not found'):
            service.execute_import('nonexistent')

    def test_IMP_102_import_single_text_items(self, app, db, app_context):
        """[IMP-102] Imports single text items successfully."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import ImportItem, ItemType, TaskType

        service = ImportService()
        session = service.create_session()
        session.transformed_items = [
            ImportItem(id='text-1', item_type=ItemType.SINGLE_TEXT, content='Content A'),
            ImportItem(id='text-2', item_type=ItemType.SINGLE_TEXT, content='Content B'),
        ]
        session.task_type = TaskType.RATING

        result = service.execute_import(
            session.session_id,
            create_scenario=True,
            created_by='testuser'
        )

        assert result.status == 'complete'
        assert result.imported_count == 2
        assert result.options.get('scenario_id') is not None

    def test_IMP_103_import_conversation_items(self, app, db, app_context):
        """[IMP-103] Imports conversation items with messages."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import (
            ImportItem, ItemType, TaskType, Message, MessageRole
        )

        service = ImportService()
        session = service.create_session()
        session.transformed_items = [
            ImportItem(
                id='conv-1',
                item_type=ItemType.CONVERSATION,
                conversation=[
                    Message(role=MessageRole.USER, content='Hello'),
                    Message(role=MessageRole.ASSISTANT, content='Hi there'),
                ]
            ),
        ]
        session.task_type = TaskType.MAIL_RATING

        result = service.execute_import(
            session.session_id,
            create_scenario=True,
            created_by='testuser'
        )

        assert result.status == 'complete'
        assert result.imported_count == 1

    def test_IMP_104_import_qa_pair_items(self, app, db, app_context):
        """[IMP-104] Imports QA pair items."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import ImportItem, ItemType, TaskType

        service = ImportService()
        session = service.create_session()
        session.transformed_items = [
            ImportItem(
                id='qa-1',
                item_type=ItemType.QA_PAIR,
                question='What is AI?',
                answer='Artificial Intelligence.'
            ),
        ]
        session.task_type = TaskType.RATING

        result = service.execute_import(session.session_id, created_by='testuser')
        assert result.status == 'complete'

    def test_IMP_105_import_text_pair_items(self, app, db, app_context):
        """[IMP-105] Imports text pair items for comparison."""
        from services.data_import.import_service import ImportService
        from services.data_import.adapters.base_adapter import ImportItem, ItemType, TaskType

        service = ImportService()
        session = service.create_session()
        session.transformed_items = [
            ImportItem(
                id='pair-1',
                item_type=ItemType.TEXT_PAIR,
                text_a='Version A text',
                text_b='Version B text',
                label_a='GPT-4',
                label_b='Human',
            ),
        ]
        session.task_type = TaskType.COMPARISON

        result = service.execute_import(session.session_id, created_by='testuser')
        assert result.status == 'complete'
