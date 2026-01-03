# anonymize_constants.py
"""
Constants, patterns, and data structures for the anonymize service.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dateutil import parser


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


# fmt: off
COUNTRIES_GERMAN = [
    "Afghanistan", "Ägypten", "Albanien", "Algerien", "Andorra", "Angola",
    "Antigua und Barbuda", "Äquatorialguinea", "Argentinien", "Armenien",
    "Aserbaidschan", "Äthiopien", "Australien", "Bahamas", "Bahrain",
    "Bangladesch", "Barbados", "Belarus", "Belgien", "Belize", "Benin",
    "Bhutan", "Bolivien", "Bosnien und Herzegowina", "Botswana", "Brasilien",
    "Brunei", "Bulgarien", "Burkina Faso", "Burundi", "Chile", "China",
    "Cookinseln", "Costa Rica", "Dänemark", "Deutschland", "Dominica",
    "Dominikanische Republik", "Dschibuti", "Ecuador", "El Salvador",
    "Elfenbeinküste", "Eritrea", "Estland", "Eswatini", "Fidschi", "Finnland",
    "Frankreich", "Gabun", "Gambia", "Georgien", "Ghana", "Grenada",
    "Griechenland", "Großbritannien", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Indien", "Indonesien", "Irak", "Iran",
    "Irland", "Island", "Israel", "Italien", "Jamaika", "Japan", "Jemen",
    "Jordanien", "Kambodscha", "Kamerun", "Kanada", "Kap Verde", "Kasachstan",
    "Katar", "Kenia", "Kirgisistan", "Kiribati", "Kolumbien", "Komoren",
    "Kongo", "Kroatien", "Kuba", "Kuwait", "Laos", "Lesotho", "Lettland",
    "Libanon", "Liberia", "Libyen", "Liechtenstein", "Litauen", "Luxemburg",
    "Madagaskar", "Malawi", "Malaysia", "Malediven", "Mali", "Malta",
    "Marokko", "Marshallinseln", "Mauretanien", "Mauritius", "Mexiko",
    "Mikronesien", "Moldawien", "Monaco", "Mongolei", "Montenegro",
    "Mosambik", "Myanmar", "Namibia", "Nauru", "Nepal", "Neuseeland",
    "Nicaragua", "Niger", "Nigeria", "Nordkorea", "Nordmazedonien",
    "Norwegen", "Oman", "Österreich", "Pakistan", "Palau", "Panama",
    "Papua-Neuguinea", "Paraguay", "Peru", "Philippinen", "Polen", "Portugal",
    "Ruanda", "Rumänien", "Russland", "Salomonen", "Sambia", "Samoa",
    "San Marino", "São Tomé und Príncipe", "Saudi-Arabien", "Schweden",
    "Senegal", "Serbien", "Seychellen", "Sierra Leone", "Simbabwe",
    "Singapur", "Slowakei", "Slowenien", "Somalia", "Spanien", "Sri Lanka",
    "St. Kitts und Nevis", "St. Lucia", "St. Vincent und die Grenadinen",
    "Südafrika", "Sudan", "Südsudan", "Suriname", "Syrien", "Tadschikistan",
    "Tansania", "Thailand", "Timor-Leste", "Togo", "Tonga",
    "Trinidad und Tobago", "Tschad", "Tschechien", "Tunesien", "Türkei",
    "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "Ungarn", "Uruguay",
    "Usbekistan", "Vanuatu", "Vatikanstadt", "Venezuela",
    "Vereinigte Arabische Emirate", "Vietnam", "Zentralafrikanische Republik",
    "Zypern",
]
# fmt: on

GERMAN_MONTHS_FULL = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]

GERMAN_MONTHS_ABBR = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

_GERMAN_MONTH_TOKENS = (
    {m.lower() for m in GERMAN_MONTHS_FULL}
    | {m.lower() for m in GERMAN_MONTHS_ABBR}
    | {"sept"}
)


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


# LLM Configuration
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
- DATE: auch ungenaue Datumsangaben wie Monate ("März", "August") und Jahreszahlen ("2020").
- AGE: numerische Altersangaben (z.B. "3", "15", "42") wenn klar als Alter gemeint.
- Markiere KEINE Pronomen oder generische Rollen ohne Identifikatoren (z.B. "mein Sohn"), keine Krankheiten/Symptome, keine allgemeinen Orte wie "Kindergarten" ohne konkreten Namen.
- Markiere keine Inhalte, die nicht im Originaltext stehen."""
