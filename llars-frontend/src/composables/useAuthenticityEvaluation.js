/**
 * useAuthenticityEvaluation - Composable for fake/real authenticity evaluation
 *
 * Provides state management and API interaction for authenticity evaluation
 * where users vote whether content is real (human-written) or fake (AI-generated).
 *
 * Uses the generic evaluation session endpoint for loading items and
 * authenticity-specific endpoints for voting.
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

export function useAuthenticityEvaluation(scenarioId) {
  // State
  const items = ref([])
  const currentItem = ref(null)
  const currentItemIndex = ref(0)
  const messages = ref([])
  const content = ref('')
  const config = ref(null)
  const existingVote = ref(null)

  // Vote state
  const vote = ref(null) // 'real' or 'fake'
  const confidence = ref(50)
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
    const completed = items.value.filter(item => item.voted || item.evaluated).length
    const inProgress = items.value.filter(
      item => !item.voted && !item.evaluated && item.status === 'Progressing'
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

    // If has a vote
    if (vote.value || currentItem.value.voted || currentItem.value.evaluated) {
      return 'done'
    }

    // If has notes or confidence changed
    if (notes.value || confidence.value !== 50) {
      return 'in_progress'
    }

    return 'pending'
  })

  // Load scenario items via generic evaluation session endpoint
  async function loadItems() {
    loading.value = true
    error.value = null

    try {
      // Use the generic evaluation session endpoint
      const response = await axios.get(`/api/evaluation/session/${scenarioId.value}`)
      items.value = response.data.items || []
      config.value = response.data.config

      // Load first item if available
      if (items.value.length > 0 && !currentItem.value) {
        const firstItem = items.value[0]
        const itemId = firstItem.thread_id || firstItem.id || firstItem.item_id
        await loadItem(itemId)
      }
    } catch (err) {
      console.error('Failed to load authenticity items:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load items'
    } finally {
      loading.value = false
    }
  }

  // Load a specific item's content using authenticity endpoint
  async function loadItem(threadId) {
    error.value = null

    // Check cache first - if cached, apply immediately without loading state
    const cacheKey = String(threadId)
    if (itemCache.value[cacheKey]) {
      applyItemData(itemCache.value[cacheKey], threadId)
      return
    }

    loadingItem.value = true

    try {
      // Use the authenticity-specific endpoint to get thread details
      const response = await axios.get(`/api/email_threads/authenticity/${threadId}`)

      // Cache the response
      itemCache.value[cacheKey] = response.data

      applyItemData(response.data, threadId)
    } catch (err) {
      console.error('Failed to load item:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to load item'
    } finally {
      loadingItem.value = false
    }
  }

  // Helper to apply item data (used by loadItem and cache)
  function applyItemData(data, threadId) {
    currentItem.value = {
      thread_id: data.thread_id,
      subject: data.subject,
      sender: data.sender
    }
    messages.value = data.messages || []
    content.value = ''
    existingVote.value = data.vote

    // Initialize vote state from existing vote
    if (existingVote.value) {
      vote.value = existingVote.value.vote || null
      confidence.value = typeof existingVote.value.confidence === 'number'
        ? existingVote.value.confidence
        : 50
      notes.value = existingVote.value.notes || ''
    } else {
      vote.value = null
      confidence.value = 50
      notes.value = ''
    }

    // Update current index
    const index = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === threadId
    )
    if (index >= 0) {
      currentItemIndex.value = index
    }
  }

  // Get thread ID from current item
  function getThreadId() {
    if (!currentItem.value) return null
    return currentItem.value.thread_id || currentItem.value.id || currentItem.value.item_id
  }

  // Update cache with current vote state
  function updateCache() {
    const threadId = getThreadId()
    if (!threadId) return
    const cacheKey = String(threadId)
    if (itemCache.value[cacheKey]) {
      itemCache.value[cacheKey] = {
        ...itemCache.value[cacheKey],
        vote: {
          vote: vote.value,
          confidence: confidence.value,
          notes: notes.value || ''
        }
      }
    }
  }

  // Submit vote using authenticity endpoint
  async function submitVote(voteValue) {
    const threadId = getThreadId()
    if (!threadId) return { success: false, error: 'No item selected' }

    saving.value = true
    error.value = null

    try {
      // Use the authenticity-specific vote endpoint
      const response = await axios.post(
        `/api/email_threads/authenticity/${threadId}/vote`,
        {
          vote: voteValue,
          confidence: confidence.value,
          notes: notes.value || null
        }
      )

      vote.value = voteValue

      // Update cache with current state
      updateCache()

      // Update item status in list
      const itemIndex = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === threadId
      )
      if (itemIndex >= 0) {
        items.value[itemIndex].voted = true
        items.value[itemIndex].evaluated = true
        items.value[itemIndex].vote = voteValue
      }

      return { success: true, vote: response.data.vote }
    } catch (err) {
      console.error('Failed to submit vote:', err)
      error.value = err.response?.data?.error || err.response?.data?.message || 'Failed to save vote'
      return { success: false, error: error.value }
    } finally {
      saving.value = false
    }
  }

  // Save metadata (confidence, notes) using authenticity endpoint - debounced
  const saveMetadata = debounce(async () => {
    const threadId = getThreadId()
    if (!threadId) return

    saving.value = true
    try {
      // Use the authenticity-specific metadata endpoint
      await axios.patch(
        `/api/email_threads/authenticity/${threadId}/metadata`,
        {
          confidence: confidence.value,
          notes: notes.value || null
        }
      )

      // Update cache with current state
      updateCache()
    } catch (err) {
      console.error('Failed to save metadata:', err)
    } finally {
      saving.value = false
    }
  }, 800)

  // Navigation functions
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

  // Reset state
  function reset() {
    items.value = []
    currentItem.value = null
    currentItemIndex.value = 0
    messages.value = []
    content.value = ''
    config.value = null
    vote.value = null
    confidence.value = 50
    notes.value = ''
    existingVote.value = null
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
    vote,
    confidence,
    notes,
    existingVote,

    // Loading states
    loading,
    loadingItem,
    saving,
    error,

    // Computed
    progress,
    hasNext,
    hasPrev,
    currentItemStatus,

    // Methods
    loadItems,
    loadItem,
    submitVote,
    saveMetadata,
    goToItem,
    goNext,
    goPrev,
    reset
  }
}
