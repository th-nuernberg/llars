<template>
  <div class="placeholder-palette">
    <!-- Header -->
    <div class="palette-header">
      <LIcon size="16" class="mr-1">mdi-variable</LIcon>
      <span class="palette-title">{{ $t('promptEngineering.testing.placeholderPalette') }}</span>
      <v-spacer />
      <LTag v-if="allVariables.length > 0" variant="info" size="small">
        {{ allVariables.length }}
      </LTag>
    </div>

    <!-- Variables List -->
    <div class="placeholder-list">
      <!-- Empty state -->
      <div v-if="allVariables.length === 0" class="no-placeholders">
        <LIcon size="24" color="grey-lighten-1" class="mb-1">mdi-variable-box</LIcon>
        <p class="hint-text">{{ $t('promptEngineering.testing.noPlaceholdersHint') }}</p>
      </div>

      <!-- User-Created Variables (from VariableManagerDialog) -->
      <div v-if="userVariables.length > 0" class="variables-section">
        <div class="section-label">
          <LIcon size="12" class="mr-1">mdi-account-edit</LIcon>
          {{ $t('promptEngineering.variables.existing') }}
        </div>
        <div class="placeholders-container">
          <div
            v-for="v in userVariables"
            :key="'user-' + v.name"
            class="placeholder-item user-variable"
            draggable="true"
            @dragstart="onDragStart(v, $event)"
            @dragend="onDragEnd"
          >
            <div class="placeholder-tag">
              <LIcon size="12" class="drag-handle">mdi-drag-vertical</LIcon>
              <span class="tag-name">{{ formatPlaceholder(v.name) }}</span>
            </div>
            <div v-if="v.content" class="content-preview">
              {{ truncate(v.content, 50) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Extracted Variables (from prompt text) -->
      <div v-if="extractedVariables.length > 0" class="variables-section">
        <div class="section-label">
          <LIcon size="12" class="mr-1">mdi-text-search</LIcon>
          {{ $t('promptEngineering.testing.inPrompt') }}
        </div>
        <div class="placeholders-container">
          <div
            v-for="v in extractedVariablesFiltered"
            :key="'extracted-' + v.name"
            class="placeholder-item extracted-variable"
            :class="{ 'has-value': hasUserValue(v.name) }"
          >
            <div class="placeholder-tag extracted">
              <span class="tag-name">{{ formatPlaceholder(v.name) }}</span>
              <span v-if="v.occurrences > 1" class="occurrence-badge">×{{ v.occurrences }}</span>
            </div>
            <LTag v-if="hasUserValue(v.name)" variant="success" size="sm">
              <LIcon size="10">mdi-check</LIcon>
            </LTag>
            <LTag v-else variant="warning" size="sm">
              {{ $t('promptEngineering.testing.empty') }}
            </LTag>
          </div>
        </div>
      </div>
    </div>

    <!-- Usage Hint -->
    <div v-if="userVariables.length > 0" class="usage-hint">
      <LIcon size="12" class="mr-1">mdi-cursor-move</LIcon>
      <span>{{ $t('promptEngineering.testing.dragHint') }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  promptId: {
    type: [String, Number],
    default: null
  },
  extractedVariables: {
    type: Array,
    default: () => []
  },
  userVariables: {
    type: Array,
    default: () => []
  }
})

const { t } = useI18n()

// Invalid variable names to filter out
const INVALID_NAMES = new Set([
  'undefined', 'null', 'true', 'false', 'NaN', 'Infinity'
])

const VALID_NAME_REGEX = /^[a-zA-Z_][a-zA-Z0-9_]*$/

// Filter valid extracted variables
const extractedVariablesFiltered = computed(() => {
  if (!Array.isArray(props.extractedVariables)) return []
  return props.extractedVariables.filter(v => {
    if (!v || typeof v !== 'object') return false
    if (!v.name || typeof v.name !== 'string') return false
    if (INVALID_NAMES.has(v.name)) return false
    if (!VALID_NAME_REGEX.test(v.name)) return false
    return true
  })
})

// All variables combined
const allVariables = computed(() => {
  return [...props.userVariables, ...extractedVariablesFiltered.value]
})

// Check if a variable has a user-defined value
const hasUserValue = (name) => {
  return props.userVariables.some(v => v.name === name && v.content)
}

// Helper to format placeholder display
const formatPlaceholder = (name) => `{{${name}}}`

// Truncate text for preview
const truncate = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

// Drag handlers
const onDragStart = (variable, event) => {
  event.dataTransfer.setData('text/placeholder', variable.name)
  event.dataTransfer.setData('text/plain', `{{${variable.name}}}`)
  event.dataTransfer.effectAllowed = 'copy'
  event.target.classList.add('dragging')
}

const onDragEnd = (event) => {
  event.target.classList.remove('dragging')
}
</script>

<style scoped>
.placeholder-palette {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.palette-header {
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.palette-title {
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.placeholder-list {
  min-height: 40px;
}

.no-placeholders {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  text-align: center;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 6px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.1);
}

.hint-text {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0;
}

.variables-section {
  margin-bottom: 12px;
}

.section-label {
  display: flex;
  align-items: center;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 6px;
}

.placeholders-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Placeholder Item */
.placeholder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.placeholder-item.user-variable {
  cursor: grab;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.placeholder-item.user-variable:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  transform: translateX(2px);
}

.placeholder-item.user-variable.dragging {
  cursor: grabbing;
  opacity: 0.6;
  transform: scale(0.98);
}

.placeholder-item.extracted-variable {
  border-left: 3px solid rgba(var(--v-theme-on-surface), 0.2);
}

.placeholder-item.extracted-variable.has-value {
  border-left-color: rgb(var(--v-theme-success));
}

.placeholder-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px 4px 4px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.15), rgba(var(--v-theme-primary), 0.08));
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
  border-radius: 4px 2px 4px 2px;
  user-select: none;
}

.placeholder-tag.extracted {
  background: linear-gradient(135deg, rgba(var(--v-theme-on-surface), 0.08), rgba(var(--v-theme-on-surface), 0.04));
  border-color: rgba(var(--v-theme-on-surface), 0.2);
}

.drag-handle {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.tag-name {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.placeholder-tag.extracted .tag-name {
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.occurrence-badge {
  font-size: 0.6rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background: rgba(var(--v-theme-on-surface), 0.1);
  padding: 1px 4px;
  border-radius: 4px;
  margin-left: 2px;
}

.content-preview {
  flex: 1;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.usage-hint {
  display: flex;
  align-items: center;
  font-size: 0.65rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}
</style>
