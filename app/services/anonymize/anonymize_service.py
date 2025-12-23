from __future__ import annotations

import json
import logging
import os
import pickle
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from dateutil import parser

from llm.openai_utils import extract_message_text
from services.anonymize.pseudonymize_db import PseudonymizeDBHandler


class GermanParserInfo(parser.parserinfo):
    WEEKDAYS = [
        ("Mo.", "Montag"),
        ("Di.", "Dienstag"),
        ("Mi.", "Mittwoch"),
        ("Do.", "Donnerstag"),
        ("Fr.", "Freitag"),
        ("Sa.", "Samstag"),
        ("So.", "Sonntag"),
    ]
    MONTHS = [
        ("Jan", "Januar"),
        ("Feb", "Februar"),
        ("Mär", "März"),
        ("Apr", "April"),
        ("Mai", "Mai"),
        ("Jun", "Juni"),
        ("Jul", "Juli"),
        ("Aug", "August"),
        ("Sep", "Sept", "September"),
        ("Okt", "Oktober"),
        ("Nov", "November"),
        ("Dec", "Dezember"),
    ]


COUNTRIES_GERMAN = [
    "Afghanistan",
    "Ägypten",
    "Albanien",
    "Algerien",
    "Andorra",
    "Angola",
    "Antigua und Barbuda",
    "Äquatorialguinea",
    "Argentinien",
    "Armenien",
    "Aserbaidschan",
    "Äthiopien",
    "Australien",
    "Bahamas",
    "Bahrain",
    "Bangladesch",
    "Barbados",
    "Belarus",
    "Belgien",
    "Belize",
    "Benin",
    "Bhutan",
    "Bolivien",
    "Bosnien und Herzegowina",
    "Botswana",
    "Brasilien",
    "Brunei",
    "Bulgarien",
    "Burkina Faso",
    "Burundi",
    "Chile",
    "China",
    "Cookinseln",
    "Costa Rica",
    "Dänemark",
    "Deutschland",
    "Dominica",
    "Dominikanische Republik",
    "Dschibuti",
    "Ecuador",
    "El Salvador",
    "Elfenbeinküste",
    "Eritrea",
    "Estland",
    "Eswatini",
    "Fidschi",
    "Finnland",
    "Frankreich",
    "Gabun",
    "Gambia",
    "Georgien",
    "Ghana",
    "Grenada",
    "Griechenland",
    "Großbritannien",
    "Guatemala",
    "Guinea",
    "Guinea-Bissau",
    "Guyana",
    "Haiti",
    "Honduras",
    "Indien",
    "Indonesien",
    "Irak",
    "Iran",
    "Irland",
    "Island",
    "Israel",
    "Italien",
    "Jamaika",
    "Japan",
    "Jemen",
    "Jordanien",
    "Kambodscha",
    "Kamerun",
    "Kanada",
    "Kap Verde",
    "Kasachstan",
    "Katar",
    "Kenia",
    "Kirgisistan",
    "Kiribati",
    "Kolumbien",
    "Komoren",
    "Kongo",
    "Kroatien",
    "Kuba",
    "Kuwait",
    "Laos",
    "Lesotho",
    "Lettland",
    "Libanon",
    "Liberia",
    "Libyen",
    "Liechtenstein",
    "Litauen",
    "Luxemburg",
    "Madagaskar",
    "Malawi",
    "Malaysia",
    "Malediven",
    "Mali",
    "Malta",
    "Marokko",
    "Marshallinseln",
    "Mauretanien",
    "Mauritius",
    "Mexiko",
    "Mikronesien",
    "Moldawien",
    "Monaco",
    "Mongolei",
    "Montenegro",
    "Mosambik",
    "Myanmar",
    "Namibia",
    "Nauru",
    "Nepal",
    "Neuseeland",
    "Nicaragua",
    "Niger",
    "Nigeria",
    "Nordkorea",
    "Nordmazedonien",
    "Norwegen",
    "Oman",
    "Österreich",
    "Pakistan",
    "Palau",
    "Panama",
    "Papua-Neuguinea",
    "Paraguay",
    "Peru",
    "Philippinen",
    "Polen",
    "Portugal",
    "Ruanda",
    "Rumänien",
    "Russland",
    "Salomonen",
    "Sambia",
    "Samoa",
    "San Marino",
    "São Tomé und Príncipe",
    "Saudi-Arabien",
    "Schweden",
    "Senegal",
    "Serbien",
    "Seychellen",
    "Sierra Leone",
    "Simbabwe",
    "Singapur",
    "Slowakei",
    "Slowenien",
    "Somalia",
    "Spanien",
    "Sri Lanka",
    "St. Kitts und Nevis",
    "St. Lucia",
    "St. Vincent und die Grenadinen",
    "Südafrika",
    "Sudan",
    "Südsudan",
    "Suriname",
    "Syrien",
    "Tadschikistan",
    "Tansania",
    "Thailand",
    "Timor-Leste",
    "Togo",
    "Tonga",
    "Trinidad und Tobago",
    "Tschad",
    "Tschechien",
    "Tunesien",
    "Türkei",
    "Turkmenistan",
    "Tuvalu",
    "Uganda",
    "Ukraine",
    "Ungarn",
    "Uruguay",
    "Usbekistan",
    "Vanuatu",
    "Vatikanstadt",
    "Venezuela",
    "Vereinigte Arabische Emirate",
    "Vietnam",
    "Zentralafrikanische Republik",
    "Zypern",
]

