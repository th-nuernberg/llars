"""
Unit Tests: Thread Service
==========================

Tests for the email thread management service.

Test IDs:
- THREAD-001 to THREAD-015: Thread Lookup
- THREAD-020 to THREAD-035: Thread Creation/Update
- THREAD-040 to THREAD-055: Message Management
- THREAD-060 to THREAD-075: Feature Management
- THREAD-080 to THREAD-090: Utility Methods
- THREAD-100 to THREAD-110: Access Control

Status: Implemented
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, MagicMock


class TestThreadLookup:
    """
    Thread Lookup Tests

    Tests for thread retrieval methods.
    """

    def test_THREAD_001_get_thread_by_id_found(self, app, db, app_context):
        """
        [THREAD-001] Get Thread by ID - Gefunden

        Thread mit gültiger ID sollte gefunden werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        # Setup
        function_type = FeatureFunctionType(name='test_func_001')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2001,
            chat_id=1,
            institut_id=1,
            subject='Test Thread',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        # Test
        found = ThreadService.get_thread_by_id(2001)

        assert found is not None
        assert found.thread_id == 2001
        assert found.subject == 'Test Thread'

    def test_THREAD_002_get_thread_by_id_not_found(self, app, db, app_context):
        """
        [THREAD-002] Get Thread by ID - Nicht gefunden

        Nicht existierende ID sollte None zurückgeben.
        """
        from services.thread_service import ThreadService

        found = ThreadService.get_thread_by_id(99999)

        assert found is None

    def test_THREAD_003_get_thread_by_id_empty(self, app, db, app_context):
        """
        [THREAD-003] Get Thread by ID - Leer/None

        Leere ID sollte None zurückgeben.
        """
        from services.thread_service import ThreadService

        assert ThreadService.get_thread_by_id(0) is None
        assert ThreadService.get_thread_by_id(None) is None

    def test_THREAD_004_get_thread_by_id_with_function_type(self, app, db, app_context):
        """
        [THREAD-004] Get Thread by ID - Mit Function Type

        Thread mit korrektem Function Type sollte gefunden werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_004')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2004,
            chat_id=4,
            institut_id=4,
            subject='Function Type Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        # Should find with correct function_type_id
        found = ThreadService.get_thread_by_id(2004, function_type.function_type_id)
        assert found is not None

        # Should not find with wrong function_type_id
        not_found = ThreadService.get_thread_by_id(2004, 9999)
        assert not_found is None

    def test_THREAD_005_get_threads_by_function_type(self, app, db, app_context):
        """
        [THREAD-005] Get Threads by Function Type

        Alle Threads mit passendem Function Type sollten gefunden werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_005')
        db.session.add(function_type)
        db.session.commit()

        # Create multiple threads
        for i in range(3):
            thread = EmailThread(
                thread_id=2050 + i,
                chat_id=50 + i,
                institut_id=5,
                subject=f'Thread {i}',
                function_type_id=function_type.function_type_id
            )
            db.session.add(thread)
        db.session.commit()

        # Test
        threads = ThreadService.get_threads_by_function_type(function_type.function_type_id)

        assert len(threads) >= 3

    def test_THREAD_006_get_threads_by_function_type_empty(self, app, db, app_context):
        """
        [THREAD-006] Get Threads by Function Type - Leer

        Keine Threads sollte leere Liste zurückgeben.
        """
        from services.thread_service import ThreadService

        threads = ThreadService.get_threads_by_function_type(99999)

        assert threads == []


