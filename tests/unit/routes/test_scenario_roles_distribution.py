"""
Tests for Scenario Roles & Evaluation Consistency.

Covers:
1. Item distribution when assessors are added late (round_robin)
2. Item redistribution when assessors are removed / demoted
3. Agreement metrics filtering by active assessor role
4. Owner-as-assessor flag in scenario creation
5. Stats cache invalidation on role changes
6. Golden-value agreement metrics with hand-calculated expected values
7. Metric direction shifts on role changes
8. Boundary conditions (perfect agreement, single rater, all degraded)

Test IDs: SCEN_DIST_001 - SCEN_DIST_037
"""

import itertools
import json
from datetime import datetime, timedelta

import pytest

from tests.unit.routes.conftest import _make_token, _AuthClient

# Auto-incrementing counter for unique chat_id values (avoids unique constraint errors)
_chat_id_counter = itertools.count(1000)


# =============================================================================
# Helpers — keep local to avoid coupling to other test modules
# =============================================================================

def _make_scenario(db, *, name='Test', ftype_id=1, created_by='admin',
                   config_json=None):
    """Create a RatingScenarios row."""
    from db.models.scenario import RatingScenarios
    s = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        begin=datetime.utcnow(),
        end=datetime.utcnow() + timedelta(days=30),
        created_by=created_by,
        config_json=config_json or {},
    )
    db.session.add(s)
    db.session.commit()
    return s


def _make_user(db, username, *, api_key=None, is_active=True, role_name=None):
    """Create a User + optional role."""
    from db.models.user import User
    from db.models.permission import Role, UserRole
    u = User(
        username=username,
        password_hash='hash',
        api_key=api_key or f'key-{username}',
        collab_color='#000000',
        is_active=is_active,
    )
    db.session.add(u)
    db.session.commit()

    if role_name:
        role = Role.query.filter_by(role_name=role_name).first()
        if role:
            db.session.add(UserRole(
                username=username,
                role_id=role.id,
                assigned_by='test',
                assigned_at=datetime.utcnow(),
            ))
            db.session.commit()

    db.session.refresh(u)
    return u


def _add_scenario_user(db, scenario_id, user_id, *,
                       access_level='MEMBER', is_assessor=False,
                       is_viewer=True, role_str='VIEWER'):
    """Create a ScenarioUsers entry."""
    from db.models.scenario import ScenarioUsers, ScenarioRoles, InvitationStatus, MembershipStatus
    role_map = {
        'OWNER': ScenarioRoles.OWNER,
        'VIEWER': ScenarioRoles.VIEWER,
        'ASSESSOR': ScenarioRoles.ASSESSOR,
        'MANAGER': ScenarioRoles.MANAGER,
    }
    # Derive 2-axis roles from legacy flags
    manager_role = 'owner' if access_level == 'OWNER' else ('viewer' if is_viewer and not is_assessor else 'none')
    evaluation_role = 'assessor' if is_assessor else 'none'
    su = ScenarioUsers(
        scenario_id=scenario_id,
        user_id=user_id,
        role=role_map.get(role_str, ScenarioRoles.VIEWER),
        access_level=access_level,
        is_assessor=is_assessor,
        is_viewer=is_viewer,
        manager_role=manager_role,
        evaluation_role=evaluation_role,
        invitation_status=InvitationStatus.ACCEPTED,
        membership_status=MembershipStatus.ACTIVE,
        invited_by='test',
    )
    db.session.add(su)
    db.session.commit()
    return su


def _make_item_and_link(db, scenario_id, *, subject='Item'):
    """Create an EvaluationItem + ScenarioItems link, return ScenarioItems."""
    from db.models.scenario import EvaluationItem, ScenarioItems
    cid = next(_chat_id_counter)
    item = EvaluationItem(
        subject=subject,
        chat_id=cid,
        institut_id=cid,
        function_type_id=1,
    )
    db.session.add(item)
    db.session.commit()

    si = ScenarioItems(scenario_id=scenario_id, item_id=item.item_id)
    db.session.add(si)
    db.session.commit()
    return si


def _make_distribution(db, scenario_id, scenario_user_id, scenario_item_id):
    """Create a ScenarioItemDistribution entry."""
    from db.models.scenario import ScenarioItemDistribution
    dist = ScenarioItemDistribution(
        scenario_id=scenario_id,
        scenario_user_id=scenario_user_id,
        scenario_item_id=scenario_item_id,
    )
    db.session.add(dist)
    db.session.commit()
    return dist


def _create_feature(db, item_id, *, content='feature', model_id=None):
    """Create a Feature for the given item."""
    from db.models.scenario import Feature
    f = Feature(
        item_id=item_id,
        content=content,
        model_id=model_id or 'test-model',
    )
    db.session.add(f)
    db.session.commit()
    return f


def _create_ranking(db, user_id, feature_id, bucket='gut'):
    """Create a UserFeatureRanking entry."""
    from db.models.scenario import UserFeatureRanking
    r = UserFeatureRanking(
        user_id=user_id,
        feature_id=feature_id,
        bucket=bucket,
    )
    db.session.add(r)
    db.session.commit()
    return r


def _create_rating(db, user_id, feature_id, rating_content):
    """Create a UserFeatureRating entry."""
    from db.models.scenario import UserFeatureRating
    r = UserFeatureRating(
        user_id=user_id,
        feature_id=feature_id,
        rating_content=rating_content,
    )
    db.session.add(r)
    db.session.commit()
    return r


# =============================================================================
# 1. Item Distribution — assign_items_to_new_assessor
# =============================================================================

