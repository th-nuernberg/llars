/**
 * Unified Evaluation Data Schemas
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Diese Datei definiert das einheitliche Datenformat für alle Evaluationstypen
 * in LLARS. Die Schemas sind synchron mit dem Backend:
 *
 * - Backend: app/schemas/evaluation_data_schemas.py (Pydantic Models)
 * - Frontend: llars-frontend/src/schemas/evaluationSchemas.js (Diese Datei)
 *
 * UNTERSCHIED zu anderen Schemas:
 * - evaluation_schemas.py: Schemas für LLM-OUTPUT (strukturierte Antworten)
 * - evaluation_data_schemas.py: Schemas für EVALUATION-INPUT (Daten zum Bewerten)
 *
 * WICHTIG:
 * - Item.id ist IMMER technisch (z.B. "item_1", "item_2") - NIEMALS LLM-Namen!
 * - Item.label ist für UI-Anzeige (generische Labels)
 * - Item.source enthält die tatsächliche Herkunft (human/llm/unknown)
 *
 * Schema-Version: 1.0
 * Datum: 2026-01-27
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 */

// =============================================================================
// Enums / Constants
// =============================================================================

/**
 * Schema versions
 * @readonly
 * @enum {string}
 */
export const SchemaVersion = Object.freeze({
  V1_0: '1.0'
})

/**
 * Evaluation types corresponding to function_type_id
 * @readonly
 * @enum {string}
 */
export const EvaluationType = Object.freeze({
  RANKING: 'ranking',           // function_type_id = 1
  RATING: 'rating',             // function_type_id = 2
  MAIL_RATING: 'mail_rating',   // function_type_id = 3
  COMPARISON: 'comparison',     // function_type_id = 4
  AUTHENTICITY: 'authenticity', // function_type_id = 5
  LABELING: 'labeling'          // function_type_id = 7
})

/**
 * Source types for items
 * @readonly
 * @enum {string}
 */
export const SourceType = Object.freeze({
  HUMAN: 'human',
  LLM: 'llm',
  UNKNOWN: 'unknown'
})

/**
 * Content types for reference and items
 * @readonly
 * @enum {string}
 */
export const ContentType = Object.freeze({
  TEXT: 'text',
  CONVERSATION: 'conversation'
})

/**
 * Ranking modes
 * @readonly
 * @enum {string}
 */
export const RankingMode = Object.freeze({
  SIMPLE: 'simple',
  MULTI_GROUP: 'multi_group'
})

/**
 * Labeling modes
 * @readonly
 * @enum {string}
 */
export const LabelingMode = Object.freeze({
  SINGLE: 'single',
  MULTI: 'multi'
})

/**
 * Maps function_type_id to EvaluationType
 */
export const FUNCTION_TYPE_MAP = Object.freeze({
  1: EvaluationType.RANKING,
  2: EvaluationType.RATING,
  3: EvaluationType.MAIL_RATING,
  4: EvaluationType.COMPARISON,
  5: EvaluationType.AUTHENTICITY,
  7: EvaluationType.LABELING
})

/**
 * Maps EvaluationType to function_type_id
 */
export const EVALUATION_TYPE_TO_ID = Object.freeze({
  [EvaluationType.RANKING]: 1,
  [EvaluationType.RATING]: 2,
  [EvaluationType.MAIL_RATING]: 3,
  [EvaluationType.COMPARISON]: 4,
  [EvaluationType.AUTHENTICITY]: 5,
  [EvaluationType.LABELING]: 7
})

// =============================================================================
// Type Definitions (JSDoc)
// =============================================================================

/**
 * Localized string with German and English
 * @typedef {Object} LocalizedString
 * @property {string} de - German text
 * @property {string} en - English text
 */

/**
 * Source information for an item
 * @typedef {Object} Source
 * @property {('human'|'llm'|'unknown')} type - Source type
 * @property {string} [name] - Name (e.g., LLM model name)
 * @property {Object} [metadata] - Additional metadata
 */

/**
 * A message in a conversation
 * @typedef {Object} Message
 * @property {string} role - Role (e.g., "Klient", "Berater")
 * @property {string} content - Message content
 * @property {string} [timestamp] - ISO 8601 timestamp
 * @property {Object} [metadata] - Additional metadata
 */

