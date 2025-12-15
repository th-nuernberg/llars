<template>
  <v-card flat class="pa-4 h-100 d-flex flex-column">
    <v-row class="flex-grow-1 align-stretch">
      <!-- Left side: Progress Section -->
      <v-col cols="12" md="6" class="d-flex">
        <v-card variant="outlined" class="pa-4 flex-grow-1 d-flex flex-column">
          <!-- Status Header -->
          <div class="d-flex align-center mb-4">
            <v-progress-circular
              v-if="isActiveProcess"
              :model-value="currentProgressPercent"
              :indeterminate="isIndeterminate"
              :size="48"
              :width="4"
              color="primary"
              class="mr-4"
            >
              <span v-if="!isIndeterminate" class="text-caption">{{ currentProgressPercent }}%</span>
            </v-progress-circular>
            <v-icon v-else-if="isCompleted" size="48" color="success" class="mr-4">mdi-check-circle</v-icon>
            <v-icon v-else-if="hasError" size="48" color="error" class="mr-4">mdi-alert-circle</v-icon>
            <v-icon v-else size="48" color="grey" class="mr-4">mdi-clock-outline</v-icon>

            <div>
              <h3 class="text-h6">{{ statusTitle }}</h3>
              <p class="text-body-2 text-medium-emphasis mb-0">{{ statusDescription }}</p>
            </div>
          </div>

          <!-- Progress Bar -->
          <v-progress-linear
            :model-value="currentProgressPercent"
            :indeterminate="isIndeterminate"
            :color="progressColor"
            height="8"
            rounded
            class="mb-4"
          />

          <!-- Crawling Phase Details -->
          <template v-if="isCrawling">
            <!-- Phase Chips -->
            <div class="d-flex flex-wrap gap-2 mb-4">
              <v-chip
                size="small"
                :color="phase1Done ? 'success' : (phase1Active ? 'primary' : 'grey')"
                variant="tonal"
              >
                <v-icon start size="small">{{ phase1Done ? 'mdi-check' : 'mdi-map-search' }}</v-icon>
                Phase 1: Exploration
              </v-chip>
              <v-chip
                size="small"
                :color="phase2Done ? 'success' : (phase2Active ? 'primary' : 'grey')"
                variant="tonal"
              >
                <v-icon start size="small">{{ phase2Done ? 'mdi-check' : 'mdi-spider-web' }}</v-icon>
                Phase 2: Crawling
              </v-chip>
            </div>

            <!-- Current URL -->
            <div v-if="crawlProgress.currentUrl" class="mb-3">
              <div class="text-caption text-medium-emphasis d-flex align-center">
                <v-progress-circular
                  v-if="phase2Active"
                  indeterminate
                  size="14"
                  width="2"
                  color="primary"
                  class="mr-2"
                />
                Aktuelle Seite wird gecrawlt:
              </div>
              <div class="text-body-2 text-truncate">{{ crawlProgress.currentUrl }}</div>
              <v-progress-linear
                v-if="phase2Active"
                indeterminate
                height="3"
                rounded
                class="mt-2"
              />
            </div>

            <!-- Crawl Stats -->
            <div class="d-flex gap-2 flex-wrap mb-4">
              <v-chip size="small" color="success" variant="tonal">
                <v-icon start size="small">mdi-file-document</v-icon>
                {{ totalDocuments }} Dokumente
              </v-chip>
              <v-chip v-if="crawlProgress.urlsTotal" size="small" color="primary" variant="tonal">
                <v-icon start size="small">mdi-target-variant</v-icon>
                {{ crawlProgress.urlsCompleted || 0 }}/{{ crawlProgress.urlsTotal }} URLs
              </v-chip>
              <v-chip v-if="crawlProgress.imagesExtracted" size="small" color="deep-purple" variant="tonal">
                <v-icon start size="small">mdi-image</v-icon>
                {{ crawlProgress.imagesExtracted }} Bilder
              </v-chip>
              <v-chip v-if="crawlProgress.screenshotsTaken" size="small" color="orange" variant="tonal">
                <v-icon start size="small">mdi-camera</v-icon>
                {{ crawlProgress.screenshotsTaken }} Screenshots
              </v-chip>
              <v-chip size="small" color="info" variant="tonal">
                <v-icon start size="small">mdi-clock</v-icon>
                {{ formatDuration(crawlProgress.elapsedTime) }}
              </v-chip>
            </div>

            <!-- Crawler Type Badge -->
            <v-chip
              v-if="crawlProgress.crawlerType"
              size="small"
              :color="crawlProgress.crawlerType === 'Playwright' ? 'purple' : 'grey'"
              variant="tonal"
              class="mb-3"
            >
              <v-icon start size="small">
                {{ crawlProgress.crawlerType === 'Playwright' ? 'mdi-web' : 'mdi-code-tags' }}
              </v-icon>
              {{ crawlProgress.crawlerType }} Crawler
            </v-chip>

            <!-- Recent Pages -->
            <div v-if="crawlProgress.recentPages && crawlProgress.recentPages.length > 0">
              <div class="text-caption text-medium-emphasis mb-2">Zuletzt gecrawlt:</div>
              <v-list density="compact" class="bg-transparent flex-grow-1" style="overflow-y: auto">
                <v-list-item
                  v-for="(page, index) in displayRecentPages"
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
          </template>

          <!-- Embedding Phase Details -->
          <template v-if="isEmbedding">
            <div class="d-flex gap-2 flex-wrap">
              <v-chip size="small" color="info" variant="tonal">
                <v-icon start size="small">mdi-file-document</v-icon>
                {{ embeddingDocCount }} Dokumente
              </v-chip>
              <v-chip size="small" color="success" variant="tonal">
                <v-icon start size="small">mdi-vector-polygon</v-icon>
                {{ embeddingChunkCount }} Chunks
              </v-chip>
              <v-chip size="small" color="primary" variant="tonal">
                <v-icon start size="small">mdi-percent</v-icon>
                {{ embeddingProgressPercent }}%
              </v-chip>
            </div>

            <div v-if="embeddingProgress.documentsProcessed" class="mt-3 text-body-2 text-medium-emphasis">
              Verarbeitet: {{ embeddingProgress.documentsProcessed }} / {{ embeddingProgress.documentsTotal || '?' }} Dokumente
            </div>

            <div v-if="embeddingProgress.currentDocument" class="mt-3">
              <div class="text-caption text-medium-emphasis d-flex align-center">
                <v-progress-circular
                  indeterminate
                  size="14"
                  width="2"
                  color="primary"
                  class="mr-2"
                />
                Aktuelles Dokument:
              </div>
              <div class="text-body-2 text-truncate">{{ embeddingProgress.currentDocument }}</div>
            </div>
          </template>

          <!-- Stage Indicator -->
          <v-divider v-if="crawlProgress.stage && isCrawling" class="my-4" />
          <div v-if="crawlProgress.stage && isCrawling" class="d-flex align-center">
            <v-icon
              size="small"
              :color="getStageColor(crawlProgress.stage)"
              class="mr-2"
            >
              {{ getStageIcon(crawlProgress.stage) }}
            </v-icon>
            <span class="text-body-2">{{ getStageLabel(crawlProgress.stage) }}</span>
          </div>
        </v-card>
      </v-col>

      <!-- Right side: Document Preview & Actions -->
      <v-col cols="12" md="6" class="d-flex flex-column">
        <!-- Collection Preview -->
        <v-card variant="outlined" class="pa-4 mb-4 flex-grow-1 d-flex flex-column">
          <div class="d-flex align-center mb-3">
            <v-icon size="32" color="primary" class="mr-2">mdi-folder-text-outline</v-icon>
            <div class="text-h6">Collection-Vorschau</div>
            <v-spacer />
            <v-btn
              icon
              variant="text"
              size="small"
              :loading="documentsLoading"
              :disabled="!collectionDocuments.length && !documentsLoading"
              @click="$emit('refresh-documents')"
            >
              <v-icon>mdi-refresh</v-icon>
              <v-tooltip activator="parent" location="top">Aktualisieren</v-tooltip>
            </v-btn>
          </div>

          <v-skeleton-loader
            v-if="documentsLoading && !collectionDocuments.length"
            type="list-item-two-line, list-item-two-line, list-item-two-line"
            class="mb-2"
          />

          <div v-else-if="!collectionDocuments.length" class="text-medium-emphasis text-center py-6">
            <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-file-document-outline</v-icon>
            <div>Noch keine Dokumente geladen.</div>
            <div class="text-caption">Warte auf Crawling...</div>
          </div>

          <v-list
            v-else
            density="comfortable"
            class="bg-transparent flex-grow-1"
            style="overflow-y: auto"
          >
            <v-list-item
              v-for="doc in collectionDocuments.slice(0, 10)"
              :key="doc.id"
              density="comfortable"
              class="px-0"
            >
              <template #prepend>
                <v-avatar size="32" color="primary" class="mr-2" variant="tonal">
                  <v-icon size="18">{{ getDocIcon(doc.mime_type) }}</v-icon>
                </v-avatar>
              </template>
              <v-list-item-title class="text-body-2 text-truncate">
                {{ doc.title || doc.filename }}
              </v-list-item-title>
              <v-list-item-subtitle class="text-caption text-medium-emphasis">
                {{ doc.mime_type || 'unbekannt' }} · {{ formatFileSize(doc.file_size_bytes) }}
              </v-list-item-subtitle>
              <template #append>
                <v-chip size="x-small" :color="getStatusColor(doc.status)" variant="tonal">
                  {{ getStatusLabel(doc.status) }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>

          <div v-if="collectionDocuments.length > 10" class="text-caption text-center text-medium-emphasis mt-2">
            + {{ collectionDocuments.length - 10 }} weitere Dokumente
          </div>
        </v-card>

        <!-- Continue Hint -->
        <v-card variant="outlined" class="pa-4">
          <div class="text-center">
            <v-icon size="48" color="info" class="mb-3">mdi-arrow-right-circle</v-icon>
            <h3 class="text-h6 mb-2">Weiter zur Konfiguration?</h3>
            <p class="text-body-2 text-medium-emphasis mb-4">
              Sie können bereits mit der Chatbot-Konfiguration beginnen,
              während das {{ isCrawling ? 'Crawling' : 'Embedding' }} im Hintergrund weiterläuft.
            </p>
            <v-btn
              color="primary"
              variant="tonal"
              block
              @click="$emit('skip-to-config')"
            >
              <v-icon start>mdi-cog</v-icon>
              Jetzt konfigurieren
            </v-btn>
            <p v-if="isCrawling" class="text-caption text-center text-medium-emphasis mt-2 mb-0">
              Der Chatbot kann erst nach Abschluss des Embeddings getestet werden.
            </p>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mt-4"
    >
      {{ errorMessage }}
    </v-alert>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  buildStatus: {
    type: String,
    default: 'crawling'
  },
  crawlProgress: {
    type: Object,
    default: () => ({
      stage: 'idle',
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
      crawlerType: 'basic',
      message: ''
    })
  },
  embeddingProgress: {
    type: [Number, Object],
    default: () => ({ progress: 0 })
  },
  collectionInfo: {
    type: Object,
    default: null
  },
  collectionDocuments: {
    type: Array,
    default: () => []
  },
  documentsLoading: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: null
  }
})