class TestAssignItemsToNewAssessor:
    """Tests for assign_items_to_new_assessor() utility."""

    def test_SCEN_DIST_001_round_robin_assigns_items_to_new_assessor(
        self, rdb, real_app, seed_function_types
    ):
        """New assessor in round_robin mode gets proportional share of undone items."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import assign_items_to_new_assessor
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'})
            user_a = _make_user(rdb, 'assessor_a')
            user_b = _make_user(rdb, 'assessor_b')

            su_a = _add_scenario_user(rdb, scenario.id, user_a.id,
                                      is_assessor=True, role_str='ASSESSOR')

            # Create 6 items and assign all to assessor_a
            items = [_make_item_and_link(rdb, scenario.id, subject=f'Item {i}') for i in range(6)]
            for si in items:
                _make_distribution(rdb, scenario.id, su_a.id, si.id)

            # Verify: assessor_a has 6 items
            a_count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su_a.id
            ).count()
            assert a_count == 6

            # Add assessor_b — should get ~3 items (6 / 2)
            su_b = _add_scenario_user(rdb, scenario.id, user_b.id,
                                      is_assessor=True, role_str='ASSESSOR')
            assign_items_to_new_assessor(scenario.id, scenario, su_b.id)
            rdb.session.commit()

            a_after = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su_a.id
            ).count()
            b_after = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su_b.id
            ).count()

            assert b_after == 3, f"New assessor should get 3 items, got {b_after}"
            assert a_after == 3, f"Original assessor should keep 3 items, got {a_after}"
            # Total unchanged
            assert a_after + b_after == 6

    def test_SCEN_DIST_002_all_mode_skips_distribution(
        self, rdb, real_app, seed_function_types
    ):
        """In 'all' distribution mode, no distribution records are created."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import assign_items_to_new_assessor
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'all'})
            user_a = _make_user(rdb, 'all_user')
            su_a = _add_scenario_user(rdb, scenario.id, user_a.id,
                                      is_assessor=True, role_str='ASSESSOR')
            _make_item_and_link(rdb, scenario.id, subject='Shared item')

            assign_items_to_new_assessor(scenario.id, scenario, su_a.id)
            rdb.session.commit()

            count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id
            ).count()
            assert count == 0

    def test_SCEN_DIST_003_first_assessor_gets_all_items(
        self, rdb, real_app, seed_function_types
    ):
        """First assessor in round_robin with no existing assessors gets all items."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import assign_items_to_new_assessor
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'})
            user_a = _make_user(rdb, 'first_assessor')
            su_a = _add_scenario_user(rdb, scenario.id, user_a.id,
                                      is_assessor=True, role_str='ASSESSOR')

            for i in range(4):
                _make_item_and_link(rdb, scenario.id, subject=f'Item {i}')

            assign_items_to_new_assessor(scenario.id, scenario, su_a.id)
            rdb.session.commit()

            count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su_a.id
            ).count()
            assert count == 4

    def test_SCEN_DIST_004_three_assessors_fair_split(
        self, rdb, real_app, seed_function_types
    ):
        """Adding a 3rd assessor splits undone items fairly among 3 users."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import assign_items_to_new_assessor
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'})
            u1 = _make_user(rdb, 'u1')
            u2 = _make_user(rdb, 'u2')
            u3 = _make_user(rdb, 'u3')

            su1 = _add_scenario_user(rdb, scenario.id, u1.id, is_assessor=True, role_str='ASSESSOR')
            su2 = _add_scenario_user(rdb, scenario.id, u2.id, is_assessor=True, role_str='ASSESSOR')

            # 9 items total, 5 to u1, 4 to u2 (simulating uneven initial distribution)
            items = [_make_item_and_link(rdb, scenario.id, subject=f'I{i}') for i in range(9)]
            for si in items[:5]:
                _make_distribution(rdb, scenario.id, su1.id, si.id)
            for si in items[5:]:
                _make_distribution(rdb, scenario.id, su2.id, si.id)

            # Add u3 — should get 9//3 = 3 items
            su3 = _add_scenario_user(rdb, scenario.id, u3.id, is_assessor=True, role_str='ASSESSOR')
            assign_items_to_new_assessor(scenario.id, scenario, su3.id)
            rdb.session.commit()

            c3 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su3.id
            ).count()
            assert c3 == 3, f"3rd assessor should get 3 items, got {c3}"

            # Total must remain 9
            total = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id
            ).count()
            assert total == 9


# =============================================================================
# 2. Item Redistribution — reassign_items_from_user
# =============================================================================

class TestReassignItemsFromUser:
    """Tests for reassign_items_from_user() utility."""

    def test_SCEN_DIST_005_removed_assessor_items_redistributed(
        self, rdb, real_app, seed_function_types
    ):
        """When an assessor is removed, their undone items go to remaining assessors."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import reassign_items_from_user
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'})
            u1 = _make_user(rdb, 'keep1')
            u2 = _make_user(rdb, 'remove_me')

            su1 = _add_scenario_user(rdb, scenario.id, u1.id, is_assessor=True, role_str='ASSESSOR')
            su2 = _add_scenario_user(rdb, scenario.id, u2.id, is_assessor=True, role_str='ASSESSOR')

            items = [_make_item_and_link(rdb, scenario.id, subject=f'R{i}') for i in range(4)]
            # u1 gets 2, u2 gets 2
            for si in items[:2]:
                _make_distribution(rdb, scenario.id, su1.id, si.id)
            for si in items[2:]:
                _make_distribution(rdb, scenario.id, su2.id, si.id)

            # Remove u2 — their 2 items should move to u1
            reassign_items_from_user(scenario.id, scenario, su2.id)
            rdb.session.commit()

            c1 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su1.id
            ).count()
            c2 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su2.id
            ).count()

            assert c1 == 4, f"Remaining assessor should have all 4 items, got {c1}"
            assert c2 == 0, f"Removed assessor should have 0 items, got {c2}"

    def test_SCEN_DIST_006_all_mode_skips_reassignment(
        self, rdb, real_app, seed_function_types
    ):
        """In 'all' mode, reassignment is a no-op."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import reassign_items_from_user
            # Should not raise
            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'all'})
            u = _make_user(rdb, 'all_remove')
            su = _add_scenario_user(rdb, scenario.id, u.id, is_assessor=True, role_str='ASSESSOR')
            reassign_items_from_user(scenario.id, scenario, su.id)

    def test_SCEN_DIST_007_no_remaining_assessors_clears_distributions(
        self, rdb, real_app, seed_function_types
    ):
        """If no assessors remain, distributions are deleted."""
        with real_app.app_context():
            from routes.scenarios.scenario_utils import reassign_items_from_user
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'})
            u = _make_user(rdb, 'solo')
            su = _add_scenario_user(rdb, scenario.id, u.id, is_assessor=True, role_str='ASSESSOR')

            items = [_make_item_and_link(rdb, scenario.id, subject=f'S{i}') for i in range(3)]
            for si in items:
                _make_distribution(rdb, scenario.id, su.id, si.id)

            reassign_items_from_user(scenario.id, scenario, su.id)
            rdb.session.commit()

            count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id
            ).count()
            assert count == 0


