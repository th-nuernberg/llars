/**
 * useWorkerState Composable Tests
 *
 * Tests for worker state management, pillar helpers, and progress calculations.
 * Test IDs: WORKER_ST_001 - WORKER_ST_025
 */

import { describe, it, expect } from 'vitest'
import {
  PILLAR_CONFIG,
  CRITERIA_CONFIG,
  STEP_CONFIG,
  WORKER_COLORS,
  useWorkerState
} from '@/components/Judge/WorkerLane/composables/useWorkerState'
import { reactive } from 'vue'

describe('useWorkerState', () => {
  function createProps(overrides = {}) {
    return reactive({
      workerId: 0,
      currentComparison: null,
      streamContent: '',
      isStreaming: false,
      ...overrides
    })
  }

  // ==================== Constants ====================

  describe('constants', () => {
    it('WORKER_ST_001: PILLAR_CONFIG has 5 entries', () => {
      expect(Object.keys(PILLAR_CONFIG)).toHaveLength(5)
    })

    it('WORKER_ST_002: CRITERIA_CONFIG has 6 criteria', () => {
      expect(CRITERIA_CONFIG).toHaveLength(6)
    })

    it('WORKER_ST_003: each criterion has key, short, and full', () => {
      CRITERIA_CONFIG.forEach(c => {
        expect(c).toHaveProperty('key')
        expect(c).toHaveProperty('short')
        expect(c).toHaveProperty('full')
      })
    })

    it('WORKER_ST_004: STEP_CONFIG has 6 steps', () => {
      expect(STEP_CONFIG).toHaveLength(6)
    })

    it('WORKER_ST_005: WORKER_COLORS has 5 colors', () => {
      expect(WORKER_COLORS).toHaveLength(5)
    })
  })

  // ==================== Computed Properties ====================

  describe('workerColorName', () => {
    it('WORKER_ST_006: returns color based on workerId modulo', () => {
      const state = useWorkerState(createProps({ workerId: 0 }))
      expect(state.workerColorName.value).toBe('blue')
    })

    it('WORKER_ST_007: wraps around for large IDs', () => {
      const state = useWorkerState(createProps({ workerId: 5 }))
      expect(state.workerColorName.value).toBe('blue')
    })
  })

  describe('isActive', () => {
    it('WORKER_ST_008: inactive when no comparison and no stream', () => {
      const state = useWorkerState(createProps())
      expect(state.isActive.value).toBe(false)
    })

    it('WORKER_ST_009: active when has current comparison', () => {
      const state = useWorkerState(createProps({ currentComparison: { id: 1 } }))
      expect(state.isActive.value).toBe(true)
    })

    it('WORKER_ST_010: active when has stream content', () => {
      const state = useWorkerState(createProps({ streamContent: 'some content' }))
      expect(state.isActive.value).toBe(true)
    })
  })

  describe('statusType', () => {
    it('WORKER_ST_011: returns idle when no comparison and not streaming', () => {
      const state = useWorkerState(createProps())
      expect(state.statusType.value).toBe('idle')
    })

    it('WORKER_ST_012: returns streaming when isStreaming', () => {
      const state = useWorkerState(createProps({ isStreaming: true }))
      expect(state.statusType.value).toBe('streaming')
    })

    it('WORKER_ST_013: returns active when has comparison', () => {
      const state = useWorkerState(createProps({ currentComparison: { id: 1 } }))
      expect(state.statusType.value).toBe('active')
    })
  })

  describe('statusColor', () => {
    it('WORKER_ST_014: returns grey for idle', () => {
      const state = useWorkerState(createProps())
      expect(state.statusColor.value).toBe('grey')
    })

    it('WORKER_ST_015: returns warning for streaming', () => {
      const state = useWorkerState(createProps({ isStreaming: true }))
      expect(state.statusColor.value).toBe('warning')
    })

    it('WORKER_ST_016: returns info for active', () => {
      const state = useWorkerState(createProps({ currentComparison: { id: 1 } }))
      expect(state.statusColor.value).toBe('info')
    })
  })

  describe('statusText', () => {
    it('WORKER_ST_017: returns Wartet for idle', () => {
      const state = useWorkerState(createProps())
      expect(state.statusText.value).toBe('Wartet')
    })

    it('WORKER_ST_018: returns Streamt for streaming', () => {
      const state = useWorkerState(createProps({ isStreaming: true }))
      expect(state.statusText.value).toBe('Streamt')
    })
  })

  // ==================== Progress ====================

  describe('progressOffset', () => {
    it('WORKER_ST_019: returns full circumference when 0 steps completed', () => {
      const state = useWorkerState(createProps())
      const offset = state.progressOffset(0)
      expect(offset).toBeCloseTo(state.progressCircumference.value)
    })

    it('WORKER_ST_020: returns 0 when all 6 steps completed', () => {
      const state = useWorkerState(createProps())
      const offset = state.progressOffset(6)
      expect(offset).toBeCloseTo(0)
    })
  })

  // ==================== Pillar Helpers ====================

  describe('getPillarIcon', () => {
    it('WORKER_ST_021: returns icon for known pillar', () => {
      const state = useWorkerState(createProps())
      expect(state.getPillarIcon(1)).toBe('mdi-theater')
    })

    it('WORKER_ST_022: returns help-circle for unknown pillar', () => {
      const state = useWorkerState(createProps())
      expect(state.getPillarIcon(99)).toBe('mdi-help-circle')
    })
  })

  describe('getPillarShortName', () => {
    it('WORKER_ST_023: extracts Sn from Säule n format', () => {
      const state = useWorkerState(createProps())
      expect(state.getPillarShortName('Säule 3')).toBe('S3')
    })

    it('WORKER_ST_024: truncates other names', () => {
      const state = useWorkerState(createProps())
      const result = state.getPillarShortName('Rollenspiele')
      expect(result).toBe('Rollen')
    })

    it('WORKER_ST_025: returns empty string for falsy name', () => {
      const state = useWorkerState(createProps())
      expect(state.getPillarShortName(null)).toBe('')
      expect(state.getPillarShortName('')).toBe('')
    })
  })

  describe('truncateText', () => {
    it('WORKER_ST_026: returns full text if under maxLength', () => {
      const state = useWorkerState(createProps())
      expect(state.truncateText('short', 10)).toBe('short')
    })

    it('WORKER_ST_027: truncates long text', () => {
      const state = useWorkerState(createProps())
      expect(state.truncateText('This is a very long text', 10)).toBe('This is a ...')
    })

    it('WORKER_ST_028: returns empty string for falsy text', () => {
      const state = useWorkerState(createProps())
      expect(state.truncateText(null, 10)).toBe('')
      expect(state.truncateText('', 10)).toBe('')
    })
  })
})
