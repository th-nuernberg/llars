"""
``/api/v1/scenarios/<id>/results`` — programmatic results export.

Long-format vote dump + IRR summary, served under ``scenario:read``.
This is the API a researcher reaches for when they need a defensible
audit trail of *who voted what, when, on which item* — across every
function type, in a single stable schema.

Why a separate route from ``/api/scenarios/<id>/export`` (legacy)
-----------------------------------------------------------------
The legacy export uses one row schema per function type, requires an
Authentik OAuth session (cannot be scripted with API keys), and silently
drops human votes for the function types it doesn't have an ``elif``
branch for. The v1 results endpoint is API-key-friendly, scope-gated, and
returns the same long-format columns regardless of type — so a single
parser handles all six.
"""

from __future__ import annotations

import csv
import io
import json
import logging

from flask import Response, g, jsonify, request

from auth.decorators import api_key_or_token_required, require_api_scope
from db.models import RatingScenarios, ScenarioUsers
from decorators.error_handler import (
    NotFoundError,
    ValidationError as ApiValidationError,
    handle_api_errors,
)
from services.evaluation.results_export_service import (
    ROW_COLUMNS,
    collect_metrics,
    collect_results,
)
from services.permission_service import PermissionService

from . import api_v1_bp

logger = logging.getLogger(__name__)


_ALLOWED_FORMATS = {"json", "csv", "jsonl"}


def _user_can_read_scenario(scenario: RatingScenarios, user) -> bool:
    """Same visibility rules as ``GET /api/v1/scenarios/{id}``: admin or
    creator or member."""
    if user is None:
        return False
    if PermissionService.user_has_role(user.username, "admin"):
        return True
    if scenario.created_by == user.username:
        return True
    return ScenarioUsers.query.filter_by(
        scenario_id=scenario.id, user_id=user.id
    ).first() is not None


