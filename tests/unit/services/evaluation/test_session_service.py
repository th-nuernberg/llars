"""
Tests for EvaluationSessionService.

Comprehensive unit tests covering session management for all evaluation types:
- Session creation and loading
- Thread/item status calculation (done/in_progress/pending)
- Item navigation and feature retrieval
- Access control checks
- Batch status loading optimization

Test IDs: [SESS_SVC_001] through [SESS_SVC_038]
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


# =============================================================================
# Helpers
# =============================================================================

def _create_function_type(db_session, name, ftype_id):
    """Create a FeatureFunctionType."""
    from db.models.scenario import FeatureFunctionType

    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db_session.session.add(ftype)
    db_session.session.flush()
    return ftype


def _create_user(db_session, username='testuser'):
    """Create a test user."""
    from db.models.user import User
    import hashlib

    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db_session.session.add(user)
    db_session.session.flush()
    return user


def _create_scenario(db_session, name, ftype_id, created_by='creator', config_json=None):
    """Create a scenario."""
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


def _create_item_and_link(db_session, scenario_id, subject='Item', chat_id=1):
    """Create an EvaluationItem and link to scenario."""
    from db.models.scenario import EvaluationItem, ScenarioItems

    item = EvaluationItem(subject=subject, chat_id=chat_id)
    db_session.session.add(item)
    db_session.session.flush()

    si = ScenarioItems(scenario_id=scenario_id, item_id=item.item_id)
    db_session.session.add(si)
    db_session.session.flush()
    return item


def _add_user_to_scenario(db_session, scenario_id, user_id, role_name='ASSESSOR'):
    """Add user to scenario with given role + new flags."""
    from db.models.scenario import ScenarioUsers, ScenarioRoles

    role = ScenarioRoles.ASSESSOR if role_name == 'ASSESSOR' else ScenarioRoles.OWNER
    is_assessor = role_name == 'ASSESSOR'
    is_owner = role_name == 'OWNER'
    su = ScenarioUsers(
        scenario_id=scenario_id, user_id=user_id, role=role,
        access_level='OWNER' if is_owner else 'MEMBER',
        is_assessor=is_assessor,
        is_viewer=is_owner,  # Owner always gets viewer access
        manager_role='owner' if is_owner else 'none',
        evaluation_role='assessor' if is_assessor else 'none',
    )
    db_session.session.add(su)
    db_session.session.flush()
    return su


# =============================================================================
# _is_owner
# =============================================================================

class TestIsOwner:
    """Tests for _is_owner helper."""

    def test_SESS_SVC_001_is_owner_true(self, app, db):
        """Should return True when user is the scenario creator."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'owner_user')
            scenario = _create_scenario(db, 'Test', 1, created_by='owner_user')
            db.session.commit()

            assert EvaluationSessionService._is_owner(scenario, user.id) is True

    def test_SESS_SVC_002_is_owner_false_different_user(self, app, db):
        """Should return False when user is not the creator."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'other_user')
            scenario = _create_scenario(db, 'Test', 1, created_by='creator')
            db.session.commit()

            assert EvaluationSessionService._is_owner(scenario, user.id) is False

    def test_SESS_SVC_003_is_owner_false_no_created_by(self, app, db):
        """Should return False when scenario has no created_by."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'user1')
            scenario = _create_scenario(db, 'Test', 1, created_by=None)
            db.session.commit()

            assert EvaluationSessionService._is_owner(scenario, user.id) is False

    def test_SESS_SVC_004_is_owner_false_nonexistent_user(self, app, db):
        """Should return False when user ID does not exist."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            scenario = _create_scenario(db, 'Test', 1, created_by='someone')
            db.session.commit()

            assert EvaluationSessionService._is_owner(scenario, 99999) is False


# =============================================================================
# get_session_data
# =============================================================================

class TestGetSessionData:
    """Tests for get_session_data."""

    def test_SESS_SVC_005_session_not_found(self, app, db):
        """Should return error for nonexistent scenario."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService.get_session_data(99999, 1)
            assert 'error' in result

    def test_SESS_SVC_006_session_no_access(self, app, db):
        """Should return error when user has no access."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'no_access')
            scenario = _create_scenario(db, 'Private', 1, created_by='other')
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' in result

    def test_SESS_SVC_007_session_owner_access(self, app, db):
        """Owner should have access to session data."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'owner')
            scenario = _create_scenario(db, 'Owner Test', 1, created_by='owner')
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' not in result
            assert result['scenario']['name'] == 'Owner Test'
            assert result['scenario']['is_owner'] is True

    def test_SESS_SVC_008_session_evaluator_access(self, app, db):
        """Evaluator should have access via ScenarioUsers."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'evaluator')
            scenario = _create_scenario(db, 'Eval Test', 1, created_by='other')
            _add_user_to_scenario(db, scenario.id, user.id, 'ASSESSOR')
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' not in result
            assert result['scenario']['name'] == 'Eval Test'

    def test_SESS_SVC_009_session_returns_items(self, app, db):
        """Session data should include linked items."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'items_user')
            scenario = _create_scenario(db, 'Items Test', 1, created_by='items_user')
            _create_item_and_link(db, scenario.id, 'Item A', chat_id=10)
            _create_item_and_link(db, scenario.id, 'Item B', chat_id=11)
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' not in result
            assert len(result['items']) == 2

    def test_SESS_SVC_010_session_config_string_parsed(self, app, db):
        """String config_json should be parsed to dict."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import RatingScenarios

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'config_user')
            scenario = _create_scenario(db, 'Config Test', 1, created_by='config_user')
            # Manually set string config
            scenario.config_json = '{"key": "value"}'
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' not in result
            assert result['config'] == {"key": "value"}

    def test_SESS_SVC_011_session_empty_scenario(self, app, db):
        """Scenario with no items should return empty items list."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'empty_user')
            scenario = _create_scenario(db, 'Empty', 1, created_by='empty_user')
            db.session.commit()

            result = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert 'error' not in result
            assert result['items'] == []


