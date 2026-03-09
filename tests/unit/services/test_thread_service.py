"""
Unit Tests: Thread Service (Extended)
======================================

Additional comprehensive tests for thread_service.py covering areas
not fully tested in the existing tests/unit/services/thread/test_thread_service.py.

Test IDs: THRD-001 to THRD-030

Key areas:
- Thread with multiple messages ordered by timestamp
- Feature count accuracy
- Thread with messages and features (edge cases)
- Thread creation error handling
- Message with empty generated_by defaults to "Human"
- JSON content with list type
- Consulting category types empty
- get_thread_count with zero results
"""

import pytest
import json
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_function_type(db, name):
    from db.models import FeatureFunctionType
    ft = FeatureFunctionType(name=name)
    db.session.add(ft)
    db.session.commit()
    return ft


def _make_thread(db, function_type_id, *, chat_id=1, institut_id=1, subject='Test'):
    from db.models import EmailThread
    thread = EmailThread(
        chat_id=chat_id,
        institut_id=institut_id,
        subject=subject,
        function_type_id=function_type_id
    )
    db.session.add(thread)
    db.session.commit()
    db.session.refresh(thread)
    return thread


# ===========================================================================
# Thread creation edge cases
# ===========================================================================

class TestThreadCreationExtended:
    """Extended thread creation tests."""

    def test_THRD_001_create_thread_different_function_types(self, app, db, app_context):
        """[THRD-001] Same chat_id/institut_id with different function types create separate threads."""
        from services.thread_service import ThreadService

        ft1 = _make_function_type(db, 'thrd_ft1_001')
        ft2 = _make_function_type(db, 'thrd_ft2_001')

        s1, t1, _ = ThreadService.create_or_update_thread(
            'chat001', 'inst001', ft1.function_type_id, 'Subject A'
        )
        s2, t2, _ = ThreadService.create_or_update_thread(
            'chat001', 'inst001', ft2.function_type_id, 'Subject B'
        )

        assert s1 is True and s2 is True
        assert t1.thread_id != t2.thread_id
        assert t1.subject == 'Subject A'
        assert t2.subject == 'Subject B'

    def test_THRD_002_create_thread_updates_subject_and_sender(self, app, db, app_context):
        """[THRD-002] Updating an existing thread changes both subject and sender."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_002')

        ThreadService.create_or_update_thread(
            'chat002', 'inst002', ft.function_type_id, 'Original', 'SenderA'
        )
        _, thread, _ = ThreadService.create_or_update_thread(
            'chat002', 'inst002', ft.function_type_id, 'Updated', 'SenderB'
        )

        assert thread.subject == 'Updated'
        assert thread.sender == 'SenderB'


# ===========================================================================
# Message management extended
# ===========================================================================

class TestMessageManagementExtended:
    """Extended message management tests."""

    def test_THRD_005_add_message_default_generated_by(self, app, db, app_context):
        """[THRD-005] Empty generated_by defaults to 'Human'."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_005')
        thread = _make_thread(db, ft.function_type_id, chat_id=5)

        success, msg, _ = ThreadService.add_message_to_thread(
            thread_id=thread.thread_id,
            sender='User',
            content='Test content',
            timestamp=datetime.now(),
            generated_by=''
        )

        assert success is True
        assert msg.generated_by == 'Human'

    def test_THRD_006_add_multiple_messages(self, app, db, app_context):
        """[THRD-006] Multiple messages can be added to the same thread."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_006')
        thread = _make_thread(db, ft.function_type_id, chat_id=6)

        base_time = datetime(2024, 6, 1, 10, 0, 0)
        for i in range(5):
            success, msg, _ = ThreadService.add_message_to_thread(
                thread_id=thread.thread_id,
                sender=f'User{i}',
                content=f'Message {i}',
                timestamp=base_time + timedelta(minutes=i)
            )
            assert success is True

        result = ThreadService.get_thread_with_messages_and_features(
            thread.thread_id, ft.function_type_id
        )
        assert len(result['messages']) == 5


# ===========================================================================
# Feature management extended
# ===========================================================================

class TestFeatureManagementExtended:
    """Extended feature management tests."""

    def test_THRD_010_add_feature_list_content(self, app, db, app_context):
        """[THRD-010] List content is JSON-encoded."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_010')
        thread = _make_thread(db, ft.function_type_id, chat_id=10)

        content_list = ['item1', 'item2', 'item3']
        success, feature, _ = ThreadService.add_feature_to_thread(
            thread.thread_id, 'ListLLM', 'list_type_010', content_list
        )

        assert success is True
        parsed = json.loads(feature.content)
        assert parsed == content_list

    def test_THRD_011_add_feature_string_content_unchanged(self, app, db, app_context):
        """[THRD-011] String content is stored as-is (not JSON-encoded)."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_011')
        thread = _make_thread(db, ft.function_type_id, chat_id=11)

        success, feature, _ = ThreadService.add_feature_to_thread(
            thread.thread_id, 'StringLLM', 'str_type_011', 'Plain text content'
        )

        assert success is True
        assert feature.content == 'Plain text content'

    def test_THRD_012_add_features_multiple_types(self, app, db, app_context):
        """[THRD-012] Multiple feature types on one thread."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_012')
        thread = _make_thread(db, ft.function_type_id, chat_id=12)

        types = ['summary_012', 'recommendation_012', 'analysis_012']
        for t in types:
            success, _, _ = ThreadService.add_feature_to_thread(
                thread.thread_id, 'MultiLLM', t, f'Content for {t}'
            )
            assert success is True

        count = ThreadService.get_feature_count_for_thread(thread.thread_id)
        assert count == 3


