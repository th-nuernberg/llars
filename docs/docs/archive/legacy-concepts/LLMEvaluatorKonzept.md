# LLM-as-Evaluator: Technisches Konzept

**Version:** 1.0 | **Stand:** 14. Januar 2026
**Fokus:** Constrained Decoding, Transparenz, anpassbare Prompts

---

## 1. Übersicht: Szenario-Typen und ihre Datenformate

### 1.1 Aktuelle Evaluation-Typen

| Typ | Menschliche Eingabe | LLM-Ausgabe | Transparenz-Bedarf |
|-----|---------------------|-------------|-------------------|
| **Ranking** | Drag&Drop in 4 Buckets | `{"gut": [...], "mittel": [...], ...}` | Bucket-Zuordnung + Reasoning |
| **Rating** | 1-5 Sterne pro Feature | `{"ratings": [{"feature_id": X, "rating": Y}]}` | Score + Reasoning pro Feature |
| **Authenticity** | real/fake Button + Confidence | `{"vote": "real", "confidence": 3}` | Vote + Confidence + Reasoning |
| **Mail Rating** | 1-5 Sterne für Thread | `{"rating": 4, "reasoning": "..."}` | Gesamtscore + Reasoning |
| **Comparison** | A/B/Tie Auswahl | `{"winner": "A", "confidence": 4}` | Winner + Reasoning |
| **Text Classification** | Label-Auswahl | `{"label": "X", "confidence": 3}` | Label + Reasoning |

### 1.2 Was fehlt für vollständige Transparenz

| Typ | Aktuell | Benötigt |
|-----|---------|----------|
| Ranking | Nur Bucket-Zuordnung | + Reasoning pro Bucket, + Gesamtbegründung |
| Rating | Nur Scores | + Reasoning pro Feature |
| Authenticity | Vote + Confidence | + Detailliertes Reasoning |
| Mail Rating | Rating + Reasoning | Vollständig |
| Comparison | Winner + Reasoning | + Kriterien-basierte Scores |

---

## 2. Erweiterte Pydantic-Schemas für Constrained Decoding

### 2.1 Base-Schema für alle Evaluation-Typen

```python
# app/schemas/evaluation_schemas.py

from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any
from enum import Enum


class EvaluatorMeta(BaseModel):
    """Metadaten für jede LLM-Evaluation."""
    processing_time_ms: Optional[int] = Field(None, description="Verarbeitungszeit")
    model_version: Optional[str] = Field(None, description="Modellversion")
    prompt_version: Optional[str] = Field(None, description="Prompt-Version für Reproduzierbarkeit")


class BaseEvaluationResult(BaseModel):
    """Basis-Schema für alle Evaluations-Ergebnisse."""
    reasoning: str = Field(
        min_length=20,
        max_length=2000,
        description="Ausführliche Begründung der Entscheidung"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Konfidenz der Bewertung (0=unsicher, 1=sehr sicher)"
    )
    meta: Optional[EvaluatorMeta] = None
```

### 2.2 Ranking-Schema (Erweitert)

```python
class BucketReasoning(BaseModel):
    """Begründung für die Zuordnung zu einem Bucket."""
    feature_ids: List[int] = Field(description="Feature-IDs in diesem Bucket")
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Warum wurden diese Features diesem Bucket zugeordnet?"
    )


class RankingEvaluationResult(BaseEvaluationResult):
    """
    Strukturiertes Ranking-Ergebnis für LLM-Evaluatoren.

    Features werden in 4 Qualitäts-Buckets eingeteilt:
    - gut: Hochwertige Features
    - mittel: Akzeptable Features
    - schlecht: Minderwertige Features
    - neutral: Nicht eindeutig zuordenbar
    """

    buckets: Dict[Literal["gut", "mittel", "schlecht", "neutral"], BucketReasoning] = Field(
        description="Bucket-Zuordnungen mit Begründungen"
    )

    overall_assessment: str = Field(
        min_length=50,
        max_length=500,
        description="Gesamteinschätzung der Feature-Qualität für diesen Thread"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "buckets": {
                    "gut": {
                        "feature_ids": [1, 3],
                        "reasoning": "Diese Features zeigen präzise Analyse und sind gut formuliert."
                    },
                    "mittel": {
                        "feature_ids": [2, 5],
                        "reasoning": "Brauchbar, aber mit Verbesserungspotential."
                    },
                    "schlecht": {
                        "feature_ids": [4],
                        "reasoning": "Oberflächliche Analyse ohne Mehrwert."
                    },
                    "neutral": {
                        "feature_ids": [],
                        "reasoning": "Keine Features in dieser Kategorie."
                    }
                },
                "overall_assessment": "Die Mehrzahl der Features ist von guter Qualität...",
                "reasoning": "Die Bewertung basiert auf Präzision, Relevanz und...",
                "confidence": 0.85
            }
        }
```

