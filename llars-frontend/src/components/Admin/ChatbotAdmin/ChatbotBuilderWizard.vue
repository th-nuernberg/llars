<template>
  <div ref="wizardHost" class="wizard-host">
    <v-card class="wizard-card" variant="outlined">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4">
        <v-icon class="mr-2" color="primary">mdi-wizard-hat</v-icon>
        <div>
          <div class="text-h6">Chatbot Builder</div>
          <div class="text-caption text-medium-emphasis">
            Website crawlen, Chunks erstellen und Chatbot konfigurieren
          </div>
        </div>
        <v-spacer />

        <!-- Processing Indicator with Progress -->
        <template v-if="isProcessing">
          <div class="d-flex align-center mr-3">
            <v-progress-circular
              v-if="overallProgressPercent === 0"
              indeterminate
              size="18"
              width="2"
              color="primary"
              class="mr-2"
            />
            <v-progress-circular
              v-else
              :model-value="overallProgressPercent"
              size="22"
              width="3"
              color="primary"
              class="mr-2"
            >
              <span class="text-caption">{{ overallProgressPercent }}</span>
            </v-progress-circular>
            <span class="text-caption text-medium-emphasis">
              {{ headerStatusText }}
              <span v-if="currentProgressText">({{ currentProgressText }})</span>
            </span>
          </div>
        </template>

        <LBtn
          variant="text"
          size="small"
          prepend-icon="mdi-arrow-left"
          @click="handleClose"
        >
          Zurück
        </LBtn>
      </v-card-title>

      <v-divider />

        <!-- Custom Stepper Header with Clickable Steps -->
        <div class="wizard-steps pa-4">
          <div class="d-flex justify-space-between align-center">
            <template v-for="(item, index) in stepItems" :key="item.value">
              <!-- Step Circle + Title -->
              <div
                class="step-item text-center"
                :class="{
                  'step-active': currentStep === item.value,
                  'step-complete': currentStep > item.value,
                  'step-clickable': canNavigateToStep(item.value),
                  'step-disabled': !canNavigateToStep(item.value)
                }"
                @click="handleStepClick(item.value)"
              >
                <div class="step-circle mx-auto mb-1">
                  <v-icon v-if="currentStep > item.value" size="small" color="white">mdi-check</v-icon>
                  <span v-else>{{ item.value }}</span>
                </div>
                <div class="step-title text-caption">{{ item.title }}</div>

                <!-- Mini Progress under active step -->
                <div v-if="getStepProgress(item.value) !== null" class="step-progress mt-1">
                  <v-progress-linear
                    :model-value="getStepProgress(item.value)"
                    :indeterminate="getStepProgress(item.value) === 0"
                    height="3"
                    rounded
                    :color="currentStep === item.value ? 'primary' : 'grey'"
                  />
                </div>
              </div>

              <!-- Connector Line -->
              <div
                v-if="index < stepItems.length - 1"
                class="step-connector flex-grow-1 mx-2"
                :class="{ 'step-connector-complete': currentStep > item.value }"
              />
            </template>
          </div>
        </div>

        <!-- Stepper Content -->
        <v-stepper
          v-model="currentStep"
          :items="stepItems"
          flat
          hide-actions
          class="stepper-content flex-grow-1"
        >

        <!-- Step 1: URL Input -->
        <template #item.1>
          <StepCrawlerConfig
            v-model:url="wizardData.url"
            v-model:config="crawlerConfig"
            :error-message="errors.url || errors.general"
            :loading="loading"
            @start="handleStartWizard"
          />
        </template>

        <!-- Step 2: Crawling Progress -->
        <template #item.2>
          <StepCollectionSetup
            mode="crawling"
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :collection-documents="collectionDocuments"
            :documents-loading="documentsLoading"
            :error-message="errors.crawl || errors.general"
            @skip-to-config="handleSkipToConfig"
            @refresh-documents="handleRefreshDocuments"
            @pause="handlePauseBuild"
          />
        </template>

        <!-- Step 3: Embedding Progress -->
        <template #item.3>
          <StepCollectionSetup
            mode="embedding"
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :collection-documents="collectionDocuments"
            :documents-loading="documentsLoading"
            :error-message="errors.embedding || errors.general"
            @skip-to-config="handleSkipToConfig"
            @refresh-documents="handleRefreshDocuments"
            @pause="handlePauseBuild"
          />
        </template>

        <!-- Step 4: Configuration -->
        <template #item.4>
          <StepChatbotConfig
            v-model:config="wizardData"
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :generating-fields="generating"
            :can-generate="!!chatbotId"
            :models="llmModels"
            :models-loading="llmModelsLoading"
            @generate-field="handleGenerateField"
            @refresh-models="syncAndLoadModels"
          />
        </template>

        <!-- Step 5: Complete -->
        <template #item.5>
          <StepReview
            :config="wizardData"
            :url="wizardData.url"
            :collection-info="collectionInfo"
            :embedding-in-progress="isEmbedding"
            :embedding-progress="embeddingProgressPercent"
            @test="handleTestChatbot"
            @close="handleClose"
          />
        </template>
      </v-stepper>

      <!-- Footer Actions -->
      <v-card-actions v-if="currentStep < 5" class="pa-3 wizard-footer">
        <LBtn
          v-if="currentStep > 1"
          variant="text"
          size="small"
          @click="handlePreviousStep"
        >
          Zurück
        </LBtn>
        <v-spacer />

        <!-- Step 1: Start Button -->
        <LBtn
          v-if="currentStep === 1"
          variant="primary"
          :loading="loading"
          :disabled="!wizardData.url || loading"
          prepend-icon="mdi-rocket-launch"
          @click="handleStartWizard"
        >
          Crawling starten
        </LBtn>

        <!-- Step 2/3: Progress Actions -->
        <template v-if="currentStep === 2 || currentStep === 3">
          <LBtn
            v-if="isProcessing"
            variant="warning"
            size="small"
            prepend-icon="mdi-pause"
            class="mr-2"
            @click="handlePauseBuild"
          >
            Pausieren
          </LBtn>
          <LBtn
            variant="primary"
            size="small"
            prepend-icon="mdi-skip-forward"
            @click="handleSkipToConfig"
          >
            Zur Konfiguration
          </LBtn>
        </template>

        <!-- Step 4: Finalize Button -->
        <!-- Crawling muss fertig sein, aber Embedding kann im Hintergrund weiterlaufen -->
        <LBtn
          v-if="currentStep === 4"
          variant="primary"
          :loading="loading"
          :disabled="isCrawling || loading || !canFinalize"
          prepend-icon="mdi-check"
          @click="handleFinalizeChatbot"
        >
          <template v-if="isCrawling">Warte auf Crawling...</template>
          <template v-else-if="isEmbedding">Chatbot erstellen (Embedding läuft weiter)</template>
          <template v-else>Chatbot erstellen</template>
        </LBtn>
      </v-card-actions>

        <!-- Error Alert -->
        <v-alert
          v-if="hasAnyError"
          type="error"
          variant="tonal"
          class="mx-4 mb-4"
          closable
          @click:close="clearError()"
        >
          {{ errors.general || errors.crawl || errors.embedding || errors.config || errors.url }}
        </v-alert>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getSocket, useSocketState } from '@/services/socketService'
