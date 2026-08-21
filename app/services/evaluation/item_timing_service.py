"""Per-case evaluation timing service.

Single write path for ``EvaluationItemTiming`` — the generic "time on item"
measure shared by all six evaluation types. Each rater interface sends
``time_on_item_ms`` (client-measured: item-shown → first save) with its vote;
the submit endpoints call :meth:`ItemTimingService.record_item_timing` to persist
it, first-write-only.

Read side (export): :meth:`timings_for_scenario` batch-loads the map the v1 and
legacy exports join against.

See: app/db/models/evaluation_item_timing.py for the storage rationale.
"""

from __future__ import annotations

import logging
import statistics
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from db import db
from db.models.evaluation_item_timing import EvaluationItemTiming

logger = logging.getLogger(__name__)


class ItemTimingService:
    """Persist and read per-(user, item, scenario) time-on-case values."""

    @staticmethod
    def coerce_ms(value: Any) -> Optional[int]:
        """Best-effort parse of a client-supplied duration into a non-negative
        int of milliseconds. Returns None for missing/garbage input so a bad
        client value never blocks the actual vote from being saved."""
        if value is None:
            return None
        try:
            ms = int(round(float(value)))
        except (TypeError, ValueError):
            return None
        if ms < 0:
            return None
        # Cap absurd values (> 24h) — almost certainly a client clock glitch or a
        # tab left open for a day; keep the column meaningful for the mean/median.
        return min(ms, 24 * 60 * 60 * 1000)

    @staticmethod
    def extract_from_payload(data: Optional[Dict[str, Any]]) -> Optional[int]:
        """Pull the timing value from a submit request body.

        Accepts a top-level ``time_on_item_ms`` (the uniform contract every
        interface now sends) or a nested ``timing.time_on_item_ms`` /
        ``copilot.time_on_item_ms`` (labeling's existing shape), so the caller
        doesn't have to know which the client used.
        """
        if not isinstance(data, dict):
            return None
        if "time_on_item_ms" in data:
            return ItemTimingService.coerce_ms(data.get("time_on_item_ms"))
        for nested_key in ("timing", "copilot"):
            nested = data.get(nested_key)
            if isinstance(nested, dict) and "time_on_item_ms" in nested:
                return ItemTimingService.coerce_ms(nested.get("time_on_item_ms"))
        return None

    @staticmethod
    def record_item_timing(
        scenario_id: int,
        user_id: int,
        item_id: int,
        time_on_item_ms: Optional[int],
        function_type: Optional[str] = None,
        span_id: str = "",
    ) -> Optional[EvaluationItemTiming]:
        """Upsert the timing row for one case, first-write-only.

        No-op when ``time_on_item_ms`` is None/invalid. Adds/updates the row on
        the current session but does NOT commit — the calling submit endpoint
        commits it together with the vote (so timing and vote persist atomically
        or not at all). First-write-only: once a value exists it is never
        overwritten, so revisits/corrections keep the primary time-to-first-save.

        ``span_id`` distinguishes the cases of a conversation-labeling item:
        there one item holds ~92 separate decisions, and each needs its own
        measurement. With the old (user, item, scenario) key only the FIRST
        span of a conversation would ever be timed and the remaining ones would
        collide with the unique constraint — silently, since this path is
        best-effort. ``""`` keeps every other type on exactly one row per item.
        """
        ms = ItemTimingService.coerce_ms(time_on_item_ms)
        if ms is None:
            return None

        row = EvaluationItemTiming.query.filter_by(
            user_id=user_id, item_id=item_id, scenario_id=scenario_id,
            span_id=span_id
        ).first()
        if row is None:
            row = EvaluationItemTiming(
                scenario_id=scenario_id,
                item_id=item_id,
                user_id=user_id,
                span_id=span_id,
                function_type=function_type,
                time_on_item_ms=ms,
            )
            db.session.add(row)
        elif row.time_on_item_ms is None:
            # First real value for a row that existed without timing.
            row.time_on_item_ms = ms
            if function_type and not row.function_type:
                row.function_type = function_type
        # else: already timed → leave untouched (first-write-only).
        return row

    @staticmethod
    def resolve_scenario_id(
        item_id: int, preferred: Any = None
    ) -> Optional[int]:
        """Pick the scenario a per-case timing row belongs to.

        The ranking and authenticity submit routes are thread-scoped (no
        scenario in the URL) and a thread can belong to several scenarios.
        Trust a client-supplied ``preferred`` id only if it is actually one of
        the thread's scenarios (so a spoofed id can't attach timing to an
        unrelated scenario); otherwise fall back to the thread's first scenario.

        Resolved directly from the ``scenario_items`` link table — the canonical
        item↔scenario mapping — rather than via scenario_stats_service, to avoid
        pulling the routes import graph into this leaf service.
        """
        from db.models.scenario import ScenarioItems

        sids = [
            si.scenario_id
            for si in ScenarioItems.query.filter_by(item_id=item_id).all()
        ]
        try:
            p = int(preferred) if preferred is not None else None
        except (TypeError, ValueError):
            p = None
        if p is not None and p in sids:
            return p
        return sids[0] if sids else None

    @staticmethod
    def record_for_thread(
        item_id: int,
        user_id: int,
        time_on_item_ms: Any,
        preferred_scenario_id: Any = None,
        function_type: Optional[str] = None,
    ) -> Optional[EvaluationItemTiming]:
        """Convenience wrapper for thread-scoped routes: resolve the scenario
        from the thread, then record. No-op if timing or scenario can't be
        resolved."""
        ms = ItemTimingService.coerce_ms(time_on_item_ms)
        if ms is None:
            return None
        scenario_id = ItemTimingService.resolve_scenario_id(
            item_id, preferred_scenario_id
        )
        if scenario_id is None:
            return None
        return ItemTimingService.record_item_timing(
            scenario_id, user_id, item_id, ms, function_type=function_type
        )

    @staticmethod
    def timings_for_scenario(scenario_id: int) -> Dict[Tuple[int, int, str], int]:
        """Return ``{(user_id, item_id, span_id): time_on_item_ms}``.

        Only rows with a non-null time are included, so the export can treat a
        missing key as "not captured" and fall back to the derived measure.

        The span segment is part of the key because conversation labeling stores
        one timing row PER SPAN: keying by (user, item) alone would collapse ~92
        rows per conversation and hand every span the same duration. Types
        without spans store '' there, so the key degrades cleanly.
        """
        rows = EvaluationItemTiming.query.filter(
            EvaluationItemTiming.scenario_id == scenario_id,
            EvaluationItemTiming.time_on_item_ms.isnot(None),
        ).all()
        return {
            (r.user_id, r.item_id, r.span_id or ""): r.time_on_item_ms
            for r in rows
        }

    @staticmethod
    def derive_deltas(
        pairs: List[Tuple[Any, Any, Optional[str]]]
    ) -> Dict[Tuple[Any, Any], int]:
        """Compute the derived per-case timing fallback.

        Input: ``(user_id, item_id, timestamp_iso)`` triples. Output:
        ``{(user_id, item_id): ms}`` = the gap between a voter's consecutive item
        timestamps (earliest per item), so the first case per voter and rows with
        no timestamp get no entry. Raw (idle gaps not filtered); shared by the v1
        and legacy exports so the fallback is computed one way.
        """
        first_seen: Dict[Tuple[Any, Any], datetime] = {}
        for uid, iid, ts in pairs:
            if uid is None or iid is None or not ts:
                continue
            try:
                dt = ts if isinstance(ts, datetime) else datetime.fromisoformat(str(ts))
            except (TypeError, ValueError):
                continue
            key = (uid, iid)
            if key not in first_seen or dt < first_seen[key]:
                first_seen[key] = dt

        by_voter: Dict[Any, List[Tuple[datetime, Any]]] = {}
        for (uid, iid), dt in first_seen.items():
            by_voter.setdefault(uid, []).append((dt, iid))

        deltas: Dict[Tuple[Any, Any], int] = {}
        for uid, seq in by_voter.items():
            seq.sort(key=lambda x: (x[0], x[1]))
            for i in range(1, len(seq)):
                gap = (seq[i][0] - seq[i - 1][0]).total_seconds() * 1000.0
                if gap >= 0:
                    deltas[(uid, seq[i][1])] = int(round(gap))
        return deltas

    @staticmethod
    def summarize_cases(
        cases: Iterable[Tuple[Any, Any, Any, Optional[int], Optional[int]]]
    ) -> Dict[str, Any]:
        """Aggregate per-case timing into per-voter statistics for the export.

        Input: ``(voter_id, voter_username, item_id, captured_ms, derived_ms)``
        tuples — one PER EXPORT ROW. Rating/ranking emit several rows per case
        (one per dimension/feature), so this dedupes to ONE effective time per
        ``(voter, item)`` first (captured value wins over the derived fallback);
        otherwise a multi-dimension rating would count that case's time N times
        and skew the mean/median.

        Returns ``{"unit": "ms", "per_voter": [...], "overall": {...}|None}``,
        each voter block carrying ``n`` (cases with a time), ``captured_n`` /
        ``derived_n`` (how many came from real vs derived timing), ``mean_ms``,
        ``median_ms``, ``min_ms``, ``max_ms``, ``std_ms`` (sample SD; None for
        n<2) and ``total_ms``. Cases with no time at all are skipped.
        """
        # Dedupe to one effective value per (voter, item).
        per_case: Dict[Tuple[Any, Any], Tuple[int, str, Any]] = {}
        for vid, uname, iid, captured, derived in cases:
            if vid is None or iid is None:
                continue
            value = captured if captured is not None else derived
            if value is None:
                continue
            source = "captured" if captured is not None else "derived"
            key = (vid, iid)
            existing = per_case.get(key)
            # Keep the first seen; upgrade derived→captured if a better row shows up.
            if existing is None or (existing[1] == "derived" and source == "captured"):
                per_case[key] = (int(value), source, uname)

        by_voter: Dict[Any, Dict[str, Any]] = {}
        for (vid, _iid), (value, source, uname) in per_case.items():
            b = by_voter.setdefault(
                vid, {"username": uname, "values": [], "captured": 0, "derived": 0}
            )
            b["values"].append(value)
            b[source] += 1

        def _stats(values: List[int]) -> Dict[str, Any]:
            vals = sorted(values)
            return {
                "mean_ms": round(statistics.fmean(vals)),
                "median_ms": round(statistics.median(vals)),
                "min_ms": vals[0],
                "max_ms": vals[-1],
                "std_ms": round(statistics.stdev(vals)) if len(vals) >= 2 else None,
                "total_ms": sum(vals),
            }

        per_voter: List[Dict[str, Any]] = []
        all_values: List[int] = []
        for vid, b in by_voter.items():
            all_values.extend(b["values"])
            per_voter.append({
                "voter_id": vid,
                "voter_username": b["username"],
                "n": len(b["values"]),
                "captured_n": b["captured"],
                "derived_n": b["derived"],
                **_stats(b["values"]),
            })
        per_voter.sort(key=lambda x: ((x["voter_username"] or ""), str(x["voter_id"])))

        overall = None
        if all_values:
            overall = {"n": len(all_values), **_stats(all_values)}
            overall.pop("total_ms", None)  # a grand total of case-times isn't meaningful

        return {"unit": "ms", "per_voter": per_voter, "overall": overall}

    @staticmethod
    def stamp_rows(rows: List[Dict[str, Any]], scenario_id: int) -> None:
        """Add ``time_on_item_ms`` + ``time_since_prev_ms`` to legacy GUI-export
        rows in place (the v1 export has its own stamping over its stable schema).

        Human rows are those carrying a ``user_id``; the item id is taken from
        ``item_id`` or (fallback) ``thread_id``; the derived delta uses the row's
        ``timestamp``. Both columns are seeded on every human row so the CSV
        header stays stable even when nothing was captured.

        A "case" is the item for every type except conversation labeling, where
        it is the span — a conversation carries ~92 independently timed
        decisions. Rows without a span contribute '' and behave as before.
        """
        def _iid(r: Dict[str, Any]) -> Any:
            iid = r.get("item_id")
            return iid if iid is not None else r.get("thread_id")

        def _case(r: Dict[str, Any]) -> Any:
            return (_iid(r), r.get("span_id") or "")

        human = [r for r in rows if r.get("user_id") is not None]
        for r in human:
            r.setdefault("time_on_item_ms", None)
            r.setdefault("time_since_prev_ms", None)

        timing_map = ItemTimingService.timings_for_scenario(scenario_id)
        for r in human:
            t = timing_map.get((r.get("user_id"), _iid(r), r.get("span_id") or ""))
            if t is not None:
                r["time_on_item_ms"] = t

        deltas = ItemTimingService.derive_deltas(
            [(r.get("user_id"), _case(r), r.get("timestamp")) for r in human]
        )
        for r in human:
            key = (r.get("user_id"), _case(r))
            if key in deltas:
                r["time_since_prev_ms"] = deltas[key]