# =============================================================================
# _batch_get_evaluation_statuses
# =============================================================================

class TestBatchGetEvaluationStatuses:
    """Tests for batch status loading."""

    def test_SESS_SVC_012_empty_thread_ids(self, app, db):
        """Empty thread IDs should return empty dict."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService._batch_get_evaluation_statuses(
                [], 1, 'ranking', 1
            )
            assert result == {}

    def test_SESS_SVC_013_all_pending_by_default(self, app, db):
        """Thread IDs with no evaluations should all be 'pending'."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'ranking', 1)
            user = _create_user(db, 'batch_user')
            db.session.commit()

            result = EvaluationSessionService._batch_get_evaluation_statuses(
                [1, 2, 3], user.id, 'ranking', 1
            )
            assert all(v == 'pending' for v in result.values())


# =============================================================================
# _batch_status_ranking
# =============================================================================

class TestBatchStatusRanking:
    """Tests for ranking batch status."""

    def test_SESS_SVC_014_ranking_all_pending(self, app, db):
        """Items with no features should be pending."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService._batch_status_ranking([1, 2], 1)
            assert result[1] == 'pending'
            assert result[2] == 'pending'

    def test_SESS_SVC_015_ranking_done_when_fully_ranked(self, app, db):
        """Items should be 'done' when all features are ranked."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, Feature, FeatureType,
            UserFeatureRanking
        )
        from db.models.user import User

        with app.app_context():
            user = _create_user(db, 'ranker')
            item = EvaluationItem(subject='Rank Item', chat_id=300)
            db.session.add(item)
            db.session.flush()

            ft = FeatureType(name='summary')
            db.session.add(ft)
            db.session.flush()

            feature = Feature(item_id=item.item_id, type_id=ft.type_id, content='text')
            db.session.add(feature)
            db.session.flush()

            ranking = UserFeatureRanking(
                user_id=user.id, feature_id=feature.feature_id,
                ranking_content=1.0, bucket='good'
            )
            db.session.add(ranking)
            db.session.commit()

            result = EvaluationSessionService._batch_status_ranking(
                [item.item_id], user.id
            )
            assert result[item.item_id] == 'done'

    def test_SESS_SVC_016_ranking_in_progress(self, app, db):
        """Items with partial rankings should be 'in_progress'."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, Feature, FeatureType,
            UserFeatureRanking
        )

        with app.app_context():
            user = _create_user(db, 'partial_ranker')
            item = EvaluationItem(subject='Partial', chat_id=301)
            db.session.add(item)
            db.session.flush()

            ft = FeatureType(name='summary2')
            db.session.add(ft)
            db.session.flush()

            # Two features, only one ranked
            f1 = Feature(item_id=item.item_id, type_id=ft.type_id, content='text1')
            f2 = Feature(item_id=item.item_id, type_id=ft.type_id, content='text2')
            db.session.add_all([f1, f2])
            db.session.flush()

            ranking = UserFeatureRanking(
                user_id=user.id, feature_id=f1.feature_id,
                ranking_content=1.0, bucket='good'
            )
            db.session.add(ranking)
            db.session.commit()

            result = EvaluationSessionService._batch_status_ranking(
                [item.item_id], user.id
            )
            assert result[item.item_id] == 'in_progress'


# =============================================================================
# _batch_status_rating
# =============================================================================

class TestBatchStatusRating:
    """Tests for rating batch status."""

    def test_SESS_SVC_017_rating_done_with_dim_status(self, app, db):
        """Item with DONE dimensional rating should show done."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            RatingScenarios, FeatureFunctionType,
            EvaluationItem, ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'rating', 2)
            user = _create_user(db, 'dim_rater')
            scenario = _create_scenario(db, 'Dim Rating', 2, config_json={
                'dimensions': [{'id': 'coherence'}, {'id': 'fluency'}]
            })
            item = EvaluationItem(subject='Dim Item', chat_id=400)
            db.session.add(item)
            db.session.flush()

            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 4, 'fluency': 5},
                overall_score=4.5, status=ProgressionStatus.DONE
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._batch_status_rating(
                [item.item_id], user.id, scenario.id
            )
            assert result[item.item_id] == 'done'

    def test_SESS_SVC_018_rating_in_progress_partial_dims(self, app, db):
        """Partial dimensional rating should show in_progress."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            RatingScenarios, FeatureFunctionType,
            EvaluationItem, ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'rating', 2)
            user = _create_user(db, 'partial_rater')
            scenario = _create_scenario(db, 'Partial', 2, config_json={
                'dimensions': [{'id': 'coherence'}, {'id': 'fluency'}]
            })
            item = EvaluationItem(subject='Partial Item', chat_id=401)
            db.session.add(item)
            db.session.flush()

            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'coherence': 4},  # Missing fluency
                overall_score=4.0, status=ProgressionStatus.PROGRESSING
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._batch_status_rating(
                [item.item_id], user.id, scenario.id
            )
            assert result[item.item_id] == 'in_progress'


# =============================================================================
# _get_thread_evaluation_status (single-item)
# =============================================================================

class TestGetThreadEvaluationStatus:
    """Tests for per-thread evaluation status."""

    def test_SESS_SVC_019_authenticity_done(self, app, db):
        """Authenticity vote should mark thread as done."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import EvaluationItem
        from db.models.authenticity import UserAuthenticityVote

        with app.app_context():
            user = _create_user(db, 'auth_voter')
            item = EvaluationItem(subject='Auth Item', chat_id=500)
            db.session.add(item)
            db.session.flush()

            vote = UserAuthenticityVote(
                user_id=user.id, item_id=item.item_id, vote='fake'
            )
            db.session.add(vote)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'authenticity'
            )
            assert result == 'done'

    def test_SESS_SVC_020_authenticity_pending(self, app, db):
        """No vote should be pending."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            user = _create_user(db, 'no_voter')
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                99999, user.id, 'authenticity'
            )
            assert result == 'pending'

    def test_SESS_SVC_021_labeling_done(self, app, db):
        """Labeling with category should be done."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import EvaluationItem, RatingScenarios, FeatureFunctionType
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'labeler')
            scenario = _create_scenario(db, 'Label Test', 7)
            item = EvaluationItem(subject='Label Item', chat_id=600)
            db.session.add(item)
            db.session.flush()

            label_eval = ItemLabelingEvaluation(
                user_id=user.id, item_id=item.item_id,
                scenario_id=scenario.id, category_id='positive'
            )
            db.session.add(label_eval)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_SESS_SVC_022_labeling_unsure_is_done(self, app, db):
        """Labeling marked as unsure should also be done."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import EvaluationItem, ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'unsure_labeler')
            scenario = _create_scenario(db, 'Unsure Label', 7)
            item = EvaluationItem(subject='Unsure Item', chat_id=601)
            db.session.add(item)
            db.session.flush()

            label_eval = ItemLabelingEvaluation(
                user_id=user.id, item_id=item.item_id,
                scenario_id=scenario.id, is_unsure=True
            )
            db.session.add(label_eval)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_SESS_SVC_023_labeling_pending(self, app, db):
        """No labeling evaluation should be pending."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'no_labeler')
            scenario = _create_scenario(db, 'No Label', 7)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                99999, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'pending'

    def test_SESS_SVC_024_unknown_type_returns_pending(self, app, db):
        """Unknown function type should return pending."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService._get_thread_evaluation_status(
                1, 1, 'nonexistent_type'
            )
            assert result == 'pending'


# =============================================================================
# _is_thread_evaluated (backward compat)
# =============================================================================

class TestIsThreadEvaluated:
    """Tests for backward compatibility wrapper."""

    def test_SESS_SVC_025_evaluated_returns_true_for_done(self, app, db):
        """Should return True when status is 'done'."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import EvaluationItem
        from db.models.authenticity import UserAuthenticityVote

        with app.app_context():
            user = _create_user(db, 'bc_voter')
            item = EvaluationItem(subject='BC Item', chat_id=700)
            db.session.add(item)
            db.session.flush()

            vote = UserAuthenticityVote(
                user_id=user.id, item_id=item.item_id, vote='authentic'
            )
            db.session.add(vote)
            db.session.commit()

            result = EvaluationSessionService._is_thread_evaluated(
                item.item_id, user.id, 'authenticity'
            )
            assert result is True

    def test_SESS_SVC_026_evaluated_returns_false_for_pending(self, app, db):
        """Should return False when not evaluated."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            user = _create_user(db, 'bc_none')
            db.session.commit()

            result = EvaluationSessionService._is_thread_evaluated(
                99999, user.id, 'authenticity'
            )
            assert result is False


# =============================================================================
# get_thread_features
# =============================================================================

class TestGetThreadFeatures:
    """Tests for get_thread_features."""

    def test_SESS_SVC_027_features_thread_not_found(self, app, db):
        """Should return error when thread does not exist."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService.get_thread_features(1, 99999, 1)
            assert 'error' in result

    def test_SESS_SVC_028_features_returned_correctly(self, app, db):
        """Should return messages and features for a thread."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, Message, Feature, FeatureType
        )

        with app.app_context():
            user = _create_user(db, 'feat_user')
            item = EvaluationItem(subject='Feat Item', chat_id=800)
            db.session.add(item)
            db.session.flush()

            msg = Message(
                item_id=item.item_id, sender='Alice',
                content='Hello', timestamp=datetime.utcnow()
            )
            db.session.add(msg)

            ft = FeatureType(name='summary3')
            db.session.add(ft)
            db.session.flush()

            feature = Feature(
                item_id=item.item_id, type_id=ft.type_id,
                content='Summary text', model_id='gpt-4'
            )
            db.session.add(feature)
            db.session.commit()

            result = EvaluationSessionService.get_thread_features(1, item.item_id, user.id)
            assert 'error' not in result
            assert result['thread_id'] == item.item_id
            assert len(result['messages']) == 1
            assert result['messages'][0]['sender'] == 'Alice'
            assert len(result['features']) == 1
            assert result['features'][0]['model_name'] == 'gpt-4'
            assert result['features'][0]['evaluated'] is False


# =============================================================================
# save_feature_rating
# =============================================================================

class TestSaveFeatureRating:
    """Tests for save_feature_rating."""

    def test_SESS_SVC_029_save_new_feature_rating(self, app, db):
        """Should create a new feature rating."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, Feature, FeatureType, UserFeatureRating
        )

        with app.app_context():
            user = _create_user(db, 'feature_rater')
            item = EvaluationItem(subject='Rate Feature', chat_id=900)
            db.session.add(item)
            db.session.flush()

            ft = FeatureType(name='summary4')
            db.session.add(ft)
            db.session.flush()

            feature = Feature(
                item_id=item.item_id, type_id=ft.type_id,
                content='Feature text'
            )
            db.session.add(feature)
            db.session.commit()

            result = EvaluationSessionService.save_feature_rating(
                scenario_id=1,
                feature_id=feature.feature_id,
                user_id=user.id,
                rating=4,
                thread_id=item.item_id
            )

            assert result['success'] is True
            saved = UserFeatureRating.query.filter_by(
                user_id=user.id, feature_id=feature.feature_id
            ).first()
            assert saved is not None
            assert saved.rating_content == 4

    def test_SESS_SVC_030_save_feature_rating_nonexistent(self, app, db):
        """Rating nonexistent feature should return error."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService.save_feature_rating(
                scenario_id=1, feature_id=99999, user_id=1,
                rating=3, thread_id=1
            )
            assert 'error' in result

    def test_SESS_SVC_031_save_feature_rating_update(self, app, db):
        """Updating a feature rating should modify existing record."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, Feature, FeatureType, UserFeatureRating
        )

        with app.app_context():
            user = _create_user(db, 'update_rater')
            item = EvaluationItem(subject='Update Rate', chat_id=901)
            db.session.add(item)
            db.session.flush()

            ft = FeatureType(name='summary5')
            db.session.add(ft)
            db.session.flush()

            feature = Feature(
                item_id=item.item_id, type_id=ft.type_id,
                content='Update text'
            )
            db.session.add(feature)
            db.session.commit()

            # First rating
            EvaluationSessionService.save_feature_rating(
                scenario_id=1, feature_id=feature.feature_id,
                user_id=user.id, rating=3, thread_id=item.item_id
            )

            # Update
            EvaluationSessionService.save_feature_rating(
                scenario_id=1, feature_id=feature.feature_id,
                user_id=user.id, rating=5, thread_id=item.item_id
            )

            count = UserFeatureRating.query.filter_by(
                user_id=user.id, feature_id=feature.feature_id
            ).count()
            assert count == 1

            saved = UserFeatureRating.query.filter_by(
                user_id=user.id, feature_id=feature.feature_id
            ).first()
            assert saved.rating_content == 5


