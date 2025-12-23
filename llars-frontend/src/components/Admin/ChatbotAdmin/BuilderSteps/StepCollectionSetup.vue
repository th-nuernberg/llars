<template>
  <div class="step-container">
    <div class="step-content">
      <!-- Left Panel: Progress -->
      <div class="panel progress-panel">
        <div class="panel-header">
          <v-progress-circular
            v-if="isActiveProcess"
            :model-value="currentProgressPercent"
            :indeterminate="isIndeterminate"
            :size="40"
            :width="3"
            color="primary"
          >
            <span v-if="!isIndeterminate" class="text-caption">{{ currentProgressPercent }}%</span>
          </v-progress-circular>
          <v-icon v-else-if="isCompleted" size="40" color="success">mdi-check-circle</v-icon>
          <v-icon v-else-if="hasError" size="40" color="error">mdi-alert-circle</v-icon>
          <v-icon v-else size="40" color="grey">mdi-clock-outline</v-icon>

          <div class="header-text">
            <h3 class="text-subtitle-1 font-weight-medium">{{ statusTitle }}</h3>
            <p class="text-caption text-medium-emphasis mb-0">{{ statusDescription }}</p>
          </div>
        </div>

        <!-- Progress Bar -->
        <v-progress-linear
          :model-value="currentProgressPercent"
          :indeterminate="isIndeterminate"
          :color="progressColor"
          height="6"
          rounded
          class="mb-3"
        />

        <!-- Phase Tags -->
        <div v-if="isCrawling" class="phase-tags mb-3">
          <LTag :variant="phase1Done ? 'success' : (phase1Active ? 'primary' : 'gray')" size="sm">
            <v-icon start size="14">{{ phase1Done ? 'mdi-check' : 'mdi-map-search' }}</v-icon>
            Phase 1: Exploration
          </LTag>
          <LTag :variant="phase2Done ? 'success' : (phase2Active ? 'primary' : 'gray')" size="sm">
            <v-icon start size="14">{{ phase2Done ? 'mdi-check' : 'mdi-spider-web' }}</v-icon>
            Phase 2: Crawling
          </LTag>
        </div>

        <!-- Current URL -->
        <div v-if="crawlProgress.currentUrl && phase2Active" class="current-url mb-3">
          <div class="text-caption text-medium-emphasis d-flex align-center">
            <v-progress-circular indeterminate size="12" width="2" color="primary" class="mr-1" />
            Aktuelle Seite wird gecrawlt:
          </div>
          <div class="text-body-2 text-truncate">{{ crawlProgress.currentUrl }}</div>
          <v-progress-linear indeterminate height="2" rounded class="mt-1" />
        </div>

        <!-- Crawling Stats (only in crawling mode) -->
        <template v-if="isCrawling">
          <div class="stats-grid mb-3">
            <LTag variant="success" size="sm" prepend-icon="mdi-file-document">
              {{ totalDocuments }} Dokumente
            </LTag>
            <LTag v-if="crawlProgress.urlsTotal" variant="primary" size="sm" prepend-icon="mdi-link">
              {{ crawlProgress.urlsCompleted || 0 }}/{{ crawlProgress.urlsTotal }} URLs
            </LTag>
            <LTag v-if="crawlProgress.imagesExtracted" variant="secondary" size="sm" prepend-icon="mdi-image">
              {{ crawlProgress.imagesExtracted }} Bilder
            </LTag>
            <LTag v-if="crawlProgress.screenshotsTaken" variant="warning" size="sm" prepend-icon="mdi-camera">
              {{ crawlProgress.screenshotsTaken }} Screenshots
            </LTag>
            <LTag variant="info" size="sm" prepend-icon="mdi-clock">
              {{ formatDuration(crawlProgress.elapsedTime) }}
            </LTag>
          </div>

          <!-- Crawler Type -->
          <LTag
            v-if="crawlProgress.crawlerType"
            :variant="crawlProgress.crawlerType === 'Playwright' ? 'accent' : 'gray'"
            size="sm"
            :prepend-icon="crawlProgress.crawlerType === 'Playwright' ? 'mdi-web' : 'mdi-code-tags'"
            class="mb-3"
          >
            {{ crawlProgress.crawlerType }} Crawler
          </LTag>

          <!-- Recent Pages -->
          <div v-if="displayRecentPages.length > 0" class="recent-pages">
            <div class="text-caption text-medium-emphasis mb-1">Zuletzt gecrawlt:</div>
            <div class="pages-list">
              <div v-for="(page, index) in displayRecentPages" :key="index" class="page-item">
                <v-icon size="14" color="success" class="mr-1">mdi-check</v-icon>
                <span class="text-body-2 text-truncate">{{ extractPageTitle(page) }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Embedding Details (only in embedding mode) -->
        <template v-if="isEmbedding">
          <!-- Embedding Progress Info -->
          <div class="embedding-info mb-3">
            <div class="text-caption text-medium-emphasis mb-2">
              <v-icon size="14" class="mr-1">mdi-vector-polygon</v-icon>
              Dokumente werden in Vektoren umgewandelt...
            </div>
            <v-progress-linear
              :model-value="embeddingProgressPercent"
              :indeterminate="embeddingProgressPercent === 0 && buildStatus === 'embedding'"
              height="8"
              rounded
              color="primary"
              class="mb-2"
            />
          </div>

          <!-- Embedding Stats -->
          <div class="stats-grid mb-3">
            <LTag variant="info" size="sm" prepend-icon="mdi-file-document">
              {{ embeddingDocCount }} Dokumente
            </LTag>
            <LTag variant="success" size="sm" prepend-icon="mdi-vector-polygon">
              {{ embeddingChunkCount }} Chunks
            </LTag>
            <LTag variant="primary" size="sm" prepend-icon="mdi-percent">
              {{ embeddingProgressPercent }}%
            </LTag>
          </div>

          <!-- Collection Info -->
          <div v-if="collectionInfo" class="collection-info">
            <div class="text-caption text-medium-emphasis mb-1">Collection Details:</div>
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">Name:</span>
                <span class="info-value">{{ collectionInfo.name || collectionInfo.display_name }}</span>
              </div>
              <div v-if="collectionInfo.embedding_model" class="info-item">
                <span class="info-label">Embedding Modell:</span>
                <span class="info-value text-truncate">{{ collectionInfo.embedding_model }}</span>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Right Panel: Collection Preview -->
      <div class="panel collection-panel">
        <div class="panel-header">
          <v-icon size="24" color="primary" class="mr-2">mdi-folder-text-outline</v-icon>
          <span class="text-subtitle-1 font-weight-medium">Collection-Vorschau</span>
          <v-spacer />
          <v-btn
            icon
            variant="text"
            size="x-small"
            :loading="documentsLoading"
            @click="$emit('refresh-documents')"
          >
            <v-icon size="18">mdi-refresh</v-icon>
          </v-btn>
        </div>

        <div class="documents-list">
          <v-skeleton-loader
            v-if="documentsLoading && !collectionDocuments.length"
            type="list-item-two-line, list-item-two-line, list-item-two-line"
          />

          <div v-else-if="!collectionDocuments.length" class="empty-state">
            <v-icon size="32" color="grey-lighten-1">mdi-file-document-outline</v-icon>
            <div class="text-caption text-medium-emphasis">Warte auf Crawling...</div>
          </div>

          <template v-else>
            <div
              v-for="doc in collectionDocuments.slice(0, 10)"
              :key="doc.id"
              class="doc-item"
            >
              <v-avatar size="28" color="primary" variant="tonal" class="mr-2">
                <v-icon size="16">{{ getDocIcon(doc.mime_type) }}</v-icon>
              </v-avatar>
              <div class="doc-info">
                <div class="doc-title text-truncate">{{ doc.title || doc.filename }}</div>
                <div class="doc-meta text-truncate">{{ doc.mime_type || 'unbekannt' }} · {{ formatFileSize(doc.file_size_bytes) }}</div>
              </div>
              <LTag :variant="getStatusVariant(doc.status)" size="sm">
                {{ getStatusLabel(doc.status) }}
              </LTag>
            </div>

            <div v-if="collectionDocuments.length > 10" class="text-caption text-center text-medium-emphasis mt-2">
              + {{ collectionDocuments.length - 10 }} weitere Dokumente
            </div>
          </template>
        </div>

        <!-- Continue Action -->
        <div class="continue-action">
          <v-icon size="24" color="primary" class="mb-1">mdi-arrow-right-circle</v-icon>
          <div class="text-body-2 font-weight-medium">Weiter zur Konfiguration?</div>
          <LBtn
            variant="primary"
            size="small"
            prepend-icon="mdi-skip-forward"
            block
            class="mt-2"
            @click="$emit('skip-to-config')"
          >
            Zur Konfiguration
          </LBtn>
        </div>
      </div>
    </div>

    <!-- Error Alert -->
    <v-alert v-if="errorMessage" type="error" variant="tonal" class="error-alert">
      {{ errorMessage }}
    </v-alert>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  buildStatus: { type: String, default: 'crawling' },
  // Mode determines which UI to show, independent of buildStatus
  // 'crawling' = crawling-focused UI, 'embedding' = embedding-focused UI
  mode: { type: String, default: null },
  crawlProgress: {
    type: Object,
    default: () => ({
      stage: 'idle', pagesProcessed: 0, pagesTotal: 0, urlsTotal: 0, urlsCompleted: 0,
      documentsCreated: 0, documentsLinked: 0, imagesExtracted: 0, screenshotsTaken: 0,
      currentUrl: '', recentPages: [], elapsedTime: 0, crawlerType: 'basic', message: ''
    })
  },
  embeddingProgress: { type: [Number, Object], default: () => ({ progress: 0 }) },
  collectionInfo: { type: Object, default: null },
  collectionDocuments: { type: Array, default: () => [] },
  documentsLoading: { type: Boolean, default: false },
  errorMessage: { type: String, default: null }
})

