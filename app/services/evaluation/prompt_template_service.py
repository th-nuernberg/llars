"""
Prompt Template Service for LLM Evaluators.

Manages prompt templates for different evaluation task types.
Provides default prompts and allows scenario-specific overrides.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from db import db
from db.models import PromptTemplate

logger = logging.getLogger(__name__)


# =============================================================================
# Default Prompts for Each Task Type
# =============================================================================

DEFAULT_PROMPTS: Dict[str, Dict[str, Any]] = {
    "ranking": {
        "name": "Default Ranking Prompt",
        "system_prompt": """Du bist ein strenger Evaluator für Feature-Rankings in Beratungsgesprächen.
Deine Aufgabe ist es, Features (Analysen eines LLM zu einem Beratungsgespräch) nach ihrer Qualität zu bewerten.

Bewertungskriterien:
- Präzision: Wie genau und spezifisch ist die Analyse?
- Relevanz: Wie relevant ist das Feature für das Beratungsgespräch?
- Tiefgang: Wie tiefgehend ist die Analyse?
- Nützlichkeit: Wie nützlich ist das Feature für das Verständnis des Gesprächs?

Du musst JEDES Feature GENAU EINMAL einem der vier Buckets zuordnen:
- gut: Hochwertige, präzise und relevante Analysen
- mittel: Akzeptable Analysen mit Verbesserungspotential
- schlecht: Oberflächliche oder irrelevante Analysen
- neutral: Nicht eindeutig kategorisierbar

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format. Keine zusätzlichen Erklärungen außerhalb des JSON.""",
        "user_prompt_template": """Ordne alle folgenden Feature-IDs genau einmal einem Bucket zu.

Features (zufällig sortiert):
{features}

