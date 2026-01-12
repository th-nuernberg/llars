/**
 * usePromptVariables - Generisches Variablen-System für Prompt-Testing
 *
 * Extrahiert {{variablen}} aus Prompts und ermöglicht das Befüllen mit beliebigen Daten.
 * Komplett agnostisch - macht keine Annahmen über Variablennamen oder Datenformate.
 *
 * Features:
 * - Automatische Extraktion von {{variablen}} aus Prompt-Text
 * - Persistierung der Werte pro Prompt (optional mit promptId)
 * - Default-Werte und Beschreibungen für Variablen
 * - Unterstützung für manuelle Eingabe, Datei-Upload und Datasets
 *
 * @example
 * // Einfache Nutzung (ohne Persistierung)
 * const { variables, values, setValue, resolvedPrompt } = usePromptVariables(promptText)
 *
 * // Mit Persistierung pro Prompt
 * const { variables, values, setValue, resolvedPrompt } = usePromptVariables(promptText, { promptId: 123 })
 *
 * // Variablen werden automatisch erkannt
 * console.log(variables.value) // [{ name: 'input_data', occurrences: 2, ... }]
 *
 * // Werte setzen (werden automatisch persistiert wenn promptId gesetzt)
 * setValue('input_data', 'Mein Text hier...')
 * setValue('output_format', 'JSON')
 *
 * // Default-Wert und Beschreibung setzen
 * setVariableConfig('input_data', { defaultValue: 'Beispiel...', description: 'Die Eingabedaten' })
 *
 * // Aufgelöster Prompt
 * console.log(resolvedPrompt.value) // Prompt mit ersetzten Variablen
 */

import { ref, computed, watch, toValue } from 'vue'

// Storage key prefix for variable persistence
const STORAGE_KEY_PREFIX = 'llars_prompt_variables_'

// Storage key for variable configurations (defaults, descriptions)
const CONFIG_STORAGE_KEY_PREFIX = 'llars_prompt_var_config_'

/**
 * Evaluiert einen einfachen JSON-Pfad auf einem Objekt.
 * Unterstützt: $.field, $.nested.field, $.array[0], $.array[*] (join mit \n)
 *
 * @param {Object} data - Das Datenobjekt
 * @param {string} path - Der JSON-Pfad (z.B. "$.messages[0].content")
 * @returns {*} Der Wert am Pfad oder undefined
 */
function evaluateJsonPath(data, path) {
  if (!path || path === '$') return data

  // Entferne führendes "$."
  const cleanPath = path.startsWith('$.') ? path.slice(2) : path

  const parts = cleanPath.split(/\.(?![^\[]*\])/)
  let current = data

  for (const part of parts) {
    if (current === undefined || current === null) return undefined

    // Array-Zugriff: field[0] oder field[*]
    const arrayMatch = part.match(/^([^[]+)\[(\d+|\*)\]$/)
    if (arrayMatch) {
      const [, fieldName, indexOrStar] = arrayMatch
      current = current[fieldName]

      if (!Array.isArray(current)) return undefined

      if (indexOrStar === '*') {
        // Alle Array-Elemente joinen
        return current.map(item =>
          typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item)
        ).join('\n\n')
      } else {
        current = current[parseInt(indexOrStar)]
      }
    } else {
      current = current[part]
    }
  }

  return current
}

/**
 * Formatiert einen Wert für die Prompt-Ersetzung.
 *
 * @param {*} value - Der zu formatierende Wert
 * @returns {string} Der formatierte String
 */
