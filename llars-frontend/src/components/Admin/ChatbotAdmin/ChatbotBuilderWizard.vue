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
          <v-card flat class="pa-4">
            <div class="text-center mb-6">
              <v-icon size="64" color="primary">mdi-web</v-icon>
              <h2 class="text-h5 mt-4">Website URL eingeben</h2>
              <p class="text-medium-emphasis">
                Geben Sie die URL der Website ein, aus der der Chatbot lernen soll.
              </p>
            </div>

            <v-text-field
              v-model="wizardData.url"
              label="Website URL"
              placeholder="https://example.com"
              prepend-inner-icon="mdi-link"
              variant="outlined"
              :rules="[rules.required, rules.url]"
              :error-messages="errors.url"
              @keyup.enter="startWizard"
            />

            <!-- Crawler Options -->
            <v-expansion-panels class="mt-4">
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <v-icon class="mr-2">mdi-cog</v-icon>
                  Erweiterte Crawler-Einstellungen
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-row>
                    <v-col cols="6">
                      <v-text-field
                        v-model.number="crawlerConfig.maxPages"
                        label="Max. Seiten"
                        type="number"
                        min="1"
                        max="500"
                        variant="outlined"
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-text-field
                        v-model.number="crawlerConfig.maxDepth"
                        label="Max. Tiefe"
                        type="number"
                        min="1"
                        max="10"
                        variant="outlined"
                        density="compact"
                      />
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>

            <v-alert
              v-if="errors.general"
              type="error"
              variant="tonal"
              class="mt-4"
            >
              {{ errors.general }}
            </v-alert>
          </v-card>
        </template>

        <!-- Step 2: Crawling Progress (Combined with ability to continue) -->
        <template #item.2>
          <v-card flat class="pa-4">
            <!-- Progress Section -->
            <v-row>
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4 h-100">
                  <div class="d-flex align-center mb-4">
                    <v-progress-circular
                      v-if="buildStatus === 'crawling'"
                      :size="48"
                      :width="4"
                      color="primary"
                      indeterminate
                      class="mr-4"
                    />
                    <v-icon v-else size="48" color="success" class="mr-4">mdi-check-circle</v-icon>
                    <div>
                      <h3 class="text-h6">
                        {{ buildStatus === 'crawling' ? 'Crawling läuft...' : 'Crawling abgeschlossen' }}
                      </h3>
                      <p class="text-body-2 text-medium-emphasis mb-0">
                        {{ crawlProgress.pagesProcessed }} / {{ crawlProgress.pagesTotal || '?' }} Seiten
                      </p>
                    </div>
                  </div>

                  <!-- Progress Bar -->
                  <v-progress-linear
                    :model-value="crawlProgressPercent"
                    :indeterminate="crawlProgress.pagesTotal === 0 && buildStatus === 'crawling'"
                    color="primary"
                    height="8"
                    rounded
                    class="mb-4"
                  />

                  <!-- Current URL -->
                  <div v-if="crawlProgress.currentUrl" class="mb-3">
                    <div class="text-caption text-medium-emphasis">Aktuelle Seite:</div>
                    <div class="text-body-2 text-truncate">{{ crawlProgress.currentUrl }}</div>
                  </div>

                  <!-- Stats -->
                  <div class="d-flex gap-3 flex-wrap">
                    <v-chip size="small" color="success" variant="tonal">
                      <v-icon start size="small">mdi-file-document</v-icon>
                      {{ crawlProgress.documentsCreated + crawlProgress.documentsLinked }} Dokumente
                    </v-chip>
                    <v-chip size="small" color="info" variant="tonal">
                      <v-icon start size="small">mdi-clock</v-icon>
                      {{ formatDuration(crawlProgress.elapsedTime) }}
                    </v-chip>
                  </div>

                  <!-- Recent Pages -->
                  <div v-if="crawlProgress.recentPages.length > 0" class="mt-4">
                    <div class="text-caption text-medium-emphasis mb-2">Zuletzt gecrawlt:</div>
                    <v-list density="compact" class="bg-transparent" max-height="150" style="overflow-y: auto">
                      <v-list-item
                        v-for="(page, index) in crawlProgress.recentPages.slice(-5).reverse()"
                        :key="index"
                        density="compact"
                        class="px-0"
                      >
                        <template #prepend>
                          <v-icon size="small" color="success" class="mr-2">mdi-check</v-icon>
                        </template>
                        <v-list-item-title class="text-body-2 text-truncate">
                          {{ extractPageTitle(page) }}
                        </v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-card>
              </v-col>

              <!-- Right side: Continue to config hint -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4 h-100 d-flex flex-column">
                  <div class="text-center flex-grow-1 d-flex flex-column justify-center">
                    <v-icon size="64" color="info" class="mb-4">mdi-arrow-right-circle</v-icon>
                    <h3 class="text-h6 mb-2">Weiter zur Konfiguration?</h3>
                    <p class="text-body-2 text-medium-emphasis">
                      Sie können bereits mit der Chatbot-Konfiguration beginnen, während das Crawling im Hintergrund weiterläuft.
                    </p>
                  </div>
                  <v-btn
                    color="primary"
                    size="large"
                    block
                    class="mt-4"
                    @click="skipToConfiguration"
                  >
                    <v-icon start>mdi-cog</v-icon>
                    Jetzt konfigurieren
                  </v-btn>
                  <p class="text-caption text-center text-medium-emphasis mt-2 mb-0">
                    Der Chatbot kann erst nach Abschluss des Crawlings getestet werden.
                  </p>
                </v-card>
              </v-col>
            </v-row>

            <v-alert
              v-if="errors.crawl"
              type="error"
              variant="tonal"
              class="mt-4"
            >
              {{ errors.crawl }}
            </v-alert>
          </v-card>
        </template>

        <!-- Step 3: Embedding -->
        <template #item.3>
          <v-card flat class="pa-4">
            <v-row>
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4 h-100">
                  <div class="d-flex align-center mb-4">
                    <v-progress-circular
                      v-if="buildStatus === 'embedding'"
                      :model-value="embeddingProgress"
                      :size="48"
                      :width="4"
                      color="primary"
                    >
                      <span class="text-caption">{{ embeddingProgress }}%</span>
                    </v-progress-circular>
                    <v-icon v-else size="48" color="success" class="mr-4">mdi-check-circle</v-icon>
                    <div class="ml-4">
                      <h3 class="text-h6">
                        {{ buildStatus === 'embedding' ? 'Embedding läuft...' : 'Embedding abgeschlossen' }}
                      </h3>
                      <p class="text-body-2 text-medium-emphasis mb-0">
                        {{ embeddingStatusMessage }}
                      </p>
                    </div>
                  </div>

                  <v-progress-linear
                    :model-value="embeddingProgress"
                    color="primary"
                    height="8"
                    rounded
                    class="mb-4"
                  />

                  <div v-if="collectionInfo" class="d-flex gap-3 flex-wrap">
                    <v-chip size="small" color="info" variant="tonal">
                      <v-icon start size="small">mdi-file-document</v-icon>
                      {{ collectionInfo.document_count }} Dokumente
                    </v-chip>
                    <v-chip size="small" color="success" variant="tonal">
                      <v-icon start size="small">mdi-vector-polygon</v-icon>
                      {{ collectionInfo.total_chunks || 0 }} Chunks
                    </v-chip>
                  </div>
                </v-card>
              </v-col>

              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4 h-100 d-flex flex-column">
                  <div class="text-center flex-grow-1 d-flex flex-column justify-center">
                    <v-icon size="64" color="info" class="mb-4">mdi-arrow-right-circle</v-icon>
                    <h3 class="text-h6 mb-2">Weiter zur Konfiguration?</h3>
                    <p class="text-body-2 text-medium-emphasis">
                      Sie können bereits mit der Chatbot-Konfiguration beginnen, während das Embedding im Hintergrund weiterläuft.
                    </p>
                  </div>
                  <v-btn
                    color="primary"
                    size="large"
                    block
                    class="mt-4"
                    @click="skipToConfiguration"
                  >
                    <v-icon start>mdi-cog</v-icon>
                    Jetzt konfigurieren
                  </v-btn>
                </v-card>
              </v-col>
            </v-row>
          </v-card>
        </template>

        <!-- Step 4: Configuration -->
        <template #item.4>
          <v-card flat class="pa-4">
            <!-- Background process banner -->
            <v-alert
              v-if="isProcessing"
              type="info"
              variant="tonal"
              class="mb-4"
            >
              <div class="d-flex align-center">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  class="mr-3"
                />
                <span>
                  {{ buildStatus === 'crawling' ? 'Crawling läuft im Hintergrund...' : 'Embedding läuft im Hintergrund...' }}
                  <strong>{{ buildStatus === 'crawling' ? `${crawlProgress.pagesProcessed} Seiten` : `${embeddingProgress}%` }}</strong>
                </span>
              </div>
            </v-alert>

            <div class="text-center mb-6">
              <v-icon size="64" color="primary">mdi-cog</v-icon>
              <h2 class="text-h5 mt-4">Chatbot konfigurieren</h2>
              <p class="text-medium-emphasis">
                Passen Sie die Einstellungen Ihres Chatbots an.
              </p>
            </div>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="wizardData.name"
                  label="Interner Name"
                  prepend-inner-icon="mdi-identifier"
                  variant="outlined"
                  :rules="[rules.required]"
                  hint="Nur Kleinbuchstaben und Unterstriche"
                >
                  <template #append>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      :loading="generating.name"
                      :disabled="!chatbotId"
                      @click="generateField('name')"
                    >
                      <v-icon>mdi-auto-fix</v-icon>
                      <v-tooltip activator="parent" location="top">
                        Mit KI generieren
                      </v-tooltip>
                    </v-btn>
                  </template>
                </v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="wizardData.displayName"
                  label="Anzeigename"
                  prepend-inner-icon="mdi-format-title"
                  variant="outlined"
                  :rules="[rules.required]"
                >
                  <template #append>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      :loading="generating.display_name"
                      :disabled="!chatbotId"
                      @click="generateField('display_name')"
                    >
                      <v-icon>mdi-auto-fix</v-icon>
                      <v-tooltip activator="parent" location="top">
                        Mit KI generieren
                      </v-tooltip>
                    </v-btn>
                  </template>
                </v-text-field>
              </v-col>
            </v-row>

            <v-textarea
              v-model="wizardData.systemPrompt"
              label="System Prompt"
              prepend-inner-icon="mdi-text-box"
              variant="outlined"
              rows="4"
              :rules="[rules.required]"
            >
              <template #append>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :loading="generating.system_prompt"
                  :disabled="!chatbotId"
                  @click="generateField('system_prompt')"
                >
                  <v-icon>mdi-auto-fix</v-icon>
                  <v-tooltip activator="parent" location="top">
                    Mit KI generieren
                  </v-tooltip>
                </v-btn>
              </template>
            </v-textarea>

            <v-textarea
              v-model="wizardData.welcomeMessage"
              label="Willkommensnachricht"
              prepend-inner-icon="mdi-message-text"
              variant="outlined"
              rows="2"
            >
              <template #append>
                <v-btn
                  icon
                  variant="text"
                  size="small"
                  :loading="generating.welcome_message"
                  :disabled="!chatbotId"
                  @click="generateField('welcome_message')"
                >
                  <v-icon>mdi-auto-fix</v-icon>
                  <v-tooltip activator="parent" location="top">
                    Mit KI generieren
                  </v-tooltip>
                </v-btn>
              </template>
            </v-textarea>

            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="wizardData.icon"
                  label="Icon"
                  prepend-inner-icon="mdi-emoticon"
                  variant="outlined"
                  placeholder="mdi-robot"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="wizardData.color"
                  label="Farbe"
                  variant="outlined"
                  type="color"
                />
              </v-col>
            </v-row>
          </v-card>
        </template>

        <!-- Step 5: Complete -->
        <template #item.5>
          <v-card flat class="pa-4">
            <div class="text-center">
              <v-icon size="80" color="success">mdi-check-circle</v-icon>
              <h2 class="text-h4 mt-4">Chatbot erstellt!</h2>
              <p class="text-medium-emphasis mt-2">
                Ihr Chatbot "{{ wizardData.displayName }}" wurde erfolgreich erstellt.
              </p>

              <v-card class="mt-6 mx-auto" max-width="400" variant="outlined">
                <v-card-text>
                  <div class="d-flex align-center mb-4">
                    <v-avatar :color="wizardData.color" size="48" class="mr-4">
                      <v-icon color="white">{{ wizardData.icon || 'mdi-robot' }}</v-icon>
                    </v-avatar>
                    <div class="text-left">
                      <div class="text-h6">{{ wizardData.displayName }}</div>
                      <div class="text-caption text-medium-emphasis">{{ wizardData.name }}</div>
                    </div>
                  </div>
                  <v-divider class="mb-4" />
                  <div class="text-body-2 text-left">
                    <div class="mb-2">
                      <strong>Quelle:</strong> {{ wizardData.url }}
                    </div>
                    <div v-if="collectionInfo">
                      <strong>Wissensbasis:</strong>
                      {{ collectionInfo.document_count }} Dokumente,
                      {{ collectionInfo.total_chunks }} Chunks
                    </div>
                  </div>
                </v-card-text>
              </v-card>

              <div class="mt-6">
                <v-btn
                  color="primary"
                  size="large"
                  prepend-icon="mdi-chat"
                  class="mr-4"
                  @click="testChatbot"
                >
                  Chatbot testen
                </v-btn>
                <v-btn
                  variant="outlined"
                  size="large"
                  prepend-icon="mdi-close"
                  @click="closeDialog"
                >
                  Schliessen
                </v-btn>
              </div>
            </div>
          </v-card>
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
const crawlerJobId = ref(null)

