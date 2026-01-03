/**
 * LatexEditorPane Composables
 *
 * Re-exports all composables for cleaner imports.
 * These composables encapsulate specific functionality of the LaTeX editor:
 *
 * - useLatexToolbar: Formatting toolbar and snippet insertion
 * - useLatexCompletions: CodeMirror autocompletion sources
 * - useGhostText: AI ghost text completion suggestions
 * - useLatexDecorations: CodeMirror decorations management
 *
 * @module LatexEditorPane/composables
 *
 * @example
 * import {
 *   useLatexToolbar,
 *   useLatexCompletions,
 *   useGhostText,
 *   useLatexDecorations
 * } from './composables'
 */

export { useLatexToolbar } from './useLatexToolbar'
export { useLatexCompletions } from './useLatexCompletions'
export { useGhostText } from './useGhostText'
export { useLatexDecorations } from './useLatexDecorations'
