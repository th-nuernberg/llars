/**
 * useResultsConstants Tests
 *
 * Tests for table header builders and constant arrays.
 * Test IDs: JUDGE_CONST_001 - JUDGE_CONST_015
 */

import { describe, it, expect, vi } from 'vitest'
import {
  buildMetricsHeaders,
  buildComparisonHeaders,
  buildSwapHeaders,
  buildDetailedSwapHeaders,
  buildThreadHeaders,
  LIKERT_METRICS
} from '@/components/Judge/JudgeResults/composables/useResultsConstants'

const t = vi.fn((key) => key)

describe('useResultsConstants', () => {
  // ==================== LIKERT_METRICS ====================

  describe('LIKERT_METRICS', () => {
    it('JUDGE_CONST_001: contains 6 metrics', () => {
      expect(LIKERT_METRICS).toHaveLength(6)
    })

    it('JUDGE_CONST_002: contains expected metric keys', () => {
      expect(LIKERT_METRICS).toContain('counsellor_coherence')
      expect(LIKERT_METRICS).toContain('client_coherence')
      expect(LIKERT_METRICS).toContain('quality')
      expect(LIKERT_METRICS).toContain('empathy')
      expect(LIKERT_METRICS).toContain('authenticity')
      expect(LIKERT_METRICS).toContain('solution_orientation')
    })
  })

  // ==================== Header Builders ====================

  describe('buildMetricsHeaders', () => {
    it('JUDGE_CONST_003: returns array of headers', () => {
      const headers = buildMetricsHeaders(t)
      expect(Array.isArray(headers)).toBe(true)
      expect(headers.length).toBeGreaterThan(0)
    })

    it('JUDGE_CONST_004: each header has title, key, and sortable', () => {
      const headers = buildMetricsHeaders(t)
      headers.forEach(h => {
        expect(h).toHaveProperty('title')
        expect(h).toHaveProperty('key')
        expect(h).toHaveProperty('sortable')
      })
    })

    it('JUDGE_CONST_005: includes expected keys', () => {
      const headers = buildMetricsHeaders(t)
      const keys = headers.map(h => h.key)
      expect(keys).toContain('name')
      expect(keys).toContain('wins')
      expect(keys).toContain('win_rate')
    })
  })

  describe('buildComparisonHeaders', () => {
    it('JUDGE_CONST_006: returns comparison headers', () => {
      const headers = buildComparisonHeaders(t)
      const keys = headers.map(h => h.key)
      expect(keys).toContain('comparison_index')
      expect(keys).toContain('winner')
      expect(keys).toContain('confidence_score')
    })

    it('JUDGE_CONST_007: matchup is not sortable', () => {
      const headers = buildComparisonHeaders(t)
      const matchup = headers.find(h => h.key === 'matchup')
      expect(matchup.sortable).toBe(false)
    })
  })

  describe('buildSwapHeaders', () => {
    it('JUDGE_CONST_008: returns swap analysis headers', () => {
      const headers = buildSwapHeaders(t)
      expect(headers.length).toBeGreaterThan(0)
      const keys = headers.map(h => h.key)
      expect(keys).toContain('consistent')
    })
  })

  describe('buildDetailedSwapHeaders', () => {
    it('JUDGE_CONST_009: returns detailed swap headers', () => {
      const headers = buildDetailedSwapHeaders(t)
      const keys = headers.map(h => h.key)
      expect(keys).toContain('consistency')
      expect(keys).toContain('bias')
      expect(keys).toContain('conf_delta')
    })
  })

  describe('buildThreadHeaders', () => {
    it('JUDGE_CONST_010: returns thread performance headers', () => {
      const headers = buildThreadHeaders(t)
      const keys = headers.map(h => h.key)
      expect(keys).toContain('thread_id')
      expect(keys).toContain('win_rate')
      expect(keys).toContain('likert_consistency_score')
    })
  })
})
