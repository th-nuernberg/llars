"""
Tests for SchemaAdapter service.

Comprehensive unit tests covering:
- Schema adaptation for different evaluation types
- Access checking (CRITICAL: multi-scenario item access bug fix area)
- Legacy format conversion
- Ranking/rating/mail_rating/authenticity thread data

Test IDs: [SCHEMA_SVC_001] through [SCHEMA_SVC_032]
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# =============================================================================
# Helpers
# =============================================================================

def _create_function_type(db_session, name, ftype_id):
    from db.models.scenario import FeatureFunctionType

    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db_session.session.add(ftype)
    db_session.session.flush()
    return ftype


def _create_user(db_session, username='schema_user'):
    from db.models.user import User
    import hashlib

    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db_session.session.add(user)
    db_session.session.flush()
    return user


def _create_scenario(db_session, name, ftype_id, created_by='creator', config_json=None):
    from db.models.scenario import RatingScenarios

    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        config_json=config_json or {},
        created_by=created_by
    )
    db_session.session.add(scenario)
    db_session.session.flush()
    return scenario


def _create_item(db_session, subject='Item', chat_id=1, institut_id=None):
    from db.models.scenario import EvaluationItem

    item = EvaluationItem(subject=subject, chat_id=chat_id)
    if institut_id:
        item.institut_id = institut_id
    db_session.session.add(item)
    db_session.session.flush()
    return item


def _link_item_to_scenario(db_session, scenario_id, item_id):
    from db.models.scenario import ScenarioItems

    si = ScenarioItems(scenario_id=scenario_id, item_id=item_id)
    db_session.session.add(si)
    db_session.session.flush()
    return si


def _add_user_to_scenario(db_session, scenario_id, user_id, role_name='ASSESSOR'):
    from db.models.scenario import ScenarioUsers, ScenarioRoles

    role = ScenarioRoles.ASSESSOR if role_name == 'ASSESSOR' else ScenarioRoles.OWNER
    su = ScenarioUsers(scenario_id=scenario_id, user_id=user_id, role=role)
    db_session.session.add(su)
    db_session.session.flush()
    return su


def _add_message(db_session, item_id, sender='Alice', content='Hello'):
    from db.models.scenario import Message

    msg = Message(
        item_id=item_id, sender=sender,
        content=content, timestamp=datetime.utcnow()
    )
    db_session.session.add(msg)
    db_session.session.flush()
    return msg


def _add_feature(db_session, item_id, content='Feature text', model_id='gpt-4'):
    from db.models.scenario import Feature, FeatureType

    ft = FeatureType.query.filter_by(name='summary').first()
    if not ft:
        ft = FeatureType(name='summary')
        db_session.session.add(ft)
        db_session.session.flush()

    feature = Feature(
        item_id=item_id, type_id=ft.type_id,
        content=content, model_id=model_id
    )
    db_session.session.add(feature)
    db_session.session.flush()
    return feature


# =============================================================================
# check_scenario_access - CRITICAL: Multi-Scenario Item Access
# =============================================================================

class TestCheckScenarioAccess:
    """
    Tests for check_scenario_access.

    CRITICAL BUG FIX AREA (per MEMORY.md):
    Items can belong to MULTIPLE scenarios via scenario_items table.
    check_scenario_access must check ALL scenarios, not just .first().
    """

    def test_SCHEMA_SVC_001_access_no_scenario_items(self, app, db):
        """Item with no scenario links should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.check_scenario_access(99999, 1)
            assert result is None

    def test_SCHEMA_SVC_002_access_via_scenario_user(self, app, db):
        """User with ScenarioUsers membership should get access."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'member_user')
            scenario = _create_scenario(db, 'Access Test', 1)
            item = _create_item(db, 'Access Item', chat_id=100)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            _add_user_to_scenario(db, scenario.id, user.id)
            db.session.commit()

            result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
            assert result is not None
            assert result.id == scenario.id

    def test_SCHEMA_SVC_003_access_via_owner(self, app, db):
        """Scenario creator should have access even without ScenarioUsers entry."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'owner_user')
            scenario = _create_scenario(db, 'Owner Access', 1, created_by='owner_user')
            item = _create_item(db, 'Owner Item', chat_id=101)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
            assert result is not None

    def test_SCHEMA_SVC_004_access_via_admin(self, app, db):
        """Admin user should have access."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'admin_check')
            scenario = _create_scenario(db, 'Admin Access', 1, created_by='other')
            item = _create_item(db, 'Admin Item', chat_id=102)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            with patch('services.evaluation.schema_adapter_service.PermissionService') as mock_perm:
                mock_perm.check_permission.return_value = True
                result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
                assert result is not None

    def test_SCHEMA_SVC_005_access_denied_no_membership(self, app, db):
        """Non-member, non-owner, non-admin should be denied."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'denied_user')
            scenario = _create_scenario(db, 'Denied', 1, created_by='other')
            item = _create_item(db, 'Denied Item', chat_id=103)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            with patch('services.evaluation.schema_adapter_service.PermissionService') as mock_perm:
                mock_perm.check_permission.return_value = False
                result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
                assert result is None

    def test_SCHEMA_SVC_006_multi_scenario_access_first_match(self, app, db):
        """CRITICAL: Item in multiple scenarios should check ALL and return first match."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'multi_user')

            # Create two scenarios
            scenario1 = _create_scenario(db, 'Scenario 1', 1, created_by='other1')
            scenario2 = _create_scenario(db, 'Scenario 2', 1, created_by='other2')

            item = _create_item(db, 'Multi Item', chat_id=104)

            # Link item to BOTH scenarios
            _link_item_to_scenario(db, scenario1.id, item.item_id)
            _link_item_to_scenario(db, scenario2.id, item.item_id)

            # User has access to scenario2 only
            _add_user_to_scenario(db, scenario2.id, user.id)
            db.session.commit()

            result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
            # Should find access via scenario2
            assert result is not None
            assert result.id == scenario2.id

    def test_SCHEMA_SVC_007_multi_scenario_no_access(self, app, db):
        """Item in multiple scenarios, user has no access to any."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'no_multi_access')

            scenario1 = _create_scenario(db, 'S1', 1, created_by='other')
            scenario2 = _create_scenario(db, 'S2', 1, created_by='other')

            item = _create_item(db, 'No Access Multi', chat_id=105)
            _link_item_to_scenario(db, scenario1.id, item.item_id)
            _link_item_to_scenario(db, scenario2.id, item.item_id)
            db.session.commit()

            with patch('services.evaluation.schema_adapter_service.PermissionService') as mock_perm:
                mock_perm.check_permission.return_value = False
                result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
                assert result is None

    def test_SCHEMA_SVC_008_item_added_to_new_scenario_still_accessible_from_old(self, app, db):
        """
        CRITICAL: Items from generation wizard added to new scenarios should
        still be accessible from previous scenarios.
        """
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'gen_wizard_user')

            # Original scenario
            original = _create_scenario(db, 'Original', 1, created_by='creator')
            # New scenario from generation wizard
            new_scenario = _create_scenario(db, 'Generated', 1, created_by='creator2')

            item = _create_item(db, 'Generated Item', chat_id=106)

            # Item belongs to both scenarios (as happens with generation wizard)
            _link_item_to_scenario(db, original.id, item.item_id)
            _link_item_to_scenario(db, new_scenario.id, item.item_id)

            # User has access to original scenario
            _add_user_to_scenario(db, original.id, user.id)
            db.session.commit()

            result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
            assert result is not None
            assert result.id == original.id


