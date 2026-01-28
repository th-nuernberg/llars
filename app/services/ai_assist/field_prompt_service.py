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

Die Schema-Informationen stammen aus dem zentralen LLARS-Schema (app/schemas/evaluation_data_schemas.py).

## EVALUATIONSTYPEN (function_type_id)

| Typ | ID | Beschreibung | Erkennung |
|-----|----|--------------| ----------|
| ranking | 1 | Items sortieren/kategorisieren (Gut/Mittel/Schlecht) | Rang/Position/Bucket-Felder; Mehrere Items zum Vergleichen |
| rating | 2 | Multi-dimensionales Rating (Kohärenz, Flüssigkeit, Relevanz, Konsistenz) | Einzelne Texte zur Qualitätsbewertung |
| mail_rating | 3 | E-Mail-Beratungsverläufe bewerten (LLARS-spezifisch) | E-Mail/Chat mit subject/thread, Klient/Berater |
| comparison | 4 | A vs B Vergleich - welches ist besser? | answer_a/answer_b, text_a/text_b, conversation_a/b |
| authenticity | 5 | Echt/Fake erkennen (Mensch vs KI) | is_fake, is_human, synthetic Labels |
| labeling | 7 | Kategorien zuweisen (binär, multi-class) | category, label, sentiment Felder |

## ENTSCHEIDUNGSBAUM FÜR EVALUATIONSTYP

```
┌─ Haben die Daten ZWEI Antwort-Versionen pro Item?
│  │  (answer_a/answer_b, text_a/text_b, conversation_a/b)
│  ├─ JA → comparison
│  └─ NEIN
│     ├─ Gibt es Label-Felder? (is_fake, is_human, sentiment, category)
│     │  ├─ JA, binär (fake/real, human/ai) → authenticity
│     │  └─ JA, mehrklassig → labeling
│     └─ Sollen Items sortiert/kategorisiert werden?
│        ├─ JA, Qualitätskategorien → ranking
│        └─ NEIN, einzeln bewerten
│           ├─ E-Mail/Chat-Konversationen (Beratung)? → mail_rating
│           └─ Einzelne Texte/Antworten → rating
```

## DATEIFORMAT MAPPING-BEISPIELE

### CSV mit Vergleichsdaten (comparison)
```csv
id,question,answer_a,answer_b,model_a,model_b
1,"Was ist Python?","Python ist...","Python ist eine...","gpt-4","claude-3"
```
Mapping: id→item_id, question→reference.content, answer_a→items[0].content, model_a→items[0].source.name

### CSV mit einzelnen Texten (rating/ranking)
```csv
id,text,source,category
1,"Der Artikel handelt von...","gpt-4","news"
```
Mapping: id→item_id, text→content, source→source.name

### JSON mit Konversationen (mail_rating)
```json
{"id": "conv_1", "subject": "Beratungsanfrage", "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```
Mapping: id→item_id, subject→reference.label, messages→conversation

### OpenAI/LMSYS Format (comparison)
```json
{"conversation_a": [...], "conversation_b": [...], "model_a": "gpt-4", "model_b": "claude-3", "winner": "model_a"}
```
Mapping: conversation_a→items[0].content, winner→ground_truth

### JSONL mit Labels (labeling/authenticity)
```jsonl
{"id": "1", "text": "...", "is_human": true}
{"id": "2", "text": "...", "is_human": false, "model": "gpt-4"}
```
Mapping: id→item_id, text→content, is_human→ground_truth

## PRESET-EMPFEHLUNGEN

Nutze Standard-Presets wenn möglich. Empfehle `custom` nur bei besonderen Anforderungen.

