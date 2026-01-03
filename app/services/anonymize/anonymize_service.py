# anonymize_service.py
"""
Anonymize Service - Main service class for text pseudonymization.

This module combines all anonymize functionality:
- anonymize_constants: Constants, patterns, data structures
- anonymize_paths: Resource path configuration
- anonymize_entity_detection: Regex and Flair NER detection
- anonymize_llm_detection: LLM-based entity detection
- anonymize_generators: Replacement generation
"""

from __future__ import annotations

import logging
import os
import pickle
import random
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

from .anonymize_constants import EntityOccurrence
from .anonymize_paths import get_paths
from .anonymize_entity_detection import (
    find_mail,
    find_ahv,
    find_phones,
    find_plz,
    find_dates,
    find_flair_ner,
    find_plz_from_loc,
    select_entities,
    _load_ner_tagger,
)
from .anonymize_llm_detection import (
    llm_quick_status,
    find_llm_entities,
)
from .anonymize_generators import (
    generate_age,
    generate_phone,
    generate_person,
    generate_location,
    shift_date_string,
)
from services.anonymize.pseudonymize_db import PseudonymizeDBHandler

logger = logging.getLogger(__name__)


class AnonymizeService:
    """Main service class for text anonymization/pseudonymization."""

    # Re-export for backward compatibility
    _paths = staticmethod(get_paths)
    llm_quick_status = staticmethod(llm_quick_status)
    _find_llm_entities = staticmethod(find_llm_entities)

    @staticmethod
    def quick_status() -> dict[str, Any]:
        """Quick check if required files exist."""
        paths = get_paths()
        file_checks = {
            "db": paths["db"].exists(),
            "ner_model": paths["ner_model"].exists(),
            "recommender": paths["recommender"].exists(),
            "scaler": paths["scaler"].exists(),
        }
        return {"ready": all(file_checks.values()), "files": file_checks}

    @staticmethod
    @lru_cache(maxsize=1)
    def _db() -> PseudonymizeDBHandler:
        """Get the pseudonymize database handler (cached)."""
        paths = get_paths()
        return PseudonymizeDBHandler(paths["db"])

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_recommender() -> tuple[Any, Any]:
        """Load the municipality recommender model (cached)."""
        paths = get_paths()
        with open(paths["recommender"], "rb") as f:
            recommender = pickle.load(f)
        with open(paths["scaler"], "rb") as f:
            scaler = pickle.load(f)
        return recommender, scaler

    @staticmethod
    def health_check() -> dict[str, Any]:
        """Full health check including model loading."""
        paths = get_paths()

        file_checks = {
            "db": paths["db"].exists(),
            "ner_model": paths["ner_model"].exists(),
            "recommender": paths["recommender"].exists(),
            "scaler": paths["scaler"].exists(),
        }

        details: dict[str, Any] = {"files": file_checks}

        ready = all(file_checks.values())
        if not ready:
            details["ready"] = False
            return details

        try:
            _ = AnonymizeService._db().get_random_canton()
            details["db_ok"] = True
        except Exception as e:  # pragma: no cover
            details["db_ok"] = False
            details["db_error"] = str(e)
            ready = False

        try:
            _ = AnonymizeService._load_recommender()
            details["recommender_ok"] = True
        except Exception as e:  # pragma: no cover
            details["recommender_ok"] = False
            details["recommender_error"] = str(e)
            ready = False

        try:
            tagger = _load_ner_tagger()
            from flair.data import Sentence
            sent = Sentence("Max Mustermann wohnt in Zürich.")
            tagger.predict(sent)
            details["ner_ok"] = True
        except Exception as e:  # pragma: no cover
            details["ner_ok"] = False
            details["ner_error"] = str(e)
            ready = False

        details["ready"] = bool(ready)
        return details

    @staticmethod
    def pseudonymize(
        text: str,
        group_overrides: Optional[dict[str, dict[str, Any]]] = None,
        date_shift_days: Optional[int] = None,
        action: Optional[dict[str, Any]] = None,
        name_origin: Optional[str] = None,
        name_count: Optional[int] = None,
        engine: Optional[str] = None,
        llm_model: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Pseudonymize text by detecting and replacing PII entities.

        Args:
            text: Input text to pseudonymize
            group_overrides: Manual overrides for entity groups
            date_shift_days: Days to shift dates (random if None)
            action: Action to perform (e.g., {"type": "randomize", "group_id": "..."})
            name_origin: Origin region for name generation (default: Swiss_DE)
            name_count: Pool size for name selection
            engine: Detection engine ("offline", "llm", "hybrid")
            llm_model: LLM model ID for LLM/hybrid engine

        Returns:
            Dict with input_text, output_text, entities, groups, date_shift_days
        """
        group_overrides = group_overrides or {}
        name_origin = name_origin or os.environ.get("ANONYMIZE_NAME_REGION", "Swiss_DE")
        name_count = int(name_count or os.environ.get("ANONYMIZE_NAME_COUNT", "1000"))
        engine = (engine or "offline").strip().lower()
        if engine not in {"offline", "llm", "hybrid"}:
            engine = "offline"

        cleaned_text = (text or "").replace("'", "")
        if cleaned_text.strip() == "":
            return {
                "input_text": cleaned_text,
                "output_text": cleaned_text,
                "entities": [],
                "groups": [],
                "date_shift_days": date_shift_days,
                "warnings": ["EMPTY_INPUT"],
            }

        # Collect entity candidates
        candidates: list[EntityOccurrence] = []
        candidates.extend(find_mail(cleaned_text))
        candidates.extend(find_ahv(cleaned_text))
        candidates.extend(find_phones(cleaned_text))
        candidates.extend(find_plz(cleaned_text))

        parsed_dates = find_dates(cleaned_text)
        candidates.extend([occ for _, occ in parsed_dates])

        llm_entities: list[EntityOccurrence] = []
        if engine in {"llm", "hybrid"}:
            llm_entities = find_llm_entities(cleaned_text, model=llm_model)
            candidates.extend(llm_entities)
            candidates.extend(find_plz_from_loc(cleaned_text, llm_entities))

        ner_entities: list[EntityOccurrence] = []
        if engine in {"offline", "hybrid"}:
            ner_entities = find_flair_ner(cleaned_text)
            candidates.extend(ner_entities)
            candidates.extend(find_plz_from_loc(cleaned_text, ner_entities))

        entities = select_entities(candidates)

        # Group by label + exact original string
        groups: dict[str, dict[str, Any]] = {}
        labels_present = {e.label for e in entities}

        db: Optional[PseudonymizeDBHandler] = None
        recommender_model: Any = None
        scaler: Any = None

        if labels_present.intersection({"PER", "LOC"}):
            try:
                db = AnonymizeService._db()
            except Exception as e:
                logger.warning(f"[Anonymize] DB not available: {e}")
                db = None

        if "LOC" in labels_present:
            try:
                recommender_model, scaler = AnonymizeService._load_recommender()
            except Exception as e:
                logger.warning(f"[Anonymize] Recommender not available: {e}")
                recommender_model, scaler = None, None

        # Date shift (document-wide)
        if date_shift_days is None:
            date_shift_days = random.randint(-5 * 356, -1)
        date_shift_years = int(date_shift_days // 365)

        name_part_map: dict[str, str] = {}
        location_map: dict[str, str] = {}
        location_dbhit: dict[str, bool] = {}
        date_map: dict[str, str] = {}
        age_map: dict[str, str] = {}

        action_type = (action or {}).get("type")
        action_group = (action or {}).get("group_id")

        def group_id(label: str, original: str) -> str:
            return f"{label}:{original}"

        # Pre-parse date occurrences for consistent replacements
        date_by_span: dict[tuple[int, int], Optional[datetime]] = {
            (occ.start, occ.end): dt for dt, occ in parsed_dates
        }

        for occ in entities:
            original = occ.text
            gid = group_id(occ.label, original)

            if gid not in groups:
                groups[gid] = {
                    "group_id": gid,
                    "label": occ.label,
                    "original": original,
                    "replacement": None,
                    "mode": None,
                    "db_hit": None,
                    "count": 0,
                    "first_start": occ.start,
                }

            groups[gid]["count"] += 1

        # Generate replacements (with overrides + action)
        for gid, g in groups.items():
            label = str(g["label"])
            original = str(g["original"])

            override = group_overrides.get(gid)
            override_replacement = override.get("replacement") if isinstance(override, dict) else None
            override_mode = override.get("mode") if isinstance(override, dict) else None

            should_randomize = action_type == "randomize" and action_group == gid

            replacement: str
            mode: str

            if override_replacement is not None and not should_randomize:
                replacement = str(override_replacement)
                mode = str(override_mode or "manual")
            else:
                if label == "PER":
                    if db is None:
                        replacement = "▓" * 10
                        mode = "auto"
                    else:
                        replacement = generate_person(
                            db=db,
                            old_fullname=original,
                            name_origin=name_origin,
                            name_count=name_count,
                            name_part_map=name_part_map,
                            force_new=should_randomize,
                        )
                        mode = "random" if should_randomize else "auto"
                elif label == "LOC":
                    if db is None:
                        replacement = "▓" * 10
                        mode = "auto"
                    else:
                        if should_randomize or original not in location_map:
                            replacement_loc, db_hit = generate_location(
                                db=db,
                                old_location=original,
                                recommend=True,
                                recommender_model=recommender_model,
                                scaler=scaler,
                            )
                            location_map[original] = replacement_loc
                            location_dbhit[original] = db_hit
                        replacement = location_map[original]
                        mode = "random" if should_randomize else "auto"
                elif label == "DATE":
                    if should_randomize:
                        delta = random.randint(-5 * 356, -1)
                        dt = date_by_span.get(
                            (int(g["first_start"]), int(g["first_start"]) + len(original))
                        )
                        replacement = shift_date_string(
                            original,
                            delta_days=delta,
                            delta_years=int(delta // 365),
                            parsed_dt=dt,
                        )
                        mode = "random"
                    else:
                        if gid not in date_map:
                            dt = date_by_span.get(
                                (int(g["first_start"]), int(g["first_start"]) + len(original))
                            )
                            replacement = shift_date_string(
                                original,
                                delta_days=int(date_shift_days),
                                delta_years=date_shift_years,
                                parsed_dt=dt,
                            )
                            date_map[gid] = replacement
                        replacement = date_map[gid]
                        mode = "auto"
                elif label == "AGE":
                    replacement = generate_age(
                        original=original,
                        age_map=age_map,
                        force_new=should_randomize,
                    )
                    mode = "random" if should_randomize else "auto"
                elif label == "PHONE":
                    replacement = generate_phone() if should_randomize else "▓▓▓ ▓▓▓ ▓▓ ▓▓"
                    mode = "random" if should_randomize else "auto"
                elif label == "AHV":
                    replacement = "▓▓▓.▓▓▓▓.▓▓▓▓.▓▓"
                    mode = "auto"
                elif label == "PLZ":
                    replacement = "▓▓▓▓"
                    mode = "auto"
                elif label == "MAIL":
                    replacement = "▓▓▓▓@▓▓▓.▓▓▓"
                    mode = "auto"
                else:
                    replacement = original
                    mode = "auto"

            db_hit: Optional[bool] = None
            if label == "PER":
                if db is not None:
                    parts = [p for p in original.split() if p]
                    db_hit = any(db.is_in_firstname_db(p) or db.is_in_lastname_db(p) for p in parts)
            elif label == "LOC":
                if db is not None:
                    db_hit = location_dbhit.get(original)
                    if db_hit is None:
                        normalized = original[5:].strip() if original[:4].isdigit() and len(original) >= 5 else original
                        from .anonymize_constants import COUNTRIES_GERMAN
                        db_hit = (
                            db.get_muncipality_features(normalized) is not None
                            or db.is_in_district_db(normalized)
                            or db.is_in_canton_db(normalized)
                            or normalized in COUNTRIES_GERMAN
                        )

            g["replacement"] = replacement
            g["mode"] = mode
            g["db_hit"] = db_hit

        # Build output and output spans
        entities_sorted = sorted(entities, key=lambda e: (e.start, e.end))

        output_parts: list[str] = []
        output_entities: list[dict[str, Any]] = []
        cursor = 0
        out_pos = 0

        for occ in entities_sorted:
            gid = group_id(occ.label, occ.text)
            replacement = str(groups[gid]["replacement"])

            if occ.start < cursor:
                continue

            prefix = cleaned_text[cursor:occ.start]
            output_parts.append(prefix)
            out_pos += len(prefix)

            out_start = out_pos
            output_parts.append(replacement)
            out_pos += len(replacement)

            output_entities.append(
                {
                    "label": occ.label,
                    "start": occ.start,
                    "end": occ.end,
                    "text": occ.text,
                    "group_id": gid,
                    "replacement": replacement,
                    "output_start": out_start,
                    "output_end": out_pos,
                }
            )

            cursor = occ.end

        output_parts.append(cleaned_text[cursor:])
        output_text = "".join(output_parts)

        group_list = list(groups.values())
        group_list.sort(key=lambda g: (int(g.get("first_start", 0)), str(g.get("label", ""))))
        for g in group_list:
            g.pop("first_start", None)
            label = str(g.get("label", ""))
            g["can_randomize"] = label in {"PER", "LOC", "DATE", "PHONE", "AGE"}

        return {
            "input_text": cleaned_text,
            "output_text": output_text,
            "entities": output_entities,
            "groups": group_list,
            "date_shift_days": int(date_shift_days),
        }
