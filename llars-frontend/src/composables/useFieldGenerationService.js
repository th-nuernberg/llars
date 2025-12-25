/**
 * Global Field Generation Service
 *
 * This service manages field generation streams independently of Vue components.
 * Streams continue running in the background even when the user navigates away,
 * and the accumulated content is preserved for when they return.
 */

import { reactive, readonly } from 'vue'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

// Global singleton state (lives outside of Vue component lifecycle)
const state = reactive({
  // Map of chatbotId -> field -> { generating, content, error, abortController }
  sessions: {}
})

/**
 * Get or create a session for a chatbot
 */
function getSession(chatbotId) {
  if (!state.sessions[chatbotId]) {
    state.sessions[chatbotId] = {
      fields: {},
      generating: {}
    }
  }
  return state.sessions[chatbotId]
}

/**
 * Get the current field state
 */
function getFieldState(chatbotId, field) {
  const session = getSession(chatbotId)
  if (!session.fields[field]) {
    session.fields[field] = {
      content: '',
      error: null,
      completed: false
    }
  }
  return session.fields[field]
}

/**
 * Check if a field is currently being generated
 */
function isGenerating(chatbotId, field) {
  const session = getSession(chatbotId)
  return !!session.generating[field]
}

/**
 * Get the current content for a field
 */
function getContent(chatbotId, field) {
  const fieldState = getFieldState(chatbotId, field)
  return fieldState.content
}

/**
 * Check if generation completed for a field
 */
function isCompleted(chatbotId, field) {
  const fieldState = getFieldState(chatbotId, field)
  return fieldState.completed
}

/**
 * Start streaming field generation
 * Returns immediately - the stream runs in the background
 */
async function startStreamGeneration(chatbotId, field, onUpdate = null) {
  if (!chatbotId) {
    console.warn('[FieldGenService] No chatbotId provided')
    return
  }

  const session = getSession(chatbotId)
  const fieldState = getFieldState(chatbotId, field)

  // If already generating, don't start again
  if (session.generating[field]) {
    console.log(`[FieldGenService] Field ${field} already generating for chatbot ${chatbotId}`)
    return
  }

  // Reset field state for new generation
  fieldState.content = ''
  fieldState.error = null
  fieldState.completed = false

  // Create abort controller for this stream
  const abortController = new AbortController()
  session.generating[field] = {
    abortController,
    startedAt: Date.now()
  }

  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)

  try {
    const response = await fetch(`/api/chatbots/${chatbotId}/wizard/generate-field`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ field, stream: true }),
      signal: abortController.signal
    })

    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      // Check if aborted
      if (abortController.signal.aborted) {
        break
      }

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue

        try {
          const payload = JSON.parse(line.replace(/^data:\s*/, ''))
          if (payload.delta) {
            fieldState.content += payload.delta
            // Notify callback if provided
            if (onUpdate) {
              onUpdate(fieldState.content, false)
            }
          }
          if (payload.done && payload.value) {
            fieldState.content = payload.value
            fieldState.completed = true
            if (onUpdate) {
              onUpdate(fieldState.content, true)
            }
          }
        } catch (e) {
          console.error('[FieldGenService] Stream parse error:', e)
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim().startsWith('data:')) {
      try {
        const payload = JSON.parse(buffer.replace(/^data:\s*/, ''))
        if (payload.value) {
          fieldState.content = payload.value
          fieldState.completed = true
          if (onUpdate) {
            onUpdate(fieldState.content, true)
          }
        }
      } catch (e) {
        console.error('[FieldGenService] Final buffer parse error:', e)
      }
    }

    // Mark as completed if not already
    if (!fieldState.completed && fieldState.content) {
      fieldState.completed = true
      if (onUpdate) {
        onUpdate(fieldState.content, true)
      }
    }

  } catch (error) {
    if (error.name === 'AbortError') {
      console.log(`[FieldGenService] Stream aborted for field ${field}`)
    } else {
      console.error(`[FieldGenService] Error generating ${field}:`, error)
      fieldState.error = error.message
    }
  } finally {
    // Clean up generating state
    delete session.generating[field]
  }
}

/**
 * Start non-streaming field generation (for short fields like name, icon, color)
 */
