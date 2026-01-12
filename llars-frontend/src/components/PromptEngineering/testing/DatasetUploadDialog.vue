<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="800"
    persistent
    scrollable
  >
    <LCard class="dataset-upload-card">
      <template #header>
        <div class="dialog-header">
          <div class="header-left">
            <LIcon size="24" color="primary" class="mr-2">mdi-database-plus</LIcon>
            <span class="header-title">{{ $t('promptEngineering.testing.createDataset') }}</span>
          </div>
          <v-btn icon variant="text" size="small" @click="handleClose">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </div>
      </template>

      <div class="dialog-body">
        <!-- Step Indicator -->
        <div class="step-indicator">
          <div
            v-for="(step, idx) in steps"
            :key="step.id"
            :class="['step', { 'step-active': currentStep === idx, 'step-done': currentStep > idx }]"
          >
            <div class="step-number">
              <LIcon v-if="currentStep > idx" size="16">mdi-check</LIcon>
              <span v-else>{{ idx + 1 }}</span>
            </div>
            <span class="step-label">{{ step.label }}</span>
          </div>
        </div>

        <!-- Step 1: Upload -->
        <div v-if="currentStep === 0" class="step-content">
          <h3 class="step-title">{{ $t('promptEngineering.testing.uploadFile') }}</h3>
          <p class="step-description">{{ $t('promptEngineering.testing.uploadDescription') }}</p>

          <!-- Drag & Drop Zone -->
          <div
            :class="['drop-zone', { 'drop-zone-active': isDragging }]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            @click="$refs.fileInput.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".json,.csv,.txt,.md"
              style="display: none"
              @change="handleFileSelect"
            />

            <LIcon
              :size="isDragging ? 56 : 48"
              :color="isDragging ? 'primary' : 'grey'"
              class="mb-3"
            >
              {{ isDragging ? 'mdi-cloud-upload' : 'mdi-cloud-upload-outline' }}
            </LIcon>

            <div class="drop-title">
              {{ isDragging ? $t('promptEngineering.testing.dropHere') : $t('promptEngineering.testing.dragFile') }}
            </div>

            <div class="drop-subtitle">{{ $t('promptEngineering.testing.orClick') }}</div>

            <div class="drop-formats">
              <LTag v-for="fmt in ['JSON', 'CSV', 'TXT', 'MD']" :key="fmt" variant="info" size="small" class="mr-1">
                {{ fmt }}
              </LTag>
            </div>
          </div>

          <!-- Uploaded File Info -->
          <v-card v-if="uploadedFile" variant="outlined" class="mt-4">
            <v-list-item>
              <template #prepend>
                <LIcon :color="getFileColor(uploadedFile.name)" size="24">
                  {{ getFileIcon(uploadedFile.name) }}
                </LIcon>
              </template>

              <v-list-item-title>{{ uploadedFile.name }}</v-list-item-title>
              <v-list-item-subtitle>
                {{ formatSize(uploadedFile.size) }} | {{ detectedType }}
              </v-list-item-subtitle>

              <template #append>
                <LIcon v-if="!parseError" color="success">mdi-check-circle</LIcon>
                <v-tooltip v-else location="top">
                  <template #activator="{ props }">
                    <LIcon v-bind="props" color="error">mdi-alert-circle</LIcon>
                  </template>
                  {{ parseError }}
                </v-tooltip>
                <v-btn icon size="small" variant="text" class="ml-2" @click="clearFile">
                  <LIcon>mdi-close</LIcon>
                </v-btn>
              </template>
            </v-list-item>
          </v-card>
        </div>

        <!-- Step 2: Configure -->
        <div v-if="currentStep === 1" class="step-content">
          <h3 class="step-title">{{ $t('promptEngineering.testing.configureDataset') }}</h3>

          <!-- Dataset Name -->
          <v-text-field
            v-model="datasetName"
            :label="$t('promptEngineering.testing.datasetName')"
            variant="outlined"
            density="compact"
            class="mb-4"
            :rules="[v => !!v || $t('promptEngineering.testing.nameRequired')]"
          />

          <!-- Detected Structure -->
          <div class="structure-info">
            <div class="structure-header">
              <LIcon size="18" class="mr-2">mdi-file-tree</LIcon>
              <span>{{ $t('promptEngineering.testing.detectedStructure') }}</span>
            </div>

            <div class="structure-details">
              <LTag :variant="isArrayData ? 'success' : 'info'" class="mr-2">
                {{ isArrayData ? `${dataItems.length} Items` : 'Single Object' }}
              </LTag>
              <LTag v-if="availableFields.length > 0" variant="secondary">
                {{ availableFields.length }} {{ $t('promptEngineering.testing.fields') }}
              </LTag>
            </div>
          </div>

          <!-- Variable Mapping (wenn Variablen vorhanden) -->
          <div v-if="promptVariables.length > 0" class="mapping-section">
            <div class="mapping-header">
              <LIcon size="18" class="mr-2">mdi-link-variant</LIcon>
              <span>{{ $t('promptEngineering.testing.variableMapping') }}</span>
            </div>
            <p class="mapping-description">{{ $t('promptEngineering.testing.mappingDescription') }}</p>

            <div v-for="variable in promptVariables" :key="variable.name" class="mapping-row">
              <code class="mapping-variable">{{ formatPlaceholder(variable.name) }}</code>
              <LIcon size="16" class="mx-2">mdi-arrow-right</LIcon>
              <v-select
                v-model="variableMapping[variable.name]"
                :items="mappingOptions"
                item-title="label"
                item-value="path"
                density="compact"
                variant="outlined"
                hide-details
                :placeholder="$t('promptEngineering.testing.selectField')"
                clearable
                class="mapping-select"
              >
                <template #item="{ item, props }">
                  <v-list-item v-bind="props">
                    <template #prepend>
                      <LIcon size="14" :color="getPathColor(item.raw.type)" class="mr-2">
                        {{ getPathIcon(item.raw.type) }}
                      </LIcon>
                    </template>
                    <v-list-item-subtitle v-if="item.raw.preview">
                      {{ item.raw.preview }}
                    </v-list-item-subtitle>
                  </v-list-item>
                </template>
              </v-select>
            </div>
          </div>

          <!-- Item Name Field (für Array-Daten) -->
          <div v-if="isArrayData" class="item-name-section">
            <div class="mapping-header">
              <LIcon size="18" class="mr-2">mdi-tag</LIcon>
              <span>{{ $t('promptEngineering.testing.itemNameField') }}</span>
            </div>
            <v-select
              v-model="itemNameField"
              :items="stringFields"
              item-title="label"
              item-value="path"
              density="compact"
              variant="outlined"
              hide-details
              :placeholder="$t('promptEngineering.testing.selectNameField')"
              clearable
            />
          </div>
        </div>

        <!-- Step 3: Preview -->
        <div v-if="currentStep === 2" class="step-content">
          <h3 class="step-title">{{ $t('promptEngineering.testing.preview') }}</h3>

          <div class="preview-summary">
            <LTag variant="success" size="small" class="mr-2">
              <LIcon start size="12">mdi-check</LIcon>
              {{ previewItems.length }} Items
            </LTag>
            <LTag v-if="Object.keys(variableMapping).length > 0" variant="info" size="small">
              {{ Object.keys(variableMapping).filter(k => variableMapping[k]).length }} {{ $t('promptEngineering.testing.mappedVariables') }}
            </LTag>
          </div>

          <!-- Preview Cards -->
          <div class="preview-list">
            <v-card
              v-for="(item, idx) in previewItems.slice(0, 3)"
              :key="idx"
              variant="outlined"
              class="preview-card"
            >
              <v-card-title class="text-subtitle-2">
                <LIcon size="16" class="mr-2">mdi-file-document</LIcon>
                {{ item.name || `Item ${idx + 1}` }}
              </v-card-title>
              <v-card-text>
                <div v-for="(value, key) in item.variables" :key="key" class="preview-variable">
                  <code class="preview-var-name">{{ key }}</code>
                  <span class="preview-var-value">{{ truncateValue(value) }}</span>
                </div>
              </v-card-text>
            </v-card>

            <div v-if="previewItems.length > 3" class="preview-more">
              + {{ previewItems.length - 3 }} {{ $t('promptEngineering.testing.moreItems') }}
            </div>
          </div>
        </div>
      </div>

      <template #actions>
        <div class="dialog-actions">
          <LBtn v-if="currentStep > 0" variant="text" @click="prevStep">
            <LIcon start>mdi-chevron-left</LIcon>
            {{ $t('common.back') }}
          </LBtn>
          <v-spacer />
          <LBtn variant="cancel" @click="handleClose">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn
            v-if="currentStep < 2"
            variant="primary"
            :disabled="!canProceed"
            @click="nextStep"
          >
            {{ $t('common.next') }}
            <LIcon end>mdi-chevron-right</LIcon>
          </LBtn>
          <LBtn
            v-else
            variant="primary"
            :loading="isSaving"
            @click="saveDataset"
          >
            <LIcon start>mdi-content-save</LIcon>
            {{ $t('promptEngineering.testing.saveDataset') }}
          </LBtn>
        </div>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { analyzeJsonStructure, parseFileContent } from '../composables/usePromptVariables'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  promptVariables: {
    type: Array,
    default: () => []
  },
  promptId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'created'])