### 2.3 Rating-Schema (Erweitert)

```python
class FeatureRating(BaseModel):
    """Bewertung eines einzelnen Features."""
    feature_id: int
    rating: int = Field(ge=1, le=5, description="Bewertung 1-5")
    reasoning: str = Field(
        min_length=10,
        max_length=300,
        description="Begründung für diese Bewertung"
    )
    strengths: Optional[List[str]] = Field(None, description="Stärken des Features")
    weaknesses: Optional[List[str]] = Field(None, description="Schwächen des Features")


class RatingEvaluationResult(BaseEvaluationResult):
    """
    Strukturiertes Rating-Ergebnis für LLM-Evaluatoren.

    Jedes Feature wird auf einer Skala von 1-5 bewertet.
    """

    ratings: List[FeatureRating] = Field(
        description="Bewertungen pro Feature"
    )

    average_rating: float = Field(
        ge=1.0, le=5.0,
        description="Durchschnittliche Bewertung"
    )

    thread_summary: str = Field(
        min_length=30,
        max_length=500,
        description="Zusammenfassung der Konversation als Kontext"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ratings": [
                    {
                        "feature_id": 1,
                        "rating": 4,
                        "reasoning": "Präzise Analyse der Kundenbedürfnisse.",
                        "strengths": ["Klar formuliert", "Relevant"],
                        "weaknesses": ["Könnte detaillierter sein"]
                    }
                ],
                "average_rating": 3.8,
                "thread_summary": "Beratungsgespräch über Kreditantrag...",
                "reasoning": "Die Features zeigen insgesamt gute Qualität...",
                "confidence": 0.8
            }
        }
```

### 2.4 Authenticity-Schema (Erweitert)

```python
class AuthenticityIndicator(BaseModel):
    """Ein einzelner Indikator für Echtheit/Künstlichkeit."""
    indicator: str = Field(description="Beschreibung des Indikators")
    supports: Literal["real", "fake"] = Field(description="Unterstützt welche Hypothese?")
    weight: float = Field(ge=0.0, le=1.0, description="Gewichtung dieses Indikators")


class AuthenticityEvaluationResult(BaseEvaluationResult):
    """
    Strukturiertes Authenticity-Ergebnis für LLM-Evaluatoren.

    Bewertet ob eine Konversation echt (menschlich) oder
    künstlich (KI-generiert) ist.
    """

    vote: Literal["real", "fake"] = Field(
        description="Finale Entscheidung: real oder fake"
    )

    confidence_score: int = Field(
        ge=1, le=5,
        description="Konfidenz 1-5 (für Kompatibilität mit UI)"
    )

    indicators: List[AuthenticityIndicator] = Field(
        min_items=2,
        max_items=10,
        description="Indikatoren die zur Entscheidung geführt haben"
    )

    linguistic_analysis: str = Field(
        min_length=30,
        max_length=500,
        description="Sprachliche Analyse der Konversation"
    )

    behavioral_analysis: str = Field(
        min_length=30,
        max_length=500,
        description="Verhaltensanalyse der Gesprächspartner"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vote": "fake",
                "confidence_score": 4,
                "indicators": [
                    {
                        "indicator": "Unnatürlich konsistenter Sprachstil",
                        "supports": "fake",
                        "weight": 0.8
                    },
                    {
                        "indicator": "Fehlende Tippfehler oder Korrekturen",
                        "supports": "fake",
                        "weight": 0.6
                    }
                ],
                "linguistic_analysis": "Der Text zeigt ungewöhnlich perfekte Grammatik...",
                "behavioral_analysis": "Das Verhalten des Klienten wirkt zu linear...",
                "reasoning": "Mehrere Indikatoren deuten auf KI-Generierung hin...",
                "confidence": 0.75
            }
        }
```

### 2.5 Mail-Rating-Schema (Erweitert)

