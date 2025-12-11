<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
    persistent
  >
    <v-card>
      <v-card-title class="text-h5 pa-4">
        <v-icon icon="mdi-upload" class="mr-2"></v-icon>
        Dokumente hochladen
      </v-card-title>

      <v-divider></v-divider>

      <v-card-text class="pa-4">
        <!-- Collection auswählen -->
        <v-select
          v-model="selectedCollection"
          label="Collection auswählen *"
          :items="collectionItems"
          variant="outlined"
          density="comfortable"
          :rules="[v => !!v || 'Bitte wählen Sie eine Collection']"
          class="mb-4"
        >
          <template v-slot:selection="{ item }">
            <v-icon :icon="getIcon(item.raw.icon)" :color="item.raw.color" class="mr-2"></v-icon>
            {{ item.raw.display_name }}
          </template>
          <template v-slot:item="{ item, props }">
            <v-list-item v-bind="props">
              <template v-slot:prepend>
                <v-avatar :color="item.raw.color" size="32">
                  <v-icon :icon="getIcon(item.raw.icon)" color="white" size="20"></v-icon>
                </v-avatar>
              </template>
            </v-list-item>
          </template>
        </v-select>

        <!-- Drag & Drop Zone -->
        <v-card
          :class="['drop-zone', { 'drop-zone-active': isDragging }]"
          variant="outlined"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="handleDrop"
        >
          <v-card-text class="text-center pa-8">
            <v-icon
              :icon="isDragging ? 'mdi-cloud-upload' : 'mdi-cloud-upload-outline'"
              :size="isDragging ? 72 : 64"
              :color="isDragging ? 'primary' : 'grey-lighten-1'"
              class="mb-4"
            ></v-icon>

            <div class="text-h6 mb-2">
              {{ isDragging ? 'Dateien hier ablegen' : 'Dateien hierher ziehen' }}
            </div>

            <div class="text-medium-emphasis mb-4">oder</div>

            <LBtn
              variant="primary"
              prepend-icon="mdi-file-plus"
              @click="$refs.fileInput.click()"
            >
              Dateien auswählen
            </LBtn>

            <input
              ref="fileInput"
              type="file"
              multiple
              accept=".pdf,.txt,.md"
              style="display: none"
              @change="handleFileSelect"
            />

            <div class="text-caption text-medium-emphasis mt-4">
              Erlaubte Formate: PDF, TXT, MD (Markdown)
            </div>
          </v-card-text>
        </v-card>

        <!-- Dateiliste -->
        <v-card v-if="files.length > 0" variant="outlined" class="mt-4">
          <v-card-title class="text-subtitle-1 pa-3">
            Ausgewählte Dateien ({{ files.length }})
          </v-card-title>
          <v-divider></v-divider>

          <v-list density="compact">
            <v-list-item
              v-for="(file, index) in files"
              :key="index"
              class="file-item"
            >
              <template v-slot:prepend>
                <v-icon
                  :icon="getFileIcon(file.name)"
                  :color="getFileColor(file.name)"
                ></v-icon>
              </template>

              <v-list-item-title>{{ file.name }}</v-list-item-title>
              <v-list-item-subtitle>{{ formatSize(file.size) }}</v-list-item-subtitle>

              <template v-slot:append>
                <!-- Upload Status -->
                <div v-if="uploadProgress[index] !== undefined" class="mr-2">
                  <v-progress-circular
                    v-if="uploadProgress[index] < 100"
                    :model-value="uploadProgress[index]"
                    :size="24"
                    :width="3"
                    color="primary"
                  >
                    <span class="text-caption">{{ uploadProgress[index] }}</span>
                  </v-progress-circular>
                  <v-icon v-else color="success" icon="mdi-check-circle"></v-icon>
                </div>

                <!-- Error Status -->
                <v-tooltip v-if="uploadErrors[index]" location="top">
                  <template v-slot:activator="{ props }">
                    <v-icon v-bind="props" color="error" icon="mdi-alert-circle" class="mr-2"></v-icon>
                  </template>
                  <span>{{ uploadErrors[index] }}</span>
                </v-tooltip>

                <!-- Remove Button -->
                <v-btn
                  icon="mdi-close"
                  size="x-small"
                  variant="text"
                  @click="removeFile(index)"
                  :disabled="isUploading"
                ></v-btn>
              </template>
            </v-list-item>
          </v-list>

          <!-- Gesamtfortschritt -->
          <v-card-text v-if="isUploading" class="pa-3">
            <div class="d-flex align-center mb-2">
              <span class="text-caption text-medium-emphasis">Gesamtfortschritt</span>
              <v-spacer></v-spacer>
              <span class="text-caption font-weight-medium">{{ overallProgress }}%</span>
            </div>
            <v-progress-linear
              :model-value="overallProgress"
              color="primary"
              height="6"
              rounded
            ></v-progress-linear>
          </v-card-text>
        </v-card>

        <!-- Upload Zusammenfassung -->
        <v-alert
          v-if="uploadComplete"
          type="success"
          variant="tonal"
          density="compact"
          class="mt-4"
        >
          {{ successCount }} von {{ files.length }} Datei(en) erfolgreich hochgeladen
        </v-alert>

        <v-alert
          v-if="errorCount > 0 && uploadComplete"
          type="error"
          variant="tonal"
          density="compact"
          class="mt-2"
        >
          {{ errorCount }} Datei(en) konnten nicht hochgeladen werden
        </v-alert>
      </v-card-text>

      <v-divider></v-divider>

      <v-card-actions class="pa-4">
        <v-spacer></v-spacer>
        <LBtn
          variant="cancel"
          @click="handleClose"
          :disabled="isUploading"
        >
          {{ uploadComplete ? 'Schließen' : 'Abbrechen' }}
        </LBtn>
        <LBtn
          variant="primary"
          @click="handleUpload"
          :disabled="!canUpload"
          :loading="isUploading"
        >
          Hochladen
        </LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  collections: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'uploaded'])

