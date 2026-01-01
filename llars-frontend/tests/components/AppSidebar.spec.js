/**
 * AppSidebar Component Tests
 *
 * Tests for the LLARS sidebar navigation component.
 * Test IDs: COMP_SDB_001 - COMP_SDB_055
 *
 * Coverage:
 * - Rendering and structure
 * - Header (icon, title, subtitle)
 * - Collapse functionality
 * - Navigation items
 * - Item selection
 * - Badges
 * - Footer and home link
 * - Slots
 * - LocalStorage persistence
 * - Reactivity
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AppSidebar from '@/components/common/AppSidebar.vue'

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

// Mock router
const mockRouter = {
  push: vi.fn()
}

function mountAppSidebar(props = {}, options = {}) {
  return mount(AppSidebar, {
    props,
    global: {
      stubs: {
        'v-icon': {
          template: '<i class="v-icon" :style="{ fontSize: size + \'px\' }"><slot>{{ $attrs.icon }}</slot></i>',
          props: ['size', 'icon']
        },
        'v-chip': {
          template: '<span class="v-chip" :class="[`bg-${color}`, variant]"><slot /></span>',
          props: ['size', 'color', 'variant']
        }
      },
      mocks: {
        $router: mockRouter
      }
    },
    ...options
  })
}

const sampleItems = [
  { value: 'dashboard', title: 'Dashboard', icon: 'mdi-view-dashboard' },
  { value: 'settings', title: 'Settings', icon: 'mdi-cog' },
  { value: 'users', title: 'Users', icon: 'mdi-account-group', badge: 5 },
  { value: 'reports', title: 'Reports', icon: 'mdi-chart-bar', badge: 'New', badgeColor: 'accent' }
]

describe('AppSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.clear()
    Object.defineProperty(window, 'localStorage', { value: localStorageMock })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_SDB_001: renders with default props', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.app-sidebar').exists()).toBe(true)
    })

    it('COMP_SDB_002: has app-sidebar class', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.classes()).toContain('app-sidebar')
    })

    it('COMP_SDB_003: renders as aside element', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.element.tagName).toBe('ASIDE')
    })

    it('COMP_SDB_004: renders sidebar-header', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.find('.sidebar-header').exists()).toBe(true)
    })

    it('COMP_SDB_005: renders sidebar-nav', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.find('.sidebar-nav').exists()).toBe(true)
    })

    it('COMP_SDB_006: renders sidebar-footer', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.find('.sidebar-footer').exists()).toBe(true)
    })

    it('COMP_SDB_007: renders sidebar-divider', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.findAll('.sidebar-divider').length).toBeGreaterThanOrEqual(1)
    })
  })

  // ==================== Header Tests ====================

  describe('Header', () => {
    it('COMP_SDB_008: renders header title', () => {
      const wrapper = mountAppSidebar({ title: 'Navigation' })

      expect(wrapper.find('.header-title').text()).toBe('Navigation')
    })

    it('COMP_SDB_009: renders header subtitle', () => {
      const wrapper = mountAppSidebar({ title: 'Nav', subtitle: 'Main Menu' })

      expect(wrapper.find('.header-subtitle').text()).toBe('Main Menu')
    })

    it('COMP_SDB_010: does not render subtitle when not provided', () => {
      const wrapper = mountAppSidebar({ title: 'Nav' })

      expect(wrapper.find('.header-subtitle').exists()).toBe(false)
    })

    it('COMP_SDB_011: renders header icon', () => {
      const wrapper = mountAppSidebar({ icon: 'mdi-cog', title: 'Settings' })

      expect(wrapper.find('.header-icon').exists()).toBe(true)
    })

    it('COMP_SDB_012: uses default icon mdi-menu', () => {
      const wrapper = mountAppSidebar({ title: 'Test' })

      expect(wrapper.find('.header-icon').text()).toContain('mdi-menu')
    })

    it('COMP_SDB_013: renders collapse button', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.find('.collapse-btn').exists()).toBe(true)
    })

    it('COMP_SDB_014: collapse button shows left chevron when expanded', () => {
      const wrapper = mountAppSidebar({ collapsed: false })

      expect(wrapper.find('.collapse-btn .v-icon').text()).toContain('mdi-chevron-left')
    })

    it('COMP_SDB_015: collapse button shows right chevron when collapsed', () => {
      const wrapper = mountAppSidebar({ collapsed: true })

      expect(wrapper.find('.collapse-btn .v-icon').text()).toContain('mdi-chevron-right')
    })
  })

  // ==================== Collapse Tests ====================

  describe('Collapse Functionality', () => {
    it('COMP_SDB_016: does not have collapsed class by default', () => {
      const wrapper = mountAppSidebar()

      expect(wrapper.classes()).not.toContain('collapsed')
    })

    it('COMP_SDB_017: has collapsed class when collapsed prop is true', () => {
      const wrapper = mountAppSidebar({ collapsed: true })

      expect(wrapper.classes()).toContain('collapsed')
    })

    it('COMP_SDB_018: emits update:collapsed on toggle click', async () => {
      const wrapper = mountAppSidebar({ collapsed: false })

      await wrapper.find('.collapse-btn').trigger('click')

      expect(wrapper.emitted('update:collapsed')).toBeTruthy()
      expect(wrapper.emitted('update:collapsed')[0]).toEqual([true])
    })

    it('COMP_SDB_019: toggles collapsed state internally', async () => {
      const wrapper = mountAppSidebar({ collapsed: false })

      expect(wrapper.classes()).not.toContain('collapsed')

      await wrapper.find('.collapse-btn').trigger('click')

      expect(wrapper.classes()).toContain('collapsed')
    })

    it('COMP_SDB_020: hides header text when collapsed', () => {
      const wrapper = mountAppSidebar({ title: 'Test', subtitle: 'Sub', collapsed: true })

      expect(wrapper.find('.header-title').exists()).toBe(false)
      expect(wrapper.find('.header-subtitle').exists()).toBe(false)
    })

    it('COMP_SDB_021: shows collapsed icon when collapsed', () => {
      const wrapper = mountAppSidebar({ icon: 'mdi-cog', title: 'Test', collapsed: true })

      expect(wrapper.find('.header-icon-collapsed').exists()).toBe(true)
    })

    it('COMP_SDB_022: header-content has justify-center class when collapsed', () => {
      const wrapper = mountAppSidebar({ collapsed: true })

      expect(wrapper.find('.header-content').classes()).toContain('justify-center')
    })

    it('COMP_SDB_023: collapse button has correct title when expanded', () => {
      const wrapper = mountAppSidebar({ collapsed: false })

      expect(wrapper.find('.collapse-btn').attributes('title')).toBe('Zuklappen')
    })

    it('COMP_SDB_024: collapse button has correct title when collapsed', () => {
      const wrapper = mountAppSidebar({ collapsed: true })

      expect(wrapper.find('.collapse-btn').attributes('title')).toBe('Erweitern')
    })
  })

  // ==================== Navigation Items Tests ====================

  describe('Navigation Items', () => {
    it('COMP_SDB_025: renders navigation items', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems.length).toBe(4)
    })

    it('COMP_SDB_026: displays item titles', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const labels = wrapper.findAll('.nav-label')
      expect(labels[0].text()).toBe('Dashboard')
      expect(labels[1].text()).toBe('Settings')
    })

    it('COMP_SDB_027: displays item icons', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const icons = wrapper.findAll('.nav-icon .v-icon')
      expect(icons[0].text()).toContain('mdi-view-dashboard')
      expect(icons[1].text()).toContain('mdi-cog')
    })

    it('COMP_SDB_028: hides labels when collapsed', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, collapsed: true })

      // Labels exist but are hidden via CSS - check v-if condition
      const labels = wrapper.findAll('.nav-label')
      expect(labels.length).toBe(0)
    })

    it('COMP_SDB_029: items have title attribute when collapsed', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, collapsed: true })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems[0].attributes('title')).toBe('Dashboard')
      expect(navItems[1].attributes('title')).toBe('Settings')
    })

    it('COMP_SDB_030: items do not have title attribute when expanded', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, collapsed: false })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems[0].attributes('title')).toBeUndefined()
    })
  })

  // ==================== Item Selection Tests ====================

  describe('Item Selection', () => {
    it('COMP_SDB_031: emits update:modelValue on item click', async () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      await navItems[0].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['dashboard'])
    })

    it('COMP_SDB_032: emits item-click on item click', async () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      await navItems[1].trigger('click')

      expect(wrapper.emitted('item-click')).toBeTruthy()
      expect(wrapper.emitted('item-click')[0][0]).toEqual(sampleItems[1])
    })

    it('COMP_SDB_033: active item has active class', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, modelValue: 'settings' })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems[0].classes()).not.toContain('active')
      expect(navItems[1].classes()).toContain('active')
    })

    it('COMP_SDB_034: no item active when modelValue is empty', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, modelValue: '' })

      const activeItems = wrapper.findAll('.sidebar-nav .nav-item.active')
      expect(activeItems.length).toBe(0)
    })

    it('COMP_SDB_035: clicking different items emits correct values', async () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')

      await navItems[0].trigger('click')
      await navItems[2].trigger('click')
      await navItems[3].trigger('click')

      const emitted = wrapper.emitted('update:modelValue')
      expect(emitted).toHaveLength(3)
      expect(emitted[0]).toEqual(['dashboard'])
      expect(emitted[1]).toEqual(['users'])
      expect(emitted[2]).toEqual(['reports'])
    })
  })

  // ==================== Badge Tests ====================

  describe('Badges', () => {
    it('COMP_SDB_036: renders badge when provided', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const badges = wrapper.findAll('.nav-badge')
      expect(badges.length).toBe(2)
    })

    it('COMP_SDB_037: displays badge content', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const badges = wrapper.findAll('.nav-badge')
      expect(badges[0].text()).toBe('5')
      expect(badges[1].text()).toBe('New')
    })

    it('COMP_SDB_038: badge uses default primary color', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const badges = wrapper.findAll('.nav-badge')
      expect(badges[0].classes()).toContain('bg-primary')
    })

    it('COMP_SDB_039: badge uses custom color when provided', () => {
      const wrapper = mountAppSidebar({ items: sampleItems })

      const badges = wrapper.findAll('.nav-badge')
      expect(badges[1].classes()).toContain('bg-accent')
    })

    it('COMP_SDB_040: hides badges when collapsed', () => {
      const wrapper = mountAppSidebar({ items: sampleItems, collapsed: true })

      const badges = wrapper.findAll('.nav-badge')
      expect(badges.length).toBe(0)
    })
  })

  // ==================== Footer Tests ====================

  describe('Footer and Home Link', () => {
    it('COMP_SDB_041: renders home link by default', () => {
      const wrapper = mountAppSidebar()

      const footerItems = wrapper.findAll('.sidebar-footer .nav-item')
      expect(footerItems.length).toBe(1)
    })

    it('COMP_SDB_042: home link has correct label', () => {
      const wrapper = mountAppSidebar()

      const homeLink = wrapper.find('.sidebar-footer .nav-item')
      expect(homeLink.find('.nav-label').text()).toBe('Zur Startseite')
    })

    it('COMP_SDB_043: home link has home icon', () => {
      const wrapper = mountAppSidebar()

      const homeLink = wrapper.find('.sidebar-footer .nav-item')
      expect(homeLink.find('.v-icon').text()).toContain('mdi-home')
    })

    it('COMP_SDB_044: home link navigates to /Home on click', async () => {
      const wrapper = mountAppSidebar()

      await wrapper.find('.sidebar-footer .nav-item').trigger('click')

      expect(mockRouter.push).toHaveBeenCalledWith('/Home')
    })

    it('COMP_SDB_045: hides home link when showHomeLink is false', () => {
      const wrapper = mountAppSidebar({ showHomeLink: false })

      const footerItems = wrapper.findAll('.sidebar-footer .nav-item')
      expect(footerItems.length).toBe(0)
    })

    it('COMP_SDB_046: home link has title when collapsed', () => {
      const wrapper = mountAppSidebar({ collapsed: true })

      const homeLink = wrapper.find('.sidebar-footer .nav-item')
      expect(homeLink.attributes('title')).toBe('Zur Startseite')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_SDB_047: footer slot replaces default home link', () => {
      const wrapper = mountAppSidebar({}, {
        slots: {
          footer: '<button class="custom-footer-btn">Custom Footer</button>'
        }
      })

      expect(wrapper.find('.custom-footer-btn').exists()).toBe(true)
      expect(wrapper.find('.sidebar-footer .nav-item').exists()).toBe(false)
    })
  })

  // ==================== LocalStorage Tests ====================

  describe('LocalStorage Persistence', () => {
    it('COMP_SDB_048: saves collapsed state to localStorage', async () => {
      const wrapper = mountAppSidebar({ storageKey: 'test-sidebar' })

      await wrapper.find('.collapse-btn').trigger('click')

      expect(localStorageMock.setItem).toHaveBeenCalledWith('sidebar_test-sidebar', 'true')
    })

    it('COMP_SDB_049: reads collapsed state from localStorage', () => {
      localStorageMock.getItem.mockReturnValue('true')

      const wrapper = mountAppSidebar({ storageKey: 'test-sidebar' })

      expect(localStorageMock.getItem).toHaveBeenCalledWith('sidebar_test-sidebar')
      expect(wrapper.classes()).toContain('collapsed')
    })

    it('COMP_SDB_050: does not use localStorage when storageKey is null', async () => {
      const wrapper = mountAppSidebar({ storageKey: null })

      await wrapper.find('.collapse-btn').trigger('click')

      expect(localStorageMock.setItem).not.toHaveBeenCalled()
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_SDB_051: updates collapsed state when prop changes', async () => {
      const wrapper = mountAppSidebar({ collapsed: false })

      expect(wrapper.classes()).not.toContain('collapsed')

      await wrapper.setProps({ collapsed: true })

      expect(wrapper.classes()).toContain('collapsed')
    })

    it('COMP_SDB_052: updates active item when modelValue changes', async () => {
      const wrapper = mountAppSidebar({ items: sampleItems, modelValue: 'dashboard' })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems[0].classes()).toContain('active')

      await wrapper.setProps({ modelValue: 'users' })

      expect(navItems[0].classes()).not.toContain('active')
      expect(navItems[2].classes()).toContain('active')
    })

    it('COMP_SDB_053: updates items when prop changes', async () => {
      const wrapper = mountAppSidebar({ items: sampleItems.slice(0, 2) })

      expect(wrapper.findAll('.sidebar-nav .nav-item').length).toBe(2)

      await wrapper.setProps({ items: sampleItems })

      expect(wrapper.findAll('.sidebar-nav .nav-item').length).toBe(4)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_SDB_054: handles empty items array', () => {
      const wrapper = mountAppSidebar({ items: [] })

      const navItems = wrapper.findAll('.sidebar-nav .nav-item')
      expect(navItems.length).toBe(0)
    })

    it('COMP_SDB_055: multiple instances are independent', async () => {
      const wrapper1 = mountAppSidebar({ items: sampleItems, modelValue: 'dashboard' })
      const wrapper2 = mountAppSidebar({ items: sampleItems, modelValue: 'settings' })

      expect(wrapper1.findAll('.nav-item.active')[0].text()).toContain('Dashboard')
      expect(wrapper2.findAll('.nav-item.active')[0].text()).toContain('Settings')

      // Toggle collapse on wrapper1 only
      await wrapper1.find('.collapse-btn').trigger('click')

      expect(wrapper1.classes()).toContain('collapsed')
      expect(wrapper2.classes()).not.toContain('collapsed')
    })
  })
})