```python
class QualityCriterion(BaseModel):
    """Bewertung eines Qualitätskriteriums."""
    name: str
    score: int = Field(ge=1, le=5)
    reasoning: str = Field(min_length=10, max_length=200)


class MailRatingEvaluationResult(BaseEvaluationResult):
    """
    Strukturiertes Mail-Rating-Ergebnis für LLM-Evaluatoren.

    Bewertet die Gesamtqualität einer E-Mail-Beratungskonversation.
    """

    overall_rating: int = Field(
        ge=1, le=5,
        description="Gesamtbewertung 1-5"
    )

    criteria: List[QualityCriterion] = Field(
        min_items=3,
        max_items=6,
        description="Bewertung nach einzelnen Kriterien"
    )

    strengths: List[str] = Field(
        min_items=1,
        max_items=5,
        description="Stärken der Beratung"
    )

    areas_for_improvement: List[str] = Field(
        min_items=0,
        max_items=5,
        description="Verbesserungspotential"
    )

    summary: str = Field(
        min_length=50,
        max_length=500,
        description="Zusammenfassende Bewertung"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "overall_rating": 4,
                "criteria": [
                    {"name": "Empathie", "score": 5, "reasoning": "Sehr einfühlsam..."},
                    {"name": "Fachlichkeit", "score": 4, "reasoning": "Kompetent..."},
                    {"name": "Verständlichkeit", "score": 4, "reasoning": "Klar..."},
                    {"name": "Hilfsbereitschaft", "score": 4, "reasoning": "Engagiert..."},
                    {"name": "Lösungsorientierung", "score": 3, "reasoning": "Könnte konkreter..."}
                ],
                "strengths": ["Empathische Kommunikation", "Fachliche Kompetenz"],
                "areas_for_improvement": ["Konkretere Handlungsempfehlungen"],
                "summary": "Eine insgesamt gute Beratung mit Stärken in...",
                "reasoning": "Die Bewertung basiert auf der Analyse von...",
                "confidence": 0.85
            }
        }
```

### 2.6 Text-Classification-Schema (Generisch)

```python
class ClassificationEvaluationResult(BaseEvaluationResult):
    """
    Strukturiertes Classification-Ergebnis für LLM-Evaluatoren.

    Klassifiziert Text in vordefinierte Kategorien.
    """

    label: str = Field(description="Gewähltes Label/Kategorie")

    confidence_score: int = Field(
        ge=1, le=5,
        description="Konfidenz 1-5"
    )

    alternative_labels: List[Dict[str, Any]] = Field(
        default=[],
        description="Alternative Labels mit Wahrscheinlichkeiten"
    )

    key_phrases: List[str] = Field(
        min_items=1,
        max_items=5,
        description="Schlüsselphrasen die zur Klassifikation führten"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "label": "complaint",
                "confidence_score": 4,
                "alternative_labels": [
                    {"label": "inquiry", "probability": 0.2}
                ],
                "key_phrases": ["unzufrieden", "Beschwerde", "inakzeptabel"],
                "reasoning": "Der Text enthält eindeutige Beschwerdemerkmale...",
                "confidence": 0.8
            }
        }
```

---

## 3. Constrained Decoding Implementation

### 3.1 Schema-basierte LLM-Anfrage

```python
# app/services/llm/constrained_llm_service.py

from pydantic import BaseModel
from typing import Type, TypeVar, Optional
import json

T = TypeVar('T', bound=BaseModel)


class ConstrainedLLMService:
    """
    Service für strukturierte LLM-Ausgaben mit Constrained Decoding.

    Unterstützt:
    - OpenAI JSON Mode + Schema-Validierung
    - Anthropic Tool Use für strukturierte Ausgaben
    - vLLM/Outlines für echtes Constrained Decoding (lokal)
    """

    @staticmethod
    def request_structured(
        client,
        model_id: str,
        prompt: str,
        response_schema: Type[T],
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> T:
        """
        Fordert strukturierte Ausgabe vom LLM an.

        Args:
            client: LLM Client (OpenAI, Anthropic, etc.)
            model_id: Modell-ID
            prompt: User-Prompt
            response_schema: Pydantic-Schema für die Antwort
            system_prompt: Optional System-Prompt
            max_retries: Anzahl Wiederholungsversuche

        Returns:
            Validiertes Pydantic-Objekt
        """

        # JSON Schema aus Pydantic extrahieren
        json_schema = response_schema.model_json_schema()

        # Schema in Prompt einbetten
        schema_instruction = f"""
Du MUSST deine Antwort EXAKT im folgenden JSON-Schema formatieren:

```json
{json.dumps(json_schema, indent=2, ensure_ascii=False)}
```

Antworte NUR mit validem JSON. Keine Erklärungen außerhalb des JSON.
"""

        full_system = (system_prompt or "") + "\n\n" + schema_instruction

        for attempt in range(max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": full_system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2000,
                    extra_body={"response_format": {"type": "json_object"}}
                )

                content = response.choices[0].message.content
                parsed = json.loads(content)

                # Pydantic-Validierung
                return response_schema.model_validate(parsed)

            except Exception as e:
                if attempt == max_retries:
                    raise
                # Retry mit Fehler-Feedback
                prompt += f"\n\nFehler bei vorherigem Versuch: {str(e)}. Bitte korrigieren."

        raise ValueError("Konnte keine valide Antwort erhalten")

    @staticmethod
    def get_schema_for_task_type(task_type: str) -> Type[BaseModel]:
        """Gibt das passende Schema für einen Task-Typ zurück."""
        schema_map = {
            "ranking": RankingEvaluationResult,
            "rating": RatingEvaluationResult,
            "labeling": ClassificationEvaluationResult,  # includes authenticity
            "comparison": ComparisonEvaluationResult,
        }
        return schema_map.get(task_type, BaseEvaluationResult)
```