# =============================================================================
# get_scenario_for_item
# =============================================================================

class TestGetScenarioForItem:
    """Tests for get_scenario_for_item."""

    def test_SCHEMA_SVC_009_no_scenario(self, app, db):
        """Item with no scenario should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_scenario_for_item(99999)
            assert result is None

    def test_SCHEMA_SVC_010_returns_scenario(self, app, db):
        """Should return the scenario for a linked item."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            scenario = _create_scenario(db, 'Linked', 1)
            item = _create_item(db, 'Linked Item', chat_id=200)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            result = SchemaAdapter.get_scenario_for_item(item.item_id)
            assert result is not None
            assert result.id == scenario.id


# =============================================================================
# get_ranking_thread_data
# =============================================================================

class TestGetRankingThreadData:
    """Tests for get_ranking_thread_data."""

    def test_SCHEMA_SVC_011_ranking_not_found(self, app, db):
        """Nonexistent item should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_ranking_thread_data(99999, 1)
            assert result is None

    @patch('services.ranking_service.RankingService')
    def test_SCHEMA_SVC_012_ranking_returns_legacy_format(self, mock_rs, app, db):
        """Should return legacy ranking format with messages and features."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        mock_rs.has_user_fully_ranked_thread.return_value = False

        with app.app_context():
            user = _create_user(db, 'ranking_user')
            item = _create_item(db, 'Ranking Item', chat_id=300)
            _add_message(db, item.item_id, 'Bob', 'Message text')
            _add_feature(db, item.item_id, 'Feature A', 'model-1')
            db.session.commit()

            result = SchemaAdapter.get_ranking_thread_data(item.item_id, user.id)
            assert result is not None
            assert result['chat_id'] == 300
            assert result['subject'] == 'Ranking Item'
            assert result['ranked'] is False
            assert len(result['messages']) == 1
            assert result['messages'][0]['sender'] == 'Bob'
            assert len(result['features']) == 1
            assert result['features'][0]['model_name'] == 'model-1'

    @patch('services.ranking_service.RankingService')
    def test_SCHEMA_SVC_013_ranking_with_ranked_status(self, mock_rs, app, db):
        """Should reflect ranked=True when user has fully ranked."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        mock_rs.has_user_fully_ranked_thread.return_value = True

        with app.app_context():
            user = _create_user(db, 'ranked_user')
            item = _create_item(db, 'Ranked Item', chat_id=301)
            db.session.commit()

            result = SchemaAdapter.get_ranking_thread_data(item.item_id, user.id)
            assert result['ranked'] is True

    @patch('services.ranking_service.RankingService')
    def test_SCHEMA_SVC_014_ranking_skip_ranked_status(self, mock_rs, app, db):
        """include_ranked_status=False should skip the check."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            user = _create_user(db, 'skip_rank')
            item = _create_item(db, 'Skip Rank', chat_id=302)
            db.session.commit()

            result = SchemaAdapter.get_ranking_thread_data(
                item.item_id, user.id, include_ranked_status=False
            )
            assert result['ranked'] is False
            mock_rs.has_user_fully_ranked_thread.assert_not_called()


