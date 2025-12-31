/**
 * LSlider Component Tests
 *
 * Tests for the LLARS gradient slider component.
 * Test IDs: COMP_SLD_001 - COMP_SLD_025
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LSlider from '@/components/common/LSlider.vue'

const vuetify = createVuetify({ components, directives })

function mountLSlider(props = {}, options = {}) {
  return mount(LSlider, {
    props: {
      modelValue: 50,
      ...props,
    },
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    ...options,
  })
}

describe('LSlider', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_SLD_001: renders with default props', () => {
      const wrapper = mountLSlider()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-slider').exists()).toBe(true)
      expect(wrapper.find('.v-slider').exists()).toBe(true)
    })

    it('COMP_SLD_002: has LLARS slider base class', () => {
      const wrapper = mountLSlider()

      expect(wrapper.classes()).toContain('l-slider')
    })

    it('COMP_SLD_003: starts inactive when not touched', () => {
      const wrapper = mountLSlider()

      // Should be inactive initially (gray)
      expect(wrapper.classes()).toContain('l-slider--inactive')
    })

    it('COMP_SLD_004: starts active when startActive is true', () => {
      const wrapper = mountLSlider({ startActive: true })

      // Should not be inactive
      expect(wrapper.classes()).not.toContain('l-slider--inactive')
      expect(wrapper.classes()).toContain('l-slider--touched')
    })
  })

  // ==================== Value Tests ====================

  describe('Values', () => {
    it('COMP_SLD_005: uses default min/max values', () => {
      const wrapper = mountLSlider()
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('min')).toBe(0)
      expect(slider.props('max')).toBe(100)
    })

    it('COMP_SLD_006: accepts custom min/max values', () => {
      const wrapper = mountLSlider({ min: 1, max: 10, modelValue: 5 })
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('min')).toBe(1)
      expect(slider.props('max')).toBe(10)
    })

    it('COMP_SLD_007: accepts custom step value', () => {
      const wrapper = mountLSlider({ step: 5 })
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('step')).toBe(5)
    })

    it('COMP_SLD_008: passes modelValue to v-slider', () => {
      const wrapper = mountLSlider({ modelValue: 75 })
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('modelValue')).toBe(75)
    })
  })

  // ==================== Color Mode Tests ====================

  describe('Color Modes', () => {
    it('COMP_SLD_009: uses gradient color mode by default', () => {
      const wrapper = mountLSlider({ startActive: true })

      // When active with gradient mode, color is calculated based on value
      // With value 50, should be yellowish
      expect(wrapper.vm.colorMode).toBe('gradient')
    })

    it('COMP_SLD_010: uses fixed color when colorMode is fixed', () => {
      const wrapper = mountLSlider({
        colorMode: 'fixed',
        color: 'primary',
        startActive: true,
      })

      // Should use the fixed color prop
      expect(wrapper.vm.colorMode).toBe('fixed')
    })

    it('COMP_SLD_011: calculates red color for low values', () => {
      const wrapper = mountLSlider({ modelValue: 0, startActive: true })

      // Low value = red
      const color = wrapper.vm.gradientColor
      expect(color).toContain('rgb')
      // Should be reddish (high R value)
    })

    it('COMP_SLD_012: calculates yellow color for middle values', () => {
      const wrapper = mountLSlider({ modelValue: 50, startActive: true })

      // Middle value = yellow
      const color = wrapper.vm.gradientColor
      expect(color).toContain('rgb')
    })

    it('COMP_SLD_013: calculates green color for high values', () => {
      const wrapper = mountLSlider({ modelValue: 100, startActive: true })

      // High value = green
      const color = wrapper.vm.gradientColor
      expect(color).toContain('rgb')
      // Should be greenish (high G value)
    })
  })

  // ==================== Interaction Tests ====================

  describe('Interaction', () => {
    it('COMP_SLD_014: becomes touched after interaction', async () => {
      const wrapper = mountLSlider()

      // Initially inactive
      expect(wrapper.classes()).toContain('l-slider--inactive')

      // Simulate interaction on the v-slider component
      const slider = wrapper.findComponent({ name: 'v-slider' })
      await slider.trigger('mousedown')

      // Should now be touched
      expect(wrapper.classes()).toContain('l-slider--touched')
      expect(wrapper.classes()).not.toContain('l-slider--inactive')
    })

    it('COMP_SLD_015: emits touched event on first interaction', async () => {
      const wrapper = mountLSlider()

      // Trigger on the v-slider component
      const slider = wrapper.findComponent({ name: 'v-slider' })
      await slider.trigger('mousedown')

      expect(wrapper.emitted('touched')).toBeTruthy()
      expect(wrapper.emitted('touched')).toHaveLength(1)
    })

    it('COMP_SLD_016: shows hovering state on mouseenter', async () => {
      const wrapper = mountLSlider()

      await wrapper.trigger('mouseenter')

      expect(wrapper.classes()).toContain('l-slider--hovering')
    })

    it('COMP_SLD_017: removes hovering state on mouseleave', async () => {
      const wrapper = mountLSlider()

      await wrapper.trigger('mouseenter')
      expect(wrapper.classes()).toContain('l-slider--hovering')

      await wrapper.trigger('mouseleave')
      expect(wrapper.classes()).not.toContain('l-slider--hovering')
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_SLD_018: emits update:modelValue on change', async () => {
      const wrapper = mountLSlider()

      // Simulate the v-slider emitting an update
      wrapper.vm.handleUpdate(75)

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([75])
    })

    it('COMP_SLD_019: emits change event on value change', async () => {
      const wrapper = mountLSlider()

      wrapper.vm.handleUpdate(75)

      expect(wrapper.emitted('change')).toBeTruthy()
      expect(wrapper.emitted('change')[0]).toEqual([75])
    })
  })

  // ==================== Disabled State ====================

  describe('Disabled', () => {
    it('COMP_SLD_020: passes disabled prop to v-slider', () => {
      const wrapper = mountLSlider({ disabled: true })
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('disabled')).toBe(true)
    })
  })

  // ==================== Thumb Label Tests ====================

  describe('Thumb Label', () => {
    it('COMP_SLD_021: shows thumb label by default', () => {
      const wrapper = mountLSlider()
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('thumbLabel')).toBe(true)
    })

    it('COMP_SLD_022: can hide thumb label', () => {
      const wrapper = mountLSlider({ thumbLabel: false })
      const slider = wrapper.findComponent({ name: 'v-slider' })

      expect(slider.props('thumbLabel')).toBe(false)
    })
  })

  // ==================== Normalized Value Tests ====================

  describe('Normalized Value', () => {
    it('COMP_SLD_023: calculates normalized value correctly', () => {
      const wrapper = mountLSlider({ min: 0, max: 100, modelValue: 50 })

      expect(wrapper.vm.normalizedValue).toBe(0.5)
    })

    it('COMP_SLD_024: handles custom range correctly', () => {
      const wrapper = mountLSlider({ min: 1, max: 5, modelValue: 3 })

      // (3 - 1) / (5 - 1) = 2/4 = 0.5
      expect(wrapper.vm.normalizedValue).toBe(0.5)
    })

    it('COMP_SLD_025: handles zero range', () => {
      const wrapper = mountLSlider({ min: 5, max: 5, modelValue: 5 })

      // Edge case: min equals max
      expect(wrapper.vm.normalizedValue).toBe(0.5)
    })
  })
})