class TestThreadCreationUpdate:
    """
    Thread Creation/Update Tests

    Tests for creating and updating threads.
    """

    def test_THREAD_020_create_thread_new(self, app, db, app_context):
        """
        [THREAD-020] Create Thread - Neu

        Neuer Thread sollte erstellt werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_020')
        db.session.add(function_type)
        db.session.commit()

        success, thread, error = ThreadService.create_or_update_thread(
            chat_id='chat_020',
            institut_id='inst_020',
            function_type_id=function_type.function_type_id,
            subject='New Thread',
            sender='Test Sender'
        )

        assert success is True
        assert thread is not None
        assert thread.subject == 'New Thread'
        assert thread.sender == 'Test Sender'
        assert error is None

    def test_THREAD_021_create_thread_update_existing(self, app, db, app_context):
        """
        [THREAD-021] Create Thread - Update Existing

        Existierender Thread sollte aktualisiert werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_021')
        db.session.add(function_type)
        db.session.commit()

        # Create initial thread
        initial_thread = EmailThread(
            chat_id='chat_021',
            institut_id='inst_021',
            subject='Original Subject',
            sender='Original Sender',
            function_type_id=function_type.function_type_id
        )
        db.session.add(initial_thread)
        db.session.commit()
        initial_id = initial_thread.thread_id

        # Update thread
        success, thread, error = ThreadService.create_or_update_thread(
            chat_id='chat_021',
            institut_id='inst_021',
            function_type_id=function_type.function_type_id,
            subject='Updated Subject',
            sender='Updated Sender'
        )

        assert success is True
        assert thread.thread_id == initial_id  # Same thread
        assert thread.subject == 'Updated Subject'
        assert thread.sender == 'Updated Sender'

    def test_THREAD_022_create_thread_default_sender(self, app, db, app_context):
        """
        [THREAD-022] Create Thread - Default Sender

        Thread sollte mit Default Sender erstellt werden.
        """
        from services.thread_service import ThreadService
        from db.models import FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_022')
        db.session.add(function_type)
        db.session.commit()

        success, thread, error = ThreadService.create_or_update_thread(
            chat_id='chat_022',
            institut_id='inst_022',
            function_type_id=function_type.function_type_id,
            subject='Default Sender Test'
        )

        assert success is True
        assert thread.sender == 'Alias'


