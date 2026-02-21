"""
Unified Evaluation Data Schemas.

SCHEMA GROUND TRUTH - DIESE DATEI IST DIE ZENTRALE REFERENZ!
============================================================

Diese Schemas definieren das einheitliche Datenformat für alle Evaluationstypen
in LLARS. Sie dienen als zentrale Ground Truth und werden von Backend und
Frontend referenziert.

UNTERSCHIED zu evaluation_schemas.py:
- evaluation_schemas.py: Schemas für LLM-OUTPUT (strukturierte Antworten)
- evaluation_data_schemas.py: Schemas für EVALUATION-INPUT (Daten zum Bewerten)

ALLE Module die Evaluation-Daten verarbeiten MÜSSEN diese Schemas nutzen:
- Batch Generation: app/services/generation/batch_generation_service.py
- Output Export: app/services/generation/output_export_service.py
- Scenario Manager: app/routes/scenarios/
- Schema API: app/routes/scenarios/scenario_schema_api.py
- Frontend: llars-frontend/src/schemas/evaluationSchemas.js

TERMINOLOGIE:
- Item (EvaluationItem): Eltern-Entität, gruppiert zusammengehörige Features
  (z.B. ein E-Mail-Thread, ein Quelltext).
- Feature: Eine generierte Alternative/Antwort FÜR ein Item (z.B. eine Zusammenfassung).
  Jedes Feature wird in genau EINEN Bucket einsortiert. Das Feature ist die
  UNIT OF ANALYSIS für Ranking-IRR ("Bucket-Krippendorff").
  Buckets: gut(3) > mittel(2) > neutral(1) > schlecht(0) - ordinal.

WICHTIGE KONVENTIONEN:
- Item.id: Technische ID (z.B. "item_1") - NIEMALS LLM-Namen!
- Item.label: UI-Anzeigename (generische Labels)
- Item.source: Herkunft mit type (human/llm/unknown)

Dokumentation: .claude/plans/evaluation-data-schemas.md

Schema-Version: 1.0
Datum: 2026-01-27
"""

from enum import Enum
from typing import Optional, Union, List, Dict, Any
from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================

class SchemaVersion(str, Enum):
    """Unterstützte Schema-Versionen."""
    V1_0 = "1.0"


class EvaluationType(str, Enum):
    """Evaluationstypen entsprechend function_type_id."""
    RANKING = "ranking"           # function_type_id = 1
    RATING = "rating"             # function_type_id = 2
    MAIL_RATING = "mail_rating"   # function_type_id = 3
    COMPARISON = "comparison"     # function_type_id = 4
    AUTHENTICITY = "authenticity" # function_type_id = 5
    LABELING = "labeling"         # function_type_id = 7

    @classmethod
    def from_function_type_id(cls, type_id: int) -> "EvaluationType":
        """Konvertiert function_type_id zu EvaluationType."""
        mapping = {
            1: cls.RANKING,
            2: cls.RATING,
            3: cls.MAIL_RATING,
            4: cls.COMPARISON,
            5: cls.AUTHENTICITY,
            7: cls.LABELING,
        }
        if type_id not in mapping:
            raise ValueError(f"Unknown function_type_id: {type_id}")
        return mapping[type_id]

    def to_function_type_id(self) -> int:
        """Konvertiert EvaluationType zu function_type_id."""
        mapping = {
            self.RANKING: 1,
            self.RATING: 2,
            self.MAIL_RATING: 3,
            self.COMPARISON: 4,
            self.AUTHENTICITY: 5,
            self.LABELING: 7,
        }
        return mapping[self]


class SourceType(str, Enum):
    """Herkunft eines Items."""
    HUMAN = "human"
    LLM = "llm"
    UNKNOWN = "unknown"


class ContentType(str, Enum):
    """Inhaltstyp für Reference und Item."""
    TEXT = "text"
    CONVERSATION = "conversation"


class RankingMode(str, Enum):
    """Ranking-Modi."""
    SIMPLE = "simple"
    MULTI_GROUP = "multi_group"


class LabelingMode(str, Enum):
    """Labeling-Modi."""
    SINGLE = "single"
    MULTI = "multi"


# =============================================================================
# Basis-Strukturen
# =============================================================================

class LocalizedString(BaseModel):
    """Mehrsprachiger String (DE/EN)."""
    de: str
    en: str

    model_config = {"frozen": True}


class Source(BaseModel):
    """Herkunft eines Items (Mensch, LLM, Unbekannt)."""
    type: SourceType
    name: Optional[str] = None  # Bei LLM: "mistralai/Mistral-Small-3.2"
    metadata: Optional[Dict[str, Any]] = None


class Message(BaseModel):
    """Eine Nachricht in einer Konversation."""
    role: str  # "Klient", "Berater", "User", "Assistant"
    content: str
    timestamp: Optional[str] = None  # ISO 8601
    metadata: Optional[Dict[str, Any]] = None


