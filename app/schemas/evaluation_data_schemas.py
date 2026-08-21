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
from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    # LLARS-specific subclass of COMPARISON for counselling-context
    # message comparisons. Same A/B mechanics as comparison; adds a
    # "send" framing (the rater picks the response that would be sent
    # to the client) plus an optional response-prompt textarea so
    # raters can briefly note why they chose it.
    COMMUNICATION_COMPARISON = "communication_comparison"  # function_type_id = 8
    # LLARS-specific variant of LABELING for sequential in-context coding.
    # One item is a whole conversation; one VOTE is a single span inside it,
    # labeled in reading order with the conversation history in view. Reuses
    # the labeling label set, co-pilot and parts machinery — the difference is
    # the unit of decision, which is why the vote tables carry a span_id.
    CONVERSATION_LABELING = "conversation_labeling"  # function_type_id = 9

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
            8: cls.COMMUNICATION_COMPARISON,
            9: cls.CONVERSATION_LABELING,
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
            self.COMMUNICATION_COMPARISON: 8,
            self.CONVERSATION_LABELING: 9,
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


class Span(BaseModel):
    """Eine labelbare Einheit innerhalb einer Nachricht.

    ``start``/``end`` sind Zeichen-Offsets in ``Message.content`` und sind die
    Wahrheit — der Nachrichtentext wird EINMAL gespeichert, Spans referenzieren
    ihn nur. Bei 8.307 Spans über 86 Gespräche ist das der Unterschied zwischen
    ~1 MB und ~100 MB.

    ``text`` darf der Import mitliefern (bequem für Debugging und Export), ist
    aber redundant; der Server validiert es gegen die Offsets und verlässt sich
    im Zweifel auf ``content[start:end]``.

    ``span_id`` ist ein STABILER String aus dem Import (z. B.
    ``gemco_A/1/m2/s003``), keine laufende DB-ID: nur so ist ein Re-Import
    idempotent und sind Exporte aus zwei Zeitpunkten joinbar.
    """

    span_id: str = Field(..., min_length=1, max_length=64)
    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("end")
    @classmethod
    def _end_after_start(cls, v: int, info) -> int:
        start = info.data.get("start")
        if start is not None and v <= start:
            raise ValueError(f"span end ({v}) must be greater than start ({start})")
        return v


