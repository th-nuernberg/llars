<!-- ChatWithBots.vue - Chat interface with chatbot selection and file upload -->
<template>
  <v-container fluid class="chat-page pa-0">
    <v-row no-gutters class="chat-container">
      <!-- Chatbot Selection Sidebar -->
      <v-col cols="12" md="3" class="chatbot-sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
        <div class="sidebar-header">
          <div class="d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="mr-2">mdi-robot</v-icon>
              <span v-if="!sidebarCollapsed" class="font-weight-bold">Chatbots</span>
            </div>
            <v-btn
              icon
              variant="text"
              size="small"
              @click="sidebarCollapsed = !sidebarCollapsed"
            >
              <v-icon>{{ sidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
            </v-btn>
          </div>
        </div>

        <v-divider />

        <!-- Chatbot List -->
        <div v-if="!sidebarCollapsed" class="chatbot-list">
          <v-skeleton-loader v-if="loadingChatbots" type="list-item@3" />
          <template v-else>
            <v-list density="compact" class="pa-0">
              <v-list-item
                v-for="bot in chatbots"
                :key="bot.id"
                :active="selectedChatbot?.id === bot.id"
                @click="selectChatbot(bot)"
                class="chatbot-item"
              >
                <template #prepend>
                  <v-avatar :color="bot.color || 'primary'" size="36">
                    <v-icon color="white">{{ bot.icon || 'mdi-robot' }}</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">
                  {{ bot.display_name }}
                </v-list-item-title>
                <v-list-item-subtitle class="text-truncate">
                  {{ bot.description || 'Keine Beschreibung' }}
                </v-list-item-subtitle>
                <template #append>
                  <v-chip v-if="bot.rag_enabled" size="x-small" color="info" variant="tonal">
                    RAG
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <div v-if="chatbots.length === 0" class="text-center pa-4 text-medium-emphasis">
              <v-icon size="32" class="mb-2">mdi-robot-off</v-icon>
              <div>Keine Chatbots verfügbar</div>
            </div>
          </template>
        </div>
      </v-col>

      <!-- Main Chat Area -->
      <v-col cols="12" :md="sidebarCollapsed ? 12 : 9" class="chat-main">
        <!-- Chat Header -->
        <div v-if="selectedChatbot" class="chat-header">
          <div class="d-flex align-center">
            <v-avatar :color="selectedChatbot.color || 'primary'" size="40" class="mr-3">
              <v-icon color="white">{{ selectedChatbot.icon || 'mdi-robot' }}</v-icon>
            </v-avatar>
            <div>
              <div class="font-weight-bold">{{ selectedChatbot.display_name }}</div>
              <div class="text-caption text-medium-emphasis">
                {{ selectedChatbot.model_name }}
                <v-chip v-if="capabilities?.vision" size="x-small" color="success" variant="tonal" class="ml-1">
                  Vision
                </v-chip>
              </div>
            </div>
          </div>
          <v-btn
            icon
            variant="text"
            @click="clearChat"
            title="Chat leeren"
          >
            <v-icon>mdi-delete-outline</v-icon>
          </v-btn>
        </div>

        <!-- Empty State -->
        <div v-if="!selectedChatbot" class="empty-state">
          <v-icon size="80" color="grey-lighten-1">mdi-robot-confused</v-icon>
          <h3 class="text-h5 mt-4">Chatbot auswählen</h3>
          <p class="text-medium-emphasis">
            Wählen Sie einen Chatbot aus der Liste, um eine Unterhaltung zu beginnen.
          </p>
        </div>

        <!-- Chat Messages -->
        <div v-else class="chat-messages" ref="chatContainer">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0 && selectedChatbot.welcome_message" class="welcome-message">
            <v-card variant="tonal" color="primary" class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-avatar :color="selectedChatbot.color || 'primary'" size="32" class="mr-2">
                  <v-icon color="white" size="18">{{ selectedChatbot.icon || 'mdi-robot' }}</v-icon>
                </v-avatar>
                <span class="font-weight-bold">{{ selectedChatbot.display_name }}</span>
              </div>
              {{ selectedChatbot.welcome_message }}
            </v-card>
          </div>

          <!-- Messages -->
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message-container', message.sender]"
          >
            <!-- Bot Avatar -->
            <template v-if="message.sender === 'bot'">
              <v-avatar :color="selectedChatbot?.color || 'primary'" size="36" class="message-avatar">
                <v-icon color="white" size="20">{{ selectedChatbot?.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
            </template>

            <div class="message">
              <!-- File attachments -->
              <div v-if="message.files && message.files.length > 0" class="message-files mb-2">
                <v-chip
                  v-for="(file, idx) in message.files"
                  :key="idx"
                  size="small"
                  variant="outlined"
                  class="mr-1 mb-1"
                >
                  <v-icon start size="14">
                    {{ getFileIcon(file.type) }}
                  </v-icon>
                  {{ file.filename }}
                </v-chip>
              </div>

              <div class="message-content" v-html="formatMessage(message.content)"></div>

              <!-- Sources -->
              <div v-if="message.sources && message.sources.length > 0" class="message-sources mt-2">
                <v-expansion-panels variant="accordion" density="compact">
                  <v-expansion-panel>
                    <v-expansion-panel-title class="text-caption">
                      <v-icon start size="14">mdi-file-document-multiple</v-icon>
                      {{ message.sources.length }} Quellen
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <div v-for="(source, idx) in message.sources" :key="idx" class="source-item">
                        <strong>{{ source.title }}</strong>
                        <span class="text-caption ml-2">({{ (source.relevance * 100).toFixed(0) }}%)</span>
                        <div class="text-caption text-medium-emphasis">{{ source.excerpt }}</div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </div>

              <div v-if="message.streaming" class="stream-indicator">
                <v-progress-circular indeterminate size="12" width="2" />
              </div>
              <div class="message-timestamp">{{ message.timestamp }}</div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div v-if="selectedChatbot" class="chat-input">
          <!-- File Preview -->
          <div v-if="selectedFiles.length > 0" class="file-preview mb-2">
            <v-chip
              v-for="(file, idx) in selectedFiles"
              :key="idx"
              closable
              size="small"
              class="mr-1"
              @click:close="removeFile(idx)"
            >
              <v-icon start size="14">{{ getFileIcon(file.type) }}</v-icon>
              {{ file.name }}
              <span class="text-caption ml-1">({{ formatFileSize(file.size) }})</span>
            </v-chip>
          </div>

          <div class="d-flex align-center gap-2">
            <!-- File Upload Button -->
            <v-btn
              icon
              variant="text"
              :disabled="isProcessing"
              @click="triggerFileInput"
              :title="fileUploadTooltip"
            >
              <v-icon>mdi-paperclip</v-icon>
            </v-btn>
            <input
              ref="fileInput"
              type="file"
              multiple
              :accept="acceptedFileTypes"
              style="display: none"
              @change="handleFileSelect"
            />

            <!-- Message Input -->
            <v-text-field
              v-model="newMessage"
              @keyup.enter="sendMessage"
              placeholder="Schreibe eine Nachricht..."
              variant="outlined"
              :loading="isProcessing"
              :disabled="isProcessing"
              hide-details
              density="comfortable"
              class="flex-grow-1"
            />

            <!-- Send Button -->
            <v-btn
              icon
              color="primary"
              :disabled="(!newMessage.trim() && selectedFiles.length === 0) || isProcessing"
              :loading="isProcessing"
              @click="sendMessage"
            >
              <v-icon>mdi-send</v-icon>
            </v-btn>
          </div>

          <!-- Supported file types info -->
          <div class="text-caption text-medium-emphasis mt-1">
            <template v-if="capabilities?.vision">
              Bilder, PDFs, Word, Excel, PowerPoint
            </template>
            <template v-else>
              PDFs, Word, Excel, PowerPoint (kein Bild-Support)
            </template>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

// State
const chatbots = ref([])
const selectedChatbot = ref(null)
const capabilities = ref(null)
const messages = ref([])
const newMessage = ref('')
const isProcessing = ref(false)
const loadingChatbots = ref(true)
const sidebarCollapsed = ref(false)
const selectedFiles = ref([])
const sessionId = ref(null)

const chatContainer = ref(null)
const fileInput = ref(null)

const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Computed
const acceptedFileTypes = computed(() => {
  const types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
  if (capabilities.value?.vision) {
    types.push('.png', '.jpg', '.jpeg', '.gif', '.webp')
  }
  return types.join(',')
})

const fileUploadTooltip = computed(() => {
  if (capabilities.value?.vision) {
    return 'Bilder und Dokumente hochladen'
  }
  return 'Dokumente hochladen (PDF, Word, Excel, PowerPoint)'
})

// Methods
async function loadChatbots() {
  loadingChatbots.value = true
  try {
    const response = await axios.get('/api/chatbots')
    if (response.data.success) {
      // Only show active chatbots
      chatbots.value = response.data.chatbots.filter(b => b.is_active)
    }
  } catch (error) {
    console.error('Error loading chatbots:', error)
    showSnackbar('Fehler beim Laden der Chatbots', 'error')
  } finally {
    loadingChatbots.value = false
  }
}

async function selectChatbot(bot) {
  selectedChatbot.value = bot
  messages.value = []
  selectedFiles.value = []
  sessionId.value = crypto.randomUUID()

  // Load capabilities
  try {
    const response = await axios.get(`/api/chatbots/${bot.id}/capabilities`)
    if (response.data.success) {
      capabilities.value = response.data.capabilities
    }
  } catch (error) {
    console.error('Error loading capabilities:', error)
    capabilities.value = { vision: false, rag: bot.rag_enabled }
  }

  // Load from localStorage if exists
  const storageKey = `chat_${bot.id}`
  const saved = localStorage.getItem(storageKey)
  if (saved) {
    try {
      const data = JSON.parse(saved)
      messages.value = data.messages || []
      sessionId.value = data.sessionId || sessionId.value
    } catch (e) {
      console.error('Error loading saved chat:', e)
    }
  }
}

function saveChat() {
  if (!selectedChatbot.value) return
  const storageKey = `chat_${selectedChatbot.value.id}`
  localStorage.setItem(storageKey, JSON.stringify({
    messages: messages.value,
    sessionId: sessionId.value
  }))
}

function clearChat() {
  messages.value = []
  if (selectedChatbot.value) {
    const storageKey = `chat_${selectedChatbot.value.id}`
    localStorage.removeItem(storageKey)
  }
  sessionId.value = crypto.randomUUID()
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      showSnackbar(`${file.name} ist zu groß (max 10MB)`, 'error')
      continue
    }
    selectedFiles.value.push(file)
  }
  // Reset input
  event.target.value = ''
}

function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

async function sendMessage() {
  if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || isProcessing.value) return
  if (!selectedChatbot.value) return

  const userMessage = newMessage.value.trim()
  const files = [...selectedFiles.value]

  // Add user message
  const userMsgObj = {
    id: Date.now(),
    content: userMessage || '(Dateien hochgeladen)',
    sender: 'user',
    timestamp: new Date().toLocaleTimeString(),
    files: files.map(f => ({ filename: f.name, type: getFileType(f.name) }))
  }
  messages.value.push(userMsgObj)

  // Clear input
  newMessage.value = ''
  selectedFiles.value = []
  isProcessing.value = true

  // Add placeholder for bot response
  const botMsgObj = {
    id: Date.now() + 1,
    content: '',
    sender: 'bot',
    timestamp: '',
    streaming: true
  }
  messages.value.push(botMsgObj)
  scrollToBottom()

  try {
    // Build form data for file upload
    const formData = new FormData()
    formData.append('message', userMessage)
    formData.append('session_id', sessionId.value)
    formData.append('include_sources', 'true')

    for (const file of files) {
      formData.append('files', file)
    }

    const response = await axios.post(
      `/api/chatbots/${selectedChatbot.value.id}/chat`,
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' }
      }
    )

    if (response.data.success) {
      // Update bot message
      const lastIdx = messages.value.length - 1
      messages.value[lastIdx] = {
        ...messages.value[lastIdx],
        content: response.data.response,
        timestamp: new Date().toLocaleTimeString(),
        streaming: false,
        sources: response.data.sources
      }
      saveChat()
    } else {
      throw new Error(response.data.error || 'Unbekannter Fehler')
    }

  } catch (error) {
    console.error('Chat error:', error)
    const lastIdx = messages.value.length - 1
    messages.value[lastIdx] = {
      ...messages.value[lastIdx],
      content: 'Es ist ein Fehler aufgetreten. Bitte versuchen Sie es erneut.',
      timestamp: new Date().toLocaleTimeString(),
      streaming: false
    }
    showSnackbar(error.response?.data?.error || 'Fehler beim Senden', 'error')
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

function formatMessage(content) {
  if (!content) return ''
  // Parse markdown and sanitize
  const html = marked.parse(content, { breaks: true })
  return DOMPurify.sanitize(html)
}

function getFileIcon(type) {
  switch (type) {
    case 'image': return 'mdi-image'
    case 'pdf': return 'mdi-file-pdf-box'
    case 'word': return 'mdi-file-word'
    case 'excel': return 'mdi-file-excel'
    case 'powerpoint': return 'mdi-file-powerpoint'
    default: return 'mdi-file'
  }
}

function getFileType(filename) {
  const ext = filename.split('.').pop()?.toLowerCase()
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'].includes(ext)) return 'image'
  if (ext === 'pdf') return 'pdf'
  if (['doc', 'docx'].includes(ext)) return 'word'
  if (['xls', 'xlsx'].includes(ext)) return 'excel'
  if (['ppt', 'pptx'].includes(ext)) return 'powerpoint'
  return 'document'
}

function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// Watch for chatbot changes
watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// Lifecycle
onMounted(() => {
  loadChatbots()
})
</script>

<style scoped>
.chat-page {
  height: 100%;
  background-color: rgb(var(--v-theme-background));
}

.chat-container {
  height: calc(100vh - 64px);
}

.chatbot-sidebar {
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}

.sidebar-collapsed {
  max-width: 60px !important;
  flex: 0 0 60px !important;
}

.sidebar-header {
  padding: 16px;
  background: rgba(var(--v-theme-primary), 0.05);
}

.chatbot-list {
  flex: 1;
  overflow-y: auto;
}

.chatbot-item {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.chatbot-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.chat-main {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
}

.chat-header {
  padding: 12px 24px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  max-width: 600px;
  margin: 0 auto;
}

.message-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 80%;
}

.message-container.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.message {
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
  min-width: 100px;
}

.message-container.user .message {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-bottom-right-radius: 4px;
}

.message-container.bot .message {
  background: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface));
  border-bottom-left-radius: 4px;
}

.message-content {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content :deep(p) {
  margin-bottom: 0.5em;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

.message-files {
  display: flex;
  flex-wrap: wrap;
}

.message-sources {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  padding-top: 8px;
}

.source-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.source-item:last-child {
  border-bottom: none;
}

.message-timestamp {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 4px;
}

.stream-indicator {
  margin-top: 8px;
}

.chat-input {
  padding: 16px 24px;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.file-preview {
  display: flex;
  flex-wrap: wrap;
}

.gap-2 {
  gap: 8px;
}

@media (max-width: 960px) {
  .chatbot-sidebar {
    display: none;
  }

  .message-container {
    max-width: 90%;
  }
}
</style>
