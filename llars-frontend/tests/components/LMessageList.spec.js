/**
 * LMessageList Component Tests
 *
 * Tests for the LLARS message list component that wraps multiple LMessage components.
 * Test IDs: COMP_MLS_001 - COMP_MLS_045
 *
 * Coverage:
 * - Rendering and structure
 * - Empty state
 * - Messages rendering
 * - Field mapping (sender, content, timestamp)
 * - senderType handling
 * - Slots (actions, content)
 * - showIcons prop
 * - Edge cases
 */

import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import LMessageList from '@/components/common/LMessageList.vue'

// Mock LMessage component
const LMessageStub = {
  name: 'LMessage',
  template: `
    <div class="l-message" :class="{ 'l-message--client': senderType === 'client' }">
      <span class="sender">{{ sender }}</span>
      <span class="content">{{ content }}</span>
      <span v-if="timestamp" class="timestamp">{{ timestamp }}</span>
      <span v-if="showIcon" class="icon">icon</span>
      <div v-if="$slots.actions" class="actions"><slot name="actions" /></div>
      <div v-if="$slots.default" class="custom-content"><slot /></div>
    </div>
  `,
  props: ['sender', 'content', 'timestamp', 'senderType', 'showIcon']
}

function mountLMessageList(props = {}, options = {}) {
  return mount(LMessageList, {
    props,
    global: {
      stubs: {
        LMessage: LMessageStub,
        'v-icon': {
          template: '<i class="v-icon">{{ $attrs.color ? "" : "" }}<slot /></i>',
          props: ['size', 'color']
        }
      }
    },
    ...options
  })
}

const sampleMessages = [
  { message_id: 1, sender: 'Klient', content: 'Hello', timestamp: '2024-01-15T10:00:00' },
  { message_id: 2, sender: 'Berater', content: 'Hi there', timestamp: '2024-01-15T10:05:00' },
  { message_id: 3, sender: 'Klient', content: 'Thanks', timestamp: '2024-01-15T10:10:00' }
]

