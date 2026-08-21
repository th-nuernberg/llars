/**
 * LCardSkeleton Component Tests
 *
 * Tests for the LLARS card skeleton loading placeholder component.
 * Test IDs: COMP_CS_001 - COMP_CS_018
 */

import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LCardSkeleton from '@/components/common/LCardSkeleton.vue'
import LCard from '@/components/common/LCard.vue'

const vuetify = createVuetify({ components, directives })

function mountLCardSkeleton(props = {}, options = {}) {
  return mount(LCardSkeleton, {
    props,
    global: {
      plugins: [vuetify],
      components: { LCard },
      stubs: {
        LIcon: { template: '<i><slot /></i>' },
        LTag: { template: '<span><slot /></span>' }
      },
      ...options.global
    },
    ...options
  })
}

describe('LCardSkeleton', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_CS_001: renders with default props', () => {
      const wrapper = mountLCardSkeleton()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-card-skeleton').exists()).toBe(true)
    })

    it('COMP_CS_002: applies minimum height from prop', () => {
      const wrapper = mountLCardSkeleton({ minHeight: 300 })

      const style = wrapper.attributes('style') || wrapper.find('.l-card-skeleton').attributes('style')
      expect(style).toContain('min-height')
    })
  })

  // ==================== Header Section Tests ====================

  describe('Header Section', () => {
    it('COMP_CS_003: renders avatar circle by default', () => {
      const wrapper = mountLCardSkeleton({ showAvatar: true })

      expect(wrapper.find('.l-card-skeleton__block--circle').exists()).toBe(true)
    })

    it('COMP_CS_004: hides avatar when showAvatar is false', () => {
      const wrapper = mountLCardSkeleton({ showAvatar: false })

      // The circle block for avatar should not be inside the header-main
      const headerMain = wrapper.find('.l-card-skeleton__header-main')
      if (headerMain.exists()) {
        expect(headerMain.find('.l-card-skeleton__block--circle').exists()).toBe(false)
      }
    })

    it('COMP_CS_005: renders title skeleton line', () => {
      const wrapper = mountLCardSkeleton()

      expect(wrapper.find('.l-card-skeleton__titles').exists()).toBe(true)
      expect(wrapper.find('.l-card-skeleton__titles .l-card-skeleton__block--line').exists()).toBe(true)
    })

    it('COMP_CS_006: renders subtitle when showSubtitle is true (default)', () => {
      const wrapper = mountLCardSkeleton({ showSubtitle: true })

      const titles = wrapper.find('.l-card-skeleton__titles')
      const lines = titles.findAll('.l-card-skeleton__block--line')
      expect(lines.length).toBeGreaterThanOrEqual(2)
    })

    it('COMP_CS_007: hides subtitle when showSubtitle is false', () => {
      const wrapper = mountLCardSkeleton({ showSubtitle: false })

      const titles = wrapper.find('.l-card-skeleton__titles')
      const lines = titles.findAll('.l-card-skeleton__block--line')
      expect(lines).toHaveLength(1)
    })

    it('COMP_CS_008: renders status pill when showStatus is true (default)', () => {
      const wrapper = mountLCardSkeleton({ showStatus: true })

      const header = wrapper.find('.l-card-skeleton__header')
      expect(header.find('.l-card-skeleton__block--pill').exists()).toBe(true)
    })

    it('COMP_CS_009: hides status pill when showStatus is false', () => {
      const wrapper = mountLCardSkeleton({ showStatus: false })

      const header = wrapper.find('.l-card-skeleton__header')
      expect(header.find('.l-card-skeleton__block--pill').exists()).toBe(false)
    })
  })

  // ==================== Description Section Tests ====================

  describe('Description Section', () => {
    it('COMP_CS_010: renders description lines based on descriptionLines prop', () => {
      const wrapper = mountLCardSkeleton({ descriptionLines: 3 })

      const description = wrapper.find('.l-card-skeleton__description')
      expect(description.exists()).toBe(true)
      const lines = description.findAll('.l-card-skeleton__block--line')
      expect(lines).toHaveLength(3)
    })

    it('COMP_CS_011: does not render description when descriptionLines is 0', () => {
      const wrapper = mountLCardSkeleton({ descriptionLines: 0 })

      expect(wrapper.find('.l-card-skeleton__description').exists()).toBe(false)
    })
  })

  // ==================== Stats Section Tests ====================

  describe('Stats Section', () => {
    it('COMP_CS_012: renders stat blocks based on statCount', () => {
      const wrapper = mountLCardSkeleton({ statCount: 3 })

      const stats = wrapper.find('.l-card-skeleton__stats')
      expect(stats.exists()).toBe(true)
      const blocks = stats.findAll('.l-card-skeleton__block--line')
      expect(blocks).toHaveLength(3)
    })

    it('COMP_CS_013: does not render stats section when statCount is 0', () => {
      const wrapper = mountLCardSkeleton({ statCount: 0 })

      expect(wrapper.find('.l-card-skeleton__stats').exists()).toBe(false)
    })
  })

  // ==================== Tags Section Tests ====================

  describe('Tags Section', () => {
    it('COMP_CS_014: renders tag pills based on tagCount', () => {
      const wrapper = mountLCardSkeleton({ tagCount: 3 })

      const tags = wrapper.find('.l-card-skeleton__tags')
      expect(tags.exists()).toBe(true)
      const pills = tags.findAll('.l-card-skeleton__block--pill')
      expect(pills).toHaveLength(3)
    })

    it('COMP_CS_015: does not render tags section when tagCount is 0', () => {
      const wrapper = mountLCardSkeleton({ tagCount: 0 })

      expect(wrapper.find('.l-card-skeleton__tags').exists()).toBe(false)
    })
  })

  // ==================== Actions Section Tests ====================

  describe('Actions Section', () => {
    it('COMP_CS_016: renders default actions (pill + circle) when showActions is true', () => {
      const wrapper = mountLCardSkeleton({ showActions: true })

      const actions = wrapper.find('.l-card__actions')
      expect(actions.find('.l-card-skeleton__block--pill').exists()).toBe(true)
      expect(actions.find('.l-card-skeleton__block--circle').exists()).toBe(true)
    })

    it('COMP_CS_017: does not render actions when showActions is false', () => {
      const wrapper = mountLCardSkeleton({ showActions: false })

      // When showActions is false, the actions slot is not populated,
      // so LCard does not render the .l-card__actions wrapper at all
      expect(wrapper.find('.l-card__actions').exists()).toBe(false)
    })
  })

  // ==================== Compact Mode Tests ====================

  describe('Compact Mode', () => {
    it('COMP_CS_018: applies compact class when compact is true', () => {
      const wrapper = mountLCardSkeleton({ compact: true })

      expect(wrapper.find('.l-card-skeleton--compact').exists()).toBe(true)
    })
  })
})
