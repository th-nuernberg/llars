/**
 * Composable for handling data import in the Scenario Manager.
 *
 * Wraps the import service APIs for uploading files, transforming data,
 * and executing imports into scenarios.
 */
import { ref } from 'vue'
import importService from '@/services/importService'

export function useDataImport() {
  // State
  const importing = ref(false)
  const importProgress = ref(0)
  const importError = ref(null)
  const importSession = ref(null)

  /**
   * Upload a file and analyze its format.
   * @param {File} file - The file to upload
   * @returns {Promise<Object>} Session object with detection results
   */
  async function uploadFile(file) {
    importing.value = true
    importProgress.value = 10
    importError.value = null

    try {
      const session = await importService.uploadFile(file)
      importSession.value = session
      importProgress.value = 30
      return session
    } catch (error) {
      importError.value = error.response?.data?.error || error.message || 'Upload failed'
      throw error
    }
  }

  /**
   * Transform the uploaded data.
   * @param {string} sessionId - Session ID from upload
   * @param {Object} options - Transform options (mappings, format_override, etc.)
   * @returns {Promise<Object>} Updated session
   */
  async function transformData(sessionId, options = {}) {
    importProgress.value = 50
    importError.value = null

    try {
      const session = await importService.transform(sessionId, options)
      importSession.value = session
      importProgress.value = 70
      return session
    } catch (error) {
      importError.value = error.response?.data?.error || error.message || 'Transform failed'
      throw error
    }
  }

  /**
   * Execute the import into the database.
   * @param {string} sessionId - Session ID
   * @param {Object} options - Import options
   * @param {string} options.task_type - Task type (rating, ranking, etc.)
   * @param {string} options.source_name - Name for the imported data
   * @param {boolean} options.create_scenario - Whether to create a new scenario
   * @param {number} options.scenario_id - Existing scenario ID to import into
   * @returns {Promise<Object>} Import result
   */
  async function executeImport(sessionId, options = {}) {
    importProgress.value = 80
    importError.value = null

    try {
      const result = await importService.execute(sessionId, options)
      importSession.value = result
      importProgress.value = 100
      return result
    } catch (error) {
      importError.value = error.response?.data?.error || error.message || 'Import failed'
      throw error
    } finally {
      importing.value = false
    }
  }

  /**
   * Full import workflow: upload, transform, execute.
   * @param {File} file - The file to import
   * @param {Object} options - Import options
   * @param {number} options.scenarioId - Scenario ID to import into
   * @param {string} options.taskType - Task type (derived from scenario if not provided)
   * @returns {Promise<Object>} Import result
   */
  async function importFileToScenario(file, { scenarioId, taskType = null }) {
    importing.value = true
    importProgress.value = 0
    importError.value = null

    try {
      // Step 1: Upload and analyze
      const uploadResult = await uploadFile(file)
      const sessionId = uploadResult.session_id

      // Step 2: Transform
      await transformData(sessionId)

      // Step 3: Execute import
      const result = await executeImport(sessionId, {
        create_scenario: false,
        scenario_id: scenarioId,
        task_type: taskType
      })

      return result
    } catch (error) {
      // Error already set in individual steps
      throw error
    } finally {
      importing.value = false
    }
  }

  /**
   * AI-assisted import workflow.
   * @param {File} file - The file to import
   * @param {string} userIntent - User's description of what they want to do
   * @param {Object} options - Import options
   * @returns {Promise<Object>} Import result
   */
  async function importWithAI(file, userIntent, { scenarioId }) {
    importing.value = true
    importProgress.value = 0
    importError.value = null

    try {
      // Step 1: Upload
      const uploadResult = await uploadFile(file)
      const sessionId = uploadResult.session_id

      // Step 2: AI analyze intent
      importProgress.value = 40
      const aiAnalysis = await importService.aiAnalyzeIntent({
        session_id: sessionId,
        user_intent: userIntent,
        file_count: 1
      })

      // Step 3: AI transform
      importProgress.value = 60
      await importService.aiTransform(sessionId, aiAnalysis)

      // Step 4: Execute
      const result = await executeImport(sessionId, {
        create_scenario: false,
        scenario_id: scenarioId,
        ai_analysis: aiAnalysis
      })

      return result
    } catch (error) {
      throw error
    } finally {
      importing.value = false
    }
  }

  /**
   * Get sample data from a session for preview.
   * @param {string} sessionId - Session ID
   * @param {number} count - Number of items to return
   * @returns {Promise<Object>} Sample data
   */
  async function getSample(sessionId, count = 5) {
    try {
      return await importService.getSample(sessionId, count)
    } catch (error) {
      console.error('Failed to get sample:', error)
      throw error
    }
  }

  /**
   * Reset import state.
   */
  function resetImport() {
    importing.value = false
    importProgress.value = 0
    importError.value = null
    importSession.value = null
  }

  return {
    // State
    importing,
    importProgress,
    importError,
    importSession,

    // Methods
    uploadFile,
    transformData,
    executeImport,
    importFileToScenario,
    importWithAI,
    getSample,
    resetImport
  }
}
