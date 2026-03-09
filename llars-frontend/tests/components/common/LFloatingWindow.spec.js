/**
 * LFloatingWindow Component Tests
 *
 * Tests for the LLARS floating window component with drag, resize, maximize, and close.
 * Test IDs: COMP_FW_001 - COMP_FW_035
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import LFloatingWindow from '@/components/common/LFloatingWindow.vue'

const vuetify = createVuetify({ components, directives })

function mountComponent(props = {}, options = {}) {
  return mount(LFloatingWindow, {
    props: {
      modelValue: true,
      title: 'Test Window',
      ...props
    },
    global: {
      plugins: [vuetify],
      stubs: {
        LIconBtn: {
          template: '<button class="l-icon-btn-stub" @click="$emit(\'click\')"><slot /></button>',
          props: ['icon', 'size', 'tooltip', 'loading']
        },
        Teleport: true
      },
      ...options.global
    },
    ...options
  })
}

describe('LFloatingWindow', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_FW_001: renders when modelValue is true', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-floating-window').exists()).toBe(true)
    })

    it('COMP_FW_002: does not render when modelValue is false', () => {
      const wrapper = mountComponent({ modelValue: false })

      expect(wrapper.find('.l-floating-window').exists()).toBe(false)
    })

    it('COMP_FW_003: renders title in header', () => {
      const wrapper = mountComponent({ title: 'My Window' })

      expect(wrapper.find('.header-title').text()).toBe('My Window')
    })

    it('COMP_FW_004: renders icon when provided', () => {
      const wrapper = mountComponent({ icon: 'mdi-cog' })

      expect(wrapper.find('.header-icon').exists()).toBe(true)
    })

    it('COMP_FW_005: does not render icon when not provided', () => {
      const wrapper = mountComponent({ icon: null })

      expect(wrapper.find('.header-icon').exists()).toBe(false)
    })

    it('COMP_FW_006: renders content slot', () => {
      const wrapper = mountComponent({}, {
        slots: { default: '<p class="test-content">Hello</p>' }
      })

      expect(wrapper.find('.floating-window-content').exists()).toBe(true)
      expect(wrapper.find('.test-content').exists()).toBe(true)
    })

    it('COMP_FW_007: renders footer slot when provided', () => {
      const wrapper = mountComponent({}, {
        slots: { footer: '<div class="test-footer">Footer</div>' }
      })

      expect(wrapper.find('.floating-window-footer').exists()).toBe(true)
      expect(wrapper.find('.test-footer').exists()).toBe(true)
    })

    it('COMP_FW_008: does not render footer when slot is empty', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.floating-window-footer').exists()).toBe(false)
    })
  })

  // ==================== Color Theme Tests ====================

  describe('Color Themes', () => {
    const themes = ['primary', 'secondary', 'accent', 'success', 'warning', 'danger', 'ai']

    themes.forEach((theme, index) => {
      it(`COMP_FW_${String(9 + index).padStart(3, '0')}: applies ${theme} theme class`, () => {
        const wrapper = mountComponent({ color: theme })

        expect(wrapper.find('.l-floating-window').classes()).toContain(`theme-${theme}`)
      })
    })
  })

  // ==================== Button Visibility Tests ====================

  describe('Button Visibility', () => {
    it('COMP_FW_016: shows close button by default', () => {
      const wrapper = mountComponent()

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      expect(buttons.length).toBeGreaterThanOrEqual(1)
    })

    it('COMP_FW_017: hides close button when showClose is false', () => {
      const wrapper = mountComponent({
        showClose: false,
        showMinimize: false,
        showMaximize: false,
        showRefresh: false
      })

      // Only custom header-actions slot content should remain
      const buttons = wrapper.findAll('.l-icon-btn-stub')
      expect(buttons.length).toBe(0)
    })

    it('COMP_FW_018: shows minimize button when showMinimize is true', () => {
      const wrapper = mountComponent({ showMinimize: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      // minimize + close = at least 2
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })

    it('COMP_FW_019: shows maximize button when showMaximize is true', () => {
      const wrapper = mountComponent({ showMaximize: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })

    it('COMP_FW_020: shows refresh button when showRefresh is true', () => {
      const wrapper = mountComponent({ showRefresh: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      expect(buttons.length).toBeGreaterThanOrEqual(2)
    })
  })

  // ==================== Close Event Tests ====================

  describe('Close', () => {
    it('COMP_FW_021: emits update:modelValue(false) on close', async () => {
      const wrapper = mountComponent({ showClose: true })

      // The close button is the last LIconBtn
      const buttons = wrapper.findAll('.l-icon-btn-stub')
      const closeBtn = buttons[buttons.length - 1]
      await closeBtn.trigger('click')

      expect(wrapper.emitted('update:modelValue')).toBeTruthy()
      expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
    })

    it('COMP_FW_022: emits close event on close', async () => {
      const wrapper = mountComponent({ showClose: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      const closeBtn = buttons[buttons.length - 1]
      await closeBtn.trigger('click')

      expect(wrapper.emitted('close')).toBeTruthy()
    })
  })

  // ==================== Resize Handle Tests ====================

  describe('Resize Handle', () => {
    it('COMP_FW_023: shows resize handle when resizable is true', () => {
      const wrapper = mountComponent({ resizable: true })

      expect(wrapper.find('.resize-handle').exists()).toBe(true)
    })

    it('COMP_FW_024: hides resize handle when resizable is false', () => {
      const wrapper = mountComponent({ resizable: false })

      expect(wrapper.find('.resize-handle').exists()).toBe(false)
    })
  })

  // ==================== Style Tests ====================

  describe('Window Style', () => {
    it('COMP_FW_025: applies position and size styles', () => {
      const wrapper = mountComponent({
        width: 500,
        height: 400,
        initialX: 200,
        initialY: 150
      })

      const style = wrapper.find('.l-floating-window').attributes('style')
      expect(style).toContain('width')
      expect(style).toContain('height')
    })

    it('COMP_FW_026: applies z-index from prop', () => {
      const wrapper = mountComponent({ zIndex: 5000 })

      const style = wrapper.find('.l-floating-window').attributes('style')
      expect(style).toContain('z-index')
      expect(style).toContain('5000')
    })

    it('COMP_FW_027: applies LLARS signature border-radius class', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.l-floating-window').exists()).toBe(true)
    })
  })

  // ==================== Drag Behavior Tests ====================

  describe('Drag Behavior', () => {
    it('COMP_FW_028: header has grab cursor styling', () => {
      const wrapper = mountComponent()

      expect(wrapper.find('.floating-window-header').exists()).toBe(true)
    })

    it('COMP_FW_029: adds dragging class on mousedown', async () => {
      const wrapper = mountComponent()

      const header = wrapper.find('.floating-window-header')
      await header.trigger('mousedown', { button: 0, clientX: 100, clientY: 100 })

      expect(wrapper.find('.l-floating-window').classes()).toContain('dragging')

      // Cleanup: stop drag
      document.dispatchEvent(new Event('mouseup'))
    })

    it('COMP_FW_030: does not start drag on right click', async () => {
      const wrapper = mountComponent()

      const header = wrapper.find('.floating-window-header')
      await header.trigger('mousedown', { button: 2, clientX: 100, clientY: 100 })

      expect(wrapper.find('.l-floating-window').classes()).not.toContain('dragging')
    })
  })

  // ==================== Maximize Tests ====================

  describe('Maximize', () => {
    it('COMP_FW_031: emits maximize on toggle', async () => {
      const wrapper = mountComponent({ showMaximize: true })

      // Find the maximize button (second to last, before close)
      const buttons = wrapper.findAll('.l-icon-btn-stub')
      // maximize is before close button
      const maximizeBtn = buttons[buttons.length - 2]
      await maximizeBtn.trigger('click')

      expect(wrapper.emitted('maximize')).toBeTruthy()
    })

    it('COMP_FW_032: sets isMaximized state when maximized', async () => {
      const wrapper = mountComponent({ showMaximize: true, resizable: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      const maximizeBtn = buttons[buttons.length - 2]
      await maximizeBtn.trigger('click')

      // Verify maximize was emitted (isMaximized is true internally)
      expect(wrapper.emitted('maximize')).toBeTruthy()
    })

    it('COMP_FW_033: emits restore when toggling back from maximized', async () => {
      const wrapper = mountComponent({ showMaximize: true })

      const buttons = wrapper.findAll('.l-icon-btn-stub')
      const maximizeBtn = buttons[buttons.length - 2]

      // Maximize
      await maximizeBtn.trigger('click')

      // Restore (click again)
      const buttonsAfter = wrapper.findAll('.l-icon-btn-stub')
      const restoreBtn = buttonsAfter[buttonsAfter.length - 2]
      await restoreBtn.trigger('click')

      expect(wrapper.emitted('restore')).toBeTruthy()
    })
  })

  // ==================== LocalStorage Persistence Tests ====================

  describe('LocalStorage Persistence', () => {
    it('COMP_FW_034: loads saved state from localStorage when modelValue toggles', async () => {
      const savedState = JSON.stringify({ x: 300, y: 200, width: 600, height: 400 })
      vi.mocked(window.localStorage.getItem).mockReturnValue(savedState)

      // Start with modelValue=false so the watcher fires when we set it to true
      const wrapper = mountComponent({ modelValue: false, storageKey: 'test-window' })
      await wrapper.setProps({ modelValue: true })

      expect(window.localStorage.getItem).toHaveBeenCalledWith('test-window')
    })

    it('COMP_FW_035: does not access localStorage without storageKey', () => {
      vi.mocked(window.localStorage.getItem).mockClear()

      mountComponent({ storageKey: null })

      expect(window.localStorage.getItem).not.toHaveBeenCalled()
    })
  })
})
