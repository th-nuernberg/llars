/**
 * Composable for Schema-based Evaluation Data
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Die Schemas sind definiert in:
 * - Backend: app/schemas/evaluation_data_schemas.py
 * - Frontend: llars-frontend/src/schemas/evaluationSchemas.js
 *
 * Verwendung:
 *   const { data, error, isValid, setData, fetchItem } = useEvaluationSchema()
 *
 *   // Daten direkt setzen
 *   setData(apiResponse)
 *
 *   // Oder von API laden
 *   await fetchItem(scenarioId, itemId)
 *
 *   // Multi-Group Ranking
 *   if (isMultiGroup.value) {
 *     groups.value.forEach(group => {
 *       const items = groupedItems.value[group.id]
 *     })
 *   }
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 */

import { ref, computed, readonly } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import {
  validateEvaluationData,
  isMultiGroupRanking as checkMultiGroup,
  getRankingGroups,
  groupItemsByGroup,
  getLocalizedText,
  EvaluationType,
  RankingMode
} from '@/schemas/evaluationSchemas'

/**
 * Composable for working with EvaluationData schema
 * @returns {Object}
 */
export function useEvaluationSchema() {
  const { locale } = useI18n()

  // State
  const data = ref(null)
  const error = ref(null)
  const validationResult = ref({ valid: false, errors: [], warnings: [] })
  const isLoading = ref(false)

  // Computed
  const isValid = computed(() => validationResult.value.valid)
  const errors = computed(() => validationResult.value.errors)
  const warnings = computed(() => validationResult.value.warnings)

  /**
   * Evaluation type
   */
  const type = computed(() => data.value?.type || null)

  /**
   * Schema version
   */
  const schemaVersion = computed(() => data.value?.schema_version || null)

  /**
   * Reference (context displayed on right side)
   */
  const reference = computed(() => data.value?.reference || null)

  /**
   * Items to evaluate (displayed on left side)
   */
  const items = computed(() => data.value?.items || [])

  /**
   * Type-specific configuration
   */
  const config = computed(() => data.value?.config || null)

  /**
   * Ground truth (if available)
   */
  const groundTruth = computed(() => data.value?.ground_truth || null)

  /**
   * Is this multi-group ranking?
   */
  const isMultiGroup = computed(() => checkMultiGroup(data.value))

  /**
   * Ranking groups (for multi-group mode)
   */
  const groups = computed(() => getRankingGroups(data.value))

  /**
   * Items grouped by their group field
   */
  const groupedItems = computed(() => groupItemsByGroup(data.value?.items))

  /**
   * Buckets (for ranking)
   */
  const buckets = computed(() => {
    if (!config.value) return []
    if (config.value.mode === RankingMode.MULTI_GROUP) {
      // Return buckets from first group (they're usually the same)
      return config.value.groups?.[0]?.buckets || []
    }
    return config.value.buckets || []
  })

  /**
   * Dimensions (for rating)
   */
  const dimensions = computed(() => config.value?.dimensions || [])

  /**
   * Scale (for rating)
   */
  const scale = computed(() => config.value?.scale || null)

  /**
   * Set and validate data
   * @param {Object} rawData - Raw EvaluationData object
   * @returns {boolean} - Whether data is valid
   */
  function setData(rawData) {
    const result = validateEvaluationData(rawData)
    validationResult.value = result

    if (result.valid) {
      data.value = rawData
      error.value = null
    } else {
      error.value = result.errors.map(e => e.message).join(', ')
    }

    // Log warnings in development
    if (result.warnings.length > 0) {
      console.warn('[useEvaluationSchema] Validation warnings:', result.warnings)
    }

    return result.valid
  }

  /**
   * Clear data
   */
  function clear() {
    data.value = null
    error.value = null
    validationResult.value = { valid: false, errors: [], warnings: [] }
  }

  /**
   * Fetch item data from API
   * @param {number} scenarioId - Scenario ID
   * @param {number} itemId - Item ID
   * @param {Object} [options] - Options
   * @param {boolean} [options.includeGroundTruth=false] - Include ground truth
   * @returns {Promise<boolean>} - Whether fetch was successful
   */
  async function fetchItem(scenarioId, itemId, options = {}) {
    isLoading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      if (options.includeGroundTruth) {
        params.append('include_ground_truth', 'true')
      }

      const url = `/api/scenarios/${scenarioId}/items/${itemId}/schema${params.toString() ? '?' + params.toString() : ''}`
      const response = await axios.get(url)

      return setData(response.data)
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch multiple items in batch
   * @param {number} scenarioId - Scenario ID
   * @param {number[]} itemIds - Item IDs
   * @param {Object} [options] - Options
   * @returns {Promise<Object[]>} - Array of EvaluationData objects
   */
  async function fetchItemsBatch(scenarioId, itemIds, options = {}) {
    isLoading.value = true
    error.value = null

    try {
      const response = await axios.post(`/api/scenarios/${scenarioId}/items/schema/batch`, {
        item_ids: itemIds,
        include_ground_truth: options.includeGroundTruth || false
      })

      return response.data.items || []
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      return []
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Fetch scenario overview
   * @param {number} scenarioId - Scenario ID
   * @returns {Promise<Object|null>} - Scenario overview
   */
  async function fetchScenarioOverview(scenarioId) {
    isLoading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/scenarios/${scenarioId}/schema`)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.error || e.message
      return null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get localized text helper
   * @param {Object|string} value - LocalizedString or plain string
   * @returns {string}
   */
  function localize(value) {
    return getLocalizedText(value, locale.value)
  }

  /**
   * Check if type matches
   * @param {string} typeToCheck - Type to check
   * @returns {boolean}
   */
  function isType(typeToCheck) {
    return type.value === typeToCheck
  }

  // Helper methods for specific types
  const isRanking = computed(() => type.value === EvaluationType.RANKING)
  const isRating = computed(() => type.value === EvaluationType.RATING)
  const isMailRating = computed(() => type.value === EvaluationType.MAIL_RATING)
  const isComparison = computed(() => type.value === EvaluationType.COMPARISON)
  const isAuthenticity = computed(() => type.value === EvaluationType.AUTHENTICITY)
  const isLabeling = computed(() => type.value === EvaluationType.LABELING)

  return {
    // State (readonly)
    data: readonly(data),
    error: readonly(error),
    isLoading: readonly(isLoading),

    // Validation
    isValid,
    errors,
    warnings,

    // Computed from data
    type,
    schemaVersion,
    reference,
    items,
    config,
    groundTruth,

    // Ranking-specific
    isMultiGroup,
    groups,
    groupedItems,
    buckets,

    // Rating-specific
    dimensions,
    scale,

    // Type checks
    isRanking,
    isRating,
    isMailRating,
    isComparison,
    isAuthenticity,
    isLabeling,
    isType,

    // Methods
    setData,
    clear,
    fetchItem,
    fetchItemsBatch,
    fetchScenarioOverview,
    localize
  }
}

export default useEvaluationSchema
