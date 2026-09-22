"""
Shared identity of the two labeling evaluation types.

There are two of them and they share almost their whole stack:

    7  labeling               one item  -> one decision
    9  conversation_labeling  one item (a whole conversation) -> one decision
                              PER SPAN inside it

Everything downstream — the vote table, the co-pilot, scenario parts, export,
agreement metrics — is identical; only the unit of decision differs, which is
why the vote/log/timing tables carry a ``span_id``.

Why this module exists
----------------------
The obvious way to add the second type is to append ``or x == 'conversation_labeling'``
to each of the ~20 places that currently test for ``'labeling'``. That is
exactly how ``communication_comparison`` (type 8) was added, and it is still
missing from a dozen dispatchers years later — the v1 serializer reported those
scenarios as "rating", and their LLM evaluators silently never ran, because two
branches were overlooked.

So: one definition, imported everywhere. Adding a third labeling flavour later
means changing this file, not hunting for branches.

This mirrors the existing ``HelperFunctions.COMPARISON_FUNCTION_TYPE_IDS = (4, 8)``
idiom for the comparison family.

The module carries a second shared rule for the same reason: when is one
labeling row *done*, and when is it merely *in progress*? See the
"Per-row status" section at the bottom.
"""

from typing import Optional, Union

# --- Individual ids (kept for call sites that mean *specifically* one type) ---
LABELING_FUNCTION_TYPE_ID = 7
CONVERSATION_LABELING_FUNCTION_TYPE_ID = 9

# --- The family ---------------------------------------------------------------
LABELING_FUNCTION_TYPE_IDS = (
    LABELING_FUNCTION_TYPE_ID,
    CONVERSATION_LABELING_FUNCTION_TYPE_ID,
)

LABELING_TYPE_NAME = "labeling"
CONVERSATION_LABELING_TYPE_NAME = "conversation_labeling"

LABELING_TYPE_NAMES = (LABELING_TYPE_NAME, CONVERSATION_LABELING_TYPE_NAME)


def is_labeling_type(function_type: Optional[Union[str, int]]) -> bool:
    """True for BOTH labeling flavours (accepts a type name or a numeric id).

    Use this wherever the logic is "this is a labeling scenario" — label sets,
    co-pilot, parts, the ItemLabelingEvaluation vote table.
    """
    if function_type is None:
        return False
    if isinstance(function_type, int):
        return function_type in LABELING_FUNCTION_TYPE_IDS
    return str(function_type) in LABELING_TYPE_NAMES


def is_span_labeling(function_type: Optional[Union[str, int]]) -> bool:
    """True only for conversation labeling — the flavour with one vote per span.

    Use this for the parts that genuinely differ: span-aware progress, the
    per-span co-pilot key, span columns in the export.
    """
    if function_type is None:
        return False
    if isinstance(function_type, int):
        return function_type == CONVERSATION_LABELING_FUNCTION_TYPE_ID
    return str(function_type) == CONVERSATION_LABELING_TYPE_NAME


# =============================================================================
# Per-row status ("has this rater finished this labeling case?")
# =============================================================================
#
# Question-first labeling (see DecisionQuestionsConfig) puts one or more
# decision questions IN FRONT of the label, and every click is persisted
# immediately. A row can therefore exist while the rater is still working:
# answers saved, no label yet. Before this rule existed such a row was
# indistinguishable from "nothing happened" and the item kept showing
# "ausstehend" while the answers were already in the database — the rater on
# production scenario 758 answered two of three questions, navigated away and
# saw no trace of it.
#
# "Done" therefore stays exactly what it always was (a label, or an explicit
# "unsure"), and everything between an empty row and that decision becomes
# "in_progress". The rule lives HERE and nowhere else, because the per-item
# status is computed in five independent places (session batch view, single
# item lookup, HelperFunctions progression, scenario stats, span progress) —
# the classic rule only agreed across them by coincidence, and a second,
# subtler rule would not have stayed in sync.

LABELING_STATUS_DONE = "done"
LABELING_STATUS_IN_PROGRESS = "in_progress"
LABELING_STATUS_PENDING = "pending"

# Ordering for "take the strongest status seen" — conversation labeling holds
# many rows per item, and a single decided span must not be hidden by a later
# partial one.
_LABELING_STATUS_RANK = {
    LABELING_STATUS_PENDING: 0,
    LABELING_STATUS_IN_PROGRESS: 1,
    LABELING_STATUS_DONE: 2,
}