class TestMessageManagement:
    """
    Message Management Tests

    Tests for adding and managing messages.
    """

    def test_THREAD_040_add_message_to_thread(self, app, db, app_context):
        """
        [THREAD-040] Add Message to Thread

        Nachricht sollte zum Thread hinzugefügt werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType, Message

        function_type = FeatureFunctionType(name='test_func_040')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2040,
            chat_id=40,
            institut_id=40,
            subject='Message Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        timestamp = datetime(2024, 1, 15, 10, 30, 0)

        success, message, error = ThreadService.add_message_to_thread(
            thread_id=2040,
            sender='Test User',
            content='Hello, this is a test message',
            timestamp=timestamp
        )

        assert success is True
        assert message is not None
        assert message.content == 'Hello, this is a test message'
        assert message.sender == 'Test User'
        assert error is None

    def test_THREAD_041_add_message_duplicate(self, app, db, app_context):
        """
        [THREAD-041] Add Message - Duplicate

        Doppelte Nachricht sollte existierende zurückgeben.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType, Message

        function_type = FeatureFunctionType(name='test_func_041')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2041,
            chat_id=41,
            institut_id=41,
            subject='Duplicate Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        timestamp = datetime(2024, 1, 15, 11, 0, 0)
        content = 'Duplicate message content'

        # Add first message
        success1, message1, _ = ThreadService.add_message_to_thread(
            thread_id=2041,
            sender='User',
            content=content,
            timestamp=timestamp
        )

        # Add duplicate
        success2, message2, _ = ThreadService.add_message_to_thread(
            thread_id=2041,
            sender='User',
            content=content,
            timestamp=timestamp
        )

        assert success1 is True
        assert success2 is True
        assert message1.message_id == message2.message_id  # Same message

    def test_THREAD_042_add_message_generated_by(self, app, db, app_context):
        """
        [THREAD-042] Add Message - Generated By

        Generated By Feld sollte gesetzt werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_042')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2042,
            chat_id=42,
            institut_id=42,
            subject='Generated By Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        success, message, _ = ThreadService.add_message_to_thread(
            thread_id=2042,
            sender='Bot',
            content='AI generated message',
            timestamp=datetime.now(),
            generated_by='GPT-4'
        )

        assert success is True
        assert message.generated_by == 'GPT-4'

    def test_THREAD_043_parse_timestamp_standard_format(self, app, app_context):
        """
        [THREAD-043] Parse Timestamp - Standard Format

        Standard Format sollte korrekt geparsed werden.
        """
        from services.thread_service import ThreadService

        result = ThreadService.parse_timestamp('2024-01-15 10:30:00')

        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30

    def test_THREAD_044_parse_timestamp_iso_format(self, app, app_context):
        """
        [THREAD-044] Parse Timestamp - ISO Format

        ISO Format sollte korrekt geparsed werden.
        """
        from services.thread_service import ThreadService

        result = ThreadService.parse_timestamp('2024-01-15T10:30:00')

        assert result is not None
        assert result.year == 2024
        assert result.hour == 10

    def test_THREAD_045_parse_timestamp_invalid(self, app, app_context):
        """
        [THREAD-045] Parse Timestamp - Invalid

        Ungültiges Format sollte None zurückgeben.
        """
        from services.thread_service import ThreadService

        assert ThreadService.parse_timestamp('not a timestamp') is None
        assert ThreadService.parse_timestamp('') is None
        assert ThreadService.parse_timestamp(None) is None


class TestFeatureManagement:
    """
    Feature Management Tests

    Tests for adding and managing features.
    """

    def test_THREAD_060_add_feature_to_thread(self, app, db, app_context):
        """
        [THREAD-060] Add Feature to Thread

        Feature sollte zum Thread hinzugefügt werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_060')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2060,
            chat_id=60,
            institut_id=60,
            subject='Feature Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        success, feature, error = ThreadService.add_feature_to_thread(
            thread_id=2060,
            llm_name='GPT-4',
            feature_type_name='situation_summary',
            content='This is a summary of the situation.'
        )

        assert success is True
        assert feature is not None
        assert feature.content == 'This is a summary of the situation.'
        assert error is None

    def test_THREAD_061_add_feature_creates_llm(self, app, db, app_context):
        """
        [THREAD-061] Add Feature - Creates LLM

        LLM sollte erstellt werden wenn nicht vorhanden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType, LLM

        function_type = FeatureFunctionType(name='test_func_061')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2061,
            chat_id=61,
            institut_id=61,
            subject='LLM Create Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        # Ensure LLM doesn't exist
        unique_llm_name = f'NewLLM_{uuid4().hex[:8]}'
        assert LLM.query.filter_by(name=unique_llm_name).first() is None

        success, feature, _ = ThreadService.add_feature_to_thread(
            thread_id=2061,
            llm_name=unique_llm_name,
            feature_type_name='test_type',
            content='Test content'
        )

        assert success is True
        # LLM should now exist
        llm = LLM.query.filter_by(name=unique_llm_name).first()
        assert llm is not None

    def test_THREAD_062_add_feature_creates_feature_type(self, app, db, app_context):
        """
        [THREAD-062] Add Feature - Creates Feature Type

        Feature Type sollte erstellt werden wenn nicht vorhanden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType, FeatureType, LLM

        function_type = FeatureFunctionType(name='test_func_062')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2062,
            chat_id=62,
            institut_id=62,
            subject='Feature Type Create Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        llm = LLM(name='TestLLM062')
        db.session.add(llm)
        db.session.commit()

        # Ensure FeatureType doesn't exist
        unique_type_name = f'new_feature_type_{uuid4().hex[:8]}'
        assert FeatureType.query.filter_by(name=unique_type_name).first() is None

        success, feature, _ = ThreadService.add_feature_to_thread(
            thread_id=2062,
            llm_name='TestLLM062',
            feature_type_name=unique_type_name,
            content='Test content'
        )

        assert success is True
        # FeatureType should now exist
        ft = FeatureType.query.filter_by(name=unique_type_name).first()
        assert ft is not None

    def test_THREAD_063_add_feature_duplicate(self, app, db, app_context):
        """
        [THREAD-063] Add Feature - Duplicate

        Doppeltes Feature sollte existierendes zurückgeben.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType, LLM, FeatureType

        function_type = FeatureFunctionType(name='test_func_063')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2063,
            chat_id=63,
            institut_id=63,
            subject='Duplicate Feature Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        llm = LLM(name='DupLLM063')
        db.session.add(llm)

        feature_type = FeatureType(name='dup_type_063')
        db.session.add(feature_type)
        db.session.commit()

        # Add first feature
        success1, feature1, _ = ThreadService.add_feature_to_thread(
            thread_id=2063,
            llm_name='DupLLM063',
            feature_type_name='dup_type_063',
            content='Content 1'
        )

        # Add duplicate (same thread, llm, type)
        success2, feature2, _ = ThreadService.add_feature_to_thread(
            thread_id=2063,
            llm_name='DupLLM063',
            feature_type_name='dup_type_063',
            content='Content 2'
        )

        assert success1 is True
        assert success2 is True
        assert feature1.feature_id == feature2.feature_id  # Same feature

    def test_THREAD_064_add_feature_json_content(self, app, db, app_context):
        """
        [THREAD-064] Add Feature - JSON Content

        Dict/List Content sollte zu JSON konvertiert werden.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType
        import json

        function_type = FeatureFunctionType(name='test_func_064')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2064,
            chat_id=64,
            institut_id=64,
            subject='JSON Content Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)
        db.session.commit()

        content_dict = {'key': 'value', 'items': [1, 2, 3]}

        success, feature, _ = ThreadService.add_feature_to_thread(
            thread_id=2064,
            llm_name='JSONTestLLM',
            feature_type_name='json_type',
            content=content_dict
        )

        assert success is True
        # Content should be JSON string
        parsed = json.loads(feature.content)
        assert parsed['key'] == 'value'
        assert parsed['items'] == [1, 2, 3]


