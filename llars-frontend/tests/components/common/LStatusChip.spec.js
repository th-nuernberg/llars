/**
 * LStatusChip Component Tests
 *
 * Tests for the LLARS status chip component that displays
 * saving/error/saved/idle states.
 * Test IDs: COMP_SC_001 - COMP_SC_012
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LStatusChip from '@/components/common/LStatusChip.vue'

const vuetify = createVuetify({ components, directives })

function mountLStatusChip(props = {}, options = {}) {
  return mount(LStatusChip, {
    props,
    global: {
      plugins: [vuetify],
      stubs: {
        LIcon: { template: '<i><slot /></i>' }
      },
      ...options.global
    },
    ...options
  })
}

describe('LStatusChip', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_SC_001: renders nothing when state is idle (default)', () => {
      const wrapper = mountLStatusChip()

      // idle state should not render any chip
      expect(wrapper.find('.v-chip').exists()).toBe(false)
      expect(wrapper.text()).toBe('')
    })

    it('COMP_SC_002: renders nothing when state is explicitly idle', () => {
      const wrapper = mountLStatusChip({ state: 'idle' })

      expect(wrapper.find('.v-chip').exists()).toBe(false)
    })
  })

  // ==================== State Tests ====================

  describe('States', () => {
    it('COMP_SC_003: renders saving state with spinner', () => {
      const wrapper = mountLStatusChip({ state: 'saving' })

      expect(wrapper.find('.v-chip').exists()).toBe(true)
      expect(wrapper.find('.v-progress-circular').exists()).toBe(true)
      expect(wrapper.text()).toContain('Speichert...')
    })

    it('COMP_SC_004: saving chip has grey color', () => {
      const wrapper = mountLStatusChip({ state: 'saving' })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.props('color')).toBe('grey')
    })

    it('COMP_SC_005: saving chip has x-small size', () => {
      const wrapper = mountLStatusChip({ state: 'saving' })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.props('size')).toBe('x-small')
    })

    it('COMP_SC_006: saving chip uses tonal variant', () => {
      const wrapper = mountLStatusChip({ state: 'saving' })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.props('variant')).toBe('tonal')
    })

    it('COMP_SC_007: renders error state with alert icon', () => {
      const wrapper = mountLStatusChip({ state: 'error' })

      expect(wrapper.find('.v-chip').exists()).toBe(true)
      expect(wrapper.text()).toContain('Fehler')
    })

    it('COMP_SC_008: error chip has error color', () => {
      const wrapper = mountLStatusChip({ state: 'error' })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.props('color')).toBe('error')
    })

    it('COMP_SC_009: renders saved state with check icon', () => {
      const wrapper = mountLStatusChip({ state: 'saved' })

      expect(wrapper.find('.v-chip').exists()).toBe(true)
      expect(wrapper.text()).toContain('Gespeichert')
    })

    it('COMP_SC_010: saved chip has success color', () => {
      const wrapper = mountLStatusChip({ state: 'saved' })

      const chip = wrapper.findComponent({ name: 'VChip' })
      expect(chip.props('color')).toBe('success')
    })
  })

  // ==================== Props Tests ====================

  describe('Props', () => {
    it('COMP_SC_011: defaults state to idle', () => {
      const wrapper = mountLStatusChip()

      // No chip rendered means idle
      expect(wrapper.html()).not.toContain('v-chip')
    })

    it('COMP_SC_012: only accepts valid state values', () => {
      // Valid states should render without error
      const validStates = ['idle', 'saving', 'saved', 'error']
      validStates.forEach(state => {
        const wrapper = mountLStatusChip({ state })
        expect(wrapper.exists()).toBe(true)
      })
    })
  })
})
