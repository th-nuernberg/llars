# anonymize_entity_detection.py
"""
Entity detection methods using regex patterns and Flair NER.
"""

from __future__ import annotations

import re
from datetime import datetime
from functools import lru_cache
from typing import Optional

from dateutil import parser

from .anonymize_constants import (
    EntityOccurrence,
    GermanParserInfo,
    DATE_PATTERNS,
    MAIL_PATTERN,
    AHV_PATTERN,
    PLZ_PATTERN,
    PLZ_PATTERN_DE,
    SVN_PATTERN,
    AGE_PATTERN,
    IBAN_PATTERN,
    URL_PATTERN,
    TIME_PATTERN,
    STREET_PATTERN,
    PHONE_PATTERNS,
    ENTITY_PRIORITY,
    _get_resource_base_dir,
)


@lru_cache(maxsize=1)
def _load_ner_tagger():
    """Load the Flair NER tagger (cached)."""
    try:
        import torch
        import flair
        from flair.models import SequenceTagger
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "Flair is not installed - install 'flair' in backend requirements."
        ) from e

    flair.device = torch.device("cpu")
    from .anonymize_paths import get_paths
    paths = get_paths()
    return SequenceTagger.load(str(paths["ner_model"]))


def find_mail(text: str) -> list[EntityOccurrence]:
    """Find email addresses in text."""
    return [
        EntityOccurrence(label="MAIL", start=m.start(), end=m.end(), text=m.group(0))
        for m in MAIL_PATTERN.finditer(text)
    ]


def find_ahv(text: str) -> list[EntityOccurrence]:
    """Find Swiss AHV numbers in text."""
    return [
        EntityOccurrence(label="AHV", start=m.start(), end=m.end(), text=m.group(0))
        for m in AHV_PATTERN.finditer(text)
    ]


def find_phones(text: str) -> list[EntityOccurrence]:
    """Find phone numbers in text."""
    found: list[EntityOccurrence] = []
    for pattern in PHONE_PATTERNS:
        for m in pattern.finditer(text):
            found.append(EntityOccurrence(label="PHONE", start=m.start(), end=m.end(), text=m.group(0)))
    return found


def find_plz(text: str) -> list[EntityOccurrence]:
    """Find postal codes near 'PLZ' keyword in text (Swiss 4-digit)."""
    found: list[EntityOccurrence] = []
    for m_plz in re.finditer(r"\bPLZ\b", text, flags=re.IGNORECASE):
        idx = m_plz.start()
        substring_start = max(0, idx - 20)
        substring_end = min(len(text), idx + 20)
        substring = text[substring_start:substring_end]
        for m in PLZ_PATTERN.finditer(substring):
            start = substring_start + m.start()
            end = substring_start + m.end()
            found.append(EntityOccurrence(label="PLZ", start=start, end=end, text=m.group(0)))
    return found


def find_plz_de(text: str) -> list[EntityOccurrence]:
    """Find German postal codes (5-digit) in text."""
    return [
        EntityOccurrence(label="PLZ", start=m.start(), end=m.end(), text=m.group(0))
        for m in PLZ_PATTERN_DE.finditer(text)
    ]


def find_svn(text: str) -> list[EntityOccurrence]:
    """Find German social security numbers (Sozialversicherungsnummer) in text."""
    return [
        EntityOccurrence(label="SVN", start=m.start(), end=m.end(), text=m.group(0))
        for m in SVN_PATTERN.finditer(text)
    ]


def find_age(text: str) -> list[EntityOccurrence]:
    """Find age mentions in text like '(34)' or '34 Jahre'."""
    found: list[EntityOccurrence] = []
    for m in AGE_PATTERN.finditer(text):
        # The pattern has two groups: (34) or 34 Jahre
        age_value = m.group(1) or m.group(2)
        if age_value:
            age_int = int(age_value)
            # Only consider reasonable ages (0-120)
            if 0 <= age_int <= 120:
                found.append(EntityOccurrence(
                    label="AGE",
                    start=m.start(),
                    end=m.end(),
                    text=m.group(0)
                ))
    return found


def find_iban(text: str) -> list[EntityOccurrence]:
    """Find IBAN numbers in text."""
    found: list[EntityOccurrence] = []
    for m in IBAN_PATTERN.finditer(text):
        iban = m.group(0).replace(" ", "")
        # Validate IBAN length (15-34 characters)
        if 15 <= len(iban) <= 34:
            found.append(EntityOccurrence(
                label="IBAN",
                start=m.start(),
                end=m.end(),
                text=m.group(0)
            ))
    return found


def find_url(text: str) -> list[EntityOccurrence]:
    """Find URLs in text."""
    return [
        EntityOccurrence(label="URL", start=m.start(), end=m.end(), text=m.group(0))
        for m in URL_PATTERN.finditer(text)
    ]


