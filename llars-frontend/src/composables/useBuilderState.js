/**
 * Chatbot Builder State Management Composable
 *
 * Manages the state for the multi-step chatbot builder wizard.
 * Handles wizard data, progress tracking, and step navigation.
 */

import { ref, computed } from 'vue'

export function useBuilderState() {
  // Core state
  const currentStep = ref(1)
  const loading = ref(false)
  const chatbotId = ref(null)
  const buildStatus = ref('draft')
  const crawlerJobId = ref(null)

  // Wizard data
  const wizardData = ref({
    url: '',
    name: '',
    displayName: '',
    systemPrompt: 'Du bist ein hilfreicher Assistent.',
    welcomeMessage: '',
    icon: 'mdi-robot',
    color: '#5d7a4a'
  })

  // Crawler configuration
  const crawlerConfig = ref({
    maxPages: 50,
    maxDepth: 3
  })

  // Progress tracking
  const crawlProgress = ref({
    pagesProcessed: 0,
    pagesTotal: 0,
    documentsCreated: 0,
    documentsLinked: 0,
    currentUrl: '',
    recentPages: [],
    elapsedTime: 0,
    startTime: null
  })

  const embeddingProgress = ref(0)
  const collectionInfo = ref(null)

  // Error tracking
  const errors = ref({
    url: null,
    crawl: null,
    general: null
  })

  // Field generation tracking
  const generating = ref({
    name: false,
    display_name: false,
    system_prompt: false,
    welcome_message: false
  })

  // Computed
  const isProcessing = computed(() => {
    return ['crawling', 'embedding'].includes(buildStatus.value)
  })

  const crawlProgressPercent = computed(() => {
    if (crawlProgress.value.pagesTotal === 0) return 0
    return Math.round((crawlProgress.value.pagesProcessed / crawlProgress.value.pagesTotal) * 100)
  })

  // Step navigation
  const canNavigateToStep = (step) => {
    // Can always go back to previous steps
    if (step < currentStep.value) return true

    // Can navigate forward based on build status
    switch (buildStatus.value) {
      case 'draft':
        return step <= 1
      case 'crawling':
        // During crawling, allow skip to step 4 (configuration)
        return step <= 4
      case 'embedding':
        // During embedding, allow skip to step 4 (configuration)
        return step <= 4
      case 'configuring':
        return step <= 4
      case 'ready':
        return step <= 5
      default:
        return step <= currentStep.value
    }
  }

  const navigateToStep = (step) => {
    if (!canNavigateToStep(step)) return

    // Handle navigation logic
    if (step === 4 && currentStep.value < 4) {
      // Skip to configuration
      currentStep.value = 4
    } else {
      currentStep.value = step
    }
  }

  // Progress updates
  const updateCrawlProgress = (data) => {
    if (data.pages_crawled !== undefined) {
      crawlProgress.value.pagesProcessed = data.pages_crawled
    }
    if (data.max_pages !== undefined) {
      crawlProgress.value.pagesTotal = data.max_pages
    }
    if (data.current_url) {
      crawlProgress.value.currentUrl = data.current_url
    }
    if (data.documents_created !== undefined) {
      crawlProgress.value.documentsCreated = data.documents_created
    }
    if (data.documents_linked !== undefined) {
      crawlProgress.value.documentsLinked = data.documents_linked
    }
  }

  const updateElapsedTime = () => {
    if (crawlProgress.value.startTime) {
      crawlProgress.value.elapsedTime = (Date.now() - crawlProgress.value.startTime) / 1000
    }
  }

  const addRecentPage = (url) => {
    crawlProgress.value.recentPages.push(url)
  }

  const updateEmbeddingProgress = (progress) => {
    embeddingProgress.value = progress
  }

  const updateCollectionInfo = (info) => {
    collectionInfo.value = info
  }

  // Reset functions
  const resetWizard = () => {
    currentStep.value = 1
    chatbotId.value = null
    crawlerJobId.value = null
    buildStatus.value = 'draft'
    embeddingProgress.value = 0
    collectionInfo.value = null
    crawlProgress.value = {
      pagesProcessed: 0,
      pagesTotal: 0,
      documentsCreated: 0,
      documentsLinked: 0,
      currentUrl: '',
      recentPages: [],
      elapsedTime: 0,
      startTime: null
    }
    errors.value = { url: null, crawl: null, general: null }
    wizardData.value = {
      url: '',
      name: '',
      displayName: '',
      systemPrompt: 'Du bist ein hilfreicher Assistent.',
      welcomeMessage: '',
      icon: 'mdi-robot',
      color: '#5d7a4a'
    }
  }

  const resetErrors = () => {
    errors.value = { url: null, crawl: null, general: null }
  }

  return {
    // State
    currentStep,
    loading,
    chatbotId,
    buildStatus,
    crawlerJobId,
    wizardData,
    crawlerConfig,
    crawlProgress,
    embeddingProgress,
    collectionInfo,
    errors,
    generating,

    // Computed
    isProcessing,
    crawlProgressPercent,

    // Navigation
    canNavigateToStep,
    navigateToStep,

    // Updates
    updateCrawlProgress,
    updateElapsedTime,
    addRecentPage,
    updateEmbeddingProgress,
    updateCollectionInfo,

    // Reset
    resetWizard,
    resetErrors
  }
}

export default useBuilderState
