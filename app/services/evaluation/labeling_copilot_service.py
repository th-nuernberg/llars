"""Labeling Co-Pilot Service.

LLM pre-annotation for labeling scenarios (function_type 7), modeled after the
DMRS Co-Pilot in PsyDefConv (arXiv:2512.15601): suggestions are generated as a
batch BEFORE annotation (LLMAITaskRunner, task_type='copilot_labeling'), cached
per (item, prompt-version, model) in LLMTaskResult, and shown to annotators as
clearly marked, never pre-selected suggestions.

Study-critical responsibilities of this service:
- Scenario-owned prompt versioning: prompt/codebook changes bump prompt_version
  and append to prompt_history, so item->prompt-version mapping stays auditable.
- Hidden control subset: a deterministic hash over (scenario, user, item, salt)
  hides suggestions for a configured share of (user, item) pairs. Decided ONLY
  server-side; the client cannot distinguish "control item" from "generation
  failed" (anchoring analysis must stay covert).
- Logging: one LabelingCopilotLog row per labeled item snapshotting what was
  shown, acceptance (server-computed), helpfulness and time-on-item.

See .claude/plans/labeling-copilot-design.md for the full design.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from db import db
from db.models import LabelingCopilotLog, LLMTaskResult, RatingScenarios, ScenarioThreads

logger = logging.getLogger(__name__)

# function_type_id for labeling scenarios
# The co-pilot is identical for both labeling flavours; only the key gains a
# span segment (see is_hidden_control / record_label_event).
from services.evaluation.labeling_types import (  # noqa: E402
    CONVERSATION_LABELING_FUNCTION_TYPE_ID,
    LABELING_FUNCTION_TYPE_IDS,
    is_labeling_type,
)

LABELING_FUNCTION_TYPE_ID = 7

# Default prompt template shown in the wizard; placeholders are replaced
# verbatim (string replace, not str.format - templates may contain JSON braces).
DEFAULT_COPILOT_PROMPT = (
    "Du bist ein sorgfältiger Annotations-Assistent für kategorisches Labeling.\n"
    "Deine Aufgabe: Ordne das folgende Item einer der erlaubten Kategorien zu und "
    "begründe deinen Vorschlag knapp mit Textbelegen.\n\n"
    "Erlaubte Kategorien:\n{labels}\n\n"
    "Kodierregeln / Codebook:\n{codebook}\n\n"
    "Kontext:\n{context}\n\n"
    "Zu labelndes Item:\n{item}\n\n"
    "Stütze dich ausschließlich auf den Text. Wenn die Evidenz dünn ist, "
    "wähle konservativ und benenne die Unsicherheit in der Begründung."
)

VALID_CONFIDENCES = {"high", "medium", "low"}


class LabelingCopilotService:
    """Config handling, visibility, suggestion delivery and logging for the co-pilot."""

    TASK_TYPE = "copilot_labeling"
    # LLMEvalRun rows are unique per (scenario_id, model_id). Prefixing the model
    # id keeps a copilot run distinct from a regular LLM evaluator using the SAME
    # model in the same scenario (queue + lock separation).
    QUEUE_MODEL_PREFIX = "copilot:"

    # ------------------------------------------------------------------
    # Config access
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dict(raw: Any) -> Dict[str, Any]:
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                return {}
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def locate_inner_config(config: Any) -> Dict[str, Any]:
        """Return the inner labeling config dict (where labels/categories live).

        config_json layouts in the wild (see LabelingInterface.vue unwrap):
        - wizard:  {eval_config: {type, config: {...}}}
        - api_v1:  {eval_config: {type, config: {...}}} or {type, config: {...}}
        - legacy:  the labeling config directly at top level
        """
        config = LabelingCopilotService._to_dict(config)
        eval_config = LabelingCopilotService._to_dict(config.get("eval_config"))
        for candidate in (
            LabelingCopilotService._to_dict(eval_config.get("config")),
            LabelingCopilotService._to_dict(config.get("config")),
            eval_config,
            config,
        ):
            if candidate:
                return candidate
        return {}

    @staticmethod
    def get_copilot_config(scenario_or_config: Any) -> Optional[Dict[str, Any]]:
        """Return the copilot config dict if the co-pilot is enabled, else None."""
        config = scenario_or_config
        if isinstance(scenario_or_config, RatingScenarios):
            config = scenario_or_config.config_json
        inner = LabelingCopilotService.locate_inner_config(config)
        copilot = LabelingCopilotService._to_dict(inner.get("copilot"))
        if not copilot or not copilot.get("enabled"):
            return None
        return copilot

    # Labeling settings that the v1 API may write headlessly (see
    # routes/api_v1/scenario_copilot_routes.py PUT .../labeling-config).
    # Everything else in the labeling config (labels, mode, parts, copilot)
    # has its own write path or is study-immutable once votes exist.
    LABELING_SETTINGS_FIELDS = frozenset({"questions", "second_choice", "labels"})

    @staticmethod
    def update_labeling_settings(config: Any, body: Dict[str, Any]) -> Dict[str, Any]:
        """Return a new config with ``questions`` / ``second_choice`` merged
        into the inner labeling config (and its ``config.config`` mirror).

        Why a dedicated path: the generic ``PUT /api/scenarios/<id>`` is
        session-only, and the v1 PATCH deliberately refuses ``eval_config``.
        Studies driven by scripts (VRM, see vrm-corpus) still need to switch
        question-first labeling and the second choice on without a browser.

        ``questions`` is validated against ``DecisionQuestionsConfig`` (a
        mapping target that is not a label id is rejected); ``None`` removes
        the block. Raises ``ValueError`` with a user-facing message.

        ``labels`` MERGES by id instead of replacing the list: a running study
        fixes the wording of one category without resending the whole label set,
        and — more importantly — cannot silently drop a label that votes already
        reference. Adding or removing categories mid-study stays a deliberate UI
        action. Each entry is validated against ``LabelOption``, which is what
        keeps ``rule`` and ``anchors`` (the codebook text shown while labeling)
        well-formed.
        """
        from pydantic import ValidationError as PydanticValidationError
        from schemas.evaluation_data_schemas import DecisionQuestionsConfig, LabelOption

        unknown = set(body) - LabelingCopilotService.LABELING_SETTINGS_FIELDS
        if unknown:
            raise ValueError(
                f"Unknown fields: {sorted(unknown)}. "
                f"Editable: {sorted(LabelingCopilotService.LABELING_SETTINGS_FIELDS)}"
            )
        if not body:
            raise ValueError(
                "Request body must contain questions, second_choice and/or labels"
            )

        next_config = json.loads(json.dumps(LabelingCopilotService._to_dict(config)))
        inner = LabelingCopilotService.locate_inner_config(next_config)
        if not inner:
            raise ValueError("Scenario has no labeling config")

        updates: Dict[str, Any] = {}
        if "second_choice" in body:
            if not isinstance(body["second_choice"], bool):
                raise ValueError("second_choice must be a boolean")
            updates["second_choice"] = body["second_choice"]
        if "questions" in body:
            questions = body["questions"]
            if questions is None:
                updates["questions"] = None
            else:
                try:
                    validated = DecisionQuestionsConfig.model_validate(questions)
                except PydanticValidationError as exc:
                    raise ValueError(f"questions: {exc.errors()[0].get('msg', exc)}")
                label_ids = {
                    str(lbl.get("id"))
                    for lbl in (inner.get("labels") or inner.get("categories") or [])
                    if isinstance(lbl, dict)
                }
                missing = sorted(set(validated.mapping.values()) - label_ids) if label_ids else []
                if missing:
                    raise ValueError(f"questions.mapping targets unknown labels: {missing}")
                updates["questions"] = validated.model_dump(mode="json")

        if "labels" in body:
            patches = body["labels"]
            if not isinstance(patches, list) or not patches:
                raise ValueError("labels must be a non-empty list")
            current = inner.get("labels") or inner.get("categories") or []
            by_id = {str(lbl.get("id")): lbl for lbl in current if isinstance(lbl, dict)}
            for patch in patches:
                if not isinstance(patch, dict) or not patch.get("id"):
                    raise ValueError("each label patch needs an id")
                label_id = str(patch["id"])
                if label_id not in by_id:
                    raise ValueError(
                        f"unknown label id {label_id!r} — "
                        f"known: {sorted(by_id)}. Adding categories is a UI action."
                    )
                merged = {**by_id[label_id], **patch, "id": label_id}
                try:
                    LabelOption.model_validate(merged)
                except PydanticValidationError as exc:
                    err = exc.errors()[0]
                    raise ValueError(
                        f"labels[{label_id}].{'.'.join(str(p) for p in err.get('loc', ()))}: "
                        f"{err.get('msg', exc)}"
                    )
                by_id[label_id] = merged
            updates["labels"] = [by_id[str(lbl.get("id"))] for lbl in current
                                 if isinstance(lbl, dict)]

        def _apply(target: Dict[str, Any]) -> None:
            for key, value in updates.items():
                if value is None:
                    target.pop(key, None)
                else:
                    target[key] = value

        _apply(inner)
        # v1-created scenarios mirror the inner config at config.config — keep
        # both copies in sync (same as the copilot PUT and the settings tab).
        mirror = next_config.get("config")
        if isinstance(mirror, dict) and mirror is not inner:
            _apply(mirror)
        return next_config

    @staticmethod
    def get_questions_config(config: Any) -> Optional[Dict[str, Any]]:
        """Return the question-first block ({items, mapping, sliders}) if the
        scenario has it enabled and at least one question — else None."""
        inner = LabelingCopilotService.locate_inner_config(config)
        questions = LabelingCopilotService._to_dict(inner.get("questions"))
        if not questions or questions.get("enabled") is False:
            return None
        items = [q for q in (questions.get("items") or []) if isinstance(q, dict) and q.get("id")]
        if not items:
            return None
        return {
            "items": items,
            "mapping": {str(k): str(v) for k, v in (questions.get("mapping") or {}).items()},
            "sliders": bool(questions.get("sliders")),
        }

    @staticmethod
    def build_questions_block(questions: Dict[str, Any]) -> str:
        """Human-readable rendering of the decision questions for the LLM
        prompt (German first, English fallback), incl. the answer→label map."""

        def _loc(value: Any) -> str:
            if isinstance(value, dict):
                return str(value.get("de") or value.get("en") or "")
            return str(value) if value else ""

        lines = []
        for idx, q in enumerate(questions["items"], 1):
            opts = " / ".join(
                f"{o.get('id')} = {_loc(o.get('label'))}"
                + (f" ({_loc(o.get('hint'))})" if _loc(o.get("hint")) else "")
                for o in (q.get("options") or []) if isinstance(o, dict)
            )
            lines.append(f"{idx}. {q['id']} — {_loc(q.get('title'))}: {_loc(q.get('text'))}\n   Antworten: {opts}")
        mapping = questions.get("mapping") or {}
        if mapping:
            lines.append("Antwortschlüssel → Label: " + ", ".join(f"{k} → {v}" for k, v in mapping.items()))
        return "\n".join(lines)

    @staticmethod
    def extract_label_options(config: Any) -> List[Dict[str, str]]:
        """Extract label options as [{id, name, description}] from either the
        schema format (labels: [{id, label:{de,en}, description:{de,en}}]) or
        the wizard format (categories: [{id?, name:{de}|str, description?}])."""

        def _localized(value: Any) -> str:
            if isinstance(value, dict):
                return str(value.get("de") or value.get("en") or "")
            return str(value) if value else ""

        inner = LabelingCopilotService.locate_inner_config(config)
        raw_options = inner.get("labels") or inner.get("categories") or []
        options: List[Dict[str, str]] = []
        for entry in raw_options:
            if isinstance(entry, str):
                options.append({"id": entry, "name": entry, "description": ""})
                continue
            if not isinstance(entry, dict):
                continue
            name = _localized(entry.get("label")) or _localized(entry.get("name"))
            label_id = str(entry.get("id") or name or "").strip()
            if not label_id:
                continue
            options.append({
                "id": label_id,
                "name": name or label_id,
                "description": _localized(entry.get("description")),
            })
        return options

    # ------------------------------------------------------------------
    # Config normalization (create/update paths)
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_config_on_write(
        config: Any,
        previous_config: Any = None,
    ) -> Any:
        """Normalize the copilot section of a scenario config before persisting.

        - Generates hidden_control_salt once (kept stable afterwards so the
          control-subset assignment stays reproducible).
        - Bumps prompt_version + appends prompt_history when prompt/codebook
          changed compared to the previously stored config (study requirement:
          item->prompt-version mapping must stay meaningful).

        Returns the (possibly modified) config; safe to call for non-labeling
        configs (no-op when no copilot section exists).
        """
        config_dict = LabelingCopilotService._to_dict(config)
        if not config_dict:
            return config
        inner = LabelingCopilotService.locate_inner_config(config_dict)
        copilot = inner.get("copilot")
        if not isinstance(copilot, dict):
            return config

        previous = LabelingCopilotService._to_dict(previous_config)
        prev_copilot = {}
        if previous:
            prev_inner = LabelingCopilotService.locate_inner_config(previous)
            prev_copilot = LabelingCopilotService._to_dict(prev_inner.get("copilot"))

        # Salt: create once, then keep stable (reproducible control subset)
        if prev_copilot.get("hidden_control_salt"):
            copilot["hidden_control_salt"] = prev_copilot["hidden_control_salt"]
        elif not copilot.get("hidden_control_salt"):
            copilot["hidden_control_salt"] = secrets.token_hex(8)

        prompt = (copilot.get("prompt") or "").strip() or DEFAULT_COPILOT_PROMPT
        copilot["prompt"] = prompt
        codebook = (copilot.get("codebook") or "").strip()

        prev_version = int(prev_copilot.get("prompt_version") or 0)
        prev_prompt = (prev_copilot.get("prompt") or "").strip()
        prev_codebook = (prev_copilot.get("codebook") or "").strip()
        history = prev_copilot.get("prompt_history")
        history = list(history) if isinstance(history, list) else []

        # top_k is part of the EFFECTIVE prompt: the fixed format_instruction
        # the runner appends asks for exactly top_k suggestions. Changing it
        # must bump the version, otherwise the runner's cache-skip (keyed on
        # prompt_version) would keep stale Top-1 results after a switch to
        # Top-2 — and vice versa.
        def _norm_top_k(value):
            try:
                return max(1, min(2, int(value or 1)))
            except (TypeError, ValueError):
                return 1

        top_k = _norm_top_k(copilot.get("top_k"))
        prev_top_k = _norm_top_k(prev_copilot.get("top_k"))

        # The decision questions are part of the EFFECTIVE prompt too (the
        # runner renders them into the format instruction), so a change must
        # bump the version for the same cache-staleness reason as top_k.
        def _questions_sig(cfg: Any) -> str:
            q = LabelingCopilotService.get_questions_config(cfg) if cfg else None
            return json.dumps(q, sort_keys=True, ensure_ascii=False) if q else ""

        questions_sig = _questions_sig(config_dict)
        prev_questions_sig = _questions_sig(previous)

        if prev_version == 0:
            # First write of a copilot config
            new_version = 1
        elif (prompt != prev_prompt or codebook != prev_codebook or top_k != prev_top_k
              or questions_sig != prev_questions_sig):
            new_version = prev_version + 1
        else:
            new_version = prev_version

        if new_version != prev_version:
            history.append({
                "version": new_version,
                "prompt": prompt,
                "codebook": codebook or None,
                "top_k": top_k,
                "updated_at": datetime.utcnow().isoformat(),
            })

        copilot["prompt_version"] = new_version
        copilot["prompt_history"] = history
        inner["copilot"] = copilot
        # v1-created scenarios keep a mirror of the inner config at config.config.
        # update_labeling_settings mirrors questions/second_choice/labels, so the
        # copilot block has to follow — otherwise the two copies drift and anyone
        # reading the mirror sees a stale prompt_version. That happened on the VRM
        # study scenario: authoritative v3, mirror still v1. The runner reads the
        # authoritative block (locate_inner_config), so the audit trail was intact,
        # but a stale mirror is a trap for every later reader.
        mirror = config_dict.get("config")
        if isinstance(mirror, dict) and mirror is not inner and isinstance(mirror.get("copilot"), dict):
            mirror["copilot"] = json.loads(json.dumps(copilot))
        return config_dict

    # ------------------------------------------------------------------
    # Hidden control subset
    # ------------------------------------------------------------------

    @staticmethod
    def is_hidden_control(
        scenario_id: int,
        user_id: int,
        item_id: int,
        copilot_cfg: Dict[str, Any],
        span_id: str = "",
    ) -> bool:
        """Deterministic per (scenario, user, item, span): hash-bucket < ratio.

        Per user+item (not per item) so every item is labeled by some raters
        WITH and by others WITHOUT the suggestion -> within-item anchoring
        comparison, and the "without copilot" alpha filter keeps coverage
        across all items.

        For conversation labeling the decision unit is the SPAN, so the hash
        includes it: otherwise a whole conversation (~92 decisions) would fall
        into the control group as one block, which is both a much coarser
        sample and exactly the wrong granularity for measuring anchoring in a
        sequence of consecutive suggestions.

        ``span_id=""`` reproduces the classic per-item behaviour bit for bit —
        the empty string is appended, but the existing salted digest for
        classic scenarios is unchanged because the format string ends with the
        salt. IMPORTANT: the salt of an existing study must never change, so
        the span segment is appended AFTER it rather than inserted.
        """
        try:
            ratio = float(copilot_cfg.get("hidden_control_ratio") or 0.0)
        except (TypeError, ValueError):
            ratio = 0.0
        if ratio <= 0:
            return False
        salt = str(copilot_cfg.get("hidden_control_salt") or "")
        # Classic scenarios (span_id="") keep their historical digest exactly:
        # the suffix is only appended when a span is actually addressed.
        key = f"{scenario_id}:{user_id}:{item_id}:{salt}"
        if span_id:
            key = f"{key}:{span_id}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 10000
        return bucket < int(round(ratio * 10000))

    # ------------------------------------------------------------------
    # Suggestion delivery
    # ------------------------------------------------------------------

    @staticmethod
    def _get_cached_result(
        scenario_id: int,
        item_id: int,
        copilot_cfg: Dict[str, Any],
    ) -> Optional[LLMTaskResult]:
        """Cache row for (item, current prompt_version, configured model), or None."""
        model_id = copilot_cfg.get("model_id")
        if not model_id:
            return None
        row = LLMTaskResult.query.filter_by(
            scenario_id=scenario_id,
            item_id=item_id,
            model_id=model_id,
            task_type=LabelingCopilotService.TASK_TYPE,
        ).first()
        if not row or not row.payload_json:
            return None
        if str(row.prompt_version or "") != str(copilot_cfg.get("prompt_version") or 1):
            return None  # stale: prompt changed since generation, re-run pending
        suggestions = (row.payload_json or {}).get("suggestions")
        if not isinstance(suggestions, list) or not suggestions:
            return None
        return row

    @staticmethod
    def get_visible_suggestions_map(
        scenario: RatingScenarios,
        user_id: int,
        item_ids: List[int],
    ) -> Dict[int, Dict[str, Any]]:
        """Suggestions to deliver with a labeling session, keyed by item_id.

        Applies the hidden-control filter. Items without an entry simply carry
        no suggestion (frontend renders nothing) - indistinguishable from a
        failed generation, which keeps the control subset covert.
        Intentionally does NOT expose model_id or prompt internals to raters.
        """
        copilot_cfg = LabelingCopilotService.get_copilot_config(scenario)
        if not copilot_cfg or not item_ids:
            return {}

        model_id = copilot_cfg.get("model_id")
        if not model_id:
            return {}

        # Scenario parts: suggestions only for items in copilot-enabled parts.
        # None = parts inactive → no gating (today's behaviour). Items outside
        # copilot parts simply carry no suggestion — indistinguishable from
        # hidden-control / failed generation, so the partition stays covert.
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        part_gate = ScenarioPartsService.copilot_item_ids(scenario)
        if part_gate is not None:
            item_ids = [i for i in item_ids if i in part_gate]
            if not item_ids:
                return {}
        current_version = str(copilot_cfg.get("prompt_version") or 1)
        rows = LLMTaskResult.query.filter(
            LLMTaskResult.scenario_id == scenario.id,
            LLMTaskResult.model_id == model_id,
            LLMTaskResult.task_type == LabelingCopilotService.TASK_TYPE,
            LLMTaskResult.item_id.in_(item_ids),
            LLMTaskResult.payload_json.isnot(None),
        ).all()

        # Conversation labeling caches ALL spans of a conversation in ONE row
        # (payload_json["spans"][span_id]) rather than one row per span: the
        # unique key of LLMTaskResult is per item, and a study of this shape has
        # ~92 spans per item — a row each would multiply the table by two orders
        # of magnitude for no gain.
        span_mode = scenario.function_type_id == CONVERSATION_LABELING_FUNCTION_TYPE_ID

        result: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            if str(row.prompt_version or "") != current_version:
                continue
            payload = row.payload_json or {}

            if span_mode:
                spans = payload.get("spans")
                if not isinstance(spans, dict) or not spans:
                    continue
                # The control subset is drawn PER SPAN. Filtering whole items
                # here would put ~92 consecutive decisions into the control
                # group as one block — the wrong granularity for measuring
                # anchoring across a run of successive suggestions.
                visible = {}
                for span_id, entry in spans.items():
                    suggestions = (entry or {}).get("suggestions")
                    if not isinstance(suggestions, list) or not suggestions:
                        continue
                    if LabelingCopilotService.is_hidden_control(
                        scenario.id, user_id, row.item_id, copilot_cfg, str(span_id)
                    ):
                        continue
                    visible[str(span_id)] = {"suggestions": suggestions}
                if visible:
                    result[row.item_id] = {"spans": visible}
                continue

            suggestions = payload.get("suggestions")
            if not isinstance(suggestions, list) or not suggestions:
                continue
            if LabelingCopilotService.is_hidden_control(
                scenario.id, user_id, row.item_id, copilot_cfg
            ):
                continue
            result[row.item_id] = {"suggestions": suggestions}
        return result

    # ------------------------------------------------------------------
    # Conversation labeling: span inventory + server-side {context}
    # ------------------------------------------------------------------

    @staticmethod
    def spans_for_item(item) -> List[Dict[str, Any]]:
        """Ordered span index of a conversation item (empty for other types)."""
        meta = getattr(item, "metadata_json", None) or {}
        block = meta.get("conversation_labeling")
        if not isinstance(block, dict):
            return []
        spans = block.get("spans")
        return spans if isinstance(spans, list) else []

    @staticmethod
    def build_span_context(
        messages: List[Any],
        span: Dict[str, Any],
        copilot_cfg: Dict[str, Any],
        conversation_cfg: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the {context} block for ONE span, server-side.

        Previously {context} came from ``metadata.context`` — a value the
        importer had to assemble and keep in sync with what the interface
        shows. Building it here makes "the human and the model see the same
        window" a property of the code instead of a convention: both follow the
        scenario's ``context_window`` / ``no_future_messages`` settings.

        Convention (PsyDefDetect): context runs up to and INCLUDING the target
        span, never beyond. The target itself is marked so the model knows
        which clause it is being asked about.

        ``messages`` must already be in reading order.
        """
        cfg = conversation_cfg or {}
        try:
            window = int(cfg.get("context_window", 3))
        except (TypeError, ValueError):
            window = 3
        no_future = cfg.get("no_future_messages", True) is not False

        target_idx = int(span.get("message_index") or 0)
        first = 0 if window < 0 else max(0, target_idx - window)
        last = target_idx if no_future else len(messages) - 1

        lines: List[str] = []
        for i in range(first, min(last, len(messages) - 1) + 1):
            msg = messages[i]
            sender = getattr(msg, "sender", "") or ""
            content = str(getattr(msg, "content", "") or "")
            if i == target_idx:
                # Cut the target message at the end of the span: everything
                # after it is future information the rater does not have when
                # deciding either.
                end = int(span.get("end") or len(content))
                content = content[:end]
            lines.append(f"{sender}: {content}".strip())

        return "\n".join(lines).strip() or "(kein zusätzlicher Kontext)"

    # ------------------------------------------------------------------
    # Logging (called from the labeling evaluate endpoint)
    # ------------------------------------------------------------------

    @staticmethod
    def record_label_event(
        scenario: RatingScenarios,
        user_id: int,
        item_id: int,
        final_label: Optional[str],
        time_on_item_ms: Optional[int] = None,
        helpful: Optional[bool] = None,
        span_id: str = "",
    ) -> Optional[LabelingCopilotLog]:
        """Upsert the copilot log row for a labeled item.

        No-op when the co-pilot is not enabled for the scenario. Everything
        study-relevant (shown, suggested labels, acceptance) is derived
        server-side from config + cache - the client only contributes
        time_on_item_ms and the helpful flag.
        """
        copilot_cfg = LabelingCopilotService.get_copilot_config(scenario)
        if not copilot_cfg:
            return None

        hidden = LabelingCopilotService.is_hidden_control(
            scenario.id, user_id, item_id, copilot_cfg, span_id
        )
        # Scenario parts: items outside copilot-enabled parts never showed a
        # suggestion, regardless of cache/hash — the log row must snapshot
        # shown=False for them (their timing feeds the without-copilot
        # baseline; per-part aggregates separate the phases).
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        part_gate = ScenarioPartsService.copilot_item_ids(scenario)
        if part_gate is not None and item_id not in part_gate:
            hidden = True
        cached = None
        if not hidden:
            cached = LabelingCopilotService._get_cached_result(
                scenario.id, item_id, copilot_cfg
            )

        shown = cached is not None
        suggestions = (cached.payload_json or {}).get("suggestions") if cached else None
        primary = None
        secondary = None
        if suggestions:
            primary = str(suggestions[0].get("label_id") or "") or None
            if len(suggestions) > 1:
                secondary = str(suggestions[1].get("label_id") or "") or None

        accepted = None
        accepted_any = None
        if shown and final_label is not None:
            accepted = final_label == primary
            accepted_any = final_label in {s for s in (primary, secondary) if s}

        log = LabelingCopilotLog.query.filter_by(
            user_id=user_id, item_id=item_id, scenario_id=scenario.id,
            span_id=span_id
        ).first()
        if log is None:
            log = LabelingCopilotLog(
                scenario_id=scenario.id, item_id=item_id, user_id=user_id,
                span_id=span_id
            )
            db.session.add(log)

        log.suggestion_result_id = cached.id if cached else None
        log.shown = shown
        log.suggested_label = primary
        log.suggested_label_2 = secondary
        log.suggestions_json = {"suggestions": suggestions} if suggestions else None
        log.model_id = copilot_cfg.get("model_id")
        log.prompt_version = int(copilot_cfg.get("prompt_version") or 1)
        log.final_label = final_label
        log.accepted = accepted
        log.accepted_any = accepted_any
        if helpful is not None:
            log.helpful = bool(helpful)
        # First-write only: revisits/corrections must not overwrite the primary
        # "time to first label" measure.
        if time_on_item_ms is not None and log.time_on_item_ms is None:
            try:
                log.time_on_item_ms = max(0, int(time_on_item_ms))
            except (TypeError, ValueError):
                pass
        return log

    # ------------------------------------------------------------------
    # Batch generation control
    # ------------------------------------------------------------------

    @staticmethod
    def queue_model_id(model_id: str) -> str:
        return f"{LabelingCopilotService.QUEUE_MODEL_PREFIX}{model_id}"

    @staticmethod
    def strip_queue_prefix(queued_model_id: str) -> str:
        prefix = LabelingCopilotService.QUEUE_MODEL_PREFIX
        if queued_model_id.startswith(prefix):
            return queued_model_id[len(prefix):]
        return queued_model_id

    @staticmethod
    def start_generation(scenario: RatingScenarios, clear_errors: bool = True) -> Dict[str, Any]:
        """Enqueue the durable batch generation of suggestions for a scenario.

        clear_errors: like the manual evaluator retry flow, drop error records
        first so the runner treats those items as pending again.
        """
        copilot_cfg = LabelingCopilotService.get_copilot_config(scenario)
        if not copilot_cfg:
            return {"queued": False, "reason": "copilot_disabled"}
        model_id = copilot_cfg.get("model_id")
        if not model_id:
            return {"queued": False, "reason": "no_model"}

        if clear_errors:
            LLMTaskResult.query.filter(
                LLMTaskResult.scenario_id == scenario.id,
                LLMTaskResult.model_id == model_id,
                LLMTaskResult.task_type == LabelingCopilotService.TASK_TYPE,
                LLMTaskResult.error.isnot(None),
            ).delete(synchronize_session=False)
            db.session.commit()

        from services.background_jobs import LLMEvalQueueService
        LLMEvalQueueService.enqueue_run(
            scenario.id,
            model_id=LabelingCopilotService.queue_model_id(model_id),
            requested_all=True,
            task_type=LabelingCopilotService.TASK_TYPE,
        )
        logger.info(
            "[Copilot] Queued suggestion generation for scenario %s model %s (prompt v%s)",
            scenario.id, model_id, copilot_cfg.get("prompt_version"),
        )
        return {"queued": True, "model_id": model_id,
                "prompt_version": copilot_cfg.get("prompt_version")}

    @staticmethod
    def get_status(scenario: RatingScenarios) -> Dict[str, Any]:
        """Generation status for the assessors tab / wizard: counts + freshness."""
        copilot_cfg = LabelingCopilotService.get_copilot_config(scenario)
        if not copilot_cfg:
            return {"enabled": False}
        model_id = copilot_cfg.get("model_id")
        current_version = str(copilot_cfg.get("prompt_version") or 1)

        # Scenario parts: the generation scope is limited to copilot-enabled
        # parts, so status counts must use the same denominator — otherwise a
        # partitioned study would forever show "pending" items the runner
        # deliberately skips.
        from services.evaluation.scenario_parts_service import ScenarioPartsService
        part_gate = ScenarioPartsService.copilot_item_ids(scenario)
        if part_gate is not None:
            total_items = len(part_gate)
        else:
            total_items = ScenarioThreads.query.filter_by(scenario_id=scenario.id).count()
        rows = LLMTaskResult.query.filter_by(
            scenario_id=scenario.id,
            model_id=model_id,
            task_type=LabelingCopilotService.TASK_TYPE,
        ).all() if model_id else []
        if part_gate is not None:
            # Rows generated before a part was switched off would otherwise
            # inflate completed/stale beyond the scoped denominator.
            rows = [r for r in rows if r.item_id in part_gate]

        completed = sum(
            1 for r in rows
            if r.payload_json and str(r.prompt_version or "") == current_version
        )
        stale = sum(
            1 for r in rows
            if r.payload_json and str(r.prompt_version or "") != current_version
        )
        errors = sum(1 for r in rows if r.error and not r.payload_json)

        from services.background_jobs import LLMEvalQueueService
        running = bool(model_id) and LLMEvalQueueService.is_active(
            scenario.id, LabelingCopilotService.queue_model_id(model_id)
        )

        return {
            "enabled": True,
            "model_id": model_id,
            "prompt_version": copilot_cfg.get("prompt_version") or 1,
            "top_k": copilot_cfg.get("top_k") or 1,
            "hidden_control_ratio": copilot_cfg.get("hidden_control_ratio") or 0.0,
            "total_items": total_items,
            "completed": completed,
            "stale": stale,
            "errors": errors,
            "pending": max(0, total_items - completed - stale - errors),
            "running": running,
        }

    # ------------------------------------------------------------------
    # Aggregates (export / evaluation)
    # ------------------------------------------------------------------

    @staticmethod
    def get_copilot_metrics(scenario_id: int) -> Dict[str, Any]:
        """Acceptance/helpful/time aggregates over the copilot log.

        Reported per annotator and per suggested label; times split by
        shown/hidden (basis for the PsyDefConv-style time comparison).
        """
        logs = LabelingCopilotLog.query.filter_by(scenario_id=scenario_id).all()
        if not logs:
            return {"available": False}

        def _rate(rows: List[LabelingCopilotLog], attr: str) -> Optional[float]:
            vals = [getattr(r, attr) for r in rows if getattr(r, attr) is not None]
            return round(sum(1 for v in vals if v) / len(vals), 4) if vals else None

        def _mean_time(rows: List[LabelingCopilotLog]) -> Optional[float]:
            vals = [r.time_on_item_ms for r in rows if r.time_on_item_ms is not None]
            return round(sum(vals) / len(vals), 1) if vals else None

        shown_rows = [r for r in logs if r.shown]
        hidden_rows = [r for r in logs if not r.shown]

        by_user: Dict[int, Dict[str, Any]] = {}
        for user_id in sorted({r.user_id for r in logs}):
            user_rows = [r for r in logs if r.user_id == user_id]
            user_shown = [r for r in user_rows if r.shown]
            by_user[user_id] = {
                "labeled_items": len(user_rows),
                "shown_items": len(user_shown),
                "acceptance_rate": _rate(user_shown, "accepted"),
                "acceptance_rate_any": _rate(user_shown, "accepted_any"),
                "helpful_rate": _rate(user_shown, "helpful"),
                "mean_time_ms_with_copilot": _mean_time(user_shown),
                "mean_time_ms_without_copilot": _mean_time(
                    [r for r in user_rows if not r.shown]
                ),
            }

        by_label: Dict[str, Any] = {}
        for label in sorted({r.suggested_label for r in shown_rows if r.suggested_label}):
            label_rows = [r for r in shown_rows if r.suggested_label == label]
            by_label[label] = {
                "suggested_count": len(label_rows),
                "acceptance_rate": _rate(label_rows, "accepted"),
            }

        # Scenario parts: additionally aggregate per part so calibration
        # phases (no copilot) and the main phase (copilot + hidden control)
        # can be compared directly in the export. Empty when parts inactive.
        by_part: Dict[str, Any] = {}
        scenario = RatingScenarios.query.get(scenario_id)
        if scenario is not None:
            from services.evaluation.scenario_parts_service import ScenarioPartsService
            part_map = ScenarioPartsService.item_part_map(scenario)
            if part_map:
                for part_id in sorted({part_map.get(r.item_id) for r in logs
                                       if part_map.get(r.item_id)}):
                    rows = [r for r in logs if part_map.get(r.item_id) == part_id]
                    part_shown = [r for r in rows if r.shown]
                    part_hidden = [r for r in rows if not r.shown]
                    by_part[part_id] = {
                        "logged_items": len(rows),
                        "shown_items": len(part_shown),
                        "hidden_items": len(part_hidden),
                        "acceptance_rate": _rate(part_shown, "accepted"),
                        "acceptance_rate_any": _rate(part_shown, "accepted_any"),
                        "helpful_rate": _rate(part_shown, "helpful"),
                        "mean_time_ms_with_copilot": _mean_time(part_shown),
                        "mean_time_ms_without_copilot": _mean_time(part_hidden),
                    }

        return {
            "available": True,
            "logged_items": len(logs),
            "shown_items": len(shown_rows),
            "hidden_control_items": len(hidden_rows),
            "acceptance_rate": _rate(shown_rows, "accepted"),
            "acceptance_rate_any": _rate(shown_rows, "accepted_any"),
            "helpful_rate": _rate(shown_rows, "helpful"),
            "mean_time_ms_with_copilot": _mean_time(shown_rows),
            "mean_time_ms_without_copilot": _mean_time(hidden_rows),
            "per_annotator": by_user,
            "per_label": by_label,
            "per_part": by_part,
        }
