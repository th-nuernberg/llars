/**
 * LlarsBrand Component Tests
 *
 * Tests for the LLARS brand wordmark component. The wordmark renders the
 * mixed-case string "Llars" with CSS small-caps so the leading "L" stays full
 * height while "lars" becomes small capitals (equivalent to `\textsc{Llars}`),
 * while screen readers always announce the canonical "LLARS" via aria-label.
 *
 * Test IDs: COMP_BRAND_001 - COMP_BRAND_006
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LlarsBrand from '@/components/common/LlarsBrand.vue'

describe('LlarsBrand', () => {
  it('COMP_BRAND_001: renders the mixed-case wordmark text "Llars"', () => {
    const wrapper = mount(LlarsBrand)
    // The literal source casing is load-bearing for small-caps: one uppercase
    // "L" + lowercase "lars". Must NOT be all-caps "LLARS".
    expect(wrapper.text()).toBe('Llars')
  })

  it('COMP_BRAND_002: applies the .llars-wordmark class for small-caps styling', () => {
    const wrapper = mount(LlarsBrand)
    expect(wrapper.find('span.llars-wordmark').exists()).toBe(true)
  })

  it('COMP_BRAND_003: exposes accessible name "LLARS" by default', () => {
    const wrapper = mount(LlarsBrand)
    expect(wrapper.attributes('aria-label')).toBe('LLARS')
  })

  it('COMP_BRAND_004: allows overriding the accessible name', () => {
    const wrapper = mount(LlarsBrand, { props: { ariaLabel: 'LLARS Platform' } })
    expect(wrapper.attributes('aria-label')).toBe('LLARS Platform')
  })

  it('COMP_BRAND_005: renders a single span element with role=text', () => {
    const wrapper = mount(LlarsBrand)
    const span = wrapper.find('span')
    expect(span.exists()).toBe(true)
    expect(span.attributes('role')).toBe('text')
  })

  it('COMP_BRAND_006: never emits the all-caps brand string in visible text', () => {
    const wrapper = mount(LlarsBrand)
    expect(wrapper.text()).not.toBe('LLARS')
  })
})
