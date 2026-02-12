<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="emit('update:modelValue', $event)"
    max-width="1200"
    persistent
    scrollable
  >
    <LCard class="test-prompt-card">
      <template #header>
        <div class="dialog-header">
          <div class="header-left">
            <LIcon size="24" color="primary" class="mr-2">mdi-rocket-launch</LIcon>
            <span class="header-title">{{ $t('promptEngineering.testPrompt.title') }}</span>
            <LTag v-if="variableStats.total > 0" variant="info" size="small" class="ml-2">
              {{ variableStats.filled }}/{{ variableStats.total }}
              {{ $t('promptEngineering.testing.variables') }}
            </LTag>
          </div>
          <v-btn icon variant="text" size="small" @click="closeDialog">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </div>
      </template>

      <div class="dialog-body">
        <div class="main-layout">
          <!-- Left Panel: Variables Overview -->
          <div class="variables-panel">
            <div class="panel-header">
              <LIcon size="18" class="mr-2">mdi-variable</LIcon>
              <span class="panel-title">{{ $t('promptEngineering.testing.variables') }}</span>
            </div>

            <div class="variables-content">
              <!-- No Variables -->
              <div v-if="userVariables.length === 0 && extractedVariables.length === 0" class="no-variables">
                <LIcon size="48" color="grey" class="mb-3">mdi-variable-box</LIcon>
                <p class="no-variables-title">{{ $t('promptEngineering.testing.noVariables') }}</p>
                <p class="no-variables-hint">{{ $t('promptEngineering.testing.noVariablesHint') }}</p>
              </div>

              <!-- Variables List -->
              <div v-else class="variables-list">
                <div
                  v-for="v in displayVariables"
                  :key="v.name"
                  class="variable-item"
                  :class="{ 'has-value': v.hasValue, 'missing-value': !v.hasValue }"
                >
                  <div class="variable-header">
                    <span class="variable-tag">{{ formatTag(v.name) }}</span>
                    <LTag v-if="v.hasValue" variant="success" size="sm">
                      <LIcon size="10">mdi-check</LIcon>
                    </LTag>
                    <LTag v-else variant="warning" size="sm">
                      {{ $t('promptEngineering.testing.empty') }}
                    </LTag>
                  </div>
                  <div v-if="v.content" class="variable-value">
                    {{ truncate(v.content, 100) }}
                  </div>
                </div>
              </div>

              <!-- Missing Variables Warning -->
              <div v-if="missingVariables.length > 0" class="missing-warning">
                <LIcon size="16" color="warning" class="mr-2">mdi-alert</LIcon>
                <span>{{ $t('promptEngineering.testing.variablesRemaining', { count: missingVariables.length }) }}</span>
              </div>
            </div>
          </div>

          <!-- Right Panel: Config + Response -->
          <div class="response-panel">
            <!-- Configuration Section -->
            <div class="config-section">
              <div class="config-grid">
                <!-- Model Selection -->
                <div class="config-item">
                  <label class="config-label">
                    <LIcon size="14" class="mr-1">mdi-brain</LIcon>
                    {{ $t('promptEngineering.testPrompt.model') }}
                  </label>
                  <LlmModelSelect
                    v-model="selectedModel"
                    label=""
                    prepend-icon=""
                    density="compact"
                    :clearable="false"
                    :hide-details="true"
                    class="config-select"
                  />
                </div>

                <!-- Temperature -->
                <div class="config-item">
                  <label class="config-label">
                    <LIcon size="14" class="mr-1">mdi-thermometer</LIcon>
                    {{ $t('promptEngineering.testPrompt.temperature') }}: {{ temperature.toFixed(2) }}
                  </label>
                  <v-slider
                    v-model="temperature"
                    :min="0"
                    :max="1"
                    :step="0.05"
                    density="compact"
                    hide-details
                    color="primary"
                  />
                </div>

                <!-- Max Tokens -->
                <div class="config-item">
                  <label class="config-label">
                    <LIcon size="14" class="mr-1">mdi-counter</LIcon>
                    {{ $t('promptEngineering.testPrompt.maxTokens') }}
                  </label>
                  <v-text-field
                    v-model.number="maxTokens"
                    type="number"
                    density="compact"
                    variant="outlined"
                    hide-details
                    :min="100"
                    :max="8192"
                    class="config-input"
                  />
                </div>
              </div>

              <!-- Mode Toggles (hidden for cleaner UI) -->
              <div v-if="false" class="mode-toggles">
                <v-chip
                  :color="jsonMode ? 'success' : 'default'"
                  :variant="jsonMode ? 'flat' : 'outlined'"
                  @click="jsonMode = !jsonMode"
                  class="mode-chip"
                >
                  <LIcon start size="16">mdi-code-json</LIcon>
                  {{ $t('promptEngineering.testPrompt.jsonMode') }}
                </v-chip>
              </div>
            </div>

            <!-- JSON Schema (when JSON mode enabled) -->
            <v-expand-transition>
              <div v-if="jsonMode" class="schema-section">
                <div class="section-header">
                  <LIcon size="16" class="mr-1">mdi-code-braces</LIcon>
                  <span class="section-title">{{ $t('promptEngineering.testPrompt.jsonSchema') }}</span>
                </div>
                <v-textarea
                  v-model="jsonSchemaInput"
                  rows="3"
                  variant="outlined"
                  density="compact"
                  placeholder="{}"
                  hide-details
                  class="schema-input"
                />
              </div>
            </v-expand-transition>

            <!-- Sent Prompt Section -->
            <div class="prompt-section">
              <div class="section-header">
                <LIcon size="16" class="mr-1">mdi-message-text</LIcon>
                <span class="section-title">{{ $t('promptEngineering.testPrompt.sentPrompt') }}</span>
                <v-spacer />
                <LBtn
                  variant="text"
                  size="small"
                  :prepend-icon="promptCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up'"
                  @click="promptCollapsed = !promptCollapsed"
                >
                  {{ promptCollapsed ? $t('promptEngineering.testPrompt.showMore') : $t('promptEngineering.testPrompt.showLess') }}
                </LBtn>
              </div>
              <div class="prompt-content" v-html="promptHighlighted"></div>
            </div>

            <!-- Response Section -->
            <div class="response-section">
              <div class="section-header">
                <LIcon size="16" class="mr-1">mdi-robot</LIcon>
                <span class="section-title">{{ $t('promptEngineering.testPrompt.response') }}</span>
                <v-spacer />
                <LTag v-if="isStreaming" variant="info" size="small">
                  <v-progress-circular
                    indeterminate
                    size="12"
                    width="2"
                    class="mr-1"
                  />
                  {{ $t('promptEngineering.testPrompt.generating') }}
                </LTag>
                <LTag v-else-if="responseComplete" variant="success" size="small">
                  <LIcon start size="12">mdi-check</LIcon>
                  {{ $t('promptEngineering.testPrompt.done') }}
                </LTag>
              </div>

              <!-- Progress Bar -->
              <v-progress-linear
                v-if="isStreaming"
                indeterminate
                color="primary"
                height="3"
                class="mb-3"
              />

              <!-- Response Content -->
              <div class="response-container" ref="responseContainer" @scroll="handleScroll">
                <div class="response-content">
                  <pre class="response-text">{{ response }}</pre>
                  <div v-if="isStreaming" class="typing-indicator">
                    <span class="dot"></span>
                    <span class="dot"></span>
                    <span class="dot"></span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #actions>
        <div class="dialog-actions">
          <LBtn
            v-if="isStreaming"
            variant="danger"
            prepend-icon="mdi-stop"
            @click="cancelGeneration"
          >
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn
            v-else
            variant="accent"
            prepend-icon="mdi-refresh"
            @click="regenerate"
          >
            {{ $t('promptEngineering.testPrompt.regenerate') }}
          </LBtn>
          <LBtn variant="cancel" @click="closeDialog">
            {{ $t('common.close') }}
          </LBtn>
        </div>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import { sanitizeHtml } from '@/utils/sanitize'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'
