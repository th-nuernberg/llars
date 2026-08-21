"""
Tests for Scenario Parts (Teile/Phasen für Labeling-Szenarien).

Covers the study-critical mechanics from the design doc
(.claude/plans/scenario-parts-design.md):
- Pydantic PartsConfig validation (duplicate ids, spec-less middle parts)
- opt-in: no parts / disabled / unresolved => feature inactive
- spec resolution (size boundaries in upload order, external ids via chat_id)
- partition invariant (duplicates, foreign ids, unassigned items)
- session delivery: sequential ordering identical across users, deterministic
  per-user random shuffle, locked-part filtering (assessor vs. manager)
- assessor invisibility: parts/copilot stripped from delivered config
- copilot gating per part (suggestions, log 'shown', runner scope, status)
- export 'part' column + agreement metrics ?part= filter
- owner API primitives (update_part, append_items_to_part)
- v1 one-shot create roundtrip at service level

Test IDs: [PARTS_001] through [PARTS_024]
"""

import hashlib

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# Helpers
# =============================================================================

def _create_function_type(db, name='labeling', ftype_id=7):
    from db.models.scenario import FeatureFunctionType
    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db.session.add(ftype)
    db.session.flush()
    return ftype


def _create_user(db, username='parts_user'):
    from db.models.user import User
    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def _labeling_inner_config(parts=None, copilot=None):
    inner = {
        'categories': [
            {'id': 'disclosure', 'name': {'de': 'Disclosure'}},
            {'id': 'edification', 'name': {'de': 'Edification'}},
        ],
        'allowUnsure': True,
    }
    if parts is not None:
        inner['parts'] = parts
    if copilot is not None:
        inner['copilot'] = copilot
    return inner


def _scenario_config(parts=None, copilot=None):
    """Wizard-style nesting: eval_config.config holds the labeling config."""
    return {'eval_config': {'type': 'labeling',
                            'config': _labeling_inner_config(parts, copilot)}}


def _create_scenario(db, config_json=None, name='Parts Scenario', created_by='creator'):
    from db.models.scenario import RatingScenarios
    _create_function_type(db)
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=7,
        config_json=config_json if config_json is not None else _scenario_config(),
        created_by=created_by,
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario


def _create_items(db, scenario, count, chat_id_start=1000):
    from db.models.scenario import EvaluationItem, ScenarioThreads
    items = []
    for i in range(count):
        item = EvaluationItem(subject=f'Item {i + 1}', chat_id=chat_id_start + i)
        db.session.add(item)
        db.session.flush()
        db.session.add(ScenarioThreads(scenario_id=scenario.id, thread_id=item.item_id))
        items.append(item)
    db.session.flush()
    return items


def _add_assessor(db, scenario, user):
    from db.models.scenario import (
        ScenarioUsers, ScenarioRoles, InvitationStatus, MembershipStatus,
    )
    su = ScenarioUsers(
        scenario_id=scenario.id, user_id=user.id, role=ScenarioRoles.ASSESSOR,
        access_level='MEMBER', is_assessor=True, is_viewer=False,
        manager_role='none', evaluation_role='assessor',
        invitation_status=InvitationStatus.ACCEPTED,
        membership_status=MembershipStatus.ACTIVE,
    )
    db.session.add(su)
    db.session.flush()
    return su


def _parts_config(part_specs, enabled=True):
    """part_specs: list of dicts merged over sensible defaults."""
    parts = []
    for idx, spec in enumerate(part_specs):
        part = {'id': f'p{idx + 1}', 'name': f'Teil {idx + 1}',
                'order': 'sequential', 'copilot': False, 'locked': False}
        part.update(spec)
        parts.append(part)
    return {'enabled': enabled, 'list': parts}