# =============================================================================
# mark_thread_complete
# =============================================================================

class TestMarkThreadComplete:
    """Tests for mark_thread_complete."""

    def test_SESS_SVC_032_mark_complete_returns_success(self, app, db):
        """Should always return success (completion is implicit)."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            result = EvaluationSessionService.mark_thread_complete(1, 1, 1)
            assert result['success'] is True
            assert result['status'] == 'completed'


# =============================================================================
# emit_evaluation_update
# =============================================================================

class TestEmitEvaluationUpdate:
    """Tests for the module-level emit function."""

    def test_SESS_SVC_033_emit_no_socketio(self, app, db):
        """Should not raise when socketio is not available."""
        from services.evaluation.session_service import emit_evaluation_update

        with app.app_context():
            # Should not raise
            emit_evaluation_update(1, 1, 1)

    def test_SESS_SVC_034_emit_with_socketio(self, app, db):
        """Should call socketio.emit when available."""
        from services.evaluation.session_service import emit_evaluation_update

        with app.app_context():
            mock_socketio = MagicMock()
            app.extensions = {'socketio': mock_socketio}

            emit_evaluation_update(1, 42, 7)
            mock_socketio.emit.assert_called_once()
            call_args = mock_socketio.emit.call_args
            assert call_args[0][0] == 'evaluation:item_evaluated'
            assert call_args[0][1]['item_id'] == 42


# =============================================================================
# Dimensional rating status with nested config
# =============================================================================

class TestDimensionalRatingStatusConfig:
    """Tests for dimension config at various nesting levels."""

    def test_SESS_SVC_035_rating_done_with_all_dims_no_status_flag(self, app, db):
        """Should detect done when all dims rated even if status is not DONE."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, RatingScenarios, FeatureFunctionType,
            ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'rating', 2)
            user = _create_user(db, 'nested_config_user')
            scenario = _create_scenario(db, 'Nested Config', 2, config_json={
                'dimensions': [{'id': 'a'}, {'id': 'b'}]
            })
            item = EvaluationItem(subject='Nested Item', chat_id=1000)
            db.session.add(item)
            db.session.flush()

            # Status is PROGRESSING but all dimensions are rated
            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'a': 4, 'b': 5},
                overall_score=4.5, status=ProgressionStatus.PROGRESSING
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'rating', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_SESS_SVC_036_rating_nested_eval_config_dimensions(self, app, db):
        """Should find dimensions in eval_config.dimensions."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'rating', 2)
            user = _create_user(db, 'eval_cfg_user')
            scenario = _create_scenario(db, 'Eval Config', 2, config_json={
                'eval_config': {
                    'dimensions': [{'id': 'x'}, {'id': 'y'}]
                }
            })
            item = EvaluationItem(subject='Eval Config Item', chat_id=1001)
            db.session.add(item)
            db.session.flush()

            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'x': 3, 'y': 4},
                overall_score=3.5, status=ProgressionStatus.PROGRESSING
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'rating', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_SESS_SVC_037_rating_wizard_nested_config(self, app, db):
        """Should find dimensions in eval_config.config.dimensions (wizard path)."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'rating', 2)
            user = _create_user(db, 'wizard_user')
            scenario = _create_scenario(db, 'Wizard Config', 2, config_json={
                'eval_config': {
                    'config': {
                        'dimensions': [{'id': 'w1'}, {'id': 'w2'}]
                    }
                }
            })
            item = EvaluationItem(subject='Wizard Item', chat_id=1002)
            db.session.add(item)
            db.session.flush()

            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'w1': 5, 'w2': 5},
                overall_score=5.0, status=ProgressionStatus.PROGRESSING
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'rating', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_SESS_SVC_038_mail_rating_uses_same_logic(self, app, db):
        """mail_rating should use the same status logic as rating."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import (
            EvaluationItem, ItemDimensionRating, ProgressionStatus
        )

        with app.app_context():
            _create_function_type(db, 'mail_rating', 3)
            user = _create_user(db, 'mail_rater')
            scenario = _create_scenario(db, 'Mail Rating', 3, config_json={
                'dimensions': [{'id': 'q'}, {'id': 'c'}]
            })
            item = EvaluationItem(subject='Mail Item', chat_id=1003)
            db.session.add(item)
            db.session.flush()

            dr = ItemDimensionRating(
                user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
                dimension_ratings={'q': 4, 'c': 3},
                overall_score=3.5, status=ProgressionStatus.DONE
            )
            db.session.add(dr)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'mail_rating', scenario_id=scenario.id
            )
            assert result == 'done'
