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
          <v-skeleton-loader v-if="isLoading('chatbots')" type="list-item@3" />
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

              <div
                class="message-content"
                v-html="formatMessage(message.content, message.sources)"
                @click="handleFootnoteClick($event, message.sources)"
              ></div>

              <!-- Sources Legend -->
              <div v-if="message.sources && message.sources.length > 0" class="message-sources mt-2">
                <div class="sources-legend">
                  <div class="sources-header text-caption d-flex align-center mb-1">
                    <v-icon size="14" class="mr-1">mdi-bookmark-multiple</v-icon>
                    <span>Quellen</span>
                  </div>
                  <div class="sources-list">
                    <v-chip
                      v-for="source in message.sources"
                      :key="source.footnote_id"
                      size="small"
                      variant="tonal"
                      color="primary"
                      class="source-chip mr-1 mb-1"
                      @click="showSourceDetail(source)"
                    >
                      <span class="font-weight-bold mr-1">[{{ source.footnote_id }}]</span>
                      <span class="text-truncate" style="max-width: 240px;">
                        {{ source.title || source.filename || 'Quelle' }}
                      </span>
                    </v-chip>
                  </div>
                </div>
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

    <!-- Source Detail Dialog -->
    <v-dialog v-model="sourceDialog.show" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-chip size="small" color="primary" class="mr-2">
            [{{ sourceDialog.source?.footnote_id }}]
          </v-chip>
          {{ sourceDialog.source?.title || sourceDialog.source?.filename || 'Quelle' }}
        </v-card-title>
        <v-card-subtitle v-if="sourceDialog.source?.collection_name">
          <v-icon size="14" class="mr-1">mdi-folder</v-icon>
          {{ sourceDialog.source?.collection_name }}
          <v-chip size="x-small" class="ml-2" color="success" variant="tonal">
            {{ ((sourceDialog.source?.relevance || 0) * 100).toFixed(0) }}% relevant
          </v-chip>
        </v-card-subtitle>
        <v-card-subtitle v-if="sourceDialog.source?.filename">
          <v-icon size="14" class="mr-1">mdi-file</v-icon>
          {{ sourceDialog.source.filename }}
        </v-card-subtitle>
        <v-divider />
        <v-card-text class="source-excerpt">
          {{ sourceDialog.source?.excerpt }}
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
            <v-icon start>mdi-download</v-icon>
            Dokument
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="sourceDialog.show = false">
            Schließen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { io } from 'socket.io-client'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useChatMessages } from './ChatWithBots/composables/useChatMessages.js'

// Composable for chat message operations
const {
  isProcessing,
  currentSources,
  addUserMessage,
  addBotPlaceholder,
  updateBotMessage,
  setBotError,
  sendViaREST,
  getFileType
} = useChatMessages()

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['chatbots'])

// Socket.IO connection
const socket = ref(null)

const route = useRoute()

// Chatbot data
const chatbots = ref([])
const selectedChatbot = ref(null)
const capabilities = ref(null)

// Chat state
const messages = ref([])
const newMessage = ref('')
const sessionId = ref(null)

// UI state
const sidebarCollapsed = ref(false)
const selectedFiles = ref([])

// Refs
const chatContainer = ref(null)
const fileInput = ref(null)

// Snackbar state
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Source detail dialog state
const sourceDialog = ref({
  show: false,
  source: null
})

// ==================== COMPUTED PROPERTIES ====================

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

// ==================== CHATBOT MANAGEMENT ====================

/**
 * Load available chatbots from API
 */
async function loadChatbots() {
  try {
    const response = await axios.get('/api/chatbots')
    if (response.data.success) {
      // Only show active chatbots
      chatbots.value = response.data.chatbots.filter(b => b.is_active)
    }
  } catch (error) {
    console.error('Error loading chatbots:', error)
    showSnackbar('Fehler beim Laden der Chatbots', 'error')
  }
}

async function maybeAutoSelectFromRoute() {
  const raw = route.query.chatbot_id || route.query.bot
  const id = raw ? parseInt(String(raw), 10) : null
  if (!id || Number.isNaN(id)) return
  if (selectedChatbot.value?.id === id) return

  const bot = chatbots.value.find(b => b.id === id)
  if (!bot) {
    showSnackbar('Chatbot nicht verfügbar oder keine Berechtigung', 'warning')
    return
  }

  await selectChatbot(bot)
}