# =============================================================================
# 3. API Routes — Invite with Distribution + Cache Invalidation
# =============================================================================

class TestInviteWithDistribution:
    """Tests that POST /api/scenarios/<id>/invite creates distributions for round_robin."""

    def test_SCEN_DIST_008_invite_assessor_creates_distribution(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Inviting an assessor to a round_robin scenario assigns items."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            # Admin gets auto-created as OWNER by sm_create, but here we create manually
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            # Create items
            for i in range(4):
                _make_item_and_link(rdb, scenario.id, subject=f'API Item {i}')

            # Create a user to invite
            new_user = _make_user(rdb, 'invited_user', role_name='evaluator')

            response = auth_admin.post(
                f'/api/scenarios/{scenario.id}/invite',
                json={'user_ids': [new_user.id], 'role': 'ASSESSOR'},
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['added'] == 1

            # Check distribution was created (first assessor gets all items)
            su = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=new_user.id
            ).first()
            assert su is not None
            assert su.is_assessor is True

            dist_count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su.id
            ).count()
            assert dist_count == 4, f"First assessor should get all 4 items, got {dist_count}"

    def test_SCEN_DIST_009_invite_viewer_no_distribution(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Inviting a viewer does NOT create any distributions."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            _make_item_and_link(rdb, scenario.id)
            viewer = _make_user(rdb, 'viewer_user', role_name='evaluator')

            response = auth_admin.post(
                f'/api/scenarios/{scenario.id}/invite',
                json={'user_ids': [viewer.id], 'role': 'VIEWER'},
            )
            assert response.status_code == 200

            dist_count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id
            ).count()
            assert dist_count == 0


# =============================================================================
# 4. API Routes — Role Change with Distribution
# =============================================================================

class TestRoleChangeDistribution:
    """Tests that PUT /api/scenarios/<id>/users/<uid>/role triggers distribution changes."""

    def test_SCEN_DIST_010_viewer_to_assessor_assigns_items(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Changing viewer→assessor assigns items via round_robin distribution."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            # Create items
            for i in range(4):
                _make_item_and_link(rdb, scenario.id, subject=f'Role Item {i}')

            # Add a viewer
            user = _make_user(rdb, 'role_change_user', role_name='evaluator')
            _add_scenario_user(rdb, scenario.id, user.id, is_viewer=True, role_str='VIEWER')

            # Change to assessor
            response = auth_admin.put(
                f'/api/scenarios/{scenario.id}/users/{user.id}/role',
                json={'role': 'ASSESSOR'},
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['is_assessor'] is True

            su = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=user.id
            ).first()
            dist_count = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su.id
            ).count()
            # First assessor → gets all items
            assert dist_count == 4

    def test_SCEN_DIST_011_assessor_to_viewer_redistributes(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Changing assessor→viewer redistributes undone items to remaining assessors."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            items = [_make_item_and_link(rdb, scenario.id, subject=f'D{i}') for i in range(6)]

            u1 = _make_user(rdb, 'stays_assessor', role_name='evaluator')
            u2 = _make_user(rdb, 'becomes_viewer', role_name='evaluator')

            su1 = _add_scenario_user(rdb, scenario.id, u1.id,
                                     is_assessor=True, role_str='ASSESSOR')
            su2 = _add_scenario_user(rdb, scenario.id, u2.id,
                                     is_assessor=True, role_str='ASSESSOR')

            # u1 gets 3, u2 gets 3
            for si in items[:3]:
                _make_distribution(rdb, scenario.id, su1.id, si.id)
            for si in items[3:]:
                _make_distribution(rdb, scenario.id, su2.id, si.id)

            # Demote u2 to viewer
            response = auth_admin.put(
                f'/api/scenarios/{scenario.id}/users/{u2.id}/role',
                json={'role': 'VIEWER'},
            )
            assert response.status_code == 200

            # u1 should now have all 6 items
            c1 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su1.id
            ).count()
            c2 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su2.id
            ).count()

            assert c1 == 6, f"Remaining assessor should have 6 items, got {c1}"
            assert c2 == 0, f"Demoted viewer should have 0 items, got {c2}"


# =============================================================================
# 5. API Routes — Remove User with Redistribution
# =============================================================================

class TestRemoveUserRedistribution:
    """Tests that DELETE /api/scenarios/<id>/users/<uid> redistributes items."""

    def test_SCEN_DIST_012_remove_assessor_redistributes(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Archiving an assessor redistributes their items."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            items = [_make_item_and_link(rdb, scenario.id, subject=f'RM{i}') for i in range(4)]

            u1 = _make_user(rdb, 'kept', role_name='evaluator')
            u2 = _make_user(rdb, 'removed', role_name='evaluator')

            su1 = _add_scenario_user(rdb, scenario.id, u1.id,
                                     is_assessor=True, role_str='ASSESSOR')
            su2 = _add_scenario_user(rdb, scenario.id, u2.id,
                                     is_assessor=True, role_str='ASSESSOR')

            for si in items[:2]:
                _make_distribution(rdb, scenario.id, su1.id, si.id)
            for si in items[2:]:
                _make_distribution(rdb, scenario.id, su2.id, si.id)

            response = auth_admin.delete(f'/api/scenarios/{scenario.id}/users/{u2.id}')
            assert response.status_code == 200

            c1 = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su1.id
            ).count()
            assert c1 == 4, f"Remaining assessor should have all items, got {c1}"


# =============================================================================
# 6. Agreement Metrics — Role Filtering
# =============================================================================

