"""
Tests for the Labeling Co-Pilot service (LLM pre-annotation).

Covers the study-critical mechanics:
- scenario-owned prompt versioning (bump + history on change, stable salt)
- deterministic hidden-control assignment per (scenario, user, item)
- suggestion cache lookup gated on the CURRENT prompt version
- log upsert with server-derived shown/accepted and first-write-only timing
- runner payload validation/normalization

Test IDs: [COPILOT_001] through [COPILOT_022]
"""

import pytest
from unittest.mock import patch


# =============================================================================
# Helpers
# =============================================================================

def _copilot_config(**overrides):
    cfg = {
        'enabled': True,
        'model_id': 'Global/Mistral/Mistral-Small-3.2-24B-Instruct-2506',
        'prompt': 'Labele {item} mit {labels}. Kontext: {context}. Regeln: {codebook}',
        'codebook': 'R vs I: Bezugsrahmen-Test.',
        'prompt_version': 1,
        'top_k': 2,
        'hidden_control_ratio': 0.2,
        'hidden_control_salt': 'abc123',
    }
    cfg.update(overrides)
    return cfg


def _scenario_config(copilot=None):
    """Wizard-style nesting: eval_config.config holds the labeling config."""
    inner = {
        'categories': [
            {'id': 'disclosure', 'name': {'de': 'Disclosure'}, 'description': {'de': 'Eigene Erfahrung'}},
            {'id': 'edification', 'name': {'de': 'Edification'}},
            {'id': 'question', 'name': {'de': 'Question'}},
        ],
        'allowUnsure': True,
    }
    if copilot is not None:
        inner['copilot'] = copilot
    return {'eval_config': {'type': 'labeling', 'config': inner}}


def _create_function_type(db, name='labeling', ftype_id=7):
    from db.models.scenario import FeatureFunctionType
    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db.session.add(ftype)
    db.session.flush()
    return ftype


def _create_user(db, username='copilot_user'):
    from db.models.user import User
    import hashlib
    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def _create_scenario(db, config_json, name='Copilot Scenario'):
    from db.models.scenario import RatingScenarios
    _create_function_type(db)
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=7,
        config_json=config_json,
        created_by='creator',
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario


def _create_item(db, scenario, subject='Ich habe meinen Job verloren.', chat_id=100):
    from db.models.scenario import EvaluationItem, ScenarioThreads
    item = EvaluationItem(subject=subject, chat_id=chat_id)
    db.session.add(item)
    db.session.flush()
    db.session.add(ScenarioThreads(scenario_id=scenario.id, thread_id=item.item_id))
    db.session.flush()
    return item


def _create_cache_row(db, scenario, item, model_id, suggestions, prompt_version='1'):
    from db.models import LLMTaskResult
    row = LLMTaskResult(
        scenario_id=scenario.id,
        item_id=item.item_id,
        model_id=model_id,
        task_type='copilot_labeling',
        payload_json={'suggestions': suggestions},
        prompt_version=prompt_version,
    )
    db.session.add(row)
    db.session.flush()
    return row


SUGGESTIONS = [
    {'label_id': 'disclosure', 'rationale': '1. Person, eigene Erfahrung',
     'evidence': 'Ich habe meinen Job verloren', 'confidence': 'high'},
    {'label_id': 'edification', 'rationale': 'Objektive Information möglich',
     'evidence': 'Job verloren', 'confidence': 'low'},
]


# =============================================================================
# Config normalization (prompt versioning + salt)
# =============================================================================

