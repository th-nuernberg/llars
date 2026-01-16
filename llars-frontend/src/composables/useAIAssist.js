/**
 * AI-Assist Composable
 *
 * Provides AI-powered field generation for form fields.
 * Handles loading states, streaming, and error handling.
 *
 * @example
 * const { generate, generating, error } = useAIAssist()
 *
 * const value = await generate('scenario.settings.name', {
 *   scenario_type: 'rating',
 *   existing_description: 'My description'
 * })
 */

import { ref, reactive } from 'vue'
import axios from 'axios'

// Global state to track active generations (prevents duplicate requests)
const activeGenerations = reactive({})

/**
 * AI-Assist composable for form field generation
 * @returns {Object} AI assist methods and state
 */
export function useAIAssist() {
  const generating = ref(false)
  const error = ref(null)

  /**
   * Generate a value for a form field using AI
   *
   * @param {string} fieldKey - The field key (e.g., 'scenario.settings.name')
   * @param {Object} context - Context variables for the prompt
   * @param {boolean} stream - Whether to stream the response
   * @returns {Promise<string>} The generated value
   */
  async function generate(fieldKey, context = {}, stream = false) {
    if (activeGenerations[fieldKey]) {
      console.warn(`Generation already in progress for ${fieldKey}`)
      return null
    }

    generating.value = true
    activeGenerations[fieldKey] = true
    error.value = null

    try {
      if (stream) {
        return await generateStreaming(fieldKey, context)
      } else {
        return await generateDirect(fieldKey, context)
      }
    } catch (e) {
      error.value = e.message || 'Generation failed'
      throw e
    } finally {
      generating.value = false
      delete activeGenerations[fieldKey]
    }
  }

  /**
   * Generate directly (non-streaming)
   */
  async function generateDirect(fieldKey, context) {
    const response = await axios.post('/api/ai-assist/generate', {
      field_key: fieldKey,
      context,
      stream: false
    })

    if (response.data.success) {
      return response.data.value
    }

    throw new Error(response.data.error || 'Generation failed')
  }

  /**
   * Generate with streaming
   */
  async function generateStreaming(fieldKey, context) {
    const response = await fetch('/api/ai-assist/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include',
      body: JSON.stringify({
        field_key: fieldKey,
        context,
        stream: true
      })
    })

    if (!response.ok || !response.body) {
      throw new Error(`Streaming failed: ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let result = ''
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue

        try {
          const payload = JSON.parse(line.replace(/^data:\s*/, ''))
          if (payload.delta) result += payload.delta
          if (payload.done && payload.value) result = payload.value
          if (payload.error) throw new Error(payload.error)
        } catch (e) {
          if (e.message !== 'Generation failed') {
            console.error('Stream parse error:', e)
          }
        }
      }
    }

    return result
  }

  /**
   * Check if a specific field is currently generating
   * @param {string} fieldKey - The field key to check
   * @returns {boolean} Whether generation is in progress
   */
  function isGenerating(fieldKey) {
    return !!activeGenerations[fieldKey]
  }

  /**
   * Get list of available field prompts
   * @returns {Promise<Array>} List of available prompts
   */
  async function getAvailablePrompts() {
    try {
      const response = await axios.get('/api/ai-assist/prompts')
      return response.data.prompts || []
    } catch (e) {
      console.error('Failed to fetch available prompts:', e)
      return []
    }
  }

  return {
    generate,
    generating,
    error,
    isGenerating,
    getAvailablePrompts
  }
}

export default useAIAssist
