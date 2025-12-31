/**
 * LActionGroup Component Tests
 *
 * Tests for the LLARS action button group component.
 * Test IDs: COMP_ACT_001 - COMP_ACT_045
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LActionGroup from '@/components/common/LActionGroup.vue'
import LIconBtn from '@/components/common/LIconBtn.vue'

const vuetify = createVuetify({ components, directives })

function mountLActionGroup(props = {}, options = {}) {
  return mount(LActionGroup, {
    props: {
      actions: ['view', 'edit', 'delete'],
      ...props,
    },
    global: {
      plugins: [vuetify],
      components: { LIconBtn },
      ...options.global,
    },
    slots: options.slots || {},
    ...options,
  })
}

describe('LActionGroup', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_ACT_001: renders with required props', () => {
      const wrapper = mountLActionGroup()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-action-group').exists()).toBe(true)
    })

    it('COMP_ACT_002: has LLARS action group base class', () => {
      const wrapper = mountLActionGroup()

      expect(wrapper.classes()).toContain('l-action-group')
    })

    it('COMP_ACT_003: renders correct number of action buttons', () => {
      const wrapper = mountLActionGroup({ actions: ['view', 'edit', 'delete'] })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons.length).toBe(3)
    })

    it('COMP_ACT_004: renders single action', () => {
      const wrapper = mountLActionGroup({ actions: ['view'] })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons.length).toBe(1)
    })

    it('COMP_ACT_005: renders many actions', () => {
      const wrapper = mountLActionGroup({
        actions: ['view', 'edit', 'delete', 'copy', 'download', 'stats']
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons.length).toBe(6)
    })
  })

  // ==================== Preset Actions Tests ====================

  describe('Preset Actions', () => {
    it('COMP_ACT_006: resolves view preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['view'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-eye')
      expect(button.props('tooltip')).toBe('Anzeigen')
    })

    it('COMP_ACT_007: resolves edit preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['edit'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-pencil')
      expect(button.props('tooltip')).toBe('Bearbeiten')
    })

    it('COMP_ACT_008: resolves delete preset with danger variant', () => {
      const wrapper = mountLActionGroup({ actions: ['delete'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-delete')
      expect(button.props('tooltip')).toBe('Löschen')
      expect(button.props('variant')).toBe('danger')
    })

    it('COMP_ACT_009: resolves stats preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['stats'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-chart-bar')
      expect(button.props('tooltip')).toBe('Statistiken')
    })

    it('COMP_ACT_010: resolves download preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['download'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-download')
      expect(button.props('tooltip')).toBe('Herunterladen')
    })

    it('COMP_ACT_011: resolves copy preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['copy'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-content-copy')
      expect(button.props('tooltip')).toBe('Kopieren')
    })

    it('COMP_ACT_012: resolves lock preset with warning variant', () => {
      const wrapper = mountLActionGroup({ actions: ['lock'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-lock')
      expect(button.props('variant')).toBe('warning')
    })

    it('COMP_ACT_013: resolves unlock preset with success variant', () => {
      const wrapper = mountLActionGroup({ actions: ['unlock'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-lock-open-variant')
      expect(button.props('variant')).toBe('success')
    })

    it('COMP_ACT_014: resolves refresh preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['refresh'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-refresh')
    })

    it('COMP_ACT_015: resolves close preset correctly', () => {
      const wrapper = mountLActionGroup({ actions: ['close'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-close')
    })

    it('COMP_ACT_016: resolves add preset with success variant', () => {
      const wrapper = mountLActionGroup({ actions: ['add'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-plus')
      expect(button.props('variant')).toBe('success')
    })

    it('COMP_ACT_017: resolves play preset with success variant', () => {
      const wrapper = mountLActionGroup({ actions: ['play'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-play')
      expect(button.props('variant')).toBe('success')
    })

    it('COMP_ACT_018: resolves pause preset with warning variant', () => {
      const wrapper = mountLActionGroup({ actions: ['pause'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-pause')
      expect(button.props('variant')).toBe('warning')
    })

    it('COMP_ACT_019: resolves stop preset with danger variant', () => {
      const wrapper = mountLActionGroup({ actions: ['stop'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-stop')
      expect(button.props('variant')).toBe('danger')
    })
  })

  // ==================== Custom Actions Tests ====================

  describe('Custom Actions', () => {
    it('COMP_ACT_020: renders custom action object', () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'custom', icon: 'mdi-star', tooltip: 'Favorit' }]
      })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-star')
      expect(button.props('tooltip')).toBe('Favorit')
    })

    it('COMP_ACT_021: applies custom variant', () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'custom', icon: 'mdi-star', variant: 'primary' }]
      })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('variant')).toBe('primary')
    })

    it('COMP_ACT_022: handles loading state on custom action', () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'custom', icon: 'mdi-sync', loading: true }]
      })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('loading')).toBe(true)
    })

    it('COMP_ACT_023: handles disabled state on custom action', () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'custom', icon: 'mdi-block', disabled: true }]
      })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('disabled')).toBe(true)
    })

    it('COMP_ACT_024: mixes presets and custom actions', () => {
      const wrapper = mountLActionGroup({
        actions: [
          'view',
          { key: 'custom', icon: 'mdi-star', tooltip: 'Favorit' },
          'delete'
        ]
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons.length).toBe(3)
      expect(buttons[0].props('icon')).toBe('mdi-eye')
      expect(buttons[1].props('icon')).toBe('mdi-star')
      expect(buttons[2].props('icon')).toBe('mdi-delete')
    })

    it('COMP_ACT_025: uses default icon for custom action without icon', () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'custom', tooltip: 'Custom action' }]
      })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-circle')
    })
  })

  // ==================== Size Tests ====================

  describe('Size', () => {
    it('COMP_ACT_026: uses small size by default', () => {
      const wrapper = mountLActionGroup()

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('size')).toBe('small')
    })

    it('COMP_ACT_027: applies x-small size', () => {
      const wrapper = mountLActionGroup({ size: 'x-small' })

      const buttons = wrapper.findAllComponents(LIconBtn)
      buttons.forEach(button => {
        expect(button.props('size')).toBe('x-small')
      })
    })

    it('COMP_ACT_028: applies default size', () => {
      const wrapper = mountLActionGroup({ size: 'default' })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('size')).toBe('default')
    })

    it('COMP_ACT_029: applies large size', () => {
      const wrapper = mountLActionGroup({ size: 'large' })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('size')).toBe('large')
    })

    it('COMP_ACT_030: applies size to all buttons', () => {
      const wrapper = mountLActionGroup({
        actions: ['view', 'edit', 'delete'],
        size: 'large'
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      buttons.forEach(button => {
        expect(button.props('size')).toBe('large')
      })
    })
  })

  // ==================== Gap Tests ====================

  describe('Gap', () => {
    it('COMP_ACT_031: uses sm gap by default', () => {
      const wrapper = mountLActionGroup()

      expect(wrapper.classes()).toContain('l-action-group--gap-sm')
    })

    it('COMP_ACT_032: applies none gap', () => {
      const wrapper = mountLActionGroup({ gap: 'none' })

      expect(wrapper.classes()).toContain('l-action-group--gap-none')
    })

    it('COMP_ACT_033: applies xs gap', () => {
      const wrapper = mountLActionGroup({ gap: 'xs' })

      expect(wrapper.classes()).toContain('l-action-group--gap-xs')
    })

    it('COMP_ACT_034: applies md gap', () => {
      const wrapper = mountLActionGroup({ gap: 'md' })

      expect(wrapper.classes()).toContain('l-action-group--gap-md')
    })

    it('COMP_ACT_035: applies lg gap', () => {
      const wrapper = mountLActionGroup({ gap: 'lg' })

      expect(wrapper.classes()).toContain('l-action-group--gap-lg')
    })
  })

  // ==================== Align Tests ====================

  describe('Align', () => {
    it('COMP_ACT_036: uses end alignment by default', () => {
      const wrapper = mountLActionGroup()

      expect(wrapper.classes()).toContain('l-action-group--align-end')
    })

    it('COMP_ACT_037: applies start alignment', () => {
      const wrapper = mountLActionGroup({ align: 'start' })

      expect(wrapper.classes()).toContain('l-action-group--align-start')
    })

    it('COMP_ACT_038: applies center alignment', () => {
      const wrapper = mountLActionGroup({ align: 'center' })

      expect(wrapper.classes()).toContain('l-action-group--align-center')
    })
  })

  // ==================== Event Tests ====================

  describe('Events', () => {
    it('COMP_ACT_039: emits action event on button click', async () => {
      const wrapper = mountLActionGroup({ actions: ['view'] })

      const button = wrapper.findComponent(LIconBtn)
      await button.trigger('click')

      expect(wrapper.emitted('action')).toBeTruthy()
      expect(wrapper.emitted('action')[0][0]).toBe('view')
    })

    it('COMP_ACT_040: emits correct key for each action', async () => {
      const wrapper = mountLActionGroup({ actions: ['view', 'edit', 'delete'] })

      const buttons = wrapper.findAllComponents(LIconBtn)

      await buttons[0].trigger('click')
      expect(wrapper.emitted('action')[0][0]).toBe('view')

      await buttons[1].trigger('click')
      expect(wrapper.emitted('action')[1][0]).toBe('edit')

      await buttons[2].trigger('click')
      expect(wrapper.emitted('action')[2][0]).toBe('delete')
    })

    it('COMP_ACT_041: emits action object as second parameter', async () => {
      const wrapper = mountLActionGroup({ actions: ['delete'] })

      const button = wrapper.findComponent(LIconBtn)
      await button.trigger('click')

      const emitted = wrapper.emitted('action')[0]
      expect(emitted[0]).toBe('delete')
      expect(emitted[1]).toMatchObject({
        key: 'delete',
        icon: 'mdi-delete',
        variant: 'danger'
      })
    })

    it('COMP_ACT_042: emits custom action key', async () => {
      const wrapper = mountLActionGroup({
        actions: [{ key: 'favorite', icon: 'mdi-star' }]
      })

      const button = wrapper.findComponent(LIconBtn)
      await button.trigger('click')

      expect(wrapper.emitted('action')[0][0]).toBe('favorite')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_ACT_043: renders named slot instead of button', () => {
      const wrapper = mountLActionGroup(
        { actions: ['edit', 'delete'] },
        {
          slots: {
            edit: '<button class="custom-edit">Custom Edit</button>'
          }
        }
      )

      // Custom slot should be rendered
      expect(wrapper.find('.custom-edit').exists()).toBe(true)

      // Only one LIconBtn (for delete), edit is replaced by slot
      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons.length).toBe(1)
      expect(buttons[0].props('icon')).toBe('mdi-delete')
    })

    it('COMP_ACT_044: slot receives action prop', () => {
      const wrapper = mountLActionGroup(
        { actions: ['edit'] },
        {
          slots: {
            edit: `<template #edit="{ action }">
              <span class="action-key">{{ action.key }}</span>
            </template>`
          }
        }
      )

      // The slot should have access to action
      expect(wrapper.find('.action-key').exists()).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_ACT_045: handles unknown preset gracefully', () => {
      // Should log warning but not crash
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const wrapper = mountLActionGroup({ actions: ['unknown-action'] })

      const button = wrapper.findComponent(LIconBtn)
      expect(button.props('icon')).toBe('mdi-help')

      consoleSpy.mockRestore()
    })

    it('COMP_ACT_046: preserves action order', () => {
      const wrapper = mountLActionGroup({
        actions: ['delete', 'view', 'edit']
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons[0].props('icon')).toBe('mdi-delete')
      expect(buttons[1].props('icon')).toBe('mdi-eye')
      expect(buttons[2].props('icon')).toBe('mdi-pencil')
    })

    it('COMP_ACT_047: handles all control presets together', () => {
      const wrapper = mountLActionGroup({
        actions: ['play', 'pause', 'stop']
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons[0].props('variant')).toBe('success')
      expect(buttons[1].props('variant')).toBe('warning')
      expect(buttons[2].props('variant')).toBe('danger')
    })

    it('COMP_ACT_048: handles settings and info presets', () => {
      const wrapper = mountLActionGroup({
        actions: ['settings', 'info']
      })

      const buttons = wrapper.findAllComponents(LIconBtn)
      expect(buttons[0].props('icon')).toBe('mdi-cog')
      expect(buttons[1].props('icon')).toBe('mdi-information')
    })
  })
})
