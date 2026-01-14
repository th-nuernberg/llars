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

import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
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
  const { t } = useI18n()

  const latexCommandInfo = computed(() => ({
    '\\documentclass': t('latexCollab.completions.documentclass'),
    '\\usepackage': t('latexCollab.completions.usepackage'),
    '\\begin': t('latexCollab.completions.begin'),
    '\\end': t('latexCollab.completions.end'),
    '\\section': t('latexCollab.completions.section'),
    '\\subsection': t('latexCollab.completions.subsection'),
    '\\subsubsection': t('latexCollab.completions.subsubsection'),
    '\\paragraph': t('latexCollab.completions.paragraph'),
    '\\textbf': t('latexCollab.completions.textbf'),
    '\\textit': t('latexCollab.completions.textit'),
    '\\emph': t('latexCollab.completions.emph'),
    '\\underline': t('latexCollab.completions.underline'),
    '\\item': t('latexCollab.completions.item'),
    '\\label': t('latexCollab.completions.label'),
    '\\ref': t('latexCollab.completions.ref'),
    '\\pageref': t('latexCollab.completions.pageref'),
    '\\cite': t('latexCollab.completions.cite'),
    '\\citet': t('latexCollab.completions.citet'),
    '\\citep': t('latexCollab.completions.citep'),
    '\\includegraphics': t('latexCollab.completions.includegraphics'),
    '\\caption': t('latexCollab.completions.caption'),
    '\\centering': t('latexCollab.completions.centering'),
    '\\footnote': t('latexCollab.completions.footnote'),
    '\\url': t('latexCollab.completions.url'),
    '\\href': t('latexCollab.completions.href'),
    '\\title': t('latexCollab.completions.title'),
    '\\author': t('latexCollab.completions.author'),
    '\\date': t('latexCollab.completions.date'),
    '\\maketitle': t('latexCollab.completions.maketitle'),
    '\\tableofcontents': t('latexCollab.completions.tableofcontents'),
    '\\newcommand': t('latexCollab.completions.newcommand'),
    '\\renewcommand': t('latexCollab.completions.renewcommand'),
    '\\input': t('latexCollab.completions.input'),
    '\\include': t('latexCollab.completions.include'),
    '\\frac': t('latexCollab.completions.frac'),
    '\\sqrt': t('latexCollab.completions.sqrt'),
    '\\sum': t('latexCollab.completions.sum'),
    '\\int': t('latexCollab.completions.int')
  }))

  const localizedLatexCommands = computed(() => (
    LATEX_COMMAND_COMPLETIONS.map(cmd => ({
      ...cmd,
      info: latexCommandInfo.value[cmd.label] || cmd.info
    }))
  ))

  const aiCommandInfo = computed(() => ({
    '@ai': t('latexCollab.aiCommands.ai'),
    '@rewrite': t('latexCollab.aiCommands.rewrite'),
    '@expand': t('latexCollab.aiCommands.expand'),
    '@summarize': t('latexCollab.aiCommands.summarize'),
    '@fix': t('latexCollab.aiCommands.fix'),
    '@translate': t('latexCollab.aiCommands.translate'),
    '@cite': t('latexCollab.aiCommands.cite'),
    '@abstract': t('latexCollab.aiCommands.abstract'),
    '@titles': t('latexCollab.aiCommands.titles')
  }))

  const localizedAiCommands = computed(() => (
    AI_COMMAND_COMPLETIONS.map(cmd => ({
      ...cmd,
      info: aiCommandInfo.value[cmd.label] || cmd.info
    }))
  ))

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
      options: localizedLatexCommands.value,
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
      options: localizedAiCommands.value,
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
