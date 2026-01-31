/**
 * Evaluation Presets & Configuration Schema
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Dieses Modul definiert UI-Presets für Evaluations-Konfigurationen.
 * Die einheitlichen Schema-Definitionen befinden sich in:
 *
 * - Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
 * - Frontend: llars-frontend/src/schemas/evaluationSchemas.js (Validation)
 * - Transformer: app/services/evaluation/schema_transformer_service.py
 *
 * WICHTIG:
 * - Presets hier definieren UI-Konfiguration
 * - EvaluationData Schemas definieren Daten-Format für API
 * - SchemaTransformer konvertiert DB-Daten → Schema-Format
 *
 * TYPEN-MAPPING (function_type_id) - aus evaluationSchemas.js:
 * - 1 = ranking
 * - 2 = rating
 * - 3 = mail_rating
 * - 4 = comparison
 * - 5 = authenticity
 * - 7 = labeling
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 *
 * Defines generalized evaluation configurations for:
 * - Rating (Likert scales, continuous, etc.)
 * - Ranking (buckets, pairwise, etc.)
 * - Labeling/Classification (binary, multi-class, multi-label)
 * - Comparison (A vs B, multiple items)
 *
 * Plus LLARS domain-specific presets for psychosocial online counseling:
 * - Mail Rating (multi-dimensional email quality assessment)
 * - Message Authenticity (fake/real message detection)
 */

// Import from unified schema definitions
import {
  EvaluationType,
  FUNCTION_TYPE_MAP,
  EVALUATION_TYPE_TO_ID,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultRankingBuckets
} from '@/schemas/evaluationSchemas'

// ===== Evaluation Types (re-export from schema) =====
// Generalized evaluation types - use schema as source of truth
export const EVAL_TYPES = EvaluationType

// ===== Type ID Mapping (from unified schema) =====
// Re-export from schema for backward compatibility
export const TYPE_ID_MAP = FUNCTION_TYPE_MAP
export const ID_TYPE_MAP = EVALUATION_TYPE_TO_ID

// Re-export factory functions for convenience
export { createDefaultScale, createDefaultRatingDimensions, createDefaultRankingBuckets }

// ===== Base Type Mapping (for LLARS domain types) =====
// Maps domain-specific types to their underlying base type
export const BASE_TYPE_MAP = {
  [EVAL_TYPES.RATING]: EVAL_TYPES.RATING,
  [EVAL_TYPES.RANKING]: EVAL_TYPES.RANKING,
  [EVAL_TYPES.LABELING]: EVAL_TYPES.LABELING,
  [EVAL_TYPES.COMPARISON]: EVAL_TYPES.COMPARISON,
  [EVAL_TYPES.MAIL_RATING]: EVAL_TYPES.RATING,      // mail_rating uses rating base
  [EVAL_TYPES.AUTHENTICITY]: EVAL_TYPES.LABELING    // authenticity uses labeling base
}

// Check if a type is LLARS domain-specific
export function isLlarsDomainType(evalType) {
  return [EVAL_TYPES.MAIL_RATING, EVAL_TYPES.AUTHENTICITY].includes(evalType)
}

// Get the base type for any evaluation type
export function getBaseType(evalType) {
  return BASE_TYPE_MAP[evalType] || evalType
}

