/**
 * LViewToggle Component Tests
 *
 * Tests for the LLARS card/list view mode toggle component.
 * Test IDs: COMP_VT_001 - COMP_VT_014
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LViewToggle from '@/components/common/LViewToggle.vue'

function mountLViewToggle(props = {}, options = {}) {
  return mount(LViewToggle, {
    props,
    global: {
      stubs: {
        LIcon: { template: '<i><slot /></i>', props: ['size'] }
      },
      ...options.global
    },
    ...options
  })
}

describe('LViewToggle', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_VT_001: renders with default props', () => {
      const wrapper = mountLViewToggle()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-view-toggle').exists()).toBe(true)
    })

    it('COMP_VT_002: renders two toggle buttons', () => {
      const wrapper = mountLViewToggle()

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons).toHaveLength(2)
    })

    it('COMP_VT_003: first button is for list view', () => {
      const wrapper = mountLViewToggle({ listLabel: 'List' })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons[0].attributes('title')).toBe('List')
    })

    it('COMP_VT_004: second button is for cards view', () => {
      const wrapper = mountLViewToggle({ cardsLabel: 'Cards' })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons[1].attributes('title')).toBe('Cards')
    })
  })

  // ==================== v-model / Active State Tests ====================

  describe('v-model', () => {
    it('COMP_VT_005: cards button is active by default', () => {
      const wrapper = mountLViewToggle()

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons[1].classes()).toContain('active')
      expect(buttons[0].classes()).not.toContain('active')
    })

    it('COMP_VT_006: list button is active when modelValue is list', () => {
      const wrapper = mountLViewToggle({ modelValue: 'list' })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons[0].classes()).toContain('active')
      expect(buttons[1].classes()).not.toContain('active')
    })

    it('COMP_VT_007: emits update:modelValue with list when list button clicked', async () => {
      const wrapper = mountLViewToggle({ modelValue: 'cards' })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      await buttons[0].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['list'])
    })

    it('COMP_VT_008: emits update:modelValue with cards when cards button clicked', async () => {
      const wrapper = mountLViewToggle({ modelValue: 'list' })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      await buttons[1].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['cards'])
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_VT_009: applies default size class', () => {
      const wrapper = mountLViewToggle()

      expect(wrapper.classes()).toContain('l-view-toggle--default')
    })

    it('COMP_VT_010: applies small size class', () => {
      const wrapper = mountLViewToggle({ size: 'small' })

      expect(wrapper.classes()).toContain('l-view-toggle--small')
    })

    it('COMP_VT_011: applies large size class', () => {
      const wrapper = mountLViewToggle({ size: 'large' })

      expect(wrapper.classes()).toContain('l-view-toggle--large')
    })

    it('COMP_VT_012: passes correct icon size for small', () => {
      const wrapper = mountLViewToggle({ size: 'small' })

      const icons = wrapper.findAllComponents({ name: 'LIcon' })
      if (icons.length > 0) {
        expect(icons[0].props('size')).toBe(16)
      }
    })

    it('COMP_VT_013: passes correct icon size for large', () => {
      const wrapper = mountLViewToggle({ size: 'large' })

      const icons = wrapper.findAllComponents({ name: 'LIcon' })
      if (icons.length > 0) {
        expect(icons[0].props('size')).toBe(22)
      }
    })
  })

  // ==================== Custom Labels Tests ====================

  describe('Custom Labels', () => {
    it('COMP_VT_014: uses custom labels for title attributes', () => {
      const wrapper = mountLViewToggle({
        cardsLabel: 'Kachelansicht',
        listLabel: 'Listenansicht'
      })

      const buttons = wrapper.findAll('.l-view-toggle__btn')
      expect(buttons[0].attributes('title')).toBe('Listenansicht')
      expect(buttons[1].attributes('title')).toBe('Kachelansicht')
    })
  })
})
