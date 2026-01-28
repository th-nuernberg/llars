"""
Field Prompt Service for AI-Assisted Form Fields.

Manages prompt templates for AI field generation.
Provides CRUD operations and default prompt seeding.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from db import db
from db.models import FieldPromptTemplate

logger = logging.getLogger(__name__)


# =============================================================================
# Default Prompts for Common Fields
# =============================================================================

DEFAULT_FIELD_PROMPTS: Dict[str, Dict[str, Any]] = {
    "scenario.settings.name": {
        "display_name": "Szenario-Name",
        "description": "Generiert einen prägnanten Namen für ein Evaluations-Szenario basierend auf Typ und Beschreibung.",
        "system_prompt": """Du bist ein Experte für wissenschaftliche Studiendesigns.
Generiere einen prägnanten, beschreibenden Namen für ein Evaluations-Szenario.

Der Name sollte:
- 3-6 Wörter lang sein
- Den Studientyp widerspiegeln
- Professionell und akademisch klingen
- Auf Deutsch sein

Antworte NUR mit dem Namen, ohne Erklärung oder Anführungszeichen.""",
        "user_prompt_template": """Generiere einen Namen für ein {scenario_type}-Szenario.

Vorhandene Beschreibung: {existing_description}
Vorhandener Name (falls vorhanden): {existing_name}

Antworte nur mit dem Namen.""",
        "context_variables": ["scenario_type", "existing_description", "existing_name"],
        "max_tokens": 50,
        "temperature": 0.7,
    },
    "scenario.settings.description": {
        "display_name": "Szenario-Beschreibung",
        "description": "Generiert eine kurze Beschreibung für ein Evaluations-Szenario.",
        "system_prompt": """Du bist ein Experte für wissenschaftliche Studiendesigns.
Generiere eine kurze, präzise Beschreibung für ein Evaluations-Szenario.

Die Beschreibung sollte:
- 1-3 Sätze lang sein
- Den Zweck der Studie erklären
- Die Methodik kurz erwähnen
- Auf Deutsch sein

Antworte NUR mit der Beschreibung, ohne Anführungszeichen.""",
        "user_prompt_template": """Generiere eine Beschreibung für ein {scenario_type}-Szenario.

Szenario-Name: {scenario_name}
Bekannte Details:
- Evaluationstyp: {scenario_type}

Antworte nur mit der Beschreibung.""",
        "context_variables": ["scenario_type", "scenario_name"],
        "max_tokens": 150,
        "temperature": 0.7,
    },
    "scenario.rating.scale_labels": {
        "display_name": "Bewertungsskala-Labels",
        "description": "Generiert passende Labels für die Bewertungsskala eines Rating-Szenarios.",
        "system_prompt": """Du bist ein Experte für Fragebogen- und Skalen-Design.
Generiere passende deutsche Labels für eine Bewertungsskala.

Die Labels sollten:
- Klar und eindeutig sein
- Gleichmäßig abgestuft sein
- Zum Bewertungskontext passen

Antworte mit den Labels, getrennt durch Kommas.""",
        "user_prompt_template": """Generiere {scale_size} Labels für eine Bewertungsskala.

Kontext: {evaluation_context}
Beispiel für 5er-Skala: "Sehr schlecht, Schlecht, Neutral, Gut, Sehr gut"

Antworte nur mit den Labels, durch Kommas getrennt.""",
        "context_variables": ["scale_size", "evaluation_context"],
        "max_tokens": 100,
        "temperature": 0.5,
    },
    "scenario.labeling.categories": {
        "display_name": "Kategorien für Labeling",
        "description": "Generiert Kategorien für ein Labeling/Klassifikations-Szenario.",
        "system_prompt": """Du bist ein Experte für Datenklassifikation und Labeling.
Generiere passende Kategorien für ein Klassifikations-Szenario.

Die Kategorien sollten:
- Klar voneinander abgrenzbar sein
- Alle relevanten Fälle abdecken
- Auf Deutsch sein

Antworte mit den Kategorien, jede auf einer neuen Zeile.""",
        "user_prompt_template": """Generiere {num_categories} Kategorien für ein Labeling-Szenario.

Thema: {topic}
Beschreibung: {description}