/**
 * Select a chatbot and load its chat history
 */
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

// ==================== CHAT PERSISTENCE ====================

/**
 * Save current chat to localStorage
 */
function saveChat() {
  if (!selectedChatbot.value) return
  const storageKey = `chat_${selectedChatbot.value.id}`
  localStorage.setItem(storageKey, JSON.stringify({
    messages: messages.value,
    sessionId: sessionId.value
  }))
}

/**
 * Clear current chat and localStorage
 */
function clearChat() {
  messages.value = []
  if (selectedChatbot.value) {
    const storageKey = `chat_${selectedChatbot.value.id}`
    localStorage.removeItem(storageKey)
  }
  sessionId.value = crypto.randomUUID()
}

// ==================== FILE HANDLING ====================

/**
 * Trigger file input dialog
 */
function triggerFileInput() {
  fileInput.value?.click()
}

/**
 * Handle file selection from input
 */
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

/**
 * Remove file from selection
 */
function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

// ==================== MESSAGE SENDING ====================

/**
 * Main message sending function
 * Handles both text-only and file upload scenarios
 * Uses Socket.IO for streaming when available, falls back to REST API
 */
async function sendMessage() {
  if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || isProcessing.value) return
  if (!selectedChatbot.value) return

  const userMessage = newMessage.value.trim()
  const files = [...selectedFiles.value]
  const hasFiles = files.length > 0

  // Add user message to chat
  addUserMessage(messages, userMessage, files)

  // Clear input
  newMessage.value = ''
  selectedFiles.value = []
  isProcessing.value = true

  // Add placeholder for bot response
  addBotPlaceholder(messages)
  scrollToBottom()

  // Files require REST API (Socket.IO doesn't support file uploads)
  // Also use REST as fallback if socket is not connected
  if (hasFiles || !socket.value?.connected) {
    await sendMessageViaREST(userMessage, files)
  } else {
    // Use Socket.IO for streaming text-only messages
    socket.value.emit('chatbot:stream', {
      chatbot_id: selectedChatbot.value.id,
      message: userMessage,
      session_id: sessionId.value,
      username: null,
      token: sessionStorage.getItem('auth_token')
    })
  }
}

/**
 * Send message via REST API
 * Handles both text-only and file upload
 */
async function sendMessageViaREST(userMessage, files = []) {
  try {
    const result = await sendViaREST(
      selectedChatbot.value.id,
      userMessage,
      sessionId.value,
      files
    )

    if (result.success) {
      updateBotMessage(
        messages,
        result.content,
        new Date().toLocaleTimeString(),
        false,
        result.sources
      )
      saveChat()
    } else {
      setBotError(messages)
      showSnackbar(result.error || 'Fehler beim Senden', 'error')
    }
  } catch (error) {
    console.error('Chat error:', error)
    setBotError(messages)
    showSnackbar('Fehler beim Senden', 'error')
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

// ==================== UI UTILITIES ====================

/**
 * Scroll chat container to bottom
 */
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

/**
 * Show snackbar notification
 */
function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// ==================== MESSAGE FORMATTING ====================

/**
 * Format message content with markdown and footnote support
 */
function formatMessage(content, sources = []) {
  if (!content) return ''

  // Replace footnote references [1], [2], etc. with clickable links
  let processedContent = content
  if (sources && sources.length > 0) {
    // Create a map of footnote_id to source
    const sourceMap = {}
    sources.forEach(s => {
      sourceMap[s.footnote_id] = s
    })

    // Replace [1], [2], etc. with clickable footnote links
    processedContent = content.replace(/\[(\d+)\]/g, (match, num) => {
      const footnoteId = parseInt(num)
      const source = sourceMap[footnoteId]
      if (source) {
        const title = source.title || 'Quelle ' + footnoteId
        // Create a clickable superscript footnote
        return `<sup class="footnote-ref" data-footnote-id="${footnoteId}" title="${title}">[${num}]</sup>`
      }
      return match
    })
  }

  // Parse markdown and sanitize
  const html = marked.parse(processedContent, { breaks: true })
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-footnote-id', 'title']
  })
}

