<template>
  <v-dialog
    v-model="dialogModel"
    max-width="1000"
    persistent
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-4 bg-primary">
        <v-icon class="mr-2">mdi-wizard-hat</v-icon>
        <span>Chatbot Builder Wizard</span>
        <v-spacer />
        <!-- Background process indicator -->
        <v-chip
          v-if="isProcessing"
          size="small"
          :color="buildStatus === 'crawling' ? 'warning' : 'info'"
          class="mr-3"
        >
          <v-progress-circular
            indeterminate
            size="14"
            width="2"
            class="mr-2"
          />
          {{ buildStatus === 'crawling' ? 'Crawling läuft...' : 'Embedding läuft...' }}
        </v-chip>
        <v-btn icon variant="text" @click="closeDialog">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Stepper -->
      <v-stepper
        v-model="currentStep"
        :items="stepItems"
        alt-labels
        flat
        hide-actions
      >
        <!-- Custom clickable header -->
        <template #header-item="{ item }">
          <v-stepper-item
            :value="item.value"
            :title="item.title"
            :complete="currentStep > item.value"
            :color="currentStep >= item.value ? 'primary' : undefined"
            :class="{ 'cursor-pointer': canNavigateToStep(item.value) }"
            :style="canNavigateToStep(item.value) ? 'cursor: pointer' : 'cursor: default'"
            @click="navigateToStep(item.value)"
          />
        </template>

        <!-- Step 1: URL Input -->
        <template #item.1>
          <StepCrawlerConfig
            v-model:url="wizardData.url"
            v-model:config="crawlerConfig"
            :error-message="errors.url || errors.general"
            @start="startWizard"
          />
        </template>

        <!-- Step 2 & 3: Crawling & Embedding Progress (Combined) -->
        <template #item.2>
          <StepCollectionSetup
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :error-message="errors.crawl"
            @skip-to-config="skipToConfiguration"
            @pause="pauseBuild"
          />
        </template>

        <template #item.3>
          <StepCollectionSetup
            :build-status="buildStatus"
            :crawl-progress="crawlProgress"
            :embedding-progress="embeddingProgress"
            :collection-info="collectionInfo"
            :error-message="errors.crawl"
            @skip-to-config="skipToConfiguration"
            @pause="pauseBuild"
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
            @generate-field="generateField"
          />
        </template>

        <!-- Step 5: Complete -->
        <template #item.5>
          <StepReview
            :config="wizardData"
            :url="wizardData.url"
            :collection-info="collectionInfo"
            @test="testChatbot"
            @close="closeDialog"
          />
        </template>
      </v-stepper>

      <!-- Actions -->
      <v-card-actions v-if="currentStep < 5" class="pa-4">
        <v-btn
          v-if="currentStep > 1"
          variant="text"
          @click="previousStep"
        >
          Zurück
        </v-btn>
        <v-spacer />
        <v-btn
          v-if="currentStep === 1"
          color="primary"
          :loading="loading"
          :disabled="!wizardData.url"
          @click="startWizard"
        >
          Crawling starten
        </v-btn>
        <v-btn
          v-else-if="currentStep === 4"
          color="primary"
          :loading="loading"
          :disabled="isProcessing"
          @click="finalizeChatbot"
        >
          <template v-if="isProcessing">
            <v-progress-circular
              indeterminate
              size="16"
              width="2"
              class="mr-2"
            />
            Warte auf {{ buildStatus === 'crawling' ? 'Crawling' : 'Embedding' }}...
          </template>
          <template v-else>
            Chatbot erstellen
          </template>
        </v-btn>
        <v-btn
          v-else-if="isProcessing && (currentStep === 2 || currentStep === 3)"
          variant="outlined"
          color="warning"
          @click="pauseBuild"
        >
          Pausieren
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { getSocket, useSocketState } from '@/services/socketService'
import { useBuilderState } from '@/composables/useBuilderState'
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

// Dialog model
const dialogModel = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Socket.IO
const { isConnected } = useSocketState()
const socket = ref(null)

// Builder state
const {
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
  isProcessing,
  canNavigateToStep,
  navigateToStep,
  updateCrawlProgress,
  updateElapsedTime,
  addRecentPage,
  updateEmbeddingProgress,
  updateCollectionInfo,
  resetWizard,
  resetErrors
} = useBuilderState()

