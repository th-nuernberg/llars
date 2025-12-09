<template>
  <v-dialog
    v-model="dialogModel"
    max-width="1000"
    persistent
    scrollable
  >
    <v-card>
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-4 bg-primary">
        <v-icon class="mr-2">mdi-wizard-hat</v-icon>
        <span>Chatbot Builder Wizard</span>
        <v-spacer />

        <!-- Processing Indicator with Progress -->
        <template v-if="isProcessing">
          <div class="d-flex align-center mr-3">
            <v-progress-circular
              v-if="overallProgressPercent === 0"
              indeterminate
              size="20"
              width="2"
              color="white"
              class="mr-2"
            />
            <v-progress-circular
              v-else
              :model-value="overallProgressPercent"
              size="24"
              width="3"
              color="white"
              class="mr-2"
            >
              <span class="text-caption">{{ overallProgressPercent }}</span>
            </v-progress-circular>
            <span class="text-body-2">
              {{ headerStatusText }}
              <span v-if="currentProgressText">({{ currentProgressText }})</span>
            </span>
          </div>
        </template>

        <v-btn icon variant="text" @click="handleClose">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>


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
        class="stepper-content"
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
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :collection-documents="collectionDocuments"
            :documents-loading="documentsLoading"
            :error-message="errors.crawl || errors.general"
            @skip-to-config="handleSkipToConfig"
            @refresh-documents="fetchCollectionDocuments"
            @pause="handlePauseBuild"
          />
        </template>

        <!-- Step 3: Embedding Progress -->
        <template #item.3>
          <StepCollectionSetup
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :collection-documents="collectionDocuments"
            :documents-loading="documentsLoading"
            :error-message="errors.embedding || errors.general"
            @skip-to-config="handleSkipToConfig"
            @refresh-documents="fetchCollectionDocuments"
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
            @generate-field="handleGenerateField"
          />
        </template>

        <!-- Step 5: Complete -->
        <template #item.5>
          <StepReview
            :config="wizardData"
            :url="wizardData.url"
            :collection-info="collectionInfo"
            @test="handleTestChatbot"
            @close="handleClose"
          />
        </template>
      </v-stepper>

      <!-- Footer Actions -->
      <v-card-actions v-if="currentStep < 5" class="pa-4">
        <v-btn
          v-if="currentStep > 1"
          variant="text"
          @click="handlePreviousStep"
        >
          Zurück
        </v-btn>
        <v-spacer />

        <!-- Step 1: Start Button -->
        <v-btn
          v-if="currentStep === 1"
          color="primary"
          :loading="loading"
          :disabled="!wizardData.url || loading"
          @click="handleStartWizard"
        >
          <v-icon start>mdi-rocket-launch</v-icon>
          Crawling starten
        </v-btn>

        <!-- Step 2/3: Progress Actions -->
        <template v-if="currentStep === 2 || currentStep === 3">
          <v-btn
            v-if="isProcessing"
            variant="outlined"
            color="warning"
            class="mr-2"
            @click="handlePauseBuild"
          >
            <v-icon start>mdi-pause</v-icon>
            Pausieren
          </v-btn>
          <v-btn
            color="primary"
            variant="text"
            @click="handleSkipToConfig"
          >
            <v-icon start>mdi-skip-forward</v-icon>
            Zur Konfiguration
          </v-btn>
        </template>

        <!-- Step 4: Finalize Button -->
        <v-btn
          v-if="currentStep === 4"
          color="primary"
          :loading="loading"
          :disabled="isProcessing || loading || !canFinalize"
          @click="handleFinalizeChatbot"
        >
          <template v-if="isProcessing">
            <v-progress-circular
              indeterminate
              size="16"
              width="2"
              class="mr-2"
            />
            Warte auf {{ isCrawling ? 'Crawling' : 'Embedding' }}...
          </template>
          <template v-else>
            <v-icon start>mdi-check</v-icon>
            Chatbot erstellen
          </template>
        </v-btn>
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
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getSocket, useSocketState } from '@/services/socketService'
import { useBuilderState, BUILD_STATUS, WIZARD_STEPS } from '@/composables/useBuilderState'
import StepCrawlerConfig from './BuilderSteps/StepCrawlerConfig.vue'
import StepCollectionSetup from './BuilderSteps/StepCollectionSetup.vue'
import StepChatbotConfig from './BuilderSteps/StepChatbotConfig.vue'
import StepReview from './BuilderSteps/StepReview.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'created', 'test'])

// ===== Dialog Model =====
const dialogModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// ===== Socket.IO =====
const { isConnected } = useSocketState()
const socket = ref(null)
const socketSubscribed = ref(false)