import { useI18n } from 'vue-i18n'

// Socket.IO configuration
const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true
  },
  prompt: {
    type: String,
    required: true
  },
  promptId: {
    type: [String, Number],
    default: null
  },
  // Collaborative variables from parent (synced via Yjs)
  variables: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])
const { t } = useI18n()

// Socket connection
let socket = null

// Storage keys for configuration (not variables)
const STORAGE_KEY_MODEL = 'llars_test_prompt_model'
const STORAGE_KEY_TEMP = 'llars_test_prompt_temperature'
const STORAGE_KEY_TOKENS = 'llars_test_prompt_max_tokens'

// Use collaborative variables from props
const userVariables = computed(() => props.variables)

// Extract variables from prompt text
const VARIABLE_REGEX = /\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}/g
const INVALID_NAMES = new Set(['undefined', 'null', 'true', 'false', 'NaN', 'Infinity'])

const extractedVariables = computed(() => {
  const found = new Map()
  let match
  const regex = new RegExp(VARIABLE_REGEX.source, 'g')

  while ((match = regex.exec(props.prompt)) !== null) {
    const name = match[1]
    if (INVALID_NAMES.has(name)) continue

    if (!found.has(name)) {
      found.set(name, { name, occurrences: 1 })
    } else {
      found.get(name).occurrences++
    }
  }

  return Array.from(found.values())
})

