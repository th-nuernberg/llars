<template>
  <div class="step-upload pa-6">
    <!-- Upload Drop Zone -->
    <div
      class="drop-zone"
      :class="{
        'drop-zone--active': isDragging,
        'drop-zone--success': hasUploads && !hasErrors,
        'drop-zone--partial': hasUploads && hasErrors,
        'drop-zone--error': !hasUploads && uploadError
      }"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="handleDrop"
      @click="openFilePicker"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".json,.jsonl,.csv,.xlsx,.tsv"
        multiple
        class="d-none"
        @change="handleFileSelect"
      />

      <!-- Uploading State -->
      <template v-if="isUploading">
        <v-progress-circular
          :model-value="uploadProgress"
          :indeterminate="uploadProgress === 0"
          color="primary"
          size="64"
          width="6"
        >
          <span class="text-caption">{{ uploadProgress }}%</span>
        </v-progress-circular>
        <div class="text-body-1 mt-4 font-weight-medium">{{ processingStatus }}</div>
        <div class="text-caption text-medium-emphasis mt-2">
          {{ processedFiles }} von {{ totalFiles }} Dateien
        </div>
      </template>

      <!-- Success State -->
      <template v-else-if="hasUploads && !hasErrors">
        <LIcon size="64" color="success" class="mb-2">mdi-check-circle</LIcon>
        <div class="text-h6 font-weight-medium">{{ uploadSummary }}</div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          {{ totalItemCount.toLocaleString() }} Einträge geladen
        </div>
        <div class="text-caption text-medium-emphasis mt-3">
          Weitere hinzufügen per Drag & Drop
        </div>
      </template>

      <!-- Partial Success State -->
      <template v-else-if="hasUploads && hasErrors">
        <LIcon size="64" color="warning" class="mb-2">mdi-alert-circle</LIcon>
        <div class="text-h6 font-weight-medium">{{ uploadSummary }}</div>
        <div class="text-body-2 text-warning mt-1">
          {{ failedFiles.length }} Dateien fehlgeschlagen
        </div>
      </template>

      <!-- Error State -->
      <template v-else-if="uploadError">
        <LIcon size="64" color="error" class="mb-2">mdi-close-circle</LIcon>
        <div class="text-h6 font-weight-medium text-error">Upload fehlgeschlagen</div>
        <div class="text-body-2 mt-2">{{ uploadError }}</div>
        <LBtn variant="text" size="small" class="mt-3" @click.stop="clearError">
          Erneut versuchen
        </LBtn>
      </template>

      <!-- Empty State -->
      <template v-else>
        <LIcon size="64" color="primary" :class="{ 'bounce': isDragging }">
          mdi-cloud-upload-outline
        </LIcon>
        <div class="text-h6 mt-3 font-weight-medium">Dateien & Ordner hochladen</div>
        <div class="text-body-2 text-medium-emphasis mt-2">
          Drag & Drop oder klicken
        </div>
      </template>
    </div>

    <!-- Supported Formats -->
    <div class="text-center mt-3">
      <span class="formats-label">JSON · JSONL · CSV · TSV · XLSX</span>
    </div>

    <!-- Uploaded Files Tree -->
    <v-expand-transition>
      <div v-if="hasUploads" class="uploaded-section mt-6">
        <div class="d-flex align-center justify-space-between mb-3">
          <span class="text-subtitle-2 d-flex align-center">
            <LIcon size="18" class="mr-2" color="primary">mdi-file-tree</LIcon>
            Hochgeladene Inhalte
          </span>
          <LBtn
            variant="text"
            size="small"
            color="error"
            prepend-icon="mdi-delete-outline"
            :disabled="isUploading"
            @click.stop="resetUpload"
          >
            Zurücksetzen
          </LBtn>
        </div>

        <!-- Tree View -->
        <div class="file-tree">
          <template v-for="(group, folderPath) in groupedUploads" :key="folderPath">
            <!-- Folder Header -->
            <div
              v-if="folderPath !== '_root'"
              class="folder-row"
              @click="toggleFolder(folderPath)"
            >
              <LIcon size="20" color="amber-darken-2" class="mr-2">
                {{ expandedFolders[folderPath] ? 'mdi-folder-open' : 'mdi-folder' }}
              </LIcon>
              <span class="folder-name">{{ folderPath }}</span>
              <v-spacer />
              <span class="file-count">{{ group.length }}</span>
              <LIcon size="18" class="ml-1">
                {{ expandedFolders[folderPath] ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </LIcon>
            </div>

            <!-- Files -->
            <v-expand-transition>
              <div v-show="folderPath === '_root' || expandedFolders[folderPath]">
                <div
                  v-for="file in group"
                  :key="file.session_id"
                  class="file-row"
                  :class="{ 'file-row--nested': folderPath !== '_root' }"
                >
                  <LIcon size="18" :color="getFormatColor(file.detected_format)" class="mr-2">
                    {{ getFormatIcon(file.detected_format) }}
                  </LIcon>
                  <span class="file-name">{{ file.displayName || file.filename }}</span>
                  <v-spacer />
                  <span class="file-meta">
                    {{ (file.item_count || file.structure?.item_count || 0).toLocaleString() }}
                  </span>
                  <v-btn
                    icon
                    size="x-small"
                    variant="text"
                    class="ml-1 remove-btn"
                    @click.stop="removeFile(file.session_id)"
                  >
                    <LIcon size="16">mdi-close</LIcon>
                  </v-btn>
                </div>
              </div>
            </v-expand-transition>
          </template>
        </div>

        <!-- Stats Cards -->
        <div class="stats-row mt-4">
          <div class="stat-card">
            <div class="stat-value">{{ totalFileCount }}</div>
            <div class="stat-label">Dateien</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ totalItemCount.toLocaleString() }}</div>
            <div class="stat-label">Einträge</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ folderCount }}</div>
            <div class="stat-label">Ordner</div>
          </div>
        </div>

        <!-- Failed Files Alert -->
        <v-alert
          v-if="failedFiles.length > 0"
          type="warning"
          variant="tonal"
          density="compact"
          class="mt-4"
          closable
          @click:close="failedFiles = []"
        >
          <div class="text-body-2 font-weight-medium">
            {{ failedFiles.length }} Dateien konnten nicht verarbeitet werden
          </div>
          <div class="text-caption mt-1">
            {{ failedFiles.slice(0, 3).join(', ') }}
            <span v-if="failedFiles.length > 3">und {{ failedFiles.length - 3 }} weitere</span>
          </div>
        </v-alert>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import importService from '@/services/importService'