defineEmits(['skip-to-config', 'pause', 'refresh-documents'])

// Display mode: if explicit mode is set, use it; otherwise derive from buildStatus
const displayMode = computed(() => props.mode || props.buildStatus)

// Status computeds - use displayMode to determine UI focus
const isCrawling = computed(() => displayMode.value === 'crawling')
const isEmbedding = computed(() => displayMode.value === 'embedding')
// These still use buildStatus for actual process state
const isActiveProcess = computed(() => ['crawling', 'embedding'].includes(props.buildStatus))
const isCompleted = computed(() => ['configuring', 'ready'].includes(props.buildStatus))
const hasError = computed(() => props.buildStatus === 'error')
const crawlStage = computed(() => props.crawlProgress.stage)

// Phase helpers
const phase1Active = computed(() => isCrawling.value && crawlStage.value === 'planning')
const phase1Done = computed(() => isCrawling.value && ['planning_done', 'crawling', 'completed'].includes(crawlStage.value))
const phase2Active = computed(() => isCrawling.value && ['planning_done', 'crawling'].includes(crawlStage.value))
const phase2Done = computed(() => isCrawling.value && crawlStage.value === 'completed')

const totalDocuments = computed(() => (props.crawlProgress.documentsCreated || 0) + (props.crawlProgress.documentsLinked || 0))

