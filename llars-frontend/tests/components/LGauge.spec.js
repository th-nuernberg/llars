/**
 * LGauge Component Tests
 *
 * Tests for the LLARS gauge/metric component with progress bar.
 * Test IDs: COMP_GAU_001 - COMP_GAU_055
 *
 * Coverage:
 * - Rendering and structure
 * - Icon props and styling
 * - Label and value display
 * - Value formatting (K, M abbreviations)
 * - Progress bar
 * - Color modes (fixed, threshold, inverse)
 * - Compact mode
 * - Loading state
 * - Slots (value, subtitle)
 * - Edge cases
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LGauge from '@/components/common/LGauge.vue'

function mountLGauge(props = {}, options = {}) {
  return mount(LGauge, {
    props: {
      label: 'Test Metric',
      ...props
    },
    global: {
      stubs: {
        'v-icon': {
          template: '<i class="v-icon" :style="{ fontSize: size + \'px\' }">{{ icon }}</i>',
          props: ['icon', 'size']
        }
      }
    },
    ...options
  })
}

describe('LGauge', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_GAU_001: renders with required label prop', () => {
      const wrapper = mountLGauge({ label: 'CPU Usage' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-gauge').exists()).toBe(true)
    })

    it('COMP_GAU_002: has l-gauge class', () => {
      const wrapper = mountLGauge()

      expect(wrapper.classes()).toContain('l-gauge')
    })

    it('COMP_GAU_003: renders header section', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.l-gauge__header').exists()).toBe(true)
    })

    it('COMP_GAU_004: renders icon wrapper', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.l-gauge__icon-wrapper').exists()).toBe(true)
    })

    it('COMP_GAU_005: renders icon', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_GAU_006: renders info section', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.l-gauge__info').exists()).toBe(true)
    })

    it('COMP_GAU_007: renders label', () => {
      const wrapper = mountLGauge({ label: 'Memory' })

      expect(wrapper.find('.l-gauge__label').text()).toBe('Memory')
    })

    it('COMP_GAU_008: renders value', () => {
      const wrapper = mountLGauge({ value: 42 })

      expect(wrapper.find('.l-gauge__value').exists()).toBe(true)
    })
  })

  // ==================== Icon Tests ====================

  describe('Icon', () => {
    it('COMP_GAU_009: uses default icon mdi-chart-box', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_GAU_010: uses custom icon when provided', () => {
      const wrapper = mountLGauge({ icon: 'mdi-cpu-64-bit' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_GAU_011: uses default icon size of 20', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.v-icon').attributes('style')).toContain('20px')
    })

    it('COMP_GAU_012: accepts custom icon size', () => {
      const wrapper = mountLGauge({ iconSize: 24 })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('24px')
    })

    it('COMP_GAU_013: icon wrapper has background color', () => {
      const wrapper = mountLGauge({ color: 'primary', colorMode: 'fixed' })
      const style = wrapper.find('.l-gauge__icon-wrapper').attributes('style')

      expect(style).toContain('background-color')
    })

    it('COMP_GAU_014: icon wrapper has text color', () => {
      const wrapper = mountLGauge({ color: 'primary', colorMode: 'fixed' })
      const style = wrapper.find('.l-gauge__icon-wrapper').attributes('style')

      expect(style).toContain('color')
    })
  })

  // ==================== Value Formatting Tests ====================

  describe('Value Formatting', () => {
    it('COMP_GAU_015: displays integer values without decimal', () => {
      const wrapper = mountLGauge({ value: 42 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('42')
    })

    it('COMP_GAU_016: displays decimal values with one decimal place', () => {
      const wrapper = mountLGauge({ value: 42.567 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('42.6')
    })

    it('COMP_GAU_017: formats thousands with K suffix', () => {
      const wrapper = mountLGauge({ value: 1500 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('1.5K')
    })

    it('COMP_GAU_018: formats millions with M suffix', () => {
      const wrapper = mountLGauge({ value: 2500000 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('2.5M')
    })

    it('COMP_GAU_019: appends suffix to value', () => {
      const wrapper = mountLGauge({ value: 54, suffix: '%' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('54%')
    })

    it('COMP_GAU_020: appends suffix to K formatted value', () => {
      const wrapper = mountLGauge({ value: 2000, suffix: ' req/s' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('2.0K req/s')
    })

    it('COMP_GAU_021: displays string values as-is', () => {
      const wrapper = mountLGauge({ value: 'N/A', suffix: '' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('N/A')
    })

    it('COMP_GAU_022: displays string values with suffix', () => {
      const wrapper = mountLGauge({ value: 'Active', suffix: ' status' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('Active status')
    })
  })

  // ==================== Progress Bar Tests ====================

  describe('Progress Bar', () => {
    it('COMP_GAU_023: shows progress bar by default', () => {
      const wrapper = mountLGauge({ percent: 50 })

      expect(wrapper.find('.l-gauge__progress').exists()).toBe(true)
    })

    it('COMP_GAU_024: hides progress bar when showProgress is false', () => {
      const wrapper = mountLGauge({ showProgress: false })

      expect(wrapper.find('.l-gauge__progress').exists()).toBe(false)
    })

    it('COMP_GAU_025: renders track element', () => {
      const wrapper = mountLGauge({ percent: 50 })

      expect(wrapper.find('.l-gauge__track').exists()).toBe(true)
    })

    it('COMP_GAU_026: renders fill element', () => {
      const wrapper = mountLGauge({ percent: 50 })

      expect(wrapper.find('.l-gauge__fill').exists()).toBe(true)
    })

    it('COMP_GAU_027: fill width matches percent', () => {
      const wrapper = mountLGauge({ percent: 75 })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      expect(fillStyle).toContain('width: 75%')
    })

    it('COMP_GAU_028: clamps percent at 100', () => {
      const wrapper = mountLGauge({ percent: 150 })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      expect(fillStyle).toContain('width: 100%')
    })

    it('COMP_GAU_029: clamps percent at 0', () => {
      const wrapper = mountLGauge({ percent: -20 })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      expect(fillStyle).toContain('width: 0%')
    })

    it('COMP_GAU_030: hides percent text by default', () => {
      const wrapper = mountLGauge({ percent: 50 })

      expect(wrapper.find('.l-gauge__percent').exists()).toBe(false)
    })

    it('COMP_GAU_031: shows percent text when showPercent is true', () => {
      const wrapper = mountLGauge({ percent: 50, showPercent: true })

      expect(wrapper.find('.l-gauge__percent').exists()).toBe(true)
      expect(wrapper.find('.l-gauge__percent').text()).toBe('50%')
    })

    it('COMP_GAU_032: rounds percent text', () => {
      const wrapper = mountLGauge({ percent: 66.7, showPercent: true })

      expect(wrapper.find('.l-gauge__percent').text()).toBe('67%')
    })
  })

  // ==================== Color Mode Tests ====================

  describe('Color Mode - Threshold', () => {
    it('COMP_GAU_033: uses success color for percent < 60', () => {
      const wrapper = mountLGauge({ percent: 30, colorMode: 'threshold' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Success color is #98d4bb
      expect(fillStyle).toContain('#98d4bb')
    })

    it('COMP_GAU_034: uses warning color for percent 60-80', () => {
      const wrapper = mountLGauge({ percent: 70, colorMode: 'threshold' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Warning color is #e8c87a
      expect(fillStyle).toContain('#e8c87a')
    })

    it('COMP_GAU_035: uses danger color for percent > 80', () => {
      const wrapper = mountLGauge({ percent: 90, colorMode: 'threshold' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Danger color is #e8a087
      expect(fillStyle).toContain('#e8a087')
    })
  })

  describe('Color Mode - Inverse', () => {
    it('COMP_GAU_036: uses danger color for percent < 20', () => {
      const wrapper = mountLGauge({ percent: 10, colorMode: 'inverse' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Danger color is #e8a087
      expect(fillStyle).toContain('#e8a087')
    })

    it('COMP_GAU_037: uses warning color for percent 20-40', () => {
      const wrapper = mountLGauge({ percent: 30, colorMode: 'inverse' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Warning color is #e8c87a
      expect(fillStyle).toContain('#e8c87a')
    })

    it('COMP_GAU_038: uses success color for percent > 40', () => {
      const wrapper = mountLGauge({ percent: 50, colorMode: 'inverse' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Success color is #98d4bb
      expect(fillStyle).toContain('#98d4bb')
    })
  })

  describe('Color Mode - Fixed', () => {
    it('COMP_GAU_039: uses specified LLARS color name', () => {
      const wrapper = mountLGauge({ percent: 50, colorMode: 'fixed', color: 'accent' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Accent color is #88c4c8
      expect(fillStyle).toContain('#88c4c8')
    })

    it('COMP_GAU_040: uses custom hex color', () => {
      const wrapper = mountLGauge({ percent: 50, colorMode: 'fixed', color: '#ff5500' })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      expect(fillStyle).toContain('#ff5500')
    })
  })

  // ==================== Subtitle Tests ====================

  describe('Subtitle', () => {
    it('COMP_GAU_041: hides subtitle by default', () => {
      const wrapper = mountLGauge()

      expect(wrapper.find('.l-gauge__subtitle').exists()).toBe(false)
    })

    it('COMP_GAU_042: shows subtitle when prop provided', () => {
      const wrapper = mountLGauge({ subtitle: '16.4 / 22.8 GB' })

      expect(wrapper.find('.l-gauge__subtitle').exists()).toBe(true)
      expect(wrapper.find('.l-gauge__subtitle').text()).toBe('16.4 / 22.8 GB')
    })
  })

  // ==================== Compact Mode Tests ====================

  describe('Compact Mode', () => {
    it('COMP_GAU_043: does not have compact class by default', () => {
      const wrapper = mountLGauge()

      expect(wrapper.classes()).not.toContain('l-gauge--compact')
    })

    it('COMP_GAU_044: has compact class when compact prop is true', () => {
      const wrapper = mountLGauge({ compact: true })

      expect(wrapper.classes()).toContain('l-gauge--compact')
    })
  })

  // ==================== Loading State Tests ====================

  describe('Loading State', () => {
    it('COMP_GAU_045: does not have loading class by default', () => {
      const wrapper = mountLGauge()

      expect(wrapper.classes()).not.toContain('l-gauge--loading')
    })

    it('COMP_GAU_046: has loading class when loading prop is true', () => {
      const wrapper = mountLGauge({ loading: true })

      expect(wrapper.classes()).toContain('l-gauge--loading')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_GAU_047: uses value slot when provided', () => {
      const wrapper = mountLGauge(
        { value: 42 },
        {
          slots: {
            value: '<span class="custom-value">Custom 42</span>'
          }
        }
      )

      expect(wrapper.find('.l-gauge__value .custom-value').exists()).toBe(true)
      expect(wrapper.find('.custom-value').text()).toBe('Custom 42')
    })

    it('COMP_GAU_048: uses subtitle slot when provided', () => {
      const wrapper = mountLGauge(
        { subtitle: 'Ignored' },
        {
          slots: {
            subtitle: '<span class="custom-subtitle">Custom Subtitle</span>'
          }
        }
      )

      expect(wrapper.find('.l-gauge__subtitle .custom-subtitle').exists()).toBe(true)
      expect(wrapper.find('.custom-subtitle').text()).toBe('Custom Subtitle')
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_GAU_049: updates percent reactively', async () => {
      const wrapper = mountLGauge({ percent: 30 })

      expect(wrapper.find('.l-gauge__fill').attributes('style')).toContain('width: 30%')

      await wrapper.setProps({ percent: 80 })

      expect(wrapper.find('.l-gauge__fill').attributes('style')).toContain('width: 80%')
    })

    it('COMP_GAU_050: updates color based on percent change', async () => {
      const wrapper = mountLGauge({ percent: 30, colorMode: 'threshold' })
      let fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Initially success (< 60)
      expect(fillStyle).toContain('#98d4bb')

      await wrapper.setProps({ percent: 90 })
      fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      // Now danger (> 80)
      expect(fillStyle).toContain('#e8a087')
    })

    it('COMP_GAU_051: updates value display reactively', async () => {
      const wrapper = mountLGauge({ value: 50, suffix: '%' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('50%')

      await wrapper.setProps({ value: 75 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('75%')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_GAU_052: handles null percent', () => {
      const wrapper = mountLGauge({ percent: null })
      const fillStyle = wrapper.find('.l-gauge__fill').attributes('style')

      expect(fillStyle).toContain('width: 0%')
    })

    it('COMP_GAU_053: handles zero value', () => {
      const wrapper = mountLGauge({ value: 0, suffix: '%' })

      expect(wrapper.find('.l-gauge__value').text()).toBe('0%')
    })

    it('COMP_GAU_054: handles exactly 1000 value', () => {
      const wrapper = mountLGauge({ value: 1000 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('1.0K')
    })

    it('COMP_GAU_055: handles exactly 1000000 value', () => {
      const wrapper = mountLGauge({ value: 1000000 })

      expect(wrapper.find('.l-gauge__value').text()).toBe('1.0M')
    })
  })
})
