/**
 * Evaluation Presets & Configuration Schema
 *
 * Defines generalized evaluation configurations for:
 * - Rating (Likert scales, continuous, etc.)
 * - Ranking (buckets, pairwise, etc.)
 * - Labeling/Classification (binary, multi-class, multi-label)
 * - Comparison (A vs B, multiple items)
 */

// ===== Evaluation Types =====
// Generalized evaluation types - mail_rating removed (use rating instead)
export const EVAL_TYPES = {
  RATING: 'rating',
  RANKING: 'ranking',
  LABELING: 'labeling',
  COMPARISON: 'comparison'
}

// ===== Type ID Mapping (for DB compatibility) =====
// DB IDs: 1=ranking, 2=rating, 4=comparison, 5=authenticity (mapped to labeling)
// Note: ID 3 (mail_rating) is deprecated, ID 5 (authenticity) is a labeling preset
export const TYPE_ID_MAP = {
  1: EVAL_TYPES.RANKING,
  2: EVAL_TYPES.RATING,
  4: EVAL_TYPES.COMPARISON,
  5: EVAL_TYPES.LABELING,    // authenticity → labeling preset
  7: EVAL_TYPES.LABELING     // text_classification → labeling
}

export const ID_TYPE_MAP = {
  [EVAL_TYPES.RANKING]: 1,
  [EVAL_TYPES.RATING]: 2,
  [EVAL_TYPES.COMPARISON]: 4,
  [EVAL_TYPES.LABELING]: 5   // Use authenticity ID for labeling
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

// ===== All Presets by Type =====
// Note: mail_rating removed - use rating presets with custom dimensions instead
export const PRESETS_BY_TYPE = {
  [EVAL_TYPES.RATING]: RATING_PRESETS,
  [EVAL_TYPES.RANKING]: RANKING_PRESETS,
  [EVAL_TYPES.LABELING]: LABELING_PRESETS,
  [EVAL_TYPES.COMPARISON]: COMPARISON_PRESETS
}

// ===== Default Config by Type =====
export const DEFAULT_CONFIG_BY_TYPE = {
  [EVAL_TYPES.RATING]: RATING_PRESETS['likert-5'].config,
  [EVAL_TYPES.RANKING]: RANKING_PRESETS['buckets-3'].config,
  [EVAL_TYPES.LABELING]: LABELING_PRESETS['binary-authentic'].config,
  [EVAL_TYPES.COMPARISON]: COMPARISON_PRESETS['pairwise'].config
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
  [EVAL_TYPES.RATING]: {
    name: { de: 'Rating', en: 'Rating' },
    description: { de: 'Bewertung auf einer Skala (Likert, Sterne, Prozent)', en: 'Rate on a scale (Likert, stars, percentage)' },
    icon: 'mdi-star-outline',
    color: '#D1BC8A'
  },
  [EVAL_TYPES.RANKING]: {
    name: { de: 'Ranking', en: 'Ranking' },
    description: { de: 'Items sortieren oder in Kategorien einteilen', en: 'Sort items or categorize into buckets' },
    icon: 'mdi-sort-variant',
    color: '#b0ca97'
  },
  [EVAL_TYPES.LABELING]: {
    name: { de: 'Labeling', en: 'Labeling' },
    description: { de: 'Kategorien zuweisen (binär, multi-class, multi-label)', en: 'Assign categories (binary, multi-class, multi-label)' },
    icon: 'mdi-tag-multiple',
    color: '#e8a087'
  },
  [EVAL_TYPES.COMPARISON]: {
    name: { de: 'Vergleich', en: 'Comparison' },
    description: { de: 'Items paarweise vergleichen (A vs B)', en: 'Compare items pairwise (A vs B)' },
    icon: 'mdi-compare-horizontal',
    color: '#c4a0d4'
  }
}
