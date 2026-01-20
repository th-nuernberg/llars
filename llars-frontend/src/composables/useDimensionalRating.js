/**
 * useDimensionalRating - Composable for multi-dimensional item rating
 *
 * Provides state management and API interaction for the new generalized
 * rating system where items are evaluated on multiple dimensions
 * (e.g., Coherence, Fluency, Relevance, Consistency).
 *
 * Usage:
 * const {
 *   items, currentItem, currentItemIndex, dimensionRatings,
 *   config, dimensions, overallScore, progress, canSubmit,
 *   loading, error,
 *   loadItems, loadItem, setDimensionRating, submitRating,
 *   goToItem, goNext, goPrev, hasNext, hasPrev
 * } = useDimensionalRating(scenarioId)
 */

import { ref, computed, watch } from 'vue'
import axios from 'axios'

export function useDimensionalRating(scenarioId) {
  // State
  const items = ref([])
  const currentItem = ref(null)
  const currentItemIndex = ref(0)
  const messages = ref([])
  const content = ref('')
  const config = ref(null)
  const dimensionRatings = ref({})
  const feedback = ref('')
  const existingRating = ref(null)

  // Loading states
  const loading = ref(false)
  const loadingItem = ref(false)
  const submitting = ref(false)
  const error = ref(null)

  // Computed: Dimensions from config
  const dimensions = computed(() => {
    return config.value?.dimensions || []
  })

  // Computed: Scale settings
  const scaleMin = computed(() => config.value?.min || 1)
  const scaleMax = computed(() => config.value?.max || 5)
  const scaleStep = computed(() => config.value?.step || 1)
  const scaleLabels = computed(() => config.value?.labels || {})

  // Computed: Overall score (weighted average)
  const overallScore = computed(() => {
    if (!dimensions.value.length) return null

    const ratings = dimensionRatings.value
    const dims = dimensions.value

    let totalWeight = 0
    let weightedSum = 0
    let ratedCount = 0

    for (const dim of dims) {
      const score = ratings[dim.id]
      if (score !== null && score !== undefined) {
        const weight = dim.weight || 1
        weightedSum += score * weight
        totalWeight += weight
        ratedCount++
      }
    }

    if (totalWeight === 0) return null
    return Math.round((weightedSum / totalWeight) * 100) / 100
  })

  // Computed: How many dimensions are rated
  const ratedDimensionCount = computed(() => {
    return dimensions.value.filter(
      dim => dimensionRatings.value[dim.id] !== null &&
             dimensionRatings.value[dim.id] !== undefined
    ).length
  })

  // Computed: Can submit (all dimensions rated)
  const canSubmit = computed(() => {
    return dimensions.value.every(
      dim => dimensionRatings.value[dim.id] !== null &&
             dimensionRatings.value[dim.id] !== undefined
    )
  })

  // Computed: Progress statistics
  const progress = computed(() => {
    const total = items.value.length
    const completed = items.value.filter(item => item.evaluated).length
    const inProgress = items.value.filter(
      item => !item.evaluated && item.status === 'Progressing'
    ).length

    return {
      total,
      completed,
      inProgress,
      notStarted: total - completed - inProgress,
      percent: total > 0 ? Math.round((completed / total) * 100) : 0
    }
  })

  // Computed: Navigation
  const hasNext = computed(() => currentItemIndex.value < items.value.length - 1)
  const hasPrev = computed(() => currentItemIndex.value > 0)

  // Load scenario configuration
  async function loadConfig() {
    try {
      const response = await axios.get(`/api/evaluation/rating/${scenarioId.value}/config`)
      config.value = response.data.config
    } catch (err) {
      console.error('Failed to load rating config:', err)
      error.value = err.response?.data?.message || 'Failed to load configuration'
    }
  }

  // Load all items for the scenario
  async function loadItems() {
    loading.value = true
    error.value = null

    try {
      // Load config first if not loaded
      if (!config.value) {
        await loadConfig()
      }

      const response = await axios.get(`/api/evaluation/rating/${scenarioId.value}/items`)
      items.value = response.data.items || []

      // Load first item if available
      if (items.value.length > 0 && !currentItem.value) {
        await loadItem(items.value[0].item_id)
      }
    } catch (err) {
      console.error('Failed to load rating items:', err)
      error.value = err.response?.data?.message || 'Failed to load items'
    } finally {
      loading.value = false
    }
  }

  // Load a specific item's content
  async function loadItem(itemId) {
    loadingItem.value = true
    error.value = null

    try {
      const response = await axios.get(
        `/api/evaluation/rating/${scenarioId.value}/items/${itemId}`
      )

      currentItem.value = response.data.item
      messages.value = response.data.messages || []
      content.value = response.data.content || ''
      existingRating.value = response.data.existing_rating

      // Update config if returned
      if (response.data.config) {
        config.value = response.data.config
      }

      // Initialize dimension ratings from existing rating or empty
      if (existingRating.value) {
        dimensionRatings.value = { ...existingRating.value.dimension_ratings }
        feedback.value = existingRating.value.feedback || ''
      } else {
        // Initialize all dimensions as null
        dimensionRatings.value = {}
        for (const dim of dimensions.value) {
          dimensionRatings.value[dim.id] = null
        }
        feedback.value = ''
      }

      // Update current index
      const index = items.value.findIndex(item => item.item_id === itemId)
      if (index >= 0) {
        currentItemIndex.value = index
      }
    } catch (err) {
      console.error('Failed to load item:', err)
      error.value = err.response?.data?.message || 'Failed to load item'
    } finally {
      loadingItem.value = false
    }
  }

  // Set rating for a dimension
  function setDimensionRating(dimensionId, value) {
    dimensionRatings.value = {
      ...dimensionRatings.value,
      [dimensionId]: value
    }
  }

  // Submit rating for current item
  async function submitRating(options = {}) {
    if (!currentItem.value) return { success: false, error: 'No item selected' }

    const { autoAdvance = true } = options
    submitting.value = true
    error.value = null

    try {
      const response = await axios.post(
        `/api/evaluation/rating/${scenarioId.value}/items/${currentItem.value.item_id}/rate`,
        {
          dimension_ratings: dimensionRatings.value,
          feedback: feedback.value || null,
          auto_complete: true
        }
      )

      // Update item status in list
      const itemIndex = items.value.findIndex(
        item => item.item_id === currentItem.value.item_id
      )
      if (itemIndex >= 0) {
        items.value[itemIndex].evaluated = response.data.rating?.status === 'Done'
        items.value[itemIndex].status = response.data.rating?.status
        items.value[itemIndex].overall_score = response.data.rating?.overall_score
      }

      // Auto-advance to next item if requested
      if (autoAdvance && hasNext.value && response.data.rating?.status === 'Done') {
        await goNext()
      }

      return { success: true, rating: response.data.rating }
    } catch (err) {
      console.error('Failed to submit rating:', err)
      error.value = err.response?.data?.message || 'Failed to save rating'
      return { success: false, error: error.value }
    } finally {
      submitting.value = false
    }
  }

  // Navigation functions
  async function goToItem(index) {
    if (index >= 0 && index < items.value.length) {
      await loadItem(items.value[index].item_id)
    }
  }

  async function goNext() {
    if (hasNext.value) {
      await goToItem(currentItemIndex.value + 1)
    }
  }

  async function goPrev() {
    if (hasPrev.value) {
      await goToItem(currentItemIndex.value - 1)
    }
  }

  // Find next unevaluated item
  function findNextUnevaluated() {
    const nextIndex = items.value.findIndex(
      (item, idx) => idx > currentItemIndex.value && !item.evaluated
    )
    return nextIndex >= 0 ? nextIndex : -1
  }

  // Reset state
  function reset() {
    items.value = []
    currentItem.value = null
    currentItemIndex.value = 0
    messages.value = []
    content.value = ''
    config.value = null
    dimensionRatings.value = {}
    feedback.value = ''
    existingRating.value = null
    error.value = null
  }

  // Watch for scenario ID changes
  watch(scenarioId, (newId, oldId) => {
    if (newId !== oldId && newId) {
      reset()
      loadItems()
    }
  }, { immediate: false })

  return {
    // State
    items,
    currentItem,
    currentItemIndex,
    messages,
    content,
    config,
    dimensionRatings,
    feedback,
    existingRating,

    // Loading states
    loading,
    loadingItem,
    submitting,
    error,

    // Computed
    dimensions,
    scaleMin,
    scaleMax,
    scaleStep,
    scaleLabels,
    overallScore,
    ratedDimensionCount,
    canSubmit,
    progress,
    hasNext,
    hasPrev,

    // Methods
    loadConfig,
    loadItems,
    loadItem,
    setDimensionRating,
    submitRating,
    goToItem,
    goNext,
    goPrev,
    findNextUnevaluated,
    reset
  }
}
