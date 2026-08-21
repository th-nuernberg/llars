"""
Unit tests for span-level progress (conversation labeling, function_type 9).

Classic labeling asks one question per item, so "done" is a single row lookup.
Conversation labeling asks one question per SPAN, so an item is done only when
every span in it has a decision — and, unlike classic labeling, it has a real
intermediate state: one conversation is ~92 spans and roughly 20 minutes of
work, so a rater must be able to see "40 of 92" rather than a flat "pending"
for most of a working day.

The span inventory lives on ``EvaluationItem.metadata_json`` under a reserved
key (written by the v1 importer); these tests build that structure directly so
they stay independent of the import path.

Test IDs: [SPANPROG-001] through [SPANPROG-014]
"""

import pytest


CL_KEY = "conversation_labeling"


# =============================================================================
# Helpers
# =============================================================================

def _create_user(db_session, username):
    from db.models.user import User
    import hashlib

    api_key = f'test-api-key-{hashlib.md5(username.encode()).hexdigest()[:16]}'
    user = User(username=username, password_hash='x', api_key=api_key, is_active=True)
    db_session.session.add(user)
    db_session.session.flush()
    return user


def _create_scenario(db_session, name='Conv Scenario'):
    from db.models.scenario import RatingScenarios, FeatureFunctionType

    if not FeatureFunctionType.query.get(9):
        db_session.session.add(
            FeatureFunctionType(function_type_id=9, name='conversation_labeling')
        )
        db_session.session.flush()

    scenario = RatingScenarios(
        scenario_name=name, function_type_id=9, created_by='creator', config_json={}
    )
    db_session.session.add(scenario)
    db_session.session.flush()
    return scenario


def _create_item_with_spans(db_session, span_ids, chat_id=1):
    """Item carrying the span index the importer would have written."""
    from db.models.scenario import EvaluationItem

    item = EvaluationItem(
        subject='Conversation',
        chat_id=chat_id,
        function_type_id=9,
        metadata_json={
            'subcorpus': 'gemco_A',          # study metadata must survive
            CL_KEY: {
                'spans': [
                    {'span_id': sid, 'message_index': 1, 'message_id': 2,
                     'span_index': i, 'start': i * 10, 'end': i * 10 + 5}
                    for i, sid in enumerate(span_ids)
                ],
                'labelable_messages': [1],
            },
        },
    )
    db_session.session.add(item)
    db_session.session.flush()
    return item


def _vote(db_session, user, item, scenario, span_id, category_id='D', is_unsure=False):
    from db.models.scenario import ItemLabelingEvaluation

    row = ItemLabelingEvaluation(
        user_id=user.id, item_id=item.item_id, scenario_id=scenario.id,
        span_id=span_id, category_id=category_id, is_unsure=is_unsure,
    )
    db_session.session.add(row)
    db_session.session.flush()
    return row


def _svc():
    from services.evaluation import span_progress_service
    return span_progress_service


# =============================================================================
# Span inventory
# =============================================================================

class TestSpanInventory:

    def test_SPANPROG_001_reads_span_ids_from_metadata(self, app, db, app_context):
        """[SPANPROG-001] The ordered span ids come out of the item metadata."""
        item = _create_item_with_spans(db, ['s1', 's2', 's3'])
        assert _svc().span_ids_for_items([item.item_id])[item.item_id] == ['s1', 's2', 's3']

    def test_SPANPROG_002_item_without_span_index_is_empty(self, app, db, app_context):
        """[SPANPROG-002] A non-conversation item yields [], not a crash."""
        from db.models.scenario import EvaluationItem

        item = EvaluationItem(subject='Plain', chat_id=99, metadata_json={'axis': 'x'})
        db.session.add(item)
        db.session.flush()
        assert _svc().span_ids_for_items([item.item_id])[item.item_id] == []

    def test_SPANPROG_003_tolerates_missing_and_malformed_metadata(self, app, db, app_context):
        """[SPANPROG-003] NULL / wrong-shaped metadata degrades to empty."""
        svc = _svc()
        assert svc.span_ids_from_metadata(None) == []
        assert svc.span_ids_from_metadata({}) == []
        assert svc.span_ids_from_metadata({CL_KEY: 'nonsense'}) == []
        assert svc.span_ids_from_metadata({CL_KEY: {'spans': 'nope'}}) == []
        assert svc.span_ids_from_metadata({CL_KEY: {'spans': [{'no_id': 1}]}}) == []

    def test_SPANPROG_004_empty_input_is_a_noop(self, app, db, app_context):
        """[SPANPROG-004] No item ids means no query and no error."""
        assert _svc().span_ids_for_items([]) == {}


