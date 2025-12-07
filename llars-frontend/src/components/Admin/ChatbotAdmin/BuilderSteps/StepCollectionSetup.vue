<template>
  <v-card flat class="pa-4">
    <v-row>
      <!-- Left side: Progress Section -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="pa-4 h-100">
          <div class="d-flex align-center mb-4">
            <v-progress-circular
              v-if="isActiveProcess"
              :model-value="currentProgressValue"
              :indeterminate="isIndeterminate"
              :size="48"
              :width="4"
              color="primary"
              class="mr-4"
            >
              <span v-if="!isIndeterminate" class="text-caption">{{ currentProgressValue }}%</span>
            </v-progress-circular>
            <v-icon v-else size="48" color="success" class="mr-4">mdi-check-circle</v-icon>
            <div>
              <h3 class="text-h6">{{ currentStatusTitle }}</h3>
              <p class="text-body-2 text-medium-emphasis mb-0">{{ currentStatusDescription }}</p>
            </div>
          </div>

          <!-- Progress Bar -->
          <v-progress-linear
            :model-value="currentProgressValue"
            :indeterminate="isIndeterminate"
            color="primary"
            height="8"
            rounded
            class="mb-4"
          />

          <!-- Crawling Details -->
          <template v-if="buildStatus === 'crawling'">
            <!-- Current URL -->
            <div v-if="crawlProgress.currentUrl" class="mb-3">
              <div class="text-caption text-medium-emphasis">Aktuelle Seite:</div>
              <div class="text-body-2 text-truncate">{{ crawlProgress.currentUrl }}</div>
            </div>

            <!-- Stats -->
            <div class="d-flex gap-3 flex-wrap mb-4">
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
            <div v-if="crawlProgress.recentPages.length > 0">
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
          </template>

          <!-- Embedding Details -->
          <template v-if="buildStatus === 'embedding'">
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
          </template>
        </v-card>
      </v-col>

      <!-- Right side: Continue hint -->
      <v-col cols="12" md="6">
        <v-card variant="outlined" class="pa-4 h-100 d-flex flex-column">
          <div class="text-center flex-grow-1 d-flex flex-column justify-center">
            <v-icon size="64" color="info" class="mb-4">mdi-arrow-right-circle</v-icon>
            <h3 class="text-h6 mb-2">Weiter zur Konfiguration?</h3>
            <p class="text-body-2 text-medium-emphasis">
              Sie können bereits mit der Chatbot-Konfiguration beginnen, während das {{ buildStatus === 'crawling' ? 'Crawling' : 'Embedding' }} im Hintergrund weiterläuft.
            </p>
          </div>
          <v-btn
            color="primary"
            size="large"
            block
            class="mt-4"
            @click="$emit('skip-to-config')"
          >
            <v-icon start>mdi-cog</v-icon>
            Jetzt konfigurieren
          </v-btn>
          <p v-if="buildStatus === 'crawling'" class="text-caption text-center text-medium-emphasis mt-2 mb-0">
            Der Chatbot kann erst nach Abschluss des Crawlings getestet werden.
          </p>
        </v-card>
      </v-col>
    </v-row>

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
      pagesProcessed: 0,
      pagesTotal: 0,
      documentsCreated: 0,
      documentsLinked: 0,
      currentUrl: '',
      recentPages: [],
      elapsedTime: 0
    })
  },
  embeddingProgress: {
    type: Number,
    default: 0
  },
  collectionInfo: {
    type: Object,
    default: null
  },
  errorMessage: {
    type: String,
    default: null
  }
})

defineEmits(['skip-to-config', 'pause'])

// Computed
const isActiveProcess = computed(() => {
  return ['crawling', 'embedding'].includes(props.buildStatus)
})

const currentProgressValue = computed(() => {
  if (props.buildStatus === 'crawling') {
    if (props.crawlProgress.pagesTotal === 0) return 0
    return Math.round((props.crawlProgress.pagesProcessed / props.crawlProgress.pagesTotal) * 100)
  } else if (props.buildStatus === 'embedding') {
    return props.embeddingProgress
  }
  return 100
})

const isIndeterminate = computed(() => {
  return props.buildStatus === 'crawling' && props.crawlProgress.pagesTotal === 0
})

const currentStatusTitle = computed(() => {
  if (props.buildStatus === 'crawling') {
    return isActiveProcess.value ? 'Crawling läuft...' : 'Crawling abgeschlossen'
  } else if (props.buildStatus === 'embedding') {
    return isActiveProcess.value ? 'Embedding läuft...' : 'Embedding abgeschlossen'
  }
  return 'Abgeschlossen'
})

const currentStatusDescription = computed(() => {
  if (props.buildStatus === 'crawling') {
    return `${props.crawlProgress.pagesProcessed} / ${props.crawlProgress.pagesTotal || '?'} Seiten`
  } else if (props.buildStatus === 'embedding') {
    return `Fortschritt: ${props.embeddingProgress}%`
  }
  return 'Alle Dokumente wurden erfolgreich verarbeitet.'
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
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}

.h-100 {
  height: 100%;
}
</style>
