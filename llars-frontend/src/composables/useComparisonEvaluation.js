/**
 * useComparisonEvaluation - Composable for A/B comparison evaluation
 *
 * Provides state management and API interaction for comparison evaluation
 * where users choose between two options (A vs B) or declare a tie.
 *
 * Uses generic session endpoint for loading items. Comparison items
 * contain two options (option_a, option_b) which are displayed side by side.
 */

import { ref, computed, watch } from 'vue'
import axios from 'axios'

/**
 * Debounce helper for auto-save
 */
function debounce(fn, delay) {
  let timeoutId = null
  return (...args) => {
    if (timeoutId) clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn(...args), delay)
  }
}

export function useComparisonEvaluation(scenarioId) {
  // State
  const items = ref([])
  const currentItem = ref(null)
  const currentItemIndex = ref(0)
  const config = ref(null)
  const existingComparison = ref(null)

  // Option content
  const optionA = ref({ messages: [], content: '' })
  const optionB = ref({ messages: [], content: '' })

  // Comparison state
  const selectedOption = ref(null) // 'A', 'B', or 'tie'
  const notes = ref('')

  // Loading states
  const loading = ref(false)
  const loadingItem = ref(false)
  const saving = ref(false)
  const error = ref(null)

  // Cache for loaded item details (prevents flicker on navigation)
  const itemCache = ref({})

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

  // Computed: Current item status
  const currentItemStatus = computed(() => {
    if (!currentItem.value) return 'pending'

    if (selectedOption.value || currentItem.value.evaluated) {
      return 'done'
    }

    if (notes.value) {
      return 'in_progress'
    }

    return 'pending'
  })

  // Load items via generic evaluation session endpoint
  async function loadItems() {
    loading.value = true
    error.value = null

    try {
      // Use generic session endpoint
      const response = await axios.get(`/api/evaluation/session/${scenarioId.value}`)
      items.value = response.data.items || []
      config.value = response.data.config

      if (items.value.length > 0 && !currentItem.value) {
        const firstItem = items.value[0]
        const itemId = firstItem.thread_id || firstItem.id || firstItem.item_id
        await loadItem(itemId)
      }
    } catch (err) {
      console.error('Failed to load comparison items:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load items'
    } finally {
      loading.value = false
    }
  }

  // Load a specific item
  // For comparison, items should have option_a and option_b data
  async function loadItem(itemId) {
    error.value = null

    // Check cache first - if cached, apply immediately without loading state
    const cacheKey = String(itemId)
    if (itemCache.value[cacheKey]) {
      applyItemData(itemCache.value[cacheKey], itemId)
      return
    }

    loadingItem.value = true

    try {
      // Try to get thread features which may contain comparison options
      const response = await axios.get(
        `/api/evaluation/session/${scenarioId.value}/threads/${itemId}/features`
      )

      // Cache the response
      itemCache.value[cacheKey] = response.data

      applyItemData(response.data, itemId)
    } catch (err) {
      console.error('Failed to load item:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load item'
    } finally {
      loadingItem.value = false
    }
  }

  // Helper to apply item data (used by loadItem and cache)
  function applyItemData(data, itemId) {
    currentItem.value = {
      item_id: itemId,
      thread_id: itemId,
      subject: data.subject
    }

    // For comparison scenarios, features represent the two options
    const features = data.features || []
    if (features.length >= 2) {
      optionA.value = {
        messages: [],
        content: features[0]?.content || '',
        model: features[0]?.model_name || 'Option A'
      }
      optionB.value = {
        messages: [],
        content: features[1]?.content || '',
        model: features[1]?.model_name || 'Option B'
      }
    } else {
      // Fallback: use messages as content
      optionA.value = { messages: data.messages || [], content: '' }
      optionB.value = { messages: [], content: '' }
    }

    existingComparison.value = null
    selectedOption.value = null
    notes.value = ''

    const index = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === itemId
    )
    if (index >= 0) {
      currentItemIndex.value = index
    }
  }

  // Get item ID from current item
  function getItemId() {
    if (!currentItem.value) return null
    return currentItem.value.item_id || currentItem.value.thread_id || currentItem.value.id
  }

  // Select option (auto-saves)
  // Update cache with current comparison state
  function updateCache() {
    const itemId = getItemId()
    if (!itemId) return
    const cacheKey = String(itemId)
    if (itemCache.value[cacheKey]) {
      itemCache.value[cacheKey] = {
        ...itemCache.value[cacheKey],
        existing_comparison: {
          choice: selectedOption.value,
          notes: notes.value || ''
        }
      }
    }
  }

  async function selectOption(option) {
    const itemId = getItemId()
    if (!itemId) return { success: false, error: 'No item selected' }

    saving.value = true
    error.value = null

    try {
      // Use generic evaluation submission endpoint
      await axios.post(
        `/api/evaluation/session/${scenarioId.value}/items/${itemId}/evaluate`,
        {
          function_type: 'comparison',
          choice: option,
          notes: notes.value || null
        }
      )

      selectedOption.value = option

      // Update cache with current state
      updateCache()

      const itemIndex = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === itemId
      )
      if (itemIndex >= 0) {
        items.value[itemIndex].evaluated = true
      }

      return { success: true, choice: option }
    } catch (err) {
      console.error('Failed to save comparison:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to save comparison'
      return { success: false, error: error.value }
    } finally {
      saving.value = false
    }
  }

  // Save metadata (notes) - debounced
  // Note: No separate metadata endpoint; notes are saved with the comparison
  const saveMetadata = debounce(async () => {
    if (!currentItem.value || !selectedOption.value) return
    // Notes are saved with the option selection
  }, 800)

  // Navigation
  async function goToItem(index) {
    if (index >= 0 && index < items.value.length) {
      const item = items.value[index]
      const itemId = item.thread_id || item.id || item.item_id
      await loadItem(itemId)
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

  // Reset
  function reset() {
    items.value = []
    currentItem.value = null
    currentItemIndex.value = 0
    optionA.value = { messages: [], content: '' }
    optionB.value = { messages: [], content: '' }
    config.value = null
    selectedOption.value = null
    notes.value = ''
    existingComparison.value = null
    error.value = null
  }

  watch(scenarioId, (newId, oldId) => {
    if (newId !== oldId && newId) {
      reset()
      loadItems()
    }
  }, { immediate: false })

  return {
    items,
    currentItem,
    currentItemIndex,
    optionA,
    optionB,
    config,
    selectedOption,
    notes,
    existingComparison,
    loading,
    loadingItem,
    saving,
    error,
    progress,
    hasNext,
    hasPrev,
    currentItemStatus,
    loadItems,
    loadItem,
    selectOption,
    saveMetadata,
    goToItem,
    goNext,
    goPrev,
    reset
  }
}