// Display variables with their values
const displayVariables = computed(() => {
  return extractedVariables.value.map(v => {
    const userVar = userVariables.value.find(uv => uv.name === v.name)
    return {
      name: v.name,
      occurrences: v.occurrences,
      content: userVar?.content || '',
      hasValue: !!(userVar?.content)
    }
  })
})

// Missing variables (in prompt but no value)
const missingVariables = computed(() => {
  return displayVariables.value.filter(v => !v.hasValue)
})

// Variable stats
const variableStats = computed(() => ({
  total: extractedVariables.value.length,
  filled: displayVariables.value.filter(v => v.hasValue).length
}))

// Resolve prompt by replacing variables
const resolvedPrompt = computed(() => {
  let result = props.prompt

  for (const userVar of userVariables.value) {
    if (userVar.name && userVar.content) {
      const placeholder = new RegExp(`\\{\\{${userVar.name}\\}\\}`, 'g')
      result = result.replace(placeholder, userVar.content)
    }
  }

  return result
})

// Configuration state
const selectedModel = ref(localStorage.getItem(STORAGE_KEY_MODEL) || '')
const temperature = ref(parseFloat(localStorage.getItem(STORAGE_KEY_TEMP)) || 0.15)
const maxTokens = ref(parseInt(localStorage.getItem(STORAGE_KEY_TOKENS)) || 4096)
const jsonMode = ref(false)
const jsonSchemaInput = ref('{}')

// Prompt display state
const promptCollapsed = ref(true)

// Helpers
const formatTag = (name) => `{{${name}}}`

const truncate = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

const collapsedPrompt = computed(() => {
  const text = resolvedPrompt.value
  if (text.length <= 200) return text
  const firstPart = text.slice(0, 100)
  const lastPart = text.slice(-100)
  const hiddenSummary = t('promptEngineering.testPrompt.hiddenSummary', { count: text.length - 200 })
  return `${firstPart}\n\n${hiddenSummary}\n\n${lastPart}`
})

const promptHighlighted = computed(() => {
  const text = promptCollapsed.value ? collapsedPrompt.value : resolvedPrompt.value
  let htmlText = (text || '').replace(/\n/g, '<br/>')

  // Highlight replaced variable values
  for (const userVar of userVariables.value) {
    if (userVar.content) {
      const escapedContent = userVar.content.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const pattern = new RegExp(escapedContent.replace(/\n/g, '<br/>'), 'g')
      htmlText = htmlText.replace(pattern, `<span class="variable-highlight">${userVar.content.replace(/\n/g, '<br/>')}</span>`)
    }
  }

  return sanitizeHtml(htmlText)
})

// Response state
const response = ref('')
const isStreaming = ref(false)
const responseComplete = ref(false)
const responseContainer = ref(null)
const follow = ref(true)

// Request tracking
let pendingRequest = false
let requestId = 0

// Socket initialization
const socketConnected = ref(false)

function initSocket() {
  if (socket) return

  const username = localStorage.getItem('username') || t('promptEngineering.user.unknown')
  const rawBase = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const trimmedBase = String(rawBase || '').replace(/\/+$/, '')
  const socketBase = trimmedBase.endsWith('/api')
    ? trimmedBase.slice(0, -4)
    : (trimmedBase || window.location.origin)

  socket = io(socketBase, {
    path: '/socket.io/',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket,
    query: { username },
    headers: { 'Content-Type': 'application/json; charset=utf-8' }
  })

  socket.on('connect', () => {
    socketConnected.value = true
    if (props.modelValue && pendingRequest) {
      pendingRequest = false
      sendTestPrompt()
    }
  })

  socket.on('disconnect', () => {
    socketConnected.value = false
  })

  socket.on('connect_error', (error) => {
    isStreaming.value = false
    response.value = t('promptEngineering.testPrompt.connectionError', { message: error.message })
  })

  socket.on('test_prompt_response', (data) => {
    response.value += data.content

    nextTick(() => {
      if (follow.value && responseContainer.value) {
        responseContainer.value.scrollTop = responseContainer.value.scrollHeight
      }
    })

    if (data.complete) {
      isStreaming.value = false
      responseComplete.value = true
    }
  })
}

function sendTestPrompt() {
  response.value = ''
  isStreaming.value = true
  responseComplete.value = false
  follow.value = true

  requestId++
  const currentRequestId = requestId

  if (!socket?.connected) {
    pendingRequest = true
    return
  }

  const promptString = resolvedPrompt.value

  let schemaObj = {}
  if (jsonMode.value) {
    try {
      schemaObj = JSON.parse(jsonSchemaInput.value)
    } catch (e) {
      console.error('[TestPrompt] Invalid JSON Schema:', e)
    }
  }

  const payload = {
    prompt: promptString,
    jsonMode: jsonMode.value,
    schema: schemaObj,
    sngMode: false,
    model: selectedModel.value,
    temperature: temperature.value,
    maxTokens: maxTokens.value,
    requestId: currentRequestId
  }

  socket.emit('test_prompt_stream', payload)
}