// State
const currentStep = ref(1)
const loading = ref(false)
const chatbotId = ref(null)
const buildStatus = ref('draft')
const embeddingProgress = ref(0)
const collectionInfo = ref(null)
const pollingInterval = ref(null)

const wizardData = ref({
  url: '',
  name: '',
  displayName: '',
  systemPrompt: 'Du bist ein hilfreicher Assistent.',
  welcomeMessage: '',
  icon: 'mdi-robot',
  color: '#5d7a4a'
})

const crawlerConfig = ref({
  maxPages: 50,
  maxDepth: 3
})

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

const errors = ref({
  url: null,
  crawl: null,
  general: null
})

const generating = ref({
  name: false,
  display_name: false,
  system_prompt: false,
  welcome_message: false
})

// Stepper items
const stepItems = [
  { title: 'URL', value: 1 },
  { title: 'Crawling', value: 2 },
  { title: 'Embedding', value: 3 },
  { title: 'Konfiguration', value: 4 },
  { title: 'Fertig', value: 5 }
]

// Rules
const rules = {
  required: v => !!v || 'Pflichtfeld',
  url: v => {
    if (!v) return true
    try {
      new URL(v)
      return true
    } catch {
      return 'Ungültige URL'
    }
  }
}

// Computed
const isProcessing = computed(() => {
  return ['crawling', 'embedding'].includes(buildStatus.value)
})

