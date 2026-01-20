/**
 * useRatingEvaluation - Rating-specific Evaluation Composable
 *
 * Extends useEvaluationSession with rating-specific functionality for
 * evaluating EmailThread features on a Likert scale.
 *
 * Features:
 *   - Load thread with its features
 *   - Navigate between features within a thread
 *   - Rate features on configurable scale
 *   - Support for edited content (text corrections)
 *   - Auto-advance to next feature after rating
 *
 * Usage:
 *   const { thread, features, currentFeature, rateFeature }
 *     = useRatingEvaluation(scenarioId)
 */

import { ref, computed, watch, readonly } from 'vue'
import axios from 'axios'
import { useEvaluationSession, SESSION_STATUS } from './useEvaluationSession'

/**
 * Rating-specific evaluation composable
 * @param {number} scenarioId - Scenario ID
 * @returns {Object} Rating state and methods
 */
export function useRatingEvaluation(scenarioId) {
  // Use base session composable
  const session = useEvaluationSession(scenarioId, 'rating')

  // ===== Rating-specific State =====
  const features = ref([])
  const currentFeatureIndex = ref(0)
  const messages = ref([])
  const featureTypes = ref([])
  const activeFeatureType = ref(null)
  const editedContent = ref({})
  const ratingInProgress = ref(false)

  // ===== Computed =====

  const currentThread = computed(() => session.currentItem.value)

  const currentFeature = computed(() => {
    if (features.value.length === 0 || currentFeatureIndex.value < 0) return null
    return features.value[currentFeatureIndex.value] || null
  })

  const hasNextFeature = computed(() => {
    return currentFeatureIndex.value < features.value.length - 1
  })

  const hasPrevFeature = computed(() => {
    return currentFeatureIndex.value > 0
  })

  const featureProgress = computed(() => {
    const total = features.value.length
    const completed = features.value.filter(f => f.evaluated).length
    return { total, completed, percent: total > 0 ? Math.round((completed / total) * 100) : 0 }
  })

  const featuresByType = computed(() => {
    const grouped = {}
    features.value.forEach(feature => {
      const type = feature.feature_type || feature.function_type_name || 'other'
      if (!grouped[type]) {
        grouped[type] = []
      }
      grouped[type].push(feature)
    })
    return grouped
  })

  const currentFeatureType = computed(() => {
    if (!currentFeature.value) return null
    return currentFeature.value.feature_type || currentFeature.value.function_type_name || 'other'
  })

  // ===== Feature Navigation =====

  function goToFeature(index) {
    if (index < 0 || index >= features.value.length) return false
    currentFeatureIndex.value = index
    return true
  }

  function goNextFeature() {
    if (!hasNextFeature.value) return false
    currentFeatureIndex.value++
    return true
  }

  function goPrevFeature() {
    if (!hasPrevFeature.value) return false
    currentFeatureIndex.value--
    return true
  }

  function goToFirstIncompleteFeature() {
    const index = features.value.findIndex(f => !f.evaluated)
    if (index >= 0) {
      currentFeatureIndex.value = index
      return true
    }
    return false
  }

  function selectFeatureByType(featureType) {
    activeFeatureType.value = featureType
    const typeFeatures = featuresByType.value[featureType]
    if (typeFeatures && typeFeatures.length > 0) {
      const firstIndex = features.value.indexOf(typeFeatures[0])
      if (firstIndex >= 0) {
        currentFeatureIndex.value = firstIndex
      }
    }
  }

  // ===== Thread Loading =====

  /**
   * Load features for the current thread
   */
  async function loadThreadFeatures(threadId) {
    if (!threadId) return

    try {
      const response = await axios.get(
        `/api/evaluation/session/${scenarioId}/threads/${threadId}/features`
      )

      features.value = response.data.features || []
      messages.value = response.data.messages || []
      featureTypes.value = response.data.feature_types || []

      // Reset to first incomplete feature
      currentFeatureIndex.value = 0
      goToFirstIncompleteFeature()

      // Set active feature type
      if (featureTypes.value.length > 0 && !activeFeatureType.value) {
        activeFeatureType.value = featureTypes.value[0]
      }

      // Clear edited content for new thread
      editedContent.value = {}
    } catch (err) {
      console.error('Failed to load thread features:', err)
      features.value = []
      messages.value = []
    }
  }

  // Watch for thread changes and load features
  watch(() => session.currentItem.value, (newThread) => {
    if (newThread?.thread_id || newThread?.id) {
      loadThreadFeatures(newThread.thread_id || newThread.id)
    }
  }, { immediate: true })

  // ===== Rating Actions =====

  /**
   * Rate a feature
   * @param {number} featureId - Feature ID to rate
   * @param {number} rating - Rating value (e.g., 1-5)
   * @param {Object} options - Additional options
   * @param {string} options.editedText - Corrected text if user made edits
   * @param {string} options.comment - Optional comment
   * @param {boolean} options.autoAdvance - Auto-advance to next feature (default: true)
   */
  async function rateFeature(featureId, rating, options = {}) {
    if (!featureId || rating === null || rating === undefined) {
      throw new Error('Feature ID and rating are required')
    }

    const { editedText, comment, autoAdvance = true } = options

    ratingInProgress.value = true

    try {
      const response = await axios.post(
        `/api/evaluation/session/${scenarioId}/features/${featureId}/rate`,
        {
          rating,
          edited_content: editedText || editedContent.value[featureId],
          comment,
          thread_id: currentThread.value?.thread_id || currentThread.value?.id
        }
      )

      // Update local feature state
      const featureIndex = features.value.findIndex(f => f.id === featureId || f.feature_id === featureId)
      if (featureIndex >= 0) {
        features.value[featureIndex].evaluated = true
        features.value[featureIndex].rating = rating
        features.value[featureIndex].evaluation = response.data.evaluation
      }

      // Clear edited content for this feature
      delete editedContent.value[featureId]

      // Auto-advance to next feature
      if (autoAdvance && hasNextFeature.value) {
        goNextFeature()
      } else if (autoAdvance && !hasNextFeature.value) {
        // All features rated - check if should advance to next thread
        if (featureProgress.value.completed >= featureProgress.value.total) {
          // Mark thread as evaluated
          if (currentThread.value) {
            await markThreadComplete()
          }
        }
      }

      return response.data
    } catch (err) {
      console.error('Failed to rate feature:', err)
      throw err
    } finally {
      ratingInProgress.value = false
    }
  }

  /**
   * Mark current thread as complete and advance to next
   */
  async function markThreadComplete() {
    try {
      await session.submitEvaluation(
        currentThread.value.thread_id || currentThread.value.id,
        { status: 'completed' }
      )

      // Advance to next thread if available
      if (session.hasNext.value) {
        session.goNext()
      }
    } catch (err) {
      console.error('Failed to mark thread complete:', err)
    }
  }

  /**
   * Set edited content for a feature
   * @param {number} featureId - Feature ID
   * @param {string} text - Edited text
   */
  function setEditedContent(featureId, text) {
    editedContent.value[featureId] = text
  }

  /**
   * Check if feature has been edited
   * @param {number} featureId - Feature ID
   * @returns {boolean}
   */
  function hasEdits(featureId) {
    return !!editedContent.value[featureId]
  }

  /**
   * Get edited content for a feature
   * @param {number} featureId - Feature ID
   * @returns {string|null}
   */
  function getEditedContent(featureId) {
    return editedContent.value[featureId] || null
  }

  // ===== Exposed API =====

  return {
    // Base session exports
    ...session,

    // Rating-specific state
    features: readonly(features),
    currentFeatureIndex: readonly(currentFeatureIndex),
    messages: readonly(messages),
    featureTypes: readonly(featureTypes),
    activeFeatureType,
    ratingInProgress: readonly(ratingInProgress),

    // Computed
    currentThread,
    currentFeature,
    hasNextFeature,
    hasPrevFeature,
    featureProgress,
    featuresByType,
    currentFeatureType,

    // Feature Navigation
    goToFeature,
    goNextFeature,
    goPrevFeature,
    goToFirstIncompleteFeature,
    selectFeatureByType,

    // Rating Actions
    loadThreadFeatures,
    rateFeature,
    markThreadComplete,

    // Edited Content
    editedContent: readonly(editedContent),
    setEditedContent,
    hasEdits,
    getEditedContent
  }
}
