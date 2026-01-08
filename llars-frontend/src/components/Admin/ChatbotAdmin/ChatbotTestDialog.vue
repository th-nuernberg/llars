<template>
  <v-dialog
    :model-value="modelValue"
    max-width="800"
    scrollable
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card class="d-flex flex-column" style="height: 700px">
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between bg-primary">
        <div class="d-flex align-center">
          <v-avatar
            :color="chatbot?.color || 'primary'"
            size="32"
            class="mr-3"
          >
            <LIcon color="white" size="20">{{ chatbot?.icon || 'mdi-robot' }}</LIcon>
          </v-avatar>
          <div>
            <div>{{ chatbot?.display_name || 'Chatbot Test' }}</div>
            <v-chip size="x-small" color="warning" variant="flat" class="mt-1">
              TEST-MODUS
            </v-chip>
          </div>
        </div>
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-fullscreen"
            variant="text"
            @click="openInFullScreen"
          >
            <v-tooltip activator="parent" location="bottom">
              Vollbild öffnen
            </v-tooltip>
          </v-btn>
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="closeDialog"
          />
        </div>
      </v-card-title>

      <!-- Messages Area -->
      <v-card-text
        ref="messagesContainer"
        class="flex-grow-1 overflow-y-auto pa-4"
        style="background: rgba(var(--v-theme-surface-variant), 0.3)"
      >
        <!-- Welcome Message -->
        <div v-if="messages.length === 0 && chatbot?.welcome_message" class="message-wrapper assistant">
          <div class="message assistant-message">
            <div class="message-content">{{ chatbot.welcome_message }}</div>
          </div>
        </div>

        <!-- Messages -->
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-wrapper"
          :class="[message.role, { 'system-info': message.isSystemInfo }]"
        >
          <div class="message" :class="[`${message.role}-message`, { 'system-info-message': message.isSystemInfo }]">
            <div class="message-header" v-if="message.role === 'assistant'">
              <v-avatar :color="chatbot?.color || 'primary'" size="24" class="mr-2">
                <LIcon color="white" size="16">{{ chatbot?.icon || 'mdi-robot' }}</LIcon>
              </v-avatar>
              <span class="text-caption">{{ chatbot?.display_name }}</span>
            </div>
            <div class="message-content">{{ message.content }}</div>

            <!-- Sources -->
            <div v-if="message.sources && message.sources.length > 0" class="sources mt-2">
              <v-divider class="mb-2" />
              <div class="text-caption text-medium-emphasis mb-1">
                <LIcon size="14" class="mr-1">mdi-file-document</LIcon>
                Quellen:
              </div>
              <v-chip
                v-for="(source, i) in message.sources"
                :key="i"
                size="x-small"
                variant="outlined"
                class="mr-1 mb-1"
                @click="showSourceDetail(source)"
              >
                <span class="font-weight-bold mr-1">[{{ source.footnote_id || (i + 1) }}]</span>
                <span class="text-truncate" style="max-width: 240px;">
                  {{ source.title || source.filename || 'Quelle' }}
                </span>
                <v-tooltip activator="parent" location="top">
                  {{ source.title || source.filename || 'Quelle' }}
                </v-tooltip>
              </v-chip>
            </div>

            <!-- Metadata -->
            <div v-if="message.metadata" class="metadata mt-2">
              <div class="text-caption text-medium-emphasis">
                <LIcon size="12">mdi-clock-outline</LIcon>
                {{ message.metadata.response_time }}ms
                <span v-if="message.metadata.tokens" class="ml-2">
                  <LIcon size="12">mdi-counter</LIcon>
                  {{ message.metadata.tokens }} Tokens
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="loading" class="message-wrapper assistant">
          <div class="message assistant-message">
            <v-progress-circular
              indeterminate
              size="20"
              width="2"
              color="primary"
              class="mr-2"
            />
            <span class="text-medium-emphasis">Antwortet...</span>
          </div>
        </div>
      </v-card-text>

      <!-- Input Area -->
      <v-divider />
      <v-card-actions class="pa-4">
        <v-text-field
          v-model="inputMessage"
          placeholder="Nachricht eingeben..."
          variant="outlined"
          density="comfortable"
          hide-details
          @keyup.enter="sendMessage"
          :disabled="loading"
        >
          <template #append-inner>
            <v-btn
              icon="mdi-send"
              color="primary"
              variant="text"
              :disabled="!inputMessage.trim() || loading"
              @click="sendMessage"
            />
          </template>
        </v-text-field>
      </v-card-actions>

      <!-- Footer Stats -->
      <v-card-text class="py-2 px-4 bg-surface-variant">
        <div class="d-flex justify-space-between align-center text-caption text-medium-emphasis">
          <div class="d-flex gap-4">
            <div>
              <LIcon size="14">mdi-message-text</LIcon>
              {{ messages.length }} Nachrichten
            </div>
            <div v-if="totalResponseTime > 0">
              <LIcon size="14">mdi-clock-outline</LIcon>
              Ø {{ averageResponseTime }}ms
            </div>
            <div v-if="totalTokens > 0">
              <LIcon size="14">mdi-counter</LIcon>
              {{ totalTokens }} Tokens gesamt
            </div>
          </div>
          <v-btn
            size="x-small"
            variant="text"
            :icon="showSettings ? 'mdi-chevron-down' : 'mdi-cog'"
            @click="showSettings = !showSettings"
          >
            <v-tooltip activator="parent" location="top">
              Test-Einstellungen
            </v-tooltip>
          </v-btn>
        </div>

        <!-- Admin Test Settings Panel -->
        <v-expand-transition>
          <div v-if="showSettings" class="mt-4 pt-4" style="border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12)">
            <v-row dense>
              <v-col cols="12" md="6">
                <v-slider
                  v-model="testSettings.temperature"
                  label="Temperature"
                  min="0"
                  max="2"
                  step="0.1"
                  thumb-label
                  hide-details
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-slider
                  v-model="testSettings.maxTokens"
                  label="Max Tokens"
                  min="100"
                  max="4096"
                  step="100"
                  thumb-label
                  hide-details
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-slider
                  v-model="testSettings.retrievalK"
                  label="RAG Top-K"
                  min="1"
                  max="10"
                  step="1"
                  thumb-label
                  hide-details
                  density="compact"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-slider
                  v-model="testSettings.minRelevance"
                  label="Min Relevanz"
                  min="0"
                  max="1"
                  step="0.05"
                  thumb-label
                  hide-details
                  density="compact"
                />
              </v-col>
            </v-row>
            <v-row dense class="mt-2">
              <v-col cols="12">
                <v-textarea
                  v-model="testSettings.systemPromptOverride"
                  label="System Prompt Override (leer = Original verwenden)"
                  variant="outlined"
                  density="compact"
                  rows="2"
                  hide-details
                />
              </v-col>
            </v-row>
            <div class="d-flex justify-end mt-2">
              <v-btn
                size="small"
                variant="text"
                @click="resetSettings"
              >
                Zurücksetzen
              </v-btn>
              <v-btn
                size="small"
                color="primary"
                variant="tonal"
                class="ml-2"
                @click="applySettings"
              >
                Anwenden
              </v-btn>
            </div>
          </div>
        </v-expand-transition>
      </v-card-text>
    </v-card>

    <!-- Source Detail Dialog -->
    <v-dialog v-model="sourceDialog.show" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-chip v-if="sourceDialog.source?.footnote_id" size="small" color="primary" class="mr-2">
            [{{ sourceDialog.source.footnote_id }}]
          </v-chip>
          {{ sourceDialog.source?.title || sourceDialog.source?.filename || 'Quelle' }}
          <v-spacer />
          <LIconBtn icon="mdi-close" @click="sourceDialog.show = false" />
        </v-card-title>
        <v-card-subtitle v-if="sourceDialog.source?.collection_name" class="d-flex align-center">
          <LIcon size="14" class="mr-1">mdi-folder</LIcon>
          {{ sourceDialog.source.collection_name }}
          <v-chip v-if="sourceDialog.source?.relevance !== undefined" size="x-small" class="ml-2" color="success" variant="tonal">
            {{ ((sourceDialog.source.relevance || 0) * 100).toFixed(0) }}% relevant
          </v-chip>
        </v-card-subtitle>
        <v-divider />
        <v-card-text class="source-excerpt">
          {{ sourceDialog.source?.excerpt || '-' }}
        </v-card-text>
        <v-card-actions>
          <v-btn
            v-if="sourceDialog.source?.download_url"
            :href="sourceDialog.source.download_url"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="tonal"
          >
            <LIcon start>mdi-download</LIcon>
            Dokument
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="sourceDialog.show = false">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3500">
      {{ snackbar.text }}
    </v-snackbar>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import axios from 'axios'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const props = defineProps({
  modelValue: Boolean,
  chatbot: Object
})

