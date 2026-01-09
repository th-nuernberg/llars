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
            <span class="header-title">Prompt testen</span>
          </div>
          <v-btn icon variant="text" size="small" @click="closeDialog">
            <LIcon>mdi-close</LIcon>
          </v-btn>
        </div>
      </template>

      <div class="dialog-body">
        <!-- Configuration Row -->
        <div class="config-section">
          <div class="config-grid">
            <!-- Model Selection -->
            <div class="config-item">
              <label class="config-label">
                <LIcon size="14" class="mr-1">mdi-brain</LIcon>
                Modell
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
                Temperatur: {{ temperature.toFixed(2) }}
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
                Max Tokens
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

          <!-- Mode Toggles -->
          <div class="mode-toggles">
            <v-chip
              :color="jsonMode ? 'success' : 'default'"
              :variant="jsonMode ? 'flat' : 'outlined'"
              @click="jsonMode = !jsonMode"
              class="mode-chip"
            >
              <LIcon start size="16">mdi-code-json</LIcon>
              JSON Mode
            </v-chip>
            <v-chip
              :color="sngMode ? 'info' : 'default'"
              :variant="sngMode ? 'flat' : 'outlined'"
              @click="sngMode = !sngMode"
              class="mode-chip"
            >
              <LIcon start size="16">mdi-graph</LIcon>
              SNG Visualisierung
            </v-chip>
          </div>
        </div>

        <!-- Examples Section -->
        <div class="examples-section">
          <div class="section-header">
            <LIcon size="16" class="mr-1">mdi-file-document-multiple</LIcon>
            <span class="section-title">Beispieldaten</span>
          </div>
          <div class="examples-chips">
            <v-chip
              v-for="(ex, idx) in examples"
              :key="idx"
              :color="idx === selectedExampleIndex ? 'primary' : 'default'"
              :variant="idx === selectedExampleIndex ? 'flat' : 'outlined'"
              @click="selectExample(idx)"
              class="example-chip"
            >
              {{ ex.name }}
              <LIcon v-if="ex.error" end size="14" color="error">mdi-alert-circle</LIcon>
            </v-chip>
          </div>

          <!-- Example Preview -->
          <v-expand-transition>
            <div v-if="showExamplePreview" class="example-preview">
              <div class="preview-header">
                <span class="preview-title">Vorschau: {{ examples[selectedExampleIndex]?.name }}</span>
                <v-btn
                  icon
                  variant="text"
                  size="x-small"
                  @click="showExamplePreview = false"
                >
                  <LIcon size="16">mdi-chevron-up</LIcon>
                </v-btn>
              </div>
              <pre class="preview-content">{{ selectedExampleFormatted }}</pre>
            </div>
          </v-expand-transition>

          <LBtn
            v-if="!showExamplePreview"
            variant="text"
            size="small"
            prepend-icon="mdi-eye"
            @click="showExamplePreview = true"
          >
            Beispiel anzeigen
          </LBtn>
        </div>

        <!-- JSON Schema (when JSON mode enabled) -->
        <v-expand-transition>
          <div v-if="jsonMode" class="schema-section">
            <div class="section-header">
              <LIcon size="16" class="mr-1">mdi-code-braces</LIcon>
              <span class="section-title">JSON Schema</span>
            </div>
            <v-textarea
              v-model="jsonSchemaInput"
              rows="4"
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
            <span class="section-title">Gesendetes Prompt</span>
            <v-spacer />
            <LBtn
              variant="text"
              size="small"
              :prepend-icon="promptCollapsed ? 'mdi-chevron-down' : 'mdi-chevron-up'"
              @click="promptCollapsed = !promptCollapsed"
            >
              {{ promptCollapsed ? 'Mehr anzeigen' : 'Weniger' }}
            </LBtn>
          </div>
          <div class="prompt-content" v-html="promptHighlighted"></div>
        </div>

        <!-- Response Section -->
        <div class="response-section">
          <div class="section-header">
            <LIcon size="16" class="mr-1">mdi-robot</LIcon>
            <span class="section-title">Antwort</span>
            <v-spacer />
            <LTag v-if="isStreaming" variant="info" size="small">
              <v-progress-circular
                indeterminate
                size="12"
                width="2"
                class="mr-1"
              />
              Generiert...
            </LTag>
            <LTag v-else-if="responseComplete" variant="success" size="small">
              <LIcon start size="12">mdi-check</LIcon>
              Fertig
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
          <div v-if="!sngMode" class="response-container" ref="responseContainer" @scroll="handleScroll">
            <div class="response-content">
              <pre class="response-text">{{ response }}</pre>
              <div v-if="isStreaming" class="typing-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>

          <!-- SNG Visualization -->
          <div v-else class="sng-container">
            <div v-if="isStreaming" class="sng-loading">
              <v-progress-circular indeterminate color="primary" />
              <span class="mt-2">Generiere Graph-Daten...</span>
            </div>
            <template v-else-if="responseComplete">
              <SocialNetworkGraph
                v-if="!parseError && networkJson"
                :data="networkJson"
              />
              <div v-else-if="parseError" class="sng-error">
                <LIcon size="48" color="error">mdi-alert-circle</LIcon>
                <span class="error-text">Fehler: Ungültiges JSON für SocialNetworkGraph</span>
                <pre class="error-detail">{{ response }}</pre>
              </div>
              <div v-else class="sng-empty">
                <LIcon size="48" color="grey">mdi-graph-outline</LIcon>
                <span>Keine Daten zum Plotten verfügbar</span>
              </div>
            </template>
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
            Abbrechen
          </LBtn>
          <LBtn
            v-else
            variant="accent"
            prepend-icon="mdi-refresh"
            @click="regenerate"
          >
            Erneut generieren
          </LBtn>
          <LBtn variant="cancel" @click="closeDialog">
            Schließen
          </LBtn>
        </div>
      </template>
    </LCard>
  </v-dialog>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from 'vue'
