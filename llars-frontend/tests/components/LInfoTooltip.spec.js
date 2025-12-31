/**
 * LInfoTooltip Component Tests
 *
 * Tests for the LLARS info tooltip component with icon button trigger.
 * Test IDs: COMP_ITT_001 - COMP_ITT_040
 *
 * Coverage:
 * - Rendering and structure
 * - Icon prop and sizes
 * - Title and text props
 * - Slot content
 * - Location prop
 * - maxWidth prop
 * - Accessibility (aria-label)
 * - Edge cases
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LInfoTooltip from '@/components/common/LInfoTooltip.vue'

function mountLInfoTooltip(props = {}, options = {}) {
  return mount(LInfoTooltip, {
    props,
    global: {
      stubs: {
        'v-tooltip': {
          template: `
            <div class="v-tooltip" :location="location">
              <slot name="activator" :props="{}"></slot>
              <div class="v-tooltip-content"><slot></slot></div>
            </div>
          `,
          props: ['location']
        },
        'v-btn': {
          template: `
            <button
              class="v-btn l-info-tooltip__btn"
              :class="[variant, size]"
              :aria-label="ariaLabel"
            >
              <slot></slot>
            </button>
          `,
          props: ['variant', 'size', 'ariaLabel']
        },
        'v-icon': {
          template: '<i class="v-icon" :style="{ fontSize: size + \'px\' }"><slot />{{ icon }}</i>',
          props: ['icon', 'size']
        }
      }
    },
    ...options
  })
}

describe('LInfoTooltip', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_ITT_001: renders with default props', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.v-tooltip').exists()).toBe(true)
    })

    it('COMP_ITT_002: renders button trigger', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__btn').exists()).toBe(true)
    })

    it('COMP_ITT_003: renders icon in button', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_ITT_004: renders tooltip content area', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__content').exists()).toBe(true)
    })

    it('COMP_ITT_005: renders text area', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__text').exists()).toBe(true)
    })
  })

  // ==================== Icon Tests ====================

  describe('Icon', () => {
    it('COMP_ITT_006: uses default info icon', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.v-icon').text()).toContain('mdi-information-outline')
    })

    it('COMP_ITT_007: uses custom icon when provided', () => {
      const wrapper = mountLInfoTooltip({ icon: 'mdi-help-circle' })

      expect(wrapper.find('.v-icon').text()).toContain('mdi-help-circle')
    })

    it('COMP_ITT_008: icon changes reactively', async () => {
      const wrapper = mountLInfoTooltip({ icon: 'mdi-alert' })

      expect(wrapper.find('.v-icon').text()).toContain('mdi-alert')

      await wrapper.setProps({ icon: 'mdi-lightbulb' })

      expect(wrapper.find('.v-icon').text()).toContain('mdi-lightbulb')
    })
  })

  // ==================== Size Tests ====================

  describe('Sizes', () => {
    it('COMP_ITT_009: uses small size by default', () => {
      const wrapper = mountLInfoTooltip()
      const btn = wrapper.find('.l-info-tooltip__btn')

      expect(btn.classes()).toContain('small')
    })

    it('COMP_ITT_010: accepts x-small size', () => {
      const wrapper = mountLInfoTooltip({ size: 'x-small' })

      expect(wrapper.find('.l-info-tooltip__btn').classes()).toContain('x-small')
    })

    it('COMP_ITT_011: accepts default size', () => {
      const wrapper = mountLInfoTooltip({ size: 'default' })

      expect(wrapper.find('.l-info-tooltip__btn').classes()).toContain('default')
    })

    it('COMP_ITT_012: accepts large size', () => {
      const wrapper = mountLInfoTooltip({ size: 'large' })

      expect(wrapper.find('.l-info-tooltip__btn').classes()).toContain('large')
    })

    it('COMP_ITT_013: accepts x-large size', () => {
      const wrapper = mountLInfoTooltip({ size: 'x-large' })

      expect(wrapper.find('.l-info-tooltip__btn').classes()).toContain('x-large')
    })

    it('COMP_ITT_014: maps x-small to 14px icon', () => {
      const wrapper = mountLInfoTooltip({ size: 'x-small' })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('14px')
    })

    it('COMP_ITT_015: maps small to 18px icon', () => {
      const wrapper = mountLInfoTooltip({ size: 'small' })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('18px')
    })

    it('COMP_ITT_016: maps default to 20px icon', () => {
      const wrapper = mountLInfoTooltip({ size: 'default' })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('20px')
    })

    it('COMP_ITT_017: maps large to 24px icon', () => {
      const wrapper = mountLInfoTooltip({ size: 'large' })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('24px')
    })

    it('COMP_ITT_018: maps x-large to 28px icon', () => {
      const wrapper = mountLInfoTooltip({ size: 'x-large' })

      expect(wrapper.find('.v-icon').attributes('style')).toContain('28px')
    })
  })

  // ==================== Title Tests ====================

  describe('Title', () => {
    it('COMP_ITT_019: does not render title by default', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__title').exists()).toBe(false)
    })

    it('COMP_ITT_020: renders title when provided', () => {
      const wrapper = mountLInfoTooltip({ title: 'Important Info' })

      expect(wrapper.find('.l-info-tooltip__title').exists()).toBe(true)
      expect(wrapper.find('.l-info-tooltip__title').text()).toBe('Important Info')
    })

    it('COMP_ITT_021: does not render title when empty string', () => {
      const wrapper = mountLInfoTooltip({ title: '' })

      expect(wrapper.find('.l-info-tooltip__title').exists()).toBe(false)
    })
  })

  // ==================== Text Tests ====================

  describe('Text', () => {
    it('COMP_ITT_022: renders text prop', () => {
      const wrapper = mountLInfoTooltip({ text: 'This is helpful info' })

      expect(wrapper.find('.l-info-tooltip__text').text()).toBe('This is helpful info')
    })

    it('COMP_ITT_023: renders empty when no text', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__text').text()).toBe('')
    })

    it('COMP_ITT_024: handles multiline text', () => {
      const wrapper = mountLInfoTooltip({ text: 'Line 1\nLine 2' })

      expect(wrapper.find('.l-info-tooltip__text').text()).toBe('Line 1\nLine 2')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slot', () => {
    it('COMP_ITT_025: uses slot content over text prop', () => {
      const wrapper = mountLInfoTooltip(
        { text: 'Prop text' },
        {
          slots: {
            default: 'Slot content'
          }
        }
      )

      expect(wrapper.find('.l-info-tooltip__text').text()).toBe('Slot content')
    })

    it('COMP_ITT_026: slot can contain HTML', () => {
      const wrapper = mountLInfoTooltip({}, {
        slots: {
          default: '<ul><li>Item 1</li></ul>'
        }
      })

      expect(wrapper.find('.l-info-tooltip__text ul').exists()).toBe(true)
    })

    it('COMP_ITT_027: text prop is used when no slot', () => {
      const wrapper = mountLInfoTooltip({ text: 'Fallback text' })

      expect(wrapper.find('.l-info-tooltip__text span').text()).toBe('Fallback text')
    })
  })

  // ==================== Location Tests ====================

  describe('Location', () => {
    it('COMP_ITT_028: uses bottom location by default', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.v-tooltip').attributes('location')).toBe('bottom')
    })

    it('COMP_ITT_029: accepts top location', () => {
      const wrapper = mountLInfoTooltip({ location: 'top' })

      expect(wrapper.find('.v-tooltip').attributes('location')).toBe('top')
    })

    it('COMP_ITT_030: accepts left location', () => {
      const wrapper = mountLInfoTooltip({ location: 'left' })

      expect(wrapper.find('.v-tooltip').attributes('location')).toBe('left')
    })

    it('COMP_ITT_031: accepts right location', () => {
      const wrapper = mountLInfoTooltip({ location: 'right' })

      expect(wrapper.find('.v-tooltip').attributes('location')).toBe('right')
    })
  })

  // ==================== maxWidth Tests ====================

  describe('maxWidth', () => {
    it('COMP_ITT_032: applies default maxWidth of 360px', () => {
      const wrapper = mountLInfoTooltip()
      const style = wrapper.find('.l-info-tooltip__content').attributes('style')

      expect(style).toContain('max-width: 360px')
    })

    it('COMP_ITT_033: accepts number maxWidth', () => {
      const wrapper = mountLInfoTooltip({ maxWidth: 500 })
      const style = wrapper.find('.l-info-tooltip__content').attributes('style')

      expect(style).toContain('max-width: 500px')
    })

    it('COMP_ITT_034: accepts string maxWidth', () => {
      const wrapper = mountLInfoTooltip({ maxWidth: '80vw' })
      const style = wrapper.find('.l-info-tooltip__content').attributes('style')

      expect(style).toContain('max-width: 80vw')
    })

    it('COMP_ITT_035: handles null maxWidth', () => {
      const wrapper = mountLInfoTooltip({ maxWidth: null })
      const style = wrapper.find('.l-info-tooltip__content').attributes('style')

      expect(style).toBeUndefined()
    })
  })

  // ==================== Accessibility Tests ====================

  describe('Accessibility', () => {
    it('COMP_ITT_036: uses ariaLabel prop when provided', () => {
      const wrapper = mountLInfoTooltip({ ariaLabel: 'More information' })

      expect(wrapper.find('.l-info-tooltip__btn').attributes('aria-label')).toBe('More information')
    })

    it('COMP_ITT_037: falls back to title for aria-label', () => {
      const wrapper = mountLInfoTooltip({ title: 'Help Title' })

      expect(wrapper.find('.l-info-tooltip__btn').attributes('aria-label')).toBe('Help Title')
    })

    it('COMP_ITT_038: uses "Info" as default aria-label', () => {
      const wrapper = mountLInfoTooltip()

      expect(wrapper.find('.l-info-tooltip__btn').attributes('aria-label')).toBe('Info')
    })

    it('COMP_ITT_039: ariaLabel takes precedence over title', () => {
      const wrapper = mountLInfoTooltip({
        title: 'Title',
        ariaLabel: 'Custom Label'
      })

      expect(wrapper.find('.l-info-tooltip__btn').attributes('aria-label')).toBe('Custom Label')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_ITT_040: component works without any props', () => {
      const wrapper = mount(LInfoTooltip, {
        global: {
          stubs: {
            'v-tooltip': {
              template: '<div class="v-tooltip"><slot name="activator" :props="{}"></slot><slot></slot></div>'
            },
            'v-btn': {
              template: '<button class="v-btn l-info-tooltip__btn"><slot></slot></button>'
            },
            'v-icon': {
              template: '<i class="v-icon">{{ icon }}</i>',
              props: ['icon', 'size']
            }
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-info-tooltip__btn').exists()).toBe(true)
    })
  })
})