class TestThreadWithData:
    """
    Thread with Data Tests

    Tests for retrieving threads with messages and features.
    """

    def test_THREAD_070_get_thread_with_messages_and_features(self, app, db, app_context):
        """
        [THREAD-070] Get Thread with Messages and Features

        Thread mit allen Daten sollte zurückgegeben werden.
        """
        from services.thread_service import ThreadService
        from db.models import (
            EmailThread, FeatureFunctionType, Message,
            Feature, LLM, FeatureType
        )

        function_type = FeatureFunctionType(name='test_func_070')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2070,
            chat_id=70,
            institut_id=70,
            subject='Full Data Test',
            sender='Test Sender',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        # Add message
        message = Message(
            thread_id=2070,
            sender='User',
            content='Test message',
            timestamp=datetime.now()
        )
        db.session.add(message)

        # Add feature
        llm = LLM(name='TestLLM070')
        db.session.add(llm)
        feature_type = FeatureType(name='test_type_070')
        db.session.add(feature_type)
        db.session.flush()

        feature = Feature(
            thread_id=2070,
            type_id=feature_type.type_id,
            llm_id=llm.llm_id,
            content='Test feature'
        )
        db.session.add(feature)
        db.session.commit()

        # Test
        result = ThreadService.get_thread_with_messages_and_features(
            2070, function_type.function_type_id
        )

        assert result is not None
        assert result['thread_id'] == 2070
        assert result['subject'] == 'Full Data Test'
        assert len(result['messages']) == 1
        assert len(result['features']) == 1

    def test_THREAD_071_get_thread_with_data_not_found(self, app, db, app_context):
        """
        [THREAD-071] Get Thread with Data - Not Found

        Nicht existierender Thread sollte None zurückgeben.
        """
        from services.thread_service import ThreadService

        result = ThreadService.get_thread_with_messages_and_features(99999, 1)

        assert result is None


