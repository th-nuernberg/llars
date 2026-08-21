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
