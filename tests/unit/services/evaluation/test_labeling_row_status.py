"""
Tests for the three-way labeling row status (question-first labeling).

Background
----------
Question-first labeling puts decision questions IN FRONT of the label and
persists every single click. A row can therefore exist while the rater is still
working: answers saved, ``category_id`` still NULL. Before the shared rule
existed, such a row was indistinguishable from "nothing happened" — a rater on
production scenario 758 answered two of three questions, navigated away, and the
item kept showing "ausstehend" although the answers were already in the DB.

The rule (``labeling_types.labeling_row_status``):

    done         category_id IS NOT NULL OR is_unsure
    in_progress  row exists, not done, and holds answers_json / second_choice_id
                 / non-empty feedback
    pending      everything else (including "no row at all")

These tests pin the rule itself, its SQL twins, every place that computes the
per-item status from it, and the two places that must NOT treat a partial row
as a vote (results export, IRR).

Test IDs: [LABEL_STATUS_001] through [LABEL_STATUS_026]
"""

import hashlib


# =============================================================================
# Helpers
# =============================================================================

def _types():
    from services.evaluation import labeling_types
    return labeling_types


def _create_function_type(db, ftype_id=7, name='labeling'):
    from db.models.scenario import FeatureFunctionType

    existing = FeatureFunctionType.query.get(ftype_id)
    if existing:
        return existing
    ftype = FeatureFunctionType(function_type_id=ftype_id, name=name)
    db.session.add(ftype)
    db.session.flush()
    return ftype


def _create_user(db, username):
    from db.models.user import User

    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def _create_scenario(db, name='Question Labeling', ftype_id=7):
    from db.models.scenario import RatingScenarios

    _create_function_type(db, ftype_id, 'labeling' if ftype_id == 7 else 'conversation_labeling')
    scenario = RatingScenarios(
        scenario_name=name,
        function_type_id=ftype_id,
        config_json={},
        created_by='creator',
    )
    db.session.add(scenario)
    db.session.flush()
    return scenario


def _create_item(db, scenario=None, subject='Fall', chat_id=1, metadata_json=None):
    from db.models.scenario import EvaluationItem, ScenarioItems

    item = EvaluationItem(subject=subject, chat_id=chat_id, metadata_json=metadata_json)
    db.session.add(item)
    db.session.flush()
    if scenario is not None:
        db.session.add(ScenarioItems(scenario_id=scenario.id, item_id=item.item_id))
        db.session.flush()
    return item


def _add_member(db, scenario, user, evaluation_role='assessor'):
    from db.models.scenario import (
        InvitationStatus, MembershipStatus, ScenarioUsers,
    )

    su = ScenarioUsers(
        scenario_id=scenario.id,
        user_id=user.id,
        evaluation_role=evaluation_role,
        invitation_status=InvitationStatus.ACCEPTED,
        membership_status=MembershipStatus.ACTIVE,
    )
    db.session.add(su)
    db.session.flush()
    return su


def _row(db, user, item, scenario, **kwargs):
    """Persist one ItemLabelingEvaluation with the given shape."""
    from db.models.scenario import ItemLabelingEvaluation

    row = ItemLabelingEvaluation(
        user_id=user.id,
        item_id=item.item_id,
        scenario_id=scenario.id,
        span_id=kwargs.pop('span_id', ''),
        category_id=kwargs.pop('category_id', None),
        is_unsure=kwargs.pop('is_unsure', False),
        feedback=kwargs.pop('feedback', None),
        second_choice_id=kwargs.pop('second_choice_id', None),
        answers_json=kwargs.pop('answers_json', None),
    )
    assert not kwargs, f'unexpected kwargs: {kwargs}'
    db.session.add(row)
    db.session.flush()
    return row


class _Detached:
    """Row-shaped stand-in for the pure-Python helper tests (no DB needed)."""

    def __init__(self, **kwargs):
        self.category_id = kwargs.get('category_id')
        self.is_unsure = kwargs.get('is_unsure', False)
        self.feedback = kwargs.get('feedback')
        self.second_choice_id = kwargs.get('second_choice_id')
        self.answers_json = kwargs.get('answers_json')


# Answers as the question-first interface sends them after two of three clicks.
PARTIAL_ANSWERS = {'q1': 'S', 'lean': {'q1': 40}, 'derived': None, 'source': 'questions'}


# =============================================================================
# The rule itself
# =============================================================================

