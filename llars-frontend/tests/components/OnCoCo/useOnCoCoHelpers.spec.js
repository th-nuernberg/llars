/**
 * useOnCoCoHelpers Composable Tests
 *
 * Tests for status helpers, formatting, and pillar helpers.
 * Test IDs: ONCOCO_HELP_001 - ONCOCO_HELP_025
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key, params) => params ? `${key}:${JSON.stringify(params)}` : key),
    locale: { value: 'de' }
  }))
}))

import { useOnCoCoHelpers } from '@/components/OnCoCo/OnCoCoResults/composables/useOnCoCoHelpers'

describe('useOnCoCoHelpers', () => {
  let helpers

  beforeEach(() => {
    helpers = useOnCoCoHelpers()
  })

  // ==================== Status Helpers ====================

  describe('getStatusColor', () => {
    it('ONCOCO_HELP_001: returns grey for pending', () => {
      expect(helpers.getStatusColor('pending')).toBe('grey')
    })

    it('ONCOCO_HELP_002: returns info for running', () => {
      expect(helpers.getStatusColor('running')).toBe('info')
    })

    it('ONCOCO_HELP_003: returns success for completed', () => {
      expect(helpers.getStatusColor('completed')).toBe('success')
    })

    it('ONCOCO_HELP_004: returns error for failed', () => {
      expect(helpers.getStatusColor('failed')).toBe('error')
    })

    it('ONCOCO_HELP_005: returns grey for unknown status', () => {
      expect(helpers.getStatusColor('unknown')).toBe('grey')
    })
  })

  describe('getStatusIcon', () => {
    it('ONCOCO_HELP_006: returns clock icon for pending', () => {
      expect(helpers.getStatusIcon('pending')).toBe('mdi-clock-outline')
    })

    it('ONCOCO_HELP_007: returns play icon for running', () => {
      expect(helpers.getStatusIcon('running')).toBe('mdi-play-circle')
    })

    it('ONCOCO_HELP_008: returns check icon for completed', () => {
      expect(helpers.getStatusIcon('completed')).toBe('mdi-check-circle')
    })

    it('ONCOCO_HELP_009: returns alert icon for failed', () => {
      expect(helpers.getStatusIcon('failed')).toBe('mdi-alert-circle')
    })

    it('ONCOCO_HELP_010: returns help icon for unknown status', () => {
      expect(helpers.getStatusIcon('unknown')).toBe('mdi-help-circle')
    })
  })

  describe('getStatusText', () => {
    it('ONCOCO_HELP_011: returns translated text for known status', () => {
      expect(helpers.getStatusText('pending')).toBe('oncoco.status.pending')
    })

    it('ONCOCO_HELP_012: returns raw status for unknown status', () => {
      expect(helpers.getStatusText('custom_status')).toBe('custom_status')
    })
  })

  // ==================== Formatting Helpers ====================

  describe('formatDate', () => {
    it('ONCOCO_HELP_013: formats valid date', () => {
      const result = helpers.formatDate('2025-06-15T14:30:00Z')
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('ONCOCO_HELP_014: returns placeholder for null', () => {
      expect(helpers.formatDate(null)).toBe('oncoco.results.placeholders.date')
    })

    it('ONCOCO_HELP_015: returns placeholder for empty string', () => {
      expect(helpers.formatDate('')).toBe('oncoco.results.placeholders.date')
    })
  })

  describe('formatDuration', () => {
    it('ONCOCO_HELP_016: returns 0s for null', () => {
      expect(helpers.formatDuration(null)).toBe('0s')
    })

    it('ONCOCO_HELP_017: returns 0s for negative', () => {
      expect(helpers.formatDuration(-5)).toBe('0s')
    })

    it('ONCOCO_HELP_018: formats seconds under 60', () => {
      expect(helpers.formatDuration(45)).toBe('45s')
    })

    it('ONCOCO_HELP_019: formats minutes and seconds', () => {
      expect(helpers.formatDuration(125)).toBe('2m 5s')
    })

    it('ONCOCO_HELP_020: formats hours and minutes', () => {
      expect(helpers.formatDuration(3725)).toBe('1h 2m')
    })

    it('ONCOCO_HELP_021: rounds seconds correctly', () => {
      expect(helpers.formatDuration(0.4)).toBe('0s')
      expect(helpers.formatDuration(30.7)).toBe('31s')
    })
  })

  // ==================== Table Headers ====================

  describe('table headers', () => {
    it('ONCOCO_HELP_022: distributionHeaders has expected keys', () => {
      const keys = helpers.distributionHeaders.map(h => h.key)
      expect(keys).toContain('label')
      expect(keys).toContain('role')
      expect(keys).toContain('count')
    })

    it('ONCOCO_HELP_023: comparisonHeaders has expected keys', () => {
      const keys = helpers.comparisonHeaders.map(h => h.key)
      expect(keys).toContain('pillar_name')
      expect(keys).toContain('avg_confidence')
    })

    it('ONCOCO_HELP_024: sentenceHeaders has expected keys', () => {
      const keys = helpers.sentenceHeaders.map(h => h.key)
      expect(keys).toContain('sentence_text')
      expect(keys).toContain('confidence')
    })
  })
})
