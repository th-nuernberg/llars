/**
 * LTabs Component Tests
 *
 * Tests for the LLARS tabs navigation component.
 * Test IDs: COMP_TAB_001 - COMP_TAB_040
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LTabs from '@/components/common/LTabs.vue'

const vuetify = createVuetify({ components, directives })

const defaultTabs = [
  { value: 'tab1', label: 'Tab One' },
  { value: 'tab2', label: 'Tab Two' },
  { value: 'tab3', label: 'Tab Three' }
]

function mountLTabs(props = {}, options = {}) {
  return mount(LTabs, {
    props: {
      tabs: defaultTabs,
      ...props,
    },
    global: {
      plugins: [vuetify],
      ...options.global,
    },
    slots: options.slots || {},
    ...options,
  })
}

describe('LTabs', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_TAB_001: renders with required props', () => {
      const wrapper = mountLTabs()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-tabs-container').exists()).toBe(true)
      expect(wrapper.find('.l-tabs').exists()).toBe(true)
    })

    it('COMP_TAB_002: renders correct number of tabs', () => {
      const wrapper = mountLTabs()

      const tabs = wrapper.findAll('.l-tab')
      expect(tabs.length).toBe(3)
    })

    it('COMP_TAB_003: renders tab labels', () => {
      const wrapper = mountLTabs()

      const labels = wrapper.findAll('.l-tab__label')
      expect(labels[0].text()).toBe('Tab One')
      expect(labels[1].text()).toBe('Tab Two')
      expect(labels[2].text()).toBe('Tab Three')
    })

    it('COMP_TAB_004: renders tabs as buttons', () => {
      const wrapper = mountLTabs()

      const tabs = wrapper.findAll('.l-tab')
      tabs.forEach(tab => {
        expect(tab.element.tagName).toBe('BUTTON')
      })
    })

    it('COMP_TAB_005: has LLARS tabs container class', () => {
      const wrapper = mountLTabs()

      expect(wrapper.find('.l-tabs-container').exists()).toBe(true)
    })
  })

  // ==================== Active State Tests ====================

  describe('Active State', () => {
    it('COMP_TAB_006: first tab active by default with index modelValue', () => {
      const wrapper = mountLTabs({ modelValue: 0, tabs: [
        { label: 'First' },
        { label: 'Second' }
      ]})

      const tabs = wrapper.findAll('.l-tab')
      expect(tabs[0].classes()).toContain('l-tab--active')
      expect(tabs[1].classes()).not.toContain('l-tab--active')
    })

    it('COMP_TAB_007: correct tab active with string modelValue', () => {
      const wrapper = mountLTabs({ modelValue: 'tab2' })

      const tabs = wrapper.findAll('.l-tab')
      expect(tabs[0].classes()).not.toContain('l-tab--active')
      expect(tabs[1].classes()).toContain('l-tab--active')
      expect(tabs[2].classes()).not.toContain('l-tab--active')
    })

    it('COMP_TAB_008: correct tab active with numeric modelValue', () => {
      const wrapper = mountLTabs({
        modelValue: 1,
        tabs: [
          { value: 0, label: 'First' },
          { value: 1, label: 'Second' },
          { value: 2, label: 'Third' }
        ]
      })

      const tabs = wrapper.findAll('.l-tab')
      expect(tabs[1].classes()).toContain('l-tab--active')
    })

    it('COMP_TAB_009: updates active tab when modelValue changes', async () => {
      const wrapper = mountLTabs({ modelValue: 'tab1' })

      expect(wrapper.findAll('.l-tab')[0].classes()).toContain('l-tab--active')

      await wrapper.setProps({ modelValue: 'tab3' })

      expect(wrapper.findAll('.l-tab')[0].classes()).not.toContain('l-tab--active')
      expect(wrapper.findAll('.l-tab')[2].classes()).toContain('l-tab--active')
    })
  })

  // ==================== Tab Selection Tests ====================

  describe('Tab Selection', () => {
    it('COMP_TAB_010: emits update:modelValue on tab click', async () => {
      const wrapper = mountLTabs({ modelValue: 'tab1' })

      await wrapper.findAll('.l-tab')[1].trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['tab2'])
    })

    it('COMP_TAB_011: emits correct value for each tab', async () => {
      const wrapper = mountLTabs({ modelValue: 'tab1' })
      const tabs = wrapper.findAll('.l-tab')

      await tabs[0].trigger('click')
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['tab1'])

      await tabs[1].trigger('click')
      expect(wrapper.emitted('update:modelValue')[1]).toEqual(['tab2'])

      await tabs[2].trigger('click')
      expect(wrapper.emitted('update:modelValue')[2]).toEqual(['tab3'])
    })

    it('COMP_TAB_012: uses index when tab has no value', async () => {
      const wrapper = mountLTabs({
        modelValue: 0,
        tabs: [
          { label: 'First' },
          { label: 'Second' }
        ]
      })

      await wrapper.findAll('.l-tab')[1].trigger('click')

      expect(wrapper.emitted('update:modelValue')[0]).toEqual([1])
    })
  })

  // ==================== Icon Tests ====================

  describe('Icons', () => {
    it('COMP_TAB_013: renders icon when provided', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', icon: 'mdi-home' },
          { value: 'tab2', label: 'Tab Two' }
        ]
      })

      const icons = wrapper.findAll('.l-tab__icon')
      expect(icons.length).toBe(1)
    })

    it('COMP_TAB_014: does not render icon when not provided', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One' }
        ]
      })

      expect(wrapper.find('.l-tab__icon').exists()).toBe(false)
    })

    it('COMP_TAB_015: renders correct icon content', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', icon: 'mdi-robot' }
        ]
      })

      const icon = wrapper.find('.v-icon')
      expect(icon.exists()).toBe(true)
    })

    it('COMP_TAB_016: renders icons for multiple tabs', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', icon: 'mdi-home' },
          { value: 'tab2', label: 'Tab Two', icon: 'mdi-cog' },
          { value: 'tab3', label: 'Tab Three', icon: 'mdi-account' }
        ]
      })

      const icons = wrapper.findAll('.l-tab__icon')
      expect(icons.length).toBe(3)
    })
  })

  // ==================== Badge Tests ====================

  describe('Badges', () => {
    it('COMP_TAB_017: renders badge when provided', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', badge: 5 }
        ]
      })

      expect(wrapper.find('.l-tab__badge').exists()).toBe(true)
      expect(wrapper.find('.l-tab__badge').text()).toBe('5')
    })

    it('COMP_TAB_018: does not render badge when not provided', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One' }
        ]
      })

      expect(wrapper.find('.l-tab__badge').exists()).toBe(false)
    })

    it('COMP_TAB_019: renders badge with zero value', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', badge: 0 }
        ]
      })

      expect(wrapper.find('.l-tab__badge').exists()).toBe(true)
      expect(wrapper.find('.l-tab__badge').text()).toBe('0')
    })

    it('COMP_TAB_020: renders string badge', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', badge: 'NEW' }
        ]
      })

      expect(wrapper.find('.l-tab__badge').text()).toBe('NEW')
    })

    it('COMP_TAB_021: renders badges on multiple tabs', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab One', badge: 3 },
          { value: 'tab2', label: 'Tab Two' },
          { value: 'tab3', label: 'Tab Three', badge: 10 }
        ]
      })

      const badges = wrapper.findAll('.l-tab__badge')
      expect(badges.length).toBe(2)
    })
  })

  // ==================== Variant Tests ====================

  describe('Variants', () => {
    it('COMP_TAB_022: uses filled variant by default', () => {
      const wrapper = mountLTabs()

      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--filled')
    })

    it('COMP_TAB_023: applies filled variant class', () => {
      const wrapper = mountLTabs({ variant: 'filled' })

      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--filled')
    })

    it('COMP_TAB_024: applies outlined variant class', () => {
      const wrapper = mountLTabs({ variant: 'outlined' })

      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--outlined')
    })

    it('COMP_TAB_025: applies underlined variant class', () => {
      const wrapper = mountLTabs({ variant: 'underlined' })

      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--underlined')
    })

    it('COMP_TAB_026: only one variant class at a time', () => {
      const wrapper = mountLTabs({ variant: 'outlined' })

      const tabsClasses = wrapper.find('.l-tabs').classes()
      expect(tabsClasses).toContain('l-tabs--outlined')
      expect(tabsClasses).not.toContain('l-tabs--filled')
      expect(tabsClasses).not.toContain('l-tabs--underlined')
    })
  })

  // ==================== Grow Tests ====================

  describe('Grow', () => {
    it('COMP_TAB_027: does not have grow class by default', () => {
      const wrapper = mountLTabs()

      expect(wrapper.find('.l-tabs').classes()).not.toContain('l-tabs--grow')
    })

    it('COMP_TAB_028: applies grow class when grow is true', () => {
      const wrapper = mountLTabs({ grow: true })

      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--grow')
    })

    it('COMP_TAB_029: does not apply grow class when grow is false', () => {
      const wrapper = mountLTabs({ grow: false })

      expect(wrapper.find('.l-tabs').classes()).not.toContain('l-tabs--grow')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_TAB_030: renders default slot content', () => {
      const wrapper = mountLTabs(
        {},
        { slots: { default: '<div class="custom-content">Tab Content</div>' } }
      )

      expect(wrapper.find('.l-tabs-content').exists()).toBe(true)
      expect(wrapper.find('.custom-content').exists()).toBe(true)
      expect(wrapper.find('.custom-content').text()).toBe('Tab Content')
    })

    it('COMP_TAB_031: does not render content area without slot', () => {
      const wrapper = mountLTabs()

      expect(wrapper.find('.l-tabs-content').exists()).toBe(false)
    })
  })

  // ==================== Complete Tab Tests ====================

  describe('Complete Tabs', () => {
    it('COMP_TAB_032: renders complete tabs with all features', () => {
      const wrapper = mountLTabs({
        modelValue: 'collections',
        tabs: [
          { value: 'chatbots', label: 'Chatbots', icon: 'mdi-robot' },
          { value: 'collections', label: 'Collections', icon: 'mdi-folder-multiple', badge: 5 },
          { value: 'documents', label: 'Documents', icon: 'mdi-file-document', badge: 12 }
        ],
        variant: 'filled',
        grow: true
      }, {
        slots: { default: '<div class="tab-panel">Panel Content</div>' }
      })

      // Check structure
      expect(wrapper.find('.l-tabs-container').exists()).toBe(true)
      expect(wrapper.find('.l-tabs').exists()).toBe(true)
      expect(wrapper.findAll('.l-tab').length).toBe(3)

      // Check active tab
      expect(wrapper.findAll('.l-tab')[1].classes()).toContain('l-tab--active')

      // Check icons
      expect(wrapper.findAll('.l-tab__icon').length).toBe(3)

      // Check badges
      expect(wrapper.findAll('.l-tab__badge').length).toBe(2)

      // Check classes
      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--filled')
      expect(wrapper.find('.l-tabs').classes()).toContain('l-tabs--grow')

      // Check content
      expect(wrapper.find('.l-tabs-content').exists()).toBe(true)
      expect(wrapper.find('.tab-panel').exists()).toBe(true)
    })

    it('COMP_TAB_033: handles tab switching correctly', async () => {
      const wrapper = mountLTabs({
        modelValue: 'tab1',
        tabs: [
          { value: 'tab1', label: 'First', icon: 'mdi-numeric-1' },
          { value: 'tab2', label: 'Second', icon: 'mdi-numeric-2' },
          { value: 'tab3', label: 'Third', icon: 'mdi-numeric-3' }
        ]
      })

      const tabs = wrapper.findAll('.l-tab')

      // Initial state
      expect(tabs[0].classes()).toContain('l-tab--active')

      // Click second tab
      await tabs[1].trigger('click')
      expect(wrapper.emitted('update:modelValue')[0]).toEqual(['tab2'])

      // Update modelValue
      await wrapper.setProps({ modelValue: 'tab2' })
      expect(tabs[0].classes()).not.toContain('l-tab--active')
      expect(tabs[1].classes()).toContain('l-tab--active')

      // Click third tab
      await tabs[2].trigger('click')
      expect(wrapper.emitted('update:modelValue')[1]).toEqual(['tab3'])
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_TAB_034: handles single tab', () => {
      const wrapper = mountLTabs({
        tabs: [{ value: 'only', label: 'Only Tab' }]
      })

      expect(wrapper.findAll('.l-tab').length).toBe(1)
    })

    it('COMP_TAB_035: handles many tabs', () => {
      const manyTabs = Array.from({ length: 10 }, (_, i) => ({
        value: `tab${i}`,
        label: `Tab ${i + 1}`
      }))

      const wrapper = mountLTabs({ tabs: manyTabs })

      expect(wrapper.findAll('.l-tab').length).toBe(10)
    })

    it('COMP_TAB_036: handles falsy value by using index', () => {
      // When tab.value is falsy (empty string), component uses index instead
      const wrapper = mountLTabs({
        modelValue: 0,
        tabs: [
          { value: '', label: 'Empty Value' },
          { value: 'other', label: 'Other' }
        ]
      })

      // First tab (index 0) should be active since empty string falls back to index
      expect(wrapper.findAll('.l-tab')[0].classes()).toContain('l-tab--active')
    })

    it('COMP_TAB_037: handles tab with icon and badge together', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Complete', icon: 'mdi-star', badge: 99 }
        ]
      })

      const tab = wrapper.find('.l-tab')
      expect(tab.find('.l-tab__icon').exists()).toBe(true)
      expect(tab.find('.l-tab__label').exists()).toBe(true)
      expect(tab.find('.l-tab__badge').exists()).toBe(true)
    })

    it('COMP_TAB_038: preserves tab order', () => {
      const orderedTabs = [
        { value: 'z', label: 'Zebra' },
        { value: 'a', label: 'Apple' },
        { value: 'm', label: 'Mango' }
      ]

      const wrapper = mountLTabs({ tabs: orderedTabs })
      const labels = wrapper.findAll('.l-tab__label')

      expect(labels[0].text()).toBe('Zebra')
      expect(labels[1].text()).toBe('Apple')
      expect(labels[2].text()).toBe('Mango')
    })

    it('COMP_TAB_039: handles special characters in labels', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Tab & More' },
          { value: 'tab2', label: '<Script>' },
          { value: 'tab3', label: 'Übersicht' }
        ]
      })

      const labels = wrapper.findAll('.l-tab__label')
      expect(labels[0].text()).toBe('Tab & More')
      expect(labels[1].text()).toBe('<Script>')
      expect(labels[2].text()).toBe('Übersicht')
    })

    it('COMP_TAB_040: handles large badge numbers', () => {
      const wrapper = mountLTabs({
        tabs: [
          { value: 'tab1', label: 'Notifications', badge: 9999 }
        ]
      })

      expect(wrapper.find('.l-tab__badge').text()).toBe('9999')
    })
  })
})
