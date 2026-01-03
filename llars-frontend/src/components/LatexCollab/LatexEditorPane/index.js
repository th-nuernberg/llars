/**
 * LatexEditorPane Module
 *
 * Exports the main component and all shared utilities for the LaTeX editor.
 * This module provides a collaborative LaTeX editing experience with:
 *
 * - Real-time collaboration via Yjs
 * - Git-like diff visualization
 * - AI completion suggestions (ghost text)
 * - Rich formatting toolbar
 * - Comment annotations
 *
 * @module LatexEditorPane
 *
 * @example
 * // Import the main component
 * import LatexEditorPane from '@/components/LatexCollab/LatexEditorPane'
 *
 * // Or import specific utilities
 * import {
 *   LATEX_COMMAND_COMPLETIONS,
 *   TEXT_FORMAT_BUTTONS,
 *   useLatexToolbar
 * } from '@/components/LatexCollab/LatexEditorPane'
 */

// Re-export main component (default export from .vue file)
export { default } from '../LatexEditorPane.vue'

// Re-export constants for external use
export * from './constants'

// Re-export widgets for custom extensions
export * from './widgets'

// Re-export composables for custom editor implementations
export * from './composables'
