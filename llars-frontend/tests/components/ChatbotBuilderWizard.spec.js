import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import ChatbotBuilderWizard from '@/components/Admin/ChatbotAdmin/ChatbotBuilderWizard.vue'
import axios from 'axios'

const vuetify = createVuetify({ components, directives })

const socketHandlers = {}
const mockSocket = {
  on: vi.fn((event, handler) => {
    socketHandlers[event] = handler
  }),
  off: vi.fn((event) => {
    delete socketHandlers[event]
  }),
  emit: vi.fn()
}

vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

vi.mock('@/services/socketService', () => ({
  getSocket: () => mockSocket,
  useSocketState: () => ({ isConnected: ref(true) })
}))

vi.mock('@/composables/useFieldGenerationService', () => ({
  fieldGenerationService: {
    subscribeToField: vi.fn(() => () => {}),
    getAllFieldContents: vi.fn(() => ({})),
    getGeneratingFields: vi.fn(() => ({})),
    isGenerating: vi.fn(() => false),
    generateField: vi.fn(),
    clearSession: vi.fn()
  }
}))

vi.mock('@/utils/logI18n', () => ({
  logI18n: vi.fn(),
  logI18nParams: vi.fn()
}))

function mountWizard() {
  return mount(ChatbotBuilderWizard, {
    props: {
      resumeChatbotId: 7
    },
    global: {
      plugins: [vuetify],
      stubs: {
        StepCrawlerConfig: true,
        StepChatbotConfig: true,
        StepReview: true,
        LBtn: {
          template: '<button><slot /></button>'
        },
        LTag: {
          template: '<span><slot /></span>'
        }
      }
    }
  })
}

describe('ChatbotBuilderWizard', () => {
  beforeEach(() => {
    Object.keys(socketHandlers).forEach(key => delete socketHandlers[key])
    mockSocket.on.mockClear()
    mockSocket.off.mockClear()
    mockSocket.emit.mockClear()
    axios.get.mockReset()
    axios.post.mockReset()
  })

  it('resyncs on missing crawler session instead of showing a fatal error banner', async () => {
    axios.get
      .mockResolvedValueOnce({
        data: {
          success: true,
          build_status: 'crawling',
          collection: {
            id: 11,
            crawl_job_id: 'job-1',
            embedding_progress: 0
          }
        }
      })
      .mockResolvedValueOnce({
        data: {
          chatbot: {
            id: 7,
            source_url: 'https://example.com',
            name: 'example-bot',
            display_name: 'Example Bot',
            system_prompt: 'Du bist hilfreich.'
          }
        }
      })
      .mockResolvedValueOnce({
        data: {
          success: true,
          build_status: 'crawling',
          collection: {
            id: 11,
            crawl_job_id: 'job-1',
            embedding_progress: 0
          }
        }
      })
      .mockResolvedValueOnce({
        data: {
          chatbot: {
            id: 7,
            source_url: 'https://example.com',
            name: 'example-bot',
            display_name: 'Example Bot',
            system_prompt: 'Du bist hilfreich.'
          }
        }
      })

    const wrapper = mountWizard()
    await flushPromises()

    expect(mockSocket.emit).toHaveBeenCalledWith('crawler:get_status', { session_id: 'job-1' })
    expect(socketHandlers['crawler:error']).toBeTypeOf('function')

    socketHandlers['crawler:error']({
      session_id: 'job-1',
      error: 'Session not found'
    })
    await flushPromises()

    expect(axios.get).toHaveBeenCalledTimes(4)
    expect(wrapper.text()).toContain(
      'Crawler-Live-Session nicht mehr verfügbar. Der aktuelle Status wird aus dem Backend synchronisiert...'
    )
    expect(wrapper.text()).not.toContain(
      'Crawler-Session nicht mehr verfügbar (Backend neu gestartet oder Crawl beendet). Live-Updates sind nicht verfügbar.'
    )
  })
})
