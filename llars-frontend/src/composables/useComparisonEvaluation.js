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
  // Per-case timing: ms from item display to the A/B choice save (sent with the
  // vote so exports carry time-on-case). Backend is first-write-only.
  const itemShownAt = ref(null)

  // State
  const items = ref([])
  const currentItem = ref(null)
  const currentItemIndex = ref(0)
  const config = ref(null)
  const existingComparison = ref(null)

  // Option content (the two candidate replies for A/B vote)
  const optionA = ref({ messages: [], content: '' })
  const optionB = ref({ messages: [], content: '' })

  // Conversation context (shown above A/B for Turing-Test-style scenarios:
  // dialogue-up-to-now, then 2 candidate next-turn replies as A/B).
  const contextMessages = ref([])
  const contextSubject = ref('')

  // Per-item research metadata from EvaluationItem.metadata_json.
  // Used for {{variable}} substitution in the scenario task description.
  const currentItemMeta = ref({})

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

  // Gamification: reward-popup config + milestone trigger.
  // Toggles + thresholds come from the scenario's config_json (set in the
  // wizard via ComparisonConfigEditor). Defaults match the Pydantic schema.
  // `milestoneEvent` is set in `selectOption` after a successful POST and
  // cleared by the consumer (ComparisonInterface.vue closes the dialog and
  // calls `clearMilestone()`).
  const milestoneEvent = ref(null) // { count, isFirst } | null

  // Pull a comparison-config field from any of the three places the wizard,
  // the seeders and legacy clients store it:
  //   1. `config_json.eval_config.config.<key>`  (wizard, modern flow)
  //   2. `config_json.<key>`                      (some seeders)
  //   3. `config_json.<snake_case_key>`           (Pydantic round-trips)
  // Returns the first defined value, or `undefined`.
  function readCfgField(...keys) {
    const cfg = config.value || {}
    const evalCfg = cfg?.eval_config?.config || {}
    for (const k of keys) {
      if (evalCfg[k] !== undefined) return evalCfg[k]
      if (cfg[k] !== undefined) return cfg[k]
    }
    return undefined
  }

  const gamification = computed(() => {
    const enabled =
      readCfgField('gamificationEnabled', 'gamification_enabled') === true
    const first = readCfgField(
      'gamificationFirstMilestone',
      'gamification_first_milestone'
    )
    const recurring = readCfgField(
      'gamificationRecurringMilestone',
      'gamification_recurring_milestone'
    )
    return {
      enabled,
      first: Number.isFinite(Number(first)) ? Number(first) : 10,
      recurring: Number.isFinite(Number(recurring)) ? Number(recurring) : 5
    }
  })

  // Items remaining until the next milestone fires — drives the
  // motivation badge in ComparisonInterface header. Returns null when
  // gamification is off or no further milestone is reachable.
  const itemsUntilNextMilestone = computed(() => {
    const g = gamification.value
    if (!g.enabled) return null
    const completed = items.value.filter(it => it.evaluated).length
    const { first, recurring } = g
    if (completed < first) return first - completed
    if (recurring <= 0) return null
    const since = completed - first
    const into = since % recurring
    return into === 0 ? recurring : recurring - into
  })

  // True for the *next* unevaluated card whenever submitting it would hit a
  // milestone — used to apply the .milestone-frame highlight before the click.
  const isMilestoneCard = computed(() => {
    if (!gamification.value.enabled) return false
    const completed = items.value.filter(item => item.evaluated).length
    const next = completed + 1
    const { first, recurring } = gamification.value
    if (!first || first < 1) return false
    if (next === first) return true
    if (next > first && recurring > 0 && (next - first) % recurring === 0) return true
    return false
  })

  function clearMilestone() {
    milestoneEvent.value = null
  }

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

    // Start the per-case timer when the item becomes visible.
    itemShownAt.value = Date.now()

    // For comparison scenarios, features represent the two options.
    // Fallback: TEXT_PAIR imports store the two options as messages.
    const features = data.features || []
    const messages = data.messages || []

    // Reset context — only populated for "context + 2 candidates" layout below
    contextMessages.value = []
    contextSubject.value = data.subject || ''
    currentItemMeta.value = data.metadata_json || {}

    if (features.length >= 2) {
      // Two layouts share this branch:
      // (a) Turing-Test layout: messages = dialogue context up to now,
      //     features[0/1] = candidate next-turn replies (rendered above A/B)
      // (b) Standalone layout: only features, no surrounding dialogue
      // We always treat features[0/1] as A/B and surface messages — if any —
      // as conversation context to the UI.
      contextMessages.value = messages
      optionA.value = {
        messages: [],
        content: features[0]?.content || '',
        model: features[0]?.model_name || features[0]?.model_id || 'Option A'
      }
      optionB.value = {
        messages: [],
        content: features[1]?.content || '',
        model: features[1]?.model_name || features[1]?.model_id || 'Option B'
      }
    } else if (messages.length >= 2) {
      // Fallback: messages represent comparison options (wizard TEXT_PAIR import)
      // Split messages evenly between Option A and Option B
      const midpoint = Math.ceil(messages.length / 2)
      optionA.value = {
        messages: messages.slice(0, midpoint),
        content: ''
      }
      optionB.value = {
        messages: messages.slice(midpoint),
        content: ''
      }
    } else if (features.length === 1) {
      // Single feature as Option A, messages as context for Option B
      optionA.value = {
        messages: [],
        content: features[0]?.content || '',
        model: features[0]?.model_name || 'Option A'
      }
      optionB.value = {
        messages: messages,
        content: ''
      }
    } else {
      // Last resort: whatever content is available goes to Option A
      optionA.value = { messages: messages, content: '' }
      optionB.value = { messages: [], content: '' }
    }

    // Restore existing comparison evaluation if available
    const existing = data.existing_comparison
    if (existing && existing.choice) {
      existingComparison.value = existing
      selectedOption.value = existing.choice
      notes.value = existing.notes || ''
    } else {
      existingComparison.value = null
      selectedOption.value = null
      notes.value = ''
    }

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
          notes: notes.value || null,
          time_on_item_ms: itemShownAt.value ? Date.now() - itemShownAt.value : null
        }
      )

      selectedOption.value = option

      // Update cache with current state
      updateCache()

      const itemIndex = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === itemId
      )
      const wasEvaluated = itemIndex >= 0 ? items.value[itemIndex].evaluated : false
      if (itemIndex >= 0) {
        items.value[itemIndex].evaluated = true
      }

      // Fire a milestone event only on the *first* time this item is
      // evaluated — re-saving an existing choice should not retrigger the
      // popup. The threshold is checked against the new completed count.
      if (gamification.value.enabled && !wasEvaluated) {
        const completed = items.value.filter(it => it.evaluated).length
        const { first, recurring } = gamification.value
        const isFirst = completed === first
        const isRecurring =
          completed > first && recurring > 0 && (completed - first) % recurring === 0
        if (isFirst || isRecurring) {
          milestoneEvent.value = { count: completed, isFirst }
        }
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

  /**
   * Persist the rater's free-text note.
   *
   * This used to be an empty stub whose comment claimed "notes are saved with
   * the option selection". That is only true for a note typed BEFORE choosing:
   * selectOption() sends the current text along. A note added or edited AFTER
   * the choice reached nothing — the dialog closed, the call chain ran, and the
   * text was silently dropped.
   *
   * There is no notes-only endpoint because ItemComparisonEvaluation.choice is
   * NOT NULL: a note without a decision cannot be represented. So this re-sends
   * the EXISTING choice together with the new text. Without a choice yet the
   * text stays in memory and rides along with the upcoming selectOption().
   */
  const saveMetadata = debounce(async () => {
    const itemId = getItemId()
    if (!itemId || !selectedOption.value) return
    try {
      await axios.post(
        `/api/evaluation/session/${scenarioId.value}/items/${itemId}/evaluate`,
        {
          function_type: 'comparison',
          choice: selectedOption.value,
          notes: notes.value || null
        }
      )
      updateCache()
    } catch (e) {
      error.value = e.response?.data?.error || 'Failed to save note'
    }
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
    contextMessages.value = []
    contextSubject.value = ''
    currentItemMeta.value = {}
    config.value = null
    selectedOption.value = null
    notes.value = ''
    existingComparison.value = null
    error.value = null
    milestoneEvent.value = null
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
    contextMessages,
    contextSubject,
    currentItemMeta,
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
    gamification,
    isMilestoneCard,
    itemsUntilNextMilestone,
    milestoneEvent,
    clearMilestone,
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