const { t } = useI18n()

// Helper to format variable placeholder (avoids Vue template parser issues with nested braces)
const formatPlaceholder = (name) => `{{${name}}}`

// Steps
const steps = [
  { id: 'upload', label: t('promptEngineering.testing.steps.upload') },
  { id: 'configure', label: t('promptEngineering.testing.steps.configure') },
  { id: 'preview', label: t('promptEngineering.testing.steps.preview') }
]

// State
const currentStep = ref(0)
const isDragging = ref(false)
const uploadedFile = ref(null)
const fileContent = ref(null)
const detectedType = ref(null)
const parseError = ref(null)
const datasetName = ref('')
const variableMapping = ref({})
const itemNameField = ref(null)
const isSaving = ref(false)
const fileInput = ref(null)

// Computed
const isArrayData = computed(() => Array.isArray(fileContent.value))

const dataItems = computed(() => {
  if (!fileContent.value) return []
  if (Array.isArray(fileContent.value)) return fileContent.value
  return [fileContent.value]
})

const availableFields = computed(() => {
  if (!fileContent.value) return []

  const sample = isArrayData.value ? fileContent.value[0] : fileContent.value
  if (!sample || typeof sample !== 'object') return []

  return analyzeJsonStructure(sample, '$', 2)
})

const mappingOptions = computed(() => {
  return [
    { path: '$', label: t('promptEngineering.testing.entireObject'), type: 'object', preview: '' },
    ...availableFields.value.map(f => ({
      path: f.path,
      label: f.path,
      type: f.type,
      preview: f.preview
    }))
  ]
})

