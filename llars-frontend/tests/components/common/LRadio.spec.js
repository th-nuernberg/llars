/**
 * LRadio Component Tests
 *
 * Tests for the LLARS custom radio button component with animated dot indicator.
 * Test IDs: COMP_RAD_001 - COMP_RAD_017
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LRadio from '@/components/common/LRadio.vue'

function mountLRadio(props = {}, options = {}) {
  return mount(LRadio, {
    props: { value: 'test', ...props },
    ...options
  })
}

describe('LRadio', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_RAD_001: renders with required props', () => {
      const wrapper = mountLRadio({ value: 'opt1' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('label.l-radio').exists()).toBe(true)
      expect(wrapper.find('input[type="radio"]').exists()).toBe(true)
    })

    it('COMP_RAD_002: renders the box and dot elements', () => {
      const wrapper = mountLRadio()

      expect(wrapper.find('.l-radio__box').exists()).toBe(true)
      expect(wrapper.find('.l-radio__dot').exists()).toBe(true)
    })

    it('COMP_RAD_003: hides the native input visually', () => {
      const wrapper = mountLRadio()

      expect(wrapper.find('input').classes()).toContain('l-radio__input')
    })
  })

  // ==================== Label Tests ====================

  describe('Label', () => {
    it('COMP_RAD_004: renders label from prop', () => {
      const wrapper = mountLRadio({ label: 'Option A' })

      expect(wrapper.find('.l-radio__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Option A')
    })

    it('COMP_RAD_005: renders label from default slot', () => {
      const wrapper = mountLRadio({}, {
        slots: { default: 'Slot Label' }
      })

      expect(wrapper.find('.l-radio__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Slot Label')
    })

    it('COMP_RAD_006: does not render label element when no label or slot', () => {
      const wrapper = mountLRadio()

      expect(wrapper.find('.l-radio__label').exists()).toBe(false)
    })
  })

  // ==================== Selection Tests ====================

  describe('Selection', () => {
    it('COMP_RAD_007: is checked when modelValue matches value', () => {
      const wrapper = mountLRadio({
        modelValue: 'opt1',
        value: 'opt1'
      })

      expect(wrapper.find('input').element.checked).toBe(true)
      expect(wrapper.classes()).toContain('l-radio--checked')
    })

    it('COMP_RAD_008: is not checked when modelValue does not match', () => {
      const wrapper = mountLRadio({
        modelValue: 'opt2',
        value: 'opt1'
      })

      expect(wrapper.find('input').element.checked).toBe(false)
      expect(wrapper.classes()).not.toContain('l-radio--checked')
    })

    it('COMP_RAD_009: emits update:modelValue with its value on change', async () => {
      const wrapper = mountLRadio({
        modelValue: null,
        value: 'opt1'
      })

      await wrapper.find('input').trigger('change')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['opt1'])
    })

    it('COMP_RAD_010: emits change event on selection', async () => {
      const wrapper = mountLRadio({
        modelValue: null,
        value: 'opt1'
      })

      await wrapper.find('input').trigger('change')

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('change')[0]).toEqual(['opt1'])
    })

    it('COMP_RAD_011: works with numeric values', () => {
      const wrapper = mountLRadio({
        modelValue: 2,
        value: 2
      })

      expect(wrapper.classes()).toContain('l-radio--checked')
    })
  })

  // ==================== Name Attribute Tests ====================

  describe('Name attribute', () => {
    it('COMP_RAD_012: sets name attribute on input', () => {
      const wrapper = mountLRadio({ name: 'group1' })

      expect(wrapper.find('input').attributes('name')).toBe('group1')
    })

    it('COMP_RAD_013: sets value attribute on input', () => {
      const wrapper = mountLRadio({ value: 'myval' })

      expect(wrapper.find('input').attributes('value')).toBe('myval')
    })
  })

  // ==================== State Tests ====================

  describe('States', () => {
    it('COMP_RAD_014: applies disabled class when disabled', () => {
      const wrapper = mountLRadio({ disabled: true })

      expect(wrapper.classes()).toContain('l-radio--disabled')
    })

    it('COMP_RAD_015: disables the input element when disabled', () => {
      const wrapper = mountLRadio({ disabled: true })

      expect(wrapper.find('input').element.disabled).toBe(true)
    })

    it('COMP_RAD_016: applies error class when error is true', () => {
      const wrapper = mountLRadio({ error: true })

      expect(wrapper.classes()).toContain('l-radio--error')
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_RAD_017: input is accessible via label element', () => {
      const wrapper = mountLRadio({ label: 'Radio option' })

      expect(wrapper.find('label').exists()).toBe(true)
      expect(wrapper.find('label input[type="radio"]').exists()).toBe(true)
    })
  })
})
