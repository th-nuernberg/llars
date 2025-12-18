<!-- ChatWithBots.vue - Chat interface with chatbot selection and file upload -->
<template>
  <div class="chat-page">
    <div class="chat-container" ref="containerRef">
      <!-- Chatbot Selection Sidebar -->
      <aside class="chatbot-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <!-- Header -->
        <div class="sidebar-header">
          <div class="header-content" :class="{ 'justify-center': sidebarCollapsed }">
            <template v-if="!sidebarCollapsed">
              <v-icon class="header-icon" size="24">mdi-robot</v-icon>
              <div class="header-text">
                <span class="header-title">Chatbots</span>
              </div>
            </template>
            <v-icon v-else class="header-icon-collapsed" size="24">mdi-robot</v-icon>
          </div>
          <button
            class="collapse-btn"
            @click="toggleSidebar"
            :title="sidebarCollapsed ? 'Erweitern' : 'Zuklappen'"
          >
            <v-icon size="20">{{ sidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
          </button>
        </div>

        <div class="sidebar-divider"></div>

        <!-- Chatbot List -->
        <nav class="sidebar-nav">
          <v-skeleton-loader v-if="isLoading('chatbots')" type="list-item@3" />
          <template v-else>
            <button
              v-for="bot in chatbots"
              :key="bot.id"
              class="nav-item chatbot-item"
              :class="{ active: selectedChatbot?.id === bot.id }"
              @click="selectChatbot(bot)"
              :title="sidebarCollapsed ? bot.display_name : undefined"
            >
              <div class="nav-icon">
                <v-avatar :color="bot.color || 'primary'" size="32">
                  <v-icon color="white" size="18">{{ bot.icon || 'mdi-robot' }}</v-icon>
                </v-avatar>
              </div>
              <template v-if="!sidebarCollapsed">
                <div class="chatbot-info">
                  <span class="nav-label">{{ bot.display_name }}</span>
                  <span class="chatbot-description">{{ bot.description || 'Keine Beschreibung' }}</span>
                </div>
                <LTag
                  v-if="getChatbotTypeTag(bot)"
                  :variant="getChatbotTypeTag(bot).variant"
                  size="sm"
                  class="nav-badge"
                >
                  {{ getChatbotTypeTag(bot).label }}
                </LTag>
              </template>
            </button>

            <div v-if="chatbots.length === 0 && !sidebarCollapsed" class="text-center pa-4 text-medium-emphasis">
              <v-icon size="32" class="mb-2">mdi-robot-off</v-icon>
              <div>Keine Chatbots verfügbar</div>
            </div>
          </template>
        </nav>

        <!-- Footer -->
        <div class="sidebar-footer">
          <div class="sidebar-divider"></div>
          <button
            class="nav-item"
            @click="router.push('/Home')"
            :title="sidebarCollapsed ? 'Zur Startseite' : undefined"
          >
            <div class="nav-icon">
              <v-icon size="20">mdi-home</v-icon>
            </div>
            <span v-if="!sidebarCollapsed" class="nav-label">Zur Startseite</span>
          </button>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <div class="chat-main" :style="sourcePanel.open ? leftPanelStyle() : {}">
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
                <LTag v-if="capabilities?.vision" variant="success" size="sm" class="ml-1">
                  Vision
                </LTag>
              </div>
            </div>
          </div>
          <div class="d-flex align-center ga-1">
            <v-btn
              icon
              variant="text"
              @click="toggleSourcePanel"
              title="Quellen"
            >
              <v-icon>{{ sourcePanel.open ? 'mdi-bookmark-off-outline' : 'mdi-bookmark-multiple-outline' }}</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              @click="clearChat"
              title="Chat leeren"
            >
              <v-icon>mdi-delete-outline</v-icon>
            </v-btn>
          </div>
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
          <!-- Agent Reasoning Display (for ACT, ReAct, ReflAct modes) -->
          <AgentReasoningDisplay
            ref="agentReasoningRef"
            :agent-status="agentStatus"
            :is-processing="isProcessing"
          />

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
      </div>

      <!-- Resize Divider -->
      <div
        v-if="sourcePanel.open"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Sources Side Panel -->
      <div v-if="sourcePanel.open" class="sources-panel" :style="rightPanelStyle()">
        <v-card class="sources-panel-card" variant="outlined">
          <div class="sources-panel-header">
            <div class="d-flex align-center text-truncate">
              <v-icon class="mr-2">mdi-bookmark-multiple</v-icon>
              <span class="font-weight-bold text-truncate">
                {{ sourcePanel.source?.title || sourcePanel.source?.filename || 'Quelle' }}
              </span>
            </div>
            <div class="d-flex align-center">
              <v-btn
                icon
                variant="text"
                size="small"
                @click="sourcePanel.pinned = !sourcePanel.pinned"
                :title="sourcePanel.pinned ? 'Lösen' : 'Anheften'"
              >
                <v-icon>{{ sourcePanel.pinned ? 'mdi-pin' : 'mdi-pin-outline' }}</v-icon>
              </v-btn>
              <v-btn
                icon
                variant="text"
                size="small"
                @click="closeSourcePanel"
                title="Schließen"
              >
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </div>
          </div>

          <v-divider />

          <v-tabs v-model="sourcePanel.tab" bg-color="primary" density="compact">
            <v-tab value="excerpt">
              <v-icon start>mdi-text-box</v-icon>
              Ausschnitt
            </v-tab>
            <v-tab value="screenshot" :disabled="!sourcePanel.source?.screenshot_url">
              <v-icon start>mdi-image</v-icon>
              Screenshot
            </v-tab>
            <v-tab value="document" :disabled="!sourcePanel.source?.content_url">
              <v-icon start>mdi-file-document</v-icon>
              Dokument
            </v-tab>
          </v-tabs>

          <v-window v-model="sourcePanel.tab" class="sources-panel-window">
            <v-window-item value="excerpt">
              <div class="sources-panel-content">
                <div v-if="!sourcePanel.source" class="text-center pa-6 text-medium-emphasis">
                  <v-icon size="48" class="mb-2">mdi-bookmark-outline</v-icon>
                  <div>Quelle auswählen</div>
                </div>
                <template v-else>
                  <div class="d-flex flex-wrap ga-2 mb-3">
                    <v-chip v-if="sourcePanel.source.collection_name" size="small" variant="tonal" color="primary">
                      <v-icon start size="14">mdi-folder</v-icon>
                      {{ sourcePanel.source.collection_name }}
                    </v-chip>
                    <v-chip v-if="sourcePanel.source.page_number" size="small" variant="outlined">
                      <v-icon start size="14">mdi-book-open-page-variant</v-icon>
                      Seite {{ sourcePanel.source.page_number }}
                    </v-chip>
                    <v-chip v-if="sourcePanel.source.chunk_index !== null && sourcePanel.source.chunk_index !== undefined" size="small" variant="outlined">
                      <v-icon start size="14">mdi-text</v-icon>
                      Chunk {{ sourcePanel.source.chunk_index }}
                    </v-chip>
                    <v-chip v-if="sourcePanel.source.relevance !== null && sourcePanel.source.relevance !== undefined" size="small" variant="tonal" color="success">
                      {{ ((sourcePanel.source.relevance || 0) * 100).toFixed(0) }}% relevant
                    </v-chip>
                  </div>

                  <div class="sources-panel-excerpt">
                    {{ sourcePanel.source.excerpt }}
                  </div>

                  <div class="d-flex align-center mt-4">
                    <v-btn
                      v-if="sourcePanel.source.download_url"
                      :href="sourcePanel.source.download_url"
                      target="_blank"
                      rel="noopener"
                      color="primary"
                      variant="tonal"
                    >
                      <v-icon start>mdi-download</v-icon>
                      Dokument
                    </v-btn>
                    <v-spacer />
                    <v-btn
                      variant="text"
                      @click="sourcePanel.tab = 'document'"
                      :disabled="!sourcePanel.source.content_url"
                    >
                      <v-icon start>mdi-file-search</v-icon>
                      Text anzeigen
                    </v-btn>
                  </div>
                </template>
              </div>
            </v-window-item>

            <v-window-item value="screenshot">
              <div class="sources-panel-content">
                <v-skeleton-loader v-if="sourcePanel.loadingScreenshot" type="image" height="320" />
                <v-alert
                  v-else-if="sourcePanel.screenshotError"
                  type="error"
                  variant="tonal"
                  density="compact"
                >
                  {{ sourcePanel.screenshotError }}
                </v-alert>
                <div v-else class="sources-panel-screenshot">
                  <div v-if="!sourcePanel.screenshotBlobUrl" class="text-center pa-6 text-medium-emphasis">
                    <v-icon size="48" class="mb-2">mdi-image-off</v-icon>
                    <div>Kein Screenshot verfügbar</div>
                  </div>
                  <template v-else>
                    <div class="d-flex justify-end mb-2">
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="primary"
                        @click="openFullscreen('screenshot')"
                      >
                        <v-icon start>mdi-fullscreen</v-icon>
                        Vergrößern
                      </v-btn>
                    </div>
                    <v-card
                      variant="outlined"
                      class="overflow-hidden screenshot-card"
                      @click="openFullscreen('screenshot')"
                    >
                      <v-img :src="sourcePanel.screenshotBlobUrl" contain max-height="420">
                        <template #placeholder>
                          <div class="d-flex align-center justify-center fill-height">
                            <v-progress-circular indeterminate color="primary" size="24" />
                          </div>
                        </template>
                      </v-img>
                    </v-card>
                  </template>
                </div>
              </div>
            </v-window-item>

            <v-window-item value="document">
              <div class="sources-panel-content">
                <v-skeleton-loader v-if="sourcePanel.loadingContent" type="article" />
                <v-alert
                  v-else-if="sourcePanel.contentError"
                  type="error"
                  variant="tonal"
                  density="compact"
                >
                  {{ sourcePanel.contentError }}
                </v-alert>
                <div v-else class="sources-panel-document">
                  <div v-if="!sourcePanel.documentContent" class="text-center pa-6 text-medium-emphasis">
                    <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
                    <div>Kein Inhalt verfügbar</div>
                  </div>
                  <template v-else>
                    <div class="d-flex justify-end mb-2">
                      <v-btn
                        size="small"
                        variant="tonal"
                        color="primary"
                        @click="openFullscreen('document')"
                      >
                        <v-icon start>mdi-fullscreen</v-icon>
                        Vergrößern
                      </v-btn>
                    </div>
                    <div class="sources-panel-text">
                      {{ sourcePanel.documentContent }}
                    </div>
                  </template>
                </div>
              </div>
            </v-window-item>
          </v-window>
        </v-card>
      </div>
    </div>

    <!-- Fullscreen Dialog for Screenshot/Document -->
    <v-dialog v-model="fullscreenDialog.show" fullscreen transition="dialog-bottom-transition">
      <v-card class="fullscreen-dialog-card">
        <v-toolbar color="primary" density="compact">
          <v-toolbar-title class="d-flex align-center">
            <v-icon class="mr-2">{{ fullscreenDialog.type === 'screenshot' ? 'mdi-image' : 'mdi-file-document' }}</v-icon>
            {{ sourcePanel.source?.title || sourcePanel.source?.filename || 'Quelle' }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn icon @click="fullscreenDialog.show = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <div class="fullscreen-content">
          <!-- Screenshot Fullscreen -->
          <template v-if="fullscreenDialog.type === 'screenshot'">
            <div class="fullscreen-image-container">
              <img
                v-if="sourcePanel.screenshotBlobUrl"
                :src="sourcePanel.screenshotBlobUrl"
                alt="Screenshot"
                class="fullscreen-image"
              />
            </div>
          </template>
          <!-- Document Fullscreen -->
          <template v-else-if="fullscreenDialog.type === 'document'">
            <div class="fullscreen-document-container">
              <div class="fullscreen-document-text">
                {{ sourcePanel.documentContent }}
              </div>
            </div>
          </template>
        </div>
      </v-card>
    </v-dialog>

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
          <LTag variant="success" size="sm" class="ml-2">
            {{ ((sourceDialog.source?.relevance || 0) * 100).toFixed(0) }}% relevant
          </LTag>
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
            variant="text"
            @click="pinSourceToPanel(sourceDialog.source)"
          >
            <v-icon start>mdi-pin</v-icon>
            Anheften
          </v-btn>
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { io } from 'socket.io-client'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useChatMessages } from './ChatWithBots/composables/useChatMessages.js'
import { usePanelResize } from '@/composables/usePanelResize'
import { AUTH_STORAGE_KEYS, clearAuthStorage, getAuthStorageItem } from '@/utils/authStorage'
import AgentReasoningDisplay from './Chat/AgentReasoningDisplay.vue'

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

// Panel Resize - for sources panel
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 65,
  minLeftPercent: 40,
  maxLeftPercent: 80,
  storageKey: 'chat-sources-panel-width'
})