import { useBuilderState, BUILD_STATUS, WIZARD_STEPS } from '@/composables/useBuilderState'
import { fieldGenerationService } from '@/composables/useFieldGenerationService'
import StepCrawlerConfig from './BuilderSteps/StepCrawlerConfig.vue'
import StepCollectionSetup from './BuilderSteps/StepCollectionSetup.vue'
import StepChatbotConfig from './BuilderSteps/StepChatbotConfig.vue'
import StepReview from './BuilderSteps/StepReview.vue'

const props = defineProps({
  resumeChatbotId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['created', 'test', 'close'])

// ===== Socket.IO =====
const { isConnected } = useSocketState()
const socket = ref(null)
const socketSubscribed = ref(false)

// ===== Layout =====
const wizardHost = ref(null)

// ===== Local State =====
const collectionDocuments = ref([])
const documentsLoading = ref(false)
const hasAutoGeneratedFields = ref(false)
const elapsedTimeInterval = ref(null)
// Track fields that were interrupted during generation (for UI feedback)
const interruptedGenerations = ref([])
// Track field generation subscriptions for cleanup
const fieldSubscriptions = ref([])

// ===== LLM Models =====
const llmModels = ref([])
const llmModelsLoading = ref(false)

// ===== Builder State =====
const {
  currentStep,
  loading,
  chatbotId,
  buildStatus,
  crawlerJobId,
  collectionId,
  wizardData,
  crawlerConfig,
  crawlProgress,
  embeddingProgress,
  collectionInfo,
  errors,
  generating,
  isProcessing,
  isCrawling,
  isEmbedding,
  hasAnyError,
  canNavigateToStep,
  navigateToStep,
  setStatus,
  updateCrawlProgress,
  updateElapsedTime,
  addRecentPage,
  updateEmbeddingProgress,
  updateCollectionInfo,
  setError,
  clearError,
  setGenerating,
  resetWizard,
  setChatbotId,
  setCrawlerJobId,
  setCollectionId,
  setLoading,
  startCrawlTimer
} = useBuilderState()

async function loadModels() {
  llmModelsLoading.value = true
  try {
    const response = await axios.get('/api/llm/models?active_only=true&model_type=llm')
    if (response.data?.success) {
      llmModels.value = response.data.models || []

      // Default selection (only if not set yet)
      if (!wizardData.value.modelName) {
        const def = llmModels.value.find(m => m.is_default) || llmModels.value[0]
        if (def?.model_id) {
          wizardData.value.modelName = def.model_id
        }
      }
    }
  } catch (error) {
    console.error('[Wizard] Error loading LLM models:', error)
    llmModels.value = []
  } finally {
    llmModelsLoading.value = false
  }
}

async function syncAndLoadModels() {
  llmModelsLoading.value = true
  try {
    await axios.post('/api/llm/models/sync')
  } catch (error) {
    console.warn('[Wizard] Model sync failed:', error)
  } finally {
    llmModelsLoading.value = false
  }
  await loadModels()
}

// ===== Stepper Config =====
const stepItems = [
  { title: 'URL', value: WIZARD_STEPS.URL_INPUT },
  { title: 'Crawling', value: WIZARD_STEPS.CRAWLING },
  { title: 'Embedding', value: WIZARD_STEPS.EMBEDDING },
  { title: 'Konfiguration', value: WIZARD_STEPS.CONFIGURATION },
  { title: 'Fertig', value: WIZARD_STEPS.COMPLETE }
]

// ===== Computed =====
const canFinalize = computed(() => {
  return wizardData.value.name &&
         wizardData.value.displayName &&
         wizardData.value.systemPrompt
})

// Progress computed values for header
const crawlProgressPercent = computed(() => {
  const progress = crawlProgress.value
  const total = progress.urlsTotal || progress.pagesTotal || 0
  if (total === 0) return 0
  const completed = progress.urlsCompleted || progress.pagesProcessed || 0
  return Math.min(100, Math.round((completed / total) * 100))
})

const embeddingProgressPercent = computed(() => {
  const progress = embeddingProgress.value
  if (typeof progress === 'number') return Math.round(progress)
  return Math.round(progress?.progress || 0)
})

const overallProgressPercent = computed(() => {
  if (isCrawling.value) return crawlProgressPercent.value
  if (isEmbedding.value) return embeddingProgressPercent.value
  return 0
})

const headerStatusText = computed(() => {
  if (isCrawling.value) {
    const stage = crawlProgress.value.stage
    if (stage === 'planning') return 'Phase 1: URL-Erkundung'
    if (stage === 'planning_done') return 'Phase 2: Inhalte erfassen'
    if (stage === 'crawling') return 'Phase 2: Inhalte erfassen'
    if (stage === 'completed') return 'Crawling abgeschlossen'
    return 'Crawling'
  }
  if (isEmbedding.value) {
    return 'Embedding'
  }
  return 'Verarbeitung'
})

const currentProgressText = computed(() => {
  if (isCrawling.value) {
    const p = crawlProgress.value
    const completed = p.urlsCompleted || p.pagesProcessed || 0
    const total = p.urlsTotal || p.pagesTotal || 0
    const docs = (p.documentsCreated || 0) + (p.documentsLinked || 0)

    // During planning phase, show discovered URLs
    if (p.stage === 'planning') {
      return total > 0 ? `${total} URLs gefunden` : 'Suche URLs...'
    }

    // Transition from planning to crawling
    if (p.stage === 'planning_done') {
      return `${total} URLs, starte Erfassung...`
    }

    // Crawling completed
    if (p.stage === 'completed') {
      return `${total} URLs, ${docs} Dokumente`
    }

    // During crawling phase
    if (total > 0) {
      return `${completed}/${total} URLs, ${docs} Docs`
    }
    if (docs > 0) {
      return `${docs} Dokumente`
    }
    return 'Wird gestartet...'
  }
  if (isEmbedding.value) {
    return `${embeddingProgressPercent.value}%`
  }
  return ''
})

// Get progress for a specific step (for mini progress bars)
function getStepProgress(step) {
  if (step === WIZARD_STEPS.CRAWLING && (isCrawling.value || currentStep.value > WIZARD_STEPS.CRAWLING)) {
    return currentStep.value > WIZARD_STEPS.CRAWLING ? 100 : crawlProgressPercent.value
  }
  if (step === WIZARD_STEPS.EMBEDDING && (isEmbedding.value || currentStep.value > WIZARD_STEPS.EMBEDDING)) {
    return currentStep.value > WIZARD_STEPS.EMBEDDING ? 100 : embeddingProgressPercent.value
  }
  return null
}

// ===== Step Navigation =====
function getStepColor(step) {
  if (currentStep.value > step) return 'success'
  if (currentStep.value === step) return 'primary'
  return undefined
}

function handleStepClick(step) {
  if (canNavigateToStep(step)) {
    navigateToStep(step)
  }
}

function handlePreviousStep() {
  if (currentStep.value > 1) {
    navigateToStep(currentStep.value - 1)
  }
}

function handleSkipToConfig() {
  navigateToStep(WIZARD_STEPS.CONFIGURATION)
  requestCollectionDocuments({ force: true })
}

const FALLBACK_URL = 'https://www.dg-agentur.de/'
const SCHEME_REGEX = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\//

const getEffectiveWizardUrl = (value) => {
  if (!value || !value.trim()) return ''
  const trimmed = value.trim()
  if (SCHEME_REGEX.test(trimmed)) {
    return trimmed
  }
  return FALLBACK_URL
}

// ===== Wizard Start =====
async function handleStartWizard() {
  const rawUrl = wizardData.value.url
  if (!rawUrl || !rawUrl.trim()) {
    setError('url', 'URL ist erforderlich')
    return
  }

  const effectiveUrl = getEffectiveWizardUrl(rawUrl)

  // Validate URL
  try {
    const parsedUrl = new URL(effectiveUrl)
    if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
      setError('url', 'URL muss mit http:// oder https:// beginnen')
      return
    }
  } catch {
    setError('url', 'Ungültige URL')
    return
  }

  setLoading(true)
  clearError()

  try {
    // Create wizard chatbot
    const response = await axios.post('/api/chatbots/wizard', {
      url: effectiveUrl
    })

    if (response.data.success) {
      setChatbotId(response.data.chatbot_id)
      wizardData.value.name = response.data.name || ''
      wizardData.value.displayName = response.data.display_name || ''

      // Move to crawling step
      setStatus(BUILD_STATUS.CRAWLING)
      startCrawlTimer()
      startElapsedTimeUpdates()  // Start timer immediately

      // Start crawl - get job_id first
      const crawlResult = await startCrawl()

      if (crawlResult?.job_id) {
        // Subscribe to progress updates AFTER we have the job_id
        subscribeToProgress(crawlResult.job_id)
      }

      // Initial document fetch
      requestCollectionDocuments({ force: true })
    } else {
      setError('general', response.data.error || 'Fehler beim Starten des Wizards')
    }
  } catch (error) {
    console.error('Error starting wizard:', error)
    setError('general', error.response?.data?.error || 'Fehler beim Starten des Wizards')
  } finally {
    setLoading(false)
  }
}