### 3.2 Integration in LLMAITaskRunner

```python
# Erweiterung von llm_ai_task_runner.py

@staticmethod
def _run_ranking_structured(
    model_id: str,
    thread_ids: Iterable[int],
    scenario_id: int,
    prompt_template: Optional[str] = None
) -> None:
    """Ranking mit strukturierter Ausgabe und Constrained Decoding."""

    client = LLMClientFactory.get_client_for_model(model_id)

    for thread_id in thread_ids:
        # ... existing checks ...

        features = Feature.query.filter_by(thread_id=thread_id).all()

        # Prompt aus Template oder Default
        prompt = prompt_template or DEFAULT_RANKING_PROMPT
        prompt = prompt.format(
            features=format_features(features),
            buckets="gut, mittel, schlecht, neutral"
        )

        # Strukturierte Anfrage
        result = ConstrainedLLMService.request_structured(
            client=client,
            model_id=model_id,
            prompt=prompt,
            response_schema=RankingEvaluationResult,
            system_prompt=RANKING_SYSTEM_PROMPT
        )

        # Speichern mit vollem Reasoning
        LLMTaskResult.create_or_update(
            scenario_id=scenario_id,
            thread_id=thread_id,
            model_id=model_id,
            task_type="ranking",
            payload_json=result.model_dump(),
            raw_response=None,  # Nicht mehr nötig - alles im payload
            error=None
        )
```

---

## 4. Anpassbare Prompt-Templates

### 4.1 Prompt-Template-Modell

```python
# app/db/models/prompt_template.py

class PromptTemplate(db.Model):
    """
    Speichert anpassbare Prompt-Templates für LLM-Evaluatoren.
    """
    __tablename__ = 'prompt_templates'

    id = db.Column(db.Integer, primary_key=True)

    # Identifikation
    name = db.Column(db.String(100), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # ranking, rating, etc.
    version = db.Column(db.String(20), default="1.0")

    # Prompts
    system_prompt = db.Column(db.Text, nullable=False)
    user_prompt_template = db.Column(db.Text, nullable=False)

    # Konfiguration
    variables = db.Column(db.JSON, default=list)  # ["features", "thread_content", ...]
    output_schema_version = db.Column(db.String(20), default="1.0")

    # Metadaten
    is_default = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Optional: Scenario-spezifisch
    scenario_id = db.Column(db.Integer, db.ForeignKey('rating_scenarios.id'), nullable=True)
```

### 4.2 Default-Prompt-Templates

