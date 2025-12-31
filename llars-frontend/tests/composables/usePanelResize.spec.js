/**
 * usePanelResize Composable Tests
 *
 * Tests for the LLARS panel resize composable.
 * Test IDs: RESIZE_001 - RESIZE_045
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} })
  }
})()

Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Import after mocks
import { usePanelResize } from '@/composables/usePanelResize'

// Helper to create a test component that uses the composable
function createTestComponent(options = {}) {
  return defineComponent({
    setup() {
      const panelResize = usePanelResize(options)
      return { ...panelResize }
    },
    render() {
      return h('div', { ref: 'containerRef' }, 'Test')
    }
  })
}

describe('usePanelResize Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()

    // Reset document body styles
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('RESIZE_001: exports usePanelResize function', () => {
      expect(typeof usePanelResize).toBe('function')
    })

    it('RESIZE_002: returns all expected properties', () => {
      const result = usePanelResize()

      expect(result).toHaveProperty('leftPanelWidth')
      expect(result).toHaveProperty('isResizing')
      expect(result).toHaveProperty('containerRef')
      expect(result).toHaveProperty('startResize')
      expect(result).toHaveProperty('leftPanelStyle')
      expect(result).toHaveProperty('rightPanelStyle')
    })

    it('RESIZE_003: leftPanelWidth is a ref', () => {
      const result = usePanelResize()

      expect(result.leftPanelWidth).toBeDefined()
      expect(typeof result.leftPanelWidth.value).toBe('number')
    })

    it('RESIZE_004: isResizing is a ref with boolean value', () => {
      const result = usePanelResize()

      expect(typeof result.isResizing.value).toBe('boolean')
    })

    it('RESIZE_005: containerRef is a ref', () => {
      const result = usePanelResize()

      expect(result.containerRef).toBeDefined()
    })

    it('RESIZE_006: startResize is a function', () => {
      const result = usePanelResize()

      expect(typeof result.startResize).toBe('function')
    })

    it('RESIZE_007: leftPanelStyle is a function', () => {
      const result = usePanelResize()

      expect(typeof result.leftPanelStyle).toBe('function')
    })

    it('RESIZE_008: rightPanelStyle is a function', () => {
      const result = usePanelResize()

      expect(typeof result.rightPanelStyle).toBe('function')
    })
  })

  // ==================== Default Values Tests ====================

  describe('Default Values', () => {
    it('RESIZE_009: uses 50% as default initial width', () => {
      const result = usePanelResize()

      expect(result.leftPanelWidth.value).toBe(50)
    })

    it('RESIZE_010: isResizing is false initially', () => {
      const result = usePanelResize()

      expect(result.isResizing.value).toBe(false)
    })

    it('RESIZE_011: containerRef is null initially', () => {
      const result = usePanelResize()

      expect(result.containerRef.value).toBeNull()
    })
  })

  // ==================== Options Tests ====================

  describe('Options', () => {
    it('RESIZE_012: accepts custom initialLeftPercent', () => {
      const result = usePanelResize({ initialLeftPercent: 30 })

      expect(result.leftPanelWidth.value).toBe(30)
    })

    it('RESIZE_013: accepts custom minLeftPercent', () => {
      const result = usePanelResize({ minLeftPercent: 10 })

      // Width should still be default 50, min is just a constraint
      expect(result.leftPanelWidth.value).toBe(50)
    })

    it('RESIZE_014: accepts custom maxLeftPercent', () => {
      const result = usePanelResize({ maxLeftPercent: 90 })

      expect(result.leftPanelWidth.value).toBe(50)
    })

    it('RESIZE_015: accepts storageKey option', () => {
      const result = usePanelResize({ storageKey: 'test-panel-width' })

      // Just verifying it doesn't throw
      expect(result.leftPanelWidth.value).toBe(50)
    })

    it('RESIZE_016: accepts all options together', () => {
      const result = usePanelResize({
        initialLeftPercent: 40,
        minLeftPercent: 25,
        maxLeftPercent: 75,
        storageKey: 'custom-key'
      })

      expect(result.leftPanelWidth.value).toBe(40)
    })
  })

  // ==================== Style Functions Tests ====================

  describe('Style Functions', () => {
    it('RESIZE_017: leftPanelStyle returns correct width', () => {
      const result = usePanelResize({ initialLeftPercent: 50 })
      const style = result.leftPanelStyle()

      expect(style.width).toBe('calc(50% - 3px)')
    })

    it('RESIZE_018: leftPanelStyle includes flexShrink', () => {
      const result = usePanelResize()
      const style = result.leftPanelStyle()

      expect(style.flexShrink).toBe(0)
    })

    it('RESIZE_019: rightPanelStyle returns complementary width', () => {
      const result = usePanelResize({ initialLeftPercent: 50 })
      const style = result.rightPanelStyle()

      expect(style.width).toBe('calc(50% - 3px)')
    })

    it('RESIZE_020: rightPanelStyle includes flexShrink', () => {
      const result = usePanelResize()
      const style = result.rightPanelStyle()

      expect(style.flexShrink).toBe(0)
    })

    it('RESIZE_021: styles update when leftPanelWidth changes', () => {
      const result = usePanelResize({ initialLeftPercent: 30 })

      expect(result.leftPanelStyle().width).toBe('calc(30% - 3px)')
      expect(result.rightPanelStyle().width).toBe('calc(70% - 3px)')

      result.leftPanelWidth.value = 60

      expect(result.leftPanelStyle().width).toBe('calc(60% - 3px)')
      expect(result.rightPanelStyle().width).toBe('calc(40% - 3px)')
    })

    it('RESIZE_022: styles handle edge values', () => {
      const result = usePanelResize({ initialLeftPercent: 20 })

      expect(result.leftPanelStyle().width).toBe('calc(20% - 3px)')
      expect(result.rightPanelStyle().width).toBe('calc(80% - 3px)')
    })
  })

  // ==================== startResize Tests ====================

  describe('startResize', () => {
    it('RESIZE_023: startResize sets isResizing to true', () => {
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(result.isResizing.value).toBe(true)
    })

    it('RESIZE_024: startResize calls preventDefault', () => {
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
    })

    it('RESIZE_025: startResize sets cursor style on body', () => {
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(document.body.style.cursor).toBe('col-resize')
    })

    it('RESIZE_026: startResize sets userSelect style on body', () => {
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(document.body.style.userSelect).toBe('none')
    })

    it('RESIZE_027: startResize adds mousemove listener', () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener')
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(addEventListenerSpy).toHaveBeenCalledWith('mousemove', expect.any(Function))
    })

    it('RESIZE_028: startResize adds mouseup listener', () => {
      const addEventListenerSpy = vi.spyOn(document, 'addEventListener')
      const result = usePanelResize()
      const mockEvent = { preventDefault: vi.fn() }

      result.startResize(mockEvent)

      expect(addEventListenerSpy).toHaveBeenCalledWith('mouseup', expect.any(Function))
    })
  })

  // ==================== Mouse Movement Tests ====================

  describe('Mouse Movement', () => {
    it('RESIZE_029: mousemove updates leftPanelWidth when resizing', () => {
      const result = usePanelResize({
        initialLeftPercent: 50,
        minLeftPercent: 20,
        maxLeftPercent: 80
      })

      // Set up container ref with mock getBoundingClientRect
      result.containerRef.value = {
        getBoundingClientRect: () => ({
          width: 1000,
          left: 0
        })
      }

      // Start resizing
      result.startResize({ preventDefault: vi.fn() })

      // Simulate mousemove
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 300 })
      document.dispatchEvent(mouseMoveEvent)

      expect(result.leftPanelWidth.value).toBe(30)
    })

    it('RESIZE_030: mousemove clamps to minLeftPercent', () => {
      const result = usePanelResize({
        initialLeftPercent: 50,
        minLeftPercent: 25,
        maxLeftPercent: 75
      })

      result.containerRef.value = {
        getBoundingClientRect: () => ({
          width: 1000,
          left: 0
        })
      }

      result.startResize({ preventDefault: vi.fn() })

      // Try to move to 10% (below min)
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 100 })
      document.dispatchEvent(mouseMoveEvent)

      expect(result.leftPanelWidth.value).toBe(25)
    })

    it('RESIZE_031: mousemove clamps to maxLeftPercent', () => {
      const result = usePanelResize({
        initialLeftPercent: 50,
        minLeftPercent: 25,
        maxLeftPercent: 75
      })

      result.containerRef.value = {
        getBoundingClientRect: () => ({
          width: 1000,
          left: 0
        })
      }

      result.startResize({ preventDefault: vi.fn() })

      // Try to move to 90% (above max)
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 900 })
      document.dispatchEvent(mouseMoveEvent)

      expect(result.leftPanelWidth.value).toBe(75)
    })

    it('RESIZE_032: mousemove does nothing when not resizing', () => {
      const result = usePanelResize({ initialLeftPercent: 50 })

      result.containerRef.value = {
        getBoundingClientRect: () => ({
          width: 1000,
          left: 0
        })
      }

      // Don't call startResize - just dispatch mousemove
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 300 })
      document.dispatchEvent(mouseMoveEvent)

      expect(result.leftPanelWidth.value).toBe(50) // Unchanged
    })

    it('RESIZE_033: mousemove handles container offset', () => {
      const result = usePanelResize({
        initialLeftPercent: 50,
        minLeftPercent: 0,
        maxLeftPercent: 100
      })

      result.containerRef.value = {
        getBoundingClientRect: () => ({
          width: 1000,
          left: 100 // Container starts at 100px
        })
      }

      result.startResize({ preventDefault: vi.fn() })

      // Mouse at 400px, container at 100px, so relative position is 300px
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 400 })
      document.dispatchEvent(mouseMoveEvent)

      expect(result.leftPanelWidth.value).toBe(30)
    })
  })

  // ==================== Stop Resize Tests ====================

  describe('Stop Resize', () => {
    it('RESIZE_034: mouseup sets isResizing to false', () => {
      const result = usePanelResize()

      result.startResize({ preventDefault: vi.fn() })
      expect(result.isResizing.value).toBe(true)

      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(result.isResizing.value).toBe(false)
    })

    it('RESIZE_035: mouseup clears cursor style', () => {
      const result = usePanelResize()

      result.startResize({ preventDefault: vi.fn() })
      expect(document.body.style.cursor).toBe('col-resize')

      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(document.body.style.cursor).toBe('')
    })

    it('RESIZE_036: mouseup clears userSelect style', () => {
      const result = usePanelResize()

      result.startResize({ preventDefault: vi.fn() })
      expect(document.body.style.userSelect).toBe('none')

      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(document.body.style.userSelect).toBe('')
    })

    it('RESIZE_037: mouseup removes event listeners', () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')
      const result = usePanelResize()

      result.startResize({ preventDefault: vi.fn() })

      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousemove', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('mouseup', expect.any(Function))
    })
  })

  // ==================== LocalStorage Tests ====================

  describe('LocalStorage', () => {
    it('RESIZE_038: saves width to localStorage on mouseup when storageKey provided', () => {
      const result = usePanelResize({
        initialLeftPercent: 50,
        storageKey: 'test-width'
      })

      result.containerRef.value = {
        getBoundingClientRect: () => ({ width: 1000, left: 0 })
      }

      result.startResize({ preventDefault: vi.fn() })

      // Move to 40%
      const mouseMoveEvent = new MouseEvent('mousemove', { clientX: 400 })
      document.dispatchEvent(mouseMoveEvent)

      // Stop resizing
      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(localStorageMock.setItem).toHaveBeenCalledWith('test-width', '40')
    })

    it('RESIZE_039: does not save to localStorage when no storageKey', () => {
      const result = usePanelResize({ initialLeftPercent: 50 })

      result.startResize({ preventDefault: vi.fn() })

      const mouseUpEvent = new MouseEvent('mouseup')
      document.dispatchEvent(mouseUpEvent)

      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })

    it('RESIZE_040: loads width from localStorage on mount', async () => {
      localStorageMock.getItem.mockReturnValue('35')

      const TestComponent = createTestComponent({
        initialLeftPercent: 50,
        minLeftPercent: 20,
        maxLeftPercent: 80,
        storageKey: 'saved-width'
      })

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(wrapper.vm.leftPanelWidth).toBe(35)
    })

    it('RESIZE_041: ignores invalid localStorage value', async () => {
      localStorageMock.getItem.mockReturnValue('invalid')

      const TestComponent = createTestComponent({
        initialLeftPercent: 50,
        storageKey: 'bad-value'
      })

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(wrapper.vm.leftPanelWidth).toBe(50)
    })

    it('RESIZE_042: ignores localStorage value below min', async () => {
      localStorageMock.getItem.mockReturnValue('10')

      const TestComponent = createTestComponent({
        initialLeftPercent: 50,
        minLeftPercent: 25,
        maxLeftPercent: 75,
        storageKey: 'low-value'
      })

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(wrapper.vm.leftPanelWidth).toBe(50)
    })

    it('RESIZE_043: ignores localStorage value above max', async () => {
      localStorageMock.getItem.mockReturnValue('90')

      const TestComponent = createTestComponent({
        initialLeftPercent: 50,
        minLeftPercent: 25,
        maxLeftPercent: 75,
        storageKey: 'high-value'
      })

      const wrapper = mount(TestComponent)
      await nextTick()

      expect(wrapper.vm.leftPanelWidth).toBe(50)
    })
  })

  // ==================== Cleanup Tests ====================

  describe('Cleanup', () => {
    it('RESIZE_044: removes event listeners on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      // Start resizing to add listeners
      wrapper.vm.startResize({ preventDefault: vi.fn() })

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('mousemove', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('mouseup', expect.any(Function))
    })

    it('RESIZE_045: cleanup is safe when not resizing', async () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent)

      // Just unmount without starting resize
      expect(() => wrapper.unmount()).not.toThrow()
    })
  })
})