// ===== Rating Configuration =====
export const RATING_PRESETS = {
  'likert-5': {
    id: 'likert-5',
    name: 'Likert-5',
    description: '5-Punkte Likert-Skala (Standard)',
    config: {
      type: 'likert',
      min: 1,
      max: 5,
      step: 1,
      labels: {
        1: { de: 'Stimme gar nicht zu', en: 'Strongly disagree' },
        2: { de: 'Stimme nicht zu', en: 'Disagree' },
        3: { de: 'Neutral', en: 'Neutral' },
        4: { de: 'Stimme zu', en: 'Agree' },
        5: { de: 'Stimme voll zu', en: 'Strongly agree' }
      },
      showLabels: true,
      allowHalf: false
    }
  },
  'likert-7': {
    id: 'likert-7',
    name: 'Likert-7',
    description: '7-Punkte Likert-Skala (feinere Abstufung)',
    config: {
      type: 'likert',
      min: 1,
      max: 7,
      step: 1,
      labels: {
        1: { de: 'Stimme gar nicht zu', en: 'Strongly disagree' },
        2: { de: 'Stimme nicht zu', en: 'Disagree' },
        3: { de: 'Stimme eher nicht zu', en: 'Somewhat disagree' },
        4: { de: 'Neutral', en: 'Neutral' },
        5: { de: 'Stimme eher zu', en: 'Somewhat agree' },
        6: { de: 'Stimme zu', en: 'Agree' },
        7: { de: 'Stimme voll zu', en: 'Strongly agree' }
      },
      showLabels: true,
      allowHalf: false
    }
  },
  'stars-5': {
    id: 'stars-5',
    name: '5-Sterne',
    description: 'Klassische 5-Sterne Bewertung',
    config: {
      type: 'stars',
      min: 1,
      max: 5,
      step: 1,
      labels: null,
      showLabels: false,
      allowHalf: true
    }
  },
  'stars-10': {
    id: 'stars-10',
    name: '10-Punkte',
    description: '10-Punkte Skala für detaillierte Bewertung',
    config: {
      type: 'numeric',
      min: 1,
      max: 10,
      step: 1,
      labels: {
        1: { de: 'Sehr schlecht', en: 'Very poor' },
        5: { de: 'Durchschnittlich', en: 'Average' },
        10: { de: 'Ausgezeichnet', en: 'Excellent' }
      },
      showLabels: true,
      allowHalf: false
    }
  },
  'percentage': {
    id: 'percentage',
    name: 'Prozent',
    description: 'Bewertung in Prozent (0-100)',
    config: {
      type: 'slider',
      min: 0,
      max: 100,
      step: 5,
      labels: {
        0: { de: '0%', en: '0%' },
        50: { de: '50%', en: '50%' },
        100: { de: '100%', en: '100%' }
      },
      showLabels: true,
      unit: '%'
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Skala definieren',
    config: {
      type: 'likert',
      min: 1,
      max: 5,
      step: 1,
      labels: {},
      showLabels: true,
      allowHalf: false
    }
  },

  // ===== LLM Evaluator Multi-Dimensional Presets =====
  'llm-judge-standard': {
    id: 'llm-judge-standard',
    name: 'LLM Evaluator Standard',
    description: 'Standard-Metriken für Text-Evaluation (Coherence, Fluency, Relevance, Consistency)',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'coherence',
          name: { de: 'Kohärenz', en: 'Coherence' },
          description: { de: 'Logischer Aufbau und Zusammenhang', en: 'Logical structure and flow' },
          weight: 0.25
        },
        {
          id: 'fluency',
          name: { de: 'Flüssigkeit', en: 'Fluency' },
          description: { de: 'Sprachliche Qualität und Lesbarkeit', en: 'Language quality and readability' },
          weight: 0.25
        },
        {
          id: 'relevance',
          name: { de: 'Relevanz', en: 'Relevance' },
          description: { de: 'Bezug zum Thema/Kontext', en: 'Topic and context relevance' },
          weight: 0.25
        },
        {
          id: 'consistency',
          name: { de: 'Konsistenz', en: 'Consistency' },
          description: { de: 'Widerspruchsfreiheit und Faktentreue', en: 'Factual consistency' },
          weight: 0.25
        }
      ],
      labels: {
        1: { de: 'Sehr schlecht', en: 'Very poor' },
        2: { de: 'Schlecht', en: 'Poor' },
        3: { de: 'Akzeptabel', en: 'Acceptable' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Sehr gut', en: 'Very good' }
      },
      showOverallScore: true,
      allowFeedback: true
    }
  },
  'summeval': {
    id: 'summeval',
    name: 'SummEval Demo (Mixed Scales)',
    description: 'Demo-Preset mit 7 Dimensionen und unterschiedlichen Skalengrößen',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'creativity',
          name: { de: 'Kreativität', en: 'Creativity' },
          description: { de: 'Originalität und kreative Qualität des Textes', en: 'Originality and creative quality of the text' },
          weight: 0.15,
          scale: {
            type: 'likert',
            min: 0,
            max: 9,
            labels: {
              0: { de: 'Keine', en: 'None' },
              3: { de: 'Wenig', en: 'Low' },
              6: { de: 'Mittel', en: 'Medium' },
              9: { de: 'Sehr hoch', en: 'Very high' }
            }
          }
        },
        {
          id: 'accuracy',
          name: { de: 'Genauigkeit', en: 'Accuracy' },
          description: { de: 'Faktische Korrektheit der Informationen', en: 'Factual correctness of information' },
          weight: 0.15,
          scale: {
            type: 'likert',
            min: 1,
            max: 3,
            labels: {
              1: { de: 'Falsch', en: 'Incorrect' },
              2: { de: 'Teilweise korrekt', en: 'Partially correct' },
              3: { de: 'Korrekt', en: 'Correct' }
            }
          }
        },
        {
          id: 'engagement',
          name: { de: 'Engagement', en: 'Engagement' },
          description: { de: 'Wie fesselnd und interessant ist der Text?', en: 'How captivating and interesting is the text?' },
          weight: 0.15,
          scale: {
            type: 'likert',
            min: 1,
            max: 7,
            labels: {
              1: { de: 'Langweilig', en: 'Boring' },
              4: { de: 'Neutral', en: 'Neutral' },
              7: { de: 'Fesselnd', en: 'Captivating' }
            }
          }
        },
        {
          id: 'bias_free',
          name: { de: 'Vorurteilsfrei', en: 'Bias-Free' },
          description: { de: 'Ist der Text frei von Vorurteilen und Verzerrungen?', en: 'Is the text free from bias and distortions?' },
          weight: 0.10,
          scale: {
            type: 'binary',
            min: 1,
            max: 2,
            labels: {
              1: { de: 'Ja', en: 'Yes' },
              2: { de: 'Nein', en: 'No' }
            },
            colors: {
              1: '#66BB6A',
              2: '#AB47BC'
            }
          }
        },
        {
          id: 'complexity',
          name: { de: 'Komplexität', en: 'Complexity' },
          description: { de: 'Angemessene Komplexität für die Zielgruppe', en: 'Appropriate complexity for the target audience' },
          weight: 0.15,
          scale: {
            type: 'likert',
            min: 0,
            max: 3,
            labels: {
              0: { de: 'Zu einfach', en: 'Too simple' },
              1: { de: 'Etwas einfach', en: 'Somewhat simple' },
              2: { de: 'Angemessen', en: 'Appropriate' },
              3: { de: 'Zu komplex', en: 'Too complex' }
            }
          }
        },
        {
          id: 'structure',
          name: { de: 'Struktur', en: 'Structure' },
          description: { de: 'Logischer Aufbau und Gliederung', en: 'Logical structure and organization' },
          weight: 0.15
          // Uses global scale (1-5)
        },
        {
          id: 'actionable',
          name: { de: 'Umsetzbarkeit', en: 'Actionable' },
          description: { de: 'Enthält der Text praktisch umsetzbare Empfehlungen?', en: 'Does the text contain actionable recommendations?' },
          weight: 0.15,
          scale: {
            type: 'binary',
            min: 1,
            max: 2,
            labels: {
              1: { de: 'Ja', en: 'Yes' },
              2: { de: 'Nein', en: 'No' }
            },
            colors: {
              1: '#4CAF50',
              2: '#FF5722'
            }
          }
        }
      ],
      labels: {
        1: { de: 'Sehr schlecht', en: 'Very poor' },
        2: { de: 'Schlecht', en: 'Poor' },
        3: { de: 'Akzeptabel', en: 'Acceptable' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Sehr gut', en: 'Very good' }
      },
      showOverallScore: true,
      allowFeedback: false
    }
  },
  'response-quality': {
    id: 'response-quality',
    name: 'Antwort-Qualität',
    description: 'Bewertung von LLM-generierten Antworten auf Nutzerfragen',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'helpfulness',
          name: { de: 'Hilfsbereitschaft', en: 'Helpfulness' },
          description: { de: 'Wie nützlich ist die Antwort für den Nutzer?', en: 'How useful is the answer for the user?' },
          weight: 0.30
        },
        {
          id: 'accuracy',
          name: { de: 'Genauigkeit', en: 'Accuracy' },
          description: { de: 'Faktische Korrektheit der Informationen', en: 'Factual correctness of information' },
          weight: 0.30
        },
        {
          id: 'completeness',
          name: { de: 'Vollständigkeit', en: 'Completeness' },
          description: { de: 'Werden alle relevanten Aspekte abgedeckt?', en: 'Are all relevant aspects covered?' },
          weight: 0.20
        },
        {
          id: 'clarity',
          name: { de: 'Klarheit', en: 'Clarity' },
          description: { de: 'Verständlichkeit und Strukturiertheit', en: 'Understandability and structure' },
          weight: 0.20
        }
      ],
      labels: {
        1: { de: 'Unzureichend', en: 'Insufficient' },
        2: { de: 'Mangelhaft', en: 'Poor' },
        3: { de: 'Befriedigend', en: 'Satisfactory' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Ausgezeichnet', en: 'Excellent' }
      },
      showOverallScore: true,
      allowFeedback: true
    }
  },
  'text-quality-3dim': {
    id: 'text-quality-3dim',
    name: 'Textqualität (3 Dimensionen)',
    description: 'Kompakte Bewertung mit 3 Kerndimensionen',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'content',
          name: { de: 'Inhalt', en: 'Content' },
          description: { de: 'Informationsgehalt und Relevanz', en: 'Information value and relevance' },
          weight: 0.40
        },
        {
          id: 'language',
          name: { de: 'Sprache', en: 'Language' },
          description: { de: 'Grammatik, Stil, Lesbarkeit', en: 'Grammar, style, readability' },
          weight: 0.30
        },
        {
          id: 'structure',
          name: { de: 'Struktur', en: 'Structure' },
          description: { de: 'Aufbau, Gliederung, Logik', en: 'Organization, outline, logic' },
          weight: 0.30
        }
      ],
      labels: {
        1: { de: 'Sehr schlecht', en: 'Very poor' },
        2: { de: 'Schlecht', en: 'Poor' },
        3: { de: 'Akzeptabel', en: 'Acceptable' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Sehr gut', en: 'Very good' }
      },
      showOverallScore: true,
      allowFeedback: true
    }
  },
  'news-article': {
    id: 'news-article',
    name: 'Nachrichtenartikel',
    description: 'Bewertung von Nachrichtenartikeln nach journalistischen Standards',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'accuracy',
          name: { de: 'Genauigkeit', en: 'Accuracy' },
          description: { de: 'Faktische Korrektheit und Quellennähe', en: 'Factual correctness and source accuracy' },
          weight: 0.30
        },
        {
          id: 'objectivity',
          name: { de: 'Objektivität', en: 'Objectivity' },
          description: { de: 'Ausgewogene Darstellung ohne Verzerrung', en: 'Balanced presentation without bias' },
          weight: 0.25
        },
        {
          id: 'completeness',
          name: { de: 'Vollständigkeit', en: 'Completeness' },
          description: { de: 'Abdeckung aller relevanten Aspekte', en: 'Coverage of all relevant aspects' },
          weight: 0.25
        },
        {
          id: 'readability',
          name: { de: 'Lesbarkeit', en: 'Readability' },
          description: { de: 'Verständlichkeit und Sprachqualität', en: 'Understandability and language quality' },
          weight: 0.20
        }
      ],
      labels: {
        1: { de: 'Mangelhaft', en: 'Poor' },
        2: { de: 'Unzureichend', en: 'Insufficient' },
        3: { de: 'Befriedigend', en: 'Satisfactory' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Sehr gut', en: 'Very good' }
      },
      showOverallScore: true,
      allowFeedback: true
    }
  },
  'multi-dimensional-custom': {
    id: 'multi-dimensional-custom',
    name: 'Multi-Dimensional (Benutzerdefiniert)',
    description: 'Eigene Dimensionen definieren für mehrdimensionales Rating',
    config: {
      type: 'multi-dimensional',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [],
      labels: {
        1: { de: 'Sehr schlecht', en: 'Very poor' },
        2: { de: 'Schlecht', en: 'Poor' },
        3: { de: 'Akzeptabel', en: 'Acceptable' },
        4: { de: 'Gut', en: 'Good' },
        5: { de: 'Sehr gut', en: 'Very good' }
      },
      showOverallScore: true,
      allowFeedback: true
    }
  }
}

