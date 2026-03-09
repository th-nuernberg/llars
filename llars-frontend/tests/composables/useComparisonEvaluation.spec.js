/**
 * useComparisonEvaluation Composable Tests
 *
 * Tests for the A/B comparison evaluation composable.
 * Test IDs: COMP_EVAL_001 - COMP_EVAL_030
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

let useComparisonEvaluation

describe('useComparisonEvaluation Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    vi.useFakeTimers()

    const module = await import('@/composables/useComparisonEvaluation')
    useComparisonEvaluation = module.useComparisonEvaluation
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('COMP_EVAL_001: exports useComparisonEvaluation function', () => {
      expect(typeof useComparisonEvaluation).toBe('function')
    })

    it('COMP_EVAL_002: returns all expected properties', () => {
      const scenarioId = ref(1)
      const result = useComparisonEvaluation(scenarioId)

      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('currentItem')
      expect(result).toHaveProperty('currentItemIndex')
      expect(result).toHaveProperty('optionA')
      expect(result).toHaveProperty('optionB')
      expect(result).toHaveProperty('config')
      expect(result).toHaveProperty('selectedOption')
      expect(result).toHaveProperty('notes')
      expect(result).toHaveProperty('existingComparison')
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
      expect(result).toHaveProperty('selectOption')
      expect(result).toHaveProperty('saveMetadata')
      expect(result).toHaveProperty('goToItem')
      expect(result).toHaveProperty('goNext')
      expect(result).toHaveProperty('goPrev')
      expect(result).toHaveProperty('reset')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('COMP_EVAL_003: selectedOption is null initially', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.selectedOption.value).toBeNull()
    })

    it('COMP_EVAL_004: optionA has default structure', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.optionA.value).toEqual({ messages: [], content: '' })
    })

    it('COMP_EVAL_005: optionB has default structure', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.optionB.value).toEqual({ messages: [], content: '' })
    })

    it('COMP_EVAL_006: items is empty initially', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.items.value).toEqual([])
    })

    it('COMP_EVAL_007: notes is empty initially', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.notes.value).toBe('')
    })
  })

  // ==================== Winner Selection ====================

  describe('Winner Selection', () => {
    it('COMP_EVAL_008: selectOption A saves to API', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10, thread_id: 10 }
      comp.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      const result = await comp.selectOption('A')

      expect(result.success).toBe(true)
      expect(result.choice).toBe('A')
      expect(axios.post).toHaveBeenCalledWith(
        '/api/evaluation/session/1/items/10/evaluate',
        expect.objectContaining({
          function_type: 'comparison',
          choice: 'A'
        })
      )
    })

    it('COMP_EVAL_009: selectOption B saves correctly', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10 }
      comp.items.value = [{ item_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      const result = await comp.selectOption('B')

      expect(result.success).toBe(true)
      expect(result.choice).toBe('B')
    })

    it('COMP_EVAL_010: selectOption tie saves correctly', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10 }
      comp.items.value = [{ item_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      const result = await comp.selectOption('tie')

      expect(result.success).toBe(true)
      expect(result.choice).toBe('tie')
    })

    it('COMP_EVAL_011: selectOption updates local state', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10 }
      comp.items.value = [{ item_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({ data: {} })

      await comp.selectOption('A')

      expect(comp.selectedOption.value).toBe('A')
      expect(comp.items.value[0].evaluated).toBe(true)
    })

    it('COMP_EVAL_012: selectOption returns error when no item', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      const result = await comp.selectOption('A')

      expect(result.success).toBe(false)
      expect(result.error).toBe('No item selected')
    })

    it('COMP_EVAL_013: selectOption handles API error', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10 }
      comp.items.value = [{ item_id: 10, evaluated: false }]

      axios.post.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      const result = await comp.selectOption('A')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Server error')
      expect(comp.error.value).toBe('Server error')
    })

    it('COMP_EVAL_014: selectOption includes notes', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 10 }
      comp.items.value = [{ item_id: 10, evaluated: false }]
      comp.notes.value = 'A is more coherent'

      axios.post.mockResolvedValue({ data: {} })

      await comp.selectOption('A')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          notes: 'A is more coherent'
        })
      )
    })
  })

  // ==================== Current Item Status ====================

  describe('Current Item Status', () => {
    it('COMP_EVAL_015: currentItemStatus is pending when no item', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.currentItemStatus.value).toBe('pending')
    })

    it('COMP_EVAL_016: currentItemStatus is done when option selected', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 1, evaluated: false }
      comp.selectedOption.value = 'A'

      expect(comp.currentItemStatus.value).toBe('done')
    })

    it('COMP_EVAL_017: currentItemStatus is done when item evaluated', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 1, evaluated: true }

      expect(comp.currentItemStatus.value).toBe('done')
    })

    it('COMP_EVAL_018: currentItemStatus is in_progress with notes only', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 1, evaluated: false }
      comp.notes.value = 'Some thoughts'

      expect(comp.currentItemStatus.value).toBe('in_progress')
    })

    it('COMP_EVAL_019: currentItemStatus is pending with no interaction', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.currentItem.value = { item_id: 1, evaluated: false }

      expect(comp.currentItemStatus.value).toBe('pending')
    })
  })

  // ==================== Progress ====================

  describe('Comparison Progress', () => {
    it('COMP_EVAL_020: progress tracks completion', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [
        { item_id: 1, evaluated: true },
        { item_id: 2, evaluated: false },
        { item_id: 3, evaluated: false, status: 'Progressing' },
        { item_id: 4, evaluated: true }
      ]

      expect(comp.progress.value.total).toBe(4)
      expect(comp.progress.value.completed).toBe(2)
      expect(comp.progress.value.inProgress).toBe(1)
      expect(comp.progress.value.notStarted).toBe(1)
      expect(comp.progress.value.percent).toBe(50)
    })

    it('COMP_EVAL_021: progress is 0 when empty', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      expect(comp.progress.value.percent).toBe(0)
    })
  })

  // ==================== Load Items ====================

  describe('Load Items', () => {
    it('COMP_EVAL_022: loadItems calls session endpoint', async () => {
      const scenarioId = ref(42)
      const comp = useComparisonEvaluation(scenarioId)

      axios.get.mockResolvedValue({
        data: { items: [], config: {} }
      })

      await comp.loadItems()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/session/42')
    })

    it('COMP_EVAL_023: loadItems populates items and config', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      const mockItems = [{ thread_id: 1 }, { thread_id: 2 }]
      const mockConfig = { type: 'pairwise' }

      axios.get.mockResolvedValue({
        data: { items: mockItems, config: mockConfig }
      })

      await comp.loadItems()

      expect(comp.items.value).toHaveLength(2)
      expect(comp.config.value).toEqual(mockConfig)
    })

    it('COMP_EVAL_024: loadItems sets error on failure', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      await comp.loadItems()

      expect(comp.error.value).toBe('Not found')
      expect(comp.loading.value).toBe(false)
    })
  })

  // ==================== Load Item with Options ====================

  describe('Load Item', () => {
    it('COMP_EVAL_025: loadItem populates options from features', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          features: [
            { content: 'Option A content', model_name: 'GPT-4' },
            { content: 'Option B content', model_name: 'Claude' }
          ],
          subject: 'Test comparison'
        }
      })

      await comp.loadItem(5)

      expect(comp.optionA.value.content).toBe('Option A content')
      expect(comp.optionA.value.model).toBe('GPT-4')
      expect(comp.optionB.value.content).toBe('Option B content')
      expect(comp.optionB.value.model).toBe('Claude')
    })

    it('COMP_EVAL_026: loadItem uses cache on second call', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          features: [
            { content: 'A', model_name: 'M1' },
            { content: 'B', model_name: 'M2' }
          ],
          subject: 'Test'
        }
      })

      await comp.loadItem(5)

      // Reset get mock to verify cache hit
      axios.get.mockClear()

      await comp.loadItem(5)

      // Should NOT call API again (cache hit)
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('COMP_EVAL_027: loadItem handles fallback with single feature', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          features: [{ content: 'Only one' }],
          messages: [{ sender: 'user', text: 'hello' }]
        }
      })

      await comp.loadItem(5)

      // Fallback: messages go to optionA
      expect(comp.optionA.value.messages).toHaveLength(1)
    })

    it('COMP_EVAL_028: loadItem resets selection state', async () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ thread_id: 5 }]
      comp.selectedOption.value = 'A'
      comp.notes.value = 'old notes'

      axios.get.mockResolvedValue({
        data: {
          features: [
            { content: 'A' },
            { content: 'B' }
          ]
        }
      })

      await comp.loadItem(5)

      expect(comp.selectedOption.value).toBeNull()
      expect(comp.notes.value).toBe('')
    })
  })

  // ==================== Navigation ====================

  describe('Navigation', () => {
    it('COMP_EVAL_029: hasNext and hasPrev work correctly', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ item_id: 1 }, { item_id: 2 }, { item_id: 3 }]
      comp.currentItemIndex.value = 1

      expect(comp.hasNext.value).toBe(true)
      expect(comp.hasPrev.value).toBe(true)
    })
  })

  // ==================== Reset ====================

  describe('Reset', () => {
    it('COMP_EVAL_030: reset clears all state', () => {
      const scenarioId = ref(1)
      const comp = useComparisonEvaluation(scenarioId)

      comp.items.value = [{ item_id: 1 }]
      comp.currentItem.value = { item_id: 1 }
      comp.selectedOption.value = 'B'
      comp.notes.value = 'notes'
      comp.error.value = 'error'
      comp.optionA.value = { messages: [], content: 'text' }

      comp.reset()

      expect(comp.items.value).toHaveLength(0)
      expect(comp.currentItem.value).toBeNull()
      expect(comp.selectedOption.value).toBeNull()
      expect(comp.notes.value).toBe('')
      expect(comp.error.value).toBeNull()
      expect(comp.optionA.value).toEqual({ messages: [], content: '' })
      expect(comp.optionB.value).toEqual({ messages: [], content: '' })
    })
  })
})
