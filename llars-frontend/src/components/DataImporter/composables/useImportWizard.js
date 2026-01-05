/**
 * Composable for Data Importer Wizard state management.
 *
 * Handles the entire import workflow: upload, analyze, transform, validate, execute.
 */

import { ref, computed } from 'vue'
import importService from '@/services/importService'

export function useImportWizard() {
  // Session state
  const session = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // AI-generated script
  const aiScript = ref(null)

  // Status text for header
  const statusText = computed(() => {
    if (!session.value) return ''
    switch (session.value.status) {
      case 'analyzing':
        return 'Analysiere Datei...'
      case 'transforming':
        return 'Transformiere Daten...'
      case 'validating':
        return 'Validiere Daten...'
      case 'importing':
        return 'Importiere Daten...'
      default:
        return ''
    }
  })

  const isProcessing = computed(() => {
    return ['analyzing', 'transforming', 'validating', 'importing'].includes(session.value?.status)
  })

  /**
   * Upload a file and analyze its format.
   */
  async function uploadFile(file) {
    loading.value = true
    error.value = null

    try {
      const result = await importService.uploadFile(file)
      session.value = result
      return result
    } catch (err) {
      error.value = err.message || 'Upload fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Request AI analysis of the data structure.
   */
  async function analyzeWithAI() {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await importService.aiAnalyze(session.value.session_id)

      // Merge AI suggestions into session
      if (result.ai_analyzed) {
        session.value = {
          ...session.value,
          ai_analysis: result,
          detected_format: result.detected_format || session.value.detected_format,
          structure: {
            ...session.value.structure,
            ai_field_mapping: result.field_mapping,
            ai_suggested_task_type: result.suggested_task_type
          }
        }
      }

      return result
    } catch (err) {
      error.value = err.message || 'AI-Analyse fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Transform data using detected or specified format.
   */
  async function transform(options = {}) {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await importService.transform(session.value.session_id, options)
      session.value = result

      if (!result.success && result.errors?.length) {
        error.value = result.errors[0]
      }

      return result
    } catch (err) {
      error.value = err.message || 'Transformation fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Generate AI transformation script.
   */
  async function generateAIScript(fieldHints = {}) {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await importService.aiTransformScript(session.value.session_id, fieldHints)
      aiScript.value = result

      return result
    } catch (err) {
      error.value = err.message || 'Skript-Generierung fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Validate transformed data.
   */
  async function validate() {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await importService.validate(session.value.session_id)
      session.value = result

      if (!result.validation?.valid && result.validation?.errors?.length) {
        error.value = result.validation.errors[0]
      }

      return result
    } catch (err) {
      error.value = err.message || 'Validierung fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Transform data using AI analysis.
   */
  async function transformWithAI(aiAnalysis) {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      const result = await importService.aiTransform(session.value.session_id, aiAnalysis)
      session.value = result

      if (!result.success && result.errors?.length) {
        error.value = result.errors[0]
      }

      return result
    } catch (err) {
      error.value = err.message || 'AI-Transformation fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Execute the import.
   * If aiAnalysis is provided, runs AI transform first.
   */
  async function executeImport({ taskType, sourceName, aiAnalysis = null }) {
    if (!session.value?.session_id) {
      error.value = 'Keine Session vorhanden'
      return
    }

    loading.value = true
    error.value = null

    try {
      // Run AI transform if analysis provided and not yet transformed
      if (aiAnalysis && session.value.status !== 'transformed') {
        const transformResult = await importService.aiTransform(session.value.session_id, aiAnalysis)
        session.value = transformResult

        if (!transformResult.success && transformResult.errors?.length) {
          error.value = transformResult.errors[0]
          return transformResult
        }
      }

      // Execute the import
      const result = await importService.execute(session.value.session_id, {
        task_type: taskType,
        source_name: sourceName
      })
      session.value = result

      if (result.errors?.length) {
        error.value = result.errors[0]
      }

      return result
    } catch (err) {
      error.value = err.message || 'Import fehlgeschlagen'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get sample data for preview.
   */
  async function getSample(count = 5) {
    if (!session.value?.session_id) return []

    try {
      const result = await importService.getSample(session.value.session_id, count)
      return result.sample || []
    } catch (err) {
      console.error('Failed to get sample:', err)
      return []
    }
  }

  /**
   * Reset the session.
   */
  function resetSession() {
    session.value = null
    error.value = null
    aiScript.value = null
  }

  return {
    // State
    session,
    loading,
    error,
    aiScript,
    isProcessing,
    statusText,

    // Actions
    uploadFile,
    analyzeWithAI,
    transform,
    transformWithAI,
    generateAIScript,
    validate,
    executeImport,
    getSample,
    resetSession
  }
}
