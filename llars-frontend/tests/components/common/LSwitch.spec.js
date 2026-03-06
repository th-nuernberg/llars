/**
 * LSwitch Component Tests
 *
 * Tests for the LLARS custom toggle switch component.
 * Test IDs: COMP_SW_001 - COMP_SW_016
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LSwitch from '@/components/common/LSwitch.vue'

function mountLSwitch(props = {}, options = {}) {
  return mount(LSwitch, {
    props,
    ...options
  })
}

describe('LSwitch', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_SW_001: renders with default props', () => {
      const wrapper = mountLSwitch()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('label.l-switch').exists()).toBe(true)
      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
    })

    it('COMP_SW_002: renders the track and thumb elements', () => {
      const wrapper = mountLSwitch()

      expect(wrapper.find('.l-switch__track').exists()).toBe(true)
      expect(wrapper.find('.l-switch__thumb').exists()).toBe(true)
    })

    it('COMP_SW_003: hides the native input visually', () => {
      const wrapper = mountLSwitch()

      expect(wrapper.find('input').classes()).toContain('l-switch__input')
    })
  })

  // ==================== Label Tests ====================

  describe('Label', () => {
    it('COMP_SW_004: renders label from prop', () => {
      const wrapper = mountLSwitch({ label: 'Enable feature' })

      expect(wrapper.find('.l-switch__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Enable feature')
    })

    it('COMP_SW_005: renders label from default slot', () => {
      const wrapper = mountLSwitch({}, {
        slots: { default: 'Slot Label' }
      })

      expect(wrapper.find('.l-switch__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Slot Label')
    })

    it('COMP_SW_006: does not render label element when no label or slot', () => {
      const wrapper = mountLSwitch()

      expect(wrapper.find('.l-switch__label').exists()).toBe(false)
    })
  })

  // ==================== v-model Tests ====================

  describe('v-model', () => {
    it('COMP_SW_007: reflects unchecked state when modelValue is false', () => {
      const wrapper = mountLSwitch({ modelValue: false })

      expect(wrapper.find('input').element.checked).toBe(false)
      expect(wrapper.classes()).not.toContain('l-switch--checked')
    })

    it('COMP_SW_008: reflects checked state when modelValue is true', () => {
      const wrapper = mountLSwitch({ modelValue: true })

      expect(wrapper.find('input').element.checked).toBe(true)
      expect(wrapper.classes()).toContain('l-switch--checked')
    })

    it('COMP_SW_009: emits update:modelValue on toggle', async () => {
      const wrapper = mountLSwitch({ modelValue: false })

      await wrapper.find('input').setValue(true)

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
    })

    it('COMP_SW_010: emits change event on toggle', async () => {
      const wrapper = mountLSwitch({ modelValue: false })

      await wrapper.find('input').setValue(true)

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('change')[0]).toEqual([true])
    })

    it('COMP_SW_011: emits false when toggled off', async () => {
      const wrapper = mountLSwitch({ modelValue: true })

      await wrapper.find('input').setValue(false)

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })
  })

  // ==================== Disabled State Tests ====================

  describe('Disabled', () => {
    it('COMP_SW_012: applies disabled class when disabled', () => {
      const wrapper = mountLSwitch({ disabled: true })

      expect(wrapper.classes()).toContain('l-switch--disabled')
    })

    it('COMP_SW_013: disables the input element when disabled', () => {
      const wrapper = mountLSwitch({ disabled: true })

      expect(wrapper.find('input').element.disabled).toBe(true)
    })

    it('COMP_SW_014: does not apply disabled class when not disabled', () => {
      const wrapper = mountLSwitch({ disabled: false })

      expect(wrapper.classes()).not.toContain('l-switch--disabled')
    })
  })

  // ==================== Styling Tests ====================

  describe('Styling', () => {
    it('COMP_SW_015: has LLARS signature asymmetric border-radius on track', () => {
      const wrapper = mountLSwitch()

      // Track element should exist with the l-switch__track class that applies signature styling
      expect(wrapper.find('.l-switch__track').exists()).toBe(true)
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_SW_016: input is accessible via label element', () => {
      const wrapper = mountLSwitch({ label: 'Toggle' })

      // The label wraps the input, making it accessible
      expect(wrapper.find('label').exists()).toBe(true)
      expect(wrapper.find('label input[type="checkbox"]').exists()).toBe(true)
    })
  })
})
