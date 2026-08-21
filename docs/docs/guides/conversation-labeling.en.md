# Conversation Labeling

Conversation labeling (`function_type_id = 9`) is the scenario type for studies
that label **inside** a conversation: the category goes to each sense unit, not
to the message as a whole.

It was built for the VRM study (Verbal Response Modes, after Stiles), which codes
roughly 8,300 spans across 86 counselling threads.

## When to use it — and when not

| Situation | Type |
|-----------|------|
| One text gets **one** category | Labeling (7) |
| One conversation gets **one** category | Labeling (7), item = conversation |
| Every sense unit in the conversation gets **its own** category | **Conversation labeling (9)** |

The difference is not cosmetic. It decides what the numbers are computed over:

- **The unit of analysis** is the span, not the item. Krippendorff's alpha runs
  over span cells; one conversation contributes ~92 rows to the rater matrix,
  not one.
- **Progress** has a genuine middle state. A conversation is only complete once
  *every* span is decided — "40 of 92" is a normal state that classic labeling
  does not have.
- **Time on task** is measured per span, not per conversation.

## Segmentation comes from the import

Raters do **not** draw the spans. They are fixed at import time and frozen for
the duration of the study.

That is a methodological decision, not a technical limit: if everyone segmented
for themselves, the rows of the rater matrix would no longer be the same units,
and an agreement coefficient across them would not be interpretable. Disagreement
about the category could no longer be separated from disagreement about the cut.

When a boundary is plainly wrong there are two routes:

1. **Report it** through a dedicated label card (e.g. "wrong span boundary").
   This is the normal route — segmentation stays identical for everyone and the
   problem is documented.
2. **Split or merge** with the two understated tools at the bottom of the
   panel. Deliberately the exception.

## The interface

The conversation sits on the left as speech bubbles, the decision on the right.

**Turn by turn.** Only what has been said up to the current point is visible.
Once a counsellor message is fully labeled, the client's reply appears with an
animation and work continues at the first span of the next message. Later
messages stay hidden: raters should not know how the conversation ends.

**Auto-advance is on by default.** After a decision the focus jumps to the next
span. At ~92 decisions per conversation, clicking back into the text is
otherwise the single largest cost of the whole task. The switch remembers its
state. *Deselecting* does not advance — otherwise you could never get back to
correct something.

**Keyboard:** digits `1`–`9` pick a category, `Enter` advances, `Backspace`
steps back.

**Already-decided spans** carry their label inline in the text. That is how a
rater sees their own sequence — and notices two identical labels in a row, the
signal that this is really one block.

**Every selection saves immediately.** Embedded in the evaluation session the
layout hides its action bar and with it any save button — an interface that
waits for one persists nothing. That has already happened once in a production
study.

The free-text note is saved debounced (800 ms) rather than per keystroke, and
flushed the moment a span is left.

## Co-pilot

With the co-pilot enabled, a model suggestion with rationale and textual
evidence sits above the categories.

- **Never pre-selected.** Accepting costs a deliberate click.
- **Per span**, not per conversation — one suggestion for a whole thread would
  be worthless.
- **Same view as the human.** The server-built `{context}` follows the same
  visibility rules (`context_window`, `no_future_messages`). Otherwise the two
  would decide on different information and would not be comparable.
- **Hidden control subset.** A share of spans is served without a suggestion,
  decided server-side by a deterministic hash — reproducible, and never exposed
  to raters.
- **Helpfulness** can be rated with a thumbs vote, which lands on *that* span's
  log row.

## Splitting a span

A quiet text link "split span" sits at the bottom of the panel, above the note
field. It opens a
character-level cut picker: click into the text, see both halves as a preview,
confirm.

Three rules keep the study data honest:

- The cut must fall **strictly inside** — at the edge it would create a
  zero-length unit.
- New ids are **derived** (`x` → `x+a` / `x+b`), not renumbered. An earlier
  export still joins and untouched spans keep their ids.
- The vote on the old span is **deleted for every rater**, together with its
  co-pilot log row and timing. A decision about the whole span is not a decision
  about either half, and those measurements describe a unit that no longer
  exists.

## Merging spans

The reverse. Spans are marked with **ctrl/cmd-click** in the text — marked
spans get a dashed outline and the button shows the count. "Merge spans" stays
greyed out until the marking can actually become one unit.

Marking them yourself is the point: an earlier version picked the partner on its
own (the following span, else the preceding one). That read as arbitrary,
because nothing on screen said which neighbour was meant.

Any number can be marked; they merge when they form an **unbroken run** within
**one message**. Only **whitespace** may sit between them. That is not a
formality: in a real segmentation the separator belongs to no span — sentence
spans typically sit one space apart — and demanding exact contiguity would have
left the button dead in every genuine conversation. Absorbing a space is
harmless, absorbing words is not: nobody decided about those.

A plain click navigates as usual and **clears the marking** — otherwise a
forgotten selection would keep the button armed while you are somewhere else.

The new id is derived, and undoing a split is the common case: `x+a` + `x+b`
gives back plain `x`. A study that split and merged again carries exactly the
ids it started with.

Here too **both** votes disappear for every rater. Two decisions about two units
are not one decision about their union, and keeping either would put an opinion
in someone's mouth.

### "I'll just label both the same"

When two adjacent spans carry the same category, a prompt offers to merge them
in one click — both while standing on one of them and immediately afterwards,
when auto-advance has already moved on.

The click is deliberate: this must **not** happen automatically. The
segmentation is shared by every rater. If it changed based on *one* person's
labels, the units would shift under everyone else — and their votes on both
halves would be deleted. Two people would no longer be judging the same things,
which is precisely what makes an agreement coefficient meaningless.

For analysis, collapsing identical neighbours is an analysis step (block merge)
rather than an edit to the data.

Because both tools change the segmentation for *everyone*, they sit quietly at
the bottom above the note field — they should stay the exception rather than
compete with the label buttons.

## Analysis

In the scenario manager's evaluation tab, like any other type — except that the
unit is the span.

The export additionally carries `span_id`, `message_id` and `span_index`. The
`span_id` is a **stable string from the import**, not a running database id:
that is what keeps a re-import idempotent and lets exports from two points in
time be joined. The three columns sit at the end of the column list so analyses
that index by position keep working.

When an LLM takes part as an assessor, its "vote" for agreement is its
**primary suggestion** — exactly the one a human would have been shown.

## Creating one

Through the v1 scenario API with `type: "conversation_labeling"`. The exact data
format including validation rules is documented under
[Evaluation data formats](../entwickler/evaluation-datenformate.md#9-conversation-labeling-function_type_id--9).

In short: an item is a conversation, its messages carry `labelable: true|false`,
and labelable messages hold a list of spans with `span_id`, `start` and `end` —
character offsets into the message text, which is stored only **once**.

## Known limits

- The **LLM evaluator** (assessors tab) still runs this type through the
  whole-item classifier and would therefore produce one label per conversation
  rather than per span. For model comparison the co-pilot path is what counts,
  which works span by span.
- **Batch generation** across spans is not yet sized for the full study's
  volume.