import { io } from 'socket.io-client'
import SocialNetworkGraph from './SocialNetworkGraph.vue'
import { sanitizeHtml } from '@/utils/sanitize'
import LlmModelSelect from '@/components/common/LlmModelSelect.vue'

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
  }
})

const emit = defineEmits(['update:modelValue'])

// Socket connection
let socket = null

// Configuration state - load from localStorage if available
const STORAGE_KEY_MODEL = 'llars_test_prompt_model'
const STORAGE_KEY_TEMP = 'llars_test_prompt_temperature'
const STORAGE_KEY_TOKENS = 'llars_test_prompt_max_tokens'

const selectedModel = ref(localStorage.getItem(STORAGE_KEY_MODEL) || '')
const temperature = ref(parseFloat(localStorage.getItem(STORAGE_KEY_TEMP)) || 0.15)
const maxTokens = ref(parseInt(localStorage.getItem(STORAGE_KEY_TOKENS)) || 4096)
const jsonMode = ref(true)
const sngMode = ref(false)
const jsonSchemaInput = ref('{}')

// Example state
const selectedExampleIndex = ref(0)
const showExamplePreview = ref(false)

// Prompt display state
const promptCollapsed = ref(true)

// Response state
const response = ref('')
const isStreaming = ref(false)
const responseComplete = ref(false)
const responseContainer = ref(null)
const follow = ref(true)

// Request tracking to prevent race conditions
let pendingRequest = false
let requestId = 0

// SNG state
const networkJson = ref(null)
const parseError = ref(false)

// Load examples
function formatHistory(data) {
  const requiredTop = ['type', 'chat_id', 'institut_id', 'subject', 'sender', 'total_messages', 'messages']
  for (const key of requiredTop) {
    if (!(key in data)) return { text: '', error: true }
  }
  if (!Array.isArray(data.messages)) return { text: '', error: true }
  const lines = []
  for (const msg of data.messages) {
    const requiredMsg = ['message_id', 'sender', 'content', 'timestamp', 'generated_by']
    for (const mk of requiredMsg) {
      if (!(mk in msg)) return { text: '', error: true }
    }
    const ts = msg.timestamp
    const parts = ts.split(' ')
    if (parts.length !== 2) return { text: '', error: true }
    const [date, time] = parts
    lines.push(`${msg.sender} schrieb am ${date} um ${time}: ${msg.content}`)
  }
  return { text: lines.join('\n\n'), error: false }
}

const exampleModules = import.meta.glob('./examples/*.json', { eager: true })
const examples = Object.entries(exampleModules).map(([path, module]) => {
  const data = module.default || module
  const name = data.subject || data.id || path.split('/').pop().replace('.json', '')
  const { text: formatted, error } = formatHistory(data)
  return { name, data, formatted, error }
})

const selectedExampleFormatted = computed(() => {
  const ex = examples[selectedExampleIndex.value]
  return ex ? ex.formatted : ''
})

// Prompt with example replaced
const replacedPrompt = computed(() => {
  const placeholder = '{{complete_email_history}}'
  const exampleText = selectedExampleFormatted.value
  return props.prompt.split(placeholder).join(exampleText)
})

