/**
 * Formatters Utility Tests
 *
 * Tests for shared formatting functions (dates, durations, percentages, metrics, status).
 * Test IDs: UTIL_FMT_001 - UTIL_FMT_070
 */

import { describe, it, expect } from 'vitest'
import {
  formatDate,
  formatDateWithSeconds,
  formatDuration,
  formatDurationMinutes,
  formatPercentage,
  formatMetric,
  formatCriterionName,
  formatLikertMetric,
  getStatusIcon,
  getQueueStatusIcon,
  getStatusText,
  getQueueStatusText,
  getPillarName,
  getBiasLabel,
  parseUserProviderModelId
} from '@/utils/formatters'

// ==================== formatDate Tests ====================

describe('formatDate', () => {
  it('UTIL_FMT_001: returns "-" for null input', () => {
    expect(formatDate(null)).toBe('-')
  })

  it('UTIL_FMT_002: returns "-" for undefined input', () => {
    expect(formatDate(undefined)).toBe('-')
  })

  it('UTIL_FMT_003: returns "-" for empty string', () => {
    expect(formatDate('')).toBe('-')
  })

  it('UTIL_FMT_004: formats a valid ISO date string', () => {
    const result = formatDate('2025-06-15T14:30:00Z')
    // German locale: DD.MM.YYYY, HH:MM
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
    expect(result).toContain('15')
    expect(result).toContain('06')
    expect(result).toContain('2025')
  })

  it('UTIL_FMT_005: applies custom options', () => {
    const result = formatDate('2025-06-15T14:30:00Z', { weekday: 'long' })
    // Should include weekday in output
    expect(result.length).toBeGreaterThan(10)
  })

  it('UTIL_FMT_006: overrides default options', () => {
    const result = formatDate('2025-06-15T14:30:00Z', { hour: undefined, minute: undefined })
    // Should still produce a valid date string
    expect(typeof result).toBe('string')
    expect(result).not.toBe('-')
  })
})

// ==================== formatDateWithSeconds Tests ====================

describe('formatDateWithSeconds', () => {
  it('UTIL_FMT_007: returns "-" for null input', () => {
    expect(formatDateWithSeconds(null)).toBe('-')
  })

  it('UTIL_FMT_008: returns "-" for empty string', () => {
    expect(formatDateWithSeconds('')).toBe('-')
  })

  it('UTIL_FMT_009: formats date with seconds', () => {
    const result = formatDateWithSeconds('2025-06-15T14:30:45Z')
    expect(result).toMatch(/\d{2}\.\d{2}\.\d{4}/)
    expect(result).toContain('2025')
  })
})

// ==================== formatDuration Tests ====================

describe('formatDuration', () => {
  it('UTIL_FMT_010: returns "0s" for null', () => {
    expect(formatDuration(null)).toBe('0s')
  })

  it('UTIL_FMT_011: returns "0s" for 0', () => {
    expect(formatDuration(0)).toBe('0s')
  })

  it('UTIL_FMT_012: returns "0s" for negative values', () => {
    expect(formatDuration(-5)).toBe('0s')
  })

  it('UTIL_FMT_013: formats seconds under 60', () => {
    expect(formatDuration(45)).toBe('45s')
  })

  it('UTIL_FMT_014: rounds fractional seconds', () => {
    expect(formatDuration(45.7)).toBe('46s')
  })

  it('UTIL_FMT_015: formats minutes and seconds', () => {
    expect(formatDuration(200)).toBe('3m 20s')
  })

  it('UTIL_FMT_016: formats exactly 60 seconds as 1m', () => {
    expect(formatDuration(60)).toBe('1m 0s')
  })

  it('UTIL_FMT_017: formats hours and minutes', () => {
    expect(formatDuration(8100)).toBe('2h 15m')
  })

  it('UTIL_FMT_018: formats exactly 1 hour', () => {
    expect(formatDuration(3600)).toBe('1h 0m')
  })
})

// ==================== formatDurationMinutes Tests ====================

