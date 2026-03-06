/**
 * useModelRegistry Composable Tests
 *
 * Tests for the central model registry (display names, colors, providers).
 * Test IDs: REG_001 - REG_040
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock formatters - parseUserProviderModelId
vi.mock('@/utils/formatters', () => ({
  parseUserProviderModelId: vi.fn((modelId, hint) => {
    if (!modelId || typeof modelId !== 'string' || !modelId.startsWith('user-provider:')) return null
    const rest = modelId.slice('user-provider:'.length)
    const parts = rest.split(':')
    const providerId = parts[0]
    const username = parts.length >= 3 ? parts[1] : null
    const modelName = parts.length >= 3 ? parts.slice(2).join(':') : parts.slice(1).join(':')
    const providerLabel = hint || 'Provider'
    const displayName = username
      ? `${username}/${providerLabel}/${modelName}`
      : `${providerLabel}/${modelName}`
    return { providerId, username, modelName, providerLabel, displayName }
  })
}))

let useModelRegistry

describe('useModelRegistry', () => {
  beforeEach(async () => {
    vi.resetModules()

    // Re-apply mock after resetModules
    vi.doMock('@/utils/formatters', () => ({
      parseUserProviderModelId: vi.fn((modelId, hint) => {
        if (!modelId || typeof modelId !== 'string' || !modelId.startsWith('user-provider:')) return null
        const rest = modelId.slice('user-provider:'.length)
        const parts = rest.split(':')
        const providerId = parts[0]
        const username = parts.length >= 3 ? parts[1] : null
        const modelName = parts.length >= 3 ? parts.slice(2).join(':') : parts.slice(1).join(':')
        const providerLabel = hint || 'Provider'
        const displayName = username
          ? `${username}/${providerLabel}/${modelName}`
          : `${providerLabel}/${modelName}`
        return { providerId, username, modelName, providerLabel, displayName }
      })
    }))

    const mod = await import('@/composables/useModelRegistry')
    useModelRegistry = mod.useModelRegistry
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('REG_001: useModelRegistry returns all expected properties', () => {
      const result = useModelRegistry()
      expect(result).toHaveProperty('registry')
      expect(result).toHaveProperty('updateRegistry')
      expect(result).toHaveProperty('formatModelName')
      expect(result).toHaveProperty('getModelColor')
      expect(result).toHaveProperty('getProviderName')
    })

    it('REG_002: all methods are functions', () => {
      const { updateRegistry, formatModelName, getModelColor, getProviderName } = useModelRegistry()
      expect(typeof updateRegistry).toBe('function')
      expect(typeof formatModelName).toBe('function')
      expect(typeof getModelColor).toBe('function')
      expect(typeof getProviderName).toBe('function')
    })
  })

  // ==================== Initial State Tests ====================

  describe('Initial State', () => {
    it('REG_003: registry starts empty', () => {
      const { registry } = useModelRegistry()
      expect(Object.keys(registry.value)).toHaveLength(0)
    })
  })

  // ==================== updateRegistry Tests ====================

  describe('updateRegistry', () => {
    it('REG_004: adds entries to registry', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { display_name: 'Model One', color: '#ff0000' }
      })
      expect(registry.value['model-1']).toBeDefined()
      expect(registry.value['model-1'].display_name).toBe('Model One')
    })

    it('REG_005: merges new entries with existing', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { display_name: 'Model One' }
      })
      updateRegistry({
        'model-2': { display_name: 'Model Two' }
      })
      expect(registry.value['model-1']).toBeDefined()
      expect(registry.value['model-2']).toBeDefined()
    })

    it('REG_006: overwrites existing entries with same key', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { display_name: 'Old Name' }
      })
      updateRegistry({
        'model-1': { display_name: 'New Name' }
      })
      expect(registry.value['model-1'].display_name).toBe('New Name')
    })

    it('REG_007: ignores null input', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry(null)
      expect(Object.keys(registry.value)).toHaveLength(0)
    })

    it('REG_008: ignores undefined input', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry(undefined)
      expect(Object.keys(registry.value)).toHaveLength(0)
    })

    it('REG_009: ignores non-object input', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry('not-an-object')
      expect(Object.keys(registry.value)).toHaveLength(0)
    })

    it('REG_010: handles empty object input', () => {
      const { registry, updateRegistry } = useModelRegistry()
      updateRegistry({})
      expect(Object.keys(registry.value)).toHaveLength(0)
    })
  })

  // ==================== formatModelName Tests ====================

  describe('formatModelName', () => {
    it('REG_011: returns "Unknown" for null modelId', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName(null)).toBe('Unknown')
    })

    it('REG_012: returns "Unknown" for undefined modelId', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName(undefined)).toBe('Unknown')
    })

    it('REG_013: returns "Unknown" for empty string', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName('')).toBe('Unknown')
    })

    it('REG_014: strips Global/ prefix', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName('Global/OpenAI/gpt-4')).toBe('OpenAI/gpt-4')
    })

    it('REG_015: strips Global/ prefix for any model', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName('Global/Mistral/Mistral-Small')).toBe('Mistral/Mistral-Small')
    })

    it('REG_016: uses parseUserProviderModelId for user-provider models', () => {
      const { formatModelName } = useModelRegistry()
      const result = formatModelName('user-provider:42:john:gpt-4o')
      expect(result).toBe('john/Provider/gpt-4o')
    })

    it('REG_017: passes user_provider_name hint for user-provider models', () => {
      const { formatModelName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'user-provider:42:john:gpt-4o': {
          user_provider_name: 'IONOS'
        }
      })
      const result = formatModelName('user-provider:42:john:gpt-4o')
      expect(result).toBe('john/IONOS/gpt-4o')
    })

    it('REG_018: returns DB display_name when different from modelId', () => {
      const { formatModelName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'some-model-id': { display_name: 'Pretty Model Name' }
      })
      expect(formatModelName('some-model-id')).toBe('Pretty Model Name')
    })

    it('REG_019: returns raw modelId when display_name equals modelId', () => {
      const { formatModelName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'some-model-id': { display_name: 'some-model-id' }
      })
      expect(formatModelName('some-model-id')).toBe('some-model-id')
    })

    it('REG_020: returns raw modelId when not in registry and no special prefix', () => {
      const { formatModelName } = useModelRegistry()
      expect(formatModelName('plain-model')).toBe('plain-model')
    })

    it('REG_021: Global/ prefix takes priority over DB display_name', () => {
      const { formatModelName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'Global/OpenAI/gpt-4': { display_name: 'GPT-4 Display' }
      })
      // Global/ prefix path is checked before DB display_name
      expect(formatModelName('Global/OpenAI/gpt-4')).toBe('OpenAI/gpt-4')
    })

    it('REG_022: user-provider prefix takes priority over DB display_name', () => {
      const { formatModelName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'user-provider:42:gpt-4o': { display_name: 'Custom Display' }
      })
      const result = formatModelName('user-provider:42:gpt-4o')
      // user-provider parsing should take priority
      expect(result).toContain('gpt-4o')
    })
  })

  // ==================== getModelColor Tests ====================

  describe('getModelColor', () => {
    it('REG_023: returns null for unknown model', () => {
      const { getModelColor } = useModelRegistry()
      expect(getModelColor('unknown-model')).toBeNull()
    })

    it('REG_024: returns color from registry', () => {
      const { getModelColor, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { color: '#ff0000' }
      })
      expect(getModelColor('model-1')).toBe('#ff0000')
    })

    it('REG_025: returns null when entry exists but no color', () => {
      const { getModelColor, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { display_name: 'Model One' }
      })
      expect(getModelColor('model-1')).toBeNull()
    })

    it('REG_026: returns updated color after re-registration', () => {
      const { getModelColor, updateRegistry } = useModelRegistry()
      updateRegistry({ 'model-1': { color: '#ff0000' } })
      updateRegistry({ 'model-1': { color: '#00ff00' } })
      expect(getModelColor('model-1')).toBe('#00ff00')
    })
  })

  // ==================== getProviderName Tests ====================

  describe('getProviderName', () => {
    it('REG_027: returns null for unknown model', () => {
      const { getProviderName } = useModelRegistry()
      expect(getProviderName('unknown-model')).toBeNull()
    })

    it('REG_028: returns user_provider_name from registry', () => {
      const { getProviderName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'user-provider:42:gpt-4o': { user_provider_name: 'IONOS' }
      })
      expect(getProviderName('user-provider:42:gpt-4o')).toBe('IONOS')
    })

    it('REG_029: returns null when entry exists but no user_provider_name', () => {
      const { getProviderName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'model-1': { display_name: 'Model One', color: '#fff' }
      })
      expect(getProviderName('model-1')).toBeNull()
    })

    it('REG_030: returns null for non-user-provider models', () => {
      const { getProviderName, updateRegistry } = useModelRegistry()
      updateRegistry({
        'Global/OpenAI/gpt-4': { display_name: 'GPT-4' }
      })
      expect(getProviderName('Global/OpenAI/gpt-4')).toBeNull()
    })
  })

  // ==================== Singleton/Shared State Tests ====================

  describe('Shared State', () => {
    it('REG_031: multiple useModelRegistry() calls share state', () => {
      const instance1 = useModelRegistry()
      const instance2 = useModelRegistry()

      instance1.updateRegistry({
        'model-1': { display_name: 'Shared Model', color: '#abc' }
      })

      expect(instance2.registry.value['model-1']).toBeDefined()
      expect(instance2.getModelColor('model-1')).toBe('#abc')
    })

    it('REG_032: formatModelName in one instance sees updates from another', () => {
      const instance1 = useModelRegistry()
      const instance2 = useModelRegistry()

      instance1.updateRegistry({
        'my-model': { display_name: 'Fancy Name' }
      })

      expect(instance2.formatModelName('my-model')).toBe('Fancy Name')
    })

    it('REG_033: registry computed property is reactive', () => {
      const { registry, updateRegistry } = useModelRegistry()
      expect(Object.keys(registry.value)).toHaveLength(0)

      updateRegistry({ 'a': { display_name: 'A' } })
      expect(Object.keys(registry.value)).toHaveLength(1)

      updateRegistry({ 'b': { display_name: 'B' } })
      expect(Object.keys(registry.value)).toHaveLength(2)
    })
  })
})
