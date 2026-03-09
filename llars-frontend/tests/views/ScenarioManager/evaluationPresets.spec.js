/**
 * Evaluation Presets Tests
 *
 * Tests for the evaluation presets configuration module.
 * Validates preset definitions, structure, utility functions, and config validation.
 * Test IDs: PRESET_001 - PRESET_070
 */

import { describe, it, expect } from 'vitest'

import {
  EVAL_TYPES,
  TYPE_ID_MAP,
  ID_TYPE_MAP,
  BASE_TYPE_MAP,
  isLlarsDomainType,
  getBaseType,
  RATING_PRESETS,
  RANKING_PRESETS,
  LABELING_PRESETS,
  COMPARISON_PRESETS,
  MAIL_RATING_PRESETS,
  AUTHENTICITY_PRESETS,
  PRESETS_BY_TYPE,
  DEFAULT_CONFIG_BY_TYPE,
  TYPE_INFO,
  getPreset,
  getPresetsArray,
  getDefaultConfig,
  cloneConfig,
  validateConfig,
  getTypesByCategory,
  getGeneralTypes,
  getLlarsTypes,
  createDefaultScale,
  createDefaultRatingDimensions,
  createDefaultRankingBuckets
} from '@/views/ScenarioManager/config/evaluationPresets'

// =============================================================================
// Helper to validate localized string shape { de: string, en: string }
// =============================================================================
function expectLocalizedString(obj, path = '') {
  expect(obj, `${path} should exist`).toBeDefined()
  expect(typeof obj.de, `${path}.de should be a string`).toBe('string')
  expect(typeof obj.en, `${path}.en should be a string`).toBe('string')
  expect(obj.de.length, `${path}.de should not be empty`).toBeGreaterThan(0)
  expect(obj.en.length, `${path}.en should not be empty`).toBeGreaterThan(0)
}

// Helper: validate a preset has all required fields
function expectValidPreset(preset, presetId) {
  expect(preset.id, `${presetId}: id`).toBe(presetId)
  expectLocalizedString(preset.name, `${presetId}.name`)
  expectLocalizedString(preset.description, `${presetId}.description`)
  expect(preset.config, `${presetId}: config should exist`).toBeDefined()
  expect(typeof preset.config, `${presetId}: config should be an object`).toBe('object')
}

// =============================================================================
// EVAL_TYPES & Type Mappings
// =============================================================================

describe('EVAL_TYPES', () => {
  it('PRESET_001: defines all six evaluation types', () => {
    expect(EVAL_TYPES.RATING).toBe('rating')
    expect(EVAL_TYPES.RANKING).toBe('ranking')
    expect(EVAL_TYPES.LABELING).toBe('labeling')
    expect(EVAL_TYPES.COMPARISON).toBe('comparison')
    expect(EVAL_TYPES.MAIL_RATING).toBe('mail_rating')
    expect(EVAL_TYPES.AUTHENTICITY).toBe('authenticity')
  })

  it('PRESET_002: has exactly 6 types', () => {
    expect(Object.keys(EVAL_TYPES)).toHaveLength(6)
  })
})

describe('TYPE_ID_MAP', () => {
  it('PRESET_003: maps function_type_ids to evaluation types', () => {
    expect(TYPE_ID_MAP[1]).toBe('ranking')
    expect(TYPE_ID_MAP[2]).toBe('rating')
    expect(TYPE_ID_MAP[3]).toBe('mail_rating')
    expect(TYPE_ID_MAP[4]).toBe('comparison')
    expect(TYPE_ID_MAP[5]).toBe('authenticity')
    expect(TYPE_ID_MAP[7]).toBe('labeling')
  })

  it('PRESET_004: does not contain function_type_id 6', () => {
    expect(TYPE_ID_MAP[6]).toBeUndefined()
  })
})