// ===== Crawl Control =====
async function startCrawl() {
  try {
    const takeScreenshots = crawlerConfig.value.usePlaywright && crawlerConfig.value.takeScreenshots !== false
    const useVisionLlm = crawlerConfig.value.useVisionLlm && takeScreenshots
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/crawl`, {
      max_pages: crawlerConfig.value.maxPages,
      max_depth: crawlerConfig.value.maxDepth,
      use_playwright: crawlerConfig.value.usePlaywright,
      use_vision_llm: useVisionLlm,
      take_screenshots: takeScreenshots
    })

    if (response.data.success) {
      setCrawlerJobId(response.data.job_id)
      if (response.data.collection_id) {
        setCollectionId(response.data.collection_id)
      }

      // Immediately set initial crawl progress to show UI feedback
      updateCrawlProgress({
        stage: 'planning',
        urlsTotal: 0,
        urlsCompleted: 0,
        message: 'URL-Erkundung startet...',
        crawlerType: crawlerConfig.value.usePlaywright ? 'Playwright' : 'Basic'
      })

      return response.data // Return the result so caller can use job_id
    } else {
      setError('crawl', response.data.error || 'Fehler beim Starten des Crawlings')
      setStatus(BUILD_STATUS.ERROR)
      return null
    }
  } catch (error) {
    console.error('Error starting crawl:', error)
    setError('crawl', error.response?.data?.error || 'Fehler beim Crawlen')
    setStatus(BUILD_STATUS.ERROR)
    return null
  }
}

async function handlePauseBuild() {
  if (!chatbotId.value) return

  try {
    await axios.post(`/api/chatbots/${chatbotId.value}/wizard/pause`)
    setStatus(BUILD_STATUS.PAUSED)
    stopElapsedTimeUpdates()
  } catch (error) {
    console.error('Error pausing build:', error)
    setError('general', 'Fehler beim Pausieren')
  }
}

// ===== Socket.IO Subscriptions =====
function subscribeToProgress(jobId = null) {
  socket.value = getSocket()
  if (!socket.value) {
    console.warn('[Wizard] Socket not available, cannot subscribe to live updates')
    setError('general', 'Live-Updates nicht verfügbar (Socket.IO)')
    return
  }

  if (socketSubscribed.value) return
  socketSubscribed.value = true

  // Subscribe to wizard session room (server-authoritative updates)
  if (chatbotId.value) {
    console.log('[Wizard] Joining wizard session room:', chatbotId.value)
    socket.value.emit('wizard:join_session', { chatbot_id: chatbotId.value })
  }

  // Subscribe to crawler job - use passed jobId or stored one
  const effectiveJobId = jobId || crawlerJobId.value
  if (effectiveJobId) {
    console.log('[Wizard] Joining crawler session:', effectiveJobId)
    socket.value.emit('crawler:join_session', { session_id: effectiveJobId })
    socket.value.emit('crawler:get_status', { session_id: effectiveJobId })
  }

  // Subscribe to collection progress (embedding) + initial status
  if (collectionId.value) {
    socket.value.emit('rag:subscribe_collection', { collection_id: collectionId.value })
    requestCollectionDocuments({ force: true })
  }

  // Wizard session events (server-authoritative)
  socket.value.on('wizard:state', handleWizardState)
  socket.value.on('wizard:progress', handleWizardProgress)
  socket.value.on('wizard:status_changed', handleWizardStatusChanged)
  socket.value.on('wizard:elapsed_time', handleWizardElapsedTime)
  socket.value.on('wizard:error', handleWizardError)

  // Crawler progress
  socket.value.on('crawler:progress', handleCrawlerProgress)
  socket.value.on('crawler:status', handleCrawlerProgress)
  socket.value.on('crawler:page_crawled', handlePageCrawled)
  socket.value.on('crawler:complete', handleCrawlerComplete)
  socket.value.on('crawler:error', handleCrawlerError)

  // Embedding progress
  socket.value.on('rag:collection_status', handleCollectionStatus)
  socket.value.on('rag:collection_progress', handleEmbeddingProgress)
  socket.value.on('rag:collection_completed', handleEmbeddingComplete)
  socket.value.on('rag:collection_error', handleEmbeddingError)
  socket.value.on('rag:collection_documents', handleCollectionDocuments)
  socket.value.on('rag:document_processed', handleDocumentProcessed)
  socket.value.on('rag:error', handleRagError)

  console.log('[Wizard] Subscribed to socket events')
}

function unsubscribeFromProgress() {
  if (!socket.value || !socketSubscribed.value) return

  // Leave wizard session room
  if (chatbotId.value) {
    socket.value.emit('wizard:leave_session', { chatbot_id: chatbotId.value })
  }
  if (collectionId.value) {
    socket.value.emit('rag:unsubscribe_collection', { collection_id: collectionId.value })
  }
  if (crawlerJobId.value) {
    socket.value.emit('crawler:leave_session', { session_id: crawlerJobId.value })
  }

  // Wizard session events
  socket.value.off('wizard:state', handleWizardState)
  socket.value.off('wizard:progress', handleWizardProgress)
  socket.value.off('wizard:status_changed', handleWizardStatusChanged)
  socket.value.off('wizard:elapsed_time', handleWizardElapsedTime)
  socket.value.off('wizard:error', handleWizardError)

  // Crawler events
  socket.value.off('crawler:progress', handleCrawlerProgress)
  socket.value.off('crawler:status', handleCrawlerProgress)
  socket.value.off('crawler:page_crawled', handlePageCrawled)
  socket.value.off('crawler:complete', handleCrawlerComplete)
  socket.value.off('crawler:error', handleCrawlerError)

  // Embedding events
  socket.value.off('rag:collection_status', handleCollectionStatus)
  socket.value.off('rag:collection_progress', handleEmbeddingProgress)
  socket.value.off('rag:collection_completed', handleEmbeddingComplete)
  socket.value.off('rag:collection_error', handleEmbeddingError)
  socket.value.off('rag:collection_documents', handleCollectionDocuments)
  socket.value.off('rag:document_processed', handleDocumentProcessed)
  socket.value.off('rag:error', handleRagError)

  socketSubscribed.value = false
  documentsLoading.value = false
  console.log('[Wizard] Unsubscribed from socket events')
}

// ===== Wizard Socket Event Handlers (Server-Authoritative) =====
function handleWizardState(data) {
  // Filter: Only process events for THIS wizard's chatbot
  if (chatbotId.value && data?.chatbot_id && data.chatbot_id !== chatbotId.value) {
    return // Event is for a different chatbot
  }

  console.log('[Wizard] Received wizard:state from server:', data)

  // Update session state from server
  if (data.session) {
    if (data.session.build_status) {
      setStatus(data.session.build_status)
    }
    if (data.session.current_step) {
      navigateToStep(data.session.current_step)
    }
    // Update wizard data from server if in configuring/ready state
    if (data.session.wizard_data && ['configuring', 'ready'].includes(data.session.build_status)) {
      const serverData = typeof data.session.wizard_data === 'string'
        ? JSON.parse(data.session.wizard_data)
        : data.session.wizard_data
      // Only update empty fields to avoid overwriting user edits
      if (serverData.name && !wizardData.value.name) wizardData.value.name = serverData.name
      if (serverData.displayName && !wizardData.value.displayName) wizardData.value.displayName = serverData.displayName
      if (serverData.systemPrompt && !wizardData.value.systemPrompt) wizardData.value.systemPrompt = serverData.systemPrompt
      if (serverData.welcomeMessage && !wizardData.value.welcomeMessage) wizardData.value.welcomeMessage = serverData.welcomeMessage
      if (serverData.icon && !wizardData.value.icon) wizardData.value.icon = serverData.icon
      if (serverData.color && !wizardData.value.color) wizardData.value.color = serverData.color
    }
  }

  // Update progress from server
  if (data.progress) {
    handleWizardProgress(data)
  }
}

// ===== Wizard Socket Event Handlers =====
// IMPORTANT: All handlers must filter by chatbot_id because the socket is a singleton
// shared across multiple wizard instances (tabs). Without filtering, events from
// one chatbot would be processed by all open wizard tabs.

function handleWizardProgress(data) {
  // Filter: Only process events for THIS wizard's chatbot
  if (chatbotId.value && data?.chatbot_id && data.chatbot_id !== chatbotId.value) {
    return // Event is for a different chatbot
  }

  console.log('[Wizard] Received wizard:progress from server:', data)

  if (!data.progress) return

  // Update crawl progress
  if (data.progress.crawl_stage) {
    updateCrawlProgress({
      stage: data.progress.crawl_stage,
      urlsTotal: data.progress.urls_total || 0,
      urlsCompleted: data.progress.urls_completed || 0,
      documentsCreated: data.progress.documents_created || 0,
      currentUrl: data.progress.current_url || ''
    })
  }

  // Update embedding progress
  if (data.progress.embedding_progress !== undefined) {
    updateEmbeddingProgress({
      progress: data.progress.embedding_progress,
      documentsTotal: data.progress.documents_total || 0,
      documentsProcessed: data.progress.documents_processed || 0,
      currentDocument: data.progress.current_document || ''
    })
  }
}

function handleWizardStatusChanged(data) {
  // Filter: Only process events for THIS wizard's chatbot
  if (chatbotId.value && data?.chatbot_id && data.chatbot_id !== chatbotId.value) {
    return // Event is for a different chatbot
  }

  console.log('[Wizard] Received wizard:status_changed from server:', data)

  if (data.status) {
    setStatus(data.status)
  }
  if (data.step !== null && data.step !== undefined) {
    navigateToStep(data.step)
  }
}

function handleWizardElapsedTime(data) {
  // Filter: Only process events for THIS wizard's chatbot
  if (chatbotId.value && data?.chatbot_id && data.chatbot_id !== chatbotId.value) {
    return // Event is for a different chatbot
  }

  console.log('[Wizard] Received wizard:elapsed_time from server:', data)
  // Server-side elapsed time - could be used for more accurate time display
  // For now, we continue using local timer but this could sync it
}

function handleWizardError(data) {
  // Filter: Only process events for THIS wizard's chatbot
  if (chatbotId.value && data?.chatbot_id && data.chatbot_id !== chatbotId.value) {
    return // Event is for a different chatbot
  }

  console.error('[Wizard] Received wizard:error from server:', data)
  if (data.message) {
    setError(data.source || 'general', data.message)
  }
}

// ===== Crawler Socket Event Handlers =====
// IMPORTANT: All handlers must filter by job_id because the socket is a singleton
// shared across multiple wizard instances (tabs). Without filtering, events from
// one crawler job would be processed by all open wizard tabs.

function handleCrawlerProgress(data) {
  // Filter: Only process events for THIS wizard's crawler job
  if (crawlerJobId.value && data?.session_id && data.session_id !== crawlerJobId.value) {
    return // Event is for a different crawler job
  }

  console.log('[Wizard] Crawler progress:', data)

  // Map backend data to frontend format
  const status = (data.status || '').toLowerCase()
  const mappedStage = data.stage || (
    (status === 'queued' || status === 'planning') ? 'planning'
      : (status === 'completed' || status === 'finished') ? 'completed'
        : 'crawling'
  )

  const progressData = {
    stage: mappedStage,
    urlsTotal: data.urls_total || data.urlsTotal || 0,
    urlsCompleted: data.urls_completed || data.urlsCompleted || 0,
    pagesProcessed: data.pages_crawled || data.pagesProcessed || 0,
    pagesTotal: data.max_pages || data.pagesTotal || 0,
    documentsCreated: data.documents_created || data.documentsCreated || 0,
    documentsLinked: data.documents_linked || data.documentsLinked || 0,
    imagesExtracted: data.images_extracted || data.imagesExtracted || 0,
    screenshotsTaken: data.screenshots_taken || data.screenshotsTaken || 0,
    currentUrl: data.current_url || data.currentUrl || '',
    crawlerType: data.crawler_type || data.crawlerType || 'Basic',
    message: data.message || ''
  }

  updateCrawlProgress(progressData)
  updateElapsedTime()
}

function handlePageCrawled(data) {
  // Filter: Only process events for THIS wizard's crawler job
  if (crawlerJobId.value && data?.session_id && data.session_id !== crawlerJobId.value) {
    return // Event is for a different crawler job
  }

  console.log('[Wizard] Page crawled:', data)
  if (data.url) {
    addRecentPage(data.url)
  }
  if (data.documents_created !== undefined) {
    updateCrawlProgress({ documents_created: data.documents_created })
  }
  if (data.documents_linked !== undefined) {
    updateCrawlProgress({ documents_linked: data.documents_linked })
  }
  if (data.document) {
    upsertCollectionDocument(data.document)
  }
  updateElapsedTime()
}

function handleCrawlerComplete(data) {
  // Filter: Only process events for THIS wizard's crawler job
  if (crawlerJobId.value && data?.session_id && data.session_id !== crawlerJobId.value) {
    return // Event is for a different crawler job
  }

  console.log('[Wizard] Crawler complete:', data)
  updateCrawlProgress({
    pages_crawled: data.pages_crawled,
    documents_created: data.documents_created,
    documents_linked: data.documents_linked,
    stage: 'completed'
  })

  // Transition to embedding
  setStatus(BUILD_STATUS.EMBEDDING)
  requestCollectionDocuments({ force: true })
}

function handleCrawlerError(data) {
  // Filter: Only process events for THIS wizard's crawler job
  if (crawlerJobId.value && data?.session_id && data.session_id !== crawlerJobId.value) {
    return // Event is for a different crawler job
  }

  const message = data?.error || 'Crawling fehlgeschlagen'
  console.error('[Wizard] Crawler error:', data)

  if (typeof message === 'string' && message.toLowerCase().includes('session not found')) {
    if (chatbotId.value) {
      syncWizardFromBackend(chatbotId.value).then(() => {
        if (buildStatus.value !== BUILD_STATUS.CRAWLING) {
          clearError('crawl')
        }
      }).catch(() => {})
    }

    setError('crawl', 'Crawler-Session nicht mehr verfügbar (Backend neu gestartet oder Crawl beendet). Live-Updates sind nicht verfügbar.')
    return
  }

  setError('crawl', message)
}

function handleCollectionStatus(data) {
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return

  if (data?.collection_id) {
    updateCollectionInfo({
      id: data.collection_id,
      name: data.name,
      embedding_status: data.embedding_status,
      embedding_error: data.embedding_error,
      document_count: data.document_count,
      total_chunks: data.total_chunks,
      image_chunks_total: data.image_chunks_total,
      image_chunks_completed: data.image_chunks_completed
    })
  }

  if (data?.embedding_progress !== undefined) {
    updateEmbeddingProgress({ progress: data.embedding_progress })
  }
}

function handleCollectionDocuments(data) {
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return
  collectionDocuments.value = data?.documents || []
  documentsLoading.value = false
}

function handleDocumentProcessed(data) {
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return
  if (data?.document) {
    upsertCollectionDocument(data.document)
  }
}

function handleRagError(data) {
  documentsLoading.value = false
  console.warn('[Wizard] RAG socket error:', data)
}

function handleEmbeddingProgress(data) {
  console.log('[Wizard] Embedding progress:', data)
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return

  updateEmbeddingProgress(data)

  // Only switch to embedding status when crawling is actually complete
  // The crawler emits 'completed' stage when done
  if (buildStatus.value === BUILD_STATUS.CRAWLING) {
    const crawlStage = crawlProgress.value.stage
    // Only transition if crawl is done (completed or planning_done with all URLs processed)
    if (crawlStage === 'completed' ||
        (crawlProgress.value.urlsTotal > 0 &&
         crawlProgress.value.urlsCompleted >= crawlProgress.value.urlsTotal)) {
      setStatus(BUILD_STATUS.EMBEDDING)
    }
    // Otherwise, embedding is running in the background but we stay on crawling view
  }

  const infoUpdate = {}
  if (data.documents_total !== undefined) {
    infoUpdate.document_count = data.documents_total
  }
  if (data.chunks_completed !== undefined) {
    infoUpdate.total_chunks = data.chunks_completed
  }
  if (data.image_chunks_total !== undefined) {
    infoUpdate.image_chunks_total = data.image_chunks_total
  }
  if (data.image_chunks_completed !== undefined) {
    infoUpdate.image_chunks_completed = data.image_chunks_completed
  }
  if (Object.keys(infoUpdate).length) {
    updateCollectionInfo(infoUpdate)
  }
}

async function syncChatbotIconAndColor() {
  if (!chatbotId.value) return
  try {
    const response = await axios.get(`/api/chatbots/${chatbotId.value}`)
    const chatbot = response.data?.chatbot
    if (chatbot) {
      // Only update if backend has values (generated by build monitor)
      if (chatbot.icon && chatbot.icon !== 'mdi-robot') {
        wizardData.value.icon = chatbot.icon
      }
      if (chatbot.color && chatbot.color !== '#5d7a4a') {
        wizardData.value.color = chatbot.color
      }
    }
  } catch (error) {
    console.warn('[Wizard] Failed to sync icon/color:', error)
  }
}

async function handleEmbeddingComplete(data) {
  console.log('[Wizard] Embedding complete:', data)
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return

  updateEmbeddingProgress(100)
  updateCollectionInfo({
    document_count: data.total_documents,
    total_chunks: data.total_chunks,
    image_chunks_total: data.image_chunks_total,
    image_chunks_completed: data.image_chunks_completed
  })

  setStatus(BUILD_STATUS.CONFIGURING)
  requestCollectionDocuments({ force: true })

  // Wait briefly for build monitor to generate icon/color, then sync
  await new Promise(resolve => setTimeout(resolve, 2000))
  await syncChatbotIconAndColor()

  // Auto-generate fields when reaching config
  autoGenerateFields()
}

function handleEmbeddingError(data) {
  console.error('[Wizard] Embedding error:', data)
  if (collectionId.value && data?.collection_id && data.collection_id !== collectionId.value) return

  setError('embedding', data.error || 'Embedding fehlgeschlagen')
  setStatus(BUILD_STATUS.ERROR)
}

// ===== Timers (UI only) =====
function startElapsedTimeUpdates() {
  if (elapsedTimeInterval.value) return
  elapsedTimeInterval.value = setInterval(updateElapsedTime, 1000)
}

function stopElapsedTimeUpdates() {
  if (elapsedTimeInterval.value) {
    clearInterval(elapsedTimeInterval.value)
    elapsedTimeInterval.value = null
  }
}

// ===== Collection Documents (WebSocket) =====
function upsertCollectionDocument(doc) {
  if (!doc || doc.id === undefined || doc.id === null) return

  const idx = collectionDocuments.value.findIndex(d => d.id === doc.id)
  if (idx >= 0) {
    collectionDocuments.value[idx] = { ...collectionDocuments.value[idx], ...doc }
    return
  }

  collectionDocuments.value.unshift(doc)
  if (collectionDocuments.value.length > 200) {
    collectionDocuments.value = collectionDocuments.value.slice(0, 200)
  }
}

function handleRefreshDocuments() {
  requestCollectionDocuments({ force: true })
}

function requestCollectionDocuments({ force = false } = {}) {
  if (!collectionId.value) return

  if (!socket.value) {
    console.warn('[Wizard] Socket not available, cannot fetch collection documents')
    documentsLoading.value = false
    return
  }

  documentsLoading.value = true
  socket.value.emit('rag:get_collection_documents', { collection_id: collectionId.value, limit: 50 })
}

// ===== Field Generation (using global service) =====

/**
 * Subscribe to field updates from the global service.
 * This syncs the service's state with the local wizardData.
 */
function subscribeToFieldUpdates() {
  if (!chatbotId.value) return

  // Unsubscribe from any existing subscriptions
  unsubscribeFromFieldUpdates()

  const fields = ['name', 'display_name', 'system_prompt', 'welcome_message', 'icon', 'color']

  fields.forEach(field => {
    const unsubscribe = fieldGenerationService.subscribeToField(
      chatbotId.value,
      field,
      ({ content, generating: isGen, completed }) => {
        // Update generating state
        setGenerating(field, isGen)

        // Update content if we have it
        if (content) {
          applyFieldValue(field, content)
        }
      }
    )
    fieldSubscriptions.value.push(unsubscribe)
  })
}

/**
 * Unsubscribe from field updates (called on unmount)
 */
function unsubscribeFromFieldUpdates() {
  fieldSubscriptions.value.forEach(unsub => unsub())
  fieldSubscriptions.value = []
}

/**
 * Sync any existing content from the service to wizardData.
 * Called when returning to the wizard.
 */
function syncFieldsFromService() {
  if (!chatbotId.value) return

  const contents = fieldGenerationService.getAllFieldContents(chatbotId.value)
  Object.entries(contents).forEach(([field, content]) => {
    if (content) {
      applyFieldValue(field, content)
    }
  })

  // Also sync generating states
  const generatingFields = fieldGenerationService.getGeneratingFields(chatbotId.value)
  Object.entries(generatingFields).forEach(([field, isGen]) => {
    setGenerating(field, isGen)
  })
}

async function autoGenerateFields() {
  if (hasAutoGeneratedFields.value) return
  if (!chatbotId.value) return

  hasAutoGeneratedFields.value = true

  const fields = ['name', 'display_name', 'system_prompt', 'welcome_message', 'icon', 'color']
  for (const field of fields) {
    // Skip color generation if the user or backend already set a non-default value
    if (field === 'color' && wizardData.value.color && wizardData.value.color !== '#5d7a4a') {
      console.log('[Wizard] Skipping color generation - color already set:', wizardData.value.color)
      continue
    }
    await handleGenerateField(field)
  }
}

async function handleGenerateField(field, options = {}) {
  if (!chatbotId.value) return

  // Check if already generating via the service
  if (fieldGenerationService.isGenerating(chatbotId.value, field)) {
    console.log(`[Wizard] Field ${field} already generating`)
    return
  }

  setGenerating(field, true)

  try {
    // Use the global service - it handles streaming vs direct automatically
    const result = await fieldGenerationService.generateField(
      chatbotId.value,
      field,
      {
        force_llm: options.force_llm,
        onUpdate: (content, done) => {
          // Live update for streaming fields
          applyFieldValue(field, content)
          if (done) {
            setGenerating(field, false)
          }
        }
      }
    )

    // For non-streaming fields, apply the result directly
    if (result !== undefined && result !== null) {
      applyFieldValue(field, result)
    }
  } catch (error) {
    console.error(`[Wizard] Error generating ${field}:`, error)
  } finally {
    // For non-streaming fields, this is needed
    // For streaming, the onUpdate callback handles it
    if (!['system_prompt', 'welcome_message'].includes(field)) {
      setGenerating(field, false)
    }
  }
}

function applyFieldValue(field, value) {
  switch (field) {
    case 'name':
      wizardData.value.name = value
      break
    case 'display_name':
      wizardData.value.displayName = value
      break
    case 'system_prompt':
      wizardData.value.systemPrompt = value
      break
    case 'welcome_message':
      wizardData.value.welcomeMessage = value
      break
    case 'icon':
      wizardData.value.icon = value
      break
    case 'color':
      wizardData.value.color = value
      break
  }
}

function getFieldValue(field) {
  switch (field) {
    case 'name':
      return wizardData.value.name
    case 'display_name':
      return wizardData.value.displayName
    case 'system_prompt':
      return wizardData.value.systemPrompt
    case 'welcome_message':
      return wizardData.value.welcomeMessage
    case 'icon':
      return wizardData.value.icon
    case 'color':
      return wizardData.value.color
    default:
      return null
  }
}

// ===== Finalize =====
async function handleFinalizeChatbot() {
  if (!chatbotId.value) return
  // Only block if crawling is in progress - embedding can continue in background
  if (isCrawling.value) return

  setLoading(true)

  try {
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/finalize`, {
      name: wizardData.value.name,
      display_name: wizardData.value.displayName,
      system_prompt: wizardData.value.systemPrompt,
      model_name: wizardData.value.modelName,
      welcome_message: wizardData.value.welcomeMessage,
      fallback_message: wizardData.value.fallbackMessage,
      icon: wizardData.value.icon,
      color: wizardData.value.color
    })

    if (response.data.success) {
      // Don't change the build status - keep tracking embedding if still running
      // The backend has already set the chatbot to "ready"
      if (!isEmbedding.value) {
        setStatus(BUILD_STATUS.READY)
      }
      // Clear the field generation service session
      fieldGenerationService.clearSession(chatbotId.value)
      emit('created', chatbotId.value)

      // Log if embedding is still in progress
      if (response.data.embedding_in_progress) {
        console.log(`[Wizard] Chatbot finalized, embedding still in progress: ${response.data.embedding_progress}%`)
      }
    } else {
      setError('general', response.data.error || 'Fehler beim Erstellen')
    }
  } catch (error) {
    console.error('[Wizard] Finalize error:', error)
    setError('general', error.response?.data?.error || 'Fehler beim Erstellen')
  } finally {
    setLoading(false)
  }
}

