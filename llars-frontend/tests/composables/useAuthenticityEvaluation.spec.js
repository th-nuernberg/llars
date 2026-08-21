/**
 * useAuthenticityEvaluation Composable Tests
 *
 * Tests for the fake/real authenticity evaluation composable.
 * Test IDs: AUTH_EVAL_001 - AUTH_EVAL_035
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn()
  }
}))

import axios from 'axios'

let useAuthenticityEvaluation

describe('useAuthenticityEvaluation Composable', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    vi.useFakeTimers()

    const module = await import('@/composables/useAuthenticityEvaluation')
    useAuthenticityEvaluation = module.useAuthenticityEvaluation
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('AUTH_EVAL_001: exports useAuthenticityEvaluation function', () => {
      expect(typeof useAuthenticityEvaluation).toBe('function')
    })

    it('AUTH_EVAL_002: returns all expected properties', () => {
      const scenarioId = ref(1)
      const result = useAuthenticityEvaluation(scenarioId)

      expect(result).toHaveProperty('items')
      expect(result).toHaveProperty('currentItem')
      expect(result).toHaveProperty('currentItemIndex')
      expect(result).toHaveProperty('messages')
      expect(result).toHaveProperty('content')
      expect(result).toHaveProperty('config')
      expect(result).toHaveProperty('vote')
      expect(result).toHaveProperty('confidence')
      expect(result).toHaveProperty('notes')
      expect(result).toHaveProperty('existingVote')
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
      expect(result).toHaveProperty('submitVote')
      expect(result).toHaveProperty('saveMetadata')
      expect(result).toHaveProperty('goToItem')
      expect(result).toHaveProperty('goNext')
      expect(result).toHaveProperty('goPrev')
      expect(result).toHaveProperty('reset')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('AUTH_EVAL_003: vote is null initially', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.vote.value).toBeNull()
    })

    it('AUTH_EVAL_004: confidence defaults to 50', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.confidence.value).toBe(50)
    })

    it('AUTH_EVAL_005: notes is empty initially', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.notes.value).toBe('')
    })

    it('AUTH_EVAL_006: existingVote is null initially', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.existingVote.value).toBeNull()
    })
  })

  // ==================== Submit Vote ====================

  describe('Submit Vote', () => {
    it('AUTH_EVAL_007: submitVote real calls correct endpoint', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({
        data: { vote: { vote: 'real', confidence: 50 } }
      })

      const result = await auth.submitVote('real')

      expect(result.success).toBe(true)
      expect(axios.post).toHaveBeenCalledWith(
        '/api/email_threads/authenticity/10/vote',
        expect.objectContaining({
          vote: 'real',
          confidence: 50
        })
      )
    })

    it('AUTH_EVAL_008: submitVote fake calls correct endpoint', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockResolvedValue({
        data: { vote: { vote: 'fake', confidence: 80 } }
      })

      auth.confidence.value = 80

      const result = await auth.submitVote('fake')

      expect(result.success).toBe(true)
      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          vote: 'fake',
          confidence: 80
        })
      )
    })

    it('AUTH_EVAL_009: submitVote updates local state', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false, voted: false }]

      axios.post.mockResolvedValue({
        data: { vote: { vote: 'real' } }
      })

      await auth.submitVote('real')

      expect(auth.vote.value).toBe('real')
      expect(auth.items.value[0].voted).toBe(true)
      expect(auth.items.value[0].evaluated).toBe(true)
      expect(auth.items.value[0].vote).toBe('real')
    })

    it('AUTH_EVAL_010: submitVote returns error when no item', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      const result = await auth.submitVote('real')

      expect(result.success).toBe(false)
      expect(result.error).toBe('No item selected')
    })

    it('AUTH_EVAL_011: submitVote handles API error', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false }]

      axios.post.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      const result = await auth.submitVote('fake')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Server error')
      expect(auth.error.value).toBe('Server error')
    })

    it('AUTH_EVAL_012: submitVote includes notes', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false }]
      auth.notes.value = 'Seems AI generated'

      axios.post.mockResolvedValue({
        data: { vote: { vote: 'fake' } }
      })

      await auth.submitVote('fake')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          notes: 'Seems AI generated'
        })
      )
    })

    it('AUTH_EVAL_013: submitVote includes confidence value', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.items.value = [{ thread_id: 10, evaluated: false }]
      auth.confidence.value = 90

      axios.post.mockResolvedValue({
        data: { vote: { vote: 'real' } }
      })

      await auth.submitVote('real')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          confidence: 90
        })
      )
    })
  })

  // ==================== Current Item Status ====================

  describe('Current Item Status', () => {
    it('AUTH_EVAL_014: currentItemStatus is pending when no item', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.currentItemStatus.value).toBe('pending')
    })

    it('AUTH_EVAL_015: currentItemStatus is done when voted', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, evaluated: false }
      auth.vote.value = 'real'

      expect(auth.currentItemStatus.value).toBe('done')
    })

    it('AUTH_EVAL_016: currentItemStatus is done when item has voted flag', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, voted: true }

      expect(auth.currentItemStatus.value).toBe('done')
    })

    it('AUTH_EVAL_017: currentItemStatus is done when item is evaluated', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, evaluated: true }

      expect(auth.currentItemStatus.value).toBe('done')
    })

    it('AUTH_EVAL_018: currentItemStatus is in_progress when confidence changed', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, evaluated: false }
      auth.confidence.value = 75 // Changed from default 50

      expect(auth.currentItemStatus.value).toBe('in_progress')
    })

    it('AUTH_EVAL_019: currentItemStatus is in_progress when notes added', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, evaluated: false }
      auth.notes.value = 'Some notes'

      expect(auth.currentItemStatus.value).toBe('in_progress')
    })

    it('AUTH_EVAL_020: currentItemStatus is pending with default confidence', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 1, evaluated: false }

      expect(auth.currentItemStatus.value).toBe('pending')
    })
  })

  // ==================== Progress ====================

  describe('Progress', () => {
    it('AUTH_EVAL_021: progress tracks voted items', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [
        { thread_id: 1, voted: true },
        { thread_id: 2, evaluated: true },
        { thread_id: 3, voted: false, evaluated: false, status: 'Progressing' },
        { thread_id: 4, voted: false, evaluated: false }
      ]

      expect(auth.progress.value.total).toBe(4)
      expect(auth.progress.value.completed).toBe(2)
      expect(auth.progress.value.inProgress).toBe(1)
      expect(auth.progress.value.notStarted).toBe(1)
      expect(auth.progress.value.percent).toBe(50)
    })

    it('AUTH_EVAL_022: progress is 0 when empty', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.progress.value.percent).toBe(0)
    })
  })

  // ==================== Load Items ====================

  describe('Load Items', () => {
    it('AUTH_EVAL_023: loadItems calls session endpoint', async () => {
      const scenarioId = ref(42)
      const auth = useAuthenticityEvaluation(scenarioId)

      axios.get.mockResolvedValue({
        data: { items: [], config: {} }
      })

      await auth.loadItems()

      expect(axios.get).toHaveBeenCalledWith('/api/evaluation/session/42')
    })

    it('AUTH_EVAL_024: loadItems populates items and config', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      axios.get.mockResolvedValue({
        data: {
          items: [{ thread_id: 1 }, { thread_id: 2 }],
          config: { type: 'authenticity' }
        }
      })

      await auth.loadItems()

      expect(auth.items.value).toHaveLength(2)
      expect(auth.config.value).toEqual({ type: 'authenticity' })
    })

    it('AUTH_EVAL_025: loadItems sets error on failure', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { error: 'Not found' } }
      })

      await auth.loadItems()

      expect(auth.error.value).toBe('Not found')
      expect(auth.loading.value).toBe(false)
    })
  })

  // ==================== Load Item ====================

  describe('Load Item', () => {
    it('AUTH_EVAL_026: loadItem calls authenticity endpoint', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          thread_id: 5,
          subject: 'Test',
          sender: 'user@test.com',
          messages: [{ text: 'hello' }],
          vote: null
        }
      })

      await auth.loadItem(5)

      expect(axios.get).toHaveBeenCalledWith('/api/email_threads/authenticity/5')
      expect(auth.currentItem.value.thread_id).toBe(5)
      expect(auth.currentItem.value.subject).toBe('Test')
      expect(auth.currentItem.value.sender).toBe('user@test.com')
      expect(auth.messages.value).toHaveLength(1)
    })

    it('AUTH_EVAL_027: loadItem restores existing vote', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          thread_id: 5,
          subject: 'Test',
          sender: 'user@test.com',
          messages: [],
          vote: {
            vote: 'fake',
            confidence: 85,
            notes: 'Clearly AI generated'
          }
        }
      })

      await auth.loadItem(5)

      expect(auth.vote.value).toBe('fake')
      expect(auth.confidence.value).toBe(85)
      expect(auth.notes.value).toBe('Clearly AI generated')
    })

    it('AUTH_EVAL_028: loadItem resets state when no existing vote', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 5 }]
      auth.vote.value = 'real'
      auth.confidence.value = 90
      auth.notes.value = 'old notes'

      axios.get.mockResolvedValue({
        data: {
          thread_id: 5,
          subject: 'Test',
          sender: 'user@test.com',
          messages: [],
          vote: null
        }
      })

      await auth.loadItem(5)

      expect(auth.vote.value).toBeNull()
      expect(auth.confidence.value).toBe(50)
      expect(auth.notes.value).toBe('')
    })

    it('AUTH_EVAL_029: loadItem uses cache on second call', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 5 }]

      axios.get.mockResolvedValue({
        data: {
          thread_id: 5,
          subject: 'Test',
          sender: 'user@test.com',
          messages: [],
          vote: null
        }
      })

      await auth.loadItem(5)

      axios.get.mockClear()

      await auth.loadItem(5)

      // Should NOT call API again (cache hit)
      expect(axios.get).not.toHaveBeenCalled()
    })

    it('AUTH_EVAL_030: loadItem handles API error', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      axios.get.mockRejectedValue({
        response: { data: { error: 'Thread not found' } }
      })

      await auth.loadItem(999)

      expect(auth.error.value).toBe('Thread not found')
      expect(auth.loadingItem.value).toBe(false)
    })
  })

  // ==================== Save Metadata ====================

  describe('Save Metadata', () => {
    it('AUTH_EVAL_031: saveMetadata calls patch endpoint', async () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.currentItem.value = { thread_id: 10 }
      auth.confidence.value = 75
      auth.notes.value = 'Updated notes'

      axios.patch.mockResolvedValue({ data: {} })

      auth.saveMetadata()

      // Advance past debounce timer
      vi.advanceTimersByTime(1000)

      await vi.runAllTimersAsync()

      expect(axios.patch).toHaveBeenCalledWith(
        '/api/email_threads/authenticity/10/metadata',
        expect.objectContaining({
          confidence: 75,
          notes: 'Updated notes'
        })
      )
    })
  })

  // ==================== Navigation ====================

  describe('Navigation', () => {
    it('AUTH_EVAL_032: hasNext and hasPrev work correctly', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 1 }, { thread_id: 2 }, { thread_id: 3 }]
      auth.currentItemIndex.value = 1

      expect(auth.hasNext.value).toBe(true)
      expect(auth.hasPrev.value).toBe(true)
    })

    it('AUTH_EVAL_033: hasNext false at last item', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 1 }]
      auth.currentItemIndex.value = 0

      expect(auth.hasNext.value).toBe(false)
    })
  })

  // ==================== Reset ====================

  describe('Reset', () => {
    it('AUTH_EVAL_034: reset clears all state', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      auth.items.value = [{ thread_id: 1 }]
      auth.currentItem.value = { thread_id: 1 }
      auth.vote.value = 'real'
      auth.confidence.value = 80
      auth.notes.value = 'notes'
      auth.error.value = 'error'
      auth.existingVote.value = { vote: 'real' }

      auth.reset()

      expect(auth.items.value).toHaveLength(0)
      expect(auth.currentItem.value).toBeNull()
      expect(auth.vote.value).toBeNull()
      expect(auth.confidence.value).toBe(50)
      expect(auth.notes.value).toBe('')
      expect(auth.existingVote.value).toBeNull()
      expect(auth.error.value).toBeNull()
    })
  })

  // ==================== Saving State ====================

  describe('Saving State', () => {
    it('AUTH_EVAL_035: saving is false initially', () => {
      const scenarioId = ref(1)
      const auth = useAuthenticityEvaluation(scenarioId)

      expect(auth.saving.value).toBe(false)
    })
  })
})