Antworte mit den Kategorien, eine pro Zeile.""",
        "context_variables": ["num_categories", "topic", "description"],
        "max_tokens": 200,
        "temperature": 0.6,
    },
    "chatbot.config.name": {
        "display_name": "Chatbot-Name",
        "description": "Generiert einen kreativen Namen für einen Chatbot.",
        "system_prompt": """Du bist ein Experte für Chatbot-Design und Branding.
Generiere einen einprägsamen Namen für einen Chatbot.

Der Name sollte:
- Kurz und merkbar sein (1-3 Wörter)
- Zum Zweck des Chatbots passen
- Freundlich und einladend klingen

Antworte NUR mit dem Namen, ohne Erklärung.""",
        "user_prompt_template": """Generiere einen Namen für einen Chatbot.

Zweck: {purpose}
Zielgruppe: {target_audience}
Vorhandener Name: {existing_name}

Antworte nur mit dem Namen.""",
        "context_variables": ["purpose", "target_audience", "existing_name"],
        "max_tokens": 30,
        "temperature": 0.8,
    },
    "chatbot.config.system_prompt": {
        "display_name": "Chatbot System-Prompt",
        "description": "Generiert einen System-Prompt für einen Chatbot basierend auf seinem Zweck.",
        "system_prompt": """Du bist ein Experte für Prompt Engineering.
Erstelle einen effektiven System-Prompt für einen Chatbot.

Der Prompt sollte:
- Die Rolle und Persönlichkeit definieren
- Klare Verhaltensregeln setzen
- Den Umgangston festlegen
- Grenzen definieren

Schreibe den Prompt direkt, ohne Meta-Kommentare.""",
        "user_prompt_template": """Erstelle einen System-Prompt für den Chatbot "{chatbot_name}".

Zweck: {purpose}
Ton: {tone}
Besonderheiten: {special_instructions}

Schreibe den System-Prompt direkt.""",
        "context_variables": ["chatbot_name", "purpose", "tone", "special_instructions"],
        "max_tokens": 500,
        "temperature": 0.7,
    },
    "chatbot.config.welcome_message": {
        "display_name": "Chatbot Begrüßung",
        "description": "Generiert eine Willkommensnachricht für einen Chatbot.",
        "system_prompt": """Du bist ein Experte für Chatbot-UX.
Erstelle eine freundliche Willkommensnachricht für einen Chatbot.

Die Nachricht sollte:
- Freundlich und einladend sein
- Den Chatbot kurz vorstellen
- Zum Gespräch einladen
- 1-3 Sätze lang sein

Antworte NUR mit der Nachricht.""",
        "user_prompt_template": """Erstelle eine Willkommensnachricht für "{chatbot_name}".

Zweck: {purpose}
Ton: {tone}

Antworte nur mit der Nachricht.""",
        "context_variables": ["chatbot_name", "purpose", "tone"],
        "max_tokens": 150,
        "temperature": 0.7,
    },
    "rag.collection.name": {
        "display_name": "Collection-Name",
        "description": "Generiert einen Namen für eine RAG-Collection.",
        "system_prompt": """Du bist ein Experte für Wissensmanagement.
Generiere einen beschreibenden Namen für eine Dokumenten-Collection.

Der Name sollte:
- Kurz und prägnant sein
- Den Inhalt widerspiegeln
- Professionell klingen

Antworte NUR mit dem Namen.""",
        "user_prompt_template": """Generiere einen Namen für eine Dokumenten-Collection.

Dokumenttypen: {document_types}
Themenbereich: {topic}

Antworte nur mit dem Namen.""",
        "context_variables": ["document_types", "topic"],
        "max_tokens": 30,
        "temperature": 0.6,
    },
    "rag.collection.description": {
        "display_name": "Collection-Beschreibung",
        "description": "Generiert eine Beschreibung für eine RAG-Collection.",
        "system_prompt": """Du bist ein Experte für Wissensmanagement.
Generiere eine kurze Beschreibung für eine Dokumenten-Collection.

Die Beschreibung sollte:
- 1-2 Sätze lang sein
- Den Zweck und Inhalt erklären

Antworte NUR mit der Beschreibung.""",
        "user_prompt_template": """Generiere eine Beschreibung für die Collection "{collection_name}".

Dokumenttypen: {document_types}
Themenbereich: {topic}

