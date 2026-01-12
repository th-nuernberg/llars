/**
 * useAIChat Composable
 *
 * Manages AI chat state and interactions for the AI Writing Assistant.
 */

import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import aiWritingService from '@/services/aiWritingService'

export function useAIChat() {
  const { t } = useI18n()

  // State
  const messages = ref([])
  const isLoading = ref(false)
  const error = ref(null)
  const currentStreamingMessage = ref('')

  // Computed
  const hasMessages = computed(() => messages.value.length > 0)

  const historyForAPI = computed(() => {
    return messages.value.map(msg => ({
      role: msg.role,
      content: msg.content
    }))
  })

  /**
   * Send a message to the AI chat
   * @param {string} message - User message
   * @param {string} documentContent - Current document content for context
   * @param {boolean} stream - Whether to stream the response
   * @returns {Promise<Object>} Response with message and artifacts
   */
  async function sendMessage(message, documentContent = '', stream = false) {
    if (!message.trim()) return null

    error.value = null
    isLoading.value = true

    // Add user message
    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: message,
      timestamp: new Date()
    }
    messages.value.push(userMessage)

    try {
      if (stream) {
        // Streaming response
        currentStreamingMessage.value = ''
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: '',
          artifacts: [],
          timestamp: new Date()
        }
        messages.value.push(assistantMessage)

        const result = await aiWritingService.streamChat(
          {
            message,
            document_content: documentContent,
            history: historyForAPI.value.slice(0, -2) // Exclude current messages
          },
          (delta, done) => {
            currentStreamingMessage.value += delta
            // Update the last message
            const lastMsg = messages.value[messages.value.length - 1]
            if (lastMsg.role === 'assistant') {
              lastMsg.content = currentStreamingMessage.value
            }
          }
        )

        // Update with final artifacts
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg.role === 'assistant') {
          lastMsg.artifacts = result.artifacts || []
        }

        return result
      } else {
        // Non-streaming response
        const result = await aiWritingService.chat({
          message,
          document_content: documentContent,
          history: historyForAPI.value.slice(0, -1) // Exclude current message
        })

        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: result.response,
          artifacts: result.artifacts || [],
          timestamp: new Date()
        }
        messages.value.push(assistantMessage)

        return result
      }
    } catch (e) {
      error.value = e.message || t('latexCollabAi.errors.chatFailed')
      // Remove failed user message
      messages.value = messages.value.filter(m => m.id !== userMessage.id)
      throw e
    } finally {
      isLoading.value = false
      currentStreamingMessage.value = ''
    }
  }

  /**
   * Execute an @-command
   * @param {string} command - Command name
   * @param {string} args - Command arguments
   * @param {string} selectedText - Selected text
   * @param {string} documentContent - Document content
   * @returns {Promise<Object>} Command result
   */
  async function executeCommand(command, args, selectedText, documentContent) {
    isLoading.value = true
    error.value = null

    try {
      const result = await aiWritingService.executeCommand({
        command,
        args,
        selected_text: selectedText,
        document_content: documentContent
      })

      // Add command result as messages
      messages.value.push({
        id: Date.now(),
        role: 'user',
        content: `@${command} ${args}`.trim(),
        timestamp: new Date()
      })

      messages.value.push({
        id: Date.now() + 1,
        role: 'assistant',
        content: result.response,
        artifacts: result.artifacts || [],
        timestamp: new Date()
      })

      return result
    } catch (e) {
      error.value = e.message || t('latexCollabAi.errors.commandFailed')
      throw e
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Clear chat history
   */
  function clearHistory() {
    messages.value = []
    error.value = null
  }

  /**
   * Remove a specific message
   * @param {number} messageId - Message ID to remove
   */
  function removeMessage(messageId) {
    messages.value = messages.value.filter(m => m.id !== messageId)
  }

  return {
    // State
    messages,
    isLoading,
    error,
    currentStreamingMessage,

    // Computed
    hasMessages,
    historyForAPI,

    // Methods
    sendMessage,
    executeCommand,
    clearHistory,
    removeMessage
  }
}

export default useAIChat