@api_v1_bp.route("/scenarios/<int:scenario_id>/results", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.results")
def export_scenario_results_v1(scenario_id: int):
    """
    Long-format export of every vote on the scenario, plus IRR summary.

    Query params:
        format=json|csv|jsonl    (default: json)
        include_humans=0|1       (default: 1)
        include_llms=0|1         (default: 1)
        include_metrics=0|1      (default: 1) — bundle the IRR block in JSON
        include_payload=0|1      (default: 0) — attach raw LLM payload to each LLM row

    Response (JSON):
        {
          "scenario": { id, name, function_type, ... },
          "rows": [ {scenario_id, item_id, voter_kind, ...}, ... ],
          "metrics": {
              "krippendorff_alpha": {value, interpretation, aggregation_method},
              ...
          },
          "exported_at": "ISO 8601"
        }

    Response (CSV):
        text/csv with the long-format rows. The IRR block is omitted (CSV
        is per-row data only); fetch ``?format=json`` to also get metrics.

    Response (JSONL):
        text/jsonl, one row per line, no envelope.
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario or not _user_can_read_scenario(scenario, g.authentik_user):
        # Mirror the M1-fix pattern: never differentiate "doesn't exist"
        # from "you can't see it" so we don't leak ID validity.
        raise NotFoundError(f"Scenario {scenario_id} not found")

    fmt = (request.args.get("format") or "json").lower()
    if fmt not in _ALLOWED_FORMATS:
        raise ApiValidationError(
            f"Unsupported format '{fmt}'. Use one of: {sorted(_ALLOWED_FORMATS)}"
        )

    include_humans = request.args.get("include_humans", "1") not in ("0", "false", "no")
    include_llms = request.args.get("include_llms", "1") not in ("0", "false", "no")
    include_metrics = request.args.get("include_metrics", "1") not in ("0", "false", "no")
    include_payload = request.args.get("include_payload", "0") in ("1", "true", "yes")

    payload = collect_results(
        scenario,
        include_humans=include_humans,
        include_llms=include_llms,
        include_payload=include_payload,
    )

    metrics_block = collect_metrics(scenario) if include_metrics else None

    if fmt == "json":
        return jsonify({
            "success": True,
            "scenario": {
                "id": scenario.id,
                "name": scenario.scenario_name,
                "function_type": payload["function_type"],
                "function_type_id": scenario.function_type_id,
                "item_count": payload["item_count"],
                "voter_count": payload["voter_count"],
                "row_count": payload["row_count"],
            },
            "rows": payload["rows"],
            "metrics": metrics_block,
            # Labeling co-pilot aggregates (acceptance/helpful/time per
            # annotator + per label); only present when the scenario logged
            # co-pilot data. None for other scenario types.
            "copilot_metrics": payload.get("copilot_metrics"),
            # Per-voter time-on-case aggregates (n / mean / median / min / max /
            # std + captured-vs-derived counts) + overall block. Only present
            # when at least one case has a (real or derived) time.
            "timing_metrics": payload.get("timing_metrics"),
            "exported_at": payload["exported_at"],
        })

    if fmt == "jsonl":
        # One JSON object per line, no envelope. Stream-friendly for
        # large exports.
        def _stream():
            for row in payload["rows"]:
                yield json.dumps(row, default=str) + "\n"
        return Response(
            _stream(),
            mimetype="application/jsonl",
            headers={
                "Content-Disposition": (
                    f'attachment; filename="scenario_{scenario.id}_results.jsonl"'
                ),
            },
        )

    # CSV
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        # Always emit the full column list (even on empty exports) so the
        # downstream parser sees the contract regardless of which rows
        # happened to be present.
        fieldnames=ROW_COLUMNS,
        extrasaction="ignore",
    )
    writer.writeheader()
    # CSV-Formula-Injection-Schutz: Item-Labels/Usernamen/Vote-Strings stammen
    # teils aus importierten/frei wählbaren Daten und dürfen in Excel nicht als
    # Formel ausgeführt werden (siehe services/security/csv_safety.py).
    from services.security.csv_safety import csv_safe_row
    for row in payload["rows"]:
        writer.writerow(csv_safe_row(row))
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="scenario_{scenario.id}_results.csv"'
            ),
        },
    )


@api_v1_bp.route("/scenarios/<int:scenario_id>/metrics", methods=["GET"])
@api_key_or_token_required
@require_api_scope("scenario:read")
@handle_api_errors(logger_name="api_v1.results")
def export_scenario_metrics_v1(scenario_id: int):
    """
    Just the IRR / agreement summary without the row dump.

    Useful when a CI job wants to assert ``α > 0.667`` without downloading
    the entire vote table.

    Query params (labeling only):
        copilot=with|without  — restrict to cells labeled with/without a
                                visible co-pilot suggestion
        part=<part_id>        — restrict to ONE scenario part (IRR per
                                calibration phase); combinable with copilot
    """
    scenario = RatingScenarios.query.get(scenario_id)
    if not scenario or not _user_can_read_scenario(scenario, g.authentik_user):
        raise NotFoundError(f"Scenario {scenario_id} not found")

    copilot_filter = request.args.get("copilot") or None
    if copilot_filter not in (None, "with", "without"):
        raise ApiValidationError("copilot must be 'with' or 'without'")
    part_filter = request.args.get("part") or None

    # Validate the part id UP FRONT (unknown id = caller error -> 400).
    # Everything else (e.g. "No evaluations found" on a fresh scenario) keeps
    # the endpoint's original contract: 200 with an empty metrics block, so
    # study scripts can poll before the first label lands.
    if part_filter:
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        known_parts = sorted(set(ScenarioPartsService.item_part_map(scenario).values()))
        if part_filter not in known_parts:
            raise ApiValidationError(
                f"Unknown part '{part_filter}'. "
                f"Known parts: {known_parts or 'none (parts not active)'}"
            )

    metrics = collect_metrics(
        scenario, copilot_filter=copilot_filter, part_filter=part_filter
    )
    return jsonify({"success": True, **metrics})
