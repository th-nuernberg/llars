/**
 * useAICompletion Composable
 *
 * Manages ghost text completion state and logic.
 */

import { ref, computed } from 'vue'
import aiWritingService from '@/services/aiWritingService'

export function useAICompletion() {
  // State
  const ghostText = ref('')
  const alternatives = ref([])
  const currentAlternativeIndex = ref(0)
  const isLoading = ref(false)
  const error = ref(null)
  const lastCursorPosition = ref(0)

  // Debounce timer
  let debounceTimer = null
  const DEBOUNCE_DELAY = 500 // ms

  // Computed
  const hasGhostText = computed(() => ghostText.value.length > 0)
  const hasAlternatives = computed(() => alternatives.value.length > 1)

  /**
   * Request a completion with debouncing
   * @param {string} context - Text around cursor
   * @param {number} cursorPosition - Position in context
   * @param {string} documentType - 'latex' or 'markdown'
   */
  function requestCompletion(context, cursorPosition, documentType = 'latex') {
    // Clear previous timer
    if (debounceTimer) {
      clearTimeout(debounceTimer)
    }

    // Don't request if context is too short
    if (context.length < 10) {
      clearGhostText()
      return
    }

    lastCursorPosition.value = cursorPosition

    // Debounce the request
    debounceTimer = setTimeout(async () => {
      await fetchCompletion(context, cursorPosition, documentType)
    }, DEBOUNCE_DELAY)
  }

  /**
   * Cancel pending completion request
   */
  function cancelRequest() {
    if (debounceTimer) {
      clearTimeout(debounceTimer)
      debounceTimer = null
    }
  }

  /**
   * Fetch completion from API
   * @param {string} context - Text around cursor
   * @param {number} cursorPosition - Position in context
   * @param {string} documentType - Document type
   */
  async function fetchCompletion(context, cursorPosition, documentType) {
    isLoading.value = true
    error.value = null

    try {
      const result = await aiWritingService.complete({
        context,
        cursor_position: cursorPosition,
        document_type: documentType,
        max_tokens: 100,
        temperature: 0.3
      })

      if (result.success && result.completion) {
        ghostText.value = result.completion
        alternatives.value = [result.completion, ...(result.alternatives || [])]
        currentAlternativeIndex.value = 0
      } else {
        clearGhostText()
      }
    } catch (e) {
      error.value = e.message
      clearGhostText()
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Trigger manual completion (Ctrl+Space)
   * @param {string} context - Text around cursor
   * @param {number} cursorPosition - Position in context
   * @param {string} documentType - Document type
   */
  async function triggerManualCompletion(context, cursorPosition, documentType = 'latex') {
    cancelRequest()
    lastCursorPosition.value = cursorPosition
    await fetchCompletion(context, cursorPosition, documentType)
  }

  /**
   * Accept current ghost text
   * @returns {string} The accepted text
   */
  function acceptGhostText() {
    const accepted = ghostText.value
    clearGhostText()
    return accepted
  }

  /**
   * Reject/dismiss ghost text
   */
  function rejectGhostText() {
    clearGhostText()
  }

  /**
   * Cycle to next alternative (Alt+])
   */
  function nextAlternative() {
    if (!hasAlternatives.value) return

    currentAlternativeIndex.value = (currentAlternativeIndex.value + 1) % alternatives.value.length
    ghostText.value = alternatives.value[currentAlternativeIndex.value]
  }

  /**
   * Cycle to previous alternative (Alt+[)
   */
  function previousAlternative() {
    if (!hasAlternatives.value) return

    currentAlternativeIndex.value = (currentAlternativeIndex.value - 1 + alternatives.value.length) % alternatives.value.length
    ghostText.value = alternatives.value[currentAlternativeIndex.value]
  }

  /**
   * Clear all ghost text state
   */
  function clearGhostText() {
    ghostText.value = ''
    alternatives.value = []
    currentAlternativeIndex.value = 0
  }

  /**
   * Check if cursor moved (invalidates ghost text)
   * @param {number} newPosition - New cursor position
   * @returns {boolean} Whether ghost text should be cleared
   */
  function shouldClearOnCursorMove(newPosition) {
    // If cursor moved beyond where ghost text would be inserted
    return newPosition !== lastCursorPosition.value
  }

  return {
    // State
    ghostText,
    alternatives,
    currentAlternativeIndex,
    isLoading,
    error,
    lastCursorPosition,

    // Computed
    hasGhostText,
    hasAlternatives,

    // Methods
    requestCompletion,
    cancelRequest,
    triggerManualCompletion,
    acceptGhostText,
    rejectGhostText,
    nextAlternative,
    previousAlternative,
    clearGhostText,
    shouldClearOnCursorMove
  }
}

export default useAICompletion
