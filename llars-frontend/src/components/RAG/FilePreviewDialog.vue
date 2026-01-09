<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    fullscreen
    transition="dialog-bottom-transition"
    class="file-preview-dialog"
  >
    <v-card class="d-flex flex-column bg-grey-darken-4">
      <!-- Toolbar -->
      <v-toolbar color="grey-darken-3" density="compact">
        <LIcon :icon="getFileIcon()" :color="getFileColor()" class="ml-4 mr-2" />
        <v-toolbar-title class="text-body-1">
          {{ document?.filename || document?.title || 'Dokument' }}
        </v-toolbar-title>

        <v-chip v-if="document?.status" size="small" :color="getStatusColor()" class="mx-2">
          {{ document.status }}
        </v-chip>

        <v-spacer />

        <!-- Actions -->
        <v-btn
          icon="mdi-information-outline"
          variant="text"
          @click="$emit('showDetails', document)"
          title="Details anzeigen"
        />
        <v-btn
          icon="mdi-download"
          variant="text"
          @click="handleDownload"
          title="Herunterladen"
        />
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        />
      </v-toolbar>

      <!-- Content -->
      <div class="flex-grow-1 d-flex align-center justify-center file-preview-content">
        <!-- Loading State -->
        <v-progress-circular
          v-if="loading"
          indeterminate
          color="primary"
          size="64"
        />

        <!-- PDF Viewer -->
        <iframe
          v-else-if="isPdf && viewUrl"
          :src="viewUrl"
          class="pdf-frame"
        />

        <!-- Image Viewer -->
        <img
          v-else-if="isImage && viewUrl"
          :src="viewUrl"
          :alt="document?.filename"
          class="image-preview"
          @load="loading = false"
        />

        <!-- Text/Markdown Viewer -->
        <div v-else-if="isText && textContent" class="text-preview pa-6">
          <pre class="text-content">{{ textContent }}</pre>
        </div>

        <!-- Unsupported Format -->
        <div v-else class="text-center pa-8">
          <LIcon size="96" color="grey-lighten-1" class="mb-4">mdi-file-document-outline</LIcon>
          <div class="text-h6 text-grey-lighten-1 mb-2">Vorschau nicht verfuegbar</div>
          <div class="text-body-2 text-grey mb-6">
            {{ getFileTypeLabel() }}
          </div>
          <v-btn
            variant="tonal"
            color="primary"
            size="large"
            prepend-icon="mdi-download"
            @click="handleDownload"
          >
            Datei herunterladen
          </v-btn>
        </div>
      </div>

      <!-- Footer with file info -->
      <v-footer class="bg-grey-darken-3 pa-2">
        <div class="d-flex align-center justify-space-between w-100 text-caption text-grey-lighten-1">
          <div class="d-flex align-center ga-4">
            <span v-if="document?.file_size_bytes">
              <LIcon size="14" class="mr-1">mdi-harddisk</LIcon>
              {{ formatSize(document.file_size_bytes) }}
            </span>
            <span v-if="document?.chunk_count">
              <LIcon size="14" class="mr-1">mdi-puzzle</LIcon>
              {{ document.chunk_count }} Chunks
            </span>
            <span v-if="document?.collection_name">
              <LIcon size="14" class="mr-1">mdi-folder</LIcon>
              {{ document.collection_name }}
            </span>
          </div>
          <div v-if="document?.uploaded_at">
            <LIcon size="14" class="mr-1">mdi-calendar</LIcon>
            {{ formatDate(document.uploaded_at) }}
          </div>
        </div>
      </v-footer>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
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

const emit = defineEmits(['update:modelValue', 'download', 'showDetails'])

const loading = ref(false)
const textContent = ref('')

// Computed URLs
const viewUrl = computed(() => {
  if (!props.document?.id) return ''
  return `/api/rag/documents/${props.document.id}/view`
})

const downloadUrl = computed(() => {
  if (!props.document?.id) return ''
  return `/api/rag/documents/${props.document.id}/download`
})

// File type detection
const fileType = computed(() => {
  return props.document?.file_type?.toLowerCase() ||
    props.document?.mime_type?.split('/').pop() ||
    getExtension(props.document?.filename) ||
    ''
})

const mimeType = computed(() => props.document?.mime_type || '')

const isPdf = computed(() => {
  return fileType.value === 'pdf' || mimeType.value === 'application/pdf'
})

const isImage = computed(() => {
  const imageTypes = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp']
  return imageTypes.includes(fileType.value) || mimeType.value.startsWith('image/')
})

const isText = computed(() => {
  const textTypes = ['txt', 'md', 'markdown', 'csv', 'json', 'xml', 'html', 'css', 'js']
  return textTypes.includes(fileType.value) ||
    mimeType.value.startsWith('text/') ||
    mimeType.value === 'application/json'
})

const canPreview = computed(() => isPdf.value || isImage.value || isText.value)

// Helpers
function getExtension(filename) {
  if (!filename) return ''
  const parts = filename.split('.')
  return parts.length > 1 ? parts.pop().toLowerCase() : ''
}

function getFileIcon() {
  if (isPdf.value) return 'mdi-file-pdf-box'
  if (isImage.value) return 'mdi-file-image'
  if (isText.value) return 'mdi-file-document'
  if (fileType.value === 'docx' || fileType.value === 'doc') return 'mdi-file-word'
  return 'mdi-file'
}

function getFileColor() {
  if (isPdf.value) return 'red'
  if (isImage.value) return 'green'
  if (isText.value) return 'blue'
  return 'grey'
}

function getStatusColor() {
  const colors = {
    'pending': 'warning',
    'processing': 'info',
    'indexed': 'success',
    'failed': 'error'
  }
  return colors[props.document?.status] || 'grey'
}

function getFileTypeLabel() {
  const labels = {
    'pdf': 'PDF Dokument',
    'docx': 'Word Dokument',
    'doc': 'Word Dokument',
    'txt': 'Textdatei',
    'md': 'Markdown',
    'csv': 'CSV Datei'
  }
  return labels[fileType.value] || fileType.value?.toUpperCase() || 'Unbekanntes Format'
}

function formatSize(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('de-DE', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Actions
function handleDownload() {
  if (props.document?.id) {
    window.open(downloadUrl.value, '_blank')
  }
  emit('download', props.document)
}

// Load text content for text files
async function loadTextContent() {
  if (!props.document?.id || !isText.value) return

  loading.value = true
  try {
    const response = await axios.get(`/api/rag/documents/${props.document.id}/content`)
    textContent.value = response.data.content || ''
  } catch (error) {
    console.error('Error loading text content:', error)
    textContent.value = 'Fehler beim Laden des Inhalts'
  } finally {
    loading.value = false
  }
}

// Watch for dialog open
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    loading.value = true
    textContent.value = ''

    if (isText.value) {
      loadTextContent()
    } else if (isPdf.value) {
      // PDF loads via iframe, show loading briefly
      setTimeout(() => { loading.value = false }, 500)
    } else if (isImage.value) {
      // Image will trigger @load event
      loading.value = true
    } else {
      loading.value = false
    }
  }
})
</script>

<style scoped>
.file-preview-dialog {
  z-index: 2500;
}

.file-preview-content {
  background: #1e1e1e;
  overflow: auto;
}

.pdf-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #525659;
}

.image-preview {
  max-width: 95%;
  max-height: 95%;
  object-fit: contain;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.text-preview {
  width: 100%;
  height: 100%;
  overflow: auto;
  background: #2d2d2d;
}

.text-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #e0e0e0;
  margin: 0;
}
</style>