class TestLabelingRowStatusHelper:

    def test_LABEL_STATUS_001_no_row_is_pending(self):
        """[LABEL_STATUS_001] A missing row is 'pending', so callers can feed
        the result of a .first() straight in."""
        assert _types().labeling_row_status(None) == 'pending'

    def test_LABEL_STATUS_002_empty_row_is_pending(self):
        """[LABEL_STATUS_002] A row with nothing in it carries no information."""
        assert _types().labeling_row_status(_Detached()) == 'pending'

    def test_LABEL_STATUS_003_category_is_done(self):
        """[LABEL_STATUS_003] A chosen label is the completion criterion."""
        assert _types().labeling_row_status(_Detached(category_id='A')) == 'done'

    def test_LABEL_STATUS_004_unsure_alone_is_done(self):
        """[LABEL_STATUS_004] "Unsure" is an explicit decision, not an absence."""
        assert _types().labeling_row_status(_Detached(is_unsure=True)) == 'done'

    def test_LABEL_STATUS_005_answers_only_is_in_progress(self):
        """[LABEL_STATUS_005] The scenario-758 case: questions answered, no label."""
        row = _Detached(answers_json=PARTIAL_ANSWERS)
        assert _types().labeling_row_status(row) == 'in_progress'

    def test_LABEL_STATUS_006_second_choice_only_is_in_progress(self):
        """[LABEL_STATUS_006] A runner-up without a first choice is unfinished
        work, not a vote."""
        row = _Detached(second_choice_id='B')
        assert _types().labeling_row_status(row) == 'in_progress'

    def test_LABEL_STATUS_007_feedback_only_is_in_progress(self):
        """[LABEL_STATUS_007] Free-text typed before deciding still counts."""
        row = _Detached(feedback='unklar formuliert')
        assert _types().labeling_row_status(row) == 'in_progress'

    def test_LABEL_STATUS_008_blank_feedback_is_not_input(self):
        """[LABEL_STATUS_008] Whitespace is not rater input — an autosave of an
        empty textarea must not flip an untouched item to 'in Bearbeitung'."""
        assert _types().labeling_row_status(_Detached(feedback='   ')) == 'pending'

    def test_LABEL_STATUS_009_empty_answers_container_is_not_input(self):
        """[LABEL_STATUS_009] {} / [] / 'null' are empty containers, not answers."""
        types = _types()
        for empty in ({}, [], '', '{}', '[]', 'null', '  '):
            assert types.labeling_row_status(_Detached(answers_json=empty)) == 'pending'

    def test_LABEL_STATUS_010_answers_as_json_string_still_count(self):
        """[LABEL_STATUS_010] Some driver/column combinations hand the JSON back
        as text; the rule must not change meaning with the load path."""
        row = _Detached(answers_json='{"q1": "S"}')
        assert _types().labeling_row_status(row) == 'in_progress'

    def test_LABEL_STATUS_011_decision_beats_partial_input(self):
        """[LABEL_STATUS_011] A full save carries answers AND a label -> done."""
        row = _Detached(category_id='A', answers_json=PARTIAL_ANSWERS,
                        second_choice_id='B', feedback='passt')
        assert _types().labeling_row_status(row) == 'done'

    def test_LABEL_STATUS_012_strongest_status_wins(self):
        """[LABEL_STATUS_012] Conversation labeling aggregates many span rows per
        item: one decided span must not be hidden by a later partial one."""
        strongest = _types().strongest_labeling_status
        assert strongest('pending', 'in_progress') == 'in_progress'
        assert strongest('in_progress', 'done') == 'done'
        assert strongest('done', 'pending') == 'done'
        assert strongest(None, None) == 'pending'
        assert strongest() == 'pending'

    def test_LABEL_STATUS_013_sql_twins_agree_with_python_rule(self, app, db):
        """[LABEL_STATUS_013] The SQL clauses used by the batch stats query must
        classify exactly like the Python helper.

        The batch path cannot afford to load every feedback/answers_json blob,
        so it filters in SQL — which is a second implementation of the same
        rule. This test is what keeps the twins from drifting apart.
        """
        from db.models.scenario import ItemLabelingEvaluation

        types = _types()
        user = _create_user(db, 'twins_rater')
        scenario = _create_scenario(db, 'Twins')
        shapes = [
            {},
            {'category_id': 'A'},
            {'is_unsure': True},
            {'answers_json': PARTIAL_ANSWERS},
            {'second_choice_id': 'B'},
            {'feedback': 'hm'},
            {'category_id': 'A', 'answers_json': PARTIAL_ANSWERS},
        ]
        items = []
        for index, shape in enumerate(shapes):
            item = _create_item(db, scenario, chat_id=900 + index)
            _row(db, user, item, scenario, **shape)
            items.append(item)
        db.session.commit()

        sql_decided = {
            r.item_id for r in ItemLabelingEvaluation.query.filter(
                types.labeling_decided_clause()
            ).all()
        }
        sql_partial = {
            r.item_id for r in ItemLabelingEvaluation.query.filter(
                types.labeling_partial_clause()
            ).all()
        }

        for item in items:
            row = ItemLabelingEvaluation.query.filter_by(item_id=item.item_id).one()
            assert (item.item_id in sql_decided) == types.labeling_row_is_decided(row)
            assert (item.item_id in sql_partial) == types.labeling_row_has_partial_input(row)


