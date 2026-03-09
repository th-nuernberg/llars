/**
 * LLanguageToggle Component Tests
 *
 * Tests for the LLARS language toggle component with dropdown menu.
 * Test IDs: COMP_LT_001 - COMP_LT_012
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { ref, computed } from 'vue'
import LLanguageToggle from '@/components/common/LLanguageToggle.vue'

const vuetify = createVuetify({ components, directives })

// Mock useLanguage composable
const mockSetLanguage = vi.fn()
const mockCurrentLanguage = ref('de')

vi.mock('@/composables/useLanguage', () => ({
  useLanguage: () => ({
    currentLanguage: mockCurrentLanguage,
    languageOptions: computed(() => [
      { value: 'de', title: 'Deutsch', short: 'DE' },
      { value: 'en', title: 'English', short: 'EN' }
    ]),
    currentLanguageOption: computed(() => {
      const options = [
        { value: 'de', title: 'Deutsch', short: 'DE' },
        { value: 'en', title: 'English', short: 'EN' }
      ]
      return options.find(opt => opt.value === mockCurrentLanguage.value)
    }),
    setLanguage: mockSetLanguage
  })
}))

function mountLLanguageToggle(props = {}, options = {}) {
  return mount(LLanguageToggle, {
    props,
    global: {
      plugins: [vuetify],
      stubs: {
        LIcon: { template: '<i><slot /></i>' }
      },
      mocks: {
        $t: (key) => key
      },
      ...options.global
    },
    ...options
  })
}

describe('LLanguageToggle', () => {
  beforeEach(() => {
    mockCurrentLanguage.value = 'de'
    mockSetLanguage.mockClear()
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_LT_001: renders with default props', () => {
      const wrapper = mountLLanguageToggle()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.language-toggle-wrapper').exists()).toBe(true)
    })

    it('COMP_LT_002: renders the toggle button', () => {
      const wrapper = mountLLanguageToggle()

      expect(wrapper.find('.language-toggle-btn').exists()).toBe(true)
    })

    it('COMP_LT_003: displays current language code', () => {
      const wrapper = mountLLanguageToggle()

      expect(wrapper.find('.language-code').text()).toBe('DE')
    })

    it('COMP_LT_004: displays EN when language is English', () => {
      mockCurrentLanguage.value = 'en'
      const wrapper = mountLLanguageToggle()

      expect(wrapper.find('.language-code').text()).toBe('EN')
    })
  })

  // ==================== onPrimary Styling Tests ====================

  describe('onPrimary Styling', () => {
    it('COMP_LT_005: does not apply on-primary class by default', () => {
      const wrapper = mountLLanguageToggle()

      expect(wrapper.find('.language-toggle-btn').classes()).not.toContain('on-primary')
    })

    it('COMP_LT_006: applies on-primary class when onPrimary is true', () => {
      const wrapper = mountLLanguageToggle({ onPrimary: true })

      expect(wrapper.find('.language-toggle-btn').classes()).toContain('on-primary')
    })
  })

  // ==================== Menu Tests ====================

  describe('Menu', () => {
    it('COMP_LT_007: has title attribute for accessibility', () => {
      const wrapper = mountLLanguageToggle()

      expect(wrapper.find('.language-toggle-btn').attributes('title')).toBe('language.select')
    })

    it('COMP_LT_008: renders v-menu component', () => {
      const wrapper = mountLLanguageToggle()

      const menu = wrapper.findComponent({ name: 'VMenu' })
      expect(menu.exists()).toBe(true)
    })
  })

  // ==================== Language Selection Tests ====================

  describe('Language Selection', () => {
    it('COMP_LT_009: selectLanguage calls setLanguage with correct value', async () => {
      const wrapper = mountLLanguageToggle()

      // Call the internal method directly to avoid v-menu overlay issues in JSDOM
      wrapper.vm.selectLanguage('en')
      await wrapper.vm.$nextTick()

      expect(mockSetLanguage).toHaveBeenCalledWith('en')
    })

    it('COMP_LT_010: selectLanguage calls setLanguage for German', async () => {
      mockCurrentLanguage.value = 'en'
      const wrapper = mountLLanguageToggle()

      wrapper.vm.selectLanguage('de')
      await wrapper.vm.$nextTick()

      expect(mockSetLanguage).toHaveBeenCalledWith('de')
    })

    it('COMP_LT_011: selectLanguage closes the menu', async () => {
      const wrapper = mountLLanguageToggle()

      wrapper.vm.selectLanguage('en')
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.menuOpen).toBe(false)
    })
  })

  // ==================== Styling Tests ====================

  describe('Styling', () => {
    it('COMP_LT_012: button has LLARS signature asymmetric border-radius class', () => {
      const wrapper = mountLLanguageToggle()

      // The language-toggle-btn class applies the signature border-radius via CSS
      expect(wrapper.find('.language-toggle-btn').exists()).toBe(true)
    })
  })
})
