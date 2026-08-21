"""
Tests for per-case evaluation timing (EvaluationItemTiming + export wiring).

Covers:
- value coercion + payload extraction (top-level / nested shapes)
- first-write-only upsert semantics
- scenario resolution for thread-scoped routes
- the v1 export stamping the real time_on_item_ms column AND the derived
  created_at-delta fallback (time_since_prev_ms)

Test IDs: [TIMING_001] through [TIMING_012]
"""

from datetime import datetime

import pytest


# =============================================================================
# Helpers
# =============================================================================

def _create_function_type(db, name='comparison', ftype_id=4):
    from db.models.scenario import FeatureFunctionType
    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db.session.add(ftype)
    db.session.flush()
    return ftype


def _create_user(db, username='timing_user'):
    from db.models.user import User
    import hashlib
    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def _create_scenario(db, name='Timing Scenario', ftype_id=4):
    from db.models.scenario import RatingScenarios
    _create_function_type(db, ftype_id=ftype_id)
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        config_json={},
        created_by='creator',
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario


def _create_item(db, scenario, subject='Fall', chat_id=100):
    from db.models.scenario import EvaluationItem, ScenarioItems
    item = EvaluationItem(subject=subject, chat_id=chat_id)
    db.session.add(item)
    db.session.flush()
    db.session.add(ScenarioItems(scenario_id=scenario.id, item_id=item.item_id))
    db.session.flush()
    return item


def _add_member(db, scenario, user):
    from db.models.scenario import ScenarioUsers
    db.session.add(ScenarioUsers(
        scenario_id=scenario.id, user_id=user.id,
        manager_role='none', evaluation_role='assessor',
    ))
    db.session.flush()


def _add_comparison_vote(db, scenario, item, user, choice='A', created_at=None):
    from db.models.scenario import ItemComparisonEvaluation
    ev = ItemComparisonEvaluation(
        scenario_id=scenario.id, item_id=item.item_id, user_id=user.id,
        choice=choice, notes=None,
    )
    if created_at is not None:
        ev.created_at = created_at
        ev.updated_at = created_at
    db.session.add(ev)
    db.session.flush()
    return ev


# =============================================================================
# Value coercion + payload extraction
# =============================================================================

