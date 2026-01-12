<template>
  <div class="variable-editor" :class="{ 'is-config-open': showConfigPanel }">
    <!-- Variable Header -->
    <div class="variable-header">
      <code class="variable-name">{{ formatPlaceholder(variable.name) }}</code>
      <span v-if="variable.occurrences > 1" class="occurrence-badge">
        {{ variable.occurrences }}x
      </span>
      <LTag v-if="isFilled" variant="success" size="small">
        <LIcon start size="12">mdi-check</LIcon>
        {{ $t('promptEngineering.testing.filled') }}
      </LTag>
      <LTag v-else variant="warning" size="small">
        <LIcon start size="12">mdi-alert</LIcon>
        {{ $t('promptEngineering.testing.empty') }}
      </LTag>
      <v-spacer />
      <!-- Config Toggle Button -->
      <v-btn
        icon
        size="x-small"
        variant="text"
        :color="showConfigPanel ? 'primary' : 'default'"
        @click="showConfigPanel = !showConfigPanel"
      >
        <LIcon size="16">{{ showConfigPanel ? 'mdi-chevron-up' : 'mdi-cog' }}</LIcon>
      </v-btn>
    </div>

    <!-- Description Preview (wenn vorhanden und Config nicht offen) -->
    <div v-if="variable.description && !showConfigPanel" class="description-preview">
      <LIcon size="12" class="mr-1">mdi-information</LIcon>
      {{ variable.description }}
    </div>

    <!-- Config Panel (expandable) -->
    <v-expand-transition>
      <div v-if="showConfigPanel" class="config-panel">
        <v-text-field
          v-model="configForm.description"
          :label="$t('promptEngineering.testing.description')"
          :placeholder="$t('promptEngineering.testing.descriptionPlaceholder')"
          density="compact"
          variant="outlined"
          hide-details
          class="mb-2"
        />
        <v-textarea
          v-model="configForm.defaultValue"
          :label="$t('promptEngineering.testing.defaultValue')"
          :placeholder="$t('promptEngineering.testing.defaultValuePlaceholder')"
          density="compact"
          variant="outlined"
          rows="2"
          auto-grow
          hide-details
          class="mb-2"
        />
        <div class="config-actions">
          <LBtn
            variant="primary"
            size="small"
            @click="saveConfig"
          >
            <LIcon start size="14">mdi-check</LIcon>
            {{ $t('common.save') }}
          </LBtn>
          <LBtn
            v-if="configForm.defaultValue && !isFilled"
            variant="text"
            size="small"
            @click="applyDefault"
          >
            <LIcon start size="14">mdi-arrow-down</LIcon>
            {{ $t('promptEngineering.testing.applyDefault') }}
          </LBtn>
        </div>
      </div>
    </v-expand-transition>

    <!-- Input Mode Tabs -->
    <div class="input-mode-tabs">
      <v-btn-toggle v-model="inputMode" mandatory density="compact">
        <v-btn value="text" size="small">
          <LIcon start size="14">mdi-pencil</LIcon>
          {{ $t('promptEngineering.testing.text') }}
        </v-btn>
        <v-btn value="file" size="small">
          <LIcon start size="14">mdi-file-upload</LIcon>
          {{ $t('promptEngineering.testing.file') }}
        </v-btn>
        <v-btn value="dataset" size="small" :disabled="!hasDatasets">
          <LIcon start size="14">mdi-database</LIcon>
          {{ $t('promptEngineering.testing.dataset') }}
        </v-btn>
      </v-btn-toggle>
    </div>

    <!-- Text Input Mode -->
    <div v-if="inputMode === 'text'" class="input-section">
      <v-textarea
        v-model="textValue"
        variant="outlined"
        density="compact"
        rows="3"
        auto-grow
        :placeholder="$t('promptEngineering.testing.enterValue')"
        hide-details
        @update:modelValue="handleTextInput"
      />
    </div>

    <!-- File Upload Mode -->
    <div v-else-if="inputMode === 'file'" class="input-section">
      <!-- Drop Zone (wenn keine Datei) -->
      <div
        v-if="!uploadedFile"
        :class="['drop-zone', { 'drop-zone-active': isDragging }]"
        @click="triggerFileInput"
        @drop.prevent="handleDrop"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".json,.csv,.txt,.md"
          style="display: none"
          @change="handleFileSelect"
        />
        <LIcon :size="isDragging ? 36 : 32" :color="isDragging ? 'primary' : 'grey'">
          {{ isDragging ? 'mdi-cloud-upload' : 'mdi-cloud-upload-outline' }}
        </LIcon>
        <span class="drop-text">{{ $t('promptEngineering.testing.dropFile') }}</span>
        <small class="drop-hint">JSON, CSV, TXT, MD</small>
      </div>

      <!-- Datei-Info (wenn Datei hochgeladen) -->
      <div v-else class="file-info">
        <div class="file-header">
          <LIcon :color="getFileColor(uploadedFile.name)" class="mr-2">
            {{ getFileIcon(uploadedFile.name) }}
          </LIcon>
          <span class="file-name">{{ uploadedFile.name }}</span>
          <span class="file-size">{{ formatSize(uploadedFile.size) }}</span>
          <v-btn icon size="x-small" variant="text" @click="clearFile">
            <LIcon size="16">mdi-close</LIcon>
          </v-btn>
        </div>

        <!-- JSON Path Selector (nur bei JSON) -->
        <div v-if="fileType === 'json' && jsonPaths.length > 0" class="path-selector">
          <label class="path-label">{{ $t('promptEngineering.testing.selectPath') }}</label>
          <v-select
            v-model="selectedPath"
            :items="jsonPathItems"
            item-title="label"
            item-value="path"
            density="compact"
            variant="outlined"
            hide-details
            :placeholder="$t('promptEngineering.testing.entireFile')"
            clearable
            @update:modelValue="handlePathSelect"
          >
            <template #item="{ item, props }">
              <v-list-item v-bind="props">
                <template #prepend>
                  <LIcon size="16" :color="getPathColor(item.raw.type)" class="mr-2">
                    {{ getPathIcon(item.raw.type) }}
                  </LIcon>
                </template>
                <v-list-item-subtitle>{{ item.raw.preview }}</v-list-item-subtitle>
              </v-list-item>
            </template>
          </v-select>
        </div>

        <!-- Vorschau des ausgewählten Werts -->
        <div v-if="filePreview" class="file-preview">
          <div class="preview-header">
            <span>{{ $t('promptEngineering.testing.preview') }}</span>
            <span class="char-count">{{ previewCharCount }} {{ $t('promptEngineering.testing.chars') }}</span>
          </div>
          <pre class="preview-content">{{ truncatedPreview }}</pre>
        </div>
      </div>
    </div>

    <!-- Dataset Mode -->
    <div v-else-if="inputMode === 'dataset'" class="input-section">
      <v-select
        v-model="selectedDatasetId"
        :items="datasets"
        item-title="name"
        item-value="id"
        density="compact"
        variant="outlined"
        :placeholder="$t('promptEngineering.testing.selectDataset')"
        hide-details
        class="mb-2"
        @update:modelValue="handleDatasetSelect"
      >
        <template #item="{ item, props }">
          <v-list-item v-bind="props">
            <template #append>
              <LTag variant="info" size="small">{{ item.raw.items?.length || 0 }} Items</LTag>
            </template>
          </v-list-item>
        </template>
      </v-select>

      <v-select
        v-if="selectedDatasetId && datasetItems.length > 0"
        v-model="selectedItemId"
        :items="datasetItems"
        item-title="name"
        item-value="id"
        density="compact"
        variant="outlined"
        :placeholder="$t('promptEngineering.testing.selectItem')"
        hide-details
        @update:modelValue="handleItemSelect"
      />

      <div v-if="!hasDatasets" class="no-datasets">
        <LIcon size="24" color="grey" class="mb-2">mdi-database-off</LIcon>
        <span>{{ $t('promptEngineering.testing.noDatasets') }}</span>
        <LBtn variant="text" size="small" @click="$emit('createDataset')">
          {{ $t('promptEngineering.testing.createDataset') }}
        </LBtn>
      </div>
    </div>

    <!-- Kompakte Wert-Vorschau (immer sichtbar wenn gefüllt) -->
    <div v-if="isFilled && inputMode !== 'file'" class="value-summary">
      <div class="summary-header">
        <LIcon size="14" class="mr-1">mdi-text</LIcon>
        <span>{{ valueCharCount }} {{ $t('promptEngineering.testing.chars') }}</span>
        <v-spacer />
        <LBtn variant="text" size="x-small" @click="showFullPreview = !showFullPreview">
          {{ showFullPreview ? $t('common.less') : $t('common.more') }}
        </LBtn>
      </div>
      <pre v-if="showFullPreview" class="summary-content">{{ currentValue }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { analyzeJsonStructure, parseFileContent } from '../composables/usePromptVariables'

const props = defineProps({
  variable: {
    type: Object,
    required: true
  },
  value: {
    type: [String, Object, Array],
    default: null
  },
  meta: {
    type: Object,
    default: () => ({})
  },
  config: {
    type: Object,
    default: () => ({})
  },
  datasets: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update', 'updateConfig', 'createDataset'])
const { t } = useI18n()

// Helper to format variable placeholder (avoids Vue template parser issues with nested braces)
const formatPlaceholder = (name) => `{{${name}}}`

// State
const inputMode = ref('text')
const textValue = ref('')
const showConfigPanel = ref(false)

// Config form state
const configForm = reactive({
  description: '',
  defaultValue: ''
})

// Initialize config form from props
watch(() => props.config, (newConfig) => {
  if (newConfig) {
    configForm.description = newConfig.description || props.variable.description || ''
    configForm.defaultValue = newConfig.defaultValue || props.variable.defaultValue || ''
  }
}, { immediate: true })

// Also watch variable for initial values
watch(() => props.variable, (newVar) => {
  if (newVar && !props.config?.description) {
    configForm.description = newVar.description || ''
    configForm.defaultValue = newVar.defaultValue || ''
  }
}, { immediate: true })

const saveConfig = () => {
  emit('updateConfig', props.variable.name, {
    description: configForm.description,
    defaultValue: configForm.defaultValue
  })
  showConfigPanel.value = false
}

const applyDefault = () => {
  if (configForm.defaultValue) {
    textValue.value = configForm.defaultValue
    emit('update', props.variable.name, configForm.defaultValue, { source: 'default' })
  }
}
const isDragging = ref(false)
const uploadedFile = ref(null)
const fileContent = ref(null)
const fileType = ref(null)
const jsonPaths = ref([])
const selectedPath = ref(null)
const selectedDatasetId = ref(null)
const selectedItemId = ref(null)
const showFullPreview = ref(false)
const fileInput = ref(null)

// Computed
const isFilled = computed(() => {
  return props.value !== null && props.value !== undefined && props.value !== ''
})

const hasDatasets = computed(() => props.datasets.length > 0)

const currentValue = computed(() => {
  if (props.value === null || props.value === undefined) return ''
  if (typeof props.value === 'object') return JSON.stringify(props.value, null, 2)
  return String(props.value)
})

const valueCharCount = computed(() => currentValue.value.length)

const filePreview = computed(() => {
  if (!fileContent.value) return null

  let value = fileContent.value
  if (selectedPath.value && fileType.value === 'json') {
    value = evaluateSimplePath(fileContent.value, selectedPath.value)
  }

  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
})

const previewCharCount = computed(() => filePreview.value?.length || 0)

const truncatedPreview = computed(() => {
  const preview = filePreview.value || ''
  if (preview.length <= 500) return preview
  return preview.slice(0, 500) + '\n...'
})

const jsonPathItems = computed(() => {
  return jsonPaths.value.map(p => ({
    path: p.path,
    label: p.path,
    type: p.type,
    preview: p.preview
  }))
})

const datasetItems = computed(() => {
  const dataset = props.datasets.find(d => d.id === selectedDatasetId.value)
  return dataset?.items || []
})

// Methods
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleTextInput = (value) => {
  emit('update', props.variable.name, value, { source: 'manual' })
}

const handleDrop = (event) => {
  isDragging.value = false
  const files = event.dataTransfer?.files
  if (files?.length > 0) {
    processFile(files[0])
  }
}

const handleFileSelect = (event) => {
  const files = event.target?.files
  if (files?.length > 0) {
    processFile(files[0])
  }
}

const processFile = async (file) => {
  uploadedFile.value = file

  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target.result
    const parsed = parseFileContent(file.name, content)

    fileContent.value = parsed.data
    fileType.value = parsed.type

    if (parsed.error) {
      console.error('Parse error:', parsed.error)
      return
    }

    // JSON-Struktur analysieren
    if (parsed.type === 'json' && typeof parsed.data === 'object') {
      jsonPaths.value = analyzeJsonStructure(parsed.data)
    }

    // Initial den gesamten Inhalt setzen
    emit('update', props.variable.name, parsed.data, {
      source: 'file',
      fileName: file.name,
      jsonPath: null
    })
  }

  reader.readAsText(file)
}

const handlePathSelect = (path) => {
  if (!fileContent.value) return

  let value = fileContent.value
  if (path) {
    value = evaluateSimplePath(fileContent.value, path)
  }

  emit('update', props.variable.name, value, {
    source: 'file',
    fileName: uploadedFile.value?.name,
    jsonPath: path
  })
}

const evaluateSimplePath = (data, path) => {
  if (!path || path === '$') return data

  const cleanPath = path.startsWith('$.') ? path.slice(2) : path
  const parts = cleanPath.split(/\.(?![^\[]*\])/)
  let current = data

  for (const part of parts) {
    if (current === undefined || current === null) return undefined

    const arrayMatch = part.match(/^([^[]+)\[(\d+|\*)\]$/)
    if (arrayMatch) {
      const [, fieldName, indexOrStar] = arrayMatch
      current = current[fieldName]

      if (!Array.isArray(current)) return undefined

      if (indexOrStar === '*') {
        return current.map(item =>
          typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item)
        ).join('\n\n')
      } else {
        current = current[parseInt(indexOrStar)]
      }
    } else {
      current = current[part]
    }
  }

  return current
}

const clearFile = () => {
  uploadedFile.value = null
  fileContent.value = null
  fileType.value = null
  jsonPaths.value = []
  selectedPath.value = null
  emit('update', props.variable.name, null, {})
}

const handleDatasetSelect = () => {
  selectedItemId.value = null
}

const handleItemSelect = (itemId) => {
  const dataset = props.datasets.find(d => d.id === selectedDatasetId.value)
  const item = dataset?.items?.find(i => i.id === itemId)

  if (item?.variables?.[props.variable.name]) {
    emit('update', props.variable.name, item.variables[props.variable.name], {
      source: 'dataset',
      datasetId: selectedDatasetId.value,
      datasetItemId: itemId,
      datasetItemName: item.name
    })
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

const getFileIcon = (filename) => {
  const ext = filename?.split('.').pop()?.toLowerCase()
  const icons = {
    json: 'mdi-code-json',
    csv: 'mdi-file-table',
    txt: 'mdi-file-document',
    md: 'mdi-language-markdown'
  }
  return icons[ext] || 'mdi-file'
}

const getFileColor = (filename) => {
  const ext = filename?.split('.').pop()?.toLowerCase()
  const colors = {
    json: 'orange',
    csv: 'green',
    txt: 'blue',
    md: 'purple'
  }
  return colors[ext] || 'grey'
}

const getPathIcon = (type) => {
  const icons = {
    object: 'mdi-code-braces',
    array: 'mdi-code-brackets',
    array_all: 'mdi-format-list-bulleted',
    string: 'mdi-format-text',
    number: 'mdi-numeric',
    boolean: 'mdi-toggle-switch'
  }
  return icons[type] || 'mdi-help'
}

const getPathColor = (type) => {
  const colors = {
    object: 'orange',
    array: 'blue',
    array_all: 'purple',
    string: 'green',
    number: 'red',
    boolean: 'teal'
  }
  return colors[type] || 'grey'
}

// Watchers
watch(() => props.value, (newVal) => {
  if (inputMode.value === 'text' && typeof newVal === 'string') {
    textValue.value = newVal
  }
}, { immediate: true })

watch(() => props.meta, (newMeta) => {
  if (newMeta?.source === 'file') {
    inputMode.value = 'file'
  } else if (newMeta?.source === 'dataset') {
    inputMode.value = 'dataset'
    selectedDatasetId.value = newMeta.datasetId
    selectedItemId.value = newMeta.datasetItemId
  }
}, { immediate: true })
</script>

<style scoped>
.variable-editor {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}

.variable-editor.is-config-open {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
}

.variable-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.variable-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.occurrence-badge {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  background: rgba(var(--v-theme-on-surface), 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Description Preview */
.description-preview {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  background: rgba(var(--v-theme-info), 0.08);
  padding: 4px 8px;
  border-radius: 4px;
  margin-bottom: 10px;
}

/* Config Panel */
.config-panel {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.config-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.input-mode-tabs {
  margin-bottom: 10px;
}

.input-section {
  margin-bottom: 8px;
}

/* Drop Zone */
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.25);
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.drop-zone:hover {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background: rgba(var(--v-theme-primary), 0.03);
}

.drop-zone-active {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
  transform: scale(1.01);
}

.drop-text {
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.drop-hint {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* File Info */
.file-info {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 12px;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 10px;
}

.file-name {
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-right: 8px;
}

/* Path Selector */
.path-selector {
  margin-bottom: 10px;
}

.path-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  display: block;
  margin-bottom: 4px;
}

/* File Preview */
.file-preview {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  padding: 8px;
  margin-top: 8px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 6px;
}

.char-count {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.preview-content {
  font-size: 0.8rem;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 150px;
  overflow-y: auto;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* No Datasets */
.no-datasets {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Value Summary */
.value-summary {
  background: rgba(var(--v-theme-success), 0.08);
  border-radius: 6px;
  padding: 8px;
  margin-top: 8px;
}

.summary-header {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.summary-content {
  font-size: 0.8rem;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
  margin: 8px 0 0 0;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Scrollbar */
.preview-content::-webkit-scrollbar,
.summary-content::-webkit-scrollbar {
  width: 4px;
}

.preview-content::-webkit-scrollbar-thumb,
.summary-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}
</style>