function formatValue(value) {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

/**
 * Hauptfunktion: Variablen-Management für Prompts
 *
 * @param {Ref<string>|ComputedRef<string>|string} promptText - Reaktiver Prompt-Text
 * @param {Object} options - Optionale Konfiguration
 * @param {string|number|Ref<string|number>} options.promptId - Prompt-ID für Persistierung (optional)
 * @param {boolean} options.autoPersist - Automatische Persistierung aktivieren (default: true wenn promptId gesetzt)
 * @returns {Object} Variablen-Management-Objekt
 */
export function usePromptVariables(promptText, options = {}) {
  const { promptId = null, autoPersist = true } = options

  // Alle erkannten Variablen (aus Prompt-Text extrahiert)
  const variables = ref([])

  // Manuell erstellte Variablen (vom Benutzer hinzugefügt)
  const manualVariables = ref([])

  // Werte für jede Variable
  const values = ref({})

  // Metadaten für Variablen (Quelle, Datei-Info, etc.)
  const metadata = ref({})

  // Variablen-Konfiguration (Default-Werte, Beschreibungen)
  const variableConfig = ref({})

  // Flag ob initiales Laden abgeschlossen ist
  const isLoaded = ref(false)

  // Invalid variable names to filter out (corrupted data, JS reserved words)
  const INVALID_VARIABLE_NAMES = new Set([
    'undefined', 'null', 'true', 'false', 'NaN', 'Infinity',
    'Object', 'Array', 'String', 'Number', 'Boolean', 'Function'
  ])

  /**
   * Gibt die aktuelle promptId zurück (unterstützt reactive refs)
   */
  const getPromptId = () => {
    const id = toValue(promptId)
    return id ? String(id) : null
  }

  /**
   * Prüft ob ein Variablenname gültig ist
   */
  const isValidVariableName = (name) => {
    if (!name || typeof name !== 'string') return false
    if (INVALID_VARIABLE_NAMES.has(name)) return false
    if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(name)) return false
    return true
  }

  /**
   * Filtert ungültige Einträge aus einem Objekt
   */
  const filterValidEntries = (obj) => {
    if (!obj || typeof obj !== 'object') return {}
    const filtered = {}
    for (const [key, value] of Object.entries(obj)) {
      if (isValidVariableName(key)) {
        filtered[key] = value
      }
    }
    return filtered
  }

  /**
   * Lädt persistierte Werte aus localStorage
   * Bereinigt korrupte Daten und persistiert bereinigte Version zurück
   */
  const loadFromStorage = () => {
    const id = getPromptId()
    if (!id) return

    let needsCleanup = false

    try {
      // Lade Werte
      const storedValues = localStorage.getItem(`${STORAGE_KEY_PREFIX}${id}`)
      if (storedValues) {
        const parsed = JSON.parse(storedValues)
        if (parsed && typeof parsed === 'object') {
          const originalValuesCount = Object.keys(parsed.values || {}).length
          const originalMetaCount = Object.keys(parsed.metadata || {}).length

          // Filtere ungültige Variablen-Namen heraus
          values.value = filterValidEntries(parsed.values || {})
          metadata.value = filterValidEntries(parsed.metadata || {})

          // Prüfe ob Daten bereinigt wurden
          if (Object.keys(values.value).length !== originalValuesCount ||
              Object.keys(metadata.value).length !== originalMetaCount) {
            needsCleanup = true
            console.info('[usePromptVariables] Cleaned up corrupted storage entries')
          }
        }
      }

      // Lade Konfiguration (Defaults, Beschreibungen)
      const storedConfig = localStorage.getItem(`${CONFIG_STORAGE_KEY_PREFIX}${id}`)
      if (storedConfig) {
        const parsed = JSON.parse(storedConfig)
        if (parsed && typeof parsed === 'object') {
          const originalConfigCount = Object.keys(parsed).length

          // Filtere ungültige Variablen-Namen heraus
          variableConfig.value = filterValidEntries(parsed)

          // Prüfe ob Daten bereinigt wurden
          if (Object.keys(variableConfig.value).length !== originalConfigCount) {
            needsCleanup = true
            console.info('[usePromptVariables] Cleaned up corrupted config entries')
          }
        }
      }

      // Lade manuell erstellte Variablen
      const storedManual = localStorage.getItem(`${STORAGE_KEY_PREFIX}${id}_manual`)
      if (storedManual) {
        const parsed = JSON.parse(storedManual)
        if (Array.isArray(parsed)) {
          const originalCount = parsed.length
          manualVariables.value = parsed.filter(v =>
            v && typeof v === 'object' && isValidVariableName(v.name)
          )
          if (manualVariables.value.length !== originalCount) {
            needsCleanup = true
            console.info('[usePromptVariables] Cleaned up corrupted manual variables')
          }
        }
      }

      // Persistiere bereinigte Daten zurück
      if (needsCleanup) {
        saveToStorage()
      }
    } catch (e) {
      console.warn('[usePromptVariables] Failed to load from storage:', e)
    }

    isLoaded.value = true
  }

  /**
   * Speichert Werte in localStorage
   */
  const saveToStorage = () => {
    const id = getPromptId()
    if (!id || !autoPersist) return

    try {
      // Speichere Werte und Metadaten
      const data = {
        values: values.value,
        metadata: metadata.value,
        updatedAt: new Date().toISOString()
      }
      localStorage.setItem(`${STORAGE_KEY_PREFIX}${id}`, JSON.stringify(data))

      // Speichere Konfiguration separat
      if (Object.keys(variableConfig.value).length > 0) {
        localStorage.setItem(`${CONFIG_STORAGE_KEY_PREFIX}${id}`, JSON.stringify(variableConfig.value))
      }

      // Speichere manuell erstellte Variablen
      if (manualVariables.value.length > 0) {
        localStorage.setItem(`${STORAGE_KEY_PREFIX}${id}_manual`, JSON.stringify(manualVariables.value))
      } else {
        localStorage.removeItem(`${STORAGE_KEY_PREFIX}${id}_manual`)
      }
    } catch (e) {
      console.warn('[usePromptVariables] Failed to save to storage:', e)
    }
  }

  /**
   * Löscht persistierte Daten aus localStorage
   */
  const clearStorage = () => {
    const id = getPromptId()
    if (!id) return

    try {
      localStorage.removeItem(`${STORAGE_KEY_PREFIX}${id}`)
      localStorage.removeItem(`${CONFIG_STORAGE_KEY_PREFIX}${id}`)
      localStorage.removeItem(`${STORAGE_KEY_PREFIX}${id}_manual`)
    } catch (e) {
      console.warn('[usePromptVariables] Failed to clear storage:', e)
    }
  }

  /**
   * Extrahiert alle {{variablen}} aus dem Prompt-Text.
   * Komplett agnostisch - keine Annahmen über Bedeutung.
   * Filtert ungültige Namen wie "undefined" heraus.
   * Reichert Variablen mit Konfiguration (Default, Beschreibung) an.
   */
  const extract = () => {
    const text = toValue(promptText) || ''
    const regex = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g
    const found = new Map()
    let match

    while ((match = regex.exec(text)) !== null) {
      const name = match[1]

      // Skip invalid/corrupted variable names
      if (INVALID_VARIABLE_NAMES.has(name)) {
        continue
      }

      if (!found.has(name)) {
        // Hole Konfiguration für diese Variable (falls vorhanden)
        const config = variableConfig.value[name] || {}

        found.set(name, {
          name,
          occurrences: 1,
          positions: [match.index],
          // Konfiguration aus Storage
          defaultValue: config.defaultValue || '',
          description: config.description || '',
          type: config.type || 'text'
        })
      } else {
        const existing = found.get(name)
        existing.occurrences++
        existing.positions.push(match.index)
      }
    }

    variables.value = Array.from(found.values())

    // Wende Default-Werte an für Variablen ohne Wert
    applyDefaults()
  }

  /**
   * Wendet Default-Werte auf Variablen an, die noch keinen Wert haben.
   */
  const applyDefaults = () => {
    for (const variable of variables.value) {
      const hasValue = values.value[variable.name] !== undefined &&
                       values.value[variable.name] !== null &&
                       values.value[variable.name] !== ''

      if (!hasValue && variable.defaultValue) {
        // Setze Default-Wert ohne zu persistieren (um Endlosschleife zu vermeiden)
        values.value = {
          ...values.value,
          [variable.name]: variable.defaultValue
        }
        metadata.value = {
          ...metadata.value,
          [variable.name]: { source: 'default' }
        }
      }
    }
  }

  /**
   * Setzt den Wert einer Variable.
   *
   * @param {string} varName - Name der Variable
   * @param {*} value - Der Wert (String, Object, Array, etc.)
   * @param {Object} meta - Optionale Metadaten (source, fileName, etc.)
   */
  const setValue = (varName, value, meta = {}) => {
    // Validiere Variablennamen
    if (!isValidVariableName(varName)) {
      console.warn('[usePromptVariables] Invalid variable name rejected:', varName)
      return
    }

    values.value = { ...values.value, [varName]: value }
    if (Object.keys(meta).length > 0) {
      metadata.value = { ...metadata.value, [varName]: meta }
    }

    // Persistiere wenn aktiviert
    if (getPromptId() && autoPersist) {
      saveToStorage()
    }
  }

  /**
   * Setzt die Konfiguration einer Variable (Default-Wert, Beschreibung, Typ).
   *
   * @param {string} varName - Name der Variable
   * @param {Object} config - Konfigurationsobjekt
   * @param {string} config.defaultValue - Default-Wert für die Variable
   * @param {string} config.description - Beschreibung der Variable
   * @param {string} config.type - Typ: 'text' | 'json' | 'file'
   */
  const setVariableConfig = (varName, config = {}) => {
    // Validiere Variablennamen
    if (!isValidVariableName(varName)) {
      console.warn('[usePromptVariables] Invalid variable name rejected for config:', varName)
      return
    }

    const existing = variableConfig.value[varName] || {}
    variableConfig.value = {
      ...variableConfig.value,
      [varName]: {
        ...existing,
        ...config,
        updatedAt: new Date().toISOString()
      }
    }

    // Aktualisiere die Variable in der Liste
    const varIndex = variables.value.findIndex(v => v.name === varName)
    if (varIndex !== -1) {
      variables.value[varIndex] = {
        ...variables.value[varIndex],
        defaultValue: config.defaultValue ?? variables.value[varIndex].defaultValue,
        description: config.description ?? variables.value[varIndex].description,
        type: config.type ?? variables.value[varIndex].type
      }
    }

    // Persistiere wenn aktiviert
    if (getPromptId() && autoPersist) {
      saveToStorage()
    }
  }

  /**
   * Holt die Konfiguration einer Variable.
   *
   * @param {string} varName - Name der Variable
   * @returns {Object} Konfigurationsobjekt oder leeres Objekt
   */
  const getVariableConfig = (varName) => {
    return variableConfig.value[varName] || {}
  }

  /**
   * Fügt eine manuell erstellte Variable hinzu.
   * Diese Variable existiert nicht im Prompt-Text, kann aber Werte erhalten.
   *
   * @param {string} varName - Name der Variable
   * @param {Object} config - Optionale Konfiguration (description, defaultValue, type)
   * @returns {boolean} true wenn erfolgreich, false wenn Name ungültig oder bereits existiert
   */
  const addManualVariable = (varName, config = {}) => {
    // Validiere Variablennamen
    if (!isValidVariableName(varName)) {
      console.warn('[usePromptVariables] Invalid variable name rejected:', varName)
      return false
    }

    // Prüfe ob Variable bereits existiert (in extrahierten oder manuellen)
    const existsInExtracted = variables.value.some(v => v.name === varName)
    const existsInManual = manualVariables.value.some(v => v.name === varName)

    if (existsInExtracted || existsInManual) {
      console.warn('[usePromptVariables] Variable already exists:', varName)
      return false
    }

    // Füge neue manuelle Variable hinzu
    const newVar = {
      name: varName,
      occurrences: 0,
      positions: [],
      defaultValue: config.defaultValue || '',
      description: config.description || '',
      type: config.type || 'text',
      isManual: true,
      createdAt: new Date().toISOString()
    }

    manualVariables.value = [...manualVariables.value, newVar]

    // Speichere Konfiguration
    if (config.defaultValue || config.description || config.type) {
      setVariableConfig(varName, config)
    }

    // Persistiere
    if (getPromptId() && autoPersist) {
      saveToStorage()
    }

    return true
  }

  /**
   * Entfernt eine manuell erstellte Variable.
   *
   * @param {string} varName - Name der Variable
   * @returns {boolean} true wenn erfolgreich entfernt
   */
  const removeManualVariable = (varName) => {
    const index = manualVariables.value.findIndex(v => v.name === varName)
    if (index === -1) {
      return false
    }

    // Entferne Variable
    manualVariables.value = manualVariables.value.filter(v => v.name !== varName)

    // Lösche auch den Wert und Metadaten
    clearValue(varName)

    // Persistiere
    if (getPromptId() && autoPersist) {
      saveToStorage()
    }

    return true
  }

  /**
   * Setzt den Wert einer Variable aus einer hochgeladenen Datei.
   *
   * @param {string} varName - Name der Variable
   * @param {*} fileContent - Geparster Dateiinhalt
   * @param {string} jsonPath - Optionaler JSON-Pfad (z.B. "$.messages")
   * @param {string} fileName - Name der Originaldatei
   */
  const setFromFile = (varName, fileContent, jsonPath = null, fileName = '') => {
    let value = fileContent

    if (jsonPath && typeof fileContent === 'object') {
      value = evaluateJsonPath(fileContent, jsonPath)
    }

    setValue(varName, value, {
      source: 'file',
      fileName,
      jsonPath
    })
  }

  /**
   * Setzt Werte aus einem Dataset-Item.
   *
   * @param {Object} item - Dataset-Item mit variables-Objekt
   */
  const setFromDatasetItem = (item) => {
    if (!item || !item.variables) return

    for (const [varName, value] of Object.entries(item.variables)) {
      setValue(varName, value, {
        source: 'dataset',
        datasetItemId: item.id,
        datasetItemName: item.name
      })
    }
  }

  /**
   * Löscht den Wert einer Variable.
   *
   * @param {string} varName - Name der Variable
   */
  const clearValue = (varName) => {
    const newValues = { ...values.value }
    delete newValues[varName]
    values.value = newValues

    const newMeta = { ...metadata.value }
    delete newMeta[varName]
    metadata.value = newMeta
  }

  /**
   * Löscht alle Werte.
   */
  const clearAll = () => {
    values.value = {}
    metadata.value = {}
  }

  /**
   * Berechnet den aufgelösten Prompt mit allen ersetzten Variablen.
   */
  const resolvedPrompt = computed(() => {
    const text = typeof promptText === 'string' ? promptText : promptText.value || ''
    let result = text

    for (const variable of variables.value) {
      const value = values.value[variable.name]
      if (value !== undefined && value !== null) {
        const placeholder = new RegExp(`\\{\\{${variable.name}\\}\\}`, 'g')
        result = result.replace(placeholder, formatValue(value))
      }
    }

    return result
  })

  /**
   * Validierte Variablen-Liste - garantiert nur gültige Objekte.
   * Filtert alle korrupten Einträge heraus (Booleans, Strings, null, etc.).
   * Merged extrahierte und manuell erstellte Variablen.
   */
  const validVariables = computed(() => {
    const extractedValid = Array.isArray(variables.value)
      ? variables.value.filter(v => {
          if (!v || typeof v !== 'object') return false
          if (!v.name || typeof v.name !== 'string') return false
          if (!isValidVariableName(v.name)) return false
          return true
        })
      : []

    const manualValid = Array.isArray(manualVariables.value)
      ? manualVariables.value.filter(v => {
          if (!v || typeof v !== 'object') return false
          if (!v.name || typeof v.name !== 'string') return false
          if (!isValidVariableName(v.name)) return false
          return true
        })
      : []

    // Merge: Extrahierte zuerst, dann manuelle (die nicht im Prompt sind)
    const extractedNames = new Set(extractedValid.map(v => v.name))
    const manualNotInPrompt = manualValid.filter(v => !extractedNames.has(v.name))

    // Markiere extrahierte als "isExtracted" und manuelle als "isManual"
    const result = [
      ...extractedValid.map(v => ({ ...v, isExtracted: true, isManual: false })),
      ...manualNotInPrompt.map(v => ({ ...v, isExtracted: false, isManual: true }))
    ]

    return result
  })

  /**
   * Prüft ob alle Variablen einen Wert haben.
   */
  const allFilled = computed(() => {
    return validVariables.value.every(v => {
      const value = values.value[v.name]
      return value !== undefined && value !== null && value !== ''
    })
  })

  /**
   * Liste der noch nicht gefüllten Variablen.
   */
  const unfilledVariables = computed(() => {
    return validVariables.value.filter(v => {
      const value = values.value[v.name]
      return value === undefined || value === null || value === ''
    })
  })

  /**
   * Liste der gefüllten Variablen mit Metadaten.
   */
  const filledVariables = computed(() => {
    return validVariables.value
      .filter(v => {
        const value = values.value[v.name]
        return value !== undefined && value !== null && value !== ''
      })
      .map(v => ({
        ...v,
        value: values.value[v.name],
        meta: metadata.value[v.name] || {}
      }))
  })

  /**
   * Statistiken über Variablen.
   */
  const stats = computed(() => ({
    total: validVariables.value.length,
    filled: filledVariables.value.length,
    unfilled: unfilledVariables.value.length,
    percentFilled: validVariables.value.length > 0
      ? Math.round((filledVariables.value.length / validVariables.value.length) * 100)
      : 100
  }))

  /**
   * Gibt den formatierten Wert einer Variable zurück.
   *
   * @param {string} varName - Name der Variable
   * @returns {string} Formatierter Wert oder leerer String
   */
  const getFormattedValue = (varName) => {
    const value = values.value[varName]
    return formatValue(value)
  }

  /**
   * Gibt eine Vorschau des Werts zurück (gekürzt wenn zu lang).
   *
   * @param {string} varName - Name der Variable
   * @param {number} maxLength - Maximale Länge
   * @returns {string} Gekürzte Vorschau
   */
  const getValuePreview = (varName, maxLength = 100) => {
    const formatted = getFormattedValue(varName)
    if (formatted.length <= maxLength) return formatted
    return formatted.slice(0, maxLength) + '...'
  }

  // Initialisierung: Lade persistierte Daten
  if (getPromptId()) {
    loadFromStorage()
  } else {
    isLoaded.value = true
  }

  // Variablen bei Änderung des Prompts neu extrahieren
  watch(
    () => toValue(promptText),
    () => {
      extract()
    },
    { immediate: true }
  )

  // Bei Änderung der promptId neu laden
  watch(
    () => toValue(promptId),
    (newId, oldId) => {
      if (newId !== oldId && newId) {
        loadFromStorage()
        extract()
      }
    }
  )

  return {
    // State
    variables,
    manualVariables,
    validVariables, // Safe version that merges extracted + manual and filters corrupted entries
    values,
    metadata,
    variableConfig,
    isLoaded,

    // Setter
    setValue,
    setVariableConfig,
    setFromFile,
    setFromDatasetItem,
    clearValue,
    clearAll,

    // Manual Variable Management
    addManualVariable,
    removeManualVariable,

    // Config
    getVariableConfig,

    // Persistence
    loadFromStorage,
    saveToStorage,
    clearStorage,

    // Computed
    resolvedPrompt,
    allFilled,
    unfilledVariables,
    filledVariables,
    stats,

    // Helpers
    getFormattedValue,
    getValuePreview,
    extract,

    // Utils
    getPromptId,
    isValidVariableName
  }
}

