/**
 * LCard Component Tests
 *
 * Tests for the LLARS card component.
 * Test IDs: COMP_CRD_001 - COMP_CRD_040
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LCard from '@/components/common/LCard.vue'
import LTag from '@/components/common/LTag.vue'

const vuetify = createVuetify({ components, directives })

function mountLCard(props = {}, options = {}) {
  return mount(LCard, {
    props,
    global: {
      plugins: [vuetify],
      components: { LTag },
      ...options.global,
    },
    slots: options.slots || {},
    ...options,
  })
}

describe('LCard', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_CRD_001: renders with default props', () => {
      const wrapper = mountLCard()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-card').exists()).toBe(true)
    })

    it('COMP_CRD_002: has LLARS card base class', () => {
      const wrapper = mountLCard()

      expect(wrapper.classes()).toContain('l-card')
    })

    it('COMP_CRD_003: renders title when provided', () => {
      const wrapper = mountLCard({ title: 'Test Card Title' })

      expect(wrapper.find('.l-card__title').exists()).toBe(true)
      expect(wrapper.find('.l-card__title').text()).toBe('Test Card Title')
    })

    it('COMP_CRD_004: renders subtitle when provided', () => {
      const wrapper = mountLCard({ title: 'Title', subtitle: 'Subtitle text' })

      expect(wrapper.find('.l-card__subtitle').exists()).toBe(true)
      expect(wrapper.find('.l-card__subtitle').text()).toBe('Subtitle text')
    })

    it('COMP_CRD_005: does not render subtitle when not provided', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__subtitle').exists()).toBe(false)
    })

    it('COMP_CRD_006: renders header section when title provided', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__header').exists()).toBe(true)
    })

    it('COMP_CRD_007: does not render header when no title and no header slot', () => {
      const wrapper = mountLCard()

      expect(wrapper.find('.l-card__header').exists()).toBe(false)
    })
  })

  // ==================== Icon & Avatar Tests ====================

  describe('Icon & Avatar', () => {
    it('COMP_CRD_008: renders avatar with icon when icon prop provided', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot' })

      expect(wrapper.find('.l-card__avatar').exists()).toBe(true)
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_CRD_009: does not render avatar when no icon provided', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__avatar').exists()).toBe(false)
    })

    it('COMP_CRD_010: applies custom avatar size', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot', avatarSize: 56 })

      const avatar = wrapper.findComponent({ name: 'v-avatar' })
      expect(avatar.props('size')).toBe(56)
    })

    it('COMP_CRD_011: uses default avatar size of 40', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot' })

      const avatar = wrapper.findComponent({ name: 'v-avatar' })
      expect(avatar.props('size')).toBe(40)
    })

    it('COMP_CRD_012: applies icon color when provided', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot', iconColor: 'black' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('color')).toBe('black')
    })

    it('COMP_CRD_013: uses white as default icon color', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot' })

      const icon = wrapper.findComponent({ name: 'v-icon' })
      expect(icon.props('color')).toBe('white')
    })
  })

  // ==================== Color & Accent Tests ====================

  describe('Color & Accent', () => {
    it('COMP_CRD_014: renders accent bar when color provided', () => {
      const wrapper = mountLCard({ color: '#b0ca97' })

      expect(wrapper.find('.l-card__accent').exists()).toBe(true)
    })

    it('COMP_CRD_015: does not render accent bar without color', () => {
      const wrapper = mountLCard()

      expect(wrapper.find('.l-card__accent').exists()).toBe(false)
    })

    it('COMP_CRD_016: applies color to accent bar', () => {
      const wrapper = mountLCard({ color: '#b0ca97' })

      const accent = wrapper.find('.l-card__accent')
      // Style can be in hex or rgb format depending on browser
      const style = accent.attributes('style')
      expect(style).toMatch(/background-color:\s*(#b0ca97|rgb\(176,\s*202,\s*151\))/)
    })

    it('COMP_CRD_017: adds has-accent class when color provided', () => {
      const wrapper = mountLCard({ color: '#b0ca97' })

      expect(wrapper.classes()).toContain('l-card--has-accent')
    })

    it('COMP_CRD_018: applies color to avatar background', () => {
      const wrapper = mountLCard({ title: 'Title', icon: 'mdi-robot', color: '#b0ca97' })

      const avatar = wrapper.findComponent({ name: 'v-avatar' })
      expect(avatar.props('color')).toBe('#b0ca97')
    })
  })

  // ==================== Status Tests ====================

  describe('Status', () => {
    it('COMP_CRD_019: renders status tag when status provided', () => {
      const wrapper = mountLCard({ title: 'Title', status: 'Active' })

      expect(wrapper.find('.l-card__status').exists()).toBe(true)
      expect(wrapper.text()).toContain('Active')
    })

    it('COMP_CRD_020: does not render status section without status', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__status').exists()).toBe(false)
    })

    it('COMP_CRD_021: applies status variant to LTag', () => {
      const wrapper = mountLCard({ title: 'Title', status: 'Success', statusVariant: 'success' })

      const tag = wrapper.findComponent(LTag)
      expect(tag.props('variant')).toBe('success')
    })

    it('COMP_CRD_022: uses gray as default status variant', () => {
      const wrapper = mountLCard({ title: 'Title', status: 'Pending' })

      const tag = wrapper.findComponent(LTag)
      expect(tag.props('variant')).toBe('gray')
    })

    it('COMP_CRD_023: validates status variant values', () => {
      const validVariants = ['primary', 'secondary', 'accent', 'success', 'info', 'warning', 'danger', 'gray']

      validVariants.forEach(variant => {
        const wrapper = mountLCard({ title: 'Title', status: 'Test', statusVariant: variant })
        const tag = wrapper.findComponent(LTag)
        expect(tag.props('variant')).toBe(variant)
      })
    })
  })

  // ==================== Stats Tests ====================

  describe('Stats', () => {
    it('COMP_CRD_024: renders stats row when stats provided', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [{ icon: 'mdi-file', value: 10, label: 'Files' }]
      })

      expect(wrapper.find('.l-card__stats').exists()).toBe(true)
    })

    it('COMP_CRD_025: does not render stats row when empty', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__stats').exists()).toBe(false)
    })

    it('COMP_CRD_026: renders multiple stats', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [
          { icon: 'mdi-file', value: 10, label: 'Files' },
          { icon: 'mdi-folder', value: 5, label: 'Folders' },
          { icon: 'mdi-message', value: 3, label: 'Messages' }
        ]
      })

      const stats = wrapper.findAll('.l-card__stat')
      expect(stats.length).toBe(3)
    })

    it('COMP_CRD_027: renders stat icon when provided', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [{ icon: 'mdi-file', value: 10, label: 'Files' }]
      })

      const stat = wrapper.find('.l-card__stat')
      expect(stat.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_CRD_028: renders stat value', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [{ value: 42, label: 'Items' }]
      })

      expect(wrapper.find('.l-card__stat-value').text()).toBe('42')
    })

    it('COMP_CRD_029: renders stat label when provided', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [{ value: 10, label: 'Documents' }]
      })

      expect(wrapper.find('.l-card__stat-label').text()).toBe('Documents')
    })

    it('COMP_CRD_030: does not render stat label when not provided', () => {
      const wrapper = mountLCard({
        title: 'Title',
        stats: [{ value: 10 }]
      })

      expect(wrapper.find('.l-card__stat-label').exists()).toBe(false)
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    it('COMP_CRD_031: applies flat class when flat is true', () => {
      const wrapper = mountLCard({ flat: true })

      expect(wrapper.classes()).toContain('l-card--flat')
    })

    it('COMP_CRD_032: does not have flat class by default', () => {
      const wrapper = mountLCard()

      expect(wrapper.classes()).not.toContain('l-card--flat')
    })

    it('COMP_CRD_033: applies outlined class when outlined is true', () => {
      const wrapper = mountLCard({ outlined: true })

      expect(wrapper.classes()).toContain('l-card--outlined')
    })

    it('COMP_CRD_034: does not have outlined class by default', () => {
      const wrapper = mountLCard()

      expect(wrapper.classes()).not.toContain('l-card--outlined')
    })
  })

  // ==================== Clickable Tests ====================

  describe('Clickable', () => {
    it('COMP_CRD_035: applies clickable class when clickable is true', () => {
      const wrapper = mountLCard({ clickable: true })

      expect(wrapper.classes()).toContain('l-card--clickable')
    })

    it('COMP_CRD_036: does not have clickable class by default', () => {
      const wrapper = mountLCard()

      expect(wrapper.classes()).not.toContain('l-card--clickable')
    })

    it('COMP_CRD_037: emits click event when clickable and clicked', async () => {
      const wrapper = mountLCard({ clickable: true })

      await wrapper.trigger('click')

      expect(wrapper.emitted('click')).toBeTruthy()
      expect(wrapper.emitted('click')).toHaveLength(1)
    })

    it('COMP_CRD_038: does not emit click event when not clickable', async () => {
      const wrapper = mountLCard({ clickable: false })

      await wrapper.trigger('click')

      expect(wrapper.emitted('click')).toBeFalsy()
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_CRD_039: renders default slot content', () => {
      const wrapper = mountLCard(
        { title: 'Title' },
        { slots: { default: '<p>Card content here</p>' } }
      )

      expect(wrapper.find('.l-card__content').exists()).toBe(true)
      expect(wrapper.find('.l-card__content').text()).toContain('Card content here')
    })

    it('COMP_CRD_040: does not render content section without default slot', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__content').exists()).toBe(false)
    })

    it('COMP_CRD_041: renders custom header slot', () => {
      const wrapper = mountLCard(
        {},
        { slots: { header: '<div class="custom-header">Custom Header</div>' } }
      )

      expect(wrapper.find('.l-card__header').exists()).toBe(true)
      expect(wrapper.find('.custom-header').exists()).toBe(true)
    })

    it('COMP_CRD_042: renders custom avatar slot', () => {
      const wrapper = mountLCard(
        { title: 'Title', icon: 'mdi-robot' },
        { slots: { avatar: '<span class="custom-avatar">AV</span>' } }
      )

      expect(wrapper.find('.custom-avatar').exists()).toBe(true)
    })

    it('COMP_CRD_043: renders custom status slot', () => {
      const wrapper = mountLCard(
        { title: 'Title' },
        { slots: { status: '<span class="custom-status">Custom Status</span>' } }
      )

      expect(wrapper.find('.l-card__status').exists()).toBe(true)
      expect(wrapper.find('.custom-status').exists()).toBe(true)
    })

    it('COMP_CRD_044: renders custom stats slot', () => {
      const wrapper = mountLCard(
        { title: 'Title' },
        { slots: { stats: '<div class="custom-stats">Custom Stats</div>' } }
      )

      expect(wrapper.find('.l-card__stats').exists()).toBe(true)
      expect(wrapper.find('.custom-stats').exists()).toBe(true)
    })

    it('COMP_CRD_045: renders tags slot', () => {
      const wrapper = mountLCard(
        { title: 'Title' },
        { slots: { tags: '<span class="tag">Tag 1</span><span class="tag">Tag 2</span>' } }
      )

      expect(wrapper.find('.l-card__tags').exists()).toBe(true)
      expect(wrapper.findAll('.tag').length).toBe(2)
    })

    it('COMP_CRD_046: does not render tags section without tags slot', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__tags').exists()).toBe(false)
    })

    it('COMP_CRD_047: renders actions slot', () => {
      const wrapper = mountLCard(
        { title: 'Title' },
        { slots: { actions: '<button class="action-btn">Edit</button>' } }
      )

      expect(wrapper.find('.l-card__actions').exists()).toBe(true)
      expect(wrapper.find('.action-btn').exists()).toBe(true)
    })

    it('COMP_CRD_048: does not render actions section without actions slot', () => {
      const wrapper = mountLCard({ title: 'Title' })

      expect(wrapper.find('.l-card__actions').exists()).toBe(false)
    })
  })

  // ==================== Complete Card Tests ====================

  describe('Complete Card', () => {
    it('COMP_CRD_049: renders complete card with all props', () => {
      const wrapper = mountLCard({
        title: 'My Chatbot',
        subtitle: 'chatbot-123',
        icon: 'mdi-robot',
        color: '#b0ca97',
        status: 'Active',
        statusVariant: 'success',
        stats: [
          { icon: 'mdi-folder', value: 3, label: 'Collections' },
          { icon: 'mdi-message', value: 12, label: 'Messages' }
        ],
        clickable: true
      }, {
        slots: {
          default: '<p>A helpful assistant</p>',
          tags: '<span>RAG</span>',
          actions: '<button>Edit</button>'
        }
      })

      // Check all sections exist
      expect(wrapper.find('.l-card__header').exists()).toBe(true)
      expect(wrapper.find('.l-card__accent').exists()).toBe(true)
      expect(wrapper.find('.l-card__avatar').exists()).toBe(true)
      expect(wrapper.find('.l-card__title').text()).toBe('My Chatbot')
      expect(wrapper.find('.l-card__subtitle').text()).toBe('chatbot-123')
      expect(wrapper.find('.l-card__status').exists()).toBe(true)
      expect(wrapper.find('.l-card__content').exists()).toBe(true)
      expect(wrapper.findAll('.l-card__stat').length).toBe(2)
      expect(wrapper.find('.l-card__tags').exists()).toBe(true)
      expect(wrapper.find('.l-card__actions').exists()).toBe(true)
      expect(wrapper.classes()).toContain('l-card--clickable')
      expect(wrapper.classes()).toContain('l-card--has-accent')
    })

    it('COMP_CRD_050: renders minimal card correctly', () => {
      const wrapper = mountLCard()

      expect(wrapper.find('.l-card').exists()).toBe(true)
      expect(wrapper.find('.l-card__header').exists()).toBe(false)
      expect(wrapper.find('.l-card__content').exists()).toBe(false)
      expect(wrapper.find('.l-card__stats').exists()).toBe(false)
      expect(wrapper.find('.l-card__actions').exists()).toBe(false)
    })
  })
})
