/**
 * Composable for managing LLM models
 *
 * Provides access to available LLM models with caching and filtering.
 */

import { ref, computed, readonly } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

// Shared state across components (singleton pattern)
const models = ref([])
const loading = ref(false)
const error = ref(null)
const lastFetch = ref(null)

// Cache duration: 5 minutes
const CACHE_DURATION = 5 * 60 * 1000

export function useLLMModels() {
  const { getToken } = useAuth()

  /**
   * Get authorization headers
   */
  function getHeaders() {
    return {
      Authorization: `Bearer ${getToken()}`
    }
  }

  /**
   * Fetch available models from API
   * @param {Object} options - Filter options
   * @param {boolean} options.activeOnly - Only return active models (default: true)
   * @param {string} options.modelType - Filter by type: llm, embedding, reranker
   * @param {boolean} options.visionOnly - Only vision-capable models
   * @param {boolean} options.reasoningOnly - Only reasoning-capable models
   * @param {boolean} options.forceRefresh - Bypass cache
   */
  async function fetchModels(options = {}) {
    const {
      activeOnly = true,
      modelType = 'llm',
      visionOnly = false,
      reasoningOnly = false,
      forceRefresh = false
    } = options

    // Check cache validity
    const cacheValid = lastFetch.value && (Date.now() - lastFetch.value < CACHE_DURATION)
    if (cacheValid && !forceRefresh && models.value.length > 0) {
      return models.value
    }

    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      params.append('active_only', activeOnly.toString())
      if (modelType) params.append('model_type', modelType)
      if (visionOnly) params.append('vision_only', 'true')
      if (reasoningOnly) params.append('reasoning_only', 'true')

      const response = await axios.get(`/api/llm/models/available?${params}`, {
        headers: getHeaders()
      })

      models.value = response.data.models || []
      lastFetch.value = Date.now()
      return models.value
    } catch (err) {
      error.value = err.response?.data?.error || 'Failed to fetch models'
      console.error('Error fetching LLM models:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get models formatted for v-select component
   */
  const selectItems = computed(() => {
    return models.value.map(model => ({
      id: model.model_id,
      name: model.display_name || model.model_id,
      provider: model.provider_name || 'Unknown',
      description: model.description,
      costPer1k: model.cost_per_1k_tokens,
      supportsVision: model.supports_vision,
      supportsReasoning: model.supports_reasoning,
      isDefault: model.is_default,
      raw: model
    }))
  })

  /**
   * Get models grouped by provider
   */
  const groupedByProvider = computed(() => {
    const grouped = {}
    for (const model of models.value) {
      const provider = model.provider_name || 'Other'
      if (!grouped[provider]) {
        grouped[provider] = []
      }
      grouped[provider].push({
        id: model.model_id,
        name: model.display_name || model.model_id,
        costPer1k: model.cost_per_1k_tokens,
        raw: model
      })
    }
    return grouped
  })

  /**
   * Find model by ID
   */
  function getModelById(modelId) {
    return models.value.find(m => m.model_id === modelId) || null
  }

  /**
   * Get default model
   */
  const defaultModel = computed(() => {
    return models.value.find(m => m.is_default) || models.value[0] || null
  })

  /**
   * Invalidate cache
   */
  function invalidateCache() {
    lastFetch.value = null
  }

  return {
    // State (readonly)
    models: readonly(models),
    loading: readonly(loading),
    error: readonly(error),

    // Computed
    selectItems,
    groupedByProvider,
    defaultModel,

    // Methods
    fetchModels,
    getModelById,
    invalidateCache
  }
}
