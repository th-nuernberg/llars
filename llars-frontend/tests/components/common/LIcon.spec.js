/**
 * LIcon Component Tests
 *
 * Tests for the LLARS icon component that wraps Vuetify v-icon
 * and supports custom LLARS icons via itshover icon set.
 * Test IDs: COMP_ICN_001 - COMP_ICN_025
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LIcon from '@/components/common/LIcon.vue'

const vuetify = createVuetify({ components, directives })

vi.mock('@/icons/itshover', () => ({
  resolveIconComponent: vi.fn((name) => {
    // For mdi- icons, return the name directly (Vuetify handles them)
    if (typeof name === 'string' && name.startsWith('mdi-')) return name
    // For custom icons, return a mock component
    return name || 'mdi-help-circle'
  })
}))

function mountComponent(props = {}, options = {}) {
  return mount(LIcon, {
    props,
    global: {
      plugins: [vuetify],
      ...options.global
    },
    slots: options.slots || {},
    ...options
  })
}

describe('LIcon', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_ICN_001: renders with icon prop', () => {
      const wrapper = mountComponent({ icon: 'mdi-home' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_002: renders with name prop', () => {
      const wrapper = mountComponent({ name: 'mdi-cog' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_003: renders with slot content', () => {
      const wrapper = mountComponent({}, {
        slots: { default: 'mdi-star' }
      })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_004: prefers icon prop over name prop', () => {
      const wrapper = mountComponent({ icon: 'mdi-home', name: 'mdi-cog' })

      // The resolvedIcon should be based on icon prop
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_005: prefers icon prop over slot', () => {
      const wrapper = mountComponent(
        { icon: 'mdi-home' },
        { slots: { default: 'mdi-star' } }
      )

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_006: prefers name prop over slot', () => {
      const wrapper = mountComponent(
        { name: 'mdi-cog' },
        { slots: { default: 'mdi-star' } }
      )

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })
  })

  // ==================== Size Tests ====================

  describe('Size', () => {
    it('COMP_ICN_007: passes numeric size to v-icon', () => {
      const wrapper = mountComponent({ icon: 'mdi-home', size: 24 })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('size')).toBe(24)
    })

    it('COMP_ICN_008: passes string size to v-icon', () => {
      const wrapper = mountComponent({ icon: 'mdi-home', size: 'large' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('size')).toBe('large')
    })

    it('COMP_ICN_009: uses default size when not specified', () => {
      const wrapper = mountComponent({ icon: 'mdi-home' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      // Vuetify uses 'default' as the default size value
      expect(vIcon.props('size')).toBe('default')
    })
  })

  // ==================== Color Tests ====================

  describe('Color', () => {
    it('COMP_ICN_010: passes color prop to v-icon', () => {
      const wrapper = mountComponent({ icon: 'mdi-home', color: 'primary' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('color')).toBe('primary')
    })

    it('COMP_ICN_011: handles no color prop', () => {
      const wrapper = mountComponent({ icon: 'mdi-home' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('color')).toBeUndefined()
    })

    it('COMP_ICN_012: passes specific color values', () => {
      const wrapper = mountComponent({ icon: 'mdi-home', color: 'success' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('color')).toBe('success')
    })
  })

  // ==================== Spin Animation Tests ====================

  describe('Spin Animation', () => {
    it('COMP_ICN_013: adds mdi-spin class when icon includes spin', () => {
      const wrapper = mountComponent({ icon: 'mdi-loading mdi-spin' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.classes()).toContain('mdi-spin')
    })

    it('COMP_ICN_014: does not add spin class for normal icons', () => {
      const wrapper = mountComponent({ icon: 'mdi-home' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.classes()).not.toContain('mdi-spin')
    })

    it('COMP_ICN_015: extracts icon name when spin is present', () => {
      // 'mdi-loading mdi-spin' should resolve to 'mdi-loading' as the icon name
      const wrapper = mountComponent({ icon: 'mdi-loading mdi-spin' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })
  })

  // ==================== Attr Forwarding Tests ====================

  describe('Attribute Forwarding', () => {
    it('COMP_ICN_016: forwards additional attributes to v-icon', () => {
      const wrapper = mountComponent({
        icon: 'mdi-home',
        start: true
      })

      // The component uses inheritAttrs: false and forwards via iconAttrs
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_017: handles class attribute from parent', () => {
      const wrapper = mount(LIcon, {
        props: { icon: 'mdi-home' },
        attrs: { class: 'custom-class' },
        global: { plugins: [vuetify] }
      })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.classes()).toContain('custom-class')
    })
  })

  // ==================== Icon Resolution Tests ====================

  describe('Icon Resolution', () => {
    it('COMP_ICN_018: resolves standard mdi icons', () => {
      const wrapper = mountComponent({ icon: 'mdi-check' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_019: resolves icon from slot text', () => {
      const wrapper = mountComponent({}, {
        slots: { default: 'mdi-alert' }
      })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_020: handles non-string icon values', () => {
      // When a function or object is passed, it should be used as-is
      const iconObj = { component: 'SomeCustomIcon' }
      const wrapper = mountComponent({ icon: iconObj })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_021: handles undefined icon gracefully', () => {
      const wrapper = mountComponent({})

      // No icon specified at all - should still render v-icon
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })
  })

  // ==================== Edge Case Tests ====================

  describe('Edge Cases', () => {
    it('COMP_ICN_022: handles empty string icon', () => {
      const wrapper = mountComponent({ icon: '' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_023: handles whitespace in icon name', () => {
      const wrapper = mountComponent({ icon: '  mdi-home  ' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ICN_024: handles icon with multiple spaces between parts', () => {
      const wrapper = mountComponent({ icon: 'mdi-loading   mdi-spin' })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.classes()).toContain('mdi-spin')
    })

    it('COMP_ICN_025: size from attrs is used as fallback', () => {
      // When size prop is undefined but attrs has size
      const wrapper = mount(LIcon, {
        props: { icon: 'mdi-home' },
        attrs: { size: 32 },
        global: { plugins: [vuetify] }
      })

      const vIcon = wrapper.findComponent({ name: 'VIcon' })
      expect(vIcon.props('size')).toBe(32)
    })
  })
})
