"""
Rating Preset Service.

Manages rating presets for multi-dimensional evaluation.
Provides preset configurations for various evaluation use cases:
- Standard Likert scales
- LLM-as-Judge metrics
- Mail/Counseling evaluation (LLARS-specific)
- Custom presets

Synced with frontend evaluationPresets.js for consistency.
"""

import logging
from typing import Dict, List, Optional, Any
from copy import deepcopy

logger = logging.getLogger(__name__)


# =============================================================================
# Standard Rating Presets
# =============================================================================

STANDARD_PRESETS = {
    'likert-5': {
        'id': 'likert-5',
        'name': {'de': 'Likert-5', 'en': 'Likert-5'},
        'description': {'de': '5-Punkte Likert-Skala (Standard)', 'en': '5-point Likert scale (Standard)'},
        'category': 'standard',
        'config': {
            'type': 'likert',
            'min': 1,
            'max': 5,
            'step': 1,
            'labels': {
                '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
                '2': {'de': 'Schlecht', 'en': 'Poor'},
                '3': {'de': 'Akzeptabel', 'en': 'Acceptable'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            },
            'showLabels': True,
            'dimensions': []
        }
    },
    'likert-7': {
        'id': 'likert-7',
        'name': {'de': 'Likert-7', 'en': 'Likert-7'},
        'description': {'de': '7-Punkte Likert-Skala', 'en': '7-point Likert scale'},
        'category': 'standard',
        'config': {
            'type': 'likert',
            'min': 1,
            'max': 7,
            'step': 1,
            'labels': {
                '1': {'de': 'Stimme gar nicht zu', 'en': 'Strongly disagree'},
                '2': {'de': 'Stimme nicht zu', 'en': 'Disagree'},
                '3': {'de': 'Stimme eher nicht zu', 'en': 'Somewhat disagree'},
                '4': {'de': 'Neutral', 'en': 'Neutral'},
                '5': {'de': 'Stimme eher zu', 'en': 'Somewhat agree'},
                '6': {'de': 'Stimme zu', 'en': 'Agree'},
                '7': {'de': 'Stimme voll zu', 'en': 'Strongly agree'}
            },
            'showLabels': True,
            'dimensions': []
        }
    },
    'binary-0-1': {
        'id': 'binary-0-1',
        'name': {'de': 'Binär (0-1)', 'en': 'Binary (0-1)'},
        'description': {'de': 'Einfache Ja/Nein-Bewertung', 'en': 'Simple Yes/No rating'},
        'category': 'standard',
        'config': {
            'type': 'binary',
            'min': 0,
            'max': 1,
            'step': 1,
            'labels': {
                '0': {'de': 'Nein', 'en': 'No'},
                '1': {'de': 'Ja', 'en': 'Yes'}
            },
            'showLabels': True,
            'dimensions': []
        }
    },
    'four-point-0-3': {
        'id': 'four-point-0-3',
        'name': {'de': '4-Punkte (0-3)', 'en': '4-Point (0-3)'},
        'description': {'de': '4-Punkte Skala mit Null', 'en': '4-point scale starting at zero'},
        'category': 'standard',
        'config': {
            'type': 'likert',
            'min': 0,
            'max': 3,
            'step': 1,
            'labels': {
                '0': {'de': 'Nicht vorhanden', 'en': 'Not present'},
                '1': {'de': 'Schwach', 'en': 'Weak'},
                '2': {'de': 'Gut', 'en': 'Good'},
                '3': {'de': 'Ausgezeichnet', 'en': 'Excellent'}
            },
            'showLabels': True,
            'dimensions': []
        }
    },
    'ten-point-0-9': {
        'id': 'ten-point-0-9',
        'name': {'de': '10-Punkte (0-9)', 'en': '10-Point (0-9)'},
        'description': {'de': '10-Punkte Skala für feine Abstufung', 'en': '10-point scale for fine granularity'},
        'category': 'standard',
        'config': {
            'type': 'numeric',
            'min': 0,
            'max': 9,
            'step': 1,
            'labels': {
                '0': {'de': 'Inakzeptabel', 'en': 'Unacceptable'},
                '5': {'de': 'Akzeptabel', 'en': 'Acceptable'},
                '9': {'de': 'Herausragend', 'en': 'Outstanding'}
            },
            'showLabels': True,
            'dimensions': []
        }
    },
    'ten-point-1-10': {
        'id': 'ten-point-1-10',
        'name': {'de': '10-Punkte (1-10)', 'en': '10-Point (1-10)'},
        'description': {'de': '10-Punkte Skala (1-basiert)', 'en': '10-point scale (1-based)'},
        'category': 'standard',
        'config': {
            'type': 'numeric',
            'min': 1,
            'max': 10,
            'step': 1,
            'labels': {
                '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
                '5': {'de': 'Durchschnittlich', 'en': 'Average'},
                '10': {'de': 'Ausgezeichnet', 'en': 'Excellent'}
            },
            'showLabels': True,
            'dimensions': []
        }
    }
}


# =============================================================================
# LLM-as-Judge Presets (Multi-Dimensional)
# =============================================================================

LLM_JUDGE_PRESETS = {
    'llm-judge-standard': {
        'id': 'llm-judge-standard',
        'name': {'de': 'LLM-as-Judge Standard', 'en': 'LLM-as-Judge Standard'},
        'description': {
            'de': 'Standard-Metriken für Text-Evaluation (Coherence, Fluency, Relevance, Consistency)',
            'en': 'Standard metrics for text evaluation (Coherence, Fluency, Relevance, Consistency)'
        },
        'category': 'llm-judge',
        'config': {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {
                    'id': 'coherence',
                    'name': {'de': 'Kohärenz', 'en': 'Coherence'},
                    'description': {'de': 'Logischer Aufbau und Zusammenhang', 'en': 'Logical structure and flow'},
                    'weight': 0.25,
                    'prompt_hint': 'Bewerte den logischen Aufbau und die Verknüpfung der Ideen'
                },
                {
                    'id': 'fluency',
                    'name': {'de': 'Flüssigkeit', 'en': 'Fluency'},
                    'description': {'de': 'Sprachliche Qualität und Lesbarkeit', 'en': 'Language quality and readability'},
                    'weight': 0.25,
                    'prompt_hint': 'Bewerte Grammatik, Stil und allgemeine Lesbarkeit'
                },
                {
                    'id': 'relevance',
                    'name': {'de': 'Relevanz', 'en': 'Relevance'},
                    'description': {'de': 'Bezug zum Thema/Kontext', 'en': 'Topic and context relevance'},
                    'weight': 0.25,
                    'prompt_hint': 'Bewerte wie relevant der Inhalt für das Thema ist'
                },
                {
                    'id': 'consistency',
                    'name': {'de': 'Konsistenz', 'en': 'Consistency'},
                    'description': {'de': 'Widerspruchsfreiheit und Faktentreue', 'en': 'Factual consistency'},
                    'weight': 0.25,
                    'prompt_hint': 'Bewerte die faktische Korrektheit und Widerspruchsfreiheit'
                }
            ],
            'labels': {
                '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
                '2': {'de': 'Schlecht', 'en': 'Poor'},
                '3': {'de': 'Akzeptabel', 'en': 'Acceptable'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            },
            'showOverallScore': True,
            'allowFeedback': True
        }
    },
    'summeval': {
        'id': 'summeval',
        'name': {'de': 'SummEval', 'en': 'SummEval'},
        'description': {
            'de': 'Metriken aus dem SummEval-Benchmark für Zusammenfassungen',
            'en': 'Metrics from the SummEval benchmark for summarization'
        },
        'category': 'llm-judge',
        'config': {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {
                    'id': 'coherence',
                    'name': {'de': 'Kohärenz', 'en': 'Coherence'},
                    'description': {'de': 'Logischer Aufbau und strukturelle Qualität', 'en': 'Logical structure and flow'},
                    'weight': 0.25
                },
                {
                    'id': 'consistency',
                    'name': {'de': 'Konsistenz', 'en': 'Consistency'},
                    'description': {'de': 'Faktische Übereinstimmung mit dem Quelltext', 'en': 'Factual alignment with source'},
                    'weight': 0.25
                },
                {
                    'id': 'fluency',
                    'name': {'de': 'Flüssigkeit', 'en': 'Fluency'},
                    'description': {'de': 'Grammatik, Lesbarkeit, Sprachqualität', 'en': 'Grammar, readability, language quality'},
                    'weight': 0.25
                },
                {
                    'id': 'relevance',
                    'name': {'de': 'Relevanz', 'en': 'Relevance'},
                    'description': {'de': 'Wichtige Informationen aus dem Quelltext', 'en': 'Important information from source'},
                    'weight': 0.25
                }
            ],
            'labels': {
                '1': {'de': 'Sehr schlecht', 'en': 'Very poor'},
                '2': {'de': 'Schlecht', 'en': 'Poor'},
                '3': {'de': 'Akzeptabel', 'en': 'Acceptable'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            },
            'showOverallScore': True,
            'allowFeedback': False
        }
    },
    'response-quality': {
        'id': 'response-quality',
        'name': {'de': 'Antwort-Qualität', 'en': 'Response Quality'},
        'description': {
            'de': 'Bewertung von LLM-generierten Antworten auf Nutzerfragen',
            'en': 'Rating of LLM-generated responses to user questions'
        },
        'category': 'llm-judge',
        'config': {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {
                    'id': 'helpfulness',
                    'name': {'de': 'Hilfsbereitschaft', 'en': 'Helpfulness'},
                    'description': {'de': 'Wie nützlich ist die Antwort für den Nutzer?', 'en': 'How useful is the answer for the user?'},
                    'weight': 0.30
                },
                {
                    'id': 'accuracy',
                    'name': {'de': 'Genauigkeit', 'en': 'Accuracy'},
                    'description': {'de': 'Faktische Korrektheit der Informationen', 'en': 'Factual correctness of information'},
                    'weight': 0.30
                },
                {
                    'id': 'completeness',
                    'name': {'de': 'Vollständigkeit', 'en': 'Completeness'},
                    'description': {'de': 'Werden alle relevanten Aspekte abgedeckt?', 'en': 'Are all relevant aspects covered?'},
                    'weight': 0.20
                },
                {
                    'id': 'clarity',
                    'name': {'de': 'Klarheit', 'en': 'Clarity'},
                    'description': {'de': 'Verständlichkeit und Strukturiertheit', 'en': 'Understandability and structure'},
                    'weight': 0.20
                }
            ],
            'labels': {
                '1': {'de': 'Unzureichend', 'en': 'Insufficient'},
                '2': {'de': 'Mangelhaft', 'en': 'Poor'},
                '3': {'de': 'Befriedigend', 'en': 'Satisfactory'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Ausgezeichnet', 'en': 'Excellent'}
            },
            'showOverallScore': True,
            'allowFeedback': True
        }
    }
}


# =============================================================================
# Mail/Counseling Presets (LLARS-specific)
# =============================================================================

MAIL_RATING_PRESETS = {
    'beratungsqualitaet': {
        'id': 'beratungsqualitaet',
        'name': {'de': 'Beratungsqualität', 'en': 'Counseling Quality'},
        'description': {
            'de': 'Mehrdimensionale Bewertung der Beratungsqualität in E-Mail-Konversationen',
            'en': 'Multi-dimensional rating of counseling quality in email conversations'
        },
        'category': 'mail',
        'llarsSpecific': True,
        'config': {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {
                    'id': 'empathie',
                    'name': {'de': 'Empathie', 'en': 'Empathy'},
                    'description': {'de': 'Einfühlungsvermögen und emotionale Resonanz', 'en': 'Empathy and emotional resonance'},
                    'weight': 0.25,
                    'prompt_hint': 'Bewerte wie gut der Berater auf die emotionalen Bedürfnisse eingeht'
                },
                {
                    'id': 'klarheit',
                    'name': {'de': 'Klarheit', 'en': 'Clarity'},
                    'description': {'de': 'Verständlichkeit und Strukturiertheit der Antwort', 'en': 'Clarity and structure of response'},
                    'weight': 0.20,
                    'prompt_hint': 'Bewerte wie klar und strukturiert die Antwort formuliert ist'
                },
                {
                    'id': 'professionalitaet',
                    'name': {'de': 'Professionalität', 'en': 'Professionalism'},
                    'description': {'de': 'Fachliche Kompetenz und angemessene Sprache', 'en': 'Professional competence and appropriate language'},
                    'weight': 0.20,
                    'prompt_hint': 'Bewerte die fachliche Qualität und angemessene Ausdrucksweise'
                },
                {
                    'id': 'hilfsbereitschaft',
                    'name': {'de': 'Hilfsbereitschaft', 'en': 'Helpfulness'},
                    'description': {'de': 'Konkrete Unterstützungsangebote und Handlungsvorschläge', 'en': 'Concrete support offers and action suggestions'},
                    'weight': 0.20,
                    'prompt_hint': 'Bewerte wie hilfreich die konkreten Vorschläge und Angebote sind'
                },
                {
                    'id': 'angemessenheit',
                    'name': {'de': 'Angemessenheit', 'en': 'Appropriateness'},
                    'description': {'de': 'Passung der Antwort zur Anfrage', 'en': 'Fit of response to inquiry'},
                    'weight': 0.15,
                    'prompt_hint': 'Bewerte wie gut die Antwort zur ursprünglichen Anfrage passt'
                }
            ],
            'labels': {
                '1': {'de': 'Unzureichend', 'en': 'Insufficient'},
                '2': {'de': 'Mangelhaft', 'en': 'Poor'},
                '3': {'de': 'Befriedigend', 'en': 'Satisfactory'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            },
            'showOverallScore': True,
            'allowFeedback': True
        }
    },
    'antwortqualitaet': {
        'id': 'antwortqualitaet',
        'name': {'de': 'Antwortqualität', 'en': 'Response Quality'},
        'description': {
            'de': 'Bewertung der Qualität einzelner Beraterantworten',
            'en': 'Rating of individual counselor responses'
        },
        'category': 'mail',
        'llarsSpecific': True,
        'config': {
            'type': 'multi-dimensional',
            'min': 1,
            'max': 5,
            'step': 1,
            'dimensions': [
                {
                    'id': 'inhalt',
                    'name': {'de': 'Inhaltliche Qualität', 'en': 'Content Quality'},
                    'description': {'de': 'Relevanz und Nützlichkeit des Inhalts', 'en': 'Relevance and usefulness of content'},
                    'weight': 0.35
                },
                {
                    'id': 'struktur',
                    'name': {'de': 'Struktur', 'en': 'Structure'},
                    'description': {'de': 'Logischer Aufbau und Gliederung', 'en': 'Logical structure and organization'},
                    'weight': 0.25
                },
                {
                    'id': 'ton',
                    'name': {'de': 'Tonalität', 'en': 'Tone'},
                    'description': {'de': 'Angemessener und respektvoller Umgangston', 'en': 'Appropriate and respectful tone'},
                    'weight': 0.25
                },
                {
                    'id': 'vollstaendigkeit',
                    'name': {'de': 'Vollständigkeit', 'en': 'Completeness'},
                    'description': {'de': 'Alle relevanten Aspekte werden angesprochen', 'en': 'All relevant aspects are addressed'},
                    'weight': 0.15
                }
            ],
            'labels': {
                '1': {'de': 'Unzureichend', 'en': 'Insufficient'},
                '2': {'de': 'Mangelhaft', 'en': 'Poor'},
                '3': {'de': 'Befriedigend', 'en': 'Satisfactory'},
                '4': {'de': 'Gut', 'en': 'Good'},
                '5': {'de': 'Sehr gut', 'en': 'Very good'}
            },
            'showOverallScore': True,
            'allowFeedback': True
        }
    }
}


# =============================================================================
# All Presets Combined
# =============================================================================

ALL_PRESETS = {
    **STANDARD_PRESETS,
    **LLM_JUDGE_PRESETS,
    **MAIL_RATING_PRESETS
}

# Category definitions
CATEGORIES = {
    'standard': {
        'id': 'standard',
        'name': {'de': 'Standard-Skalen', 'en': 'Standard Scales'},
        'description': {'de': 'Einfache Likert- und numerische Skalen', 'en': 'Simple Likert and numeric scales'},
        'icon': 'mdi-numeric'
    },
    'llm-judge': {
        'id': 'llm-judge',
        'name': {'de': 'LLM-as-Judge', 'en': 'LLM-as-Judge'},
        'description': {'de': 'Multi-dimensionale Metriken für LLM-Evaluation', 'en': 'Multi-dimensional metrics for LLM evaluation'},
        'icon': 'mdi-robot'
    },
    'mail': {
        'id': 'mail',
        'name': {'de': 'Mail/Beratung', 'en': 'Mail/Counseling'},
        'description': {'de': 'Spezialisierte Bewertung für E-Mail-Beratung', 'en': 'Specialized rating for email counseling'},
        'icon': 'mdi-email-check'
    }
}


class RatingPresetService:
    """Service for managing rating presets."""

    @staticmethod
    def get_all_presets() -> List[Dict]:
        """
        Get all available presets.

        Returns:
            List of preset dictionaries
        """
        return list(deepcopy(ALL_PRESETS).values())

    @staticmethod
    def get_preset(preset_id: str) -> Optional[Dict]:
        """
        Get a specific preset by ID.

        Args:
            preset_id: Preset ID

        Returns:
            Preset dictionary or None if not found
        """
        preset = ALL_PRESETS.get(preset_id)
        return deepcopy(preset) if preset else None

    @staticmethod
    def get_presets_by_category(category: str) -> List[Dict]:
        """
        Get presets filtered by category.

        Args:
            category: Category ID ('standard', 'llm-judge', 'mail')

        Returns:
            List of presets in the category
        """
        return [
            deepcopy(preset)
            for preset in ALL_PRESETS.values()
            if preset.get('category') == category
        ]

    @staticmethod
    def get_categories() -> List[Dict]:
        """
        Get all category definitions.

        Returns:
            List of category dictionaries
        """
        return list(CATEGORIES.values())

    @staticmethod
    def get_presets_for_type(eval_type: str) -> List[Dict]:
        """
        Get presets suitable for an evaluation type.

        Args:
            eval_type: Evaluation type ('rating', 'mail_rating')

        Returns:
            List of suitable presets
        """
        if eval_type == 'mail_rating':
            # Return mail presets + general rating presets
            return RatingPresetService.get_presets_by_category('mail') + \
                   RatingPresetService.get_presets_by_category('llm-judge')
        elif eval_type == 'rating':
            # Return all presets
            return RatingPresetService.get_all_presets()
        else:
            return RatingPresetService.get_all_presets()

    @staticmethod
    def validate_config(config: Dict) -> Dict[str, Any]:
        """
        Validate a rating configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Dictionary with 'valid' boolean and 'errors' list
        """
        errors = []

        if not config:
            errors.append('Configuration is required')
            return {'valid': False, 'errors': errors}

        # Validate scale range
        min_val = config.get('min')
        max_val = config.get('max')

        if min_val is None:
            errors.append('min value is required')
        if max_val is None:
            errors.append('max value is required')

        if min_val is not None and max_val is not None:
            if min_val >= max_val:
                errors.append('min must be less than max')
            if max_val - min_val > 100:
                errors.append('Scale range exceeds maximum (100)')

        step = config.get('step', 1)
        if step <= 0:
            errors.append('step must be positive')

        # Validate dimensions if multi-dimensional
        if config.get('type') == 'multi-dimensional':
            dimensions = config.get('dimensions', [])
            if not dimensions:
                errors.append('At least one dimension is required for multi-dimensional rating')
            else:
                total_weight = sum(d.get('weight', 0) for d in dimensions)
                if abs(total_weight - 1.0) > 0.01:
                    errors.append(f'Dimension weights should sum to 1.0 (current: {total_weight:.2f})')

                for dim in dimensions:
                    if not dim.get('id'):
                        errors.append('Each dimension must have an id')
                    if not dim.get('name'):
                        errors.append(f"Dimension {dim.get('id', '?')} must have a name")

        return {'valid': len(errors) == 0, 'errors': errors}

    @staticmethod
    def get_mail_rating_presets() -> List[Dict]:
        """
        Get presets specifically for mail rating.

        Returns:
            List of mail rating presets
        """
        return RatingPresetService.get_presets_by_category('mail')

    @staticmethod
    def get_dimension_template() -> Dict:
        """
        Get a template for creating a new dimension.

        Returns:
            Dimension template dictionary
        """
        return {
            'id': '',
            'name': {'de': '', 'en': ''},
            'description': {'de': '', 'en': ''},
            'weight': 0.25,
            'prompt_hint': ''
        }