Antworte nur mit der Beschreibung.""",
        "context_variables": ["collection_name", "document_types", "topic"],
        "max_tokens": 100,
        "temperature": 0.6,
    },
    "latex.document.abstract": {
        "display_name": "Abstract",
        "description": "Generiert ein Abstract für ein LaTeX-Dokument.",
        "system_prompt": """Du bist ein Experte für wissenschaftliches Schreiben.
Generiere ein Abstract für ein akademisches Dokument.

Das Abstract sollte:
- 150-300 Wörter lang sein
- Ziel, Methode und Ergebnisse zusammenfassen
- Akademischen Stil verwenden

Antworte NUR mit dem Abstract-Text.""",
        "user_prompt_template": """Generiere ein Abstract für das Dokument.

Titel: {title}
Hauptthemen: {topics}
Inhaltsübersicht: {content_summary}

Schreibe das Abstract.""",
        "context_variables": ["title", "topics", "content_summary"],
        "max_tokens": 400,
        "temperature": 0.5,
    },
    "scenario.analysis": {
        "display_name": "Szenario-Datenanalyse",
        "description": "Analysiert hochgeladene Daten und generiert KI-Vorschläge für Evaluationstyp, Name, Beschreibung und Konfiguration.",
        "system_prompt": """Du bist ein Experte für Evaluations-Studiendesign. Analysiere die bereitgestellten Daten und generiere Vorschläge für ein LLARS-Evaluationsszenario.

## LLARS ZIEL-SCHEMA

Das Ziel ist die Transformation der Eingabedaten in das LLARS EvaluationData-Format:

```typescript
interface EvaluationData {
  schema_version: "1.0";
  type: "ranking" | "rating" | "mail_rating" | "comparison" | "authenticity" | "labeling";
  reference?: Reference;      // Kontext/Original (z.B. Frage, Originalartikel)
  items: Item[];              // Zu bewertende Elemente
  config: EvaluationConfig;   // Typ-spezifische Konfiguration
  ground_truth?: GroundTruth; // Falls vorhanden: Referenzlösung
}

interface Item {
  id: string;                 // Technische ID: "item_1", "item_2"
  label: string;              // UI-Name: "Antwort A", "Zusammenfassung 1"
  source: {
    type: "human" | "llm" | "unknown";
    name?: string;            // Bei LLM: Modellname
  };
  content: string | Conversation;
}

interface Reference {
  type: "text" | "conversation";
  label: string;              // "Original-Artikel", "Kundenanfrage"
  content: string | Message[];
}

interface Message {
  role: string;               // "Klient", "Berater", "User", "Assistant"
  content: string;
}
```

## EVALUATIONSTYPEN

| Typ | Wann verwenden | Erkennungsmuster |
|-----|----------------|------------------|
| **comparison** | A vs B Vergleich | Felder mit `_a`/`_b` Suffix, `model_a`/`model_b`, `winner` |
| **authenticity** | Mensch vs KI erkennen | Felder: `is_human`, `is_fake`, `is_synthetic`, `is_ai` |
| **labeling** | Kategorien zuweisen | Felder: `label`, `category`, `sentiment`, `class` (nicht binär human/fake) |
| **ranking** | Items in Buckets sortieren | Mehrere Items pro Datensatz, `rank`, `position`, `bucket` Felder |
| **mail_rating** | Beratungsverläufe bewerten | Messages-Array mit Klient/Berater Rollen, `subject`, `thread` |
| **rating** | Einzeltexte mehrdimensional bewerten | Einzelne Texte ohne spezielle Struktur (DEFAULT) |

## ENTSCHEIDUNGSLOGIK

1. **Vergleichsstruktur?** → Felder mit `_a`/`_b`, `conversation_a`/`conversation_b` → `comparison`
2. **Binäre Authentizitäts-Labels?** → `is_human`, `is_fake`, `is_synthetic` → `authenticity`
3. **Kategorien-Labels?** → `label`, `category`, `sentiment` (mehrere Werte) → `labeling`
4. **Konversations-Array mit Beratungsrollen?** → `messages` mit `Klient`/`Berater` → `mail_rating`
5. **Mehrere Items zum Sortieren?** → Items-Array oder Rang-Felder → `ranking`
6. **Einzelne Texte?** → Nur `text`/`content` Felder → `rating`