# =============================================================================
# get_rating_thread_data
# =============================================================================

class TestGetRatingThreadData:
    """Tests for get_rating_thread_data."""

    def test_SCHEMA_SVC_015_rating_not_found(self, app, db):
        """Nonexistent item should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_rating_thread_data(99999, 1)
            assert result is None

    def test_SCHEMA_SVC_016_rating_returns_legacy_format(self, app, db):
        """Should return legacy rating format."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            user = _create_user(db, 'rating_user')
            item = _create_item(db, 'Rating Item', chat_id=400)
            _add_message(db, item.item_id)
            _add_feature(db, item.item_id)
            db.session.commit()

            result = SchemaAdapter.get_rating_thread_data(item.item_id, user.id)
            assert result is not None
            assert 'chat_id' in result
            assert 'messages' in result
            assert 'features' in result
            assert result['subject'] == 'Rating Item'


# =============================================================================
# get_mail_rating_thread_data
# =============================================================================

class TestGetMailRatingThreadData:
    """Tests for get_mail_rating_thread_data."""

    def test_SCHEMA_SVC_017_mail_rating_not_found(self, app, db):
        """Nonexistent item should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_mail_rating_thread_data(99999, 1)
            assert result is None

    def test_SCHEMA_SVC_018_mail_rating_returns_format(self, app, db):
        """Should return mail rating format with thread_id."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            user = _create_user(db, 'mail_user')
            item = _create_item(db, 'Mail Item', chat_id=500)
            _add_message(db, item.item_id, 'Klient', 'Hallo')
            _add_message(db, item.item_id, 'Berater', 'Guten Tag')
            db.session.commit()

            result = SchemaAdapter.get_mail_rating_thread_data(item.item_id, user.id)
            assert result is not None
            assert result['thread_id'] == item.item_id
            assert len(result['messages']) == 2
            assert 'features' not in result  # mail_rating has no features


# =============================================================================
# get_authenticity_thread_data
# =============================================================================