const selectedCollection = ref(null)
const files = ref([])
const isDragging = ref(false)
const isUploading = ref(false)
const uploadProgress = ref({})
const uploadErrors = ref({})
const uploadComplete = ref(false)

const collectionItems = computed(() => {
  return props.collections.map(c => ({
    value: c.name,
    display_name: c.display_name || c.name,
    icon: c.icon,
    color: c.color
  }))
})

const canUpload = computed(() => {
  return selectedCollection.value && files.value.length > 0 && !isUploading.value
})

const overallProgress = computed(() => {
  if (Object.keys(uploadProgress.value).length === 0) return 0
  const total = Object.values(uploadProgress.value).reduce((sum, val) => sum + val, 0)
  return Math.round(total / files.value.length)
})

const successCount = computed(() => {
  return Object.values(uploadProgress.value).filter(p => p === 100).length
})

const errorCount = computed(() => {
  return Object.keys(uploadErrors.value).length
})

const getIcon = (iconName) => {
  const iconMap = {
    'book': 'mdi-book',
    'folder': 'mdi-folder',
    'faq': 'mdi-comment-question',
    'database': 'mdi-database',
    'text': 'mdi-text-box',
    'email': 'mdi-email',
    'archive': 'mdi-archive'
  }
  return iconMap[iconName] || 'mdi-folder'
}

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  const iconMap = {
    'pdf': 'mdi-file-pdf-box',
    'txt': 'mdi-file-document',
    'md': 'mdi-language-markdown'
  }
  return iconMap[ext] || 'mdi-file'
}

const getFileColor = (filename) => {
  const ext = filename.split('.').pop().toLowerCase()
  const colorMap = {
    'pdf': 'red',
    'txt': 'blue',
    'md': 'green'
  }
  return colorMap[ext] || 'grey'
}

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const handleDrop = (event) => {
  isDragging.value = false
  const droppedFiles = Array.from(event.dataTransfer.files)
  addFiles(droppedFiles)
}

const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
}

const addFiles = (newFiles) => {
  const validExtensions = ['pdf', 'txt', 'md']
  const validFiles = newFiles.filter(file => {
    const ext = file.name.split('.').pop().toLowerCase()
    return validExtensions.includes(ext)
  })

  files.value.push(...validFiles)
}

const removeFile = (index) => {
  files.value.splice(index, 1)
  delete uploadProgress.value[index]
  delete uploadErrors.value[index]
}

const handleUpload = async () => {
  if (!canUpload.value) return

  isUploading.value = true
  uploadComplete.value = false
  uploadProgress.value = {}
  uploadErrors.value = {}

  const formData = new FormData()
  formData.append('collection_name', selectedCollection.value)

  files.value.forEach((file, index) => {
    formData.append('files', file)
    uploadProgress.value[index] = 0
  })

  try {
    const response = await axios.post('/api/rag/documents/upload-multiple', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)

        // Verteile Fortschritt gleichmäßig auf alle Dateien
        files.value.forEach((_, index) => {
          uploadProgress.value[index] = percentCompleted
        })
      }
    })

    // Verarbeite Upload-Ergebnisse
    if (response.data.results) {
      response.data.results.forEach((result, index) => {
        if (result.success) {
          uploadProgress.value[index] = 100
        } else {
          uploadErrors.value[index] = result.error || 'Unbekannter Fehler'
          uploadProgress.value[index] = 0
        }
      })
    }

    uploadComplete.value = true
    emit('uploaded', response.data)

    // Auto-close nach erfolgreichen Upload ohne Fehler
    if (errorCount.value === 0) {
      setTimeout(() => {
        handleClose()
      }, 2000)
    }
  } catch (error) {
    console.error('Upload error:', error)

    // Markiere alle Dateien als fehlgeschlagen
    files.value.forEach((_, index) => {
      uploadErrors.value[index] = error.response?.data?.message || 'Upload fehlgeschlagen'
      uploadProgress.value[index] = 0
    })

    uploadComplete.value = true
  } finally {
    isUploading.value = false
  }
}

const handleClose = () => {
  // Reset state
  selectedCollection.value = null
  files.value = []
  uploadProgress.value = {}
  uploadErrors.value = {}
  uploadComplete.value = false
  isDragging.value = false

  emit('update:modelValue', false)
}
</script>

<style scoped>
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.3);
  transition: all 0.3s ease;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.drop-zone-active {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  transform: scale(1.02);
}

.file-item {
  color: rgb(var(--v-theme-on-surface));
}

.file-item :deep(.v-list-item-title) {
  color: rgb(var(--v-theme-on-surface));
}

.file-item :deep(.v-list-item-subtitle) {
  color: rgba(var(--v-theme-on-surface), 0.7);
}
</style>