/**
 * Conversation content with multiple messages
 * @typedef {Object} ConversationContent
 * @property {'conversation'} type - Always "conversation"
 * @property {Message[]} messages - Array of messages
 */

/**
 * Reference/context for evaluation (displayed on right side)
 * @typedef {Object} Reference
 * @property {('text'|'conversation')} type - Content type
 * @property {string} label - UI display name
 * @property {string|Message[]} content - Text or messages
 * @property {Object} [metadata] - Additional metadata
 */

/**
 * An item to be evaluated (displayed on left side)
 * @typedef {Object} Item
 * @property {string} id - Technical ID (e.g., "item_1") - NEVER LLM names!
 * @property {string} label - UI display name (generic, e.g., "Summary 1")
 * @property {Source} source - Origin information
 * @property {string|ConversationContent} content - Text or conversation
 * @property {string} [group] - Group ID for multi-group ranking
 */

/**
 * Ground truth for supervised evaluation
 * @typedef {Object} GroundTruth
 * @property {string|number|string[]|Object} value - Ground truth value
 * @property {Source} [source] - Source of ground truth
 * @property {number} [confidence] - Confidence (0-1)
 */

/**
 * A bucket for ranking
 * @typedef {Object} Bucket
 * @property {string} id - Bucket ID (e.g., "good")
 * @property {LocalizedString} label - Display name
 * @property {string} color - Hex color
 * @property {number} order - Sort order (1 = best)
 */

/**
 * Group definition for multi-group ranking
 * @typedef {Object} RankingGroup
 * @property {string} id - Group ID
 * @property {LocalizedString} label - Tab name
 * @property {LocalizedString} [description] - Tooltip
 * @property {Bucket[]} buckets - Buckets for this group
 * @property {boolean} [allowTies=true] - Allow ties
 */

/**
 * Simple ranking configuration
 * @typedef {Object} SimpleRankingConfig
 * @property {'simple'} mode - Mode
 * @property {Bucket[]} buckets - Buckets
 * @property {boolean} [allowTies=true] - Allow ties
 * @property {boolean} [requireComplete=true] - Require all items assigned
 */

/**
 * Multi-group ranking configuration
 * @typedef {Object} MultiGroupRankingConfig
 * @property {'multi_group'} mode - Mode
 * @property {RankingGroup[]} groups - Groups with tabs
 * @property {boolean} [requireComplete=true] - Require complete
 */

/**
 * Rating scale
 * @typedef {Object} Scale
 * @property {number} [min=1] - Minimum value
 * @property {number} [max=5] - Maximum value
 * @property {number} [step=1] - Step size
 * @property {Object<string, LocalizedString>} [labels] - Value labels
 */

/**
 * Rating dimension
 * @typedef {Object} Dimension
 * @property {string} id - Dimension ID
 * @property {LocalizedString} label - Display name
 * @property {LocalizedString} [description] - Description
 * @property {number} [weight=0.25] - Weight for overall score
 */

/**
 * Rating configuration
 * @typedef {Object} RatingConfig
 * @property {Scale} scale - Rating scale
 * @property {Dimension[]} dimensions - Rating dimensions
 * @property {boolean} [showOverall=true] - Show overall score
 */

/**
 * Mail rating configuration (extends RatingConfig)
 * @typedef {Object} MailRatingConfig
 * @property {Scale} scale - Rating scale
 * @property {Dimension[]} dimensions - Rating dimensions
 * @property {boolean} [showOverall=true] - Show overall score
 * @property {string} [focusRole] - Role to evaluate (e.g., "Berater")
 */

/**
 * Comparison configuration
 * @typedef {Object} ComparisonConfig
 * @property {LocalizedString} question - Question to ask
 * @property {string[]} [criteria] - Evaluation criteria
 * @property {boolean} [allowTie=true] - Allow tie option
 * @property {boolean} [showSource=false] - Show LLM names
 */

/**
 * Authenticity option
 * @typedef {Object} AuthenticityOption
 * @property {string} id - Option ID (e.g., "human", "ai")
 * @property {LocalizedString} label - Display name
 */

/**
 * Authenticity configuration
 * @typedef {Object} AuthenticityConfig
 * @property {AuthenticityOption[]} options - Available options
 * @property {boolean} [showConfidence=true] - Show confidence slider
 */