# =============================================================================
# Session service: batch + single item
# =============================================================================

class TestSessionServiceStatus:

    def test_LABEL_STATUS_014_single_item_partial_is_in_progress(self, app, db):
        """[LABEL_STATUS_014] _get_thread_evaluation_status reports the middle
        state instead of claiming the rater never started."""
        from services.evaluation.session_service import EvaluationSessionService

        user = _create_user(db, 'single_partial')
        scenario = _create_scenario(db)
        item = _create_item(db, scenario, chat_id=310)
        _row(db, user, item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        status = EvaluationSessionService._get_thread_evaluation_status(
            item.item_id, user.id, 'labeling', scenario_id=scenario.id
        )
        assert status == 'in_progress'

    def test_LABEL_STATUS_015_batch_reports_all_three_states(self, app, db):
        """[LABEL_STATUS_015] The overview list distinguishes pending, partial
        and finished items for the same rater."""
        from services.evaluation.session_service import EvaluationSessionService

        user = _create_user(db, 'batch_partial')
        scenario = _create_scenario(db)
        done_item = _create_item(db, scenario, chat_id=311)
        partial_item = _create_item(db, scenario, chat_id=312)
        untouched_item = _create_item(db, scenario, chat_id=313)
        _row(db, user, done_item, scenario, category_id='A')
        _row(db, user, partial_item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        result = EvaluationSessionService._batch_get_evaluation_statuses(
            [done_item.item_id, partial_item.item_id, untouched_item.item_id],
            user.id, 'labeling', scenario.id,
        )
        assert result[done_item.item_id] == 'done'
        assert result[partial_item.item_id] == 'in_progress'
        assert result[untouched_item.item_id] == 'pending'

    def test_LABEL_STATUS_016_prefill_includes_partial_rows(self, app, db):
        """[LABEL_STATUS_016] The interface can only restore the answered
        questions if the prefill query does not filter on category_id."""
        from services.evaluation.session_service import EvaluationSessionService

        user = _create_user(db, 'prefill_partial')
        scenario = _create_scenario(db)
        item = _create_item(db, scenario, chat_id=314)
        _row(db, user, item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        saved = EvaluationSessionService._batch_get_saved_evaluations(
            [item.item_id], user.id, 'labeling', scenario.id
        )
        assert saved[item.item_id]['category_id'] is None
        assert saved[item.item_id]['answers_json'] == PARTIAL_ANSWERS


# =============================================================================
# HelperFunctions progression enum
# =============================================================================

class TestProgressionState:

    def test_LABEL_STATUS_017_partial_row_is_progressing(self, app, db):
        """[LABEL_STATUS_017] get_thread_progression_state must report
        PROGRESSING, the enum the manager views render as 'in Bearbeitung'."""
        from db.models.scenario import ProgressionStatus
        from routes.HelperFunctions import get_thread_progression_state

        user = _create_user(db, 'prog_partial')
        scenario = _create_scenario(db)
        item = _create_item(db, scenario, chat_id=320)
        _row(db, user, item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        state = get_thread_progression_state(item, user.id, 7)
        assert state == ProgressionStatus.PROGRESSING

    def test_LABEL_STATUS_018_decided_and_empty_rows_unchanged(self, app, db):
        """[LABEL_STATUS_018] The existing two states keep their meaning."""
        from db.models.scenario import ProgressionStatus
        from routes.HelperFunctions import get_thread_progression_state

        user = _create_user(db, 'prog_states')
        scenario = _create_scenario(db)
        done_item = _create_item(db, scenario, chat_id=321)
        empty_item = _create_item(db, scenario, chat_id=322)
        _row(db, user, done_item, scenario, category_id='A')
        _row(db, user, empty_item, scenario)
        db.session.commit()

        assert get_thread_progression_state(done_item, user.id, 7) == ProgressionStatus.DONE
        assert get_thread_progression_state(empty_item, user.id, 7) == ProgressionStatus.NOT_STARTED


# =============================================================================
# Scenario stats aggregation
# =============================================================================

class TestScenarioStatsProgress:

    def test_LABEL_STATUS_019_batch_progression_states(self, app, db):
        """[LABEL_STATUS_019] The aggregate behind the progress bars counts a
        partial item as PROGRESSING, never as DONE."""
        from db.models.scenario import ProgressionStatus
        from services.scenario_stats_service import _batch_get_progression_states

        user = _create_user(db, 'stats_partial')
        scenario = _create_scenario(db)
        done_item = _create_item(db, scenario, chat_id=330)
        partial_item = _create_item(db, scenario, chat_id=331)
        untouched_item = _create_item(db, scenario, chat_id=332)
        _row(db, user, done_item, scenario, category_id='A')
        _row(db, user, partial_item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        states = _batch_get_progression_states(
            thread_ids=[done_item.item_id, partial_item.item_id, untouched_item.item_id],
            user_ids=[user.id],
            function_type_id=7,
            scenario_id=scenario.id,
        )
        assert states[(done_item.item_id, user.id)] == ProgressionStatus.DONE
        assert states[(partial_item.item_id, user.id)] == ProgressionStatus.PROGRESSING
        assert states[(untouched_item.item_id, user.id)] == ProgressionStatus.NOT_STARTED

    def test_LABEL_STATUS_020_progress_stats_counts_partial_separately(self, app, db):
        """[LABEL_STATUS_020] get_progress_stats surfaces the count, so a rater
        who answered questions is not reported as having done nothing."""
        from services.scenario_stats_service import get_progress_stats

        user = _create_user(db, 'stats_bars')
        scenario = _create_scenario(db)
        _add_member(db, scenario, user)
        done_item = _create_item(db, scenario, chat_id=333)
        partial_item = _create_item(db, scenario, chat_id=334)
        _create_item(db, scenario, chat_id=335)
        _row(db, user, done_item, scenario, category_id='A')
        _row(db, user, partial_item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        stats = get_progress_stats(scenario.id, skip_provenance=True)
        rater = next(r for r in stats['rater_stats'] if r['username'] == 'stats_bars')
        assert rater['done_threads'] == 1
        assert rater['progressing_threads'] == 1
        assert rater['not_started_threads'] == 1

    def test_LABEL_STATUS_021_decided_row_wins_over_partial_sibling(self, app, db):
        """[LABEL_STATUS_021] Conversation labeling writes one row per span. A
        decided span must keep the item at DONE even when a later span only
        holds answers — progress never regresses on a second row."""
        from db.models.scenario import ProgressionStatus
        from services.scenario_stats_service import _batch_get_progression_states

        user = _create_user(db, 'stats_spans')
        scenario = _create_scenario(db, 'Conv', ftype_id=9)
        item = _create_item(db, scenario, chat_id=336)
        _row(db, user, item, scenario, span_id='s1', category_id='A')
        _row(db, user, item, scenario, span_id='s2', answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        states = _batch_get_progression_states(
            thread_ids=[item.item_id], user_ids=[user.id],
            function_type_id=9, scenario_id=scenario.id,
        )
        assert states[(item.item_id, user.id)] == ProgressionStatus.DONE


# =============================================================================
# Conversation labeling: span progress
# =============================================================================

class TestSpanProgress:

    def _item_with_spans(self, db, scenario, span_ids, chat_id=340):
        return _create_item(
            db, scenario, subject='Gespräch', chat_id=chat_id,
            metadata_json={
                'conversation_labeling': {
                    'spans': [
                        {'span_id': sid, 'message_index': 1, 'message_id': 2,
                         'span_index': i, 'start': i * 10, 'end': i * 10 + 5}
                        for i, sid in enumerate(span_ids)
                    ],
                }
            },
        )

    def test_LABEL_STATUS_022_answered_span_makes_item_in_progress(self, app, db):
        """[LABEL_STATUS_022] "Started but not decided" must count at span level
        too, otherwise a conversation with answered questions reads as pending."""
        from services.evaluation.span_progress_service import item_status_map

        user = _create_user(db, 'span_partial')
        scenario = _create_scenario(db, 'Conv spans', ftype_id=9)
        item = self._item_with_spans(db, scenario, ['s1', 's2'])
        _row(db, user, item, scenario, span_id='s1', answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        assert item_status_map(scenario.id, user.id, [item.item_id])[item.item_id] == 'in_progress'

    def test_LABEL_STATUS_023_partial_span_does_not_complete_the_item(self, app, db):
        """[LABEL_STATUS_023] Only decided spans may complete a conversation."""
        from services.evaluation.span_progress_service import item_status_map, span_counts

        user = _create_user(db, 'span_not_done')
        scenario = _create_scenario(db, 'Conv spans 2', ftype_id=9)
        item = self._item_with_spans(db, scenario, ['s1', 's2'], chat_id=341)
        _row(db, user, item, scenario, span_id='s1', category_id='A')
        _row(db, user, item, scenario, span_id='s2', answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        assert item_status_map(scenario.id, user.id, [item.item_id])[item.item_id] == 'in_progress'
        # The span counter stays a count of DECISIONS.
        assert span_counts(scenario.id, user.id, [item.item_id]) == {'total': 2, 'done': 1}


# =============================================================================
# Export + IRR must not see partial rows as votes
# =============================================================================

class TestExportExclusion:

    def test_LABEL_STATUS_024_partial_row_is_not_exported_as_a_vote(self, app, db):
        """[LABEL_STATUS_024] A row without a decision would otherwise land in
        the results file with an empty vote_value_str."""
        from services.evaluation import results_export_service as export

        user = _create_user(db, 'export_partial')
        scenario = _create_scenario(db, 'Export')
        _add_member(db, scenario, user)
        done_item = _create_item(db, scenario, chat_id=350)
        partial_item = _create_item(db, scenario, chat_id=351)
        _row(db, user, done_item, scenario, category_id='A')
        _row(db, user, partial_item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        result = export.collect_results(scenario, include_llms=False)
        human_rows = [r for r in result['rows'] if r['voter_kind'] == 'human']
        assert [r['item_id'] for r in human_rows] == [done_item.item_id]
        assert human_rows[0]['vote_value_str'] == 'A'

    def test_LABEL_STATUS_025_unsure_row_is_still_exported(self, app, db):
        """[LABEL_STATUS_025] "Unsure" is a decision and must keep its row —
        the exclusion is about unfinished work, not about empty labels."""
        from services.evaluation import results_export_service as export

        user = _create_user(db, 'export_unsure')
        scenario = _create_scenario(db, 'Export unsure')
        _add_member(db, scenario, user)
        item = _create_item(db, scenario, chat_id=352)
        _row(db, user, item, scenario, is_unsure=True, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        result = export.collect_results(scenario, include_llms=False)
        human_rows = [r for r in result['rows'] if r['voter_kind'] == 'human']
        assert len(human_rows) == 1
        assert human_rows[0]['status'] == 'unsure'

    def test_LABEL_STATUS_026_partial_row_is_not_an_irr_unit(self, app, db):
        """[LABEL_STATUS_026] Feeding a label-less row into the agreement matrix
        would make one rater look like they voted 'nothing'."""
        from services.evaluation.agreement_metrics_service import AgreementMetricsService

        user_a = _create_user(db, 'irr_a')
        user_b = _create_user(db, 'irr_b')
        scenario = _create_scenario(db, 'IRR')
        _add_member(db, scenario, user_a)
        _add_member(db, scenario, user_b)
        item = _create_item(db, scenario, chat_id=353)
        _row(db, user_a, item, scenario, category_id='A')
        _row(db, user_b, item, scenario, answers_json=PARTIAL_ANSWERS)
        db.session.commit()

        from collections import defaultdict
        evaluations = {'raters': [], 'items': [], 'data': defaultdict(dict)}
        human_raters = AgreementMetricsService._collect_human_evaluations(
            scenario.id, 'labeling', [item.item_id], evaluations
        )
        assert human_raters == {f'human:{user_a.id}'}
        assert list(evaluations['data'][item.item_id]) == [f'human:{user_a.id}']