class TestAgreementMetricsRoleFilter:
    """Tests that agreement metrics only include active assessors."""

    def test_SCEN_DIST_013_demoted_user_excluded_from_ranking_metrics(
        self, rdb, real_app, seed_function_types
    ):
        """Demoted assessor's rankings are excluded from agreement metrics."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService
            from db.models.scenario import ScenarioUsers, MembershipStatus

            scenario = _make_scenario(rdb, ftype_id=1)  # ranking
            u_active = _make_user(rdb, 'active_ranker')
            u_demoted = _make_user(rdb, 'demoted_ranker')

            su_active = _add_scenario_user(rdb, scenario.id, u_active.id,
                                           is_assessor=True, role_str='ASSESSOR')
            su_demoted = _add_scenario_user(rdb, scenario.id, u_demoted.id,
                                            is_assessor=False, is_viewer=True,
                                            role_str='VIEWER')

            # Create item + features + rankings
            si = _make_item_and_link(rdb, scenario.id, subject='Rank Item')
            f1 = _create_feature(rdb, si.item_id, content='Feature 1')

            _create_ranking(rdb, u_active.id, f1.feature_id, bucket='gut')
            _create_ranking(rdb, u_demoted.id, f1.feature_id, bucket='schlecht')

            # Collect evaluations — should only include active assessor
            evals = AgreementMetricsService._collect_evaluations(
                scenario_id=scenario.id,
                task_type='ranking',
                include_llm=False,
                include_human=True,
            )

            human_raters = [r for r in evals['raters'] if r.startswith('human:')]
            assert len(human_raters) == 1, f"Expected 1 active rater, got {human_raters}"
            assert f'human:{u_active.id}' in human_raters
            assert f'human:{u_demoted.id}' not in human_raters

    def test_SCEN_DIST_014_demoted_user_excluded_from_rating_metrics(
        self, rdb, real_app, seed_function_types
    ):
        """Demoted assessor's ratings are excluded from agreement metrics."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService
            from db.models.scenario import UserFeatureRating, Feature

            scenario = _make_scenario(rdb, ftype_id=2)  # rating
            u_active = _make_user(rdb, 'active_rater')
            u_demoted = _make_user(rdb, 'demoted_rater')

            _add_scenario_user(rdb, scenario.id, u_active.id,
                               is_assessor=True, role_str='ASSESSOR')
            _add_scenario_user(rdb, scenario.id, u_demoted.id,
                               is_assessor=False, is_viewer=True, role_str='VIEWER')

            si = _make_item_and_link(rdb, scenario.id, subject='Rate Item')
            f1 = _create_feature(rdb, si.item_id, content='Rate Feature')

            # Create ratings for both users
            for uid in [u_active.id, u_demoted.id]:
                rdb.session.add(UserFeatureRating(
                    user_id=uid,
                    feature_id=f1.feature_id,
                    rating_content=4,
                ))
            rdb.session.commit()

            evals = AgreementMetricsService._collect_evaluations(
                scenario_id=scenario.id,
                task_type='rating',
                include_llm=False,
                include_human=True,
            )

            human_raters = [r for r in evals['raters'] if r.startswith('human:')]
            assert len(human_raters) == 1
            assert f'human:{u_active.id}' in human_raters
            assert f'human:{u_demoted.id}' not in human_raters

    def test_SCEN_DIST_015_active_assessor_user_ids_helper(
        self, rdb, real_app, seed_function_types
    ):
        """_get_active_assessor_user_ids returns correct set."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService
            from db.models.scenario import MembershipStatus

            scenario = _make_scenario(rdb)
            u1 = _make_user(rdb, 'a1')
            u2 = _make_user(rdb, 'a2')
            u3 = _make_user(rdb, 'v1')

            _add_scenario_user(rdb, scenario.id, u1.id, is_assessor=True, role_str='ASSESSOR')
            _add_scenario_user(rdb, scenario.id, u2.id, is_assessor=True, role_str='ASSESSOR')
            _add_scenario_user(rdb, scenario.id, u3.id, is_assessor=False, is_viewer=True,
                               role_str='VIEWER')

            ids = AgreementMetricsService._get_active_assessor_user_ids(scenario.id)
            assert ids == {u1.id, u2.id}


# =============================================================================
# 7. Owner as Assessor — Scenario Creation
# =============================================================================

class TestOwnerAsAssessor:
    """Tests for the owner_as_assessor flag in scenario creation."""

    def test_SCEN_DIST_016_create_scenario_owner_as_viewer_default(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """By default, owner is created as viewer (is_assessor=False)."""
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers

            response = auth_admin.post('/api/scenarios', json={
                'scenario_name': 'Default Owner',
                'function_type_id': 1,
            })
            assert response.status_code == 201
            data = response.get_json()
            sid = data['scenario']['id']

            owner_su = ScenarioUsers.query.filter_by(
                scenario_id=sid, access_level='OWNER'
            ).first()
            assert owner_su is not None
            assert owner_su.is_assessor is False
            assert owner_su.is_viewer is True

    def test_SCEN_DIST_017_create_scenario_owner_as_assessor(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """With owner_as_assessor=true, owner starts as assessor."""
        with real_app.app_context():
            from db.models.scenario import ScenarioUsers

            response = auth_admin.post('/api/scenarios', json={
                'scenario_name': 'Assessor Owner',
                'function_type_id': 1,
                'owner_as_assessor': True,
            })
            assert response.status_code == 201
            data = response.get_json()
            sid = data['scenario']['id']

            owner_su = ScenarioUsers.query.filter_by(
                scenario_id=sid, access_level='OWNER'
            ).first()
            assert owner_su is not None
            assert owner_su.is_assessor is True
            assert owner_su.is_viewer is False


# =============================================================================
# 8. End-to-End: Full Workflow
# =============================================================================

class TestEndToEndWorkflow:
    """Full workflow: create scenario → add assessors → change roles → verify metrics."""

    def test_SCEN_DIST_018_full_round_robin_lifecycle(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Full lifecycle: create → add items → invite assessors → redistribute on remove.

        Note: Items must exist BEFORE inviting assessors, because distribution
        only happens during invite/role-change, not at item-creation time.
        The scenario creation API does NOT auto-distribute items (items come later
        via import). Distribution kicks in when users are added as assessors.
        """
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers

            # 1. Create round_robin scenario (owner as viewer default)
            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')
            sid = scenario.id

            # 2. Add items first
            items = [_make_item_and_link(rdb, sid, subject=f'E2E {i}') for i in range(6)]

            # 3. Invite 1st assessor — gets all 6 items
            u1 = _make_user(rdb, 'e2e_assessor1', role_name='evaluator')
            resp = auth_admin.post(f'/api/scenarios/{sid}/invite',
                                   json={'user_ids': [u1.id], 'role': 'ASSESSOR'})
            assert resp.status_code == 200

            su1 = ScenarioUsers.query.filter_by(scenario_id=sid, user_id=u1.id).first()
            total = ScenarioItemDistribution.query.filter_by(scenario_id=sid).count()
            assert total == 6, f"First assessor should get all 6 items, got {total}"

            # 4. Invite 2nd assessor — should get 3 items (6/2)
            u2 = _make_user(rdb, 'e2e_assessor2', role_name='evaluator')
            resp = auth_admin.post(f'/api/scenarios/{sid}/invite',
                                   json={'user_ids': [u2.id], 'role': 'ASSESSOR'})
            assert resp.status_code == 200

            su2 = ScenarioUsers.query.filter_by(scenario_id=sid, user_id=u2.id).first()
            total = ScenarioItemDistribution.query.filter_by(scenario_id=sid).count()
            assert total == 6, f"Total should still be 6, got {total}"

            # 5. Invite 3rd assessor — should get 2 items (6/3)
            u3 = _make_user(rdb, 'e2e_assessor3', role_name='evaluator')
            resp = auth_admin.post(f'/api/scenarios/{sid}/invite',
                                   json={'user_ids': [u3.id], 'role': 'ASSESSOR'})
            assert resp.status_code == 200

            total = ScenarioItemDistribution.query.filter_by(scenario_id=sid).count()
            assert total == 6, f"Total should still be 6, got {total}"

            # 6. Remove u2 — items redistributed to u1 and u3
            resp = auth_admin.delete(f'/api/scenarios/{sid}/users/{u2.id}')
            assert resp.status_code == 200

            c2 = ScenarioItemDistribution.query.filter_by(
                scenario_id=sid, scenario_user_id=su2.id
            ).count()
            assert c2 == 0, f"Removed user should have 0 items, got {c2}"

            total = ScenarioItemDistribution.query.filter_by(scenario_id=sid).count()
            assert total == 6, f"Total should still be 6, got {total}"

    def test_SCEN_DIST_020_invite_second_assessor_splits_items(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """Inviting a 2nd assessor splits existing assessor's items proportionally."""
        with real_app.app_context():
            from db.models.scenario import ScenarioItemDistribution, ScenarioUsers
            from routes.scenarios.scenario_utils import assign_items_to_new_assessor

            scenario = _make_scenario(rdb, config_json={'distribution_mode': 'round_robin'},
                                      created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            items = [_make_item_and_link(rdb, scenario.id, subject=f'Split {i}') for i in range(10)]

            # First assessor via invite gets all 10
            u1 = _make_user(rdb, 'split_a', role_name='evaluator')
            resp = auth_admin.post(f'/api/scenarios/{scenario.id}/invite',
                                   json={'user_ids': [u1.id], 'role': 'ASSESSOR'})
            assert resp.status_code == 200

            su1 = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=u1.id
            ).first()
            c1_before = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su1.id
            ).count()
            assert c1_before == 10

            # Second assessor should get 5 items (10 / 2)
            u2 = _make_user(rdb, 'split_b', role_name='evaluator')
            resp = auth_admin.post(f'/api/scenarios/{scenario.id}/invite',
                                   json={'user_ids': [u2.id], 'role': 'ASSESSOR'})
            assert resp.status_code == 200

            su2 = ScenarioUsers.query.filter_by(
                scenario_id=scenario.id, user_id=u2.id
            ).first()
            c1_after = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su1.id
            ).count()
            c2_after = ScenarioItemDistribution.query.filter_by(
                scenario_id=scenario.id, scenario_user_id=su2.id
            ).count()

            assert c1_after == 5, f"First assessor should keep 5, got {c1_after}"
            assert c2_after == 5, f"Second assessor should get 5, got {c2_after}"
            assert c1_after + c2_after == 10


