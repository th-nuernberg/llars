/**
 * useAIEditor Composable
 *
 * Provides AI-powered editor features:
 * - @-command autocompletion and execution
 * - Ghost text completion (inline suggestions)
 * - AI-powered text operations
 *
 * @module LatexCollabAI/composables/useAIEditor
 */

import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import aiWritingService from '@/services/aiWritingService'

// Import shared constants from LatexEditorPane module
// These are used across both LaTeX and LaTeX AI editors
import {
  AI_COLLAB_COLOR,
  AI_COLLAB_USERNAME,
  AI_COMMAND_COMPLETIONS
} from '@/components/LatexCollab/LatexEditorPane/constants'

// Re-export for consumers of this composable
export { AI_COLLAB_COLOR, AI_COLLAB_USERNAME }

export function useAIEditor() {
  const { t } = useI18n()

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

  const aiCommandDescriptions = computed(() => ({
    '@ai': t('latexCollabAi.commandDescriptions.ai'),
    '@rewrite': t('latexCollabAi.commandDescriptions.rewrite'),
    '@expand': t('latexCollabAi.commandDescriptions.expand'),
    '@summarize': t('latexCollabAi.commandDescriptions.summarize'),
    '@fix': t('latexCollabAi.commandDescriptions.fix'),
    '@translate': t('latexCollabAi.commandDescriptions.translate'),
    '@cite': t('latexCollabAi.commandDescriptions.cite'),
    '@abstract': t('latexCollabAi.commandDescriptions.abstract'),
    '@titles': t('latexCollabAi.commandDescriptions.titles')
  }))

  const aiCommands = computed(() => (
    AI_COMMAND_COMPLETIONS.map(cmd => ({
      ...cmd,
      type: 'ai',
      info: aiCommandInfo.value[cmd.label] || cmd.info,
      description: aiCommandDescriptions.value[cmd.label] || ''
    }))
  ))

  // State
  const isProcessing = ref(false)
  const lastError = ref(null)
  const ghostText = ref('')
  const ghostTextPosition = ref(null)
  const showGhostText = ref(false)

  // Ghost text completion settings
  const completionEnabled = ref(true)
  const completionDelay = ref(800) // ms before triggering completion
  let completionTimer = null

  /**
   * Get AI command completions for CodeMirror autocompletion
   * @param {Object} context - CodeMirror completion context
   * @returns {Object|null} Completion result
   */
  function aiCommandCompletionSource(context) {
    // Match @-commands at word boundary
    const word = context.matchBefore(/@[A-Za-z]*$/)
    if (!word || (word.from === word.to && !context.explicit)) return null

    return {
      from: word.from,
      options: aiCommands.value.map(cmd => ({
        label: cmd.label,
        type: 'text',
        info: cmd.info,
        detail: cmd.description,
        apply: (view, completion, from, to) => {
          // Replace @command with placeholder for argument
          const text = cmd.label === '@ai' ? cmd.label + ' ' : cmd.label + ' '
          view.dispatch({
            changes: { from, to, insert: text },
            selection: { anchor: from + text.length }
          })
        }
      })),
      validFor: /^@[A-Za-z]*$/
    }
  }

  /**
   * Parse @-command from text
   * @param {string} text - Line text
   * @returns {Object|null} Parsed command { command, args, fullMatch }
   */
  function parseCommand(text) {
    const match = text.match(/^@(\w+)(?:\s+(.*))?$/)
    if (!match) return null
    return {
      command: match[1].toLowerCase(),
      args: (match[2] || '').trim(),
      fullMatch: match[0]
    }
  }

  /**
   * Execute an @-command
   * @param {string} command - Command name (without @)
   * @param {string} args - Command arguments
   * @param {string} selectedText - Currently selected text
   * @param {string} documentContent - Full document content
   * @returns {Promise<Object>} Result with response and artifacts
   */
  async function executeCommand(command, args, selectedText, documentContent) {
    isProcessing.value = true
    lastError.value = null

    try {
      const result = await aiWritingService.executeCommand({
        command,
        args,
        selected_text: selectedText,
        document_content: documentContent
      })

      return result
    } catch (e) {
      lastError.value = e.message || t('latexCollabAi.errors.processingFailed')
      throw e
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * Request ghost text completion at cursor position
   * @param {string} context - Text around cursor
   * @param {number} cursorPosition - Position in context
   * @returns {Promise<string>} Suggested completion
   */
  async function requestCompletion(context, cursorPosition) {
    if (!completionEnabled.value) return ''

    try {
      const result = await aiWritingService.complete({
        context,
        cursor_position: cursorPosition,
        document_type: 'latex',
        max_tokens: 100,
        temperature: 0.3
      })

      if (result.completion) {
        return result.completion
      }
      return ''
    } catch (e) {
      console.warn('[AIEditor] Completion failed:', e)
      return ''
    }
  }

  /**
   * Schedule ghost text completion after typing pause
   * @param {Object} view - CodeMirror view
   * @param {Function} callback - Callback with completion text
   */
  function scheduleCompletion(view, callback) {
    if (completionTimer) {
      clearTimeout(completionTimer)
    }

    if (!completionEnabled.value) return

    completionTimer = setTimeout(async () => {
      const pos = view.state.selection.main.head
      const doc = view.state.doc

      // Get context around cursor (500 chars before, 200 after)
      const contextStart = Math.max(0, pos - 500)
      const contextEnd = Math.min(doc.length, pos + 200)
      const beforeCursor = doc.sliceString(contextStart, pos)
      const afterCursor = doc.sliceString(pos, contextEnd)
      const context = beforeCursor + '[CURSOR]' + afterCursor

      const completion = await requestCompletion(context, beforeCursor.length)
      if (completion && callback) {
        callback(completion, pos)
      }
    }, completionDelay.value)
  }

  /**
   * Cancel pending completion
   */
  function cancelCompletion() {
    if (completionTimer) {
      clearTimeout(completionTimer)
      completionTimer = null
    }
    ghostText.value = ''
    showGhostText.value = false
  }

  /**
   * Accept ghost text completion
   * @param {Object} view - CodeMirror view
   */
  function acceptCompletion(view) {
    if (!ghostText.value || ghostTextPosition.value === null) return false

    view.dispatch({
      changes: {
        from: ghostTextPosition.value,
        to: ghostTextPosition.value,
        insert: ghostText.value
      },
      selection: { anchor: ghostTextPosition.value + ghostText.value.length }
    })

    cancelCompletion()
    return true
  }

  /**
   * Rewrite selected text
   * @param {string} text - Text to rewrite
   * @param {string} style - Style (academic, concise, expanded, simplified)
   * @param {string} context - Surrounding context
   * @returns {Promise<string>} Rewritten text
   */
  async function rewriteText(text, style = 'academic', context = '') {
    isProcessing.value = true
    try {
      const result = await aiWritingService.rewrite({
        text,
        style,
        context
      })
      return result.result
    } catch (e) {
      lastError.value = e.message
      throw e
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * Expand text with more details
   * @param {string} text - Text to expand
   * @param {string} context - Surrounding context
   * @returns {Promise<string>} Expanded text
   */
  async function expandText(text, context = '') {
    isProcessing.value = true
    try {
      const result = await aiWritingService.expand({
        text,
        context
      })
      return result.result
    } catch (e) {
      lastError.value = e.message
      throw e
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * Summarize text
   * @param {string} text - Text to summarize
   * @returns {Promise<string>} Summarized text
   */
  async function summarizeText(text) {
    isProcessing.value = true
    try {
      const result = await aiWritingService.summarize({
        text
      })
      return result.result
    } catch (e) {
      lastError.value = e.message
      throw e
    } finally {
      isProcessing.value = false
    }
  }

  /**
   * Fix LaTeX errors in content
   * @param {string} content - LaTeX content
   * @returns {Promise<Object>} Errors and suggestions
   */
  async function fixLatex(content) {
    isProcessing.value = true
    try {
      const result = await aiWritingService.fixLatex(content)
      return result
    } catch (e) {
      lastError.value = e.message
      throw e
    } finally {
      isProcessing.value = false
    }
  }

  // Cleanup
  function cleanup() {
    cancelCompletion()
  }

  return {
    // State
    isProcessing,
    lastError,
    ghostText,
    ghostTextPosition,
    showGhostText,
    completionEnabled,
    completionDelay,

    // Constants
    AI_COMMANDS: aiCommands.value,
    AI_COLLAB_COLOR,
    AI_COLLAB_USERNAME,

    // Autocompletion
    aiCommandCompletionSource,
    parseCommand,

    // Command execution
    executeCommand,

    // Ghost text completion
    requestCompletion,
    scheduleCompletion,
    cancelCompletion,
    acceptCompletion,

    // Text operations
    rewriteText,
    expandText,
    summarizeText,
    fixLatex,

    // Cleanup
    cleanup
  }
}

export default useAIEditor
