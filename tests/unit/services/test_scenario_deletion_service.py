"""
Tests for services.scenario_deletion_service.delete_scenario_deep.

Regression suite for the 2026-08-16 prod incident: the IJCAI seeder's --reset
did a bare ``db.session.delete(scenario)`` and crashed with IntegrityError
(1048, "Column 'scenario_id' cannot be null") because the per-item evaluation
relationships on RatingScenarios carry no ORM cascade. The shared service must
(a) survive exactly that constellation, (b) hard-delete items orphaned by the
deletion, and (c) keep items still shared with another scenario.
"""

import pytest

pytestmark = pytest.mark.unit


def _make_scenario(db, name='SDEL Scenario', created_by='ijcai_demo'):
    from db.models import RatingScenarios
    scenario = RatingScenarios(scenario_name=name, created_by=created_by)
    db.session.add(scenario)
    db.session.commit()
    db.session.refresh(scenario)
    return scenario


def _make_user(db, username='sdel-user'):
    from db.models import User
    user = User(username=username, group_id=1, is_active=True, is_ai=False)
    if hasattr(user, 'password_hash'):
        user.password_hash = 'x'
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user


def _make_linked_item(db, scenario, subject='SDEL item'):
    """EvaluationItem linked to ``scenario`` with one message and one feature."""
    from db.models import Message, Feature
    from db.models.scenario import EvaluationItem, ScenarioItems
    item = EvaluationItem(subject=subject)
    db.session.add(item)
    db.session.flush()
    db.session.add(ScenarioItems(scenario_id=scenario.id, item_id=item.item_id))
    db.session.add(Message(item_id=item.item_id, sender='human', content='hello'))
    db.session.add(Feature(item_id=item.item_id, content='candidate'))
    db.session.commit()
    db.session.refresh(item)
    return item


class TestDeleteScenarioDeep:

    def test_SDEL_001_survives_dimension_rating_child(self, app, db, app_context):
        """[SDEL-001] Exact prod-crash repro: scenario with a dimension rating."""
        from db.models import RatingScenarios
        from db.tables import ItemDimensionRating
        from services.scenario_deletion_service import delete_scenario_deep

        scenario = _make_scenario(db)
        user = _make_user(db)
        item = _make_linked_item(db, scenario)
        db.session.add(ItemDimensionRating(
            user_id=user.id,
            item_id=item.item_id,
            scenario_id=scenario.id,
            dimension_ratings={'coherence': 4},
        ))
        db.session.commit()

        delete_scenario_deep(scenario)  # must not raise IntegrityError
        db.session.commit()

        assert RatingScenarios.query.get(scenario.id) is None
        assert ItemDimensionRating.query.count() == 0

    def test_SDEL_002_orphaned_item_is_hard_deleted(self, app, db, app_context):
        """[SDEL-002] Items only linked to the deleted scenario vanish fully."""
        from db.models import Message, Feature
        from db.models.scenario import EvaluationItem
        from services.scenario_deletion_service import delete_scenario_deep

        scenario = _make_scenario(db)
        item = _make_linked_item(db, scenario)
        item_id = item.item_id  # read before delete — instance detaches below

        orphaned = delete_scenario_deep(scenario)
        db.session.commit()
        # Drop the identity map: the bulk deletes above bypass the session, so
        # a plain .get() would hand back the stale cached instance and raise
        # ObjectDeletedError on attribute access instead of returning None.
        db.session.expunge_all()

        assert orphaned == 1
        assert EvaluationItem.query.get(item_id) is None
        assert Message.query.filter_by(item_id=item_id).count() == 0
        assert Feature.query.filter_by(item_id=item_id).count() == 0

    def test_SDEL_003_item_shared_with_other_scenario_survives(self, app, db, app_context):
        """[SDEL-003] Multi-scenario items are never hard-deleted."""
        from db.models.scenario import EvaluationItem, ScenarioItems
        from services.scenario_deletion_service import delete_scenario_deep

        scenario_a = _make_scenario(db, name='SDEL A')
        scenario_b = _make_scenario(db, name='SDEL B')
        item = _make_linked_item(db, scenario_a)
        db.session.add(ScenarioItems(scenario_id=scenario_b.id, item_id=item.item_id))
        db.session.commit()

        orphaned = delete_scenario_deep(scenario_a)
        db.session.commit()

        assert orphaned == 0
        assert EvaluationItem.query.get(item.item_id) is not None
        assert ScenarioItems.query.filter_by(
            scenario_id=scenario_b.id, item_id=item.item_id
        ).count() == 1