```python
# app/services/llm/default_prompts.py

DEFAULT_PROMPTS = {
    "ranking": {
        "system": """Du bist ein erfahrener Evaluator für die Qualitätsbewertung von LLM-generierten Features.

Deine Aufgabe ist es, Features einer E-Mail-Beratungskonversation in Qualitätskategorien einzuordnen.

Bewertungskriterien:
- Präzision: Wie genau beschreibt das Feature einen relevanten Aspekt?
- Relevanz: Wie wichtig ist das Feature für die Beratungsqualität?
- Formulierung: Wie klar und verständlich ist das Feature formuliert?
- Mehrwert: Bietet das Feature neue Erkenntnisse?

Du MUSST deine Antwort im vorgegebenen JSON-Schema formatieren.""",

        "user": """Ordne die folgenden Features den Qualitäts-Buckets zu.

**Buckets:**
- gut: Hochwertige Features (präzise, relevant, gut formuliert)
- mittel: Akzeptable Features (brauchbar, aber verbesserungsfähig)
- schlecht: Minderwertige Features (unpräzise, irrelevant, schlecht formuliert)
- neutral: Nicht eindeutig zuordenbar

**Konversationskontext:**
{thread_content}

**Features zur Bewertung:**
{features}

Begründe jede Bucket-Zuordnung und gib eine Gesamteinschätzung."""
    },

    "rating": {
        "system": """Du bist ein Experte für die Bewertung von Feature-Qualität.

Bewerte jedes Feature auf einer Skala von 1 bis 5:
- 5: Exzellent - Präzise, relevant, wertvoll
- 4: Gut - Überdurchschnittlich, minor Verbesserungspotential
- 3: Durchschnittlich - Akzeptabel, aber mit Schwächen
- 2: Unterdurchschnittlich - Mehrere Probleme
- 1: Mangelhaft - Kaum brauchbar

Begründe jede Bewertung konkret.""",

        "user": """Bewerte die Qualität der folgenden Features.

**Konversation:**
{thread_content}

**Features:**
{features}

Gib für jedes Feature eine Bewertung (1-5) mit Begründung."""
    },

    "authenticity": {
        "system": """Du bist ein Experte für die Erkennung von KI-generierten Texten.

Analysiere Konversationen auf Hinweise für menschliche oder künstliche Erstellung.

Achte auf:
- Sprachliche Natürlichkeit (Tippfehler, Korrekturen, umgangssprachliche Elemente)
- Emotionale Authentizität (Variabilität, Konsistenz mit Situation)
- Verhaltensrealismus (Nachfragen, Themenwechsel, Ablenkungen)
- Konversationsdynamik (Timing, Antwortlängen, Turn-Taking)""",

        "user": """Analysiere die folgende Konversation.

Entscheide:
- "real": Wahrscheinlich von Menschen geschrieben
- "fake": Wahrscheinlich KI-generiert

**Konversation:**
{thread_content}

Begründe deine Entscheidung mit konkreten Indikatoren."""
    },

    "mail_rating": {
        "system": """Du bist ein Experte für die Bewertung von E-Mail-Beratungsqualität.

Bewertungskriterien:
1. Empathie: Einfühlungsvermögen und emotionale Unterstützung
2. Fachlichkeit: Kompetenz und korrektes Wissen
3. Verständlichkeit: Klarheit und Zugänglichkeit der Kommunikation
4. Hilfsbereitschaft: Engagement und Serviceorientierung
5. Lösungsorientierung: Konkrete Handlungsempfehlungen

Gesamtbewertung 1-5:
- 5: Exzellente Beratung
- 4: Gute Beratung
- 3: Akzeptable Beratung
- 2: Verbesserungswürdige Beratung
- 1: Mangelhafte Beratung""",

        "user": """Bewerte die Qualität dieser E-Mail-Beratung.

**Betreff:** {subject}

**Konversation:**
{thread_content}

Gib Scores für jedes Kriterium und eine Gesamtbewertung."""
    }
}
```

### 4.3 Scenario-Level Prompt-Override

```python
# In RatingScenarios.config_json

{
    "function_type_id": 1,
    "llm_evaluators": ["gpt-4o", "claude-3-5-sonnet"],
    "distribution_mode": "round_robin",

    # NEU: Custom Prompts für dieses Szenario
    "prompt_config": {
        "template_id": 42,  # Referenz auf PromptTemplate
        # ODER inline:
        "system_prompt_override": "Du bist ein Berater-Evaluator für Finanzberatungen...",
        "user_prompt_override": null,  # Verwendet Default
        "additional_instructions": "Achte besonders auf regulatorische Compliance."
    }
}
```

---

## 5. Transparenz-Explorer: Darstellung pro Szenario-Typ

### 5.1 ResponseCard-Komponente (Universal)