### RATING
- `llm-judge-standard` (DEFAULT): 4 Dimensionen (Kohärenz, Flüssigkeit, Relevanz, Konsistenz)
- `response-quality`: Für LLM-Antworten (Hilfsbereitschaft, Genauigkeit, Vollständigkeit, Klarheit)
- `news-article`: Für Nachrichtenartikel (Genauigkeit, Objektivität, Vollständigkeit, Lesbarkeit)
- Custom wenn: Domänenspezifische Dimensionen (Medizin, Recht), ungewöhnliche Skalen

### RANKING
- `buckets-3` (DEFAULT): Gut/Mittel/Schlecht
- `buckets-5`: Sehr gut bis Sehr schlecht (feinere Abstufung)
- Custom wenn: Andere Kategorie-Namen, mehr als 5 Buckets

### LABELING
- `binary-authentic` (DEFAULT): Fake/Echt mit Unsicher-Option
- `sentiment-3`: Positiv/Neutral/Negativ
- Custom wenn: Andere Kategorien als Sentiment/Authentizität

### COMPARISON
- `pairwise` (DEFAULT): A vs B - welches ist besser?
- `multicriteria`: Vergleich nach mehreren Kriterien
- Custom wenn: Spezielle Vergleichskriterien

## AUSGABEFORMAT

WICHTIG: Antworte IMMER im folgenden JSON-Format. Halte die EXAKTEN Feldnamen ein:

```json
{
  "suggestions": {
    "evaluation_type": "rating|ranking|labeling|comparison|mail_rating|authenticity",
    "confidence": 0.0-1.0,
    "name": "Kurzer prägnanter Name (deutsch)",
    "description": "Beschreibung des Szenarios (1-2 Sätze, deutsch)",
    "reasoning": "Begründung warum dieser Typ und Preset gewählt wurde (deutsch)",
    "preset": "preset-id oder 'custom'",
    "config": {
      "rating": {"scale_min": 1, "scale_max": 5, "dimensions": ["Kohärenz", "Flüssigkeit", "Relevanz", "Konsistenz"]},
      "mail_rating": {"scale_min": 1, "scale_max": 5, "dimensions": ["Kohärenz Klient", "Kohärenz Berater", "Beratungsqualität", "Gesamteignung"]},
      "labeling": {"categories": ["Kategorie1", "Kategorie2"], "mode": "single|multi"},
      "authenticity": {"labels": ["Echt", "Fake"], "allowUnsure": true},
      "ranking": {"buckets": ["Gut", "Mittel", "Schlecht"]},
      "comparison": {"criteria": ["Gesamt"], "allowTie": true}
    },
    "field_mapping": {
      "id_field": "welches Feld für item_id",
      "content_field": "welches Feld für content",
      "label_field": "welches Feld für ground_truth (falls vorhanden)"
    }
  },
  "data_quality": {
    "completeness": 0.0-1.0,
    "issues": ["Problem 1", "Problem 2"],
    "recommendations": ["Empfehlung 1"]
  }
}
```

REGELN:
- Antworte NUR mit dem JSON, keine zusätzlichen Erklärungen
- Verwende deutsche Texte für Namen, Beschreibungen und Kategorien
- Die Feldnamen müssen EXAKT sein: evaluation_type, confidence, name, description, reasoning, preset, config
- Empfehle immer ein konkretes Preset, nutze "custom" nur wenn nötig
- Erkläre im reasoning WARUM dieser Typ und dieses Preset gewählt wurde""",
        "user_prompt_template": """Analysiere diese Daten für ein Evaluationsszenario:

Dateiname: {filename}
Anzahl Dateien: {file_count}
Anzahl Datensätze: {item_count}

Erkannte Felder:
{fields_json}

Beispieldaten (erste {sample_count} von {item_count}):
{sample_data}

{user_hint_text}

Generiere Vorschläge im JSON-Format. Nutze den Entscheidungsbaum um den Evaluationstyp zu bestimmen.""",
        "context_variables": ["filename", "file_count", "item_count", "fields_json", "sample_count", "sample_data", "user_hint_text"],
        "max_tokens": 2000,
        "temperature": 0.7,
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