# =============================================================================
# Item status
# =============================================================================

class TestItemStatus:

    def test_SPANPROG_005_no_votes_is_pending(self, app, db, app_context):
        """[SPANPROG-005] Nothing decided yet."""
        u = _create_user(db, 'sp_u1')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1', 's2'])
        status = _svc().item_status_map(sc.id, u.id, [item.item_id])
        assert status[item.item_id] == 'pending'

    def test_SPANPROG_006_some_votes_is_in_progress(self, app, db, app_context):
        """[SPANPROG-006] Partial work is visible — the whole point of the type.

        Classic labeling is binary; here a rater can sit inside one item for
        ~20 minutes, so "in_progress" has to exist.
        """
        u = _create_user(db, 'sp_u2')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1', 's2', 's3'])
        _vote(db, u, item, sc, 's1')
        status = _svc().item_status_map(sc.id, u.id, [item.item_id])
        assert status[item.item_id] == 'in_progress'

    def test_SPANPROG_007_all_spans_voted_is_done(self, app, db, app_context):
        """[SPANPROG-007] Done requires EVERY span, not just one."""
        u = _create_user(db, 'sp_u3')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1', 's2'])
        _vote(db, u, item, sc, 's1')
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'in_progress'
        _vote(db, u, item, sc, 's2')
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'done'

    def test_SPANPROG_008_unsure_counts_as_a_decision(self, app, db, app_context):
        """[SPANPROG-008] 'Unsure' is a decision, mirroring classic labeling."""
        u = _create_user(db, 'sp_u4')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1'])
        _vote(db, u, item, sc, 's1', category_id=None, is_unsure=True)
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'done'

    def test_SPANPROG_009_empty_row_is_not_a_decision(self, app, db, app_context):
        """[SPANPROG-009] A row with neither category nor unsure does not count."""
        u = _create_user(db, 'sp_u5')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1'])
        _vote(db, u, item, sc, 's1', category_id=None, is_unsure=False)
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'pending'

    def test_SPANPROG_010_votes_on_unknown_spans_do_not_complete(self, app, db, app_context):
        """[SPANPROG-010] A stale vote for a removed span cannot fake completion.

        Guards re-imports: if the inventory shrinks or ids change, leftover
        rows must not make an item look finished.
        """
        u = _create_user(db, 'sp_u6')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1', 's2'])
        _vote(db, u, item, sc, 'ghost-span')
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'pending'

    def test_SPANPROG_011_votes_are_per_user(self, app, db, app_context):
        """[SPANPROG-011] One rater finishing does not finish it for the other."""
        u1 = _create_user(db, 'sp_a')
        u2 = _create_user(db, 'sp_b')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, ['s1'])
        _vote(db, u1, item, sc, 's1')
        assert _svc().item_status_map(sc.id, u1.id, [item.item_id])[item.item_id] == 'done'
        assert _svc().item_status_map(sc.id, u2.id, [item.item_id])[item.item_id] == 'pending'

    def test_SPANPROG_012_item_without_spans_stays_pending(self, app, db, app_context):
        """[SPANPROG-012] Nothing to do must not be reported as done."""
        u = _create_user(db, 'sp_u7')
        sc = _create_scenario(db)
        item = _create_item_with_spans(db, [])
        assert _svc().item_status_map(sc.id, u.id, [item.item_id])[item.item_id] == 'pending'


# =============================================================================
# Aggregate counts
# =============================================================================

