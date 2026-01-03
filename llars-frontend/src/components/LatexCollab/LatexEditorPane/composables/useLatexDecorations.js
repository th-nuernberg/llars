/**
 * useLatexDecorations Composable
 *
 * Manages CodeMirror decorations for the LaTeX collaborative editor.
 * Handles multiple types of visual overlays:
 *
 * 1. Git Diff Highlighting - Shows inserted/deleted text compared to baseline
 * 2. Remote Cursors - Shows other users' cursor positions and selections
 * 3. Comment Ranges - Highlights text ranges with associated comments
 * 4. Collab Activity - Shows recent edits by other users (line border)
 * 5. Ghost Text - Displays AI completion suggestions
 *
 * @module LatexEditorPane/composables/useLatexDecorations
 *
 * @example
 * import { useLatexDecorations } from './composables/useLatexDecorations'
 *
 * const {
 *   decorationsField,
 *   setDecorations,
 *   updateDecorations,
 *   deletedLinesRef
 * } = useLatexDecorations({
 *   view,
 *   getYtext,
 *   ydoc,
 *   yhighlights,
 *   remoteCursors,
 *   ghostText,
 *   ghostTextPosition,
 *   comments,
 *   activeCommentId,
 *   username,
 *   // ... git diff functions from useGitDiff
 * })
 */

import { ref } from 'vue'
import * as Y from 'yjs'
import { StateEffect, StateField, RangeSet } from '@codemirror/state'
import { Decoration, gutter } from '@codemirror/view'
import { CaretWidget, GhostTextWidget, deletionMarkerInstance } from '../widgets'

/**
 * Creates a composable for managing CodeMirror decorations.
 *
 * @param {Object} options - Configuration options
 * @param {import('vue').Ref<import('@codemirror/view').EditorView|null>} options.view - CodeMirror EditorView ref
 * @param {Function} options.getYtext - Function returning the Y.Text instance
 * @param {import('vue').Ref<import('yjs').Doc|null>} options.ydoc - Yjs document ref
 * @param {Function} options.getYhighlights - Function returning the Y.Map for highlights
 * @param {import('vue').Ref<Object>} options.remoteCursors - Remote user cursors
 * @param {import('vue').Ref<string>} options.ghostText - Current ghost text content
 * @param {import('vue').Ref<number|null>} options.ghostTextPosition - Ghost text position
 * @param {import('vue').Ref<Array>} options.comments - Document comments
 * @param {import('vue').Ref<number|null>} options.activeCommentId - Currently selected comment
 * @param {import('vue').Ref<string>} options.username - Current user's username
 * @param {import('vue').Ref<Object>} options.documentProps - Document props (for ID)
 * @param {Function} options.computeCharacterDiffs - Git diff function
 * @param {Function} options.getInsertRanges - Git diff function
 * @param {Function} options.diffsToDecorations - Git diff function
 * @param {Function} options.hasChanges - Git diff function
 * @param {Function} options.getChangeSummary - Git diff function
 * @param {Function} options.emitGitSummary - Function to emit git summary
 *
 * @returns {Object} Decoration state and methods
 */
