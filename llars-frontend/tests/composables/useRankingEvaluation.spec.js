/**
 * useRankingEvaluation Composable Tests
 *
 * Tests for the bucket-based ranking evaluation composable.
 * Test IDs: RANK_EVAL_001 - RANK_EVAL_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

import axios from 'axios'

let useRankingEvaluation

describe('useRankingEvaluation Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    vi.useFakeTimers()

    const module = await import('@/composables/useRankingEvaluation')
    useRankingEvaluation = module.useRankingEvaluation
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('RANK_EVAL_001: exports useRankingEvaluation function', () => {
      expect(typeof useRankingEvaluation).toBe('function')
    })

    it('RANK_EVAL_002: returns all expected properties', () => {
      const scenarioId = ref(1)
      const result = useRankingEvaluation(scenarioId)

      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('currentItem')
      expect(result).toHaveProperty('currentItemIndex')
      expect(result).toHaveProperty('messages')
      expect(result).toHaveProperty('content')
      expect(result).toHaveProperty('config')
      expect(result).toHaveProperty('selectedBucket')
      expect(result).toHaveProperty('notes')
      expect(result).toHaveProperty('buckets')
      expect(result).toHaveProperty('existingRanking')
      expect(result).toHaveProperty('loading')
      expect(result).toHaveProperty('loadingItem')
      expect(result).toHaveProperty('saving')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('progress')
      expect(result).toHaveProperty('hasNext')
      expect(result).toHaveProperty('hasPrev')
      expect(result).toHaveProperty('currentItemStatus')
      expect(result).toHaveProperty('loadItems')
      expect(result).toHaveProperty('loadItem')
      expect(result).toHaveProperty('selectBucket')
      expect(result).toHaveProperty('saveMetadata')
      expect(result).toHaveProperty('goToItem')
      expect(result).toHaveProperty('goNext')
      expect(result).toHaveProperty('goPrev')
      expect(result).toHaveProperty('reset')
    })
  })

  // ==================== Default Buckets ====================

  describe('Bucket Management', () => {
    it('RANK_EVAL_003: provides default buckets when no config', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      const defaultBuckets = ranking.buckets.value

      expect(defaultBuckets).toHaveLength(3)
      expect(defaultBuckets[0].id).toBe('good')
      expect(defaultBuckets[1].id).toBe('moderate')
      expect(defaultBuckets[2].id).toBe('bad')
    })

    it('RANK_EVAL_004: uses config buckets when provided', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.config.value = {
        buckets: [
          { id: 'excellent', name: 'Excellent' },
          { id: 'average', name: 'Average' },
          { id: 'poor', name: 'Poor' },
          { id: 'terrible', name: 'Terrible' }
        ]
      }

      expect(ranking.buckets.value).toHaveLength(4)
      expect(ranking.buckets.value[0].id).toBe('excellent')
      expect(ranking.buckets.value[3].id).toBe('terrible')
    })

    it('RANK_EVAL_005: falls back to default buckets when config has empty array', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.config.value = { buckets: [] }

      expect(ranking.buckets.value).toHaveLength(3)
      expect(ranking.buckets.value[0].id).toBe('good')
    })

    it('RANK_EVAL_006: selectedBucket is null initially', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.selectedBucket.value).toBeNull()
    })
  })

  // ==================== Item Assignment (selectBucket) ====================

  describe('Bucket Selection', () => {
    it('RANK_EVAL_007: selectBucket saves to API', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 10 }
      ranking.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      const result = await ranking.selectBucket('good')

      expect(result.success).toBe(true)
      expect(result.bucket).toBe('good')
      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/10/evaluate',
        expect.objectContaining({
          function_type: 'ranking',
          bucket: 'good'
        })
      )
    })

    it('RANK_EVAL_008: selectBucket updates local state', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 10 }
      ranking.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      await ranking.selectBucket('moderate')

      expect(ranking.selectedBucket.value).toBe('moderate')
      expect(ranking.items.value[0].evaluated).toBe(true)
      expect(ranking.items.value[0].ranked).toBe(true)
    })

    it('RANK_EVAL_009: selectBucket returns error when no item selected', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      const result = await ranking.selectBucket('good')

      expect(result.success).toBe(false)
      expect(result.error).toBe('No item selected')
    })

    it('RANK_EVAL_010: selectBucket handles API error', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 10 }
      ranking.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      const result = await ranking.selectBucket('good')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Server error')
      expect(ranking.error.value).toBe('Server error')
    })

    it('RANK_EVAL_011: selectBucket includes notes when present', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 10 }
      ranking.items.value = [{ thread_id: 10, evaluated: false }]
      ranking.notes.value = 'This is a note'

      axios.post.mockResolvedValue({ data: {} })

      await ranking.selectBucket('good')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          notes: 'This is a note'
        })
      )
    })
  })

  // ==================== Current Item Status ====================

  describe('Current Item Status', () => {
    it('RANK_EVAL_012: currentItemStatus is pending when no item', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.currentItemStatus.value).toBe('pending')
    })

    it('RANK_EVAL_013: currentItemStatus is done when bucket selected', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 1, evaluated: false }
      ranking.selectedBucket.value = 'good'

      expect(ranking.currentItemStatus.value).toBe('done')
    })

    it('RANK_EVAL_014: currentItemStatus is done when item is evaluated', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 1, evaluated: true }

      expect(ranking.currentItemStatus.value).toBe('done')
    })

    it('RANK_EVAL_015: currentItemStatus is in_progress when has notes only', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 1, evaluated: false }
      ranking.notes.value = 'Some notes'

      expect(ranking.currentItemStatus.value).toBe('in_progress')
    })

    it('RANK_EVAL_016: currentItemStatus is pending with no interaction', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 1, evaluated: false }

      expect(ranking.currentItemStatus.value).toBe('pending')
    })
  })

  // ==================== Progress ====================

  describe('Progress', () => {
    it('RANK_EVAL_017: progress tracks evaluation state', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [
        { thread_id: 1, evaluated: true },
        { thread_id: 2, evaluated: false, status: 'Progressing' },
        { thread_id: 3, evaluated: false }
      ]

      expect(ranking.progress.value.total).toBe(3)
      expect(ranking.progress.value.completed).toBe(1)
      expect(ranking.progress.value.inProgress).toBe(1)
      expect(ranking.progress.value.notStarted).toBe(1)
      expect(ranking.progress.value.percent).toBe(33)
    })

    it('RANK_EVAL_018: progress percent is 0 when empty', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.progress.value.percent).toBe(0)
    })
  })

  // ==================== Navigation ====================

  describe('Navigation', () => {
    it('RANK_EVAL_019: hasNext computed is correct', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 1 }, { thread_id: 2 }]
      ranking.currentItemIndex.value = 0

      expect(ranking.hasNext.value).toBe(true)
    })

    it('RANK_EVAL_020: hasNext is false at last item', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 1 }, { thread_id: 2 }]
      ranking.currentItemIndex.value = 1

      expect(ranking.hasNext.value).toBe(false)
    })

    it('RANK_EVAL_021: hasPrev is false at first item', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 1 }, { thread_id: 2 }]
      ranking.currentItemIndex.value = 0

      expect(ranking.hasPrev.value).toBe(false)
    })

    it('RANK_EVAL_022: hasPrev is true when not at first', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 1 }, { thread_id: 2 }]
      ranking.currentItemIndex.value = 1

      expect(ranking.hasPrev.value).toBe(true)
    })
  })

  // ==================== Load Items ====================

  describe('Load Items', () => {
    it('RANK_EVAL_023: loadItems calls session endpoint', async () => {
      const scenarioId = ref(42)
      const ranking = useRankingEvaluation(scenarioId)

      axios.get.mockResolvedValue({
        data: { items: [], config: {} }
      })

      await ranking.loadItems()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/session/42')
    })

    it('RANK_EVAL_024: loadItems populates items and config', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      const mockItems = [
        { thread_id: 1, evaluated: false },
        { thread_id: 2, evaluated: true }
      ]
      const mockConfig = { buckets: [{ id: 'good', name: 'Good' }] }

      axios.get.mockResolvedValue({
        data: { items: mockItems, config: mockConfig }
      })

      await ranking.loadItems()

      expect(ranking.items.value).toHaveLength(2)
      expect(ranking.config.value).toEqual(mockConfig)
    })

    it('RANK_EVAL_025: loadItems sets error on failure', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      await ranking.loadItems()

      expect(ranking.error.value).toBe('Not found')
      expect(ranking.loading.value).toBe(false)
    })
  })

  // ==================== Load Item ====================

  describe('Load Item', () => {
    it('RANK_EVAL_026: loadItem calls ranking endpoint', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 5 }]

      axios.get
        .mockResolvedValueOnce({
          data: { chat_id: 1, subject: 'Test', ranked: false, messages: [] }
        })
        .mockRejectedValueOnce(new Error('No ranking'))

      await ranking.loadItem(5)

      expect(axios.get).toHaveBeenCalledWith('/api/email_threads/rankings/5')
      expect(ranking.currentItem.value.thread_id).toBe(5)
      expect(ranking.currentItem.value.subject).toBe('Test')
    })

    it('RANK_EVAL_027: loadItem sets selectedBucket when ranking exists', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 5 }]

      axios.get
        .mockResolvedValueOnce({
          data: { chat_id: 1, subject: 'Test', ranked: true, messages: [] }
        })
        .mockResolvedValueOnce({
          data: [{ bucket: 'good' }]
        })

      await ranking.loadItem(5)

      expect(ranking.selectedBucket.value).toBe('ranked')
    })

    it('RANK_EVAL_028: loadItem sets error on failure', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { error: 'Thread not found' } }
      })

      await ranking.loadItem(999)

      expect(ranking.error.value).toBe('Thread not found')
      expect(ranking.loadingItem.value).toBe(false)
    })
  })

  // ==================== Reset ====================

  describe('Reset', () => {
    it('RANK_EVAL_029: reset clears all state', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.items.value = [{ thread_id: 1 }]
      ranking.currentItem.value = { thread_id: 1 }
      ranking.selectedBucket.value = 'good'
      ranking.notes.value = 'some notes'
      ranking.error.value = 'some error'

      ranking.reset()

      expect(ranking.items.value).toHaveLength(0)
      expect(ranking.currentItem.value).toBeNull()
      expect(ranking.currentItemIndex.value).toBe(0)
      expect(ranking.selectedBucket.value).toBeNull()
      expect(ranking.notes.value).toBe('')
      expect(ranking.existingRanking.value).toBeNull()
      expect(ranking.error.value).toBeNull()
    })
  })

  // ==================== Saving State ====================

  describe('Saving State', () => {
    it('RANK_EVAL_030: saving is false initially', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.saving.value).toBe(false)
    })

    it('RANK_EVAL_031: loading is false initially', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.loading.value).toBe(false)
    })

    it('RANK_EVAL_032: loadingItem is false initially', () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      expect(ranking.loadingItem.value).toBe(false)
    })
  })

  // ==================== Thread ID Helper ====================

  describe('Thread ID Resolution', () => {
    it('RANK_EVAL_033: selectBucket resolves thread_id from currentItem', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { thread_id: 42 }
      ranking.items.value = [{ thread_id: 42, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      await ranking.selectBucket('good')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/42/evaluate',
        expect.anything()
      )
    })

    it('RANK_EVAL_034: selectBucket resolves id fallback', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { id: 99 }
      ranking.items.value = [{ id: 99, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      await ranking.selectBucket('moderate')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/99/evaluate',
        expect.anything()
      )
    })

    it('RANK_EVAL_035: selectBucket resolves item_id fallback', async () => {
      const scenarioId = ref(1)
      const ranking = useRankingEvaluation(scenarioId)

      ranking.currentItem.value = { item_id: 77 }
      ranking.items.value = [{ item_id: 77, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      await ranking.selectBucket('bad')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/77/evaluate',
        expect.anything()
      )
    })
  })
})