const stringFields = computed(() => {
  return availableFields.value
    .filter(f => f.type === 'string')
    .map(f => ({
      path: f.path,
      label: f.path,
      type: f.type,
      preview: f.preview
    }))
})

const previewItems = computed(() => {
  return dataItems.value.map((item, idx) => {
    const name = itemNameField.value
      ? evaluatePath(item, itemNameField.value)
      : `Item ${idx + 1}`

    const variables = {}
    for (const [varName, path] of Object.entries(variableMapping.value)) {
      if (path) {
        variables[varName] = evaluatePath(item, path)
      }
    }

    return { id: idx, name, variables, raw: item }
  })
})

const canProceed = computed(() => {
  if (currentStep.value === 0) {
    return uploadedFile.value && !parseError.value
  }
  if (currentStep.value === 1) {
    return datasetName.value.trim().length > 0
  }
  return true
})

// Methods
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

const processFile = (file) => {
  uploadedFile.value = file
  parseError.value = null

  // Set default name from file
  datasetName.value = file.name.replace(/\.[^.]+$/, '')

  const reader = new FileReader()
  reader.onload = (e) => {
    const content = e.target.result
    const parsed = parseFileContent(file.name, content)

    if (parsed.error) {
      parseError.value = parsed.error
      fileContent.value = null
      return
    }

    fileContent.value = parsed.data
    detectedType.value = parsed.type

    // Initialize mapping for prompt variables
    variableMapping.value = {}
    props.promptVariables.forEach(v => {
      variableMapping.value[v.name] = null
    })
  }

  reader.onerror = () => {
    parseError.value = t('promptEngineering.testing.readError')
  }

  reader.readAsText(file)
}

const clearFile = () => {
  uploadedFile.value = null
  fileContent.value = null
  detectedType.value = null
  parseError.value = null
  datasetName.value = ''
  variableMapping.value = {}
  itemNameField.value = null
}

const evaluatePath = (data, path) => {
  if (!path || path === '$') return data

  const cleanPath = path.startsWith('$.') ? path.slice(2) : path
  const parts = cleanPath.split('.')
  let current = data

  for (const part of parts) {
    if (current === undefined || current === null) return undefined
    current = current[part]
  }

  return current
}

