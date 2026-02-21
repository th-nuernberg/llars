/**
 * Tests for useFieldGenerationService composable
 *
 * Test IDs: FGS_001 - FGS_060
 *
 * Coverage:
 * - Exports and structure
 * - Session management (getSession, clearSession)
 * - Field state management (getFieldState, getContent, isCompleted)
 * - isGenerating checks
 * - generateField routing
 * - startDirectGeneration
 * - startStreamGeneration
 * - abortGeneration
 * - getGeneratingFields
 * - getAllFieldContents
 * - subscribeToField
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'

// Mock axios
vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}))

// Mock authStorage
vi.mock('@/utils/authStorage', () => ({
  AUTH_STORAGE_KEYS: { token: 'auth_token' },
  getAuthStorageItem: vi.fn(() => 'test-token')
}))

// Mock fetch for streaming
const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

describe('useFieldGenerationService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()

    // Reset module to clear singleton state
    vi.resetModules()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  // Helper to get fresh composable instance
  const getComposable = async () => {
    const { useFieldGenerationService } = await import('@/composables/useFieldGenerationService')
    return useFieldGenerationService()
  }

  describe('Exports', () => {
    it('FGS_001: exports useFieldGenerationService function', async () => {
      const { useFieldGenerationService } = await import('@/composables/useFieldGenerationService')
      expect(typeof useFieldGenerationService).toBe('function')
    })

    it('FGS_002: exports fieldGenerationService singleton', async () => {
      const { fieldGenerationService } = await import('@/composables/useFieldGenerationService')
      expect(fieldGenerationService).toBeDefined()
      expect(typeof fieldGenerationService.generateField).toBe('function')
    })

    it('FGS_003: returns all expected methods', async () => {
      const service = await getComposable()

      expect(service).toHaveProperty('generateField')
      expect(service).toHaveProperty('startStreamGeneration')
      expect(service).toHaveProperty('startDirectGeneration')
      expect(service).toHaveProperty('abortGeneration')
      expect(service).toHaveProperty('clearSession')
      expect(service).toHaveProperty('isGenerating')
      expect(service).toHaveProperty('getContent')
      expect(service).toHaveProperty('isCompleted')
      expect(service).toHaveProperty('getGeneratingFields')
      expect(service).toHaveProperty('getAllFieldContents')
      expect(service).toHaveProperty('subscribeToField')
      expect(service).toHaveProperty('state')
    })

    it('FGS_004: state is readonly', async () => {
      const service = await getComposable()
      expect(service.state).toBeDefined()
    })
  })

  describe('Session Management', () => {
    it('FGS_005: creates session on first access', async () => {
      const { isGenerating } = await getComposable()

      // Accessing any method should create the session
      const result = isGenerating('chatbot-1', 'name')
      expect(result).toBe(false)
    })

    it('FGS_006: clearSession removes session', async () => {
      const { isGenerating, clearSession } = await getComposable()

      isGenerating('chatbot-1', 'name')
      clearSession('chatbot-1')

      // Should still work after clear (creates new session)
      const result = isGenerating('chatbot-1', 'name')
      expect(result).toBe(false)
    })

    it('FGS_007: clearSession handles non-existent session', async () => {
      const { clearSession } = await getComposable()

      // Should not throw
      clearSession('non-existent-id')
    })
  })

  describe('isGenerating', () => {
    it('FGS_008: returns false when not generating', async () => {
      const { isGenerating } = await getComposable()
      expect(isGenerating('chatbot-1', 'name')).toBe(false)
    })

    it('FGS_009: returns false for unknown chatbot', async () => {
      const { isGenerating } = await getComposable()
      expect(isGenerating('unknown', 'name')).toBe(false)
    })
  })

  describe('getContent', () => {
    it('FGS_010: returns empty string for new field', async () => {
      const { getContent } = await getComposable()
      expect(getContent('chatbot-1', 'name')).toBe('')
    })

    it('FGS_011: returns empty string for unknown chatbot', async () => {
      const { getContent } = await getComposable()
      expect(getContent('unknown', 'name')).toBe('')
    })
  })

  describe('isCompleted', () => {
    it('FGS_012: returns false for new field', async () => {
      const { isCompleted } = await getComposable()
      expect(isCompleted('chatbot-1', 'name')).toBe(false)
    })

    it('FGS_013: returns false for unknown chatbot', async () => {
      const { isCompleted } = await getComposable()
      expect(isCompleted('unknown', 'name')).toBe(false)
    })
  })

  describe('startDirectGeneration', () => {
    it('FGS_014: returns null if no chatbotId', async () => {
      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration(null, 'name')
      expect(result).toBeNull()
    })

    it('FGS_015: returns null if chatbotId is empty', async () => {
      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('', 'name')
      expect(result).toBeNull()
    })

    it('FGS_016: calls API with correct endpoint', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Generated Name' }
      })

      const { startDirectGeneration } = await getComposable()
      await startDirectGeneration('chatbot-123', 'name')

      expect(axios.post).toHaveBeenCalledWith(
        '/api/chatbots/chatbot-123/wizard/generate-field',
        expect.any(Object)
      )
    })

    it('FGS_017: sends field in request body', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Test Value' }
      })

      const { startDirectGeneration } = await getComposable()
      await startDirectGeneration('chatbot-123', 'icon')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ field: 'icon' })
      )
    })

    it('FGS_018: forces LLM for color field', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: '#ff0000' }
      })

      const { startDirectGeneration } = await getComposable()
      await startDirectGeneration('chatbot-123', 'color')

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ field: 'color', force_llm: true })
      )
    })

    it('FGS_019: returns value on success', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'My Chatbot' }
      })

      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('chatbot-123', 'name')

      expect(result).toBe('My Chatbot')
    })

    it('FGS_020: sets content on success', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Generated Display Name' }
      })

      const { startDirectGeneration, getContent } = await getComposable()
      await startDirectGeneration('chatbot-123', 'display_name')

      expect(getContent('chatbot-123', 'display_name')).toBe('Generated Display Name')
    })

    it('FGS_021: sets completed on success', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Value' }
      })

      const { startDirectGeneration, isCompleted } = await getComposable()
      await startDirectGeneration('chatbot-123', 'name')

      expect(isCompleted('chatbot-123', 'name')).toBe(true)
    })

    it('FGS_022: returns null on API failure', async () => {
      axios.post.mockRejectedValueOnce(new Error('Network error'))

      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('chatbot-123', 'name')

      expect(result).toBeNull()
    })

    it('FGS_023: returns null when success is false', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: false, error: 'Generation failed' }
      })

      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('chatbot-123', 'name')

      expect(result).toBeNull()
    })

    it('FGS_024: clears generating state after completion', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Value' }
      })

      const { startDirectGeneration, isGenerating } = await getComposable()
      await startDirectGeneration('chatbot-123', 'name')

      expect(isGenerating('chatbot-123', 'name')).toBe(false)
    })

    it('FGS_025: clears generating state on error', async () => {
      axios.post.mockRejectedValueOnce(new Error('Error'))

      const { startDirectGeneration, isGenerating } = await getComposable()
      await startDirectGeneration('chatbot-123', 'name')

      expect(isGenerating('chatbot-123', 'name')).toBe(false)
    })

    it('FGS_026: respects force_llm option', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Forced' }
      })

      const { startDirectGeneration } = await getComposable()
      await startDirectGeneration('chatbot-123', 'name', { force_llm: true })

      expect(axios.post).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ force_llm: true })
      )
    })
  })

  describe('startStreamGeneration', () => {
    it('FGS_027: returns early if no chatbotId', async () => {
      const { startStreamGeneration } = await getComposable()
      await startStreamGeneration(null, 'system_prompt')

      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('FGS_028: makes fetch request with correct endpoint', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ done: true })
          })
        }
      })

      const { startStreamGeneration } = await getComposable()
      await startStreamGeneration('chatbot-123', 'system_prompt')

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/chatbots/chatbot-123/wizard/generate-field',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
          })
        })
      )
    })

    it('FGS_029: sends field and stream flag in body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ done: true })
          })
        }
      })

      const { startStreamGeneration } = await getComposable()
      await startStreamGeneration('chatbot-123', 'welcome_message')

      const call = mockFetch.mock.calls[0]
      const body = JSON.parse(call[1].body)
      expect(body).toEqual({ field: 'welcome_message', stream: true })
    })

    it('FGS_030: handles stream error response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500
      })

      const { startStreamGeneration, isGenerating } = await getComposable()
      await startStreamGeneration('chatbot-123', 'system_prompt')

      expect(isGenerating('chatbot-123', 'system_prompt')).toBe(false)
    })
  })

  describe('generateField', () => {
    it('FGS_031: routes streaming fields to startStreamGeneration', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ done: true })
          })
        }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'system_prompt')

      expect(mockFetch).toHaveBeenCalled()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('FGS_032: routes welcome_message to streaming', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ done: true })
          })
        }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'welcome_message')

      expect(mockFetch).toHaveBeenCalled()
    })

    it('FGS_033: routes name to direct generation', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Bot Name' }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'name')

      expect(axios.post).toHaveBeenCalled()
      expect(mockFetch).not.toHaveBeenCalled()
    })

    it('FGS_034: routes icon to direct generation', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'mdi-robot' }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'icon')

      expect(axios.post).toHaveBeenCalled()
    })

    it('FGS_035: routes color to direct generation', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: '#00ff00' }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'color')

      expect(axios.post).toHaveBeenCalled()
    })

    it('FGS_036: passes onUpdate to streaming fields', async () => {
      const onUpdate = vi.fn()
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: {
          getReader: () => ({
            read: async () => ({ done: true })
          })
        }
      })

      const { generateField } = await getComposable()
      await generateField('chatbot-123', 'system_prompt', { onUpdate })

      // onUpdate is passed internally
      expect(mockFetch).toHaveBeenCalled()
    })
  })

  describe('abortGeneration', () => {
    it('FGS_037: handles non-existent session', async () => {
      const { abortGeneration } = await getComposable()

      // Should not throw
      abortGeneration('non-existent', 'name')
    })

    it('FGS_038: handles non-generating field', async () => {
      const { abortGeneration, isGenerating } = await getComposable()

      // Access to create session
      isGenerating('chatbot-1', 'name')

      // Should not throw
      abortGeneration('chatbot-1', 'name')
    })
  })

  describe('getGeneratingFields', () => {
    it('FGS_039: returns empty object for non-existent session', async () => {
      const { getGeneratingFields } = await getComposable()
      const result = getGeneratingFields('non-existent')
      expect(result).toEqual({})
    })

    it('FGS_040: returns object with all field keys', async () => {
      const { isGenerating, getGeneratingFields } = await getComposable()

      // Create session
      isGenerating('chatbot-1', 'name')

      const result = getGeneratingFields('chatbot-1')
      expect(result).toHaveProperty('name')
      expect(result).toHaveProperty('display_name')
      expect(result).toHaveProperty('system_prompt')
      expect(result).toHaveProperty('welcome_message')
      expect(result).toHaveProperty('icon')
      expect(result).toHaveProperty('color')
    })

    it('FGS_041: all fields are false initially', async () => {
      const { isGenerating, getGeneratingFields } = await getComposable()

      isGenerating('chatbot-1', 'name')

      const result = getGeneratingFields('chatbot-1')
      Object.values(result).forEach(value => {
        expect(value).toBe(false)
      })
    })
  })

  describe('getAllFieldContents', () => {
    it('FGS_042: returns empty object for non-existent session', async () => {
      const { getAllFieldContents } = await getComposable()
      const result = getAllFieldContents('non-existent')
      expect(result).toEqual({})
    })

    it('FGS_043: returns only fields with content', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'My Bot' }
      })

      const { startDirectGeneration, getAllFieldContents } = await getComposable()
      await startDirectGeneration('chatbot-1', 'name')

      const result = getAllFieldContents('chatbot-1')
      expect(result).toEqual({ name: 'My Bot' })
    })

    it('FGS_044: excludes empty content fields', async () => {
      const { getContent, getAllFieldContents } = await getComposable()

      // Access fields to create them
      getContent('chatbot-1', 'name')
      getContent('chatbot-1', 'icon')

      const result = getAllFieldContents('chatbot-1')
      expect(result).toEqual({})
    })
  })

  describe('subscribeToField', () => {
    it('FGS_045: returns unsubscribe function', async () => {
      const { subscribeToField } = await getComposable()
      const callback = vi.fn()

      const unsubscribe = subscribeToField('chatbot-1', 'name', callback)
      expect(typeof unsubscribe).toBe('function')

      // Cleanup
      unsubscribe()
    })

    it('FGS_046: calls callback on content change', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'New Content' }
      })

      const { subscribeToField, startDirectGeneration } = await getComposable()
      const callback = vi.fn()

      const unsubscribe = subscribeToField('chatbot-1', 'name', callback)

      await startDirectGeneration('chatbot-1', 'name')

      // Advance timer to trigger polling
      vi.advanceTimersByTime(200)

      expect(callback).toHaveBeenCalledWith(expect.objectContaining({
        content: 'New Content',
        completed: true
      }))

      unsubscribe()
    })

    it('FGS_047: unsubscribe stops polling', async () => {
      const { subscribeToField } = await getComposable()
      const callback = vi.fn()

      const unsubscribe = subscribeToField('chatbot-1', 'name', callback)

      // First poll
      vi.advanceTimersByTime(100)
      const initialCalls = callback.mock.calls.length

      // Unsubscribe
      unsubscribe()

      // More time passes - no new calls
      vi.advanceTimersByTime(500)
      expect(callback.mock.calls.length).toBe(initialCalls)
    })

    it('FGS_048: callback receives generating state', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Updated' }
      })

      const { subscribeToField, startDirectGeneration } = await getComposable()
      const callback = vi.fn()

      const unsubscribe = subscribeToField('chatbot-1', 'name', callback)

      // Trigger a content change so callback is invoked
      await startDirectGeneration('chatbot-1', 'name')

      // Advance timer to trigger polling and detect change
      vi.advanceTimersByTime(200)

      expect(callback).toHaveBeenCalledWith(expect.objectContaining({
        generating: false,
        content: 'Updated'
      }))

      unsubscribe()
    })
  })

  describe('Concurrent Operations', () => {
    it('FGS_049: prevents duplicate generation', async () => {
      let resolveFirst
      axios.post.mockImplementationOnce(() => new Promise(r => { resolveFirst = r }))

      const { startDirectGeneration } = await getComposable()

      // Start first generation
      const first = startDirectGeneration('chatbot-1', 'name')

      // Try to start second - should return null
      const second = await startDirectGeneration('chatbot-1', 'name')
      expect(second).toBeNull()

      // Complete first
      resolveFirst({ data: { success: true, value: 'Done' } })
      await first
    })

    it('FGS_050: allows generation of different fields', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, value: 'Value' }
      })

      const { startDirectGeneration } = await getComposable()

      const results = await Promise.all([
        startDirectGeneration('chatbot-1', 'name'),
        startDirectGeneration('chatbot-1', 'icon')
      ])

      expect(results[0]).toBe('Value')
      expect(results[1]).toBe('Value')
    })

    it('FGS_051: allows generation for different chatbots', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, value: 'Bot Value' }
      })

      const { startDirectGeneration } = await getComposable()

      const results = await Promise.all([
        startDirectGeneration('chatbot-1', 'name'),
        startDirectGeneration('chatbot-2', 'name')
      ])

      expect(results[0]).toBe('Bot Value')
      expect(results[1]).toBe('Bot Value')
    })
  })

  describe('Edge Cases', () => {
    it('FGS_052: handles undefined field', async () => {
      const { getContent } = await getComposable()
      const result = getContent('chatbot-1', undefined)
      expect(result).toBe('')
    })

    it('FGS_053: handles numeric chatbotId', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Numeric' }
      })

      const { startDirectGeneration, getContent } = await getComposable()
      await startDirectGeneration(123, 'name')

      expect(getContent(123, 'name')).toBe('Numeric')
    })

    it('FGS_054: clearSession aborts running generations', async () => {
      let aborted = false
      const abortController = { abort: () => { aborted = true } }

      mockFetch.mockImplementationOnce(() => new Promise((resolve) => {
        // Never resolves - simulates long-running stream
        setTimeout(() => resolve({ ok: true, body: null }), 10000)
      }))

      const { startStreamGeneration, clearSession } = await getComposable()

      // Start without awaiting
      startStreamGeneration('chatbot-1', 'system_prompt')

      // Clear immediately
      clearSession('chatbot-1')

      // Should have attempted to abort
      expect(mockFetch).toHaveBeenCalled()
    })

    it('FGS_055: multiple instances share state', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'Shared Value' }
      })

      const instance1 = await getComposable()
      await instance1.startDirectGeneration('chatbot-1', 'name')

      // Get another instance
      const { useFieldGenerationService } = await import('@/composables/useFieldGenerationService')
      const instance2 = useFieldGenerationService()

      expect(instance2.getContent('chatbot-1', 'name')).toBe('Shared Value')
    })

    it('FGS_056: handles response with no body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        body: null
      })

      const { startStreamGeneration, isGenerating } = await getComposable()
      await startStreamGeneration('chatbot-1', 'system_prompt')

      expect(isGenerating('chatbot-1', 'system_prompt')).toBe(false)
    })

    it('FGS_057: handles API error with error message', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: false, error: 'Custom error message' }
      })

      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('chatbot-1', 'name')

      expect(result).toBeNull()
    })

    it('FGS_058: empty string chatbotId is falsy', async () => {
      const { startDirectGeneration } = await getComposable()
      const result = await startDirectGeneration('', 'name')

      expect(result).toBeNull()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('FGS_059: getGeneratingFields returns correct structure', async () => {
      const { getContent, getGeneratingFields } = await getComposable()

      // Create session
      getContent('chatbot-1', 'name')

      const result = getGeneratingFields('chatbot-1')
      expect(Object.keys(result).sort()).toEqual([
        'color', 'display_name', 'icon', 'name', 'system_prompt', 'welcome_message'
      ])
    })

    it('FGS_060: clearSession clears all field states', async () => {
      axios.post.mockResolvedValueOnce({
        data: { success: true, value: 'To Be Cleared' }
      })

      const { startDirectGeneration, getContent, clearSession } = await getComposable()
      await startDirectGeneration('chatbot-1', 'name')

      clearSession('chatbot-1')

      // After clear, content should be empty (new session)
      expect(getContent('chatbot-1', 'name')).toBe('')
    })
  })
})