class TestSpanCounts:

    def test_SPANPROG_013_counts_spans_not_items(self, app, db, app_context):
        """[SPANPROG-013] Progress is measured in spans across all items."""
        u = _create_user(db, 'sp_u8')
        sc = _create_scenario(db)
        i1 = _create_item_with_spans(db, ['a1', 'a2', 'a3'], chat_id=1)
        i2 = _create_item_with_spans(db, ['b1', 'b2'], chat_id=2)
        _vote(db, u, i1, sc, 'a1')
        _vote(db, u, i1, sc, 'a2')
        _vote(db, u, i2, sc, 'b1')

        counts = _svc().span_counts(sc.id, u.id, [i1.item_id, i2.item_id])
        assert counts == {'total': 5, 'done': 3}

    def test_SPANPROG_014_study_metadata_survives_alongside_spans(self, app, db, app_context):
        """[SPANPROG-014] The reserved key must not shadow research metadata.

        Both live in the same JSON blob; losing 'subcorpus' would silently
        break the study's own sampling analysis.
        """
        item = _create_item_with_spans(db, ['s1'])
        assert item.metadata_json['subcorpus'] == 'gemco_A'
        assert CL_KEY in item.metadata_json


# =============================================================================
# Span splitting
#
# The unitizing is frozen at import time on purpose — re-segmenting mid-study
# would make units incomparable between raters. Splitting is the sanctioned
# exception for a span that plainly carries two intents, so its guarantees
# matter more than usual: no zero-length units, derived ids, and no vote
# silently surviving onto a unit nobody actually judged.
#
# Test IDs: [SPANSPLIT-001] through [SPANSPLIT-008]
# =============================================================================

class TestSpanSplit:

    def _svc(self):
        from services.evaluation import span_progress_service
        return span_progress_service

    def test_SPANSPLIT_001_splits_into_two_at_the_offset(self, app, db, app_context):
        """[SPANSPLIT-001] One span becomes two, boundaries meet at the offset."""
        item = _create_item_with_spans(db, ['s1', 's2'])
        # s1 spans [0,5) per the helper; cut at 3.
        out = self._svc().split_span(item, 's1', 3)
        spans = out['spans']

        assert len(spans) == 3
        left, right = spans[0], spans[1]
        assert (left['span_id'], right['span_id']) == ('s1+a', 's1+b')
        assert left['start'] == 0 and left['end'] == 3
        assert right['start'] == 3 and right['end'] == 5

    def test_SPANSPLIT_002_keeps_reading_order(self, app, db, app_context):
        """[SPANSPLIT-002] The halves stay in place; later spans follow."""
        item = _create_item_with_spans(db, ['s1', 's2', 's3'])
        spans = self._svc().split_span(item, 's2', 13)['spans']
        assert [s['span_id'] for s in spans] == ['s1', 's2+a', 's2+b', 's3']

    def test_SPANSPLIT_003_renumbers_span_index_densely(self, app, db, app_context):
        """[SPANSPLIT-003] span_index stays a dense sequence.

        The interface walks the spans positionally; a gap would make it skip.
        """
        item = _create_item_with_spans(db, ['s1', 's2', 's3'])
        spans = self._svc().split_span(item, 's1', 3)['spans']
        assert [s['span_index'] for s in spans] == [0, 1, 2, 3]

    def test_SPANSPLIT_004_rejects_offset_on_the_boundary(self, app, db, app_context):
        """[SPANSPLIT-004] Cutting at an edge would create a zero-length unit."""
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1'])
        for bad in (0, 5):
            with _pytest.raises(ValueError):
                self._svc().split_span(item, 's1', bad)

    def test_SPANSPLIT_005_rejects_offset_outside_the_span(self, app, db, app_context):
        """[SPANSPLIT-005] An offset in a neighbouring span is not a split."""
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1', 's2'])
        with _pytest.raises(ValueError):
            self._svc().split_span(item, 's1', 12)

    def test_SPANSPLIT_006_rejects_unknown_span(self, app, db, app_context):
        """[SPANSPLIT-006] Unknown span id fails loudly."""
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1'])
        with _pytest.raises(ValueError):
            self._svc().split_span(item, 'does-not-exist', 2)

    def test_SPANSPLIT_007_ids_are_derived_not_renumbered(self, app, db, app_context):
        """[SPANSPLIT-007] Untouched spans keep their ids.

        Renumbering everything would orphan every vote and every exported row
        that referenced the old ids.
        """
        item = _create_item_with_spans(db, ['alpha', 'beta', 'gamma'])
        spans = self._svc().split_span(item, 'beta', 13)['spans']
        ids = [s['span_id'] for s in spans]
        assert 'alpha' in ids and 'gamma' in ids
        assert 'beta' not in ids

    def test_SPANSPLIT_008_carries_message_binding(self, app, db, app_context):
        """[SPANSPLIT-008] Both halves stay bound to the same message."""
        item = _create_item_with_spans(db, ['s1'])
        spans = self._svc().split_span(item, 's1', 3)['spans']
        assert spans[0]['message_index'] == spans[1]['message_index'] == 1
        assert spans[0]['message_id'] == spans[1]['message_id'] == 2