/**
 * Hilfsfunktion: Analysiert die Struktur einer JSON-Datei.
 * Gibt navigierbare Pfade zurück.
 *
 * @param {*} data - Das zu analysierende Datenobjekt
 * @param {string} prefix - Aktueller Pfad-Prefix
 * @param {number} maxDepth - Maximale Tiefe
 * @returns {Array<{path: string, type: string, preview: string}>}
 */
export function analyzeJsonStructure(data, prefix = '$', maxDepth = 3) {
  const paths = []

  function traverse(obj, currentPath, depth) {
    if (depth > maxDepth) return

    if (Array.isArray(obj)) {
      paths.push({
        path: currentPath,
        type: 'array',
        length: obj.length,
        preview: `Array[${obj.length}]`
      })

      // Erstes Element analysieren für Struktur
      if (obj.length > 0 && typeof obj[0] === 'object') {
        traverse(obj[0], `${currentPath}[0]`, depth + 1)
      }

      // Wildcard-Pfad für alle Elemente
      if (obj.length > 0) {
        paths.push({
          path: `${currentPath}[*]`,
          type: 'array_all',
          preview: `Alle ${obj.length} Elemente`
        })
      }
    } else if (obj !== null && typeof obj === 'object') {
      paths.push({
        path: currentPath,
        type: 'object',
        keys: Object.keys(obj).length,
        preview: `Object{${Object.keys(obj).slice(0, 3).join(', ')}${Object.keys(obj).length > 3 ? '...' : ''}}`
      })

      for (const [key, value] of Object.entries(obj)) {
        traverse(value, `${currentPath}.${key}`, depth + 1)
      }
    } else {
      const type = typeof obj
      let preview = String(obj)
      if (preview.length > 50) {
        preview = preview.slice(0, 50) + '...'
      }

      paths.push({
        path: currentPath,
        type,
        preview
      })
    }
  }

  traverse(data, prefix, 0)
  return paths
}

