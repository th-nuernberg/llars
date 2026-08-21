/**
 * useStreamingParser Composable Tests
 *
 * Tests for the incremental JSON streaming parser used in AI Analysis.
 * Test IDs: STREAM_001 - STREAM_045
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useStreamingParser, FIELD_STATE } from '@/components/ScenarioWizard/AIAnalysis/useStreamingParser'

describe('useStreamingParser', () => {
  let parser

  beforeEach(() => {
    parser = useStreamingParser()
  })

  // ==================== Initial State Tests ====================

  describe('initial state', () => {
    it('STREAM_001: starts with empty buffer', () => {
      expect(parser.buffer.value).toBe('')
    })

    it('STREAM_002: starts with null parsed values', () => {
      expect(parser.parsed.evalType).toBeNull()
      expect(parser.parsed.evalTypeConfidence).toBeNull()
      expect(parser.parsed.evalTypeReasoning).toBe('')
      expect(parser.parsed.scenarioName).toBe('')
      expect(parser.parsed.scenarioDescription).toBe('')
      expect(parser.parsed.dataQuality).toBeNull()
      expect(parser.parsed.configSuggestions).toBeNull()
    })

    it('STREAM_003: starts with all fields pending', () => {
      expect(parser.fieldState.evalType).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.evalTypeConfidence).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.evalTypeReasoning).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.scenarioName).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.scenarioDescription).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.configSuggestions).toBe(FIELD_STATE.PENDING)
      expect(parser.fieldState.dataQuality).toBe(FIELD_STATE.PENDING)
    })

    it('STREAM_004: starts not streaming and not complete', () => {
      expect(parser.isStreaming.value).toBe(false)
      expect(parser.isComplete.value).toBe(false)
    })

    it('STREAM_005: starts with no error', () => {
      expect(parser.error.value).toBeNull()
    })

    it('STREAM_006: confidencePercent is 0 initially', () => {
      expect(parser.confidencePercent.value).toBe(0)
    })

    it('STREAM_007: hasAnyContent is false initially', () => {
      expect(parser.hasAnyContent.value).toBeFalsy()
    })
  })

  // ==================== FIELD_STATE Constants ====================

  describe('FIELD_STATE constants', () => {
    it('STREAM_008: exports correct field states', () => {
      expect(FIELD_STATE.PENDING).toBe('pending')
      expect(FIELD_STATE.STREAMING).toBe('streaming')
      expect(FIELD_STATE.COMPLETE).toBe('complete')
    })
  })

  // ==================== processChunk Tests ====================

  describe('processChunk', () => {
    it('STREAM_009: appends chunk to buffer', () => {
      parser.processChunk('{"evaluation_type"')
      expect(parser.buffer.value).toBe('{"evaluation_type"')
    })

    it('STREAM_010: sets isStreaming to true', () => {
      parser.processChunk('any chunk')
      expect(parser.isStreaming.value).toBe(true)
    })

    it('STREAM_011: extracts evaluation_type from complete JSON chunk', () => {
      parser.processChunk('{"evaluation_type": "ranking"}')
      expect(parser.parsed.evalType).toBe('ranking')
      expect(parser.fieldState.evalType).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_012: extracts eval_type (old field name)', () => {
      parser.processChunk('{"eval_type": "rating"}')
      expect(parser.parsed.evalType).toBe('rating')
      expect(parser.fieldState.evalType).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_013: extracts confidence as number', () => {
      parser.processChunk('{"confidence": 0.85}')
      expect(parser.parsed.evalTypeConfidence).toBe(0.85)
      expect(parser.fieldState.evalTypeConfidence).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_014: extracts eval_type_confidence (old field name)', () => {
      parser.processChunk('{"eval_type_confidence": 0.92}')
      expect(parser.parsed.evalTypeConfidence).toBe(0.92)
    })

    it('STREAM_015: extracts scenario name with new field name', () => {
      parser.processChunk('{"name": "My Scenario"}')
      expect(parser.parsed.scenarioName).toBe('My Scenario')
      expect(parser.fieldState.scenarioName).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_016: extracts scenario_name (old field name)', () => {
      parser.processChunk('{"scenario_name": "Old Scenario"}')
      expect(parser.parsed.scenarioName).toBe('Old Scenario')
    })

    it('STREAM_017: extracts description with new field name', () => {
      parser.processChunk('{"description": "A test description"}')
      expect(parser.parsed.scenarioDescription).toBe('A test description')
      expect(parser.fieldState.scenarioDescription).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_018: extracts scenario_description (old field name)', () => {
      parser.processChunk('{"scenario_description": "Old description"}')
      expect(parser.parsed.scenarioDescription).toBe('Old description')
    })

    it('STREAM_019: extracts reasoning with new field name', () => {
      parser.processChunk('{"reasoning": "Because of the data structure"}')
      expect(parser.parsed.evalTypeReasoning).toBe('Because of the data structure')
      expect(parser.fieldState.evalTypeReasoning).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_020: extracts eval_type_reasoning (old field name)', () => {
      parser.processChunk('{"eval_type_reasoning": "Old reasoning"}')
      expect(parser.parsed.evalTypeReasoning).toBe('Old reasoning')
    })

    it('STREAM_021: detects config_suggestions start', () => {
      parser.processChunk('{"config_suggestions": {"key": "value"}}')
      expect(parser.fieldState.configSuggestions).toBe(FIELD_STATE.STREAMING)
    })

    it('STREAM_022: detects config start', () => {
      parser.processChunk('{"config": {"type": "ranking"}}')
      expect(parser.fieldState.configSuggestions).toBe(FIELD_STATE.STREAMING)
    })

    it('STREAM_023: handles incremental chunks across multiple calls', () => {
      parser.processChunk('{"evaluation_type": "ran')
      expect(parser.parsed.evalType).toBeNull()

      parser.processChunk('king"}')
      expect(parser.parsed.evalType).toBe('ranking')
    })

    it('STREAM_024: handles streaming text field that is incomplete', () => {
      parser.processChunk('{"name": "Partial scenario na')
      // The field is still streaming (no closing quote)
      expect(parser.parsed.scenarioName).toBe('Partial scenario na')
      expect(parser.fieldState.scenarioName).toBe(FIELD_STATE.STREAMING)
    })

    it('STREAM_025: handles escaped characters in streaming fields', () => {
      parser.processChunk('{"reasoning": "Line 1\\nLine 2"}')
      expect(parser.parsed.evalTypeReasoning).toBe('Line 1\nLine 2')
    })

    it('STREAM_026: handles escaped quotes in streaming fields', () => {
      parser.processChunk('{"reasoning": "He said \\"hello\\""}')
      expect(parser.parsed.evalTypeReasoning).toBe('He said "hello"')
    })

    it('STREAM_027: does not re-extract completed fields', () => {
      parser.processChunk('{"evaluation_type": "ranking"}')
      expect(parser.parsed.evalType).toBe('ranking')

      // Add more data - should not change completed field
      parser.processChunk(', "evaluation_type": "rating"')
      expect(parser.parsed.evalType).toBe('ranking')
    })

    it('STREAM_028: extracts multiple fields from a single large chunk', () => {
      parser.processChunk('{"evaluation_type": "comparison", "confidence": 0.75, "name": "Test", "description": "Desc", "reasoning": "Reason"}')
      expect(parser.parsed.evalType).toBe('comparison')
      expect(parser.parsed.evalTypeConfidence).toBe(0.75)
      expect(parser.parsed.scenarioName).toBe('Test')
      expect(parser.parsed.scenarioDescription).toBe('Desc')
      expect(parser.parsed.evalTypeReasoning).toBe('Reason')
    })
  })

  // ==================== processSuggestions Tests ====================

  describe('processSuggestions', () => {
    it('STREAM_029: processes complete suggestions with new field names', () => {
      parser.processSuggestions({
        evaluation_type: 'labeling',
        confidence: 0.9,
        reasoning: 'Good match',
        name: 'Label Scenario',
        description: 'For labeling tasks',
        config: { type: 'labeling' }
      })

      expect(parser.parsed.evalType).toBe('labeling')
      expect(parser.parsed.evalTypeConfidence).toBe(0.9)
      expect(parser.parsed.evalTypeReasoning).toBe('Good match')
      expect(parser.parsed.scenarioName).toBe('Label Scenario')
      expect(parser.parsed.scenarioDescription).toBe('For labeling tasks')
      expect(parser.parsed.configSuggestions).toEqual({ type: 'labeling' })
    })

    it('STREAM_030: processes suggestions with old field names', () => {
      parser.processSuggestions({
        eval_type: 'rating',
        eval_type_confidence: 0.8,
        eval_type_reasoning: 'Matches rating pattern',
        scenario_name: 'Old Name',
        scenario_description: 'Old Desc',
        config_suggestions: { min: 1, max: 5 }
      })

      expect(parser.parsed.evalType).toBe('rating')
      expect(parser.parsed.evalTypeConfidence).toBe(0.8)
      expect(parser.parsed.evalTypeReasoning).toBe('Matches rating pattern')
      expect(parser.parsed.scenarioName).toBe('Old Name')
      expect(parser.parsed.scenarioDescription).toBe('Old Desc')
      expect(parser.parsed.configSuggestions).toEqual({ min: 1, max: 5 })
    })

    it('STREAM_031: sets all field states to COMPLETE', () => {
      parser.processSuggestions({
        evaluation_type: 'ranking',
        confidence: 0.95,
        reasoning: 'R',
        name: 'N',
        description: 'D',
        config: {}
      })

      expect(parser.fieldState.evalType).toBe(FIELD_STATE.COMPLETE)
      expect(parser.fieldState.evalTypeConfidence).toBe(FIELD_STATE.COMPLETE)
      expect(parser.fieldState.evalTypeReasoning).toBe(FIELD_STATE.COMPLETE)
      expect(parser.fieldState.scenarioName).toBe(FIELD_STATE.COMPLETE)
      expect(parser.fieldState.scenarioDescription).toBe(FIELD_STATE.COMPLETE)
      expect(parser.fieldState.configSuggestions).toBe(FIELD_STATE.COMPLETE)
    })

    it('STREAM_032: handles confidence of 0 correctly (nullish coalescing)', () => {
      parser.processSuggestions({ confidence: 0 })
      expect(parser.parsed.evalTypeConfidence).toBe(0)
    })

    it('STREAM_033: handles partial suggestions (only some fields)', () => {
      parser.processSuggestions({ evaluation_type: 'ranking' })
      expect(parser.parsed.evalType).toBe('ranking')
      expect(parser.parsed.evalTypeConfidence).toBeNull()
      expect(parser.parsed.scenarioName).toBe('')
    })
  })

  // ==================== processDataQuality Tests ====================

  describe('processDataQuality', () => {
    it('STREAM_034: stores data quality object', () => {
      const quality = { score: 0.8, issues: ['missing_headers'] }
      parser.processDataQuality(quality)
      expect(parser.parsed.dataQuality).toEqual(quality)
      expect(parser.fieldState.dataQuality).toBe(FIELD_STATE.COMPLETE)
    })
  })

  // ==================== finalize Tests ====================

  describe('finalize', () => {
    it('STREAM_035: sets isStreaming to false and isComplete to true', () => {
      parser.processChunk('some data')
      expect(parser.isStreaming.value).toBe(true)

      parser.finalize()
      expect(parser.isStreaming.value).toBe(false)
      expect(parser.isComplete.value).toBe(true)
    })

    it('STREAM_036: marks all remaining fields as COMPLETE', () => {
      parser.finalize()
      Object.values(parser.fieldState).forEach(state => {
        expect(state).toBe(FIELD_STATE.COMPLETE)
      })
    })
  })

  // ==================== setError Tests ====================

  describe('setError', () => {
    it('STREAM_037: sets error value and stops streaming', () => {
      parser.processChunk('data')
      expect(parser.isStreaming.value).toBe(true)

      parser.setError('Connection lost')
      expect(parser.error.value).toBe('Connection lost')
      expect(parser.isStreaming.value).toBe(false)
    })
  })

  // ==================== reset Tests ====================

  describe('reset', () => {
    it('STREAM_038: clears buffer and parsed values', () => {
      parser.processChunk('{"evaluation_type": "ranking", "confidence": 0.9}')
      parser.processSuggestions({
        evaluation_type: 'ranking',
        confidence: 0.9,
        name: 'Test',
        description: 'Desc',
        reasoning: 'R'
      })

      parser.reset()

      expect(parser.buffer.value).toBe('')
      expect(parser.parsed.evalType).toBeNull()
      expect(parser.parsed.evalTypeConfidence).toBeNull()
      expect(parser.parsed.evalTypeReasoning).toBe('')
      expect(parser.parsed.scenarioName).toBe('')
      expect(parser.parsed.scenarioDescription).toBe('')
      expect(parser.parsed.dataQuality).toBeNull()
      expect(parser.parsed.configSuggestions).toBeNull()
    })

    it('STREAM_039: resets all field states to PENDING', () => {
      parser.finalize()
      parser.reset()

      Object.values(parser.fieldState).forEach(state => {
        expect(state).toBe(FIELD_STATE.PENDING)
      })
    })

    it('STREAM_040: resets streaming and complete flags', () => {
      parser.processChunk('data')
      parser.finalize()
      parser.reset()

      expect(parser.isStreaming.value).toBe(false)
      expect(parser.isComplete.value).toBe(false)
    })

    it('STREAM_041: clears error', () => {
      parser.setError('Some error')
      parser.reset()
      expect(parser.error.value).toBeNull()
    })
  })

  // ==================== Computed Tests ====================

  describe('computed properties', () => {
    it('STREAM_042: confidencePercent rounds to integer', () => {
      parser.processSuggestions({ confidence: 0.856 })
      expect(parser.confidencePercent.value).toBe(86)
    })

    it('STREAM_043: confidencePercent handles 100%', () => {
      parser.processSuggestions({ confidence: 1.0 })
      expect(parser.confidencePercent.value).toBe(100)
    })

    it('STREAM_044: hasAnyContent is true when evalType is set', () => {
      parser.processSuggestions({ evaluation_type: 'ranking' })
      expect(parser.hasAnyContent.value).toBeTruthy()
    })

    it('STREAM_045: hasAnyContent is true when scenarioName is set', () => {
      parser.processChunk('{"name": "Test Scenario"}')
      expect(parser.hasAnyContent.value).toBeTruthy()
    })
  })
})