defineEmits(['skip-to-config', 'pause', 'refresh-documents'])

// Computed Status
const isCrawling = computed(() => props.buildStatus === 'crawling')
const isEmbedding = computed(() => props.buildStatus === 'embedding')
const isActiveProcess = computed(() => ['crawling', 'embedding'].includes(props.buildStatus))
const isCompleted = computed(() => ['configuring', 'ready'].includes(props.buildStatus))
const hasError = computed(() => props.buildStatus === 'error')

const crawlStage = computed(() => props.crawlProgress.stage)

// Phase helpers (Crawling step)
const phase1Active = computed(() => isCrawling.value && crawlStage.value === 'planning')
const phase1Done = computed(() => isCrawling.value && ['planning_done', 'crawling', 'completed'].includes(crawlStage.value))
const phase2Active = computed(() => isCrawling.value && ['planning_done', 'crawling'].includes(crawlStage.value))
const phase2Done = computed(() => isCrawling.value && crawlStage.value === 'completed')

const totalDocuments = computed(() => {
  return (props.crawlProgress.documentsCreated || 0) + (props.crawlProgress.documentsLinked || 0)
})

const embeddingProgressPercent = computed(() => {
  if (typeof props.embeddingProgress === 'number') {
    return Math.min(100, Math.round(props.embeddingProgress))
  }
  return Math.min(100, Math.round(props.embeddingProgress?.progress || 0))
})