/**
 * Label option
 * @typedef {Object} LabelOption
 * @property {string} id - Label ID
 * @property {LocalizedString} label - Display name
 * @property {LocalizedString} [description] - Description
 * @property {string} [color] - Hex color
 */

/**
 * Labeling configuration
 * @typedef {Object} LabelingConfig
 * @property {('single'|'multi')} mode - Selection mode
 * @property {LabelOption[]} labels - Available labels
 * @property {boolean} [allowOther=false] - Allow "other" option
 * @property {number} [minLabels] - Min labels (multi mode)
 * @property {number} [maxLabels] - Max labels (multi mode)
 */

/**
 * Main evaluation data schema
 * @typedef {Object} EvaluationData
 * @property {string} schema_version - Schema version (e.g., "1.0")
 * @property {string} type - Evaluation type
 * @property {Reference} [reference] - Reference/context
 * @property {Item[]} items - Items to evaluate
 * @property {SimpleRankingConfig|MultiGroupRankingConfig|RatingConfig|MailRatingConfig|ComparisonConfig|AuthenticityConfig|LabelingConfig} config - Type-specific config
 * @property {GroundTruth} [ground_truth] - Ground truth (optional)
 */

// =============================================================================
// Default Values / Factory Functions
// =============================================================================

/**
 * Creates default ranking buckets (Good/Moderate/Poor)
 * @returns {Bucket[]}
 */
export function createDefaultRankingBuckets() {
  return [
    {
      id: 'good',
      label: { de: 'Gut', en: 'Good' },
      color: '#98d4bb',
      order: 1
    },
    {
      id: 'moderate',
      label: { de: 'Moderat', en: 'Moderate' },
      color: '#D1BC8A',
      order: 2
    },
    {
      id: 'poor',
      label: { de: 'Schlecht', en: 'Poor' },
      color: '#e8a087',
      order: 3
    }
  ]
}

/**
 * Creates default rating scale (1-5)
 * @returns {Scale}
 */
export function createDefaultScale() {
  return {
    min: 1,
    max: 5,
    step: 1,
    labels: {
      '1': { de: 'Sehr schlecht', en: 'Very poor' },
      '2': { de: 'Schlecht', en: 'Poor' },
      '3': { de: 'Akzeptabel', en: 'Acceptable' },
      '4': { de: 'Gut', en: 'Good' },
      '5': { de: 'Sehr gut', en: 'Very good' }
    }
  }
}

/**
 * Creates default rating dimensions (SummEval-style)
 * @returns {Dimension[]}
 */
export function createDefaultRatingDimensions() {
  return [
    {
      id: 'coherence',
      label: { de: 'Kohärenz', en: 'Coherence' },
      description: { de: 'Logischer Aufbau und Zusammenhang', en: 'Logical structure and connection' },
      weight: 0.25
    },
    {
      id: 'fluency',
      label: { de: 'Flüssigkeit', en: 'Fluency' },
      description: { de: 'Grammatik und Lesbarkeit', en: 'Grammar and readability' },
      weight: 0.25
    },
    {
      id: 'relevance',
      label: { de: 'Relevanz', en: 'Relevance' },
      description: { de: 'Wichtige Informationen erfasst', en: 'Important information captured' },
      weight: 0.25
    },
    {
      id: 'consistency',
      label: { de: 'Konsistenz', en: 'Consistency' },
      description: { de: 'Faktentreue zum Original', en: 'Factual accuracy to source' },
      weight: 0.25
    }
  ]
}

/**
 * Creates default authenticity options
 * @returns {AuthenticityOption[]}
 */
export function createDefaultAuthenticityOptions() {
  return [
    {
      id: 'human',
      label: { de: 'Echt', en: 'Real' }
    },
    {
      id: 'ai',
      label: { de: 'KI-generiert', en: 'AI-generated' }
    }
  ]
}

/**
 * Creates a simple ranking config
 * @param {Object} [options]
 * @param {Bucket[]} [options.buckets]
 * @param {boolean} [options.allowTies=true]
 * @param {boolean} [options.requireComplete=true]
 * @returns {SimpleRankingConfig}
 */
export function createSimpleRankingConfig(options = {}) {
  return {
    mode: RankingMode.SIMPLE,
    buckets: options.buckets || createDefaultRankingBuckets(),
    allowTies: options.allowTies ?? true,
    requireComplete: options.requireComplete ?? true
  }
}