// Socket.IO connection
const socket = ref(null)

const route = useRoute()
const router = useRouter()

// Chatbot data
const chatbots = ref([])
const selectedChatbot = ref(null)
const capabilities = ref(null)

// Chat state
const messages = ref([])
const newMessage = ref('')
const sessionId = ref(null)

// UI state - sidebar with localStorage persistence
const sidebarCollapsed = ref(false)

// Load sidebar state from localStorage
const storedSidebar = localStorage.getItem('sidebar_chat')
if (storedSidebar !== null) {
  sidebarCollapsed.value = storedSidebar === 'true'
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_chat', String(sidebarCollapsed.value))
}

const selectedFiles = ref([])

const sourcePanel = ref({
  open: false,
  pinned: false,
  tab: 'excerpt',
  source: null,
  documentContent: '',
  loadedDocumentId: null,
  screenshotBlobUrl: null,
  loadedScreenshotDocumentId: null,
  loadingScreenshot: false,
  screenshotError: null,
  loadingContent: false,
  contentError: null
})

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

// Fullscreen dialog state
const fullscreenDialog = ref({
  show: false,
  type: null // 'screenshot' or 'document'
})

// Agent reasoning display state
const agentStatus = ref(null)
const agentEventCounter = ref(0)
const agentReasoningRef = ref(null)

