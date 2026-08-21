"""Scenario Parts Service (Teile/Phasen für Labeling-Szenarien).

Optionale Gliederung eines Labeling-Szenarios (function_type 7) in geordnete
Teile mit Teil-eigenen Optionen — getragen von Kalibrierungs-Studien wie
VRM-OnCoCo (P1 Kalibrierung → IRR/Alignment → P2 → IRR-Gate → P3 Hauptphase
mit Co-Pilot + verdecktem Kontrollsubset):

- order:   'sequential' = item_ids-Reihenfolge, für ALLE Rater identisch;
           'random' = deterministischer Per-User-Shuffle (Seed aus
           scenario/user/part — Muster von LabelingCopilotService.is_hidden_control)
- copilot: Teil-Override unter dem Master-Schalter copilot.enabled; der
           Runner generiert nur für Items aus Co-Pilot-Teilen
- locked:  gesperrte Teile werden Assessoren nicht ausgeliefert und zählen
           nicht in deren Fortschritt (Studien-Gate, Owner schaltet frei)

Sicherheits-Invariante (studienkritisch): Für Evaluatoren ist die Teilung
UNSICHTBAR. Kein part-Feld an Session-Items, parts-/copilot-Sektionen werden
aus jeder an Assessoren ausgelieferten Config gestrippt
(sanitize_config_for_assessor), Item-Summen werden auf offene Teile skaliert.
Ein freigeschalteter Teil sieht für Rater aus wie "es sind neue Items da".

Config-Ort: config_json.eval_config.config.parts (Geschwister von 'copilot',
gleiche Unwrap-Mechanik wie LabelingCopilotService.locate_inner_config).
Kanonisch gespeichert werden INTERNE EvaluationItem-IDs (int); Erstellungs-
Specs ('size' = die nächsten N Items in Upload-Reihenfolge, oder externe
String-IDs aus dem v1-Payload) löst resolve_specs() in derselben Transaktion
auf. Solange kein Teil aufgelöste item_ids hat, ist die Config "unresolved"
und verhält sich wie enabled=false (zweistufiger Wizard-Flow: Szenario
zuerst, Item-Import danach).

Siehe .claude/plans/scenario-parts-design.md für das vollständige Design.
"""

from __future__ import annotations

import hashlib
import json
import logging
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from db import db
from db.models import RatingScenarios, ScenarioThreads, User

logger = logging.getLogger(__name__)

# Both labeling flavours use scenario parts identically — a part is a set of
# items either way; for conversation labeling those items happen to be whole
# conversations, which is exactly what the study wants `size` to count.
from services.evaluation.labeling_types import (  # noqa: E402
    LABELING_FUNCTION_TYPE_IDS,
    is_labeling_type,
)

LABELING_FUNCTION_TYPE_ID = 7

VALID_ORDERS = ("sequential", "random")

# Felder, die PUT /parts/<part_id> ändern darf. item_ids sind bewusst NICHT
# dabei: die Partition-Invariante macht Einzel-Teil-Edits ill-defined
# (siehe Design-Doc §4); Nachladen läuft über POST /items mit part_id.
PART_EDITABLE_FIELDS = {"locked", "copilot", "name", "order"}


class PartsConfigError(ValueError):
    """Validierungs-/Auflösungsfehler in einer Parts-Config.

    ValueError-Subklasse, damit Aufrufer sie in ihre jeweilige
    HTTP-Fehlermechanik (400) heben können.
    """