class TestConfigNormalization:

    def test_COPILOT_001_first_write_stamps_salt_and_version(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        config = _scenario_config(_copilot_config(hidden_control_salt=None, prompt_version=0))
        config['eval_config']['config']['copilot'].pop('hidden_control_salt')
        config['eval_config']['config']['copilot'].pop('prompt_version')

        result = LabelingCopilotService.normalize_config_on_write(config)
        copilot = result['eval_config']['config']['copilot']

        assert copilot['hidden_control_salt']
        assert copilot['prompt_version'] == 1
        assert len(copilot['prompt_history']) == 1
        assert copilot['prompt_history'][0]['version'] == 1

    def test_COPILOT_002_unchanged_prompt_keeps_version(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        previous = LabelingCopilotService.normalize_config_on_write(
            _scenario_config(_copilot_config())
        )
        prev_copilot = previous['eval_config']['config']['copilot']

        unchanged = _scenario_config(_copilot_config(
            prompt=prev_copilot['prompt'], codebook=prev_copilot['codebook']
        ))
        result = LabelingCopilotService.normalize_config_on_write(unchanged, previous)
        copilot = result['eval_config']['config']['copilot']

        assert copilot['prompt_version'] == prev_copilot['prompt_version']
        assert copilot['hidden_control_salt'] == prev_copilot['hidden_control_salt']

    def test_COPILOT_003_changed_prompt_bumps_version_and_history(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        previous = LabelingCopilotService.normalize_config_on_write(
            _scenario_config(_copilot_config())
        )
        prev_copilot = previous['eval_config']['config']['copilot']

        changed = _scenario_config(_copilot_config(prompt='Neuer Prompt {item} {labels}'))
        result = LabelingCopilotService.normalize_config_on_write(changed, previous)
        copilot = result['eval_config']['config']['copilot']

        assert copilot['prompt_version'] == prev_copilot['prompt_version'] + 1
        assert copilot['prompt_history'][-1]['version'] == copilot['prompt_version']
        # Salt must stay stable across edits (reproducible control subset)
        assert copilot['hidden_control_salt'] == prev_copilot['hidden_control_salt']

    def test_COPILOT_004_codebook_change_bumps_version(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        previous = LabelingCopilotService.normalize_config_on_write(
            _scenario_config(_copilot_config())
        )
        base = previous['eval_config']['config']['copilot']
        changed = _scenario_config(_copilot_config(prompt=base['prompt'], codebook='Andere Regeln'))
        result = LabelingCopilotService.normalize_config_on_write(changed, previous)
        assert result['eval_config']['config']['copilot']['prompt_version'] == base['prompt_version'] + 1

    def test_COPILOT_005_noop_without_copilot_section(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        config = _scenario_config()
        result = LabelingCopilotService.normalize_config_on_write(config)
        assert 'copilot' not in result['eval_config']['config']


# =============================================================================
# Config access helpers
# =============================================================================

class TestConfigAccess:

    def test_COPILOT_006_get_copilot_config_requires_enabled(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        assert LabelingCopilotService.get_copilot_config(
            _scenario_config(_copilot_config(enabled=False))
        ) is None
        assert LabelingCopilotService.get_copilot_config(_scenario_config()) is None
        assert LabelingCopilotService.get_copilot_config(
            _scenario_config(_copilot_config())
        ) is not None

    def test_COPILOT_007_extract_label_options_wizard_categories(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        options = LabelingCopilotService.extract_label_options(_scenario_config())
        assert [o['id'] for o in options] == ['disclosure', 'edification', 'question']
        assert options[0]['description'] == 'Eigene Erfahrung'

    def test_COPILOT_008_extract_label_options_schema_labels(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        config = {'type': 'labeling', 'config': {
            'mode': 'single',
            'labels': [
                {'id': 'a', 'label': {'de': 'Label A', 'en': 'Label A'}},
                {'id': 'b', 'label': {'en': 'Label B'}, 'description': {'en': 'Desc B'}},
            ],
        }}
        options = LabelingCopilotService.extract_label_options(config)
        assert [o['id'] for o in options] == ['a', 'b']
        assert options[1]['description'] == 'Desc B'


# =============================================================================
# Hidden control subset
# =============================================================================

class TestHiddenControl:

    def test_COPILOT_009_deterministic(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        cfg = _copilot_config(hidden_control_ratio=0.5)
        first = LabelingCopilotService.is_hidden_control(1, 2, 3, cfg)
        for _ in range(5):
            assert LabelingCopilotService.is_hidden_control(1, 2, 3, cfg) == first

    def test_COPILOT_010_ratio_zero_never_hides(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        cfg = _copilot_config(hidden_control_ratio=0.0)
        assert not any(
            LabelingCopilotService.is_hidden_control(1, user_id, item_id, cfg)
            for user_id in range(5) for item_id in range(50)
        )

    def test_COPILOT_011_ratio_roughly_respected(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        cfg = _copilot_config(hidden_control_ratio=0.2)
        pairs = [(u, i) for u in range(4) for i in range(500)]
        hidden = sum(
            1 for (u, i) in pairs
            if LabelingCopilotService.is_hidden_control(42, u, i, cfg)
        )
        share = hidden / len(pairs)
        assert 0.15 < share < 0.25

    def test_COPILOT_012_salt_changes_assignment(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        cfg_a = _copilot_config(hidden_control_ratio=0.5, hidden_control_salt='salt-a')
        cfg_b = _copilot_config(hidden_control_ratio=0.5, hidden_control_salt='salt-b')
        assignments_a = [LabelingCopilotService.is_hidden_control(1, 1, i, cfg_a) for i in range(200)]
        assignments_b = [LabelingCopilotService.is_hidden_control(1, 1, i, cfg_b) for i in range(200)]
        assert assignments_a != assignments_b


# =============================================================================
# Suggestion delivery (session map)
# =============================================================================

class TestSuggestionDelivery:

    def test_COPILOT_013_visible_map_returns_current_version(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.0)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db)
        item = _create_item(db, scenario)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        result = LabelingCopilotService.get_visible_suggestions_map(
            scenario, user.id, [item.item_id]
        )
        assert item.item_id in result
        assert result[item.item_id]['suggestions'][0]['label_id'] == 'disclosure'

    def test_COPILOT_014_stale_prompt_version_not_delivered(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.0, prompt_version=2)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'stale_user')
        item = _create_item(db, scenario, chat_id=101)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        result = LabelingCopilotService.get_visible_suggestions_map(
            scenario, user.id, [item.item_id]
        )
        assert result == {}

    def test_COPILOT_015_hidden_control_item_not_delivered(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.2)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'hidden_user')
        item = _create_item(db, scenario, chat_id=102)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        with patch.object(LabelingCopilotService, 'is_hidden_control', return_value=True):
            result = LabelingCopilotService.get_visible_suggestions_map(
                scenario, user.id, [item.item_id]
            )
        assert result == {}


# =============================================================================
# Log upsert (record_label_event)
# =============================================================================

class TestRecordLabelEvent:

    def test_COPILOT_016_disabled_copilot_writes_no_log(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        scenario = _create_scenario(db, _scenario_config())
        user = _create_user(db, 'nolog_user')
        item = _create_item(db, scenario, chat_id=103)
        assert LabelingCopilotService.record_label_event(
            scenario, user.id, item.item_id, 'disclosure'
        ) is None

    def test_COPILOT_017_accepted_primary(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.0)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'accept_user')
        item = _create_item(db, scenario, chat_id=104)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        log = LabelingCopilotService.record_label_event(
            scenario, user.id, item.item_id, 'disclosure', time_on_item_ms=4200, helpful=True
        )
        db.session.flush()

        assert log.shown is True
        assert log.suggested_label == 'disclosure'
        assert log.suggested_label_2 == 'edification'
        assert log.accepted is True
        assert log.accepted_any is True
        assert log.helpful is True
        assert log.time_on_item_ms == 4200
        assert log.prompt_version == 1

    def test_COPILOT_018_accepted_any_via_secondary(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.0)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'secondary_user')
        item = _create_item(db, scenario, chat_id=105)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        log = LabelingCopilotService.record_label_event(
            scenario, user.id, item.item_id, 'edification'
        )
        assert log.accepted is False
        assert log.accepted_any is True

    def test_COPILOT_019_hidden_item_logs_shown_false(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.2)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'control_user')
        item = _create_item(db, scenario, chat_id=106)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        with patch.object(LabelingCopilotService, 'is_hidden_control', return_value=True):
            log = LabelingCopilotService.record_label_event(
                scenario, user.id, item.item_id, 'disclosure', time_on_item_ms=3000
            )

        assert log.shown is False
        assert log.suggested_label is None
        assert log.accepted is None  # no acceptance semantics without a shown suggestion
        assert log.time_on_item_ms == 3000  # timing still recorded (control condition!)

    def test_COPILOT_020_time_is_first_write_only(self, app, db):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        copilot = _copilot_config(hidden_control_ratio=0.0)
        scenario = _create_scenario(db, _scenario_config(copilot))
        user = _create_user(db, 'timing_user')
        item = _create_item(db, scenario, chat_id=107)
        _create_cache_row(db, scenario, item, copilot['model_id'], SUGGESTIONS, '1')

        LabelingCopilotService.record_label_event(
            scenario, user.id, item.item_id, 'disclosure', time_on_item_ms=5000
        )
        db.session.flush()
        log = LabelingCopilotService.record_label_event(
            scenario, user.id, item.item_id, 'question', time_on_item_ms=99999
        )
        db.session.flush()

        from db.models import LabelingCopilotLog
        rows = LabelingCopilotLog.query.filter_by(
            scenario_id=scenario.id, user_id=user.id, item_id=item.item_id
        ).all()
        assert len(rows) == 1  # upsert, not duplicate
        assert log.time_on_item_ms == 5000  # first write wins
        assert log.final_label == 'question'  # label update IS reflected
        assert log.accepted is False


# =============================================================================
# Runner payload validation
# =============================================================================

class TestValidateCopilotPayload:

    ALLOWED = ['disclosure', 'edification', 'question']

    def test_COPILOT_021_normalizes_and_trims(self, app, db):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        payload = {'suggestions': [
            {'label_id': 'DISCLOSURE', 'rationale': 'r1', 'evidence': 'e1', 'confidence': 'HIGH'},
            {'label_id': 'disclosure', 'rationale': 'dupe'},
            {'label_id': 'unknown_label', 'rationale': 'dropped'},
            {'label_id': 'question', 'rationale': 'r2', 'confidence': 'nonsense'},
        ]}
        result = LLMAITaskRunner._validate_copilot_payload(payload, self.ALLOWED, 2)
        assert [s['label_id'] for s in result] == ['disclosure', 'question']
        assert result[0]['confidence'] == 'high'
        assert result[1]['confidence'] == 'medium'  # invalid confidence normalized

    def test_COPILOT_022_rejects_garbage_accepts_bare_object(self, app, db):
        from services.llm.llm_ai_task_runner import LLMAITaskRunner
        assert LLMAITaskRunner._validate_copilot_payload(None, self.ALLOWED, 2) is None
        assert LLMAITaskRunner._validate_copilot_payload({'suggestions': 'x'}, self.ALLOWED, 2) is None
        assert LLMAITaskRunner._validate_copilot_payload(
            {'suggestions': [{'label_id': 'nope'}]}, self.ALLOWED, 2
        ) is None
        bare = LLMAITaskRunner._validate_copilot_payload(
            {'label_id': 'question', 'rationale': 'direct'}, self.ALLOWED, 1
        )
        assert bare and bare[0]['label_id'] == 'question'


class TestTopKVersionBump:
    """top_k gehört zum effektiven Prompt → Versionswechsel (COPILOT_023/024)."""

    def _cfg(self, top_k, version=None, salt='abc123'):
        copilot = {
            'enabled': True, 'model_id': 'm', 'prompt': 'P {item} {labels}',
            'codebook': '', 'top_k': top_k, 'hidden_control_salt': salt,
        }
        if version is not None:
            copilot['prompt_version'] = version
        return {'eval_config': {'config': {'categories': [], 'copilot': copilot}}}

    def test_COPILOT_023_top_k_change_bumps_version(self):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        prev = LabelingCopilotService.normalize_config_on_write(self._cfg(1), None)
        nxt = LabelingCopilotService.normalize_config_on_write(self._cfg(2), prev)
        cop = LabelingCopilotService.locate_inner_config(nxt)['copilot']
        assert cop['prompt_version'] == 2
        assert cop['prompt_history'][-1]['top_k'] == 2

    def test_COPILOT_024_same_top_k_keeps_version(self):
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        prev = LabelingCopilotService.normalize_config_on_write(self._cfg(2), None)
        nxt = LabelingCopilotService.normalize_config_on_write(self._cfg(2), prev)
        cop = LabelingCopilotService.locate_inner_config(nxt)['copilot']
        assert cop['prompt_version'] == 1
