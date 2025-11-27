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
            <v-icon color="white" size="20">{{ chatbot?.icon || 'mdi-robot' }}</v-icon>
          </v-avatar>
          <div>
            <div>{{ chatbot?.display_name || 'Chatbot Test' }}</div>
            <v-chip size="x-small" color="warning" variant="flat" class="mt-1">
              TEST-MODUS
            </v-chip>
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="closeDialog"
        />
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
          :class="message.role"
        >
          <div class="message" :class="`${message.role}-message`">
            <div class="message-header" v-if="message.role === 'assistant'">
              <v-avatar :color="chatbot?.color || 'primary'" size="24" class="mr-2">
                <v-icon color="white" size="16">{{ chatbot?.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
              <span class="text-caption">{{ chatbot?.display_name }}</span>
            </div>
            <div class="message-content">{{ message.content }}</div>

            <!-- Sources -->
            <div v-if="message.sources && message.sources.length > 0" class="sources mt-2">
              <v-divider class="mb-2" />
              <div class="text-caption text-medium-emphasis mb-1">
                <v-icon size="14" class="mr-1">mdi-file-document</v-icon>
                Quellen:
              </div>
              <v-chip
                v-for="(source, i) in message.sources"
                :key="i"
                size="x-small"
                variant="outlined"
                class="mr-1 mb-1"
              >
                {{ source.filename }}
              </v-chip>
            </div>

            <!-- Metadata -->
            <div v-if="message.metadata" class="metadata mt-2">
              <div class="text-caption text-medium-emphasis">
                <v-icon size="12">mdi-clock-outline</v-icon>
                {{ message.metadata.response_time }}ms
                <span v-if="message.metadata.tokens" class="ml-2">
                  <v-icon size="12">mdi-counter</v-icon>
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
        <div class="d-flex justify-space-between text-caption text-medium-emphasis">
          <div>
            <v-icon size="14">mdi-message-text</v-icon>
            {{ messages.length }} Nachrichten
          </div>
          <div v-if="totalResponseTime > 0">
            <v-icon size="14">mdi-clock-outline</v-icon>
            Ø {{ averageResponseTime }}ms
          </div>
          <div v-if="totalTokens > 0">
            <v-icon size="14">mdi-counter</v-icon>
            {{ totalTokens }} Tokens gesamt
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import axios from 'axios'

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

    const response = await axios.post(`/api/chatbots/${props.chatbot.id}/test`, {
      message: userMessage,
      conversation_history: messages.value.slice(0, -1) // Exclude current message
    })

    const endTime = performance.now()
    const responseTime = Math.round(endTime - startTime)

    if (response.data.success) {
      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        sources: response.data.sources || [],
        metadata: {
          response_time: responseTime,
          tokens: response.data.tokens
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

function resetChat() {
  messages.value = []
  inputMessage.value = ''
}

// Watch for dialog open/close
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    resetChat()
  }
})
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