# =============================================================================
# 9. Read-Only / can_evaluate — Role Switch Correctness
# =============================================================================

class TestReadonlyOnRoleSwitch:
    """Tests that readonly (can_evaluate) switches correctly on role changes.

    The chain is:
    - Backend: user_can_evaluate() checks is_assessor + membership_status
    - Backend: session_service returns can_evaluate in session data
    - Frontend: uses can_evaluate to show viewer-banner and disable buttons
    """

    def test_SCEN_DIST_021_assessor_can_evaluate(
        self, rdb, real_app, seed_function_types
    ):
        """Active assessor has can_evaluate=True."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate

            scenario = _make_scenario(rdb)
            user = _make_user(rdb, 'eval_yes')
            _add_scenario_user(rdb, scenario.id, user.id,
                               is_assessor=True, role_str='ASSESSOR')

            assert user_can_evaluate(user.id, scenario.id) is True

    def test_SCEN_DIST_022_viewer_cannot_evaluate(
        self, rdb, real_app, seed_function_types
    ):
        """Viewer (is_assessor=False) has can_evaluate=False."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate

            scenario = _make_scenario(rdb)
            user = _make_user(rdb, 'eval_no')
            _add_scenario_user(rdb, scenario.id, user.id,
                               is_assessor=False, is_viewer=True, role_str='VIEWER')

            assert user_can_evaluate(user.id, scenario.id) is False

    def test_SCEN_DIST_023_role_change_assessor_to_viewer_switches_readonly(
        self, rdb, real_app, seed_function_types
    ):
        """When user is demoted from assessor to viewer, can_evaluate flips to False."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate
            from db.models.scenario import ScenarioUsers, ScenarioRoles

            scenario = _make_scenario(rdb)
            user = _make_user(rdb, 'switch_off')
            su = _add_scenario_user(rdb, scenario.id, user.id,
                                    is_assessor=True, role_str='ASSESSOR')

            # Before: can evaluate
            assert user_can_evaluate(user.id, scenario.id) is True

            # Demote to viewer (same as sm_update_user_role does)
            su.is_assessor = False
            su.is_viewer = True
            su.evaluation_role = 'none'
            su.manager_role = 'viewer'
            su.role = ScenarioRoles.VIEWER
            rdb.session.commit()

            # After: cannot evaluate
            assert user_can_evaluate(user.id, scenario.id) is False

    def test_SCEN_DIST_024_role_change_viewer_to_assessor_enables_evaluation(
        self, rdb, real_app, seed_function_types
    ):
        """When user is promoted from viewer to assessor, can_evaluate flips to True."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate
            from db.models.scenario import ScenarioUsers, ScenarioRoles

            scenario = _make_scenario(rdb)
            user = _make_user(rdb, 'switch_on')
            su = _add_scenario_user(rdb, scenario.id, user.id,
                                    is_assessor=False, is_viewer=True, role_str='VIEWER')

            # Before: cannot evaluate
            assert user_can_evaluate(user.id, scenario.id) is False

            # Promote to assessor
            su.is_assessor = True
            su.is_viewer = False
            su.evaluation_role = 'assessor'
            su.manager_role = 'none'
            su.role = ScenarioRoles.ASSESSOR
            rdb.session.commit()

            # After: can evaluate
            assert user_can_evaluate(user.id, scenario.id) is True

    def test_SCEN_DIST_025_archived_user_cannot_evaluate(
        self, rdb, real_app, seed_function_types
    ):
        """Archived user cannot evaluate even if is_assessor was True."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate
            from db.models.scenario import MembershipStatus

            scenario = _make_scenario(rdb)
            user = _make_user(rdb, 'archived_user')
            su = _add_scenario_user(rdb, scenario.id, user.id,
                                    is_assessor=True, role_str='ASSESSOR')

            assert user_can_evaluate(user.id, scenario.id) is True

            # Archive the user (sm_remove_user sets is_assessor=False + ARCHIVED)
            su.membership_status = MembershipStatus.ARCHIVED
            rdb.session.commit()

            assert user_can_evaluate(user.id, scenario.id) is False

    def test_SCEN_DIST_026_session_service_can_evaluate_matches(
        self, rdb, real_app, seed_function_types
    ):
        """Session service returns can_evaluate consistent with user_can_evaluate()."""
        with real_app.app_context():
            from services.evaluation.session_service import EvaluationSessionService
            from db.models.scenario import ScenarioRoles

            scenario = _make_scenario(rdb)
            assessor = _make_user(rdb, 'session_assessor')
            viewer = _make_user(rdb, 'session_viewer')

            _add_scenario_user(rdb, scenario.id, assessor.id,
                               is_assessor=True, role_str='ASSESSOR')
            _add_scenario_user(rdb, scenario.id, viewer.id,
                               is_assessor=False, is_viewer=True, role_str='VIEWER')

            # Create at least one item so session loads
            _make_item_and_link(rdb, scenario.id)

            # Assessor: can_evaluate=True
            session_a = EvaluationSessionService.get_session_data(scenario.id, assessor.id)
            assert session_a['scenario']['can_evaluate'] is True

            # Viewer: can_evaluate=False
            session_v = EvaluationSessionService.get_session_data(scenario.id, viewer.id)
            assert session_v['scenario']['can_evaluate'] is False

    def test_SCEN_DIST_027_role_change_via_api_updates_can_evaluate(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """PUT /role API updates is_assessor so can_evaluate changes in session."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate
            from services.evaluation.session_service import EvaluationSessionService

            scenario = _make_scenario(rdb, created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            user = _make_user(rdb, 'api_role_switch', role_name='evaluator')
            _add_scenario_user(rdb, scenario.id, user.id,
                               is_assessor=True, role_str='ASSESSOR')
            _make_item_and_link(rdb, scenario.id)

            # Before: can evaluate
            assert user_can_evaluate(user.id, scenario.id) is True
            session = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert session['scenario']['can_evaluate'] is True

            # Demote via API
            resp = auth_admin.put(
                f'/api/scenarios/{scenario.id}/users/{user.id}/role',
                json={'role': 'VIEWER'},
            )
            assert resp.status_code == 200
            assert resp.get_json()['is_assessor'] is False

            # After: cannot evaluate
            assert user_can_evaluate(user.id, scenario.id) is False
            session = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert session['scenario']['can_evaluate'] is False

            # Promote back via API
            resp = auth_admin.put(
                f'/api/scenarios/{scenario.id}/users/{user.id}/role',
                json={'role': 'ASSESSOR'},
            )
            assert resp.status_code == 200
            assert resp.get_json()['is_assessor'] is True

            # Re-enabled
            assert user_can_evaluate(user.id, scenario.id) is True
            session = EvaluationSessionService.get_session_data(scenario.id, user.id)
            assert session['scenario']['can_evaluate'] is True

    def test_SCEN_DIST_028_remove_user_api_blocks_evaluation(
        self, auth_admin, rdb, real_app, seed_function_types, radmin
    ):
        """DELETE user (archive) blocks can_evaluate even though is_assessor was True."""
        with real_app.app_context():
            from routes.HelperFunctions import user_can_evaluate

            scenario = _make_scenario(rdb, created_by='admin')
            _add_scenario_user(rdb, scenario.id, radmin.id,
                               access_level='OWNER', is_viewer=True, role_str='OWNER')

            user = _make_user(rdb, 'removed_eval', role_name='evaluator')
            _add_scenario_user(rdb, scenario.id, user.id,
                               is_assessor=True, role_str='ASSESSOR')

            assert user_can_evaluate(user.id, scenario.id) is True

            # Archive via API
            resp = auth_admin.delete(f'/api/scenarios/{scenario.id}/users/{user.id}')
            assert resp.status_code == 200

            # Archived → cannot evaluate
            assert user_can_evaluate(user.id, scenario.id) is False


# =============================================================================
# 10. Golden-Value Agreement Metrics — Ranking
# =============================================================================

class TestGoldenValueRankingMetrics:
    """Golden-value tests for ranking agreement metrics.

    Uses hand-calculated expected values to verify metric correctness
    and ensure role changes produce predictable metric shifts.

    Dataset: 3 raters (A, B, C), 4 features, bucket-ranking.
    Ordinal mapping: gut=3, mittel=2, neutral=1, schlecht=0.

    | Feature | Rater A | Rater B | Rater C | Ordinal |
    |---------|---------|---------|---------|---------|
    | F1      | gut     | gut     | mittel  | 3,3,2   |
    | F2      | schlecht| schlecht| schlecht| 0,0,0   |
    | F3      | mittel  | neutral | mittel  | 2,1,2   |
    | F4      | gut     | gut     | gut     | 3,3,3   |
    """

    @staticmethod
    def _setup_ranking_scenario(rdb, real_app):
        """Create 3-rater ranking scenario with golden dataset.

        Returns (scenario, raters, scenario_users, features) tuple.
        """
        scenario = _make_scenario(rdb, ftype_id=1)
        raters = [
            _make_user(rdb, 'gv_rank_a'),
            _make_user(rdb, 'gv_rank_b'),
            _make_user(rdb, 'gv_rank_c'),
        ]
        scenario_users = [
            _add_scenario_user(rdb, scenario.id, u.id,
                               is_assessor=True, role_str='ASSESSOR')
            for u in raters
        ]

        # 4 items, 1 feature each
        features = []
        for i in range(4):
            si = _make_item_and_link(rdb, scenario.id, subject=f'GV Rank {i}')
            features.append(
                _create_feature(rdb, si.item_id, content=f'GV Feature {i}')
            )

        # Ranking assignments per feature
        bucket_matrix = [
            ['gut', 'gut', 'mittel'],       # F1: 3,3,2
            ['schlecht', 'schlecht', 'schlecht'],  # F2: 0,0,0
            ['mittel', 'neutral', 'mittel'],  # F3: 2,1,2
            ['gut', 'gut', 'gut'],            # F4: 3,3,3
        ]
        for fi, buckets in enumerate(bucket_matrix):
            for user, bucket in zip(raters, buckets):
                _create_ranking(rdb, user.id, features[fi].feature_id,
                                bucket=bucket)

        return scenario, raters, scenario_users, features

    def test_SCEN_DIST_029_three_raters_metrics_exist(
        self, rdb, real_app, seed_function_types
    ):
        """3 raters, 4 features — all expected ranking metrics are returned."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService

            scenario, _, _, _ = self._setup_ranking_scenario(rdb, real_app)

            result = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )

            assert 'error' not in result
            m = result['metrics']
            assert result['rater_count'] == 3

            # All expected metrics exist and are in valid ranges
            for key in ('krippendorff_alpha', 'fleiss_kappa', 'percent_agreement',
                        'spearman_rho', 'kendall_w'):
                assert key in m, f"Missing metric: {key}"
                assert -1.0 <= m[key]['value'] <= 100.0

            # Cohen κ only for exactly 2 raters
            assert 'cohens_kappa' not in m

    def test_SCEN_DIST_030_rater_degraded_metrics_shift(
        self, rdb, real_app, seed_function_types
    ):
        """Rater C degraded to viewer → only A+B → metrics improve (more agreement)."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService
            from db.models.scenario import ScenarioRoles

            scenario, raters, sus, _ = self._setup_ranking_scenario(rdb, real_app)

            # --- Before: 3 raters ---
            before = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )
            m_before = before['metrics']
            assert before['rater_count'] == 3

            # --- Degrade rater C to viewer ---
            sus[2].is_assessor = False
            sus[2].is_viewer = True
            sus[2].evaluation_role = 'none'
            sus[2].manager_role = 'viewer'
            sus[2].role = ScenarioRoles.VIEWER
            rdb.session.commit()

            # --- After: 2 raters (A+B) ---
            after = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )
            m_after = after['metrics']
            assert after['rater_count'] == 2

            # Direction checks: remaining raters agree more → metrics improve
            assert m_after['krippendorff_alpha']['value'] > m_before['krippendorff_alpha']['value']
            assert m_after['percent_agreement']['value'] > m_before['percent_agreement']['value']

            # Structural: Cohen κ appears only for exactly 2 raters
            assert 'cohens_kappa' not in m_before
            assert 'cohens_kappa' in m_after