def _resolved_three_part_scenario(db, sizes=(4, 3), copilot=None, locked=(False, True, True),
                                  part_copilot=(False, False, True), item_count=10):
    """Standard fixture: 10 items, parts p1(4)/p2(3)/p3(rest=3)."""
    from services.evaluation.scenario_parts_service import ScenarioPartsService
    parts = _parts_config([
        {'size': sizes[0], 'locked': locked[0], 'copilot': part_copilot[0]},
        {'size': sizes[1], 'locked': locked[1], 'copilot': part_copilot[1]},
        {'locked': locked[2], 'copilot': part_copilot[2]},
    ])
    scenario = _create_scenario(db, _scenario_config(parts=parts, copilot=copilot))
    items = _create_items(db, scenario, item_count)
    assert ScenarioPartsService.resolve_specs(scenario) is True
    db.session.flush()
    return scenario, items


# =============================================================================
# Pydantic schema validation
# =============================================================================

class TestPartsConfigSchema:
    def test_PARTS_001_valid_config_accepted(self):
        from schemas.evaluation_data_schemas import PartsConfig
        cfg = PartsConfig(enabled=True, list=[
            {'id': 'p1', 'size': 100},
            {'id': 'p2', 'size': 50},
            {'id': 'p3'},
        ])
        assert len(cfg.list) == 3
        assert cfg.list[0].order == 'sequential'

    def test_PARTS_002_duplicate_ids_rejected(self):
        from pydantic import ValidationError
        from schemas.evaluation_data_schemas import PartsConfig
        with pytest.raises(ValidationError, match='duplicate part id'):
            PartsConfig(enabled=True, list=[
                {'id': 'p1', 'size': 10}, {'id': 'p1'},
            ])

    def test_PARTS_003_specless_middle_part_rejected(self):
        from pydantic import ValidationError
        from schemas.evaluation_data_schemas import PartsConfig
        with pytest.raises(ValidationError, match='only the last part'):
            PartsConfig(enabled=True, list=[
                {'id': 'p1'}, {'id': 'p2', 'size': 10},
            ])

    def test_PARTS_004_labeling_config_accepts_parts(self):
        from schemas.evaluation_data_schemas import LabelingConfig
        cfg = LabelingConfig(
            mode='single',
            labels=[{'id': 'a', 'label': {'de': 'A', 'en': 'A'}}],
            parts={'enabled': True, 'list': [{'size': 2}, {}]},
        )
        assert cfg.parts.enabled is True


# =============================================================================
# Opt-in / resolution state
# =============================================================================