# ===========================================================================
# Thread with data extended
# ===========================================================================

class TestThreadWithDataExtended:
    """Extended tests for get_thread_with_messages_and_features."""

    def test_THRD_015_thread_with_no_messages_or_features(self, app, db, app_context):
        """[THRD-015] Thread with no messages or features returns empty lists."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_015')
        thread = _make_thread(db, ft.function_type_id, chat_id=15, subject='Empty')

        result = ThreadService.get_thread_with_messages_and_features(
            thread.thread_id, ft.function_type_id
        )

        assert result is not None
        assert result['messages'] == []
        assert result['features'] == []
        assert result['subject'] == 'Empty'

    def test_THRD_016_thread_with_data_wrong_function_type(self, app, db, app_context):
        """[THRD-016] Wrong function_type_id returns None."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_016')
        thread = _make_thread(db, ft.function_type_id, chat_id=16)

        result = ThreadService.get_thread_with_messages_and_features(
            thread.thread_id, 99999
        )
        assert result is None


# ===========================================================================
# Count methods
# ===========================================================================

class TestCountMethods:
    """Tests for count methods."""

    def test_THRD_020_thread_count_zero(self, app, db, app_context):
        """[THRD-020] Thread count returns 0 for unused function type."""
        from services.thread_service import ThreadService

        count = ThreadService.get_thread_count_by_function_type(99999)
        assert count == 0

    def test_THRD_021_feature_count_zero(self, app, db, app_context):
        """[THRD-021] Feature count returns 0 for thread with no features."""
        from services.thread_service import ThreadService

        ft = _make_function_type(db, 'thrd_ft_021')
        thread = _make_thread(db, ft.function_type_id, chat_id=21)

        count = ThreadService.get_feature_count_for_thread(thread.thread_id)
        assert count == 0

    def test_THRD_022_feature_count_nonexistent_thread(self, app, db, app_context):
        """[THRD-022] Feature count returns 0 for nonexistent thread."""
        from services.thread_service import ThreadService

        count = ThreadService.get_feature_count_for_thread(99999)
        assert count == 0


# ===========================================================================
# Parse timestamp extended
# ===========================================================================

class TestParseTimestampExtended:
    """Extended timestamp parsing tests."""

    def test_THRD_025_parse_timestamp_with_timezone(self, app, app_context):
        """[THRD-025] Timestamp with timezone info is parsed."""
        from services.thread_service import ThreadService

        result = ThreadService.parse_timestamp('2024-06-15T10:30:00+02:00')
        assert result is not None
        assert result.year == 2024
        assert result.month == 6

    def test_THRD_026_parse_timestamp_date_only(self, app, app_context):
        """[THRD-026] Date-only string is parsed."""
        from services.thread_service import ThreadService

        result = ThreadService.parse_timestamp('2024-06-15')
        assert result is not None
        assert result.year == 2024
        assert result.day == 15


# ===========================================================================
# Map function type extended
# ===========================================================================

class TestMapFunctionTypeExtended:
    """Extended function type mapping tests."""

    def test_THRD_028_map_mixed_case(self, app, app_context):
        """[THRD-028] Mixed case inputs are handled."""
        from services.thread_service import ThreadService

        assert ThreadService.map_function_type_input('RaNkInG') == 1
        assert ThreadService.map_function_type_input('Mail_Rating') == 3

    def test_THRD_029_map_all_valid_inputs(self, app, app_context):
        """[THRD-029] All documented valid inputs map correctly."""
        from services.thread_service import ThreadService

        valid_mappings = {
            '1': 1, '2': 2, '3': 3,
            'ranking': 1, 'rating': 2, 'mail_rating': 3,
            'rank': 1, 'rate': 2,
            'rankings': 1, 'ratings': 2, 'mail_ratings': 3
        }

        for input_val, expected in valid_mappings.items():
            result = ThreadService.map_function_type_input(input_val)
            assert result == expected, f"Failed for input '{input_val}'"


# ===========================================================================
# Consulting categories
# ===========================================================================

class TestConsultingCategoriesExtended:
    """Extended consulting category tests."""

    def test_THRD_030_consulting_categories_empty(self, app, db, app_context):
        """[THRD-030] Empty DB returns empty list for consulting categories."""
        from services.thread_service import ThreadService
        from db.models import ConsultingCategoryType

        # Clear any existing categories
        ConsultingCategoryType.query.delete()
        db.session.commit()

        result = ThreadService.get_consulting_category_types()
        assert result == []
