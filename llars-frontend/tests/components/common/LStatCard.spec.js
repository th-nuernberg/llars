/**
 * LStatCard Component Tests
 *
 * Tests for the LLARS statistics card component for dashboards.
 * Test IDs: COMP_STAT_001 - COMP_STAT_020
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LStatCard from '@/components/common/LStatCard.vue'

const vuetify = createVuetify({ components, directives })

function mountLStatCard(props = {}, options = {}) {
  return mount(LStatCard, {
    props: {
      value: '42',
      label: 'Test Label',
      ...props
    },
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

describe('LStatCard', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_STAT_001: renders with required props', () => {
      const wrapper = mountLStatCard()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-stat-card').exists()).toBe(true)
    })

    it('COMP_STAT_002: displays the value', () => {
      const wrapper = mountLStatCard({ value: '623' })

      expect(wrapper.find('.l-stat-card__value').text()).toBe('623')
    })

    it('COMP_STAT_003: displays the label', () => {
      const wrapper = mountLStatCard({ label: 'RAG Documents' })

      expect(wrapper.find('.l-stat-card__label').text()).toBe('RAG Documents')
    })

    it('COMP_STAT_004: renders the icon', () => {
      const wrapper = mountLStatCard({ icon: 'mdi-file-document' })

      expect(wrapper.find('.l-stat-card__icon-wrapper').exists()).toBe(true)
      expect(wrapper.find('.l-stat-card__icon-wrapper i').exists()).toBe(true)
    })

    it('COMP_STAT_005: renders accent bar at bottom', () => {
      const wrapper = mountLStatCard()

      expect(wrapper.find('.l-stat-card__accent').exists()).toBe(true)
    })

    it('COMP_STAT_006: accepts numeric value', () => {
      const wrapper = mountLStatCard({ value: 100 })

      expect(wrapper.find('.l-stat-card__value').text()).toBe('100')
    })
  })

  // ==================== Color Tests ====================

  describe('Color', () => {
    it('COMP_STAT_007: uses default color #b0ca97', () => {
      const wrapper = mountLStatCard()

      const accent = wrapper.find('.l-stat-card__accent')
      expect(accent.attributes('style')).toContain('#b0ca97')
    })

    it('COMP_STAT_008: applies custom color to icon wrapper', () => {
      const wrapper = mountLStatCard({ color: '#a8c5e2' })

      const iconWrapper = wrapper.find('.l-stat-card__icon-wrapper')
      expect(iconWrapper.attributes('style')).toContain('#a8c5e2')
    })

    it('COMP_STAT_009: applies custom color to accent bar', () => {
      const wrapper = mountLStatCard({ color: '#ff0000' })

      const accent = wrapper.find('.l-stat-card__accent')
      expect(accent.attributes('style')).toContain('#ff0000')
    })
  })

  // ==================== Trend Tests ====================

  describe('Trend', () => {
    it('COMP_STAT_010: does not render trend when not provided', () => {
      const wrapper = mountLStatCard()

      expect(wrapper.find('.l-stat-card__trend').exists()).toBe(false)
    })

    it('COMP_STAT_011: renders trend text when provided', () => {
      const wrapper = mountLStatCard({ trend: '+15%' })

      expect(wrapper.find('.l-stat-card__trend').exists()).toBe(true)
      expect(wrapper.find('.l-stat-card__trend').text()).toContain('+15%')
    })

    it('COMP_STAT_012: applies up trend class when trendUp is true', () => {
      const wrapper = mountLStatCard({ trend: '+15%', trendUp: true })

      expect(wrapper.find('.l-stat-card__trend--up').exists()).toBe(true)
      expect(wrapper.find('.l-stat-card__trend--down').exists()).toBe(false)
    })

    it('COMP_STAT_013: applies down trend class when trendUp is false', () => {
      const wrapper = mountLStatCard({ trend: '-5%', trendUp: false })

      expect(wrapper.find('.l-stat-card__trend--down').exists()).toBe(true)
      expect(wrapper.find('.l-stat-card__trend--up').exists()).toBe(false)
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_STAT_014: applies sm size class', () => {
      const wrapper = mountLStatCard({ size: 'sm' })

      expect(wrapper.classes()).toContain('l-stat-card--sm')
    })

    it('COMP_STAT_015: applies md size class by default', () => {
      const wrapper = mountLStatCard()

      expect(wrapper.classes()).toContain('l-stat-card--md')
    })

    it('COMP_STAT_016: applies lg size class', () => {
      const wrapper = mountLStatCard({ size: 'lg' })

      expect(wrapper.classes()).toContain('l-stat-card--lg')
    })
  })

  // ==================== Clickable Tests ====================

  describe('Clickable', () => {
    it('COMP_STAT_017: is not clickable by default', () => {
      const wrapper = mountLStatCard()

      expect(wrapper.classes()).not.toContain('l-stat-card--clickable')
    })

    it('COMP_STAT_018: applies clickable class when clickable is true', () => {
      const wrapper = mountLStatCard({ clickable: true })

      expect(wrapper.classes()).toContain('l-stat-card--clickable')
    })

    it('COMP_STAT_019: emits click event when clickable and clicked', async () => {
      const wrapper = mountLStatCard({ clickable: true })

      await wrapper.trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')).toHaveLength(1)
    })

    it('COMP_STAT_020: does not emit click when not clickable', async () => {
      const wrapper = mountLStatCard({ clickable: false })

      await wrapper.trigger('click')

      expect(wrapper.emitted('click')).toBeFalsy()
    })
  })
})
