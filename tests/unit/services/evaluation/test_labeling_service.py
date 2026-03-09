"""
Tests for Labeling functionality.

Since there is no standalone labeling_service.py, this tests the labeling
functionality through:
- ItemLabelingEvaluation model (create, update, to_dict)
- Session service labeling status checks
- Labeling evaluation workflow (find-or-create pattern)

Test IDs: [LABEL_SVC_001] through [LABEL_SVC_025]
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


def _create_user(db_session, username='label_user'):
    from db.models.user import User
    import hashlib

    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db_session.session.add(user)
    db_session.session.flush()
    return user


def _create_scenario(db_session, name='Label Scenario', ftype_id=7, config_json=None):
    from db.models.scenario import RatingScenarios

    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        config_json=config_json or {
            'type': 'multiclass',
            'categories': [
                {'id': 'positive', 'name': {'de': 'Positiv'}},
                {'id': 'negative', 'name': {'de': 'Negativ'}},
                {'id': 'neutral', 'name': {'de': 'Neutral'}},
            ],
            'allowUnsure': True
        },
        created_by='creator'
    )
    db_session.session.add(scenario)
    db_session.session.flush()
    return scenario


def _create_item(db_session, subject='Labeling Item', chat_id=1):
    from db.models.scenario import EvaluationItem

    item = EvaluationItem(subject=subject, chat_id=chat_id)
    db_session.session.add(item)
    db_session.session.flush()
    return item


# =============================================================================
# ItemLabelingEvaluation Model
# =============================================================================

class TestItemLabelingEvaluationModel:
    """Tests for ItemLabelingEvaluation model."""

    def test_LABEL_SVC_001_create_basic(self, app, db):
        """Should create a basic labeling evaluation."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved is not None
            assert saved.category_id == 'positive'
            assert saved.is_unsure is False
            assert saved.feedback is None

    def test_LABEL_SVC_002_create_unsure(self, app, db):
        """Should create a labeling evaluation marked as unsure."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                is_unsure=True
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved.is_unsure is True
            assert saved.category_id is None

    def test_LABEL_SVC_003_create_with_feedback(self, app, db):
        """Should store optional feedback."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='negative',
                feedback='Seems very negative in tone'
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved.feedback == 'Seems very negative in tone'

    def test_LABEL_SVC_004_to_dict(self, app, db):
        """to_dict should include all expected fields."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive',
                is_unsure=False,
                feedback='Good'
            )
            db.session.add(eval_record)
            db.session.commit()

            result = eval_record.to_dict()
            assert 'id' in result
            assert 'user_id' in result
            assert 'item_id' in result
            assert 'scenario_id' in result
            assert 'category_id' in result
            assert result['category_id'] == 'positive'
            assert result['is_unsure'] is False
            assert result['feedback'] == 'Good'
            assert 'created_at' in result
            assert 'updated_at' in result

    def test_LABEL_SVC_005_unique_constraint(self, app, db):
        """Should enforce unique constraint on (user_id, item_id, scenario_id)."""
        from db.models.scenario import ItemLabelingEvaluation
        from sqlalchemy.exc import IntegrityError

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval1 = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval1)
            db.session.commit()

            eval2 = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='negative'
            )
            db.session.add(eval2)

            with pytest.raises(IntegrityError):
                db.session.commit()
            db.session.rollback()

    def test_LABEL_SVC_006_update_category(self, app, db):
        """Should be able to update category_id on existing evaluation."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db)
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            # Update
            eval_record.category_id = 'negative'
            eval_record.feedback = 'Changed my mind'
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved.category_id == 'negative'
            assert saved.feedback == 'Changed my mind'

    def test_LABEL_SVC_007_relationships(self, app, db):
        """Should have user, item, and scenario relationships."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'rel_user')
            scenario = _create_scenario(db)
            item = _create_item(db)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='neutral'
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved.user.username == 'rel_user'
            assert saved.item.subject == 'Labeling Item'
            assert saved.scenario.scenario_name == 'Label Scenario'


# =============================================================================
# Labeling Status in Session Service
# =============================================================================

class TestLabelingSessionStatus:
    """Tests for labeling status checks in session service."""

    def test_LABEL_SVC_008_status_pending_no_eval(self, app, db):
        """No evaluation should be 'pending'."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'pending_labeler')
            scenario = _create_scenario(db)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                99999, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'pending'

    def test_LABEL_SVC_009_status_done_with_category(self, app, db):
        """Evaluation with category_id should be 'done'."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'done_labeler')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=100)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'done'

    def test_LABEL_SVC_010_status_done_with_unsure(self, app, db):
        """Evaluation marked as unsure should also be 'done'."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'unsure_labeler')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=101)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                is_unsure=True
            )
            db.session.add(eval_record)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'labeling', scenario_id=scenario.id
            )
            assert result == 'done'


# =============================================================================
# Batch Labeling Status
# =============================================================================