/**
 * Hilfsfunktion: Parst Dateiinhalt basierend auf Dateiendung.
 *
 * @param {string} fileName - Name der Datei
 * @param {string} content - Roher Dateiinhalt
 * @returns {{data: *, type: string, error: string|null}}
 */
export function parseFileContent(fileName, content) {
  const ext = fileName.split('.').pop().toLowerCase()

  try {
    switch (ext) {
      case 'json':
        return {
          data: JSON.parse(content),
          type: 'json',
          error: null
        }

      case 'csv': {
        const lines = content.trim().split('\n')
        if (lines.length === 0) {
          return { data: [], type: 'csv', error: null }
        }

        const headers = lines[0].split(',').map(h => h.trim().replace(/^["']|["']$/g, ''))
        const rows = lines.slice(1).map(line => {
          const values = line.split(',').map(v => v.trim().replace(/^["']|["']$/g, ''))
          const row = {}
          headers.forEach((header, i) => {
            row[header] = values[i] || ''
          })
          return row
        })

        return {
          data: rows,
          type: 'csv',
          error: null
        }
      }

      case 'txt':
      case 'md':
        return {
          data: content,
          type: 'text',
          error: null
        }

      default:
        return {
          data: content,
          type: 'unknown',
          error: null
        }
    }
  } catch (e) {
    return {
      data: null,
      type: ext,
      error: e.message
    }
  }
}

export default usePromptVariables
