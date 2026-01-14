/**
 * Chatbot Builder State Management Composable
 *
 * Manages the state for the multi-step chatbot builder wizard.
 * Provides centralized state management with clear status transitions.
 *
 * Build Status Flow:
 *   draft -> crawling -> embedding -> configuring -> ready
 *                  \-> error (from any state)
 *                  \-> paused (from crawling/embedding)
 */

import { ref, computed, readonly } from 'vue'
import { logI18nParams } from '@/utils/logI18n'

// Valid build status values
export const BUILD_STATUS = {
  DRAFT: 'draft',
  CRAWLING: 'crawling',
  EMBEDDING: 'embedding',
  CONFIGURING: 'configuring',
  READY: 'ready',
  ERROR: 'error',
  PAUSED: 'paused'
}

// Valid crawl stages
export const CRAWL_STAGE = {
  IDLE: 'idle',
  PLANNING: 'planning',
  PLANNING_DONE: 'planning_done',
  CRAWLING: 'crawling',
  COMPLETED: 'completed'
}

// Step definitions
export const WIZARD_STEPS = {
  URL_INPUT: 1,
  CRAWLING: 2,
  EMBEDDING: 3,
  CONFIGURATION: 4,
  COMPLETE: 5
}

export function useBuilderState() {
  // ===== Core State =====
  const currentStep = ref(WIZARD_STEPS.URL_INPUT)
  const loading = ref(false)
  const chatbotId = ref(null)
  const buildStatus = ref(BUILD_STATUS.DRAFT)
  const crawlerJobId = ref(null)
  const collectionId = ref(null)

  // ===== Wizard Data =====
  const wizardData = ref({
    url: '',
    name: '',
    displayName: '',
    systemPrompt: 'Du bist ein hilfreicher Assistent.',
    modelName: '',
    welcomeMessage: '',
    fallbackMessage: 'Entschuldigung, ich konnte keine passende Antwort finden.',
    icon: 'mdi-robot',
    color: '#5d7a4a'
  })

  // ===== Crawler Configuration =====
  const crawlerConfig = ref({
    maxPages: 50,
    maxDepth: 3,
    usePlaywright: true,
    useVisionLlm: false,
    takeScreenshots: true
  })

  // ===== Crawl Progress =====
  const crawlProgress = ref({
    stage: CRAWL_STAGE.IDLE,
    pagesProcessed: 0,
    pagesTotal: 0,
    urlsTotal: 0,
    urlsCompleted: 0,
    documentsCreated: 0,
    documentsLinked: 0,
    imagesExtracted: 0,
    screenshotsTaken: 0,
    currentUrl: '',
    recentPages: [],
    elapsedTime: 0,
    startTime: null,
    crawlerType: 'basic',
    message: ''
  })

  // ===== Embedding Progress =====
  const embeddingProgress = ref({
    progress: 0,
    documentsTotal: 0,
    documentsProcessed: 0,
    chunksTotal: 0,
    chunksProcessed: 0,
    currentDocument: ''
  })

  // ===== Collection Info =====
  const collectionInfo = ref(null)

  // ===== Error State =====
  const errors = ref({
    url: null,
    crawl: null,
    embedding: null,
    config: null,
    general: null
  })

  // ===== Field Generation State =====
  const generating = ref({
    name: false,
    display_name: false,
    system_prompt: false,
    welcome_message: false,
    icon: false,
    color: false
  })

  // ===== Computed Properties =====
  const isProcessing = computed(() => {
    return [BUILD_STATUS.CRAWLING, BUILD_STATUS.EMBEDDING].includes(buildStatus.value)
  })

  const isCrawling = computed(() => buildStatus.value === BUILD_STATUS.CRAWLING)
  const isEmbedding = computed(() => buildStatus.value === BUILD_STATUS.EMBEDDING)
  const isConfiguring = computed(() => buildStatus.value === BUILD_STATUS.CONFIGURING)
  const isReady = computed(() => buildStatus.value === BUILD_STATUS.READY)
  const hasError = computed(() => buildStatus.value === BUILD_STATUS.ERROR)
  const isPaused = computed(() => buildStatus.value === BUILD_STATUS.PAUSED)

  const crawlProgressPercent = computed(() => {
    const total = crawlProgress.value.urlsTotal || crawlProgress.value.pagesTotal
    if (total === 0) return 0
    const completed = crawlProgress.value.urlsCompleted || crawlProgress.value.pagesProcessed
    return Math.min(100, Math.round((completed / total) * 100))
  })

  const embeddingProgressPercent = computed(() => {
    return Math.min(100, Math.round(embeddingProgress.value.progress || 0))
  })

  const hasAnyError = computed(() => {
    return Object.values(errors.value).some(e => e !== null)
  })

  const totalDocuments = computed(() => {
    return crawlProgress.value.documentsCreated + crawlProgress.value.documentsLinked
  })

  // ===== Step Navigation =====
  const canNavigateToStep = (step) => {
    // Step 1 is always accessible
    if (step === WIZARD_STEPS.URL_INPUT) return true

    // Must have chatbotId for steps 2+
    if (!chatbotId.value) return false

    // Step 2-4 are accessible once chatbot exists
    if (step >= WIZARD_STEPS.CRAWLING && step <= WIZARD_STEPS.CONFIGURATION) {
      return true
    }

    // Step 5 only when ready
    if (step === WIZARD_STEPS.COMPLETE) {
      return buildStatus.value === BUILD_STATUS.READY
    }

    return false
  }

  const navigateToStep = (step) => {
    if (!canNavigateToStep(step)) return false
    currentStep.value = step
    return true
  }

  // ===== Status Transitions =====
  const setStatus = (newStatus, errorMessage = null) => {
    const validStatuses = Object.values(BUILD_STATUS)
    if (!validStatuses.includes(newStatus)) {
      logI18nParams('error', 'logs.builder.invalidStatus', { status: newStatus })
      return false
    }

    buildStatus.value = newStatus

    if (newStatus === BUILD_STATUS.ERROR && errorMessage) {
      errors.value.general = errorMessage
    }

    // Auto-advance step based on status
    if (newStatus === BUILD_STATUS.CRAWLING && currentStep.value < WIZARD_STEPS.CRAWLING) {
      currentStep.value = WIZARD_STEPS.CRAWLING
    } else if (newStatus === BUILD_STATUS.EMBEDDING && currentStep.value < WIZARD_STEPS.EMBEDDING) {
      currentStep.value = WIZARD_STEPS.EMBEDDING
    } else if (newStatus === BUILD_STATUS.CONFIGURING && currentStep.value < WIZARD_STEPS.CONFIGURATION) {
      currentStep.value = WIZARD_STEPS.CONFIGURATION
    } else if (newStatus === BUILD_STATUS.READY) {
      currentStep.value = WIZARD_STEPS.COMPLETE
    }

    return true
  }

  // ===== Progress Updates =====
  const updateCrawlProgress = (data) => {
    // Handle both snake_case (from backend) and camelCase (from mapping)
    if (data.pages_crawled !== undefined || data.pagesProcessed !== undefined) {
      crawlProgress.value.pagesProcessed = data.pages_crawled ?? data.pagesProcessed
    }
    if (data.max_pages !== undefined || data.pagesTotal !== undefined) {
      crawlProgress.value.pagesTotal = data.max_pages ?? data.pagesTotal
    }
    if (data.urls_total !== undefined || data.urlsTotal !== undefined) {
      crawlProgress.value.urlsTotal = data.urls_total ?? data.urlsTotal
      // Keep pagesTotal in sync for legacy progress bar
      if (!data.max_pages && !data.pagesTotal) {
        crawlProgress.value.pagesTotal = data.urls_total ?? data.urlsTotal
      }
    }
    if (data.urls_completed !== undefined || data.urlsCompleted !== undefined) {
      crawlProgress.value.urlsCompleted = data.urls_completed ?? data.urlsCompleted
      crawlProgress.value.pagesProcessed = data.urls_completed ?? data.urlsCompleted
    }
    if (data.documents_created !== undefined || data.documentsCreated !== undefined) {
      crawlProgress.value.documentsCreated = data.documents_created ?? data.documentsCreated
    }
    if (data.documents_linked !== undefined || data.documentsLinked !== undefined) {
      crawlProgress.value.documentsLinked = data.documents_linked ?? data.documentsLinked
    }
    if (data.images_extracted !== undefined || data.imagesExtracted !== undefined) {
      crawlProgress.value.imagesExtracted = data.images_extracted ?? data.imagesExtracted
    }
    if (data.screenshots_taken !== undefined || data.screenshotsTaken !== undefined) {
      crawlProgress.value.screenshotsTaken = data.screenshots_taken ?? data.screenshotsTaken
    }
    if (data.current_url || data.currentUrl) {
      crawlProgress.value.currentUrl = data.current_url || data.currentUrl
    }
    if (data.stage) {
      // Prevent stage regression (causes UI flicker between Phase 1/2)
      const stageRank = {
        [CRAWL_STAGE.IDLE]: 0,
        [CRAWL_STAGE.PLANNING]: 1,
        [CRAWL_STAGE.PLANNING_DONE]: 2,
        [CRAWL_STAGE.CRAWLING]: 3,
        [CRAWL_STAGE.COMPLETED]: 4
      }
      const current = crawlProgress.value.stage
      const next = data.stage
      const currentRank = stageRank[current] ?? 0
      const nextRank = stageRank[next]
      if (nextRank !== undefined && nextRank >= currentRank) {
        crawlProgress.value.stage = next
      }
    }
    if (data.crawler_type || data.crawlerType) {
      crawlProgress.value.crawlerType = data.crawler_type || data.crawlerType
    }
    if (data.message) {
      crawlProgress.value.message = data.message
    }
  }

  const updateElapsedTime = () => {
    if (crawlProgress.value.startTime) {
      crawlProgress.value.elapsedTime = (Date.now() - crawlProgress.value.startTime) / 1000
    }
  }

  const addRecentPage = (url) => {
    if (!url) return
    // Limit to last 20 pages
    if (crawlProgress.value.recentPages.length >= 20) {
      crawlProgress.value.recentPages.shift()
    }
    crawlProgress.value.recentPages.push(url)
  }

  const updateEmbeddingProgress = (data) => {
    if (typeof data === 'number') {
      embeddingProgress.value.progress = data
    } else if (typeof data === 'object') {
      if (data.progress !== undefined) {
        embeddingProgress.value.progress = data.progress
      }
      if (data.current_document !== undefined || data.currentDocument !== undefined) {
        embeddingProgress.value.currentDocument = data.current_document ?? data.currentDocument ?? ''
      }
      if (data.documents_total !== undefined) {
        embeddingProgress.value.documentsTotal = data.documents_total
      }
      if (data.documents_processed !== undefined) {
        embeddingProgress.value.documentsProcessed = data.documents_processed
      }
      if (data.chunks_total !== undefined) {
        embeddingProgress.value.chunksTotal = data.chunks_total
      }
      if (data.chunks_completed !== undefined) {
        embeddingProgress.value.chunksProcessed = data.chunks_completed
      }
    }
  }

  const updateCollectionInfo = (info) => {
    if (!info) return
    collectionInfo.value = {
      ...collectionInfo.value,
      ...info
    }
  }

  // ===== Error Management =====
  const setError = (type, message) => {
    if (type in errors.value) {
      errors.value[type] = message
    } else {
      errors.value.general = message
    }
  }

  const clearError = (type) => {
    if (type) {
      if (type in errors.value) {
        errors.value[type] = null
      }
    } else {
      // Clear all errors
      Object.keys(errors.value).forEach(key => {
        errors.value[key] = null
      })
    }
  }

  // ===== Field Generation =====
  const setGenerating = (field, isGenerating) => {
    if (field in generating.value) {
      generating.value[field] = isGenerating
    }
  }

  const isAnyFieldGenerating = computed(() => {
    return Object.values(generating.value).some(v => v)
  })

  // ===== Reset Functions =====
  const resetCrawlProgress = () => {
    crawlProgress.value = {
      stage: CRAWL_STAGE.IDLE,
      pagesProcessed: 0,
      pagesTotal: 0,
      urlsTotal: 0,
      urlsCompleted: 0,
      documentsCreated: 0,
      documentsLinked: 0,
      imagesExtracted: 0,
      screenshotsTaken: 0,
      currentUrl: '',
      recentPages: [],
      elapsedTime: 0,
      startTime: null,
      crawlerType: 'basic',
      message: ''
    }
  }

  const resetEmbeddingProgress = () => {
    embeddingProgress.value = {
      progress: 0,
      documentsTotal: 0,
      documentsProcessed: 0,
      chunksTotal: 0,
      chunksProcessed: 0
    }
  }

  const resetWizard = () => {
    currentStep.value = WIZARD_STEPS.URL_INPUT
    loading.value = false
    chatbotId.value = null
    crawlerJobId.value = null
    collectionId.value = null
    buildStatus.value = BUILD_STATUS.DRAFT

    wizardData.value = {
      url: '',
      name: '',
      displayName: '',
      systemPrompt: 'Du bist ein hilfreicher Assistent.',
      modelName: '',
      welcomeMessage: '',
      fallbackMessage: 'Entschuldigung, ich konnte keine passende Antwort finden.',
      icon: 'mdi-robot',
      color: '#5d7a4a'
    }

    crawlerConfig.value = {
      maxPages: 50,
      maxDepth: 3,
      usePlaywright: true,
      useVisionLlm: false,
      takeScreenshots: true
    }

    resetCrawlProgress()
    resetEmbeddingProgress()
    collectionInfo.value = null
    clearError()

    // Reset all generating states
    generating.value = {
      name: false,
      display_name: false,
      system_prompt: false,
      welcome_message: false,
      icon: false,
      color: false
    }
  }

  // ===== Initialize from existing chatbot =====
  const initFromChatbot = (chatbot) => {
    if (!chatbot) return

    chatbotId.value = chatbot.id
    buildStatus.value = chatbot.build_status || BUILD_STATUS.DRAFT

    if (chatbot.source_url) {
      wizardData.value.url = chatbot.source_url
    }
    if (chatbot.name) {
      wizardData.value.name = chatbot.name
    }
    if (chatbot.display_name) {
      wizardData.value.displayName = chatbot.display_name
    }
    if (chatbot.system_prompt) {
      wizardData.value.systemPrompt = chatbot.system_prompt
    }
    if (chatbot.model_name) {
      wizardData.value.modelName = chatbot.model_name
    }
    if (chatbot.welcome_message) {
      wizardData.value.welcomeMessage = chatbot.welcome_message
    }
    if (chatbot.fallback_message) {
      wizardData.value.fallbackMessage = chatbot.fallback_message
    }
    if (chatbot.icon) {
      wizardData.value.icon = chatbot.icon
    }
    if (chatbot.color) {
      wizardData.value.color = chatbot.color
    }

    // Set step based on status
    switch (buildStatus.value) {
      case BUILD_STATUS.CRAWLING:
        currentStep.value = WIZARD_STEPS.CRAWLING
        break
      case BUILD_STATUS.EMBEDDING:
        currentStep.value = WIZARD_STEPS.EMBEDDING
        break
      case BUILD_STATUS.CONFIGURING:
        currentStep.value = WIZARD_STEPS.CONFIGURATION
        break
      case BUILD_STATUS.READY:
        currentStep.value = WIZARD_STEPS.COMPLETE
        break
      default:
        currentStep.value = WIZARD_STEPS.URL_INPUT
    }
  }

  return {
    // State (readonly where possible)
    currentStep,
    loading,
    chatbotId,
    buildStatus: readonly(buildStatus),
    crawlerJobId,
    collectionId,
    wizardData,
    crawlerConfig,
    crawlProgress: readonly(crawlProgress),
    embeddingProgress: readonly(embeddingProgress),
    collectionInfo: readonly(collectionInfo),
    errors: readonly(errors),
    generating: readonly(generating),

    // Computed
    isProcessing,
    isCrawling,
    isEmbedding,
    isConfiguring,
    isReady,
    hasError,
    isPaused,
    crawlProgressPercent,
    embeddingProgressPercent,
    hasAnyError,
    totalDocuments,
    isAnyFieldGenerating,

    // Navigation
    canNavigateToStep,
    navigateToStep,

    // Status
    setStatus,

    // Progress Updates
    updateCrawlProgress,
    updateElapsedTime,
    addRecentPage,
    updateEmbeddingProgress,
    updateCollectionInfo,

    // Error Management
    setError,
    clearError,

    // Field Generation
    setGenerating,

    // Reset
    resetCrawlProgress,
    resetEmbeddingProgress,
    resetWizard,

    // Initialize
    initFromChatbot,

    // Direct setters for specific fields
    setChatbotId: (id) => { chatbotId.value = id },
    setCrawlerJobId: (id) => { crawlerJobId.value = id },
    setCollectionId: (id) => { collectionId.value = id },
    setLoading: (val) => { loading.value = val },
    startCrawlTimer: () => { crawlProgress.value.startTime = Date.now() }
  }
}

export default useBuilderState
