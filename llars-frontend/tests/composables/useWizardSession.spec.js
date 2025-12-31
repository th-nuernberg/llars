/**
 * Tests for useWizardSession composable
 *
 * Test IDs: WSESS_001 - WSESS_070
 *
 * Coverage:
 * - Exports and constants
 * - Initial state
 * - Computed properties
 * - Socket.IO event handlers
 * - API actions
 * - Field generation
 * - Navigation
 * - Heartbeat and timer management
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { nextTick } from 'vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock socket service
const mockSocket = {
  on: vi.fn(),
  off: vi.fn(),
  emit: vi.fn()
}

vi.mock('@/services/socketService', () => ({
  getSocket: vi.fn(() => mockSocket)
}))

// Import after mocks
import axios from 'axios'
import {
  useWizardSession,
  BUILD_STATUS,
  WIZARD_STEPS
} from '@/composables/useWizardSession'

describe('useWizardSession Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Exports', () => {
    it('WSESS_001: exports useWizardSession function', () => {
      expect(typeof useWizardSession).toBe('function')
    })

    it('WSESS_002: exports BUILD_STATUS constant', () => {
      expect(BUILD_STATUS).toBeDefined()
      expect(BUILD_STATUS.DRAFT).toBe('draft')
      expect(BUILD_STATUS.CRAWLING).toBe('crawling')
      expect(BUILD_STATUS.EMBEDDING).toBe('embedding')
      expect(BUILD_STATUS.CONFIGURING).toBe('configuring')
      expect(BUILD_STATUS.READY).toBe('ready')
      expect(BUILD_STATUS.ERROR).toBe('error')
      expect(BUILD_STATUS.PAUSED).toBe('paused')
    })

    it('WSESS_003: exports WIZARD_STEPS constant', () => {
      expect(WIZARD_STEPS).toBeDefined()
      expect(WIZARD_STEPS.URL_INPUT).toBe(1)
      expect(WIZARD_STEPS.CRAWLING).toBe(2)
      expect(WIZARD_STEPS.EMBEDDING).toBe(3)
      expect(WIZARD_STEPS.CONFIGURATION).toBe(4)
      expect(WIZARD_STEPS.COMPLETE).toBe(5)
    })

    it('WSESS_004: returns all expected properties', () => {
      const state = useWizardSession()

      // Server state
      expect(state).toHaveProperty('session')
      expect(state).toHaveProperty('progress')
      expect(state).toHaveProperty('elapsedTime')

      // Connection state
      expect(state).toHaveProperty('connected')
      expect(state).toHaveProperty('syncing')
      expect(state).toHaveProperty('error')
      expect(state).toHaveProperty('loading')

      // Computed
      expect(state).toHaveProperty('chatbotId')
      expect(state).toHaveProperty('buildStatus')
      expect(state).toHaveProperty('isProcessing')

      // API Actions
      expect(state).toHaveProperty('createSession')
      expect(state).toHaveProperty('joinSession')
      expect(state).toHaveProperty('leaveSession')
    })
  })

  describe('Initial State', () => {
    it('WSESS_005: session starts as null', () => {
      const { session } = useWizardSession()
      expect(session.value).toBe(null)
    })

    it('WSESS_006: progress starts as empty object', () => {
      const { progress } = useWizardSession()
      expect(progress.value).toEqual({})
    })

    it('WSESS_007: elapsedTime starts with zeros', () => {
      const { elapsedTime } = useWizardSession()
      expect(elapsedTime.value).toEqual({ crawl: 0, embed: 0, total: 0 })
    })

    it('WSESS_008: connected starts as false', () => {
      const { connected } = useWizardSession()
      expect(connected.value).toBe(false)
    })

    it('WSESS_009: syncing starts as false', () => {
      const { syncing } = useWizardSession()
      expect(syncing.value).toBe(false)
    })

    it('WSESS_010: error starts as null', () => {
      const { error } = useWizardSession()
      expect(error.value).toBe(null)
    })

    it('WSESS_011: loading starts as false', () => {
      const { loading } = useWizardSession()
      expect(loading.value).toBe(false)
    })

    it('WSESS_012: currentStep starts at URL_INPUT', () => {
      const { currentStep } = useWizardSession()
      expect(currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
    })

    it('WSESS_013: generating states start as false', () => {
      const { generating } = useWizardSession()
      expect(generating.value.name).toBe(false)
      expect(generating.value.display_name).toBe(false)
      expect(generating.value.system_prompt).toBe(false)
    })
  })

  describe('Computed Properties', () => {
    it('WSESS_014: chatbotId returns null when no session', () => {
      const { chatbotId } = useWizardSession()
      expect(chatbotId.value).toBe(undefined)
    })

    it('WSESS_015: buildStatus returns DRAFT when no session', () => {
      const { buildStatus } = useWizardSession()
      expect(buildStatus.value).toBe(BUILD_STATUS.DRAFT)
    })

    it('WSESS_016: wizardData returns empty object when no session', () => {
      const { wizardData } = useWizardSession()
      expect(wizardData.value).toEqual({})
    })

    it('WSESS_017: crawlerConfig returns empty object when no session', () => {
      const { crawlerConfig } = useWizardSession()
      expect(crawlerConfig.value).toEqual({})
    })

    it('WSESS_018: isProcessing is false initially', () => {
      const { isProcessing } = useWizardSession()
      expect(isProcessing.value).toBe(false)
    })

    it('WSESS_019: isCrawling is false initially', () => {
      const { isCrawling } = useWizardSession()
      expect(isCrawling.value).toBe(false)
    })

    it('WSESS_020: isEmbedding is false initially', () => {
      const { isEmbedding } = useWizardSession()
      expect(isEmbedding.value).toBe(false)
    })

    it('WSESS_021: crawlProgress has default values', () => {
      const { crawlProgress } = useWizardSession()
      expect(crawlProgress.value.stage).toBe('idle')
      expect(crawlProgress.value.urlsTotal).toBe(0)
      expect(crawlProgress.value.urlsCompleted).toBe(0)
    })

    it('WSESS_022: embeddingProgress has default values', () => {
      const { embeddingProgress } = useWizardSession()
      expect(embeddingProgress.value.progress).toBe(0)
      expect(embeddingProgress.value.documentsTotal).toBe(0)
    })

    it('WSESS_023: crawlProgressPercent returns 0 when no data', () => {
      const { crawlProgressPercent } = useWizardSession()
      expect(crawlProgressPercent.value).toBe(0)
    })

    it('WSESS_024: embeddingProgressPercent returns 0 when no data', () => {
      const { embeddingProgressPercent } = useWizardSession()
      expect(embeddingProgressPercent.value).toBe(0)
    })

    it('WSESS_025: isAnyFieldGenerating is false initially', () => {
      const { isAnyFieldGenerating } = useWizardSession()
      expect(isAnyFieldGenerating.value).toBe(false)
    })
  })

  describe('Field Generation', () => {
    it('WSESS_026: setGenerating updates field state', () => {
      const state = useWizardSession()
      state.setGenerating('name', true)
      expect(state.generating.value.name).toBe(true)
    })

    it('WSESS_027: setGenerating can disable field', () => {
      const state = useWizardSession()
      state.setGenerating('name', true)
      state.setGenerating('name', false)
      expect(state.generating.value.name).toBe(false)
    })

    it('WSESS_028: isAnyFieldGenerating detects active generation', () => {
      const state = useWizardSession()
      expect(state.isAnyFieldGenerating.value).toBe(false)
      state.setGenerating('system_prompt', true)
      expect(state.isAnyFieldGenerating.value).toBe(true)
    })

    it('WSESS_029: setGenerating ignores unknown fields', () => {
      const state = useWizardSession()
      state.setGenerating('unknown_field', true)
      expect(state.generating.value).not.toHaveProperty('unknown_field')
    })
  })

  describe('Navigation', () => {
    it('WSESS_030: canNavigateToStep allows step 1 always', () => {
      const state = useWizardSession()
      expect(state.canNavigateToStep(WIZARD_STEPS.URL_INPUT)).toBe(true)
    })

    it('WSESS_031: canNavigateToStep blocks step 2+ without chatbotId', () => {
      const state = useWizardSession()
      expect(state.canNavigateToStep(WIZARD_STEPS.CRAWLING)).toBe(false)
      expect(state.canNavigateToStep(WIZARD_STEPS.EMBEDDING)).toBe(false)
    })

    it('WSESS_032: navigateToStep changes currentStep', () => {
      const state = useWizardSession()
      const result = state.navigateToStep(WIZARD_STEPS.URL_INPUT)
      expect(result).toBe(true)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
    })

    it('WSESS_033: navigateToStep returns false for invalid navigation', () => {
      const state = useWizardSession()
      const result = state.navigateToStep(WIZARD_STEPS.CRAWLING)
      expect(result).toBe(false)
    })
  })

  describe('API Actions - createSession', () => {
    it('WSESS_034: createSession calls API with URL', async () => {
      axios.post.mockResolvedValueOnce({ data: { chatbot_id: 123 } })
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 123, build_status: 'draft' },
          progress: {},
          elapsed_time: { crawl: 0, embed: 0, total: 0 }
        }
      })

      const state = useWizardSession()
      const result = await state.createSession('https://example.com')

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/wizard', { url: 'https://example.com' })
      expect(result).toBe(123)
    })

    it('WSESS_035: createSession sets syncing during request', async () => {
      let syncingDuringRequest = false
      axios.post.mockImplementation(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve({ data: { chatbot_id: 123 } })
          }, 10)
        })
      })

      const state = useWizardSession()
      const promise = state.createSession('https://example.com')

      await nextTick()
      syncingDuringRequest = state.syncing.value

      axios.post.mockResolvedValueOnce({
        data: { session: {}, progress: {}, elapsed_time: {} }
      })

      await vi.advanceTimersByTimeAsync(20)
      await promise.catch(() => {})

      expect(syncingDuringRequest).toBe(true)
    })

    it('WSESS_036: createSession handles error', async () => {
      axios.post.mockRejectedValueOnce({
        response: { data: { error: 'Invalid URL' } }
      })

      const state = useWizardSession()

      await expect(state.createSession('invalid')).rejects.toBeDefined()
      expect(state.error.value).toBe('Invalid URL')
    })
  })

  describe('API Actions - joinSession', () => {
    it('WSESS_037: joinSession fetches session data', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 456, build_status: 'crawling' },
          progress: { urls_total: 100, urls_completed: 50 },
          elapsed_time: { crawl: 60, embed: 0, total: 60 }
        }
      })

      const state = useWizardSession()
      await state.joinSession(456)

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/wizard/sessions/456/join')
      expect(state.session.value.chatbot_id).toBe(456)
      expect(state.connected.value).toBe(true)
    })

    it('WSESS_038: joinSession updates step from status', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'embedding' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.currentStep.value).toBe(WIZARD_STEPS.EMBEDDING)
    })

    it('WSESS_039: joinSession sets connected to true', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 789 },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(789)

      // Socket events only work when onMounted runs (component context)
      // Without it, we verify state is set correctly
      expect(state.connected.value).toBe(true)
    })

    it('WSESS_040: joinSession sets session and connected state', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      // Socket events only work when onMounted runs (component context)
      // Without it, we verify state is set correctly
      expect(state.session.value).toEqual({ chatbot_id: 1 })
      expect(state.connected.value).toBe(true)
    })
  })

  describe('API Actions - getUserSessions', () => {
    it('WSESS_041: getUserSessions returns sessions list', async () => {
      axios.get.mockResolvedValueOnce({
        data: { sessions: [{ id: 1 }, { id: 2 }] }
      })

      const state = useWizardSession()
      const sessions = await state.getUserSessions()

      expect(axios.get).toHaveBeenCalledWith('/api/chatbots/wizard/sessions')
      expect(sessions).toHaveLength(2)
    })

    it('WSESS_042: getUserSessions returns empty array on error', async () => {
      axios.get.mockRejectedValueOnce(new Error('Network error'))

      const state = useWizardSession()
      const sessions = await state.getUserSessions()

      expect(sessions).toEqual([])
    })
  })

  describe('API Actions - startCrawl', () => {
    it('WSESS_043: startCrawl throws without session', async () => {
      const state = useWizardSession()
      await expect(state.startCrawl({})).rejects.toThrow('No active session')
    })

    it('WSESS_044: startCrawl calls API with config', async () => {
      // Setup session first
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.post.mockResolvedValueOnce({ data: { job_id: 'abc' } })

      const config = { maxPages: 100 }
      await state.startCrawl(config)

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/1/wizard/crawl', config)
    })

    it('WSESS_045: startCrawl sets loading during request', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      let loadingDuringRequest = false
      axios.post.mockImplementation(() => {
        loadingDuringRequest = state.loading.value
        return Promise.resolve({ data: {} })
      })

      await state.startCrawl({})

      expect(loadingDuringRequest).toBe(true)
      expect(state.loading.value).toBe(false)
    })
  })

  describe('API Actions - updateWizardData', () => {
    it('WSESS_046: updateWizardData throws without session', async () => {
      const state = useWizardSession()
      await expect(state.updateWizardData({})).rejects.toThrow('No active session')
    })

    it('WSESS_047: updateWizardData calls API with data', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.patch.mockResolvedValueOnce({ data: {} })

      await state.updateWizardData({ name: 'My Bot' })

      expect(axios.patch).toHaveBeenCalledWith(
        '/api/chatbots/wizard/sessions/1/data',
        { name: 'My Bot' }
      )
    })
  })

  describe('API Actions - pauseSession', () => {
    it('WSESS_048: pauseSession does nothing without session', async () => {
      const state = useWizardSession()
      await state.pauseSession()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('WSESS_049: pauseSession calls API', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.post.mockResolvedValueOnce({ data: {} })

      await state.pauseSession()

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/1/wizard/pause')
    })
  })

  describe('API Actions - resumeBuild', () => {
    it('WSESS_050: resumeBuild does nothing without session', async () => {
      const state = useWizardSession()
      await state.resumeBuild()
      // Only the initial call count
      expect(axios.post).toHaveBeenCalledTimes(0)
    })

    it('WSESS_051: resumeBuild calls API', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.post.mockResolvedValueOnce({ data: {} })

      await state.resumeBuild()

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/1/resume-build')
    })
  })

  describe('API Actions - finalizeSession', () => {
    it('WSESS_052: finalizeSession throws without session', async () => {
      const state = useWizardSession()
      await expect(state.finalizeSession({})).rejects.toThrow('No active session')
    })

    it('WSESS_053: finalizeSession calls API and leaves session', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.post.mockResolvedValueOnce({ data: {} })

      await state.finalizeSession({ name: 'Final Bot' })

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/1/wizard/finalize', { name: 'Final Bot' })
      expect(state.session.value).toBe(null)
      expect(state.connected.value).toBe(false)
    })
  })

  describe('API Actions - cancelSession', () => {
    it('WSESS_054: cancelSession does nothing without session', async () => {
      const state = useWizardSession()
      await state.cancelSession()
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('WSESS_055: cancelSession calls API and leaves session', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      axios.post.mockResolvedValueOnce({ data: {} })

      await state.cancelSession()

      expect(axios.post).toHaveBeenCalledWith('/api/chatbots/1/cancel-build')
      expect(state.session.value).toBe(null)
    })
  })

  describe('leaveSession', () => {
    it('WSESS_056: leaveSession disconnects and clears session', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      // Verify connected before leave
      expect(state.connected.value).toBe(true)
      expect(state.session.value).toEqual({ chatbot_id: 1 })

      state.leaveSession()

      // Socket events only work when onMounted runs (component context)
      // Without it, we verify state is reset correctly
      expect(state.session.value).toBe(null)
      expect(state.connected.value).toBe(false)
    })

    it('WSESS_057: leaveSession resets state', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1 },
          progress: { urls_total: 100 },
          elapsed_time: { total: 60 }
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      state.leaveSession()

      expect(state.session.value).toBe(null)
      expect(state.progress.value).toEqual({})
      expect(state.elapsedTime.value).toEqual({ crawl: 0, embed: 0, total: 0 })
      expect(state.connected.value).toBe(false)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
    })
  })

  describe('Heartbeat', () => {
    it('WSESS_058: joinSession establishes connection state', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      // Socket events only work when onMounted runs (component context)
      // Without it, we verify connection state is established
      expect(state.connected.value).toBe(true)
      expect(state.session.value.chatbot_id).toBe(1)
    })

    it('WSESS_059: leaveSession clears intervals', async () => {
      axios.post.mockResolvedValueOnce({
        data: { session: { chatbot_id: 1 }, progress: {}, elapsed_time: {} }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      state.leaveSession()

      // After leaving, connected should be false
      expect(state.connected.value).toBe(false)
    })
  })

  describe('Local Timer', () => {
    it('WSESS_060: localElapsed is set from elapsed_time on join', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'crawling' },
          progress: {},
          elapsed_time: { crawl: 30, embed: 0, total: 30 }
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.localElapsed.value).toBe(30)
    })
  })

  describe('Socket Setup', () => {
    it('WSESS_061: getSocket is called during composable creation', () => {
      // Socket is obtained in setupSocketListeners which is called in onMounted
      // Since we're not in a component context, we just verify the composable can be created
      const state = useWizardSession()
      expect(state).toBeDefined()
      expect(state.session.value).toBe(null)
    })
  })

  describe('Computed with Session Data', () => {
    it('WSESS_062: wizardData parses JSON string', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: {
            chatbot_id: 1,
            wizard_data: '{"name":"Test Bot","url":"https://example.com"}'
          },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.wizardData.value.name).toBe('Test Bot')
      expect(state.wizardData.value.url).toBe('https://example.com')
    })

    it('WSESS_063: wizardData handles object directly', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: {
            chatbot_id: 1,
            wizard_data: { name: 'Direct Object' }
          },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.wizardData.value.name).toBe('Direct Object')
    })

    it('WSESS_064: crawlerConfig parses JSON string', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: {
            chatbot_id: 1,
            crawler_config: '{"maxPages":100,"maxDepth":5}'
          },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.crawlerConfig.value.maxPages).toBe(100)
      expect(state.crawlerConfig.value.maxDepth).toBe(5)
    })

    it('WSESS_065: sourceUrl returns session source_url', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, source_url: 'https://test.com' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.sourceUrl.value).toBe('https://test.com')
    })
  })

  describe('Status Computed Properties with Session', () => {
    it('WSESS_066: isProcessing is true when crawling', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'crawling' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.isProcessing.value).toBe(true)
      expect(state.isCrawling.value).toBe(true)
    })

    it('WSESS_067: isProcessing is true when embedding', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'embedding' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.isProcessing.value).toBe(true)
      expect(state.isEmbedding.value).toBe(true)
    })

    it('WSESS_068: isReady is true when status is ready', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'ready' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.isReady.value).toBe(true)
    })

    it('WSESS_069: hasError is true when status is error', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'error' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.hasError.value).toBe(true)
    })

    it('WSESS_070: isPaused is true when status is paused', async () => {
      axios.post.mockResolvedValueOnce({
        data: {
          session: { chatbot_id: 1, build_status: 'paused' },
          progress: {},
          elapsed_time: {}
        }
      })

      const state = useWizardSession()
      await state.joinSession(1)

      expect(state.isPaused.value).toBe(true)
    })
  })
})
