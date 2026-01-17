/**
 * Import Service for LLARS Data Importer.
 *
 * Handles API communication for the import wizard workflow.
 */

import axios from 'axios'

const API_BASE = '/api/import'

const importService = {
  /**
   * Get list of supported import formats.
   */
  async getFormats() {
    const response = await axios.get(`${API_BASE}/formats`)
    return response.data
  },

  /**
   * Upload a file and analyze its format.
   * @param {File} file - The file to upload
   */
  async uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await axios.post(`${API_BASE}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  /**
   * Get session status and details.
   * @param {string} sessionId - Session ID
   */
  async getSession(sessionId) {
    const response = await axios.get(`${API_BASE}/session/${sessionId}`)
    return response.data
  },

  /**
   * Get sample of transformed items for preview.
   * @param {string} sessionId - Session ID
   * @param {number} count - Number of items to return
   */
  async getSample(sessionId, count = 5) {
    const response = await axios.get(`${API_BASE}/session/${sessionId}/sample`, {
      params: { count }
    })
    return response.data
  },

  /**
   * Transform raw data using detected or specified format.
   * @param {string} sessionId - Session ID
   * @param {Object} options - Transformation options
   */
  async transform(sessionId, options = {}) {
    const response = await axios.post(`${API_BASE}/transform`, {
      session_id: sessionId,
      options
    })
    return response.data
  },

  /**
   * Validate transformed data.
   * @param {string} sessionId - Session ID
   */
  async validate(sessionId) {
    const response = await axios.post(`${API_BASE}/validate`, {
      session_id: sessionId
    })
    return response.data
  },

  /**
   * Execute the import and create database records.
   * @param {string} sessionId - Session ID
   * @param {Object} options - Import options
   */
  async execute(sessionId, options = {}) {
    const response = await axios.post(`${API_BASE}/execute`, {
      session_id: sessionId,
      ...options
    })
    return response.data
  },

  /**
   * Delete an import session.
   * @param {string} sessionId - Session ID
   */
  async deleteSession(sessionId) {
    const response = await axios.delete(`${API_BASE}/session/${sessionId}`)
    return response.data
  },

  // =========================================================================
  // AI-Assisted Endpoints
  // =========================================================================

  /**
   * Use AI to analyze data structure.
   * @param {string} sessionId - Session ID
   */
  async aiAnalyze(sessionId) {
    const response = await axios.post(`${API_BASE}/ai/analyze`, {
      session_id: sessionId
    })
    return response.data
  },

  /**
   * Use AI to analyze user intent and data structure together.
   * @param {Object} params - Analysis parameters
   * @param {string} params.session_id - Session ID
   * @param {string} params.user_intent - User's description of what they want to do
   * @param {number} params.file_count - Number of files uploaded
   */
  async aiAnalyzeIntent(params) {
    const response = await axios.post(`${API_BASE}/ai/analyze-intent`, params)
    return response.data
  },

  /**
   * Transform data using AI-generated field mappings.
   * @param {string} sessionId - Session ID
   * @param {Object} aiAnalysis - AI analysis result from aiAnalyzeIntent
   */
  async aiTransform(sessionId, aiAnalysis) {
    const response = await axios.post(`${API_BASE}/ai/transform`, {
      session_id: sessionId,
      ai_analysis: aiAnalysis
    })
    return response.data
  },

  /**
   * Generate a transformation script using AI.
   * @param {string} sessionId - Session ID
   * @param {Object} fieldHints - Optional field hints
   */
  async aiTransformScript(sessionId, fieldHints = {}) {
    const response = await axios.post(`${API_BASE}/ai/transform-script`, {
      session_id: sessionId,
      field_hints: fieldHints
    })
    return response.data
  },

  /**
   * Get AI suggestions for improving field mapping.
   * @param {string} sessionId - Session ID
   * @param {Object} currentMapping - Current field mapping
   */
  async aiSuggest(sessionId, currentMapping = {}) {
    const response = await axios.post(`${API_BASE}/ai/suggest`, {
      session_id: sessionId,
      current_mapping: currentMapping
    })
    return response.data
  },

  /**
   * Get the URL for the AI chat stream endpoint.
   * Use with fetch() for SSE streaming.
   * @returns {string} The chat stream endpoint URL
   */
  getChatStreamUrl() {
    return `${API_BASE}/ai/chat-stream`
  },

  /**
   * Create the request body for AI chat stream.
   * @param {string} sessionId - Session ID
   * @param {Array} messages - Chat messages [{role, content}]
   * @param {Object} currentConfig - Current configuration
   * @returns {string} JSON stringified body
   */
  buildChatStreamBody(sessionId, messages, currentConfig = {}) {
    return JSON.stringify({
      session_id: sessionId,
      messages: messages.map(m => ({
        role: m.role,
        content: m.content
      })),
      current_config: currentConfig
    })
  },

  /**
   * Import data directly into an existing scenario (without file upload).
   * Used by ScenarioWizard which parses files client-side.
   *
   * @param {Array} data - Array of items to import
   * @param {number} scenarioId - ID of existing scenario to import into
   * @param {string} taskType - Task type (rating, ranking, authenticity, etc.)
   * @param {string} sourceName - Name for the import source
   * @returns {Promise<Object>} Import result
   */
  async importFromData(data, scenarioId, taskType, sourceName = 'Wizard Import') {
    const response = await axios.post(`${API_BASE}/from-data`, {
      data,
      scenario_id: scenarioId,
      task_type: taskType,
      source_name: sourceName
    })
    return response.data
  }
}

export default importService
