/**
 * Color Helpers Utility Tests
 *
 * Tests for shared color utility functions used across LLARS components.
 * Test IDs: UTIL_CLR_001 - UTIL_CLR_050
 */

import { describe, it, expect } from 'vitest'
import {
  getScoreColor,
  getWinRateColor,
  getConfidenceColor,
  getRankColor,
  getStatusColor,
  getQueueStatusColor,
  getLikertConsistencyColor,
  getConsistencyQualityColor
} from '@/utils/colorHelpers'

// ==================== getScoreColor Tests (1-5 scale) ====================

describe('getScoreColor', () => {
  it('UTIL_CLR_001: returns success for score >= 4.5', () => {
    expect(getScoreColor(4.5)).toBe('success')
  })

  it('UTIL_CLR_002: returns success for score 5.0', () => {
    expect(getScoreColor(5.0)).toBe('success')
  })

  it('UTIL_CLR_003: returns info for score >= 3.5 and < 4.5', () => {
    expect(getScoreColor(3.5)).toBe('info')
  })

  it('UTIL_CLR_004: returns info for score 4.4', () => {
    expect(getScoreColor(4.4)).toBe('info')
  })

  it('UTIL_CLR_005: returns warning for score >= 2.5 and < 3.5', () => {
    expect(getScoreColor(2.5)).toBe('warning')
  })

  it('UTIL_CLR_006: returns warning for score 3.4', () => {
    expect(getScoreColor(3.4)).toBe('warning')
  })

  it('UTIL_CLR_007: returns error for score < 2.5', () => {
    expect(getScoreColor(2.4)).toBe('error')
  })

  it('UTIL_CLR_008: returns error for score 1.0', () => {
    expect(getScoreColor(1.0)).toBe('error')
  })

  it('UTIL_CLR_009: returns error for score 0', () => {
    expect(getScoreColor(0)).toBe('error')
  })
})

// ==================== getWinRateColor Tests (0-1 scale) ====================

describe('getWinRateColor', () => {
  it('UTIL_CLR_010: returns success for winRate >= 0.7', () => {
    expect(getWinRateColor(0.7)).toBe('success')
  })

  it('UTIL_CLR_011: returns success for winRate 1.0', () => {
    expect(getWinRateColor(1.0)).toBe('success')
  })

  it('UTIL_CLR_012: returns info for winRate >= 0.5 and < 0.7', () => {
    expect(getWinRateColor(0.5)).toBe('info')
  })

  it('UTIL_CLR_013: returns info for winRate 0.69', () => {
    expect(getWinRateColor(0.69)).toBe('info')
  })

  it('UTIL_CLR_014: returns warning for winRate >= 0.3 and < 0.5', () => {
    expect(getWinRateColor(0.3)).toBe('warning')
  })

  it('UTIL_CLR_015: returns error for winRate < 0.3', () => {
    expect(getWinRateColor(0.29)).toBe('error')
  })

  it('UTIL_CLR_016: returns error for winRate 0', () => {
    expect(getWinRateColor(0)).toBe('error')
  })
})

// ==================== getConfidenceColor Tests (0-1 scale) ====================

describe('getConfidenceColor', () => {
  it('UTIL_CLR_017: returns success for confidence >= 0.8', () => {
    expect(getConfidenceColor(0.8)).toBe('success')
  })

  it('UTIL_CLR_018: returns info for confidence >= 0.6 and < 0.8', () => {
    expect(getConfidenceColor(0.6)).toBe('info')
  })

  it('UTIL_CLR_019: returns warning for confidence >= 0.4 and < 0.6', () => {
    expect(getConfidenceColor(0.4)).toBe('warning')
  })

  it('UTIL_CLR_020: returns error for confidence < 0.4', () => {
    expect(getConfidenceColor(0.39)).toBe('error')
  })

  it('UTIL_CLR_021: returns success for confidence 1.0', () => {
    expect(getConfidenceColor(1.0)).toBe('success')
  })
})

// ==================== getRankColor Tests (0-based index) ====================

