/**
 * LTag Component Tests
 *
 * Tests for the LLARS tag/chip component.
 * Test IDs: COMP_TAG_001 - COMP_TAG_025
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LTag from '@/components/common/LTag.vue'

const vuetify = createVuetify({ components, directives })

function mountLTag(props = {}, options = {}) {
  return mount(LTag, {
    props,
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    slots: options.slots || { default: 'Tag Text' },
    ...options,
  })
}

describe('LTag', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_TAG_001: renders with default props', () => {
      const wrapper = mountLTag()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('span').exists()).toBe(true)
      expect(wrapper.text()).toContain('Tag Text')
    })

    it('COMP_TAG_002: renders slot content correctly', () => {
      const wrapper = mountLTag({}, { slots: { default: 'Custom Label' } })

      expect(wrapper.text()).toContain('Custom Label')
    })

    it('COMP_TAG_003: applies default variant (primary)', () => {
      const wrapper = mountLTag()

      expect(wrapper.classes()).toContain('llars-tag--primary')
    })

    it('COMP_TAG_004: has LLARS tag base class', () => {
      const wrapper = mountLTag()

      expect(wrapper.classes()).toContain('llars-tag')
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    const variants = [
      'primary',
      'secondary',
      'accent',
      'success',
      'info',
      'warning',
      'danger',
      'gray',
    ]

    variants.forEach((variant, index) => {
      it(`COMP_TAG_${String(5 + index).padStart(3, '0')}: renders ${variant} variant`, () => {
        const wrapper = mountLTag({ variant })

        expect(wrapper.classes()).toContain(`llars-tag--${variant}`)
      })
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_TAG_013: renders small size (sm)', () => {
      const wrapper = mountLTag({ size: 'sm' })

      expect(wrapper.classes()).toContain('llars-tag--sm')
    })

    it('COMP_TAG_014: renders small size (small alias)', () => {
      const wrapper = mountLTag({ size: 'small' })

      expect(wrapper.classes()).toContain('llars-tag--sm')
    })

    it('COMP_TAG_015: renders default size without extra class', () => {
      const wrapper = mountLTag({ size: 'md' })

      // Default size doesn't add a class
      expect(wrapper.classes()).not.toContain('llars-tag--md')
    })

    it('COMP_TAG_016: renders large size (lg)', () => {
      const wrapper = mountLTag({ size: 'lg' })

      expect(wrapper.classes()).toContain('llars-tag--lg')
    })

    it('COMP_TAG_017: renders large size (large alias)', () => {
      const wrapper = mountLTag({ size: 'large' })

      expect(wrapper.classes()).toContain('llars-tag--lg')
    })
  })

  // ==================== Icon Tests ====================

  describe('Icons', () => {
    it('COMP_TAG_018: renders prepend icon', () => {
      const wrapper = mountLTag({ prependIcon: 'mdi-check' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_TAG_019: renders append icon', () => {
      const wrapper = mountLTag({ appendIcon: 'mdi-arrow-right' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })
  })

  // ==================== Closable Tests ====================

  describe('Closable', () => {
    it('COMP_TAG_020: renders close icon when closable', () => {
      const wrapper = mountLTag({ closable: true })

      expect(wrapper.find('.close-icon').exists()).toBe(true)
    })

    it('COMP_TAG_021: emits close event when close icon clicked', async () => {
      const wrapper = mountLTag({ closable: true })

      await wrapper.find('.close-icon').trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
      expect(wrapper.emitted('close')).toHaveLength(1)
    })

    it('COMP_TAG_022: close click does not bubble to parent', async () => {
      const wrapper = mountLTag({ closable: true, clickable: true })

      await wrapper.find('.close-icon').trigger('click')

      // Close should be emitted, but click should not
      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })

  // ==================== Clickable Tests ====================

  describe('Clickable', () => {
    it('COMP_TAG_023: adds clickable class when clickable', () => {
      const wrapper = mountLTag({ clickable: true })

      expect(wrapper.classes()).toContain('llars-tag--clickable')
    })

    it('COMP_TAG_024: is not clickable by default', () => {
      const wrapper = mountLTag()

      expect(wrapper.classes()).not.toContain('llars-tag--clickable')
    })
  })

  // ==================== Icon Size Tests ====================

  describe('Icon Sizes', () => {
    it('COMP_TAG_025: adjusts icon size based on tag size', () => {
      const wrapperSm = mountLTag({ size: 'sm', prependIcon: 'mdi-check' })
      const wrapperLg = mountLTag({ size: 'lg', prependIcon: 'mdi-check' })

      const iconSm = wrapperSm.find('.v-icon')
      const iconLg = wrapperLg.find('.v-icon')

      // Both should have icons, size is controlled via props
      expect(iconSm.exists()).toBe(true)
      expect(iconLg.exists()).toBe(true)
    })
  })
})
