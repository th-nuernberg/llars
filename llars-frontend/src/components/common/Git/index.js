/**
 * Common Git Components
 *
 * Shared Git UI components for use across different workspace types
 * (LaTeX Collab, Prompt Engineering, Markdown Collab, etc.)
 *
 * These components are designed to be workspace-agnostic and can be
 * configured via props for different API endpoints and features.
 */

export { default as GitDetailDialog } from './GitDetailDialog.vue'
export { default as GitStatusWidget } from './GitStatusWidget.vue'
export { default as DiffViewer } from './DiffViewer.vue'
