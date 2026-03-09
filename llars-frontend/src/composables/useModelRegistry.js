/**
 * Central model registry composable (singleton).
 *
 * Provides consistent display names and colors for any LLM model_id.
 * The registry is populated from backend API responses that include a
 * `model_registry` dict (stats, provenance, LLM evaluation progress).
 *
 * Usage:
 *   const { updateRegistry, formatModelName, getModelColor } = useModelRegistry()
 */

import { ref, computed } from 'vue'
import { parseUserProviderModelId } from '@/utils/formatters'

// Shared singleton state – lives outside the composable function so every
// component that calls useModelRegistry() shares the same reactive map.
const registry = ref({})

export function useModelRegistry() {

  /**
   * Merge new entries into the shared registry.
   * @param {Object} newEntries - { model_id: { display_name, color, user_provider_name } }
   */
  function updateRegistry(newEntries) {
    if (!newEntries || typeof newEntries !== 'object') return
    registry.value = { ...registry.value, ...newEntries }
  }

  /**
   * Format a model_id into a human-readable display name.
   *
   * Priority:
   *   1. user-provider models → parseUserProviderModelId with backend hint
   *   2. Global/ prefix → strip prefix
   *   3. DB display_name (if different from raw id)
   *   4. raw model_id
   */
  function formatModelName(modelId) {
    if (!modelId) return 'Unknown'

    const entry = registry.value[modelId]

    // User-provider models: use parser with resolved provider name hint
    if (modelId.startsWith('user-provider:')) {
      const hint = entry?.user_provider_name || null
      const parsed = parseUserProviderModelId(modelId, hint)
      if (parsed) return parsed.displayName
    }

    // Global/ models: strip prefix
    if (modelId.startsWith('Global/')) {
      return modelId.slice('Global/'.length)
    }

    // DB models with a meaningful display_name
    if (entry?.display_name && entry.display_name !== modelId) {
      return entry.display_name
    }

    return modelId
  }

  /**
   * Get the stable color for a model_id (from backend registry).
   * Returns null if not yet in registry.
   */
  function getModelColor(modelId) {
    return registry.value[modelId]?.color || null
  }

  /**
   * Get the resolved user-provider name (e.g. "IONOS") for a model_id.
   * Returns null for non-user-provider models or if not yet in registry.
   */
  function getProviderName(modelId) {
    return registry.value[modelId]?.user_provider_name || null
  }

  return {
    registry: computed(() => registry.value),
    updateRegistry,
    formatModelName,
    getModelColor,
    getProviderName,
  }
}
