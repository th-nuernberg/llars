<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    max-width="800"
    scrollable
  >
    <LCard class="variable-manager-card">
      <template #header>
        <div class="dialog-header">
          <div class="header-left">
            <LIcon size="24" color="primary" class="mr-2">mdi-variable</LIcon>
            <span class="header-title">{{ $t('promptEngineering.variables.title') }}</span>
            <LTag v-if="variablesList.length > 0" variant="info" size="small" class="ml-2">
              {{ variablesList.length }}
            </LTag>
          </div>
          <v-btn icon variant="text" size="small" @click="closeDialog">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </div>
      </template>

      <div class="dialog-body">
        <!-- New Variable Form -->
        <div class="new-variable-section">
          <div class="section-title">
            <LIcon size="16" class="mr-1">mdi-plus-circle</LIcon>
            {{ $t('promptEngineering.variables.createNew') }}
          </div>

          <div class="new-variable-form">
            <v-text-field
              v-model="newVarName"
              :label="$t('promptEngineering.variables.name')"
              :placeholder="$t('promptEngineering.variables.namePlaceholder')"
              density="compact"
              variant="outlined"
              hide-details
              :error="!!nameError"
              class="name-input"
              @keyup.enter="focusContent"
            >
              <template #prepend-inner>
                <span class="tag-preview">{{ openBraces }}</span>
              </template>
              <template #append-inner>
                <span class="tag-preview">{{ closeBraces }}</span>
              </template>
            </v-text-field>

            <v-textarea
              ref="contentInput"
              v-model="newVarContent"
              :label="$t('promptEngineering.variables.content')"
              :placeholder="$t('promptEngineering.variables.contentPlaceholder')"
              density="compact"
              variant="outlined"
              rows="3"
              auto-grow
              hide-details
              class="content-input"
            />

            <div v-if="nameError" class="error-message">{{ nameError }}</div>

            <LBtn
              variant="primary"
              :disabled="!canCreate"
              @click="handleCreate"
              class="create-btn"
            >
              <LIcon start>mdi-plus</LIcon>
              {{ $t('promptEngineering.variables.create') }}
            </LBtn>
          </div>
        </div>

        <!-- Variables List -->
        <div class="variables-list-section">
          <div class="section-title">
            <LIcon size="16" class="mr-1">mdi-format-list-bulleted</LIcon>
            {{ $t('promptEngineering.variables.existing') }}
          </div>

          <div v-if="variablesList.length === 0" class="empty-state">
            <LIcon size="48" color="grey-lighten-1">mdi-variable-box</LIcon>
            <p>{{ $t('promptEngineering.variables.noVariables') }}</p>
            <p class="hint">{{ $t('promptEngineering.variables.noVariablesHint') }}</p>
          </div>

          <div v-else class="variables-list">
            <div
              v-for="variable in variablesList"
              :key="variable.name"
              class="variable-item"
              :class="{ 'is-editing': editingVar === variable.name }"
            >
              <!-- View Mode -->
              <template v-if="editingVar !== variable.name">
                <div class="variable-header">
                  <div class="variable-tag">
                    <LIcon size="14" class="drag-icon">mdi-drag-vertical</LIcon>
                    <span class="tag-name">{{ formatTag(variable.name) }}</span>
                  </div>
                  <v-spacer />
                  <div class="variable-actions">
                    <v-btn icon size="x-small" variant="text" @click="startEdit(variable)">
                      <LIcon size="16">mdi-pencil</LIcon>
                    </v-btn>
                    <v-btn icon size="x-small" variant="text" color="error" @click="handleDelete(variable.name)">
                      <LIcon size="16">mdi-delete</LIcon>
                    </v-btn>
                  </div>
                </div>
                <div class="variable-content-preview">
                  {{ truncate(variable.content, 150) }}
                </div>
              </template>

              <!-- Edit Mode -->
              <template v-else>
                <div class="edit-form">
                  <v-textarea
                    v-model="editContent"
                    :label="$t('promptEngineering.variables.content')"
                    density="compact"
                    variant="outlined"
                    rows="3"
                    auto-grow
                    hide-details
                  />
                  <div class="edit-actions">
                    <LBtn variant="primary" size="small" @click="saveEdit(variable.name)">
                      <LIcon start size="14">mdi-check</LIcon>
                      {{ $t('common.save') }}
                    </LBtn>
                    <LBtn variant="text" size="small" @click="cancelEdit">
                      {{ $t('common.cancel') }}
                    </LBtn>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Usage Hint -->
        <div class="usage-hint">
          <LIcon size="16" class="mr-2">mdi-information-outline</LIcon>
          <span>{{ $t('promptEngineering.variables.usageHint') }}</span>
        </div>
      </div>

      <template #actions>
        <LBtn variant="cancel" @click="closeDialog">
          {{ $t('common.close') }}
        </LBtn>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  promptId: {
    type: [String, Number],
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'variablesChanged'])
const { t } = useI18n()

// Template helpers to avoid Vue parsing issues with braces
const openBraces = '{{'
const closeBraces = '}}'

// Storage key
const STORAGE_KEY = 'llars_prompt_variables_simple'

const getStorageKey = () => {
  return props.promptId ? `${STORAGE_KEY}_${props.promptId}` : STORAGE_KEY
}

