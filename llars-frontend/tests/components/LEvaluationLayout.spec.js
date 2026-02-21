/**
 * LEvaluationLayout Component Tests
 *
 * Tests for the LLARS evaluation layout wrapper component.
 * Test IDs: COMP_EVL_001 - COMP_EVL_055
 *
 * Coverage:
 * - Rendering and structure
 * - Header section (back button, title, subtitle, slots)
 * - Error bar
 * - Main content slot
 * - Action bar (prev/next buttons, progress indicator)
 * - Status display
 * - Mobile responsiveness
 * - Events (back, prev, next, clear-error)
 * - Edge cases
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import LEvaluationLayout from '@/components/common/LEvaluationLayout.vue'

// Mock useMobile composable
const mockIsMobile = ref(false)
vi.mock('@/composables/useMobile', () => ({
  useMobile: () => ({
    isMobile: mockIsMobile
  })
}))

// Mock LBtn component
const LBtnStub = {
  name: 'LBtn',
  template: `
    <button
      class="l-btn"
      :class="[variant, size]"
      :disabled="disabled"
      @click="$emit('click')"
    >
      <span v-if="prependIcon" class="prepend-icon">{{ prependIcon }}</span>
      <slot />
      <span v-if="appendIcon" class="append-icon">{{ appendIcon }}</span>
    </button>
  `,
  props: ['variant', 'size', 'disabled', 'prependIcon', 'appendIcon'],
  emits: ['click']
}

// Mock LEvaluationStatus component
const LEvaluationStatusStub = {
  name: 'LEvaluationStatus',
  template: '<div class="l-evaluation-status" :data-status="status" :data-saving="saving">{{ status }}</div>',
  props: ['status', 'saving']
}

function mountLEvaluationLayout(props = {}, options = {}) {
  return mount(LEvaluationLayout, {
    props,
    global: {
      stubs: {
        LBtn: LBtnStub,
        LEvaluationStatus: LEvaluationStatusStub,
        'v-alert': {
          template: `
            <div class="v-alert" :class="type">
              <slot />
              <button class="close-btn" @click="$emit('click:close')">×</button>
            </div>
          `,
          props: ['type', 'variant', 'density', 'closable'],
          emits: ['click:close']
        }
      }
    },
    ...options
  })
}

describe('LEvaluationLayout', () => {
  beforeEach(() => {
    mockIsMobile.value = false
  })

  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_EVL_001: renders with default props', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.evaluation-layout').exists()).toBe(true)
    })

    it('COMP_EVL_002: has evaluation-layout class', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.classes()).toContain('evaluation-layout')
    })

    it('COMP_EVL_003: renders header section', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.evaluation-header').exists()).toBe(true)
    })

    it('COMP_EVL_004: renders content section', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.evaluation-content').exists()).toBe(true)
    })

    it('COMP_EVL_005: renders action bar', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.evaluation-action-bar').exists()).toBe(true)
    })
  })

  // ==================== Header Tests ====================

  describe('Header', () => {
    it('COMP_EVL_006: renders back button', () => {
      const wrapper = mountLEvaluationLayout()
      const backBtn = wrapper.find('.header-left .l-btn')

      expect(backBtn.exists()).toBe(true)
      expect(backBtn.find('.prepend-icon').text()).toContain('mdi-arrow-left')
    })

    it('COMP_EVL_007: back button has default label "Übersicht"', () => {
      const wrapper = mountLEvaluationLayout()
      const backBtn = wrapper.find('.header-left .l-btn')

      expect(backBtn.text()).toContain('Übersicht')
    })

    it('COMP_EVL_008: back button uses custom backLabel', () => {
      const wrapper = mountLEvaluationLayout({ backLabel: 'Zurück' })
      const backBtn = wrapper.find('.header-left .l-btn')

      expect(backBtn.text()).toContain('Zurück')
    })

    it('COMP_EVL_009: emits back event when back button clicked', async () => {
      const wrapper = mountLEvaluationLayout()
      const backBtn = wrapper.find('.header-left .l-btn')

      await backBtn.trigger('click')

      expect(wrapper.emitted('back')).toBeTruthy()
      expect(wrapper.emitted('back')).toHaveLength(1)
    })

    it('COMP_EVL_010: does not render title when not provided', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.header-title').exists()).toBe(false)
    })

    it('COMP_EVL_011: renders title when provided', () => {
      const wrapper = mountLEvaluationLayout({ title: 'Ranking Evaluation' })

      expect(wrapper.find('.header-title h2').text()).toBe('Ranking Evaluation')
    })

    it('COMP_EVL_012: does not render subtitle when not provided', () => {
      const wrapper = mountLEvaluationLayout({ title: 'Test' })

      expect(wrapper.find('.header-title .text-caption').exists()).toBe(false)
    })

    it('COMP_EVL_013: renders subtitle when provided', () => {
      const wrapper = mountLEvaluationLayout({
        title: 'Test',
        subtitle: 'Thread #123'
      })

      expect(wrapper.find('.header-title .text-caption').text()).toBe('Thread #123')
    })

    it('COMP_EVL_014: renders header-center slot', () => {
      const wrapper = mountLEvaluationLayout({}, {
        slots: {
          'header-center': '<div class="custom-center">Center Content</div>'
        }
      })

      expect(wrapper.find('.header-center .custom-center').exists()).toBe(true)
    })

    it('COMP_EVL_015: renders header-right slot', () => {
      const wrapper = mountLEvaluationLayout({}, {
        slots: {
          'header-right': '<button class="custom-action">Action</button>'
        }
      })

      expect(wrapper.find('.header-right .custom-action').exists()).toBe(true)
    })
  })

  // ==================== Error Bar Tests ====================

  describe('Error Bar', () => {
    it('COMP_EVL_016: does not render error bar by default', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.error-bar').exists()).toBe(false)
    })

    it('COMP_EVL_017: renders error bar when error provided', () => {
      const wrapper = mountLEvaluationLayout({ error: 'Something went wrong' })

      expect(wrapper.find('.error-bar').exists()).toBe(true)
    })

    it('COMP_EVL_018: displays error message', () => {
      const wrapper = mountLEvaluationLayout({ error: 'Network error' })

      expect(wrapper.find('.v-alert').text()).toContain('Network error')
    })

    it('COMP_EVL_019: error alert has error type', () => {
      const wrapper = mountLEvaluationLayout({ error: 'Error message' })

      expect(wrapper.find('.v-alert').classes()).toContain('error')
    })

    it('COMP_EVL_020: emits clear-error when alert closed', async () => {
      const wrapper = mountLEvaluationLayout({ error: 'Error' })
      const closeBtn = wrapper.find('.v-alert .close-btn')

      expect(closeBtn.exists()).toBe(true)
      await closeBtn.trigger('click')

      expect(wrapper.emitted('clear-error')).toBeTruthy()
    })
  })

  // ==================== Main Content Tests ====================

  describe('Main Content', () => {
    it('COMP_EVL_021: renders default slot content', () => {
      const wrapper = mountLEvaluationLayout({}, {
        slots: {
          default: '<div class="main-content">Main Content Here</div>'
        }
      })

      expect(wrapper.find('.evaluation-content .main-content').exists()).toBe(true)
    })

    it('COMP_EVL_022: content area is flexible', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.evaluation-content').exists()).toBe(true)
    })
  })

  // ==================== Action Bar Tests ====================

  describe('Action Bar', () => {
    it('COMP_EVL_023: renders prev button', () => {
      const wrapper = mountLEvaluationLayout()
      const buttons = wrapper.findAll('.action-bar-left .l-btn')

      expect(buttons[0].text()).toContain('Vorheriger')
    })

    it('COMP_EVL_024: renders next button', () => {
      const wrapper = mountLEvaluationLayout()
      const buttons = wrapper.findAll('.action-bar-left .l-btn')

      expect(buttons[1].text()).toContain('Nächster')
    })

    it('COMP_EVL_025: prev button has chevron-left icon', () => {
      const wrapper = mountLEvaluationLayout()
      const prevBtn = wrapper.findAll('.action-bar-left .l-btn')[0]

      expect(prevBtn.find('.prepend-icon').text()).toContain('mdi-chevron-left')
    })

    it('COMP_EVL_026: next button has chevron-right icon', () => {
      const wrapper = mountLEvaluationLayout()
      const nextBtn = wrapper.findAll('.action-bar-left .l-btn')[1]

      expect(nextBtn.find('.append-icon').text()).toContain('mdi-chevron-right')
    })

    it('COMP_EVL_027: prev button is disabled by default', () => {
      const wrapper = mountLEvaluationLayout()
      const prevBtn = wrapper.findAll('.action-bar-left .l-btn')[0]

      expect(prevBtn.attributes('disabled')).toBeDefined()
    })

    it('COMP_EVL_028: next button is disabled by default', () => {
      const wrapper = mountLEvaluationLayout()
      const nextBtn = wrapper.findAll('.action-bar-left .l-btn')[1]

      expect(nextBtn.attributes('disabled')).toBeDefined()
    })

    it('COMP_EVL_029: prev button enabled when canGoPrev is true', () => {
      const wrapper = mountLEvaluationLayout({ canGoPrev: true })
      const prevBtn = wrapper.findAll('.action-bar-left .l-btn')[0]

      expect(prevBtn.attributes('disabled')).toBeUndefined()
    })

    it('COMP_EVL_030: next button enabled when canGoNext is true', () => {
      const wrapper = mountLEvaluationLayout({ canGoNext: true })
      const nextBtn = wrapper.findAll('.action-bar-left .l-btn')[1]

      expect(nextBtn.attributes('disabled')).toBeUndefined()
    })

    it('COMP_EVL_031: emits prev event when prev button clicked', async () => {
      const wrapper = mountLEvaluationLayout({ canGoPrev: true })
      const prevBtn = wrapper.findAll('.action-bar-left .l-btn')[0]

      await prevBtn.trigger('click')

      expect(wrapper.emitted('prev')).toBeTruthy()
    })

    it('COMP_EVL_032: emits next event when next button clicked', async () => {
      const wrapper = mountLEvaluationLayout({ canGoNext: true })
      const nextBtn = wrapper.findAll('.action-bar-left .l-btn')[1]

      await nextBtn.trigger('click')

      expect(wrapper.emitted('next')).toBeTruthy()
    })

    it('COMP_EVL_033: renders action-bar-right slot', () => {
      const wrapper = mountLEvaluationLayout({}, {
        slots: {
          'action-bar-right': '<button class="save-btn">Save</button>'
        }
      })

      expect(wrapper.find('.action-bar-right .save-btn').exists()).toBe(true)
    })
  })

  // ==================== Status Display Tests ====================

  describe('Status Display', () => {
    it('COMP_EVL_034: renders LEvaluationStatus', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.l-evaluation-status').exists()).toBe(true)
    })

    it('COMP_EVL_035: passes status prop to LEvaluationStatus', () => {
      const wrapper = mountLEvaluationLayout({ status: 'done' })

      expect(wrapper.find('.l-evaluation-status').attributes('data-status')).toBe('done')
    })

    it('COMP_EVL_036: passes saving prop to LEvaluationStatus', () => {
      const wrapper = mountLEvaluationLayout({ saving: true })

      expect(wrapper.find('.l-evaluation-status').attributes('data-saving')).toBe('true')
    })

    it('COMP_EVL_037: default status is pending', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.l-evaluation-status').attributes('data-status')).toBe('pending')
    })
  })

  // ==================== Progress Indicator Tests ====================

  describe('Progress Indicator', () => {
    it('COMP_EVL_038: does not show progress when totalItems is 0', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 0 })

      expect(wrapper.find('.progress-indicator').exists()).toBe(false)
    })

    it('COMP_EVL_039: shows progress when totalItems > 0', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 10, currentIndex: 0 })

      expect(wrapper.find('.progress-indicator').exists()).toBe(true)
    })

    it('COMP_EVL_040: displays correct progress text', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 10, currentIndex: 4 })

      expect(wrapper.find('.progress-indicator').text()).toBe('5 / 10')
    })

    it('COMP_EVL_041: progress shows 1-based index', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 5, currentIndex: 0 })

      expect(wrapper.find('.progress-indicator').text()).toBe('1 / 5')
    })

    it('COMP_EVL_042: progress updates with currentIndex', async () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 5, currentIndex: 2 })

      expect(wrapper.find('.progress-indicator').text()).toBe('3 / 5')

      await wrapper.setProps({ currentIndex: 4 })

      expect(wrapper.find('.progress-indicator').text()).toBe('5 / 5')
    })
  })

  // ==================== Mobile Tests ====================

  describe('Mobile', () => {
    it('COMP_EVL_043: does not have is-mobile class by default', () => {
      mockIsMobile.value = false
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.classes()).not.toContain('is-mobile')
    })

    it('COMP_EVL_044: has is-mobile class when on mobile', () => {
      mockIsMobile.value = true
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.classes()).toContain('is-mobile')
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_EVL_045: updates title reactively', async () => {
      const wrapper = mountLEvaluationLayout({ title: 'Original' })

      expect(wrapper.find('.header-title h2').text()).toBe('Original')

      await wrapper.setProps({ title: 'Updated' })

      expect(wrapper.find('.header-title h2').text()).toBe('Updated')
    })

    it('COMP_EVL_046: updates error reactively', async () => {
      const wrapper = mountLEvaluationLayout({ error: '' })

      expect(wrapper.find('.error-bar').exists()).toBe(false)

      await wrapper.setProps({ error: 'New error' })

      expect(wrapper.find('.error-bar').exists()).toBe(true)
    })

    it('COMP_EVL_047: updates canGoPrev reactively', async () => {
      const wrapper = mountLEvaluationLayout({ canGoPrev: false })
      const prevBtn = wrapper.findAll('.action-bar-left .l-btn')[0]

      expect(prevBtn.attributes('disabled')).toBeDefined()

      await wrapper.setProps({ canGoPrev: true })

      expect(prevBtn.attributes('disabled')).toBeUndefined()
    })

    it('COMP_EVL_048: updates canGoNext reactively', async () => {
      const wrapper = mountLEvaluationLayout({ canGoNext: false })
      const nextBtn = wrapper.findAll('.action-bar-left .l-btn')[1]

      expect(nextBtn.attributes('disabled')).toBeDefined()

      await wrapper.setProps({ canGoNext: true })

      expect(nextBtn.attributes('disabled')).toBeUndefined()
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_EVL_049: handles empty strings for optional props', () => {
      const wrapper = mountLEvaluationLayout({
        title: '',
        subtitle: '',
        error: '',
        backLabel: ''
      })

      expect(wrapper.find('.header-title').exists()).toBe(false)
      expect(wrapper.find('.error-bar').exists()).toBe(false)
    })

    it('COMP_EVL_050: handles zero currentIndex correctly', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 5, currentIndex: 0 })

      expect(wrapper.find('.progress-indicator').text()).toBe('1 / 5')
    })

    it('COMP_EVL_051: handles large totalItems', () => {
      const wrapper = mountLEvaluationLayout({ totalItems: 999, currentIndex: 500 })

      expect(wrapper.find('.progress-indicator').text()).toBe('501 / 999')
    })

    it('COMP_EVL_052: renders all sections with full props', () => {
      const wrapper = mountLEvaluationLayout({
        title: 'Full Test',
        subtitle: 'Subtitle',
        backLabel: 'Back',
        error: 'Error message',
        status: 'in_progress',
        saving: true,
        canGoPrev: true,
        canGoNext: true,
        currentIndex: 5,
        totalItems: 10
      })

      expect(wrapper.find('.header-title h2').text()).toBe('Full Test')
      expect(wrapper.find('.header-title .text-caption').text()).toBe('Subtitle')
      expect(wrapper.find('.error-bar').exists()).toBe(true)
      expect(wrapper.find('.progress-indicator').text()).toBe('6 / 10')
    })

    it('COMP_EVL_053: multiple slots work together', () => {
      const wrapper = mountLEvaluationLayout({
        title: 'Test'
      }, {
        slots: {
          'header-center': '<span class="center">Center</span>',
          'header-right': '<span class="right">Right</span>',
          default: '<div class="content">Content</div>',
          'action-bar-right': '<span class="action">Action</span>'
        }
      })

      expect(wrapper.find('.header-center .center').exists()).toBe(true)
      expect(wrapper.find('.header-right .right').exists()).toBe(true)
      expect(wrapper.find('.evaluation-content .content').exists()).toBe(true)
      expect(wrapper.find('.action-bar-right .action').exists()).toBe(true)
    })

    it('COMP_EVL_054: status prop accepts all valid values', async () => {
      const wrapper = mountLEvaluationLayout({ status: 'pending' })
      expect(wrapper.find('.l-evaluation-status').attributes('data-status')).toBe('pending')

      await wrapper.setProps({ status: 'in_progress' })
      expect(wrapper.find('.l-evaluation-status').attributes('data-status')).toBe('in_progress')

      await wrapper.setProps({ status: 'done' })
      expect(wrapper.find('.l-evaluation-status').attributes('data-status')).toBe('done')
    })

    it('COMP_EVL_055: component works with minimal props', () => {
      const wrapper = mountLEvaluationLayout()

      expect(wrapper.find('.evaluation-layout').exists()).toBe(true)
      expect(wrapper.find('.evaluation-header').exists()).toBe(true)
      expect(wrapper.find('.evaluation-content').exists()).toBe(true)
      expect(wrapper.find('.evaluation-action-bar').exists()).toBe(true)
    })
  })
})