describe('ID_TYPE_MAP', () => {
  it('PRESET_005: maps evaluation types to function_type_ids', () => {
    expect(ID_TYPE_MAP.ranking).toBe(1)
    expect(ID_TYPE_MAP.rating).toBe(2)
    expect(ID_TYPE_MAP.mail_rating).toBe(3)
    expect(ID_TYPE_MAP.comparison).toBe(4)
    expect(ID_TYPE_MAP.authenticity).toBe(5)
    expect(ID_TYPE_MAP.labeling).toBe(7)
  })

  it('PRESET_006: is the inverse of TYPE_ID_MAP', () => {
    for (const [id, type] of Object.entries(TYPE_ID_MAP)) {
      expect(ID_TYPE_MAP[type]).toBe(Number(id))
    }
  })
})

// =============================================================================
// BASE_TYPE_MAP & Domain Type Functions
// =============================================================================

describe('BASE_TYPE_MAP', () => {
  it('PRESET_007: general types map to themselves', () => {
    expect(BASE_TYPE_MAP[EVAL_TYPES.RATING]).toBe(EVAL_TYPES.RATING)
    expect(BASE_TYPE_MAP[EVAL_TYPES.RANKING]).toBe(EVAL_TYPES.RANKING)
    expect(BASE_TYPE_MAP[EVAL_TYPES.LABELING]).toBe(EVAL_TYPES.LABELING)
    expect(BASE_TYPE_MAP[EVAL_TYPES.COMPARISON]).toBe(EVAL_TYPES.COMPARISON)
  })

  it('PRESET_008: domain types map to their base types', () => {
    expect(BASE_TYPE_MAP[EVAL_TYPES.MAIL_RATING]).toBe(EVAL_TYPES.RATING)
    expect(BASE_TYPE_MAP[EVAL_TYPES.AUTHENTICITY]).toBe(EVAL_TYPES.LABELING)
  })
})

describe('isLlarsDomainType', () => {
  it('PRESET_009: returns true for LLARS domain types', () => {
    expect(isLlarsDomainType(EVAL_TYPES.MAIL_RATING)).toBe(true)
    expect(isLlarsDomainType(EVAL_TYPES.AUTHENTICITY)).toBe(true)
  })

  it('PRESET_010: returns false for general types', () => {
    expect(isLlarsDomainType(EVAL_TYPES.RATING)).toBe(false)
    expect(isLlarsDomainType(EVAL_TYPES.RANKING)).toBe(false)
    expect(isLlarsDomainType(EVAL_TYPES.LABELING)).toBe(false)
    expect(isLlarsDomainType(EVAL_TYPES.COMPARISON)).toBe(false)
  })

  it('PRESET_011: returns false for unknown types', () => {
    expect(isLlarsDomainType('unknown')).toBe(false)
    expect(isLlarsDomainType(null)).toBe(false)
  })
})

describe('getBaseType', () => {
  it('PRESET_012: returns base type for domain types', () => {
    expect(getBaseType(EVAL_TYPES.MAIL_RATING)).toBe(EVAL_TYPES.RATING)
    expect(getBaseType(EVAL_TYPES.AUTHENTICITY)).toBe(EVAL_TYPES.LABELING)
  })

  it('PRESET_013: returns the type itself for general types', () => {
    expect(getBaseType(EVAL_TYPES.RATING)).toBe(EVAL_TYPES.RATING)
    expect(getBaseType(EVAL_TYPES.RANKING)).toBe(EVAL_TYPES.RANKING)
  })

  it('PRESET_014: returns the input for unknown types', () => {
    expect(getBaseType('unknown')).toBe('unknown')
  })
})

// =============================================================================
// RATING_PRESETS
// =============================================================================

