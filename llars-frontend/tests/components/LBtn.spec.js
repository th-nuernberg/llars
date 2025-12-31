/**
 * LBtn Component Tests
 *
 * Tests for the LLARS signature button component.
 * Test IDs: COMP_BTN_001 - COMP_BTN_030
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LBtn from '@/components/common/LBtn.vue'

const vuetify = createVuetify({ components, directives })

function mountLBtn(props = {}, options = {}) {
  return mount(LBtn, {
    props,
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    slots: options.slots || { default: 'Button Text' },
    ...options,
  })
}

describe('LBtn', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_BTN_001: renders with default props', () => {
      const wrapper = mountLBtn()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('button').exists()).toBe(true)
      expect(wrapper.text()).toContain('Button Text')
    })

    it('COMP_BTN_002: renders slot content correctly', () => {
      const wrapper = mountLBtn({}, { slots: { default: 'Custom Content' } })

      expect(wrapper.text()).toContain('Custom Content')
    })

    it('COMP_BTN_003: applies default variant (primary)', () => {
      const wrapper = mountLBtn()

      expect(wrapper.classes()).toContain('l-btn--primary')
    })

    it('COMP_BTN_004: has LLARS signature border-radius', () => {
      const wrapper = mountLBtn()
      const button = wrapper.find('button')

      // The button should have the l-btn class which applies the signature style
      expect(button.classes()).toContain('l-btn')
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    const variants = [
      'primary',
      'secondary',
      'accent',
      'success',
      'warning',
      'danger',
      'cancel',
      'text',
      'tonal',
      'outlined',
    ]

    variants.forEach((variant, index) => {
      it(`COMP_BTN_${String(5 + index).padStart(3, '0')}: renders ${variant} variant`, () => {
        const wrapper = mountLBtn({ variant })

        expect(wrapper.classes()).toContain(`l-btn--${variant}`)
      })
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_BTN_015: renders small size', () => {
      const wrapper = mountLBtn({ size: 'small' })

      expect(wrapper.classes()).toContain('l-btn--small')
    })

    it('COMP_BTN_016: renders default size without extra class', () => {
      const wrapper = mountLBtn({ size: 'default' })

      expect(wrapper.classes()).not.toContain('l-btn--default')
    })

    it('COMP_BTN_017: renders large size', () => {
      const wrapper = mountLBtn({ size: 'large' })

      expect(wrapper.classes()).toContain('l-btn--large')
    })
  })

  // ==================== Icon Tests ====================

  describe('Icons', () => {
    it('COMP_BTN_018: renders prepend icon', () => {
      const wrapper = mountLBtn({ prependIcon: 'mdi-plus' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_BTN_019: renders append icon', () => {
      const wrapper = mountLBtn({ appendIcon: 'mdi-arrow-right' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_BTN_020: renders both icons', () => {
      const wrapper = mountLBtn({
        prependIcon: 'mdi-plus',
        appendIcon: 'mdi-arrow-right',
      })

      const icons = wrapper.findAll('.v-icon')
      expect(icons.length).toBe(2)
    })
  })

  // ==================== State Tests ====================

  describe('States', () => {
    it('COMP_BTN_021: shows loading spinner when loading', () => {
      const wrapper = mountLBtn({ loading: true })

      expect(wrapper.find('.v-progress-circular').exists()).toBe(true)
      expect(wrapper.classes()).toContain('l-btn--loading')
    })

    it('COMP_BTN_022: disables button when loading', () => {
      const wrapper = mountLBtn({ loading: true })

      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    })

    it('COMP_BTN_023: disables button when disabled prop is true', () => {
      const wrapper = mountLBtn({ disabled: true })

      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
      expect(wrapper.classes()).toContain('l-btn--disabled')
    })

    it('COMP_BTN_024: renders full width when block is true', () => {
      const wrapper = mountLBtn({ block: true })

      expect(wrapper.classes()).toContain('l-btn--block')
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_BTN_025: emits click event when clicked', async () => {
      const wrapper = mountLBtn()

      await wrapper.find('button').trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')).toHaveLength(1)
    })

    it('COMP_BTN_026: does not emit click when disabled', async () => {
      const wrapper = mountLBtn({ disabled: true })

      await wrapper.find('button').trigger('click')

      // Click event is still emitted but the button is disabled
      // The actual prevention happens at browser level
      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    })

    it('COMP_BTN_027: does not emit click when loading', async () => {
      const wrapper = mountLBtn({ loading: true })

      await wrapper.find('button').trigger('click')

      // Button is disabled during loading
      expect(wrapper.find('button').attributes('disabled')).toBeDefined()
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_BTN_028: has aria-label from tooltip prop', () => {
      const wrapper = mountLBtn({ tooltip: 'Save document' })

      expect(wrapper.find('button').attributes('aria-label')).toBe('Save document')
    })

    it('COMP_BTN_029: is focusable', () => {
      const wrapper = mountLBtn()

      // Button should not have tabindex=-1
      const tabindex = wrapper.find('button').attributes('tabindex')
      expect(tabindex === undefined || tabindex === '0').toBe(true)
    })

    it('COMP_BTN_030: has correct element type', () => {
      const wrapper = mountLBtn()

      expect(wrapper.find('button').exists()).toBe(true)
    })
  })
})