function regenerate() {
  sendTestPrompt()
}

function cancelGeneration() {
  requestId++
  pendingRequest = false
  isStreaming.value = false
  responseComplete.value = true
  const canceledMessage = t('promptEngineering.testPrompt.generationCanceled')
  if (response.value === '') {
    response.value = canceledMessage
  } else {
    response.value += `\n\n${canceledMessage}`
  }
}

function closeDialog() {
  if (isStreaming.value) {
    cancelGeneration()
  }
  emit('update:modelValue', false)
}

function handleScroll() {
  if (!responseContainer.value) return
  const el = responseContainer.value
  const threshold = 10
  follow.value = el.scrollHeight - el.scrollTop - el.clientHeight <= threshold
}

// Watchers
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    promptCollapsed.value = true
    pendingRequest = false
    initSocket()
    nextTick(() => {
      sendTestPrompt()
    })
  } else {
    pendingRequest = false
  }
})

// Persist configuration to localStorage
watch(selectedModel, (val) => {
  if (val) localStorage.setItem(STORAGE_KEY_MODEL, val)
})

watch(temperature, (val) => {
  localStorage.setItem(STORAGE_KEY_TEMP, String(val))
})

watch(maxTokens, (val) => {
  localStorage.setItem(STORAGE_KEY_TOKENS, String(val))
})

onMounted(() => {
  if (props.modelValue) {
    initSocket()
  }
})

onUnmounted(() => {
  if (socket) {
    socket.disconnect()
    socket = null
  }
})
</script>

<style scoped>
.test-prompt-card {
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
  color: rgb(var(--v-theme-on-surface));
}

.dialog-body {
  max-height: calc(90vh - 140px);
  overflow-y: auto;
  padding: 4px;
}

/* Main Layout */
.main-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 16px;
  min-height: 450px;
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }
}

/* Variables Panel */
.variables-panel {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-on-surface), 0.02);
}

.panel-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.variables-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.no-variables {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px;
  text-align: center;
}

.no-variables-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.no-variables-hint {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.variables-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.variable-item {
  padding: 10px 12px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  border-left: 3px solid rgba(var(--v-theme-on-surface), 0.2);
}

.variable-item.has-value {
  border-left-color: rgb(var(--v-theme-success));
}

.variable-item.missing-value {
  border-left-color: rgb(var(--v-theme-warning));
}

.variable-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.variable-tag {
  font-family: 'Roboto Mono', monospace;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

.variable-value {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}

.missing-warning {
  display: flex;
  align-items: center;
  padding: 12px;
  background: rgba(var(--v-theme-warning), 0.1);
  border-radius: 8px;
  margin-top: 12px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Response Panel */
.response-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Configuration Section */
.config-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 12px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.config-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  display: flex;
  align-items: center;
}

.config-select,
.config-input {
  font-size: 0.9rem;
}

.mode-toggles {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mode-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

/* Schema Section */
.schema-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.section-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.schema-input {
  font-family: 'SF Mono', Monaco, Consolas, monospace;
}

/* Prompt Section */
.prompt-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
}

.prompt-content {
  font-size: 0.85rem;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.8);
  background: rgba(var(--v-theme-on-surface), 0.03);
  padding: 12px;
  border-radius: 8px;
  max-height: 150px;
  overflow-y: auto;
}

:deep(.variable-highlight) {
  background-color: rgba(var(--v-theme-success), 0.2);
  border-radius: 2px;
  padding: 0 2px;
}

/* Response Section */
.response-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
  flex: 1;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.response-container {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 16px;
  flex: 1;
  max-height: 500px;
  overflow-y: auto;
}

.response-content {
  position: relative;
}

.response-text {
  font-size: 0.9rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: rgb(var(--v-theme-on-surface));
  font-family: 'SF Mono', Monaco, Consolas, monospace;
}

/* Typing Indicator */
.typing-indicator {
  display: inline-flex;
  gap: 4px;
  padding: 4px 0;
}

.typing-indicator .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgb(var(--v-theme-primary));
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

/* Dialog Actions */
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

/* Scrollbar Styling */
.dialog-body::-webkit-scrollbar,
.variables-content::-webkit-scrollbar,
.response-container::-webkit-scrollbar,
.prompt-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-body::-webkit-scrollbar-track,
.variables-content::-webkit-scrollbar-track,
.response-container::-webkit-scrollbar-track,
.prompt-content::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-body::-webkit-scrollbar-thumb,
.variables-content::-webkit-scrollbar-thumb,
.response-container::-webkit-scrollbar-thumb,
.prompt-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}
</style>