class TestGetAuthenticityThreadData:
    """Tests for get_authenticity_thread_data."""

    def test_SCHEMA_SVC_019_authenticity_not_found(self, app, db):
        """Nonexistent item should return None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_authenticity_thread_data(99999, 1)
            assert result is None

    def test_SCHEMA_SVC_020_authenticity_no_vote(self, app, db):
        """No vote should return user_vote=None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            user = _create_user(db, 'no_vote_user')
            item = _create_item(db, 'Auth Item', chat_id=600)
            db.session.commit()

            result = SchemaAdapter.get_authenticity_thread_data(item.item_id, user.id)
            assert result is not None
            assert result['user_vote'] is None

    def test_SCHEMA_SVC_021_authenticity_with_vote(self, app, db):
        """Should include user vote when it exists."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.authenticity import UserAuthenticityVote

        with app.app_context():
            user = _create_user(db, 'auth_vote_user')
            item = _create_item(db, 'Auth Vote Item', chat_id=601)
            vote = UserAuthenticityVote(
                user_id=user.id, item_id=item.item_id,
                vote='fake', confidence=0.8
            )
            db.session.add(vote)
            db.session.commit()

            result = SchemaAdapter.get_authenticity_thread_data(item.item_id, user.id)
            assert result['user_vote'] is not None
            assert result['user_vote']['vote'] == 'fake'
            assert result['user_vote']['confidence'] == 0.8


# =============================================================================
# get_ranking_threads_list
# =============================================================================

class TestGetRankingThreadsList:
    """Tests for get_ranking_threads_list."""

    @patch('services.ranking_service.RankingService')
    def test_SCHEMA_SVC_022_threads_list_empty(self, mock_rs, app, db):
        """Empty items list should return empty list."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            result = SchemaAdapter.get_ranking_threads_list([], 1)
            assert result == []

    @patch('services.ranking_service.RankingService')
    def test_SCHEMA_SVC_023_threads_list_multiple(self, mock_rs, app, db):
        """Should return list with correct fields for each item."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.scenario import EvaluationItem
        mock_rs.has_user_fully_ranked_thread.return_value = False

        with app.app_context():
            item1 = _create_item(db, 'Item 1', chat_id=700)
            item2 = _create_item(db, 'Item 2', chat_id=701)
            db.session.commit()

            items = EvaluationItem.query.all()
            result = SchemaAdapter.get_ranking_threads_list(items, 1)
            assert len(result) == 2
            assert result[0]['subject'] == 'Item 1'
            assert result[1]['subject'] == 'Item 2'
            assert 'thread_id' in result[0]
            assert 'ranked' in result[0]


# =============================================================================
# schema_to_legacy_ranking
# =============================================================================

class TestSchemaToLegacyRanking:
    """Tests for schema_to_legacy_ranking conversion."""

    def test_SCHEMA_SVC_024_conversion_text_reference(self, app, db):
        """Should convert text reference to single message."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from schemas.evaluation_data_schemas import (
            EvaluationData, EvaluationType, ContentType, SourceType
        )

        with app.app_context():
            schema_data = EvaluationData(
                schema_version='1.0',
                type=EvaluationType.RANKING,
                reference={
                    'type': ContentType.TEXT,
                    'label': 'Source Article',
                    'content': 'Article text here'
                },
                items=[
                    {
                        'id': 'item_1',
                        'label': 'Summary 1',
                        'source': {'type': SourceType.LLM, 'name': 'gpt-4'},
                        'content': 'Summary content'
                    }
                ],
                config={
                    'mode': 'simple',
                    'buckets': [
                        {'id': 'good', 'label': {'de': 'Gut', 'en': 'Good'}, 'color': '#98d4bb', 'order': 1}
                    ],
                    'allow_ties': True
                }
            )

            result = SchemaAdapter.schema_to_legacy_ranking(schema_data)
            assert result['subject'] == 'Source Article'
            assert len(result['messages']) == 1
            assert result['messages'][0]['content'] == 'Article text here'
            assert len(result['features']) == 1
            assert result['features'][0]['model_name'] == 'gpt-4'

    def test_SCHEMA_SVC_025_conversion_no_reference(self, app, db):
        """Should handle missing reference gracefully."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from schemas.evaluation_data_schemas import EvaluationData, EvaluationType

        with app.app_context():
            schema_data = EvaluationData(
                schema_version='1.0',
                type=EvaluationType.RANKING,
                items=[],
                config={
                    'mode': 'simple',
                    'buckets': [
                        {'id': 'good', 'label': {'de': 'Gut', 'en': 'Good'}, 'color': '#98d4bb', 'order': 1}
                    ],
                    'allow_ties': True
                }
            )

            result = SchemaAdapter.schema_to_legacy_ranking(schema_data)
            assert result['subject'] is None
            assert result['messages'] == []
            assert result['features'] == []

    def test_SCHEMA_SVC_026_conversion_conversation_reference(self, app, db):
        """Should convert conversation reference to message list."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from schemas.evaluation_data_schemas import (
            EvaluationData, EvaluationType, ContentType
        )

        with app.app_context():
            schema_data = EvaluationData(
                schema_version='1.0',
                type=EvaluationType.RANKING,
                reference={
                    'type': ContentType.CONVERSATION,
                    'label': 'Chat',
                    'content': [
                        {'role': 'user', 'content': 'Hello'},
                        {'role': 'assistant', 'content': 'Hi there'}
                    ]
                },
                items=[],
                config={
                    'mode': 'simple',
                    'buckets': [
                        {'id': 'good', 'label': {'de': 'Gut', 'en': 'Good'}, 'color': '#98d4bb', 'order': 1}
                    ],
                    'allow_ties': True
                }
            )

            result = SchemaAdapter.schema_to_legacy_ranking(schema_data)
            assert len(result['messages']) == 2
            assert result['messages'][0]['sender'] == 'user'
            assert result['messages'][1]['content'] == 'Hi there'


