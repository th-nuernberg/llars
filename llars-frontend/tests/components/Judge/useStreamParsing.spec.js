/**
 * useStreamParsing (JudgeSession) Composable Tests
 *
 * Tests for stream JSON parsing, step extraction, and worker stream parsing.
 * Test IDs: SESS_PARSE_001 - SESS_PARSE_025
 */

import { describe, it, expect, vi } from 'vitest'
import { ref, reactive } from 'vue'
import { useStreamParsing } from '@/components/Judge/JudgeSession/composables/useStreamParsing'

describe('useStreamParsing', () => {
  function createState(content = '', workerStreams = {}) {
    return {
      llmStreamContent: ref(content),
      workerStreams: reactive(workerStreams),
      isStreaming: ref(false)
    }
  }

  // ==================== parsedStreamJson ====================

  describe('parsedStreamJson', () => {
    it('SESS_PARSE_001: returns null for empty content', () => {
      const parser = useStreamParsing(createState(''))
      expect(parser.parsedStreamJson.value).toBeNull()
    })

    it('SESS_PARSE_002: parses complete JSON response', () => {
      const json = JSON.stringify({
        winner: 'A',
        confidence: 0.85,
        scores: {
          A: { counsellor_coherence: 4, quality: 5 },
          B: { counsellor_coherence: 3, quality: 3 }
        },
        final_justification: 'A wins because...'
      })

      const parser = useStreamParsing(createState(json))
      const result = parser.parsedStreamJson.value

      expect(result.winner).toBe('A')
      expect(result.confidence).toBe(0.85)
      expect(result.final_justification).toBe('A wins because...')
      expect(result.scores.A.quality).toBe(5)
    })

    it('SESS_PARSE_003: parses incremental winner', () => {
      const content = 'Some preamble {"winner": "B", "confidence": 0.7'
      const parser = useStreamParsing(createState(content))

      expect(parser.parsedStreamJson.value.winner).toBe('B')
    })

    it('SESS_PARSE_004: parses incremental confidence', () => {
      const content = '{"confidence": 0.92'
      const parser = useStreamParsing(createState(content))

      expect(parser.parsedStreamJson.value.confidence).toBe(0.92)
    })

    it('SESS_PARSE_005: parses criteria_scores format', () => {
      const json = JSON.stringify({
        winner: 'A',
        criteria_scores: {
          quality: { score_a: 5, score_b: 2 }
        }
      })
      const parser = useStreamParsing(createState(json))

      expect(parser.parsedStreamJson.value.criteria_scores.quality).toEqual({ score_a: 5, score_b: 2 })
    })

    it('SESS_PARSE_006: returns null when nothing parseable', () => {
      const parser = useStreamParsing(createState('Random text with no JSON'))
      expect(parser.parsedStreamJson.value).toBeNull()
    })
  })

  // ==================== parsedStreamSteps ====================

  describe('parsedStreamSteps', () => {
    it('SESS_PARSE_007: returns empty array for empty content', () => {
      const parser = useStreamParsing(createState(''))
      expect(parser.parsedStreamSteps.value).toEqual([])
    })

    it('SESS_PARSE_008: parses steps from content', () => {
      const content = '{"step_1": "Analysis of counsellor", "step_2": "Analysis of client"}'
      const parser = useStreamParsing(createState(content))

      const steps = parser.parsedStreamSteps.value
      expect(steps.length).toBe(2)
      expect(steps[0].key).toBe('step_1')
      expect(steps[0].content).toBe('Analysis of counsellor')
    })

    it('SESS_PARSE_009: includes title and icon from step definitions', () => {
      const content = '{"step_1": "Some analysis"}'
      const parser = useStreamParsing(createState(content))

      const step = parser.parsedStreamSteps.value[0]
      expect(step.title).toBeDefined()
      expect(step.icon).toBeDefined()
    })

    it('SESS_PARSE_010: handles escaped characters', () => {
      const content = '{"step_1": "Line 1\\nLine 2"}'
      const parser = useStreamParsing(createState(content))

      expect(parser.parsedStreamSteps.value[0].content).toContain('\n')
    })
  })

  // ==================== getStepByKey ====================

  describe('getStepByKey', () => {
    it('SESS_PARSE_011: returns step for known key', () => {
      const content = '{"step_1": "Analysis"}'
      const parser = useStreamParsing(createState(content))

      const step = parser.getStepByKey('step_1')
      expect(step).not.toBeNull()
      expect(step.content).toBe('Analysis')
    })

    it('SESS_PARSE_012: returns null for unknown key', () => {
      const content = '{"step_1": "Analysis"}'
      const parser = useStreamParsing(createState(content))

      expect(parser.getStepByKey('step_99')).toBeNull()
    })
  })

  // ==================== Worker Stream Parsing ====================

  describe('getWorkerParsedResult', () => {
    it('SESS_PARSE_013: returns null for unknown worker', () => {
      const parser = useStreamParsing(createState(''))
      expect(parser.getWorkerParsedResult(99)).toBeNull()
    })

    it('SESS_PARSE_014: returns null for worker with empty content', () => {
      const parser = useStreamParsing(createState('', { 0: { content: '' } }))
      expect(parser.getWorkerParsedResult(0)).toBeNull()
    })

    it('SESS_PARSE_015: parses complete JSON from worker stream', () => {
      const json = JSON.stringify({
        winner: 'A',
        confidence: 0.9,
        scores: { A: { quality: 5 }, B: { quality: 3 } },
        final_justification: 'Better quality'
      })
      const parser = useStreamParsing(createState('', { 0: { content: json } }))
      const result = parser.getWorkerParsedResult(0)

      expect(result.winner).toBe('A')
      expect(result.confidence).toBe(0.9)
      expect(result.final_justification).toBe('Better quality')
    })

    it('SESS_PARSE_016: parses incremental worker content', () => {
      const content = '{"winner": "B", "confidence": 0.75'
      const parser = useStreamParsing(createState('', { 0: { content } }))
      const result = parser.getWorkerParsedResult(0)

      expect(result.winner).toBe('B')
      expect(result.confidence).toBe(0.75)
    })
  })

  describe('getWorkerScoreA / getWorkerScoreB', () => {
    it('SESS_PARSE_017: returns worker scores', () => {
      const json = JSON.stringify({
        winner: 'A',
        scores: { A: { quality: 4 }, B: { quality: 2 } }
      })
      const parser = useStreamParsing(createState('', { 0: { content: json } }))

      expect(parser.getWorkerScoreA(0, 'quality')).toBe(4)
      expect(parser.getWorkerScoreB(0, 'quality')).toBe(2)
    })

    it('SESS_PARSE_018: returns 0 for missing criterion', () => {
      const parser = useStreamParsing(createState('', { 0: { content: '{}' } }))

      expect(parser.getWorkerScoreA(0, 'quality')).toBe(0)
      expect(parser.getWorkerScoreB(0, 'quality')).toBe(0)
    })
  })

  describe('getWorkerStep', () => {
    it('SESS_PARSE_019: returns worker step content', () => {
      const content = '{"step_1": "Worker analysis complete"}'
      const parser = useStreamParsing(createState('', { 0: { content } }))

      const step = parser.getWorkerStep(0, 'step_1')
      expect(step.key).toBe('step_1')
      expect(step.content).toBe('Worker analysis complete')
      expect(step.isStreaming).toBe(false)
    })

    it('SESS_PARSE_020: returns null for worker step with no content', () => {
      const parser = useStreamParsing(createState('', { 0: { content: '{}' } }))

      expect(parser.getWorkerStep(0, 'step_1')).toBeNull()
    })

    it('SESS_PARSE_021: returns null for unknown worker', () => {
      const parser = useStreamParsing(createState(''))

      expect(parser.getWorkerStep(99, 'step_1')).toBeNull()
    })

    it('SESS_PARSE_022: detects streaming worker step', () => {
      const content = '{"step_1": "Still streaming this'
      const parser = useStreamParsing(createState('', { 0: { content } }))

      const step = parser.getWorkerStep(0, 'step_1')
      expect(step.isStreaming).toBe(true)
    })
  })
})