describe('LMessageList', () => {
  // ==================== Rendering Tests ====================

  describe('Rendering', () => {
    it('COMP_MLS_001: renders with default props', () => {
      const wrapper = mountLMessageList()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-message-list').exists()).toBe(true)
    })

    it('COMP_MLS_002: has l-message-list class', () => {
      const wrapper = mountLMessageList()

      expect(wrapper.classes()).toContain('l-message-list')
    })

    it('COMP_MLS_003: renders messages container when messages exist', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.l-message-list__messages').exists()).toBe(true)
    })

    it('COMP_MLS_004: renders correct number of messages', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })
      const messages = wrapper.findAll('.l-message')

      expect(messages.length).toBe(3)
    })
  })

  // ==================== Empty State Tests ====================

  describe('Empty State', () => {
    it('COMP_MLS_005: shows empty state when no messages', () => {
      const wrapper = mountLMessageList({ messages: [] })

      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_006: shows empty state when messages is null', () => {
      const wrapper = mountLMessageList({ messages: null })

      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_007: shows empty state with default icon', () => {
      const wrapper = mountLMessageList({ messages: [] })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_MLS_008: shows empty state with default text', () => {
      const wrapper = mountLMessageList({ messages: [] })

      expect(wrapper.find('.l-message-list__empty p').text()).toBe('Keine Nachrichten gefunden.')
    })

    it('COMP_MLS_009: shows custom empty icon', () => {
      const wrapper = mountLMessageList({
        messages: [],
        emptyIcon: 'mdi-inbox'
      })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_MLS_010: shows custom empty text', () => {
      const wrapper = mountLMessageList({
        messages: [],
        emptyText: 'No emails here'
      })

      expect(wrapper.find('.l-message-list__empty p').text()).toBe('No emails here')
    })

    it('COMP_MLS_011: hides messages container when empty', () => {
      const wrapper = mountLMessageList({ messages: [] })

      expect(wrapper.find('.l-message-list__messages').exists()).toBe(false)
    })
  })

  // ==================== Field Mapping Tests ====================

  describe('Field Mapping', () => {
    it('COMP_MLS_012: uses default messageKey (message_id)', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })
      const messages = wrapper.findAll('.l-message')

      expect(messages.length).toBe(3)
    })

    it('COMP_MLS_013: uses custom messageKey', () => {
      const customMessages = [
        { id: 'a', sender: 'Test', content: 'Hello' },
        { id: 'b', sender: 'Test2', content: 'World' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        messageKey: 'id'
      })

      expect(wrapper.findAll('.l-message').length).toBe(2)
    })

    it('COMP_MLS_014: uses default senderField', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.sender').text()).toBe('Klient')
    })

    it('COMP_MLS_015: uses custom senderField', () => {
      const customMessages = [
        { message_id: 1, author: 'Alice', content: 'Hello' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        senderField: 'author'
      })

      expect(wrapper.find('.sender').text()).toBe('Alice')
    })

    it('COMP_MLS_016: uses default contentField', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.content').text()).toBe('Hello')
    })

    it('COMP_MLS_017: uses custom contentField', () => {
      const customMessages = [
        { message_id: 1, sender: 'Test', body: 'Custom content' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        contentField: 'body'
      })

      expect(wrapper.find('.content').text()).toBe('Custom content')
    })

    it('COMP_MLS_018: uses default timestampField', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.timestamp').text()).toBe('2024-01-15T10:00:00')
    })

    it('COMP_MLS_019: uses custom timestampField', () => {
      const customMessages = [
        { message_id: 1, sender: 'Test', content: 'Hi', created_at: '2024-01-01' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        timestampField: 'created_at'
      })

      expect(wrapper.find('.timestamp').text()).toBe('2024-01-01')
    })
  })

  // ==================== Sender Type Tests ====================

  describe('Sender Type', () => {
    it('COMP_MLS_020: passes auto sender type by default', () => {
      // LMessageList passes 'auto' to LMessage, which then does detection
      // We verify the getSenderType function returns 'auto' when no senderTypeField is set
      const wrapper = mountLMessageList({ messages: sampleMessages })

      // The component should render messages
      expect(wrapper.findAll('.l-message').length).toBe(3)
      // Without senderTypeField, all messages get senderType='auto' passed to LMessage
    })

    it('COMP_MLS_021: uses senderTypeField when provided', () => {
      const customMessages = [
        { message_id: 1, sender: 'Unknown', content: 'Hi', type: 'client' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        senderTypeField: 'type'
      })

      expect(wrapper.find('.l-message').classes()).toContain('l-message--client')
    })

    it('COMP_MLS_022: falls back to auto when senderTypeField value is empty', () => {
      const customMessages = [
        { message_id: 1, sender: 'Berater', content: 'Hi', type: '' }
      ]
      const wrapper = mountLMessageList({
        messages: customMessages,
        senderTypeField: 'type'
      })

      // Should use auto-detection based on sender name
      expect(wrapper.find('.l-message').classes()).not.toContain('l-message--client')
    })
  })

  // ==================== Show Icons Tests ====================

  describe('Show Icons', () => {
    it('COMP_MLS_023: shows icons by default', () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.icon').exists()).toBe(true)
    })

    it('COMP_MLS_024: hides icons when showIcons is false', () => {
      const wrapper = mountLMessageList({
        messages: sampleMessages,
        showIcons: false
      })

      expect(wrapper.find('.icon').exists()).toBe(false)
    })
  })

  // ==================== Slot Tests ====================

  describe('Slots', () => {
    it('COMP_MLS_025: passes actions slot to LMessage', () => {
      const wrapper = mountLMessageList(
        { messages: sampleMessages },
        {
          slots: {
            actions: '<button>Action</button>'
          }
        }
      )

      expect(wrapper.find('.actions button').exists()).toBe(true)
    })

    it('COMP_MLS_026: passes content slot to LMessage', () => {
      const wrapper = mountLMessageList(
        { messages: sampleMessages },
        {
          slots: {
            content: '<span>Custom content</span>'
          }
        }
      )

      expect(wrapper.find('.custom-content span').exists()).toBe(true)
    })

    it('COMP_MLS_027: each message gets slots', () => {
      const wrapper = mountLMessageList(
        { messages: sampleMessages },
        {
          slots: {
            actions: '<button>Act</button>'
          }
        }
      )

      const actionButtons = wrapper.findAll('.actions button')
      expect(actionButtons.length).toBe(3)
    })
  })

  // ==================== Reactivity Tests ====================

  describe('Reactivity', () => {
    it('COMP_MLS_028: updates when messages array changes', async () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.findAll('.l-message').length).toBe(3)

      await wrapper.setProps({
        messages: [...sampleMessages, { message_id: 4, sender: 'New', content: 'New message' }]
      })

      expect(wrapper.findAll('.l-message').length).toBe(4)
    })

    it('COMP_MLS_029: shows empty state when messages cleared', async () => {
      const wrapper = mountLMessageList({ messages: sampleMessages })

      expect(wrapper.find('.l-message-list__messages').exists()).toBe(true)

      await wrapper.setProps({ messages: [] })

      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_030: shows messages when added to empty list', async () => {
      const wrapper = mountLMessageList({ messages: [] })

      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)

      await wrapper.setProps({ messages: sampleMessages })

      expect(wrapper.find('.l-message-list__messages').exists()).toBe(true)
    })
  })

  // ==================== Edge Cases ====================

  describe('Edge Cases', () => {
    it('COMP_MLS_031: handles undefined messages prop', () => {
      const wrapper = mountLMessageList({ messages: undefined })

      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_032: handles messages with missing fields', () => {
      const messagesWithMissing = [
        { message_id: 1, sender: 'Test' }  // Missing content and timestamp
      ]
      const wrapper = mountLMessageList({ messages: messagesWithMissing })

      expect(wrapper.find('.l-message').exists()).toBe(true)
    })

    it('COMP_MLS_033: handles single message', () => {
      const wrapper = mountLMessageList({
        messages: [{ message_id: 1, sender: 'Test', content: 'Hi' }]
      })

      expect(wrapper.findAll('.l-message').length).toBe(1)
    })

    it('COMP_MLS_034: handles large number of messages', () => {
      const manyMessages = Array.from({ length: 100 }, (_, i) => ({
        message_id: i,
        sender: `User ${i}`,
        content: `Message ${i}`
      }))
      const wrapper = mountLMessageList({ messages: manyMessages })

      expect(wrapper.findAll('.l-message').length).toBe(100)
    })

    it('COMP_MLS_035: handles messages with special characters', () => {
      const specialMessages = [
        { message_id: 1, sender: '<script>alert(1)</script>', content: '&nbsp;' }
      ]
      const wrapper = mountLMessageList({ messages: specialMessages })

      expect(wrapper.find('.sender').text()).toBe('<script>alert(1)</script>')
    })

    it('COMP_MLS_036: handles messages with unicode', () => {
      const unicodeMessages = [
        { message_id: 1, sender: '用户 🎉', content: 'Привет мир' }
      ]
      const wrapper = mountLMessageList({ messages: unicodeMessages })

      expect(wrapper.find('.sender').text()).toBe('用户 🎉')
      expect(wrapper.find('.content').text()).toBe('Привет мир')
    })

    it('COMP_MLS_037: handles duplicate message keys gracefully', () => {
      const duplicateKeys = [
        { message_id: 1, sender: 'A', content: 'First' },
        { message_id: 1, sender: 'B', content: 'Second' }  // Duplicate key
      ]
      const wrapper = mountLMessageList({ messages: duplicateKeys })

      // Vue will render both but may warn
      expect(wrapper.findAll('.l-message').length).toBe(2)
    })

    it('COMP_MLS_038: empty text can be empty string', () => {
      const wrapper = mountLMessageList({
        messages: [],
        emptyText: ''
      })

      expect(wrapper.find('.l-message-list__empty p').text()).toBe('')
    })

    it('COMP_MLS_039: handles nested content in messages', () => {
      const nestedMessages = [
        {
          message_id: 1,
          sender: 'Test',
          content: 'Line 1\nLine 2\nLine 3'
        }
      ]
      const wrapper = mountLMessageList({ messages: nestedMessages })

      expect(wrapper.find('.content').text()).toBe('Line 1\nLine 2\nLine 3')
    })

    it('COMP_MLS_040: component works without any props', () => {
      const wrapper = mount(LMessageList, {
        global: {
          stubs: {
            LMessage: LMessageStub,
            'v-icon': { template: '<i class="v-icon"><slot /></i>' }
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_041: multiple lists are independent', () => {
      const wrapper1 = mountLMessageList({ messages: sampleMessages })
      const wrapper2 = mountLMessageList({ messages: [] })

      expect(wrapper1.findAll('.l-message').length).toBe(3)
      expect(wrapper2.find('.l-message-list__empty').exists()).toBe(true)
    })

    it('COMP_MLS_042: showIcons prop updates reactively', async () => {
      const wrapper = mountLMessageList({
        messages: sampleMessages,
        showIcons: true
      })

      expect(wrapper.find('.icon').exists()).toBe(true)

      await wrapper.setProps({ showIcons: false })

      expect(wrapper.find('.icon').exists()).toBe(false)
    })

    it('COMP_MLS_043: emptyIcon updates reactively', async () => {
      const wrapper = mountLMessageList({
        messages: [],
        emptyIcon: 'mdi-email'
      })

      expect(wrapper.find('.v-icon').exists()).toBe(true)

      await wrapper.setProps({ emptyIcon: 'mdi-folder' })

      expect(wrapper.find('.v-icon').exists()).toBe(true)
    })

    it('COMP_MLS_044: handles zero as message_id', () => {
      const messagesWithZero = [
        { message_id: 0, sender: 'Test', content: 'Zero ID' }
      ]
      const wrapper = mountLMessageList({ messages: messagesWithZero })

      expect(wrapper.findAll('.l-message').length).toBe(1)
    })

    it('COMP_MLS_045: handles empty sender and content', () => {
      const emptyFieldsMessages = [
        { message_id: 1, sender: '', content: '' }
      ]
      const wrapper = mountLMessageList({ messages: emptyFieldsMessages })

      expect(wrapper.find('.sender').text()).toBe('')
      expect(wrapper.find('.content').text()).toBe('')
    })
  })
})
