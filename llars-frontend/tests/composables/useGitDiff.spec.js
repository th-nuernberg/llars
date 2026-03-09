/**
 * useGitDiff Composable Tests
 *
 * Tests for character-level diff comparison against Git baseline.
 * Test IDs: GIT_DIFF_001 - GIT_DIFF_045
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

// Mock authStorage
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: { token: 'llars_token' },
  getAuthStorageItem: vi.fn(() => 'test-token')
}))

// Mock logI18n
vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

// Mock diff-match-patch
const mockDiffMain = vi.fn()
const mockDiffCleanup = vi.fn()
class MockDiffMatchPatch {
  constructor() {
    this.diff_main = mockDiffMain
    this.diff_cleanupSemantic = mockDiffCleanup
  }
}
vi.mock('diff-match-patch', () => ({
  default: MockDiffMatchPatch
}))

// Mock @codemirror/view
vi.mock('@codemirror/view', () => ({
  Decoration: {
    mark: vi.fn((spec) => ({
      range: vi.fn((from, to) => ({ from, to, spec }))
    }))
  }
}))

import axios from 'axios'

let useGitDiff

describe('useGitDiff', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    mockDiffMain.mockReset()
    mockDiffCleanup.mockReset()

    const module = await import('@/composables/useGitDiff')
    useGitDiff = module.useGitDiff
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('GIT_DIFF_001: returns all expected properties', () => {
      const result = useGitDiff()
      expect(result).toHaveProperty('gitBaseline')
      expect(result).toHaveProperty('baselineCommitId')
      expect(result).toHaveProperty('isLoading')
      expect(result).toHaveProperty('error')
      expect(typeof result.loadBaseline).toBe('function')
      expect(typeof result.computeCharacterDiffs).toBe('function')
      expect(typeof result.getInsertRanges).toBe('function')
      expect(typeof result.diffsToDecorations).toBe('function')
      expect(typeof result.hasChanges).toBe('function')
      expect(typeof result.getChangeSummary).toBe('function')
      expect(typeof result.updateBaseline).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('GIT_DIFF_002: baseline starts null', () => {
      const { gitBaseline } = useGitDiff()
      expect(gitBaseline.value).toBeNull()
    })

    it('GIT_DIFF_003: baselineCommitId starts null', () => {
      const { baselineCommitId } = useGitDiff()
      expect(baselineCommitId.value).toBeNull()
    })

    it('GIT_DIFF_004: isLoading starts false', () => {
      const { isLoading } = useGitDiff()
      expect(isLoading.value).toBe(false)
    })

    it('GIT_DIFF_005: error starts null', () => {
      const { error } = useGitDiff()
      expect(error.value).toBeNull()
    })
  })

  // ==================== loadBaseline ====================

  describe('loadBaseline', () => {
    it('GIT_DIFF_006: loads baseline from API', async () => {
      axios.get.mockResolvedValue({
        data: { success: true, baseline: 'Hello world', commit_id: 42 }
      })

      const { loadBaseline, gitBaseline, baselineCommitId } = useGitDiff()
      await loadBaseline(1)

      expect(gitBaseline.value).toBe('Hello world')
      expect(baselineCommitId.value).toBe(42)
    })

    it('GIT_DIFF_007: uses correct API prefix', async () => {
      axios.get.mockResolvedValue({
        data: { success: true, baseline: '', commit_id: 1 }
      })

      const { loadBaseline } = useGitDiff({ apiPrefix: '/api/custom' })
      await loadBaseline(5)

      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/custom/documents/5/baseline'),
        expect.any(Object)
      )
    })

    it('GIT_DIFF_008: sets baseline null on unsuccessful response', async () => {
      axios.get.mockResolvedValue({
        data: { success: false }
      })

      const { loadBaseline, gitBaseline, baselineCommitId } = useGitDiff()
      await loadBaseline(1)

      expect(gitBaseline.value).toBeNull()
      expect(baselineCommitId.value).toBeNull()
    })

    it('GIT_DIFF_009: handles API error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const { loadBaseline, error, gitBaseline } = useGitDiff()
      await loadBaseline(1)

      expect(error.value).toBe('Network error')
      expect(gitBaseline.value).toBeNull()
    })

    it('GIT_DIFF_010: does nothing for null documentId', async () => {
      const { loadBaseline } = useGitDiff()
      await loadBaseline(null)

      expect(axios.get).not.toHaveBeenCalled()
    })

    it('GIT_DIFF_011: sets isLoading during request', async () => {
      let resolvePromise
      axios.get.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { loadBaseline, isLoading } = useGitDiff()
      const promise = loadBaseline(1)
      expect(isLoading.value).toBe(true)

      resolvePromise({ data: { success: true, baseline: '', commit_id: 1 } })
      await promise
      expect(isLoading.value).toBe(false)
    })
  })

  // ==================== computeCharacterDiffs ====================

  describe('computeCharacterDiffs', () => {
    it('GIT_DIFF_012: returns empty during loading', () => {
      const { computeCharacterDiffs, isLoading } = useGitDiff()
      isLoading.value = true

      const result = computeCharacterDiffs('text')
      expect(result).toEqual([])
    })

    it('GIT_DIFF_013: returns empty when no baseline', () => {
      const { computeCharacterDiffs } = useGitDiff()
      const result = computeCharacterDiffs('text')
      expect(result).toEqual([])
    })

    it('GIT_DIFF_014: returns empty for identical content', () => {
      const { computeCharacterDiffs, gitBaseline } = useGitDiff()
      gitBaseline.value = 'Hello world'

      const result = computeCharacterDiffs('Hello world')
      expect(result).toEqual([])
      expect(mockDiffMain).not.toHaveBeenCalled()
    })

    it('GIT_DIFF_015: computes diffs for changed content', () => {
      const diffs = [[0, 'Hello '], [1, 'beautiful '], [0, 'world']]
      mockDiffMain.mockReturnValue(diffs)

      const { computeCharacterDiffs, gitBaseline } = useGitDiff()
      gitBaseline.value = 'Hello world'

      const result = computeCharacterDiffs('Hello beautiful world')
      expect(mockDiffMain).toHaveBeenCalledWith('Hello world', 'Hello beautiful world')
      expect(mockDiffCleanup).toHaveBeenCalledWith(diffs)
      expect(result).toEqual(diffs)
    })

    it('GIT_DIFF_016: treats null content as empty string', () => {
      mockDiffMain.mockReturnValue([[0, '']])

      const { computeCharacterDiffs, gitBaseline } = useGitDiff()
      gitBaseline.value = 'Some content'

      computeCharacterDiffs(null)
      expect(mockDiffMain).toHaveBeenCalledWith('Some content', '')
    })
  })

  // ==================== hasChanges ====================

  describe('hasChanges', () => {
    it('GIT_DIFF_017: returns false during loading', () => {
      const { hasChanges, isLoading } = useGitDiff()
      isLoading.value = true
      expect(hasChanges('text')).toBe(false)
    })

    it('GIT_DIFF_018: returns false when no baseline', () => {
      const { hasChanges } = useGitDiff()
      expect(hasChanges('text')).toBe(false)
    })

    it('GIT_DIFF_019: returns false for identical content', () => {
      const { hasChanges, gitBaseline } = useGitDiff()
      gitBaseline.value = 'Hello world'
      expect(hasChanges('Hello world')).toBe(false)
    })

    it('GIT_DIFF_020: returns true for different content', () => {
      const { hasChanges, gitBaseline } = useGitDiff()
      gitBaseline.value = 'Hello world'
      expect(hasChanges('Hello universe')).toBe(true)
    })

    it('GIT_DIFF_021: treats null content as empty string', () => {
      const { hasChanges, gitBaseline } = useGitDiff()
      gitBaseline.value = ''
      expect(hasChanges(null)).toBe(false)
    })

    it('GIT_DIFF_022: detects changes from empty baseline', () => {
      const { hasChanges, gitBaseline } = useGitDiff()
      gitBaseline.value = ''
      expect(hasChanges('new content')).toBe(true)
    })
  })

  // ==================== getChangeSummary ====================

  describe('getChangeSummary', () => {
    it('GIT_DIFF_023: returns zeros for empty diffs', () => {
      const { getChangeSummary } = useGitDiff()
      const result = getChangeSummary([])
      expect(result).toEqual({ insertions: 0, deletions: 0, changes: 0 })
    })

    it('GIT_DIFF_024: returns zeros for null diffs', () => {
      const { getChangeSummary } = useGitDiff()
      const result = getChangeSummary(null)
      expect(result).toEqual({ insertions: 0, deletions: 0, changes: 0 })
    })

    it('GIT_DIFF_025: counts insertions correctly', () => {
      const { getChangeSummary } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [1, 'beautiful '],
        [0, 'world']
      ]
      const result = getChangeSummary(diffs)
      expect(result.insertions).toBe(10) // 'beautiful ' = 10 chars
      expect(result.deletions).toBe(0)
      expect(result.changes).toBe(10)
    })

    it('GIT_DIFF_026: counts deletions correctly', () => {
      const { getChangeSummary } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [-1, 'old '],
        [0, 'world']
      ]
      const result = getChangeSummary(diffs)
      expect(result.insertions).toBe(0)
      expect(result.deletions).toBe(4)
      expect(result.changes).toBe(4)
    })

    it('GIT_DIFF_027: counts mixed changes', () => {
      const { getChangeSummary } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [-1, 'old'],
        [1, 'new'],
        [0, ' world']
      ]
      const result = getChangeSummary(diffs)
      expect(result.insertions).toBe(3)
      expect(result.deletions).toBe(3)
      expect(result.changes).toBe(6)
    })
  })

  // ==================== updateBaseline ====================

  describe('updateBaseline', () => {
    it('GIT_DIFF_028: updates baseline content', () => {
      const { updateBaseline, gitBaseline } = useGitDiff()
      updateBaseline('new baseline content')
      expect(gitBaseline.value).toBe('new baseline content')
    })

    it('GIT_DIFF_029: clears changes after update', () => {
      const { updateBaseline, gitBaseline, hasChanges } = useGitDiff()
      gitBaseline.value = 'old content'

      updateBaseline('current content')
      expect(hasChanges('current content')).toBe(false)
    })
  })

  // ==================== getInsertRanges ====================

  describe('getInsertRanges', () => {
    it('GIT_DIFF_030: returns empty for null diffs', () => {
      const { getInsertRanges } = useGitDiff()
      expect(getInsertRanges(null)).toEqual([])
    })

    it('GIT_DIFF_031: returns empty for empty diffs', () => {
      const { getInsertRanges } = useGitDiff()
      expect(getInsertRanges([])).toEqual([])
    })

    it('GIT_DIFF_032: returns ranges for insertions', () => {
      const { getInsertRanges } = useGitDiff()
      const diffs = [
        [0, 'Hello '],    // 6 chars
        [1, 'beautiful '], // 10 chars inserted at pos 6
        [0, 'world']
      ]
      const ranges = getInsertRanges(diffs)
      expect(ranges).toHaveLength(1)
      expect(ranges[0]).toEqual({ from: 6, to: 16 })
    })

    it('GIT_DIFF_033: handles multiple insertions', () => {
      const { getInsertRanges } = useGitDiff()
      const diffs = [
        [1, 'AAA'],   // pos 0-3
        [0, 'BBB'],   // pos 3-6
        [1, 'CCC'],   // pos 6-9
      ]
      const ranges = getInsertRanges(diffs)
      expect(ranges).toHaveLength(2)
      expect(ranges[0]).toEqual({ from: 0, to: 3 })
      expect(ranges[1]).toEqual({ from: 6, to: 9 })
    })

    it('GIT_DIFF_034: skips deletions (no position advance)', () => {
      const { getInsertRanges } = useGitDiff()
      const diffs = [
        [0, 'AB'],    // pos 0-2
        [-1, 'XY'],   // deleted, no advance
        [1, 'CD'],    // pos 2-4
        [0, 'EF']
      ]
      const ranges = getInsertRanges(diffs)
      expect(ranges).toHaveLength(1)
      expect(ranges[0]).toEqual({ from: 2, to: 4 })
    })
  })

  // ==================== diffsToDecorations ====================

  describe('diffsToDecorations', () => {
    it('GIT_DIFF_035: returns empty for null diffs', () => {
      const { diffsToDecorations } = useGitDiff()
      const result = diffsToDecorations(null, {})
      expect(result.decorations).toEqual([])
      expect(result.deletedLines.size).toBe(0)
    })

    it('GIT_DIFF_036: returns empty for empty diffs', () => {
      const { diffsToDecorations } = useGitDiff()
      const result = diffsToDecorations([], {})
      expect(result.decorations).toEqual([])
      expect(result.deletedLines.size).toBe(0)
    })

    it('GIT_DIFF_037: returns empty when no view', () => {
      const { diffsToDecorations } = useGitDiff()
      const result = diffsToDecorations([[0, 'text']], null)
      expect(result.decorations).toEqual([])
    })

    it('GIT_DIFF_038: creates decorations for insertions', () => {
      const mockView = {
        state: {
          doc: {
            length: 100,
            lineAt: vi.fn(() => ({ number: 1 }))
          }
        }
      }

      const { diffsToDecorations } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [1, 'new '],
        [0, 'world']
      ]
      const result = diffsToDecorations(diffs, mockView)
      expect(result.decorations.length).toBeGreaterThan(0)
    })

    it('GIT_DIFF_039: tracks deleted lines', () => {
      const mockView = {
        state: {
          doc: {
            length: 100,
            lineAt: vi.fn(() => ({ number: 3 })),
            lines: 10
          }
        }
      }

      const { diffsToDecorations } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [-1, 'removed '],
        [0, 'world']
      ]
      const result = diffsToDecorations(diffs, mockView)
      expect(result.deletedLines.has(3)).toBe(true)
    })

    it('GIT_DIFF_040: skips insert decorations when disabled', () => {
      const mockView = {
        state: {
          doc: {
            length: 100,
            lineAt: vi.fn(() => ({ number: 1 }))
          }
        }
      }

      const { diffsToDecorations } = useGitDiff()
      const diffs = [
        [0, 'Hello '],
        [1, 'new '],
        [0, 'world']
      ]
      const result = diffsToDecorations(diffs, mockView, null, { includeInsertDecorations: false })
      expect(result.decorations).toEqual([])
    })

    it('GIT_DIFF_041: clamps positions to document bounds', () => {
      const mockView = {
        state: {
          doc: {
            length: 5,
            lineAt: vi.fn(() => ({ number: 1 }))
          }
        }
      }

      const { diffsToDecorations } = useGitDiff()
      const diffs = [
        [1, 'a very long inserted text that exceeds doc length']
      ]
      // Should not throw
      const result = diffsToDecorations(diffs, mockView)
      expect(result).toBeDefined()
    })

    it('GIT_DIFF_042: applies user color from highlights data', () => {
      const mockView = {
        state: {
          doc: {
            length: 100,
            lineAt: vi.fn(() => ({ number: 1 }))
          }
        }
      }

      const highlightsData = {
        '1': { color: '#ff0000', username: 'user1' }
      }

      const { diffsToDecorations } = useGitDiff()
      const diffs = [
        [1, 'inserted text']
      ]
      const result = diffsToDecorations(diffs, mockView, highlightsData)
      expect(result.decorations.length).toBeGreaterThan(0)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('GIT_DIFF_043: handles empty string baseline', () => {
      const { gitBaseline, hasChanges } = useGitDiff()
      gitBaseline.value = ''
      expect(hasChanges('')).toBe(false)
      expect(hasChanges('something')).toBe(true)
    })

    it('GIT_DIFF_044: getChangeSummary handles only equal ops', () => {
      const { getChangeSummary } = useGitDiff()
      const diffs = [[0, 'unchanged text']]
      const result = getChangeSummary(diffs)
      expect(result.insertions).toBe(0)
      expect(result.deletions).toBe(0)
      expect(result.changes).toBe(0)
    })

    it('GIT_DIFF_045: updateBaseline to null', () => {
      const { updateBaseline, gitBaseline } = useGitDiff()
      updateBaseline(null)
      expect(gitBaseline.value).toBeNull()
    })
  })
})