```vue
<!-- components/Evaluation/ResponseCard.vue -->
<template>
  <v-card class="response-card" :class="{ 'response-card--llm': isLlm }">
    <!-- Header -->
    <div class="response-header">
      <div class="evaluator-info">
        <v-avatar :color="isLlm ? 'accent' : 'primary'" size="36">
          <v-icon v-if="isLlm">mdi-robot</v-icon>
          <span v-else>{{ evaluatorInitial }}</span>
        </v-avatar>
        <div class="evaluator-details">
          <span class="evaluator-name">{{ evaluatorName }}</span>
          <span class="evaluator-type">
            <LTag :variant="isLlm ? 'info' : 'primary'" size="sm">
              {{ isLlm ? 'LLM' : 'Mensch' }}
            </LTag>
          </span>
        </div>
      </div>
      <span class="response-time">{{ formattedTime }}</span>
    </div>

    <!-- Response Content - Dynamic based on type -->
    <div class="response-content">
      <!-- RANKING -->
      <template v-if="taskType === 'ranking'">
        <RankingResponseDisplay :data="responseData" />
      </template>

      <!-- RATING -->
      <template v-else-if="taskType === 'rating'">
        <RatingResponseDisplay :data="responseData" :features="features" />
      </template>

      <!-- AUTHENTICITY -->
      <template v-else-if="taskType === 'authenticity'">
        <AuthenticityResponseDisplay :data="responseData" />
      </template>

      <!-- MAIL RATING -->
      <template v-else-if="taskType === 'mail_rating'">
        <MailRatingResponseDisplay :data="responseData" />
      </template>

      <!-- COMPARISON -->
      <template v-else-if="taskType === 'comparison'">
        <ComparisonResponseDisplay :data="responseData" />
      </template>

      <!-- CLASSIFICATION -->
      <template v-else-if="taskType === 'text_classification'">
        <ClassificationResponseDisplay :data="responseData" />
      </template>
    </div>

    <!-- LLM Reasoning Section (expandable) -->
    <v-expansion-panels v-if="isLlm && hasReasoning" variant="accordion">
      <v-expansion-panel>
        <v-expansion-panel-title>
          <v-icon class="mr-2">mdi-brain</v-icon>
          LLM Reasoning
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <div class="reasoning-content">
            <p>{{ responseData.reasoning }}</p>
          </div>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Confidence Indicator -->
    <div v-if="hasConfidence" class="confidence-bar">
      <span class="confidence-label">Konfidenz:</span>
      <v-progress-linear
        :model-value="confidencePercent"
        :color="confidenceColor"
        height="8"
        rounded
      />
      <span class="confidence-value">{{ confidencePercent }}%</span>
    </div>
  </v-card>
</template>
```

### 5.2 Ranking-Response-Display

```vue
<!-- components/Evaluation/displays/RankingResponseDisplay.vue -->
<template>
  <div class="ranking-display">
    <!-- Bucket-Visualization -->
    <div class="buckets-grid">
      <div
        v-for="(bucket, key) in orderedBuckets"
        :key="key"
        class="bucket"
        :class="`bucket--${key}`"
      >
        <div class="bucket-header">
          <span class="bucket-icon">{{ bucketIcons[key] }}</span>
          <span class="bucket-label">{{ bucketLabels[key] }}</span>
          <span class="bucket-count">{{ bucket.feature_ids?.length || 0 }}</span>
        </div>

        <div class="bucket-features">
          <div
            v-for="featureId in bucket.feature_ids"
            :key="featureId"
            class="feature-chip"
          >
            #{{ featureId }}
          </div>
        </div>

        <!-- Reasoning for this bucket -->
        <div v-if="bucket.reasoning" class="bucket-reasoning">
          <v-icon size="14" class="mr-1">mdi-comment-text</v-icon>
          {{ bucket.reasoning }}
        </div>
      </div>
    </div>

    <!-- Overall Assessment -->
    <div v-if="data.overall_assessment" class="overall-assessment">
      <h4>Gesamteinschätzung</h4>
      <p>{{ data.overall_assessment }}</p>
    </div>
  </div>
</template>

<script setup>
const bucketIcons = {
  gut: '✅',
  mittel: '➖',
  schlecht: '❌',
  neutral: '⚪'
}

const bucketLabels = {
  gut: 'Gut',
  mittel: 'Mittel',
  schlecht: 'Schlecht',
  neutral: 'Neutral'
}
</script>

<style scoped>
.buckets-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.bucket--gut { border-left: 3px solid var(--llars-success); }
.bucket--mittel { border-left: 3px solid var(--llars-warning); }
.bucket--schlecht { border-left: 3px solid var(--llars-danger); }
.bucket--neutral { border-left: 3px solid var(--llars-secondary); }
</style>
```

### 5.3 Authenticity-Response-Display