class TestOptIn:
    def test_PARTS_005_no_parts_means_inactive(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            scenario = _create_scenario(db)
            _create_items(db, scenario, 3)
            assert ScenarioPartsService.get_parts_config(scenario) is None
            assert ScenarioPartsService.get_active_parts(scenario) is None
            assert ScenarioPartsService.open_item_ids(scenario) is None
            assert ScenarioPartsService.copilot_item_ids(scenario) is None
            assert ScenarioPartsService.item_part_map(scenario) == {}
            assert ScenarioPartsService.session_item_order(
                scenario, 1, [1, 2, 3]) is None

    def test_PARTS_006_disabled_or_unresolved_means_inactive(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            disabled = _create_scenario(
                db, _scenario_config(parts=_parts_config([{'size': 2}, {}], enabled=False)))
            assert ScenarioPartsService.get_parts_config(disabled) is None

            unresolved = _create_scenario(
                db, _scenario_config(parts=_parts_config([{'size': 2}, {}])))
            _create_items(db, unresolved, 3)
            # enabled, but specs not resolved yet -> behaves inactive
            assert ScenarioPartsService.get_parts_config(unresolved) is not None
            assert ScenarioPartsService.get_active_parts(unresolved) is None


# =============================================================================
# Spec resolution + partition invariant
# =============================================================================

class TestResolution:
    def test_PARTS_007_sizes_resolve_in_upload_order_with_rest(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db)
            parts = ScenarioPartsService.get_active_parts(scenario)
            ids = [it.item_id for it in items]
            assert parts[0]['item_ids'] == ids[:4]
            assert parts[1]['item_ids'] == ids[4:7]
            assert parts[2]['item_ids'] == ids[7:]
            # size specs are consumed on resolution
            assert all('size' not in p for p in parts)
            # second call is a no-op
            assert ScenarioPartsService.resolve_specs(scenario) is False

    def test_PARTS_008_size_exceeding_items_fails_loudly(self, app, db):
        from services.evaluation.scenario_parts_service import (
            PartsConfigError, ScenarioPartsService,
        )
        with app.app_context():
            scenario = _create_scenario(
                db, _scenario_config(parts=_parts_config([{'size': 99}, {}])))
            _create_items(db, scenario, 3)
            with pytest.raises(PartsConfigError, match='exceeds'):
                ScenarioPartsService.resolve_specs(scenario)

    def test_PARTS_009_external_string_ids_resolve_via_chat_id(self, app, db):
        from db.models.scenario import EvaluationItem, ScenarioThreads
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            external_ids = ['item_001', 'item_002', 'item_003']
            parts = _parts_config([
                {'item_ids': ['item_002']},          # explicit external ref
                {},                                   # rest
            ])
            scenario = _create_scenario(db, _scenario_config(parts=parts))
            items = []
            for ext in external_ids:
                chat_id = ScenarioPartsService._external_chat_id(ext)
                item = EvaluationItem(subject=ext, chat_id=chat_id)
                db.session.add(item)
                db.session.flush()
                db.session.add(ScenarioThreads(scenario_id=scenario.id,
                                               thread_id=item.item_id))
                items.append(item)
            db.session.flush()

            assert ScenarioPartsService.resolve_specs(scenario) is True
            active = ScenarioPartsService.get_active_parts(scenario)
            assert active[0]['item_ids'] == [items[1].item_id]
            assert set(active[1]['item_ids']) == {items[0].item_id, items[2].item_id}

    def test_PARTS_010_partition_validation_catches_drift(self, app, db):
        from services.evaluation.scenario_parts_service import (
            PartsConfigError, ScenarioPartsService,
        )
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db)
            ids = [it.item_id for it in items]
            # foreign id
            with pytest.raises(PartsConfigError, match='not in scenario'):
                ScenarioPartsService.validate_partition(scenario.id, [
                    {'item_ids': ids}, {'item_ids': [999999]},
                ])
            # duplicate assignment
            with pytest.raises(PartsConfigError, match='more than one part'):
                ScenarioPartsService.validate_partition(scenario.id, [
                    {'item_ids': ids}, {'item_ids': [ids[0]]},
                ])
            # unassigned rest
            with pytest.raises(PartsConfigError, match='not assigned'):
                ScenarioPartsService.validate_partition(scenario.id, [
                    {'item_ids': ids[:2]},
                ])


# =============================================================================
# Session delivery: ordering, locked filter, invisibility
# =============================================================================

class TestSessionDelivery:
    def test_PARTS_011_sequential_order_identical_across_users(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(
                db, locked=(False, False, False))
            ids = [it.item_id for it in items]
            user_a = _create_user(db, 'rater_a')
            user_b = _create_user(db, 'rater_b')
            _add_assessor(db, scenario, user_a)
            _add_assessor(db, scenario, user_b)

            order_a = ScenarioPartsService.session_item_order(scenario, user_a.id, ids)
            order_b = ScenarioPartsService.session_item_order(scenario, user_b.id, ids)
            assert order_a == order_b == ids  # part order == upload order here

    def test_PARTS_012_locked_parts_hidden_from_assessors_visible_to_owner(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db)  # p2+p3 locked
            ids = [it.item_id for it in items]
            owner = _create_user(db, 'creator')
            rater = _create_user(db, 'rater_c')
            _add_assessor(db, scenario, rater)

            rater_order = ScenarioPartsService.session_item_order(scenario, rater.id, ids)
            assert rater_order == ids[:4]  # only open p1

            owner_order = ScenarioPartsService.session_item_order(scenario, owner.id, ids)
            assert set(owner_order) == set(ids)  # owner sees locked parts too

            assert ScenarioPartsService.open_item_ids(scenario) == set(ids[:4])

    def test_PARTS_013_random_order_deterministic_per_user(self, app, db):
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            parts = _parts_config([{'size': 8, 'order': 'random'}, {}])
            scenario = _create_scenario(db, _scenario_config(parts=parts))
            items = _create_items(db, scenario, 9)
            ScenarioPartsService.resolve_specs(scenario)
            ids = [it.item_id for it in items]
            user_a = _create_user(db, 'rater_d')
            user_b = _create_user(db, 'rater_e')
            _add_assessor(db, scenario, user_a)
            _add_assessor(db, scenario, user_b)

            first = ScenarioPartsService.session_item_order(scenario, user_a.id, ids)
            second = ScenarioPartsService.session_item_order(scenario, user_a.id, ids)
            assert first == second  # stable across reloads
            assert sorted(first[:8]) == sorted(ids[:8])  # permutation of p1
            assert first[8] == ids[8]  # rest part stays sequential

            other = ScenarioPartsService.session_item_order(scenario, user_b.id, ids)
            assert sorted(other[:8]) == sorted(ids[:8])
            # 8! permutations — a collision between two users is practically
            # impossible; if this ever flakes the seed derivation broke.
            assert other[:8] != first[:8]

    def test_PARTS_014_session_data_strips_parts_and_copilot_for_assessor(self, app, db):
        from services.evaluation.session_service import EvaluationSessionService
        with app.app_context():
            copilot = {'enabled': True, 'model_id': 'm', 'prompt_version': 1,
                       'hidden_control_ratio': 0.2, 'hidden_control_salt': 'sekret'}
            scenario, items = _resolved_three_part_scenario(db, copilot=copilot)
            rater = _create_user(db, 'rater_f')
            _add_assessor(db, scenario, rater)

            data = EvaluationSessionService.get_session_data(scenario.id, rater.id)
            blob = str(data['config'])
            assert 'parts' not in blob
            assert 'sekret' not in blob
            assert 'hidden_control' not in blob
            # only the open part's items are delivered, no part hints on items
            assert len(data['items']) == 4
            assert all('part' not in item for item in data['items'])

    def test_PARTS_015_session_data_keeps_full_config_for_owner(self, app, db):
        from services.evaluation.session_service import EvaluationSessionService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db)
            owner = _create_user(db, 'creator')

            data = EvaluationSessionService.get_session_data(scenario.id, owner.id)
            assert 'parts' in str(data['config'])
            assert len(data['items']) == len(items)


# =============================================================================
# Copilot gating per part
# =============================================================================

def _copilot_cfg(**overrides):
    cfg = {'enabled': True, 'model_id': 'Global/Test/model', 'prompt_version': 1,
           'top_k': 1, 'hidden_control_ratio': 0.0, 'hidden_control_salt': 's'}
    cfg.update(overrides)
    return cfg


def _cache_row(db, scenario, item, model_id='Global/Test/model'):
    from db.models import LLMTaskResult
    row = LLMTaskResult(
        scenario_id=scenario.id, item_id=item.item_id, model_id=model_id,
        task_type='copilot_labeling',
        payload_json={'suggestions': [{'label_id': 'disclosure', 'rationale': 'r',
                                       'evidence': 'e', 'confidence': 'high'}]},
        prompt_version='1',
    )
    db.session.add(row)
    db.session.flush()
    return row


class TestCopilotGating:
    def test_PARTS_016_suggestions_only_in_copilot_parts(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(
                db, copilot=_copilot_cfg(), locked=(False, False, False))
            rater = _create_user(db, 'rater_g')
            _add_assessor(db, scenario, rater)
            # cache rows exist for BOTH a p1 item (no copilot) and a p3 item
            # (copilot part) — with ratio 0.0 the hash gate always says shown
            _cache_row(db, scenario, items[0])
            _cache_row(db, scenario, items[9])

            visible = LabelingCopilotService.get_visible_suggestions_map(
                scenario, rater.id, [it.item_id for it in items])
            assert items[9].item_id in visible
            assert items[0].item_id not in visible

    def test_PARTS_017_log_shown_false_outside_copilot_parts(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(
                db, copilot=_copilot_cfg(), locked=(False, False, False))
            rater = _create_user(db, 'rater_h')
            _add_assessor(db, scenario, rater)
            _cache_row(db, scenario, items[0])   # p1: no copilot part
            _cache_row(db, scenario, items[9])   # p3: copilot part

            log_p1 = LabelingCopilotService.record_label_event(
                scenario, rater.id, items[0].item_id, final_label='disclosure')
            log_p3 = LabelingCopilotService.record_label_event(
                scenario, rater.id, items[9].item_id, final_label='disclosure')
            assert log_p1.shown is False
            assert log_p1.accepted is None
            assert log_p3.shown is True
            assert log_p3.accepted is True

    def test_PARTS_018_status_denominator_scoped_to_copilot_parts(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db, copilot=_copilot_cfg())
            status = LabelingCopilotService.get_status(scenario)
            # only p3 (3 items) is copilot-enabled
            assert status['total_items'] == 3

    def test_PARTS_019_runner_generates_only_for_copilot_parts(self, app, db):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        from db.models import LLMTaskResult
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db, copilot=_copilot_cfg())
            payload = {'suggestions': [{'label_id': 'disclosure', 'rationale': 'r',
                                        'evidence': 'e', 'confidence': 'high'}]}
            with patch.object(LLMAITaskRunner, '_request_json',
                              return_value=(payload, '{}')) as request_mock, \
                    patch('services.llm.llm_ai_task_runner.LLMClientFactory'
                          '.resolve_client_and_model_id',
                          return_value=(MagicMock(), 'api-model')):
                LLMAITaskRunner._run_copilot_suggestions(
                    'Global/Test/model', [it.item_id for it in items], scenario)

            rows = LLMTaskResult.query.filter_by(
                scenario_id=scenario.id, task_type='copilot_labeling').all()
            generated = {r.item_id for r in rows}
            p3_ids = {it.item_id for it in items[7:]}
            assert generated == p3_ids
            assert request_mock.call_count == 3


# =============================================================================
# Export column + metrics filter
# =============================================================================

class TestExportAndMetrics:
    def _label_items(self, db, scenario, items, user, label='disclosure'):
        from db.models.scenario import ItemLabelingEvaluation
        for item in items:
            db.session.add(ItemLabelingEvaluation(
                user_id=user.id, item_id=item.item_id,
                scenario_id=scenario.id, category_id=label))
        db.session.flush()

    def test_PARTS_020_export_rows_carry_part_column(self, app, db):
        from services.evaluation.results_export_service import ROW_COLUMNS, collect_results
        with app.app_context():
            assert 'part' in ROW_COLUMNS
            scenario, items = _resolved_three_part_scenario(db)
            rater = _create_user(db, 'rater_i')
            _add_assessor(db, scenario, rater)
            self._label_items(db, scenario, [items[0], items[9]], rater)

            payload = collect_results(scenario)
            by_item = {r['item_id']: r for r in payload['rows']}
            assert by_item[items[0].item_id]['part'] == 'p1'
            assert by_item[items[9].item_id]['part'] == 'p3'

    def test_PARTS_021_metrics_part_filter_restricts_units(self, app, db):
        from services.evaluation.agreement_metrics_service import AgreementMetricsService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(
                db, locked=(False, False, False))
            rater_a = _create_user(db, 'rater_j')
            rater_b = _create_user(db, 'rater_k')
            _add_assessor(db, scenario, rater_a)
            _add_assessor(db, scenario, rater_b)
            self._label_items(db, scenario, items, rater_a)
            self._label_items(db, scenario, items, rater_b)

            full = AgreementMetricsService.calculate_all_metrics(
                scenario_id=scenario.id, include_llm=False)
            p1_only = AgreementMetricsService.calculate_all_metrics(
                scenario_id=scenario.id, include_llm=False, part_filter='p1')
            assert full['item_count'] == 10
            assert p1_only['item_count'] == 4

            unknown = AgreementMetricsService.calculate_all_metrics(
                scenario_id=scenario.id, include_llm=False, part_filter='nope')
            assert 'error' in unknown

    def test_PARTS_022_copilot_metrics_aggregated_per_part(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(
                db, copilot=_copilot_cfg(), locked=(False, False, False))
            rater = _create_user(db, 'rater_l')
            _add_assessor(db, scenario, rater)
            _cache_row(db, scenario, items[9])
            LabelingCopilotService.record_label_event(
                scenario, rater.id, items[0].item_id, final_label='disclosure')
            LabelingCopilotService.record_label_event(
                scenario, rater.id, items[9].item_id, final_label='disclosure')
            db.session.flush()

            metrics = LabelingCopilotService.get_copilot_metrics(scenario.id)
            assert metrics['per_part']['p1']['shown_items'] == 0
            assert metrics['per_part']['p3']['shown_items'] == 1


# =============================================================================
# Owner API primitives + v1 roundtrip (service level)
# =============================================================================

class TestOwnerApi:
    def test_PARTS_023_update_part_and_append_items(self, app, db):
        from services.evaluation.scenario_parts_service import (
            PartsConfigError, ScenarioPartsService,
        )
        with app.app_context():
            scenario, items = _resolved_three_part_scenario(db)

            # unlock p2
            updated = ScenarioPartsService.update_part(scenario, 'p2', {'locked': False})
            assert updated['locked'] is False
            active = ScenarioPartsService.get_active_parts(scenario)
            assert [p['locked'] for p in active] == [False, False, True]

            # invalid inputs fail loudly
            with pytest.raises(PartsConfigError, match='Unknown part'):
                ScenarioPartsService.update_part(scenario, 'nope', {'locked': False})
            with pytest.raises(PartsConfigError, match='Unknown fields'):
                ScenarioPartsService.update_part(scenario, 'p1', {'item_ids': []})

            # append newly imported items to p3, partition stays valid
            new_items = _create_items(db, scenario, 2, chat_id_start=5000)
            ScenarioPartsService.append_items_to_part(
                scenario, 'p3', [it.item_id for it in new_items])
            part_map = ScenarioPartsService.item_part_map(scenario)
            assert all(part_map[it.item_id] == 'p3' for it in new_items)

            status = ScenarioPartsService.get_parts_status(scenario)
            assert status['enabled'] and status['resolved']
            assert [p['item_count'] for p in status['parts']] == [4, 3, 5]

    def test_PARTS_024_v1_one_shot_create_resolves_parts(self, app, db):
        from schemas.api_v1.scenario_api import (
            EvalConfigEnvelope, LlarsNativeEnvelope, ScenarioCreateRequest,
        )
        from schemas.evaluation_data_schemas import LabelingConfig
        from services.api_v1_scenario_service import ApiV1Error, create_scenario_one_shot
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        with app.app_context():
            _create_function_type(db)
            _create_user(db, 'creator')

            def _payload(with_items=True):
                items = None
                if with_items:
                    items = LlarsNativeEnvelope(items=[
                        {'id': f'item_{i}', 'label': f'Item {i}',
                         'source': {'type': 'human'}, 'content': f'Text {i}'}
                        for i in range(5)
                    ])
                return ScenarioCreateRequest(
                    name='V1 Parts Scenario',
                    eval_config=EvalConfigEnvelope(
                        type='labeling',
                        config=LabelingConfig(
                            mode='single',
                            labels=[{'id': 'a', 'label': {'de': 'A', 'en': 'A'}}],
                            parts={'enabled': True,
                                   'list': [{'name': 'P1', 'size': 3},
                                            {'name': 'P2', 'locked': True}]},
                        ),
                    ),
                    items=items,
                )

            # parts without items in the same request are rejected
            with pytest.raises(ApiV1Error, match='items in the same create request'):
                create_scenario_one_shot(_payload(with_items=False), 'creator')

            scenario = create_scenario_one_shot(_payload(), 'creator')
            active = ScenarioPartsService.get_active_parts(scenario)
            assert [len(p['item_ids']) for p in active] == [3, 2]
            assert active[1]['locked'] is True
            # ids were auto-generated
            assert [p['id'] for p in active] == ['p1', 'p2']