describe('formatDurationMinutes', () => {
  it('UTIL_FMT_019: returns "0 min" for null', () => {
    expect(formatDurationMinutes(null)).toBe('0 min')
  })

  it('UTIL_FMT_020: returns "0 min" for 0', () => {
    expect(formatDurationMinutes(0)).toBe('0 min')
  })

  it('UTIL_FMT_021: returns "0 min" for negative values', () => {
    expect(formatDurationMinutes(-10)).toBe('0 min')
  })

  it('UTIL_FMT_022: formats minutes under 60', () => {
    expect(formatDurationMinutes(30)).toBe('30 min')
  })

  it('UTIL_FMT_023: formats hours and minutes', () => {
    expect(formatDurationMinutes(90)).toBe('1h 30 min')
  })

  it('UTIL_FMT_024: formats exactly 60 minutes', () => {
    expect(formatDurationMinutes(60)).toBe('1h 0 min')
  })

  it('UTIL_FMT_025: formats large values', () => {
    expect(formatDurationMinutes(150)).toBe('2h 30 min')
  })
})

// ==================== formatPercentage Tests ====================

describe('formatPercentage', () => {
  it('UTIL_FMT_026: returns "-" for null', () => {
    expect(formatPercentage(null)).toBe('-')
  })

  it('UTIL_FMT_027: returns "-" for undefined', () => {
    expect(formatPercentage(undefined)).toBe('-')
  })

  it('UTIL_FMT_028: formats 0.755 as 75.5%', () => {
    expect(formatPercentage(0.755)).toBe('75.5%')
  })

  it('UTIL_FMT_029: formats 1.0 as 100.0%', () => {
    expect(formatPercentage(1.0)).toBe('100.0%')
  })

  it('UTIL_FMT_030: formats 0 as 0.0%', () => {
    expect(formatPercentage(0)).toBe('0.0%')
  })

  it('UTIL_FMT_031: respects custom decimal places', () => {
    expect(formatPercentage(0.7556, 2)).toBe('75.56%')
  })

  it('UTIL_FMT_032: formats with 0 decimal places', () => {
    expect(formatPercentage(0.756, 0)).toBe('76%')
  })
})

// ==================== formatMetric Tests ====================

describe('formatMetric', () => {
  it('UTIL_FMT_033: returns "-" for null', () => {
    expect(formatMetric(null)).toBe('-')
  })

  it('UTIL_FMT_034: returns "-" for undefined', () => {
    expect(formatMetric(undefined)).toBe('-')
  })

  it('UTIL_FMT_035: formats with default 2 decimals', () => {
    expect(formatMetric(3.14159)).toBe('3.14')
  })

  it('UTIL_FMT_036: formats with custom decimals', () => {
    expect(formatMetric(3.14159, 4)).toBe('3.1416')
  })

  it('UTIL_FMT_037: formats integer value', () => {
    expect(formatMetric(5, 2)).toBe('5.00')
  })
})

// ==================== formatCriterionName Tests ====================

describe('formatCriterionName', () => {
  it('UTIL_FMT_038: maps counsellor_coherence to German name', () => {
    expect(formatCriterionName('counsellor_coherence')).toBe('Berater-Kohärenz')
  })

  it('UTIL_FMT_039: maps client_coherence', () => {
    expect(formatCriterionName('client_coherence')).toBe('Klienten-Kohärenz')
  })

  it('UTIL_FMT_040: maps quality', () => {
    expect(formatCriterionName('quality')).toBe('Qualität')
  })

  it('UTIL_FMT_041: maps empathy', () => {
    expect(formatCriterionName('empathy')).toBe('Empathie')
  })

  it('UTIL_FMT_042: maps authenticity', () => {
    expect(formatCriterionName('authenticity')).toBe('Authentizität')
  })

  it('UTIL_FMT_043: maps solution_orientation', () => {
    expect(formatCriterionName('solution_orientation')).toBe('Lösungsorientierung')
  })

  it('UTIL_FMT_044: falls back to title-cased snake_case', () => {
    expect(formatCriterionName('some_unknown_metric')).toBe('Some Unknown Metric')
  })
})

// ==================== formatLikertMetric Tests ====================