describe('RATING_PRESETS', () => {
  const expectedIds = [
    'likert-5', 'likert-7', 'stars-5', 'stars-10', 'percentage', 'custom',
    'llm-judge-standard', 'summeval', 'response-quality',
    'text-quality-3dim', 'news-article', 'multi-dimensional-custom'
  ]

  it('PRESET_015: contains all expected rating presets', () => {
    for (const id of expectedIds) {
      expect(RATING_PRESETS[id], `Missing preset: ${id}`).toBeDefined()
    }
  })

  it('PRESET_016: every preset has required fields', () => {
    for (const [id, preset] of Object.entries(RATING_PRESETS)) {
      expectValidPreset(preset, id)
    }
  })

  it('PRESET_017: likert-5 has correct scale range', () => {
    const config = RATING_PRESETS['likert-5'].config
    expect(config.type).toBe('likert')
    expect(config.min).toBe(1)
    expect(config.max).toBe(5)
    expect(config.step).toBe(1)
    expect(config.showLabels).toBe(true)
    expect(config.allowHalf).toBe(false)
  })

  it('PRESET_018: likert-5 has labels for all scale values', () => {
    const labels = RATING_PRESETS['likert-5'].config.labels
    for (let i = 1; i <= 5; i++) {
      expectLocalizedString(labels[i], `label[${i}]`)
    }
  })

  it('PRESET_019: likert-7 has 7-point scale', () => {
    const config = RATING_PRESETS['likert-7'].config
    expect(config.min).toBe(1)
    expect(config.max).toBe(7)
    expect(Object.keys(config.labels)).toHaveLength(7)
  })

  it('PRESET_020: stars-5 allows half ratings', () => {
    expect(RATING_PRESETS['stars-5'].config.allowHalf).toBe(true)
    expect(RATING_PRESETS['stars-5'].config.type).toBe('stars')
  })

  it('PRESET_021: percentage preset has 0-100 range', () => {
    const config = RATING_PRESETS['percentage'].config
    expect(config.type).toBe('slider')
    expect(config.min).toBe(0)
    expect(config.max).toBe(100)
    expect(config.unit).toBe('%')
  })

  it('PRESET_022: llm-judge-standard has 4 dimensions with equal weights', () => {
    const config = RATING_PRESETS['llm-judge-standard'].config
    expect(config.type).toBe('multi-dimensional')
    expect(config.dimensions).toHaveLength(4)

    const dimIds = config.dimensions.map(d => d.id)
    expect(dimIds).toEqual(['coherence', 'fluency', 'relevance', 'consistency'])

    const totalWeight = config.dimensions.reduce((sum, d) => sum + d.weight, 0)
    expect(totalWeight).toBeCloseTo(1.0)
  })

  it('PRESET_023: llm-judge-standard dimensions have localized names and descriptions', () => {
    for (const dim of RATING_PRESETS['llm-judge-standard'].config.dimensions) {
      expectLocalizedString(dim.name, `dimension ${dim.id} name`)
      expectLocalizedString(dim.description, `dimension ${dim.id} description`)
    }
  })

  it('PRESET_024: summeval has 7 dimensions with mixed scales', () => {
    const config = RATING_PRESETS['summeval'].config
    expect(config.dimensions).toHaveLength(7)

    // Check that some dimensions have custom scales
    const creativity = config.dimensions.find(d => d.id === 'creativity')
    expect(creativity.scale).toBeDefined()
    expect(creativity.scale.min).toBe(0)
    expect(creativity.scale.max).toBe(9)

    const biasFree = config.dimensions.find(d => d.id === 'bias_free')
    expect(biasFree.scale.type).toBe('binary')

    // structure uses global scale (no custom scale)
    const structure = config.dimensions.find(d => d.id === 'structure')
    expect(structure.scale).toBeUndefined()
  })

  it('PRESET_025: summeval dimension weights sum to ~1.0', () => {
    const total = RATING_PRESETS['summeval'].config.dimensions
      .reduce((sum, d) => sum + d.weight, 0)
    expect(total).toBeCloseTo(1.0)
  })

  it('PRESET_026: multi-dimensional presets have showOverallScore and allowFeedback', () => {
    const multiDimPresets = ['llm-judge-standard', 'response-quality', 'text-quality-3dim', 'news-article']
    for (const id of multiDimPresets) {
      const config = RATING_PRESETS[id].config
      expect(config.showOverallScore, `${id}.showOverallScore`).toBe(true)
      expect(typeof config.allowFeedback, `${id}.allowFeedback`).toBe('boolean')
    }
  })

  it('PRESET_027: multi-dimensional-custom starts with empty dimensions', () => {
    const config = RATING_PRESETS['multi-dimensional-custom'].config
    expect(config.type).toBe('multi-dimensional')
    expect(config.dimensions).toEqual([])
  })
})