const collapsedPrompt = computed(() => {
  const text = replacedPrompt.value
  if (text.length <= 200) return text
  const firstPart = text.slice(0, 100)
  const lastPart = text.slice(-100)
  return `${firstPart}\n\n... [${text.length - 200} Zeichen ausgeblendet] ...\n\n${lastPart}`
})

function escapeRegex(str) {
  return str.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')
}

const promptHighlighted = computed(() => {
  const text = promptCollapsed.value ? collapsedPrompt.value : replacedPrompt.value
  const exampleText = selectedExampleFormatted.value

  let htmlText = text.replace(/\n/g, '<br/>')

  if (exampleText) {
    const escapedExample = exampleText.replace(/\n/g, '<br/>')
    const pattern = new RegExp(escapeRegex(escapedExample), 'g')
    htmlText = htmlText.replace(pattern, `<span class="example-highlight">${escapedExample}</span>`)
  }

  return sanitizeHtml(htmlText)
})

// Socket initialization
const socketConnected = ref(false)

function initSocket() {
  if (socket) return

  const username = localStorage.getItem('username') || 'Unbekannter Benutzer'
  const rawBase = import.meta.env.VITE_API_BASE_URL || window.location.origin
  const trimmedBase = String(rawBase || '').replace(/\/+$/, '')
  const socketBase = trimmedBase.endsWith('/api')
    ? trimmedBase.slice(0, -4)
    : (trimmedBase || window.location.origin)

  console.log('[TestPrompt] Connecting to socket at:', socketBase)

  socket = io(socketBase, {
    path: '/socket.io/',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket,
    query: { username },
    headers: { 'Content-Type': 'application/json; charset=utf-8' }
  })

  socket.on('connect', () => {
    console.log('[TestPrompt] Socket connected, id:', socket.id)
    socketConnected.value = true
    // Auto-send prompt when socket connects if dialog is open and request is pending
    if (props.modelValue && pendingRequest) {
      pendingRequest = false
      sendTestPrompt()
    }
  })

  socket.on('disconnect', () => {
    console.log('[TestPrompt] Socket disconnected')
    socketConnected.value = false
  })

  socket.on('connect_error', (error) => {
    console.error('[TestPrompt] Socket connection error:', error)
    isStreaming.value = false
    response.value = 'Verbindungsfehler: ' + error.message
  })

  socket.on('test_prompt_response', (data) => {
    console.log('[TestPrompt] Received chunk:', data.content?.length, 'chars, complete:', data.complete)
    response.value += data.content

    nextTick(() => {
      if (follow.value && responseContainer.value) {
        responseContainer.value.scrollTop = responseContainer.value.scrollHeight
      }
    })

    if (data.complete) {
      isStreaming.value = false
      responseComplete.value = true
      parseSngResponse()
    }
  })
}

function parseSngResponse() {
  if (!sngMode.value) return

  const raw = response.value.trim()
  let jsonText = raw

  // Remove markdown code fences if present
  const fenceMatch = raw.match(/```(?:json)?\n([\s\S]*?)\n```/)
  if (fenceMatch && fenceMatch[1]) {
    jsonText = fenceMatch[1].trim()
  } else if (!raw.startsWith('{') && raw.includes('{')) {
    const first = raw.indexOf('{')
    const last = raw.lastIndexOf('}')
    if (first !== -1 && last !== -1 && last > first) {
      jsonText = raw.slice(first, last + 1)
    }
  }

  try {
    networkJson.value = JSON.parse(jsonText)
    parseError.value = false
  } catch (e) {
    console.error('[TestPrompt] Invalid JSON for SNG:', e)
    parseError.value = true
  }
}

function sendTestPrompt() {
  console.log('[TestPrompt] sendTestPrompt called, socket:', socket ? 'exists' : 'null', 'connected:', socket?.connected)

  // Reset state immediately
  response.value = ''
  isStreaming.value = true
  responseComplete.value = false
  networkJson.value = null
  parseError.value = false
  follow.value = true

  // Increment request ID to track this request
  requestId++
  const currentRequestId = requestId

  if (!socket?.connected) {
    console.log('[TestPrompt] Socket not connected yet, marking request as pending...')
    pendingRequest = true
    return
  }

  const promptText = props.prompt
  console.log('[TestPrompt] Sending test prompt, length:', promptText?.length, 'first 100 chars:', promptText?.slice(0, 100))

  const placeholder = '{{complete_email_history}}'
  const exampleText = selectedExampleFormatted.value
  const promptString = props.prompt.split(placeholder).join(exampleText)

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
    sngMode: sngMode.value,
    model: selectedModel.value,
    temperature: temperature.value,
    maxTokens: maxTokens.value,
    requestId: currentRequestId
  }

  console.log('[TestPrompt] Emitting test_prompt_stream with payload:', {
    ...payload,
    prompt: payload.prompt.slice(0, 100) + '...'
  })

  socket.emit('test_prompt_stream', payload)
}

