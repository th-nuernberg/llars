/**
 * useChatMessages.js
 * Composable for managing chat message operations
 */
import { ref } from 'vue'
import axios from 'axios'

export function useChatMessages() {
  const isProcessing = ref(false)
  const currentSources = ref([])

  /**
   * Add a user message to the messages array
   */
  function addUserMessage(messages, content, files = []) {
    const userMsgObj = {
      id: Date.now(),
      content: content || (files.length > 0 ? '(Dateien hochgeladen)' : ''),
      sender: 'user',
      timestamp: new Date().toLocaleTimeString(),
      files: files.map(f => ({
        filename: f.name,
        type: getFileType(f.name)
      }))
    }
    messages.value.push(userMsgObj)
    return userMsgObj
  }

  /**
   * Add a placeholder bot message for streaming responses
   */
  function addBotPlaceholder(messages) {
    const botMsgObj = {
      id: Date.now() + 1,
      content: '',
      sender: 'bot',
      timestamp: '',
      streaming: true
    }
    messages.value.push(botMsgObj)
    return botMsgObj
  }

  /**
   * Update the last bot message with content and metadata
   */
  function updateBotMessage(messages, content, timestamp, streaming = false, sources = null) {
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx] = {
        ...messages.value[lastIdx],
        content,
        timestamp,
        streaming,
        ...(sources && { sources })
      }
    }
  }

  /**
   * Update the last bot message with an error
   */
  function setBotError(messages, errorMessage = 'Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.') {
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx] = {
        ...messages.value[lastIdx],
        content: errorMessage,
        timestamp: new Date().toLocaleTimeString(),
        streaming: false
      }
    }
  }

  /**
   * Send message via REST API
   * Handles both text-only and file upload scenarios
   */
  async function sendViaREST(chatbotId, message, sessionId, files = [], conversationId = null) {
    try {
      let response

      if (files.length > 0) {
        // Send with files using FormData
        const formData = new FormData()
        formData.append('message', message)
        formData.append('session_id', sessionId)
        formData.append('include_sources', 'true')
        if (conversationId) {
          formData.append('conversation_id', conversationId)
        }

        for (const file of files) {
          formData.append('files', file)
        }

        response = await axios.post(
          `/api/chatbots/${chatbotId}/chat`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        )
      } else {
        // Send text-only message
        response = await axios.post(
          `/api/chatbots/${chatbotId}/chat`,
          {
            message,
            session_id: sessionId,
            include_sources: true,
            conversation_id: conversationId
          }
        )
      }

      if (response.data.success) {
        return {
          success: true,
          content: response.data.response,
          sources: response.data.sources,
          conversationId: response.data.conversation_id,
          sessionId: response.data.session_id,
          conversationTitle: response.data.title || response.data.conversation_title,
          messageId: response.data.message_id,
          mode: response.data.mode,
          task_type: response.data.task_type,
          reasoning_steps: response.data.reasoning_steps
        }
      } else {
        throw new Error(response.data.error || 'Unbekannter Fehler')
      }
    } catch (error) {
      console.error('Chat error:', error)
      return {
        success: false,
        error: error.response?.data?.error || 'Fehler beim Senden'
      }
    }
  }

  /**
   * Get file type from filename extension
   */
  function getFileType(filename) {
    const ext = filename.split('.').pop()?.toLowerCase()
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes(ext)) return 'image'
    if (ext === 'pdf') return 'pdf'
    if (['doc', 'docx'].includes(ext)) return 'word'
    if (['xls', 'xlsx'].includes(ext)) return 'excel'
    if (['ppt', 'pptx'].includes(ext)) return 'powerpoint'
    return 'document'
  }

  return {
    // State
    isProcessing,
    currentSources,

    // Message manipulation
    addUserMessage,
    addBotPlaceholder,
    updateBotMessage,
    setBotError,

    // API operations
    sendViaREST,

    // Utilities
    getFileType
  }
}
