/**
 * useLatexCompletions Composable
 *
 * Provides CodeMirror autocompletion sources for LaTeX editing.
 * Supports two types of completions:
 * 1. LaTeX commands and environments (\\begin, \\section, etc.)
 * 2. AI @-commands for the AI-enabled editor (@ai, @rewrite, etc.)
 *
 * The completions are context-aware:
 * - Inside \\begin{} or \\end{}: suggests environment names
 * - After backslash: suggests LaTeX commands
 * - After @: suggests AI commands (when AI is enabled)
 *
 * @module LatexEditorPane/composables/useLatexCompletions
 *
 * @example
 * import { useLatexCompletions } from './composables/useLatexCompletions'
 *
 * const { latexCompletionSource, aiCompletionSource } = useLatexCompletions({
 *   aiEnabled: ref(true)
 * })
 *
 * // Use in CodeMirror autocompletion extension
 * autocompletion({
 *   override: aiEnabled.value
 *     ? [aiCompletionSource, latexCompletionSource]
 *     : [latexCompletionSource]
 * })
 */

import {
  LATEX_COMMAND_COMPLETIONS,
  LATEX_ENVIRONMENT_NAMES,
  AI_COMMAND_COMPLETIONS
} from '../constants'

/**
 * Creates autocompletion sources for the LaTeX editor.
 *
 * @param {Object} options - Configuration options
 * @param {import('vue').Ref<boolean>} options.aiEnabled - Whether AI features are enabled
 *
 * @returns {Object} Completion source functions
 * @returns {Function} return.latexCompletionSource - Completion source for LaTeX commands
 * @returns {Function} return.aiCompletionSource - Completion source for AI @-commands
 */
export function useLatexCompletions(options) {
  const { aiEnabled } = options

  /**
   * LaTeX command and environment completion source.
   *
   * Provides context-aware completions for:
   * - Environment names inside \\begin{} and \\end{}
   * - LaTeX commands after backslash (\\)
   *
   * @param {import('@codemirror/autocomplete').CompletionContext} context - CodeMirror completion context
   * @returns {import('@codemirror/autocomplete').CompletionResult|null} Completion options or null
   *
   * @example
   * // User types: \begin{fig
   * // Suggests: figure, float, etc.
   *
   * // User types: \sec
   * // Suggests: \section, \subsection, etc.
   */
  function latexCompletionSource(context) {
    // Check if we're inside an environment declaration
    // Pattern: \begin{ or \end{ followed by partial environment name
    const envMatch = context.matchBefore(/\\(begin|end)\{[A-Za-z]*$/)
    if (envMatch) {
      // Find position after the opening brace
      const braceIndex = envMatch.text.lastIndexOf('{')
      const from = braceIndex >= 0 ? envMatch.from + braceIndex + 1 : envMatch.from

      // Don't show completions if cursor is at brace without explicit request
      if (from === context.pos && !context.explicit) return null

      // Map environment names to completion options
      const options = LATEX_ENVIRONMENT_NAMES.map((env) => ({
        label: env,
        type: 'keyword',
        apply: env
      }))

      return {
        from,
        options,
        validFor: /^[A-Za-z]*$/
      }
    }

    // Check for LaTeX command (backslash followed by letters)
    const word = context.matchBefore(/\\[A-Za-z]*$/)
    if (!word || (word.from === word.to && !context.explicit)) return null

    return {
      from: word.from,
      options: LATEX_COMMAND_COMPLETIONS,
      validFor: /^\\[A-Za-z]*$/
    }
  }

  /**
   * AI @-command completion source.
   *
   * Provides completions for AI commands in the AI-enabled editor.
   * Only active when aiEnabled is true.
   *
   * @param {import('@codemirror/autocomplete').CompletionContext} context - CodeMirror completion context
   * @returns {import('@codemirror/autocomplete').CompletionResult|null} Completion options or null
   *
   * @example
   * // User types: @re
   * // Suggests: @rewrite, @ref (if available)
   */
  function aiCompletionSource(context) {
    // Only provide AI completions when AI features are enabled
    if (!aiEnabled.value) return null

    // Match @-commands: @ followed by optional letters
    const word = context.matchBefore(/@[A-Za-z]*$/)
    if (!word || (word.from === word.to && !context.explicit)) return null

    return {
      from: word.from,
      options: AI_COMMAND_COMPLETIONS,
      validFor: /^@[A-Za-z]*$/
    }
  }

  /**
   * Handles Enter key to execute @-commands.
   *
   * When the cursor is on a line starting with an @-command,
   * this function parses the command and emits it for the parent
   * component to handle.
   *
   * Command format: @command [args]
   *
   * @param {import('@codemirror/view').EditorView} editorView - CodeMirror editor view
   * @param {Function} emitAiCommand - Function to emit parsed AI command
   * @param {boolean} isAiEnabled - Whether AI features are enabled
   * @returns {boolean} True if command was executed, false otherwise
   *
   * @example
   * // Line: "@rewrite make it formal"
   * // Emits: { command: 'rewrite', args: 'make it formal', ... }
   */
  function handleEnterForAICommand(editorView, emitAiCommand, isAiEnabled) {
    if (!isAiEnabled) return false

    // Get current line content
    const { state } = editorView
    const pos = state.selection.main.head
    const line = state.doc.lineAt(pos)
    const lineText = line.text.trim()

    // Check if line starts with @-command
    // Pattern: @command [optional args]
    const cmdMatch = lineText.match(/^@(\w+)(?:\s+(.*))?$/)
    if (!cmdMatch) return false

    const command = cmdMatch[1].toLowerCase()
    const args = (cmdMatch[2] || '').trim()

    // Get selected text if any (for commands that operate on selection)
    const sel = state.selection.main
    const selectedText = sel.from !== sel.to ? state.doc.sliceString(sel.from, sel.to) : ''

    // Commands that require text to work on
    const selectionCommands = ['rewrite', 'expand', 'summarize', 'fix', 'translate', 'cite']

    // If command needs selection but none provided, don't execute
    if (selectionCommands.includes(command) && !selectedText && !args) {
      return false
    }

    // Emit command for parent to handle via AI service
    emitAiCommand({
      command,
      args,
      selectedText,
      lineFrom: line.from,
      lineTo: line.to
    })

    return true // Prevent default Enter behavior
  }

  // =========================================================================
  // RETURN PUBLIC API
  // =========================================================================

  return {
    latexCompletionSource,
    aiCompletionSource,
    handleEnterForAICommand
  }
}
