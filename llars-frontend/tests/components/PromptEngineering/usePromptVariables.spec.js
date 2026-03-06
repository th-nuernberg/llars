/**
 * usePromptVariables Composable Tests
 *
 * Tests for the generic variable system for prompt testing.
 * Test IDs: PVAR_001 - PVAR_060
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import {
  usePromptVariables,
  analyzeJsonStructure,
  parseFileContent
} from '@/components/PromptEngineering/composables/usePromptVariables'

describe('usePromptVariables', () => {
  beforeEach(() => {
    // Reset localStorage mock
    localStorage.getItem.mockReturnValue(null)
    localStorage.setItem.mockClear()
    localStorage.removeItem.mockClear()
  })

  // ==================== Variable Extraction Tests ====================

  describe('variable extraction', () => {
    it('PVAR_001: extracts single variable from prompt', () => {
      const { variables } = usePromptVariables('Hello {{name}}!')
      expect(variables.value).toHaveLength(1)
      expect(variables.value[0].name).toBe('name')
    })

    it('PVAR_002: extracts multiple variables', () => {
      const { variables } = usePromptVariables('{{greeting}} {{name}}, welcome to {{place}}!')
      expect(variables.value).toHaveLength(3)
      const names = variables.value.map(v => v.name)
      expect(names).toContain('greeting')
      expect(names).toContain('name')
      expect(names).toContain('place')
    })

    it('PVAR_003: counts occurrences of repeated variables', () => {
      const { variables } = usePromptVariables('{{name}} said hello to {{name}}')
      expect(variables.value).toHaveLength(1)
      expect(variables.value[0].occurrences).toBe(2)
    })

    it('PVAR_004: handles empty prompt', () => {
      const { variables } = usePromptVariables('')
      expect(variables.value).toHaveLength(0)
    })

    it('PVAR_005: handles prompt without variables', () => {
      const { variables } = usePromptVariables('No variables here')
      expect(variables.value).toHaveLength(0)
    })

    it('PVAR_006: tracks positions of variables', () => {
      const { variables } = usePromptVariables('Hello {{name}}!')
      expect(variables.value[0].positions).toHaveLength(1)
      expect(variables.value[0].positions[0]).toBe(6)
    })

    it('PVAR_007: extracts variables with underscores', () => {
      const { variables } = usePromptVariables('{{input_data}} and {{output_format}}')
      expect(variables.value).toHaveLength(2)
    })

    it('PVAR_008: filters out "undefined" variable name', () => {
      const { variables } = usePromptVariables('{{undefined}} {{valid_var}}')
      expect(variables.value).toHaveLength(1)
      expect(variables.value[0].name).toBe('valid_var')
    })

    it('PVAR_009: filters out "null" variable name', () => {
      const { variables } = usePromptVariables('{{null}} {{good}}')
      expect(variables.value).toHaveLength(1)
      expect(variables.value[0].name).toBe('good')
    })

    it('PVAR_010: filters out JS reserved words', () => {
      const { variables } = usePromptVariables('{{true}} {{false}} {{NaN}} {{valid}}')
      expect(variables.value).toHaveLength(1)
      expect(variables.value[0].name).toBe('valid')
    })

    it('PVAR_011: reacts to prompt text changes', async () => {
      const prompt = ref('Hello {{name}}')
      const { variables } = usePromptVariables(prompt)
      expect(variables.value).toHaveLength(1)

      prompt.value = 'Hello {{name}} and {{age}}'
      await nextTick()
      expect(variables.value).toHaveLength(2)
    })
  })

  // ==================== setValue Tests ====================

  describe('setValue', () => {
    it('PVAR_012: sets value for a variable', () => {
      const { values, setValue } = usePromptVariables('{{name}}')
      setValue('name', 'Alice')
      expect(values.value.name).toBe('Alice')
    })

    it('PVAR_013: sets metadata when provided', () => {
      const { metadata, setValue } = usePromptVariables('{{data}}')
      setValue('data', 'content', { source: 'file', fileName: 'test.txt' })
      expect(metadata.value.data.source).toBe('file')
      expect(metadata.value.data.fileName).toBe('test.txt')
    })

    it('PVAR_014: rejects invalid variable names', () => {
      const { values, setValue } = usePromptVariables('{{test}}')
      setValue('undefined', 'value')
      expect(values.value.undefined).toBeUndefined()
    })

    it('PVAR_015: persists to localStorage when promptId is set', () => {
      const { setValue } = usePromptVariables('{{name}}', { promptId: '123' })
      setValue('name', 'Test')
      expect(localStorage.setItem).toHaveBeenCalled()
    })

    it('PVAR_016: does not persist when no promptId', () => {
      const { setValue } = usePromptVariables('{{name}}')
      localStorage.setItem.mockClear()
      setValue('name', 'Test')
      // The initial load might call setItem; clear, then check
      expect(localStorage.setItem).not.toHaveBeenCalled()
    })
  })

  // ==================== resolvedPrompt Tests ====================

  describe('resolvedPrompt', () => {
    it('PVAR_017: replaces variables with their values', () => {
      const { resolvedPrompt, setValue } = usePromptVariables('Hello {{name}}!')
      setValue('name', 'World')
      expect(resolvedPrompt.value).toBe('Hello World!')
    })

    it('PVAR_018: replaces multiple occurrences of same variable', () => {
      const { resolvedPrompt, setValue } = usePromptVariables('{{name}} is {{name}}')
      setValue('name', 'Alice')
      expect(resolvedPrompt.value).toBe('Alice is Alice')
    })

    it('PVAR_019: leaves unset variables as placeholders', () => {
      const { resolvedPrompt } = usePromptVariables('Hello {{name}}!')
      expect(resolvedPrompt.value).toBe('Hello {{name}}!')
    })

    it('PVAR_020: formats objects as JSON', () => {
      const { resolvedPrompt, setValue } = usePromptVariables('Data: {{data}}')
      setValue('data', { key: 'value' })
      expect(resolvedPrompt.value).toContain('"key": "value"')
    })

    it('PVAR_021: formats numbers as strings', () => {
      const { resolvedPrompt, setValue } = usePromptVariables('Count: {{count}}')
      setValue('count', 42)
      expect(resolvedPrompt.value).toBe('Count: 42')
    })
  })

  // ==================== allFilled / unfilledVariables Tests ====================

  describe('allFilled and unfilledVariables', () => {
    it('PVAR_022: allFilled is false when variables are empty', () => {
      const { allFilled } = usePromptVariables('{{name}} {{age}}')
      expect(allFilled.value).toBe(false)
    })

    it('PVAR_023: allFilled is true when all variables have values', () => {
      const { allFilled, setValue } = usePromptVariables('{{name}} {{age}}')
      setValue('name', 'Alice')
      setValue('age', '30')
      expect(allFilled.value).toBe(true)
    })

    it('PVAR_024: allFilled is true when no variables exist', () => {
      const { allFilled } = usePromptVariables('No variables here')
      expect(allFilled.value).toBe(true)
    })

    it('PVAR_025: unfilledVariables lists variables without values', () => {
      const { unfilledVariables, setValue } = usePromptVariables('{{name}} {{age}}')
      setValue('name', 'Alice')
      expect(unfilledVariables.value).toHaveLength(1)
      expect(unfilledVariables.value[0].name).toBe('age')
    })
  })

  // ==================== stats Tests ====================

  describe('stats', () => {
    it('PVAR_026: provides correct total count', () => {
      const { stats } = usePromptVariables('{{a}} {{b}} {{c}}')
      expect(stats.value.total).toBe(3)
    })

    it('PVAR_027: calculates fill percentage', () => {
      const { stats, setValue } = usePromptVariables('{{a}} {{b}}')
      setValue('a', 'val')
      expect(stats.value.percentFilled).toBe(50)
    })

    it('PVAR_028: returns 100% when no variables exist', () => {
      const { stats } = usePromptVariables('No vars')
      expect(stats.value.percentFilled).toBe(100)
    })
  })

  // ==================== clearValue / clearAll Tests ====================

  describe('clearValue and clearAll', () => {
    it('PVAR_029: clears a specific value', () => {
      const { values, setValue, clearValue } = usePromptVariables('{{name}} {{age}}')
      setValue('name', 'Alice')
      setValue('age', '30')
      clearValue('name')
      expect(values.value.name).toBeUndefined()
      expect(values.value.age).toBe('30')
    })

    it('PVAR_030: clears all values', () => {
      const { values, setValue, clearAll } = usePromptVariables('{{name}} {{age}}')
      setValue('name', 'Alice')
      setValue('age', '30')
      clearAll()
      expect(Object.keys(values.value)).toHaveLength(0)
    })
  })

  // ==================== isValidVariableName Tests ====================

  describe('isValidVariableName', () => {
    it('PVAR_031: accepts valid names', () => {
      const { isValidVariableName } = usePromptVariables('')
      expect(isValidVariableName('valid_name')).toBe(true)
      expect(isValidVariableName('_private')).toBe(true)
      expect(isValidVariableName('camelCase')).toBe(true)
      expect(isValidVariableName('name123')).toBe(true)
    })

    it('PVAR_032: rejects invalid names', () => {
      const { isValidVariableName } = usePromptVariables('')
      expect(isValidVariableName('')).toBe(false)
      expect(isValidVariableName(null)).toBe(false)
      expect(isValidVariableName('123start')).toBe(false)
      expect(isValidVariableName('has space')).toBe(false)
      expect(isValidVariableName('undefined')).toBe(false)
      expect(isValidVariableName('Object')).toBe(false)
    })
  })

  // ==================== Manual Variables Tests ====================

  describe('manual variables', () => {
    it('PVAR_033: adds a manual variable', () => {
      const { addManualVariable, manualVariables } = usePromptVariables('No vars here')
      const result = addManualVariable('custom_var')
      expect(result).toBe(true)
      expect(manualVariables.value).toHaveLength(1)
      expect(manualVariables.value[0].name).toBe('custom_var')
      expect(manualVariables.value[0].isManual).toBe(true)
    })

    it('PVAR_034: rejects duplicate manual variable names', () => {
      const { addManualVariable } = usePromptVariables('No vars')
      addManualVariable('my_var')
      const result = addManualVariable('my_var')
      expect(result).toBe(false)
    })

    it('PVAR_035: rejects manual variable that exists in prompt', () => {
      const { addManualVariable } = usePromptVariables('{{existing_var}}')
      const result = addManualVariable('existing_var')
      expect(result).toBe(false)
    })

    it('PVAR_036: removes manual variable', () => {
      const { addManualVariable, removeManualVariable, manualVariables } = usePromptVariables('')
      addManualVariable('temp_var')
      expect(manualVariables.value).toHaveLength(1)
      const result = removeManualVariable('temp_var')
      expect(result).toBe(true)
      expect(manualVariables.value).toHaveLength(0)
    })

    it('PVAR_037: returns false when removing non-existent manual variable', () => {
      const { removeManualVariable } = usePromptVariables('')
      expect(removeManualVariable('nonexistent')).toBe(false)
    })

    it('PVAR_038: manual variables appear in validVariables', () => {
      const { addManualVariable, validVariables } = usePromptVariables('{{prompt_var}}')
      addManualVariable('manual_var')
      const names = validVariables.value.map(v => v.name)
      expect(names).toContain('prompt_var')
      expect(names).toContain('manual_var')
    })

    it('PVAR_039: rejects invalid manual variable name', () => {
      const { addManualVariable } = usePromptVariables('')
      expect(addManualVariable('undefined')).toBe(false)
      expect(addManualVariable('')).toBe(false)
    })
  })

  // ==================== Variable Config Tests ====================

  describe('variable config', () => {
    it('PVAR_040: sets and gets variable config', () => {
      const { setVariableConfig, getVariableConfig } = usePromptVariables('{{input}}')
      setVariableConfig('input', { defaultValue: 'default text', description: 'User input' })
      const config = getVariableConfig('input')
      expect(config.defaultValue).toBe('default text')
      expect(config.description).toBe('User input')
    })

    it('PVAR_041: returns empty object for unconfigured variable', () => {
      const { getVariableConfig } = usePromptVariables('{{input}}')
      expect(getVariableConfig('nonexistent')).toEqual({})
    })

    it('PVAR_042: rejects config for invalid variable name', () => {
      const { setVariableConfig, getVariableConfig } = usePromptVariables('')
      setVariableConfig('undefined', { defaultValue: 'test' })
      expect(getVariableConfig('undefined')).toEqual({})
    })
  })

  // ==================== setFromFile Tests ====================

  describe('setFromFile', () => {
    it('PVAR_043: sets value from file content', () => {
      const { values, metadata, setFromFile } = usePromptVariables('{{data}}')
      setFromFile('data', 'file content', null, 'test.txt')
      expect(values.value.data).toBe('file content')
      expect(metadata.value.data.source).toBe('file')
      expect(metadata.value.data.fileName).toBe('test.txt')
    })

    it('PVAR_044: applies JSON path when provided', () => {
      const { values, setFromFile } = usePromptVariables('{{message}}')
      setFromFile('message', { messages: ['hello', 'world'] }, '$.messages[0]', 'data.json')
      expect(values.value.message).toBe('hello')
    })
  })

  // ==================== setFromDatasetItem Tests ====================

  describe('setFromDatasetItem', () => {
    it('PVAR_045: sets values from dataset item', () => {
      const { values, metadata, setFromDatasetItem } = usePromptVariables('{{name}} {{age}}')
      setFromDatasetItem({
        id: '1',
        name: 'Item 1',
        variables: { name: 'Alice', age: '30' }
      })
      expect(values.value.name).toBe('Alice')
      expect(values.value.age).toBe('30')
      expect(metadata.value.name.source).toBe('dataset')
    })

    it('PVAR_046: handles null dataset item gracefully', () => {
      const { setFromDatasetItem } = usePromptVariables('{{test}}')
      // Should not throw
      setFromDatasetItem(null)
      setFromDatasetItem({ id: '1' })
    })
  })

  // ==================== getFormattedValue / getValuePreview Tests ====================

  describe('formatting helpers', () => {
    it('PVAR_047: getFormattedValue returns formatted string', () => {
      const { setValue, getFormattedValue } = usePromptVariables('{{data}}')
      setValue('data', { key: 'value' })
      const formatted = getFormattedValue('data')
      expect(formatted).toContain('key')
      expect(formatted).toContain('value')
    })

    it('PVAR_048: getFormattedValue returns empty string for unset variable', () => {
      const { getFormattedValue } = usePromptVariables('{{data}}')
      expect(getFormattedValue('data')).toBe('')
    })

    it('PVAR_049: getValuePreview truncates long values', () => {
      const { setValue, getValuePreview } = usePromptVariables('{{data}}')
      setValue('data', 'A'.repeat(200))
      const preview = getValuePreview('data', 50)
      expect(preview.length).toBe(53) // 50 + '...'
      expect(preview.endsWith('...')).toBe(true)
    })

    it('PVAR_050: getValuePreview returns full value when short', () => {
      const { setValue, getValuePreview } = usePromptVariables('{{data}}')
      setValue('data', 'short')
      expect(getValuePreview('data')).toBe('short')
    })
  })

  // ==================== Storage Tests ====================

  describe('storage', () => {
    it('PVAR_051: clearStorage removes all related keys', () => {
      const { clearStorage } = usePromptVariables('{{test}}', { promptId: '42' })
      clearStorage()
      expect(localStorage.removeItem).toHaveBeenCalledWith('llars_prompt_variables_42')
      expect(localStorage.removeItem).toHaveBeenCalledWith('llars_prompt_var_config_42')
      expect(localStorage.removeItem).toHaveBeenCalledWith('llars_prompt_variables_42_manual')
    })

    it('PVAR_052: loadFromStorage handles corrupted data gracefully', () => {
      localStorage.getItem.mockReturnValue('not valid json {{{')
      // Should not throw
      const { isLoaded } = usePromptVariables('{{test}}', { promptId: '99' })
      expect(isLoaded.value).toBe(true)
    })

    it('PVAR_053: isLoaded is true even without promptId', () => {
      const { isLoaded } = usePromptVariables('{{test}}')
      expect(isLoaded.value).toBe(true)
    })
  })

  // ==================== filledVariables Tests ====================

  describe('filledVariables', () => {
    it('PVAR_054: includes value and meta in filled variables', () => {
      const { filledVariables, setValue } = usePromptVariables('{{name}} {{age}}')
      setValue('name', 'Alice', { source: 'manual' })
      expect(filledVariables.value).toHaveLength(1)
      expect(filledVariables.value[0].name).toBe('name')
      expect(filledVariables.value[0].value).toBe('Alice')
      expect(filledVariables.value[0].meta.source).toBe('manual')
    })
  })

  // ==================== validVariables Tests ====================

  describe('validVariables', () => {
    it('PVAR_055: marks extracted variables correctly', () => {
      const { validVariables } = usePromptVariables('{{input_text}}')
      const v = validVariables.value.find(v => v.name === 'input_text')
      expect(v.isExtracted).toBe(true)
      expect(v.isManual).toBe(false)
    })

    it('PVAR_056: marks manual variables correctly', () => {
      const { addManualVariable, validVariables } = usePromptVariables('')
      addManualVariable('custom')
      const v = validVariables.value.find(v => v.name === 'custom')
      expect(v.isExtracted).toBe(false)
      expect(v.isManual).toBe(true)
    })
  })
})

// ==================== analyzeJsonStructure Tests ====================

describe('analyzeJsonStructure', () => {
  it('PVAR_057: analyzes simple object', () => {
    const paths = analyzeJsonStructure({ name: 'Alice', age: 30 })
    expect(paths.length).toBeGreaterThan(0)
    const objectPath = paths.find(p => p.type === 'object')
    expect(objectPath).toBeDefined()
  })

  it('PVAR_058: analyzes nested arrays', () => {
    const paths = analyzeJsonStructure({ items: [1, 2, 3] })
    const arrayPath = paths.find(p => p.type === 'array')
    expect(arrayPath).toBeDefined()
    expect(arrayPath.length).toBe(3)

    const wildcardPath = paths.find(p => p.type === 'array_all')
    expect(wildcardPath).toBeDefined()
  })

  it('PVAR_059: respects maxDepth', () => {
    const deep = { a: { b: { c: { d: { e: 'deep' } } } } }
    const paths = analyzeJsonStructure(deep, '$', 2)
    // Should not go deeper than 2 levels
    const deepPath = paths.find(p => p.path === '$.a.b.c.d')
    expect(deepPath).toBeUndefined()
  })
})

// ==================== parseFileContent Tests ====================

describe('parseFileContent', () => {
  it('PVAR_060: parses JSON file', () => {
    const result = parseFileContent('data.json', '{"key": "value"}')
    expect(result.type).toBe('json')
    expect(result.data).toEqual({ key: 'value' })
    expect(result.error).toBeNull()
  })

  it('PVAR_061: parses CSV file', () => {
    const result = parseFileContent('data.csv', 'name,age\nAlice,30\nBob,25')
    expect(result.type).toBe('csv')
    expect(result.data).toHaveLength(2)
    expect(result.data[0].name).toBe('Alice')
    expect(result.data[0].age).toBe('30')
  })

  it('PVAR_062: parses TXT file', () => {
    const result = parseFileContent('note.txt', 'Plain text content')
    expect(result.type).toBe('text')
    expect(result.data).toBe('Plain text content')
  })

  it('PVAR_063: parses MD file as text', () => {
    const result = parseFileContent('readme.md', '# Heading')
    expect(result.type).toBe('text')
    expect(result.data).toBe('# Heading')
  })

  it('PVAR_064: handles unknown file types', () => {
    const result = parseFileContent('data.xyz', 'content')
    expect(result.type).toBe('unknown')
    expect(result.data).toBe('content')
  })

  it('PVAR_065: returns error for invalid JSON', () => {
    const result = parseFileContent('bad.json', '{invalid json}')
    expect(result.error).not.toBeNull()
    expect(result.data).toBeNull()
  })

  it('PVAR_066: handles empty CSV', () => {
    const result = parseFileContent('empty.csv', '')
    expect(result.type).toBe('csv')
    expect(result.data).toEqual([])
  })
})
