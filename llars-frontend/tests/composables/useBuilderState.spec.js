/**
 * Tests for useBuilderState composable
 *
 * Test IDs: BSTATE_001 - BSTATE_085
 *
 * Coverage:
 * - Exports and constants
 * - Initial state
 * - Computed properties
 * - Step navigation
 * - Status transitions
 * - Crawl progress updates
 * - Embedding progress updates
 * - Error management
 * - Field generation state
 * - Reset functions
 * - Initialize from chatbot
 * - Direct setters
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  useBuilderState,
  BUILD_STATUS,
  CRAWL_STAGE,
  WIZARD_STEPS
} from '@/composables/useBuilderState'

describe('useBuilderState Composable', () => {
  describe('Exports', () => {
    it('BSTATE_001: exports useBuilderState function', () => {
      expect(typeof useBuilderState).toBe('function')
    })

    it('BSTATE_002: exports BUILD_STATUS constant', () => {
      expect(BUILD_STATUS).toBeDefined()
      expect(BUILD_STATUS.DRAFT).toBe('draft')
      expect(BUILD_STATUS.CRAWLING).toBe('crawling')
      expect(BUILD_STATUS.EMBEDDING).toBe('embedding')
      expect(BUILD_STATUS.CONFIGURING).toBe('configuring')
      expect(BUILD_STATUS.READY).toBe('ready')
      expect(BUILD_STATUS.ERROR).toBe('error')
      expect(BUILD_STATUS.PAUSED).toBe('paused')
    })

    it('BSTATE_003: exports CRAWL_STAGE constant', () => {
      expect(CRAWL_STAGE).toBeDefined()
      expect(CRAWL_STAGE.IDLE).toBe('idle')
      expect(CRAWL_STAGE.PLANNING).toBe('planning')
      expect(CRAWL_STAGE.PLANNING_DONE).toBe('planning_done')
      expect(CRAWL_STAGE.CRAWLING).toBe('crawling')
      expect(CRAWL_STAGE.COMPLETED).toBe('completed')
    })

    it('BSTATE_004: exports WIZARD_STEPS constant', () => {
      expect(WIZARD_STEPS).toBeDefined()
      expect(WIZARD_STEPS.URL_INPUT).toBe(1)
      expect(WIZARD_STEPS.CRAWLING).toBe(2)
      expect(WIZARD_STEPS.EMBEDDING).toBe(3)
      expect(WIZARD_STEPS.CONFIGURATION).toBe(4)
      expect(WIZARD_STEPS.COMPLETE).toBe(5)
    })

    it('BSTATE_005: returns all expected properties', () => {
      const state = useBuilderState()

      // State
      expect(state).toHaveProperty('currentStep')
      expect(state).toHaveProperty('loading')
      expect(state).toHaveProperty('chatbotId')
      expect(state).toHaveProperty('buildStatus')
      expect(state).toHaveProperty('wizardData')
      expect(state).toHaveProperty('crawlerConfig')
      expect(state).toHaveProperty('crawlProgress')
      expect(state).toHaveProperty('embeddingProgress')
      expect(state).toHaveProperty('errors')
      expect(state).toHaveProperty('generating')

      // Computed
      expect(state).toHaveProperty('isProcessing')
      expect(state).toHaveProperty('isCrawling')
      expect(state).toHaveProperty('isEmbedding')
      expect(state).toHaveProperty('crawlProgressPercent')

      // Functions
      expect(state).toHaveProperty('setStatus')
      expect(state).toHaveProperty('updateCrawlProgress')
      expect(state).toHaveProperty('resetWizard')
    })
  })

  describe('Initial State', () => {
    it('BSTATE_006: currentStep starts at URL_INPUT', () => {
      const { currentStep } = useBuilderState()
      expect(currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
    })

    it('BSTATE_007: loading starts as false', () => {
      const { loading } = useBuilderState()
      expect(loading.value).toBe(false)
    })

    it('BSTATE_008: chatbotId starts as null', () => {
      const { chatbotId } = useBuilderState()
      expect(chatbotId.value).toBe(null)
    })

    it('BSTATE_009: buildStatus starts as DRAFT', () => {
      const { buildStatus } = useBuilderState()
      expect(buildStatus.value).toBe(BUILD_STATUS.DRAFT)
    })

    it('BSTATE_010: wizardData has default values', () => {
      const { wizardData } = useBuilderState()

      expect(wizardData.value.url).toBe('')
      expect(wizardData.value.name).toBe('')
      expect(wizardData.value.displayName).toBe('')
      expect(wizardData.value.systemPrompt).toBe('Du bist ein hilfreicher Assistent.')
      expect(wizardData.value.icon).toBe('mdi-robot')
      expect(wizardData.value.color).toBe('#5d7a4a')
    })

    it('BSTATE_011: crawlerConfig has default values', () => {
      const { crawlerConfig } = useBuilderState()

      expect(crawlerConfig.value.maxPages).toBe(50)
      expect(crawlerConfig.value.maxDepth).toBe(3)
      expect(crawlerConfig.value.usePlaywright).toBe(true)
      expect(crawlerConfig.value.takeScreenshots).toBe(true)
    })

    it('BSTATE_012: crawlProgress has initial values', () => {
      const { crawlProgress } = useBuilderState()

      expect(crawlProgress.value.stage).toBe(CRAWL_STAGE.IDLE)
      expect(crawlProgress.value.pagesProcessed).toBe(0)
      expect(crawlProgress.value.pagesTotal).toBe(0)
      expect(crawlProgress.value.recentPages).toEqual([])
    })

    it('BSTATE_013: embeddingProgress has initial values', () => {
      const { embeddingProgress } = useBuilderState()

      expect(embeddingProgress.value.progress).toBe(0)
      expect(embeddingProgress.value.documentsTotal).toBe(0)
      expect(embeddingProgress.value.chunksTotal).toBe(0)
    })

    it('BSTATE_014: errors start as null', () => {
      const { errors } = useBuilderState()

      expect(errors.value.url).toBe(null)
      expect(errors.value.crawl).toBe(null)
      expect(errors.value.embedding).toBe(null)
      expect(errors.value.config).toBe(null)
      expect(errors.value.general).toBe(null)
    })

    it('BSTATE_015: generating states start as false', () => {
      const { generating } = useBuilderState()

      expect(generating.value.name).toBe(false)
      expect(generating.value.display_name).toBe(false)
      expect(generating.value.system_prompt).toBe(false)
    })
  })

  describe('Computed Properties', () => {
    it('BSTATE_016: isProcessing is true during crawling', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CRAWLING)
      expect(state.isProcessing.value).toBe(true)
    })

    it('BSTATE_017: isProcessing is true during embedding', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.EMBEDDING)
      expect(state.isProcessing.value).toBe(true)
    })

    it('BSTATE_018: isProcessing is false for other statuses', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CONFIGURING)
      expect(state.isProcessing.value).toBe(false)
    })

    it('BSTATE_019: isCrawling reflects crawling status', () => {
      const state = useBuilderState()
      expect(state.isCrawling.value).toBe(false)
      state.setStatus(BUILD_STATUS.CRAWLING)
      expect(state.isCrawling.value).toBe(true)
    })

    it('BSTATE_020: isEmbedding reflects embedding status', () => {
      const state = useBuilderState()
      expect(state.isEmbedding.value).toBe(false)
      state.setStatus(BUILD_STATUS.EMBEDDING)
      expect(state.isEmbedding.value).toBe(true)
    })

    it('BSTATE_021: isConfiguring reflects configuring status', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CONFIGURING)
      expect(state.isConfiguring.value).toBe(true)
    })

    it('BSTATE_022: isReady reflects ready status', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.READY)
      expect(state.isReady.value).toBe(true)
    })

    it('BSTATE_023: hasError reflects error status', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.ERROR)
      expect(state.hasError.value).toBe(true)
    })

    it('BSTATE_024: isPaused reflects paused status', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.PAUSED)
      expect(state.isPaused.value).toBe(true)
    })

    it('BSTATE_025: crawlProgressPercent calculates correctly', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({ urlsTotal: 100, urlsCompleted: 50 })
      expect(state.crawlProgressPercent.value).toBe(50)
    })

    it('BSTATE_026: crawlProgressPercent returns 0 when total is 0', () => {
      const state = useBuilderState()
      expect(state.crawlProgressPercent.value).toBe(0)
    })

    it('BSTATE_027: crawlProgressPercent caps at 100', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({ urlsTotal: 50, urlsCompleted: 100 })
      expect(state.crawlProgressPercent.value).toBe(100)
    })

    it('BSTATE_028: embeddingProgressPercent reflects progress', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress({ progress: 75 })
      expect(state.embeddingProgressPercent.value).toBe(75)
    })

    it('BSTATE_029: hasAnyError detects errors', () => {
      const state = useBuilderState()
      expect(state.hasAnyError.value).toBe(false)
      state.setError('url', 'Invalid URL')
      expect(state.hasAnyError.value).toBe(true)
    })

    it('BSTATE_030: totalDocuments sums created and linked', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({ documentsCreated: 10, documentsLinked: 5 })
      expect(state.totalDocuments.value).toBe(15)
    })

    it('BSTATE_031: isAnyFieldGenerating detects generating fields', () => {
      const state = useBuilderState()
      expect(state.isAnyFieldGenerating.value).toBe(false)
      state.setGenerating('name', true)
      expect(state.isAnyFieldGenerating.value).toBe(true)
    })
  })

  describe('Step Navigation', () => {
    it('BSTATE_032: canNavigateToStep allows step 1 always', () => {
      const state = useBuilderState()
      expect(state.canNavigateToStep(WIZARD_STEPS.URL_INPUT)).toBe(true)
    })

    it('BSTATE_033: canNavigateToStep blocks step 2+ without chatbotId', () => {
      const state = useBuilderState()
      expect(state.canNavigateToStep(WIZARD_STEPS.CRAWLING)).toBe(false)
    })

    it('BSTATE_034: canNavigateToStep allows step 2-4 with chatbotId', () => {
      const state = useBuilderState()
      state.setChatbotId('test-id')

      expect(state.canNavigateToStep(WIZARD_STEPS.CRAWLING)).toBe(true)
      expect(state.canNavigateToStep(WIZARD_STEPS.EMBEDDING)).toBe(true)
      expect(state.canNavigateToStep(WIZARD_STEPS.CONFIGURATION)).toBe(true)
    })

    it('BSTATE_035: canNavigateToStep blocks step 5 unless ready', () => {
      const state = useBuilderState()
      state.setChatbotId('test-id')

      expect(state.canNavigateToStep(WIZARD_STEPS.COMPLETE)).toBe(false)

      state.setStatus(BUILD_STATUS.READY)
      expect(state.canNavigateToStep(WIZARD_STEPS.COMPLETE)).toBe(true)
    })

    it('BSTATE_036: navigateToStep changes currentStep', () => {
      const state = useBuilderState()
      state.setChatbotId('test-id')

      const result = state.navigateToStep(WIZARD_STEPS.CRAWLING)
      expect(result).toBe(true)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.CRAWLING)
    })

    it('BSTATE_037: navigateToStep returns false for invalid navigation', () => {
      const state = useBuilderState()
      const result = state.navigateToStep(WIZARD_STEPS.CRAWLING)
      expect(result).toBe(false)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
    })
  })

  describe('Status Transitions', () => {
    it('BSTATE_038: setStatus changes buildStatus', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CRAWLING)
      expect(state.buildStatus.value).toBe(BUILD_STATUS.CRAWLING)
    })

    it('BSTATE_039: setStatus rejects invalid status', () => {
      const state = useBuilderState()
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const result = state.setStatus('invalid-status')
      expect(result).toBe(false)
      expect(state.buildStatus.value).toBe(BUILD_STATUS.DRAFT)

      consoleSpy.mockRestore()
    })

    it('BSTATE_040: setStatus with ERROR sets error message', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.ERROR, 'Something went wrong')
      expect(state.errors.value.general).toBe('Something went wrong')
    })

    it('BSTATE_041: setStatus auto-advances step to CRAWLING', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CRAWLING)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.CRAWLING)
    })

    it('BSTATE_042: setStatus auto-advances step to EMBEDDING', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.EMBEDDING)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.EMBEDDING)
    })

    it('BSTATE_043: setStatus auto-advances step to CONFIGURATION', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.CONFIGURING)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.CONFIGURATION)
    })

    it('BSTATE_044: setStatus auto-advances step to COMPLETE when ready', () => {
      const state = useBuilderState()
      state.setStatus(BUILD_STATUS.READY)
      expect(state.currentStep.value).toBe(WIZARD_STEPS.COMPLETE)
    })
  })

  describe('Crawl Progress Updates', () => {
    it('BSTATE_045: updateCrawlProgress handles snake_case data', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({
        pages_crawled: 10,
        max_pages: 50,
        urls_total: 100,
        urls_completed: 25
      })

      expect(state.crawlProgress.value.pagesProcessed).toBe(25)
      expect(state.crawlProgress.value.urlsTotal).toBe(100)
      expect(state.crawlProgress.value.urlsCompleted).toBe(25)
    })

    it('BSTATE_046: updateCrawlProgress handles camelCase data', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({
        pagesProcessed: 15,
        pagesTotal: 60,
        urlsTotal: 80,
        urlsCompleted: 40
      })

      // pagesProcessed syncs with urlsCompleted
      expect(state.crawlProgress.value.pagesProcessed).toBe(40)
      // pagesTotal is set explicitly, not overwritten by urlsTotal sync
      expect(state.crawlProgress.value.pagesTotal).toBe(60)
      expect(state.crawlProgress.value.urlsTotal).toBe(80)
    })

    it('BSTATE_047: updateCrawlProgress updates documents', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({
        documents_created: 20,
        documents_linked: 5
      })

      expect(state.crawlProgress.value.documentsCreated).toBe(20)
      expect(state.crawlProgress.value.documentsLinked).toBe(5)
    })

    it('BSTATE_048: updateCrawlProgress updates stage without regression', () => {
      const state = useBuilderState()

      state.updateCrawlProgress({ stage: CRAWL_STAGE.PLANNING })
      expect(state.crawlProgress.value.stage).toBe(CRAWL_STAGE.PLANNING)

      state.updateCrawlProgress({ stage: CRAWL_STAGE.CRAWLING })
      expect(state.crawlProgress.value.stage).toBe(CRAWL_STAGE.CRAWLING)

      // Should not regress
      state.updateCrawlProgress({ stage: CRAWL_STAGE.PLANNING })
      expect(state.crawlProgress.value.stage).toBe(CRAWL_STAGE.CRAWLING)
    })

    it('BSTATE_049: updateCrawlProgress updates currentUrl', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({ current_url: 'https://example.com/page' })
      expect(state.crawlProgress.value.currentUrl).toBe('https://example.com/page')
    })

    it('BSTATE_050: updateCrawlProgress updates message', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({ message: 'Processing...' })
      expect(state.crawlProgress.value.message).toBe('Processing...')
    })

    it('BSTATE_051: addRecentPage adds URL to list', () => {
      const state = useBuilderState()
      state.addRecentPage('https://example.com/page1')
      state.addRecentPage('https://example.com/page2')

      expect(state.crawlProgress.value.recentPages).toContain('https://example.com/page1')
      expect(state.crawlProgress.value.recentPages).toContain('https://example.com/page2')
    })

    it('BSTATE_052: addRecentPage limits to 20 pages', () => {
      const state = useBuilderState()

      for (let i = 0; i < 25; i++) {
        state.addRecentPage(`https://example.com/page${i}`)
      }

      expect(state.crawlProgress.value.recentPages.length).toBe(20)
      expect(state.crawlProgress.value.recentPages[0]).toBe('https://example.com/page5')
    })

    it('BSTATE_053: addRecentPage ignores empty URL', () => {
      const state = useBuilderState()
      state.addRecentPage('')
      state.addRecentPage(null)
      expect(state.crawlProgress.value.recentPages.length).toBe(0)
    })

    it('BSTATE_054: updateElapsedTime calculates from startTime', () => {
      const state = useBuilderState()
      const now = Date.now()

      state.startCrawlTimer()

      // Wait a tiny bit
      vi.spyOn(Date, 'now').mockReturnValue(now + 5000)
      state.updateElapsedTime()

      expect(state.crawlProgress.value.elapsedTime).toBeCloseTo(5, 0)

      vi.restoreAllMocks()
    })
  })

  describe('Embedding Progress Updates', () => {
    it('BSTATE_055: updateEmbeddingProgress handles number', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress(75)
      expect(state.embeddingProgress.value.progress).toBe(75)
    })

    it('BSTATE_056: updateEmbeddingProgress handles object', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress({
        progress: 50,
        documents_total: 100,
        documents_processed: 50,
        chunks_total: 500,
        chunks_completed: 250
      })

      expect(state.embeddingProgress.value.progress).toBe(50)
      expect(state.embeddingProgress.value.documentsTotal).toBe(100)
      expect(state.embeddingProgress.value.documentsProcessed).toBe(50)
      expect(state.embeddingProgress.value.chunksTotal).toBe(500)
      expect(state.embeddingProgress.value.chunksProcessed).toBe(250)
    })

    it('BSTATE_057: updateEmbeddingProgress updates currentDocument', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress({ current_document: 'doc1.pdf' })
      expect(state.embeddingProgress.value.currentDocument).toBe('doc1.pdf')
    })

    it('BSTATE_058: updateCollectionInfo merges info', () => {
      const state = useBuilderState()
      state.updateCollectionInfo({ name: 'Test Collection' })
      state.updateCollectionInfo({ documentCount: 10 })

      expect(state.collectionInfo.value.name).toBe('Test Collection')
      expect(state.collectionInfo.value.documentCount).toBe(10)
    })
  })

  describe('Error Management', () => {
    it('BSTATE_059: setError sets specific error type', () => {
      const state = useBuilderState()
      state.setError('url', 'Invalid URL format')
      expect(state.errors.value.url).toBe('Invalid URL format')
    })

    it('BSTATE_060: setError falls back to general for unknown type', () => {
      const state = useBuilderState()
      state.setError('unknown', 'Unknown error')
      expect(state.errors.value.general).toBe('Unknown error')
    })

    it('BSTATE_061: clearError clears specific error', () => {
      const state = useBuilderState()
      state.setError('url', 'Error')
      state.setError('crawl', 'Another error')

      state.clearError('url')
      expect(state.errors.value.url).toBe(null)
      expect(state.errors.value.crawl).toBe('Another error')
    })

    it('BSTATE_062: clearError without type clears all errors', () => {
      const state = useBuilderState()
      state.setError('url', 'Error 1')
      state.setError('crawl', 'Error 2')
      state.setError('general', 'Error 3')

      state.clearError()

      expect(state.errors.value.url).toBe(null)
      expect(state.errors.value.crawl).toBe(null)
      expect(state.errors.value.general).toBe(null)
    })
  })

  describe('Field Generation', () => {
    it('BSTATE_063: setGenerating updates field state', () => {
      const state = useBuilderState()
      state.setGenerating('name', true)
      expect(state.generating.value.name).toBe(true)
    })

    it('BSTATE_064: setGenerating can disable field', () => {
      const state = useBuilderState()
      state.setGenerating('name', true)
      state.setGenerating('name', false)
      expect(state.generating.value.name).toBe(false)
    })

    it('BSTATE_065: setGenerating ignores unknown fields', () => {
      const state = useBuilderState()
      state.setGenerating('unknown_field', true)
      expect(state.generating.value).not.toHaveProperty('unknown_field')
    })
  })

  describe('Reset Functions', () => {
    it('BSTATE_066: resetCrawlProgress resets to initial values', () => {
      const state = useBuilderState()
      state.updateCrawlProgress({
        urlsTotal: 100,
        urlsCompleted: 50,
        stage: CRAWL_STAGE.CRAWLING
      })

      state.resetCrawlProgress()

      expect(state.crawlProgress.value.stage).toBe(CRAWL_STAGE.IDLE)
      expect(state.crawlProgress.value.urlsTotal).toBe(0)
      expect(state.crawlProgress.value.pagesProcessed).toBe(0)
    })

    it('BSTATE_067: resetEmbeddingProgress resets to initial values', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress({ progress: 75, documents_total: 100 })

      state.resetEmbeddingProgress()

      expect(state.embeddingProgress.value.progress).toBe(0)
      expect(state.embeddingProgress.value.documentsTotal).toBe(0)
    })

    it('BSTATE_068: resetWizard resets all state', () => {
      const state = useBuilderState()

      // Modify various state
      state.setChatbotId('test-id')
      state.setStatus(BUILD_STATUS.CRAWLING)
      state.wizardData.value.url = 'https://example.com'
      state.setError('url', 'Error')
      state.setGenerating('name', true)

      state.resetWizard()

      expect(state.currentStep.value).toBe(WIZARD_STEPS.URL_INPUT)
      expect(state.chatbotId.value).toBe(null)
      expect(state.buildStatus.value).toBe(BUILD_STATUS.DRAFT)
      expect(state.wizardData.value.url).toBe('')
      expect(state.errors.value.url).toBe(null)
      expect(state.generating.value.name).toBe(false)
    })

    it('BSTATE_069: resetWizard restores default wizardData', () => {
      const state = useBuilderState()
      state.wizardData.value.systemPrompt = 'Custom prompt'
      state.wizardData.value.icon = 'mdi-custom'

      state.resetWizard()

      expect(state.wizardData.value.systemPrompt).toBe('Du bist ein hilfreicher Assistent.')
      expect(state.wizardData.value.icon).toBe('mdi-robot')
    })

    it('BSTATE_070: resetWizard restores default crawlerConfig', () => {
      const state = useBuilderState()
      state.crawlerConfig.value.maxPages = 200
      state.crawlerConfig.value.maxDepth = 10

      state.resetWizard()

      expect(state.crawlerConfig.value.maxPages).toBe(50)
      expect(state.crawlerConfig.value.maxDepth).toBe(3)
    })
  })

  describe('Initialize from Chatbot', () => {
    it('BSTATE_071: initFromChatbot sets chatbotId', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: 'chatbot-123' })
      expect(state.chatbotId.value).toBe('chatbot-123')
    })

    it('BSTATE_072: initFromChatbot sets build_status', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: '1', build_status: BUILD_STATUS.CONFIGURING })
      expect(state.buildStatus.value).toBe(BUILD_STATUS.CONFIGURING)
    })

    it('BSTATE_073: initFromChatbot populates wizardData', () => {
      const state = useBuilderState()
      state.initFromChatbot({
        id: '1',
        source_url: 'https://example.com',
        name: 'my-bot',
        display_name: 'My Bot',
        system_prompt: 'Custom prompt',
        model_name: 'gpt-4',
        welcome_message: 'Hello!',
        fallback_message: 'Sorry...',
        icon: 'mdi-star',
        color: '#ff0000'
      })

      expect(state.wizardData.value.url).toBe('https://example.com')
      expect(state.wizardData.value.name).toBe('my-bot')
      expect(state.wizardData.value.displayName).toBe('My Bot')
      expect(state.wizardData.value.systemPrompt).toBe('Custom prompt')
      expect(state.wizardData.value.modelName).toBe('gpt-4')
      expect(state.wizardData.value.welcomeMessage).toBe('Hello!')
      expect(state.wizardData.value.fallbackMessage).toBe('Sorry...')
      expect(state.wizardData.value.icon).toBe('mdi-star')
      expect(state.wizardData.value.color).toBe('#ff0000')
    })

    it('BSTATE_074: initFromChatbot sets step based on CRAWLING status', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: '1', build_status: BUILD_STATUS.CRAWLING })
      expect(state.currentStep.value).toBe(WIZARD_STEPS.CRAWLING)
    })

    it('BSTATE_075: initFromChatbot sets step based on EMBEDDING status', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: '1', build_status: BUILD_STATUS.EMBEDDING })
      expect(state.currentStep.value).toBe(WIZARD_STEPS.EMBEDDING)
    })

    it('BSTATE_076: initFromChatbot sets step based on CONFIGURING status', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: '1', build_status: BUILD_STATUS.CONFIGURING })
      expect(state.currentStep.value).toBe(WIZARD_STEPS.CONFIGURATION)
    })

    it('BSTATE_077: initFromChatbot sets step based on READY status', () => {
      const state = useBuilderState()
      state.initFromChatbot({ id: '1', build_status: BUILD_STATUS.READY })
      expect(state.currentStep.value).toBe(WIZARD_STEPS.COMPLETE)
    })

    it('BSTATE_078: initFromChatbot handles null chatbot', () => {
      const state = useBuilderState()
      state.initFromChatbot(null)
      expect(state.chatbotId.value).toBe(null)
    })
  })

  describe('Direct Setters', () => {
    it('BSTATE_079: setChatbotId sets chatbotId', () => {
      const state = useBuilderState()
      state.setChatbotId('new-id')
      expect(state.chatbotId.value).toBe('new-id')
    })

    it('BSTATE_080: setCrawlerJobId sets crawlerJobId', () => {
      const state = useBuilderState()
      state.setCrawlerJobId('job-123')
      expect(state.crawlerJobId.value).toBe('job-123')
    })

    it('BSTATE_081: setCollectionId sets collectionId', () => {
      const state = useBuilderState()
      state.setCollectionId('col-456')
      expect(state.collectionId.value).toBe('col-456')
    })

    it('BSTATE_082: setLoading sets loading state', () => {
      const state = useBuilderState()
      state.setLoading(true)
      expect(state.loading.value).toBe(true)
      state.setLoading(false)
      expect(state.loading.value).toBe(false)
    })

    it('BSTATE_083: startCrawlTimer sets startTime', () => {
      const state = useBuilderState()
      const before = Date.now()
      state.startCrawlTimer()
      const after = Date.now()

      expect(state.crawlProgress.value.startTime).toBeGreaterThanOrEqual(before)
      expect(state.crawlProgress.value.startTime).toBeLessThanOrEqual(after)
    })
  })

  describe('Edge Cases', () => {
    it('BSTATE_084: multiple instances are independent', () => {
      const state1 = useBuilderState()
      const state2 = useBuilderState()

      state1.setChatbotId('bot-1')
      state2.setChatbotId('bot-2')

      expect(state1.chatbotId.value).toBe('bot-1')
      expect(state2.chatbotId.value).toBe('bot-2')
    })

    it('BSTATE_085: embeddingProgressPercent caps at 100', () => {
      const state = useBuilderState()
      state.updateEmbeddingProgress(150)
      expect(state.embeddingProgressPercent.value).toBe(100)
    })
  })
})