logger = logging.getLogger(__name__)

GERMAN_MONTHS_FULL = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]

GERMAN_MONTHS_ABBR = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

_GERMAN_MONTH_TOKENS = {m.lower() for m in GERMAN_MONTHS_FULL} | {m.lower() for m in GERMAN_MONTHS_ABBR} | {
    "sept",
}


DATE_PATTERNS: list[str] = [
    r"(\d{1,2}(\.?)\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s\d{4})",
    r"(\d{1,2}(\.?)\s(Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?\s\d{4})",
    r"(\d{1,2}(\.?)\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s\d{2}\D)",
    r"(\d{1,2}(\.?)\s(Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?\s\d{2}\D)",
    r"(\d{1,2}\.\d{1,2}\.\d{4})",
    r"(\d{1,2}\.\d{1,2}\.\d{2}(\s|\,|\.|\:)\D)",
    r"(\d{1,2}(\.?)\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)(\s|\,|\.|\:)\D)",
    r"(\d{1,2}(\.?)\s(Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)(\s|\,|\.|\:)\D)",
    r"(\s\d{1,2}\.\d{1,2}(\s|\,|\.|\:)\D)",
    r"(\D{2}\s(Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\s\d{4})",
    r"(\D{2}\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s\d{4})",
    r"(\D{2}\s(Jan|Feb|Mär|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\s\d{2}\D)",
    r"(\D{2}\s(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember)\s\d{2}\D)",
]

MAIL_PATTERN = re.compile(r"[\w\.]+@[\w-]+\.+[\w-]{2,6}")
AHV_PATTERN = re.compile(r"756\.\d{4}\.\d{4}\.\d{2}")
PLZ_PATTERN = re.compile(r"\d{4}")

PHONE_PATTERNS = [
    re.compile(r"(?<!\d)\d{3}\s\d{3}\s\d{2}\s\d{2}(?!\d)"),
    re.compile(r"(?<!\d)\d{10}(?!\d)"),
    re.compile(r"\+\d{2}\s\d{2}\s\d{3}\s\d{2}\s\d{2}"),
    re.compile(r"\+\d{11}"),
]


ENTITY_PRIORITY = {
    "MAIL": 0,
    "AHV": 1,
    "PHONE": 2,
    "PLZ": 3,
    "DATE": 4,
    "AGE": 4,
    "PER": 5,
    "LOC": 6,
    "ORG": 10,
    "MISC": 11,
}


@dataclass(frozen=True)
class EntityOccurrence:
    label: str
    start: int
    end: int
    text: str

    @property
    def length(self) -> int:
        return max(0, self.end - self.start)

    def overlaps(self, other: "EntityOccurrence") -> bool:
        return self.start < other.end and other.start < self.end


