# anonymize_generators.py
"""
Replacement generators for the anonymize service.
"""

from __future__ import annotations

import random
import re
from datetime import datetime, timedelta
from typing import Any, Optional

from dateutil import parser

from .anonymize_constants import (
    GermanParserInfo,
    COUNTRIES_GERMAN,
    GERMAN_MONTHS_FULL,
    GERMAN_MONTHS_ABBR,
    _GERMAN_MONTH_TOKENS,
)
from services.anonymize.pseudonymize_db import PseudonymizeDBHandler


DATE_OUTPUT_FORMAT = "%d.%m.%Y"


def _format_shifted_month(original: str, shifted_dt: datetime) -> Optional[str]:
    """Format a shifted month, preserving abbreviation style."""
    token = (original or "").strip()
    if token == "":
        return None

    raw = token.rstrip(".").strip()
    if raw.lower() not in _GERMAN_MONTH_TOKENS:
        return None

    month_idx = int(shifted_dt.month) - 1
    abbr = len(raw) <= 4
    out = GERMAN_MONTHS_ABBR[month_idx] if abbr else GERMAN_MONTHS_FULL[month_idx]
    if token.endswith("."):
        out += "."
    if token and token[0].islower():
        out = out.lower()
    return out


def _randomize_age(original_age: int) -> int:
    """Randomize an age value within valid bounds."""
    n = int(original_age)

    if n < 18:
        lower, upper = 0, 17
    else:
        lower, upper = 18, 110

    for _ in range(6):
        delta = random.choice([-2, -1, 1, 2])
        candidate = max(lower, min(upper, n + delta))
        if candidate != n:
            return candidate

    # Fallback: ensure a change even at boundaries
    return lower if n != lower else min(upper, lower + 1)


def generate_age(original: str, age_map: dict[str, str], force_new: bool = False) -> str:
    """Generate a randomized age replacement."""
    key = str(original or "").strip()
    if key == "":
        return "▓▓"
    if not force_new and key in age_map:
        return age_map[key]

    if re.fullmatch(r"\d{1,3}", key):
        new_age = _randomize_age(int(key))
        age_map[key] = str(new_age)
        return age_map[key]

    age_map[key] = "▓▓"
    return age_map[key]


def generate_phone() -> str:
    """Generate a random Swiss phone number."""
    return f"07{random.randint(7, 9)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"


def generate_person(
    db: PseudonymizeDBHandler,
    old_fullname: str,
    name_origin: str,
    name_count: int,
    name_part_map: dict[str, str],
    force_new: bool = False,
) -> str:
    """Generate a pseudonymized person name."""
    parts = [p for p in old_fullname.split() if p]
    if not parts:
        return "▓" * 10

    if len(parts) == 1:
        old = parts[0]
        if force_new or old not in name_part_map:
            name_part_map[old] = db.get_random_firstname_or_lastname(name_origin, name_count, old)
        return name_part_map[old]

    new_parts: list[str] = []
    for idx, old_part in enumerate(parts):
        if not force_new and old_part in name_part_map:
            new_parts.append(name_part_map[old_part])
            continue

        if idx < len(parts) - 1:
            new = db.get_random_firstname(name_origin, name_count, parts[0])
        else:
            new = db.get_random_lastname(name_origin)
        name_part_map[old_part] = new
        new_parts.append(new)

    return " ".join(new_parts)


def generate_location(
    db: PseudonymizeDBHandler,
    old_location: str,
    recommend: bool,
    recommender_model: Any,
    scaler: Any,
) -> tuple[str, bool]:
    """Generate a pseudonymized location."""
    original = old_location.strip()
    if not original:
        return "▓" * 10, False

    normalized = original
    if normalized and normalized[0].isdigit() and len(normalized) >= 5:
        normalized = normalized[5:].strip()

    is_country = normalized in COUNTRIES_GERMAN

    muncipality = db.get_muncipality_features(normalized)
    if muncipality is not None:
        if recommend:
            try:
                import warnings
                import numpy as np

                vector = np.array([muncipality.to_feature_vector()], dtype=float)
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message=r"X does not have valid feature names.*",
                        category=UserWarning,
                    )
                    vector_scaled = scaler.transform(vector)
                    neighbors = recommender_model.kneighbors(
                        vector_scaled, return_distance=False
                    )
                idxs = [int(i) + 1 for i in list(neighbors[0])]
                candidate_ids = idxs[1:] if len(idxs) > 1 else idxs
                return db.get_random_muncipality_by_index(candidate_ids), True
            except Exception:
                return db.get_random_muncipality(), True
        return db.get_random_muncipality(), True

    if db.is_in_district_db(normalized):
        return db.get_random_district(), True
    if db.is_in_canton_db(normalized):
        return db.get_random_canton(), True
    if is_country:
        alternatives = [c for c in COUNTRIES_GERMAN if c != normalized]
        pool = alternatives or COUNTRIES_GERMAN
        return random.choice(pool), True

    return "▓" * 10, False


def shift_date_string(
    original: str,
    delta_days: int,
    delta_years: int,
    parsed_dt: Optional[datetime],
) -> str:
    """Shift a date string by the specified delta."""
    s = (original or "").strip()
    if s.isnumeric() and len(s) in (2, 4):
        try:
            return str(int(s) + int(delta_years))
        except Exception:
            return "▓" * 10

    try:
        dt = parsed_dt or parser.parse(
            s,
            fuzzy_with_tokens=True,
            parserinfo=GermanParserInfo(),
        )[0]
    except Exception:
        return "▓" * 10

    try:
        shifted = dt + timedelta(days=int(delta_days))
        month_only = _format_shifted_month(original=s, shifted_dt=shifted)
        if month_only is not None:
            return month_only
        return shifted.strftime(DATE_OUTPUT_FORMAT)
    except Exception:
        return "▓" * 10