const embeddingDocCount = computed(() => {
  if (props.collectionInfo?.document_count) {
    return props.collectionInfo.document_count
  }
  if (typeof props.embeddingProgress === 'object') {
    return props.embeddingProgress.documentsTotal || totalDocuments.value
  }
  return totalDocuments.value
})

const embeddingChunkCount = computed(() => {
  if (props.collectionInfo?.total_chunks) {
    return props.collectionInfo.total_chunks
  }
  if (typeof props.embeddingProgress === 'object') {
    return props.embeddingProgress.chunksProcessed || 0
  }
  return 0
})

const currentProgressPercent = computed(() => {
  if (isCrawling.value) {
    const total = props.crawlProgress.urlsTotal || props.crawlProgress.pagesTotal
    if (total === 0) return 0
    const completed = props.crawlProgress.urlsCompleted || props.crawlProgress.pagesProcessed
    return Math.min(100, Math.round((completed / total) * 100))
  } else if (isEmbedding.value) {
    return embeddingProgressPercent.value
  }
  return 100
})

const isIndeterminate = computed(() => {
  if (isCrawling.value) {
    const stage = props.crawlProgress.stage
    return stage === 'planning' || (props.crawlProgress.urlsTotal === 0 && props.crawlProgress.pagesTotal === 0)
  }
  return false
})

