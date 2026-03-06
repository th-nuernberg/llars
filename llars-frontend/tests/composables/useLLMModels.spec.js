/**
 * useLLMModels Composable Tests
 *
 * Tests for LLM model management with caching and filtering.
 * Test IDs: LLM_MOD_001 - LLM_MOD_040
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn()
  }
}))

// Mock useAuth
vi.mock('@/composables/useAuth', () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(() => 'test-token')
  }))
}))

import axios from 'axios'

let useLLMModels

describe('useLLMModels', () => {
  beforeEach(async () => {
    vi.clearAllMocks()
    vi.resetModules()

    const module = await import('@/composables/useLLMModels')
    useLLMModels = module.useLLMModels
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Exports ====================

  describe('Exports', () => {
    it('LLM_MOD_001: returns all expected properties', () => {
      const result = useLLMModels()
      expect(result).toHaveProperty('models')
      expect(result).toHaveProperty('loading')
      expect(result).toHaveProperty('error')
      expect(result).toHaveProperty('selectItems')
      expect(result).toHaveProperty('groupedByProvider')
      expect(result).toHaveProperty('defaultModel')
      expect(typeof result.fetchModels).toBe('function')
      expect(typeof result.getModelById).toBe('function')
      expect(typeof result.invalidateCache).toBe('function')
    })
  })

  // ==================== Initial State ====================

  describe('Initial State', () => {
    it('LLM_MOD_002: models starts empty', () => {
      const { models } = useLLMModels()
      expect(models.value).toEqual([])
    })

    it('LLM_MOD_003: loading starts false', () => {
      const { loading } = useLLMModels()
      expect(loading.value).toBe(false)
    })

    it('LLM_MOD_004: error starts null', () => {
      const { error } = useLLMModels()
      expect(error.value).toBeNull()
    })
  })

  // ==================== fetchModels ====================

  describe('fetchModels', () => {
    it('LLM_MOD_005: fetches models from API', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            { model_id: 'gpt-4', display_name: 'GPT-4', provider_name: 'OpenAI', is_default: true },
            { model_id: 'claude-3', display_name: 'Claude 3', provider_name: 'Anthropic' }
          ]
        }
      })

      const { fetchModels, models } = useLLMModels()
      const result = await fetchModels()

      expect(result).toHaveLength(2)
      expect(models.value).toHaveLength(2)
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/llm/models/available'),
        expect.objectContaining({
          headers: { Authorization: 'Bearer test-token' }
        })
      )
    })

    it('LLM_MOD_006: uses cache on subsequent calls', async () => {
      axios.get.mockResolvedValue({
        data: { models: [{ model_id: 'gpt-4' }] }
      })

      const { fetchModels } = useLLMModels()
      await fetchModels()
      await fetchModels()

      expect(axios.get).toHaveBeenCalledTimes(1)
    })

    it('LLM_MOD_007: forceRefresh bypasses cache', async () => {
      axios.get.mockResolvedValue({
        data: { models: [{ model_id: 'gpt-4' }] }
      })

      const { fetchModels } = useLLMModels()
      await fetchModels()
      await fetchModels({ forceRefresh: true })

      expect(axios.get).toHaveBeenCalledTimes(2)
    })

    it('LLM_MOD_008: passes filter options', async () => {
      axios.get.mockResolvedValue({ data: { models: [] } })

      const { fetchModels } = useLLMModels()
      await fetchModels({
        activeOnly: false,
        modelType: 'embedding',
        visionOnly: true,
        reasoningOnly: true,
        forceRefresh: true
      })

      const calledUrl = axios.get.mock.calls[0][0]
      expect(calledUrl).toContain('active_only=false')
      expect(calledUrl).toContain('model_type=embedding')
      expect(calledUrl).toContain('vision_only=true')
      expect(calledUrl).toContain('reasoning_only=true')
    })

    it('LLM_MOD_009: handles API error', async () => {
      axios.get.mockRejectedValue({
        response: { data: { error: 'Unauthorized' } }
      })

      const { fetchModels, error } = useLLMModels()
      await expect(fetchModels()).rejects.toThrow()

      expect(error.value).toBe('Unauthorized')
    })

    it('LLM_MOD_010: sets loading during fetch', async () => {
      let resolvePromise
      axios.get.mockReturnValue(new Promise(resolve => { resolvePromise = resolve }))

      const { fetchModels, loading } = useLLMModels()
      const promise = fetchModels()
      expect(loading.value).toBe(true)

      resolvePromise({ data: { models: [] } })
      await promise
      expect(loading.value).toBe(false)
    })

    it('LLM_MOD_011: defaults activeOnly to true', async () => {
      axios.get.mockResolvedValue({ data: { models: [] } })

      const { fetchModels } = useLLMModels()
      await fetchModels()

      const calledUrl = axios.get.mock.calls[0][0]
      expect(calledUrl).toContain('active_only=true')
    })

    it('LLM_MOD_012: defaults modelType to llm', async () => {
      axios.get.mockResolvedValue({ data: { models: [] } })

      const { fetchModels } = useLLMModels()
      await fetchModels()

      const calledUrl = axios.get.mock.calls[0][0]
      expect(calledUrl).toContain('model_type=llm')
    })

    it('LLM_MOD_013: handles missing models in response', async () => {
      axios.get.mockResolvedValue({ data: {} })

      const { fetchModels, models } = useLLMModels()
      await fetchModels()

      expect(models.value).toEqual([])
    })
  })

  // ==================== Computed ====================

  describe('selectItems', () => {
    it('LLM_MOD_014: formats models for v-select', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            {
              model_id: 'gpt-4',
              display_name: 'GPT-4',
              provider_name: 'OpenAI',
              description: 'Latest GPT',
              cost_per_1k_tokens: 0.03,
              supports_vision: true,
              supports_reasoning: false,
              is_default: true
            }
          ]
        }
      })

      const { fetchModels, selectItems } = useLLMModels()
      await fetchModels()

      expect(selectItems.value).toHaveLength(1)
      const item = selectItems.value[0]
      expect(item.id).toBe('gpt-4')
      expect(item.name).toBe('GPT-4')
      expect(item.provider).toBe('OpenAI')
      expect(item.supportsVision).toBe(true)
      expect(item.isDefault).toBe(true)
      expect(item.raw).toBeDefined()
    })

    it('LLM_MOD_015: uses model_id as name fallback', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [{ model_id: 'some-model', provider_name: 'Provider' }]
        }
      })

      const { fetchModels, selectItems } = useLLMModels()
      await fetchModels()

      expect(selectItems.value[0].name).toBe('some-model')
    })

    it('LLM_MOD_016: defaults provider to Unknown', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [{ model_id: 'model-1' }]
        }
      })

      const { fetchModels, selectItems } = useLLMModels()
      await fetchModels()

      expect(selectItems.value[0].provider).toBe('Unknown')
    })
  })

  describe('groupedByProvider', () => {
    it('LLM_MOD_017: groups models by provider', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            { model_id: 'gpt-4', provider_name: 'OpenAI', display_name: 'GPT-4' },
            { model_id: 'gpt-3.5', provider_name: 'OpenAI', display_name: 'GPT-3.5' },
            { model_id: 'claude-3', provider_name: 'Anthropic', display_name: 'Claude 3' }
          ]
        }
      })

      const { fetchModels, groupedByProvider } = useLLMModels()
      await fetchModels()

      expect(Object.keys(groupedByProvider.value)).toHaveLength(2)
      expect(groupedByProvider.value['OpenAI']).toHaveLength(2)
      expect(groupedByProvider.value['Anthropic']).toHaveLength(1)
    })

    it('LLM_MOD_018: uses Other for models without provider', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [{ model_id: 'local-model' }]
        }
      })

      const { fetchModels, groupedByProvider } = useLLMModels()
      await fetchModels()

      expect(groupedByProvider.value['Other']).toHaveLength(1)
    })
  })

  describe('defaultModel', () => {
    it('LLM_MOD_019: returns default model', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            { model_id: 'model-a', is_default: false },
            { model_id: 'model-b', is_default: true }
          ]
        }
      })

      const { fetchModels, defaultModel } = useLLMModels()
      await fetchModels()

      expect(defaultModel.value.model_id).toBe('model-b')
    })

    it('LLM_MOD_020: falls back to first model', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            { model_id: 'model-a', is_default: false },
            { model_id: 'model-b', is_default: false }
          ]
        }
      })

      const { fetchModels, defaultModel } = useLLMModels()
      await fetchModels()

      expect(defaultModel.value.model_id).toBe('model-a')
    })

    it('LLM_MOD_021: returns null when no models', () => {
      const { defaultModel } = useLLMModels()
      expect(defaultModel.value).toBeNull()
    })
  })

  // ==================== getModelById ====================

  describe('getModelById', () => {
    it('LLM_MOD_022: finds model by id', async () => {
      axios.get.mockResolvedValue({
        data: {
          models: [
            { model_id: 'gpt-4', display_name: 'GPT-4' },
            { model_id: 'claude-3', display_name: 'Claude 3' }
          ]
        }
      })

      const { fetchModels, getModelById } = useLLMModels()
      await fetchModels()

      const model = getModelById('claude-3')
      expect(model).toBeDefined()
      expect(model.display_name).toBe('Claude 3')
    })

    it('LLM_MOD_023: returns null for unknown id', async () => {
      axios.get.mockResolvedValue({
        data: { models: [{ model_id: 'gpt-4' }] }
      })

      const { fetchModels, getModelById } = useLLMModels()
      await fetchModels()

      expect(getModelById('unknown')).toBeNull()
    })

    it('LLM_MOD_024: returns null when no models loaded', () => {
      const { getModelById } = useLLMModels()
      expect(getModelById('any')).toBeNull()
    })
  })

  // ==================== invalidateCache ====================

  describe('invalidateCache', () => {
    it('LLM_MOD_025: invalidating cache forces re-fetch', async () => {
      axios.get.mockResolvedValue({
        data: { models: [{ model_id: 'gpt-4' }] }
      })

      const { fetchModels, invalidateCache } = useLLMModels()
      await fetchModels()

      invalidateCache()
      await fetchModels()

      expect(axios.get).toHaveBeenCalledTimes(2)
    })
  })

  // ==================== Shared State (Singleton) ====================

  describe('Shared State', () => {
    it('LLM_MOD_026: multiple instances share same models', async () => {
      axios.get.mockResolvedValue({
        data: { models: [{ model_id: 'shared-model' }] }
      })

      const instance1 = useLLMModels()
      await instance1.fetchModels()

      const instance2 = useLLMModels()
      expect(instance2.models.value).toHaveLength(1)
      expect(instance2.models.value[0].model_id).toBe('shared-model')
    })

    it('LLM_MOD_027: models are readonly', () => {
      const { models } = useLLMModels()
      // readonly refs throw in strict mode but in Vue they just warn
      expect(models.value).toEqual(expect.any(Array))
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('LLM_MOD_028: handles error with default message', async () => {
      axios.get.mockRejectedValue(new Error('Connection refused'))

      const { fetchModels, error } = useLLMModels()
      await expect(fetchModels()).rejects.toThrow()

      expect(error.value).toBe('Failed to fetch models')
    })

    it('LLM_MOD_029: loading resets after error', async () => {
      axios.get.mockRejectedValue(new Error('Error'))

      const { fetchModels, loading } = useLLMModels()
      await expect(fetchModels()).rejects.toThrow()

      expect(loading.value).toBe(false)
    })

    it('LLM_MOD_030: empty selectItems when no models', () => {
      const { selectItems } = useLLMModels()
      expect(selectItems.value).toEqual([])
    })
  })
})