// ===== Test & Close =====
function handleTestChatbot() {
  emit('test', chatbotId.value)
  handleClose()
}

function handleClose() {
  unsubscribeFromProgress()
  stopElapsedTimeUpdates()
  emit('close')
}

async function syncWizardFromBackend(id, { overwriteWizardData = false } = {}) {
  try {
    const statusResponse = await axios.get(`/api/chatbots/${id}/wizard/status`)
    if (statusResponse.data?.success) {
      const incomingStatus = statusResponse.data.build_status
      if (overwriteWizardData && ['configuring', 'ready'].includes(incomingStatus)) {
        hasAutoGeneratedFields.value = true
      }
      if (statusResponse.data.build_status) {
        setStatus(statusResponse.data.build_status)
      }

      const collection = statusResponse.data.collection
      if (collection?.id) {
        setCollectionId(collection.id)
        updateCollectionInfo(collection)
        if (collection.embedding_progress !== undefined) {
          updateEmbeddingProgress({ progress: collection.embedding_progress })
        }
        if (!crawlerJobId.value && collection.crawl_job_id) {
          setCrawlerJobId(collection.crawl_job_id)
        }
      }

      if (statusResponse.data.build_status === BUILD_STATUS.READY) {
        return
      }
    }

    const chatbotResponse = await axios.get(`/api/chatbots/${id}`)
    const chatbot = chatbotResponse.data?.chatbot
    if (chatbot) {
      // Only fill blanks to avoid overriding unsaved wizard edits (unless overwrite is requested).
      if ((overwriteWizardData || !wizardData.value.url) && chatbot.source_url) wizardData.value.url = chatbot.source_url
      if ((overwriteWizardData || !wizardData.value.name) && chatbot.name) wizardData.value.name = chatbot.name
      if ((overwriteWizardData || !wizardData.value.displayName) && chatbot.display_name) wizardData.value.displayName = chatbot.display_name
      if ((overwriteWizardData || !wizardData.value.systemPrompt) && chatbot.system_prompt) wizardData.value.systemPrompt = chatbot.system_prompt
      if ((overwriteWizardData || !wizardData.value.welcomeMessage) && chatbot.welcome_message) wizardData.value.welcomeMessage = chatbot.welcome_message
      if ((overwriteWizardData || !wizardData.value.fallbackMessage) && chatbot.fallback_message) wizardData.value.fallbackMessage = chatbot.fallback_message
      if ((overwriteWizardData || !wizardData.value.modelName) && chatbot.model_name) wizardData.value.modelName = chatbot.model_name
      if ((overwriteWizardData || !wizardData.value.icon) && chatbot.icon) wizardData.value.icon = chatbot.icon
      if ((overwriteWizardData || !wizardData.value.color) && chatbot.color) wizardData.value.color = chatbot.color
      if (chatbot.primary_collection_id && !collectionId.value) {
        setCollectionId(chatbot.primary_collection_id)
      }
    }
  } catch (error) {
    const status = error?.response?.status
    if (status !== 404 && status !== 403) {
      console.warn('[Wizard] Failed to sync wizard from backend:', error)
    }
    // 404/403 means chatbot doesn't exist or no access - just skip silently
  }
}

