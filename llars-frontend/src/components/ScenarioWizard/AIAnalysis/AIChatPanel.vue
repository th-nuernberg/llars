<template>
  <div class="ai-chat-panel" :class="{ minimized: isMinimized }">
    <!-- Header -->
    <div class="panel-header" @click="toggleMinimize">
      <div class="header-left">
        <v-icon size="20" class="mr-2" color="#b0ca97">mdi-chat</v-icon>
        <span>{{ $t('scenarioWizard.chat.title') }}</span>
      </div>
      <v-icon size="20" class="toggle-icon" :class="{ rotated: !isMinimized }">
        mdi-chevron-up
      </v-icon>
    </div>

    <!-- Content (collapsible) -->
    <v-expand-transition>
      <div v-show="!isMinimized" class="panel-content">
        <!-- Messages Area -->
        <div ref="messagesContainer" class="messages-container">
          <div v-for="message in messages" :key="message.id" class="message" :class="message.role">
            <!-- Avatar -->
            <div class="message-avatar">
              <v-icon v-if="message.role === 'assistant'" size="20" color="#b0ca97">mdi-robot</v-icon>
              <v-icon v-else size="20" color="#88c4c8">mdi-account</v-icon>
            </div>

            <!-- Content -->
            <div class="message-content">
              <!-- Text -->
              <div class="message-text">
                {{ message.content }}
                <span v-if="message.streaming" class="streaming-cursor">|</span>
              </div>

              <!-- Config Changes (if any) -->
              <div v-if="message.configChanges && message.configChanges.length > 0" class="config-changes">
                <div class="changes-header">
                  <v-icon size="14" class="mr-1">mdi-cog</v-icon>
                  {{ $t('scenarioWizard.chat.changes') }}
                </div>
                <div v-for="(change, idx) in message.configChanges" :key="idx" class="change-item">
                  <v-icon size="14" color="#98d4bb" class="mr-1">mdi-check</v-icon>
                  <span class="change-field">{{ change.field }}:</span>
                  <span class="change-value">{{ formatChangeValue(change.newValue) }}</span>
                </div>
              </div>

              <!-- Quick Actions (if any) -->
              <div v-if="message.quickActions && message.quickActions.length > 0" class="quick-actions">
                <v-btn
                  v-for="action in message.quickActions"
                  :key="action.label"
                  variant="outlined"
                  size="small"
                  class="quick-action-btn"
                  @click="sendQuickAction(action)"
                >
                  <v-icon v-if="action.icon" size="16" class="mr-1">{{ action.icon }}</v-icon>
                  {{ action.label }}
                </v-btn>
              </div>
            </div>
          </div>

          <!-- Thinking Indicator -->
          <div v-if="isThinking" class="message assistant">
            <div class="message-avatar">
              <v-icon size="20" color="#b0ca97">mdi-robot</v-icon>
            </div>
            <div class="message-content">
              <div class="thinking-indicator">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <v-textarea
            v-model="inputText"
            :placeholder="$t('scenarioWizard.chat.placeholder')"
            variant="outlined"
            density="compact"
            rows="1"
            auto-grow
            max-rows="4"
            hide-details
            :disabled="isThinking"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <v-btn
            icon
            size="small"
            color="primary"
            :disabled="!inputText.trim() || isThinking"
            class="send-btn"
            @click="sendMessage"
          >
            <v-icon>mdi-send</v-icon>
          </v-btn>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'

const { t } = useI18n()
const auth = useAuth()

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  currentConfig: {
    type: Object,
    default: () => ({})
  },
  initialMessage: {
    type: String,
    default: null
  },
  minimized: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['config-update', 'update:minimized'])

// State
const isMinimized = ref(props.minimized)
const messages = ref([])
const inputText = ref('')
const isThinking = ref(false)
const messagesContainer = ref(null)

