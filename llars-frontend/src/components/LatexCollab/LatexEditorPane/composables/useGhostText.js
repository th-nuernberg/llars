/**
 * useGhostText Composable
 *
 * Manages AI-powered ghost text (inline completion suggestions) for the LaTeX editor.
 * Ghost text appears as semi-transparent text at the cursor position, showing what
 * the AI predicts the user might type next.
 *
 * Features:
 * - Debounced completion requests (configurable delay)
 * - Tab to accept, Escape to dismiss
 * - Cursor validation (ghost text dismissed if cursor moves)
 * - Integration with Yjs for collaborative editing
 *
 * @module LatexEditorPane/composables/useGhostText
 *
 * @example
 * import { useGhostText } from './composables/useGhostText'
 *
 * const {
 *   ghostText,
 *   ghostTextPosition,
 *   setGhostText,
 *   acceptGhostText,
 *   cancelGhostText,
 *   scheduleGhostTextRequest
 * } = useGhostText({
 *   view,
 *   getYtext,
 *   ydoc,
 *   aiEnabled,
 *   ghostTextEnabled,
 *   ghostTextDelay,
 *   emitRequestCompletion,
 *   updateDecorations
 * })
 */

import { ref, onUnmounted } from 'vue'
import { AI_COLLAB_COLOR, AI_COLLAB_USERNAME } from '../constants'

/**
 * Creates a composable for managing AI ghost text completions.
 *
 * @param {Object} options - Configuration options
 * @param {import('vue').Ref<import('@codemirror/view').EditorView|null>} options.view - CodeMirror EditorView ref
 * @param {Function} options.getYtext - Function returning the Y.Text instance
 * @param {import('vue').Ref<import('yjs').Doc|null>} options.ydoc - Yjs document ref
 * @param {import('vue').Ref<boolean>} options.aiEnabled - Whether AI features are enabled
 * @param {import('vue').Ref<boolean>} options.ghostTextEnabled - Whether ghost text is enabled
 * @param {import('vue').Ref<number>} options.ghostTextDelay - Delay in ms before requesting completion
 * @param {Function} options.emitRequestCompletion - Function to emit completion request
 * @param {Function} options.updateDecorations - Function to update editor decorations
 * @param {Function} options.setSkipNextTextSync - Function to set skip sync flag
 *
 * @returns {Object} Ghost text state and methods
 */
export function useGhostText(options) {
  const {
    view,
    getYtext,
    ydoc,
    aiEnabled,
    ghostTextEnabled,
    ghostTextDelay,
    emitRequestCompletion,
    updateDecorations,
    setSkipNextTextSync
  } = options

  // =========================================================================
  // GHOST TEXT STATE
  // =========================================================================

  /**
   * The current ghost text content to display.
   * Empty string when no ghost text is shown.
   * @type {import('vue').Ref<string>}
   */
  const ghostText = ref('')

  /**
   * The document position where ghost text should appear.
   * Null when no ghost text is shown.
   * @type {import('vue').Ref<number|null>}
   */
  const ghostTextPosition = ref(null)

  /**
   * Timer for debouncing ghost text requests.
   * @type {number|null}
   */
  let ghostTextTimer = null

  // =========================================================================
  // GHOST TEXT FUNCTIONS
  // =========================================================================

  /**
   * Schedules a ghost text completion request after the configured delay.
   * Cancels any pending request before scheduling a new one.
   *
   * The request includes context around the cursor (500 chars before, 200 after)
   * with a [CURSOR] marker to indicate the insertion point.
   */
  function scheduleGhostTextRequest() {
    // Only request if both AI and ghost text are enabled
    if (!ghostTextEnabled.value || !aiEnabled.value || !view.value) return

    // Cancel any pending request
    cancelGhostText()

    // Schedule new request after delay
    ghostTextTimer = setTimeout(() => {
      if (!view.value) return

      const pos = view.value.state.selection.main.head
      const doc = view.value.state.doc

      // Get context around cursor position
      // 500 characters before for context, 200 after for trailing context
      const contextStart = Math.max(0, pos - 500)
      const contextEnd = Math.min(doc.length, pos + 200)
      const beforeCursor = doc.sliceString(contextStart, pos)
      const afterCursor = doc.sliceString(pos, contextEnd)
      const context = beforeCursor + '[CURSOR]' + afterCursor

      // Emit request for parent to handle via AI service
      emitRequestCompletion({
        context,
        cursorPosition: beforeCursor.length,
        documentPosition: pos
      })
    }, ghostTextDelay.value)
  }

  /**
   * Sets the ghost text to display at a specific position.
   * Validates that the cursor is still at the expected position.
   *
   * @param {string} text - The ghost text content to display
   * @param {number} position - The document position for the ghost text
   */
  function setGhostText(text, position) {
    if (!view.value || !text) {
      cancelGhostText()
      return
    }

    // Verify position is still valid (cursor hasn't moved)
    const currentPos = view.value.state.selection.main.head
    if (position !== currentPos) {
      // Cursor moved since request was made, don't show ghost text
      return
    }

    ghostText.value = text
    ghostTextPosition.value = position
    updateDecorations()
  }

  /**
   * Accepts the current ghost text, inserting it into the document.
   * The inserted text is marked as AI-generated for collaborative editing.
   *
   * @returns {boolean} True if ghost text was accepted, false if none available
   */
  function acceptGhostText() {
    const ytext = getYtext()
    if (!ghostText.value || ghostTextPosition.value === null || !view.value || !ytext) {
      return false
    }

    const text = ghostText.value
    const position = ghostTextPosition.value

    // Mark text as AI-generated with distinct collab attributes
    // This allows visual distinction of AI-contributed content
    const aiAttrs = { collabColor: AI_COLLAB_COLOR, collabUser: AI_COLLAB_USERNAME }

    // Insert via Yjs for collaborative sync
    setSkipNextTextSync(true)
    ydoc.value.transact(() => {
      ytext.insert(position, text, aiAttrs)
    }, 'ai')

    // Update CodeMirror view to reflect the change
    view.value.dispatch({
      changes: {
        from: position,
        to: position,
        insert: text
      },
      selection: { anchor: position + text.length }
    })

    // Clear ghost text state
    cancelGhostText()
    return true
  }

  /**
   * Cancels and clears any pending or displayed ghost text.
   * Clears the timer, resets state, and updates decorations.
   */
  function cancelGhostText() {
    // Clear pending request timer
    if (ghostTextTimer) {
      clearTimeout(ghostTextTimer)
      ghostTextTimer = null
    }

    // Reset ghost text state
    ghostText.value = ''
    ghostTextPosition.value = null

    // Update decorations to remove ghost text widget
    updateDecorations()
  }

  /**
   * Cleanup timer on component unmount to prevent memory leaks.
   */
  onUnmounted(() => {
    if (ghostTextTimer) {
      clearTimeout(ghostTextTimer)
      ghostTextTimer = null
    }
  })

  // =========================================================================
  // RETURN PUBLIC API
  // =========================================================================

  return {
    // State (read-only externally)
    ghostText,
    ghostTextPosition,

    // Methods
    scheduleGhostTextRequest,
    setGhostText,
    acceptGhostText,
    cancelGhostText
  }
}