async function startDirectGeneration(chatbotId, field, options = {}) {
  if (!chatbotId) {
    console.warn('[FieldGenService] No chatbotId provided')
    return null
  }

  const session = getSession(chatbotId)
  const fieldState = getFieldState(chatbotId, field)

  // If already generating, don't start again
  if (session.generating[field]) {
    console.log(`[FieldGenService] Field ${field} already generating for chatbot ${chatbotId}`)
    return null
  }

  // Mark as generating
  session.generating[field] = {
    startedAt: Date.now()
  }

  try {
    const forceLlm = field === 'color' ? true : options.force_llm

    const response = await axios.post(`/api/chatbots/${chatbotId}/wizard/generate-field`, {
      field,
      force_llm: forceLlm
    })

    if (response.data.success) {
      fieldState.content = response.data.value
      fieldState.completed = true
      fieldState.error = null
      return response.data.value
    } else {
      fieldState.error = response.data.error || 'Generation failed'
      return null
    }
  } catch (error) {
    console.error(`[FieldGenService] Error generating ${field}:`, error)
    fieldState.error = error.message
    return null
  } finally {
    delete session.generating[field]
  }
}

/**
 * Generate a field - automatically chooses streaming vs direct based on field type
 */
async function generateField(chatbotId, field, options = {}) {
  const streamingFields = ['system_prompt', 'welcome_message']

  if (streamingFields.includes(field)) {
    return startStreamGeneration(chatbotId, field, options.onUpdate)
  } else {
    return startDirectGeneration(chatbotId, field, options)
  }
}

/**
 * Abort a running generation
 */
function abortGeneration(chatbotId, field) {
  const session = state.sessions[chatbotId]
  if (!session) return

  const generating = session.generating[field]
  if (generating?.abortController) {
    generating.abortController.abort()
  }
}

/**
 * Clear all state for a chatbot (e.g., when wizard is completed or cancelled)
 */
function clearSession(chatbotId) {
  // Abort any running generations first
  const session = state.sessions[chatbotId]
  if (session) {
    Object.entries(session.generating).forEach(([field, gen]) => {
      if (gen?.abortController) {
        gen.abortController.abort()
      }
    })
  }
  delete state.sessions[chatbotId]
}

/**
 * Get all generating fields for a chatbot
 */
function getGeneratingFields(chatbotId) {
  const session = state.sessions[chatbotId]
  if (!session) return {}

  const result = {}
  const fields = ['name', 'display_name', 'system_prompt', 'welcome_message', 'icon', 'color']
  fields.forEach(field => {
    result[field] = !!session.generating[field]
  })
  return result
}

/**
 * Get all field contents for a chatbot
 */
function getAllFieldContents(chatbotId) {
  const session = state.sessions[chatbotId]
  if (!session) return {}

  const result = {}
  Object.entries(session.fields).forEach(([field, fieldState]) => {
    if (fieldState.content) {
      result[field] = fieldState.content
    }
  })
  return result
}

/**
 * Subscribe to updates for a specific field
 * Returns unsubscribe function
 */
function subscribeToField(chatbotId, field, callback) {
  // This is a simple polling-based approach
  // For a more sophisticated approach, we could use Vue's watch or an event emitter
  let lastContent = ''
  let lastGenerating = false

  const interval = setInterval(() => {
    const content = getContent(chatbotId, field)
    const generating = isGenerating(chatbotId, field)
    const completed = isCompleted(chatbotId, field)

    if (content !== lastContent || generating !== lastGenerating) {
      lastContent = content
      lastGenerating = generating
      callback({
        content,
        generating,
        completed
      })
    }
  }, 100) // Check every 100ms

  // Return unsubscribe function
  return () => clearInterval(interval)
}

// Export the service
export function useFieldGenerationService() {
  return {
    // State access (readonly to prevent external mutations)
    state: readonly(state),

    // Methods
    generateField,
    startStreamGeneration,
    startDirectGeneration,
    abortGeneration,
    clearSession,

    // Getters
    isGenerating,
    getContent,
    isCompleted,
    getGeneratingFields,
    getAllFieldContents,
    subscribeToField
  }
}

// Also export a singleton instance for direct use
export const fieldGenerationService = {
  generateField,
  startStreamGeneration,
  startDirectGeneration,
  abortGeneration,
  clearSession,
  isGenerating,
  getContent,
  isCompleted,
  getGeneratingFields,
  getAllFieldContents,
  subscribeToField,
  state: readonly(state)
}