// Watch for initial message
watch(() => props.initialMessage, (msg) => {
  if (msg && messages.value.length === 0) {
    addAssistantMessage(msg, getDefaultQuickActions())
  }
}, { immediate: true })

// Initialize with welcome message if no initial message provided
onMounted(() => {
  if (!props.initialMessage && messages.value.length === 0) {
    addAssistantMessage(
      t('scenarioWizard.chat.welcome'),
      getDefaultQuickActions()
    )
  }
})

// Default quick actions
function getDefaultQuickActions() {
  return [
    { label: t('scenarioWizard.chat.actions.labels'), icon: 'mdi-tag-multiple', prompt: t('scenarioWizard.chat.prompts.labels') },
    { label: t('scenarioWizard.chat.actions.scale'), icon: 'mdi-chart-line', prompt: t('scenarioWizard.chat.prompts.scale') },
    { label: t('scenarioWizard.chat.actions.changeType'), icon: 'mdi-swap-horizontal', prompt: t('scenarioWizard.chat.prompts.changeType') },
    { label: t('scenarioWizard.chat.actions.explain'), icon: 'mdi-help-circle', prompt: t('scenarioWizard.chat.prompts.explain') }
  ]
}

// Add a message
function addUserMessage(content) {
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content,
    timestamp: new Date()
  })
  scrollToBottom()
}

function addAssistantMessage(content, quickActions = null, configChanges = null) {
  messages.value.push({
    id: Date.now(),
    role: 'assistant',
    content,
    quickActions,
    configChanges,
    timestamp: new Date()
  })
  scrollToBottom()
}

// Send message
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text) return

  addUserMessage(text)
  inputText.value = ''
  isThinking.value = true

  try {
    await streamChatResponse(text)
  } catch (error) {
    console.error('Chat error:', error)
    addAssistantMessage(t('scenarioWizard.chat.error'))
  } finally {
    isThinking.value = false
  }
}

// Send quick action
function sendQuickAction(action) {
  inputText.value = action.prompt
  sendMessage()
}

// Stream chat response from API
async function streamChatResponse(userMessage) {
  const token = auth.getToken()
  const headers = {
    'Content-Type': 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const response = await fetch('/api/ai-assist/scenario-chat/stream', {
    method: 'POST',
    headers,
    credentials: 'include',
    body: JSON.stringify({
      data: props.data,
      messages: messages.value.map(m => ({
        role: m.role,
        content: m.content
      })),
      current_config: props.currentConfig
    })
  })

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEventType = null
  let streamingMessageId = null
  let configChanges = []

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEventType = line.slice(7).trim()
        continue
      }
      if (line.startsWith('data: ')) {
        const eventData = line.slice(6)
        try {
          const parsed = JSON.parse(eventData)

          switch (currentEventType) {
            case 'thinking':
              // Already showing thinking indicator
              break

            case 'config_update':
              // Store config change and emit to parent
              configChanges.push({
                field: parsed.field,
                oldValue: props.currentConfig[parsed.field],
                newValue: parsed.value
              })
              emit('config-update', { field: parsed.field, value: parsed.value })
              break

            case 'chunk':
              // Stream text into message
              if (!streamingMessageId) {
                streamingMessageId = Date.now()
                messages.value.push({
                  id: streamingMessageId,
                  role: 'assistant',
                  content: parsed.content || '',
                  streaming: true,
                  timestamp: new Date()
                })
              } else {
                const msg = messages.value.find(m => m.id === streamingMessageId)
                if (msg) {
                  msg.content += parsed.content || ''
                }
              }
              scrollToBottom()
              break

            case 'done':
              // Finalize message
              if (streamingMessageId) {
                const msg = messages.value.find(m => m.id === streamingMessageId)
                if (msg) {
                  msg.streaming = false
                  if (configChanges.length > 0) {
                    msg.configChanges = configChanges
                  }
                  // Add quick actions for follow-up
                  msg.quickActions = getFollowUpActions()
                }
              }
              break

            case 'error':
              throw new Error(parsed.error || 'Unknown error')
          }

          currentEventType = null
        } catch (parseError) {
          // Ignore incomplete JSON
        }
      }
    }
  }
}