const progressColor = computed(() => {
  if (hasError.value) return 'error'
  if (isCompleted.value) return 'success'
  return 'primary'
})

const statusTitle = computed(() => {
  if (hasError.value) return 'Fehler aufgetreten'

  if (isCrawling.value) {
    const stage = props.crawlProgress.stage
    if (stage === 'planning') return 'Phase 1: URL-Erkundung läuft...'
    if (stage === 'planning_done') return 'Phase 2: Inhalte erfassen...'
    if (stage === 'crawling') return 'Phase 2: Inhalte erfassen...'
    if (stage === 'completed') return 'Crawling abgeschlossen'
    return 'Crawling läuft...'
  }

  if (isEmbedding.value) return 'Embedding läuft...'
  if (isCompleted.value) return 'Verarbeitung abgeschlossen'

  return 'Warte auf Start...'
})

const statusDescription = computed(() => {
  if (hasError.value) return props.errorMessage || 'Ein Fehler ist aufgetreten'

  if (isCrawling.value) {
    const stage = props.crawlProgress.stage

    // Use custom message if available
    if (props.crawlProgress.message) {
      return props.crawlProgress.message
    }

    if (stage === 'planning') {
      const count = props.crawlProgress.urlsTotal || 0
      if (count > 0) {
        return `${count} URLs gefunden, suche weiter...`
      }
      return 'Erkunde verfügbare URLs...'
    }
    if (stage === 'planning_done') {
      const total = props.crawlProgress.urlsTotal || 0
      return `${total} URLs gefunden, starte Inhaltserfassung...`
    }

    // Regular crawling stage
    const total = props.crawlProgress.urlsTotal || props.crawlProgress.pagesTotal
    const completed = props.crawlProgress.urlsCompleted || props.crawlProgress.pagesProcessed
    if (total > 0) {
      return `${completed} / ${total} Seiten verarbeitet`
    }
    return 'Crawling läuft...'
  }

  if (isEmbedding.value) {
    return `Fortschritt: ${embeddingProgressPercent.value}%`
  }

  if (isCompleted.value) {
    return `${totalDocuments.value} Dokumente erfolgreich verarbeitet`
  }

  return 'Bereit zum Starten'
})

const displayRecentPages = computed(() => {
  const pages = props.crawlProgress.recentPages || []
  return pages.slice(-5).reverse()
})

// Helper Functions
function formatDuration(seconds) {
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

function formatFileSize(bytes) {
  if (!bytes) return '0 KB'
  const mb = bytes / (1024 * 1024)
  if (mb >= 1) return `${mb.toFixed(1)} MB`
  const kb = bytes / 1024
  return `${kb.toFixed(0)} KB`
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

function getDocIcon(mime) {
  if (!mime) return 'mdi-file'
  if (mime.startsWith('image/')) return 'mdi-file-image'
  if (mime === 'application/pdf') return 'mdi-file-pdf-box'
  if (mime.includes('word')) return 'mdi-file-word'
  if (mime.includes('excel') || mime.includes('spreadsheet')) return 'mdi-file-excel'
  if (mime.includes('powerpoint')) return 'mdi-file-powerpoint'
  if (mime.startsWith('text/')) return 'mdi-file-document-outline'
  return 'mdi-file'
}

function getStatusColor(status) {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'info'
    case 'pending': return 'warning'
    case 'failed': return 'error'
    default: return 'grey'
  }
}

function getStatusLabel(status) {
  switch (status) {
    case 'completed': return 'Fertig'
    case 'processing': return 'Verarbeite...'
    case 'pending': return 'Wartend'
    case 'failed': return 'Fehler'
    default: return status || 'Unbekannt'
  }
}

function getStageIcon(stage) {
  switch (stage) {
    case 'planning': return 'mdi-map-search'
    case 'planning_done': return 'mdi-spider-web'  // Show crawling icon as transition
    case 'crawling': return 'mdi-spider-web'
    case 'completed': return 'mdi-check-circle'
    default: return 'mdi-clock-outline'
  }
}

function getStageColor(stage) {
  switch (stage) {
    case 'planning': return 'warning'
    case 'planning_done': return 'primary'  // Same as crawling - transition state
    case 'crawling': return 'primary'
    case 'completed': return 'success'
    default: return 'grey'
  }
}

function getStageLabel(stage) {
  switch (stage) {
    case 'planning': return 'Phase 1: URL-Erkundung'
    case 'planning_done': return 'Phase 2: Inhalte erfassen'  // Don't show "abgeschlossen", transition to Phase 2
    case 'crawling': return 'Phase 2: Inhalte erfassen'
    case 'completed': return 'Crawling abgeschlossen'
    default: return 'Initialisierung...'
  }
}
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}

.h-100 {
  height: 100%;
}
</style>
