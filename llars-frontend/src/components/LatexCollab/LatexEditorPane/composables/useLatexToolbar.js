/**
 * useLatexToolbar Composable
 *
 * Manages the LaTeX formatting toolbar state and provides snippet insertion
 * functionality. Handles toolbar collapse state, table size picker, and
 * inserting formatted LaTeX snippets at the cursor position.
 *
 * Features:
 * - Persistent toolbar collapse state (localStorage)
 * - Table size picker with configurable rows/columns
 * - Snippet insertion with placeholder support ($CURSOR$, $SEL$)
 * - Wrap mode for surrounding selected text
 *
 * @module LatexEditorPane/composables/useLatexToolbar
 *
 * @example
 * import { useLatexToolbar } from './composables/useLatexToolbar'
 *
 * const {
 *   toolbarCollapsed,
 *   toggleToolbar,
 *   insertSnippet,
 *   // ... table picker state
 * } = useLatexToolbar({
 *   view,      // CodeMirror EditorView ref
 *   ytext,     // Yjs Y.Text instance
 *   ydoc,      // Yjs Y.Doc ref
 *   username,
 *   collabColor,
 *   socket,
 *   users,
 *   readonly
 * })
 */

import { ref, computed } from 'vue'
import { generateTableSnippet } from '../constants'

/** LocalStorage key for toolbar collapse state */
const TOOLBAR_COLLAPSED_KEY = 'latex-toolbar-collapsed'

/**
 * Creates a composable for managing the LaTeX toolbar.
 *
 * @param {Object} options - Configuration options
 * @param {import('vue').Ref<import('@codemirror/view').EditorView|null>} options.view - CodeMirror EditorView ref
 * @param {Function} options.getYtext - Function returning the Y.Text instance
 * @param {import('vue').Ref<import('yjs').Doc|null>} options.ydoc - Yjs document ref
 * @param {import('vue').Ref<string>} options.username - Current user's username
 * @param {import('vue').Ref<string>} options.collabColor - User's collaboration color
 * @param {import('vue').Ref<Object|null>} options.socket - Socket.IO instance ref
 * @param {import('vue').Ref<Object>} options.users - Active users map ref
 * @param {import('vue').Ref<boolean>} options.readonly - Whether editor is read-only
 * @param {Function} options.setSkipNextTextSync - Function to set skip sync flag
 *
 * @returns {Object} Toolbar state and methods
 */
export function useLatexToolbar(options) {
  const {
    view,
    getYtext,
    ydoc,
    username,
    collabColor,
    socket,
    users,
    readonly,
    setSkipNextTextSync
  } = options

  // =========================================================================
  // TOOLBAR STATE
  // =========================================================================

  /**
   * Whether the toolbar is collapsed.
   * Default: collapsed unless user explicitly expanded it before.
   * @type {import('vue').Ref<boolean>}
   */
  const toolbarCollapsed = ref(localStorage.getItem(TOOLBAR_COLLAPSED_KEY) !== 'false')

  /**
   * Toggles toolbar collapsed state and persists to localStorage.
   */
  function toggleToolbar() {
    toolbarCollapsed.value = !toolbarCollapsed.value
    localStorage.setItem(TOOLBAR_COLLAPSED_KEY, toolbarCollapsed.value)
  }

  // =========================================================================
  // TABLE SIZE PICKER
  // =========================================================================

  /**
   * Whether the table size picker menu is open.
   * @type {import('vue').Ref<boolean>}
   */
  const showTablePicker = ref(false)

  /**
   * Number of rows for the table to be inserted.
   * @type {import('vue').Ref<number>}
   */
  const tableRows = ref(3)

  /**
   * Number of columns for the table to be inserted.
   * @type {import('vue').Ref<number>}
   */
  const tableCols = ref(3)

  /**
   * Inserts a table with the configured dimensions.
   * Uses the generateTableSnippet function to create the LaTeX code.
   */
  function insertTable() {
    const snippet = generateTableSnippet(tableRows.value, tableCols.value)
    insertSnippet(snippet, false)
    showTablePicker.value = false
  }

  // =========================================================================
  // SNIPPET INSERTION
  // =========================================================================

  /**
   * Gets the current user's collaboration color.
   * Falls back to socket-assigned color or default teal.
   *
   * @returns {string} Hex color code
   */
  function getUserColor() {
    let userColor = collabColor.value
    if (!userColor && socket.value?.id && users.value?.[socket.value.id]) {
      userColor = users.value[socket.value.id].color
    }
    if (!userColor) {
      userColor = '#4ECDC4' // Fallback teal
    }
    return userColor
  }

  /**
   * Inserts a LaTeX snippet at the current cursor position.
   *
   * Supports two placeholder types:
   * - $CURSOR$ : Where the cursor should be positioned after insertion
   * - $SEL$    : Replaced with selected text (for wrap mode)
   *
   * @param {string} snippet - The LaTeX snippet to insert
   * @param {boolean} [wrap=false] - If true, wrap selected text with the snippet
   *
   * @example
   * // Insert a section header
   * insertSnippet('\\section{$CURSOR$}\n', false)
   *
   * // Wrap selected text in bold
   * insertSnippet('\\textbf{$SEL$}', true)
   */
  function insertSnippet(snippet, wrap = false) {
    const ytext = getYtext()
    if (!view.value || !ytext || readonly.value) return

    const state = view.value.state
    const sel = state.selection.main
    const selectedText = sel.from !== sel.to ? state.doc.sliceString(sel.from, sel.to) : ''

    let insertText = snippet
    let cursorOffset = 0

    if (wrap && selectedText) {
      // Replace $SEL$ with the selected text
      insertText = snippet.replace(/\$SEL\$/g, selectedText)
      // Cursor goes to end of insertion
      cursorOffset = insertText.length
    } else if (wrap) {
      // No selection, but wrap mode - replace $SEL$ with empty and position cursor there
      const selPos = snippet.indexOf('$SEL$')
      if (selPos !== -1) {
        insertText = snippet.replace(/\$SEL\$/g, '')
        cursorOffset = selPos
      } else {
        cursorOffset = insertText.length
      }
    } else {
      // Replace $CURSOR$ placeholder and position cursor there
      const cursorPos = snippet.indexOf('$CURSOR$')
      if (cursorPos !== -1) {
        insertText = snippet.replace(/\$CURSOR\$/g, '')
        cursorOffset = cursorPos
      } else {
        cursorOffset = insertText.length
      }
    }

    // Get user color for collab highlighting
    const userColor = getUserColor()
    const userAttrs = { collabColor: userColor, collabUser: username.value }

    // Insert via Yjs for collaborative sync
    setSkipNextTextSync(true)
    ydoc.value.transact(() => {
      // Delete selection if any
      if (sel.from !== sel.to) {
        ytext.delete(sel.from, sel.to - sel.from)
      }
      // Insert the snippet with user attributes
      ytext.insert(sel.from, insertText, userAttrs)
    }, 'cm')

    // Update CodeMirror view
    const newCursorPos = sel.from + cursorOffset
    view.value.dispatch({
      changes: {
        from: sel.from,
        to: sel.to,
        insert: insertText
      },
      selection: { anchor: newCursorPos }
    })

    // Focus the editor after insertion
    view.value.focus()
  }

  // =========================================================================
  // RETURN PUBLIC API
  // =========================================================================

  return {
    // Toolbar state
    toolbarCollapsed,
    toggleToolbar,

    // Table picker
    showTablePicker,
    tableRows,
    tableCols,
    insertTable,

    // Snippet insertion
    insertSnippet,
    getUserColor
  }
}