class LabelableMessage(Message):
    """Nachricht in einem Konversationslabeling-Item.

    ``labelable=False`` heißt „nur Kontext" (z. B. die Nachrichten der
    Ratsuchenden) — solche Nachrichten tragen keine Spans und erzeugen keine
    Entscheidungen.
    """

    message_id: Optional[Union[int, str]] = None
    labelable: bool = False
    spans: List[Span] = Field(default_factory=list)

    @field_validator("spans")
    @classmethod
    def _spans_unique_and_ordered(cls, v: List[Span]) -> List[Span]:
        ids = [s.span_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("span_id must be unique within a message")
        return v


class ConversationLabelingContent(BaseModel):
    """Item-Inhalt für den Konversationslabeling-Typ (function_type 9).

    Ein Item = ein ganzes Gespräch. Gelabelt werden die Spans der als
    ``labelable`` markierten Nachrichten, in Lesereihenfolge.
    """

    type: str = "conversation_labeling"
    messages: List[LabelableMessage]

    @field_validator("messages")
    @classmethod
    def _validate_spans_against_text(
        cls, v: List[LabelableMessage]
    ) -> List[LabelableMessage]:
        seen: set = set()
        for msg in v:
            if msg.spans and not msg.labelable:
                raise ValueError(
                    "messages carrying spans must be marked labelable=true"
                )
            for span in msg.spans:
                if span.span_id in seen:
                    raise ValueError(
                        f"duplicate span_id '{span.span_id}' within the item"
                    )
                seen.add(span.span_id)
                # Offsets must actually address the stored text, otherwise the
                # UI would highlight the wrong words and the export would carry
                # a span that cannot be reproduced from the message.
                if span.end > len(msg.content):
                    raise ValueError(
                        f"span '{span.span_id}' ends at {span.end} but the "
                        f"message is only {len(msg.content)} characters long"
                    )
                if span.text is not None:
                    actual = msg.content[span.start:span.end]
                    if span.text != actual:
                        raise ValueError(
                            f"span '{span.span_id}' text does not match the "
                            f"message at [{span.start}:{span.end}]"
                        )
        if not seen:
            raise ValueError("a conversation_labeling item needs at least one span")
        return v


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

    # ``item_header_template`` is the per-item header rendered above the
    # content being rated, with ``{{variable}}`` substitution from
    # ``EvaluationItem.metadata_json`` (same mechanism as ComparisonConfig).
    # Templates accept LocalizedString so DE and EN can coexist on the same
    # scenario. Historically only comparison types honoured this field; the
    # v1 REST API silently dropped it for rating configs because the field
    # was absent here (no ``extra='forbid'`` on the domain models).
    item_header_template: Optional[LocalizedString] = None


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

    # Eric (commit 6f2acd61): markdown-based briefing layer.
    # ``task_description_markdown`` is the long-form briefing shown to
    # the rater (replaces the short ``question`` as the prominent
    # heading on the comparison page when set). ``criteria_markdown``
    # is the bullet-list-shaped criteria block, replacing the flat
    # ``criteria`` array for clients that want bold/italics/structure.
    # ``item_header_template`` is the per-item header rendered above
    # the conversation context with ``{{variable}}`` substitution from
    # ``EvaluationItem.metadata_json``. Templates accept LocalizedString
    # so DE and EN versions can coexist on the same scenario.
    task_description_markdown: Optional[LocalizedString] = None
    criteria_markdown: Optional[LocalizedString] = None
    item_header_template: Optional[LocalizedString] = None

    # Gamification-Reward-System (Turing-Test-Studie):
    # Nach `gamification_first_milestone` Comparisons öffnet ein Popup mit
    # dem Präferenz-Profil; danach alle `gamification_recurring_milestone`
    # Comparisons erneut. Die Milestone-Karte wird im UI eingerahmt, bevor
    # der User klickt.
    gamification_enabled: bool = False
    gamification_first_milestone: int = 10
    gamification_recurring_milestone: int = 5

    # Progressive-Reveal-Modus (default off):
    # Statt allen 80 Karten auf einmal sieht der/die Bewerter:in nur die
    # ersten `gamification_first_milestone` Karten. Nach jedem Reward
    # werden die nächsten `gamification_recurring_milestone` Karten
    # entsperrt. Reduziert die wahrgenommene Last und macht den Reward
    # spürbar — Karten "kommen frei" statt nur visuell hervorgehoben zu
    # werden. Hängt von `gamification_enabled=True` ab.
    progressive_reveal: bool = False


class CommunicationComparisonConfig(ComparisonConfig):
    """
    Specialisation of ``ComparisonConfig`` for counselling-style message
    comparisons. Same A/B mechanics; adds two pieces of UX:

    1. The rater is framed as "sending" the response they pick to the
       client — the frontend renders a brief fly-out / fade animation
       on the chosen option to reinforce the consequence of the click.
       Purely visual; the persisted vote is identical to comparison.

    2. Optional ``response_prompt`` field, rendered as a single-line
       hint below the conversation context (e.g. "How would *you*
       respond here?"). Falls through to a sensible default when not
       configured.

    3. Optional ``rater_note_enabled`` to display a free-text textarea
       under the prompt so raters can leave a one-line reason for
       their choice. Persisted on the comparison evaluation row's
       ``metadata`` blob.
    """

    response_prompt: Optional[LocalizedString] = None
    rater_note_enabled: bool = True
    rater_note_placeholder: Optional[LocalizedString] = None


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


class CopilotPromptVersion(BaseModel):
    """Snapshot einer Prompt-Version des Labeling-Co-Piloten (Audit-Trail)."""
    version: int
    prompt: str
    codebook: Optional[str] = None
    updated_at: Optional[str] = None


class CopilotConfig(BaseModel):
    """Labeling-Co-Pilot: LLM-Vorschläge als Pre-Annotation pro Item.

    Der Prompt gehört zur Szenario-Konfiguration und wird szenario-eigen
    versioniert: LabelingCopilotService bumpt prompt_version und appended
    prompt_history, wenn sich prompt/codebook inhaltlich ändern. So bleibt
    die Zuordnung Item→Prompt-Version im Log erhalten (Studien-Anforderung).

    hidden_control_*: verdecktes Kontrollsubset für Anchoring-Analysen.
    Die Sichtbarkeit wird deterministisch pro (scenario, user, item) aus dem
    Salt gehasht und AUSSCHLIESSLICH serverseitig entschieden — der Client
    erfährt nie, ob ein Item Kontrollitem ist (sieht nur "kein Vorschlag").
    """
    # model_id kollidiert mit Pydantics geschütztem "model_"-Namespace
    model_config = ConfigDict(protected_namespaces=())

    enabled: bool = False
    model_id: Optional[str] = None
    # Template mit Platzhaltern {item}, {context}, {labels}, {codebook}
    prompt: Optional[str] = None
    codebook: Optional[str] = None
    prompt_version: int = 1
    prompt_history: List[CopilotPromptVersion] = Field(default_factory=list)
    top_k: int = Field(default=1, ge=1, le=2)  # Top-1 oder Top-2, gerankt
    hidden_control_ratio: float = Field(default=0.0, ge=0.0, le=0.5)
    hidden_control_salt: Optional[str] = None


class PartConfig(BaseModel):
    """Ein Teil (Phase) eines Labeling-Szenarios.

    Kanonisch gespeichert werden INTERNE EvaluationItem-IDs (int) in item_ids.
    Bei der Erstellung sind zwei Zuordnungsformen erlaubt, die der Server
    sofort auflöst (ScenarioPartsService):
    - size: "die nächsten N Items in Upload-Reihenfolge" (Wizard-Grenzen);
      der letzte Teil darf size UND item_ids weglassen (= Rest)
    - item_ids mit externen String-IDs (v1-API, Items im selben Request),
      Auflösung über den chat_id-Hash

    Solange kein Teil aufgelöste item_ids hat, ist die Parts-Config
    "unresolved" und verhält sich wie enabled=false (zweistufiger
    Wizard-Flow: Szenario zuerst, Item-Import danach).
    """
    id: Optional[str] = None  # server-generiert (p1..pn) wenn nicht gesetzt
    name: Optional[str] = None
    # sequential = item_ids-Reihenfolge, für ALLE Rater identisch;
    # random = deterministischer Per-User-Shuffle (Seed aus scenario/user/part)
    order: str = Field(default="sequential", pattern="^(sequential|random)$")
    # Teil-Override unter dem Master-Schalter copilot.enabled
    copilot: bool = False
    # Gesperrte Teile werden Assessoren nicht ausgeliefert (Studien-Gate)
    locked: bool = False
    item_ids: List[Union[int, str]] = Field(default_factory=list)
    size: Optional[int] = Field(default=None, ge=1)


class PartsConfig(BaseModel):
    """Optionale Gliederung eines Labeling-Szenarios in geordnete Teile.

    Teil-Reihenfolge = Listen-Reihenfolge; die Session konkateniert die
    offenen Teile in dieser Reihenfolge. Partition-Invariante (jedes
    Szenario-Item in genau einem Teil) wird kontextabhängig im
    ScenarioPartsService validiert, nicht hier (braucht die Item-Liste).
    Siehe .claude/plans/scenario-parts-design.md.
    """
    enabled: bool = False
    list: List[PartConfig] = Field(default_factory=list)

    @field_validator("list")
    @classmethod
    def _validate_parts(cls, parts: List[PartConfig]) -> List[PartConfig]:
        # Duplikat-IDs früh ablehnen (Export/Metrics/API adressieren über id)
        seen = set()
        for part in parts:
            if part.id:
                if part.id in seen:
                    raise ValueError(f"duplicate part id '{part.id}'")
                seen.add(part.id)
        # Höchstens ein Teil ohne Zuordnungs-Spec (weder item_ids noch size),
        # und nur als LETZTER (= Rest-Teil) — sonst wäre die Zuordnung ambig.
        for idx, part in enumerate(parts):
            if not part.item_ids and part.size is None and idx != len(parts) - 1:
                raise ValueError(
                    f"part {idx + 1} has neither item_ids nor size; "
                    "only the last part may omit both (rest)"
                )
        return parts


class LabelingConfig(BaseModel):
    """Konfiguration für Labeling/Kategorisierung."""
    mode: LabelingMode  # "single" oder "multi"
    labels: List[LabelOption]
    allow_other: bool = False
    min_labels: Optional[int] = None  # Nur bei multi
    max_labels: Optional[int] = None  # Nur bei multi
    copilot: Optional[CopilotConfig] = None
    # Optionale Teile/Phasen (Kalibrierungs-Studien); None = keine Teile
    parts: Optional[PartsConfig] = None


class ConversationLabelingConfig(LabelingConfig):
    """Konfiguration für Konversationslabeling (function_type 9).

    Erbt das komplette Labeling-Setup (Labelset, Co-Pilot, Teile) und ergänzt
    nur, wie viel Gesprächskontext sichtbar ist. Alle drei Felder sind bewusst
    Optionen und keine festen Annahmen: es sind offene Studienentscheidungen
    (vrm-corpus, offene-entscheidungen 2c), und als Option gebaut kostet die
    Entscheidung später keinen Code.

    Wichtig: Sichtbarkeit muss für Mensch UND Co-Pilot identisch sein — der
    serverseitig gebaute ``{context}`` folgt denselben Feldern.
    """

    # Wie viele vorangehende Nachrichten voll sichtbar sind; ältere werden
    # zusammengeklappt. Kappen statt ganzen Thread: die Dialogue-Act-Literatur
    # zeigt, dass die Gewinne aus wenigen vorangehenden Turns kommen, und es
    # spart Lesezeit, Speicher und Co-Pilot-Tokens.
    context_window: int = Field(3, ge=0, le=50)

    # Sichtbarkeit der noch nicht bearbeiteten Spans DERSELBEN Nachricht.
    future_spans: str = Field("dimmed", pattern="^(visible|dimmed|hidden)$")

    # Spätere Nachrichten nie zeigen (PsyDefDetect-Konvention: Kontext bis
    # einschließlich Zielspan, keine Zukunft). Hält die Ressource
    # shared-task-anschlussfähig.
    no_future_messages: bool = True


# =============================================================================
# Union aller Config-Typen
# =============================================================================

EvaluationConfig = Union[
    SimpleRankingConfig,
    MultiGroupRankingConfig,
    RatingConfig,
    MailRatingConfig,
    ComparisonConfig,
    CommunicationComparisonConfig,
    AuthenticityConfig,
    # ConversationLabelingConfig MUST precede LabelingConfig: it is a subclass,
    # and a left-to-right Union would otherwise let the parent swallow it and
    # silently drop context_window / future_spans / no_future_messages.
    ConversationLabelingConfig,
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
