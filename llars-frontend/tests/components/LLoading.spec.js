/**
 * LLoading Component Tests
 *
 * Tests for the LLARS animated loading component.
 * Test IDs: COMP_LDG_001 - COMP_LDG_040
 *
 * Coverage:
 * - Rendering and structure
 * - Size variants (sm, md, lg)
 * - Label prop
 * - Accessibility attributes
 * - Animation elements
 * - Edge cases
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LLoading from '@/components/common/LLoading.vue'

function mountLLoading(props = {}, options = {}) {
  return mount(LLoading, {
    props,
    ...options
  })
}

describe('LLoading', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_LDG_001: renders with default props', () => {
      const wrapper = mountLLoading()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-loading').exists()).toBe(true)
    })

    it('COMP_LDG_002: has l-loading class', () => {
      const wrapper = mountLLoading()

      expect(wrapper.classes()).toContain('l-loading')
    })

    it('COMP_LDG_003: renders scene container', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__scene').exists()).toBe(true)
    })

    it('COMP_LDG_004: renders back sheet', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__sheet--back').exists()).toBe(true)
    })

    it('COMP_LDG_005: renders front sheet', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__sheet--front').exists()).toBe(true)
    })

    it('COMP_LDG_006: renders all four animated lines', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__line--1').exists()).toBe(true)
      expect(wrapper.find('.l-loading__line--2').exists()).toBe(true)
      expect(wrapper.find('.l-loading__line--3').exists()).toBe(true)
      expect(wrapper.find('.l-loading__line--4').exists()).toBe(true)
    })

    it('COMP_LDG_007: renders progress element', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__progress').exists()).toBe(true)
    })

    it('COMP_LDG_008: does not render label by default', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__label').exists()).toBe(false)
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_LDG_009: uses md size by default (no size class)', () => {
      const wrapper = mountLLoading()

      expect(wrapper.classes()).not.toContain('l-loading--sm')
      expect(wrapper.classes()).not.toContain('l-loading--lg')
    })

    it('COMP_LDG_010: applies sm size class', () => {
      const wrapper = mountLLoading({ size: 'sm' })

      expect(wrapper.classes()).toContain('l-loading--sm')
    })

    it('COMP_LDG_011: applies lg size class', () => {
      const wrapper = mountLLoading({ size: 'lg' })

      expect(wrapper.classes()).toContain('l-loading--lg')
    })

    it('COMP_LDG_012: md size has no additional class', () => {
      const wrapper = mountLLoading({ size: 'md' })

      expect(wrapper.classes()).not.toContain('l-loading--sm')
      expect(wrapper.classes()).not.toContain('l-loading--lg')
      expect(wrapper.classes()).not.toContain('l-loading--md')
    })

    it('COMP_LDG_013: sm and lg are mutually exclusive', () => {
      const wrapperSm = mountLLoading({ size: 'sm' })
      const wrapperLg = mountLLoading({ size: 'lg' })

      expect(wrapperSm.classes()).toContain('l-loading--sm')
      expect(wrapperSm.classes()).not.toContain('l-loading--lg')

      expect(wrapperLg.classes()).toContain('l-loading--lg')
      expect(wrapperLg.classes()).not.toContain('l-loading--sm')
    })
  })

  // ==================== Label Tests ====================

  describe('Label', () => {
    it('COMP_LDG_014: renders label when provided', () => {
      const wrapper = mountLLoading({ label: 'Loading...' })

      expect(wrapper.find('.l-loading__label').exists()).toBe(true)
    })

    it('COMP_LDG_015: displays correct label text', () => {
      const wrapper = mountLLoading({ label: 'Please wait' })

      expect(wrapper.find('.l-loading__label').text()).toBe('Please wait')
    })

    it('COMP_LDG_016: does not render label when empty string', () => {
      const wrapper = mountLLoading({ label: '' })

      expect(wrapper.find('.l-loading__label').exists()).toBe(false)
    })

    it('COMP_LDG_017: handles long label text', () => {
      const longLabel = 'Loading your data, this might take a moment...'
      const wrapper = mountLLoading({ label: longLabel })

      expect(wrapper.find('.l-loading__label').text()).toBe(longLabel)
    })

    it('COMP_LDG_018: handles special characters in label', () => {
      const wrapper = mountLLoading({ label: 'Lädt... <test>' })

      expect(wrapper.find('.l-loading__label').text()).toBe('Lädt... <test>')
    })

    it('COMP_LDG_019: label updates reactively', async () => {
      const wrapper = mountLLoading({ label: 'Loading...' })

      expect(wrapper.find('.l-loading__label').text()).toBe('Loading...')

      await wrapper.setProps({ label: 'Almost done!' })

      expect(wrapper.find('.l-loading__label').text()).toBe('Almost done!')
    })

    it('COMP_LDG_020: label can be removed', async () => {
      const wrapper = mountLLoading({ label: 'Loading...' })

      expect(wrapper.find('.l-loading__label').exists()).toBe(true)

      await wrapper.setProps({ label: '' })

      expect(wrapper.find('.l-loading__label').exists()).toBe(false)
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_LDG_021: has role="status"', () => {
      const wrapper = mountLLoading()

      expect(wrapper.attributes('role')).toBe('status')
    })

    it('COMP_LDG_022: has aria-live="polite" when label is present', () => {
      const wrapper = mountLLoading({ label: 'Loading...' })

      expect(wrapper.attributes('aria-live')).toBe('polite')
    })

    it('COMP_LDG_023: has aria-live="off" when no label', () => {
      const wrapper = mountLLoading()

      expect(wrapper.attributes('aria-live')).toBe('off')
    })

    it('COMP_LDG_024: scene is hidden from screen readers', () => {
      const wrapper = mountLLoading()
      const scene = wrapper.find('.l-loading__scene')

      expect(scene.attributes('aria-hidden')).toBe('true')
    })

    it('COMP_LDG_025: aria-live updates when label changes', async () => {
      const wrapper = mountLLoading()

      expect(wrapper.attributes('aria-live')).toBe('off')

      await wrapper.setProps({ label: 'Now loading' })

      expect(wrapper.attributes('aria-live')).toBe('polite')
    })
  })

  // ==================== Structure Tests ====================

  describe('Structure', () => {
    it('COMP_LDG_026: lines are inside front sheet', () => {
      const wrapper = mountLLoading()
      const frontSheet = wrapper.find('.l-loading__sheet--front')

      expect(frontSheet.find('.l-loading__line--1').exists()).toBe(true)
      expect(frontSheet.find('.l-loading__line--2').exists()).toBe(true)
      expect(frontSheet.find('.l-loading__line--3').exists()).toBe(true)
      expect(frontSheet.find('.l-loading__line--4').exists()).toBe(true)
    })

    it('COMP_LDG_027: progress is inside front sheet', () => {
      const wrapper = mountLLoading()
      const frontSheet = wrapper.find('.l-loading__sheet--front')

      expect(frontSheet.find('.l-loading__progress').exists()).toBe(true)
    })

    it('COMP_LDG_028: has exactly two sheet elements', () => {
      const wrapper = mountLLoading()
      const sheets = wrapper.findAll('.l-loading__sheet')

      expect(sheets.length).toBe(2)
    })

    it('COMP_LDG_029: has exactly four line elements', () => {
      const wrapper = mountLLoading()
      const lines = wrapper.findAll('[class*="l-loading__line--"]')

      expect(lines.length).toBe(4)
    })

    it('COMP_LDG_030: label is outside scene', () => {
      const wrapper = mountLLoading({ label: 'Loading' })
      const scene = wrapper.find('.l-loading__scene')

      expect(scene.find('.l-loading__label').exists()).toBe(false)
    })
  })

  // ==================== CSS Classes Tests ====================

  describe('CSS Classes', () => {
    it('COMP_LDG_031: back sheet has correct class', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__sheet.l-loading__sheet--back').exists()).toBe(true)
    })

    it('COMP_LDG_032: front sheet has correct class', () => {
      const wrapper = mountLLoading()

      expect(wrapper.find('.l-loading__sheet.l-loading__sheet--front').exists()).toBe(true)
    })

    it('COMP_LDG_033: lines have l-loading__line base class', () => {
      const wrapper = mountLLoading()

      const line1 = wrapper.find('.l-loading__line--1')
      const line2 = wrapper.find('.l-loading__line--2')
      const line3 = wrapper.find('.l-loading__line--3')
      const line4 = wrapper.find('.l-loading__line--4')

      expect(line1.classes()).toContain('l-loading__line')
      expect(line2.classes()).toContain('l-loading__line')
      expect(line3.classes()).toContain('l-loading__line')
      expect(line4.classes()).toContain('l-loading__line')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_LDG_034: handles undefined label', () => {
      const wrapper = mountLLoading({ label: undefined })

      expect(wrapper.find('.l-loading__label').exists()).toBe(false)
    })

    it('COMP_LDG_035: handles null-ish label', () => {
      const wrapper = mountLLoading({ label: null })

      expect(wrapper.find('.l-loading__label').exists()).toBe(false)
    })

    it('COMP_LDG_036: size prop reactivity', async () => {
      const wrapper = mountLLoading({ size: 'sm' })

      expect(wrapper.classes()).toContain('l-loading--sm')

      await wrapper.setProps({ size: 'lg' })

      expect(wrapper.classes()).not.toContain('l-loading--sm')
      expect(wrapper.classes()).toContain('l-loading--lg')
    })

    it('COMP_LDG_037: multiple instances are independent', () => {
      const wrapper1 = mountLLoading({ size: 'sm', label: 'First' })
      const wrapper2 = mountLLoading({ size: 'lg', label: 'Second' })

      expect(wrapper1.classes()).toContain('l-loading--sm')
      expect(wrapper2.classes()).toContain('l-loading--lg')

      expect(wrapper1.find('.l-loading__label').text()).toBe('First')
      expect(wrapper2.find('.l-loading__label').text()).toBe('Second')
    })

    it('COMP_LDG_038: whitespace-only label is rendered', () => {
      const wrapper = mountLLoading({ label: '   ' })

      // Whitespace is truthy, so label should render
      expect(wrapper.find('.l-loading__label').exists()).toBe(true)
    })

    it('COMP_LDG_039: numeric label is converted to string', () => {
      // @ts-ignore - testing edge case
      const wrapper = mountLLoading({ label: 123 })

      expect(wrapper.find('.l-loading__label').text()).toBe('123')
    })

    it('COMP_LDG_040: component works without any props', () => {
      const wrapper = mount(LLoading)

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-loading').exists()).toBe(true)
      expect(wrapper.find('.l-loading__scene').exists()).toBe(true)
    })
  })
})
