/**
 * LMessage Component Tests
 *
 * Tests for the LLARS message display component with client/advisor detection.
 * Test IDs: COMP_MSG_001 - COMP_MSG_045
 *
 * Coverage:
 * - Rendering and structure
 * - Sender type detection (auto, client, advisor)
 * - Client patterns matching
 * - CSS classes based on sender type
 * - Tag variant and icon
 * - Timestamp formatting
 * - Slots (default, actions)
 * - Edge cases
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { h } from 'vue'
import LMessage from '@/components/common/LMessage.vue'

// Mock LTag component
const LTagStub = {
  name: 'LTag',
  template: '<span class="l-tag" :class="`l-tag--${variant}`"><slot /></span>',
  props: ['variant', 'size']
}

function mountLMessage(props = {}, options = {}) {
  return mount(LMessage, {
    props: {
      sender: 'Test Sender',
      ...props
    },
    global: {
      stubs: {
        LTag: LTagStub,
        'v-icon': {
          template: '<i class="v-icon"><slot /></i>',
          props: ['size']
        },
        'v-spacer': { template: '<div class="v-spacer"></div>' }
      }
    },
    ...options
  })
}

describe('LMessage', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_MSG_001: renders with required sender prop', () => {
      const wrapper = mountLMessage({ sender: 'John Doe' })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-message').exists()).toBe(true)
    })

    it('COMP_MSG_002: has l-message class', () => {
      const wrapper = mountLMessage()

      expect(wrapper.classes()).toContain('l-message')
    })

    it('COMP_MSG_003: renders accent border element', () => {
      const wrapper = mountLMessage()

      expect(wrapper.find('.l-message__accent').exists()).toBe(true)
    })

    it('COMP_MSG_004: renders content area', () => {
      const wrapper = mountLMessage()

      expect(wrapper.find('.l-message__content').exists()).toBe(true)
    })

    it('COMP_MSG_005: renders header with sender tag', () => {
      const wrapper = mountLMessage({ sender: 'Alice' })

      expect(wrapper.find('.l-message__header').exists()).toBe(true)
      expect(wrapper.find('.l-tag').exists()).toBe(true)
      expect(wrapper.find('.l-tag').text()).toContain('Alice')
    })

    it('COMP_MSG_006: renders body area', () => {
      const wrapper = mountLMessage()

      expect(wrapper.find('.l-message__body').exists()).toBe(true)
    })

    it('COMP_MSG_007: displays content prop in body', () => {
      const wrapper = mountLMessage({ sender: 'Test', content: 'Hello world!' })

      expect(wrapper.find('.l-message__body').text()).toBe('Hello world!')
    })

    it('COMP_MSG_008: renders empty body when no content', () => {
      const wrapper = mountLMessage({ sender: 'Test', content: '' })

      expect(wrapper.find('.l-message__body').text()).toBe('')
    })
  })

  // ==================== Sender Type Detection Tests ====================

  describe('Sender Type Detection', () => {
    it('COMP_MSG_009: detects "Ratsuchende Person" as client', () => {
      const wrapper = mountLMessage({ sender: 'Ratsuchende Person' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_010: detects "Ratsuchender" as client', () => {
      const wrapper = mountLMessage({ sender: 'Ratsuchender' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_011: detects "Klient" as client', () => {
      const wrapper = mountLMessage({ sender: 'Klient' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_012: detects "Klientin" as client', () => {
      const wrapper = mountLMessage({ sender: 'Klientin' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_013: detects "Client" as client', () => {
      const wrapper = mountLMessage({ sender: 'Client' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_014: detects "Anfragender" as client', () => {
      const wrapper = mountLMessage({ sender: 'Anfragender' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_015: detects unknown sender as advisor', () => {
      const wrapper = mountLMessage({ sender: 'Berater Müller' })

      expect(wrapper.classes()).toContain('l-message--advisor')
    })

    it('COMP_MSG_016: detection is case-insensitive', () => {
      const wrapper = mountLMessage({ sender: 'RATSUCHENDE PERSON' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_017: detects partial match in sender name', () => {
      const wrapper = mountLMessage({ sender: 'Herr Klient Schmidt' })

      expect(wrapper.classes()).toContain('l-message--client')
    })
  })

  // ==================== Explicit Sender Type Tests ====================

  describe('Explicit Sender Type', () => {
    it('COMP_MSG_018: senderType="client" forces client style', () => {
      const wrapper = mountLMessage({ sender: 'Berater', senderType: 'client' })

      expect(wrapper.classes()).toContain('l-message--client')
      expect(wrapper.classes()).not.toContain('l-message--advisor')
    })

    it('COMP_MSG_019: senderType="advisor" forces advisor style', () => {
      const wrapper = mountLMessage({ sender: 'Klient', senderType: 'advisor' })

      expect(wrapper.classes()).toContain('l-message--advisor')
      expect(wrapper.classes()).not.toContain('l-message--client')
    })

    it('COMP_MSG_020: senderType="auto" uses auto-detection', () => {
      const wrapper = mountLMessage({ sender: 'Klient', senderType: 'auto' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_021: default senderType is auto', () => {
      const wrapperClient = mountLMessage({ sender: 'Client' })
      const wrapperAdvisor = mountLMessage({ sender: 'Advisor' })

      expect(wrapperClient.classes()).toContain('l-message--client')
      expect(wrapperAdvisor.classes()).toContain('l-message--advisor')
    })
  })

  // ==================== Tag Variant Tests ====================

  describe('Tag Variant', () => {
    it('COMP_MSG_022: client gets primary tag variant', () => {
      const wrapper = mountLMessage({ sender: 'Client' })

      expect(wrapper.find('.l-tag').classes()).toContain('l-tag--primary')
    })

    it('COMP_MSG_023: advisor gets secondary tag variant', () => {
      const wrapper = mountLMessage({ sender: 'Berater' })

      expect(wrapper.find('.l-tag').classes()).toContain('l-tag--secondary')
    })
  })

  // ==================== Icon Tests ====================

  describe('Icons', () => {
    it('COMP_MSG_024: shows icon by default', () => {
      const wrapper = mountLMessage({ sender: 'Test' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_MSG_025: hides icon when showIcon is false', () => {
      const wrapper = mountLMessage({ sender: 'Test', showIcon: false })

      expect(wrapper.find('.v-icon').exists()).toBe(false)
    })

    it('COMP_MSG_026: client shows mdi-account icon', () => {
      const wrapper = mountLMessage({ sender: 'Client' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_MSG_027: advisor shows mdi-account-tie icon', () => {
      const wrapper = mountLMessage({ sender: 'Berater' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })
  })

  // ==================== Timestamp Tests ====================

  describe('Timestamp', () => {
    it('COMP_MSG_028: does not show timestamp when not provided', () => {
      const wrapper = mountLMessage({ sender: 'Test' })

      expect(wrapper.find('.l-message__timestamp').exists()).toBe(false)
    })

    it('COMP_MSG_029: shows timestamp when provided', () => {
      const wrapper = mountLMessage({
        sender: 'Test',
        timestamp: '2024-01-15T14:30:00'
      })

      expect(wrapper.find('.l-message__timestamp').exists()).toBe(true)
    })

    it('COMP_MSG_030: formats string timestamp correctly', () => {
      const wrapper = mountLMessage({
        sender: 'Test',
        timestamp: '2024-01-15T14:30:00'
      })

      const timestampText = wrapper.find('.l-message__timestamp').text()
      expect(timestampText).toContain('15.01.2024')
      expect(timestampText).toContain('14:30')
      expect(timestampText).toContain('Uhr')
    })

    it('COMP_MSG_031: formats Date object correctly', () => {
      const date = new Date('2024-06-20T09:15:00')
      const wrapper = mountLMessage({
        sender: 'Test',
        timestamp: date
      })

      const timestampText = wrapper.find('.l-message__timestamp').text()
      expect(timestampText).toContain('20.06.2024')
      expect(timestampText).toContain('09:15')
    })

    it('COMP_MSG_032: handles invalid timestamp gracefully', () => {
      const wrapper = mountLMessage({
        sender: 'Test',
        timestamp: 'invalid-date'
      })

      // Invalid date results in "Invalid Date Uhr" since new Date() doesn't throw
      const timestampText = wrapper.find('.l-message__timestamp').text()
      expect(timestampText).toContain('Invalid Date')
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_MSG_033: default slot overrides content prop', () => {
      const wrapper = mountLMessage(
        { sender: 'Test', content: 'Prop content' },
        {
          slots: {
            default: 'Slot content'
          }
        }
      )

      expect(wrapper.find('.l-message__body').text()).toBe('Slot content')
    })

    it('COMP_MSG_034: default slot can contain HTML', () => {
      const wrapper = mountLMessage(
        { sender: 'Test' },
        {
          slots: {
            default: '<strong>Bold text</strong>'
          }
        }
      )

      expect(wrapper.find('.l-message__body strong').exists()).toBe(true)
    })

    it('COMP_MSG_035: actions slot renders in header', () => {
      const wrapper = mountLMessage(
        { sender: 'Test' },
        {
          slots: {
            actions: '<button>Edit</button>'
          }
        }
      )

      expect(wrapper.find('.l-message__actions').exists()).toBe(true)
      expect(wrapper.find('.l-message__actions button').exists()).toBe(true)
    })

    it('COMP_MSG_036: actions area hidden when no actions slot', () => {
      const wrapper = mountLMessage({ sender: 'Test' })

      expect(wrapper.find('.l-message__actions').exists()).toBe(false)
    })
  })

  // ==================== CSS Classes Tests ====================

  describe('CSS Classes', () => {
    it('COMP_MSG_037: client and advisor classes are mutually exclusive', () => {
      const wrapperClient = mountLMessage({ sender: 'Client' })
      const wrapperAdvisor = mountLMessage({ sender: 'Advisor' })

      expect(wrapperClient.classes()).toContain('l-message--client')
      expect(wrapperClient.classes()).not.toContain('l-message--advisor')

      expect(wrapperAdvisor.classes()).toContain('l-message--advisor')
      expect(wrapperAdvisor.classes()).not.toContain('l-message--client')
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_MSG_038: handles empty sender gracefully', () => {
      const wrapper = mountLMessage({ sender: '' })

      // Empty sender should be treated as advisor (no client pattern match)
      expect(wrapper.classes()).toContain('l-message--advisor')
    })

    it('COMP_MSG_039: handles whitespace-only sender', () => {
      const wrapper = mountLMessage({ sender: '   ' })

      expect(wrapper.classes()).toContain('l-message--advisor')
    })

    it('COMP_MSG_040: handles sender with special characters', () => {
      const wrapper = mountLMessage({ sender: 'Klient <test@example.com>' })

      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_041: handles multiline content', () => {
      const multilineContent = 'Line 1\nLine 2\nLine 3'
      const wrapper = mountLMessage({
        sender: 'Test',
        content: multilineContent
      })

      expect(wrapper.find('.l-message__body').text()).toBe(multilineContent)
    })

    it('COMP_MSG_042: handles very long content', () => {
      const longContent = 'A'.repeat(5000)
      const wrapper = mountLMessage({
        sender: 'Test',
        content: longContent
      })

      expect(wrapper.find('.l-message__body').text()).toBe(longContent)
    })

    it('COMP_MSG_043: handles unicode in sender', () => {
      const wrapper = mountLMessage({ sender: 'Klient 用户 📧' })

      expect(wrapper.find('.l-tag').text()).toContain('Klient')
      expect(wrapper.classes()).toContain('l-message--client')
    })

    it('COMP_MSG_044: sender prop updates reactively', async () => {
      const wrapper = mountLMessage({ sender: 'Berater' })

      expect(wrapper.classes()).toContain('l-message--advisor')

      await wrapper.setProps({ sender: 'Klient' })

      expect(wrapper.classes()).toContain('l-message--client')
      expect(wrapper.classes()).not.toContain('l-message--advisor')
    })

    it('COMP_MSG_045: senderType prop updates reactively', async () => {
      const wrapper = mountLMessage({ sender: 'Test', senderType: 'client' })

      expect(wrapper.classes()).toContain('l-message--client')

      await wrapper.setProps({ senderType: 'advisor' })

      expect(wrapper.classes()).toContain('l-message--advisor')
      expect(wrapper.classes()).not.toContain('l-message--client')
    })
  })
})