# =============================================================================
# Message formatting edge cases
# =============================================================================

class TestMessageFormatting:
    """Edge cases for message formatting in legacy adapters."""

    def test_SCHEMA_SVC_027_message_timestamp_isoformat(self, app, db):
        """Timestamps should be formatted as ISO strings."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.scenario import Message

        with app.app_context():
            item = _create_item(db, 'Timestamp Item', chat_id=800)
            ts = datetime(2026, 1, 15, 12, 30, 0)
            msg = Message(
                item_id=item.item_id, sender='Test',
                content='Text', timestamp=ts
            )
            db.session.add(msg)
            db.session.commit()

            result = SchemaAdapter.get_rating_thread_data(item.item_id, 1)
            assert result['messages'][0]['timestamp'] == '2026-01-15T12:30:00'

    def test_SCHEMA_SVC_028_message_null_timestamp(self, app, db):
        """Null timestamp should be returned as None."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.scenario import Message

        with app.app_context():
            item = _create_item(db, 'Null TS Item', chat_id=801)
            msg = Message(
                item_id=item.item_id, sender='Test',
                content='Text', timestamp=None
            )
            db.session.add(msg)
            db.session.commit()

            result = SchemaAdapter.get_rating_thread_data(item.item_id, 1)
            assert result['messages'][0]['timestamp'] is None


# =============================================================================
# Feature formatting edge cases
# =============================================================================

class TestFeatureFormatting:
    """Edge cases for feature formatting."""

    def test_SCHEMA_SVC_029_feature_no_model_id(self, app, db):
        """Feature with no model_id should show 'Unknown'."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.scenario import Feature, FeatureType

        with app.app_context():
            item = _create_item(db, 'No Model Item', chat_id=900)
            ft = FeatureType.query.filter_by(name='summary').first()
            if not ft:
                ft = FeatureType(name='summary')
                db.session.add(ft)
                db.session.flush()

            feature = Feature(
                item_id=item.item_id, type_id=ft.type_id,
                content='Content', model_id=None
            )
            db.session.add(feature)
            db.session.commit()

            result = SchemaAdapter.get_ranking_thread_data(
                item.item_id, 1, include_ranked_status=False
            )
            assert result['features'][0]['model_name'] == 'Unknown'

    def test_SCHEMA_SVC_030_feature_no_type(self, app, db):
        """Feature with no type should show 'Summary' default."""
        from services.evaluation.schema_adapter_service import SchemaAdapter
        from db.models.scenario import Feature

        with app.app_context():
            item = _create_item(db, 'No Type Item', chat_id=901)
            feature = Feature(
                item_id=item.item_id, type_id=None,
                content='Content', model_id='model-x'
            )
            db.session.add(feature)
            db.session.commit()

            result = SchemaAdapter.get_ranking_thread_data(
                item.item_id, 1, include_ranked_status=False
            )
            assert result['features'][0]['type'] == 'Summary'


# =============================================================================
# Access Control: Admin fallback check
# =============================================================================

class TestAccessControlAdminFallback:
    """Tests for admin fallback in access control."""

    def test_SCHEMA_SVC_031_admin_fallback_checks_first_scenario(self, app, db):
        """Admin check should use the first scenario from scenario_items."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'admin_fb')
            scenario = _create_scenario(db, 'Admin FB', 1, created_by='other')
            item = _create_item(db, 'Admin FB Item', chat_id=1100)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            # Non-member, non-owner, but admin
            with patch('services.evaluation.schema_adapter_service.PermissionService') as mock_perm:
                mock_perm.check_permission.return_value = True
                result = SchemaAdapter.check_scenario_access(item.item_id, user.id)
                assert result is not None
                assert result.id == scenario.id

    def test_SCHEMA_SVC_032_nonexistent_user_no_access(self, app, db):
        """Nonexistent user ID should not get access."""
        from services.evaluation.schema_adapter_service import SchemaAdapter

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            scenario = _create_scenario(db, 'Ghost', 1, created_by='someone')
            item = _create_item(db, 'Ghost Item', chat_id=1200)
            _link_item_to_scenario(db, scenario.id, item.item_id)
            db.session.commit()

            result = SchemaAdapter.check_scenario_access(item.item_id, 99999)
            assert result is None
