/**
 * useAIAgentActions - Agent actions that modify LaTeX documents
 *
 * Provides methods to:
 * - Replace title, abstract, sections
 * - Replace/insert text at positions
 * - All changes are attributed to "LLARS KI"
 */

import { ref } from 'vue'

// LLARS KI attribution colors
const AI_COLLAB_USER = 'LLARS KI'
const AI_COLLAB_COLOR = '#9B59B6' // Purple

export function useAIAgentActions(getEditorFn, documentContext) {
  const lastAction = ref(null)
  const actionHistory = ref([])

  /**
   * Get editor from getter function
   * @returns {Object|null} The editor instance or null
   */
  function getEditor() {
    // Call the getter function to get the current editor
    const editor = typeof getEditorFn === 'function' ? getEditorFn() : getEditorFn
    if (!editor) {
      console.warn('[useAIAgentActions] Editor not available')
      return null
    }
    // Verify editor has required methods
    if (typeof editor.replaceRange !== 'function') {
      console.warn('[useAIAgentActions] Editor missing replaceRange method')
      return null
    }
    return editor
  }

  /**
   * Replace text at a specific range
   * @param {number} from - Start position
   * @param {number} to - End position
   * @param {string} newText - Replacement text
   * @param {Object} options - Additional options
   */
  async function replaceRange(from, to, newText, options = {}) {
    const editor = getEditor()
    if (!editor || typeof editor.replaceRange !== 'function') {
      console.error('Editor replaceRange method not available')
      return { success: false, error: 'Editor not available' }
    }

    try {
      editor.replaceRange(from, to, newText, {
        collabUser: AI_COLLAB_USER,
        collabColor: AI_COLLAB_COLOR,
        ...options
      })

      // Highlight the change
      if (typeof editor.highlightRange === 'function') {
        editor.highlightRange(from, from + newText.length)
      }

      const action = {
        type: 'replace',
        from,
        to,
        oldText: options.oldText || '',
        newText,
        timestamp: Date.now()
      }
      actionHistory.value.push(action)
      lastAction.value = action

      return { success: true, from, to: from + newText.length }
    } catch (e) {
      console.error('Failed to replace range:', e)
      return { success: false, error: e.message }
    }
  }

  /**
   * Replace the document title
   * @param {string} newTitle - New title text
   */
  async function replaceTitle(newTitle) {
    if (!documentContext) {
      return { success: false, error: 'Document context not available' }
    }

    const titlePos = documentContext.findTitlePosition()
    if (!titlePos) {
      return { success: false, error: 'No \\title{} found in document' }
    }

    const newTitleCommand = `\\title{${newTitle}}`
    return replaceRange(titlePos.from, titlePos.to, newTitleCommand, {
      oldText: titlePos.content
    })
  }

  /**
   * Replace the document abstract
   * @param {string} newAbstract - New abstract text
   */
  async function replaceAbstract(newAbstract) {
    if (!documentContext) {
      return { success: false, error: 'Document context not available' }
    }

    const abstractPos = documentContext.findAbstractPosition()
    if (!abstractPos) {
      return { success: false, error: 'No \\begin{abstract}...\\end{abstract} found' }
    }

    // Replace just the content, keeping the begin/end tags
    const newAbstractFull = `\\begin{abstract}\n${newAbstract}\n\\end{abstract}`
    return replaceRange(abstractPos.from, abstractPos.to, newAbstractFull, {
      oldText: abstractPos.content
    })
  }

  /**
   * Replace the current selection
   * @param {string} newText - Replacement text
   */
  async function replaceSelection(newText) {
    const editor = getEditor()
    if (!editor) {
      return { success: false, error: 'Editor not available' }
    }

    let from, to
    if (typeof editor.getSelectionRange === 'function') {
      const range = editor.getSelectionRange()
      from = range.from
      to = range.to
    } else if (documentContext?.selectionRange?.value) {
      from = documentContext.selectionRange.value.from
      to = documentContext.selectionRange.value.to
    }

    if (from === undefined || to === undefined || from === to) {
      return { success: false, error: 'No text selected' }
    }

    const oldText = documentContext?.selectionText?.value || ''
    return replaceRange(from, to, newText, { oldText })
  }

  /**
   * Insert text at the current cursor position
   * @param {string} text - Text to insert
   */
  async function insertAtCursor(text) {
    const editor = getEditor()
    if (!editor) {
      return { success: false, error: 'Editor not available' }
    }

    let position
    if (typeof editor.getSelectionRange === 'function') {
      const range = editor.getSelectionRange()
      position = range.from
    }

    if (position === undefined) {
      return { success: false, error: 'Cursor position not available' }
    }

    return replaceRange(position, position, text)
  }

  /**
   * Insert text after a specific section
   * @param {string} sectionTitle - Section title to insert after
   * @param {string} text - Text to insert
   */
  async function insertAfterSection(sectionTitle, text) {
    if (!documentContext) {
      return { success: false, error: 'Document context not available' }
    }

    const sections = documentContext.sections?.value || []
    const sectionIndex = sections.findIndex(s => s.title === sectionTitle)

    if (sectionIndex === -1) {
      return { success: false, error: `Section "${sectionTitle}" not found` }
    }

    // Find the end of this section (start of next section or end of document)
    let insertPosition
    if (sectionIndex < sections.length - 1) {
      insertPosition = sections[sectionIndex + 1].index
    } else {
      // Insert before \end{document} or at end
      const content = documentContext.content?.value || ''
      const endDocMatch = content.match(/\\end\{document\}/)
      insertPosition = endDocMatch ? endDocMatch.index : content.length
    }

    return replaceRange(insertPosition, insertPosition, `\n\n${text}\n`)
  }

  /**
   * Apply a quick action result (rewrite, expand, summarize, etc.)
   * @param {string} actionType - Type of action
   * @param {string} result - Result text to apply
   * @param {Object} targetRange - Optional target range {from, to}
   */
  async function applyQuickAction(actionType, result, targetRange = null) {
    if (targetRange && targetRange.from !== undefined && targetRange.to !== undefined) {
      return replaceRange(targetRange.from, targetRange.to, result)
    }

    // Default: replace selection
    return replaceSelection(result)
  }

  /**
   * Copy text to clipboard
   * @param {string} text - Text to copy
   */
  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text)
      return { success: true }
    } catch (e) {
      console.error('Failed to copy to clipboard:', e)
      return { success: false, error: e.message }
    }
  }

  /**
   * Get action history for display
   */
  function getActionHistory() {
    return actionHistory.value
  }

  /**
   * Clear action history
   */
  function clearHistory() {
    actionHistory.value = []
    lastAction.value = null
  }

  return {
    // State
    lastAction,
    actionHistory,

    // Core actions
    replaceRange,
    replaceSelection,
    insertAtCursor,

    // Document-specific actions
    replaceTitle,
    replaceAbstract,
    insertAfterSection,

    // Utility actions
    applyQuickAction,
    copyToClipboard,

    // History
    getActionHistory,
    clearHistory,

    // Constants
    AI_COLLAB_USER,
    AI_COLLAB_COLOR
  }
}

export default useAIAgentActions