// ==================== HELPER FUNCTIONS ====================

/**
 * Get the appropriate tag info for a chatbot based on its type
 * Priority: Agent Mode > RAG > null
 */
function getChatbotTypeTag(bot) {
  const agentMode = bot.prompt_settings?.agent_mode

  // Agent modes take priority
  if (agentMode && agentMode !== 'standard') {
    const agentTags = {
      'act': { label: 'ACT', variant: 'success' },
      'react': { label: 'ReAct', variant: 'accent' },
      'reflact': { label: 'ReflAct', variant: 'secondary' }
    }
    return agentTags[agentMode] || null
  }

  // RAG-enabled chatbot
  if (bot.rag_enabled) {
    return { label: 'RAG', variant: 'info' }
  }

  // Simple chatbot - no tag
  return null
}

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
  // Reset agent reasoning display
  agentStatus.value = null
  if (agentReasoningRef.value?.reset) {
    agentReasoningRef.value.reset()
  }

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
  // Reset agent reasoning display
  agentStatus.value = null
  if (agentReasoningRef.value?.reset) {
    agentReasoningRef.value.reset()
  }
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
      token: getAuthStorageItem(AUTH_STORAGE_KEYS.token)
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
  if (sourcePanel.value.pinned) {
    openSourceInPanel(source)
    return
  }

  sourceDialog.value = { show: true, source }
}