// ===== Local State =====
const collectionDocuments = ref([])
const documentsLoading = ref(false)
const lastDocFetch = ref(0)
const hasAutoGeneratedFields = ref(false)
const pollingInterval = ref(null)
const elapsedTimeInterval = ref(null)

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
    if (stage === 'planning') return 'URL-Erkundung'
    if (stage === 'planning_done') return 'Crawling startet'
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
  fetchCollectionDocuments(true)
}

// ===== Wizard Start =====
async function handleStartWizard() {
  if (!wizardData.value.url) {
    setError('url', 'URL ist erforderlich')
    return
  }

  // Validate URL
  try {
    new URL(wizardData.value.url)
  } catch {
    setError('url', 'Ungültige URL')
    return
  }

  setLoading(true)
  clearError()

  try {
    // Create wizard chatbot
    const response = await axios.post('/api/chatbots/wizard', {
      url: wizardData.value.url
    })

    if (response.data.success) {
      setChatbotId(response.data.chatbot_id)
      wizardData.value.name = response.data.name || ''
      wizardData.value.displayName = response.data.display_name || ''

      // Move to crawling step
      setStatus(BUILD_STATUS.CRAWLING)
      startCrawlTimer()

      // Start crawl - get job_id first
      const crawlResult = await startCrawl()

      if (crawlResult?.job_id) {
        // Subscribe to progress updates AFTER we have the job_id
        subscribeToProgress(crawlResult.job_id)
      }

      // Start polling as backup
      startPolling()

      // Initial document fetch
      await fetchCollectionDocuments(true)
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
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/crawl`, {
      max_pages: crawlerConfig.value.maxPages,
      max_depth: crawlerConfig.value.maxDepth,
      use_playwright: crawlerConfig.value.usePlaywright,
      use_vision_llm: crawlerConfig.value.useVisionLlm
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
    stopPolling()
  } catch (error) {
    console.error('Error pausing build:', error)
    setError('general', 'Fehler beim Pausieren')
  }
}

// ===== Socket.IO Subscriptions =====
function subscribeToProgress(jobId = null) {
  socket.value = getSocket()
  if (!socket.value) {
    console.warn('[Wizard] Socket not available, relying on polling')
    return
  }

  if (socketSubscribed.value) return
  socketSubscribed.value = true

  // Subscribe to RAG queue for embedding updates
  socket.value.emit('rag:subscribe_queue')

  // Subscribe to crawler job - use passed jobId or stored one
  const effectiveJobId = jobId || crawlerJobId.value
  if (effectiveJobId) {
    console.log('[Wizard] Joining crawler session:', effectiveJobId)
    socket.value.emit('crawler:join_session', { session_id: effectiveJobId })
  }

  // Global crawler updates
  socket.value.emit('crawler:subscribe_jobs')

  // Crawler progress
  socket.value.on('crawler:progress', handleCrawlerProgress)
  socket.value.on('crawler:page_crawled', handlePageCrawled)
  socket.value.on('crawler:complete', handleCrawlerComplete)
  socket.value.on('crawler:error', handleCrawlerError)

  // Embedding progress
  socket.value.on('rag:collection_progress', handleEmbeddingProgress)
  socket.value.on('rag:collection_completed', handleEmbeddingComplete)
  socket.value.on('rag:collection_error', handleEmbeddingError)

  console.log('[Wizard] Subscribed to socket events')
}

function unsubscribeFromProgress() {
  if (!socket.value || !socketSubscribed.value) return

  socket.value.emit('rag:unsubscribe_queue')
  if (crawlerJobId.value) {
    socket.value.emit('crawler:leave_session', { session_id: crawlerJobId.value })
  }
  socket.value.emit('crawler:unsubscribe_jobs')

  socket.value.off('crawler:progress', handleCrawlerProgress)
  socket.value.off('crawler:page_crawled', handlePageCrawled)
  socket.value.off('crawler:complete', handleCrawlerComplete)
  socket.value.off('crawler:error', handleCrawlerError)
  socket.value.off('rag:collection_progress', handleEmbeddingProgress)
  socket.value.off('rag:collection_completed', handleEmbeddingComplete)
  socket.value.off('rag:collection_error', handleEmbeddingError)

  socketSubscribed.value = false
  console.log('[Wizard] Unsubscribed from socket events')
}

// ===== Socket Event Handlers =====
function handleCrawlerProgress(data) {
  console.log('[Wizard] Crawler progress:', data)

  // Map backend data to frontend format
  const progressData = {
    stage: data.stage || (data.status === 'planning' ? 'planning' : 'crawling'),
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

  // Only fetch docs during actual crawling, not during planning
  if (progressData.stage !== 'planning') {
    throttledDocFetch()
  }
}

function handlePageCrawled(data) {
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
  updateElapsedTime()
  throttledDocFetch()
}

function handleCrawlerComplete(data) {
  console.log('[Wizard] Crawler complete:', data)
  updateCrawlProgress({
    pages_crawled: data.pages_crawled,
    documents_created: data.documents_created,
    documents_linked: data.documents_linked,
    stage: 'completed'
  })

  // Transition to embedding
  setStatus(BUILD_STATUS.EMBEDDING)
  fetchCollectionDocuments(true)
}

function handleCrawlerError(data) {
  console.error('[Wizard] Crawler error:', data)
  setError('crawl', data.error || 'Crawling fehlgeschlagen')
}

function handleEmbeddingProgress(data) {
  console.log('[Wizard] Embedding progress:', data)
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

  if (data.documents_total) {
    updateCollectionInfo({
      document_count: data.documents_total,
      total_chunks: data.chunks_completed || 0
    })
  }
  throttledDocFetch()
}

function handleEmbeddingComplete(data) {
  console.log('[Wizard] Embedding complete:', data)
  updateEmbeddingProgress(100)
  updateCollectionInfo({
    document_count: data.total_documents,
    total_chunks: data.total_chunks
  })

  setStatus(BUILD_STATUS.CONFIGURING)
  fetchCollectionDocuments(true)

  // Auto-generate fields when reaching config
  autoGenerateFields()
}

function handleEmbeddingError(data) {
  console.error('[Wizard] Embedding error:', data)
  setError('embedding', data.error || 'Embedding fehlgeschlagen')
  setStatus(BUILD_STATUS.ERROR)
}

// ===== Polling (Fallback) =====
function startPolling() {
  if (pollingInterval.value) return

  // Poll immediately on start
  pollBuildStatus()

  // Then poll every 2 seconds
  pollingInterval.value = setInterval(pollBuildStatus, 2000)

  // Also start elapsed time updates
  elapsedTimeInterval.value = setInterval(updateElapsedTime, 1000)
}

function stopPolling() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
  if (elapsedTimeInterval.value) {
    clearInterval(elapsedTimeInterval.value)
    elapsedTimeInterval.value = null
  }
}

async function pollBuildStatus() {
  if (!chatbotId.value) return

  try {
    // Fetch wizard status
    const response = await axios.get(`/api/chatbots/${chatbotId.value}/wizard/status`)

    if (response.data.success) {
      const newStatus = response.data.build_status
      const collectionStatus = response.data.collection?.embedding_status

      // Handle status transitions based on CHATBOT build_status, not collection status
      // The backend sets chatbot.build_status = 'embedding' when crawl is done
      if (newStatus === 'embedding' && buildStatus.value === BUILD_STATUS.CRAWLING) {
        setStatus(BUILD_STATUS.EMBEDDING)
      } else if (newStatus === 'configuring' && buildStatus.value !== BUILD_STATUS.CONFIGURING) {
        setStatus(BUILD_STATUS.CONFIGURING)
        autoGenerateFields()
      } else if (newStatus === 'ready') {
        setStatus(BUILD_STATUS.READY)
        stopPolling()
      } else if (newStatus === 'error') {
        setStatus(BUILD_STATUS.ERROR, response.data.build_error)
        stopPolling()
      }

      // Update collection info (embedding runs in background while crawling)
      if (response.data.collection) {
        updateCollectionInfo(response.data.collection)
        updateEmbeddingProgress(response.data.collection.embedding_progress || 0)
      }

      // Stop polling if no longer processing
      if (!['crawling', 'embedding'].includes(newStatus)) {
        stopPolling()
      }
    }

    // Also fetch crawler job status for detailed progress
    if (crawlerJobId.value && buildStatus.value === BUILD_STATUS.CRAWLING) {
      try {
        const crawlerResponse = await axios.get(`/api/crawler/jobs/${crawlerJobId.value}`)
        if (crawlerResponse.data.success && crawlerResponse.data.job) {
          const job = crawlerResponse.data.job

          // Determine the stage from job status
          let stage = 'crawling'
          if (job.status === 'queued') {
            stage = 'planning'
          } else if (job.status === 'running') {
            // Check if we have urls_total > 0 to determine if planning is done
            stage = (job.urls_total && job.urls_total > 0) ? 'crawling' : 'planning'
          } else if (job.status === 'completed' || job.status === 'finished') {
            stage = 'completed'
          }

          updateCrawlProgress({
            stage: stage,
            urlsTotal: job.urls_total || 0,
            urlsCompleted: job.urls_completed || 0,
            pagesProcessed: job.pages_crawled || 0,
            pagesTotal: job.max_pages || 0,
            documentsCreated: job.documents_created || 0,
            documentsLinked: job.documents_linked || 0,
            imagesExtracted: job.images_extracted || 0,
            screenshotsTaken: job.screenshots_taken || 0,
            crawlerType: job.use_playwright ? 'Playwright' : 'Basic'
          })

          // Check if crawl is complete
          if (job.status === 'completed' || job.status === 'finished') {
            setStatus(BUILD_STATUS.EMBEDDING)
          }
        }
      } catch (crawlerError) {
        console.warn('[Wizard] Could not fetch crawler status:', crawlerError)
      }
    }
  } catch (error) {
    console.error('[Wizard] Poll error:', error)
  }
}

// ===== Document Fetching =====
function throttledDocFetch() {
  const now = Date.now()
  if (now - lastDocFetch.value < 3000) return
  fetchCollectionDocuments()
}

async function fetchCollectionDocuments(force = false) {
  if (!chatbotId.value) return

  const now = Date.now()
  if (!force && now - lastDocFetch.value < 2000) return

  documentsLoading.value = true
  try {
    const response = await axios.get(`/api/chatbots/${chatbotId.value}/wizard/collection-documents`)
    if (response.data.success) {
      collectionDocuments.value = response.data.documents || []
      lastDocFetch.value = Date.now()
    }
  } catch (error) {
    console.error('[Wizard] Error fetching documents:', error)
  } finally {
    documentsLoading.value = false
  }
}

// ===== Field Generation =====
async function autoGenerateFields() {
  if (hasAutoGeneratedFields.value) return
  if (!chatbotId.value) return

  hasAutoGeneratedFields.value = true

  const fields = ['name', 'display_name', 'system_prompt', 'welcome_message']
  for (const field of fields) {
    await handleGenerateField(field)
  }
}

async function handleGenerateField(field) {
  if (!chatbotId.value) return
  if (generating.value[field]) return

  setGenerating(field, true)

  try {
    // Use streaming for long fields
    if (['system_prompt', 'welcome_message'].includes(field)) {
      await streamFieldGeneration(field)
    } else {
      const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/generate-field`, {
        field
      })

      if (response.data.success) {
        applyFieldValue(field, response.data.value)
      }
    }
  } catch (error) {
    console.error(`[Wizard] Error generating ${field}:`, error)
  } finally {
    setGenerating(field, false)
  }
}

