/**
 * LatexEditorPane Widgets
 *
 * CodeMirror widget classes for collaborative editing and AI features.
 * These widgets are rendered inline in the editor to show:
 * - Remote user cursors and selections
 * - AI-generated ghost text suggestions
 * - Git diff deletion markers in the gutter
 *
 * @module LatexEditorPane/widgets
 */

import { WidgetType, GutterMarker } from '@codemirror/view'

let deletionMarkerLabel = 'Deleted text'

/**
 * Remote Caret Widget
 *
 * Displays a colored vertical caret to indicate where another user's
 * cursor is positioned in the document. Used for real-time collaboration
 * to show other users' editing positions.
 *
 * @class CaretWidget
 * @extends WidgetType
 *
 * @example
 * // Create a caret widget for a remote user
 * const widget = new CaretWidget('#FF6B6B', 'Alice')
 * // The widget renders as a colored vertical line with the username as tooltip
 */
export class CaretWidget extends WidgetType {
  /**
   * Creates a new CaretWidget instance.
   *
   * @param {string} color - CSS color for the caret (e.g., '#FF6B6B')
   * @param {string} label - Username to display as tooltip
   */
  constructor(color, label) {
    super()
    /** @type {string} CSS color for the caret border */
    this.color = color
    /** @type {string} Username displayed as tooltip */
    this.label = label
  }

  /**
   * Creates the DOM element for the caret.
   *
   * @returns {HTMLElement} Span element styled as a vertical caret
   */
  toDOM() {
    const wrap = document.createElement('span')
    wrap.className = 'remote-caret'
    wrap.style.borderLeftColor = this.color
    wrap.title = this.label || ''
    return wrap
  }
}

/**
 * Ghost Text Widget
 *
 * Displays semi-transparent "ghost" text for AI completion suggestions.
 * The ghost text appears at the cursor position and can be accepted
 * with Tab or dismissed with Escape.
 *
 * Styling:
 * - Gray color (#9e9e9e) with 70% opacity
 * - Italic font style
 * - Non-interactive (pointer-events: none)
 *
 * @class GhostTextWidget
 * @extends WidgetType
 *
 * @example
 * // Create ghost text suggesting " function() {"
 * const widget = new GhostTextWidget(' function() {')
 * // User presses Tab to accept, Escape to dismiss
 */
export class GhostTextWidget extends WidgetType {
  /**
   * Creates a new GhostTextWidget instance.
   *
   * @param {string} text - The suggested text to display
   */
  constructor(text) {
    super()
    /** @type {string} The ghost text content */
    this.text = text
  }

  /**
   * Creates the DOM element for the ghost text.
   *
   * @returns {HTMLElement} Span element with ghost text styling
   */
  toDOM() {
    const span = document.createElement('span')
    span.className = 'ghost-text-suggestion'
    span.textContent = this.text
    // Inline styles for ghost text appearance
    span.style.cssText = `
      color: #9e9e9e;
      opacity: 0.7;
      font-style: italic;
      pointer-events: none;
      user-select: none;
    `
    return span
  }

  /**
   * Checks if two ghost text widgets are equal.
   * Used by CodeMirror to optimize re-rendering.
   *
   * @param {GhostTextWidget} other - Another widget to compare
   * @returns {boolean} True if both widgets have the same text
   */
  eq(other) {
    return other.text === this.text
  }
}

/**
 * Deletion Marker (Gutter)
 *
 * A gutter marker that shows a red indicator for lines where text
 * has been deleted compared to the git baseline. This provides
 * visual feedback for git diff changes in the editor gutter.
 *
 * @class DeletionMarker
 * @extends GutterMarker
 *
 * @example
 * // Mark line 42 as having deleted content
 * markers.push(deletionMarkerInstance.range(line.from))
 */
export class DeletionMarker extends GutterMarker {
  /**
   * Creates the DOM element for the deletion marker.
   *
   * @returns {HTMLElement} Div element styled as a red indicator
   */
  toDOM() {
    const el = document.createElement('div')
    el.className = 'cm-diff-delete-gutter'
    el.title = deletionMarkerLabel
    return el
  }
}

/**
 * Singleton instance of DeletionMarker.
 * Reused across all deletion markers for efficiency.
 *
 * @type {DeletionMarker}
 */
export const deletionMarkerInstance = new DeletionMarker()

export function setDeletionMarkerLabel(label) {
  deletionMarkerLabel = label
}