// State
const variablesList = ref([])
const newVarName = ref('')
const newVarContent = ref('')
const nameError = ref('')
const editingVar = ref(null)
const editContent = ref('')
const contentInput = ref(null)

// Validation
const VALID_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_]*$/
const INVALID_NAMES = new Set([
  'undefined', 'null', 'true', 'false', 'NaN', 'Infinity'
])

const canCreate = computed(() => {
  const name = newVarName.value.trim()
  if (!name) return false
  if (!VALID_NAME_REGEX.test(name)) return false
  if (INVALID_NAMES.has(name)) return false
  if (variablesList.value.some(v => v.name === name)) return false
  return true
})

// Helpers
const formatTag = (name) => `{{${name}}}`

const truncate = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

const focusContent = () => {
  nextTick(() => {
    contentInput.value?.focus()
  })
}

// Storage
const loadFromStorage = () => {
  try {
    const stored = localStorage.getItem(getStorageKey())
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        variablesList.value = parsed.filter(v =>
          v && typeof v === 'object' &&
          v.name && typeof v.name === 'string' &&
          VALID_NAME_REGEX.test(v.name) &&
          !INVALID_NAMES.has(v.name)
        )
      }
    }
  } catch (e) {
    console.warn('Failed to load variables:', e)
    variablesList.value = []
  }
}

const saveToStorage = () => {
  try {
    localStorage.setItem(getStorageKey(), JSON.stringify(variablesList.value))
    emit('variablesChanged', variablesList.value)
  } catch (e) {
    console.warn('Failed to save variables:', e)
  }
}

// Actions
const handleCreate = () => {
  const name = newVarName.value.trim()
  const content = newVarContent.value

  if (!name) {
    nameError.value = t('promptEngineering.variables.errorNameRequired')
    return
  }

  if (!VALID_NAME_REGEX.test(name)) {
    nameError.value = t('promptEngineering.variables.errorInvalidName')
    return
  }

  if (INVALID_NAMES.has(name)) {
    nameError.value = t('promptEngineering.variables.errorReservedName')
    return
  }

  if (variablesList.value.some(v => v.name === name)) {
    nameError.value = t('promptEngineering.variables.errorNameExists')
    return
  }

  variablesList.value.push({
    name,
    content,
    createdAt: new Date().toISOString()
  })

  saveToStorage()

  // Reset form
  newVarName.value = ''
  newVarContent.value = ''
  nameError.value = ''
}

const handleDelete = (name) => {
  variablesList.value = variablesList.value.filter(v => v.name !== name)
  saveToStorage()
}

const startEdit = (variable) => {
  editingVar.value = variable.name
  editContent.value = variable.content || ''
}

const saveEdit = (name) => {
  const index = variablesList.value.findIndex(v => v.name === name)
  if (index !== -1) {
    variablesList.value[index] = {
      ...variablesList.value[index],
      content: editContent.value,
      updatedAt: new Date().toISOString()
    }
    saveToStorage()
  }
  cancelEdit()
}

const cancelEdit = () => {
  editingVar.value = null
  editContent.value = ''
}

const closeDialog = () => {
  emit('update:modelValue', false)
}

// Watch for dialog open
watch(() => props.modelValue, (isOpen) => {
  if (isOpen) {
    loadFromStorage()
  }
})

// Watch for promptId changes
watch(() => props.promptId, () => {
  loadFromStorage()
})

// Expose for parent
defineExpose({
  variablesList,
  loadFromStorage
})
</script>

<style scoped>
.variable-manager-card {
  max-height: 85vh;
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
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 8px;
  max-height: calc(85vh - 140px);
  overflow-y: auto;
}

.section-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 12px;
}

/* New Variable Section */
.new-variable-section {
  background: rgba(var(--v-theme-primary), 0.05);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
  border-radius: 12px;
  padding: 16px;
}

.new-variable-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.name-input {
  max-width: 300px;
}

.name-input :deep(.v-field) {
  border-radius: 8px 3px 8px 3px;
}

.tag-preview {
  font-family: 'Roboto Mono', monospace;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  font-size: 0.9rem;
}

.content-input :deep(.v-field) {
  border-radius: 8px;
}

.error-message {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-error));
}

.create-btn {
  align-self: flex-start;
}

/* Variables List */
.variables-list-section {
  flex: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.15);
}

.empty-state p {
  margin: 8px 0 0 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.empty-state .hint {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.variable-item {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 10px;
  padding: 12px;
  transition: all 0.2s ease;
}

.variable-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.variable-item.is-editing {
  border-color: rgba(var(--v-theme-primary), 0.5);
  background: rgba(var(--v-theme-primary), 0.05);
}

.variable-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.variable-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px 4px 6px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.15), rgba(var(--v-theme-primary), 0.08));
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 6px 2px 6px 2px;
}

.drag-icon {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.tag-name {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.variable-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.variable-item:hover .variable-actions {
  opacity: 1;
}

.variable-content-preview {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  background: rgba(var(--v-theme-on-surface), 0.03);
  padding: 8px 12px;
  border-radius: 6px;
}

/* Edit Form */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-actions {
  display: flex;
  gap: 8px;
}

/* Usage Hint */
.usage-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: rgba(var(--v-theme-info), 0.1);
  border-radius: 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Scrollbar */
.dialog-body::-webkit-scrollbar {
  width: 6px;
}

.dialog-body::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-body::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}
</style>