describe('formatLikertMetric', () => {
  it('UTIL_FMT_045: is an alias for formatCriterionName', () => {
    expect(formatLikertMetric('empathy')).toBe(formatCriterionName('empathy'))
  })

  it('UTIL_FMT_046: handles unknown metric same as formatCriterionName', () => {
    expect(formatLikertMetric('custom_metric')).toBe('Custom Metric')
  })
})

// ==================== getStatusIcon Tests ====================

describe('getStatusIcon', () => {
  it('UTIL_FMT_047: returns correct icon for created', () => {
    expect(getStatusIcon('created')).toBe('mdi-file-document')
  })

  it('UTIL_FMT_048: returns correct icon for queued', () => {
    expect(getStatusIcon('queued')).toBe('mdi-clock-outline')
  })

  it('UTIL_FMT_049: returns correct icon for running', () => {
    expect(getStatusIcon('running')).toBe('mdi-play-circle')
  })

  it('UTIL_FMT_050: returns correct icon for completed', () => {
    expect(getStatusIcon('completed')).toBe('mdi-check-circle')
  })

  it('UTIL_FMT_051: returns correct icon for failed', () => {
    expect(getStatusIcon('failed')).toBe('mdi-alert-circle')
  })

  it('UTIL_FMT_052: returns fallback icon for unknown status', () => {
    expect(getStatusIcon('unknown')).toBe('mdi-help-circle')
  })
})

// ==================== getQueueStatusIcon Tests ====================

describe('getQueueStatusIcon', () => {
  it('UTIL_FMT_053: handles lowercase pending', () => {
    expect(getQueueStatusIcon('pending')).toBe('mdi-clock-outline')
  })

  it('UTIL_FMT_054: handles uppercase RUNNING', () => {
    expect(getQueueStatusIcon('RUNNING')).toBe('mdi-loading')
  })

  it('UTIL_FMT_055: returns fallback for unknown status', () => {
    expect(getQueueStatusIcon('cancelled')).toBe('mdi-help')
  })
})

// ==================== getStatusText Tests ====================

describe('getStatusText', () => {
  it('UTIL_FMT_056: returns German text for created', () => {
    expect(getStatusText('created')).toBe('Erstellt')
  })

  it('UTIL_FMT_057: returns German text for running', () => {
    expect(getStatusText('running')).toBe('Läuft')
  })

  it('UTIL_FMT_058: returns raw status for unknown', () => {
    expect(getStatusText('cancelled')).toBe('cancelled')
  })
})

// ==================== getQueueStatusText Tests ====================

describe('getQueueStatusText', () => {
  it('UTIL_FMT_059: handles lowercase completed', () => {
    expect(getQueueStatusText('completed')).toBe('Fertig')
  })

  it('UTIL_FMT_060: handles uppercase FAILED', () => {
    expect(getQueueStatusText('FAILED')).toBe('Fehler')
  })

  it('UTIL_FMT_061: returns raw status for unknown', () => {
    expect(getQueueStatusText('unknown')).toBe('unknown')
  })
})

// ==================== getPillarName Tests ====================

describe('getPillarName', () => {
  it('UTIL_FMT_062: returns name for pillar 1', () => {
    expect(getPillarName(1)).toBe('Rollenspiele')
  })

  it('UTIL_FMT_063: returns fallback for unknown pillar', () => {
    expect(getPillarName(99)).toBe('Säule 99')
  })
})

// ==================== getBiasLabel Tests ====================

describe('getBiasLabel', () => {
  it('UTIL_FMT_064: maps primacy', () => {
    expect(getBiasLabel('primacy')).toBe('Primacy Bias')
  })

  it('UTIL_FMT_065: maps balanced', () => {
    expect(getBiasLabel('balanced')).toBe('Ausbalanciert')
  })

  it('UTIL_FMT_066: returns Unbekannt for unknown', () => {
    expect(getBiasLabel('something')).toBe('Unbekannt')
  })
})

// ==================== parseUserProviderModelId Tests ====================