async function resumeWizardForChatbot(id) {
  if (!id) return

  // Reset current wizard state and load from DB (source of truth)
  unsubscribeFromProgress()
  stopElapsedTimeUpdates()
  resetWizard()
  hasAutoGeneratedFields.value = false
  setChatbotId(id)

  await syncWizardFromBackend(id, { overwriteWizardData: true })

  if (crawlerJobId.value || collectionId.value) {
    subscribeToProgress(crawlerJobId.value)
  }

  if (isCrawling.value) {
    startCrawlTimer()
    startElapsedTimeUpdates()
  }
}

// ===== Lifecycle =====
onMounted(() => {
  if (isConnected.value) {
    socket.value = getSocket()
  }
})

onUnmounted(() => {
  unsubscribeFromProgress()
  stopElapsedTimeUpdates()
  // Unsubscribe from field updates but DON'T clear the service session
  // This allows streams to continue running in the background
  unsubscribeFromFieldUpdates()
})

// If collectionId becomes available after socket subscription, subscribe to collection updates
watch(collectionId, (newId, oldId) => {
  if (!socket.value || !socketSubscribed.value) return
  if (oldId && oldId !== newId) {
    socket.value.emit('rag:unsubscribe_collection', { collection_id: oldId })
  }
  if (newId) {
    socket.value.emit('rag:subscribe_collection', { collection_id: newId })
    requestCollectionDocuments({ force: true })
  }
})