/**
 * Get icon for file type
 */
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

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ==================== SOURCE HANDLING ====================

/**
 * Show source detail dialog
 */
function showSourceDetail(source) {
  sourceDialog.value = {
    show: true,
    source: source
  }
}

/**
 * Handle click on footnote references in message content
 */
function handleFootnoteClick(event, sources) {
  const target = event.target
  if (target.classList.contains('footnote-ref')) {
    const footnoteId = parseInt(target.dataset.footnoteId)
    if (sources && sources.length > 0) {
      const source = sources.find(s => s.footnote_id === footnoteId)
      if (source) {
        showSourceDetail(source)
      }
    }
  }
}

// ==================== SOCKET.IO SETUP ====================

/**
 * Initialize Socket.IO connection and event handlers
 */
function initSocket() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  socket.value = io(baseUrl, {
    path: '/socket.io/',
    transports: ['websocket', 'polling']
  })

  socket.value.on('connect', () => {
    console.log('ChatWithBots: Socket connected')
  })

  socket.value.on('disconnect', () => {
    console.log('ChatWithBots: Socket disconnected')
  })

  // Sources are sent BEFORE streaming, so we store them for the current message
  socket.value.on('chatbot:sources', (data) => {
    currentSources.value = data.sources || []
    // Assign sources to the current bot message placeholder
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx].sources = currentSources.value
    }
  })

  // Streaming response chunks
  socket.value.on('chatbot:response', (data) => {
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      if (data.content) {
        messages.value[lastIdx].content += data.content
        scrollToBottom()
      }
      if (data.complete) {
        messages.value[lastIdx].streaming = false
        messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
        // Ensure sources are assigned
        if (currentSources.value.length > 0 && !messages.value[lastIdx].sources) {
          messages.value[lastIdx].sources = currentSources.value
        }
        currentSources.value = []
        isProcessing.value = false
        saveChat()
        scrollToBottom()
      }
    }
  })

  // Completion metadata
  socket.value.on('chatbot:complete', (data) => {
    console.log('Chatbot response complete:', data)
  })

  // Error handling
  socket.value.on('chatbot:error', (data) => {
    console.error('Chatbot error:', data.error)
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx].content = data.error || 'Ein Fehler ist aufgetreten.'
      messages.value[lastIdx].streaming = false
      messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
    }
    isProcessing.value = false
    showSnackbar(data.error || 'Fehler beim Senden', 'error')
  })
}

/**
 * Disconnect Socket.IO connection
 */
function disconnectSocket() {
  if (socket.value) {
    socket.value.disconnect()
    socket.value = null
  }
}

// ==================== WATCHERS ====================

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// ==================== LIFECYCLE HOOKS ====================

onMounted(async () => {
  await withLoading('chatbots', async () => {
    await loadChatbots()
  })
  await maybeAutoSelectFromRoute()
  initSocket()
})

onUnmounted(() => {
  disconnectSocket()
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - var(--v-layout-top, 0px) - var(--v-layout-bottom, 0px));
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

.chat-container {
  height: 100%;
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

/* Footnote references styling */
.message-content :deep(.footnote-ref) {
  color: rgb(var(--v-theme-primary));
  cursor: pointer;
  font-weight: 600;
  font-size: 0.75em;
  vertical-align: super;
  padding: 0 2px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.message-content :deep(.footnote-ref:hover) {
  background: rgba(var(--v-theme-primary), 0.15);
  text-decoration: underline;
}

.message-files {
  display: flex;
  flex-wrap: wrap;
}

.message-sources {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  padding-top: 8px;
}

.sources-legend {
  padding: 4px 0;
}

.sources-header {
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.source-chip {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.source-chip:hover {
  transform: scale(1.05);
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

/* Source detail dialog */
.source-excerpt {
  white-space: pre-wrap;
  line-height: 1.6;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 16px;
  font-size: 0.9rem;
  max-height: 400px;
  overflow-y: auto;
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