describe('parseUserProviderModelId', () => {
  it('UTIL_FMT_067: returns null for null input', () => {
    expect(parseUserProviderModelId(null)).toBeNull()
  })

  it('UTIL_FMT_068: returns null for non-string input', () => {
    expect(parseUserProviderModelId(123)).toBeNull()
  })

  it('UTIL_FMT_069: returns null for non-user-provider prefix', () => {
    expect(parseUserProviderModelId('Global/OpenAI/gpt-4')).toBeNull()
  })

  it('UTIL_FMT_070: returns null for empty user-provider prefix', () => {
    expect(parseUserProviderModelId('user-provider:')).toBeNull()
  })

  it('UTIL_FMT_071: parses new format with providerId, username, model', () => {
    const result = parseUserProviderModelId('user-provider:42:john:gpt-4o')
    expect(result).not.toBeNull()
    expect(result.providerId).toBe('42')
    expect(result.username).toBe('john')
    expect(result.modelName).toBe('gpt-4o')
    expect(result.providerLabel).toBe('OpenAI')
    expect(result.displayName).toBe('john/OpenAI/gpt-4o')
  })

  it('UTIL_FMT_072: parses old format without username', () => {
    const result = parseUserProviderModelId('user-provider:42:gpt-4o')
    expect(result).not.toBeNull()
    expect(result.providerId).toBe('42')
    expect(result.username).toBeNull()
    expect(result.modelName).toBe('gpt-4o')
  })

  it('UTIL_FMT_073: parses legacy slash format with username/provider/model', () => {
    const result = parseUserProviderModelId('user-provider:john/openai/gpt-4o')
    expect(result).not.toBeNull()
    expect(result.username).toBe('john')
    expect(result.providerLabel).toBe('OpenAI')
    expect(result.modelName).toBe('gpt-4o')
  })

  it('UTIL_FMT_074: infers OpenAI from gpt- prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:gpt-4o')
    expect(result.providerLabel).toBe('OpenAI')
  })

  it('UTIL_FMT_075: infers Anthropic from claude prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:claude-3-opus')
    expect(result.providerLabel).toBe('Anthropic')
  })

  it('UTIL_FMT_076: infers Google from gemini prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:gemini-pro')
    expect(result.providerLabel).toBe('Google')
  })

  it('UTIL_FMT_077: infers Mistral from mistral prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:mistral-large')
    expect(result.providerLabel).toBe('Mistral')
  })

  it('UTIL_FMT_078: providerNameHint overrides inference', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:gpt-4o', 'My Custom Provider')
    expect(result.providerLabel).toBe('My Custom Provider')
  })

  it('UTIL_FMT_079: normalizes provider label from model prefix slash', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:mistralai/Mistral-Small')
    expect(result.providerLabel).toBe('Mistral')
    expect(result.modelName).toBe('Mistral-Small')
  })

  it('UTIL_FMT_080: preserves unknown API prefix in model name, uses providerNameHint for label', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:meta-llama/Llama-3', 'IONOS')
    expect(result.providerLabel).toBe('IONOS')
    expect(result.modelName).toBe('meta-llama/Llama-3')
  })

  it('UTIL_FMT_081: displayName includes username when present', () => {
    const result = parseUserProviderModelId('user-provider:42:alice:gpt-4o')
    expect(result.displayName).toContain('alice/')
  })

  it('UTIL_FMT_082: displayName has no username prefix when absent', () => {
    const result = parseUserProviderModelId('user-provider:42:gpt-4o')
    // No username segment, so format is "ProviderLabel/model"
    expect(result.displayName).toBe('OpenAI/gpt-4o')
    expect(result.username).toBeNull()
  })

  it('UTIL_FMT_083: infers OpenAI from o1 prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:o1-preview')
    expect(result.providerLabel).toBe('OpenAI')
  })

  it('UTIL_FMT_084: infers Mistral from magistral prefix', () => {
    const result = parseUserProviderModelId('user-provider:42:user1:magistral-medium')
    expect(result.providerLabel).toBe('Mistral')
  })

  it('UTIL_FMT_085: normalizes IONOS provider label', () => {
    const result = parseUserProviderModelId('user-provider:john/ionos/llama-3')
    expect(result.providerLabel).toBe('IONOS')
  })
})