// When chatbotId becomes available, subscribe to field updates
watch(chatbotId, (newId, oldId) => {
  if (oldId && oldId !== newId) {
    // Unsubscribe from old chatbot's updates
    unsubscribeFromFieldUpdates()
  }
  if (newId) {
    // Sync any existing content and subscribe to updates
    syncFieldsFromService()
    subscribeToFieldUpdates()
  }
})

// Auto-generate on config step entry
watch(currentStep, async (newStep) => {
  if (newStep === WIZARD_STEPS.CONFIGURATION) {
    // Always sync icon/color when entering config step
    await syncChatbotIconAndColor()
    if (!hasAutoGeneratedFields.value) {
      await autoGenerateFields()
    }
  }
})

// Load models when wizard mounts
onMounted(async () => {
  // When opened without a chatbot to resume, always start a fresh wizard session.
  // Resuming an in-progress build is done explicitly via the Chatbots list.
  if (!props.resumeChatbotId) {
    resetWizard()
    hasAutoGeneratedFields.value = false
    await loadModels()
    return
  }

  await loadModels()
  await resumeWizardForChatbot(props.resumeChatbotId)

  // Subscribe to field updates from the global service
  // and sync any content that was generated while we were away
  if (chatbotId.value) {
    syncFieldsFromService()
    subscribeToFieldUpdates()
  }
})
</script>

