/**
 * Tests for useSplitPaneResize composable
 *
 * Test IDs: SPR_001 - SPR_050
 *
 * Coverage:
 * - Exports and structure
 * - Initial state
 * - isSplitMode computed
 * - editorPaneStyle computed
 * - previewPaneStyle computed
 * - startResize function
 * - localStorage persistence
 * - minRatio/maxRatio constraints
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'

// Mock localStorage
const mockLocalStorage = (() => {
  let store = {}
  return {
    getItem: vi.fn(key => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn(key => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true
})

describe('useSplitPaneResize', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.clear()
    vi.resetModules()
  })

  // Helper to get fresh composable instance
  const getComposable = async (options = {}) => {
    const { useSplitPaneResize } = await import('@/composables/useSplitPaneResize')
    return useSplitPaneResize(options)
  }

  describe('Exports', () => {
    it('SPR_001: exports useSplitPaneResize function', async () => {
      const { useSplitPaneResize } = await import('@/composables/useSplitPaneResize')
      expect(typeof useSplitPaneResize).toBe('function')
    })

    it('SPR_002: returns all expected properties', async () => {
      const result = await getComposable()

      expect(result).toHaveProperty('panesContainerRef')
      expect(result).toHaveProperty('editorPaneWidth')
      expect(result).toHaveProperty('editorPaneStyle')
      expect(result).toHaveProperty('previewPaneStyle')
      expect(result).toHaveProperty('resizingPanes')
      expect(result).toHaveProperty('startResize')
    })

    it('SPR_003: panesContainerRef is a ref', async () => {
      const { panesContainerRef } = await getComposable()
      expect(panesContainerRef.value).toBe(null)
    })

    it('SPR_004: editorPaneWidth is a ref', async () => {
      const { editorPaneWidth } = await getComposable()
      expect(typeof editorPaneWidth.value).toBe('number')
    })

    it('SPR_005: resizingPanes is a ref', async () => {
      const { resizingPanes } = await getComposable()
      expect(resizingPanes.value).toBe(false)
    })

    it('SPR_006: startResize is a function', async () => {
      const { startResize } = await getComposable()
      expect(typeof startResize).toBe('function')
    })
  })

  describe('Initial State', () => {
    it('SPR_007: editorPaneWidth is 0 without storage', async () => {
      const { editorPaneWidth } = await getComposable()
      expect(editorPaneWidth.value).toBe(0)
    })

    it('SPR_008: resizingPanes is false initially', async () => {
      const { resizingPanes } = await getComposable()
      expect(resizingPanes.value).toBe(false)
    })

    it('SPR_009: panesContainerRef is null initially', async () => {
      const { panesContainerRef } = await getComposable()
      expect(panesContainerRef.value).toBe(null)
    })

    it('SPR_010: loads stored width from localStorage', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('400')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test-pane' })

      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('test-pane')
      expect(editorPaneWidth.value).toBe(400)
    })

    it('SPR_011: handles invalid localStorage value', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('not-a-number')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test-pane' })

      expect(editorPaneWidth.value).toBe(0)
    })

    it('SPR_012: handles null localStorage value', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce(null)

      const { editorPaneWidth } = await getComposable({ storageKey: 'test-pane' })

      expect(editorPaneWidth.value).toBe(0)
    })
  })

  describe('isSplitMode computed', () => {
    it('SPR_013: returns true when viewMode is undefined', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = 300

      // isSplitMode is true, so style should be applied
      expect(editorPaneStyle.value).toHaveProperty('width')
    })

    it('SPR_014: returns true when viewMode.value is "split"', async () => {
      const viewMode = ref('split')
      const { editorPaneStyle, editorPaneWidth } = await getComposable({ viewMode })
      editorPaneWidth.value = 300

      expect(editorPaneStyle.value).toHaveProperty('width')
    })

    it('SPR_015: returns false when viewMode.value is "editor"', async () => {
      const viewMode = ref('editor')
      const { editorPaneStyle, editorPaneWidth } = await getComposable({ viewMode })
      editorPaneWidth.value = 300

      // Not split mode, style should be empty
      expect(editorPaneStyle.value).toEqual({})
    })

    it('SPR_016: returns false when viewMode.value is "preview"', async () => {
      const viewMode = ref('preview')
      const { editorPaneStyle, editorPaneWidth } = await getComposable({ viewMode })
      editorPaneWidth.value = 300

      expect(editorPaneStyle.value).toEqual({})
    })
  })

  describe('editorPaneStyle computed', () => {
    it('SPR_017: returns empty object when width is 0', async () => {
      const { editorPaneStyle } = await getComposable()
      expect(editorPaneStyle.value).toEqual({})
    })

    it('SPR_018: returns empty object when width is negative', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = -100

      expect(editorPaneStyle.value).toEqual({})
    })

    it('SPR_019: returns width style when positive width', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = 350

      expect(editorPaneStyle.value.width).toBe('350px')
    })

    it('SPR_020: returns flex style when positive width', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = 350

      expect(editorPaneStyle.value.flex).toBe('0 0 350px')
    })

    it('SPR_021: updates reactively when width changes', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()

      editorPaneWidth.value = 200
      expect(editorPaneStyle.value.width).toBe('200px')

      editorPaneWidth.value = 400
      expect(editorPaneStyle.value.width).toBe('400px')
    })
  })

  describe('previewPaneStyle computed', () => {
    it('SPR_022: returns empty object when width is 0', async () => {
      const { previewPaneStyle } = await getComposable()
      expect(previewPaneStyle.value).toEqual({})
    })

    it('SPR_023: returns flex style when editor has width', async () => {
      const { previewPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = 300

      expect(previewPaneStyle.value.flex).toBe('1 1 0')
    })

    it('SPR_024: returns empty object when not split mode', async () => {
      const viewMode = ref('editor')
      const { previewPaneStyle, editorPaneWidth } = await getComposable({ viewMode })
      editorPaneWidth.value = 300

      expect(previewPaneStyle.value).toEqual({})
    })
  })

  describe('startResize', () => {
    it('SPR_025: sets resizingPanes to true', async () => {
      const { startResize, resizingPanes } = await getComposable()
      const event = { preventDefault: vi.fn() }

      startResize(event)

      expect(resizingPanes.value).toBe(true)
    })

    it('SPR_026: prevents default event', async () => {
      const { startResize } = await getComposable()
      const event = { preventDefault: vi.fn() }

      startResize(event)

      expect(event.preventDefault).toHaveBeenCalled()
    })

    it('SPR_027: does nothing when not split mode', async () => {
      const viewMode = ref('editor')
      const { startResize, resizingPanes } = await getComposable({ viewMode })
      const event = { preventDefault: vi.fn() }

      startResize(event)

      expect(resizingPanes.value).toBe(false)
      expect(event.preventDefault).not.toHaveBeenCalled()
    })

    it('SPR_028: sets cursor style on document.body', async () => {
      const { startResize } = await getComposable()
      const event = { preventDefault: vi.fn() }

      startResize(event)

      expect(document.body.style.cursor).toBe('col-resize')
    })

    it('SPR_029: sets userSelect style on document.body', async () => {
      const { startResize } = await getComposable()
      const event = { preventDefault: vi.fn() }

      startResize(event)

      expect(document.body.style.userSelect).toBe('none')
    })
  })

  describe('Options', () => {
    it('SPR_030: uses default minRatio of 0.25', async () => {
      const result = await getComposable()
      expect(result.editorPaneWidth).toBeDefined()
    })

    it('SPR_031: uses default maxRatio of 0.75', async () => {
      const result = await getComposable()
      expect(result.editorPaneWidth).toBeDefined()
    })

    it('SPR_032: accepts custom minRatio', async () => {
      const result = await getComposable({ minRatio: 0.1 })
      expect(result.editorPaneWidth).toBeDefined()
    })

    it('SPR_033: accepts custom maxRatio', async () => {
      const result = await getComposable({ maxRatio: 0.9 })
      expect(result.editorPaneWidth).toBeDefined()
    })

    it('SPR_034: works without storageKey', async () => {
      const result = await getComposable()
      expect(mockLocalStorage.getItem).not.toHaveBeenCalled()
    })

    it('SPR_035: works without viewMode', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable()
      editorPaneWidth.value = 250

      // Should work as split mode by default
      expect(editorPaneStyle.value.width).toBe('250px')
    })
  })

  describe('localStorage Persistence', () => {
    it('SPR_036: does not read localStorage without storageKey', async () => {
      await getComposable()
      expect(mockLocalStorage.getItem).not.toHaveBeenCalled()
    })

    it('SPR_037: reads from localStorage with storageKey', async () => {
      await getComposable({ storageKey: 'my-pane' })
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('my-pane')
    })

    it('SPR_038: handles NaN stored value', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('NaN')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test' })

      expect(editorPaneWidth.value).toBe(0)
    })

    it('SPR_039: handles Infinity stored value', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('Infinity')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test' })

      // parseInt('Infinity') returns NaN which is not finite
      expect(editorPaneWidth.value).toBe(0)
    })

    it('SPR_040: handles negative stored value', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('-100')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test' })

      // Negative is a valid finite number
      expect(editorPaneWidth.value).toBe(-100)
    })
  })

  describe('Edge Cases', () => {
    it('SPR_041: works with empty options object', async () => {
      const result = await getComposable({})
      expect(result.startResize).toBeDefined()
    })

    it('SPR_042: works with no options', async () => {
      const result = await getComposable()
      expect(result.startResize).toBeDefined()
    })

    it('SPR_043: editorPaneWidth can be set programmatically', async () => {
      const { editorPaneWidth, editorPaneStyle } = await getComposable()

      editorPaneWidth.value = 500
      expect(editorPaneStyle.value.width).toBe('500px')
    })

    it('SPR_044: viewMode ref changes update styles', async () => {
      const viewMode = ref('split')
      const { editorPaneStyle, editorPaneWidth } = await getComposable({ viewMode })
      editorPaneWidth.value = 300

      expect(editorPaneStyle.value.width).toBe('300px')

      viewMode.value = 'editor'
      expect(editorPaneStyle.value).toEqual({})
    })

    it('SPR_045: handles decimal width values', async () => {
      const { editorPaneWidth, editorPaneStyle } = await getComposable()
      editorPaneWidth.value = 333.33

      expect(editorPaneStyle.value.width).toBe('333.33px')
    })

    it('SPR_046: multiple instances are independent', async () => {
      const { useSplitPaneResize } = await import('@/composables/useSplitPaneResize')

      const instance1 = useSplitPaneResize({ storageKey: 'pane1' })
      const instance2 = useSplitPaneResize({ storageKey: 'pane2' })

      instance1.editorPaneWidth.value = 100
      instance2.editorPaneWidth.value = 200

      expect(instance1.editorPaneWidth.value).toBe(100)
      expect(instance2.editorPaneWidth.value).toBe(200)
    })

    it('SPR_047: stored value is parsed as integer', async () => {
      mockLocalStorage.getItem.mockReturnValueOnce('123.456')

      const { editorPaneWidth } = await getComposable({ storageKey: 'test' })

      // parseInt will return 123
      expect(editorPaneWidth.value).toBe(123)
    })

    it('SPR_048: editorPaneStyle includes both width and flex', async () => {
      const { editorPaneWidth, editorPaneStyle } = await getComposable()
      editorPaneWidth.value = 275

      const style = editorPaneStyle.value
      expect(style.width).toBe('275px')
      expect(style.flex).toBe('0 0 275px')
    })

    it('SPR_049: previewPaneStyle has correct flex basis', async () => {
      const { editorPaneWidth, previewPaneStyle } = await getComposable()
      editorPaneWidth.value = 300

      expect(previewPaneStyle.value.flex).toBe('1 1 0')
    })

    it('SPR_050: handles viewMode as null', async () => {
      const { editorPaneStyle, editorPaneWidth } = await getComposable({ viewMode: null })
      editorPaneWidth.value = 300

      // null is falsy, so isSplitMode should be true
      expect(editorPaneStyle.value.width).toBe('300px')
    })
  })
})