## MAPPING-BEISPIELE

### Beispiel 1: CSV → comparison
**Eingabe:**
```csv
id,question,answer_a,answer_b,model_a,model_b
1,"Was ist KI?","KI ist...","Künstliche Intelligenz...","gpt-4","claude-3"
```
**LLARS-Ausgabe:**
```json
{
  "type": "comparison",
  "reference": {"type": "text", "label": "Frage", "content": "Was ist KI?"},
  "items": [
    {"id": "item_a", "label": "Antwort A", "source": {"type": "llm", "name": "gpt-4"}, "content": "KI ist..."},
    {"id": "item_b", "label": "Antwort B", "source": {"type": "llm", "name": "claude-3"}, "content": "Künstliche Intelligenz..."}
  ],
  "config": {"question": {"de": "Welche Antwort ist besser?"}, "allow_tie": true}
}
```
**field_mapping:** `{"id_field": "id", "content_field": "answer_a/answer_b", "reference_field": "question"}`

### Beispiel 2: JSON mit Konversationen → mail_rating
**Eingabe:**
```json
{
  "chat_id": "conv_001",
  "subject": "Beratungsanfrage",
  "mails": [
    {"role": "Klient", "content": "Ich habe ein Problem..."},
    {"role": "Berater", "content": "Vielen Dank für Ihre Nachricht..."}
  ]
}
```
**LLARS-Ausgabe:**
```json
{
  "type": "mail_rating",
  "items": [{
    "id": "conv_001",
    "label": "Beratungsanfrage",
    "source": {"type": "unknown"},
    "content": {"type": "conversation", "messages": [...]}
  }],
  "config": {"scale": {"min": 1, "max": 5}, "dimensions": [...]}
}
```
**field_mapping:** `{"id_field": "chat_id", "content_field": "mails", "label_field": "subject"}`

### Beispiel 3: JSONL mit Labels → authenticity
**Eingabe:**
```jsonl
{"id": "1", "text": "Ein gut geschriebener Text...", "is_human": true}
{"id": "2", "text": "Dieser Text wurde generiert...", "is_human": false, "model": "gpt-4"}
```
**LLARS-Ausgabe:**
```json
{
  "type": "authenticity",
  "items": [
    {"id": "1", "label": "Text 1", "source": {"type": "human"}, "content": "Ein gut geschriebener Text..."},
    {"id": "2", "label": "Text 2", "source": {"type": "llm", "name": "gpt-4"}, "content": "Dieser Text wurde generiert..."}
  ],
  "config": {"options": [{"id": "human", "label": {"de": "Mensch"}}, {"id": "ai", "label": {"de": "KI"}}]}
}
```
**field_mapping:** `{"id_field": "id", "content_field": "text", "label_field": "is_human"}`

### Beispiel 4: Texte bewerten → rating
**Eingabe:**
```json
{"id": "sum_1", "source_text": "Langer Originalartikel...", "summary": "Kurze Zusammenfassung...", "model": "gpt-4"}
```
**LLARS-Ausgabe:**
```json
{
  "type": "rating",
  "reference": {"type": "text", "label": "Original", "content": "Langer Originalartikel..."},
  "items": [{"id": "sum_1", "label": "Zusammenfassung", "source": {"type": "llm", "name": "gpt-4"}, "content": "Kurze Zusammenfassung..."}],
  "config": {"scale": {"min": 1, "max": 5}, "dimensions": [{"id": "coherence", "label": {"de": "Kohärenz"}}]}
}
```
**field_mapping:** `{"id_field": "id", "content_field": "summary", "reference_field": "source_text"}`

## KONFIGURATION NACH TYP

### rating / mail_rating
```json
{"scale": {"min": 1, "max": 5, "step": 1}, "dimensions": [
  {"id": "coherence", "label": {"de": "Kohärenz", "en": "Coherence"}, "weight": 0.25},
  {"id": "fluency", "label": {"de": "Flüssigkeit", "en": "Fluency"}, "weight": 0.25},
  {"id": "relevance", "label": {"de": "Relevanz", "en": "Relevance"}, "weight": 0.25},
  {"id": "consistency", "label": {"de": "Konsistenz", "en": "Consistency"}, "weight": 0.25}
]}
```