<style scoped>
/* Wizard host fills all available space from parent */
.wizard-host {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Wizard card fills all available space */
.wizard-card {
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 0;
  border: none;
}

/* Stepper content - fills remaining space */
.stepper-content {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.stepper-content :deep(.v-window),
.stepper-content :deep(.v-window__container),
.stepper-content :deep(.v-window-item) {
  height: 100%;
}

.stepper-content :deep(.v-window-item) {
  overflow-y: auto;
}

/* Footer stays at bottom */
.wizard-footer {
  flex-shrink: 0;
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
  background: rgb(var(--v-theme-surface));
}

/* Hide the default stepper header since we use custom */
.stepper-content :deep(.v-stepper-header) {
  display: none;
}

/* Custom Steps Styling */
.wizard-steps {
  flex-shrink: 0;
  background: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}

.step-item {
  min-width: 80px;
  transition: all 0.2s ease;
}

.step-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 500;
  background: rgba(var(--v-theme-on-surface), 0.12);
  color: rgb(var(--v-theme-on-surface));
  transition: all 0.2s ease;
}

.step-title {
  color: rgb(var(--v-theme-on-surface-variant));
  transition: color 0.2s ease;
}

.step-progress {
  width: 60px;
  margin: 0 auto;
}

/* Active Step */
.step-active .step-circle {
  background: rgb(var(--v-theme-primary));
  color: white;
  box-shadow: 0 2px 8px rgba(var(--v-theme-primary), 0.4);
}

.step-active .step-title {
  color: rgb(var(--v-theme-primary));
  font-weight: 500;
}

/* Completed Step */
.step-complete .step-circle {
  background: rgb(var(--v-theme-success));
  color: white;
}

.step-complete .step-title {
  color: rgb(var(--v-theme-success));
}

/* Clickable Step */
.step-clickable {
  cursor: pointer;
}

.step-clickable:hover .step-circle {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.step-clickable:hover .step-title {
  color: rgb(var(--v-theme-primary));
}

/* Disabled Step */
.step-disabled {
  cursor: not-allowed;
}

.step-disabled .step-circle {
  opacity: 0.5;
}

.step-disabled .step-title {
  opacity: 0.5;
}

/* Connector Line */
.step-connector {
  height: 2px;
  background: rgba(var(--v-theme-on-surface), 0.12);
  margin-top: -20px;
  transition: background 0.3s ease;
}

.step-connector-complete {
  background: rgb(var(--v-theme-success));
}
</style>
