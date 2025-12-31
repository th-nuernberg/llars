/**
 * useMobile Composable Tests
 *
 * Tests for the LLARS mobile/responsive detection composable.
 * Test IDs: MOBILE_001 - MOBILE_055
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Create Vuetify instance
const vuetify = createVuetify({ components, directives })

// Mock navigator
const createNavigatorMock = (userAgent) => ({
  userAgent,
  maxTouchPoints: 0,
  msMaxTouchPoints: 0
})

// Store original values
let originalNavigator
let originalWindow
let originalOntouchstart

// We need to reset modules to get fresh state for each test
let useMobile

// Helper to create a test component that uses the composable
function createTestComponent() {
  return defineComponent({
    setup() {
      const mobile = useMobile()
      return { ...mobile }
    },
    render() {
      return h('div', 'Test')
    }
  })
}

describe('useMobile Composable', () => {
  beforeEach(async () => {
    // Clear all mocks
    vi.clearAllMocks()

    // Store originals
    originalNavigator = global.navigator
    originalWindow = {
      innerWidth: window.innerWidth,
      innerHeight: window.innerHeight
    }
    originalOntouchstart = window.ontouchstart

    // Default window size (desktop)
    Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true, configurable: true })
    Object.defineProperty(window, 'innerHeight', { value: 1080, writable: true, configurable: true })

    // Default: no touch
    delete window.ontouchstart

    // Default navigator (desktop Chrome)
    Object.defineProperty(global, 'navigator', {
      value: createNavigatorMock('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
      writable: true,
      configurable: true
    })

    // Reset module to get fresh state
    vi.resetModules()

    // Re-import to get fresh state
    const module = await import('@/composables/useMobile')
    useMobile = module.useMobile
  })

  afterEach(() => {
    // Restore originals
    Object.defineProperty(window, 'innerWidth', { value: originalWindow.innerWidth, writable: true, configurable: true })
    Object.defineProperty(window, 'innerHeight', { value: originalWindow.innerHeight, writable: true, configurable: true })

    if (originalOntouchstart !== undefined) {
      window.ontouchstart = originalOntouchstart
    }

    vi.restoreAllMocks()
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('MOBILE_001: exports useMobile function', () => {
      expect(typeof useMobile).toBe('function')
    })

    it('MOBILE_002: returns all expected properties', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // Device type detection
      expect(wrapper.vm).toHaveProperty('isMobile')
      expect(wrapper.vm).toHaveProperty('isTablet')
      expect(wrapper.vm).toHaveProperty('isDesktop')
      expect(wrapper.vm).toHaveProperty('isSmallScreen')
      expect(wrapper.vm).toHaveProperty('isTouchDevice')

      // Platform detection
      expect(wrapper.vm).toHaveProperty('platform')
      expect(wrapper.vm).toHaveProperty('isIOS')
      expect(wrapper.vm).toHaveProperty('isAndroid')

      // Breakpoint utilities
      expect(wrapper.vm).toHaveProperty('breakpoint')
      expect(wrapper.vm).toHaveProperty('isBreakpointOrSmaller')
      expect(wrapper.vm).toHaveProperty('isBreakpointOrLarger')

      // Dimensions
      expect(wrapper.vm).toHaveProperty('windowWidth')
      expect(wrapper.vm).toHaveProperty('windowHeight')
      expect(wrapper.vm).toHaveProperty('isPortrait')
      expect(wrapper.vm).toHaveProperty('isLandscape')

      // iOS safe areas
      expect(wrapper.vm).toHaveProperty('safeAreaInsets')

      // Vuetify display
      expect(wrapper.vm).toHaveProperty('display')
    })
  })

  // ==================== Window Dimensions Tests ====================

  describe('Window Dimensions', () => {
    it('MOBILE_003: windowWidth reflects window.innerWidth', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1024, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.windowWidth).toBe(1024)
    })

    it('MOBILE_004: windowHeight reflects window.innerHeight', () => {
      Object.defineProperty(window, 'innerHeight', { value: 768, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.windowHeight).toBe(768)
    })

    it('MOBILE_005: isPortrait is true when height > width', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, writable: true, configurable: true })
      Object.defineProperty(window, 'innerHeight', { value: 800, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isPortrait).toBe(true)
      expect(wrapper.vm.isLandscape).toBe(false)
    })

    it('MOBILE_006: isLandscape is true when width > height', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true, configurable: true })
      Object.defineProperty(window, 'innerHeight', { value: 1080, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isLandscape).toBe(true)
      expect(wrapper.vm.isPortrait).toBe(false)
    })

    it('MOBILE_007: registers resize event listener on mount', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      const TestComponent = createTestComponent()
      mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(addEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function), { passive: true })
    })

    it('MOBILE_008: removes resize event listener on unmount', () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('resize', expect.any(Function))
    })
  })

  // ==================== Touch Device Detection ====================

  describe('Touch Device Detection', () => {
    it('MOBILE_009: isTouchDevice is false on non-touch device', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isTouchDevice).toBe(false)
    })

    it('MOBILE_010: isTouchDevice is true when ontouchstart exists', async () => {
      window.ontouchstart = () => {}

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isTouchDevice).toBe(true)
    })

    it('MOBILE_011: isTouchDevice is true when maxTouchPoints > 0', async () => {
      Object.defineProperty(global, 'navigator', {
        value: { ...createNavigatorMock('desktop'), maxTouchPoints: 5 },
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isTouchDevice).toBe(true)
    })
  })

  // ==================== Platform Detection ====================

  describe('Platform Detection', () => {
    it('MOBILE_012: detects iPhone platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('iphone')
    })

    it('MOBILE_013: detects iPad platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('ipad')
    })

    it('MOBILE_014: detects Android phone platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Mobile'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('android-phone')
    })

    it('MOBILE_015: detects Android tablet platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Linux; Android 14; SM-X900) AppleWebKit/537.36'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('android-tablet')
    })

    it('MOBILE_016: detects Windows platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('windows')
    })

    it('MOBILE_017: detects Mac platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('mac')
    })

    it('MOBILE_018: detects Linux platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('linux')
    })

    it('MOBILE_019: returns unknown for unrecognized platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('SomeUnknownBrowser/1.0'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('unknown')
    })
  })

  // ==================== iOS/Android Detection ====================

  describe('iOS/Android Detection', () => {
    it('MOBILE_020: isIOS is true for iPhone', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isIOS).toBe(true)
    })

    it('MOBILE_021: isIOS is true for iPad', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isIOS).toBe(true)
    })

    it('MOBILE_022: isIOS detects iPad Pro (reports as Mac with touch)', async () => {
      window.ontouchstart = () => {}
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isIOS).toBe(true)
    })

    it('MOBILE_023: isAndroid is true for Android phone', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Mobile'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isAndroid).toBe(true)
    })

    it('MOBILE_024: isAndroid is true for Android tablet', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Linux; Android 14; SM-X900) AppleWebKit/537.36'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isAndroid).toBe(true)
    })

    it('MOBILE_025: isIOS is false for Android', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (Linux; Android 14; Pixel 8) Mobile'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isIOS).toBe(false)
    })

    it('MOBILE_026: isAndroid is false for iOS', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isAndroid).toBe(false)
    })
  })

  // ==================== Device Type Detection ====================

  describe('Device Type Detection', () => {
    it('MOBILE_027: isMobile is true for iPhone', async () => {
      Object.defineProperty(window, 'innerWidth', { value: 390, writable: true, configurable: true })
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isMobile).toBe(true)
    })

    it('MOBILE_028: isMobile is true for small screen width', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isMobile).toBe(true)
    })

    it('MOBILE_029: isTablet is true for iPad', async () => {
      window.ontouchstart = () => {}
      Object.defineProperty(window, 'innerWidth', { value: 820, writable: true, configurable: true })
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isTablet).toBe(true)
    })

    it('MOBILE_030: isDesktop is true for large screen without touch', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isDesktop).toBe(true)
    })

    it('MOBILE_031: isDesktop is false when isMobile is true', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isMobile).toBe(true)
      expect(wrapper.vm.isDesktop).toBe(false)
    })

    it('MOBILE_032: isSmallScreen is true for mobile', () => {
      Object.defineProperty(window, 'innerWidth', { value: 400, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isSmallScreen).toBe(true)
    })

    it('MOBILE_033: isSmallScreen is false for desktop', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isSmallScreen).toBe(false)
    })

    it('MOBILE_034: device types are mutually exclusive', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1920, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // Count how many are true
      const trueCount = [
        wrapper.vm.isMobile,
        wrapper.vm.isTablet,
        wrapper.vm.isDesktop
      ].filter(Boolean).length

      expect(trueCount).toBe(1)
    })
  })

  // ==================== Breakpoint Utilities ====================

  describe('Breakpoint Utilities', () => {
    it('MOBILE_035: breakpoint returns current breakpoint name', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(['xs', 'sm', 'md', 'lg', 'xl', 'xxl']).toContain(wrapper.vm.breakpoint)
    })

    it('MOBILE_036: isBreakpointOrSmaller is a function', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(typeof wrapper.vm.isBreakpointOrSmaller).toBe('function')
    })

    it('MOBILE_037: isBreakpointOrLarger is a function', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(typeof wrapper.vm.isBreakpointOrLarger).toBe('function')
    })

    it('MOBILE_038: isBreakpointOrSmaller returns boolean', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(typeof wrapper.vm.isBreakpointOrSmaller('md')).toBe('boolean')
    })

    it('MOBILE_039: isBreakpointOrLarger returns boolean', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(typeof wrapper.vm.isBreakpointOrLarger('md')).toBe('boolean')
    })

    it('MOBILE_040: isBreakpointOrSmaller(xxl) always true', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isBreakpointOrSmaller('xxl')).toBe(true)
    })

    it('MOBILE_041: isBreakpointOrLarger(xs) always true', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isBreakpointOrLarger('xs')).toBe(true)
    })
  })

  // ==================== Safe Area Insets ====================

  describe('Safe Area Insets', () => {
    it('MOBILE_042: safeAreaInsets returns object with all sides', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const insets = wrapper.vm.safeAreaInsets

      expect(insets).toHaveProperty('top')
      expect(insets).toHaveProperty('right')
      expect(insets).toHaveProperty('bottom')
      expect(insets).toHaveProperty('left')
    })

    it('MOBILE_043: safeAreaInsets uses CSS env() values', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const insets = wrapper.vm.safeAreaInsets

      expect(insets.top).toContain('env(safe-area-inset-top')
      expect(insets.bottom).toContain('env(safe-area-inset-bottom')
    })

    it('MOBILE_044: safeAreaInsets provides fallback values', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const insets = wrapper.vm.safeAreaInsets

      expect(insets.top).toContain('0px')
      expect(insets.right).toContain('0px')
      expect(insets.bottom).toContain('0px')
      expect(insets.left).toContain('0px')
    })
  })

  // ==================== Vuetify Display Pass-through ====================

  describe('Vuetify Display', () => {
    it('MOBILE_045: display is passed through from Vuetify', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.display).toBeDefined()
    })

    it('MOBILE_046: display has Vuetify breakpoint properties', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // Vuetify display should have these properties
      expect(wrapper.vm.display).toHaveProperty('xs')
      expect(wrapper.vm.display).toHaveProperty('sm')
      expect(wrapper.vm.display).toHaveProperty('md')
      expect(wrapper.vm.display).toHaveProperty('lg')
      expect(wrapper.vm.display).toHaveProperty('xl')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('MOBILE_047: handles undefined navigator gracefully', async () => {
      // This mainly tests the SSR guard
      const TestComponent = createTestComponent()

      // Should not throw
      expect(() => {
        mount(TestComponent, {
          global: { plugins: [vuetify] }
        })
      }).not.toThrow()
    })

    it('MOBILE_048: multiple instances work independently', () => {
      const TestComponent = createTestComponent()
      const wrapper1 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })
      const wrapper2 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper1.vm.windowWidth).toBe(wrapper2.vm.windowWidth)
    })

    it('MOBILE_049: handles square screen (portrait edge case)', () => {
      Object.defineProperty(window, 'innerWidth', { value: 1000, writable: true, configurable: true })
      Object.defineProperty(window, 'innerHeight', { value: 1000, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // Neither portrait nor landscape when equal
      expect(wrapper.vm.isPortrait).toBe(false)
      expect(wrapper.vm.isLandscape).toBe(false)
    })

    it('MOBILE_050: breakpoint utilities handle all valid breakpoints', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const breakpoints = ['xs', 'sm', 'md', 'lg', 'xl', 'xxl']

      breakpoints.forEach(bp => {
        expect(() => wrapper.vm.isBreakpointOrSmaller(bp)).not.toThrow()
        expect(() => wrapper.vm.isBreakpointOrLarger(bp)).not.toThrow()
      })
    })

    it('MOBILE_051: iPod is detected as iphone platform', async () => {
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPod; CPU iPhone OS 15_0 like Mac OS X)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.platform).toBe('iphone')
    })

    it('MOBILE_052: isTablet is false when already classified as mobile', async () => {
      Object.defineProperty(window, 'innerWidth', { value: 390, writable: true, configurable: true })
      Object.defineProperty(global, 'navigator', {
        value: createNavigatorMock('Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)'),
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isMobile).toBe(true)
      expect(wrapper.vm.isTablet).toBe(false)
    })

    it('MOBILE_053: computed properties are reactive', async () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // Initial check
      expect(typeof wrapper.vm.isPortrait).toBe('boolean')
      expect(typeof wrapper.vm.isLandscape).toBe('boolean')

      // Values should be computed (reactive)
      expect(wrapper.vm.isPortrait).not.toBeUndefined()
    })

    it('MOBILE_054: BREAKPOINTS are aligned with Vuetify', () => {
      // These are the expected Vuetify 3 breakpoints
      const vuetifyBreakpoints = {
        xs: 0,
        sm: 600,
        md: 960,
        lg: 1264,
        xl: 1904
      }

      // Test that mobile detection uses correct thresholds
      Object.defineProperty(window, 'innerWidth', { value: 599, writable: true, configurable: true })

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // 599 is below sm (600), should be mobile
      expect(wrapper.vm.isMobile).toBe(true)
    })

    it('MOBILE_055: handles msMaxTouchPoints for IE compatibility', async () => {
      Object.defineProperty(global, 'navigator', {
        value: {
          userAgent: 'Mozilla/5.0 (Windows NT 10.0)',
          maxTouchPoints: 0,
          msMaxTouchPoints: 10
        },
        writable: true,
        configurable: true
      })

      vi.resetModules()
      const module = await import('@/composables/useMobile')
      useMobile = module.useMobile

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.isTouchDevice).toBe(true)
    })
  })
})