function openSourceFromCitation(source) {
  if (!source) return
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
  openSourceInPanel(source)
}

function toggleSourcePanel() {
  if (sourcePanel.value.open) {
    closeSourcePanel()
    return
  }
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
}

function closeSourcePanel() {
  sourcePanel.value.open = false
  sourcePanel.value.pinned = false
  sourcePanel.value.tab = 'excerpt'
}

function pinSourceToPanel(source) {
  if (!source) return
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
  sourceDialog.value.show = false
  openSourceInPanel(source)
}

function openSourceInPanel(source) {
  sourcePanel.value.source = source
  sourcePanel.value.tab = 'excerpt'
  sourcePanel.value.contentError = null
  sourcePanel.value.screenshotError = null

  if (sourcePanel.value.loadedDocumentId !== source?.document_id) {
    sourcePanel.value.documentContent = ''
    sourcePanel.value.loadedDocumentId = source?.document_id || null
  }

  if (sourcePanel.value.loadedScreenshotDocumentId !== source?.document_id) {
    if (sourcePanel.value.screenshotBlobUrl && String(sourcePanel.value.screenshotBlobUrl).startsWith('blob:')) {
      URL.revokeObjectURL(sourcePanel.value.screenshotBlobUrl)
    }
    sourcePanel.value.screenshotBlobUrl = null
    sourcePanel.value.loadedScreenshotDocumentId = source?.document_id || null
  }
}

