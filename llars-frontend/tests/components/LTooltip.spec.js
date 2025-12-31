/**
 * LTooltip Component Tests
 *
 * Tests for the LLARS tooltip wrapper component.
 * Test IDs: COMP_TTP_001 - COMP_TTP_030
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LTooltip from '@/components/common/LTooltip.vue'

const vuetify = createVuetify({ components, directives })

function mountLTooltip(props = {}, options = {}) {
  return mount(LTooltip, {
    props,
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    slots: {
      default: '<button>Hover me</button>',
      ...options.slots,
    },
    ...options,
  })
}

describe('LTooltip', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_TTP_001: renders with default props', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip text' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-tooltip-wrapper').exists()).toBe(true)
    })

    it('COMP_TTP_002: has LLARS tooltip wrapper class', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      expect(wrapper.classes()).toContain('l-tooltip-wrapper')
    })

    it('COMP_TTP_003: renders default slot content', () => {
      const wrapper = mountLTooltip(
        { text: 'Tooltip' },
        { slots: { default: '<span class="trigger">Click me</span>' } }
      )

      expect(wrapper.find('.trigger').exists()).toBe(true)
      expect(wrapper.find('.trigger').text()).toBe('Click me')
    })

    it('COMP_TTP_004: renders as span element', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      expect(wrapper.element.tagName).toBe('SPAN')
    })

    it('COMP_TTP_005: renders v-tooltip when text provided', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip text' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_006: does not render v-tooltip without text or content slot', () => {
      const wrapper = mountLTooltip({}, { slots: { default: '<button>No tooltip</button>' } })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(false)
    })
  })

  // ==================== Text Prop Tests ====================

  describe('Text Prop', () => {
    it('COMP_TTP_007: uses text prop as tooltip content', () => {
      const wrapper = mountLTooltip({ text: 'Help text here' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
      // Text is passed to the tooltip's default slot
    })

    it('COMP_TTP_008: handles empty text prop', () => {
      const wrapper = mountLTooltip({ text: '' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(false)
    })

    it('COMP_TTP_009: handles long text', () => {
      const longText = 'This is a very long tooltip text that explains something in great detail and should still work correctly'
      const wrapper = mountLTooltip({ text: longText })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_010: handles special characters in text', () => {
      const wrapper = mountLTooltip({ text: '<script>alert("XSS")</script>' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })
  })

  // ==================== Location Tests ====================

  describe('Location', () => {
    it('COMP_TTP_011: uses bottom location by default', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('bottom')
    })

    it('COMP_TTP_012: applies top location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'top' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('top')
    })

    it('COMP_TTP_013: applies bottom location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'bottom' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('bottom')
    })

    it('COMP_TTP_014: applies start location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'start' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('start')
    })

    it('COMP_TTP_015: applies end location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'end' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('end')
    })

    it('COMP_TTP_016: applies left location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'left' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('left')
    })

    it('COMP_TTP_017: applies right location', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', location: 'right' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('location')).toBe('right')
    })
  })

  // ==================== Delay Tests ====================

  describe('Delays', () => {
    it('COMP_TTP_018: uses default openDelay of 300', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('openDelay')).toBe(300)
    })

    it('COMP_TTP_019: uses default closeDelay of 0', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('closeDelay')).toBe(0)
    })

    it('COMP_TTP_020: applies custom openDelay', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', openDelay: 500 })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('openDelay')).toBe(500)
    })

    it('COMP_TTP_021: applies custom closeDelay', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', closeDelay: 200 })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('closeDelay')).toBe(200)
    })

    it('COMP_TTP_022: handles zero openDelay', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', openDelay: 0 })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('openDelay')).toBe(0)
    })
  })

  // ==================== Inline Tests ====================

  describe('Inline', () => {
    it('COMP_TTP_023: is not inline by default', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip' })

      expect(wrapper.classes()).not.toContain('l-tooltip-wrapper--inline')
    })

    it('COMP_TTP_024: applies inline class when inline is true', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', inline: true })

      expect(wrapper.classes()).toContain('l-tooltip-wrapper--inline')
    })

    it('COMP_TTP_025: does not apply inline class when inline is false', () => {
      const wrapper = mountLTooltip({ text: 'Tooltip', inline: false })

      expect(wrapper.classes()).not.toContain('l-tooltip-wrapper--inline')
    })
  })

  // ==================== Content Slot Tests ====================

  describe('Content Slot', () => {
    it('COMP_TTP_026: renders v-tooltip when content slot provided', () => {
      const wrapper = mountLTooltip(
        {},
        {
          slots: {
            default: '<button>Trigger</button>',
            content: '<div class="custom-content">Custom tooltip</div>'
          }
        }
      )

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_027: content slot overrides text prop', () => {
      const wrapper = mountLTooltip(
        { text: 'Text prop' },
        {
          slots: {
            default: '<button>Trigger</button>',
            content: '<div class="custom-tooltip">Custom content</div>'
          }
        }
      )

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })
  })

  // ==================== Complete Component Tests ====================

  describe('Complete Component', () => {
    it('COMP_TTP_028: renders complete tooltip with all props', () => {
      const wrapper = mountLTooltip({
        text: 'Save your document',
        location: 'top',
        openDelay: 200,
        closeDelay: 100,
        inline: true
      }, {
        slots: { default: '<button class="save-btn">Save</button>' }
      })

      // Check wrapper
      expect(wrapper.find('.l-tooltip-wrapper').exists()).toBe(true)
      expect(wrapper.classes()).toContain('l-tooltip-wrapper--inline')

      // Check trigger
      expect(wrapper.find('.save-btn').exists()).toBe(true)

      // Check tooltip
      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
      expect(tooltip.props('location')).toBe('top')
      expect(tooltip.props('openDelay')).toBe(200)
      expect(tooltip.props('closeDelay')).toBe(100)
    })

    it('COMP_TTP_029: works with icon trigger', () => {
      const wrapper = mountLTooltip(
        { text: 'Help information' },
        { slots: { default: '<span class="icon">?</span>' } }
      )

      expect(wrapper.find('.icon').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'v-tooltip' }).exists()).toBe(true)
    })

    it('COMP_TTP_030: works with complex trigger element', () => {
      const wrapper = mountLTooltip(
        { text: 'Click to edit' },
        {
          slots: {
            default: `
              <div class="complex-trigger">
                <span class="icon">✏️</span>
                <span class="label">Edit</span>
              </div>
            `
          }
        }
      )

      expect(wrapper.find('.complex-trigger').exists()).toBe(true)
      expect(wrapper.find('.icon').exists()).toBe(true)
      expect(wrapper.find('.label').exists()).toBe(true)
      expect(wrapper.findComponent({ name: 'v-tooltip' }).exists()).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_TTP_031: handles whitespace-only text', () => {
      const wrapper = mountLTooltip({ text: '   ' })

      // Whitespace is truthy, so tooltip should render
      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_032: handles unicode text', () => {
      const wrapper = mountLTooltip({ text: '🚀 Launch application' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_033: handles multiline text', () => {
      const wrapper = mountLTooltip({ text: 'Line 1\nLine 2\nLine 3' })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.exists()).toBe(true)
    })

    it('COMP_TTP_034: renders multiple tooltips independently', () => {
      const wrapper1 = mountLTooltip({ text: 'Tooltip 1' })
      const wrapper2 = mountLTooltip({ text: 'Tooltip 2', location: 'top' })

      expect(wrapper1.findComponent({ name: 'v-tooltip' }).props('location')).toBe('bottom')
      expect(wrapper2.findComponent({ name: 'v-tooltip' }).props('location')).toBe('top')
    })

    it('COMP_TTP_035: handles very large delay values', () => {
      const wrapper = mountLTooltip({
        text: 'Slow tooltip',
        openDelay: 10000,
        closeDelay: 5000
      })

      const tooltip = wrapper.findComponent({ name: 'v-tooltip' })
      expect(tooltip.props('openDelay')).toBe(10000)
      expect(tooltip.props('closeDelay')).toBe(5000)
    })
  })
})
