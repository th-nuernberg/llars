/**
 * useAppTheme Composable Tests
 *
 * Tests for the LLARS theme management composable.
 * Test IDs: THEME_001 - THEME_050
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value }),
    removeItem: vi.fn((key) => { delete store[key] }),
    clear: vi.fn(() => { store = {} }),
    _getStore: () => store
  }
})()

Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock matchMedia
const createMatchMediaMock = (matches = false) => {
  const listeners = []
  return {
    matches,
    addEventListener: vi.fn((event, handler) => {
      listeners.push(handler)
    }),
    removeEventListener: vi.fn(),
    addListener: vi.fn((handler) => {
      listeners.push(handler)
    }),
    removeListener: vi.fn(),
    _triggerChange: (newMatches) => {
      listeners.forEach(handler => handler({ matches: newMatches }))
    },
    _listeners: listeners
  }
}

let matchMediaMock = createMatchMediaMock(false)

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => matchMediaMock)
})

// Create Vuetify instance
const vuetify = createVuetify({ components, directives })

// We need to reset modules to get fresh state for each test
let useAppTheme, initAppTheme

// Helper to create a test component that uses the composable
function createTestComponent() {
  return defineComponent({
    setup() {
      const theme = useAppTheme()
      return { ...theme }
    },
    render() {
      return h('div', 'Test')
    }
  })
}

describe('useAppTheme Composable', () => {
  beforeEach(async () => {
    // Clear all mocks
    vi.clearAllMocks()
    localStorageMock.clear()

    // Reset matchMedia mock
    matchMediaMock = createMatchMediaMock(false)
    window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

    // Reset document attribute
    document.documentElement.removeAttribute('data-theme')

    // Reset module to get fresh state
    vi.resetModules()

    // Re-import to get fresh state
    const module = await import('@/composables/useAppTheme')
    useAppTheme = module.useAppTheme
    initAppTheme = module.initAppTheme
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Export Tests ====================

  describe('Exports', () => {
    it('THEME_001: exports useAppTheme function', () => {
      expect(typeof useAppTheme).toBe('function')
    })

    it('THEME_002: exports initAppTheme function', () => {
      expect(typeof initAppTheme).toBe('function')
    })

    it('THEME_003: useAppTheme returns all expected properties', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // State
      expect(wrapper.vm).toHaveProperty('themePreference')
      expect(wrapper.vm).toHaveProperty('currentTheme')
      expect(wrapper.vm).toHaveProperty('isDark')
      expect(wrapper.vm).toHaveProperty('systemPrefersDark')

      // Options
      expect(wrapper.vm).toHaveProperty('themeOptions')
      expect(wrapper.vm).toHaveProperty('currentThemeOption')

      // Methods
      expect(wrapper.vm).toHaveProperty('setThemePreference')
      expect(wrapper.vm).toHaveProperty('toggleTheme')
      expect(wrapper.vm).toHaveProperty('applyTheme')
    })
  })

  // ==================== Initial State Tests ====================

  describe('Initial State', () => {
    it('THEME_004: themePreference defaults to system', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.themePreference).toBe('system')
    })

    it('THEME_005: loads themePreference from localStorage', async () => {
      localStorageMock.setItem('llars-theme-preference', 'dark')

      vi.resetModules()
      const module = await import('@/composables/useAppTheme')
      useAppTheme = module.useAppTheme

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.themePreference).toBe('dark')
    })

    it('THEME_006: systemPrefersDark reflects system preference', () => {
      matchMediaMock = createMatchMediaMock(true)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      // After mount, systemPrefersDark should be updated
      expect(wrapper.vm.systemPrefersDark).toBe(true)
    })

    it('THEME_007: themeOptions contains all three options', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const options = wrapper.vm.themeOptions

      expect(options).toHaveLength(3)
      expect(options.map(o => o.value)).toEqual(['system', 'light', 'dark'])
    })

    it('THEME_008: themeOptions have correct structure', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const options = wrapper.vm.themeOptions

      options.forEach(option => {
        expect(option).toHaveProperty('value')
        expect(option).toHaveProperty('title')
        expect(option).toHaveProperty('icon')
      })
    })

    it('THEME_009: system option has correct icon', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const systemOption = wrapper.vm.themeOptions.find(o => o.value === 'system')

      expect(systemOption.icon).toBe('llars:system-theme')
    })

    it('THEME_010: light option has correct icon', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const lightOption = wrapper.vm.themeOptions.find(o => o.value === 'light')

      expect(lightOption.icon).toBe('llars:sun')
    })

    it('THEME_011: dark option has correct icon', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const darkOption = wrapper.vm.themeOptions.find(o => o.value === 'dark')

      expect(darkOption.icon).toBe('llars:moon')
    })
  })

  // ==================== setThemePreference Tests ====================

  describe('setThemePreference', () => {
    it('THEME_012: setThemePreference updates themePreference', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(wrapper.vm.themePreference).toBe('dark')
    })

    it('THEME_013: setThemePreference saves to localStorage', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')

      expect(localStorageMock.setItem).toHaveBeenCalledWith('llars-theme-preference', 'light')
    })

    it('THEME_014: setThemePreference accepts light', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')

      expect(wrapper.vm.themePreference).toBe('light')
    })

    it('THEME_015: setThemePreference accepts dark', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(wrapper.vm.themePreference).toBe('dark')
    })

    it('THEME_016: setThemePreference accepts system', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')
      wrapper.vm.setThemePreference('system')

      expect(wrapper.vm.themePreference).toBe('system')
    })

    it('THEME_017: setThemePreference rejects invalid values', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const originalPreference = wrapper.vm.themePreference
      wrapper.vm.setThemePreference('invalid')

      expect(wrapper.vm.themePreference).toBe(originalPreference)
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })

    it('THEME_018: setThemePreference calls applyTheme', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      wrapper.vm.setThemePreference('dark')

      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining('Theme applied'))

      consoleSpy.mockRestore()
    })

    it('THEME_019: setThemePreference updates data-theme attribute', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })
  })

  // ==================== toggleTheme Tests ====================

  describe('toggleTheme', () => {
    it('THEME_020: toggleTheme switches from light to dark', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')
      wrapper.vm.toggleTheme()

      expect(wrapper.vm.themePreference).toBe('dark')
    })

    it('THEME_021: toggleTheme switches from dark to light', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')
      wrapper.vm.toggleTheme()

      expect(wrapper.vm.themePreference).toBe('light')
    })

    it('THEME_022: toggleTheme saves new preference', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')
      vi.clearAllMocks()

      wrapper.vm.toggleTheme()

      expect(localStorageMock.setItem).toHaveBeenCalledWith('llars-theme-preference', 'dark')
    })
  })

  // ==================== currentThemeOption Tests ====================

  describe('currentThemeOption', () => {
    it('THEME_023: currentThemeOption returns correct option for system', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('system')

      expect(wrapper.vm.currentThemeOption.value).toBe('system')
      expect(wrapper.vm.currentThemeOption.icon).toBe('llars:system-theme')
    })

    it('THEME_024: currentThemeOption returns correct option for light', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')

      expect(wrapper.vm.currentThemeOption.value).toBe('light')
      expect(wrapper.vm.currentThemeOption.icon).toBe('llars:sun')
    })

    it('THEME_025: currentThemeOption returns correct option for dark', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(wrapper.vm.currentThemeOption.value).toBe('dark')
      expect(wrapper.vm.currentThemeOption.icon).toBe('llars:moon')
    })

    it('THEME_026: currentThemeOption updates reactively', async () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.currentThemeOption.value).toBe('system')

      wrapper.vm.setThemePreference('dark')
      await nextTick()

      expect(wrapper.vm.currentThemeOption.value).toBe('dark')
    })
  })

  // ==================== applyTheme Tests ====================

  describe('applyTheme', () => {
    it('THEME_027: applyTheme sets data-theme to light for light preference', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')

      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    })

    it('THEME_028: applyTheme sets data-theme to dark for dark preference', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })

    it('THEME_029: applyTheme respects system preference when set to system', () => {
      matchMediaMock = createMatchMediaMock(true) // System prefers dark
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('system')

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })

    it('THEME_030: applyTheme uses light when system prefers light', () => {
      matchMediaMock = createMatchMediaMock(false) // System prefers light
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('system')

      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    })

    it('THEME_031: applyTheme logs theme application', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('Theme applied: dark')
      )

      consoleSpy.mockRestore()
    })
  })

  // ==================== System Preference Change Tests ====================

  describe('System Preference Changes', () => {
    it('THEME_032: responds to system preference change when on system mode', async () => {
      matchMediaMock = createMatchMediaMock(false)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('system')
      await nextTick()

      expect(document.documentElement.getAttribute('data-theme')).toBe('light')

      // Simulate system preference change to dark
      matchMediaMock._triggerChange(true)
      await nextTick()

      expect(wrapper.vm.systemPrefersDark).toBe(true)
    })

    it('THEME_033: adds event listener for preference changes', () => {
      const TestComponent = createTestComponent()
      mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(matchMediaMock.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))
    })
  })

  // ==================== initAppTheme Tests ====================

  describe('initAppTheme', () => {
    it('THEME_034: initAppTheme loads saved theme from localStorage', () => {
      localStorageMock.setItem('llars-theme-preference', 'dark')

      initAppTheme()

      expect(localStorageMock.getItem).toHaveBeenCalledWith('llars-theme-preference')
    })

    it('THEME_035: initAppTheme sets data-theme attribute', () => {
      localStorageMock.setItem('llars-theme-preference', 'dark')

      initAppTheme()

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })

    it('THEME_036: initAppTheme defaults to system preference', () => {
      matchMediaMock = createMatchMediaMock(true)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      initAppTheme()

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })

    it('THEME_037: initAppTheme uses light when no preference and system is light', () => {
      matchMediaMock = createMatchMediaMock(false)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      initAppTheme()

      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    })

    it('THEME_038: initAppTheme works with vuetify instance', () => {
      const mockVuetify = {
        theme: {
          global: {
            name: { value: 'light' }
          }
        }
      }

      localStorageMock.setItem('llars-theme-preference', 'dark')

      initAppTheme(mockVuetify)

      expect(mockVuetify.theme.global.name.value).toBe('dark')
    })

    it('THEME_039: initAppTheme uses theme.change if available', () => {
      const changeMock = vi.fn()
      const mockVuetify = {
        theme: {
          change: changeMock
        }
      }

      localStorageMock.setItem('llars-theme-preference', 'dark')

      initAppTheme(mockVuetify)

      expect(changeMock).toHaveBeenCalledWith('dark')
    })

    it('THEME_040: initAppTheme logs initialization', () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})

      initAppTheme()

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('App theme initialized')
      )

      consoleSpy.mockRestore()
    })

    it('THEME_041: initAppTheme adds listener for system changes', () => {
      initAppTheme()

      expect(matchMediaMock.addEventListener).toHaveBeenCalledWith('change', expect.any(Function))
    })

    it('THEME_042: initAppTheme handles system mode correctly', () => {
      matchMediaMock = createMatchMediaMock(false)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      localStorageMock.setItem('llars-theme-preference', 'system')

      initAppTheme()

      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    })
  })

  // ==================== Shared State Tests ====================

  describe('Shared State', () => {
    it('THEME_043: multiple instances share themePreference', () => {
      const TestComponent = createTestComponent()
      const wrapper1 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })
      const wrapper2 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper1.vm.setThemePreference('dark')

      expect(wrapper2.vm.themePreference).toBe('dark')
    })

    it('THEME_044: multiple instances share systemPrefersDark', () => {
      matchMediaMock = createMatchMediaMock(true)
      window.matchMedia = vi.fn().mockImplementation(() => matchMediaMock)

      const TestComponent = createTestComponent()
      const wrapper1 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })
      const wrapper2 = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper1.vm.systemPrefersDark).toBe(true)
      expect(wrapper2.vm.systemPrefersDark).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('THEME_045: handles empty localStorage value', async () => {
      localStorageMock.clear()

      vi.resetModules()
      const module = await import('@/composables/useAppTheme')
      useAppTheme = module.useAppTheme

      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(wrapper.vm.themePreference).toBe('system')
    })

    it('THEME_046: themeOptions is computed and cached', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const options1 = wrapper.vm.themeOptions
      const options2 = wrapper.vm.themeOptions

      expect(options1).toBe(options2)
    })

    it('THEME_047: theme titles are in German', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      const options = wrapper.vm.themeOptions

      expect(options.find(o => o.value === 'light').title).toBe('Hell')
      expect(options.find(o => o.value === 'dark').title).toBe('Dunkel')
    })

    it('THEME_048: setThemePreference is idempotent', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('dark')
      wrapper.vm.setThemePreference('dark')
      wrapper.vm.setThemePreference('dark')

      expect(wrapper.vm.themePreference).toBe('dark')
    })

    it('THEME_049: handles rapid theme switches', () => {
      const TestComponent = createTestComponent()
      const wrapper = mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      wrapper.vm.setThemePreference('light')
      wrapper.vm.setThemePreference('dark')
      wrapper.vm.setThemePreference('system')
      wrapper.vm.setThemePreference('light')

      expect(wrapper.vm.themePreference).toBe('light')
      expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    })

    it('THEME_050: fallback for older browsers without addEventListener', () => {
      // Create mock without addEventListener
      const oldBrowserMock = {
        matches: true,
        addListener: vi.fn(),
        removeListener: vi.fn()
      }

      window.matchMedia = vi.fn().mockImplementation(() => oldBrowserMock)

      const TestComponent = createTestComponent()
      mount(TestComponent, {
        global: { plugins: [vuetify] }
      })

      expect(oldBrowserMock.addListener).toHaveBeenCalled()
    })
  })
})