class TestCoercion:

    def test_TIMING_001_coerce_none_and_garbage(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        assert ItemTimingService.coerce_ms(None) is None
        assert ItemTimingService.coerce_ms('nope') is None
        assert ItemTimingService.coerce_ms(-5) is None

    def test_TIMING_002_coerce_rounds_and_caps(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        assert ItemTimingService.coerce_ms(4200.7) == 4201
        assert ItemTimingService.coerce_ms('1500') == 1500
        # cap at 24h
        assert ItemTimingService.coerce_ms(999_999_999) == 24 * 60 * 60 * 1000

    def test_TIMING_003_extract_top_level(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        assert ItemTimingService.extract_from_payload({'time_on_item_ms': 900}) == 900

    def test_TIMING_004_extract_nested_copilot_and_timing(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        assert ItemTimingService.extract_from_payload({'copilot': {'time_on_item_ms': 700}}) == 700
        assert ItemTimingService.extract_from_payload({'timing': {'time_on_item_ms': 800}}) == 800

    def test_TIMING_005_extract_missing(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        assert ItemTimingService.extract_from_payload({}) is None
        assert ItemTimingService.extract_from_payload(None) is None


# =============================================================================
# First-write-only upsert
# =============================================================================

class TestRecord:

    def test_TIMING_006_record_creates_row(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        user = _create_user(db)
        item = _create_item(db, scenario)

        ItemTimingService.record_item_timing(
            scenario.id, user.id, item.item_id, 4200, function_type='comparison'
        )
        db.session.commit()

        m = ItemTimingService.timings_for_scenario(scenario.id)
        assert m[(user.id, item.item_id, '')] == 4200

    def test_TIMING_007_first_write_only(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        user = _create_user(db)
        item = _create_item(db, scenario)

        ItemTimingService.record_item_timing(scenario.id, user.id, item.item_id, 1000)
        db.session.commit()
        # A later (re)save must NOT overwrite the primary time-to-first-save.
        ItemTimingService.record_item_timing(scenario.id, user.id, item.item_id, 5000)
        db.session.commit()

        m = ItemTimingService.timings_for_scenario(scenario.id)
        assert m[(user.id, item.item_id, '')] == 1000

    def test_TIMING_020_spans_of_one_item_keep_separate_rows(self, app, db):
        """Conversation labeling times each SPAN, not the conversation.

        Keying the lookup by (user, item) alone collapses ~92 rows into one and
        hands every span of a conversation the same duration — a plausible
        number that is simply not the measurement.
        """
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        user = _create_user(db)
        item = _create_item(db, scenario)

        ItemTimingService.record_item_timing(
            scenario.id, user.id, item.item_id, 1500,
            function_type='conversation_labeling', span_id='m2-s01'
        )
        ItemTimingService.record_item_timing(
            scenario.id, user.id, item.item_id, 2500,
            function_type='conversation_labeling', span_id='m2-s02'
        )
        db.session.commit()

        m = ItemTimingService.timings_for_scenario(scenario.id)
        assert m[(user.id, item.item_id, 'm2-s01')] == 1500
        assert m[(user.id, item.item_id, 'm2-s02')] == 2500

    def test_TIMING_008_invalid_value_is_noop(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        user = _create_user(db)
        item = _create_item(db, scenario)

        assert ItemTimingService.record_item_timing(scenario.id, user.id, item.item_id, None) is None
        db.session.commit()
        assert ItemTimingService.timings_for_scenario(scenario.id) == {}

    def test_TIMING_009_resolve_scenario_prefers_valid_thread_scenario(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        item = _create_item(db, scenario)
        db.session.commit()
        # A spoofed scenario id not belonging to the thread falls back to the real one.
        resolved = ItemTimingService.resolve_scenario_id(item.item_id, preferred=999999)
        assert resolved == scenario.id
        # The correct id is honoured.
        assert ItemTimingService.resolve_scenario_id(item.item_id, preferred=scenario.id) == scenario.id


# =============================================================================
# Export wiring: real column + derived fallback
# =============================================================================

class TestExportTiming:

    def _build_two_item_scenario(self, db):
        scenario = _create_scenario(db, name='Comparison Timing')
        user = _create_user(db, username='rater_a')
        _add_member(db, scenario, user)
        item1 = _create_item(db, scenario, subject='Fall 1', chat_id=1)
        item2 = _create_item(db, scenario, subject='Fall 2', chat_id=2)
        # Two sequential votes 90s apart (item1 first, then item2).
        t0 = datetime(2026, 6, 5, 9, 15, 14)
        t1 = datetime(2026, 6, 5, 9, 16, 44)  # +90s
        _add_comparison_vote(db, scenario, item1, user, choice='A', created_at=t0)
        _add_comparison_vote(db, scenario, item2, user, choice='B', created_at=t1)
        db.session.commit()
        return scenario, user, item1, item2

    def test_TIMING_010_real_time_on_item_ms_in_export(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        from services.evaluation import results_export_service as export

        scenario, user, item1, item2 = self._build_two_item_scenario(db)
        ItemTimingService.record_item_timing(
            scenario.id, user.id, item1.item_id, 4200, function_type='comparison'
        )
        db.session.commit()

        result = export.collect_results(scenario, include_llms=False)
        rows = {r['item_id']: r for r in result['rows'] if r['voter_kind'] == 'human'}

        assert rows[item1.item_id]['time_on_item_ms'] == 4200
        # item2 had no captured value.
        assert rows[item2.item_id]['time_on_item_ms'] is None

    def test_TIMING_011_derived_delta_fallback(self, app, db):
        from services.evaluation import results_export_service as export

        scenario, user, item1, item2 = self._build_two_item_scenario(db)
        # No EvaluationItemTiming rows at all — the derived fallback must fill in.
        result = export.collect_results(scenario, include_llms=False)
        rows = {r['item_id']: r for r in result['rows'] if r['voter_kind'] == 'human'}

        # First case per voter has no predecessor.
        assert rows[item1.item_id]['time_since_prev_ms'] is None
        # Second case = 90s gap = 90000 ms.
        assert rows[item2.item_id]['time_since_prev_ms'] == 90000

    def test_TIMING_012_columns_present_in_schema(self, app, db):
        from services.evaluation.results_export_service import ROW_COLUMNS
        assert 'time_on_item_ms' in ROW_COLUMNS
        assert 'time_since_prev_ms' in ROW_COLUMNS


# =============================================================================
# Legacy GUI export stamping (item_id / thread_id key resolution)
# =============================================================================

class TestLegacyStamping:

    def test_TIMING_013_derive_deltas_basic(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        # user 1: two items 120s apart; user 2: single item (no delta).
        deltas = ItemTimingService.derive_deltas([
            (1, 10, '2026-06-05T09:00:00'),
            (1, 11, '2026-06-05T09:02:00'),  # +120s
            (2, 12, '2026-06-05T09:00:30'),
            (1, 13, None),                   # no timestamp → ignored
        ])
        assert deltas.get((1, 11)) == 120000
        assert (1, 10) not in deltas          # first case per voter
        assert (2, 12) not in deltas          # single item
        assert (1, 13) not in deltas

    def test_TIMING_014_stamp_rows_resolves_item_and_thread_keys(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        scenario = _create_scenario(db)
        user = _create_user(db, username='legacy_rater')
        item1 = _create_item(db, scenario, subject='A', chat_id=1)
        item2 = _create_item(db, scenario, subject='B', chat_id=2)
        ItemTimingService.record_item_timing(scenario.id, user.id, item1.item_id, 3000)
        db.session.commit()

        # Legacy rows: item1 keyed by 'item_id', item2 keyed by 'thread_id';
        # plus an LLM row (no user_id) that must be left untouched.
        rows = [
            {'user_id': user.id, 'item_id': item1.item_id, 'timestamp': '2026-06-05T09:00:00'},
            {'user_id': user.id, 'thread_id': item2.item_id, 'timestamp': '2026-06-05T09:02:00'},
            {'model_id': 'llm-x', 'thread_id': 999},
        ]
        ItemTimingService.stamp_rows(rows, scenario.id)

        # Real captured timing lands on the item_id-keyed row.
        assert rows[0]['time_on_item_ms'] == 3000
        assert rows[0]['time_since_prev_ms'] is None            # first case
        # thread_id-keyed row: no capture, derived 120s fallback.
        assert rows[1]['time_on_item_ms'] is None
        assert rows[1]['time_since_prev_ms'] == 120000
        # Columns seeded on every human row (stable CSV header).
        assert 'time_on_item_ms' in rows[0] and 'time_since_prev_ms' in rows[1]
        # LLM row untouched.
        assert 'time_on_item_ms' not in rows[2]


# =============================================================================
# Per-voter timing aggregates
# =============================================================================

class TestTimingSummary:

    def test_TIMING_015_stats_and_per_case_dedupe(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        # Voter 1: item 10 appears TWICE (e.g. two rating dimensions) with the
        # same captured time — must count once. Items 10/11 captured, 12 derived.
        summary = ItemTimingService.summarize_cases([
            (1, 'alice', 10, 10000, None),
            (1, 'alice', 10, 10000, None),   # duplicate case row → deduped
            (1, 'alice', 11, 20000, None),
            (1, 'alice', 12, None, 30000),   # derived fallback
        ])
        assert len(summary['per_voter']) == 1
        v = summary['per_voter'][0]
        assert v['voter_username'] == 'alice'
        assert v['n'] == 3
        assert v['captured_n'] == 2
        assert v['derived_n'] == 1
        assert v['mean_ms'] == 20000
        assert v['median_ms'] == 20000
        assert v['min_ms'] == 10000
        assert v['max_ms'] == 30000
        assert v['std_ms'] == 10000            # sample SD of [10000,20000,30000]
        assert v['total_ms'] == 60000
        assert summary['overall']['n'] == 3

    def test_TIMING_016_captured_beats_derived_for_same_case(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        summary = ItemTimingService.summarize_cases([
            (1, 'a', 10, None, 5000),   # derived first
            (1, 'a', 10, 8000, None),   # captured later → wins
        ])
        v = summary['per_voter'][0]
        assert v['n'] == 1
        assert v['captured_n'] == 1
        assert v['derived_n'] == 0
        assert v['mean_ms'] == 8000

    def test_TIMING_017_std_none_for_single_case(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        summary = ItemTimingService.summarize_cases([(1, 'a', 10, 4200, None)])
        assert summary['per_voter'][0]['std_ms'] is None

    def test_TIMING_018_empty_when_no_times(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        summary = ItemTimingService.summarize_cases([(1, 'a', 10, None, None)])
        assert summary['per_voter'] == []
        assert summary['overall'] is None

    def test_TIMING_019_v1_envelope_includes_timing_metrics(self, app, db):
        from services.evaluation.item_timing_service import ItemTimingService
        from services.evaluation import results_export_service as export

        scenario = _create_scenario(db, name='Comparison Metrics')
        user = _create_user(db, username='rater_metrics')
        _add_member(db, scenario, user)
        item1 = _create_item(db, scenario, subject='F1', chat_id=1)
        item2 = _create_item(db, scenario, subject='F2', chat_id=2)
        t0 = datetime(2026, 6, 5, 9, 15, 14)
        t1 = datetime(2026, 6, 5, 9, 16, 44)  # +90s
        _add_comparison_vote(db, scenario, item1, user, choice='A', created_at=t0)
        _add_comparison_vote(db, scenario, item2, user, choice='B', created_at=t1)
        ItemTimingService.record_item_timing(scenario.id, user.id, item1.item_id, 4200)
        db.session.commit()

        result = export.collect_results(scenario, include_llms=False)
        assert 'timing_metrics' in result
        v = result['timing_metrics']['per_voter'][0]
        # item1 captured 4200 + item2 derived 90000
        assert v['n'] == 2
        assert v['captured_n'] == 1
        assert v['derived_n'] == 1
        assert v['min_ms'] == 4200
        assert v['max_ms'] == 90000
        assert v['mean_ms'] == 47100
        assert isinstance(v['std_ms'], int) and v['std_ms'] > 0
