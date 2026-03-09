/**
 * useJudgeHelpers Composable Tests
 *
 * Tests for color helpers, formatting, and export functions.
 * Test IDs: JUDGE_HELP_001 - JUDGE_HELP_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('vue-i18n', () => ({
  useI18n: vi.fn(() => ({
    t: vi.fn((key, params) => params ? `${key}:${JSON.stringify(params)}` : key),
    locale: { value: 'de' }
  }))
}))

vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

import axios from 'axios'
import { useJudgeHelpers } from '@/components/Judge/JudgeResults/composables/useJudgeHelpers'

describe('useJudgeHelpers', () => {
  let helpers

  beforeEach(() => {
    vi.clearAllMocks()
    helpers = useJudgeHelpers('session-123')
  })

  // ==================== Color Helpers ====================

  describe('getRankColor', () => {
    it('JUDGE_HELP_001: returns warning for index 0', () => {
      expect(helpers.getRankColor(0)).toBe('warning')
    })

    it('JUDGE_HELP_002: returns grey-lighten-1 for index 1', () => {
      expect(helpers.getRankColor(1)).toBe('grey-lighten-1')
    })

    it('JUDGE_HELP_003: returns grey for out-of-range index', () => {
      expect(helpers.getRankColor(99)).toBe('grey')
    })
  })

  describe('getWinRateColor', () => {
    it('JUDGE_HELP_004: returns success for high win rate', () => {
      expect(helpers.getWinRateColor(0.8)).toBe('success')
    })

    it('JUDGE_HELP_005: returns info for moderate win rate', () => {
      expect(helpers.getWinRateColor(0.6)).toBe('info')
    })

    it('JUDGE_HELP_006: returns warning for low win rate', () => {
      expect(helpers.getWinRateColor(0.4)).toBe('warning')
    })

    it('JUDGE_HELP_007: returns error for very low win rate', () => {
      expect(helpers.getWinRateColor(0.2)).toBe('error')
    })
  })

  describe('getConfidenceColor', () => {
    it('JUDGE_HELP_008: returns success for >= 0.8', () => {
      expect(helpers.getConfidenceColor(0.9)).toBe('success')
    })

    it('JUDGE_HELP_009: returns info for >= 0.6', () => {
      expect(helpers.getConfidenceColor(0.7)).toBe('info')
    })

    it('JUDGE_HELP_010: returns warning for >= 0.4', () => {
      expect(helpers.getConfidenceColor(0.5)).toBe('warning')
    })

    it('JUDGE_HELP_011: returns error for < 0.4', () => {
      expect(helpers.getConfidenceColor(0.3)).toBe('error')
    })
  })

  describe('getScoreColor', () => {
    it('JUDGE_HELP_012: returns success for >= 4', () => {
      expect(helpers.getScoreColor(5)).toBe('success')
    })

    it('JUDGE_HELP_013: returns info for >= 3', () => {
      expect(helpers.getScoreColor(3)).toBe('info')
    })

    it('JUDGE_HELP_014: returns warning for >= 2', () => {
      expect(helpers.getScoreColor(2)).toBe('warning')
    })

    it('JUDGE_HELP_015: returns error for < 2', () => {
      expect(helpers.getScoreColor(1)).toBe('error')
    })
  })

  describe('getLikertConsistencyColor', () => {
    it('JUDGE_HELP_016: returns success for >= 0.7', () => {
      expect(helpers.getLikertConsistencyColor(0.8)).toBe('success')
    })

    it('JUDGE_HELP_017: returns warning for >= 0.5', () => {
      expect(helpers.getLikertConsistencyColor(0.6)).toBe('warning')
    })

    it('JUDGE_HELP_018: returns error for < 0.5', () => {
      expect(helpers.getLikertConsistencyColor(0.3)).toBe('error')
    })
  })

  describe('getConsistencyQualityColor', () => {
    it('JUDGE_HELP_019: returns success for excellent', () => {
      expect(helpers.getConsistencyQualityColor('excellent')).toBe('success')
    })

    it('JUDGE_HELP_020: returns info for good', () => {
      expect(helpers.getConsistencyQualityColor('good')).toBe('info')
    })

    it('JUDGE_HELP_021: returns warning for fair', () => {
      expect(helpers.getConsistencyQualityColor('fair')).toBe('warning')
    })

    it('JUDGE_HELP_022: returns error for poor', () => {
      expect(helpers.getConsistencyQualityColor('poor')).toBe('error')
    })

    it('JUDGE_HELP_023: returns grey for unknown', () => {
      expect(helpers.getConsistencyQualityColor('unknown')).toBe('grey')
    })
  })

  // ==================== Formatting ====================

  describe('formatDate', () => {
    it('JUDGE_HELP_024: formats valid date string', () => {
      const result = helpers.formatDate('2025-06-15T14:30:00Z')
      // Should return a formatted date string
      expect(typeof result).toBe('string')
      expect(result.length).toBeGreaterThan(0)
    })

    it('JUDGE_HELP_025: returns placeholder for null', () => {
      const result = helpers.formatDate(null)
      expect(result).toBe('judge.results.common.placeholder')
    })
  })

  describe('formatCriterionName', () => {
    it('JUDGE_HELP_026: returns translated criterion name', () => {
      const result = helpers.formatCriterionName('counsellor_coherence')
      expect(result).toBe('judge.criteria.counsellorCoherence')
    })

    it('JUDGE_HELP_027: returns original for unknown criterion', () => {
      expect(helpers.formatCriterionName('unknown_criterion')).toBe('unknown_criterion')
    })
  })

  // ==================== Export ====================

  describe('exportCSV', () => {
    it('JUDGE_HELP_028: calls CSV export endpoint', async () => {
      const mockBlob = new Blob(['csv data'])
      axios.get.mockResolvedValue({ data: mockBlob })
      global.URL.createObjectURL = vi.fn(() => 'blob:url')

      await helpers.exportCSV()

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:55080/api/judge/sessions/session-123/export/csv',
        { responseType: 'blob' }
      )
    })
  })

  describe('exportJSON', () => {
    it('JUDGE_HELP_029: calls JSON export endpoint', async () => {
      axios.get.mockResolvedValue({ data: { results: [] } })
      global.URL.createObjectURL = vi.fn(() => 'blob:url')

      await helpers.exportJSON()

      expect(axios.get).toHaveBeenCalledWith(
        'http://localhost:55080/api/judge/sessions/session-123/export/json'
      )
    })
  })
})
