/**
 * useSessionConstants Tests
 *
 * Tests for session-level constants: pillar config, step definitions, score criteria.
 * Test IDs: SESS_CONST_001 - SESS_CONST_015
 */

import { describe, it, expect } from 'vitest'
import {
  WORKER_COLORS,
  PILLAR_CONFIG,
  PILLAR_NAMES,
  STEP_DEFINITIONS,
  SCORE_CRITERIA,
  QUEUE_HEADERS,
  HISTORY_HEADERS
} from '@/components/Judge/JudgeSession/composables/useSessionConstants'

describe('useSessionConstants', () => {
  describe('WORKER_COLORS', () => {
    it('SESS_CONST_001: contains 5 colors', () => {
      expect(WORKER_COLORS).toHaveLength(5)
    })

    it('SESS_CONST_002: all entries are strings', () => {
      WORKER_COLORS.forEach(c => expect(typeof c).toBe('string'))
    })
  })

  describe('PILLAR_CONFIG', () => {
    it('SESS_CONST_003: has 5 pillar entries', () => {
      expect(Object.keys(PILLAR_CONFIG)).toHaveLength(5)
    })

    it('SESS_CONST_004: each pillar has name, icon, color, short', () => {
      Object.values(PILLAR_CONFIG).forEach(p => {
        expect(p).toHaveProperty('name')
        expect(p).toHaveProperty('icon')
        expect(p).toHaveProperty('color')
        expect(p).toHaveProperty('short')
      })
    })

    it('SESS_CONST_005: pillar 1 is Rollenspiele', () => {
      expect(PILLAR_CONFIG[1].name).toBe('Rollenspiele')
    })
  })

  describe('PILLAR_NAMES', () => {
    it('SESS_CONST_006: has 5 entries', () => {
      expect(Object.keys(PILLAR_NAMES)).toHaveLength(5)
    })

    it('SESS_CONST_007: all values are strings', () => {
      Object.values(PILLAR_NAMES).forEach(n => expect(typeof n).toBe('string'))
    })
  })

  describe('STEP_DEFINITIONS', () => {
    it('SESS_CONST_008: has 6 step entries', () => {
      expect(Object.keys(STEP_DEFINITIONS)).toHaveLength(6)
    })

    it('SESS_CONST_009: each step has title and icon', () => {
      Object.values(STEP_DEFINITIONS).forEach(s => {
        expect(s).toHaveProperty('title')
        expect(s).toHaveProperty('icon')
        expect(s.icon).toMatch(/^mdi-/)
      })
    })

    it('SESS_CONST_010: step keys are step_1 through step_6', () => {
      const keys = Object.keys(STEP_DEFINITIONS)
      for (let i = 1; i <= 6; i++) {
        expect(keys).toContain(`step_${i}`)
      }
    })
  })

  describe('SCORE_CRITERIA', () => {
    it('SESS_CONST_011: has 6 criteria', () => {
      expect(SCORE_CRITERIA).toHaveLength(6)
    })

    it('SESS_CONST_012: each criterion has key and label', () => {
      SCORE_CRITERIA.forEach(c => {
        expect(c).toHaveProperty('key')
        expect(c).toHaveProperty('label')
      })
    })

    it('SESS_CONST_013: includes expected criteria keys', () => {
      const keys = SCORE_CRITERIA.map(c => c.key)
      expect(keys).toContain('counsellor_coherence')
      expect(keys).toContain('quality')
      expect(keys).toContain('empathy')
    })
  })

  describe('QUEUE_HEADERS', () => {
    it('SESS_CONST_014: has expected column keys', () => {
      const keys = QUEUE_HEADERS.map(h => h.key)
      expect(keys).toContain('queue_position')
      expect(keys).toContain('status')
      expect(keys).toContain('result')
    })
  })

  describe('HISTORY_HEADERS', () => {
    it('SESS_CONST_015: has expected column keys', () => {
      const keys = HISTORY_HEADERS.map(h => h.key)
      expect(keys).toContain('comparison_index')
      expect(keys).toContain('winner')
      expect(keys).toContain('confidence_score')
    })
  })
})