```vue
<!-- components/Evaluation/displays/AuthenticityResponseDisplay.vue -->
<template>
  <div class="authenticity-display">
    <!-- Vote Display -->
    <div class="vote-display" :class="`vote--${data.vote}`">
      <v-icon size="48">
        {{ data.vote === 'real' ? 'mdi-account-check' : 'mdi-robot-angry' }}
      </v-icon>
      <span class="vote-label">
        {{ data.vote === 'real' ? 'Echt (Mensch)' : 'Fake (KI)' }}
      </span>
    </div>

    <!-- Confidence -->
    <div class="confidence-stars">
      <v-rating
        :model-value="data.confidence_score || data.confidence * 5"
        readonly
        density="compact"
        color="warning"
      />
      <span class="confidence-text">Konfidenz</span>
    </div>

    <!-- Indicators (for LLM) -->
    <div v-if="data.indicators?.length" class="indicators-section">
      <h4>Erkennungsmerkmale</h4>
      <div class="indicators-list">
        <div
          v-for="(indicator, idx) in data.indicators"
          :key="idx"
          class="indicator"
          :class="`indicator--${indicator.supports}`"
        >
          <span class="indicator-text">{{ indicator.indicator }}</span>
          <LTag :variant="indicator.supports === 'real' ? 'success' : 'danger'" size="sm">
            {{ indicator.supports === 'real' ? 'Echt' : 'Fake' }}
          </LTag>
          <span class="indicator-weight">{{ Math.round(indicator.weight * 100) }}%</span>
        </div>
      </div>
    </div>

    <!-- Analysis Sections -->
    <div v-if="data.linguistic_analysis" class="analysis-section">
      <h4>Sprachliche Analyse</h4>
      <p>{{ data.linguistic_analysis }}</p>
    </div>

    <div v-if="data.behavioral_analysis" class="analysis-section">
      <h4>Verhaltensanalyse</h4>
      <p>{{ data.behavioral_analysis }}</p>
    </div>
  </div>
</template>

<style scoped>
.vote--real {
  background: rgba(var(--v-theme-success), 0.1);
  color: rgb(var(--v-theme-success));
}

.vote--fake {
  background: rgba(var(--v-theme-error), 0.1);
  color: rgb(var(--v-theme-error));
}
</style>
```

### 5.4 Agreement-Comparison-View

```vue
<!-- components/Evaluation/AgreementComparisonView.vue -->
<template>
  <div class="agreement-view">
    <h3>Vergleich: Mensch vs. LLM</h3>

    <!-- Agreement Matrix -->
    <div class="agreement-matrix">
      <table>
        <thead>
          <tr>
            <th></th>
            <th v-for="evaluator in evaluators" :key="evaluator.id">
              <span :class="{ 'llm-header': evaluator.is_llm }">
                {{ evaluator.name }}
                <v-icon v-if="evaluator.is_llm" size="14">mdi-robot</v-icon>
              </span>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="evaluator in evaluators" :key="evaluator.id">
            <td class="row-header">{{ evaluator.name }}</td>
            <td
              v-for="other in evaluators"
              :key="other.id"
              :class="getAgreementClass(evaluator.id, other.id)"
            >
              {{ getAgreementScore(evaluator.id, other.id) }}%
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Summary Stats -->
    <div class="summary-stats">
      <div class="stat">
        <span class="stat-label">Mensch-Mensch Agreement</span>
        <span class="stat-value">{{ humanHumanAgreement }}%</span>
      </div>
      <div class="stat">
        <span class="stat-label">LLM-Mensch Agreement</span>
        <span class="stat-value">{{ llmHumanAgreement }}%</span>
      </div>
      <div class="stat">
        <span class="stat-label">LLM-LLM Agreement</span>
        <span class="stat-value">{{ llmLlmAgreement }}%</span>
      </div>
    </div>

    <!-- Disagreement Highlights -->
    <div v-if="disagreements.length" class="disagreements">
      <h4>Auffällige Unterschiede</h4>
      <div v-for="d in disagreements" :key="d.id" class="disagreement-item">
        <span class="disagreement-aspect">{{ d.aspect }}</span>
        <span class="disagreement-detail">{{ d.detail }}</span>
      </div>
    </div>
  </div>
</template>
```

---

## 6. Live-Monitoring für LLM-Evaluatoren

### 6.1 Socket.IO Events (Erweiterung)

```python
# app/socketio_handlers/events_llm_evaluation.py

@socketio.on('scenario:subscribe')
def handle_scenario_subscribe(data):
    """Subscribe to scenario updates."""
    scenario_id = data.get('scenario_id')
    if scenario_id:
        join_room(f'scenario_{scenario_id}')
        emit('scenario:subscribed', {'scenario_id': scenario_id})


def emit_llm_evaluation_started(scenario_id: int, model_id: str, thread_id: int):
    """Emit when LLM starts evaluating a thread."""
    socketio.emit(
        'scenario:llm_started',
        {
            'scenario_id': scenario_id,
            'model_id': model_id,
            'thread_id': thread_id,
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f'scenario_{scenario_id}'
    )


def emit_llm_evaluation_completed(
    scenario_id: int,
    model_id: str,
    thread_id: int,
    result_summary: dict
):
    """Emit when LLM completes evaluating a thread."""
    socketio.emit(
        'scenario:llm_completed',
        {
            'scenario_id': scenario_id,
            'model_id': model_id,
            'thread_id': thread_id,
            'result_summary': result_summary,  # Kurze Zusammenfassung
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f'scenario_{scenario_id}'
    )


def emit_llm_progress(scenario_id: int, model_id: str, progress: dict):
    """Emit LLM progress update."""
    socketio.emit(
        'scenario:llm_progress',
        {
            'scenario_id': scenario_id,
            'model_id': model_id,
            'completed': progress['completed'],
            'total': progress['total'],
            'current_thread': progress.get('current_thread'),
            'avg_time_ms': progress.get('avg_time_ms'),
            'timestamp': datetime.utcnow().isoformat()
        },
        room=f'scenario_{scenario_id}'
    )
```