const props = defineProps({
  session: { type: Object, default: null },
  sessions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  error: { type: String, default: null }
})

const emit = defineEmits(['update:session', 'update:sessions', 'uploaded'])

// State
const fileInput = ref(null)
const isDragging = ref(false)
const isUploading = ref(false)
const processedFiles = ref(0)
const totalFiles = ref(0)
const processingStatus = ref('')
const expandedFolders = ref({})
const uploadedFiles = ref([])
const failedFiles = ref([])
const uploadError = ref(null)

// Computed
const hasUploads = computed(() => uploadedFiles.value.length > 0)
const hasErrors = computed(() => failedFiles.value.length > 0)
const totalFileCount = computed(() => uploadedFiles.value.length)
const uploadProgress = computed(() => totalFiles.value > 0 ? Math.round((processedFiles.value / totalFiles.value) * 100) : 0)

const totalItemCount = computed(() => {
  return uploadedFiles.value.reduce((sum, f) => sum + (f.item_count || f.structure?.item_count || 0), 0)
})

const folderCount = computed(() => {
  const folders = new Set(uploadedFiles.value.map(f => f.folderPath).filter(p => p && p !== '_root'))
  return folders.size || (uploadedFiles.value.length > 0 ? 1 : 0)
})

const uploadSummary = computed(() => {
  const folders = new Set(uploadedFiles.value.map(f => f.folderPath).filter(p => p !== '_root'))
  if (folders.size > 1) {
    return `${folders.size} Ordner geladen`
  } else if (folders.size === 1) {
    return `${[...folders][0]} geladen`
  }
  return `${uploadedFiles.value.length} Dateien geladen`
})

