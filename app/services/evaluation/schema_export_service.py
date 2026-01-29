"""
Schema Export Service for AI Prompts.

Exportiert Schema-Definitionen aus dem zentralen evaluation_data_schemas.py
in ein Format, das für AI-Prompts im Scenario Wizard geeignet ist.

INTEGRATION:
    - Wird von field_prompt_service.py verwendet
    - Wird von ai_analyzer.py für konsistente Schema-Referenzen genutzt
    - Hält AI-Prompts automatisch synchron mit Schema-Änderungen

Usage:
    from services.evaluation.schema_export_service import SchemaExportService

    # Komplettes Schema für AI-Prompt
    schema_text = SchemaExportService.get_schema_for_ai_prompt()

    # Nur Evaluationstypen
    types_text = SchemaExportService.get_evaluation_types_description()

    # Preset-Empfehlungen
    presets_text = SchemaExportService.get_preset_recommendations()
"""

from __future__ import annotations

import json
import logging
from typing import Dict, List, Any

from schemas.evaluation_data_schemas import (
    EvaluationType,
    SourceType,
    ContentType,
    RankingMode,
    LabelingMode,
    create_default_ranking_buckets,
    create_default_rating_dimensions,
    create_default_scale,
)

logger = logging.getLogger(__name__)


class SchemaExportService:
    """
    Service zum Exportieren von Schema-Definitionen für AI-Prompts.

    Generiert konsistente, aktuelle Schema-Beschreibungen direkt aus den
    zentralen Pydantic-Modellen in evaluation_data_schemas.py.
    """

    # =========================================================================
    # Evaluation Type Mapping (Ground Truth)
    # =========================================================================

    EVALUATION_TYPE_INFO: Dict[EvaluationType, Dict[str, Any]] = {
        EvaluationType.RANKING: {
            "function_type_id": 1,
            "description_de": "Items sortieren oder in Qualitätskategorien einteilen (Gut/Mittel/Schlecht)",
            "description_en": "Sort items or categorize into quality buckets (Good/Moderate/Poor)",
            "detection_hints": [
                "Rang/Position/Bucket-Felder vorhanden",
                "Mehrere Items die verglichen werden sollen",
                "Qualitätssortierung gewünscht"
            ],
            "example_use_cases": [
                "Zusammenfassungen nach Qualität sortieren",
                "LLM-Antworten in Kategorien einteilen",
                "Features priorisieren"
            ]
        },
        EvaluationType.RATING: {
            "function_type_id": 2,
            "description_de": "Multi-dimensionales Rating mit LLM-as-Judge Metriken (Kohärenz, Flüssigkeit, Relevanz, Konsistenz)",
            "description_en": "Multi-dimensional rating with LLM-as-Judge metrics (Coherence, Fluency, Relevance, Consistency)",
            "detection_hints": [
                "Einzelne Texte/Antworten zur Qualitätsbewertung",
                "Keine Vergleiche zwischen Items nötig",
                "Detaillierte Metriken gewünscht"
            ],
            "example_use_cases": [
                "Textqualität auf Skala bewerten",
                "LLM-Antworten nach Metriken evaluieren",
                "Zusammenfassungsqualität messen"
            ]
        },
        EvaluationType.MAIL_RATING: {
            "function_type_id": 3,
            "description_de": "E-Mail-Beratungsverläufe bewerten (LLARS-spezifisch: Kohärenz, Beratungsqualität)",
            "description_en": "Rate email counseling threads (LLARS-specific: Coherence, Counseling Quality)",
            "detection_hints": [
                "E-Mail/Chat-Konversationen mit subject/thread",
                "Beratungskontext (Klient/Berater Rollen)",
                "Mehrteilige Dialoge"
            ],
            "example_use_cases": [
                "Online-Beratungsqualität bewerten",
                "Klient-Berater Kommunikation analysieren",
                "Beratungsverläufe evaluieren"
            ]
        },
        EvaluationType.COMPARISON: {
            "function_type_id": 4,
            "description_de": "Items paarweise vergleichen (A vs B) - welches ist besser?",
            "description_en": "Compare items pairwise (A vs B) - which is better?",
            "detection_hints": [
                "Zwei Antwort-Versionen pro Item (answer_a/answer_b, text_a/text_b)",
                "conversation_a/conversation_b Paare",
                "winner/preferred Felder für Ground-Truth"
            ],
            "example_use_cases": [
                "LLM-Antworten gegeneinander vergleichen",
                "A/B-Tests von Textvarianten",
                "Präferenz-Studien"
            ]
        },
        EvaluationType.AUTHENTICITY: {
            "function_type_id": 5,
            "description_de": "Echt/Fake erkennen - Mensch vs KI-generiert",
            "description_en": "Detect authentic vs fake - Human vs AI-generated",
            "detection_hints": [
                "is_fake, is_human, synthetic Labels",
                "generated_by, source_type Felder",
                "Binäre Klassifikation Mensch/KI"
            ],
            "example_use_cases": [
                "KI-generierte Texte erkennen",
                "Echte vs. synthetische Nachrichten unterscheiden",
                "Authentizitätsprüfung"
            ]
        },
        EvaluationType.LABELING: {
            "function_type_id": 7,
            "description_de": "Kategorien/Labels zuweisen (binär, multi-class, multi-label)",
            "description_en": "Assign categories/labels (binary, multi-class, multi-label)",
            "detection_hints": [
                "category, label, sentiment Felder",
                "Themen-Klassifikation gewünscht",
                "Mehrklassige Kategorisierung"
            ],
            "example_use_cases": [
                "Sentiment-Analyse (positiv/negativ/neutral)",
                "Themen-Kategorisierung",
                "Dringlichkeits-Einstufung"
            ]
        },
    }

    # =========================================================================
    # Preset Recommendations
    # =========================================================================

    PRESET_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
        "rating": {
            "default": "llm-judge-standard",
            "presets": {
                "llm-judge-standard": "4 Dimensionen (Kohärenz, Flüssigkeit, Relevanz, Konsistenz) - Standard für Textqualität",
                "summeval": "7 Dimensionen mit gemischten Skalen - für detaillierte Analyse",
                "response-quality": "Für LLM-Antworten (Hilfsbereitschaft, Genauigkeit, Vollständigkeit, Klarheit)",
                "news-article": "Für Nachrichtenartikel (Genauigkeit, Objektivität, Vollständigkeit, Lesbarkeit)",
                "text-quality-3dim": "Kompakt mit 3 Dimensionen (Inhalt, Sprache, Struktur)"
            },
            "use_custom_when": [
                "Domänenspezifische Dimensionen nötig (Medizin, Recht, etc.)",
                "Ungewöhnliche Skalengrößen (z.B. 0-100)",
                "Spezielle Gewichtungen erforderlich"
            ]
        },
        "ranking": {
            "default": "buckets-3",
            "presets": {
                "buckets-3": "Gut/Mittel/Schlecht - Standard für Qualitätssortierung",
                "buckets-5": "Sehr gut bis Sehr schlecht - feinere Abstufung",
                "priority": "Items nach Priorität sortieren (1. bis N.)",
                "relevance": "Nach Relevanz sortieren (Ties erlaubt)"
            },
            "use_custom_when": [
                "Andere Kategorie-Namen benötigt",
                "Mehr als 5 Buckets nötig",
                "Spezielle Farben/Icons gewünscht"
            ]
        },
        "labeling": {
            "default": "binary-authentic",
            "presets": {
                "binary-authentic": "Fake/Echt mit Unsicher-Option",
                "binary-sentiment": "Positiv/Negativ mit Neutral",
                "sentiment-3": "Positiv/Neutral/Negativ (3-Klassen)",
                "topic-multilabel": "Mehrere Themen pro Item (Multi-Label)"
            },
            "use_custom_when": [
                "Andere Kategorien als Sentiment/Authentizität",
                "Domänenspezifische Labels",
                "Mehr als 4 Kategorien"
            ]
        },
        "comparison": {
            "default": "pairwise",
            "presets": {
                "pairwise": "A vs B - welches ist besser?",
                "pairwise-confidence": "Mit Konfidenz-Bewertung (1-5)",
                "multicriteria": "Vergleich nach mehreren Kriterien (Relevanz, Qualität, Klarheit)"
            },
            "use_custom_when": [
                "Mehr als 2 Items pro Vergleich",
                "Spezielle Vergleichskriterien",
                "Turnier-Format gewünscht"
            ]
        },
        "mail_rating": {
            "default": "mail-verlauf-bewertung",
            "presets": {
                "mail-verlauf-bewertung": "Kohärenz Klient/Berater + Beratungsqualität + Gesamteignung"
            },
            "use_custom_when": [
                "Andere Dimensionen als Beratungsqualität",
                "Nicht-Beratungskontext"
            ]
        },
        "authenticity": {
            "default": "nachricht-echtheit",
            "presets": {
                "nachricht-echtheit": "Echt/Fake für Beratungsnachrichten",
                "ki-generiert": "Menschlich/KI-generiert Erkennung",
                "dringlichkeit": "Akut/Dringend/Normal/Niedrig (4-Klassen)"
            },
            "use_custom_when": [
                "Andere Labels als Echt/Fake",
                "Zusätzliche Kategorien nötig"
            ]
        }
    }

    # =========================================================================
    # INPUT DATA EXAMPLES (per Evaluation Type)
    # These show concrete examples of data patterns that indicate each type
    # =========================================================================

    INPUT_DATA_EXAMPLES: Dict[str, Dict[str, Any]] = {
        "ranking": {
            "description_de": "Mehrere Items (z.B. Zusammenfassungen) sollen nach Qualität sortiert werden",
            "description_en": "Multiple items (e.g. summaries) should be sorted by quality",
            "pattern_detection": [
                "source_text + summary_a/b/c (Referenztext + mehrere Zusammenfassungen)",
                "reference + item_a/item_b/item_c (Original + Varianten)",
                "Mehrere Felder die verglichen werden sollen"
            ],
            "example_input": {
                "id": "article_1",
                "source_text": "Die Europäische Union hat heute neue Klimaziele beschlossen...",
                "summary_a": "EU beschließt ambitionierte Klimaziele mit CO2-Reduktion um 55%...",
                "summary_b": "EU macht was mit Klima. Ist wichtig für alle.",
                "summary_c": "Die Europäische Union hat auf ihrem Gipfeltreffen..."
            },
            "why_ranking": "Es gibt EINEN Referenztext und MEHRERE Items (summary_a/b/c) die verglichen und sortiert werden sollen",
            "default_config": {
                "type": "buckets",
                "buckets": [
                    {"id": "good", "name": {"de": "Gut", "en": "Good"}, "color": "#98d4bb", "order": 1},
                    {"id": "moderate", "name": {"de": "Moderat", "en": "Moderate"}, "color": "#D1BC8A", "order": 2},
                    {"id": "poor", "name": {"de": "Schlecht", "en": "Poor"}, "color": "#e8a087", "order": 3}
                ],
                "allowTies": True
            }
        },
        "rating": {
            "description_de": "Einzelne Texte/Antworten sollen auf einer Skala bewertet werden",
            "description_en": "Single texts/responses should be rated on a scale",
            "pattern_detection": [
                "question + response (Frage mit einer Antwort)",
                "text + model/source (einzelner Text mit Quelle)",
                "Einzelne Items ohne Vergleichspaare"
            ],
            "example_input": {
                "id": "qa_001",
                "question": "Was ist Machine Learning?",
                "response": "Machine Learning ist ein Teilbereich der künstlichen Intelligenz...",
                "model": "GPT-4",
                "category": "Technologie"
            },
            "why_rating": "Es gibt einzelne Texte/Antworten die UNABHÄNGIG voneinander bewertet werden sollen (nicht verglichen)",
            "default_config": {
                "type": "multi-dimensional",
                "min": 1,
                "max": 5,
                "step": 1,
                "dimensions": [
                    {"id": "coherence", "name": {"de": "Kohärenz", "en": "Coherence"}, "weight": 0.25},
                    {"id": "fluency", "name": {"de": "Flüssigkeit", "en": "Fluency"}, "weight": 0.25},
                    {"id": "relevance", "name": {"de": "Relevanz", "en": "Relevance"}, "weight": 0.25},
                    {"id": "consistency", "name": {"de": "Konsistenz", "en": "Consistency"}, "weight": 0.25}
                ],
                "labels": {"1": {"de": "Sehr schlecht"}, "3": {"de": "Mittel"}, "5": {"de": "Sehr gut"}}
            }
        },
        "comparison": {
            "description_de": "Zwei Versionen direkt gegeneinander vergleichen (A vs B)",
            "description_en": "Compare two versions directly against each other (A vs B)",
            "pattern_detection": [
                "answer_a + answer_b oder text_a + text_b (zwei Versionen)",
                "conversation_a + conversation_b (zwei Dialoge)",
                "model_a + model_b mit winner Feld"
            ],
            "example_input": {
                "id": "cmp_001",
                "question": "Erkläre Quantencomputing",
                "answer_a": "Quantencomputer nutzen Qubits die durch Superposition...",
                "answer_b": "Quantencomputer sind schnelle Computer mit Quanten.",
                "model_a": "GPT-4",
                "model_b": "Mistral-7B"
            },
            "why_comparison": "Es gibt ZWEI Antwort-Versionen (answer_a/answer_b) die DIREKT verglichen werden sollen",
            "default_config": {
                "type": "pairwise",
                "criteria": [{"id": "overall", "name": {"de": "Gesamt", "en": "Overall"}}],
                "allowTie": True
            }
        },
        "mail_rating": {
            "description_de": "E-Mail-Konversationen (Klient-Berater) bewerten",
            "description_en": "Rate email conversations (client-counselor)",
            "pattern_detection": [
                "subject + messages[] (E-Mail-Thread)",
                "Konversation mit user/assistant oder Klient/Berater Rollen",
                "Beratungskontext erkennbar",
                "WICHTIG: NUR wenn KEIN is_human/is_fake Feld vorhanden ist!"
            ],
            "example_input": {
                "id": "thread_001",
                "subject": "Beratungsanfrage",
                "messages": [
                    {"role": "user", "content": "Hallo, ich habe ein Problem und brauche Hilfe..."},
                    {"role": "assistant", "content": "Vielen Dank für Ihre Nachricht. Ich verstehe..."}
                ]
            },
            "why_mail_rating": "Es sind KONVERSATIONEN mit messages-Array OHNE is_human/is_fake Feld. Wenn is_human/is_fake existiert → authenticity!",
            "default_config": {
                "type": "multi-dimensional",
                "min": 1,
                "max": 5,
                "dimensions": [
                    {"id": "client_coherence", "name": {"de": "Kohärenz Klient", "en": "Client Coherence"}, "weight": 0.25},
                    {"id": "counsellor_coherence", "name": {"de": "Kohärenz Berater", "en": "Counsellor Coherence"}, "weight": 0.25},
                    {"id": "quality", "name": {"de": "Beratungsqualität", "en": "Counseling Quality"}, "weight": 0.25},
                    {"id": "overall", "name": {"de": "Gesamteignung", "en": "Overall Suitability"}, "weight": 0.25}
                ]
            }
        },
        "authenticity": {
            "description_de": "Echt vs. Fake erkennen (Mensch vs. KI-generiert)",
            "description_en": "Detect authentic vs. fake (Human vs. AI-generated)",
            "pattern_detection": [
                "is_human, is_fake, synthetic Felder vorhanden → IMMER authenticity!",
                "Hat VORRANG vor messages[] Struktur!",
                "Konversation MIT is_human/is_fake = authenticity (NICHT mail_rating!)",
                "Binäre Klassifikation Mensch/KI"
            ],
            "example_input": {
                "id": "auth_001",
                "subject": "Beratungsanfrage",
                "messages": [
                    {"role": "user", "content": "Hallo, ich brauche dringend Hilfe..."},
                    {"role": "assistant", "content": "Vielen Dank für Ihre Nachricht..."}
                ],
                "is_human": True,
                "source": "human"
            },
            "why_authenticity": "OBWOHL es eine Konversation mit messages[] ist, existiert das Feld 'is_human' - das bedeutet IMMER authenticity! Das is_human/is_fake Feld hat VORRANG vor allem anderen.",
            "default_config": {
                "type": "binary",
                "categories": [
                    {"id": "authentic", "name": {"de": "Echt", "en": "Authentic"}, "color": "#98d4bb"},
                    {"id": "fake", "name": {"de": "Fake", "en": "Fake"}, "color": "#e8a087"}
                ],
                "allowUnsure": True
            }
        },
        "labeling": {
            "description_de": "Kategorien/Labels zuweisen (Sentiment, Thema, etc.)",
            "description_en": "Assign categories/labels (sentiment, topic, etc.)",
            "pattern_detection": [
                "sentiment, category, label, topic Felder",
                "Mehrklassige Kategorisierung (nicht nur binär)",
                "Themen- oder Sentiment-Analyse"
            ],
            "example_input": {
                "id": "label_001",
                "text": "Das Produkt ist absolut fantastisch! Sehr zufrieden.",
                "sentiment": "positive"
            },
            "why_labeling": "Es gibt KATEGORISCHE Labels (sentiment, topic) die auf MEHRKLASSIGE Klassifikation hindeuten",
            "default_config": {
                "type": "multiclass",
                "categories": [
                    {"id": "positive", "name": {"de": "Positiv", "en": "Positive"}, "color": "#98d4bb"},
                    {"id": "neutral", "name": {"de": "Neutral", "en": "Neutral"}, "color": "#D1BC8A"},
                    {"id": "negative", "name": {"de": "Negativ", "en": "Negative"}, "color": "#e8a087"}
                ],
                "allowUnsure": True
            }
        }
    }

    # =========================================================================
    # File Format Mapping Examples
    # =========================================================================

    FILE_FORMAT_EXAMPLES: Dict[str, Dict[str, str]] = {
        "csv_comparison": {
            "description": "CSV mit Vergleichsdaten (zwei Antworten pro Frage)",
            "input": '''id,question,answer_a,answer_b,model_a,model_b
1,"Was ist Python?","Python ist eine...","Python ist eine interpretierte...","gpt-4","claude-3"
2,"Erkläre ML","ML steht für...","Machine Learning ist...","gpt-4","claude-3"''',
            "detection": "Spalten answer_a/answer_b oder text_a/text_b → comparison",
            "mapping": "id→item_id, question→reference.content, answer_a→items[0].content, answer_b→items[1].content, model_a→items[0].source.name"
        },
        "csv_single": {
            "description": "CSV mit einzelnen Texten zur Bewertung",
            "input": '''id,text,source,category
1,"Der Artikel handelt von...","gpt-4","news"
2,"Zusammenfassung des Events...","claude-3","summary"''',
            "detection": "Einzelne text-Spalte ohne Paarung → rating oder ranking",
            "mapping": "id→item_id, text→content, source→source.name"
        },
        "json_conversation": {
            "description": "JSON mit Konversationen",
            "input": '''{
  "items": [
    {
      "id": "conv_1",
      "subject": "Beratungsanfrage",
      "messages": [
        {"role": "user", "content": "Ich habe ein Problem..."},
        {"role": "assistant", "content": "Vielen Dank für Ihre Nachricht..."}
      ]
    }
  ]
}''',
            "detection": "messages Array mit role/content → mail_rating oder rating",
            "mapping": "id→item_id, subject→reference.label, messages→conversation"
        },
        "json_openai": {
            "description": "OpenAI/LMSYS Comparison Format",
            "input": '''{
  "conversation_a": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}],
  "conversation_b": [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hi there!"}],
  "model_a": "gpt-4",
  "model_b": "claude-3",
  "winner": "model_a"
}''',
            "detection": "conversation_a/conversation_b mit winner → comparison",
            "mapping": "conversation_a→items[0].content, model_a→items[0].source.name, winner→ground_truth"
        },
        "jsonl_labeled": {
            "description": "JSONL mit Labels (eine JSON pro Zeile)",
            "input": '''{"id": "1", "text": "Das ist ein toller Artikel!", "sentiment": "positive"}
{"id": "2", "text": "Schlechte Qualität...", "sentiment": "negative"}''',
            "detection": "sentiment/category/label Felder → labeling",
            "mapping": "id→item_id, text→content, sentiment→ground_truth"
        },
        "jsonl_authenticity": {
            "description": "JSONL für Authentizitätserkennung",
            "input": '''{"id": "1", "text": "Hallo, ich brauche Hilfe...", "is_human": true}
{"id": "2", "text": "Guten Tag, wie kann ich...", "is_human": false, "model": "gpt-4"}''',
            "detection": "is_human/is_fake/synthetic Felder → authenticity",
            "mapping": "id→item_id, text→content, is_human→ground_truth, model→source.name"
        }
    }

    # =========================================================================
    # Public API Methods
    # =========================================================================

    @classmethod
    def get_schema_for_ai_prompt(cls) -> str:
        """
        Generiert die komplette Schema-Beschreibung für den AI-Prompt.

        Kombiniert alle Schema-Informationen in einem strukturierten Format,
        das die AI für Datenanalyse und Mapping verwenden kann.

        Returns:
            Formatierter String mit Schema-Dokumentation für AI-Prompt
        """
        sections = [
            cls._get_header(),
            cls.get_evaluation_types_description(),
            cls._get_decision_tree(),
            cls.get_input_data_examples(),  # NEU: Konkrete Eingabedaten-Beispiele
            cls.get_file_format_examples(),
            cls.get_preset_recommendations(),
            cls._get_target_format(),
        ]
        return "\n\n".join(sections)

    @classmethod
    def get_evaluation_types_description(cls) -> str:
        """
        Generiert Beschreibung aller Evaluationstypen aus dem zentralen Schema.

        Returns:
            Formatierte Tabelle mit Typen, IDs und Beschreibungen
        """
        lines = ["## EVALUATIONSTYPEN (aus zentralem Schema)\n"]
        lines.append("| Typ | ID | Beschreibung | Erkennung |")
        lines.append("|-----|----|--------------| ----------|")

        for eval_type, info in cls.EVALUATION_TYPE_INFO.items():
            hints = "; ".join(info["detection_hints"][:2])
            lines.append(
                f"| {eval_type.value} | {info['function_type_id']} | "
                f"{info['description_de']} | {hints} |"
            )

        return "\n".join(lines)

    @classmethod
    def get_input_data_examples(cls) -> str:
        """
        Generiert konkrete INPUT-Datenbeispiele für jeden Evaluationstyp.

        Diese Beispiele zeigen der KI, wie typische Eingabedaten für jeden
        Evaluationstyp aussehen, sodass sie das Muster erkennen kann.

        Returns:
            Formatierte Beispiele mit Pattern-Detection und Default-Config
        """
        lines = ["## KONKRETE EINGABEDATEN-BEISPIELE\n"]
        lines.append("Die folgenden Beispiele zeigen typische Eingabedaten für jeden Evaluationstyp.\n")
        lines.append("**WICHTIG:** Erkenne das Muster in den Eingabedaten um den richtigen Typ zu wählen!\n")

        for eval_type, info in cls.INPUT_DATA_EXAMPLES.items():
            lines.append(f"### {eval_type.upper()}")
            lines.append(f"**Beschreibung:** {info['description_de']}\n")

            lines.append("**Pattern-Erkennung:**")
            for pattern in info['pattern_detection']:
                lines.append(f"- {pattern}")

            lines.append("\n**Beispiel-Eingabedaten:**")
            lines.append("```json")
            lines.append(json.dumps(info['example_input'], indent=2, ensure_ascii=False))
            lines.append("```")

            lines.append(f"\n**Warum {eval_type}?** {info['why_' + eval_type]}\n")

            lines.append("**Standard-Konfiguration:**")
            lines.append("```json")
            lines.append(json.dumps(info['default_config'], indent=2, ensure_ascii=False))
            lines.append("```\n")

            lines.append("---\n")

        return "\n".join(lines)

    @classmethod
    def get_file_format_examples(cls) -> str:
        """
        Generiert Mapping-Beispiele für verschiedene Dateiformate.

        Returns:
            Formatierte Beispiele für CSV, JSON, JSONL
        """
        lines = ["## DATEIFORMAT MAPPING-BEISPIELE\n"]

        for format_key, example in cls.FILE_FORMAT_EXAMPLES.items():
            lines.append(f"### {example['description']}")
            lines.append("```")
            lines.append(example["input"])
            lines.append("```")
            lines.append(f"**Erkennung:** {example['detection']}")
            lines.append(f"**Mapping:** {example['mapping']}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def get_preset_recommendations(cls) -> str:
        """
        Generiert Preset-Empfehlungen für alle Evaluationstypen.

        Returns:
            Formatierte Empfehlungen wann Standard vs Custom
        """
        lines = ["## PRESET-EMPFEHLUNGEN\n"]
        lines.append("Nutze Standard-Presets wenn möglich. Custom nur bei besonderen Anforderungen.\n")

        for eval_type, info in cls.PRESET_RECOMMENDATIONS.items():
            lines.append(f"### {eval_type.upper()}")
            lines.append(f"**Standard:** `{info['default']}`\n")

            for preset_id, desc in info["presets"].items():
                marker = "(DEFAULT)" if preset_id == info["default"] else ""
                lines.append(f"- `{preset_id}`: {desc} {marker}")

            lines.append("\n**Nutze Custom-Config wenn:**")
            for reason in info["use_custom_when"]:
                lines.append(f"- {reason}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def get_default_config_json(cls, eval_type: str) -> Dict[str, Any]:
        """
        Gibt die Standard-Konfiguration für einen Evaluationstyp zurück.

        Args:
            eval_type: Evaluationstyp als String (z.B. "rating", "ranking")

        Returns:
            Dictionary mit Standard-Konfiguration
        """
        if eval_type == "rating":
            dimensions = create_default_rating_dimensions()
            scale = create_default_scale()
            return {
                "type": "multi-dimensional",
                "min": scale.min,
                "max": scale.max,
                "step": scale.step,
                "dimensions": [
                    {
                        "id": d.id,
                        "name": {"de": d.label.de, "en": d.label.en},
                        "weight": d.weight
                    }
                    for d in dimensions
                ],
                "labels": {
                    str(k): {"de": v.de, "en": v.en}
                    for k, v in (scale.labels or {}).items()
                }
            }

        if eval_type == "ranking":
            buckets = create_default_ranking_buckets()
            return {
                "type": "buckets",
                "buckets": [
                    {
                        "id": b.id,
                        "name": {"de": b.label.de, "en": b.label.en},
                        "color": b.color,
                        "order": b.order
                    }
                    for b in buckets
                ],
                "allowTies": True
            }

        if eval_type == "labeling":
            return {
                "type": "multiclass",
                "categories": [
                    {"id": "cat_1", "name": {"de": "Kategorie 1", "en": "Category 1"}},
                    {"id": "cat_2", "name": {"de": "Kategorie 2", "en": "Category 2"}}
                ],
                "allowUnsure": True
            }

        if eval_type == "comparison":
            return {
                "type": "pairwise",
                "criteria": [{"id": "overall", "name": {"de": "Gesamt", "en": "Overall"}}],
                "allowTie": True
            }

        if eval_type == "authenticity":
            return {
                "type": "binary",
                "categories": [
                    {"id": "authentic", "name": {"de": "Echt", "en": "Authentic"}, "color": "#98d4bb"},
                    {"id": "fake", "name": {"de": "Fake", "en": "Fake"}, "color": "#e8a087"}
                ],
                "allowUnsure": True
            }

        if eval_type == "mail_rating":
            return {
                "type": "multi-dimensional",
                "dimensions": [
                    {"id": "client_coherence", "name": {"de": "Kohärenz Klient", "en": "Client Coherence"}, "weight": 0.25},
                    {"id": "counsellor_coherence", "name": {"de": "Kohärenz Berater", "en": "Counsellor Coherence"}, "weight": 0.25},
                    {"id": "quality", "name": {"de": "Beratungsqualität", "en": "Counseling Quality"}, "weight": 0.25},
                    {"id": "overall", "name": {"de": "Gesamteignung", "en": "Overall Suitability"}, "weight": 0.25}
                ],
                "min": 1,
                "max": 5
            }

        return {}

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    @classmethod
    def _get_header(cls) -> str:
        """Generiert den Header für den AI-Prompt."""
        return """Du bist ein Experte für Evaluations-Studiendesign. Analysiere die bereitgestellten Daten
und generiere Vorschläge für ein LLARS-Evaluationsszenario.

Die folgenden Schema-Informationen stammen direkt aus dem zentralen LLARS-Schema
(app/schemas/evaluation_data_schemas.py) und sind die Ground Truth für alle Datenformate."""

    @classmethod
    def _get_decision_tree(cls) -> str:
        """Generiert den Entscheidungsbaum für Evaluationstyp-Auswahl."""
        return """## ENTSCHEIDUNGSBAUM FÜR EVALUATIONSTYP

**WICHTIG: Prüfe die Felder in dieser REIHENFOLGE!**

```
┌─ SCHRITT 1: Gibt es is_human oder is_fake Felder?
│  │  (HÖCHSTE PRIORITÄT - egal ob messages[] existiert!)
│  │
│  └─ JA → authenticity (IMMER, auch bei Konversationen!)
│
├─ SCHRITT 2: Haben die Daten ZWEI Antwort-Versionen pro Item?
│  │  (answer_a/answer_b, text_a/text_b, conversation_a/b)
│  │
│  └─ JA → comparison
│
├─ SCHRITT 3: Gibt es sentiment/category/topic/label Felder?
│  │  (NICHT is_human/is_fake - die sind authenticity!)
│  │
│  └─ JA → labeling
│
├─ SCHRITT 4: Gibt es source_text + summary_a/b/c Muster?
│  │  (Referenztext + mehrere Varianten)
│  │
│  └─ JA → ranking
│
├─ SCHRITT 5: Gibt es messages[] Array OHNE is_human/is_fake?
│  │  (Konversationen zur Qualitätsbewertung)
│  │
│  └─ JA → mail_rating
│
└─ SCHRITT 6: Einzelne Texte/Antworten
   │
   └─ → rating
```

**KRITISCHE REGEL:**
- is_human/is_fake Feld = IMMER authenticity (egal ob messages[] existiert!)
- messages[] OHNE is_human = mail_rating
- messages[] MIT is_human = authenticity"""

    @classmethod
    def _get_target_format(cls) -> str:
        """Generiert die Zielformat-Beschreibung."""
        return """## LLARS ZIELFORMAT (EvaluationData Schema)

Das Zielformat basiert auf dem Pydantic-Schema `EvaluationData`:

```json
{
  "schema_version": "1.0",
  "type": "rating|ranking|labeling|comparison|mail_rating|authenticity",
  "reference": {
    "type": "text|conversation",
    "label": "Original-Artikel",
    "content": "..."
  },
  "items": [
    {
      "id": "item_1",
      "label": "Zusammenfassung 1",
      "source": {"type": "llm|human|unknown", "name": "gpt-4"},
      "content": "...",
      "group": null
    }
  ],
  "config": {
    // Typ-spezifische Konfiguration - siehe Presets
  },
  "ground_truth": null
}
```

**Wichtige Konventionen:**
- `item.id`: Technische ID ("item_1") - NIEMALS LLM-Namen!
- `item.label`: UI-Anzeigename (generisch: "Zusammenfassung 1", "Antwort A")
- `item.source.type`: "human" | "llm" | "unknown"
- `item.source.name`: Bei LLM der Modell-Name (z.B. "gpt-4", "claude-3")
- `reference`: Kontext/Original das bewertet wird (optional)"""
