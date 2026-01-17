/**
 * Composable for Wizard Chat with SSE streaming.
 *
 * Enables conversational refinement of scenario configuration.
 * Handles SSE streaming, config extraction, and chat history.
 */

import { ref, reactive, computed } from 'vue'

const API_BASE = '/api/import'

export function useWizardChat(sessionId) {
  // Chat state
  const messages = ref([])
  const streaming = ref(false)
  const streamingContent = ref('')
  const error = ref(null)

  // Extracted configuration with loading states
  const streamingFields = reactive({
    task_type: { loading: false, value: null },
    task_description: { loading: false, value: null },
    labels: { loading: false, value: [] },
    buckets: { loading: false, value: [] },
    scales: { loading: false, value: [] },
    field_mapping: { loading: false, value: {} },
    role_mapping: { loading: false, value: {} }
  })

  // Merged configuration from all updates
  const config = ref({})

  // Computed: has any analysis been done
  const hasAnalysis = computed(() => {
    return messages.value.some(m => m.role === 'assistant')
  })

  // Computed: which config sections to show based on task type
  const showLabels = computed(() => {
    const taskType = streamingFields.task_type.value || config.value.task_type
    return ['authenticity', 'classification'].includes(taskType)
  })

  const showBuckets = computed(() => {
    const taskType = streamingFields.task_type.value || config.value.task_type
    return taskType === 'ranking'
  })

  const showScales = computed(() => {
    const taskType = streamingFields.task_type.value || config.value.task_type
    return ['rating', 'mail_rating'].includes(taskType)
  })

  /**
   * Send a message and stream the response.
   * @param {string} content - User message content
   */
  async function sendMessage(content) {
    if (!sessionId.value && !sessionId) {
      error.value = 'Keine Session vorhanden'
      return
    }

    const sessionIdValue = typeof sessionId === 'object' ? sessionId.value : sessionId

    // Add user message
    messages.value.push({
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    })

    // Reset streaming state
    streaming.value = true
    streamingContent.value = ''
    error.value = null

    // Set all fields to loading
    Object.keys(streamingFields).forEach(key => {
      streamingFields[key].loading = true
    })

    try {
      // Prepare request body
      const body = JSON.stringify({
        session_id: sessionIdValue,
        messages: messages.value.map(m => ({
          role: m.role,
          content: m.content
        })),
        current_config: config.value
      })

      // Start SSE request
      const response = await fetch(`${API_BASE}/ai/chat-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body
      })

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }

      // Read SSE stream
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE events from buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() // Keep incomplete line in buffer

        let currentEvent = null
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ') && currentEvent) {
            const data = line.slice(6)
            try {
              const parsed = JSON.parse(data)
              handleSSEEvent(currentEvent, parsed)
            } catch (e) {
              console.warn('Failed to parse SSE data:', data)
            }
            currentEvent = null
          }
        }
      }

    } catch (err) {
      console.error('Chat stream error:', err)
      error.value = err.message || 'Verbindungsfehler'
    } finally {
      streaming.value = false
      // Reset loading states
      Object.keys(streamingFields).forEach(key => {
        streamingFields[key].loading = false
      })
    }
  }

  /**
   * Handle incoming SSE event.
   */
  function handleSSEEvent(eventType, data) {
    switch (eventType) {
      case 'thinking':
        // Could show a thinking indicator
        break

      case 'config':
        // Update specific config field
        if (data.field && streamingFields[data.field]) {
          streamingFields[data.field].value = data.value
          streamingFields[data.field].loading = false
          // Also update merged config
          config.value = { ...config.value, [data.field]: data.value }
        }
        break

      case 'chunk':
        // Append text chunk
        streamingContent.value += data.content || ''
        break

      case 'done':
        // Finalize with complete config and response
        if (data.config) {
          config.value = { ...config.value, ...data.config }
          // Update all streaming fields from final config
          Object.keys(streamingFields).forEach(key => {
            if (data.config[key] !== undefined) {
              streamingFields[key].value = data.config[key]
            }
          })
        }

        // Add assistant message to history
        messages.value.push({
          role: 'assistant',
          content: data.response || streamingContent.value,
          timestamp: new Date().toISOString(),
          config: data.config
        })
        streamingContent.value = ''
        break

      case 'error':
        error.value = data.error || 'Unbekannter Fehler'
        break
    }
  }

  /**
   * Initialize config from existing analysis.
   */
  function initFromAnalysis(analysis) {
    if (!analysis) return

    config.value = {
      task_type: analysis.task_type,
      task_description: analysis.task_description,
      field_mapping: analysis.field_mapping || {},
      role_mapping: analysis.role_mapping || {},
      evaluation_criteria: analysis.evaluation_criteria || [],
      labels: analysis.labels || [],
      buckets: analysis.buckets || [],
      scales: analysis.scales || []
    }

    // Update streaming fields
    Object.keys(streamingFields).forEach(key => {
      if (config.value[key] !== undefined) {
        streamingFields[key].value = config.value[key]
      }
    })
  }

  /**
   * Clear chat history but keep config.
   */
  function clearMessages() {
    messages.value = []
    streamingContent.value = ''
    error.value = null
  }

  /**
   * Reset everything.
   */
  function reset() {
    messages.value = []
    streaming.value = false
    streamingContent.value = ''
    error.value = null
    config.value = {}

    Object.keys(streamingFields).forEach(key => {
      streamingFields[key].loading = false
      streamingFields[key].value = Array.isArray(streamingFields[key].value) ? [] : null
    })
    streamingFields.field_mapping.value = {}
    streamingFields.role_mapping.value = {}
  }

  return {
    // State
    messages,
    streaming,
    streamingContent,
    streamingFields,
    config,
    error,

    // Computed
    hasAnalysis,
    showLabels,
    showBuckets,
    showScales,

    // Actions
    sendMessage,
    initFromAnalysis,
    clearMessages,
    reset
  }
}