Antworte im folgenden JSON-Format:
{{
  "buckets": {{
    "gut": {{
      "feature_ids": [<IDs>],
      "reasoning": "<Begründung warum diese Features gut sind>"
    }},
    "mittel": {{
      "feature_ids": [<IDs>],
      "reasoning": "<Begründung warum diese Features mittel sind>"
    }},
    "schlecht": {{
      "feature_ids": [<IDs>],
      "reasoning": "<Begründung warum diese Features schlecht sind>"
    }},
    "neutral": {{
      "feature_ids": [<IDs>],
      "reasoning": "<Begründung warum diese Features neutral sind>"
    }}
  }},
  "overall_assessment": "<Gesamtbewertung der Feature-Qualität>",
  "reasoning": "<Deine detaillierte Begründung für die Gesamtbewertung>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["features"],
        "output_schema_version": "1.0",
    },
    "rating": {
        "name": "Default Rating Prompt",
        "system_prompt": """Du bist ein Experte für die Bewertung von Features in Beratungsgesprächen.
Deine Aufgabe ist es, jedes Feature (LLM-generierte Analyse) auf einer Skala von 1-5 zu bewerten.

Bewertungsskala:
1 = Sehr schlecht: Falsch, irrelevant oder irreführend
2 = Schlecht: Oberflächlich, wenig hilfreich
3 = Mittel: Akzeptabel, grundlegende Analyse
4 = Gut: Präzise, relevante und hilfreiche Analyse
5 = Sehr gut: Exzellente, tiefgehende und äußerst nützliche Analyse

Für jedes Feature sollst du:
- Die Qualität bewerten (1-5)
- Eine Begründung geben
- Stärken identifizieren
- Schwächen aufzeigen

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format.""",
        "user_prompt_template": """Bewerte die folgenden Features basierend auf dem Kontext der Konversation.

Konversation:
{thread_content}

Features zur Bewertung:
{features}

Antworte im folgenden JSON-Format:
{{
  "ratings": [
    {{
      "feature_id": <ID>,
      "rating": <1-5>,
      "reasoning": "<Begründung für diese Bewertung>",
      "strengths": ["<Stärke 1>", "<Stärke 2>"],
      "weaknesses": ["<Schwäche 1>", "<Schwäche 2>"]
    }}
  ],
  "average_rating": <Durchschnitt aller Ratings>,
  "thread_summary": "<Kurze Zusammenfassung der Konversation>",
  "reasoning": "<Gesamtbegründung für die Bewertungen>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["thread_content", "features"],
        "output_schema_version": "1.0",
    },
    "authenticity": {
        "name": "Default Authenticity Prompt",
        "system_prompt": """Du bist ein Experte für die Erkennung von KI-generierten vs. echten Konversationen.
Deine Aufgabe ist es zu entscheiden, ob eine Beratungskonversation echt (von Menschen geschrieben) oder künstlich (KI-generiert) ist.

Analysiere folgende Aspekte:
1. Sprachliche Muster: Natürlichkeit, Variabilität, Tippfehler
2. Emotionale Konsistenz: Authentische emotionale Entwicklung
3. Gesprächsdynamik: Realistische Interaktionsmuster
4. Inhaltliche Plausibilität: Glaubwürdigkeit der beschriebenen Situation

Indikatoren für ECHT:
- Natürliche Sprachvariationen und Fehler
- Authentische emotionale Reaktionen
- Unvorhersehbare Gesprächswendungen
- Inkonsistenzen, die typisch für echte Gespräche sind

Indikatoren für KÜNSTLICH:
- Unnatürlich perfekte Grammatik
- Zu konsistente Schreibweise
- Vorhersehbare Gesprächsstruktur
- Fehlen von Emotionen oder übertriebene Emotionen

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format.""",
        "user_prompt_template": """Analysiere die folgende Konversation und entscheide, ob sie echt oder künstlich ist.

Konversation:
{thread_content}

Antworte im folgenden JSON-Format:
{{
  "vote": "real" | "fake",
  "confidence_score": <1-5>,
  "indicators": [
    {{
      "indicator": "<Beschreibung des Indikators>",
      "supports": "real" | "fake",
      "weight": <0.0-1.0>
    }}
  ],
  "linguistic_analysis": "<Analyse der sprachlichen Muster>",
  "behavioral_analysis": "<Analyse des Konversationsverhaltens>",
  "reasoning": "<Gesamtbegründung für deine Entscheidung>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["thread_content"],
        "output_schema_version": "1.0",
    },
    "mail_rating": {
        "name": "Default Mail Rating Prompt",
        "system_prompt": """Du bist ein Experte für die Bewertung von E-Mail-Beratungskonversationen.
Deine Aufgabe ist es, die Gesamtqualität einer Beratungskonversation zu bewerten.

Bewertungskriterien:
1. Empathie: Einfühlungsvermögen und Verständnis
2. Fachlichkeit: Kompetenz und Expertise
3. Verständlichkeit: Klarheit der Kommunikation
4. Hilfsbereitschaft: Engagement und Unterstützung
5. Lösungsorientierung: Konkrete Handlungsempfehlungen

Bewertungsskala pro Kriterium: 1-5
Gesamtbewertung: 1-5 (Durchschnitt mit Gewichtung)

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format.""",
        "user_prompt_template": """Bewerte die folgende E-Mail-Beratungskonversation.

Betreff: {subject}

Konversation:
{thread_content}

Antworte im folgenden JSON-Format:
{{
  "overall_rating": <1-5>,
  "criteria": [
    {{"name": "Empathie", "score": <1-5>, "reasoning": "<Begründung>"}},
    {{"name": "Fachlichkeit", "score": <1-5>, "reasoning": "<Begründung>"}},
    {{"name": "Verständlichkeit", "score": <1-5>, "reasoning": "<Begründung>"}},
    {{"name": "Hilfsbereitschaft", "score": <1-5>, "reasoning": "<Begründung>"}},
    {{"name": "Lösungsorientierung", "score": <1-5>, "reasoning": "<Begründung>"}}
  ],
  "strengths": ["<Stärke 1>", "<Stärke 2>"],
  "areas_for_improvement": ["<Verbesserungsbereich 1>"],
  "summary": "<Zusammenfassende Bewertung>",
  "reasoning": "<Detaillierte Gesamtbegründung>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["subject", "thread_content"],
        "output_schema_version": "1.0",
    },
    "comparison": {
        "name": "Default Comparison Prompt",
        "system_prompt": """Du bist ein Experte für den Vergleich von Texten und Antworten.
Deine Aufgabe ist es, zwei Texte/Antworten zu vergleichen und den besseren zu wählen.

Bewertungskriterien:
- Klarheit: Wie verständlich ist der Text?
- Vollständigkeit: Werden alle relevanten Aspekte behandelt?
- Korrektheit: Sind die Informationen korrekt?
- Relevanz: Wie relevant ist die Antwort für die Frage?
- Sprachqualität: Grammatik, Stil und Lesbarkeit

Mögliche Ergebnisse:
- A: Text/Antwort A ist besser
- B: Text/Antwort B ist besser
- TIE: Beide sind gleichwertig

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format.""",
        "user_prompt_template": """Vergleiche die folgenden zwei Texte/Antworten und entscheide, welcher besser ist.

Text A:
{text_a}

Text B:
{text_b}

Antworte im folgenden JSON-Format:
{{
  "winner": "A" | "B" | "TIE",
  "confidence_score": <1-5>,
  "comparison_aspects": [
    {{"aspect": "<Aspekt>", "winner": "A" | "B" | "TIE", "reasoning": "<Begründung>"}}
  ],
  "reasoning": "<Gesamtbegründung für die Entscheidung>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["text_a", "text_b"],
        "output_schema_version": "1.0",
    },
    "text_classification": {
        "name": "Default Text Classification Prompt",
        "system_prompt": """Du bist ein Experte für Textklassifikation.
Deine Aufgabe ist es, Texte in vorgegebene Kategorien einzuordnen.

Bewerte folgende Aspekte:
- Hauptthema des Textes
- Schlüsselwörter und Phrasen
- Tonalität und Stil
- Kontext und Absicht

Gib deine Klassifikation mit Konfidenz und Begründung an.
Wenn mehrere Labels möglich sind, gib auch Alternativen an.

Antworte AUSSCHLIESSLICH im vorgegebenen JSON-Format.""",
        "user_prompt_template": """Klassifiziere den folgenden Text in eine der vorgegebenen Kategorien.

Erlaubte Labels: {labels}
{label_descriptions}

Text:
{text_content}

Antworte im folgenden JSON-Format:
{{
  "label": "<eines der erlaubten Labels>",
  "confidence_score": <1-5>,
  "alternative_labels": [
    {{"label": "<alternatives Label>", "probability": <0.0-1.0>}}
  ],
  "key_phrases": ["<Schlüsselphrase 1>", "<Schlüsselphrase 2>"],
  "reasoning": "<Begründung für die Klassifikation>",
  "confidence": <0.0-1.0>
}}""",
        "variables": ["labels", "label_descriptions", "text_content"],
        "output_schema_version": "1.0",
    },
}

# Alias: labeling uses the same prompt defaults as text_classification
DEFAULT_PROMPTS["labeling"] = DEFAULT_PROMPTS["text_classification"]


class PromptTemplateService:
    """Service for managing prompt templates for LLM evaluators."""

    @staticmethod
    def seed_defaults(created_by: str = "system") -> Dict[str, int]:
        """
        Seed default prompt templates for all task types.

        Args:
            created_by: Username who creates the templates

        Returns:
            Dict mapping task_type to template ID
        """
        created = {}

        for task_type, prompt_data in DEFAULT_PROMPTS.items():
            existing = PromptTemplate.get_default_for_task(task_type)
            if existing:
                logger.debug(
                    "Default template for '%s' already exists (id=%s)",
                    task_type, existing.id
                )
                created[task_type] = existing.id
                continue

            template = PromptTemplate(
                name=prompt_data["name"],
                task_type=task_type,
                version="1.0",
                system_prompt=prompt_data["system_prompt"],
                user_prompt_template=prompt_data["user_prompt_template"],
                variables=prompt_data.get("variables", []),
                output_schema_version=prompt_data.get("output_schema_version", "1.0"),
                is_default=True,
                is_active=True,
                created_by=created_by,
            )
            db.session.add(template)
            db.session.flush()
            created[task_type] = template.id
            logger.info(
                "Created default prompt template for '%s' (id=%s)",
                task_type, template.id
            )

        db.session.commit()
        return created

    @staticmethod
    def get_template_for_task(
        task_type: str,
        template_id: Optional[int] = None,
    ) -> Optional[PromptTemplate]:
        """
        Get the prompt template for a task type.

        Args:
            task_type: The evaluation task type
            template_id: Optional specific template ID (for scenario override)

        Returns:
            PromptTemplate or None if not found
        """
        if template_id:
            template = PromptTemplate.query.filter_by(
                id=template_id,
                is_active=True
            ).first()
            if template:
                return template
            logger.warning(
                "Template %s not found or inactive, falling back to default",
                template_id
            )

        return PromptTemplate.get_default_for_task(task_type)

    @staticmethod
    def get_all_for_task(task_type: str) -> List[PromptTemplate]:
        """Get all active templates for a task type."""
        return PromptTemplate.get_active_for_task(task_type)

    @staticmethod
    def create_template(
        name: str,
        task_type: str,
        system_prompt: str,
        user_prompt_template: str,
        *,
        variables: Optional[List[str]] = None,
        is_default: bool = False,
        created_by: Optional[str] = None,
    ) -> PromptTemplate:
        """
        Create a new prompt template.

        Args:
            name: Template name
            task_type: Evaluation task type
            system_prompt: System prompt text
            user_prompt_template: User prompt template with placeholders
            variables: List of placeholder variable names
            is_default: Whether to set as default for task type
            created_by: Creator username

        Returns:
            Created PromptTemplate
        """
        template = PromptTemplate(
            name=name,
            task_type=task_type,
            version="1.0",
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            variables=variables or [],
            output_schema_version="1.0",
            is_default=False,
            is_active=True,
            created_by=created_by,
        )
        db.session.add(template)

        if is_default:
            template.set_as_default()

        db.session.commit()
        logger.info("Created template '%s' for task '%s' (id=%s)", name, task_type, template.id)
        return template

    @staticmethod
    def update_template(
        template_id: int,
        **updates,
    ) -> Optional[PromptTemplate]:
        """
        Update a prompt template.

        Args:
            template_id: Template ID to update
            **updates: Fields to update

        Returns:
            Updated PromptTemplate or None if not found
        """
        template = PromptTemplate.query.get(template_id)
        if not template:
            return None

        allowed_fields = {
            "name", "system_prompt", "user_prompt_template",
            "variables", "is_active"
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(template, field, value)

        # Increment version on content changes
        if "system_prompt" in updates or "user_prompt_template" in updates:
            parts = template.version.split(".")
            minor = int(parts[1]) + 1 if len(parts) > 1 else 1
            template.version = f"{parts[0]}.{minor}"

        db.session.commit()
        return template

    @staticmethod
    def set_default(template_id: int) -> bool:
        """
        Set a template as the default for its task type.

        Returns:
            True if successful, False if template not found
        """
        template = PromptTemplate.query.get(template_id)
        if not template:
            return False

        template.set_as_default()
        db.session.commit()
        return True

    @staticmethod
    def render_prompt(
        template: PromptTemplate,
        **variables,
    ) -> str:
        """
        Render a prompt template with variables.

        Args:
            template: The PromptTemplate to render
            **variables: Variable values to substitute

        Returns:
            Rendered prompt string
        """
        prompt = template.user_prompt_template

        for var_name, var_value in variables.items():
            placeholder = "{" + var_name + "}"
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(var_value))

        return prompt

    @staticmethod
    def get_available_task_types() -> List[str]:
        """Get all available task types."""
        return list(DEFAULT_PROMPTS.keys())