class ConversationContent(BaseModel):
    """Konversations-Inhalt mit mehreren Messages."""
    type: str = "conversation"
    messages: List[Message]


class Reference(BaseModel):
    """
    Referenz/Kontext für die Evaluation.

    Wird typischerweise auf der rechten Seite des Interfaces angezeigt
    (z.B. Original-Artikel, Kundenanfrage, etc.).
    """
    type: ContentType
    label: str  # UI-Anzeigename: "Original-Artikel", "Beratungsverlauf"
    content: Union[str, List[Message]]  # Text oder Messages
    metadata: Optional[Dict[str, Any]] = None


class Item(BaseModel):
    """
    Ein zu bewertendes Item.

    Wird typischerweise auf der linken Seite des Interfaces angezeigt
    (z.B. Zusammenfassungen zum Ranken, Antworten zum Bewerten).
    """
    id: str  # Technische ID: "item_1", "item_2" (NIEMALS LLM-Namen!)
    label: str  # UI-Anzeigename: "Zusammenfassung 1", "Antwort A"
    source: Source
    content: Union[str, ConversationContent]
    group: Optional[str] = None  # Für Multi-Group Ranking


class GroundTruth(BaseModel):
    """
    Ground Truth für supervised evaluation.

    WICHTIG: Meist nicht vorhanden! Bei Ranking ist die Bucket-Zuordnung
    typischerweise subjektiv und es gibt keine "richtige" Antwort.
    """
    value: Union[str, int, float, List[str], Dict[str, str]]
    source: Optional[Source] = None
    confidence: Optional[float] = Field(None, ge=0, le=1)


# =============================================================================
# Ranking-Konfiguration
# =============================================================================

class Bucket(BaseModel):
    """Ein Bucket für Ranking."""
    id: str  # "good", "moderate", "poor"
    label: LocalizedString  # {"de": "Gut", "en": "Good"}
    color: str  # "#98d4bb"
    order: int  # Sortierreihenfolge (1 = beste Qualität)


class RankingGroup(BaseModel):
    """
    Gruppen-Definition für Multi-Group Ranking.

    Jede Gruppe erscheint als Tab im Interface und hat eigene Buckets.
    """
    id: str  # "summaries", "comments"
    label: LocalizedString  # Tab-Name im Frontend
    description: Optional[LocalizedString] = None  # Tooltip
    buckets: List[Bucket]
    allow_ties: bool = True


class SimpleRankingConfig(BaseModel):
    """Konfiguration für einfaches Ranking (eine Gruppe)."""
    mode: RankingMode = RankingMode.SIMPLE
    buckets: List[Bucket]
    allow_ties: bool = True
    require_complete: bool = True


class MultiGroupRankingConfig(BaseModel):
    """Konfiguration für Multi-Group Ranking (mehrere Tabs)."""
    mode: RankingMode = RankingMode.MULTI_GROUP
    groups: List[RankingGroup]
    require_complete: bool = True


RankingConfig = Union[SimpleRankingConfig, MultiGroupRankingConfig]


# =============================================================================
# Rating-Konfiguration
# =============================================================================

class Scale(BaseModel):
    """Bewertungsskala für Rating."""
    min: int = 1
    max: int = 5
    step: int = 1
    labels: Optional[Dict[str, LocalizedString]] = None  # "1": {"de": "Sehr schlecht", ...}


class Dimension(BaseModel):
    """Eine Bewertungsdimension (z.B. Kohärenz, Flüssigkeit)."""
    id: str  # "coherence", "fluency"
    label: LocalizedString
    description: Optional[LocalizedString] = None
    weight: float = Field(default=0.25, ge=0, le=1)


class RatingConfig(BaseModel):
    """Konfiguration für Multi-Dimensional Rating."""
    scale: Scale
    dimensions: List[Dimension]
    show_overall: bool = True


class MailRatingConfig(RatingConfig):
    """Konfiguration für Mail Rating (LLARS-spezifisch)."""
    focus_role: Optional[str] = None  # Welche Rolle wird bewertet? "Berater"


# =============================================================================
# Comparison-Konfiguration
# =============================================================================

class ComparisonConfig(BaseModel):
    """Konfiguration für paarweisen Vergleich (A vs B)."""
    question: LocalizedString  # "Welche Antwort ist besser?"
    criteria: Optional[List[str]] = None  # Worauf achten?
    allow_tie: bool = True
    show_source: bool = False  # LLM-Namen anzeigen?


# =============================================================================
# Authenticity-Konfiguration
# =============================================================================

class AuthenticityOption(BaseModel):
    """Eine Option für Authenticity (Echt/Fake)."""
    id: str  # "human", "ai"
    label: LocalizedString


class AuthenticityConfig(BaseModel):
    """Konfiguration für Authenticity-Bewertung."""
    options: List[AuthenticityOption]
    show_confidence: bool = True


# =============================================================================
# Labeling-Konfiguration
# =============================================================================