// Polling
const pollingInterval = ref(null)

// Stepper items
const stepItems = [
  { title: 'URL', value: 1 },
  { title: 'Crawling', value: 2 },
  { title: 'Embedding', value: 3 },
  { title: 'Konfiguration', value: 4 },
  { title: 'Fertig', value: 5 }
]

// Methods
async function startWizard() {
  if (!wizardData.value.url) {
    errors.value.url = 'URL ist erforderlich'
    return
  }

  loading.value = true
  resetErrors()

  try {
    // Create wizard chatbot
    const response = await axios.post('/api/chatbots/wizard', {
      url: wizardData.value.url
    })

    if (response.data.success) {
      chatbotId.value = response.data.chatbot_id
      wizardData.value.name = response.data.name
      wizardData.value.displayName = response.data.display_name

      // Move to step 2 and start crawl
      currentStep.value = 2
      crawlProgress.value.startTime = Date.now()

      // Start crawling
      await startCrawl()

      // Start polling for status
      startStatusPolling()
    } else {
      errors.value.general = response.data.error
    }
  } catch (error) {
    console.error('Error starting wizard:', error)
    errors.value.general = error.response?.data?.error || 'Fehler beim Starten des Wizards'
  } finally {
    loading.value = false
  }
}

async function startCrawl() {
  try {
    buildStatus.value = 'crawling'
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/crawl`)

    if (response.data.success) {
      crawlerJobId.value = response.data.job_id
      // Subscribe to crawler events
      subscribeToProgress()
    } else {
      errors.value.crawl = response.data.error
      buildStatus.value = 'error'
    }
  } catch (error) {
    console.error('Error starting crawl:', error)
    errors.value.crawl = error.response?.data?.error || 'Fehler beim Crawlen'
    buildStatus.value = 'error'
  }
}

function subscribeToProgress() {
  socket.value = getSocket()
  if (!socket.value) {
    console.warn('Socket not available, relying on polling only')
    return
  }

  // Subscribe to RAG queue for embedding updates
  socket.value.emit('rag:subscribe_queue')

  // Subscribe to crawler job updates if we have a job ID
  if (crawlerJobId.value) {
    socket.value.emit('crawler:join_session', { session_id: crawlerJobId.value })
  }

  // Also subscribe to global crawler updates
  socket.value.emit('crawler:subscribe_jobs')

  // Listen for crawler progress
  socket.value.on('crawler:progress', (data) => {
    console.log('Crawler progress:', data)
    updateCrawlProgress(data)
    updateElapsedTime()
  })

  socket.value.on('crawler:page_crawled', (data) => {
    console.log('Page crawled:', data)
    if (data.url) {
      addRecentPage(data.url)
    }
    // Update documents from the event (cumulative counts)
    if (data.documents_created !== undefined) {
      crawlProgress.value.documentsCreated = data.documents_created
    }
    if (data.documents_linked !== undefined) {
      crawlProgress.value.documentsLinked = data.documents_linked
    }
    updateElapsedTime()
  })

  socket.value.on('crawler:complete', (data) => {
    console.log('Crawler complete:', data)
    crawlProgress.value.pagesProcessed = data.pages_crawled || crawlProgress.value.pagesProcessed
    crawlProgress.value.documentsCreated = data.documents_created || crawlProgress.value.documentsCreated
    buildStatus.value = 'embedding'
    currentStep.value = 3
  })

  socket.value.on('crawler:error', (data) => {
    console.error('Crawler error:', data)
    errors.value.crawl = data.error
  })

  // Listen for embedding progress
  socket.value.on('rag:collection_progress', (data) => {
    console.log('Embedding progress:', data)
    updateEmbeddingProgress(data.progress || 0)
    if (data.documents_total) {
      updateCollectionInfo({
        ...collectionInfo.value,
        document_count: data.documents_total,
        total_chunks: data.chunks_completed || 0
      })
    }
  })

  socket.value.on('rag:collection_completed', (data) => {
    console.log('Embedding complete:', data)
    updateEmbeddingProgress(100)
    updateCollectionInfo({
      document_count: data.total_documents,
      total_chunks: data.total_chunks
    })
    buildStatus.value = 'configuring'
    if (currentStep.value < 4) {
      currentStep.value = 4
    }
  })

  socket.value.on('rag:collection_error', (data) => {
    console.error('Embedding error:', data)
    errors.value.general = data.error
    buildStatus.value = 'error'
  })
}

function unsubscribeFromProgress() {
  if (!socket.value) return

  socket.value.emit('rag:unsubscribe_queue')
  if (crawlerJobId.value) {
    socket.value.emit('crawler:leave_session', { session_id: crawlerJobId.value })
  }
  socket.value.emit('crawler:unsubscribe_jobs')

  socket.value.off('crawler:progress')
  socket.value.off('crawler:page_crawled')
  socket.value.off('crawler:complete')
  socket.value.off('crawler:error')
  socket.value.off('rag:collection_progress')
  socket.value.off('rag:collection_completed')
  socket.value.off('rag:collection_error')
}

function startStatusPolling() {
  // Poll every 2 seconds as backup to WebSocket
  pollingInterval.value = setInterval(pollBuildStatus, 2000)
}

function stopStatusPolling() {
  if (pollingInterval.value) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

async function pollBuildStatus() {
  if (!chatbotId.value) return

  try {
    const response = await axios.get(`/api/chatbots/${chatbotId.value}/wizard/status`)

    if (response.data.success) {
      const newStatus = response.data.build_status

      // Update build status
      if (newStatus !== buildStatus.value) {
        buildStatus.value = newStatus

        // Auto-advance steps based on status
        if (newStatus === 'embedding' && currentStep.value < 3) {
          currentStep.value = 3
        } else if (newStatus === 'configuring' && currentStep.value < 4) {
          currentStep.value = 4
        } else if (newStatus === 'ready') {
          stopStatusPolling()
        }
      }

      // Update collection info
      if (response.data.collection) {
        updateCollectionInfo(response.data.collection)
        updateEmbeddingProgress(response.data.collection.embedding_progress || 0)

        // Update document count for crawl progress
        if (response.data.collection.document_count) {
          crawlProgress.value.documentsCreated = response.data.collection.document_count
        }
      }

      updateElapsedTime()

      // Stop polling if no longer processing
      if (!['crawling', 'embedding'].includes(newStatus)) {
        stopStatusPolling()
      }
    }
  } catch (error) {
    console.error('Error polling status:', error)
  }
}

function skipToConfiguration() {
  currentStep.value = 4
}

async function generateField(field) {
  if (!chatbotId.value) return

  generating.value[field] = true

  try {
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/generate-field`, {
      field: field
    })

    if (response.data.success) {
      const value = response.data.value
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
  } catch (error) {
    console.error('Error generating field:', error)
  } finally {
    generating.value[field] = false
  }
}

