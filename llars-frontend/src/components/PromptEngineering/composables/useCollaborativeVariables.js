import { ref, watch } from 'vue'
import * as Y from 'yjs'

/**
 * Composable for collaborative variable management using Yjs
 * Variables are stored in the Yjs document and synchronized across all users
 */
export function useCollaborativeVariables(ydoc, showMessage, t) {
  const translate = typeof t === 'function' ? t : (key) => key
  const variables = ref([])

  // Valid variable name regex
  const VALID_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_]*$/
  const INVALID_NAMES = new Set([
    'undefined', 'null', 'true', 'false', 'NaN', 'Infinity'
  ])

  /**
   * Load variables from Y.Doc into local ref
   */
  const processYDoc = () => {
    if (!ydoc.value) return

    const variablesMap = ydoc.value.getMap('variables')
    const newVariables = []

    variablesMap.forEach((value, key) => {
      // value is a Y.Map containing name, content, createdAt, updatedAt
      newVariables.push({
        name: key,
        content: value.get('content') || '',
        createdAt: value.get('createdAt'),
        updatedAt: value.get('updatedAt')
      })
    })

    // Sort by creation date
    newVariables.sort((a, b) => {
      const dateA = a.createdAt ? new Date(a.createdAt) : new Date(0)
      const dateB = b.createdAt ? new Date(b.createdAt) : new Date(0)
      return dateA - dateB
    })

    variables.value = newVariables
  }

  /**
   * Set up observer for variables map changes
   */
  const setupObserver = () => {
    if (!ydoc.value) return

    const variablesMap = ydoc.value.getMap('variables')

    // Observe changes to the variables map
    variablesMap.observeDeep(() => {
      processYDoc()
    })

    // Initial load
    processYDoc()
  }

  /**
   * Create a new variable
   */
  const createVariable = (name, content = '') => {
    const trimmedName = name.trim()

    if (!trimmedName) {
      return { success: false, error: 'nameRequired' }
    }

    if (!VALID_NAME_REGEX.test(trimmedName)) {
      return { success: false, error: 'invalidName' }
    }

    if (INVALID_NAMES.has(trimmedName)) {
      return { success: false, error: 'reservedName' }
    }

    if (!ydoc.value) {
      console.error('No Y.Doc available to create variable')
      return { success: false, error: 'noYdoc' }
    }

    let success = false

    ydoc.value.transact(() => {
      const variablesMap = ydoc.value.getMap('variables')

      // Check if variable already exists
      if (variablesMap.has(trimmedName)) {
        return { success: false, error: 'nameExists' }
      }

      // Create new variable entry
      const varMap = new Y.Map()
      varMap.set('content', content)
      varMap.set('createdAt', new Date().toISOString())

      variablesMap.set(trimmedName, varMap)
      success = true
    })

    if (success && showMessage) {
      showMessage(translate('promptEngineering.variables.created', { name: trimmedName }))
    }

    return { success, error: success ? null : 'nameExists' }
  }

  /**
   * Update a variable's content (upsert: creates if not exists)
   */
  const updateVariable = (name, content) => {
    if (!ydoc.value) {
      console.error('No Y.Doc available to update variable')
      return false
    }

    let success = false

    ydoc.value.transact(() => {
      const variablesMap = ydoc.value.getMap('variables')
      let varMap = variablesMap.get(name)

      if (varMap) {
        varMap.set('content', content)
        varMap.set('updatedAt', new Date().toISOString())
        success = true
      } else {
        // Auto-create variable if it doesn't exist yet (e.g. extracted from prompt text)
        varMap = new Y.Map()
        varMap.set('content', content)
        varMap.set('createdAt', new Date().toISOString())
        variablesMap.set(name, varMap)
        success = true
      }
    })

    return success
  }

  /**
   * Delete a variable
   */
  const deleteVariable = (name) => {
    if (!ydoc.value) {
      console.error('No Y.Doc available to delete variable')
      return false
    }

    let success = false

    ydoc.value.transact(() => {
      const variablesMap = ydoc.value.getMap('variables')

      if (variablesMap.has(name)) {
        variablesMap.delete(name)
        success = true
      }
    })

    if (success && showMessage) {
      showMessage(translate('promptEngineering.variables.deleted', { name }))
    }

    return success
  }

  /**
   * Get a variable by name
   */
  const getVariable = (name) => {
    return variables.value.find(v => v.name === name)
  }

  /**
   * Check if a variable name is valid
   */
  const isValidName = (name) => {
    const trimmed = name.trim()
    if (!trimmed) return false
    if (!VALID_NAME_REGEX.test(trimmed)) return false
    if (INVALID_NAMES.has(trimmed)) return false
    return true
  }

  /**
   * Check if a variable name already exists
   */
  const variableExists = (name) => {
    return variables.value.some(v => v.name === name)
  }

  // Watch for ydoc changes and set up observer
  watch(
    () => ydoc.value,
    (newYdoc) => {
      if (newYdoc) {
        setupObserver()
      }
    },
    { immediate: true }
  )

  return {
    variables,
    processYDoc,
    createVariable,
    updateVariable,
    deleteVariable,
    getVariable,
    isValidName,
    variableExists
  }
}