async function loadPanelDocumentContent() {
  const source = sourcePanel.value.source
  if (!source?.content_url) return
  if (sourcePanel.value.documentContent) return

  sourcePanel.value.loadingContent = true
  sourcePanel.value.contentError = null
  try {
    const response = await axios.get(source.content_url)
    if (response.data?.success) {
      sourcePanel.value.documentContent = response.data.content || ''
    } else {
      sourcePanel.value.contentError = response.data?.error || 'Konnte Dokumenttext nicht laden'
    }
  } catch (error) {
    sourcePanel.value.contentError = error.response?.data?.error || 'Konnte Dokumenttext nicht laden'
  } finally {
    sourcePanel.value.loadingContent = false
  }
}

async function loadPanelScreenshot() {
  const source = sourcePanel.value.source
  if (!source?.screenshot_url && !source?.document_id) return
  if (sourcePanel.value.screenshotBlobUrl) return

  const url = source.screenshot_url || `/api/rag/documents/${source.document_id}/screenshot`

  sourcePanel.value.loadingScreenshot = true
  sourcePanel.value.screenshotError = null
  try {
    const response = await axios.get(url, { responseType: 'blob' })
    sourcePanel.value.screenshotBlobUrl = URL.createObjectURL(response.data)
  } catch (error) {
    sourcePanel.value.screenshotError = error.response?.data?.error || 'Konnte Screenshot nicht laden'
    sourcePanel.value.screenshotBlobUrl = null
  } finally {
    sourcePanel.value.loadingScreenshot = false
  }
}

watch(
  () => sourcePanel.value.tab,
  async (tab) => {
    if (tab === 'document') {
      await loadPanelDocumentContent()
    }
    if (tab === 'screenshot') {
      await loadPanelScreenshot()
    }
  }
)

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
        openSourceFromCitation(source)
      }
    }
  }
}

/**
 * Open fullscreen dialog for screenshot or document
 */
function openFullscreen(type) {
  fullscreenDialog.value = { show: true, type }
}

// ==================== SOCKET.IO SETUP ====================

/**
 * Initialize Socket.IO connection and event handlers
 */
function initSocket() {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || ''
  const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
  const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

  socket.value = io(baseUrl, {
    path: '/socket.io/',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket
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
    // Reset agent status on completion
    if (data.mode && data.mode !== 'standard') {
      agentStatus.value = { type: 'complete', ...data }
    }
  })

  // Agent status updates (for ACT, ReAct, ReflAct modes)
  socket.value.on('chatbot:agent_status', (data) => {
    // Add unique counter to ensure Vue detects each event
    agentEventCounter.value++
    agentStatus.value = { ...data, _eventId: agentEventCounter.value }
    console.log('Agent status:', data.type, agentEventCounter.value)
  })

  // Error handling
  socket.value.on('chatbot:error', (data) => {
    const errMsg = String(data?.error || '')
    console.error('Chatbot error:', errMsg)

    const code = String(data?.code || '')
    const lower = errMsg.toLowerCase()
    const isAuthError = (
      code.startsWith('AUTH_') ||
      lower.includes('authentication required') ||
      lower.includes('authentication failed') ||
      lower.includes('jwt expired')
    )

    if (isAuthError) {
      clearAuthStorage()
      try {
        localStorage.removeItem('username')
      } catch {}

      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      return
    }

    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx].content = errMsg || 'Ein Fehler ist aufgetreten.'
      messages.value[lastIdx].streaming = false
      messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
    }
    isProcessing.value = false
    showSnackbar(errMsg || 'Fehler beim Senden', 'error')
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
  height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

.chat-container {
  height: 100%;
  display: flex;
  overflow: hidden;
}

/* Sidebar - matching AppSidebar styling */
.chatbot-sidebar {
  width: 260px;
  min-width: 260px;
  height: 100%;
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface-variant), 0.5) 100%);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
}