export function useLatexDecorations(options) {
  const {
    view,
    getYtext,
    ydoc,
    getYhighlights,
    remoteCursors,
    ghostText,
    ghostTextPosition,
    comments,
    activeCommentId,
    username,
    documentProps,
    computeCharacterDiffs,
    getInsertRanges,
    diffsToDecorations,
    hasChanges,
    getChangeSummary,
    emitGitSummary
  } = options

  // =========================================================================
  // DECORATION STATE
  // =========================================================================

  /**
   * Tracks deleted line numbers for gutter markers.
   * @type {import('vue').Ref<Set<number>>}
   */
  const deletedLinesRef = ref(new Set())

  /**
   * Flag to prevent recursive decoration updates.
   * @type {boolean}
   */
  let applyingDecorations = false

  // =========================================================================
  // STATE EFFECT AND FIELD
  // =========================================================================

  /**
   * StateEffect for setting decorations in CodeMirror.
   * @type {import('@codemirror/state').StateEffectType<import('@codemirror/view').DecorationSet>}
   */
  const setDecorations = StateEffect.define()

  /**
   * StateField that maintains the current decoration set.
   * Maps decorations through document changes to keep them in sync.
   *
   * @type {import('@codemirror/state').StateField<import('@codemirror/view').DecorationSet>}
   */
  const decorationsField = StateField.define({
    create() {
      return Decoration.none
    },
    update(deco, tr) {
      // Map existing decorations through document changes
      let next = deco.map(tr.changes)
      // Apply any setDecorations effects
      for (const e of tr.effects) {
        if (e.is(setDecorations)) next = e.value
      }
      return next
    },
    provide: f => view.decorations.from(f)
  })

  // =========================================================================
  // HELPER FUNCTIONS
  // =========================================================================

  /**
   * Clamps a position to valid document bounds.
   *
   * @param {number} pos - Position to clamp
   * @param {number} max - Maximum valid position (document length)
   * @returns {number} Clamped position
   */
  function clampPos(pos, max) {
    if (typeof pos !== 'number' || Number.isNaN(pos)) return 0
    return Math.max(0, Math.min(pos, max))
  }

  /**
   * Converts a hex color to rgba with specified alpha.
   *
   * @param {string} hex - Hex color code (e.g., '#FF6B6B')
   * @param {number} [alpha=0.18] - Alpha value (0-1)
   * @returns {string} RGBA color string
   */
  function rgbaFromHex(hex, alpha = 0.18) {
    if (!hex || typeof hex !== 'string') return `rgba(0,0,0,${alpha})`
    const raw = hex.replace('#', '')
    if (raw.length !== 6) return `rgba(0,0,0,${alpha})`
    const r = parseInt(raw.slice(0, 2), 16)
    const g = parseInt(raw.slice(2, 4), 16)
    const b = parseInt(raw.slice(4, 6), 16)
    return `rgba(${r},${g},${b},${alpha})`
  }

  /**
   * Validates if a string is a valid hex color.
   *
   * @param {string} value - Value to check
   * @returns {boolean} True if valid hex color
   */
  function isValidHexColor(value) {
    return typeof value === 'string' && /^#[0-9a-fA-F]{6}$/.test(value)
  }

  // =========================================================================
  // DECORATION BUILDERS
  // =========================================================================

  /**
   * Builds decorations for inserted text ranges with user colors.
   * Merges Yjs collab attributes with git insert ranges to show
   * who made each insertion with their collaboration color.
   *
   * @param {Array<{from: number, to: number}>} insertRanges - Ranges of inserted text
   * @returns {Array<import('@codemirror/view').Range<import('@codemirror/view').Decoration>>}
   */
  function buildInsertDecorations(insertRanges = []) {
    const ytext = getYtext()
    if (!ytext || !view.value || insertRanges.length === 0) return []

    const decorations = []
    let pos = 0
    let rangeIndex = 0
    const delta = ytext.toDelta()
    const docLen = view.value.state.doc.length

    // Iterate through Yjs delta operations
    for (const op of delta) {
      const insert = op?.insert
      const text = typeof insert === 'string' ? insert : ''
      const length = text.length
      const attrs = op?.attributes || {}
      const color = attrs.collabColor || attrs.color
      if (length === 0) continue

      const segmentStart = pos
      const segmentEnd = pos + length

      // Skip insert ranges that end before this segment
      while (rangeIndex < insertRanges.length && insertRanges[rangeIndex].to <= segmentStart) {
        rangeIndex += 1
      }

      // Find overlapping insert ranges
      let idx = rangeIndex
      while (idx < insertRanges.length && insertRanges[idx].from < segmentEnd) {
        const range = insertRanges[idx]
        const overlapFrom = Math.max(segmentStart, range.from)
        const overlapTo = Math.min(segmentEnd, range.to)

        if (overlapFrom < overlapTo) {
          const safeFrom = clampPos(overlapFrom, docLen)
          const safeTo = clampPos(overlapTo, docLen)

          if (safeFrom < safeTo) {
            if (isValidHexColor(color)) {
              // Use user's collab color for highlighting
              const background = rgbaFromHex(color, 0.35)
              const outline = rgbaFromHex(color, 0.5)
              decorations.push(
                Decoration.mark({
                  attributes: {
                    style: `background: ${background}; border-radius: 2px; box-shadow: 0 0 0 1px ${outline}; text-decoration: underline; text-decoration-color: ${color}; text-underline-offset: 2px;`
                  }
                }).range(safeFrom, safeTo)
              )
            } else {
              // Fallback to generic insert styling
              decorations.push(
                Decoration.mark({ class: 'cm-diff-insert' }).range(safeFrom, safeTo)
              )
            }
          }
        }

        if (range.to <= segmentEnd) {
          idx += 1
        } else {
          break
        }
      }

      rangeIndex = idx
      pos += length
    }

    return decorations
  }

  /**
   * Builds decorations for comment ranges in the document.
   *
   * @returns {Array<import('@codemirror/view').Range<import('@codemirror/view').Decoration>>}
   */
  function buildCommentDecorations() {
    if (!view.value) return []
    const list = Array.isArray(comments.value) ? comments.value : []
    if (!list.length) return []

    const decos = []
    const docLen = view.value.state.doc.length

    for (const comment of list) {
      if (!comment) continue
      const from = clampPos(comment.range_start, docLen)
      const to = clampPos(comment.range_end, docLen)
      if (from >= to) continue

      // Build CSS classes based on comment state
      const classes = ['cm-comment-range']
      if (comment.resolved_at) classes.push('cm-comment-range-resolved')
      if (comment.id === activeCommentId.value) classes.push('cm-comment-range-active')

      decos.push(
        Decoration.mark({
          class: classes.join(' '),
          attributes: { 'data-comment-id': String(comment.id || '') }
        }).range(from, to)
      )
    }

    return decos
  }

  // =========================================================================
  // MAIN UPDATE FUNCTION
  // =========================================================================

  /**
   * Updates all decorations in the editor.
   * Combines multiple decoration sources into a single decoration set.
   *
   * Called when:
   * - Document content changes
   * - Remote cursors update
   * - Comments change
   * - Ghost text changes
   * - Collab highlights update
   */
  function updateDecorations() {
    if (!view.value) return
    if (applyingDecorations) return

    const decorations = []
    const ytext = getYtext()
    const yhighlights = getYhighlights()

    // -----------------------------------------------------------------------
    // 1. COLLAB HIGHLIGHTS (LINE ACTIVITY INDICATORS)
    // -----------------------------------------------------------------------

    // Convert Yjs Map to plain object for processing
    const highlightsData = {}
    if (yhighlights) {
      try {
        yhighlights.forEach((value, key) => {
          highlightsData[key] = value
        })
      } catch {
        // yhighlights might not be iterable yet
      }
    }

    // -----------------------------------------------------------------------
    // 2. GIT DIFF DECORATIONS
    // -----------------------------------------------------------------------

    const currentContent = view.value.state.doc.toString()
    const diffs = computeCharacterDiffs(currentContent)
    const insertRanges = getInsertRanges(diffs)

    // Build insert decorations with user colors
    const insertDecorations = buildInsertDecorations(insertRanges)

    // Build deletion markers for gutter
    if (diffs.length > 0) {
      const { decorations: diffDecos, deletedLines } = diffsToDecorations(
        diffs,
        view.value,
        null,
        { includeInsertDecorations: false }
      )
      decorations.push(...diffDecos)
      deletedLinesRef.value = deletedLines
    } else {
      deletedLinesRef.value = new Set()
    }

    if (insertDecorations.length > 0) {
      decorations.push(...insertDecorations)
    }

    // -----------------------------------------------------------------------
    // 3. COMMENT DECORATIONS
    // -----------------------------------------------------------------------

    const commentDecorations = buildCommentDecorations()
    if (commentDecorations.length > 0) {
      decorations.push(...commentDecorations)
    }

    // -----------------------------------------------------------------------
    // 4. REAL-TIME ACTIVITY INDICATORS
    // -----------------------------------------------------------------------

    // Show subtle left border for lines recently edited by other users
    const now = Date.now()
    const HIGHLIGHT_DURATION_MS = 15000 // 15 seconds
    const myUsername = username.value

    for (const [lineNoStr, meta] of Object.entries(highlightsData)) {
      if (!meta || !meta.ts || !meta.color) continue

      // Only show other users' recent edits (not own edits)
      if (meta.username === myUsername) continue
      if (now - meta.ts > HIGHLIGHT_DURATION_MS) continue

      const lineNo = parseInt(lineNoStr, 10)
      if (isNaN(lineNo) || lineNo < 1 || lineNo > view.value.state.doc.lines) continue

      try {
        const line = view.value.state.doc.line(lineNo)
        // Subtle left border - NO background to not interfere with character highlighting
        decorations.push(
          Decoration.line({
            attributes: {
              style: `border-left: 3px solid ${meta.color}; margin-left: -3px;`
            }
          }).range(line.from)
        )
      } catch {
        // Line might not exist
      }
    }

    // -----------------------------------------------------------------------
    // 5. REMOTE CURSOR DECORATIONS
    // -----------------------------------------------------------------------

    const docLen = view.value.state.doc.length
    for (const [userId, cursor] of Object.entries(remoteCursors.value || {})) {
      if (!cursor || cursor.blockId != String(documentProps.value.id) || !cursor.range) continue
      const color = cursor.color || '#FF6B6B'

      // Decode relative positions if available (prevents cursor drift)
      let from, to
      if (cursor.range.fromRel && cursor.range.toRel && ytext && ydoc.value) {
        try {
          const fromRelPos = Y.decodeRelativePosition(new Uint8Array(cursor.range.fromRel))
          const toRelPos = Y.decodeRelativePosition(new Uint8Array(cursor.range.toRel))

          const fromAbsPos = Y.createAbsolutePositionFromRelativePosition(fromRelPos, ydoc.value)
          const toAbsPos = Y.createAbsolutePositionFromRelativePosition(toRelPos, ydoc.value)

          from = fromAbsPos?.index ?? cursor.range.from
          to = toAbsPos?.index ?? cursor.range.to
        } catch {
          // Fallback to absolute positions
          from = cursor.range.from
          to = cursor.range.to
        }
      } else {
        // Use absolute positions (backwards compatibility)
        from = cursor.range.from
        to = cursor.range.to
      }

      from = clampPos(from, docLen)
      to = clampPos(to, docLen)

      // Add selection highlight if there's a range
      if (from !== to) {
        decorations.push(
          Decoration.mark({
            attributes: { style: `background:${rgbaFromHex(color, 0.12)}; border-radius:4px;` }
          }).range(Math.min(from, to), Math.max(from, to))
        )
      }

      // Add caret widget at cursor position
      decorations.push(
        Decoration.widget({
          widget: new CaretWidget(color, cursor.username),
          side: 1
        }).range(to)
      )
    }

    // -----------------------------------------------------------------------
    // 6. GHOST TEXT DECORATION
    // -----------------------------------------------------------------------

    if (ghostText.value && ghostTextPosition.value !== null && ghostTextPosition.value <= docLen) {
      decorations.push(
        Decoration.widget({
          widget: new GhostTextWidget(ghostText.value),
          side: 1
        }).range(ghostTextPosition.value)
      )
    }

    // -----------------------------------------------------------------------
    // APPLY ALL DECORATIONS
    // -----------------------------------------------------------------------

    const decoSet = Decoration.set(decorations, true)
    applyingDecorations = true
    try {
      view.value.dispatch({ effects: setDecorations.of(decoSet) })
    } finally {
      applyingDecorations = false
    }

    // -----------------------------------------------------------------------
    // EMIT GIT SUMMARY
    // -----------------------------------------------------------------------

    const summary = getChangeSummary(diffs)
    emitGitSummary({
      users: [],
      totalChangedLines: summary.changes > 0 ? Math.ceil(summary.changes / 40) : 0,
      insertions: summary.insertions,
      deletions: summary.deletions,
      hasChanges: hasChanges(currentContent)
    })
  }

  // =========================================================================
  // DIFF GUTTER
  // =========================================================================

  /**
   * Creates a gutter extension for showing deleted lines.
   *
   * @returns {import('@codemirror/view').Extension} Gutter extension
   */
  function createDiffGutter() {
    return gutter({
      class: 'cm-diff-gutter',
      markers: (editorView) => {
        const markers = []
        for (const lineNo of deletedLinesRef.value) {
          if (lineNo >= 1 && lineNo <= editorView.state.doc.lines) {
            const line = editorView.state.doc.line(lineNo)
            markers.push(deletionMarkerInstance.range(line.from))
          }
        }
        return RangeSet.of(markers, true)
      }
    })
  }

  // =========================================================================
  // RETURN PUBLIC API
  // =========================================================================

  return {
    // State
    deletedLinesRef,

    // CodeMirror extensions
    decorationsField,
    setDecorations,
    createDiffGutter,

    // Methods
    updateDecorations,
    clampPos,
    rgbaFromHex,
    isValidHexColor
  }
}