# =============================================================================
# 11. Golden-Value Agreement Metrics — Rating
# =============================================================================

class TestGoldenValueRatingMetrics:
    """Golden-value tests for numeric rating agreement metrics.

    Rating uses _calculate_numeric_metrics (fallback when no dimensional
    config is set). Does NOT include Fleiss κ (only ranking does).

    Dataset: 2 raters (A, B), 5 items, scale 1-5.

    | Item | Rater A | Rater B |
    |------|---------|---------|
    | I1   | 5       | 5       |
    | I2   | 4       | 3       |
    | I3   | 2       | 2       |
    | I4   | 1       | 3       |
    | I5   | 3       | 3       |
    """

    @staticmethod
    def _setup_rating_scenario(rdb, n_raters=2):
        """Create rating scenario with 2 or 3 raters.

        Base ratings for A and B are always the same.
        Rater C (if n_raters=3) gets values [5, 4, 2, 2, 3].

        Returns (scenario, raters, scenario_users, features) tuple.
        """
        scenario = _make_scenario(rdb, ftype_id=2)  # rating

        raters = [
            _make_user(rdb, 'gv_rate_a'),
            _make_user(rdb, 'gv_rate_b'),
        ]
        if n_raters >= 3:
            raters.append(_make_user(rdb, 'gv_rate_c'))

        scenario_users = [
            _add_scenario_user(rdb, scenario.id, u.id,
                               is_assessor=True, role_str='ASSESSOR')
            for u in raters
        ]

        # 5 items, 1 feature each
        features = []
        for i in range(5):
            si = _make_item_and_link(rdb, scenario.id, subject=f'GV Rate {i}')
            features.append(
                _create_feature(rdb, si.item_id, content=f'GV Rate Feature {i}')
            )

        # Rating values per item
        a_ratings = [5, 4, 2, 1, 3]
        b_ratings = [5, 3, 2, 3, 3]
        c_ratings = [5, 4, 2, 2, 3]

        for i, f in enumerate(features):
            _create_rating(rdb, raters[0].id, f.feature_id, a_ratings[i])
            _create_rating(rdb, raters[1].id, f.feature_id, b_ratings[i])
            if n_raters >= 3:
                _create_rating(rdb, raters[2].id, f.feature_id, c_ratings[i])

        return scenario, raters, scenario_users, features

    def test_SCEN_DIST_031_two_raters_metrics_exist(
        self, rdb, real_app, seed_function_types
    ):
        """2 raters, 5 items — all expected rating metrics are returned."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService

            scenario, _, _, _ = self._setup_rating_scenario(rdb, n_raters=2)

            result = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )

            assert 'error' not in result
            m = result['metrics']
            assert result['rater_count'] == 2

            # All expected metrics exist and are in valid ranges
            for key in ('krippendorff_alpha', 'cohens_kappa', 'percent_agreement',
                        'spearman_rho', 'kendall_w'):
                assert key in m, f"Missing metric: {key}"
                assert -1.0 <= m[key]['value'] <= 100.0

            # Rating path does not include Fleiss κ
            assert 'fleiss_kappa' not in m

    def test_SCEN_DIST_032_rater_added_metrics_shift(
        self, rdb, real_app, seed_function_types
    ):
        """Adding agreeable rater C improves agreement metrics."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService

            # Start with 2 raters, capture before-metrics
            scenario = _make_scenario(rdb, ftype_id=2)
            rater_a = _make_user(rdb, 'gv_shift_a')
            rater_b = _make_user(rdb, 'gv_shift_b')

            for u in [rater_a, rater_b]:
                _add_scenario_user(rdb, scenario.id, u.id,
                                   is_assessor=True, role_str='ASSESSOR')

            features = []
            for i in range(5):
                si = _make_item_and_link(rdb, scenario.id, subject=f'GV Shift {i}')
                features.append(
                    _create_feature(rdb, si.item_id, content=f'GV Shift F{i}')
                )

            a_ratings = [5, 4, 2, 1, 3]
            b_ratings = [5, 3, 2, 3, 3]
            for i, f in enumerate(features):
                _create_rating(rdb, rater_a.id, f.feature_id, a_ratings[i])
                _create_rating(rdb, rater_b.id, f.feature_id, b_ratings[i])

            before = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )
            m_before = before['metrics']
            assert before['rater_count'] == 2

            # --- Add rater C (agrees more with A) ---
            rater_c = _make_user(rdb, 'gv_shift_c')
            _add_scenario_user(rdb, scenario.id, rater_c.id,
                               is_assessor=True, role_str='ASSESSOR')
            c_ratings = [5, 4, 2, 2, 3]
            for i, f in enumerate(features):
                _create_rating(rdb, rater_c.id, f.feature_id, c_ratings[i])

            # --- After: 3 raters ---
            after = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )
            m_after = after['metrics']
            assert after['rater_count'] == 3

            # Direction checks: adding an agreeable rater improves metrics
            assert m_after['krippendorff_alpha']['value'] > m_before['krippendorff_alpha']['value']
            assert m_after['percent_agreement']['value'] > m_before['percent_agreement']['value']

            # Structural: Cohen κ disappears with 3 raters
            assert 'cohens_kappa' in m_before
            assert 'cohens_kappa' not in m_after


