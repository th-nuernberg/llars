/**
 * Vitest Setup File
 *
 * Configures the test environment with Vue, Vuetify, and common mocks.
 */

import { config } from '@vue/test-utils'
import { vi } from 'vitest'
import LIcon from '@/components/common/LIcon.vue'
import i18n from '@/i18n'

// Configure Vue Test Utils globally
config.global.plugins = [i18n]
config.global.components = {
  ...(config.global.components || {}),
  LIcon,
}

// Add common stubs
config.global.stubs = {
  // Stub router-link and router-view
  'router-link': {
    template: '<a><slot /></a>',
    props: ['to'],
  },
  'router-view': {
    template: '<div class="router-view-stub"><slot /></div>',
  },
}

// Mock commonly used browser APIs
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock ResizeObserver as a class
class ResizeObserverMock {
  constructor(callback) {
    this.callback = callback
  }
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}
global.ResizeObserver = ResizeObserverMock

// Mock IntersectionObserver as a class
class IntersectionObserverMock {
  constructor(callback, options) {
    this.callback = callback
    this.options = options
  }
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
  takeRecords = vi.fn(() => [])
}
global.IntersectionObserver = IntersectionObserverMock

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'localStorage', { value: localStorageMock })

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(window, 'sessionStorage', { value: sessionStorageMock })

// Reset mocks between tests
beforeEach(() => {
  if (i18n?.global?.locale?.value) {
    i18n.global.locale.value = 'de'
  }
  vi.clearAllMocks()
  localStorageMock.getItem.mockReset()
  localStorageMock.setItem.mockReset()
  sessionStorageMock.getItem.mockReset()
  sessionStorageMock.setItem.mockReset()
})

// Clean up after each test
afterEach(() => {
  vi.restoreAllMocks()
})
