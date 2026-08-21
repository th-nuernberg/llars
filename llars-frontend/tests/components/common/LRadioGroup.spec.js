/**
 * LRadioGroup Component Tests
 *
 * Tests for the LLARS radio group container component.
 * Test IDs: COMP_RG_001 - COMP_RG_020
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LRadioGroup from '@/components/common/LRadioGroup.vue'
import LRadio from '@/components/common/LRadio.vue'

const defaultOptions = [
  { value: 'a', label: 'Option A' },
  { value: 'b', label: 'Option B' },
  { value: 'c', label: 'Option C' }
]

function mountLRadioGroup(props = {}, options = {}) {
  return mount(LRadioGroup, {
    props: {
      options: defaultOptions,
      ...props
    },
    global: {
      components: { LRadio },
      ...options.global
    },
    ...options
  })
}

describe('LRadioGroup', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_RG_001: renders with required options prop', () => {
      const wrapper = mountLRadioGroup()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-radio-group').exists()).toBe(true)
    })

    it('COMP_RG_002: renders correct number of LRadio components', () => {
      const wrapper = mountLRadioGroup()

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios).toHaveLength(3)
    })

    it('COMP_RG_003: has radiogroup role for accessibility', () => {
      const wrapper = mountLRadioGroup()

      expect(wrapper.find('[role="radiogroup"]').exists()).toBe(true)
    })
  })

  // ==================== Option Normalization Tests ====================

  describe('Option Normalization', () => {
    it('COMP_RG_004: normalizes string options to objects', () => {
      const wrapper = mountLRadioGroup({
        options: ['red', 'green', 'blue']
      })

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios).toHaveLength(3)
      expect(radios[0].props('value')).toBe('red')
      expect(radios[0].props('label')).toBe('red')
    })

    it('COMP_RG_005: normalizes number options to objects', () => {
      const wrapper = mountLRadioGroup({
        options: [1, 2, 3]
      })

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios).toHaveLength(3)
      expect(radios[0].props('value')).toBe(1)
      expect(radios[0].props('label')).toBe('1')
    })

    it('COMP_RG_006: uses title field as fallback for label', () => {
      const wrapper = mountLRadioGroup({
        options: [
          { value: 'x', title: 'Title X' }
        ]
      })

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios[0].props('label')).toBe('Title X')
    })

    it('COMP_RG_007: falls back to stringified value when no label or title', () => {
      const wrapper = mountLRadioGroup({
        options: [{ value: 42 }]
      })

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios[0].props('label')).toBe('42')
    })
  })

  // ==================== v-model Tests ====================

  describe('v-model', () => {
    it('COMP_RG_008: passes modelValue to child LRadio components', () => {
      const wrapper = mountLRadioGroup({ modelValue: 'b' })

      const radios = wrapper.findAllComponents(LRadio)
      radios.forEach(radio => {
        expect(radio.props('modelValue')).toBe('b')
      })
    })

    it('COMP_RG_009: emits update:modelValue when a radio is selected', async () => {
      const wrapper = mountLRadioGroup({ modelValue: null })

      const radios = wrapper.findAllComponents(LRadio)
      await radios[1].vm.$emit('update:model-value', 'b')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['b'])
    })

    it('COMP_RG_010: emits change event when selection changes', async () => {
      const wrapper = mountLRadioGroup({ modelValue: null })

      const radios = wrapper.findAllComponents(LRadio)
      await radios[0].vm.$emit('update:model-value', 'a')

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('change')[0]).toEqual(['a'])
    })
  })

  // ==================== Layout Tests ====================

  describe('Layout', () => {
    it('COMP_RG_011: renders vertical layout by default', () => {
      const wrapper = mountLRadioGroup()

      expect(wrapper.classes()).not.toContain('l-radio-group--row')
    })

    it('COMP_RG_012: renders horizontal layout when row is true', () => {
      const wrapper = mountLRadioGroup({ row: true })

      expect(wrapper.classes()).toContain('l-radio-group--row')
    })
  })

  // ==================== Label / Hint / Error Tests ====================

  describe('Label, Hint, and Error', () => {
    it('COMP_RG_013: renders group label', () => {
      const wrapper = mountLRadioGroup({ label: 'Choose one' })

      expect(wrapper.find('.l-radio-group__label').exists()).toBe(true)
      expect(wrapper.find('.l-radio-group__label').text()).toBe('Choose one')
    })

    it('COMP_RG_014: sets aria-label from label prop', () => {
      const wrapper = mountLRadioGroup({ label: 'Pick color' })

      expect(wrapper.find('[role="radiogroup"]').attributes('aria-label')).toBe('Pick color')
    })

    it('COMP_RG_015: does not render label element when no label', () => {
      const wrapper = mountLRadioGroup()

      expect(wrapper.find('.l-radio-group__label').exists()).toBe(false)
    })

    it('COMP_RG_016: renders hint text', () => {
      const wrapper = mountLRadioGroup({ hint: 'Select your preference' })

      expect(wrapper.find('.l-radio-group__hint').exists()).toBe(true)
      expect(wrapper.find('.l-radio-group__hint').text()).toBe('Select your preference')
    })

    it('COMP_RG_017: renders error message and applies error styling', () => {
      const wrapper = mountLRadioGroup({
        error: true,
        errorMessage: 'Selection required'
      })

      expect(wrapper.classes()).toContain('l-radio-group--error')
      expect(wrapper.find('.l-radio-group__hint--error').exists()).toBe(true)
      expect(wrapper.find('.l-radio-group__hint').text()).toBe('Selection required')
    })
  })

  // ==================== Disabled Tests ====================

  describe('Disabled', () => {
    it('COMP_RG_018: disables all radio buttons when group is disabled', () => {
      const wrapper = mountLRadioGroup({ disabled: true })

      const radios = wrapper.findAllComponents(LRadio)
      radios.forEach(radio => {
        expect(radio.props('disabled')).toBe(true)
      })
    })

    it('COMP_RG_019: supports per-option disable', () => {
      const wrapper = mountLRadioGroup({
        options: [
          { value: 'a', label: 'A' },
          { value: 'b', label: 'B', disabled: true },
          { value: 'c', label: 'C' }
        ]
      })

      const radios = wrapper.findAllComponents(LRadio)
      expect(radios[0].props('disabled')).toBe(false)
      expect(radios[1].props('disabled')).toBe(true)
      expect(radios[2].props('disabled')).toBe(false)
    })
  })

  // ==================== Name Tests ====================

  describe('Group Name', () => {
    it('COMP_RG_020: assigns same name to all radio buttons', () => {
      const wrapper = mountLRadioGroup({ name: 'colors' })

      const radios = wrapper.findAllComponents(LRadio)
      radios.forEach(radio => {
        expect(radio.props('name')).toBe('colors')
      })
    })
  })
})
