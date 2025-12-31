/**
 * LIconBtn Component Tests
 *
 * Tests for the LLARS icon button component.
 * Test IDs: COMP_ICB_001 - COMP_ICB_045
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LIconBtn from '@/components/common/LIconBtn.vue'

const vuetify = createVuetify({ components, directives })

function mountLIconBtn(props = {}, options = {}) {
  return mount(LIconBtn, {
    props: {
      icon: 'mdi-pencil',
      ...props,
    },
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    ...options,
  })
}

describe('LIconBtn', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_ICB_001: renders with required icon prop', () => {
      const wrapper = mountLIconBtn()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-icon-btn').exists()).toBe(true)
    })

    it('COMP_ICB_002: has LLARS icon button base class', () => {
      const wrapper = mountLIconBtn()

      expect(wrapper.find('.l-icon-btn').exists()).toBe(true)
    })

    it('COMP_ICB_003: renders v-btn component', () => {
      const wrapper = mountLIconBtn()

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.exists()).toBe(true)
    })

    it('COMP_ICB_004: renders v-icon component', () => {
      const wrapper = mountLIconBtn()

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.exists()).toBe(true)
    })

    it('COMP_ICB_005: uses text variant for v-btn', () => {
      const wrapper = mountLIconBtn()

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('variant')).toBe('text')
    })
  })

  // ==================== Icon Tests ====================

  describe('Icon', () => {
    it('COMP_ICB_006: renders correct icon', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-home' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('icon')).toBe('mdi-home')
    })

    it('COMP_ICB_007: renders different icons', () => {
      const icons = ['mdi-delete', 'mdi-star', 'mdi-cog', 'mdi-account']

      icons.forEach(iconName => {
        const wrapper = mountLIconBtn({ icon: iconName })
        const icon = wrapper.findComponent({ name: 'v-icon' })
        expect(icon.props('icon')).toBe(iconName)
      })
    })

    it('COMP_ICB_008: applies correct icon size for small button', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil', size: 'small' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('size')).toBe(20)
    })

    it('COMP_ICB_009: applies correct icon size for x-small button', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil', size: 'x-small' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('size')).toBe(16)
    })

    it('COMP_ICB_010: applies correct icon size for default button', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil', size: 'default' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('size')).toBe(24)
    })

    it('COMP_ICB_011: applies correct icon size for large button', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil', size: 'large' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('size')).toBe(28)
    })

    it('COMP_ICB_012: applies correct icon size for x-large button', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil', size: 'x-large' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('size')).toBe(32)
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    it('COMP_ICB_013: uses default variant by default', () => {
      const wrapper = mountLIconBtn()

      expect(wrapper.find('.l-icon-btn--default').exists()).toBe(true)
    })

    it('COMP_ICB_014: applies default variant class', () => {
      const wrapper = mountLIconBtn({ variant: 'default' })

      expect(wrapper.find('.l-icon-btn--default').exists()).toBe(true)
    })

    it('COMP_ICB_015: applies primary variant class', () => {
      const wrapper = mountLIconBtn({ variant: 'primary' })

      expect(wrapper.find('.l-icon-btn--primary').exists()).toBe(true)
    })

    it('COMP_ICB_016: applies danger variant class', () => {
      const wrapper = mountLIconBtn({ variant: 'danger' })

      expect(wrapper.find('.l-icon-btn--danger').exists()).toBe(true)
    })

    it('COMP_ICB_017: applies success variant class', () => {
      const wrapper = mountLIconBtn({ variant: 'success' })

      expect(wrapper.find('.l-icon-btn--success').exists()).toBe(true)
    })

    it('COMP_ICB_018: applies warning variant class', () => {
      const wrapper = mountLIconBtn({ variant: 'warning' })

      expect(wrapper.find('.l-icon-btn--warning').exists()).toBe(true)
    })

    it('COMP_ICB_019: passes color to v-btn for primary variant', () => {
      const wrapper = mountLIconBtn({ variant: 'primary' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('color')).toBe('primary')
    })

    it('COMP_ICB_020: passes error color for danger variant', () => {
      const wrapper = mountLIconBtn({ variant: 'danger' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('color')).toBe('error')
    })

    it('COMP_ICB_021: passes no color for default variant', () => {
      const wrapper = mountLIconBtn({ variant: 'default' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('color')).toBeUndefined()
    })
  })

  // ==================== Size Tests ====================

  describe('Size', () => {
    it('COMP_ICB_022: uses small size by default', () => {
      const wrapper = mountLIconBtn()

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('size')).toBe('small')
    })

    it('COMP_ICB_023: applies x-small size', () => {
      const wrapper = mountLIconBtn({ size: 'x-small' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('size')).toBe('x-small')
    })

    it('COMP_ICB_024: applies default size', () => {
      const wrapper = mountLIconBtn({ size: 'default' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('size')).toBe('default')
    })

    it('COMP_ICB_025: applies large size', () => {
      const wrapper = mountLIconBtn({ size: 'large' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('size')).toBe('large')
    })

    it('COMP_ICB_026: applies x-large size', () => {
      const wrapper = mountLIconBtn({ size: 'x-large' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('size')).toBe('x-large')
    })
  })

  // ==================== Tooltip Tests ====================

  describe('Tooltip', () => {
    it('COMP_ICB_027: renders tooltip when provided', () => {
      const wrapper = mountLIconBtn({ tooltip: 'Edit item' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_ICB_028: does not render tooltip when not provided', () => {
      const wrapper = mountLIconBtn({ tooltip: null })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(false)
    })

    it('COMP_ICB_029: uses top tooltip location by default', () => {
      const wrapper = mountLIconBtn({ tooltip: 'Edit' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('top')
    })

    it('COMP_ICB_030: applies custom tooltip location', () => {
      const wrapper = mountLIconBtn({ tooltip: 'Edit', tooltipLocation: 'bottom' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('bottom')
    })

    it('COMP_ICB_031: supports all tooltip locations', () => {
      const locations = ['top', 'bottom', 'left', 'right']

      locations.forEach(location => {
        const wrapper = mountLIconBtn({ tooltip: 'Test', tooltipLocation: location })
        const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
        expect(tooltip.props('location')).toBe(location)
      })
    })
  })

  // ==================== State Tests ====================

  describe('States', () => {
    it('COMP_ICB_032: is not loading by default', () => {
      const wrapper = mountLIconBtn()

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('loading')).toBe(false)
    })

    it('COMP_ICB_033: applies loading state', () => {
      const wrapper = mountLIconBtn({ loading: true })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('loading')).toBe(true)
    })

    it('COMP_ICB_034: is not disabled by default', () => {
      const wrapper = mountLIconBtn()

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('disabled')).toBe(false)
    })

    it('COMP_ICB_035: applies disabled state', () => {
      const wrapper = mountLIconBtn({ disabled: true })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('disabled')).toBe(true)
    })

    it('COMP_ICB_036: can be both loading and disabled', () => {
      const wrapper = mountLIconBtn({ loading: true, disabled: true })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.props('loading')).toBe(true)
      expect(btn.props('disabled')).toBe(true)
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_ICB_037: emits click event on click', async () => {
      const wrapper = mountLIconBtn()

      await wrapper.findComponent({ name: 'v-btn' }).trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')).toHaveLength(1)
    })

    it('COMP_ICB_038: emits click event with event object', async () => {
      const wrapper = mountLIconBtn()

      await wrapper.findComponent({ name: 'v-btn' }).trigger('click')

      expect(wrapper.emitted('click')[0][0]).toBeDefined()
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_ICB_039: uses tooltip as aria-label when provided', () => {
      const wrapper = mountLIconBtn({ tooltip: 'Edit document' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.attributes('aria-label')).toBe('Edit document')
    })

    it('COMP_ICB_040: uses icon name as fallback aria-label', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-pencil' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.attributes('aria-label')).toBe('mdi-pencil')
    })

    it('COMP_ICB_041: uses explicit aria-label attribute if provided', () => {
      const wrapper = mountLIconBtn(
        { icon: 'mdi-pencil', tooltip: 'Edit' },
        { attrs: { 'aria-label': 'Custom Label' } }
      )

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.attributes('aria-label')).toBe('Custom Label')
    })

    it('COMP_ICB_042: sets data-matomo-name for tracking', () => {
      const wrapper = mountLIconBtn({ tooltip: 'Save' })

      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.attributes('data-matomo-name')).toBe('Save')
    })
  })

  // ==================== Complete Component Tests ====================

  describe('Complete Component', () => {
    it('COMP_ICB_043: renders complete button with all props', () => {
      const wrapper = mountLIconBtn({
        icon: 'mdi-delete',
        variant: 'danger',
        size: 'large',
        tooltip: 'Delete item',
        tooltipLocation: 'bottom',
        loading: false,
        disabled: false
      })

      // Check button
      const btn = wrapper.findComponent({ name: 'v-btn' })
      expect(btn.exists()).toBe(true)
      expect(btn.props('size')).toBe('large')
      expect(btn.props('color')).toBe('error')

      // Check icon
      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('icon')).toBe('mdi-delete')

      // Check tooltip
      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
      expect(tooltip.props('location')).toBe('bottom')

      // Check classes
      expect(wrapper.find('.l-icon-btn--danger').exists()).toBe(true)
    })

    it('COMP_ICB_044: renders minimal button correctly', () => {
      const wrapper = mountLIconBtn({ icon: 'mdi-close' })

      expect(wrapper.find('.l-icon-btn').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'v-icon' }).props('icon')).toBe('mdi-close')
      expect(wrapper.findComponent({ name: 'v-tooltip' }).exists()).toBe(false)
    })

    it('COMP_ICB_045: handles multiple buttons independently', () => {
      const wrapper1 = mountLIconBtn({ icon: 'mdi-edit', variant: 'primary' })
      const wrapper2 = mountLIconBtn({ icon: 'mdi-delete', variant: 'danger' })

      expect(wrapper1.find('.l-icon-btn--primary').exists()).toBe(true)
      expect(wrapper2.find('.l-icon-btn--danger').exists()).toBe(true)

      expect(wrapper1.findComponent({ name: 'v-icon' }).props('icon')).toBe('mdi-edit')
      expect(wrapper2.findComponent({ name: 'v-icon' }).props('icon')).toBe('mdi-delete')
    })
  })
})