class TestUtilityMethods:
    """
    Utility Methods Tests

    Tests for utility and helper methods.
    """

    def test_THREAD_080_get_thread_count_by_function_type(self, app, db, app_context):
        """
        [THREAD-080] Get Thread Count by Function Type

        Sollte korrekte Anzahl zurückgeben.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread, FeatureFunctionType

        function_type = FeatureFunctionType(name='test_func_080')
        db.session.add(function_type)
        db.session.commit()

        # Create threads
        for i in range(5):
            thread = EmailThread(
                thread_id=2080 + i,
                chat_id=80 + i,
                institut_id=80,
                subject=f'Count Test {i}',
                function_type_id=function_type.function_type_id
            )
            db.session.add(thread)
        db.session.commit()

        count = ThreadService.get_thread_count_by_function_type(function_type.function_type_id)

        assert count >= 5

    def test_THREAD_081_get_feature_count_for_thread(self, app, db, app_context):
        """
        [THREAD-081] Get Feature Count for Thread

        Sollte korrekte Feature-Anzahl zurückgeben.
        """
        from services.thread_service import ThreadService
        from db.models import (
            EmailThread, FeatureFunctionType, Feature, LLM, FeatureType
        )

        function_type = FeatureFunctionType(name='test_func_081')
        db.session.add(function_type)
        db.session.commit()

        thread = EmailThread(
            thread_id=2081,
            chat_id=81,
            institut_id=81,
            subject='Feature Count Test',
            function_type_id=function_type.function_type_id
        )
        db.session.add(thread)

        llm = LLM(name='CountLLM081')
        db.session.add(llm)
        db.session.flush()

        # Create features
        for i in range(4):
            feature_type = FeatureType(name=f'count_type_081_{i}')
            db.session.add(feature_type)
            db.session.flush()

            feature = Feature(
                thread_id=2081,
                type_id=feature_type.type_id,
                llm_id=llm.llm_id,
                content=f'Feature {i}'
            )
            db.session.add(feature)
        db.session.commit()

        count = ThreadService.get_feature_count_for_thread(2081)

        assert count == 4

    def test_THREAD_082_map_function_type_input_numbers(self, app, app_context):
        """
        [THREAD-082] Map Function Type Input - Numbers

        Numerische Eingaben sollten korrekt gemappt werden.
        """
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('1') == 1
        assert ThreadService.map_function_type_input('2') == 2
        assert ThreadService.map_function_type_input('3') == 3

    def test_THREAD_083_map_function_type_input_names(self, app, app_context):
        """
        [THREAD-083] Map Function Type Input - Names

        Benannte Eingaben sollten korrekt gemappt werden.
        """
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('ranking') == 1
        assert ThreadService.map_function_type_input('rating') == 2
        assert ThreadService.map_function_type_input('mail_rating') == 3

    def test_THREAD_084_map_function_type_input_aliases(self, app, app_context):
        """
        [THREAD-084] Map Function Type Input - Aliases

        Aliase sollten korrekt gemappt werden.
        """
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('rank') == 1
        assert ThreadService.map_function_type_input('rate') == 2
        assert ThreadService.map_function_type_input('rankings') == 1
        assert ThreadService.map_function_type_input('ratings') == 2
        assert ThreadService.map_function_type_input('mail_ratings') == 3

    def test_THREAD_085_map_function_type_input_case_insensitive(self, app, app_context):
        """
        [THREAD-085] Map Function Type Input - Case Insensitive

        Eingaben sollten case-insensitive sein.
        """
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('RANKING') == 1
        assert ThreadService.map_function_type_input('Rating') == 2
        assert ThreadService.map_function_type_input('MAIL_RATING') == 3

    def test_THREAD_086_map_function_type_input_invalid(self, app, app_context):
        """
        [THREAD-086] Map Function Type Input - Invalid

        Ungültige Eingaben sollten None zurückgeben.
        """
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('invalid') is None
        assert ThreadService.map_function_type_input('4') is None
        assert ThreadService.map_function_type_input('0') is None

    def test_THREAD_087_get_consulting_category_types(self, app, db, app_context):
        """
        [THREAD-087] Get Consulting Category Types

        Sollte alle Kategorietypen zurückgeben.
        """
        from services.thread_service import ThreadService
        from db.models import ConsultingCategoryType

        # Create category types
        for i in range(3):
            cat = ConsultingCategoryType(
                name=f'Category {i}',
                description=f'Description {i}'
            )
            db.session.add(cat)
        db.session.commit()

        result = ThreadService.get_consulting_category_types()

        assert isinstance(result, list)
        assert len(result) >= 3
        assert 'name' in result[0]
        assert 'description' in result[0]


class TestAccessControl:
    """
    Access Control Tests

    Tests for thread access control methods.
    """

    def test_THREAD_100_get_threads_for_user_mocked(self, app, db, app_context):
        """
        [THREAD-100] Get Threads for User - Mocked

        Sollte get_user_threads aufrufen.
        """
        from services.thread_service import ThreadService
        from db.models import EmailThread

        mock_threads = [MagicMock(spec=EmailThread), MagicMock(spec=EmailThread)]

        with patch('routes.HelperFunctions.get_user_threads', return_value=mock_threads):
            result = ThreadService.get_threads_for_user(user_id=1, function_type_id=1)

            assert result == mock_threads

    def test_THREAD_101_can_user_access_thread_true(self, app, db, app_context):
        """
        [THREAD-101] Can User Access Thread - True

        Sollte True zurückgeben wenn Zugriff erlaubt.
        """
        from services.thread_service import ThreadService

        with patch('routes.HelperFunctions.can_access_thread', return_value=True):
            result = ThreadService.can_user_access_thread(
                user_id=1, thread_id=100, function_type_id=1
            )

            assert result is True

    def test_THREAD_102_can_user_access_thread_false(self, app, db, app_context):
        """
        [THREAD-102] Can User Access Thread - False

        Sollte False zurückgeben wenn Zugriff nicht erlaubt.
        """
        from services.thread_service import ThreadService

        with patch('routes.HelperFunctions.can_access_thread', return_value=False):
            result = ThreadService.can_user_access_thread(
                user_id=1, thread_id=100, function_type_id=1
            )

            assert result is False
