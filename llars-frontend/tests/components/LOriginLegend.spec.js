/**
 * LOriginLegend Component Tests
 *
 * Tests the color -> referral-source legend.
 * Test IDs: COMP_ORIGINLEG_001 - COMP_ORIGINLEG_010
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LOriginLegend from '@/components/common/LOriginLegend.vue'

const vuetify = createVuetify({ components, directives })

function mountLegend(props = {}) {
  return mount(LOriginLegend, {
    props,
    global: { plugins: [vuetify] }
  })
}

const ref2026 = (color) => ({
  account: 'referral',
  referral: { slug: 'ki-2026', label: 'KI-Konferenz 2026', campaign: 'KI-Konferenz 2026', color },
  scenario: { joined_via: 'self' }
})
const refFF = (color) => ({
  account: 'referral',
  referral: { slug: 'friends', label: 'Friends & Family', campaign: 'F&F', color },
  scenario: { joined_via: 'self' }
})
const existing = { account: 'existing', referral: null, scenario: { joined_via: 'invited', invited_by: 'admin' } }

describe('LOriginLegend', () => {
  it('COMP_ORIGINLEG_001: renders nothing when there are no referral sources', () => {
    const wrapper = mountLegend({ origins: [existing, existing] })
    expect(wrapper.find('.l-origin-legend').exists()).toBe(false)
  })

  it('COMP_ORIGINLEG_002: lists one item per distinct referral source', () => {
    const wrapper = mountLegend({ origins: [ref2026('#FF6B6B'), ref2026('#FF6B6B'), refFF('#4ECDC4')] })
    expect(wrapper.find('.l-origin-legend').exists()).toBe(true)
    // two distinct referral sources (KI-Konferenz appears twice but dedupes)
    const labels = wrapper.findAll('.legend-item-label').map(n => n.text())
    expect(labels).toContain('KI-Konferenz 2026')
    expect(labels).toContain('Friends & Family')
  })

  it('COMP_ORIGINLEG_003: counts members per source', () => {
    const wrapper = mountLegend({ origins: [ref2026('#FF6B6B'), ref2026('#FF6B6B'), refFF('#4ECDC4')] })
    const counts = wrapper.findAll('.legend-item-count').map(n => n.text())
    // KI-Konferenz has 2, Friends & Family has 1
    expect(counts).toContain('2')
    expect(counts).toContain('1')
  })

  it('COMP_ORIGINLEG_004: adds an existing-account bucket when present', () => {
    const wrapper = mountLegend({ origins: [ref2026('#FF6B6B'), existing] })
    expect(wrapper.find('.legend-item--existing').exists()).toBe(true)
  })

  it('COMP_ORIGINLEG_005: collapsible mode renders a toggle and hides items by default', () => {
    const wrapper = mountLegend({
      origins: [ref2026('#FF6B6B'), refFF('#4ECDC4')],
      collapsible: true,
      defaultOpen: false
    })
    expect(wrapper.find('.legend-toggle').exists()).toBe(true)
    // v-show keeps the node mounted but sets display:none when collapsed.
    expect(wrapper.find('.legend-items').element.style.display).toBe('none')
  })
})