function selectExample(idx) {
  selectedExampleIndex.value = idx
  if (props.modelValue) {
    sendTestPrompt()
  }
}

function regenerate() {
  sendTestPrompt()
}

function cancelGeneration() {
  console.log('[TestPrompt] Cancelling generation')
  // Increment request ID to ignore any further responses from current request
  requestId++
  pendingRequest = false
  isStreaming.value = false
  responseComplete.value = true
  if (response.value === '') {
    response.value = '[Generierung abgebrochen]'
  } else {
    response.value += '\n\n[Generierung abgebrochen]'
  }
}

function closeDialog() {
  // Cancel any running generation when closing
  if (isStreaming.value) {
    cancelGeneration()
  }
  emit('update:modelValue', false)
}

// Scroll handling
function handleScroll() {
  if (!responseContainer.value) return
  const el = responseContainer.value
  const threshold = 10
  follow.value = el.scrollHeight - el.scrollTop - el.clientHeight <= threshold
}

// Watchers
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    // Reset state when dialog opens
    promptCollapsed.value = true
    pendingRequest = false

    // Initialize socket - will auto-send prompt when connected
    initSocket()

    // Send the prompt - sendTestPrompt handles both connected and not-connected cases
    nextTick(() => {
      sendTestPrompt()
    })
  } else {
    // Dialog closed - cancel any pending request
    pendingRequest = false
  }
})

watch(jsonMode, () => {
  if (props.modelValue) {
    sendTestPrompt()
  }
})

watch(sngMode, () => {
  if (props.modelValue) {
    networkJson.value = null
    parseError.value = false
    sendTestPrompt()
  }
})

// Persist configuration to localStorage
watch(selectedModel, (val) => {
  if (val) {
    localStorage.setItem(STORAGE_KEY_MODEL, val)
  }
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
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: calc(90vh - 140px);
  overflow-y: auto;
  padding: 4px;
}

/* Configuration Section */
.config-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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

/* Examples Section */
.examples-section {
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

.examples-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.example-chip {
  cursor: pointer;
  transition: all 0.2s ease;
}

.example-preview {
  background: rgba(var(--v-theme-primary), 0.06);
  border-radius: 8px;
  padding: 12px;
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.preview-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.preview-content {
  font-size: 0.8rem;
  line-height: 1.5;
  white-space: pre-wrap;
  max-height: 150px;
  overflow-y: auto;
  color: rgba(var(--v-theme-on-surface), 0.8);
  font-family: 'SF Mono', Monaco, Consolas, monospace;
}

/* Schema Section */
.schema-section {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border-radius: 12px;
  padding: 16px;
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
  max-height: 200px;
  overflow-y: auto;
}

:deep(.example-highlight) {
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
}

.response-container {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 8px;
  padding: 16px;
  max-height: 300px;
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

.typing-indicator .dot:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator .dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* SNG Container */
.sng-container {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sng-loading,
.sng-error,
.sng-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  text-align: center;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.error-text {
  color: rgb(var(--v-theme-error));
  font-weight: 500;
}

.error-detail {
  font-size: 0.75rem;
  max-width: 100%;
  overflow-x: auto;
  background: rgba(var(--v-theme-error), 0.1);
  padding: 8px;
  border-radius: 4px;
  margin-top: 8px;
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
.response-container::-webkit-scrollbar,
.preview-content::-webkit-scrollbar,
.prompt-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-body::-webkit-scrollbar-track,
.response-container::-webkit-scrollbar-track,
.preview-content::-webkit-scrollbar-track,
.prompt-content::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-body::-webkit-scrollbar-thumb,
.response-container::-webkit-scrollbar-thumb,
.preview-content::-webkit-scrollbar-thumb,
.prompt-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 3px;
}

.dialog-body::-webkit-scrollbar-thumb:hover,
.response-container::-webkit-scrollbar-thumb:hover,
.preview-content::-webkit-scrollbar-thumb:hover,
.prompt-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.25);
}
</style>