async function streamFieldGeneration(field) {
  const token = sessionStorage.getItem('auth_token')

  const response = await fetch(`/api/chatbots/${chatbotId.value}/wizard/generate-field`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ field, stream: true })
  })

  if (!response.ok || !response.body) {
    throw new Error(`Streaming failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let accumulated = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data:')) continue

      try {
        const payload = JSON.parse(line.replace(/^data:\s*/, ''))
        if (payload.delta) {
          accumulated += payload.delta
          applyFieldValue(field, accumulated)
        }
        if (payload.done && payload.value) {
          applyFieldValue(field, payload.value)
        }
      } catch (e) {
        console.error('[Wizard] Stream parse error:', e)
      }
    }
  }

  // Process remaining buffer
  if (buffer.trim().startsWith('data:')) {
    try {
      const payload = JSON.parse(buffer.replace(/^data:\s*/, ''))
      if (payload.value) {
        applyFieldValue(field, payload.value)
      }
    } catch (e) {
      console.error('[Wizard] Final buffer parse error:', e)
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
  }
}

// ===== Finalize =====
async function handleFinalizeChatbot() {
  if (!chatbotId.value) return
  if (isProcessing.value) return

  setLoading(true)

  try {
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/finalize`, {
      name: wizardData.value.name,
      display_name: wizardData.value.displayName,
      system_prompt: wizardData.value.systemPrompt,
      welcome_message: wizardData.value.welcomeMessage,
      fallback_message: wizardData.value.fallbackMessage,
      icon: wizardData.value.icon,
      color: wizardData.value.color
    })

    if (response.data.success) {
      setStatus(BUILD_STATUS.READY)
      emit('created', chatbotId.value)
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
  stopPolling()
  dialogModel.value = false
  resetWizard()
  collectionDocuments.value = []
  hasAutoGeneratedFields.value = false
}

// ===== Lifecycle =====
onMounted(() => {
  if (isConnected.value) {
    socket.value = getSocket()
  }
})

onUnmounted(() => {
  unsubscribeFromProgress()
  stopPolling()
})

// Watch dialog state
watch(dialogModel, (newValue) => {
  if (!newValue) {
    resetWizard()
    hasAutoGeneratedFields.value = false
  }
})

// Auto-generate on config step entry
watch(currentStep, async (newStep) => {
  if (newStep === WIZARD_STEPS.CONFIGURATION && !hasAutoGeneratedFields.value) {
    await autoGenerateFields()
  }
})
</script>

<style scoped>
/* Hide the default stepper header since we use custom */
.stepper-content :deep(.v-stepper-header) {
  display: none;
}

/* Custom Steps Styling */
.wizard-steps {
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