// =============================================================================
// RANKING_PRESETS
// =============================================================================

describe('RANKING_PRESETS', () => {
  const expectedIds = ['buckets-3', 'buckets-5', 'priority', 'relevance', 'custom']

  it('PRESET_028: contains all expected ranking presets', () => {
    for (const id of expectedIds) {
      expect(RANKING_PRESETS[id], `Missing preset: ${id}`).toBeDefined()
    }
  })

  it('PRESET_029: every preset has required fields', () => {
    for (const [id, preset] of Object.entries(RANKING_PRESETS)) {
      expectValidPreset(preset, id)
    }
  })

  it('PRESET_030: buckets-3 has 3 buckets with colors', () => {
    const config = RANKING_PRESETS['buckets-3'].config
    expect(config.type).toBe('buckets')
    expect(config.buckets).toHaveLength(3)
    for (const bucket of config.buckets) {
      expect(bucket.id).toBeDefined()
      expectLocalizedString(bucket.name, `bucket ${bucket.id}`)
      expect(bucket.color).toMatch(/^#[0-9a-fA-F]{6}$/)
    }
  })

  it('PRESET_031: buckets-5 has 5 buckets', () => {
    expect(RANKING_PRESETS['buckets-5'].config.buckets).toHaveLength(5)
  })

  it('PRESET_032: priority preset is ordered type', () => {
    const config = RANKING_PRESETS['priority'].config
    expect(config.type).toBe('ordered')
    expect(config.showPosition).toBe(true)
    expectLocalizedString(config.labels.first, 'priority.labels.first')
    expectLocalizedString(config.labels.last, 'priority.labels.last')
  })

  it('PRESET_033: relevance preset allows ties', () => {
    expect(RANKING_PRESETS['relevance'].config.allowTies).toBe(true)
  })

  it('PRESET_034: custom ranking starts with empty buckets', () => {
    expect(RANKING_PRESETS['custom'].config.buckets).toEqual([])
  })

  it('PRESET_035: all bucket presets have dragDrop enabled', () => {
    for (const preset of Object.values(RANKING_PRESETS)) {
      expect(preset.config.dragDrop).toBe(true)
    }
  })
})

// =============================================================================
// LABELING_PRESETS
// =============================================================================

describe('LABELING_PRESETS', () => {
  const expectedIds = ['binary-authentic', 'binary-sentiment', 'sentiment-3', 'topic-multilabel', 'custom']

  it('PRESET_036: contains all expected labeling presets', () => {
    for (const id of expectedIds) {
      expect(LABELING_PRESETS[id], `Missing preset: ${id}`).toBeDefined()
    }
  })

  it('PRESET_037: every preset has required fields', () => {
    for (const [id, preset] of Object.entries(LABELING_PRESETS)) {
      expectValidPreset(preset, id)
    }
  })

  it('PRESET_038: binary-authentic has 2 categories and unsure option', () => {
    const config = LABELING_PRESETS['binary-authentic'].config
    expect(config.type).toBe('binary')
    expect(config.categories).toHaveLength(2)
    expect(config.allowUnsure).toBe(true)
    expect(config.unsureOption).toBeDefined()
    expect(config.unsureOption.id).toBe('unsure')
  })

  it('PRESET_039: binary categories have icons and colors', () => {
    for (const cat of LABELING_PRESETS['binary-authentic'].config.categories) {
      expect(cat.icon).toBeDefined()
      expect(cat.color).toMatch(/^#[0-9a-fA-F]{6}$/)
    }
  })

  it('PRESET_040: sentiment-3 has 3 categories (multiclass)', () => {
    const config = LABELING_PRESETS['sentiment-3'].config
    expect(config.type).toBe('multiclass')
    expect(config.categories).toHaveLength(3)
    expect(config.multiLabel).toBe(false)
  })

  it('PRESET_041: topic-multilabel enables multiLabel', () => {
    const config = LABELING_PRESETS['topic-multilabel'].config
    expect(config.type).toBe('multilabel')
    expect(config.multiLabel).toBe(true)
    expect(config.minLabels).toBe(1)
    expect(config.maxLabels).toBeNull()
  })
})

// =============================================================================
// COMPARISON_PRESETS
// =============================================================================

describe('COMPARISON_PRESETS', () => {
  const expectedIds = ['pairwise', 'pairwise-confidence', 'multicriteria', 'tournament', 'custom']

  it('PRESET_042: contains all expected comparison presets', () => {
    for (const id of expectedIds) {
      expect(COMPARISON_PRESETS[id], `Missing preset: ${id}`).toBeDefined()
    }
  })

  it('PRESET_043: every preset has required fields', () => {
    for (const [id, preset] of Object.entries(COMPARISON_PRESETS)) {
      expectValidPreset(preset, id)
    }
  })

  it('PRESET_044: pairwise has basic comparison config', () => {
    const config = COMPARISON_PRESETS['pairwise'].config
    expect(config.type).toBe('pairwise')
    expect(config.itemsPerComparison).toBe(2)
    expect(config.allowTie).toBe(true)
    expect(config.showConfidence).toBe(false)
    expect(config.criteria).toHaveLength(1)
  })

  it('PRESET_045: pairwise-confidence shows confidence scale', () => {
    const config = COMPARISON_PRESETS['pairwise-confidence'].config
    expect(config.showConfidence).toBe(true)
    expect(config.confidenceScale).toEqual({ min: 1, max: 5 })
  })

  it('PRESET_046: multicriteria has 3 criteria with weights summing to 1.0', () => {
    const config = COMPARISON_PRESETS['multicriteria'].config
    expect(config.criteria).toHaveLength(3)
    const totalWeight = config.criteria.reduce((sum, c) => sum + c.weight, 0)
    expect(totalWeight).toBeCloseTo(1.0)
  })

  it('PRESET_047: tournament does not allow ties', () => {
    const config = COMPARISON_PRESETS['tournament'].config
    expect(config.type).toBe('tournament')
    expect(config.allowTie).toBe(false)
    expect(config.rounds).toBe('auto')
  })

  it('PRESET_048: comparison presets have localized questions', () => {
    for (const preset of Object.values(COMPARISON_PRESETS)) {
      expectLocalizedString(preset.config.question, `${preset.id}.question`)
    }
  })
})

// =============================================================================
// MAIL_RATING_PRESETS (LLARS Domain)
// =============================================================================

describe('MAIL_RATING_PRESETS', () => {
  it('PRESET_049: contains expected presets', () => {
    expect(MAIL_RATING_PRESETS['mail-verlauf-bewertung']).toBeDefined()
    expect(MAIL_RATING_PRESETS['custom']).toBeDefined()
  })

  it('PRESET_050: mail-verlauf-bewertung is marked as llarsSpecific and isDefault', () => {
    const preset = MAIL_RATING_PRESETS['mail-verlauf-bewertung']
    expect(preset.llarsSpecific).toBe(true)
    expect(preset.isDefault).toBe(true)
  })

  it('PRESET_051: mail-verlauf-bewertung has 4 dimensions', () => {
    const config = MAIL_RATING_PRESETS['mail-verlauf-bewertung'].config
    expect(config.type).toBe('multi-dimensional')
    expect(config.baseType).toBe('rating')
    expect(config.dimensions).toHaveLength(4)

    const dimIds = config.dimensions.map(d => d.id)
    expect(dimIds).toEqual(['client_coherence', 'counsellor_coherence', 'quality', 'overall'])
  })

  it('PRESET_052: overall dimension has binary scale', () => {
    const overall = MAIL_RATING_PRESETS['mail-verlauf-bewertung'].config.dimensions
      .find(d => d.id === 'overall')
    expect(overall.scale).toBeDefined()
    expect(overall.scale.type).toBe('binary')
    expect(overall.scale.min).toBe(1)
    expect(overall.scale.max).toBe(2)
  })

  it('PRESET_053: mail-verlauf-bewertung has inverted label scale (1=Sehr gut, 5=Sehr schlecht)', () => {
    const labels = MAIL_RATING_PRESETS['mail-verlauf-bewertung'].config.labels
    expect(labels[1].de).toBe('Sehr gut')
    expect(labels[5].de).toBe('Sehr schlecht')
  })

  it('PRESET_054: mail-verlauf-bewertung has colors for scale values', () => {
    const colors = MAIL_RATING_PRESETS['mail-verlauf-bewertung'].config.colors
    expect(colors).toBeDefined()
    expect(Object.keys(colors)).toHaveLength(5)
    for (const color of Object.values(colors)) {
      expect(color).toMatch(/^#[0-9a-fA-F]{6}$/)
    }
  })
})

// =============================================================================
// AUTHENTICITY_PRESETS (LLARS Domain)
// =============================================================================

describe('AUTHENTICITY_PRESETS', () => {
  const expectedIds = ['nachricht-echtheit', 'ki-generiert', 'dringlichkeit', 'custom']

  it('PRESET_055: contains all expected authenticity presets', () => {
    for (const id of expectedIds) {
      expect(AUTHENTICITY_PRESETS[id], `Missing preset: ${id}`).toBeDefined()
    }
  })

  it('PRESET_056: all presets are marked as llarsSpecific', () => {
    for (const preset of Object.values(AUTHENTICITY_PRESETS)) {
      expect(preset.llarsSpecific).toBe(true)
    }
  })

  it('PRESET_057: nachricht-echtheit has binary type with baseType labeling', () => {
    const config = AUTHENTICITY_PRESETS['nachricht-echtheit'].config
    expect(config.type).toBe('binary')
    expect(config.baseType).toBe('labeling')
    expect(config.requireReasoning).toBe(true)
    expect(config.categories).toHaveLength(2)
  })

  it('PRESET_058: dringlichkeit has 4 urgency categories (multiclass)', () => {
    const config = AUTHENTICITY_PRESETS['dringlichkeit'].config
    expect(config.type).toBe('multiclass')
    expect(config.categories).toHaveLength(4)
    expect(config.categories[0].id).toBe('akut')
    expect(config.categories[3].id).toBe('niedrig')
  })
})

// =============================================================================
// PRESETS_BY_TYPE
// =============================================================================

describe('PRESETS_BY_TYPE', () => {
  it('PRESET_059: maps all six types to their preset objects', () => {
    expect(PRESETS_BY_TYPE[EVAL_TYPES.RATING]).toBe(RATING_PRESETS)
    expect(PRESETS_BY_TYPE[EVAL_TYPES.RANKING]).toBe(RANKING_PRESETS)
    expect(PRESETS_BY_TYPE[EVAL_TYPES.LABELING]).toBe(LABELING_PRESETS)
    expect(PRESETS_BY_TYPE[EVAL_TYPES.COMPARISON]).toBe(COMPARISON_PRESETS)
    expect(PRESETS_BY_TYPE[EVAL_TYPES.MAIL_RATING]).toBe(MAIL_RATING_PRESETS)
    expect(PRESETS_BY_TYPE[EVAL_TYPES.AUTHENTICITY]).toBe(AUTHENTICITY_PRESETS)
  })
})

// =============================================================================
// DEFAULT_CONFIG_BY_TYPE
// =============================================================================

describe('DEFAULT_CONFIG_BY_TYPE', () => {
  it('PRESET_060: provides a default config for every type', () => {
    for (const type of Object.values(EVAL_TYPES)) {
      expect(DEFAULT_CONFIG_BY_TYPE[type], `No default config for ${type}`).toBeDefined()
    }
  })

  it('PRESET_061: rating default is llm-judge-standard config', () => {
    expect(DEFAULT_CONFIG_BY_TYPE[EVAL_TYPES.RATING]).toBe(
      RATING_PRESETS['llm-judge-standard'].config
    )
  })

  it('PRESET_062: ranking default is buckets-3 config', () => {
    expect(DEFAULT_CONFIG_BY_TYPE[EVAL_TYPES.RANKING]).toBe(
      RANKING_PRESETS['buckets-3'].config
    )
  })
})

// =============================================================================
// Utility Functions
// =============================================================================

describe('getPreset', () => {
  it('PRESET_063: returns preset by type and id', () => {
    const result = getPreset(EVAL_TYPES.RATING, 'likert-5')
    expect(result).toBe(RATING_PRESETS['likert-5'])
  })

  it('PRESET_064: returns null for unknown preset id', () => {
    expect(getPreset(EVAL_TYPES.RATING, 'nonexistent')).toBeNull()
  })

  it('PRESET_065: returns null for unknown type', () => {
    expect(getPreset('nonexistent', 'likert-5')).toBeNull()
  })
})

describe('getPresetsArray', () => {
  it('PRESET_066: returns array of presets for a type', () => {
    const arr = getPresetsArray(EVAL_TYPES.RANKING)
    expect(Array.isArray(arr)).toBe(true)
    expect(arr.length).toBe(Object.keys(RANKING_PRESETS).length)
  })

  it('PRESET_067: returns empty array for unknown type', () => {
    expect(getPresetsArray('nonexistent')).toEqual([])
  })
})

describe('getDefaultConfig', () => {
  it('PRESET_068: returns default config for valid type', () => {
    expect(getDefaultConfig(EVAL_TYPES.RATING)).toBe(DEFAULT_CONFIG_BY_TYPE[EVAL_TYPES.RATING])
  })

  it('PRESET_069: returns null for unknown type', () => {
    expect(getDefaultConfig('nonexistent')).toBeNull()
  })
})

describe('cloneConfig', () => {
  it('PRESET_070: creates a deep copy of a config', () => {
    const original = RATING_PRESETS['llm-judge-standard'].config
    const copy = cloneConfig(original)

    expect(copy).toEqual(original)
    expect(copy).not.toBe(original)
    expect(copy.dimensions).not.toBe(original.dimensions)
    // Mutating the copy should not affect the original
    copy.dimensions.push({ id: 'new' })
    expect(original.dimensions).toHaveLength(4)
  })
})

// =============================================================================
// validateConfig
// =============================================================================

describe('validateConfig', () => {
  it('PRESET_071: returns invalid for null config', () => {
    const result = validateConfig(EVAL_TYPES.RATING, null)
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('Config is required')
  })

  it('PRESET_072: validates rating config - min must be less than max', () => {
    const result = validateConfig(EVAL_TYPES.RATING, { min: 5, max: 3, step: 1 })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('Min must be less than max')
  })

  it('PRESET_073: validates rating config - step must be positive', () => {
    const result = validateConfig(EVAL_TYPES.RATING, { min: 1, max: 5, step: 0 })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('Step must be positive')
  })

  it('PRESET_074: validates valid rating config', () => {
    const result = validateConfig(EVAL_TYPES.RATING, { min: 1, max: 5, step: 1 })
    expect(result.valid).toBe(true)
    expect(result.errors).toHaveLength(0)
  })

  it('PRESET_075: validates ranking config - needs at least 2 buckets', () => {
    const result = validateConfig(EVAL_TYPES.RANKING, { type: 'buckets', buckets: [{ id: 1 }] })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('At least 2 buckets are required')
  })

  it('PRESET_076: validates labeling config - needs at least 2 categories', () => {
    const result = validateConfig(EVAL_TYPES.LABELING, { categories: [] })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('At least 2 categories are required')
  })

  it('PRESET_077: validates comparison config - needs at least 1 criterion', () => {
    const result = validateConfig(EVAL_TYPES.COMPARISON, { criteria: [] })
    expect(result.valid).toBe(false)
    expect(result.errors).toContain('At least 1 criterion is required')
  })

  it('PRESET_078: all default configs pass validation for their type', () => {
    // rating, ranking, labeling, comparison all have validateConfig logic
    for (const type of [EVAL_TYPES.RATING, EVAL_TYPES.RANKING, EVAL_TYPES.LABELING, EVAL_TYPES.COMPARISON]) {
      const config = DEFAULT_CONFIG_BY_TYPE[type]
      const result = validateConfig(type, config)
      expect(result.valid, `Default config for ${type} should be valid: ${JSON.stringify(result.errors)}`).toBe(true)
    }
  })
})

// =============================================================================
// TYPE_INFO
// =============================================================================

describe('TYPE_INFO', () => {
  it('PRESET_079: has info for every evaluation type', () => {
    for (const type of Object.values(EVAL_TYPES)) {
      const info = TYPE_INFO[type]
      expect(info, `Missing TYPE_INFO for ${type}`).toBeDefined()
      expectLocalizedString(info.name, `TYPE_INFO[${type}].name`)
      expectLocalizedString(info.description, `TYPE_INFO[${type}].description`)
      expect(info.icon, `TYPE_INFO[${type}].icon`).toBeDefined()
      expect(info.color, `TYPE_INFO[${type}].color`).toMatch(/^#[0-9a-fA-F]{6}$/)
      expect(info.category, `TYPE_INFO[${type}].category`).toBeDefined()
    }
  })

  it('PRESET_080: general types have category "general"', () => {
    expect(TYPE_INFO[EVAL_TYPES.RATING].category).toBe('general')
    expect(TYPE_INFO[EVAL_TYPES.RANKING].category).toBe('general')
    expect(TYPE_INFO[EVAL_TYPES.LABELING].category).toBe('general')
    expect(TYPE_INFO[EVAL_TYPES.COMPARISON].category).toBe('general')
  })

  it('PRESET_081: LLARS types have category "llars" and baseType', () => {
    expect(TYPE_INFO[EVAL_TYPES.MAIL_RATING].category).toBe('llars')
    expect(TYPE_INFO[EVAL_TYPES.MAIL_RATING].baseType).toBe(EVAL_TYPES.RATING)
    expect(TYPE_INFO[EVAL_TYPES.AUTHENTICITY].category).toBe('llars')
    expect(TYPE_INFO[EVAL_TYPES.AUTHENTICITY].baseType).toBe(EVAL_TYPES.LABELING)
  })
})

// =============================================================================
// Category Functions
// =============================================================================

describe('getTypesByCategory', () => {
  it('PRESET_082: returns general and llars categories', () => {
    const cats = getTypesByCategory()
    expect(cats.general).toHaveLength(4)
    expect(cats.llars).toHaveLength(2)
    expect(cats.general).toContain(EVAL_TYPES.RATING)
    expect(cats.llars).toContain(EVAL_TYPES.MAIL_RATING)
  })
})

describe('getGeneralTypes', () => {
  it('PRESET_083: returns exactly the 4 general types', () => {
    const types = getGeneralTypes()
    expect(types).toHaveLength(4)
    expect(types).toEqual([EVAL_TYPES.RATING, EVAL_TYPES.RANKING, EVAL_TYPES.LABELING, EVAL_TYPES.COMPARISON])
  })
})

describe('getLlarsTypes', () => {
  it('PRESET_084: returns the 2 LLARS-specific types', () => {
    const types = getLlarsTypes()
    expect(types).toHaveLength(2)
    expect(types).toEqual([EVAL_TYPES.MAIL_RATING, EVAL_TYPES.AUTHENTICITY])
  })
})

// =============================================================================
// Re-exported Factory Functions
// =============================================================================

describe('createDefaultScale', () => {
  it('PRESET_085: creates 1-5 scale with labels', () => {
    const scale = createDefaultScale()
    expect(scale.min).toBe(1)
    expect(scale.max).toBe(5)
    expect(scale.step).toBe(1)
    expect(Object.keys(scale.labels)).toHaveLength(5)
  })
})

describe('createDefaultRatingDimensions', () => {
  it('PRESET_086: creates 4 default dimensions', () => {
    const dims = createDefaultRatingDimensions()
    expect(dims).toHaveLength(4)
    expect(dims.map(d => d.id)).toEqual(['coherence', 'fluency', 'relevance', 'consistency'])
    const totalWeight = dims.reduce((sum, d) => sum + d.weight, 0)
    expect(totalWeight).toBeCloseTo(1.0)
  })
})

describe('createDefaultRankingBuckets', () => {
  it('PRESET_087: creates 3 default buckets', () => {
    const buckets = createDefaultRankingBuckets()
    expect(buckets).toHaveLength(3)
    expect(buckets[0].id).toBe('good')
    expect(buckets[2].id).toBe('poor')
  })
})