def _get_resource_base_dir() -> Path:
    # /app/services/anonymize -> /app
    return Path(__file__).resolve().parents[2]


class AnonymizeService:
    DATE_OUTPUT_FORMAT = "%d.%m.%Y"
    DEFAULT_LLM_MODEL = None

    LLM_ALLOWED_LABELS = {"PER", "LOC", "ORG", "DATE", "AGE", "PHONE", "MAIL", "AHV", "PLZ"}
    LLM_LABEL_ALIASES = {
        "PERSON": "PER",
        "NAME": "PER",
        "LOCATION": "LOC",
        "PLACE": "LOC",
        "ORGANISATION": "ORG",
        "ORGANIZATION": "ORG",
        "EMAIL": "MAIL",
        "E-MAIL": "MAIL",
        "ZIP": "PLZ",
        "POSTAL_CODE": "PLZ",
        "POSTCODE": "PLZ",
        "SSN": "AHV",
    }

    LLM_DETECTION_PROMPT = """Du bist ein Tool zur Erkennung von personenbezogenen Daten (PII) und relevanten Quasi-Identifikatoren in deutschen Texten.
Ziel: Pseudonymisierung/Anonymisierung durch spätere regelbasierte Ersetzung.

Antworte AUSSCHLIESSLICH mit gültigem JSON (kein Markdown, kein Fließtext).

JSON-Format:
{
  "entities": [
    {
      "label": "PER|LOC|ORG|DATE|AGE|PHONE|MAIL|AHV|PLZ",
      "start": 0,
      "end": 0,
      "text": "exakter Original-Substring"
    }
  ]
}

Regeln:
- start/end sind 0-basierte Zeichenindizes im ORIGINALTEXT (Python slicing).
- text MUSS exakt ORIGINALTEXT[start:end] entsprechen.
- Ein Objekt pro VORKOMMEN (auch wenn sich der gleiche Text wiederholt).
- DATE: auch ungenaue Datumsangaben wie Monate (\"März\", \"August\") und Jahreszahlen (\"2020\").
- AGE: numerische Altersangaben (z.B. \"3\", \"15\", \"42\") wenn klar als Alter gemeint.
- Markiere KEINE Pronomen oder generische Rollen ohne Identifikatoren (z.B. \"mein Sohn\"), keine Krankheiten/Symptome, keine allgemeinen Orte wie \"Kindergarten\" ohne konkreten Namen.
- Markiere keine Inhalte, die nicht im Originaltext stehen."""

    @staticmethod
    def _paths() -> dict[str, Path]:
        base = _get_resource_base_dir()
        model_dir = Path(os.environ.get("ANONYMIZE_MODEL_DIR", str(base / "models" / "anonymize")))
        data_dir = Path(os.environ.get("ANONYMIZE_DATA_DIR", str(base / "data" / "anonymize")))

        ner_dir = model_dir / "ner-german-large"
        ner_model_file = (
            ner_dir
            / "6b8de9edd73722050be2547acf64c037b2df833c6e8f0e88934de08385e26c1e.4b0797effcc6ebb1889d5d29784b97f0a099c1569b319d87d7c387e44e2bba48"
        )

        recommender_dir = model_dir / "recommender_system"
        return {
            "base": base,
            "model_dir": model_dir,
            "data_dir": data_dir,
            "db": data_dir / "pseudonymize.db",
            "ner_dir": ner_dir,
            "ner_model": ner_model_file,
            "recommender": recommender_dir / "MuncipalityRecommender.sav",
            "scaler": recommender_dir / "Scaler.sav",
        }

    @staticmethod
    def quick_status() -> dict[str, Any]:
        paths = AnonymizeService._paths()
        file_checks = {
            "db": paths["db"].exists(),
            "ner_model": paths["ner_model"].exists(),
            "recommender": paths["recommender"].exists(),
            "scaler": paths["scaler"].exists(),
        }
        return {"ready": all(file_checks.values()), "files": file_checks}

    @staticmethod
    def llm_quick_status() -> dict[str, Any]:
        litellm_key = os.environ.get("LITELLM_API_KEY") or ""
        litellm_base_url = os.environ.get("LITELLM_BASE_URL") or ""
        openai_key = os.environ.get("OPENAI_API_KEY") or ""

        default_model_id = None
        try:
            from db.models.llm_model import LLMModel
            default_model_id = LLMModel.get_default_model_id(model_type=LLMModel.MODEL_TYPE_LLM)
        except Exception:
            default_model_id = None

        if litellm_key.strip():
            return {
                "ready": bool(litellm_base_url.strip()),
                "provider": "litellm",
                "base_url": litellm_base_url.strip() or None,
                "default_model": default_model_id,
            }

        return {
            "ready": bool(openai_key.strip()),
            "provider": "openai" if openai_key.strip() else None,
            "default_model": default_model_id,
        }

    @staticmethod
    def _resolve_llm_model_id(model: Optional[str] = None) -> str:
        from db.models.llm_model import LLMModel

        if model:
            model_id = str(model).strip()
            db_model = LLMModel.get_by_model_id(model_id)
            if not db_model or not db_model.is_active or db_model.model_type != LLMModel.MODEL_TYPE_LLM:
                raise RuntimeError(f"LLM model '{model_id}' is not available in llm_models")
            return db_model.model_id

        default_model = LLMModel.get_default_model(model_type=LLMModel.MODEL_TYPE_LLM)
        if not default_model:
            raise RuntimeError("No default LLM model configured in llm_models")
        return default_model.model_id

    @staticmethod
    @lru_cache(maxsize=1)
    def _llm_client():
        from openai import OpenAI

        litellm_key = os.environ.get("LITELLM_API_KEY") or ""
        litellm_base_url = os.environ.get("LITELLM_BASE_URL") or ""
        if litellm_key.strip():
            if not litellm_base_url.strip():
                raise RuntimeError("LITELLM_BASE_URL is not configured")
            return OpenAI(api_key=litellm_key, base_url=litellm_base_url)

        openai_key = os.environ.get("OPENAI_API_KEY") or ""
        if not openai_key.strip():
            raise RuntimeError("Neither LITELLM_API_KEY nor OPENAI_API_KEY is configured")
        return OpenAI(api_key=openai_key)

    @staticmethod
    def _parse_llm_json(response_text: str) -> dict[str, Any]:
        raw = (response_text or "").strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
        return json.loads(raw)

    @staticmethod
    def _normalize_llm_label(label: str) -> Optional[str]:
        if not isinstance(label, str):
            return None
        key = label.strip().upper()
        key = AnonymizeService.LLM_LABEL_ALIASES.get(key, key)
        return key if key in AnonymizeService.LLM_ALLOWED_LABELS else None

    @staticmethod
    def _resolve_llm_span(
        text: str,
        start: Any,
        end: Any,
        span_text: Optional[str],
    ) -> Optional[tuple[int, int]]:
        if isinstance(start, int) and isinstance(end, int) and 0 <= start < end <= len(text):
            if span_text is None or text[start:end] == span_text:
                return start, end

        if isinstance(span_text, str) and span_text:
            matches = [m.start() for m in re.finditer(re.escape(span_text), text)]
            if len(matches) == 1:
                s = int(matches[0])
                return s, s + len(span_text)
        return None

    @staticmethod
    def _find_llm_entities(text: str, model: Optional[str] = None, max_entities: int = 250) -> list[EntityOccurrence]:
        status = AnonymizeService.llm_quick_status()
        if not status.get("ready"):
            raise RuntimeError("LLM is not configured (missing API key/base URL)")

        client = AnonymizeService._llm_client()
        model_id = AnonymizeService._resolve_llm_model_id(model)

        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": AnonymizeService.LLM_DETECTION_PROMPT},
                {"role": "user", "content": f"ORIGINALTEXT:\n{text}"},
            ],
            temperature=0.0,
            max_tokens=2000,
        )

        response_text = extract_message_text(response.choices[0].message).strip() if response.choices else ""
        if not response_text:
            return []

        try:
            parsed = AnonymizeService._parse_llm_json(response_text)
        except Exception as e:
            logger.warning(f"[Anonymize/LLM] Failed to parse JSON: {e}")
            return []

        entities = parsed.get("entities") if isinstance(parsed, dict) else None
        if not isinstance(entities, list):
            return []

        occurrences: list[EntityOccurrence] = []
        seen: set[tuple[str, int, int]] = set()

        for item in entities[:max_entities]:
            if not isinstance(item, dict):
                continue

            label = AnonymizeService._normalize_llm_label(item.get("label"))
            if not label:
                continue

            resolved = AnonymizeService._resolve_llm_span(
                text=text,
                start=item.get("start"),
                end=item.get("end"),
                span_text=item.get("text") if isinstance(item.get("text"), str) else None,
            )
            if resolved is None:
                continue
            start, end = resolved

            key = (label, start, end)
            if key in seen:
                continue
            seen.add(key)

            occurrences.append(EntityOccurrence(label=label, start=start, end=end, text=text[start:end]))

        return occurrences

    @staticmethod
    def _format_shifted_month(original: str, shifted_dt: datetime) -> Optional[str]:
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

    @staticmethod
    def _randomize_age(original_age: int) -> int:
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

    @staticmethod
    def _generate_age(original: str, age_map: dict[str, str], force_new: bool = False) -> str:
        key = str(original or "").strip()
        if key == "":
            return "▓▓"
        if not force_new and key in age_map:
            return age_map[key]

        if re.fullmatch(r"\d{1,3}", key):
            new_age = AnonymizeService._randomize_age(int(key))
            age_map[key] = str(new_age)
            return age_map[key]

        age_map[key] = "▓▓"
        return age_map[key]

    @staticmethod
    @lru_cache(maxsize=1)
    def _db() -> PseudonymizeDBHandler:
        paths = AnonymizeService._paths()
        return PseudonymizeDBHandler(paths["db"])

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_recommender() -> tuple[Any, Any]:
        paths = AnonymizeService._paths()
        with open(paths["recommender"], "rb") as f:
            recommender = pickle.load(f)
        with open(paths["scaler"], "rb") as f:
            scaler = pickle.load(f)
        return recommender, scaler

    @staticmethod
    @lru_cache(maxsize=1)
    def _load_ner_tagger():
        try:
            import torch
            import flair
            from flair.models import SequenceTagger
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Flair is not installed - install 'flair' in backend requirements."
            ) from e

        flair.device = torch.device("cpu")
        paths = AnonymizeService._paths()
        return SequenceTagger.load(str(paths["ner_model"]))

    @staticmethod
    def health_check() -> dict[str, Any]:
        paths = AnonymizeService._paths()

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
            tagger = AnonymizeService._load_ner_tagger()
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
    def _find_mail(text: str) -> list[EntityOccurrence]:
        return [
            EntityOccurrence(label="MAIL", start=m.start(), end=m.end(), text=m.group(0))
            for m in MAIL_PATTERN.finditer(text)
        ]

    @staticmethod
    def _find_ahv(text: str) -> list[EntityOccurrence]:
        return [
            EntityOccurrence(label="AHV", start=m.start(), end=m.end(), text=m.group(0))
            for m in AHV_PATTERN.finditer(text)
        ]

    @staticmethod
    def _find_phones(text: str) -> list[EntityOccurrence]:
        found: list[EntityOccurrence] = []
        for pattern in PHONE_PATTERNS:
            for m in pattern.finditer(text):
                found.append(EntityOccurrence(label="PHONE", start=m.start(), end=m.end(), text=m.group(0)))
        return found

    @staticmethod
    def _find_plz(text: str) -> list[EntityOccurrence]:
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

    @staticmethod
    def _find_dates(text: str) -> list[tuple[Optional[datetime], EntityOccurrence]]:
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

    @staticmethod
    def _find_flair_ner(text: str) -> list[EntityOccurrence]:
        tagger = AnonymizeService._load_ner_tagger()
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

    @staticmethod
    def _find_plz_from_loc(text: str, ner_entities: list[EntityOccurrence]) -> list[EntityOccurrence]:
        found: list[EntityOccurrence] = []
        for ent in ner_entities:
            if ent.label != "LOC":
                continue
            if ent.start >= 5 and text[ent.start - 5:ent.start - 1].isdigit() and text[ent.start - 1].isspace():
                start = ent.start - 5
                end = ent.start - 1
                found.append(EntityOccurrence(label="PLZ", start=start, end=end, text=text[start:end]))
        return found

    @staticmethod
    def _select_entities(candidates: list[EntityOccurrence]) -> list[EntityOccurrence]:
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

    @staticmethod
    def _generate_phone() -> str:
        return f"07{random.randint(7, 9)} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"

    @staticmethod
    def _generate_person(
        db: PseudonymizeDBHandler,
        old_fullname: str,
        name_origin: str,
        name_count: int,
        name_part_map: dict[str, str],
        force_new: bool = False,
    ) -> str:
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

    @staticmethod
    def _generate_location(
        db: PseudonymizeDBHandler,
        old_location: str,
        recommend: bool,
        recommender_model: Any,
        scaler: Any,
    ) -> tuple[str, bool]:
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

        candidates: list[EntityOccurrence] = []
        candidates.extend(AnonymizeService._find_mail(cleaned_text))
        candidates.extend(AnonymizeService._find_ahv(cleaned_text))
        candidates.extend(AnonymizeService._find_phones(cleaned_text))
        candidates.extend(AnonymizeService._find_plz(cleaned_text))

        parsed_dates = AnonymizeService._find_dates(cleaned_text)
        candidates.extend([occ for _, occ in parsed_dates])

        llm_entities: list[EntityOccurrence] = []
        if engine in {"llm", "hybrid"}:
            llm_entities = AnonymizeService._find_llm_entities(cleaned_text, model=llm_model)
            candidates.extend(llm_entities)
            candidates.extend(AnonymizeService._find_plz_from_loc(cleaned_text, llm_entities))

        ner_entities: list[EntityOccurrence] = []
        if engine in {"offline", "hybrid"}:
            ner_entities = AnonymizeService._find_flair_ner(cleaned_text)
            candidates.extend(ner_entities)
            candidates.extend(AnonymizeService._find_plz_from_loc(cleaned_text, ner_entities))

        entities = AnonymizeService._select_entities(candidates)

        # Group by label + exact original string
        groups: dict[str, dict[str, Any]] = {}
        occurrences: list[dict[str, Any]] = []

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

        # Helper to produce group id
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
                        replacement = AnonymizeService._generate_person(
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
                            replacement_loc, db_hit = AnonymizeService._generate_location(
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
                        # Randomize single date without changing document-wide shift
                        delta = random.randint(-5 * 356, -1)
                        dt = date_by_span.get(
                            (int(g["first_start"]), int(g["first_start"]) + len(original))
                        )
                        replacement = AnonymizeService._shift_date_string(
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
                            replacement = AnonymizeService._shift_date_string(
                                original,
                                delta_days=int(date_shift_days),
                                delta_years=date_shift_years,
                                parsed_dt=dt,
                            )
                            date_map[gid] = replacement
                        replacement = date_map[gid]
                        mode = "auto"
                elif label == "AGE":
                    replacement = AnonymizeService._generate_age(
                        original=original,
                        age_map=age_map,
                        force_new=should_randomize,
                    )
                    mode = "random" if should_randomize else "auto"
                elif label == "PHONE":
                    replacement = AnonymizeService._generate_phone() if should_randomize else "▓▓▓ ▓▓▓ ▓▓ ▓▓"
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
                continue  # safety - should not happen after overlap filtering

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

    @staticmethod
    def _shift_date_string(
        original: str,
        delta_days: int,
        delta_years: int,
        parsed_dt: Optional[datetime],
    ) -> str:
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
            month_only = AnonymizeService._format_shifted_month(original=s, shifted_dt=shifted)
            if month_only is not None:
                return month_only
            return shifted.strftime(AnonymizeService.DATE_OUTPUT_FORMAT)
        except Exception:
            return "▓" * 10
