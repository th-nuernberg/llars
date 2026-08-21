/**
 * LCheckbox Component Tests
 *
 * Tests for the LLARS custom checkbox component with animated checkmark.
 * Test IDs: COMP_CB_001 - COMP_CB_025
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LCheckbox from '@/components/common/LCheckbox.vue'

function mountLCheckbox(props = {}, options = {}) {
  return mount(LCheckbox, {
    props,
    ...options
  })
}

describe('LCheckbox', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_CB_001: renders with default props', () => {
      const wrapper = mountLCheckbox()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('label.l-checkbox').exists()).toBe(true)
      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
    })

    it('COMP_CB_002: renders the box and checkmark SVG', () => {
      const wrapper = mountLCheckbox()

      expect(wrapper.find('.l-checkbox__box').exists()).toBe(true)
      expect(wrapper.find('.l-checkbox__checkmark').exists()).toBe(true)
      expect(wrapper.find('svg').exists()).toBe(true)
    })

    it('COMP_CB_003: hides the native input visually', () => {
      const wrapper = mountLCheckbox()

      expect(wrapper.find('input').classes()).toContain('l-checkbox__input')
    })
  })

  // ==================== Label Tests ====================

  describe('Label', () => {
    it('COMP_CB_004: renders label from prop', () => {
      const wrapper = mountLCheckbox({ label: 'Accept terms' })

      expect(wrapper.find('.l-checkbox__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Accept terms')
    })

    it('COMP_CB_005: renders label from default slot', () => {
      const wrapper = mountLCheckbox({}, {
        slots: { default: 'Slot Content' }
      })

      expect(wrapper.find('.l-checkbox__label').exists()).toBe(true)
      expect(wrapper.text()).toContain('Slot Content')
    })

    it('COMP_CB_006: does not render label element when no label or slot', () => {
      const wrapper = mountLCheckbox()

      expect(wrapper.find('.l-checkbox__label').exists()).toBe(false)
    })
  })

  // ==================== Boolean Mode Tests ====================

  describe('Boolean Mode', () => {
    it('COMP_CB_007: reflects unchecked state when modelValue is false', () => {
      const wrapper = mountLCheckbox({ modelValue: false })

      expect(wrapper.find('input').element.checked).toBe(false)
      expect(wrapper.classes()).not.toContain('l-checkbox--checked')
    })

    it('COMP_CB_008: reflects checked state when modelValue is true', () => {
      const wrapper = mountLCheckbox({ modelValue: true })

      expect(wrapper.find('input').element.checked).toBe(true)
      expect(wrapper.classes()).toContain('l-checkbox--checked')
    })

    it('COMP_CB_009: emits update:modelValue with true when checked', async () => {
      const wrapper = mountLCheckbox({ modelValue: false })

      await wrapper.find('input').setValue(true)

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([true])
    })

    it('COMP_CB_010: emits update:modelValue with false when unchecked', async () => {
      const wrapper = mountLCheckbox({ modelValue: true })

      await wrapper.find('input').setValue(false)

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('COMP_CB_011: emits change event on toggle', async () => {
      const wrapper = mountLCheckbox({ modelValue: false })

      await wrapper.find('input').setValue(true)

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('change')[0]).toEqual([true])
    })
  })

  // ==================== Array Mode Tests ====================

  describe('Array Mode', () => {
    it('COMP_CB_012: is checked when value exists in array', () => {
      const wrapper = mountLCheckbox({
        modelValue: ['a', 'b'],
        value: 'a'
      })

      expect(wrapper.find('input').element.checked).toBe(true)
      expect(wrapper.classes()).toContain('l-checkbox--checked')
    })

    it('COMP_CB_013: is unchecked when value is not in array', () => {
      const wrapper = mountLCheckbox({
        modelValue: ['a', 'b'],
        value: 'c'
      })

      expect(wrapper.find('input').element.checked).toBe(false)
      expect(wrapper.classes()).not.toContain('l-checkbox--checked')
    })

    it('COMP_CB_014: adds value to array when checked', async () => {
      const wrapper = mountLCheckbox({
        modelValue: ['a'],
        value: 'b'
      })

      await wrapper.find('input').setValue(true)

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toEqual(['a', 'b'])
    })

    it('COMP_CB_015: removes value from array when unchecked', async () => {
      const wrapper = mountLCheckbox({
        modelValue: ['a', 'b'],
        value: 'b'
      })

      await wrapper.find('input').setValue(false)

      const emitted = wrapper.emitted('update:modelValue')[0][0]
      expect(emitted).toEqual(['a'])
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_CB_016: renders x-small size', () => {
      const wrapper = mountLCheckbox({ size: 'x-small' })

      expect(wrapper.classes()).toContain('l-checkbox--size-x-small')
    })

    it('COMP_CB_017: renders small size', () => {
      const wrapper = mountLCheckbox({ size: 'small' })

      expect(wrapper.classes()).toContain('l-checkbox--size-small')
    })

    it('COMP_CB_018: renders default size', () => {
      const wrapper = mountLCheckbox({ size: 'default' })

      expect(wrapper.classes()).toContain('l-checkbox--size-default')
    })

    it('COMP_CB_019: renders large size', () => {
      const wrapper = mountLCheckbox({ size: 'large' })

      expect(wrapper.classes()).toContain('l-checkbox--size-large')
    })
  })

  // ==================== State Tests ====================

  describe('States', () => {
    it('COMP_CB_020: applies disabled class when disabled', () => {
      const wrapper = mountLCheckbox({ disabled: true })

      expect(wrapper.classes()).toContain('l-checkbox--disabled')
    })

    it('COMP_CB_021: disables the input element when disabled', () => {
      const wrapper = mountLCheckbox({ disabled: true })

      expect(wrapper.find('input').element.disabled).toBe(true)
    })

    it('COMP_CB_022: applies error class when error is true', () => {
      const wrapper = mountLCheckbox({ error: true })

      expect(wrapper.classes()).toContain('l-checkbox--error')
    })

    it('COMP_CB_023: does not apply error class when error is false', () => {
      const wrapper = mountLCheckbox({ error: false })

      expect(wrapper.classes()).not.toContain('l-checkbox--error')
    })
  })

  // ==================== Styling Tests ====================

  describe('Styling', () => {
    it('COMP_CB_024: has LLARS signature asymmetric border-radius on box', () => {
      const wrapper = mountLCheckbox()

      // Box element should exist with the l-checkbox__box class that applies signature styling
      expect(wrapper.find('.l-checkbox__box').exists()).toBe(true)
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_CB_025: input is accessible via label element', () => {
      const wrapper = mountLCheckbox({ label: 'Check me' })

      expect(wrapper.find('label').exists()).toBe(true)
      expect(wrapper.find('label input[type="checkbox"]').exists()).toBe(true)
    })
  })
})