.chatbot-sidebar.collapsed {
  width: 64px;
  min-width: 64px;
  position: relative;
}

/* Header */
.sidebar-header {
  display: flex;
  align-items: center;
  padding: 12px;
  min-height: 64px;
  gap: 8px;
  position: relative;
}

.header-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  overflow: hidden;
  transition: justify-content 0.25s ease;
}

.header-content.justify-center {
  justify-content: center;
}

.header-icon {
  color: rgb(var(--v-theme-primary));
  flex-shrink: 0;
}

.header-icon-collapsed {
  color: rgb(var(--v-theme-primary));
}

.header-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.header-title {
  font-weight: 600;
  font-size: 15px;
  color: rgb(var(--v-theme-on-surface));
}

.collapse-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.collapsed .sidebar-header {
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 12px 8px;
  gap: 8px;
}

.collapsed .collapse-btn {
  position: static;
  margin-top: 4px;
}

/* Divider */
.sidebar-divider {
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  margin: 0 12px;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: 8px;
  overflow-y: auto;
  overflow-x: hidden;
}

.nav-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.8);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
  font-size: 14px;
  margin-bottom: 4px;
}

.collapsed .nav-item {
  justify-content: center;
  padding: 12px;
}

.nav-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  color: rgb(var(--v-theme-on-surface));
}

.nav-item.active {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.nav-item.active .nav-icon {
  color: rgb(var(--v-theme-primary));
}

.nav-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(var(--v-theme-on-surface), 0.6);
  transition: color 0.2s ease;
}

.nav-item:hover .nav-icon {
  color: rgb(var(--v-theme-primary));
}

.nav-label {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.collapsed .nav-label {
  display: none;
}

.nav-badge {
  flex-shrink: 0;
}

.collapsed .nav-badge {
  display: none;
}

/* Chatbot-specific styles */
.chatbot-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chatbot-description {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Footer */
.sidebar-footer {
  margin-top: auto;
  padding-bottom: 8px;
}

.sidebar-footer .sidebar-divider {
  margin-bottom: 8px;
}

.sidebar-footer .nav-item {
  margin: 0 8px 0;
  width: calc(100% - 16px);
}

.collapsed .sidebar-footer .nav-item {
  width: calc(100% - 16px);
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
  overflow: hidden;
  min-width: 0; /* wichtig für flex */
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

.sources-panel {
  background: rgb(var(--v-theme-surface));
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-width: 0; /* wichtig für flex */
}

/* Resize Divider */
.resize-divider {
  width: 6px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.3);
}

.resize-handle {
  width: 4px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 2px;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
}

.sources-panel-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sources-panel-header {
  padding: 12px 16px;
  background: rgba(var(--v-theme-primary), 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.sources-panel-window {
  flex: 1;
  overflow: hidden;
}

.sources-panel-window :deep(.v-window__container),
.sources-panel-window :deep(.v-window-item) {
  height: 100%;
}

.sources-panel-content {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

.sources-panel-excerpt {
  white-space: pre-wrap;
  line-height: 1.6;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
  font-size: 0.9rem;
}

.sources-panel-text {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 0.85rem;
}

.sources-panel-screenshot :deep(img) {
  cursor: zoom-in;
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

/* Screenshot Card clickable */
.screenshot-card {
  cursor: pointer;
  transition: box-shadow 0.2s ease;
}

.screenshot-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* Fullscreen Dialog */
.fullscreen-dialog-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.fullscreen-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--v-theme-surface));
}

.fullscreen-image-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 24px;
}

.fullscreen-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.fullscreen-document-container {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 32px;
}

.fullscreen-document-text {
  max-width: 900px;
  margin: 0 auto;
  white-space: pre-wrap;
  line-height: 1.8;
  font-size: 1rem;
  background: rgb(var(--v-theme-surface-variant));
  border-radius: 12px;
  padding: 32px;
}

@media (max-width: 960px) {
  .chatbot-sidebar {
    display: none;
  }

  .message-container {
    max-width: 90%;
  }

  .resize-divider {
    display: none;
  }

  .sources-panel {
    position: fixed;
    top: 64px;
    left: 0;
    right: 0;
    bottom: 30px;
    width: 100% !important;
    z-index: 100;
  }
}
</style>
