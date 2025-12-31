/**
 * Test Helpers for LLARS Frontend
 *
 * Common utilities for testing Vue components with Vuetify.
 */

import { mount, shallowMount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { vi } from 'vitest'

/**
 * Create a fresh Vuetify instance for testing
 */
export function createTestVuetify() {
  return createVuetify({
    components,
    directives,
  })
}

/**
 * Mount a component with Vuetify and common configuration
 *
 * @param {Component} component - Vue component to mount
 * @param {Object} options - Mount options
 * @returns {VueWrapper} Mounted component wrapper
 */
export function mountWithVuetify(component, options = {}) {
  const vuetify = createTestVuetify()

  return mount(component, {
    global: {
      plugins: [vuetify],
      stubs: {
        'router-link': { template: '<a><slot /></a>', props: ['to'] },
        'router-view': { template: '<div><slot /></div>' },
        ...options.global?.stubs,
      },
      mocks: {
        $router: {
          push: vi.fn(),
          replace: vi.fn(),
          go: vi.fn(),
          back: vi.fn(),
        },
        $route: {
          path: '/',
          params: {},
          query: {},
          ...options.global?.mocks?.$route,
        },
        ...options.global?.mocks,
      },
      ...options.global,
    },
    ...options,
  })
}

/**
 * Shallow mount a component with Vuetify
 *
 * @param {Component} component - Vue component to mount
 * @param {Object} options - Mount options
 * @returns {VueWrapper} Mounted component wrapper
 */
export function shallowMountWithVuetify(component, options = {}) {
  const vuetify = createTestVuetify()

  return shallowMount(component, {
    global: {
      plugins: [vuetify],
      stubs: {
        'router-link': { template: '<a><slot /></a>', props: ['to'] },
        'router-view': { template: '<div><slot /></div>' },
        ...options.global?.stubs,
      },
      ...options.global,
    },
    ...options,
  })
}

/**
 * Create a mock for usePermissions composable
 *
 * @param {Object} overrides - Permission overrides
 * @returns {Object} Mocked usePermissions return value
 */
export function mockUsePermissions(overrides = {}) {
  return {
    hasPermission: vi.fn((perm) => overrides[perm] ?? true),
    hasAnyPermission: vi.fn(() => true),
    hasAllPermissions: vi.fn(() => true),
    permissions: [],
    loading: false,
    ...overrides,
  }
}

/**
 * Create a mock for useAuth composable
 *
 * @param {Object} overrides - Auth state overrides
 * @returns {Object} Mocked useAuth return value
 */
export function mockUseAuth(overrides = {}) {
  return {
    isAuthenticated: true,
    user: {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      groups: ['researcher'],
      ...overrides.user,
    },
    token: 'mock-jwt-token',
    logout: vi.fn(),
    refreshToken: vi.fn(),
    ...overrides,
  }
}

/**
 * Create a mock axios instance
 *
 * @returns {Object} Mocked axios
 */
export function createMockAxios() {
  return {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
    defaults: {
      headers: { common: {} },
    },
  }
}

/**
 * Create a mock Socket.IO client
 *
 * @returns {Object} Mocked socket
 */
export function createMockSocket() {
  const eventHandlers = {}

  return {
    on: vi.fn((event, handler) => {
      eventHandlers[event] = handler
    }),
    emit: vi.fn(),
    off: vi.fn(),
    connect: vi.fn(),
    disconnect: vi.fn(),
    connected: true,
    // Helper to simulate receiving an event
    simulateEvent: (event, data) => {
      if (eventHandlers[event]) {
        eventHandlers[event](data)
      }
    },
  }
}

/**
 * Wait for Vue to update the DOM
 *
 * @param {number} ms - Milliseconds to wait (default: 0)
 * @returns {Promise}
 */
export function flushPromises(ms = 0) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Find a component by test-id attribute
 *
 * @param {VueWrapper} wrapper - Component wrapper
 * @param {string} testId - Test ID to find
 * @returns {DOMWrapper}
 */
export function findByTestId(wrapper, testId) {
  return wrapper.find(`[data-testid="${testId}"]`)
}

/**
 * Assert that an element has specific LLARS design classes
 *
 * @param {DOMWrapper} element - Element wrapper
 * @param {Object} expectations - Expected classes
 */
export function assertLlarsDesign(element, expectations = {}) {
  const classList = element.classes()

  if (expectations.hasAsymmetricRadius) {
    // LLARS components should have asymmetric border-radius
    const style = element.attributes('style') || ''
    const hasAsymmetric = style.includes('border-radius') ||
                          classList.some(c => c.includes('rounded'))
    expect(hasAsymmetric).toBe(true)
  }

  if (expectations.variant) {
    expect(classList.some(c => c.includes(expectations.variant))).toBe(true)
  }
}

/**
 * Create test props for LLARS components
 */
export const testProps = {
  lBtn: {
    default: { variant: 'primary' },
    secondary: { variant: 'secondary' },
    danger: { variant: 'danger' },
    withIcon: { variant: 'primary', prependIcon: 'mdi-plus' },
    loading: { variant: 'primary', loading: true },
    disabled: { variant: 'primary', disabled: true },
  },
  lTag: {
    default: { variant: 'primary' },
    success: { variant: 'success' },
    closable: { variant: 'primary', closable: true },
  },
  lCard: {
    default: {
      title: 'Test Card',
      subtitle: 'Test subtitle',
    },
    withIcon: {
      title: 'Test Card',
      icon: 'mdi-file',
      color: '#b0ca97',
    },
    withStats: {
      title: 'Test Card',
      stats: [
        { icon: 'mdi-file', value: 10, label: 'Documents' },
      ],
    },
  },
}