### 6.2 Integration in LLMAITaskRunner

```python
# Erweiterung der _run_* Methoden

@staticmethod
def _run_ranking_with_events(model_id: str, thread_ids: List[int], scenario_id: int):
    """Ranking mit Live-Events."""
    from socketio_handlers.events_llm_evaluation import (
        emit_llm_evaluation_started,
        emit_llm_evaluation_completed,
        emit_llm_progress
    )

    total = len(thread_ids)
    completed = 0
    start_times = []

    for thread_id in thread_ids:
        # Event: Started
        emit_llm_evaluation_started(scenario_id, model_id, thread_id)

        thread_start = time.time()

        try:
            # ... existing evaluation logic ...
            result = perform_ranking_evaluation(...)

            # Event: Completed
            emit_llm_evaluation_completed(
                scenario_id, model_id, thread_id,
                result_summary={
                    'buckets': {k: len(v) for k, v in result['buckets'].items()},
                    'confidence': result.get('confidence', 0)
                }
            )

        except Exception as e:
            # ... error handling ...
            pass

        # Progress Update
        completed += 1
        elapsed = (time.time() - thread_start) * 1000
        start_times.append(elapsed)

        emit_llm_progress(
            scenario_id, model_id,
            {
                'completed': completed,
                'total': total,
                'current_thread': thread_id,
                'avg_time_ms': sum(start_times) / len(start_times)
            }
        )
```

---

## 7. Datei-Struktur (Neue/Geänderte Dateien)

```
app/
├── schemas/
│   └── evaluation_schemas.py           # NEU: Alle Pydantic-Schemas
├── services/
│   └── llm/
│       ├── llm_ai_task_runner.py       # ERWEITERT: Constrained Decoding
│       ├── constrained_llm_service.py  # NEU: Schema-basierte Anfragen
│       └── default_prompts.py          # NEU: Default Prompt-Templates
├── db/
│   └── models/
│       └── prompt_template.py          # NEU: PromptTemplate Model
├── socketio_handlers/
│   └── events_llm_evaluation.py        # NEU: LLM-spezifische Events

llars-frontend/src/
├── components/
│   └── Evaluation/
│       ├── ResponseCard.vue            # NEU: Universal Response Card
│       ├── AgreementComparisonView.vue # NEU: Agreement-Visualisierung
│       └── displays/
│           ├── RankingResponseDisplay.vue
│           ├── RatingResponseDisplay.vue
│           ├── AuthenticityResponseDisplay.vue
│           ├── MailRatingResponseDisplay.vue
│           ├── ComparisonResponseDisplay.vue
│           └── ClassificationResponseDisplay.vue
└── composables/
    └── useLlmEvaluationStream.js       # NEU: Live-Updates Composable
```

---

## 8. Zusammenfassung

### Was jetzt möglich ist:

| Feature | Vorher | Nachher |
|---------|--------|---------|
| **LLM-Ausgabeformat** | Einfaches JSON | Pydantic-validiert + Reasoning |
| **Prompts** | Hartcodiert | Pro Szenario anpassbar |
| **Live-Monitoring** | Nur Fortschritt | Thread-Level Events |
| **Transparenz** | Nur Ergebnis | Vollständiges Reasoning |
| **Constrained Decoding** | json_object Mode | Schema-Validierung |

### IJCAI Demo Highlights:

1. **LLM-as-Evaluator** arbeitet parallel zu Menschen
2. **Live-Feed** zeigt LLM-Aktivität in Echtzeit
3. **Transparenz**: Jedes LLM-Reasoning sichtbar
4. **Agreement-Analyse**: Mensch vs. LLM Vergleich
5. **Anpassbare Prompts**: Für verschiedene Domänen

---

**Stand:** 14. Januar 2026
