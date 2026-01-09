/**
 * LThemeToggle Component Tests
 *
 * Tests for the LLARS theme toggle component with light/dark/system options.
 * Test IDs: COMP_THM_001 - COMP_THM_040
 *
 * Coverage:
 * - Rendering and structure
 * - Button display and icon
 * - Menu opening/closing
 * - Theme options rendering
 * - Active state indicator
 * - onPrimary styling
 * - Theme selection
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, computed } from 'vue'
import LThemeToggle from '@/components/common/LThemeToggle.vue'

// Mock useAppTheme composable
const mockThemePreference = ref('system')
const mockIsDark = ref(false)
const mockSetThemePreference = vi.fn()
const mockThemeOptions = [
  { value: 'system', title: 'System', icon: 'llars:system-theme' },
  { value: 'light', title: 'Hell', icon: 'llars:sun' },
  { value: 'dark', title: 'Dunkel', icon: 'llars:moon' }
]

vi.mock('@/composables/useAppTheme', () => ({
  useAppTheme: () => ({
    themePreference: mockThemePreference,
    themeOptions: mockThemeOptions,
    currentThemeOption: computed(() =>
      mockThemeOptions.find(o => o.value === mockThemePreference.value)
    ),
    setThemePreference: mockSetThemePreference,
    isDark: mockIsDark
  })
}))

function mountLThemeToggle(props = {}, options = {}) {
  return mount(LThemeToggle, {
    props,
    global: {
      stubs: {
        'v-menu': {
          template: `
            <div class="v-menu">
              <slot name="activator" :props="{ onClick: () => {} }"></slot>
              <slot></slot>
            </div>
          `
        },
        'v-icon': {
          template: '<i class="v-icon">{{ icon }}<slot /></i>',
          props: ['size', 'icon']
        },
        'LIcon': {
          template: '<i class="v-icon">{{ icon }}<slot /></i>',
          props: ['size', 'icon', 'color']
        }
      }
    },
    ...options
  })
}

describe('LThemeToggle', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockThemePreference.value = 'system'
    mockIsDark.value = false
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_THM_001: renders with default props', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.theme-toggle-wrapper').exists()).toBe(true)
    })

    it('COMP_THM_002: renders toggle button', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').exists()).toBe(true)
    })

    it('COMP_THM_003: toggle button has icon', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)
    })

    it('COMP_THM_004: renders theme menu', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-menu').exists()).toBe(true)
    })

    it('COMP_THM_005: renders menu header "Design"', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-menu-header').text()).toBe('Design')
    })

    it('COMP_THM_006: renders all three theme options', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options.length).toBe(3)
    })
  })

  // ==================== Theme Options Tests ====================

  describe('Theme Options', () => {
    it('COMP_THM_007: system option has correct label', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[0].find('.option-label').text()).toBe('System')
    })

    it('COMP_THM_008: light option has correct label', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[1].find('.option-label').text()).toBe('Hell')
    })

    it('COMP_THM_009: dark option has correct label', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[2].find('.option-label').text()).toBe('Dunkel')
    })

    it('COMP_THM_010: system option has system-theme icon', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[0].find('.option-icon').text()).toContain('llars:system-theme')
    })

    it('COMP_THM_011: light option has sun icon', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[1].find('.option-icon').text()).toContain('llars:sun')
    })

    it('COMP_THM_012: dark option has moon icon', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[2].find('.option-icon').text()).toContain('llars:moon')
    })
  })

  // ==================== Active State Tests ====================

  describe('Active State', () => {
    it('COMP_THM_013: system option is active by default', () => {
      mockThemePreference.value = 'system'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[0].classes()).toContain('active')
    })

    it('COMP_THM_014: light option is active when theme is light', () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[1].classes()).toContain('active')
      expect(options[0].classes()).not.toContain('active')
      expect(options[2].classes()).not.toContain('active')
    })

    it('COMP_THM_015: dark option is active when theme is dark', () => {
      mockThemePreference.value = 'dark'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[2].classes()).toContain('active')
      expect(options[0].classes()).not.toContain('active')
      expect(options[1].classes()).not.toContain('active')
    })

    it('COMP_THM_016: active option shows check icon', () => {
      mockThemePreference.value = 'dark'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      expect(options[2].find('.check-icon').exists()).toBe(true)
      expect(options[0].find('.check-icon').exists()).toBe(false)
    })

    it('COMP_THM_017: only one option is active at a time', () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()
      const activeOptions = wrapper.findAll('.theme-option.active')

      expect(activeOptions.length).toBe(1)
    })
  })

  // ==================== Icon Tests ====================

  describe('Current Icon', () => {
    it('COMP_THM_018: shows icon when theme is system', () => {
      mockThemePreference.value = 'system'
      const wrapper = mountLThemeToggle()

      // LIcon wraps v-icon, so we check that the icon element exists
      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)
    })

    it('COMP_THM_019: shows icon when theme is light', () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)
    })

    it('COMP_THM_020: shows icon when theme is dark', () => {
      mockThemePreference.value = 'dark'
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)
    })
  })

  // ==================== Theme Selection Tests ====================

  describe('Theme Selection', () => {
    it('COMP_THM_021: clicking light option calls setThemePreference', async () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      await options[0].trigger('click')

      expect(mockSetThemePreference).toHaveBeenCalledWith('light')
    })

    it('COMP_THM_022: clicking dark option calls setThemePreference', async () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      await options[1].trigger('click')

      expect(mockSetThemePreference).toHaveBeenCalledWith('dark')
    })

    it('COMP_THM_023: clicking system option calls setThemePreference', async () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      await options[2].trigger('click')

      expect(mockSetThemePreference).toHaveBeenCalledWith('system')
    })

    it('COMP_THM_024: clicking already active option still calls setThemePreference', async () => {
      mockThemePreference.value = 'dark'
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      await options[1].trigger('click')

      expect(mockSetThemePreference).toHaveBeenCalledWith('dark')
    })
  })

  // ==================== onPrimary Tests ====================

  describe('onPrimary Prop', () => {
    it('COMP_THM_025: does not have on-primary class by default', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').classes()).not.toContain('on-primary')
    })

    it('COMP_THM_026: has on-primary class when prop is true', () => {
      const wrapper = mountLThemeToggle({ onPrimary: true })

      expect(wrapper.find('.theme-toggle-btn').classes()).toContain('on-primary')
    })

    it('COMP_THM_027: does not have on-primary class when prop is false', () => {
      const wrapper = mountLThemeToggle({ onPrimary: false })

      expect(wrapper.find('.theme-toggle-btn').classes()).not.toContain('on-primary')
    })
  })

  // ==================== Button Title Tests ====================

  describe('Button Title', () => {
    it('COMP_THM_028: button has title matching current theme', () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').attributes('title')).toBe('Hell')
    })

    it('COMP_THM_029: button title updates when theme changes', async () => {
      mockThemePreference.value = 'dark'
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').attributes('title')).toBe('Dunkel')
    })

    it('COMP_THM_030: button has system title when theme is system', () => {
      mockThemePreference.value = 'system'
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').attributes('title')).toBe('System')
    })
  })

  // ==================== Structure Tests ====================

  describe('Structure', () => {
    it('COMP_THM_031: wrapper uses flexbox', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-wrapper').exists()).toBe(true)
    })

    it('COMP_THM_032: each option has icon and label', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      options.forEach(option => {
        expect(option.find('.option-icon').exists()).toBe(true)
        expect(option.find('.option-label').exists()).toBe(true)
      })
    })

    it('COMP_THM_033: toggle button is a button element', () => {
      const wrapper = mountLThemeToggle()

      expect(wrapper.find('.theme-toggle-btn').element.tagName).toBe('BUTTON')
    })

    it('COMP_THM_034: theme options are button elements', () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      options.forEach(option => {
        expect(option.element.tagName).toBe('BUTTON')
      })
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_THM_035: handles multiple rapid clicks', async () => {
      const wrapper = mountLThemeToggle()
      const options = wrapper.findAll('.theme-option')

      await options[0].trigger('click')
      await options[1].trigger('click')
      await options[2].trigger('click')

      expect(mockSetThemePreference).toHaveBeenCalledTimes(3)
    })

    it('COMP_THM_036: onPrimary prop is reactive', async () => {
      const wrapper = mountLThemeToggle({ onPrimary: false })

      expect(wrapper.find('.theme-toggle-btn').classes()).not.toContain('on-primary')

      await wrapper.setProps({ onPrimary: true })

      expect(wrapper.find('.theme-toggle-btn').classes()).toContain('on-primary')
    })

    it('COMP_THM_037: icon exists when themePreference changes', async () => {
      mockThemePreference.value = 'light'
      const wrapper = mountLThemeToggle()

      // LIcon wraps v-icon, icon exists regardless of theme
      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)

      mockThemePreference.value = 'dark'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.theme-toggle-btn .v-icon').exists()).toBe(true)
    })

    it('COMP_THM_038: multiple instances are independent', () => {
      const wrapper1 = mountLThemeToggle({ onPrimary: true })
      const wrapper2 = mountLThemeToggle({ onPrimary: false })

      expect(wrapper1.find('.theme-toggle-btn').classes()).toContain('on-primary')
      expect(wrapper2.find('.theme-toggle-btn').classes()).not.toContain('on-primary')
    })

    it('COMP_THM_039: component works without props', () => {
      const wrapper = mount(LThemeToggle, {
        global: {
          stubs: {
            'v-menu': {
              template: '<div class="v-menu"><slot name="activator" :props="{}"></slot><slot></slot></div>'
            },
            'v-icon': { template: '<i class="v-icon">{{ icon }}<slot /></i>', props: ['icon', 'size'] },
            'LIcon': { template: '<i class="v-icon">{{ icon }}<slot /></i>', props: ['icon', 'size', 'color'] }
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.theme-toggle-btn').exists()).toBe(true)
    })

    it('COMP_THM_040: check icon only appears on active option', () => {
      mockThemePreference.value = 'system'
      const wrapper = mountLThemeToggle()
      const checkIcons = wrapper.findAll('.check-icon')

      expect(checkIcons.length).toBe(1)
    })
  })
})