class LabelOption(BaseModel):
    """Eine Label-Option für Kategorisierung."""
    id: str  # "politics", "economy"
    label: LocalizedString
    description: Optional[LocalizedString] = None
    color: Optional[str] = None


class LabelingConfig(BaseModel):
    """Konfiguration für Labeling/Kategorisierung."""
    mode: LabelingMode  # "single" oder "multi"
    labels: List[LabelOption]
    allow_other: bool = False
    min_labels: Optional[int] = None  # Nur bei multi
    max_labels: Optional[int] = None  # Nur bei multi


# =============================================================================
# Union aller Config-Typen
# =============================================================================

EvaluationConfig = Union[
    SimpleRankingConfig,
    MultiGroupRankingConfig,
    RatingConfig,
    MailRatingConfig,
    ComparisonConfig,
    AuthenticityConfig,
    LabelingConfig
]


# =============================================================================
# Haupt-Schema
# =============================================================================

class EvaluationData(BaseModel):
    """
    Haupt-Schema für Evaluation-Daten.

    Dieses Schema definiert das einheitliche Format für alle Evaluationstypen.
    Es wird von der API geliefert und vom Frontend konsumiert.

    Beispiel:
        {
            "schema_version": "1.0",
            "type": "ranking",
            "reference": {
                "type": "text",
                "label": "Original-Artikel",
                "content": "..."
            },
            "items": [
                {"id": "item_1", "label": "Zusammenfassung 1", ...}
            ],
            "config": {
                "mode": "simple",
                "buckets": [...]
            }
        }
    """
    schema_version: SchemaVersion = SchemaVersion.V1_0
    type: EvaluationType
    reference: Optional[Reference] = None
    items: List[Item]
    config: EvaluationConfig
    ground_truth: Optional[GroundTruth] = None

    model_config = {"use_enum_values": True}


# =============================================================================
# Factory-Funktionen
# =============================================================================

def create_default_ranking_buckets() -> List[Bucket]:
    """Erstellt Standard-Buckets für Ranking."""
    return [
        Bucket(
            id="good",
            label=LocalizedString(de="Gut", en="Good"),
            color="#98d4bb",
            order=1
        ),
        Bucket(
            id="moderate",
            label=LocalizedString(de="Moderat", en="Moderate"),
            color="#D1BC8A",
            order=2
        ),
        Bucket(
            id="poor",
            label=LocalizedString(de="Schlecht", en="Poor"),
            color="#e8a087",
            order=3
        )
    ]


def create_default_rating_dimensions() -> List[Dimension]:
    """Erstellt Standard-Dimensionen für Rating (SummEval-Style)."""
    return [
        Dimension(
            id="coherence",
            label=LocalizedString(de="Kohärenz", en="Coherence"),
            description=LocalizedString(
                de="Logischer Aufbau und Zusammenhang",
                en="Logical structure and connection"
            ),
            weight=0.25
        ),
        Dimension(
            id="fluency",
            label=LocalizedString(de="Flüssigkeit", en="Fluency"),
            description=LocalizedString(
                de="Grammatik und Lesbarkeit",
                en="Grammar and readability"
            ),
            weight=0.25
        ),
        Dimension(
            id="relevance",
            label=LocalizedString(de="Relevanz", en="Relevance"),
            description=LocalizedString(
                de="Wichtige Informationen erfasst",
                en="Important information captured"
            ),
            weight=0.25
        ),
        Dimension(
            id="consistency",
            label=LocalizedString(de="Konsistenz", en="Consistency"),
            description=LocalizedString(
                de="Faktentreue zum Original",
                en="Factual accuracy to source"
            ),
            weight=0.25
        )
    ]


def create_default_scale() -> Scale:
    """Erstellt Standard-Skala (1-5)."""
    return Scale(
        min=1,
        max=5,
        step=1,
        labels={
            "1": LocalizedString(de="Sehr schlecht", en="Very poor"),
            "2": LocalizedString(de="Schlecht", en="Poor"),
            "3": LocalizedString(de="Akzeptabel", en="Acceptable"),
            "4": LocalizedString(de="Gut", en="Good"),
            "5": LocalizedString(de="Sehr gut", en="Very good")
        }
    )


def create_simple_ranking_config(
    buckets: Optional[List[Bucket]] = None,
    allow_ties: bool = True,
    require_complete: bool = True
) -> SimpleRankingConfig:
    """Erstellt eine einfache Ranking-Konfiguration."""
    return SimpleRankingConfig(
        mode=RankingMode.SIMPLE,
        buckets=buckets or create_default_ranking_buckets(),
        allow_ties=allow_ties,
        require_complete=require_complete
    )


def create_rating_config(
    dimensions: Optional[List[Dimension]] = None,
    scale: Optional[Scale] = None,
    show_overall: bool = True
) -> RatingConfig:
    """Erstellt eine Rating-Konfiguration."""
    return RatingConfig(
        scale=scale or create_default_scale(),
        dimensions=dimensions or create_default_rating_dimensions(),
        show_overall=show_overall
    )