describe('getRankColor', () => {
  it('UTIL_CLR_022: returns warning (gold) for rank 0 (1st place)', () => {
    expect(getRankColor(0)).toBe('warning')
  })

  it('UTIL_CLR_023: returns grey-lighten-1 (silver) for rank 1', () => {
    expect(getRankColor(1)).toBe('grey-lighten-1')
  })

  it('UTIL_CLR_024: returns orange-lighten-1 (bronze) for rank 2', () => {
    expect(getRankColor(2)).toBe('orange-lighten-1')
  })

  it('UTIL_CLR_025: returns grey-lighten-2 for rank 3', () => {
    expect(getRankColor(3)).toBe('grey-lighten-2')
  })

  it('UTIL_CLR_026: returns grey-lighten-3 for rank 4', () => {
    expect(getRankColor(4)).toBe('grey-lighten-3')
  })

  it('UTIL_CLR_027: returns grey for rank beyond array', () => {
    expect(getRankColor(5)).toBe('grey')
  })

  it('UTIL_CLR_028: returns grey for very high rank', () => {
    expect(getRankColor(100)).toBe('grey')
  })
})

// ==================== getStatusColor Tests ====================

describe('getStatusColor', () => {
  it('UTIL_CLR_029: returns grey for created', () => {
    expect(getStatusColor('created')).toBe('grey')
  })

  it('UTIL_CLR_030: returns warning for queued', () => {
    expect(getStatusColor('queued')).toBe('warning')
  })

  it('UTIL_CLR_031: returns info for running', () => {
    expect(getStatusColor('running')).toBe('info')
  })

  it('UTIL_CLR_032: returns orange for paused', () => {
    expect(getStatusColor('paused')).toBe('orange')
  })

  it('UTIL_CLR_033: returns success for completed', () => {
    expect(getStatusColor('completed')).toBe('success')
  })

  it('UTIL_CLR_034: returns error for failed', () => {
    expect(getStatusColor('failed')).toBe('error')
  })

  it('UTIL_CLR_035: returns grey for pending', () => {
    expect(getStatusColor('pending')).toBe('grey')
  })

  it('UTIL_CLR_036: returns grey for unknown status', () => {
    expect(getStatusColor('unknown')).toBe('grey')
  })
})

// ==================== getQueueStatusColor Tests ====================

describe('getQueueStatusColor', () => {
  it('UTIL_CLR_037: handles lowercase pending', () => {
    expect(getQueueStatusColor('pending')).toBe('grey')
  })

  it('UTIL_CLR_038: handles uppercase PENDING', () => {
    expect(getQueueStatusColor('PENDING')).toBe('grey')
  })

  it('UTIL_CLR_039: handles lowercase running', () => {
    expect(getQueueStatusColor('running')).toBe('warning')
  })

  it('UTIL_CLR_040: handles uppercase COMPLETED', () => {
    expect(getQueueStatusColor('COMPLETED')).toBe('success')
  })

  it('UTIL_CLR_041: handles uppercase FAILED', () => {
    expect(getQueueStatusColor('FAILED')).toBe('error')
  })

  it('UTIL_CLR_042: returns grey for unknown status', () => {
    expect(getQueueStatusColor('unknown')).toBe('grey')
  })
})

// ==================== getLikertConsistencyColor Tests ====================

describe('getLikertConsistencyColor', () => {
  it('UTIL_CLR_043: returns success for score >= 0.7', () => {
    expect(getLikertConsistencyColor(0.7)).toBe('success')
  })

  it('UTIL_CLR_044: returns success for score 1.0', () => {
    expect(getLikertConsistencyColor(1.0)).toBe('success')
  })

  it('UTIL_CLR_045: returns warning for score >= 0.5 and < 0.7', () => {
    expect(getLikertConsistencyColor(0.5)).toBe('warning')
  })

  it('UTIL_CLR_046: returns error for score < 0.5', () => {
    expect(getLikertConsistencyColor(0.49)).toBe('error')
  })

  it('UTIL_CLR_047: returns error for score 0', () => {
    expect(getLikertConsistencyColor(0)).toBe('error')
  })
})

// ==================== getConsistencyQualityColor Tests ====================

describe('getConsistencyQualityColor', () => {
  it('UTIL_CLR_048: returns success for excellent', () => {
    expect(getConsistencyQualityColor('excellent')).toBe('success')
  })

  it('UTIL_CLR_049: returns info for good', () => {
    expect(getConsistencyQualityColor('good')).toBe('info')
  })

  it('UTIL_CLR_050: returns warning for fair', () => {
    expect(getConsistencyQualityColor('fair')).toBe('warning')
  })

  it('UTIL_CLR_051: returns error for poor', () => {
    expect(getConsistencyQualityColor('poor')).toBe('error')
  })

  it('UTIL_CLR_052: returns grey for unknown quality', () => {
    expect(getConsistencyQualityColor('unknown')).toBe('grey')
  })
})
