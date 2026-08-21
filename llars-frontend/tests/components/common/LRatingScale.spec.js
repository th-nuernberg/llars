/**
 * LRatingScale Component Tests
 *
 * Tests for the LLARS Likert scale rating component.
 * Test IDs: COMP_RS_001 - COMP_RS_025
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LRatingScale from '@/components/common/LRatingScale.vue'

function mountLRatingScale(props = {}, options = {}) {
  return mount(LRatingScale, {
    props,
    ...options
  })
}

describe('LRatingScale', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_RS_001: renders with default props', () => {
      const wrapper = mountLRatingScale()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-rating-scale').exists()).toBe(true)
    })

    it('COMP_RS_002: renders correct number of scale buttons (default 1-5)', () => {
      const wrapper = mountLRatingScale()

      const buttons = wrapper.findAll('.scale-button')
      expect(buttons).toHaveLength(5)
    })

    it('COMP_RS_003: displays values on buttons', () => {
      const wrapper = mountLRatingScale({ min: 1, max: 5 })

      const values = wrapper.findAll('.scale-value')
      expect(values[0].text()).toBe('1')
      expect(values[4].text()).toBe('5')
    })

    it('COMP_RS_004: has radiogroup role for accessibility', () => {
      const wrapper = mountLRatingScale()

      expect(wrapper.find('[role="radiogroup"]').exists()).toBe(true)
    })
  })

  // ==================== Min/Max/Step Tests ====================

  describe('Min, Max, and Step', () => {
    it('COMP_RS_005: renders custom min and max range', () => {
      const wrapper = mountLRatingScale({ min: 0, max: 10 })

      const buttons = wrapper.findAll('.scale-button')
      expect(buttons).toHaveLength(11)
    })

    it('COMP_RS_006: respects custom step', () => {
      const wrapper = mountLRatingScale({ min: 0, max: 10, step: 2 })

      const buttons = wrapper.findAll('.scale-button')
      // 0, 2, 4, 6, 8, 10 = 6 buttons
      expect(buttons).toHaveLength(6)
    })

    it('COMP_RS_007: renders 7-point scale', () => {
      const wrapper = mountLRatingScale({ min: 1, max: 7 })

      const buttons = wrapper.findAll('.scale-button')
      expect(buttons).toHaveLength(7)
    })
  })

  // ==================== v-model Tests ====================

  describe('v-model', () => {
    it('COMP_RS_008: no button is selected when modelValue is null', () => {
      const wrapper = mountLRatingScale({ modelValue: null })

      expect(wrapper.find('.is-selected').exists()).toBe(false)
    })

    it('COMP_RS_009: marks correct button as selected', () => {
      const wrapper = mountLRatingScale({ modelValue: 3 })

      const buttons = wrapper.findAll('.scale-button')
      expect(buttons[2].classes()).toContain('is-selected')
    })

    it('COMP_RS_010: emits update:modelValue when button is clicked', async () => {
      const wrapper = mountLRatingScale()

      const buttons = wrapper.findAll('.scale-button')
      await buttons[2].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([3])
    })

    it('COMP_RS_011: sets aria-checked on selected button', () => {
      const wrapper = mountLRatingScale({ modelValue: 2 })

      const buttons = wrapper.findAll('.scale-button')
      expect(buttons[1].attributes('aria-checked')).toBe('true')
      expect(buttons[0].attributes('aria-checked')).toBe('false')
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    it('COMP_RS_012: applies gradient variant by default', () => {
      const wrapper = mountLRatingScale()

      expect(wrapper.classes()).toContain('l-rating-scale--gradient')
    })

    it('COMP_RS_013: applies primary variant', () => {
      const wrapper = mountLRatingScale({ variant: 'primary' })

      expect(wrapper.classes()).toContain('l-rating-scale--primary')
    })

    it('COMP_RS_014: applies neutral variant', () => {
      const wrapper = mountLRatingScale({ variant: 'neutral' })

      expect(wrapper.classes()).toContain('l-rating-scale--neutral')
    })
  })

  // ==================== Label Tests ====================

  describe('Labels', () => {
    it('COMP_RS_015: shows min/max labels when showLabels is true', () => {
      const wrapper = mountLRatingScale({
        showLabels: true,
        labels: { min: 'Poor', max: 'Excellent' }
      })

      expect(wrapper.find('.scale-header').exists()).toBe(true)
      expect(wrapper.find('.scale-label--min').text()).toBe('Poor')
      expect(wrapper.find('.scale-label--max').text()).toBe('Excellent')
    })

    it('COMP_RS_016: hides header when showLabels is false', () => {
      const wrapper = mountLRatingScale({
        showLabels: false,
        labels: { min: 'Low', max: 'High' }
      })

      expect(wrapper.find('.scale-header').exists()).toBe(false)
    })

    it('COMP_RS_017: hides header when no min/max labels provided', () => {
      const wrapper = mountLRatingScale({ showLabels: true })

      expect(wrapper.find('.scale-header').exists()).toBe(false)
    })

    it('COMP_RS_018: shows per-value labels when showValueLabels is true', () => {
      const wrapper = mountLRatingScale({
        showValueLabels: true,
        labels: { 1: 'Bad', 3: 'OK', 5: 'Great' }
      })

      expect(wrapper.find('.scale-labels-row').exists()).toBe(true)
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_RS_019: renders small size', () => {
      const wrapper = mountLRatingScale({ size: 'small' })

      expect(wrapper.classes()).toContain('l-rating-scale--small')
    })

    it('COMP_RS_020: does not apply size class for default', () => {
      const wrapper = mountLRatingScale({ size: 'default' })

      expect(wrapper.classes()).not.toContain('l-rating-scale--default')
    })

    it('COMP_RS_021: renders large size', () => {
      const wrapper = mountLRatingScale({ size: 'large' })

      expect(wrapper.classes()).toContain('l-rating-scale--large')
    })
  })

  // ==================== Disabled Tests ====================

  describe('Disabled', () => {
    it('COMP_RS_022: applies disabled class when disabled', () => {
      const wrapper = mountLRatingScale({ disabled: true })

      expect(wrapper.classes()).toContain('l-rating-scale--disabled')
    })

    it('COMP_RS_023: sets disabled attribute on all buttons', () => {
      const wrapper = mountLRatingScale({ disabled: true })

      const buttons = wrapper.findAll('.scale-button')
      buttons.forEach(button => {
        expect(button.attributes('disabled')).toBeDefined()
      })
    })

    it('COMP_RS_024: does not emit when clicked while disabled', async () => {
      const wrapper = mountLRatingScale({ disabled: true })

      const buttons = wrapper.findAll('.scale-button')
      await buttons[0].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeFalsy()
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_RS_025: buttons have role="radio" and aria-label', () => {
      const wrapper = mountLRatingScale()

      const buttons = wrapper.findAll('.scale-button')
      buttons.forEach(button => {
        expect(button.attributes('role')).toBe('radio')
        expect(button.attributes('aria-label')).toBeTruthy()
      })
    })
  })
})
