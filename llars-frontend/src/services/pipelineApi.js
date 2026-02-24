/**
 * Pipeline API Service
 * API client for automated LLM evaluation pipeline runs.
 */

import axios from 'axios'

const API_BASE = '/api/pipeline'

export const pipelineApi = {
  // ===========================================================================
  // RUN MANAGEMENT
  // ===========================================================================

  /**
   * Create a new pipeline run.
   *
   * @param {Object} data - Run creation data
   * @param {string} data.name - Run name
   * @param {Object} data.config - Pipeline configuration
   * @param {string[]} data.candidate_models - Model IDs to test
   * @param {boolean} [data.auto_start] - Start immediately after creation
   * @returns {Promise<Object>} Created run
   */
  createRun(data) {
    return axios.post(`${API_BASE}/runs`, data)
  },

  /**
   * Get list of pipeline runs for current user.
   *
   * @param {Object} [params] - Query params (status, limit)
   * @returns {Promise<Object>} List of runs
   */
  getRuns(params = {}) {
    return axios.get(`${API_BASE}/runs`, { params })
  },

  /**
   * Get full details for a run including all iterations.
   *
   * @param {number} runId - Run ID
   * @returns {Promise<Object>} Run with iterations
   */
  getRun(runId) {
    return axios.get(`${API_BASE}/runs/${runId}`)
  },

  /**
   * Delete a pipeline run.
   *
   * @param {number} runId - Run ID
   * @returns {Promise<Object>} Success response
   */
  deleteRun(runId) {
    return axios.delete(`${API_BASE}/runs/${runId}`)
  },

  // ===========================================================================
  // LIFECYCLE
  // ===========================================================================

  /**
   * Start or resume a pipeline run.
   *
   * @param {number} runId - Run ID
   * @returns {Promise<Object>} Updated run
   */
  startRun(runId) {
    return axios.post(`${API_BASE}/runs/${runId}/start`)
  },

  /**
   * Pause a running pipeline.
   *
   * @param {number} runId - Run ID
   * @returns {Promise<Object>} Updated run
   */
  pauseRun(runId) {
    return axios.post(`${API_BASE}/runs/${runId}/pause`)
  },

  /**
   * Cancel a pipeline run.
   *
   * @param {number} runId - Run ID
   * @returns {Promise<Object>} Updated run
   */
  cancelRun(runId) {
    return axios.post(`${API_BASE}/runs/${runId}/cancel`)
  },

  /**
   * Submit human review decision.
   *
   * @param {number} runId - Run ID
   * @param {string} decision - 'continue', 'deploy', or 'reject'
   * @returns {Promise<Object>} Updated run
   */
  submitReview(runId, decision) {
    return axios.post(`${API_BASE}/runs/${runId}/review`, { decision })
  },

  // ===========================================================================
  // DETAILS
  // ===========================================================================

  /**
   * Get details of a specific iteration.
   *
   * @param {number} runId - Run ID
   * @param {number} iterationNumber - Iteration number
   * @returns {Promise<Object>} Iteration details
   */
  getIteration(runId, iterationNumber) {
    return axios.get(`${API_BASE}/runs/${runId}/iterations/${iterationNumber}`)
  },

  /**
   * Get top-K best configurations from a run.
   *
   * @param {number} runId - Run ID
   * @param {Object} [params] - Query params (limit)
   * @returns {Promise<Object>} Best configs
   */
  getBestConfigs(runId, params = {}) {
    return axios.get(`${API_BASE}/runs/${runId}/best-configs`, { params })
  },
}
