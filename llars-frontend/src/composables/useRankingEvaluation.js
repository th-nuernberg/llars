/**
 * useRankingEvaluation - Composable for bucket-based ranking evaluation
 *
 * Provides state management and API interaction for ranking evaluation
 * where users sort items into predefined buckets (Good, Moderate, Bad).
 *
 * Uses generic session endpoint for loading items and ranking-specific
 * endpoints for thread details and saving.
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

export function useRankingEvaluation(scenarioId) {
  // State
  const items = ref([])
  const currentItem = ref(null)
  const currentItemIndex = ref(0)
  const messages = ref([])
  const content = ref('')
  const config = ref(null)
  const existingRanking = ref(null)

  // Ranking state
  const selectedBucket = ref(null)
  const notes = ref('')

  // Default buckets (can be overridden by config)
  const buckets = computed(() => {
    if (config.value?.buckets && config.value.buckets.length > 0) {
      return config.value.buckets
    }
    return [
      { id: 'good', name: 'Gut', icon: 'mdi-thumb-up', color: 'good', description: 'Hohe Qualität' },
      { id: 'moderate', name: 'Moderat', icon: 'mdi-thumbs-up-down', color: 'moderate', description: 'Durchschnittlich' },
      { id: 'bad', name: 'Schlecht', icon: 'mdi-thumb-down', color: 'bad', description: 'Niedrige Qualität' }
    ]
  })

  // Loading states
  const loading = ref(false)
  const loadingItem = ref(false)
  const saving = ref(false)
  const error = ref(null)

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

    if (selectedBucket.value || currentItem.value.evaluated) {
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
      console.error('Failed to load ranking items:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load items'
    } finally {
      loading.value = false
    }
  }

  // Load a specific item using ranking endpoint
  async function loadItem(threadId) {
    loadingItem.value = true
    error.value = null

    try {
      // Use ranking-specific endpoint for thread details
      const response = await axios.get(`/api/email_threads/rankings/${threadId}`)

      currentItem.value = {
        thread_id: threadId,
        chat_id: response.data.chat_id,
        subject: response.data.subject,
        ranked: response.data.ranked
      }
      messages.value = response.data.messages || []
      content.value = ''
      existingRanking.value = null

      // Get current ranking if exists
      try {
        const rankingResponse = await axios.get(`/api/email_threads/${threadId}/current_ranking`)
        existingRanking.value = rankingResponse.data
        // If there's existing ranking, mark as selected
        if (rankingResponse.data && rankingResponse.data.length > 0) {
          selectedBucket.value = 'ranked'
        } else {
          selectedBucket.value = null
        }
      } catch {
        // No existing ranking is fine
        selectedBucket.value = null
      }

      notes.value = ''

      const index = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === threadId
      )
      if (index >= 0) {
        currentItemIndex.value = index
      }
    } catch (err) {
      console.error('Failed to load item:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load item'
    } finally {
      loadingItem.value = false
    }
  }

  // Get thread ID from current item
  function getThreadId() {
    if (!currentItem.value) return null
    return currentItem.value.thread_id || currentItem.value.id || currentItem.value.item_id
  }

  // Select bucket (auto-saves)
  // Note: The existing backend uses a different ranking format (feature-based).
  // This is a simplified bucket-based implementation that marks items as evaluated.
  async function selectBucket(bucketId) {
    const threadId = getThreadId()
    if (!threadId) return { success: false, error: 'No item selected' }

    saving.value = true
    error.value = null

    try {
      // Use generic evaluation submission endpoint
      await axios.post(
        `/api/evaluation/session/${scenarioId.value}/items/${threadId}/evaluate`,
        {
          function_type: 'ranking',
          bucket: bucketId,
          notes: notes.value || null
        }
      )

      selectedBucket.value = bucketId

      const itemIndex = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === threadId
      )
      if (itemIndex >= 0) {
        items.value[itemIndex].evaluated = true
        items.value[itemIndex].ranked = true
      }

      return { success: true, bucket: bucketId }
    } catch (err) {
      console.error('Failed to save ranking:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to save ranking'
      return { success: false, error: error.value }
    } finally {
      saving.value = false
    }
  }

  // Save metadata (notes) - debounced
  // Note: Metadata endpoint may not exist for ranking; this is a no-op for now
  const saveMetadata = debounce(async () => {
    if (!currentItem.value || !selectedBucket.value) return
    // Notes are saved with the bucket selection
    // No separate metadata endpoint exists for ranking
  }, 800)

  // Navigation
  async function goToItem(index) {
    if (index >= 0 && index < items.value.length) {
      const item = items.value[index]
      const threadId = item.thread_id || item.id || item.item_id
      await loadItem(threadId)
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
    messages.value = []
    content.value = ''
    config.value = null
    selectedBucket.value = null
    notes.value = ''
    existingRanking.value = null
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
    messages,
    content,
    config,
    selectedBucket,
    notes,
    buckets,
    existingRanking,
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
    selectBucket,
    saveMetadata,
    goToItem,
    goNext,
    goPrev,
    reset
  }
}