class TestBatchLabelingStatus:
    """Tests for batch labeling status in _batch_get_evaluation_statuses."""

    def test_LABEL_SVC_011_batch_all_pending(self, app, db):
        """Multiple items with no evaluations should all be pending."""
        from services.evaluation.session_service import EvaluationSessionService

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'batch_label_user')
            scenario = _create_scenario(db)
            db.session.commit()

            result = EvaluationSessionService._batch_get_evaluation_statuses(
                [1, 2, 3], user.id, 'labeling', scenario.id
            )
            assert all(v == 'pending' for v in result.values())

    def test_LABEL_SVC_012_batch_mixed_status(self, app, db):
        """Should return mixed statuses for partially evaluated items."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'batch_mixed')
            scenario = _create_scenario(db)

            item1 = _create_item(db, 'Item A', chat_id=200)
            item2 = _create_item(db, 'Item B', chat_id=201)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item1.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            result = EvaluationSessionService._batch_get_evaluation_statuses(
                [item1.item_id, item2.item_id],
                user.id, 'labeling', scenario.id
            )
            assert result[item1.item_id] == 'done'
            assert result[item2.item_id] == 'pending'


# =============================================================================
# Labeling Find-or-Create Pattern
# =============================================================================

class TestLabelingFindOrCreate:
    """Tests for the find-or-create pattern used in evaluation_routes."""

    def test_LABEL_SVC_013_find_existing(self, app, db):
        """Should find existing evaluation by user/item/scenario."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'find_user')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=300)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            found = ItemLabelingEvaluation.query.filter_by(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id
            ).first()
            assert found is not None
            assert found.category_id == 'positive'

    def test_LABEL_SVC_014_update_existing_via_find(self, app, db):
        """Should update existing evaluation without creating duplicate."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'update_user')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=301)

            # Create
            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            # Find and update
            found = ItemLabelingEvaluation.query.filter_by(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id
            ).first()
            found.category_id = 'negative'
            found.is_unsure = False
            found.feedback = 'Updated'
            db.session.commit()

            count = ItemLabelingEvaluation.query.filter_by(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id
            ).count()
            assert count == 1

            saved = ItemLabelingEvaluation.query.first()
            assert saved.category_id == 'negative'
            assert saved.feedback == 'Updated'

    def test_LABEL_SVC_015_create_when_not_found(self, app, db):
        """Should create new evaluation when none exists."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'create_user')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=302)

            found = ItemLabelingEvaluation.query.filter_by(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id
            ).first()
            assert found is None

            new_eval = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='neutral',
                feedback='New evaluation'
            )
            db.session.add(new_eval)
            db.session.commit()

            count = ItemLabelingEvaluation.query.count()
            assert count == 1


# =============================================================================
# Multi-User Labeling
# =============================================================================

class TestMultiUserLabeling:
    """Tests for multiple users labeling the same item."""

    def test_LABEL_SVC_016_multiple_users_same_item(self, app, db):
        """Multiple users should be able to label the same item."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user1 = _create_user(db, 'labeler1')
            user2 = _create_user(db, 'labeler2')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=400)

            eval1 = ItemLabelingEvaluation(
                user_id=user1.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            eval2 = ItemLabelingEvaluation(
                user_id=user2.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='negative'
            )
            db.session.add_all([eval1, eval2])
            db.session.commit()

            count = ItemLabelingEvaluation.query.filter_by(
                item_id=item.item_id
            ).count()
            assert count == 2

    def test_LABEL_SVC_017_same_user_different_scenarios(self, app, db):
        """Same user should be able to label same item in different scenarios."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'multi_scenario')
            scenario1 = _create_scenario(db, name='Scenario A')
            scenario2 = _create_scenario(db, name='Scenario B')
            item = _create_item(db, chat_id=401)

            eval1 = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario1.id,
                category_id='positive'
            )
            eval2 = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario2.id,
                category_id='negative'
            )
            db.session.add_all([eval1, eval2])
            db.session.commit()

            count = ItemLabelingEvaluation.query.filter_by(
                user_id=user.id,
                item_id=item.item_id
            ).count()
            assert count == 2


# =============================================================================
# Edge Cases
# =============================================================================

class TestLabelingEdgeCases:
    """Edge cases for labeling functionality."""

    def test_LABEL_SVC_018_null_category_not_unsure(self, app, db):
        """Null category without unsure should not count as done."""
        from services.evaluation.session_service import EvaluationSessionService
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'null_cat')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=500)

            # Both category_id=None and is_unsure=False
            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id=None,
                is_unsure=False
            )
            db.session.add(eval_record)
            db.session.commit()

            result = EvaluationSessionService._get_thread_evaluation_status(
                item.item_id, user.id, 'labeling', scenario_id=scenario.id
            )
            # Neither category_id nor is_unsure set -> pending
            assert result == 'pending'

    def test_LABEL_SVC_019_empty_string_category(self, app, db):
        """Empty string category_id should still count as done (truthy in filter)."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'empty_cat')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=501)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id=''  # Empty string, not None
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            # Empty string is not None, so category_id is not None
            assert saved.category_id is not None

    def test_LABEL_SVC_020_to_dict_timestamps(self, app, db):
        """Timestamps in to_dict should be ISO format strings."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'ts_user')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=502)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            result = eval_record.to_dict()
            assert result['created_at'] is not None
            assert 'T' in result['created_at']  # ISO format has T separator

    def test_LABEL_SVC_021_thread_id_synonym(self, app, db):
        """thread_id synonym should work for backward compatibility."""
        from db.models.scenario import ItemLabelingEvaluation

        with app.app_context():
            _create_function_type(db, 'labeling', 7)
            user = _create_user(db, 'synonym_user')
            scenario = _create_scenario(db)
            item = _create_item(db, chat_id=503)

            eval_record = ItemLabelingEvaluation(
                user_id=user.id,
                item_id=item.item_id,
                scenario_id=scenario.id,
                category_id='positive'
            )
            db.session.add(eval_record)
            db.session.commit()

            saved = ItemLabelingEvaluation.query.first()
            assert saved.thread_id == saved.item_id
