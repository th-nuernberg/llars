/**
 * Generation API Service
 *
 * API client for batch generation jobs that connect
 * Prompt Engineering with Evaluation through LLM-generated outputs.
 *
 * @module services/generationApi
 */

import axios from 'axios'

const API_BASE = '/api/generation'

/**
 * Generation API client
 */
export const generationApi = {
  // ===========================================================================
  // JOB MANAGEMENT
  // ===========================================================================

  /**
   * Create a new batch generation job.
   *
   * @param {Object} data - Job creation data
   * @param {string} data.name - Human-readable job name
   * @param {string} [data.description] - Optional description
   * @param {Object} data.config - Job configuration
   * @param {Object} data.config.sources - Source configuration
   * @param {Array} data.config.prompts - Array of prompt configs
   * @param {Array} data.config.llm_models - Array of model IDs
   * @param {Object} [data.config.generation_params] - LLM parameters
   * @returns {Promise<Object>} Created job
   *
   * @example
   * const job = await generationApi.createJob({
   *   name: 'Summarization Test',
   *   config: {
   *     sources: { type: 'scenario', scenario_id: 123 },
   *     prompts: [{ template_id: 1, variant_name: 'Standard' }],
   *     llm_models: ['gpt-4'],
   *     generation_params: { temperature: 0.7 }
   *   }
   * })
   */
  createJob(data) {
    return axios.post(`${API_BASE}/jobs`, data)
  },

  /**
   * Get list of jobs for the current user.
   *
   * @param {Object} [params] - Query parameters
   * @param {string} [params.status] - Filter by status
   * @param {number} [params.limit=50] - Max number of jobs
   * @returns {Promise<Object>} List of jobs
   */
  getJobs(params = {}) {
    return axios.get(`${API_BASE}/jobs`, { params })
  },

  /**
   * Get details for a specific job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Job details with progress and outputs summary
   */
  getJob(jobId) {
    return axios.get(`${API_BASE}/jobs/${jobId}`)
  },

  /**
   * Delete a job.
   *
   * Only completed, failed, or cancelled jobs can be deleted.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Success response
   */
  deleteJob(jobId) {
    return axios.delete(`${API_BASE}/jobs/${jobId}`)
  },

  // ===========================================================================
  // JOB LIFECYCLE
  // ===========================================================================

  /**
   * Start a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Updated job
   */
  startJob(jobId) {
    return axios.post(`${API_BASE}/jobs/${jobId}/start`)
  },

  /**
   * Pause a running job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Updated job
   */
  pauseJob(jobId) {
    return axios.post(`${API_BASE}/jobs/${jobId}/pause`)
  },

  /**
   * Cancel a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Updated job
   */
  cancelJob(jobId) {
    return axios.post(`${API_BASE}/jobs/${jobId}/cancel`)
  },

  // ===========================================================================
  // OUTPUTS
  // ===========================================================================

  /**
   * Get outputs for a job with pagination.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [params] - Query parameters
   * @param {number} [params.page=1] - Page number
   * @param {number} [params.per_page=50] - Items per page
   * @param {string} [params.status] - Filter by status
   * @param {boolean} [params.include_prompts=false] - Include rendered prompts
   * @returns {Promise<Object>} Paginated outputs
   */
  getOutputs(jobId, params = {}) {
    return axios.get(`${API_BASE}/jobs/${jobId}/outputs`, { params })
  },

  /**
   * Get a single output by ID.
   *
   * @param {number} outputId - Output ID
   * @returns {Promise<Object>} Output details with rendered prompts
   */
  getOutput(outputId) {
    return axios.get(`${API_BASE}/outputs/${outputId}`)
  },

  // ===========================================================================
  // EXPORT
  // ===========================================================================

  /**
   * Export job outputs to CSV.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [options] - Export options
   * @param {boolean} [options.include_prompts=false] - Include rendered prompts
   * @param {string} [options.status] - Filter by status
   * @returns {Promise<Blob>} CSV file as blob
   */
  exportCsv(jobId, options = {}) {
    return axios.post(
      `${API_BASE}/jobs/${jobId}/export/csv`,
      options,
      { responseType: 'blob' }
    )
  },

  /**
   * Export job outputs to JSON.
   *
   * @param {number} jobId - Job ID
   * @param {Object} [options] - Export options
   * @param {boolean} [options.include_prompts=true] - Include rendered prompts
   * @param {string} [options.status] - Filter by status
   * @returns {Promise<Object>} JSON export data
   */
  exportJson(jobId, options = {}) {
    return axios.post(`${API_BASE}/jobs/${jobId}/export/json`, options)
  },

  // ===========================================================================
  // SCENARIO CREATION
  // ===========================================================================

  /**
   * Create an evaluation scenario from job outputs.
   *
   * @param {number} jobId - Job ID
   * @param {Object} data - Scenario creation data
   * @param {string} data.scenario_name - Name for the new scenario
   * @param {string} data.evaluation_type - Type: ranking, rating, comparison, etc.
   * @param {Object} [data.config_json] - Optional scenario configuration
   * @returns {Promise<Object>} Created scenario info
   *
   * @example
   * const result = await generationApi.createScenario(123, {
   *   scenario_name: 'Summarization Comparison',
   *   evaluation_type: 'ranking'
   * })
   */
  createScenario(jobId, data) {
    return axios.post(`${API_BASE}/jobs/${jobId}/to-scenario`, data)
  },

  // ===========================================================================
  // STATISTICS & ESTIMATION
  // ===========================================================================

  /**
   * Get detailed statistics for a job.
   *
   * @param {number} jobId - Job ID
   * @returns {Promise<Object>} Statistics grouped by prompt/model
   */
  getStatistics(jobId) {
    return axios.get(`${API_BASE}/jobs/${jobId}/statistics`)
  },

  /**
   * Estimate cost for a job configuration.
   *
   * @param {Object} config - Job configuration to estimate
   * @returns {Promise<Object>} Cost estimate with breakdown
   *
   * @example
   * const estimate = await generationApi.estimateCost({
   *   sources: { type: 'scenario', scenario_id: 123 },
   *   prompts: [{ template_id: 1 }],
   *   llm_models: ['gpt-4', 'claude-3-sonnet']
   * })
   */
  estimateCost(config) {
    return axios.post(`${API_BASE}/estimate`, { config })
  },

  // ===========================================================================
  // HEALTH CHECK
  // ===========================================================================

  /**
   * Check generation service health.
   *
   * @returns {Promise<Object>} Health status
   */
  healthCheck() {
    return axios.get(`${API_BASE}/health`)
  }
}

export default generationApi
