<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="1100"
    scrollable
  >
    <v-card v-if="document">
      <v-card-title class="d-flex align-center pa-4">
        <v-icon :icon="getFileIcon(document.file_type)" :color="getFileColor(document.file_type)" class="mr-2"></v-icon>
        {{ document.filename }}
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        ></v-btn>
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-0" style="height: 650px;">
        <v-tabs v-model="activeTab" bg-color="surface-variant">
          <v-tab value="info">
            <v-icon icon="mdi-information" class="mr-2"></v-icon>
            Info
          </v-tab>
          <v-tab v-if="documentDetails?.has_screenshot" value="screenshot">
            <v-icon icon="mdi-image" class="mr-2"></v-icon>
            Screenshot
          </v-tab>
          <v-tab value="content">
            <v-icon icon="mdi-text" class="mr-2"></v-icon>
            Inhalt
          </v-tab>
          <v-tab value="chunks">
            <v-icon icon="mdi-puzzle" class="mr-2"></v-icon>
            Chunks ({{ document.chunk_count || 0 }})
          </v-tab>
        </v-tabs>

        <v-window v-model="activeTab">
          <!-- Info Tab -->
          <v-window-item value="info">
            <v-container class="pa-4">
              <v-row>
                <v-col cols="12" md="6">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Dateiinformationen</div>
                    <v-list density="compact" class="bg-transparent">
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Dateiname</v-list-item-title>
                        <v-list-item-subtitle>{{ document.filename }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Typ</v-list-item-title>
                        <v-list-item-subtitle>{{ document.file_type?.toUpperCase() }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Größe</v-list-item-title>
                        <v-list-item-subtitle>{{ formatSize(document.file_size) }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">MD5 Hash</v-list-item-title>
                        <v-list-item-subtitle class="text-caption">{{ document.md5_hash || '-' }}</v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-col>

                <v-col cols="12" md="6">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Collection</div>
                    <v-list density="compact" class="bg-transparent">
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Name</v-list-item-title>
                        <v-list-item-subtitle>
                          <v-chip size="small" :color="getCollectionColor()">
                            {{ document.collection_name }}
                          </v-chip>
                        </v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-col>

                <!-- Source URL section if available -->
                <v-col cols="12" v-if="documentDetails?.source_url">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Quelle</div>
                    <v-card variant="outlined">
                      <v-card-text class="pa-3">
                        <div class="d-flex align-center">
                          <v-icon size="small" color="info" class="mr-2">mdi-web</v-icon>
                          <a
                            :href="documentDetails.source_url"
                            target="_blank"
                            class="text-truncate source-url-link"
                          >
                            {{ documentDetails.source_url }}
                          </a>
                          <v-spacer></v-spacer>
                          <v-btn
                            size="small"
                            icon="mdi-open-in-new"
                            variant="text"
                            :href="documentDetails.source_url"
                            target="_blank"
                          ></v-btn>
                        </div>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-col>

                <v-col cols="12" md="6">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Verarbeitungsstatus</div>
                    <v-list density="compact" class="bg-transparent">
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Status</v-list-item-title>
                        <v-list-item-subtitle>
                          <v-chip size="small" :color="getStatusColor(document.status)">
                            {{ getStatusText(document.status) }}
                          </v-chip>
                        </v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Chunks</v-list-item-title>
                        <v-list-item-subtitle>{{ document.chunk_count || 0 }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item v-if="document.error_message">
                        <v-list-item-title class="text-medium-emphasis">Fehler</v-list-item-title>
                        <v-list-item-subtitle class="text-error">{{ document.error_message }}</v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-col>

                <v-col cols="12" md="6">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Statistiken</div>
                    <v-list density="compact" class="bg-transparent">
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Abrufe</v-list-item-title>
                        <v-list-item-subtitle>{{ document.retrieval_count || 0 }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Hochgeladen</v-list-item-title>
                        <v-list-item-subtitle>{{ formatDate(document.uploaded_at) }}</v-list-item-subtitle>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-title class="text-medium-emphasis">Zuletzt indexiert</v-list-item-title>
                        <v-list-item-subtitle>{{ formatDate(document.indexed_at) }}</v-list-item-subtitle>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-col>

                <v-col cols="12" v-if="document.metadata">
                  <div class="info-section">
                    <div class="text-subtitle-2 text-medium-emphasis mb-2">Metadaten</div>
                    <v-card variant="outlined">
                      <v-card-text>
                        <pre class="text-caption">{{ JSON.stringify(document.metadata, null, 2) }}</pre>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-col>
              </v-row>
            </v-container>
          </v-window-item>

          <!-- Screenshot Tab -->
          <v-window-item value="screenshot">
            <div class="pa-4">
              <v-skeleton-loader
                v-if="loadingScreenshot"
                type="image"
                height="400"
              ></v-skeleton-loader>

              <div v-else class="screenshot-container">
                <!-- Source URL Info -->
                <v-alert
                  v-if="documentDetails?.source_url"
                  type="info"
                  variant="tonal"
                  density="compact"
                  class="mb-3"
                >
                  <div class="d-flex align-center">
                    <v-icon size="small" class="mr-2">mdi-web</v-icon>
                    <span class="text-caption text-truncate">{{ documentDetails.source_url }}</span>
                    <v-spacer></v-spacer>
                    <v-btn
                      size="x-small"
                      variant="text"
                      :href="documentDetails.source_url"
                      target="_blank"
                    >
                      <v-icon size="small">mdi-open-in-new</v-icon>
                    </v-btn>
                  </div>
                </v-alert>

                <!-- Screenshot Image -->
                <v-card variant="outlined" class="overflow-hidden">
                  <v-img
                    v-if="screenshotUrl"
                    :src="screenshotUrl"
                    max-height="500"
                    contain
                    class="screenshot-image"
                    @click="showFullScreenshot = true"
                  >
                    <template #placeholder>
                      <div class="d-flex align-center justify-center fill-height">
                        <v-progress-circular indeterminate color="primary"></v-progress-circular>
                      </div>
                    </template>
                  </v-img>
                  <div v-else class="text-center pa-8 text-medium-emphasis">
                    <v-icon size="48" class="mb-2">mdi-image-off</v-icon>
                    <div>Screenshot nicht verfügbar</div>
                  </div>
                </v-card>

                <div class="text-caption text-medium-emphasis mt-2 text-center">
                  Klicken zum Vergrößern
                </div>
              </div>
            </div>
          </v-window-item>

          <!-- Content Tab -->
          <v-window-item value="content">
            <div class="pa-4">
              <v-skeleton-loader
                v-if="loadingContent"
                type="paragraph@4"
              ></v-skeleton-loader>

              <v-card v-else variant="outlined">
                <v-card-text>
                  <div v-if="content" class="content-text">
                    {{ content }}
                  </div>
                  <div v-else class="text-center text-medium-emphasis pa-8">
                    <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
                    <div>Kein Inhalt verfügbar</div>
                  </div>
                </v-card-text>
              </v-card>
            </div>
          </v-window-item>

          <!-- Chunks Tab -->
          <v-window-item value="chunks">
            <div class="pa-4">
              <v-skeleton-loader
                v-if="loadingChunks"
                type="list-item@5"
              ></v-skeleton-loader>

              <div v-else>
                <v-expansion-panels v-if="chunks && chunks.length > 0" variant="accordion">
                  <v-expansion-panel
                    v-for="(chunk, index) in chunks"
                    :key="index"
                  >
                    <v-expansion-panel-title>
                      <div class="d-flex align-center">
                        <v-chip size="small" class="mr-2">{{ index + 1 }}</v-chip>
                        <v-icon v-if="chunk.has_image" size="small" color="info" class="mr-1">mdi-image</v-icon>
                        <span class="text-truncate">{{ chunk.text ? chunk.text.substring(0, 100) + '...' : '[Bild]' }}</span>
                      </div>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <!-- Chunk Image if available -->
                      <div v-if="chunk.has_image" class="mb-3">
                        <v-card variant="outlined" class="overflow-hidden">
                          <v-img
                            :src="getChunkImageUrl(chunk)"
                            max-height="300"
                            contain
                            class="chunk-image"
                          >
                            <template #placeholder>
                              <div class="d-flex align-center justify-center fill-height">
                                <v-progress-circular indeterminate color="primary" size="24"></v-progress-circular>
                              </div>
                            </template>
                            <template #error>
                              <div class="d-flex align-center justify-center fill-height text-medium-emphasis">
                                <v-icon class="mr-1">mdi-image-broken</v-icon>
                                Bild konnte nicht geladen werden
                              </div>
                            </template>
                          </v-img>
                        </v-card>
                        <div v-if="chunk.image_alt_text" class="text-caption text-medium-emphasis mt-1">
                          Alt: {{ chunk.image_alt_text }}
                        </div>
                      </div>

                      <!-- Chunk Text -->
                      <div v-if="chunk.text" class="chunk-text">{{ chunk.text }}</div>

                      <v-divider class="my-2"></v-divider>
                      <div class="text-caption text-medium-emphasis d-flex flex-wrap ga-2">
                        <span>Chunk ID: {{ chunk.id }}</span>
                        <span v-if="chunk.text">| Zeichen: {{ chunk.text.length }}</span>
                        <span v-if="chunk.has_image">| Hat Bild</span>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <v-card v-else variant="outlined">
                  <v-card-text class="text-center pa-8">
                    <v-icon size="48" class="mb-2 text-medium-emphasis">mdi-puzzle-outline</v-icon>
                    <div class="text-medium-emphasis">Keine Chunks vorhanden</div>
                  </v-card-text>
                </v-card>
              </div>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-btn
          prepend-icon="mdi-download"
          variant="text"
          @click="handleDownload"
        >
          Download
        </v-btn>
        <v-btn
          prepend-icon="mdi-refresh"
          variant="text"
          color="info"
          @click="handleReindex"
        >
          Neu indexieren
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          prepend-icon="mdi-delete"
          variant="text"
          color="error"
          @click="handleDelete"
        >
          Löschen
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Fullscreen Screenshot Dialog -->
  <v-dialog
    v-model="showFullScreenshot"
    fullscreen
    transition="dialog-bottom-transition"
  >
    <v-card class="d-flex flex-column" style="background: rgba(0,0,0,0.95);">
      <v-toolbar color="transparent" class="flex-grow-0">
        <v-toolbar-title class="text-white">{{ document?.filename }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-close"
          variant="text"
          color="white"
          @click="showFullScreenshot = false"
        ></v-btn>
      </v-toolbar>
      <div class="flex-grow-1 d-flex align-center justify-center pa-4">
        <v-img
          v-if="screenshotUrl"
          :src="screenshotUrl"
          contain
          max-height="90vh"
          class="fullscreen-screenshot"
        ></v-img>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  document: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'download', 'reindex', 'delete'])

const activeTab = ref('info')
const content = ref('')
const chunks = ref([])
const loadingContent = ref(false)
const loadingChunks = ref(false)

// Screenshot state
const documentDetails = ref(null)
const screenshotUrl = ref(null)
const loadingScreenshot = ref(false)
const showFullScreenshot = ref(false)

// Chunk image state
const loadingChunkImage = ref({})
const chunkImageUrls = ref({})

const getFileIcon = (fileType) => {
  const iconMap = {
    'pdf': 'mdi-file-pdf-box',
    'txt': 'mdi-file-document',
    'md': 'mdi-language-markdown',
    'markdown': 'mdi-language-markdown'
  }
  return iconMap[fileType?.toLowerCase()] || 'mdi-file'
}

const getFileColor = (fileType) => {
  const colorMap = {
    'pdf': 'red',
    'txt': 'blue',
    'md': 'green',
    'markdown': 'green'
  }
  return colorMap[fileType?.toLowerCase()] || 'grey'
}

const getCollectionColor = () => {
  return '#1976D2'
}

const getStatusColor = (status) => {
  const colorMap = {
    'pending': 'warning',
    'processing': 'info',
    'indexed': 'success',
    'failed': 'error'
  }
  return colorMap[status] || 'grey'
}

const getStatusText = (status) => {
  const textMap = {
    'pending': 'Ausstehend',
    'processing': 'Verarbeitung',
    'indexed': 'Indexiert',
    'failed': 'Fehler'
  }
  return textMap[status] || status
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadContent = async () => {
  if (!props.document?.id) return

  loadingContent.value = true
  try {
    const response = await axios.get(`/api/rag/documents/${props.document.id}/content`)
    content.value = response.data.content || ''
  } catch (error) {
    console.error('Error loading content:', error)
    content.value = 'Fehler beim Laden des Inhalts'
  } finally {
    loadingContent.value = false
  }
}

const loadChunks = async () => {
  if (!props.document?.id) return

  loadingChunks.value = true
  try {
    const response = await axios.get(`/api/rag/documents/${props.document.id}/chunks`)
    chunks.value = response.data.chunks || []
    // Reset chunk image urls
    chunkImageUrls.value = {}
  } catch (error) {
    console.error('Error loading chunks:', error)
    chunks.value = []
  } finally {
    loadingChunks.value = false
  }
}

const loadDocumentDetails = async () => {
  if (!props.document?.id) return

  try {
    const response = await axios.get(`/api/rag/documents/${props.document.id}`)
    documentDetails.value = response.data.document || null

    // Build screenshot URL if available
    if (documentDetails.value?.has_screenshot) {
      screenshotUrl.value = `/api/rag/documents/${props.document.id}/screenshot`
    } else {
      screenshotUrl.value = null
    }
  } catch (error) {
    console.error('Error loading document details:', error)
    documentDetails.value = null
    screenshotUrl.value = null
  }
}

const loadScreenshot = async () => {
  if (!props.document?.id || !documentDetails.value?.has_screenshot) return

  loadingScreenshot.value = true
  try {
    // Screenshot URL is already set in loadDocumentDetails
    // This function just manages the loading state
    screenshotUrl.value = `/api/rag/documents/${props.document.id}/screenshot`
  } finally {
    loadingScreenshot.value = false
  }
}

const getChunkImageUrl = (chunk) => {
  if (!chunk.has_image) return null
  return `/api/rag/chunks/${chunk.id}/image`
}

watch(activeTab, (newTab) => {
  if (newTab === 'content' && !content.value && !loadingContent.value) {
    loadContent()
  } else if (newTab === 'chunks' && chunks.value.length === 0 && !loadingChunks.value) {
    loadChunks()
  } else if (newTab === 'screenshot' && !screenshotUrl.value && !loadingScreenshot.value) {
    loadScreenshot()
  }
})

watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    activeTab.value = 'info'
    content.value = ''
    chunks.value = []
    // Reset screenshot state
    documentDetails.value = null
    screenshotUrl.value = null
    loadingScreenshot.value = false
    showFullScreenshot.value = false
    chunkImageUrls.value = {}
    // Load document details (including screenshot info)
    loadDocumentDetails()
  }
})

const handleDownload = () => {
  emit('download', props.document)
}

const handleReindex = () => {
  emit('reindex', props.document)
}

const handleDelete = () => {
  emit('delete', props.document)
}
</script>

<style scoped>
.info-section {
  height: 100%;
}

.content-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
}

.chunk-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-size: 0.875rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
}

.v-list-item-title {
  font-size: 0.75rem;
  font-weight: 500;
}

.v-list-item-subtitle {
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface)) !important;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  color: rgb(var(--v-theme-on-surface));
}

.screenshot-container {
  max-width: 100%;
}

.screenshot-image {
  cursor: pointer;
  transition: opacity 0.2s;
}

.screenshot-image:hover {
  opacity: 0.9;
}

.fullscreen-screenshot {
  max-width: 95vw;
}

.chunk-image {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.source-url-link {
  color: rgb(var(--v-theme-info));
  text-decoration: none;
  max-width: 80%;
}

.source-url-link:hover {
  text-decoration: underline;
}
</style>