# =============================================================================
# 12. Golden-Value Boundary Conditions
# =============================================================================

class TestGoldenValueBoundaryConditions:
    """Boundary condition tests for agreement metrics.

    Covers perfect agreement, single-rater edge case, and
    all-assessors-degraded scenario.
    """

    def test_SCEN_DIST_033_perfect_agreement(
        self, rdb, real_app, seed_function_types
    ):
        """Perfect agreement: 2 raters, identical buckets → all metrics at maximum."""
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService

            scenario = _make_scenario(rdb, ftype_id=1)  # ranking
            u1 = _make_user(rdb, 'perf_a')
            u2 = _make_user(rdb, 'perf_b')

            for u in [u1, u2]:
                _add_scenario_user(rdb, scenario.id, u.id,
                                   is_assessor=True, role_str='ASSESSOR')

            # 3 features with identical rankings
            buckets = ['gut', 'mittel', 'schlecht']
            for i, bucket in enumerate(buckets):
                si = _make_item_and_link(rdb, scenario.id, subject=f'Perf {i}')
                f = _create_feature(rdb, si.item_id, content=f'Perf F{i}')
                _create_ranking(rdb, u1.id, f.feature_id, bucket=bucket)
                _create_ranking(rdb, u2.id, f.feature_id, bucket=bucket)

            result = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )

            assert 'error' not in result
            m = result['metrics']

            # Perfect agreement → all metrics should be at or near maximum
            assert m['percent_agreement']['value'] >= 99.0
            for key in ('krippendorff_alpha', 'cohens_kappa', 'spearman_rho', 'kendall_w'):
                assert m[key]['value'] >= 0.99, f"{key} should be ~1.0 for perfect agreement"

    def test_SCEN_DIST_034_single_rater_no_meaningful_metrics(
        self, rdb, real_app, seed_function_types
    ):
        """Single active assessor → not enough raters for agreement metrics.

        With only 1 rater, no feature has ≥2 raters → metric calculation
        returns an error indicating insufficient data.
        """
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService

            scenario = _make_scenario(rdb, ftype_id=1)
            solo = _make_user(rdb, 'solo_rater')
            _add_scenario_user(rdb, scenario.id, solo.id,
                               is_assessor=True, role_str='ASSESSOR')

            # Create features and rankings for solo rater
            for i in range(3):
                si = _make_item_and_link(rdb, scenario.id, subject=f'Solo {i}')
                f = _create_feature(rdb, si.item_id, content=f'Solo F{i}')
                _create_ranking(rdb, solo.id, f.feature_id,
                                bucket=['gut', 'mittel', 'schlecht'][i])

            result = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )

            # 1 rater found, but metrics can't be computed
            assert result['rater_count'] == 1
            assert 'error' in result['metrics']

    def test_SCEN_DIST_035_all_assessors_degraded_no_evaluations(
        self, rdb, real_app, seed_function_types
    ):
        """All 3 assessors degraded to viewer → no evaluations collected.

        Active assessor set is empty → _collect_evaluations returns
        no raters → calculate_all_metrics returns top-level error.
        """
        with real_app.app_context():
            from services.evaluation.agreement_metrics_service import AgreementMetricsService
            from db.models.scenario import ScenarioRoles

            scenario = _make_scenario(rdb, ftype_id=1)
            users = [_make_user(rdb, f'deg_{i}') for i in range(3)]
            sus = [
                _add_scenario_user(rdb, scenario.id, u.id,
                                   is_assessor=True, role_str='ASSESSOR')
                for u in users
            ]

            # Create features with rankings from all 3
            for i in range(3):
                si = _make_item_and_link(rdb, scenario.id, subject=f'Deg {i}')
                f = _create_feature(rdb, si.item_id, content=f'Deg F{i}')
                for u in users:
                    _create_ranking(rdb, u.id, f.feature_id, bucket='gut')

            # Degrade all to viewer
            for su in sus:
                su.is_assessor = False
                su.is_viewer = True
                su.evaluation_role = 'none'
                su.manager_role = 'viewer'
                su.role = ScenarioRoles.VIEWER
            rdb.session.commit()

            result = AgreementMetricsService.calculate_all_metrics(
                scenario.id, include_llm=False, include_human=True,
            )

            # Top-level error: no raters found at all
            assert result == {"error": "No evaluations found"}
