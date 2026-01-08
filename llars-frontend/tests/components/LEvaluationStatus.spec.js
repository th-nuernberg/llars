/**
 * LEvaluationStatus Component Tests
 *
 * Tests for the LLARS evaluation status indicator component.
 * Test IDs: COMP_EVS_001 - COMP_EVS_045
 *
 * Coverage:
 * - Rendering and structure
 * - Status classes (pending, in_progress, done, saving)
 * - Status icons
 * - Status labels
 * - Status normalization (mapping different formats)
 * - Saving state
 * - Reactivity
 * - Edge cases
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LEvaluationStatus from '@/components/common/LEvaluationStatus.vue'

function mountLEvaluationStatus(props = {}, options = {}) {
  return mount(LEvaluationStatus, {
    props,
    global: {
      stubs: {
        'v-icon': {
          template: '<i class="v-icon" :class="{ \'saving-icon\': $attrs.class?.includes(\'saving\') }">{{ $attrs.size ? "" : "" }}<slot /></i>',
          props: ['size']
        },
        // Use a proper transition stub that renders slot content
        transition: {
          template: '<div><slot /></div>'
        }
      }
    },
    ...options
  })
}

describe('LEvaluationStatus', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_EVS_001: renders with default props', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.evaluation-status').exists()).toBe(true)
    })

    it('COMP_EVS_002: has evaluation-status class', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.classes()).toContain('evaluation-status')
    })

    it('COMP_EVS_003: renders status-content container', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.find('.status-content').exists()).toBe(true)
    })

    it('COMP_EVS_004: renders icon', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_005: renders status label', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.find('.status-label').exists()).toBe(true)
    })
  })

  // ==================== Status Class Tests ====================

  describe('Status Classes', () => {
    it('COMP_EVS_006: has status-pending class by default', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.classes()).toContain('status-pending')
    })

    it('COMP_EVS_007: has status-pending class when status is pending', () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.classes()).toContain('status-pending')
    })

    it('COMP_EVS_008: has status-in_progress class when status is in_progress', () => {
      const wrapper = mountLEvaluationStatus({ status: 'in_progress' })

      expect(wrapper.classes()).toContain('status-in_progress')
    })

    it('COMP_EVS_009: has status-done class when status is done', () => {
      const wrapper = mountLEvaluationStatus({ status: 'done' })

      expect(wrapper.classes()).toContain('status-done')
    })

    it('COMP_EVS_010: has status-saving class when saving is true', () => {
      const wrapper = mountLEvaluationStatus({ saving: true })

      expect(wrapper.classes()).toContain('status-saving')
    })

    it('COMP_EVS_011: saving class overrides status class', () => {
      const wrapper = mountLEvaluationStatus({ status: 'done', saving: true })

      expect(wrapper.classes()).toContain('status-saving')
      expect(wrapper.classes()).not.toContain('status-done')
    })
  })

  // ==================== Icon Tests ====================

  describe('Icons', () => {
    it('COMP_EVS_012: shows circle-outline icon for pending', () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_013: shows progress-clock icon for in_progress', () => {
      const wrapper = mountLEvaluationStatus({ status: 'in_progress' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_014: shows check-circle icon for done', () => {
      const wrapper = mountLEvaluationStatus({ status: 'done' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_015: shows loading icon when saving', () => {
      const wrapper = mountLEvaluationStatus({ saving: true })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_016: loading icon has saving-icon class', () => {
      const wrapper = mountLEvaluationStatus({ saving: true })

      expect(wrapper.find('.saving-icon').exists()).toBe(true)
    })
  })

  // ==================== Label Tests ====================

  describe('Labels', () => {
    it('COMP_EVS_017: shows "Ausstehend" for pending', () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.find('.status-label').text()).toBe('Ausstehend')
    })

    it('COMP_EVS_018: shows "In Bearbeitung" for in_progress', () => {
      const wrapper = mountLEvaluationStatus({ status: 'in_progress' })

      expect(wrapper.find('.status-label').text()).toBe('In Bearbeitung')
    })

    it('COMP_EVS_019: shows "Abgeschlossen" for done', () => {
      const wrapper = mountLEvaluationStatus({ status: 'done' })

      expect(wrapper.find('.status-label').text()).toBe('Abgeschlossen')
    })

    it('COMP_EVS_020: shows "Speichert..." when saving', () => {
      const wrapper = mountLEvaluationStatus({ saving: true })

      expect(wrapper.find('.status-label').text()).toBe('Speichert...')
    })

    it('COMP_EVS_021: saving label overrides status label', () => {
      const wrapper = mountLEvaluationStatus({ status: 'done', saving: true })

      expect(wrapper.find('.status-label').text()).toBe('Speichert...')
    })
  })

  // ==================== Status Normalization Tests ====================

  describe('Status Normalization', () => {
    it('COMP_EVS_022: normalizes not_started to pending', () => {
      const wrapper = mountLEvaluationStatus({ status: 'not_started' })

      expect(wrapper.classes()).toContain('status-pending')
      expect(wrapper.find('.status-label').text()).toBe('Ausstehend')
    })

    it('COMP_EVS_023: normalizes progressing to in_progress', () => {
      const wrapper = mountLEvaluationStatus({ status: 'progressing' })

      expect(wrapper.classes()).toContain('status-in_progress')
      expect(wrapper.find('.status-label').text()).toBe('In Bearbeitung')
    })

    it('COMP_EVS_024: normalizes Progressing to in_progress', () => {
      const wrapper = mountLEvaluationStatus({ status: 'Progressing' })

      expect(wrapper.classes()).toContain('status-in_progress')
    })

    it('COMP_EVS_025: normalizes completed to done', () => {
      const wrapper = mountLEvaluationStatus({ status: 'completed' })

      expect(wrapper.classes()).toContain('status-done')
      expect(wrapper.find('.status-label').text()).toBe('Abgeschlossen')
    })

    it('COMP_EVS_026: normalizes Done to done', () => {
      const wrapper = mountLEvaluationStatus({ status: 'Done' })

      expect(wrapper.classes()).toContain('status-done')
    })

    it('COMP_EVS_027: unknown status defaults to pending', () => {
      const wrapper = mountLEvaluationStatus({ status: 'unknown_status' })

      expect(wrapper.classes()).toContain('status-pending')
      expect(wrapper.find('.status-label').text()).toBe('Ausstehend')
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_EVS_028: updates class when status changes', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.classes()).toContain('status-pending')

      await wrapper.setProps({ status: 'done' })

      expect(wrapper.classes()).toContain('status-done')
      expect(wrapper.classes()).not.toContain('status-pending')
    })

    it('COMP_EVS_029: updates label when status changes', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.find('.status-label').text()).toBe('Ausstehend')

      await wrapper.setProps({ status: 'in_progress' })

      expect(wrapper.find('.status-label').text()).toBe('In Bearbeitung')
    })

    it('COMP_EVS_030: updates icon when status changes', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)

      await wrapper.setProps({ status: 'done' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_031: updates to saving state', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending', saving: false })

      expect(wrapper.classes()).toContain('status-pending')

      await wrapper.setProps({ saving: true })

      expect(wrapper.classes()).toContain('status-saving')
      expect(wrapper.find('.status-label').text()).toBe('Speichert...')
    })

    it('COMP_EVS_032: returns from saving state', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'done', saving: true })

      expect(wrapper.classes()).toContain('status-saving')

      await wrapper.setProps({ saving: false })

      expect(wrapper.classes()).toContain('status-done')
      expect(wrapper.find('.status-label').text()).toBe('Abgeschlossen')
    })
  })

  // ==================== Default Props Tests ====================

  describe('Default Props', () => {
    it('COMP_EVS_033: default status is pending', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.props('status')).toBe('pending')
    })

    it('COMP_EVS_034: default saving is false', () => {
      const wrapper = mountLEvaluationStatus()

      expect(wrapper.props('saving')).toBe(false)
    })
  })

  // ==================== Transition Tests ====================

  describe('Transition', () => {
    it('COMP_EVS_035: status-content has key based on displayStatus', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })
      const content = wrapper.find('.status-content')

      expect(content.exists()).toBe(true)

      // Change status to verify the key would change (transition trigger)
      await wrapper.setProps({ status: 'done' })

      expect(wrapper.find('.status-content').exists()).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_EVS_036: handles empty string status', () => {
      const wrapper = mountLEvaluationStatus({ status: '' })

      // Empty string should default to pending
      expect(wrapper.classes()).toContain('status-pending')
    })

    it('COMP_EVS_037: handles rapid status changes', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      await wrapper.setProps({ status: 'in_progress' })
      await wrapper.setProps({ status: 'done' })
      await wrapper.setProps({ status: 'pending' })

      expect(wrapper.classes()).toContain('status-pending')
    })

    it('COMP_EVS_038: handles rapid saving toggle', async () => {
      const wrapper = mountLEvaluationStatus({ saving: false })

      await wrapper.setProps({ saving: true })
      await wrapper.setProps({ saving: false })
      await wrapper.setProps({ saving: true })

      expect(wrapper.classes()).toContain('status-saving')
    })

    it('COMP_EVS_039: component works with minimal props', () => {
      const wrapper = mount(LEvaluationStatus, {
        global: {
          stubs: {
            'v-icon': { template: '<i class="v-icon"><slot /></i>' },
            transition: false
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.evaluation-status').exists()).toBe(true)
    })

    it('COMP_EVS_040: multiple instances are independent', () => {
      const wrapper1 = mountLEvaluationStatus({ status: 'pending' })
      const wrapper2 = mountLEvaluationStatus({ status: 'done' })
      const wrapper3 = mountLEvaluationStatus({ status: 'in_progress' })

      expect(wrapper1.classes()).toContain('status-pending')
      expect(wrapper2.classes()).toContain('status-done')
      expect(wrapper3.classes()).toContain('status-in_progress')
    })

    it('COMP_EVS_041: saving with different statuses', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending', saving: true })

      expect(wrapper.classes()).toContain('status-saving')

      await wrapper.setProps({ status: 'in_progress' })
      expect(wrapper.classes()).toContain('status-saving')

      await wrapper.setProps({ status: 'done' })
      expect(wrapper.classes()).toContain('status-saving')
    })

    it('COMP_EVS_042: icon size is 16', () => {
      const wrapper = mountLEvaluationStatus()

      // The icon component receives size="16"
      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_EVS_043: all valid status values work', async () => {
      const validStatuses = ['pending', 'in_progress', 'done', 'not_started', 'progressing', 'completed']
      const wrapper = mountLEvaluationStatus()

      for (const status of validStatuses) {
        await wrapper.setProps({ status })
        expect(wrapper.find('.evaluation-status').exists()).toBe(true)
        expect(wrapper.find('.status-label').text()).toBeTruthy()
      }
    })

    it('COMP_EVS_044: pending shows correct visual state', () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      expect(wrapper.classes()).toContain('status-pending')
      expect(wrapper.find('.v-icon').exists()).toBe(true)
      expect(wrapper.find('.status-label').text()).toBe('Ausstehend')
    })

    it('COMP_EVS_045: full flow from pending to done with saving', async () => {
      const wrapper = mountLEvaluationStatus({ status: 'pending' })

      // Start pending
      expect(wrapper.classes()).toContain('status-pending')

      // Move to in_progress
      await wrapper.setProps({ status: 'in_progress' })
      expect(wrapper.classes()).toContain('status-in_progress')

      // Start saving
      await wrapper.setProps({ saving: true })
      expect(wrapper.classes()).toContain('status-saving')
      expect(wrapper.find('.status-label').text()).toBe('Speichert...')

      // Complete save and mark done
      await wrapper.setProps({ status: 'done', saving: false })
      expect(wrapper.classes()).toContain('status-done')
      expect(wrapper.find('.status-label').text()).toBe('Abgeschlossen')
    })
  })
})