async function finalizeChatbot() {
  if (!chatbotId.value) return

  // Don't allow finalization while still processing
  if (isProcessing.value) return

  loading.value = true

  try {
    const response = await axios.post(`/api/chatbots/${chatbotId.value}/wizard/finalize`, {
      name: wizardData.value.name,
      display_name: wizardData.value.displayName,
      system_prompt: wizardData.value.systemPrompt,
      welcome_message: wizardData.value.welcomeMessage,
      icon: wizardData.value.icon,
      color: wizardData.value.color
    })

    if (response.data.success) {
      currentStep.value = 5
      emit('created', chatbotId.value)
    } else {
      errors.value.general = response.data.error
    }
  } catch (error) {
    console.error('Error finalizing chatbot:', error)
    errors.value.general = error.response?.data?.error || 'Fehler beim Erstellen'
  } finally {
    loading.value = false
  }
}

async function pauseBuild() {
  if (!chatbotId.value) return

  try {
    await axios.post(`/api/chatbots/${chatbotId.value}/wizard/pause`)
    buildStatus.value = 'paused'
    stopStatusPolling()
  } catch (error) {
    console.error('Error pausing build:', error)
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function testChatbot() {
  emit('test', chatbotId.value)
  closeDialog()
}

function closeDialog() {
  unsubscribeFromProgress()
  stopStatusPolling()
  dialogModel.value = false
  resetWizard()
}

// Lifecycle
onMounted(() => {
  if (isConnected.value) {
    socket.value = getSocket()
  }
})

onUnmounted(() => {
  unsubscribeFromProgress()
  stopStatusPolling()
})

// Watch for dialog open/close
watch(dialogModel, (newValue) => {
  if (!newValue) {
    resetWizard()
  }
})
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}

.h-100 {
  height: 100%;
}
</style>