/**
 * Creates a rating config
 * @param {Object} [options]
 * @param {Scale} [options.scale]
 * @param {Dimension[]} [options.dimensions]
 * @param {boolean} [options.showOverall=true]
 * @returns {RatingConfig}
 */
export function createRatingConfig(options = {}) {
  return {
    scale: options.scale || createDefaultScale(),
    dimensions: options.dimensions || createDefaultRatingDimensions(),
    showOverall: options.showOverall ?? true
  }
}

// =============================================================================
// Validation Functions
// =============================================================================

/**
 * Validates an EvaluationData object
 * @param {Object} data - Data to validate
 * @returns {{ valid: boolean, errors: Array<{field: string, message: string}>, warnings: Array<{field: string, message: string}> }}
 */
export function validateEvaluationData(data) {
  const errors = []
  const warnings = []

  if (!data) {
    errors.push({ field: 'root', message: 'Data is required' })
    return { valid: false, errors, warnings }
  }

  // Required fields
  if (!data.schema_version) {
    errors.push({ field: 'schema_version', message: 'Schema version is required' })
  }

  if (!data.type) {
    errors.push({ field: 'type', message: 'Type is required' })
  } else if (!Object.values(EvaluationType).includes(data.type)) {
    errors.push({ field: 'type', message: `Invalid type: ${data.type}` })
  }

  if (!data.items || !Array.isArray(data.items)) {
    errors.push({ field: 'items', message: 'Items array is required' })
  } else if (data.items.length === 0) {
    warnings.push({ field: 'items', message: 'Items array is empty' })
  } else {
    // Validate each item
    data.items.forEach((item, idx) => {
      if (!item.id) {
        errors.push({ field: `items[${idx}].id`, message: 'Item ID is required' })
      }
      if (!item.label) {
        errors.push({ field: `items[${idx}].label`, message: 'Item label is required' })
      }
      if (!item.source) {
        errors.push({ field: `items[${idx}].source`, message: 'Item source is required' })
      }
      if (item.content === undefined || item.content === null) {
        errors.push({ field: `items[${idx}].content`, message: 'Item content is required' })
      }

      // Warning: Label should not contain source name
      if (item.label && item.source?.name) {
        if (item.label.toLowerCase().includes(item.source.name.toLowerCase())) {
          warnings.push({
            field: `items[${idx}].label`,
            message: 'Label should not contain source name (use generic labels)'
          })
        }
      }
    })
  }

  if (!data.config) {
    errors.push({ field: 'config', message: 'Config is required' })
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * Checks if data is in multi-group ranking mode
 * @param {EvaluationData} data
 * @returns {boolean}
 */
export function isMultiGroupRanking(data) {
  return data?.config?.mode === RankingMode.MULTI_GROUP
}

/**
 * Gets groups from multi-group ranking config
 * @param {EvaluationData} data
 * @returns {RankingGroup[]}
 */
export function getRankingGroups(data) {
  if (!isMultiGroupRanking(data)) return []
  return data.config.groups || []
}

/**
 * Groups items by their group field
 * @param {Item[]} items
 * @returns {Object<string, Item[]>}
 */
export function groupItemsByGroup(items) {
  if (!items) return {}

  const groups = {}
  for (const item of items) {
    const groupId = item.group || 'default'
    if (!groups[groupId]) groups[groupId] = []
    groups[groupId].push(item)
  }
  return groups
}

/**
 * Gets localized text from a LocalizedString
 * @param {LocalizedString|string} value - Localized string or plain string
 * @param {string} [locale='de'] - Locale to use
 * @returns {string}
 */
export function getLocalizedText(value, locale = 'de') {
  if (!value) return ''
  if (typeof value === 'string') return value
  return value[locale] || value.de || value.en || ''
}

// =============================================================================
// Export all
// =============================================================================

export default {
  // Enums
  SchemaVersion,
  EvaluationType,
  SourceType,
  ContentType,
  RankingMode,
  LabelingMode,
  FUNCTION_TYPE_MAP,
  EVALUATION_TYPE_TO_ID,

  // Factory functions
  createDefaultRankingBuckets,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultAuthenticityOptions,
  createSimpleRankingConfig,
  createRatingConfig,

  // Validation
  validateEvaluationData,

  // Helpers
  isMultiGroupRanking,
  getRankingGroups,
  groupItemsByGroup,
  getLocalizedText
}
