/**
 * Conference Config Tests
 *
 * Tests for conference configuration constants and helper functions.
 * Test IDs: CONF_CFG_001 - CONF_CFG_015
 */

import { describe, it, expect } from 'vitest'
import {
  CORE_RANKINGS,
  PAPER_STATUSES,
  SUBMISSION_STATUSES,
  getSubmissionStatusConfig,
  getRankingColor,
  getStatusConfig
} from '@/views/ConferenceManager/config/conferenceConfig'

describe('conferenceConfig', () => {
  // ==================== Constants ====================

  describe('CORE_RANKINGS', () => {
    it('CONF_CFG_001: contains expected ranking values', () => {
      const values = CORE_RANKINGS.map(r => r.value)
      expect(values).toEqual(['A*', 'A', 'B', 'C', 'Unranked'])
    })

    it('CONF_CFG_002: each ranking has color and label', () => {
      CORE_RANKINGS.forEach(r => {
        expect(r).toHaveProperty('color')
        expect(r).toHaveProperty('label')
        expect(r.color).toMatch(/^#[0-9A-Fa-f]{6}$/)
      })
    })
  })

  describe('PAPER_STATUSES', () => {
    it('CONF_CFG_003: contains expected status values', () => {
      const values = PAPER_STATUSES.map(s => s.value)
      expect(values).toEqual(['planning', 'in_progress', 'submitted', 'accepted', 'rejected', 'published'])
    })

    it('CONF_CFG_004: each status has icon and labelKey', () => {
      PAPER_STATUSES.forEach(s => {
        expect(s).toHaveProperty('icon')
        expect(s).toHaveProperty('labelKey')
        expect(s.icon).toMatch(/^mdi-/)
      })
    })
  })

  describe('SUBMISSION_STATUSES', () => {
    it('CONF_CFG_005: contains expected submission statuses', () => {
      const values = SUBMISSION_STATUSES.map(s => s.value)
      expect(values).toEqual(['submitted', 'accepted', 'rejected', 'withdrawn'])
    })
  })

  // ==================== Helper Functions ====================

  describe('getSubmissionStatusConfig', () => {
    it('CONF_CFG_006: returns config for known status', () => {
      const config = getSubmissionStatusConfig('accepted')
      expect(config.value).toBe('accepted')
      expect(config.color).toBe('#4a9e7e')
    })

    it('CONF_CFG_007: returns first status for unknown status', () => {
      const config = getSubmissionStatusConfig('nonexistent')
      expect(config.value).toBe('submitted')
    })
  })

  describe('getRankingColor', () => {
    it('CONF_CFG_008: returns color for known ranking', () => {
      expect(getRankingColor('A*')).toBe('#8B7D3C')
    })

    it('CONF_CFG_009: returns color for A ranking', () => {
      expect(getRankingColor('A')).toBe('#4A7C59')
    })

    it('CONF_CFG_010: returns default grey for unknown ranking', () => {
      expect(getRankingColor('X')).toBe('#808080')
    })
  })

  describe('getStatusConfig', () => {
    it('CONF_CFG_011: returns config for known status', () => {
      const config = getStatusConfig('accepted')
      expect(config.value).toBe('accepted')
      expect(config.icon).toBe('mdi-check-circle-outline')
    })

    it('CONF_CFG_012: returns first status for unknown status', () => {
      const config = getStatusConfig('nonexistent')
      expect(config.value).toBe('planning')
    })

    it('CONF_CFG_013: returns correct config for all statuses', () => {
      PAPER_STATUSES.forEach(s => {
        const config = getStatusConfig(s.value)
        expect(config).toEqual(s)
      })
    })
  })
})
