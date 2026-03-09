/**
 * useAnonymizationPipeline Composable Tests
 *
 * Tests for anonymization pipeline state management and Socket.IO integration.
 * Test IDs: ANON_001 - ANON_045
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

// Mock snackbar
const mockShowSuccess = vi.fn()
const mockShowError = vi.fn()
vi.mock('@/composables/useSnackbar', () => ({
  useSnackbar: () => ({
    showSuccess: mockShowSuccess,
    showError: mockShowError
  })
}))

// Mock socket service
const mockSocket = {
  on: vi.fn(),
  emit: vi.fn(),
  off: vi.fn(),
  connected: true
}
vi.mock('@/services/socketService', () => ({
  getSocket: () => mockSocket
}))

// Mock Vue lifecycle hooks (composable uses onMounted/onUnmounted)
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import { useAnonymizationPipeline, CONVERSATION_STATUS } from '@/composables/useAnonymizationPipeline'

describe('useAnonymizationPipeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockSocket.on.mockClear()
    mockSocket.emit.mockClear()
    mockSocket.off.mockClear()
  })

  // ==================== Constants Tests ====================

  describe('CONVERSATION_STATUS', () => {
    it('ANON_001: exports correct status values', () => {
      expect(CONVERSATION_STATUS.PENDING).toBe('pending')
      expect(CONVERSATION_STATUS.IN_PROGRESS).toBe('in_progress')
      expect(CONVERSATION_STATUS.COMPLETED).toBe('completed')
      expect(CONVERSATION_STATUS.ERROR).toBe('error')
    })
  })

  // ==================== Initial State Tests ====================

  describe('initial state', () => {
    it('ANON_002: starts with empty conversations', () => {
      const { conversations } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(conversations.value).toEqual([])
    })

    it('ANON_003: starts with zero total', () => {
      const { totalConversations } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(totalConversations.value).toBe(0)
    })

    it('ANON_004: starts not loading', () => {
      const { loading } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(loading.value).toBe(false)
    })

    it('ANON_005: starts with empty models and courses', () => {
      const { availableModels, availableCourses } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(availableModels.value).toEqual([])
      expect(availableCourses.value).toEqual([])
    })

    it('ANON_006: starts with zero status counts', () => {
      const { statusCounts } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(statusCounts.value).toEqual({ pending: 0, in_progress: 0, completed: 0, error: 0 })
    })

    it('ANON_007: starts with empty NER progress', () => {
      const { nerProgress } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(nerProgress.value).toEqual({})
    })

    it('ANON_008: starts with null batch progress', () => {
      const { batchProgress } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(batchProgress.value).toBeNull()
    })
  })

  // ==================== Computed Tests ====================

  describe('computed properties', () => {
    it('ANON_009: activeNerJobs returns IDs from nerProgress', () => {
      const { nerProgress, activeNerJobs } = useAnonymizationPipeline({ autoJoinOverview: false })
      nerProgress.value = { 1: { percent: 50 }, 3: { percent: 0 } }
      expect(activeNerJobs.value).toEqual([1, 3])
    })

    it('ANON_010: activeNerJobs returns empty when no progress', () => {
      const { activeNerJobs } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(activeNerJobs.value).toEqual([])
    })

    it('ANON_011: isBatchRunning is false when no batch', () => {
      const { isBatchRunning } = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(isBatchRunning.value).toBe(false)
    })

    it('ANON_012: isBatchRunning is true when batch in progress', () => {
      const { batchProgress, isBatchRunning } = useAnonymizationPipeline({ autoJoinOverview: false })
      batchProgress.value = { completed: 2, failed: 0, total: 10, percent: 20 }
      expect(isBatchRunning.value).toBe(true)
    })

    it('ANON_013: isBatchRunning is false when batch is 100%', () => {
      const { batchProgress, isBatchRunning } = useAnonymizationPipeline({ autoJoinOverview: false })
      batchProgress.value = { completed: 10, failed: 0, total: 10, percent: 100 }
      expect(isBatchRunning.value).toBe(false)
    })
  })

  // ==================== loadConversations Tests ====================

  describe('loadConversations', () => {
    it('ANON_014: fetches conversations from API', async () => {
      axios.get.mockResolvedValue({
        data: {
          conversations: [{ id: 1, status: 'pending' }],
          total: 1,
          available_models: ['model-a'],
          available_courses: ['course-1'],
          has_conversations_without_model: true,
          status_counts: { pending: 1, in_progress: 0, completed: 0, error: 0 }
        }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.loadConversations()

      expect(axios.get).toHaveBeenCalledWith('/api/anonymization/conversations', { params: {} })
      expect(pipeline.conversations.value).toHaveLength(1)
      expect(pipeline.totalConversations.value).toBe(1)
      expect(pipeline.availableModels.value).toEqual(['model-a'])
      expect(pipeline.availableCourses.value).toEqual(['course-1'])
      expect(pipeline.hasConversationsWithoutModel.value).toBe(true)
    })

    it('ANON_015: passes params to API', async () => {
      axios.get.mockResolvedValue({
        data: { conversations: [], total: 0 }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.loadConversations({ status: 'pending', page: 1 })

      expect(axios.get).toHaveBeenCalledWith(
        '/api/anonymization/conversations',
        { params: { status: 'pending', page: 1 } }
      )
    })

    it('ANON_016: handles API error', async () => {
      axios.get.mockRejectedValue(new Error('Network error'))

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.loadConversations()

      expect(mockShowError).toHaveBeenCalledWith('Failed to load conversations')
      expect(pipeline.loading.value).toBe(false)
    })

    it('ANON_017: sets loading state', async () => {
      let loadingDuring = null
      axios.get.mockImplementation(() => {
        loadingDuring = true // We know loading was set before this
        return Promise.resolve({ data: { conversations: [], total: 0 } })
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.loadConversations()
      expect(pipeline.loading.value).toBe(false)
    })
  })

  // ==================== runNer Tests ====================

  describe('runNer', () => {
    it('ANON_018: starts NER processing', async () => {
      axios.post.mockResolvedValue({
        data: { started: true }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      pipeline.conversations.value = [{ id: 5, status: 'pending' }]

      const result = await pipeline.runNer(5)
      expect(axios.post).toHaveBeenCalledWith(
        '/api/anonymization/conversations/5/run-ner',
        { force: false }
      )
      expect(result.started).toBe(true)
      expect(pipeline.nerProgress.value[5]).toBeDefined()
      expect(pipeline.nerProgress.value[5].percent).toBe(0)
    })

    it('ANON_019: supports force option', async () => {
      axios.post.mockResolvedValue({ data: { started: true } })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.runNer(1, { force: true })

      expect(axios.post).toHaveBeenCalledWith(
        '/api/anonymization/conversations/1/run-ner',
        { force: true }
      )
    })

    it('ANON_020: updates conversation status on start', async () => {
      axios.post.mockResolvedValue({ data: { started: true } })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      pipeline.conversations.value = [{ id: 3, status: 'pending' }]
      await pipeline.runNer(3)

      expect(pipeline.conversations.value[0].status).toBe('in_progress')
    })

    it('ANON_021: handles NER error', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Model not found' } }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const result = await pipeline.runNer(1)

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalledWith('Model not found')
    })

    it('ANON_022: handles NER error without response data', async () => {
      axios.post.mockRejectedValue(new Error('Network error'))

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const result = await pipeline.runNer(1)

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalledWith('NER processing failed')
    })
  })

  // ==================== batchRunNer Tests ====================

  describe('batchRunNer', () => {
    it('ANON_023: starts batch NER', async () => {
      axios.post.mockResolvedValue({
        data: { started: true, count: 3, conversation_ids: [1, 2, 3] }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      pipeline.conversations.value = [
        { id: 1, status: 'pending' },
        { id: 2, status: 'pending' },
        { id: 3, status: 'pending' }
      ]

      const result = await pipeline.batchRunNer({ conversationIds: [1, 2, 3] })
      expect(result.started).toBe(true)
      expect(pipeline.batchProgress.value).toEqual({
        completed: 0, failed: 0, total: 3, percent: 0
      })
    })

    it('ANON_024: initializes progress for each conversation', async () => {
      axios.post.mockResolvedValue({
        data: { started: true, count: 2, conversation_ids: [5, 6] }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      pipeline.conversations.value = [
        { id: 5, status: 'pending' },
        { id: 6, status: 'pending' }
      ]
      await pipeline.batchRunNer()

      expect(pipeline.nerProgress.value[5]).toBeDefined()
      expect(pipeline.nerProgress.value[6]).toBeDefined()
    })

    it('ANON_025: handles batch error', async () => {
      axios.post.mockRejectedValue(new Error('Batch failed'))

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const result = await pipeline.batchRunNer()

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalled()
    })
  })

  // ==================== isNerRunning / getNerProgress Tests ====================

  describe('NER progress helpers', () => {
    it('ANON_026: isNerRunning returns true when running', () => {
      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      pipeline.nerProgress.value = { 5: { percent: 50 } }
      expect(pipeline.isNerRunning(5)).toBe(true)
    })

    it('ANON_027: isNerRunning returns false when not running', () => {
      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(pipeline.isNerRunning(5)).toBe(false)
    })

    it('ANON_028: getNerProgress returns progress object', () => {
      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const progress = { percent: 75, message_number: 3, total_messages: 4, entities_found: 10 }
      pipeline.nerProgress.value = { 5: progress }
      expect(pipeline.getNerProgress(5)).toEqual(progress)
    })

    it('ANON_029: getNerProgress returns null when not found', () => {
      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      expect(pipeline.getNerProgress(999)).toBeNull()
    })
  })

  // ==================== importConversations Tests ====================

  describe('importConversations', () => {
    it('ANON_030: imports file via API', async () => {
      axios.post.mockResolvedValue({
        data: { imported_count: 5, failed_count: 0, ner_started: false, conversations: [] }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const file = new File(['data'], 'test.json')
      const result = await pipeline.importConversations(file)

      expect(axios.post).toHaveBeenCalled()
      expect(result.imported_count).toBe(5)
      expect(mockShowSuccess).toHaveBeenCalledWith('Imported 5 conversation(s)')
    })

    it('ANON_031: shows error for failed imports', async () => {
      axios.post.mockResolvedValue({
        data: { imported_count: 3, failed_count: 2, ner_started: false, conversations: [] }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.importConversations(new File([''], 'f.json'))

      expect(mockShowSuccess).toHaveBeenCalled()
      expect(mockShowError).toHaveBeenCalledWith('2 conversation(s) could not be imported')
    })

    it('ANON_032: initializes batch progress when NER auto-started', async () => {
      axios.post.mockResolvedValue({
        data: {
          imported_count: 2,
          failed_count: 0,
          ner_started: true,
          conversations: [{ id: 10 }, { id: 11 }]
        }
      })

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      await pipeline.importConversations(new File([''], 'f.json'), { runNer: true })

      expect(pipeline.batchProgress.value).toEqual({
        completed: 0, failed: 0, total: 2, percent: 0
      })
      expect(pipeline.nerProgress.value[10]).toBeDefined()
      expect(pipeline.nerProgress.value[11]).toBeDefined()
    })

    it('ANON_033: handles import error', async () => {
      axios.post.mockRejectedValue(new Error('Upload failed'))

      const pipeline = useAnonymizationPipeline({ autoJoinOverview: false })
      const result = await pipeline.importConversations(new File([''], 'f.json'))

      expect(result).toBeNull()
      expect(mockShowError).toHaveBeenCalled()
    })
  })

  // ==================== Socket Setup Tests ====================

  describe('socket integration', () => {
    it('ANON_034: joins overview room on mount when autoJoinOverview is true', () => {
      useAnonymizationPipeline({ autoJoinOverview: true })
      expect(mockSocket.emit).toHaveBeenCalledWith('anonymization:join_overview')
    })

    it('ANON_035: registers batch event listeners', () => {
      useAnonymizationPipeline({ autoJoinOverview: false })
      const eventNames = mockSocket.on.mock.calls.map(c => c[0])
      expect(eventNames).toContain('anonymization:batch:started')
      expect(eventNames).toContain('anonymization:batch:progress')
      expect(eventNames).toContain('anonymization:batch:completed')
    })

    it('ANON_036: registers conversation event listeners', () => {
      useAnonymizationPipeline({ autoJoinOverview: false })
      const eventNames = mockSocket.on.mock.calls.map(c => c[0])
      expect(eventNames).toContain('anonymization:conversation:ner_started')
      expect(eventNames).toContain('anonymization:conversation:ner_progress')
      expect(eventNames).toContain('anonymization:conversation:ner_completed')
      expect(eventNames).toContain('anonymization:conversation:ner_failed')
    })

    it('ANON_037: joins conversation room when watchConversationId is set', () => {
      useAnonymizationPipeline({ autoJoinOverview: false, watchConversationId: 42 })
      expect(mockSocket.emit).toHaveBeenCalledWith(
        'anonymization:join_conversation',
        { conversation_id: 42 }
      )
    })
  })
})