const truncateValue = (value) => {
  const str = typeof value === 'object' ? JSON.stringify(value) : String(value)
  if (str.length <= 80) return str
  return str.slice(0, 80) + '...'
}

const nextStep = () => {
  if (currentStep.value < steps.length - 1) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const saveDataset = async () => {
  isSaving.value = true

  try {
    const dataset = {
      id: crypto.randomUUID(),
      name: datasetName.value,
      sourceFileName: uploadedFile.value?.name,
      variableMapping: variableMapping.value,
      itemNameField: itemNameField.value,
      items: previewItems.value.map(item => ({
        id: crypto.randomUUID(),
        name: item.name,
        variables: item.variables
      })),
      createdAt: new Date().toISOString()
    }

    // TODO: Backend API call
    // await axios.post(`/api/prompts/${props.promptId}/datasets`, dataset)

    emit('created', dataset)
    handleClose()
  } catch (error) {
    console.error('Failed to save dataset:', error)
  } finally {
    isSaving.value = false
  }
}

const handleClose = () => {
  currentStep.value = 0
  clearFile()
  emit('update:modelValue', false)
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
  const icons = { json: 'mdi-code-json', csv: 'mdi-file-table', txt: 'mdi-file-document', md: 'mdi-language-markdown' }
  return icons[ext] || 'mdi-file'
}

const getFileColor = (filename) => {
  const ext = filename?.split('.').pop()?.toLowerCase()
  const colors = { json: 'orange', csv: 'green', txt: 'blue', md: 'purple' }
  return colors[ext] || 'grey'
}

const getPathIcon = (type) => {
  const icons = { object: 'mdi-code-braces', array: 'mdi-code-brackets', string: 'mdi-format-text', number: 'mdi-numeric' }
  return icons[type] || 'mdi-help'
}

const getPathColor = (type) => {
  const colors = { object: 'orange', array: 'blue', string: 'green', number: 'red' }
  return colors[type] || 'grey'
}

// Reset when dialog closes
watch(() => props.modelValue, (isOpen) => {
  if (!isOpen) {
    currentStep.value = 0
    clearFile()
  }
})
</script>

<style scoped>
.dataset-upload-card {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.dialog-body {
  padding: 16px;
  overflow-y: auto;
  max-height: calc(90vh - 160px);
}

/* Step Indicator */
.step-indicator {
  display: flex;
  justify-content: center;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.step {
  display: flex;
  align-items: center;
  gap: 8px;
  opacity: 0.5;
}

.step-active {
  opacity: 1;
}

.step-done {
  opacity: 0.8;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.step-active .step-number {
  background: rgb(var(--v-theme-primary));
  color: white;
}

.step-done .step-number {
  background: rgb(var(--v-theme-success));
  color: white;
}

.step-label {
  font-size: 0.85rem;
  font-weight: 500;
}

/* Step Content */
.step-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.step-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.step-description {
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 16px;
}

/* Drop Zone */
.drop-zone {
  border: 2px dashed rgba(var(--v-theme-on-surface), 0.25);
  border-radius: 12px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
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

.drop-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 4px;
}

.drop-subtitle {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 12px;
}

.drop-formats {
  display: flex;
  gap: 4px;
}

/* Structure Info */
.structure-info {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 16px;
}

.structure-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  margin-bottom: 8px;
}

.structure-details {
  display: flex;
  gap: 8px;
}

/* Mapping Section */
.mapping-section {
  margin-bottom: 16px;
}

.mapping-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  margin-bottom: 8px;
}

.mapping-description {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 12px;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
}

.mapping-variable {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  min-width: 120px;
}

.mapping-select {
  flex: 1;
  max-width: 300px;
}

/* Item Name Section */
.item-name-section {
  margin-top: 16px;
}

/* Preview */
.preview-summary {
  margin-bottom: 16px;
}

.preview-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.preview-card {
  border-radius: 8px;
}

.preview-variable {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 0.85rem;
}

.preview-var-name {
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 6px;
  border-radius: 3px;
}

.preview-var-value {
  color: rgba(var(--v-theme-on-surface), 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.preview-more {
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-style: italic;
}

/* Actions */
.dialog-actions {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 0;
  gap: 8px;
}
</style>