const crawlProgressPercent = computed(() => {
  if (crawlProgress.value.pagesTotal === 0) return 0
  return Math.round((crawlProgress.value.pagesProcessed / crawlProgress.value.pagesTotal) * 100)
})

const embeddingStatusMessage = computed(() => {
  if (buildStatus.value === 'embedding') {
    return `Fortschritt: ${embeddingProgress.value}%`
  }
  return 'Alle Dokumente wurden erfolgreich eingebettet.'
})

// Helper Functions
function formatDuration(seconds) {
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

function extractPageTitle(url) {
  try {
    const urlObj = new URL(url)
    const path = urlObj.pathname
    if (path === '/' || path === '') return urlObj.hostname
    return path.split('/').filter(Boolean).pop() || urlObj.hostname
  } catch {
    return url
  }
}

// Methods
async function startWizard() {
  if (!wizardData.value.url) {
    errors.value.url = 'URL ist erforderlich'
    return
  }

  loading.value = true
  errors.value = { url: null, crawl: null, general: null }

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
    updateElapsedTime()
  })

  socket.value.on('crawler:page_crawled', (data) => {
    console.log('Page crawled:', data)
    if (data.url) {
      crawlProgress.value.recentPages.push(data.url)
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
    embeddingProgress.value = data.progress || 0
    if (data.documents_total) {
      collectionInfo.value = {
        ...collectionInfo.value,
        document_count: data.documents_total,
        total_chunks: data.chunks_completed || 0
      }
    }
  })

  socket.value.on('rag:collection_completed', (data) => {
    console.log('Embedding complete:', data)
    embeddingProgress.value = 100
    collectionInfo.value = {
      document_count: data.total_documents,
      total_chunks: data.total_chunks
    }
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

function updateElapsedTime() {
  if (crawlProgress.value.startTime) {
    crawlProgress.value.elapsedTime = (Date.now() - crawlProgress.value.startTime) / 1000
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
        collectionInfo.value = response.data.collection
        embeddingProgress.value = response.data.collection.embedding_progress || 0

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

// Navigation functions for clickable stepper
function canNavigateToStep(step) {
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

function navigateToStep(step) {
  if (!canNavigateToStep(step)) return

  // Handle navigation logic
  if (step === 4 && currentStep.value < 4) {
    // Skip to configuration
    currentStep.value = 4
  } else {
    currentStep.value = step
  }
}

function resetWizard() {
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