def _non_empty_json(value) -> bool:
    """True when an ``answers_json``-shaped value carries actual content.

    Tolerates the column coming back as a JSON *string* (older MariaDB/driver
    combinations and raw-SQL reads hand back text rather than a dict), so the
    rule does not silently change meaning depending on how the row was loaded.
    """
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() not in ("", "{}", "[]", "null")
    return bool(value)


def labeling_row_is_decided(row) -> bool:
    """True when the row holds the study datum: a label, or an explicit "unsure".

    This is the ONLY thing that counts as a completed case — and the only thing
    that may be exported as a vote or fed into the IRR.
    """
    if row is None:
        return False
    if getattr(row, "category_id", None) is not None:
        return True
    return bool(getattr(row, "is_unsure", False))


def labeling_row_has_partial_input(row) -> bool:
    """True when the row exists and holds rater input, but no decision yet.

    That is: answered decision questions, a second choice, or free-text
    feedback. An empty row (created by some other path, or a save that cleared
    everything) is NOT partial input — it is indistinguishable from nothing.
    """
    if row is None or labeling_row_is_decided(row):
        return False
    if _non_empty_json(getattr(row, "answers_json", None)):
        return True
    if getattr(row, "second_choice_id", None):
        return True
    feedback = getattr(row, "feedback", None)
    return bool(feedback and str(feedback).strip())


def labeling_row_status(row) -> str:
    """``'done' | 'in_progress' | 'pending'`` for ONE ItemLabelingEvaluation row.

    ``None`` (no row at all) is ``'pending'``, so callers can pass the result of
    a ``.first()`` straight in.
    """
    if labeling_row_is_decided(row):
        return LABELING_STATUS_DONE
    if labeling_row_has_partial_input(row):
        return LABELING_STATUS_IN_PROGRESS
    return LABELING_STATUS_PENDING


def strongest_labeling_status(*statuses) -> str:
    """The furthest-advanced of the given statuses (pending < in_progress < done).

    Needed wherever one key aggregates several rows — conversation labeling
    writes one row per span, so an item is as advanced as its best span.
    """
    best = LABELING_STATUS_PENDING
    for status in statuses:
        if _LABELING_STATUS_RANK.get(status, 0) > _LABELING_STATUS_RANK[best]:
            best = status
    return best


def labeling_decided_clause():
    """SQL twin of :func:`labeling_row_is_decided` (an ``ItemLabelingEvaluation``
    filter clause).

    Exists so the batch queries that must not load every ``feedback`` /
    ``answers_json`` blob into Python (scenario stats runs over ~100 items x
    ~90 spans x N raters) can still apply the same rule. The twins are kept
    side by side here and are pinned together by a unit test that runs both
    over the same matrix of rows.
    """
    from sqlalchemy import or_
    from db.models.scenario import ItemLabelingEvaluation as _Row

    return or_(_Row.category_id.isnot(None), _Row.is_unsure.is_(True))


# Serialized forms of "this JSON column holds nothing". A JSON column is NOT
# simply NULL when the attribute was set to Python None: SQLAlchemy's JSON type
# persists None as the JSON value ``null`` (SQL NULL needs an explicit
# ``JSON.NULL`` / ``none_as_null=True``). Every classic labeling row therefore
# has a non-NULL answers_json, and a naive ``answers_json IS NOT NULL`` would
# classify every untouched row as work in progress.
_EMPTY_JSON_TEXT = ("null", "{}", "[]", "")


def labeling_partial_clause():
    """SQL twin of :func:`labeling_row_has_partial_input` (undecided rows only).

    Compares answers_json as TEXT rather than testing for SQL NULL — see
    ``_EMPTY_JSON_TEXT`` for why. The cast renders as ``CAST(x AS CHAR)`` on
    MariaDB and ``CAST(x AS VARCHAR)`` on SQLite, and both store exactly the
    string the JSON serializer produced, so the comparison is portable.
    """
    from sqlalchemy import String, and_, cast, not_, or_
    from db.models.scenario import ItemLabelingEvaluation as _Row

    return and_(
        not_(labeling_decided_clause()),
        or_(
            and_(
                _Row.answers_json.isnot(None),
                cast(_Row.answers_json, String).notin_(_EMPTY_JSON_TEXT),
            ),
            _Row.second_choice_id.isnot(None),
            and_(_Row.feedback.isnot(None), _Row.feedback != ""),
        ),
    )