# =============================================================================
# Span merging
#
# The counterpart to splitting, and it carries the same weight: it changes the
# unit of analysis for EVERY rater, not just the one who clicked. So the
# rejections matter as much as the happy path — a merge across a gap or across
# a message boundary would produce a "unit" whose text does not exist as a
# contiguous string anywhere in the conversation.
#
# Test IDs: [SPANMERGE-001] through [SPANMERGE-007]
# =============================================================================

class TestSpanMerge:

    def _svc(self):
        from services.evaluation import span_progress_service
        return span_progress_service

    def _contiguous(self, db_session, ids):
        """Item whose spans actually touch (the shared helper leaves gaps)."""
        item = _create_item_with_spans(db_session, ids)
        spans = item.metadata_json[CL_KEY]['spans']
        cursor = 0
        for s in spans:
            s['start'] = cursor
            s['end'] = cursor + 5
            cursor += 5
        return item

    def test_SPANMERGE_001_joins_two_adjacent_spans(self, app, db, app_context):
        """[SPANMERGE-001] Two units become one spanning both."""
        item = self._contiguous(db, ['s1', 's2', 's3'])
        out = self._svc().merge_spans(item, ['s1', 's2'])
        spans = out['spans']

        assert len(spans) == 2
        assert spans[0]['start'] == 0 and spans[0]['end'] == 10
        assert out['removed_ids'] == ('s1', 's2')
        assert spans[1]['span_id'] == 's3'

    def test_SPANMERGE_002_undoing_a_split_restores_the_original_id(self, app, db, app_context):
        """[SPANMERGE-002] split then merge lands exactly where it started.

        Without this, a study that cut and reverted would carry ids like
        's1+a+m' forever and no longer join onto its own earlier export.
        """
        item = _create_item_with_spans(db, ['s1', 's2'])
        split = self._svc().split_span(item, 's1', 3)
        item.metadata_json[CL_KEY]['spans'] = split['spans']

        out = self._svc().merge_spans(item, ['s1+a', 's1+b'])
        assert out['new_id'] == 's1'
        assert [s['span_id'] for s in out['spans']] == ['s1', 's2']

    def test_SPANMERGE_003_order_of_arguments_does_not_matter(self, app, db, app_context):
        """[SPANMERGE-003] The caller should not have to know reading order."""
        item = self._contiguous(db, ['s1', 's2'])
        out = self._svc().merge_spans(item, ['s2', 's1'])
        assert out['spans'][0]['start'] == 0 and out['spans'][0]['end'] == 10

    def test_SPANMERGE_004_rejects_non_adjacent_spans(self, app, db, app_context):
        """[SPANMERGE-004] Merging across a third span would swallow it."""
        import pytest as _pytest
        item = self._contiguous(db, ['s1', 's2', 's3'])
        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's3'])

    def test_SPANMERGE_005_rejects_a_gap_between_the_spans(self, app, db, app_context):
        """[SPANMERGE-005] Text between two spans was never decided about.

        The default fixture leaves 5 characters between spans; merging across
        that would quietly pull unjudged text into a labeled unit.
        """
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1', 's2'])
        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's2'])

    def test_SPANMERGE_006_rejects_spans_from_different_messages(self, app, db, app_context):
        """[SPANMERGE-006] The union would not exist as contiguous text."""
        import pytest as _pytest
        item = self._contiguous(db, ['s1', 's2'])
        item.metadata_json[CL_KEY]['spans'][1]['message_index'] = 3
        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's2'])

    def test_SPANMERGE_007_renumbers_span_index_densely(self, app, db, app_context):
        """[SPANMERGE-007] The interface walks spans positionally."""
        item = self._contiguous(db, ['s1', 's2', 's3', 's4'])
        spans = self._svc().merge_spans(item, ['s2', 's3'])['spans']
        assert [s['span_index'] for s in spans] == [0, 1, 2]

    def test_SPANMERGE_008_drops_stale_text_field(self, app, db, app_context):
        """[SPANMERGE-008] A carried-over `text` would describe only one half.

        The offsets are the truth; a leftover snippet would make the export
        disagree with the conversation it came from.
        """
        item = self._contiguous(db, ['s1', 's2'])
        item.metadata_json[CL_KEY]['spans'][0]['text'] = 'only the first half'
        out = self._svc().merge_spans(item, ['s1', 's2'])
        assert 'text' not in out['spans'][0]

    def test_SPANMERGE_009_merges_a_run_of_three(self, app, db, app_context):
        """[SPANMERGE-009] The rater picks the spans, so more than two is normal.

        Merging only the first two of a three-span selection would silently do
        something other than what was marked.
        """
        item = self._contiguous(db, ['s1', 's2', 's3', 's4'])
        out = self._svc().merge_spans(item, ['s1', 's2', 's3'])
        spans = out['spans']
        assert len(spans) == 2
        assert spans[0]['start'] == 0 and spans[0]['end'] == 15
        assert out['removed_ids'] == ('s1', 's2', 's3')
        assert spans[1]['span_id'] == 's4'

    def test_SPANMERGE_010_rejects_a_run_with_a_hole(self, app, db, app_context):
        """[SPANMERGE-010] Selecting 1 and 3 but not 2 would swallow 2."""
        import pytest as _pytest
        item = self._contiguous(db, ['s1', 's2', 's3'])
        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's3'])

    def test_SPANMERGE_011_rejects_fewer_than_two(self, app, db, app_context):
        """[SPANMERGE-011] One span is not a merge; duplicates are not two."""
        import pytest as _pytest
        item = self._contiguous(db, ['s1', 's2'])
        for bad in ([], ['s1'], ['s1', 's1']):
            with _pytest.raises(ValueError):
                self._svc().merge_spans(item, bad)

    def test_SPANMERGE_012_ignores_the_order_they_were_marked_in(self, app, db, app_context):
        """[SPANMERGE-012] ctrl-clicking right-to-left must work the same."""
        item = self._contiguous(db, ['s1', 's2', 's3'])
        out = self._svc().merge_spans(item, ['s3', 's1', 's2'])
        assert out['spans'][0]['start'] == 0 and out['spans'][0]['end'] == 15

    def test_SPANMERGE_013_absorbs_a_whitespace_separator(self, app, db, app_context):
        """[SPANMERGE-013] Real segmentations leave the space out of every span.

        Sentence spans sit one character apart. Demanding exact contiguity
        greyed the merge control out on every genuine conversation — the demo
        item's spans are all separated by a single space.
        """
        item = _create_item_with_spans(db, ['s1', 's2'])
        spans = item.metadata_json[CL_KEY]['spans']
        spans[0]['start'], spans[0]['end'] = 0, 5
        spans[1]['start'], spans[1]['end'] = 6, 11        # one space between
        text = 'Hallo Welt!'

        out = self._svc().merge_spans(item, ['s1', 's2'], message_text=text)
        assert out['spans'][0]['start'] == 0 and out['spans'][0]['end'] == 11

    def test_SPANMERGE_014_still_refuses_to_swallow_words(self, app, db, app_context):
        """[SPANMERGE-014] Absorbing a space is harmless; absorbing text is not.

        Anything between the spans that is not whitespace was never decided
        about and must not silently become part of a labeled unit.
        """
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1', 's2'])
        spans = item.metadata_json[CL_KEY]['spans']
        spans[0]['start'], spans[0]['end'] = 0, 5
        spans[1]['start'], spans[1]['end'] = 12, 17
        text = 'Hallo ganz Welt!!'

        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's2'], message_text=text)

    def test_SPANMERGE_015_without_text_stays_strict(self, app, db, app_context):
        """[SPANMERGE-015] No text to inspect -> conservative reading.

        A caller that cannot supply the message must not accidentally get the
        permissive rule; it cannot tell a space from a word.
        """
        import pytest as _pytest
        item = _create_item_with_spans(db, ['s1', 's2'])
        spans = item.metadata_json[CL_KEY]['spans']
        spans[0]['start'], spans[0]['end'] = 0, 5
        spans[1]['start'], spans[1]['end'] = 6, 11

        with _pytest.raises(ValueError):
            self._svc().merge_spans(item, ['s1', 's2'])