// ===== Ranking Configuration =====
export const RANKING_PRESETS = {
  'buckets-3': {
    id: 'buckets-3',
    name: '3 Kategorien',
    description: 'Gut / Mittel / Schlecht',
    config: {
      type: 'buckets',
      buckets: [
        { id: 1, name: { de: 'Gut', en: 'Good' }, color: '#98d4bb' },
        { id: 2, name: { de: 'Mittel', en: 'Medium' }, color: '#D1BC8A' },
        { id: 3, name: { de: 'Schlecht', en: 'Poor' }, color: '#e8a087' }
      ],
      allowTies: false,
      dragDrop: true
    }
  },
  'buckets-5': {
    id: 'buckets-5',
    name: '5 Kategorien',
    description: 'Sehr gut bis Sehr schlecht',
    config: {
      type: 'buckets',
      buckets: [
        { id: 1, name: { de: 'Sehr gut', en: 'Very good' }, color: '#6bc48f' },
        { id: 2, name: { de: 'Gut', en: 'Good' }, color: '#98d4bb' },
        { id: 3, name: { de: 'Mittel', en: 'Average' }, color: '#D1BC8A' },
        { id: 4, name: { de: 'Schlecht', en: 'Poor' }, color: '#e8a087' },
        { id: 5, name: { de: 'Sehr schlecht', en: 'Very poor' }, color: '#d46b6b' }
      ],
      allowTies: false,
      dragDrop: true
    }
  },
  'priority': {
    id: 'priority',
    name: 'Prioritäts-Ranking',
    description: 'Items nach Priorität sortieren',
    config: {
      type: 'ordered',
      showPosition: true,
      allowTies: false,
      dragDrop: true,
      labels: {
        first: { de: 'Höchste Priorität', en: 'Highest priority' },
        last: { de: 'Niedrigste Priorität', en: 'Lowest priority' }
      }
    }
  },
  'relevance': {
    id: 'relevance',
    name: 'Relevanz-Ranking',
    description: 'Nach Relevanz sortieren',
    config: {
      type: 'ordered',
      showPosition: true,
      allowTies: true,
      dragDrop: true,
      labels: {
        first: { de: 'Sehr relevant', en: 'Very relevant' },
        last: { de: 'Nicht relevant', en: 'Not relevant' }
      }
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Kategorien definieren',
    config: {
      type: 'buckets',
      buckets: [],
      allowTies: false,
      dragDrop: true
    }
  }
}

// ===== Labeling/Classification Configuration =====
export const LABELING_PRESETS = {
  'binary-authentic': {
    id: 'binary-authentic',
    name: 'Fake/Echt',
    description: 'Binäre Authentizitätsprüfung',
    config: {
      type: 'binary',
      multiLabel: false,
      categories: [
        { id: 'authentic', name: { de: 'Echt', en: 'Authentic' }, color: '#98d4bb', icon: 'mdi-check-circle' },
        { id: 'fake', name: { de: 'Fake', en: 'Fake' }, color: '#e8a087', icon: 'mdi-alert-circle' }
      ],
      allowUnsure: true,
      unsureOption: { id: 'unsure', name: { de: 'Unsicher', en: 'Unsure' }, color: '#D1BC8A', icon: 'mdi-help-circle' }
    }
  },
  'binary-sentiment': {
    id: 'binary-sentiment',
    name: 'Positiv/Negativ',
    description: 'Sentiment-Analyse',
    config: {
      type: 'binary',
      multiLabel: false,
      categories: [
        { id: 'positive', name: { de: 'Positiv', en: 'Positive' }, color: '#98d4bb', icon: 'mdi-emoticon-happy' },
        { id: 'negative', name: { de: 'Negativ', en: 'Negative' }, color: '#e8a087', icon: 'mdi-emoticon-sad' }
      ],
      allowUnsure: true,
      unsureOption: { id: 'neutral', name: { de: 'Neutral', en: 'Neutral' }, color: '#D1BC8A', icon: 'mdi-emoticon-neutral' }
    }
  },
  'sentiment-3': {
    id: 'sentiment-3',
    name: '3-Klassen Sentiment',
    description: 'Positiv / Neutral / Negativ',
    config: {
      type: 'multiclass',
      multiLabel: false,
      categories: [
        { id: 'positive', name: { de: 'Positiv', en: 'Positive' }, color: '#98d4bb', icon: 'mdi-emoticon-happy' },
        { id: 'neutral', name: { de: 'Neutral', en: 'Neutral' }, color: '#D1BC8A', icon: 'mdi-emoticon-neutral' },
        { id: 'negative', name: { de: 'Negativ', en: 'Negative' }, color: '#e8a087', icon: 'mdi-emoticon-sad' }
      ],
      allowUnsure: false
    }
  },
  'topic-multilabel': {
    id: 'topic-multilabel',
    name: 'Themen-Tags',
    description: 'Mehrere Themen pro Item auswählen',
    config: {
      type: 'multilabel',
      multiLabel: true,
      categories: [],
      allowUnsure: false,
      minLabels: 1,
      maxLabels: null
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Kategorien definieren',
    config: {
      type: 'multiclass',
      multiLabel: false,
      categories: [],
      allowUnsure: true,
      unsureOption: null
    }
  }
}

// ===== Comparison Configuration =====
export const COMPARISON_PRESETS = {
  'pairwise': {
    id: 'pairwise',
    name: 'Paarweiser Vergleich',
    description: 'A vs B - welches ist besser?',
    config: {
      type: 'pairwise',
      itemsPerComparison: 2,
      allowTie: true,
      showConfidence: false,
      criteria: [
        { id: 'overall', name: { de: 'Gesamt', en: 'Overall' }, weight: 1.0 }
      ]
    }
  },
  'pairwise-confidence': {
    id: 'pairwise-confidence',
    name: 'Paarweise mit Konfidenz',
    description: 'A vs B mit Konfidenzbewertung',
    config: {
      type: 'pairwise',
      itemsPerComparison: 2,
      allowTie: true,
      showConfidence: true,
      confidenceScale: { min: 1, max: 5 },
      criteria: [
        { id: 'overall', name: { de: 'Gesamt', en: 'Overall' }, weight: 1.0 }
      ]
    }
  },
  'multicriteria': {
    id: 'multicriteria',
    name: 'Multi-Kriterien',
    description: 'Vergleich nach mehreren Kriterien',
    config: {
      type: 'pairwise',
      itemsPerComparison: 2,
      allowTie: true,
      showConfidence: false,
      criteria: [
        { id: 'relevance', name: { de: 'Relevanz', en: 'Relevance' }, weight: 0.4 },
        { id: 'quality', name: { de: 'Qualität', en: 'Quality' }, weight: 0.4 },
        { id: 'clarity', name: { de: 'Klarheit', en: 'Clarity' }, weight: 0.2 }
      ]
    }
  },
  'tournament': {
    id: 'tournament',
    name: 'Turnier',
    description: 'Eliminierungs-Turnier Format',
    config: {
      type: 'tournament',
      itemsPerComparison: 2,
      allowTie: false,
      rounds: 'auto',
      criteria: [
        { id: 'overall', name: { de: 'Gesamt', en: 'Overall' }, weight: 1.0 }
      ]
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Vergleichskriterien definieren',
    config: {
      type: 'pairwise',
      itemsPerComparison: 2,
      allowTie: true,
      showConfidence: false,
      criteria: []
    }
  }
}

// =============================================================================
// LLARS DOMAIN-SPECIFIC PRESETS (Psychosoziale Online-Beratung)
// =============================================================================

/**
 * Mail Rating Presets
 * For evaluating email/message quality in psychosocial online counseling
 * Base type: rating (with multiple dimensions)
 */
export const MAIL_RATING_PRESETS = {
  'mail-verlauf-bewertung': {
    id: 'mail-verlauf-bewertung',
    name: 'Mail-Verlauf Bewertung',
    description: 'Bewertung von E-Mail-Beratungsverläufen mit Kohärenz, Beratungsqualität und Gesamteignung',
    llarsSpecific: true,
    isDefault: true,
    config: {
      type: 'multi-dimensional',
      baseType: 'rating',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [
        {
          id: 'client_coherence',
          name: { de: 'Kohärenz ratsuchende Person', en: 'Client Coherence' },
          description: {
            de: 'Entsprechen die Reaktionen und Interaktionen einem natürlichen Kommunikationsmuster? Stehen die Texte in einem inhaltlichen Zusammenhang zueinander? Gibt es Brüche oder Unstimmigkeiten? Wird auf die Antwort des jeweilig anderen eingegangen und auch neue inhaltliche Aspekte generiert oder wird „stoisch" immer das gleiche wiederholt? Gibt es Halluzinationen?',
            en: 'Do the reactions and interactions follow a natural communication pattern? Are the texts coherent? Are there breaks or inconsistencies? Are there hallucinations?'
          },
          weight: 0.25
        },
        {
          id: 'counsellor_coherence',
          name: { de: 'Kohärenz beratende Person', en: 'Counsellor Coherence' },
          description: {
            de: 'Entsprechen die Reaktionen und Interaktionen einem natürlichen Kommunikationsmuster? Stehen die Texte in einem inhaltlichen Zusammenhang zueinander? Gibt es Brüche oder Unstimmigkeiten? Wird auf die Antwort des jeweilig anderen eingegangen und auch neue inhaltliche Aspekte generiert oder wird „stoisch" immer das gleiche wiederholt? Gibt es Halluzinationen?',
            en: 'Do the reactions and interactions follow a natural communication pattern? Are the texts coherent? Are there breaks or inconsistencies? Are there hallucinations?'
          },
          weight: 0.25
        },
        {
          id: 'quality',
          name: { de: 'Beratungsqualität', en: 'Counseling Quality' },
          description: {
            de: 'Ist die Antwort gut strukturiert und verständlich? Zeigt sich die beratende Person empathisch, wertschätzend und kongruent? Setzt die beratende Person gezielt Beratungstechniken ein, um das Anliegen systematisch zu bearbeiten und Lösungen zu entwickeln?',
            en: 'Is the response well-structured and understandable? Does the counselor show empathy, appreciation and congruence? Does the counselor use counseling techniques to develop solutions?'
          },
          weight: 0.25
        },
        {
          id: 'overall',
          name: { de: 'Gesamtbewertung', en: 'Overall Rating' },
          description: {
            de: 'Ist der Fall in seiner Gesamtheit authentisch und realistisch? Eignet sich der Fall hinsichtlich Thema und Fachlichkeit als gutes Beispiel für Onlineberatung?',
            en: 'Is the case authentic and realistic overall? Is the case suitable as a good example for online counseling?'
          },
          weight: 0.25,
          scale: {
            type: 'binary',
            min: 1,
            max: 2,
            labels: {
              1: { de: 'Ja', en: 'Yes' },
              2: { de: 'Nein', en: 'No' }
            },
            colors: {
              1: '#66BB6A',
              2: '#AB47BC'
            }
          }
        }
      ],
      labels: {
        1: { de: 'Sehr gut', en: 'Very good' },
        2: { de: 'Gut', en: 'Good' },
        3: { de: 'Akzeptabel', en: 'Acceptable' },
        4: { de: 'Schlecht', en: 'Poor' },
        5: { de: 'Sehr schlecht', en: 'Very poor' }
      },
      colors: {
        1: '#66BB6A',
        2: '#81C784',
        3: '#BDBDBD',
        4: '#CE93D8',
        5: '#AB47BC'
      },
      showOverallScore: false,
      allowFeedback: true,
      disableOnBadRating: true
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Bewertungsdimensionen definieren',
    llarsSpecific: true,
    config: {
      type: 'multi-dimensional',
      baseType: 'rating',
      min: 1,
      max: 5,
      step: 1,
      dimensions: [],
      labels: {},
      showOverallScore: true,
      allowComments: true
    }
  }
}

/**
 * Authenticity Presets
 * For detecting fake/authentic messages in psychosocial online counseling
 * Base type: labeling (binary classification)
 */
export const AUTHENTICITY_PRESETS = {
  'nachricht-echtheit': {
    id: 'nachricht-echtheit',
    name: 'Nachrichten-Echtheit',
    description: 'Erkennung von echten vs. gefälschten Beratungsnachrichten',
    llarsSpecific: true,
    config: {
      type: 'binary',
      baseType: 'labeling',
      multiLabel: false,
      categories: [
        {
          id: 'echt',
          name: { de: 'Echt', en: 'Authentic' },
          description: { de: 'Authentische Nachricht eines echten Ratsuchenden/Beraters', en: 'Authentic message from real client/counselor' },
          color: '#98d4bb',
          icon: 'mdi-check-decagram'
        },
        {
          id: 'fake',
          name: { de: 'Fake', en: 'Fake' },
          description: { de: 'Generierte oder gefälschte Nachricht', en: 'Generated or fake message' },
          color: '#e8a087',
          icon: 'mdi-alert-decagram'
        }
      ],
      allowUnsure: true,
      unsureOption: {
        id: 'unsicher',
        name: { de: 'Unsicher', en: 'Unsure' },
        description: { de: 'Keine eindeutige Einschätzung möglich', en: 'Cannot determine with certainty' },
        color: '#D1BC8A',
        icon: 'mdi-help-circle'
      },
      requireReasoning: true,
      reasoningPrompt: { de: 'Begründung für die Einschätzung', en: 'Reason for assessment' }
    }
  },
  'ki-generiert': {
    id: 'ki-generiert',
    name: 'KI-Erkennung',
    description: 'Erkennung von KI-generierten vs. menschlichen Texten',
    llarsSpecific: true,
    config: {
      type: 'binary',
      baseType: 'labeling',
      multiLabel: false,
      categories: [
        {
          id: 'mensch',
          name: { de: 'Menschlich', en: 'Human' },
          description: { de: 'Von einem Menschen verfasster Text', en: 'Text written by a human' },
          color: '#98d4bb',
          icon: 'mdi-account'
        },
        {
          id: 'ki',
          name: { de: 'KI-generiert', en: 'AI-generated' },
          description: { de: 'Von einer KI generierter Text', en: 'Text generated by AI' },
          color: '#88c4c8',
          icon: 'mdi-robot'
        }
      ],
      allowUnsure: true,
      unsureOption: {
        id: 'unklar',
        name: { de: 'Unklar', en: 'Unclear' },
        color: '#D1BC8A',
        icon: 'mdi-help-circle'
      },
      requireReasoning: true
    }
  },
  'dringlichkeit': {
    id: 'dringlichkeit',
    name: 'Dringlichkeits-Einschätzung',
    description: 'Einschätzung der Dringlichkeit einer Beratungsanfrage',
    llarsSpecific: true,
    config: {
      type: 'multiclass',
      baseType: 'labeling',
      multiLabel: false,
      categories: [
        {
          id: 'akut',
          name: { de: 'Akut/Krise', en: 'Acute/Crisis' },
          description: { de: 'Sofortige Intervention erforderlich', en: 'Immediate intervention required' },
          color: '#d46b6b',
          icon: 'mdi-alert'
        },
        {
          id: 'dringend',
          name: { de: 'Dringend', en: 'Urgent' },
          description: { de: 'Zeitnahe Bearbeitung notwendig', en: 'Timely processing necessary' },
          color: '#e8a087',
          icon: 'mdi-clock-alert'
        },
        {
          id: 'normal',
          name: { de: 'Normal', en: 'Normal' },
          description: { de: 'Reguläre Bearbeitungszeit', en: 'Regular processing time' },
          color: '#D1BC8A',
          icon: 'mdi-clock'
        },
        {
          id: 'niedrig',
          name: { de: 'Niedrig', en: 'Low' },
          description: { de: 'Keine besondere Eile', en: 'No particular urgency' },
          color: '#98d4bb',
          icon: 'mdi-clock-outline'
        }
      ],
      allowUnsure: false,
      requireReasoning: true
    }
  },
  'custom': {
    id: 'custom',
    name: 'Benutzerdefiniert',
    description: 'Eigene Kategorien definieren',
    llarsSpecific: true,
    config: {
      type: 'binary',
      baseType: 'labeling',
      multiLabel: false,
      categories: [],
      allowUnsure: true,
      unsureOption: null,
      requireReasoning: false
    }
  }
}

// ===== All Presets by Type =====
export const PRESETS_BY_TYPE = {
  // General types
  [EVAL_TYPES.RATING]: RATING_PRESETS,
  [EVAL_TYPES.RANKING]: RANKING_PRESETS,
  [EVAL_TYPES.LABELING]: LABELING_PRESETS,
  [EVAL_TYPES.COMPARISON]: COMPARISON_PRESETS,
  // LLARS domain-specific types
  [EVAL_TYPES.MAIL_RATING]: MAIL_RATING_PRESETS,
  [EVAL_TYPES.AUTHENTICITY]: AUTHENTICITY_PRESETS
}

// ===== Default Config by Type =====
export const DEFAULT_CONFIG_BY_TYPE = {
  // General types - RATING now uses multi-dimensional as default (LLM Evaluator standard)
  [EVAL_TYPES.RATING]: RATING_PRESETS['llm-judge-standard'].config,
  [EVAL_TYPES.RANKING]: RANKING_PRESETS['buckets-3'].config,
  [EVAL_TYPES.LABELING]: LABELING_PRESETS['binary-authentic'].config,
  [EVAL_TYPES.COMPARISON]: COMPARISON_PRESETS['pairwise'].config,
  // LLARS domain-specific types
  [EVAL_TYPES.MAIL_RATING]: MAIL_RATING_PRESETS['mail-verlauf-bewertung'].config,
  [EVAL_TYPES.AUTHENTICITY]: AUTHENTICITY_PRESETS['nachricht-echtheit'].config
}

// ===== Utility Functions =====

/**
 * Get preset by type and preset ID
 */
export function getPreset(evalType, presetId) {
  const presets = PRESETS_BY_TYPE[evalType]
  if (!presets) return null
  return presets[presetId] || null
}

/**
 * Get all presets for a type as array
 */
export function getPresetsArray(evalType) {
  const presets = PRESETS_BY_TYPE[evalType]
  if (!presets) return []
  return Object.values(presets)
}

/**
 * Get default config for type
 */
export function getDefaultConfig(evalType) {
  return DEFAULT_CONFIG_BY_TYPE[evalType] || null
}

/**
 * Create a deep copy of a config
 */
export function cloneConfig(config) {
  return JSON.parse(JSON.stringify(config))
}

/**
 * Validate evaluation config
 */
export function validateConfig(evalType, config) {
  const errors = []

  if (!config) {
    errors.push('Config is required')
    return { valid: false, errors }
  }

  switch (evalType) {
    case EVAL_TYPES.RATING:
      if (config.min >= config.max) {
        errors.push('Min must be less than max')
      }
      if (config.step <= 0) {
        errors.push('Step must be positive')
      }
      break

    case EVAL_TYPES.RANKING:
      if (config.type === 'buckets' && (!config.buckets || config.buckets.length < 2)) {
        errors.push('At least 2 buckets are required')
      }
      break

    case EVAL_TYPES.LABELING:
      if (!config.categories || config.categories.length < 2) {
        errors.push('At least 2 categories are required')
      }
      break

    case EVAL_TYPES.COMPARISON:
      if (!config.criteria || config.criteria.length === 0) {
        errors.push('At least 1 criterion is required')
      }
      break
  }

  return { valid: errors.length === 0, errors }
}

/**
 * Get type info for display
 */
export const TYPE_INFO = {
  // ===== General Evaluation Types =====
  [EVAL_TYPES.RATING]: {
    name: { de: 'Rating', en: 'Rating' },
    description: { de: 'Bewertung auf einer Skala (Likert, Sterne, Prozent)', en: 'Rate on a scale (Likert, stars, percentage)' },
    icon: 'mdi-star-outline',
    color: '#D1BC8A',
    category: 'general'
  },
  [EVAL_TYPES.RANKING]: {
    name: { de: 'Ranking', en: 'Ranking' },
    description: { de: 'Items sortieren oder in Kategorien einteilen', en: 'Sort items or categorize into buckets' },
    icon: 'mdi-podium',
    color: '#b0ca97',
    category: 'general'
  },
  [EVAL_TYPES.LABELING]: {
    name: { de: 'Labeling', en: 'Labeling' },
    description: { de: 'Kategorien zuweisen (binär, multi-class, multi-label)', en: 'Assign categories (binary, multi-class, multi-label)' },
    icon: 'mdi-tag-multiple',
    color: '#e8a087',
    category: 'general'
  },
  [EVAL_TYPES.COMPARISON]: {
    name: { de: 'Vergleich', en: 'Comparison' },
    description: { de: 'Items paarweise vergleichen (A vs B)', en: 'Compare items pairwise (A vs B)' },
    icon: 'mdi-compare-horizontal',
    color: '#c4a0d4',
    category: 'general'
  },
  // ===== LLARS Domain-Specific Types (Psychosoziale Online-Beratung) =====
  [EVAL_TYPES.MAIL_RATING]: {
    name: { de: 'Mail-Bewertung', en: 'Mail Rating' },
    description: { de: 'Mehrdimensionale Bewertung von Beratungs-E-Mails', en: 'Multi-dimensional rating of counseling emails' },
    icon: 'mdi-email-check',
    color: '#88c4c8',
    category: 'llars',
    baseType: EVAL_TYPES.RATING
  },
  [EVAL_TYPES.AUTHENTICITY]: {
    name: { de: 'Echtheit', en: 'Authenticity' },
    description: { de: 'Erkennung von echten vs. gefälschten Nachrichten', en: 'Detection of authentic vs. fake messages' },
    icon: 'mdi-shield-check',
    color: '#98d4bb',
    category: 'llars',
    baseType: EVAL_TYPES.LABELING
  }
}

/**
 * Get types grouped by category
 */
export function getTypesByCategory() {
  return {
    general: [EVAL_TYPES.RATING, EVAL_TYPES.RANKING, EVAL_TYPES.LABELING, EVAL_TYPES.COMPARISON],
    llars: [EVAL_TYPES.MAIL_RATING, EVAL_TYPES.AUTHENTICITY]
  }
}

/**
 * Get all general types
 */
export function getGeneralTypes() {
  return [EVAL_TYPES.RATING, EVAL_TYPES.RANKING, EVAL_TYPES.LABELING, EVAL_TYPES.COMPARISON]
}

/**
 * Get all LLARS domain-specific types
 */
export function getLlarsTypes() {
  return [EVAL_TYPES.MAIL_RATING, EVAL_TYPES.AUTHENTICITY]
}