### ranking
```json
{"buckets": [
  {"id": "good", "label": {"de": "Gut", "en": "Good"}, "color": "#98d4bb", "order": 1},
  {"id": "moderate", "label": {"de": "Mittel", "en": "Moderate"}, "color": "#D1BC8A", "order": 2},
  {"id": "poor", "label": {"de": "Schlecht", "en": "Poor"}, "color": "#e8a087", "order": 3}
], "allow_ties": true}
```

### comparison
```json
{"question": {"de": "Welche Antwort ist besser?", "en": "Which answer is better?"}, "allow_tie": true, "show_source": false}
```

### authenticity
```json
{"options": [
  {"id": "human", "label": {"de": "Mensch", "en": "Human"}},
  {"id": "ai", "label": {"de": "KI-generiert", "en": "AI-generated"}}
], "show_confidence": true}
```

### labeling
```json
{"mode": "single", "labels": [
  {"id": "cat1", "label": {"de": "Kategorie 1"}},
  {"id": "cat2", "label": {"de": "Kategorie 2"}}
], "allow_other": false}
```

## AUSGABEFORMAT

Antworte IMMER in diesem JSON-Format:

```json
{
  "suggestions": {
    "evaluation_type": "rating|ranking|labeling|comparison|mail_rating|authenticity",
    "confidence": 0.0-1.0,
    "name": "Kurzer prägnanter Name (deutsch)",
    "description": "Beschreibung des Szenarios (1-2 Sätze, deutsch)",
    "reasoning": "Begründung: Welche Muster wurden erkannt? Warum dieser Typ?",
    "preset": "llm-judge-standard|buckets-3|pairwise|binary-authentic|custom",
    "config": { /* Typ-spezifische Konfiguration siehe oben */ },
    "field_mapping": {
      "id_field": "Feldname für Item-ID",
      "content_field": "Feldname für Hauptinhalt",
      "reference_field": "Feldname für Kontext/Original (optional)",
      "label_field": "Feldname für Ground-Truth-Labels (optional)"
    }
  },
  "data_quality": {
    "completeness": 0.0-1.0,
    "issues": ["Problem 1"],
    "recommendations": ["Empfehlung 1"]
  }
}
```

REGELN:
- Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen
- Nutze die erkannten Muster (detected_patterns) aus der Datenanalyse
- Das field_mapping muss die tatsächlichen Feldnamen aus den Eingabedaten verwenden
- Bei Unsicherheit: `rating` als sicherer Default""",
        "user_prompt_template": """{preprocessed_data}

{user_hint_text}