class ScenarioPartsService:
    """Config-Zugriff, Auflösung, Validierung und Auslieferungs-Logik für Teile."""

    # ------------------------------------------------------------------
    # Config access (Unwrap-Mechanik identisch zum Copilot)
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
    def _inner_config(config: Any) -> Dict[str, Any]:
        from services.evaluation.labeling_copilot_service import LabelingCopilotService
        return LabelingCopilotService.locate_inner_config(config)

    @staticmethod
    def get_parts_config(scenario_or_config: Any) -> Optional[Dict[str, Any]]:
        """Parts-Dict wenn enabled (unabhängig vom Auflösungs-Zustand), sonst None."""
        config = scenario_or_config
        if isinstance(scenario_or_config, RatingScenarios):
            config = scenario_or_config.config_json
        inner = ScenarioPartsService._inner_config(config)
        parts = ScenarioPartsService._to_dict(inner.get("parts"))
        if not parts or not parts.get("enabled"):
            return None
        part_list = parts.get("list")
        if not isinstance(part_list, list) or not part_list:
            return None
        return parts

    @staticmethod
    def _resolved_ids(part: Dict[str, Any]) -> List[int]:
        """Aufgelöste (interne, int) item_ids eines Teils; [] wenn unresolved."""
        ids = part.get("item_ids")
        if not isinstance(ids, list) or not ids:
            return []
        out: List[int] = []
        for value in ids:
            if isinstance(value, bool) or not isinstance(value, int):
                return []  # externe String-IDs o. Ä. → unresolved
            out.append(value)
        return out

    @staticmethod
    def is_resolved(parts_cfg: Dict[str, Any]) -> bool:
        part_list = parts_cfg.get("list") or []
        return bool(part_list) and all(
            ScenarioPartsService._resolved_ids(p) for p in part_list
            if isinstance(p, dict)
        )

    @staticmethod
    def get_active_parts(scenario_or_config: Any) -> Optional[List[Dict[str, Any]]]:
        """Teil-Liste wenn enabled UND aufgelöst — sonst None (= Feature inaktiv).

        Unresolved (Wizard hat das Szenario erstellt, Items sind noch nicht
        importiert) verhält sich bewusst wie enabled=false: die Session darf
        in diesem Fenster nicht auf einer halben Zuordnung filtern.
        """
        parts_cfg = ScenarioPartsService.get_parts_config(scenario_or_config)
        if not parts_cfg or not ScenarioPartsService.is_resolved(parts_cfg):
            return None
        return [p for p in parts_cfg.get("list", []) if isinstance(p, dict)]

    # ------------------------------------------------------------------
    # Normalisierung + Validierung (Create/Update-Chokepoints)
    # ------------------------------------------------------------------

    @staticmethod
    def normalize_config_on_write(config: Any, previous_config: Any = None) -> Any:
        """Parts-Sektion vor dem Persistieren normalisieren.

        - Teil-IDs erzeugen (p1..pn) bzw. Eindeutigkeit erzwingen
        - Flags koerzieren (copilot/locked → bool, order → gültiger Wert)
        - Server-Autorität über aufgelöste Zuordnungen: hatte ein Teil in der
          Vorgänger-Config bereits aufgelöste item_ids, überschreiben diese
          das, was der Client schickt (Audit-Trail; generische Config-PUTs
          können die Zuordnung nicht verändern — nur POST /items mit part_id)

        No-op für Configs ohne parts-Sektion; safe für alle function_types.
        """
        config_dict = ScenarioPartsService._to_dict(config)
        if not config_dict:
            return config
        inner = ScenarioPartsService._inner_config(config_dict)
        parts = inner.get("parts")
        if not isinstance(parts, dict):
            return config

        prev_by_id: Dict[str, Dict[str, Any]] = {}
        previous = ScenarioPartsService._to_dict(previous_config)
        if previous:
            prev_inner = ScenarioPartsService._inner_config(previous)
            prev_parts = ScenarioPartsService._to_dict(prev_inner.get("parts"))
            for prev_part in prev_parts.get("list") or []:
                if isinstance(prev_part, dict) and prev_part.get("id"):
                    prev_by_id[str(prev_part["id"])] = prev_part

        raw_list = parts.get("list")
        if not isinstance(raw_list, list):
            raw_list = []
        normalized: List[Dict[str, Any]] = []
        used_ids: Set[str] = set()
        for idx, part in enumerate(raw_list):
            if not isinstance(part, dict):
                raise PartsConfigError("parts.list entries must be objects")
            part = dict(part)
            pid = str(part.get("id") or "").strip() or f"p{idx + 1}"
            while pid in used_ids:
                pid = f"{pid}_{idx + 1}"
            used_ids.add(pid)
            part["id"] = pid
            part["name"] = str(part.get("name") or "").strip() or pid
            part["order"] = part.get("order") if part.get("order") in VALID_ORDERS else "sequential"
            part["copilot"] = bool(part.get("copilot"))
            part["locked"] = bool(part.get("locked"))

            prev_part = prev_by_id.get(pid)
            prev_ids = ScenarioPartsService._resolved_ids(prev_part) if prev_part else []
            if prev_ids:
                part["item_ids"] = prev_ids
                part.pop("size", None)
            normalized.append(part)

        parts["enabled"] = bool(parts.get("enabled"))
        parts["list"] = normalized
        ScenarioPartsService._write_parts(config_dict, parts)
        return config_dict

    @staticmethod
    def _write_parts(config_dict: Dict[str, Any], parts: Dict[str, Any]) -> None:
        """Parts in die Config schreiben — inkl. v1-Spiegel-Location.

        v1-erstellte Szenarien duplizieren die innere Config an
        config['config'] UND config['eval_config']['config'] (nach einem
        DB-Roundtrip getrennte Objekte) — beide synchron halten, gleiche
        Mechanik wie die Copilot-PUT-Route.
        """
        inner = ScenarioPartsService._inner_config(config_dict)
        inner["parts"] = parts
        mirror = config_dict.get("config")
        if isinstance(mirror, dict) and mirror is not inner:
            mirror["parts"] = parts
        eval_config = config_dict.get("eval_config")
        if isinstance(eval_config, dict):
            eval_inner = eval_config.get("config")
            if isinstance(eval_inner, dict) and eval_inner is not inner:
                eval_inner["parts"] = parts

    @staticmethod
    def _scenario_item_ids_ordered(scenario_id: int) -> List[int]:
        """Alle Szenario-Item-IDs in Upload-/Erstellreihenfolge (= thread_id asc,
        identisch zur heutigen Session-Sortierung in session_service:148)."""
        rows = (
            db.session.query(ScenarioThreads.thread_id)
            .filter(ScenarioThreads.scenario_id == scenario_id)
            .order_by(ScenarioThreads.thread_id)
            .all()
        )
        return [r[0] for r in rows]

    @staticmethod
    def validate_partition(scenario_id: int, part_list: List[Dict[str, Any]]) -> None:
        """Partition-Invariante: jedes Szenario-Item in GENAU einem Teil."""
        scenario_ids = set(ScenarioPartsService._scenario_item_ids_ordered(scenario_id))
        assigned: List[int] = []
        for part in part_list:
            assigned.extend(ScenarioPartsService._resolved_ids(part))
        duplicates = {i for i in assigned if assigned.count(i) > 1} if len(assigned) != len(set(assigned)) else set()
        if duplicates:
            raise PartsConfigError(
                f"items assigned to more than one part: {sorted(duplicates)[:10]}"
            )
        assigned_set = set(assigned)
        foreign = assigned_set - scenario_ids
        if foreign:
            raise PartsConfigError(
                f"item_ids not in scenario: {sorted(foreign)[:10]}"
            )
        missing = scenario_ids - assigned_set
        if missing:
            raise PartsConfigError(
                f"{len(missing)} scenario items not assigned to any part "
                f"(e.g. {sorted(missing)[:10]})"
            )

    # ------------------------------------------------------------------
    # Auflösung der Erstellungs-Specs (size / externe IDs → interne IDs)
    # ------------------------------------------------------------------

    @staticmethod
    def _external_chat_id(external_id: str) -> int:
        # Spiegelt _generate_chat_id (api_v1_scenario_service/ImportService):
        # externe Item-IDs werden nur als chat_id-Hash persistiert.
        h = int(hashlib.md5(external_id.encode()).hexdigest()[:8], 16)
        return h % 2147483647

    @staticmethod
    def resolve_specs(scenario: RatingScenarios) -> bool:
        """size-/External-ID-Specs in interne item_ids auflösen + validieren.

        Zwei Pässe: zuerst explizite item_ids-Teile (int direkt, str via
        chat_id-Hash), dann konsumieren size-Teile die verbleibenden Items in
        Upload-Reihenfolge; ein letzter Teil ohne beides nimmt den Rest.
        Schreibt die aufgelöste Config zurück auf scenario.config_json
        (Commit macht der Aufrufer). Returns True wenn aufgelöst wurde,
        False wenn nichts zu tun war (disabled/bereits aufgelöst).
        """
        parts_cfg = ScenarioPartsService.get_parts_config(scenario)
        if not parts_cfg:
            return False
        if ScenarioPartsService.is_resolved(parts_cfg):
            return False

        ordered_ids = ScenarioPartsService._scenario_item_ids_ordered(scenario.id)
        if not ordered_ids:
            # No items yet (wizard creates the scenario before importing) —
            # stay unresolved; the import hook resolves later. The v1 create
            # path enforces "items in the same request" separately.
            return False

        # JSON-Roundtrip: nie das an SQLAlchemy hängende Dict in place mutieren
        config = json.loads(json.dumps(scenario.config_json or {}))
        inner = ScenarioPartsService._inner_config(config)
        parts = ScenarioPartsService._to_dict(inner.get("parts"))
        part_list = [dict(p) for p in parts.get("list", []) if isinstance(p, dict)]

        remaining = list(ordered_ids)
        remaining_set = set(remaining)

        chat_map: Dict[int, int] = {}
        from db.models import EvaluationItem
        for item_id, chat_id in (
            db.session.query(EvaluationItem.item_id, EvaluationItem.chat_id)
            .filter(EvaluationItem.item_id.in_(ordered_ids))
            .all()
        ):
            chat_map.setdefault(chat_id, item_id)

        def _take(ids: List[int], part_id: str) -> None:
            for item_id in ids:
                if item_id not in remaining_set:
                    raise PartsConfigError(
                        f"part '{part_id}': item {item_id} is not an unassigned "
                        "scenario item (duplicate or foreign id)"
                    )
                remaining_set.discard(item_id)
            # Reihenfolge von `remaining` erhalten (size-Teile konsumieren
            # Upload-Reihenfolge unter den noch nicht zugeordneten Items)
            remaining[:] = [i for i in remaining if i in remaining_set]

        # Pass 1: explizite Zuordnungen
        for part in part_list:
            raw_ids = part.get("item_ids")
            if not isinstance(raw_ids, list) or not raw_ids:
                continue
            resolved: List[int] = []
            for ref in raw_ids:
                if isinstance(ref, bool):
                    raise PartsConfigError(f"part '{part.get('id')}': invalid item ref {ref!r}")
                if isinstance(ref, int):
                    resolved.append(ref)
                    continue
                chat_id = ScenarioPartsService._external_chat_id(str(ref))
                item_id = chat_map.get(chat_id)
                if item_id is None:
                    raise PartsConfigError(
                        f"part '{part.get('id')}': external item id {ref!r} "
                        "does not match any item in this scenario"
                    )
                resolved.append(item_id)
            _take(resolved, str(part.get("id")))
            part["item_ids"] = resolved
            part.pop("size", None)

        # Pass 2: size-Specs + Rest-Teil in Listen-Reihenfolge
        for idx, part in enumerate(part_list):
            if ScenarioPartsService._resolved_ids(part):
                continue
            size = part.get("size")
            if size is not None:
                try:
                    size = int(size)
                except (TypeError, ValueError):
                    raise PartsConfigError(
                        f"part '{part.get('id')}': size must be an integer"
                    )
                if size < 1:
                    raise PartsConfigError(
                        f"part '{part.get('id')}': size must be >= 1"
                    )
                if size > len(remaining):
                    raise PartsConfigError(
                        f"part '{part.get('id')}': size {size} exceeds the "
                        f"{len(remaining)} unassigned items"
                    )
                part["item_ids"] = remaining[:size]
            else:
                if idx != len(part_list) - 1:
                    raise PartsConfigError(
                        f"part '{part.get('id')}' has neither item_ids nor size; "
                        "only the last part may omit both (rest)"
                    )
                if not remaining:
                    raise PartsConfigError(
                        f"part '{part.get('id')}' (rest) would be empty"
                    )
                part["item_ids"] = list(remaining)
            _take(list(part["item_ids"]), str(part.get("id")))
            part.pop("size", None)

        if remaining:
            raise PartsConfigError(
                f"{len(remaining)} items not assigned to any part "
                f"(e.g. {remaining[:10]})"
            )

        ScenarioPartsService.validate_partition(scenario.id, part_list)
        parts["list"] = part_list
        ScenarioPartsService._write_parts(config, parts)
        scenario.config_json = config
        logger.info(
            "[Parts] Resolved %d parts for scenario %s (%s)",
            len(part_list), scenario.id,
            ", ".join(f"{p['id']}={len(p['item_ids'])}" for p in part_list),
        )
        return True

    @staticmethod
    def resolve_after_import(scenario_id: int) -> None:
        """Import-Hook (execute_import): size-Specs nach dem Item-Verlinken
        auflösen. Fehler werden geloggt UND propagiert — ein Import, der die
        deklarierte Teil-Struktur nicht erfüllen kann, darf nicht still
        "ohne Teile" enden (die Studie verließe sich auf ein Gate, das es
        nicht gibt)."""
        scenario = RatingScenarios.query.get(scenario_id)
        if scenario is None or not is_labeling_type(scenario.function_type_id):
            return
        ScenarioPartsService.resolve_specs(scenario)

    @staticmethod
    def reject_unscoped_import(scenario_id: int) -> Optional[str]:
        """Fehlertext, wenn ein Item-Import ohne part_id auf ein Szenario mit
        AUFGELÖSTEN Parts trifft (stille Nicht-Zuordnung wäre die Folge);
        None wenn der Import zulässig ist (kein parts / noch unresolved)."""
        scenario = RatingScenarios.query.get(scenario_id)
        if scenario is None or not is_labeling_type(scenario.function_type_id):
            return None
        parts_cfg = ScenarioPartsService.get_parts_config(scenario)
        if not parts_cfg or not ScenarioPartsService.is_resolved(parts_cfg):
            return None
        return (
            "This scenario is partitioned into parts; adding items requires "
            "a part_id. Use POST /api/v1/scenarios/<id>/items with part_id."
        )

    # ------------------------------------------------------------------
    # Auslieferungs-Logik (Session/Runner/Stats)
    # ------------------------------------------------------------------

    @staticmethod
    def is_manager(scenario: RatingScenarios, user_id: int) -> bool:
        """Owner, Manager (manager_role != none) oder Admin — sieht alles
        (inkl. gesperrter Teile und parts-Config)."""
        user = User.query.get(user_id)
        if not user:
            return False
        if scenario.created_by and scenario.created_by == user.username:
            return True
        from db.models import ScenarioUsers
        su = ScenarioUsers.query.filter_by(
            scenario_id=scenario.id, user_id=user_id
        ).first()
        if su is not None and (su.manager_role or "none") != "none":
            return True
        try:
            from services.permission_service import PermissionService
            return PermissionService.user_has_role(user.username, "admin")
        except Exception:
            return False

    @staticmethod
    def _user_part_seed(scenario_id: int, user_id: int, part_id: str) -> int:
        # Gleiches Muster wie LabelingCopilotService.is_hidden_control:
        # deterministisch + reproduzierbar, stabil über Reloads.
        digest = hashlib.sha256(
            f"{scenario_id}:{user_id}:{part_id}".encode("utf-8")
        ).hexdigest()
        return int(digest[:8], 16)

    @staticmethod
    def session_item_order(
        scenario: RatingScenarios,
        user_id: int,
        thread_ids: List[int],
    ) -> Optional[List[int]]:
        """Sichtbare Items in Auslieferungs-Reihenfolge für die Session.

        None = Parts inaktiv → Aufrufer behält das heutige Verhalten
        (thread_id-Sortierung) bei. Sonst: offene Teile in Listen-Reihenfolge,
        innerhalb gemäß order-Modus; Manager/Owner sehen zusätzlich gesperrte
        Teile (Ergebnis-/Aufsichtsansicht).
        """
        parts = ScenarioPartsService.get_active_parts(scenario)
        if parts is None:
            return None
        include_locked = ScenarioPartsService.is_manager(scenario, user_id)

        thread_set = set(thread_ids)
        ordered: List[int] = []
        assigned: Set[int] = set()
        for part in parts:
            ids = [i for i in ScenarioPartsService._resolved_ids(part) if i in thread_set]
            assigned.update(ids)
            if part.get("locked") and not include_locked:
                continue
            if part.get("order") == "random":
                rng = random.Random(ScenarioPartsService._user_part_seed(
                    scenario.id, user_id, str(part.get("id"))
                ))
                ids = list(ids)
                rng.shuffle(ids)
            ordered.extend(ids)

        # Defensiv: nicht zugeordnete Items (Partition-Drift) hinten anhängen
        # statt sie still zu verschlucken — sichtbar für alle, in thread_id-
        # Reihenfolge. Die Partition-Validierung verhindert diesen Fall regulär.
        leftover = sorted(t for t in thread_ids if t not in assigned)
        if leftover:
            logger.warning(
                "[Parts] Scenario %s has %d items outside the partition",
                scenario.id, len(leftover),
            )
            ordered.extend(leftover)
        return ordered

    @staticmethod
    def open_item_ids(scenario_or_config: Any) -> Optional[Set[int]]:
        """Items offener (nicht gesperrter) Teile; None = Parts inaktiv."""
        parts = ScenarioPartsService.get_active_parts(scenario_or_config)
        if parts is None:
            return None
        return {
            i
            for p in parts if not p.get("locked")
            for i in ScenarioPartsService._resolved_ids(p)
        }

    @staticmethod
    def copilot_item_ids(scenario_or_config: Any) -> Optional[Set[int]]:
        """Items aus Teilen mit copilot=true; None = Parts inaktiv (kein Gating)."""
        parts = ScenarioPartsService.get_active_parts(scenario_or_config)
        if parts is None:
            return None
        return {
            i
            for p in parts if p.get("copilot")
            for i in ScenarioPartsService._resolved_ids(p)
        }

    @staticmethod
    def item_part_map(scenario_or_config: Any) -> Dict[int, str]:
        """item_id → part_id für Export/Metrics; {} wenn Parts inaktiv."""
        parts = ScenarioPartsService.get_active_parts(scenario_or_config)
        if parts is None:
            return {}
        mapping: Dict[int, str] = {}
        for part in parts:
            pid = str(part.get("id"))
            for item_id in ScenarioPartsService._resolved_ids(part):
                mapping[item_id] = pid
        return mapping

    @staticmethod
    def sanitize_config_for_assessor(config: Any) -> Any:
        """Deep-Copy der Config ohne parts-/copilot-Sektionen (alle Locations).

        Studienkritisch: Die Session-/Listen-Antworten liefern das volle
        config-Objekt an den Client. Assessoren dürfen weder die Teilung
        (parts: item_ids/locked/copilot) noch die Copilot-Interna
        (hidden_control_salt/ratio → Kontrollsubset wäre klientseitig
        berechenbar) sehen. Owner/Manager erhalten die ungestrippte Config.
        """
        config_dict = ScenarioPartsService._to_dict(config)
        if not config_dict:
            return config
        sanitized = json.loads(json.dumps(config_dict))

        def _strip(node: Any) -> None:
            if not isinstance(node, dict):
                return
            node.pop("parts", None)
            node.pop("copilot", None)

        _strip(sanitized)
        _strip(sanitized.get("config"))
        eval_config = sanitized.get("eval_config")
        _strip(eval_config)
        if isinstance(eval_config, dict):
            _strip(eval_config.get("config"))
        return sanitized

    # ------------------------------------------------------------------
    # Owner-API (Status / Update / Items-Nachladen)
    # ------------------------------------------------------------------

    @staticmethod
    def get_parts_status(scenario: RatingScenarios) -> Dict[str, Any]:
        """Status aller Teile inkl. Fortschritt pro aktivem Assessor."""
        parts_cfg = ScenarioPartsService.get_parts_config(scenario)
        if not parts_cfg:
            return {"enabled": False, "resolved": False, "parts": []}
        resolved = ScenarioPartsService.is_resolved(parts_cfg)

        from db.models import ScenarioUsers
        from db.models.scenario import (
            ItemLabelingEvaluation,
            InvitationStatus,
            MembershipStatus,
        )
        assessor_rows = (
            db.session.query(ScenarioUsers, User)
            .join(User, User.id == ScenarioUsers.user_id)
            .filter(
                ScenarioUsers.scenario_id == scenario.id,
                ScenarioUsers.evaluation_role == "assessor",
                ScenarioUsers.invitation_status == InvitationStatus.ACCEPTED,
                ScenarioUsers.membership_status == MembershipStatus.ACTIVE,
            )
            .all()
        )
        assessors = [(su.user_id, user.username) for su, user in assessor_rows]

        labeled: Dict[Tuple[int, int], bool] = {}
        if resolved and assessors:
            rows = ItemLabelingEvaluation.query.filter(
                ItemLabelingEvaluation.scenario_id == scenario.id,
                ItemLabelingEvaluation.user_id.in_([a[0] for a in assessors]),
            ).all()
            for row in rows:
                if row.category_id is not None or row.is_unsure:
                    labeled[(row.user_id, row.item_id)] = True

        parts_out: List[Dict[str, Any]] = []
        for part in parts_cfg.get("list", []):
            if not isinstance(part, dict):
                continue
            item_ids = ScenarioPartsService._resolved_ids(part)
            progress = [
                {
                    "user_id": user_id,
                    "username": username,
                    "labeled": sum(1 for i in item_ids if labeled.get((user_id, i))),
                    "total": len(item_ids),
                }
                for user_id, username in assessors
            ]
            parts_out.append({
                "id": part.get("id"),
                "name": part.get("name"),
                "order": part.get("order") or "sequential",
                "copilot": bool(part.get("copilot")),
                "locked": bool(part.get("locked")),
                "item_count": len(item_ids),
                "size": part.get("size"),
                "resolved": bool(item_ids),
                "assessors": progress,
            })

        return {"enabled": True, "resolved": resolved, "parts": parts_out}

    @staticmethod
    def update_part(
        scenario: RatingScenarios,
        part_id: str,
        fields: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Partial-Update eines Teils (locked/copilot/name/order).

        Schreibt die neue Config auf scenario.config_json (Commit macht der
        Aufrufer) und gibt den aktualisierten Teil-Status zurück.
        """
        unknown = set(fields.keys()) - PART_EDITABLE_FIELDS
        if unknown:
            raise PartsConfigError(
                f"Unknown fields: {sorted(unknown)}. "
                f"Editable: {sorted(PART_EDITABLE_FIELDS)}"
            )
        if "order" in fields and fields["order"] not in VALID_ORDERS:
            raise PartsConfigError(f"order must be one of {VALID_ORDERS}")
        for flag in ("locked", "copilot"):
            if flag in fields and not isinstance(fields[flag], bool):
                raise PartsConfigError(f"{flag} must be a boolean")
        if "name" in fields and not str(fields["name"] or "").strip():
            raise PartsConfigError("name must be a non-empty string")

        parts_cfg = ScenarioPartsService.get_parts_config(scenario)
        if not parts_cfg:
            raise PartsConfigError("Scenario has no enabled parts config")

        config = json.loads(json.dumps(scenario.config_json or {}))
        inner = ScenarioPartsService._inner_config(config)
        parts = ScenarioPartsService._to_dict(inner.get("parts"))
        part_list = [dict(p) for p in parts.get("list", []) if isinstance(p, dict)]
        target = next((p for p in part_list if str(p.get("id")) == str(part_id)), None)
        if target is None:
            known = [str(p.get("id")) for p in part_list]
            raise PartsConfigError(f"Unknown part '{part_id}'. Known parts: {known}")

        if "name" in fields:
            target["name"] = str(fields["name"]).strip()
        for key in ("order", "locked", "copilot"):
            if key in fields:
                target[key] = fields[key]

        parts["list"] = part_list
        ScenarioPartsService._write_parts(config, parts)
        scenario.config_json = config
        logger.info(
            "[Parts] Updated part '%s' of scenario %s: %s",
            part_id, scenario.id, fields,
        )
        return target

    @staticmethod
    def append_items_to_part(
        scenario: RatingScenarios,
        part_id: str,
        new_item_ids: List[int],
    ) -> None:
        """Nachgeladene Items genau einem Teil zuordnen (POST /items + part_id).

        Erwartet AUFGELÖSTE Parts; validiert die Partition nach dem Anhängen.
        Schreibt auf scenario.config_json (Commit macht der Aufrufer).
        """
        parts_cfg = ScenarioPartsService.get_parts_config(scenario)
        if not parts_cfg:
            raise PartsConfigError("Scenario has no enabled parts config")
        if not ScenarioPartsService.is_resolved(parts_cfg):
            raise PartsConfigError(
                "Parts are not resolved yet (no items assigned); create the "
                "scenario with items or import the initial items first"
            )

        config = json.loads(json.dumps(scenario.config_json or {}))
        inner = ScenarioPartsService._inner_config(config)
        parts = ScenarioPartsService._to_dict(inner.get("parts"))
        part_list = [dict(p) for p in parts.get("list", []) if isinstance(p, dict)]
        target = next((p for p in part_list if str(p.get("id")) == str(part_id)), None)
        if target is None:
            known = [str(p.get("id")) for p in part_list]
            raise PartsConfigError(f"Unknown part '{part_id}'. Known parts: {known}")

        target["item_ids"] = ScenarioPartsService._resolved_ids(target) + [
            int(i) for i in new_item_ids
        ]
        ScenarioPartsService.validate_partition(scenario.id, part_list)
        parts["list"] = part_list
        ScenarioPartsService._write_parts(config, parts)
        scenario.config_json = config
        logger.info(
            "[Parts] Appended %d items to part '%s' of scenario %s",
            len(new_item_ids), part_id, scenario.id,
        )
