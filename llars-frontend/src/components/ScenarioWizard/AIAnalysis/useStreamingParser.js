/**
 * Composable for incremental JSON parsing during SSE streaming.
 *
 * Extracts fields from a streaming JSON response and provides
 * reactive state for each field's loading/streaming/complete status.
 */

import { ref, reactive, computed } from 'vue'

/**
 * Field states during streaming
 */
export const FIELD_STATE = {
  PENDING: 'pending',
  STREAMING: 'streaming',
  COMPLETE: 'complete'
}

/**
 * Create a streaming parser for AI analysis responses.
 *
 * @returns {Object} Parser state and methods
 */
export function useStreamingParser() {
  // Raw buffer for accumulating chunks
  const buffer = ref('')

  // Parsed values
  const parsed = reactive({
    evalType: null,
    evalTypeConfidence: null,
    evalTypeReasoning: '',
    scenarioName: '',
    scenarioDescription: '',
    dataQuality: null,
    configSuggestions: null
  })

  // State for each field
  const fieldState = reactive({
    evalType: FIELD_STATE.PENDING,
    evalTypeConfidence: FIELD_STATE.PENDING,
    evalTypeReasoning: FIELD_STATE.PENDING,
    scenarioName: FIELD_STATE.PENDING,
    scenarioDescription: FIELD_STATE.PENDING,
    configSuggestions: FIELD_STATE.PENDING,
    dataQuality: FIELD_STATE.PENDING
  })

  // Overall streaming state
  const isStreaming = ref(false)
  const isComplete = ref(false)
  const error = ref(null)

  /**
   * Extract a simple value field from the buffer.
   * Looks for patterns like: "field_name": "value" or "field_name": 0.85
   */
  function extractSimpleField(fieldName, setter) {
    // Pattern for string values
    const stringPattern = new RegExp(`"${fieldName}"\\s*:\\s*"([^"]*)"`)
    const stringMatch = buffer.value.match(stringPattern)
    if (stringMatch) {
      setter(stringMatch[1])
      return true
    }

    // Pattern for number values
    const numberPattern = new RegExp(`"${fieldName}"\\s*:\\s*([0-9.]+)`)
    const numberMatch = buffer.value.match(numberPattern)
    if (numberMatch) {
      setter(parseFloat(numberMatch[1]))
      return true
    }

    return false
  }

  /**
   * Extract a streaming text field that may be incomplete.
   * Returns partial content as it streams in.
   */
  function extractStreamingField(fieldName) {
    // Find the start of the field
    const startPattern = new RegExp(`"${fieldName}"\\s*:\\s*"`)
    const startMatch = buffer.value.match(startPattern)
    if (!startMatch) return null

    const startIndex = startMatch.index + startMatch[0].length
    const remaining = buffer.value.slice(startIndex)

    // Find the end quote (not escaped)
    let endIndex = -1
    let escaped = false
    for (let i = 0; i < remaining.length; i++) {
      if (escaped) {
        escaped = false
        continue
      }
      if (remaining[i] === '\\') {
        escaped = true
        continue
      }
      if (remaining[i] === '"') {
        endIndex = i
        break
      }
    }

    // Return partial or complete content
    if (endIndex === -1) {
      // Still streaming - return partial content
      return { value: remaining.replace(/\\n/g, '\n').replace(/\\"/g, '"'), complete: false }
    } else {
      // Complete
      return { value: remaining.slice(0, endIndex).replace(/\\n/g, '\n').replace(/\\"/g, '"'), complete: true }
    }
  }

  /**
   * Process a new chunk from the stream.
   * Extraction order matches UI display order (top-to-bottom, left-to-right):
   * 1. eval_type + confidence (EvalTypeCard - top left)
   * 2. scenario_name + description (ScenarioSuggestionCard - top right)
   * 3. eval_type_reasoning (ReasoningCard - middle)
   * 4. config_suggestions (for Configuration step)
   * 5. data_quality (DataQualityCard - bottom right)
   */
  function processChunk(chunk) {
    buffer.value += chunk
    isStreaming.value = true

    // 1. Extract eval_type (EvalTypeCard - top left)
    if (fieldState.evalType !== FIELD_STATE.COMPLETE) {
      if (extractSimpleField('eval_type', (v) => { parsed.evalType = v })) {
        fieldState.evalType = FIELD_STATE.COMPLETE
      }
    }

    // 2. Extract eval_type_confidence (EvalTypeCard - top left)
    if (fieldState.evalTypeConfidence !== FIELD_STATE.COMPLETE) {
      if (extractSimpleField('eval_type_confidence', (v) => { parsed.evalTypeConfidence = v })) {
        fieldState.evalTypeConfidence = FIELD_STATE.COMPLETE
      }
    }

    // 3. Extract scenario_name (ScenarioSuggestionCard - top right)
    if (fieldState.scenarioName !== FIELD_STATE.COMPLETE) {
      const result = extractStreamingField('scenario_name')
      if (result) {
        parsed.scenarioName = result.value
        fieldState.scenarioName = result.complete ? FIELD_STATE.COMPLETE : FIELD_STATE.STREAMING
      }
    }

    // 4. Extract scenario_description (ScenarioSuggestionCard - top right)
    if (fieldState.scenarioDescription !== FIELD_STATE.COMPLETE) {
      const result = extractStreamingField('scenario_description')
      if (result) {
        parsed.scenarioDescription = result.value
        fieldState.scenarioDescription = result.complete ? FIELD_STATE.COMPLETE : FIELD_STATE.STREAMING
      }
    }

    // 5. Extract eval_type_reasoning (ReasoningCard - middle, full width)
    if (fieldState.evalTypeReasoning !== FIELD_STATE.COMPLETE) {
      const result = extractStreamingField('eval_type_reasoning')
      if (result) {
        parsed.evalTypeReasoning = result.value
        fieldState.evalTypeReasoning = result.complete ? FIELD_STATE.COMPLETE : FIELD_STATE.STREAMING
      }
    }

    // 6. Detect config_suggestions start (for Configuration step)
    if (fieldState.configSuggestions === FIELD_STATE.PENDING) {
      const configStart = buffer.value.match(/"config_suggestions"\s*:\s*\{/)
      if (configStart) {
        fieldState.configSuggestions = FIELD_STATE.STREAMING
      }
    }
  }

  /**
   * Process the suggestions event (complete parsed JSON).
   */
  function processSuggestions(suggestions) {
    if (suggestions.eval_type) {
      parsed.evalType = suggestions.eval_type
      fieldState.evalType = FIELD_STATE.COMPLETE
    }
    if (suggestions.eval_type_confidence !== undefined) {
      parsed.evalTypeConfidence = suggestions.eval_type_confidence
      fieldState.evalTypeConfidence = FIELD_STATE.COMPLETE
    }
    if (suggestions.eval_type_reasoning) {
      parsed.evalTypeReasoning = suggestions.eval_type_reasoning
      fieldState.evalTypeReasoning = FIELD_STATE.COMPLETE
    }
    if (suggestions.scenario_name) {
      parsed.scenarioName = suggestions.scenario_name
      fieldState.scenarioName = FIELD_STATE.COMPLETE
    }
    if (suggestions.scenario_description) {
      parsed.scenarioDescription = suggestions.scenario_description
      fieldState.scenarioDescription = FIELD_STATE.COMPLETE
    }
    if (suggestions.config_suggestions) {
      parsed.configSuggestions = suggestions.config_suggestions
      fieldState.configSuggestions = FIELD_STATE.COMPLETE
    }
  }

  /**
   * Process the data_quality event.
   */
  function processDataQuality(dataQuality) {
    parsed.dataQuality = dataQuality
    fieldState.dataQuality = FIELD_STATE.COMPLETE
  }

  /**
   * Mark streaming as complete.
   */
  function finalize() {
    isStreaming.value = false
    isComplete.value = true

    // Mark any remaining fields as complete
    Object.keys(fieldState).forEach(key => {
      if (fieldState[key] !== FIELD_STATE.COMPLETE) {
        fieldState[key] = FIELD_STATE.COMPLETE
      }
    })
  }

  /**
   * Set error state.
   */
  function setError(err) {
    error.value = err
    isStreaming.value = false
  }

  /**
   * Reset the parser state.
   */
  function reset() {
    buffer.value = ''
    parsed.evalType = null
    parsed.evalTypeConfidence = null
    parsed.evalTypeReasoning = ''
    parsed.scenarioName = ''
    parsed.scenarioDescription = ''
    parsed.dataQuality = null
    parsed.configSuggestions = null

    Object.keys(fieldState).forEach(key => {
      fieldState[key] = FIELD_STATE.PENDING
    })

    isStreaming.value = false
    isComplete.value = false
    error.value = null
  }

  // Computed helpers
  const confidencePercent = computed(() => {
    if (parsed.evalTypeConfidence === null) return 0
    return Math.round(parsed.evalTypeConfidence * 100)
  })

  const hasAnyContent = computed(() => {
    return parsed.evalType ||
           parsed.scenarioName ||
           parsed.scenarioDescription ||
           parsed.evalTypeReasoning
  })

  return {
    // State
    buffer,
    parsed,
    fieldState,
    isStreaming,
    isComplete,
    error,

    // Computed
    confidencePercent,
    hasAnyContent,

    // Methods
    processChunk,
    processSuggestions,
    processDataQuality,
    finalize,
    setError,
    reset,

    // Constants
    FIELD_STATE
  }
}
