"""
Scenario Stats Cache Service.

DB-backed stats cache with durable background recomputation.
Stats are always served from cache (DB or in-memory). When stale,
the web process enqueues a recompute job and dedicated worker processes
refresh the cache and push updates via Socket.IO.

Tiered refresh intervals based on scenario size:
  - S (<=50 items):  30s
  - M (<=200 items): 120s
  - L (>200 items):  300s
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from db.database import db
from db.models.scenario_stats_cache import ScenarioStatsCache
from services.background_jobs import ScenarioStatsJobService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory layer (avoids DB round-trip on hot paths)
# ---------------------------------------------------------------------------
_mem_cache: Dict[int, tuple] = {}  # scenario_id -> (timestamp, stats_dict, item_count)

# ---------------------------------------------------------------------------
# Tier logic
# ---------------------------------------------------------------------------

def _get_refresh_interval(item_count: int) -> int:
    """Return staleness threshold in seconds based on scenario size."""
    if item_count <= 50:
        return 30
    if item_count <= 200:
        return 120
    return 300


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_cached_stats(scenario_id: int) -> Dict[str, Any]:
    """Return cached stats, triggering background recompute if stale.

    1. Check in-memory cache (fastest, <1ms)
    2. Check DB cache -> return + maybe trigger recompute
    3. No cache at all -> synchronous quick stats + background full recompute
    """
    # 1. In-memory hit (no DB query needed)
    mem = _mem_cache.get(scenario_id)
    if mem is not None:
        ts, data, item_count = mem
        interval = _get_refresh_interval(item_count)
        if (time.time() - ts) < interval:
            return data
        # Stale in-memory -> trigger background recompute, return stale data
        trigger_recompute(scenario_id)
        return data

    # 2. DB cache hit
    db_row = _get_db_row(scenario_id)
    if db_row and db_row.stats_json:
        try:
            stats = json.loads(db_row.stats_json)
        except (json.JSONDecodeError, TypeError):
            stats = None

        if stats:
            # Populate in-memory cache
            cache_ts = db_row.computed_at.replace(tzinfo=timezone.utc).timestamp() if db_row.computed_at else 0
            _mem_cache[scenario_id] = (cache_ts, stats, db_row.item_count or 0)

            interval = _get_refresh_interval(db_row.item_count or 0)
            age = time.time() - cache_ts
            if age >= interval:
                trigger_recompute(scenario_id)
            return stats

    # 3. Cold start - compute synchronously but skip expensive provenance
    logger.info("[StatsCache] Cold start for scenario %s - computing synchronously (no provenance)", scenario_id)
    stats = _compute_quick_stats(scenario_id)
    if stats is not None:
        _save_to_db(scenario_id, stats)
        try:
            from db.models import ScenarioItems
            item_count = ScenarioItems.query.filter_by(scenario_id=scenario_id).count()
        except Exception:
            item_count = 0
        _mem_cache[scenario_id] = (time.time(), stats, item_count)
    # Trigger background recompute for full stats (with provenance)
    trigger_recompute(scenario_id)
    return stats or {}


def mark_dirty(scenario_id: int) -> None:
    """Mark a scenario's stats cache as stale.

    Called after rating/ranking submissions. Sets computed_at far in the past
    so the next reader triggers a background recompute.
    """
    # Evict in-memory cache immediately
    _mem_cache.pop(scenario_id, None)

    try:
        row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
        if row:
            row.computed_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
            db.session.commit()
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass  # Session may not have an active transaction (e.g. SQLite in tests)
        logger.warning("[StatsCache] Failed to mark dirty for scenario %s: %s", scenario_id, exc)

    # Immediately trigger background recompute
    trigger_recompute(scenario_id)


def invalidate_and_recompute(scenario_id: int) -> None:
    """Convenience: mark dirty + force recompute. Used by emit_scenario_stats_updated."""
    mark_dirty(scenario_id)


def trigger_recompute(scenario_id: int) -> None:
    """Queue a durable background recompute for full stats."""
    try:
        from flask import current_app
        app = current_app._get_current_object()
    except RuntimeError:
        app = None

    if app is not None and (app.testing or app.config.get('TESTING')):
        recompute_stats_for_worker(scenario_id)
        return

    try:
        row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
        if row:
            row.is_computing = True
            db.session.commit()
    except Exception:
        db.session.rollback()

    try:
        ScenarioStatsJobService.enqueue_recompute(scenario_id)
    except Exception as exc:
        db.session.rollback()
        logger.warning("[StatsCache] Failed to queue recompute for scenario %s: %s", scenario_id, exc)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_db_row(scenario_id: int) -> Optional[ScenarioStatsCache]:
    """Fetch the cache row from DB (returns None if not found)."""
    try:
        return ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
    except Exception:
        return None


def _compute_quick_stats(scenario_id: int) -> Optional[Dict[str, Any]]:
    """Compute stats without expensive provenance analysis (for cold start)."""
    try:
        from services.scenario_stats_service import get_progress_stats
        return get_progress_stats(scenario_id, skip_provenance=True)
    except Exception as exc:
        logger.error("[StatsCache] Quick stats computation failed for scenario %s: %s", scenario_id, exc)
        return None


def _compute_full_stats(scenario_id: int) -> Optional[Dict[str, Any]]:
    """Run the full stats computation including provenance (expensive)."""
    try:
        from services.scenario_stats_service import get_progress_stats
        return get_progress_stats(scenario_id, skip_provenance=False)
    except Exception as exc:
        logger.error("[StatsCache] Full stats computation failed for scenario %s: %s", scenario_id, exc)
        return None


def _save_to_db(scenario_id: int, stats: Dict[str, Any]) -> None:
    """Persist computed stats to the DB cache."""
    try:
        from db.models import RatingScenarios, ScenarioItems, FeatureFunctionType

        # Get item count and function type
        item_count = ScenarioItems.query.filter_by(scenario_id=scenario_id).count()
        scenario = RatingScenarios.query.filter_by(id=scenario_id).first()
        function_type_name = "unknown"
        if scenario:
            ft = FeatureFunctionType.query.filter_by(function_type_id=scenario.function_type_id).first()
            if ft:
                function_type_name = ft.name

        stats_json = json.dumps(stats, default=str)
        now = datetime.now(timezone.utc)

        row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
        if row:
            row.stats_json = stats_json
            row.function_type = function_type_name
            row.computed_at = now
            row.item_count = item_count
            row.is_computing = False
        else:
            row = ScenarioStatsCache(
                scenario_id=scenario_id,
                stats_json=stats_json,
                function_type=function_type_name,
                computed_at=now,
                item_count=item_count,
                is_computing=False,
            )
            db.session.add(row)

        try:
            db.session.commit()
        except Exception:
            # Race condition: another thread inserted first - update instead
            db.session.rollback()
            row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
            if row:
                row.stats_json = stats_json
                row.function_type = function_type_name
                row.computed_at = now
                row.item_count = item_count
                row.is_computing = False
                db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning("[StatsCache] Failed to save stats to DB for scenario %s: %s", scenario_id, exc)


def recompute_stats_for_worker(scenario_id: int) -> Optional[Dict[str, Any]]:
    """Compute and persist full stats from a dedicated worker process."""
    t0 = time.time()
    try:
        row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
        if row:
            row.is_computing = True
            db.session.commit()

        stats = _compute_full_stats(scenario_id)
        elapsed = time.time() - t0
        logger.info("[StatsCache] Recomputed scenario %s in %.2fs", scenario_id, elapsed)
        if stats is None:
            return None

        _save_to_db(scenario_id, stats)
        try:
            from db.models import ScenarioItems
            item_count = ScenarioItems.query.filter_by(scenario_id=scenario_id).count()
        except Exception:
            item_count = 0
        _mem_cache[scenario_id] = (time.time(), stats, item_count)
        _emit_stats_update(scenario_id, stats)
        return stats
    finally:
        try:
            row = ScenarioStatsCache.query.filter_by(scenario_id=scenario_id).first()
            if row:
                row.is_computing = False
                db.session.commit()
        except Exception:
            db.session.rollback()


def _emit_stats_update(scenario_id: int, stats: Dict[str, Any]) -> None:
    """Push updated stats to all subscribed clients via Socket.IO."""
    try:
        from flask import current_app
        socketio = current_app.extensions.get('socketio')
        if not socketio:
            return

        from services.scenario_stats_service import (
            _get_scenario_or_raise,
            _get_function_type_or_raise,
        )

        scenario = _get_scenario_or_raise(scenario_id)
        function_type = _get_function_type_or_raise(scenario.function_type_id)

        payload = {
            "scenario_id": scenario_id,
            "function_type": function_type.name,
            "kind": "progress",
            "stats": stats,
        }

        room = f"scenario_stats_{scenario_id}"
        socketio.emit("scenario:stats_updated", payload, room=room)
        logger.info("[StatsCache] Pushed stats update to %s", room)
    except Exception as exc:
        logger.warning("[StatsCache] Failed to emit stats update for scenario %s: %s", scenario_id, exc)