const embeddingProgressPercent = computed(() => {
  if (typeof props.embeddingProgress === 'number') return Math.min(100, Math.round(props.embeddingProgress))
  return Math.min(100, Math.round(props.embeddingProgress?.progress || 0))
})

const embeddingDocCount = computed(() => props.collectionInfo?.document_count || totalDocuments.value)
const embeddingChunkCount = computed(() => props.collectionInfo?.total_chunks || 0)

const currentProgressPercent = computed(() => {
  // Embedding mode - show embedding progress
  if (isEmbedding.value) {
    // If crawling is still running, show 0
    if (props.buildStatus === 'crawling') return 0
    return embeddingProgressPercent.value
  }
  // Crawling mode
  if (isCrawling.value) {
    const total = props.crawlProgress.urlsTotal || props.crawlProgress.pagesTotal
    if (total === 0) return 0
    const completed = props.crawlProgress.urlsCompleted || props.crawlProgress.pagesProcessed
    return Math.min(100, Math.round((completed / total) * 100))
  }
  return 100
})

const isIndeterminate = computed(() => {
  // Embedding mode - indeterminate if crawling or just starting
  if (isEmbedding.value) {
    return props.buildStatus === 'crawling' || embeddingProgressPercent.value === 0
  }
  // Crawling mode
  if (isCrawling.value) {
    return crawlStage.value === 'planning' || (props.crawlProgress.urlsTotal === 0 && props.crawlProgress.pagesTotal === 0)
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

  // Embedding mode - show embedding-specific titles
  if (isEmbedding.value) {
    if (props.buildStatus === 'crawling') return 'Warte auf Crawling...'
    if (embeddingProgressPercent.value >= 100) return 'Embedding abgeschlossen'
    if (embeddingProgressPercent.value > 0) return 'Embedding läuft...'
    return 'Embedding wird vorbereitet...'
  }

  // Crawling mode
  if (isCrawling.value) {
    const stage = props.crawlProgress.stage
    if (stage === 'planning') return 'Phase 1: URL-Erkundung...'
    if (['planning_done', 'crawling'].includes(stage)) return 'Phase 2: Inhalte erfassen...'
    if (stage === 'completed') return 'Crawling abgeschlossen'
    return 'Crawling läuft...'
  }

  if (isCompleted.value) return 'Verarbeitung abgeschlossen'
  return 'Warte auf Start...'
})

const statusDescription = computed(() => {
  if (hasError.value) return props.errorMessage || 'Ein Fehler ist aufgetreten'

  // Embedding mode - show embedding-specific descriptions
  if (isEmbedding.value) {
    if (props.buildStatus === 'crawling') {
      return 'Crawling muss zuerst abgeschlossen werden'
    }
    const processed = props.collectionInfo?.documents_processed || 0
    const total = embeddingDocCount.value
    const chunks = embeddingChunkCount.value
    if (embeddingProgressPercent.value >= 100) {
      return `${total} Dokumente → ${chunks} Chunks erstellt`
    }
    if (processed > 0 && total > 0) {
      return `${processed}/${total} Dokumente verarbeitet`
    }
    return `${embeddingProgressPercent.value}% - ${chunks} Chunks erstellt`
  }

  // Crawling mode
  if (props.crawlProgress.message) return props.crawlProgress.message
  if (isCrawling.value) {
    const total = props.crawlProgress.urlsTotal || props.crawlProgress.pagesTotal
    const completed = props.crawlProgress.urlsCompleted || props.crawlProgress.pagesProcessed
    if (total > 0) return `${completed}/${total} URLs, Crawling startet...`
    return `${totalDocuments.value} URLs gefunden`
  }

  if (isCompleted.value) return `${totalDocuments.value} Dokumente verarbeitet`
  return 'Bereit'
})

const displayRecentPages = computed(() => (props.crawlProgress.recentPages || []).slice(-5).reverse())

// Helpers
function formatDuration(seconds) {
  if (!seconds) return '0s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

function formatFileSize(bytes) {
  if (!bytes) return '0 KB'
  const kb = bytes / 1024
  if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`
  return `${kb.toFixed(0)} KB`
}

function extractPageTitle(url) {
  try {
    const urlObj = new URL(url)
    const path = urlObj.pathname
    if (path === '/' || path === '') return urlObj.hostname
    return path.split('/').filter(Boolean).pop() || urlObj.hostname
  } catch { return url }
}

function getDocIcon(mime) {
  if (!mime) return 'mdi-file'
  if (mime.startsWith('image/')) return 'mdi-file-image'
  if (mime === 'application/pdf') return 'mdi-file-pdf-box'
  if (mime.includes('word')) return 'mdi-file-word'
  if (mime.startsWith('text/')) return 'mdi-file-document-outline'
  return 'mdi-file'
}

function getStatusVariant(status) {
  const map = { completed: 'success', processing: 'info', pending: 'warning', failed: 'danger' }
  return map[status] || 'gray'
}

function getStatusLabel(status) {
  const map = { completed: 'Fertig', processing: 'Verarbeite...', pending: 'Wartend', failed: 'Fehler' }
  return map[status] || status || 'Unbekannt'
}
</script>

<style scoped>
.step-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.step-content {
  flex: 1;
  display: flex;
  gap: 16px;
  min-height: 0;
  overflow: hidden;
}

.panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: var(--llars-radius, 16px 4px 16px 4px);
  padding: 16px;
  min-width: 0;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-shrink: 0;
}

.header-text {
  flex: 1;
  min-width: 0;
}

.phase-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.current-url {
  padding: 8px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
}

.stats-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.recent-pages {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.pages-list {
  flex: 1;
  overflow-y: auto;
}

.page-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
}

/* Right panel */
.collection-panel {
  display: flex;
  flex-direction: column;
}

.documents-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  margin-bottom: 12px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  text-align: center;
}

.doc-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}

.doc-item:last-child {
  border-bottom: none;
}

.doc-info {
  flex: 1;
  min-width: 0;
  margin-right: 8px;
}

.doc-title {
  font-size: 13px;
  font-weight: 500;
}

.doc-meta {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.continue-action {
  flex-shrink: 0;
  text-align: center;
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
}

.error-alert {
  flex-shrink: 0;
  margin-top: 12px;
}

/* Embedding info section */
.embedding-info {
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
}

.collection-info {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.info-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
  min-width: 100px;
}

.info-value {
  font-weight: 500;
  flex: 1;
  min-width: 0;
}

/* Responsive */
@media (max-width: 960px) {
  .step-content {
    flex-direction: column;
  }

  .panel {
    max-height: 50%;
  }
}
</style>