const emit = defineEmits(['update:modelValue'])

// State
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const showSettings = ref(false)

// Source detail dialog
const sourceDialog = ref({
  show: false,
  source: null
})

// Snackbar
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Admin Test Settings
const testSettings = ref({
  temperature: 0.7,
  maxTokens: 2048,
  retrievalK: 4,
  minRelevance: 0.3,
  systemPromptOverride: ''
})

const activeSettings = ref(null) // Applied settings for testing

// Computed
const totalResponseTime = computed(() => {
  return messages.value
    .filter(m => m.metadata?.response_time)
    .reduce((sum, m) => sum + m.metadata.response_time, 0)
})

const averageResponseTime = computed(() => {
  const assistantMessages = messages.value.filter(m => m.role === 'assistant' && m.metadata?.response_time)
  if (assistantMessages.length === 0) return 0
  return Math.round(totalResponseTime.value / assistantMessages.length)
})

const totalTokens = computed(() => {
  return messages.value
    .filter(m => m.metadata?.tokens)
    .reduce((sum, m) => sum + m.metadata.tokens, 0)
})

// Methods
async function sendMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''

  // Add user message
  messages.value.push({
    role: 'user',
    content: userMessage
  })

  scrollToBottom()
  loading.value = true

  try {
    const startTime = performance.now()

    const streamingRequest = buildRequestData(userMessage, true)

    const streamed = await streamTestMessage(startTime, streamingRequest)
    if (streamed) {
      return
    }

    const requestData = buildRequestData(userMessage, false)

    const response = await axios.post(`/api/chatbots/${props.chatbot.id}/test`, requestData)

    const endTime = performance.now()
    const responseTime = Math.round(endTime - startTime)

    if (response.data.success) {
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources || [],
        metadata: {
          response_time: responseTime,
          tokens: (response.data.tokens && response.data.tokens.output !== undefined)
            ? response.data.tokens.output
            : (response.data.tokens ?? null)
        }
      }
      messages.value.push(assistantMessage)
    } else {
      // Error message
      messages.value.push({
        role: 'assistant',
        content: props.chatbot?.fallback_message || 'Entschuldigung, es ist ein Fehler aufgetreten.',
        metadata: { response_time: responseTime }
      })
    }
  } catch (error) {
    console.error('Error sending message:', error)
    messages.value.push({
      role: 'assistant',
      content: 'Fehler bei der Kommunikation mit dem Server.'
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function streamTestMessage(startTime, requestData) {
  let assistantMessage = null
  try {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    const response = await fetch(`/api/chatbots/${props.chatbot.id}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify(requestData)
    })

    if (!response.ok || !response.body) {
      return false
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    assistantMessage = {
      role: 'assistant',
      content: '',
      sources: [],
      metadata: null
    }
    messages.value.push(assistantMessage)

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        const line = part.trim()
        if (!line.startsWith('data:')) continue
        try {
          const payload = JSON.parse(line.replace(/^data:\s*/, ''))

          if (payload.delta) {
            assistantMessage.content += payload.delta
            scrollToBottom()
          }

          if (payload.done) {
            assistantMessage.sources = payload.sources || []
            assistantMessage.metadata = {
              response_time: payload.response_time_ms || Math.round(performance.now() - startTime),
              tokens: (payload.tokens && payload.tokens.output !== undefined)
                ? payload.tokens.output
                : (payload.tokens ?? null)
            }
            loading.value = false
            scrollToBottom()
            return true
          }

          if (payload.error) {
            throw new Error(payload.error)
          }
        } catch (e) {
          console.error('Failed to parse stream chunk', e, line)
        }
      }
    }

    // Process any remaining buffered data
    if (buffer.trim().startsWith('data:')) {
      try {
        const payload = JSON.parse(buffer.replace(/^data:\s*/, ''))
        if (payload.delta) {
          assistantMessage.content += payload.delta
        }
        if (payload.done) {
          assistantMessage.sources = payload.sources || []
          assistantMessage.metadata = {
            response_time: payload.response_time_ms || Math.round(performance.now() - startTime),
            tokens: (payload.tokens && payload.tokens.output !== undefined)
              ? payload.tokens.output
              : (payload.tokens ?? null)
          }
        }
      } catch (e) {
        console.error('Failed to parse final stream chunk', e, buffer)
      }
    }

    loading.value = false
    scrollToBottom()
    return true
  } catch (error) {
    console.error('Streaming test message failed:', error)
    if (assistantMessage && assistantMessage.content.length === 0) {
      messages.value.pop()
    }
    // Let caller fall back to non-streaming path
    return false
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

function closeDialog() {
  emit('update:modelValue', false)
}

function showSourceDetail(source) {
  sourceDialog.value = { show: true, source }
}

function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

function openInFullScreen() {
  if (!props.chatbot?.id) return

  try {
    const sessionId = crypto.randomUUID()
    const converted = messages.value
      .filter(m => !m.isSystemInfo && (m.role === 'user' || m.role === 'assistant'))
      .map((m, idx) => ({
        id: Date.now() + idx,
        content: m.content,
        sender: m.role === 'assistant' ? 'bot' : 'user',
        timestamp: new Date().toLocaleTimeString(),
        streaming: false,
        ...(m.sources ? { sources: m.sources } : {})
      }))

    localStorage.setItem(`chat_${props.chatbot.id}`, JSON.stringify({
      messages: converted,
      sessionId
    }))

    window.location.href = `/chat?chatbot_id=${props.chatbot.id}`
  } catch (e) {
    console.error('Failed to open chat in fullscreen:', e)
    showSnackbar('Konnte Vollbild nicht öffnen', 'error')
  }
}

function resetChat() {
  messages.value = []
  inputMessage.value = ''
}

function resetSettings() {
  if (props.chatbot) {
    testSettings.value = {
      temperature: props.chatbot.temperature || 0.7,
      maxTokens: props.chatbot.max_tokens || 2048,
      retrievalK: props.chatbot.rag_retrieval_k || 4,
      minRelevance: props.chatbot.rag_min_relevance || 0.3,
      systemPromptOverride: ''
    }
  }
  activeSettings.value = null
}

function applySettings() {
  activeSettings.value = { ...testSettings.value }
  messages.value.push({
    role: 'system',
    content: `[Test-Einstellungen angewendet: Temperature=${activeSettings.value.temperature}, MaxTokens=${activeSettings.value.maxTokens}, RAG-K=${activeSettings.value.retrievalK}]`,
    isSystemInfo: true
  })
  scrollToBottom()
}

// Watch for dialog open/close
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    resetChat()
    resetSettings()
    showSettings.value = false
  }
})

function buildRequestData(userMessage, includeStream = false) {
  const data = {
    message: userMessage,
    conversation_history: messages.value.filter(m => !m.isSystemInfo).slice(0, -1)
  }

  if (activeSettings.value) {
    data.test_settings = {
      temperature: activeSettings.value.temperature,
      max_tokens: activeSettings.value.maxTokens,
      retrieval_k: activeSettings.value.retrievalK,
      min_relevance: activeSettings.value.minRelevance,
      system_prompt_override: activeSettings.value.systemPromptOverride || null
    }
  }

  if (includeStream) {
    data.stream = true
  }

  return data
}
</script>

<style scoped>
.message-wrapper {
  margin-bottom: 16px;
  display: flex;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.message-wrapper.assistant {
  justify-content: flex-start;
}

.message {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.user-message {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-bottom-right-radius: 4px;
}

.assistant-message {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-bottom-left-radius: 4px;
}

.message-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.message-content {
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.sources {
  margin-top: 8px;
  padding-top: 8px;
}

.metadata {
  opacity: 0.7;
  font-size: 11px;
}

.text-medium-emphasis {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

/* Source dialog excerpt */
.source-excerpt {
  white-space: pre-wrap;
  line-height: 1.6;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 16px;
  max-height: 420px;
  overflow-y: auto;
}

/* System Info Messages */
.message-wrapper.system-info {
  justify-content: center;
}

.system-info-message {
  background: rgba(var(--v-theme-warning), 0.1) !important;
  border: 1px dashed rgba(var(--v-theme-warning), 0.5) !important;
  color: rgba(var(--v-theme-on-surface), 0.75);
  font-size: 12px;
  font-style: italic;
  max-width: 90% !important;
}

/* Scrollbar styling */
.v-card-text::-webkit-scrollbar {
  width: 6px;
}

.v-card-text::-webkit-scrollbar-track {
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.v-card-text::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.v-card-text::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