def find_time(text: str) -> list[EntityOccurrence]:
    """Find time patterns in text like '14:30' or '14:30 Uhr'."""
    found: list[EntityOccurrence] = []
    for m in TIME_PATTERN.finditer(text):
        time_str = m.group(0)
        # Extract hour and minute
        parts = time_str.split(":")
        if len(parts) >= 2:
            try:
                hour = int(parts[0])
                minute = int(parts[1][:2])  # Take first 2 chars in case of :00 Uhr
                # Validate time range
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    found.append(EntityOccurrence(
                        label="TIME",
                        start=m.start(),
                        end=m.end(),
                        text=time_str
                    ))
            except ValueError:
                pass
    return found


def find_street(text: str) -> list[EntityOccurrence]:
    """Find street addresses in text."""
    return [
        EntityOccurrence(label="STREET", start=m.start(), end=m.end(), text=m.group(0))
        for m in STREET_PATTERN.finditer(text)
    ]


def find_dates(text: str) -> list[tuple[Optional[datetime], EntityOccurrence]]:
    """Find date patterns in text, returning parsed datetime and occurrence."""
    found: list[tuple[Optional[datetime], EntityOccurrence]] = []
    date_spans: list[tuple[int, int]] = []
    years: set[int] = set()

    for idx, pattern in enumerate(DATE_PATTERNS):
        for m in re.finditer(pattern, text):
            raw = m.group(0)
            prefix_trim = 0
            suffix_trim = 0

            if idx in (2, 3):
                suffix_trim = 1
            elif idx in (5, 6, 7):
                suffix_trim = 2
            elif idx in (9, 10):
                prefix_trim = 3
            elif idx in (11, 12):
                prefix_trim = 3
                suffix_trim = 1
            elif idx == 8:
                prefix_trim = 1
                suffix_trim = 2

            date_string = raw[prefix_trim:len(raw) - suffix_trim if suffix_trim else None]
            start = m.start() + prefix_trim
            end = start + len(date_string)

            try:
                parsed = parser.parse(
                    date_string,
                    parserinfo=GermanParserInfo(),
                    default=datetime(day=1, month=1, year=1900),
                )
            except Exception:
                parsed = None

            if parsed is not None and parsed.year != 1900:
                years.add(int(parsed.year))

            occ = EntityOccurrence(label="DATE", start=start, end=end, text=date_string)
            found.append((parsed, occ))
            date_spans.append((occ.start, occ.end))

    # Add standalone years that occur outside already found date spans
    for year in sorted(years):
        year_str = str(year)
        for m in re.finditer(re.escape(year_str), text):
            s, e = m.start(), m.end()
            if any(s < se and ss < e for ss, se in date_spans):
                continue
            found.append((None, EntityOccurrence(label="DATE", start=s, end=e, text=year_str)))

    # Keep original order in text
    found.sort(key=lambda item: item[1].start)
    return found


def find_flair_ner(text: str) -> list[EntityOccurrence]:
    """Find named entities using Flair NER model."""
    tagger = _load_ner_tagger()
    from flair.data import Sentence

    sentence = Sentence(text)
    tagger.predict(sentence)

    found: list[EntityOccurrence] = []
    for span in sentence.get_spans("ner"):
        label = span.get_label("ner").value
        start = int(span.start_position)
        end = int(span.end_position)

        # Include trailing house number after a LOC
        if label == "LOC":
            tail = text[end:end + 12]
            m = re.match(r"^\s*\d{1,4}[a-zA-Z]?", tail)
            if m:
                end += m.end(0)

        # Trim trailing dot for LOC spans (common in German punctuation)
        if label == "LOC" and end > start and text[end - 1] == ".":
            end -= 1

        if end <= start:
            continue

        entity_text = text[start:end]
        found.append(EntityOccurrence(label=label, start=start, end=end, text=entity_text))

    return found


def find_plz_from_loc(text: str, ner_entities: list[EntityOccurrence]) -> list[EntityOccurrence]:
    """Find postal codes that appear before LOC entities."""
    found: list[EntityOccurrence] = []
    for ent in ner_entities:
        if ent.label != "LOC":
            continue
        if ent.start >= 5 and text[ent.start - 5:ent.start - 1].isdigit() and text[ent.start - 1].isspace():
            start = ent.start - 5
            end = ent.start - 1
            found.append(EntityOccurrence(label="PLZ", start=start, end=end, text=text[start:end]))
    return found


def select_entities(candidates: list[EntityOccurrence]) -> list[EntityOccurrence]:
    """Select non-overlapping entities based on priority and length."""
    sorted_candidates = sorted(
        candidates,
        key=lambda e: (
            ENTITY_PRIORITY.get(e.label, 100),
            -e.length,
            e.start,
            e.end,
        ),
    )

    selected: list[EntityOccurrence] = []
    for cand in sorted_candidates:
        if cand.length <= 0:
            continue
        if any(cand.overlaps(existing) for existing in selected):
            continue
        selected.append(cand)

    selected.sort(key=lambda e: (e.start, e.end))
    return selected
