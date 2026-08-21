/**
 * useStreamParser (WorkerLane) Composable Tests
 *
 * Tests for incremental stream parsing, score helpers, dominance calculations.
 * Test IDs: STREAM_PARSE_001 - STREAM_PARSE_035
 */

import { describe, it, expect } from 'vitest'
import { reactive, nextTick } from 'vue'
import { useStreamParser } from '@/components/Judge/WorkerLane/composables/useStreamParser'

describe('useStreamParser', () => {
  function createProps(streamContent = '') {
    return reactive({ streamContent })
  }

  // ==================== parsedResult ====================

  describe('parsedResult', () => {
    it('STREAM_PARSE_001: returns null for empty stream', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.parsedResult.value).toBeNull()
    })

    it('STREAM_PARSE_002: parses complete JSON with winner', () => {
      const json = JSON.stringify({
        winner: 'A',
        confidence: 0.85,
        scores: { A: { quality: 4 }, B: { quality: 3 } },
        final_justification: 'A is better'
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.parsedResult.value.winner).toBe('A')
      expect(parser.parsedResult.value.confidence).toBe(0.85)
      expect(parser.parsedResult.value.final_justification).toBe('A is better')
    })

    it('STREAM_PARSE_003: parses incremental winner', () => {
      const content = '{"step_1": "analysis", "winner": "B"'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedResult.value.winner).toBe('B')
    })

    it('STREAM_PARSE_004: parses incremental confidence', () => {
      const content = '{"confidence": 0.92'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedResult.value.confidence).toBe(0.92)
    })

    it('STREAM_PARSE_005: parses complete JSON with criteria_scores', () => {
      const json = JSON.stringify({
        winner: 'A',
        criteria_scores: {
          quality: { score_a: 4, score_b: 3 }
        }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.parsedResult.value.criteria_scores.quality).toEqual({ score_a: 4, score_b: 3 })
    })

    it('STREAM_PARSE_006: parses final_justification from incremental content', () => {
      const content = '{"final_justification": "This is the reason", "winner": "A"}'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedResult.value.final_justification).toBe('This is the reason')
    })
  })

  // ==================== parsedStreamSteps ====================

  describe('parsedStreamSteps', () => {
    it('STREAM_PARSE_007: returns empty array for empty content', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.parsedStreamSteps.value).toEqual([])
    })

    it('STREAM_PARSE_008: parses complete step', () => {
      const content = '{"step_1": "Analysis of coherence", "step_2": "Analysis of quality"}'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedStreamSteps.value.length).toBe(2)
      expect(parser.parsedStreamSteps.value[0].key).toBe('step_1')
      expect(parser.parsedStreamSteps.value[0].content).toBe('Analysis of coherence')
    })

    it('STREAM_PARSE_009: detects streaming step (no closing quote)', () => {
      const content = '{"step_1": "Still streaming this content'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedStreamSteps.value.length).toBe(1)
      expect(parser.parsedStreamSteps.value[0].isStreaming).toBe(true)
    })

    it('STREAM_PARSE_010: detects completed step (has closing quote)', () => {
      const content = '{"step_1": "Complete analysis", "step_2": "start"}'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedStreamSteps.value[0].isStreaming).toBe(false)
    })

    it('STREAM_PARSE_011: handles escaped characters in steps', () => {
      const content = '{"step_1": "Line 1\\nLine 2\\n\\"quoted\\"", "step_2": "x"}'
      const parser = useStreamParser(createProps(content))

      expect(parser.parsedStreamSteps.value[0].content).toContain('\n')
      expect(parser.parsedStreamSteps.value[0].content).toContain('"')
    })
  })

  // ==================== getStepByKey ====================

  describe('getStepByKey', () => {
    it('STREAM_PARSE_012: returns step by key', () => {
      const content = '{"step_1": "Analysis content"}'
      const parser = useStreamParser(createProps(content))

      const step = parser.getStepByKey('step_1')
      expect(step).toBeDefined()
      expect(step.content).toBe('Analysis content')
    })

    it('STREAM_PARSE_013: returns undefined for missing key', () => {
      const content = '{"step_1": "Analysis content"}'
      const parser = useStreamParser(createProps(content))

      expect(parser.getStepByKey('step_99')).toBeUndefined()
    })
  })

  // ==================== completedSteps ====================

  describe('completedSteps', () => {
    it('STREAM_PARSE_014: counts 0 completed steps for empty content', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.completedSteps.value).toBe(0)
    })

    it('STREAM_PARSE_015: counts completed steps correctly', () => {
      const content = '{"step_1": "Done", "step_2": "Done", "step_3": "Still going'
      const parser = useStreamParser(createProps(content))

      expect(parser.completedSteps.value).toBe(2)
    })
  })

  // ==================== currentActiveStep ====================

  describe('currentActiveStep', () => {
    it('STREAM_PARSE_016: returns undefined for empty content', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.currentActiveStep.value).toBeUndefined()
    })

    it('STREAM_PARSE_017: returns currently streaming step', () => {
      const content = '{"step_1": "Done", "step_2": "Still active'
      const parser = useStreamParser(createProps(content))

      expect(parser.currentActiveStep.value.key).toBe('step_2')
      expect(parser.currentActiveStep.value.isStreaming).toBe(true)
    })
  })

  // ==================== Score Helpers ====================

  describe('getScoreA / getScoreB', () => {
    it('STREAM_PARSE_018: returns score from scores.A', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: { quality: 4 }, B: { quality: 3 } }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getScoreA('quality')).toBe(4)
      expect(parser.getScoreB('quality')).toBe(3)
    })

    it('STREAM_PARSE_019: returns 0 for missing criterion', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: {}, B: {} }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getScoreA('nonexistent')).toBe(0)
      expect(parser.getScoreB('nonexistent')).toBe(0)
    })

    it('STREAM_PARSE_020: falls back to criteria_scores format', () => {
      const json = JSON.stringify({
        winner: 'A',
        criteria_scores: {
          quality: { score_a: 5, score_b: 2 }
        }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getScoreA('quality')).toBe(5)
      expect(parser.getScoreB('quality')).toBe(2)
    })
  })

  // ==================== Total Scores ====================

  describe('totalScoreA / totalScoreB', () => {
    it('STREAM_PARSE_021: computes total score correctly', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: {
          A: { counsellor_coherence: 4, client_coherence: 3, quality: 5, empathy: 4, authenticity: 3, solution_orientation: 4 },
          B: { counsellor_coherence: 3, client_coherence: 2, quality: 4, empathy: 3, authenticity: 2, solution_orientation: 3 }
        }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.totalScoreA.value).toBe(23)
      expect(parser.totalScoreB.value).toBe(17)
    })

    it('STREAM_PARSE_022: returns 0 when no scores', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.totalScoreA.value).toBe(0)
      expect(parser.totalScoreB.value).toBe(0)
    })
  })

  // ==================== Dominance ====================

  describe('dominanceA / dominanceB', () => {
    it('STREAM_PARSE_023: returns 50 each when no scores', () => {
      const parser = useStreamParser(createProps(''))
      expect(parser.dominanceA.value).toBe(50)
      expect(parser.dominanceB.value).toBe(50)
    })

    it('STREAM_PARSE_024: calculates dominance percentages', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: {
          A: { quality: 3 },
          B: { quality: 1 }
        }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.dominanceA.value).toBe(75)
      expect(parser.dominanceB.value).toBe(25)
    })
  })

  // ==================== Diff Helpers ====================

  describe('getDiffClass / getDiffText', () => {
    it('STREAM_PARSE_025: returns diff-positive when A > B', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: { quality: 5 }, B: { quality: 3 } }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getDiffClass('quality')).toBe('diff-positive')
      expect(parser.getDiffText('quality')).toBe('+2')
    })

    it('STREAM_PARSE_026: returns diff-negative when A < B', () => {
      const json = JSON.stringify({
        winner: 'B',
        scores: { A: { quality: 2 }, B: { quality: 5 } }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getDiffClass('quality')).toBe('diff-negative')
      expect(parser.getDiffText('quality')).toBe('-3')
    })

    it('STREAM_PARSE_027: returns diff-neutral when equal', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: { quality: 3 }, B: { quality: 3 } }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.getDiffClass('quality')).toBe('diff-neutral')
      expect(parser.getDiffText('quality')).toBe('0')
    })
  })

  // ==================== scoreDiff ====================

  describe('scoreDiff', () => {
    it('STREAM_PARSE_028: computes total score difference', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: { quality: 5, empathy: 4 }, B: { quality: 3, empathy: 3 } }
      })
      const parser = useStreamParser(createProps(json))

      expect(parser.scoreDiff.value).toBe(3) // (5+4) - (3+3)
    })
  })
})
