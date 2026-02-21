/**
 * AI Writing Service
 *
 * Frontend API client for the AI Writing Assistant.
 * Provides methods for text completion, rewriting, chat, and citation features.
 */

import axios from 'axios'
import { BASE_URL } from '@/config.js'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const API_BASE = `${BASE_URL}/api/ai-writing`

// Create axios instance with auth header
function getAuthHeaders() {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function apiPost(endpoint, data) {
  const response = await axios.post(`${API_BASE}${endpoint}`, data, {
    headers: getAuthHeaders(),
    timeout: 60000 // 60s timeout for AI operations
  })
  return response.data
}

async function apiGet(endpoint) {
  const response = await axios.get(`${API_BASE}${endpoint}`, {
    headers: getAuthHeaders(),
    timeout: 30000
  })
  return response.data
}

/**
 * Generate text completion at cursor position
 * @param {Object} params - Completion parameters
 * @param {string} params.context - Text around cursor
 * @param {number} params.cursor_position - Position in context
 * @param {string} [params.document_type='latex'] - Document type
 * @param {number} [params.max_tokens=100] - Max tokens
 * @param {number} [params.temperature=0.3] - Temperature
 * @returns {Promise<{completion: string, confidence: number, alternatives: string[]}>}
 */
export async function complete(params) {
  return apiPost('/complete', {
    context: params.context,
    cursor_position: params.cursor_position,
    document_type: params.document_type || 'latex',
    max_tokens: params.max_tokens || 100,
    temperature: params.temperature || 0.3
  })
}

/**
 * Rewrite text in a specified style
 * @param {Object} params - Rewrite parameters
 * @param {string} params.text - Text to rewrite
 * @param {string} [params.style='academic'] - Style (academic, concise, expanded, simplified)
 * @param {string} [params.context=''] - Surrounding context
 * @returns {Promise<{result: string, changes: Array}>}
 */
export async function rewrite(params) {
  return apiPost('/rewrite', {
    text: params.text,
    style: params.style || 'academic',
    context: params.context || ''
  })
}

/**
 * Expand text with more details
 * @param {Object} params - Expand parameters
 * @param {string} params.text - Text to expand
 * @param {string} [params.context=''] - Context
 * @returns {Promise<{result: string}>}
 */
export async function expand(params) {
  return apiPost('/expand', {
    text: params.text,
    context: params.context || ''
  })
}

/**
 * Summarize text
 * @param {Object} params - Summarize parameters
 * @param {string} params.text - Text to summarize
 * @returns {Promise<{result: string}>}
 */
export async function summarize(params) {
  return apiPost('/summarize', {
    text: params.text
  })
}

/**
 * Generate abstract for document
 * @param {string} content - Full document content
 * @returns {Promise<{abstract: string, word_count: number}>}
 */
export async function generateAbstract(content) {
  return apiPost('/abstract', { content })
}

/**
 * Suggest titles for document
 * @param {string} content - Document content
 * @param {number} [numSuggestions=5] - Number of suggestions
 * @returns {Promise<{titles: string[]}>}
 */
export async function suggestTitles(content, numSuggestions = 5) {
  return apiPost('/titles', {
    content,
    num_suggestions: numSuggestions
  })
}

/**
 * Fix LaTeX errors
 * @param {string} content - LaTeX content
 * @returns {Promise<{errors: Array, suggestions: string[]}>}
 */
export async function fixLatex(content) {
  return apiPost('/fix-latex', { content })
}

/**
 * Send chat message (non-streaming)
 * @param {Object} params - Chat parameters
 * @param {string} params.message - User message
 * @param {string} [params.document_content=''] - Document context
 * @param {Array} [params.history=[]] - Chat history
 * @returns {Promise<{response: string, artifacts: Array}>}
 */
export async function chat(params) {
  return apiPost('/chat', {
    message: params.message,
    document_content: params.document_content || '',
    history: params.history || [],
    stream: false
  })
}

/**
 * Send chat message with streaming
 * @param {Object} params - Chat parameters
 * @param {string} params.message - User message
 * @param {string} [params.document_content=''] - Document context
 * @param {Array} [params.history=[]] - Chat history
 * @param {Function} onChunk - Callback for each chunk
 * @returns {Promise<{response: string, artifacts: Array}>}
 */
export async function streamChat(params, onChunk) {
  const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      message: params.message,
      document_content: params.document_content || '',
      history: params.history || [],
      stream: true
    })
  })

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let fullResponse = ''
  let artifacts = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value)
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (data.delta) {
            fullResponse += data.delta
            if (onChunk) onChunk(data.delta, data.done)
          }
          if (data.done && data.artifacts) {
            artifacts = data.artifacts
          }
        } catch (e) {
          // Ignore parse errors
        }
      }
    }
  }

  return { response: fullResponse, artifacts }
}

/**
 * Execute an @-command
 * @param {Object} params - Command parameters
 * @param {string} params.command - Command name
 * @param {string} [params.args=''] - Command arguments
 * @param {string} [params.selected_text=''] - Selected text
 * @param {string} [params.document_content=''] - Document content
 * @returns {Promise<{response: string}>}
 */
export async function executeCommand(params) {
  return apiPost('/command', {
    command: params.command,
    args: params.args || '',
    selected_text: params.selected_text || '',
    document_content: params.document_content || ''
  })
}

/**
 * Find citations using RAG
 * @param {Object} params - Search parameters
 * @param {string} params.claim - Statement needing citation
 * @param {string} [params.context=''] - Surrounding context
 * @param {number[]} [params.collection_ids=[]] - RAG collection IDs
 * @param {number} [params.limit=10] - Max results
 * @param {string} [params.format='bibtex'] - Citation format
 * @returns {Promise<{citations: Array}>}
 */
export async function findCitations(params) {
  return apiPost('/find-citations', {
    claim: params.claim,
    context: params.context || '',
    collection_ids: params.collection_ids || [],
    limit: params.limit || 10,
    format: params.format || 'bibtex'
  })
}

/**
 * Review document for claims needing citations
 * @param {string} content - Document content
 * @returns {Promise<{warnings: Array, statistics: Object}>}
 */
export async function reviewCitations(content) {
  return apiPost('/review-citations', { content })
}

/**
 * Mark a citation warning as ignored
 * @param {number} documentId - Document ID
 * @param {string} text - Warning text
 * @returns {Promise<{success: boolean}>}
 */
export async function ignoreWarning(documentId, text) {
  return apiPost('/ignore-warning', {
    document_id: documentId,
    text
  })
}

/**
 * Check AI writing service health
 * @returns {Promise<{status: string, model: string}>}
 */
export async function checkHealth() {
  return apiGet('/health')
}

// Default export
export default {
  complete,
  rewrite,
  expand,
  summarize,
  generateAbstract,
  suggestTitles,
  fixLatex,
  chat,
  streamChat,
  executeCommand,
  findCitations,
  reviewCitations,
  ignoreWarning,
  checkHealth
}
