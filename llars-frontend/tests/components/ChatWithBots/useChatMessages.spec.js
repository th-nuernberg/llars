/**
 * useChatMessages Composable Tests
 *
 * Tests for message manipulation, file type detection, and REST API calls.
 * Test IDs: CHAT_MSG_001 - CHAT_MSG_030
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'

vi.mock('axios', () => ({
  default: {
    post: vi.fn()
  }
}))

vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn()
}))

import axios from 'axios'
import { useChatMessages } from '@/components/ChatWithBots/composables/useChatMessages'

describe('useChatMessages', () => {
  let chat

  beforeEach(() => {
    vi.clearAllMocks()
    chat = useChatMessages()
  })

  // ==================== Initial State ====================

  describe('initial state', () => {
    it('CHAT_MSG_001: starts not processing', () => {
      expect(chat.isProcessing.value).toBe(false)
    })

    it('CHAT_MSG_002: starts with empty sources', () => {
      expect(chat.currentSources.value).toEqual([])
    })
  })

  // ==================== addUserMessage ====================

  describe('addUserMessage', () => {
    it('CHAT_MSG_003: adds text message', () => {
      const messages = ref([])
      const msg = chat.addUserMessage(messages, 'Hello')

      expect(messages.value).toHaveLength(1)
      expect(msg.content).toBe('Hello')
      expect(msg.sender).toBe('user')
      expect(msg.files).toEqual([])
    })

    it('CHAT_MSG_004: adds message with files', () => {
      const messages = ref([])
      const files = [{ name: 'test.pdf' }, { name: 'image.png' }]
      const msg = chat.addUserMessage(messages, 'See files', files)

      expect(msg.files).toHaveLength(2)
      expect(msg.files[0].filename).toBe('test.pdf')
      expect(msg.files[0].type).toBe('pdf')
      expect(msg.files[1].type).toBe('image')
    })

    it('CHAT_MSG_005: uses fallback content when no message but has files', () => {
      const messages = ref([])
      const files = [{ name: 'doc.pdf' }]
      const msg = chat.addUserMessage(messages, '', files)

      expect(msg.content).toBe('(Dateien hochgeladen)')
    })

    it('CHAT_MSG_006: sets timestamp', () => {
      const messages = ref([])
      const msg = chat.addUserMessage(messages, 'test')

      expect(msg.timestamp).toBeDefined()
      expect(typeof msg.timestamp).toBe('string')
    })
  })

  // ==================== addBotPlaceholder ====================

  describe('addBotPlaceholder', () => {
    it('CHAT_MSG_007: adds empty bot message with streaming flag', () => {
      const messages = ref([])
      const msg = chat.addBotPlaceholder(messages)

      expect(messages.value).toHaveLength(1)
      expect(msg.sender).toBe('bot')
      expect(msg.content).toBe('')
      expect(msg.streaming).toBe(true)
    })
  })

  // ==================== updateBotMessage ====================

  describe('updateBotMessage', () => {
    it('CHAT_MSG_008: updates last bot message', () => {
      const messages = ref([
        { id: 1, sender: 'user', content: 'Hi' },
        { id: 2, sender: 'bot', content: '', streaming: true }
      ])

      chat.updateBotMessage(messages, 'Response here', '12:00', false, [{ id: 1 }])

      expect(messages.value[1].content).toBe('Response here')
      expect(messages.value[1].timestamp).toBe('12:00')
      expect(messages.value[1].streaming).toBe(false)
      expect(messages.value[1].sources).toEqual([{ id: 1 }])
    })

    it('CHAT_MSG_009: does nothing if last message is not bot', () => {
      const messages = ref([
        { id: 1, sender: 'user', content: 'Hi' }
      ])

      chat.updateBotMessage(messages, 'Response', '12:00')

      expect(messages.value[0].content).toBe('Hi')
    })

    it('CHAT_MSG_010: does nothing for empty messages array', () => {
      const messages = ref([])

      expect(() => chat.updateBotMessage(messages, 'Response', '12:00')).not.toThrow()
    })

    it('CHAT_MSG_011: omits sources when null', () => {
      const messages = ref([
        { id: 1, sender: 'bot', content: '', streaming: true }
      ])

      chat.updateBotMessage(messages, 'Response', '12:00', false, null)

      expect(messages.value[0].sources).toBeUndefined()
    })
  })

  // ==================== setBotError ====================

  describe('setBotError', () => {
    it('CHAT_MSG_012: sets error message on last bot message', () => {
      const messages = ref([
        { id: 1, sender: 'bot', content: '', streaming: true }
      ])

      chat.setBotError(messages, 'Custom error')

      expect(messages.value[0].content).toBe('Custom error')
      expect(messages.value[0].streaming).toBe(false)
    })

    it('CHAT_MSG_013: uses default error message', () => {
      const messages = ref([
        { id: 1, sender: 'bot', content: '', streaming: true }
      ])

      chat.setBotError(messages)

      expect(messages.value[0].content).toContain('Fehler')
    })
  })

  // ==================== getFileType ====================

  describe('getFileType', () => {
    it('CHAT_MSG_014: detects image types', () => {
      expect(chat.getFileType('photo.png')).toBe('image')
      expect(chat.getFileType('photo.jpg')).toBe('image')
      expect(chat.getFileType('photo.jpeg')).toBe('image')
      expect(chat.getFileType('photo.gif')).toBe('image')
      expect(chat.getFileType('photo.webp')).toBe('image')
    })

    it('CHAT_MSG_015: detects PDF', () => {
      expect(chat.getFileType('document.pdf')).toBe('pdf')
    })

    it('CHAT_MSG_016: detects Word documents', () => {
      expect(chat.getFileType('file.doc')).toBe('word')
      expect(chat.getFileType('file.docx')).toBe('word')
    })

    it('CHAT_MSG_017: detects Excel files', () => {
      expect(chat.getFileType('data.xls')).toBe('excel')
      expect(chat.getFileType('data.xlsx')).toBe('excel')
    })

    it('CHAT_MSG_018: detects PowerPoint files', () => {
      expect(chat.getFileType('slides.ppt')).toBe('powerpoint')
      expect(chat.getFileType('slides.pptx')).toBe('powerpoint')
    })

    it('CHAT_MSG_019: returns document for unknown types', () => {
      expect(chat.getFileType('file.txt')).toBe('document')
      expect(chat.getFileType('file.csv')).toBe('document')
    })
  })

  // ==================== sendViaREST ====================

  describe('sendViaREST', () => {
    it('CHAT_MSG_020: sends text message via REST', async () => {
      axios.post.mockResolvedValue({
        data: {
          success: true,
          response: 'Bot reply',
          sources: [],
          conversation_id: 'conv-1',
          session_id: 'sess-1',
          title: 'Test Chat'
        }
      })

      const result = await chat.sendViaREST('bot-1', 'Hello', 'sess-1')

      expect(result.success).toBe(true)
      expect(result.content).toBe('Bot reply')
      expect(result.conversationId).toBe('conv-1')
      expect(axios.post).toHaveBeenCalledWith(
        '/api/chatbots/bot-1/chat',
        {
          message: 'Hello',
          session_id: 'sess-1',
          include_sources: true,
          conversation_id: null
        }
      )
    })

    it('CHAT_MSG_021: sends message with files via FormData', async () => {
      axios.post.mockResolvedValue({
        data: { success: true, response: 'Got files', sources: [] }
      })

      const files = [new File(['data'], 'test.pdf')]
      const result = await chat.sendViaREST('bot-1', 'See file', 'sess-1', files)

      expect(result.success).toBe(true)
      expect(axios.post.mock.calls[0][1]).toBeInstanceOf(FormData)
    })

    it('CHAT_MSG_022: returns error on API failure', async () => {
      axios.post.mockRejectedValue({
        response: { data: { error: 'Server error' } }
      })

      const result = await chat.sendViaREST('bot-1', 'Hello', 'sess-1')

      expect(result.success).toBe(false)
      expect(result.error).toBe('Server error')
    })

    it('CHAT_MSG_023: handles unsuccessful response', async () => {
      axios.post.mockResolvedValue({
        data: { success: false, error: 'Bot unavailable' }
      })

      const result = await chat.sendViaREST('bot-1', 'Hello', 'sess-1')

      expect(result.success).toBe(false)
    })
  })
})