Analysiere die Datenstruktur und erkannten Muster. Generiere einen passenden LLARS-Evaluationsvorschlag im JSON-Format.""",
        "context_variables": ["preprocessed_data", "user_hint_text"],
        "max_tokens": 2000,
        "temperature": 0.5,
    },
}


class FieldPromptService:
    """Service for managing field prompt templates."""

    @staticmethod
    def seed_defaults() -> int:
        """
        Seed default field prompts into the database.
        Only creates prompts that don't exist yet.

        Returns:
            Number of prompts created
        """
        created = 0

        for field_key, config in DEFAULT_FIELD_PROMPTS.items():
            existing = FieldPromptTemplate.query.filter_by(field_key=field_key).first()

            if not existing:
                template = FieldPromptTemplate(
                    field_key=field_key,
                    display_name=config["display_name"],
                    description=config.get("description"),
                    system_prompt=config["system_prompt"],
                    user_prompt_template=config["user_prompt_template"],
                    context_variables=config.get("context_variables", []),
                    max_tokens=config.get("max_tokens", 200),
                    temperature=config.get("temperature", 0.7),
                    is_active=True,
                )
                db.session.add(template)
                created += 1
                logger.info(f"Created field prompt: {field_key}")

        if created > 0:
            db.session.commit()
            logger.info(f"Seeded {created} default field prompts")

        return created

    @staticmethod
    def reseed_defaults(field_keys: List[str] = None) -> Dict[str, int]:
        """
        Reseed field prompts, updating existing ones with default values.

        Args:
            field_keys: Optional list of specific field keys to reseed.
                       If None, reseeds all default prompts.

        Returns:
            Dict with 'created' and 'updated' counts
        """
        created = 0
        updated = 0

        keys_to_process = field_keys or list(DEFAULT_FIELD_PROMPTS.keys())

        for field_key in keys_to_process:
            if field_key not in DEFAULT_FIELD_PROMPTS:
                logger.warning(f"Unknown field key, skipping: {field_key}")
                continue

            config = DEFAULT_FIELD_PROMPTS[field_key]
            existing = FieldPromptTemplate.query.filter_by(field_key=field_key).first()

            if existing:
                # Update existing prompt with new defaults
                existing.display_name = config["display_name"]
                existing.description = config.get("description")
                existing.system_prompt = config["system_prompt"]
                existing.user_prompt_template = config["user_prompt_template"]
                existing.context_variables = config.get("context_variables", [])
                existing.max_tokens = config.get("max_tokens", 200)
                existing.temperature = config.get("temperature", 0.7)
                updated += 1
                logger.info(f"Updated field prompt: {field_key}")
            else:
                # Create new prompt
                template = FieldPromptTemplate(
                    field_key=field_key,
                    display_name=config["display_name"],
                    description=config.get("description"),
                    system_prompt=config["system_prompt"],
                    user_prompt_template=config["user_prompt_template"],
                    context_variables=config.get("context_variables", []),
                    max_tokens=config.get("max_tokens", 200),
                    temperature=config.get("temperature", 0.7),
                    is_active=True,
                )
                db.session.add(template)
                created += 1
                logger.info(f"Created field prompt: {field_key}")

        if created > 0 or updated > 0:
            db.session.commit()
            logger.info(f"Reseeded field prompts: {created} created, {updated} updated")

        return {"created": created, "updated": updated}

    @staticmethod
    def get_by_field_key(field_key: str) -> Optional[FieldPromptTemplate]:
        """Get prompt template by field key."""
        return FieldPromptTemplate.get_by_field_key(field_key)

    @staticmethod
    def get_all() -> List[FieldPromptTemplate]:
        """Get all field prompt templates."""
        return FieldPromptTemplate.query.order_by(FieldPromptTemplate.field_key).all()

    @staticmethod
    def get_all_active() -> List[FieldPromptTemplate]:
        """Get all active field prompt templates."""
        return FieldPromptTemplate.get_all_active()

    @staticmethod
    def create(
        field_key: str,
        display_name: str,
        system_prompt: str,
        user_prompt_template: str,
        description: Optional[str] = None,
        context_variables: Optional[List[str]] = None,
        max_tokens: int = 200,
        temperature: float = 0.7,
    ) -> FieldPromptTemplate:
        """Create a new field prompt template."""
        template = FieldPromptTemplate(
            field_key=field_key,
            display_name=display_name,
            description=description,
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            context_variables=context_variables or [],
            max_tokens=max_tokens,
            temperature=temperature,
            is_active=True,
        )
        db.session.add(template)
        db.session.commit()
        logger.info(f"Created field prompt: {field_key}")
        return template

    @staticmethod
    def update(
        template_id: int,
        **kwargs
    ) -> Optional[FieldPromptTemplate]:
        """Update a field prompt template."""
        template = FieldPromptTemplate.query.get(template_id)
        if not template:
            return None

        allowed_fields = [
            'display_name', 'description', 'system_prompt',
            'user_prompt_template', 'context_variables',
            'max_tokens', 'temperature', 'is_active'
        ]

        for field in allowed_fields:
            if field in kwargs:
                setattr(template, field, kwargs[field])

        db.session.commit()
        logger.info(f"Updated field prompt: {template.field_key}")
        return template

    @staticmethod
    def delete(template_id: int) -> bool:
        """Delete a field prompt template."""
        template = FieldPromptTemplate.query.get(template_id)
        if not template:
            return False

        field_key = template.field_key
        db.session.delete(template)
        db.session.commit()
        logger.info(f"Deleted field prompt: {field_key}")
        return True

    @staticmethod
    def render_prompt(template: FieldPromptTemplate, context: Dict[str, Any]) -> str:
        """
        Render the user prompt with context variables.

        Args:
            template: The prompt template
            context: Variable values to substitute

        Returns:
            Rendered prompt string
        """
        return template.render_user_prompt(context)
