/**
 * LUserOrigin Component Tests
 *
 * Tests the "where did this user come from" origin pill.
 * Test IDs: COMP_ORIGIN_001 - COMP_ORIGIN_010
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LUserOrigin from '@/components/common/LUserOrigin.vue'

const vuetify = createVuetify({ components, directives })

function mountOrigin(props = {}) {
  return mount(LUserOrigin, {
    props,
    global: { plugins: [vuetify] }
  })
}

const referralOrigin = {
  account: 'referral',
  referral: {
    slug: 'ki-konferenz-2026',
    label: 'KI-Konferenz 2026',
    campaign: 'KI-Konferenz 2026',
    registered_at: '2026-06-03T10:00:00',
    color: '#FF6B6B'
  },
  scenario: { joined_via: 'referral_autoenroll', invited_by: null, status: 'accepted' }
}

const existingOrigin = {
  account: 'existing',
  referral: null,
  scenario: { joined_via: 'invited', invited_by: 'admin', status: 'accepted' }
}

describe('LUserOrigin', () => {
  it('COMP_ORIGIN_001: renders nothing when origin is null', () => {
    const wrapper = mountOrigin({ origin: null })
    expect(wrapper.find('.l-user-origin').exists()).toBe(false)
  })

  it('COMP_ORIGIN_002: renders a referral pill with the link label', () => {
    const wrapper = mountOrigin({ origin: referralOrigin })
    const pill = wrapper.find('.l-user-origin')
    expect(pill.exists()).toBe(true)
    expect(pill.classes()).toContain('l-user-origin--referral')
    expect(pill.text()).toContain('KI-Konferenz 2026')
  })

  it('COMP_ORIGIN_003: colors the referral pill with the link color', () => {
    const wrapper = mountOrigin({ origin: referralOrigin })
    const pill = wrapper.find('.l-user-origin')
    // jsdom may normalize the hex to rgb(); just assert a background was set.
    expect(pill.element.style.backgroundColor).toBeTruthy()
  })

  it('COMP_ORIGIN_004: renders a neutral pill for existing accounts', () => {
    const wrapper = mountOrigin({ origin: existingOrigin })
    const pill = wrapper.find('.l-user-origin')
    expect(pill.classes()).toContain('l-user-origin--existing')
    // No referral color is applied to existing-account pills.
    expect(pill.element.style.backgroundColor).toBeFalsy()
  })

  it('COMP_ORIGIN_005: dense mode shows only a color dot, no label', () => {
    const wrapper = mountOrigin({ origin: referralOrigin, dense: true })
    expect(wrapper.find('.l-user-origin__dot').exists()).toBe(true)
    expect(wrapper.find('.l-user-origin__label').exists()).toBe(false)
  })

  it('COMP_ORIGIN_006: falls back to slug when label missing', () => {
    const origin = { ...referralOrigin, referral: { ...referralOrigin.referral, label: null } }
    const wrapper = mountOrigin({ origin })
    expect(wrapper.find('.l-user-origin').text()).toContain('ki-konferenz-2026')
  })
})