const groupedUploads = computed(() => {
  const groups = {}
  for (const file of uploadedFiles.value) {
    const path = file.folderPath || '_root'
    if (!groups[path]) groups[path] = []
    groups[path].push(file)
  }
  const sorted = {}
  if (groups['_root']) sorted['_root'] = groups['_root']
  Object.keys(groups).sort().forEach(key => {
    if (key !== '_root') sorted[key] = groups[key]
  })
  return sorted
})

// Helpers
const getFormatIcon = (format) => {
  const icons = { openai: 'mdi-chat', lmsys: 'mdi-compare', jsonl: 'mdi-code-braces', csv: 'mdi-table', generic: 'mdi-auto-fix' }
  return icons[format] || 'mdi-file-document-outline'
}

const getFormatColor = (format) => {
  const colors = { openai: 'success', lmsys: 'info', jsonl: 'warning', csv: 'primary', generic: 'secondary' }
  return colors[format] || 'grey'
}

// Actions
const openFilePicker = () => {
  if (!isUploading.value) {
    fileInput.value?.click()
  }
}

const clearError = () => {
  uploadError.value = null
  failedFiles.value = []
}

const onDragOver = (e) => {
  isDragging.value = true
  e.dataTransfer.dropEffect = 'copy'
}

const onDragLeave = () => {
  isDragging.value = false
}

// Drop handler
const handleDrop = async (event) => {
  isDragging.value = false
  uploadError.value = null
  const items = event.dataTransfer?.items
  const filesToUpload = []

  if (items) {
    const promises = []
    for (const item of items) {
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry?.()
        if (entry) {
          promises.push(traverseEntry(entry, filesToUpload, ''))
        } else {
          const file = item.getAsFile()
          if (file && isValidFile(file)) {
            filesToUpload.push({ file, folderPath: '_root', displayName: file.name })
          }
        }
      }
    }
    await Promise.all(promises)
  } else {
    const files = event.dataTransfer?.files
    for (const file of files) {
      if (isValidFile(file)) {
        filesToUpload.push({ file, folderPath: '_root', displayName: file.name })
      }
    }
  }

  if (filesToUpload.length > 0) {
    await uploadFiles(filesToUpload)
  }
}

// Recursive folder traversal
const traverseEntry = async (entry, files, basePath) => {
  if (entry.isFile) {
    return new Promise((resolve) => {
      entry.file((file) => {
        if (isValidFile(file)) {
          const folderPath = basePath || '_root'
          files.push({ file, folderPath, displayName: file.name })
        }
        resolve()
      })
    })
  } else if (entry.isDirectory) {
    const reader = entry.createReader()
    const newPath = basePath ? `${basePath}/${entry.name}` : entry.name
    expandedFolders.value[newPath] = true

    return new Promise((resolve) => {
      const readAll = (allEntries = []) => {
        reader.readEntries(async (entries) => {
          if (entries.length === 0) {
            await Promise.all(allEntries.map(e => traverseEntry(e, files, newPath)))
            resolve()
          } else {
            readAll([...allEntries, ...entries])
          }
        })
      }
      readAll()
    })
  }
}

const isValidFile = (file) => {
  const validExtensions = ['.json', '.jsonl', '.csv', '.xlsx', '.tsv']
  const name = file.name.toLowerCase()
  if (name.startsWith('.') || name === 'thumbs.db' || name === 'desktop.ini') return false
  return validExtensions.some(ext => name.endsWith(ext))
}

const handleFileSelect = async (event) => {
  uploadError.value = null
  const files = Array.from(event.target.files || [])
    .filter(isValidFile)
    .map(file => ({ file, folderPath: '_root', displayName: file.name }))
  if (files.length > 0) await uploadFiles(files)
  event.target.value = ''
}