// Get follow-up quick actions
function getFollowUpActions() {
  return [
    { label: t('scenarioWizard.chat.actions.looksGood'), icon: 'mdi-check', prompt: '' },
    { label: t('scenarioWizard.chat.actions.moreChanges'), icon: 'mdi-pencil', prompt: t('scenarioWizard.chat.prompts.moreChanges') }
  ]
}

// Format change value for display
function formatChangeValue(value) {
  if (Array.isArray(value)) {
    return value.map(v => typeof v === 'object' ? v.name || v.label : v).join(', ')
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value)
  }
  return String(value)
}

// Toggle minimize
function toggleMinimize() {
  isMinimized.value = !isMinimized.value
  emit('update:minimized', isMinimized.value)
}

// Scroll to bottom of messages
async function scrollToBottom() {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.ai-chat-panel {
  background: rgba(var(--v-theme-on-surface), 0.02);
  border: 1px solid rgba(176, 202, 151, 0.3);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
  margin-top: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  background: rgba(176, 202, 151, 0.08);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease;
}

.panel-header:hover {
  background: rgba(176, 202, 151, 0.12);
}

.header-left {
  display: flex;
  align-items: center;
  font-size: 14px;
  font-weight: 600;
  color: #b0ca97;
}

.toggle-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
  transition: transform 0.3s ease;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 350px;
}

/* Messages Container */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Message */
.message {
  display: flex;
  gap: 12px;
  animation: message-appear 0.3s ease-out;
}

@keyframes message-appear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.user .message-avatar {
  background: rgba(136, 196, 200, 0.15);
}

.message.assistant .message-avatar {
  background: rgba(176, 202, 151, 0.15);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  font-size: 14px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.9);
  background: rgba(var(--v-theme-on-surface), 0.03);
  padding: 12px 16px;
  border-radius: 4px 16px 16px 16px;
}

.message.user .message-text {
  background: rgba(136, 196, 200, 0.1);
  border-radius: 16px 4px 16px 16px;
}

/* Streaming Cursor */
.streaming-cursor {
  color: #b0ca97;
  font-weight: bold;
  animation: cursor-blink 1s infinite;
}

@keyframes cursor-blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

/* Config Changes */
.config-changes {
  margin-top: 12px;
  padding: 12px;
  background: rgba(152, 212, 187, 0.1);
  border-radius: 8px;
  border-left: 3px solid #98d4bb;
}

.changes-header {
  display: flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #98d4bb;
  margin-bottom: 8px;
}

.change-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  margin-bottom: 4px;
}

.change-item:last-child {
  margin-bottom: 0;
}

.change-field {
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-right: 4px;
}

.change-value {
  color: #98d4bb;
  font-weight: 500;
}

/* Quick Actions */
.quick-actions {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quick-action-btn {
  text-transform: none;
  font-size: 12px;
  border-color: rgba(176, 202, 151, 0.4);
  color: #b0ca97;
}

.quick-action-btn:hover {
  background: rgba(176, 202, 151, 0.1);
  border-color: #b0ca97;
}

/* Thinking Indicator */
.thinking-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px 16px 16px 16px;
}

.thinking-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #b0ca97;
  animation: thinking-bounce 1.4s ease-in-out infinite;
}

.thinking-indicator .dot:nth-child(1) { animation-delay: 0s; }
.thinking-indicator .dot:nth-child(2) { animation-delay: 0.2s; }
.thinking-indicator .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes thinking-bounce {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Input Area */
.input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.input-area :deep(.v-field) {
  border-radius: 12px 4px 12px 4px;
}

.send-btn {
  align-self: flex-end;
}
</style>