// Upload handler with error handling
const uploadFiles = async (filesToUpload) => {
  isUploading.value = true
  totalFiles.value = filesToUpload.length
  processedFiles.value = 0
  failedFiles.value = []

  for (const { file, folderPath, displayName } of filesToUpload) {
    processingStatus.value = displayName
    try {
      const result = await importService.uploadFile(file)
      result.folderPath = folderPath
      result.displayName = displayName
      uploadedFiles.value.push(result)
    } catch (err) {
      console.error(`Upload failed: ${file.name}`, err)
      failedFiles.value.push(displayName)

      // Check for rate limit error
      if (err.response?.status === 429) {
        uploadError.value = 'Rate Limit erreicht. Bitte warten und erneut versuchen.'
        break
      }
    }
    processedFiles.value++
  }

  isUploading.value = false
  emitUpdates()
}

const toggleFolder = (path) => {
  expandedFolders.value[path] = !expandedFolders.value[path]
}

const removeFile = (sessionId) => {
  const index = uploadedFiles.value.findIndex(f => f.session_id === sessionId)
  if (index !== -1) {
    uploadedFiles.value.splice(index, 1)
    emitUpdates()
  }
}

const resetUpload = () => {
  uploadedFiles.value = []
  expandedFolders.value = {}
  failedFiles.value = []
  uploadError.value = null
  emit('update:session', null)
  emit('update:sessions', [])
}

const emitUpdates = () => {
  emit('update:sessions', uploadedFiles.value)
  if (uploadedFiles.value.length > 0) {
    emit('update:session', uploadedFiles.value[0])
    emit('uploaded', uploadedFiles.value)
  } else {
    emit('update:session', null)
  }
}

onMounted(() => {
  if (props.sessions?.length > 0) {
    uploadedFiles.value = [...props.sessions]
  } else if (props.session) {
    uploadedFiles.value = [props.session]
  }
})
</script>

<style scoped>
/* LLARS Design System */
.drop-zone {
  border: 2px dashed rgba(176, 202, 151, 0.5);
  border-radius: 16px 4px 16px 4px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(176, 202, 151, 0.03);
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.drop-zone:hover {
  border-color: #b0ca97;
  background: rgba(176, 202, 151, 0.08);
}

.drop-zone--active {
  border-color: #b0ca97;
  border-width: 3px;
  background: rgba(176, 202, 151, 0.15);
  transform: scale(1.01);
}

.drop-zone--success {
  border-color: #98d4bb;
  border-style: solid;
  background: rgba(152, 212, 187, 0.08);
}

.drop-zone--partial {
  border-color: #D1BC8A;
  border-style: solid;
  background: rgba(209, 188, 138, 0.08);
}

.drop-zone--error {
  border-color: #e8a087;
  border-style: solid;
  background: rgba(232, 160, 135, 0.08);
}

.formats-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  letter-spacing: 0.5px;
}

/* File Tree */
.file-tree {
  border: 1px solid rgba(var(--v-border-color), 0.12);
  border-radius: 8px 2px 8px 2px;
  max-height: 280px;
  overflow-y: auto;
}

.folder-row {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.4);
  cursor: pointer;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.08);
}

.folder-row:hover {
  background: rgba(var(--v-theme-surface-variant), 0.6);
}

.folder-name {
  font-weight: 500;
  font-size: 0.875rem;
}

.file-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.file-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.05);
}

.file-row:last-child {
  border-bottom: none;
}

.file-row--nested {
  padding-left: 36px;
}

.file-row:hover {
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.file-row:hover .remove-btn {
  opacity: 1;
}

.file-name {
  font-size: 0.875rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.file-meta {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.remove-btn {
  opacity: 0;
  transition: opacity 0.15s;
  color: rgba(var(--v-theme-error), 0.7);
}

/* Stats */
.stats-row {
  display: flex;
  gap: 12px;
}

.stat-card {
  flex: 1;
  text-align: center;
  padding: 12px 8px;
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 6px 2px 6px 2px;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.stat-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 2px;
}

/* Animation */
.bounce {
  animation: bounce 0.5s ease infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
</style>
