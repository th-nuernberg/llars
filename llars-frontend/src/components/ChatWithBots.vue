<!-- ChatWithBots.vue - Chat interface with ChatGPT-style grouped sidebar (Refactored) -->
<template>
  <div class="chat-page" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Mobile Navigation Drawer -->
    <MobileChatDrawer
      v-if="isMobile"
      v-model="sidebar.mobileSidebarOpen.value"
      :search-query="sidebar.searchQuery.value"
      :chatbots="chatbots"
      :selected-chatbot="selectedChatbot"
      :selected-conversation="selectedConversation"
      :expanded-bots="sidebar.expandedBots.value"
      :loading="isLoading('chatbots')"
      :get-chat-count="sidebar.getChatCount"
      :get-filtered-conversations="sidebar.getFilteredConversations"
      :get-display-title="sidebar.getDisplayTitle"
      @update:search-query="sidebar.searchQuery.value = $event"
      @new-chat="startNewChat"
      @toggle-bot="handleToggleBot"
      @select-conversation="handleSelectConversation"
      @navigate-home="router.push('/Home')"
    />

    <div class="chat-container" ref="containerRef">
      <!-- Desktop Sidebar -->
      <ChatSidebar
        v-if="!isMobile"
        :collapsed="sidebar.sidebarCollapsed.value"
        :search-query="sidebar.searchQuery.value"
        :chatbots="chatbots"
        :selected-chatbot="selectedChatbot"
        :selected-conversation="selectedConversation"
        :expanded-bots="sidebar.expandedBots.value"
        :loading="isLoading('chatbots')"
        :conversations-loading="isLoading('conversations')"
        :get-chat-count="sidebar.getChatCount"
        :get-filtered-conversations="sidebar.getFilteredConversations"
        :get-display-title="sidebar.getDisplayTitle"
        :get-chatbot-type-tag="sidebar.getChatbotTypeTag"
        @new-chat="startNewChat"
        @toggle-collapse="sidebar.toggleSidebar"
        @update:search-query="sidebar.searchQuery.value = $event"
        @toggle-bot="handleToggleBot"
        @select-conversation="handleSelectConversation"
        @rename-conversation="renameConversation"
        @delete-conversation="deleteConversation"
        @navigate-home="router.push('/Home')"
      />

      <!-- Main Chat Area -->
      <div class="chat-main" :style="sourcePanelState.open ? leftPanelStyle() : {}">
        <!-- Chat Header -->
        <div v-if="selectedChatbot" class="chat-header">
          <div class="header-left">
            <v-btn
              v-if="isMobile"
              icon
              variant="text"
              size="small"
              class="mr-2"
              @click="sidebar.mobileSidebarOpen.value = true"
            >
              <LIcon>mdi-menu</LIcon>
            </v-btn>
            <v-avatar :color="selectedChatbot.color || '#b0ca97'" :size="isMobile ? 32 : 36" class="bot-avatar">
              <LIcon color="white" :size="isMobile ? 18 : 20">{{ selectedChatbot.icon || 'mdi-robot' }}</LIcon>
            </v-avatar>
            <div class="header-info">
              <div class="header-title" :class="{ 'streaming-text': getHeaderTitle().isStreaming }">
                {{ getHeaderTitle().text }}
                <span v-if="getHeaderTitle().isStreaming" class="typing-cursor"></span>
              </div>
              <div class="header-subtitle">
                {{ selectedChatbot.display_name }}
                <span class="model-name">• {{ selectedChatbot.model_name }}</span>
                <LTag v-if="capabilities?.vision" variant="success" size="sm" class="ml-1">
                  Vision
                </LTag>
              </div>
            </div>
          </div>
          <div class="header-actions">
            <LTooltip :text="sourcePanelState.open ? $t('chat.hideSources') : $t('chat.showSources')">
              <button class="header-action" @click="sourcePanelComposable.toggleSourcePanel">
                <LIcon size="20">{{ sourcePanelState.open ? 'mdi-text-box-remove-outline' : 'mdi-text-box-search-outline' }}</LIcon>
              </button>
            </LTooltip>
            <LTooltip :text="$t('chat.newChat')">
              <button class="header-action" @click="startNewChat()">
                <LIcon size="20">mdi-plus</LIcon>
              </button>
            </LTooltip>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!selectedChatbot" class="empty-state">
          <v-btn
            v-if="isMobile"
            icon
            variant="tonal"
            color="primary"
            size="large"
            class="mb-4"
            @click="sidebar.mobileSidebarOpen = true"
          >
            <LIcon>mdi-menu</LIcon>
          </v-btn>
          <LIcon :size="isMobile ? 60 : 80" color="grey-lighten-1">mdi-robot-confused</LIcon>
          <h3 :class="isMobile ? 'text-h6 mt-3' : 'text-h5 mt-4'">{{ $t('chat.selectChatbot') }}</h3>
          <p class="text-medium-emphasis" :class="isMobile ? 'text-body-2 px-4' : ''">
            {{ isMobile ? $t('chat.selectChatbotHintMobile') : $t('chat.selectChatbotHint') }}
          </p>
        </div>

        <!-- Chat Messages -->
        <ChatMessageList
          v-else
          ref="messageListRef"
          :messages="messages"
          :chatbot="selectedChatbot"
          @show-source="sourcePanelComposable.showSourceDetail"
          @footnote-click="sourcePanelComposable.openSourceFromCitation"
        >
          <template #agent-reasoning>
            <AgentReasoningDisplay
              ref="agentReasoningRef"
              :agent-status="agentStatus"
              :is-processing="chatMessages.isProcessing.value"
            />
          </template>
        </ChatMessageList>

        <!-- Chat Input -->
        <ChatInput
          v-if="selectedChatbot"
          v-model="newMessage"
          ref="chatInputRef"
          :loading="chatMessages.isProcessing.value"
          :disabled="chatMessages.isProcessing.value"
          :supports-vision="capabilities?.vision"
          @send="handleSendMessage"
        />
      </div>

      <!-- Resize Divider -->
      <div
        v-if="sourcePanelState.open"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Sources Side Panel -->
      <SourcePanel
        v-if="sourcePanelState.open"
        :source="sourcePanelState.source"
        :active-tab="sourcePanelState.tab"
        :pinned="sourcePanelState.pinned"
        :panel-style="rightPanelStyle()"
        :document-content="sourcePanelState.documentContent"
        :screenshot-url="sourcePanelState.screenshotBlobUrl"
        :loading-screenshot="sourcePanelState.loadingScreenshot"
        :loading-content="sourcePanelState.loadingContent"
        :screenshot-error="sourcePanelState.screenshotError"
        :content-error="sourcePanelState.contentError"
        @close="sourcePanelComposable.closeSourcePanel"
        @update:pinned="sourcePanelState.pinned = $event"
        @update:active-tab="sourcePanelState.tab = $event"
        @fullscreen="sourcePanelComposable.openFullscreen"
      />
    </div>

    <!-- Fullscreen Dialog -->
    <v-dialog v-model="fullscreenDialog.show" fullscreen transition="dialog-bottom-transition">
      <div class="fullscreen-dialog">
        <div class="fullscreen-header">
          <div class="fullscreen-title">
            <LIcon size="20" class="mr-2">{{ fullscreenDialog.type === 'screenshot' ? 'mdi-image' : 'mdi-file-document' }}</LIcon>
            <span>{{ sourcePanelState.source?.title || sourcePanelState.source?.filename || $t('chat.source') }}</span>
          </div>
          <button class="fullscreen-close" @click="fullscreenDialog.show = false">
            <LIcon size="20">mdi-close</LIcon>
          </button>
        </div>
        <div class="fullscreen-body">
          <template v-if="fullscreenDialog.type === 'screenshot'">
            <div class="fullscreen-image-wrapper">
              <img
                v-if="sourcePanelState.screenshotBlobUrl"
                :src="sourcePanelState.screenshotBlobUrl"
                alt="Screenshot"
                class="fullscreen-img"
              />
            </div>
          </template>
          <template v-else-if="fullscreenDialog.type === 'document'">
            <div class="fullscreen-document-wrapper">
              <div class="fullscreen-doc-text">
                {{ sourcePanelState.documentContent }}
              </div>
            </div>
          </template>
        </div>
      </div>
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
          {{ sourceDialog.source?.title || sourceDialog.source?.filename || $t('chat.source') }}
        </v-card-title>
        <v-card-subtitle v-if="sourceDialog.source?.collection_name">
          <LIcon size="14" class="mr-1">mdi-folder</LIcon>
          {{ sourceDialog.source?.collection_name }}
          <LTag variant="success" size="sm" class="ml-2">
            {{ ((sourceDialog.source?.relevance || 0) * 100).toFixed(0) }}% {{ $t('chat.relevant') }}
          </LTag>
        </v-card-subtitle>
        <v-divider />
        <v-card-text class="source-excerpt">
          {{ sourceDialog.source?.excerpt }}
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="sourcePanelComposable.pinSourceToPanel(sourceDialog.source)">
            <LIcon start>mdi-pin</LIcon>
            {{ $t('chat.pinSource') }}
          </v-btn>
          <v-btn
            v-if="sourceDialog.source?.download_url"
            :href="sourceDialog.source.download_url"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="tonal"
          >
            <LIcon start>mdi-download</LIcon>
            {{ $t('chat.document') }}
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="sourceDialog.show = false">
            {{ $t('common.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

// Composables
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'
import { useActiveDuration, useTypingMetrics, useScrollDepth } from '@/composables/useAnalyticsMetrics'
import { matomoTrackEvent } from '@/plugins/llars-metrics'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { logI18n } from '@/utils/logI18n'

// Local composables
import { useChatMessages } from './ChatWithBots/composables/useChatMessages.js'
import { useChatSocket } from './ChatWithBots/composables/useChatSocket.js'
import { useChatSidebar } from './ChatWithBots/composables/useChatSidebar.js'
import { useSourcePanel } from './ChatWithBots/composables/useSourcePanel.js'

// Components
import ChatSidebar from './ChatWithBots/sidebar/ChatSidebar.vue'
import ChatMessageList from './ChatWithBots/messages/ChatMessageList.vue'
import ChatInput from './ChatWithBots/input/ChatInput.vue'
import SourcePanel from './ChatWithBots/panels/SourcePanel.vue'
import MobileChatDrawer from './ChatWithBots/mobile/MobileChatDrawer.vue'
import AgentReasoningDisplay from './Chat/AgentReasoningDisplay.vue'

// ==================== COMPOSABLES ====================

const chatMessages = useChatMessages()
const chatSocket = useChatSocket()
const sidebar = useChatSidebar()
const sourcePanelComposable = useSourcePanel()
// Destructure refs for proper Vue reactivity in template
const {
  sourcePanel: sourcePanelState,
  sourceDialog,
  fullscreenDialog
} = sourcePanelComposable
const { isLoading, withLoading } = useSkeletonLoading(['chatbots', 'conversations'])
const { isMobile, isTablet } = useMobile()

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

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// ==================== STATE ====================

const chatbots = ref([])
const selectedChatbot = ref(null)
const capabilities = ref(null)
const conversations = ref([])
const selectedConversation = ref(null)
const messages = ref([])
const newMessage = ref('')
const sessionId = ref(null)

// Agent status
const agentStatus = ref(null)
const agentEventCounter = ref(0)

// Refs
const messageListRef = ref(null)
const chatInputRef = ref(null)
const agentReasoningRef = ref(null)

// Timeout for processing fallback
let processingTimeoutId = null
const PROCESSING_TIMEOUT_MS = 120000 // 2 minutes

// Snackbar
const snackbar = ref({ show: false, text: '', color: 'success' })

// Draft Storage Key
const DRAFT_STORAGE_KEY = 'llars-chat-drafts'

// ==================== ANALYTICS ====================

const chatbotEntity = computed(() => selectedChatbot.value ? `bot:${selectedChatbot.value.id}` : '')

useActiveDuration({
  category: 'chat',
  action: 'session_active_ms',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

const typingMetrics = useTypingMetrics({
  category: 'chat',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

watch(newMessage, (newVal, oldVal) => {
  if (newVal.length > oldVal.length) {
    typingMetrics.recordInput(newVal.length - oldVal.length)
  }
})

useScrollDepth(computed(() => messageListRef.value?.containerRef), {
  category: 'chat',
  action: 'scroll_depth',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

// ==================== COMPUTED ====================

function getHeaderTitle() {
  if (sidebar.streamingTitle.value.isStreaming && sidebar.streamingTitle.value.conversationId === selectedConversation.value?.id) {
    return { text: sidebar.streamingTitle.value.text || '', isStreaming: true }
  }
  return { text: selectedConversation.value?.title || selectedChatbot.value?.display_name || '', isStreaming: false }
}

// ==================== CHATBOT MANAGEMENT ====================

async function loadChatbots() {
  try {
    const response = await axios.get('/api/chatbots')
    if (response.data.success) {
      chatbots.value = response.data.chatbots.filter(b => b.is_active)
    }
  } catch (error) {
    logI18n('error', 'logs.chatWithBots.loadChatbotsFailed', error)
    showSnackbar(t('chat.loadChatbotsFailed'), 'error')
  }
}

async function selectChatbot(bot, createNewChat = false) {
  matomoTrackEvent('chat', 'chatbot_select', `bot:${bot.id}`, 1, { entity: `bot:${bot.id}` })

  // Save draft before switching chatbot
  saveDraft()

  selectedChatbot.value = bot
  messages.value = []
  sessionId.value = null
  selectedConversation.value = null
  conversations.value = []
  agentStatus.value = null
  chatMessages.isProcessing.value = false // Reset processing state
  agentReasoningRef.value?.reset?.()

  sidebar.expandBot(bot.id)

  try {
    const response = await axios.get(`/api/chatbots/${bot.id}/capabilities`)
    if (response.data.success) {
      capabilities.value = response.data.capabilities
    }
  } catch (error) {
    capabilities.value = { vision: false, rag: bot.rag_enabled }
  }

  // Load conversations but don't auto-select
  await loadConversations(false)

  // Restore draft for this chatbot if exists
  restoreDraft()

  // Only create conversation if explicitly requested (e.g., via "New Chat" button)
  if (createNewChat) {
    await createConversation()
  }
}

// ==================== CONVERSATIONS ====================

async function loadConversations(autoSelect = false) {
  if (!selectedChatbot.value) return
  const botId = selectedChatbot.value.id

  await withLoading('conversations', async () => {
    try {
      const response = await axios.get(`/api/chatbots/${botId}/conversations`)
      conversations.value = response.data.conversations || []
      sidebar.setBotConversations(botId, conversations.value)
    } catch (error) {
      logI18n('error', 'logs.chatWithBots.loadConversationsFailed', error)
      conversations.value = []
    }
  })

  // Only auto-select if explicitly requested (e.g., after deleting current conversation)
  if (autoSelect && conversations.value.length > 0) {
    await selectConversation(conversations.value[0])
  }
}

/**
 * Start a new chat - resets state without creating conversation in DB.
 * The actual conversation is created lazily when the first message is sent.
 */
function startNewChat() {
  if (!selectedChatbot.value) return

  // Save any existing draft before starting new chat
  saveDraft()

  // Reset state for new chat
  selectedConversation.value = null
  messages.value = []
  sessionId.value = crypto.randomUUID()
  newMessage.value = ''
  agentStatus.value = null
  agentReasoningRef.value?.reset?.()
  chatMessages.isProcessing.value = false
}

/**
 * Create a conversation in the database.
 * Called lazily when the first message is sent.
 */
async function createConversation(title = null) {
  if (!selectedChatbot.value) return
  const botId = selectedChatbot.value.id

  try {
    const response = await axios.post(`/api/chatbots/${botId}/conversations`, {
      title: title || 'Neuer Chat'
    })
    if (response.data.success) {
      const convo = response.data.conversation
      conversations.value = [convo, ...conversations.value]
      // Don't add to sidebar yet - only show in history after first message is sent
      // sidebar.upsertConversation() is called in socket response handler
      selectedConversation.value = convo
      sessionId.value = convo.session_id
    }
  } catch (error) {
    showSnackbar(t('chat.createChatFailed'), 'error')
  }
}

async function selectConversation(conversation) {
  if (!conversation || !selectedChatbot.value) return

  // Save draft before switching conversations
  saveDraft()

  selectedConversation.value = conversation
  sessionId.value = conversation.session_id

  // Reset processing state when switching conversations
  chatMessages.isProcessing.value = false
  sourcePanelComposable.resetForConversationChange()
  agentStatus.value = null
  agentReasoningRef.value?.reset?.()
  newMessage.value = '' // Clear input when switching conversations

  await loadConversationMessages(conversation.id)
}

async function loadConversationMessages(conversationId) {
  if (!selectedChatbot.value || !conversationId) return

  try {
    const response = await axios.get(`/api/chatbots/${selectedChatbot.value.id}/conversations/${conversationId}`)
    if (response.data.success) {
      const convo = response.data.conversation
      selectedConversation.value = { ...convo }
      sessionId.value = convo.session_id
      messages.value = (convo.messages || []).map(m => ({
        id: m.id,
        sender: m.role === 'user' ? 'user' : 'bot',
        content: m.content,
        sources: m.rag_sources,
        agentTrace: Array.isArray(m.agent_trace) ? m.agent_trace : [],
        streamMetadata: m.stream_metadata || null,
        timestamp: m.created_at ? new Date(m.created_at).toLocaleTimeString() : '',
        streaming: false
      }))

      const lastAgentMessage = [...(convo.messages || [])]
        .reverse()
        .find(m => m.role === 'assistant' && Array.isArray(m.agent_trace) && m.agent_trace.length > 0)

      if (lastAgentMessage) {
        agentEventCounter.value++
        agentStatus.value = {
          type: 'complete',
          mode: lastAgentMessage.stream_metadata?.mode || selectedChatbot.value?.prompt_settings?.agent_mode || 'standard',
          task_type: selectedChatbot.value?.prompt_settings?.task_type || 'lookup',
          reasoning_steps: lastAgentMessage.agent_trace,
          _eventId: agentEventCounter.value
        }
      }
    }
  } catch (error) {
    showSnackbar(t('chat.loadChatFailed'), 'error')
    messages.value = []
  }
}

function updateConversationTitle(conversationId, title) {
  if (!conversationId || !title) return
  if (selectedConversation.value?.id === conversationId) {
    selectedConversation.value = { ...selectedConversation.value, title }
  }
  const idx = conversations.value.findIndex(c => c.id === conversationId)
  if (idx !== -1) {
    conversations.value[idx] = { ...conversations.value[idx], title }
  }
  if (selectedChatbot.value?.id) {
    sidebar.updateConversationTitle(selectedChatbot.value.id, conversationId, title)
  }
}

async function renameConversation(conv) {
  const newTitle = prompt(t('chat.renamePrompt'), conv.title || t('chat.newChat'))
  if (!newTitle || newTitle === conv.title) return

  try {
    await axios.patch(`/api/chatbots/${selectedChatbot.value?.id}/conversations/${conv.id}`, { title: newTitle })
    updateConversationTitle(conv.id, newTitle)
    showSnackbar(t('chat.chatRenamed'), 'success')
  } catch (error) {
    showSnackbar(t('chat.renameFailed'), 'error')
  }
}

async function deleteConversation(conv) {
  if (!confirm(t('chat.deleteConfirm'))) return

  const botId = selectedChatbot.value?.id
  try {
    await axios.delete(`/api/chatbots/${botId}/conversations/${conv.id}`)
    conversations.value = conversations.value.filter(c => c.id !== conv.id)
    sidebar.removeConversation(botId, conv.id)

    // If we deleted the currently selected conversation, select another or start fresh
    if (selectedConversation.value?.id === conv.id) {
      if (conversations.value.length > 0) {
        // Select the first available conversation
        await selectConversation(conversations.value[0])
      } else {
        // No conversations left, reset to new chat state (lazy creation)
        startNewChat()
      }
    }
    showSnackbar(t('chat.chatDeleted'), 'success')
  } catch (error) {
    showSnackbar(t('chat.deleteFailed'), 'error')
  }
}

// ==================== MESSAGE HANDLING ====================

async function handleSendMessage({ message, files }) {
  if ((!message && files.length === 0) || chatMessages.isProcessing.value) return
  if (!selectedChatbot.value) return
  if (!sessionId.value) sessionId.value = crypto.randomUUID()

  // Lazy chat creation: only create conversation when actually sending a message
  if (!selectedConversation.value) await createConversation()

  if (message) {
    const bucket = message.length < 50 ? 'short' : message.length < 200 ? 'medium' : 'long'
    matomoTrackEvent('chat', 'message_send', `${chatbotEntity.value}|len:${bucket}`, message.length, { entity: chatbotEntity.value })
  }

  chatMessages.addUserMessage(messages, message, files)
  newMessage.value = ''

  // Clear draft after successfully adding message to queue
  clearDraft()
  chatMessages.isProcessing.value = true
  agentReasoningRef.value?.reset?.()

  const agentMode = selectedChatbot.value?.prompt_settings?.agent_mode
  if (agentMode && agentMode !== 'standard') {
    agentEventCounter.value++
    agentStatus.value = {
      type: 'init',
      mode: agentMode,
      task_type: selectedChatbot.value?.prompt_settings?.task_type || 'lookup',
      max_iterations: selectedChatbot.value?.prompt_settings?.agent_max_iterations || 5,
      _eventId: agentEventCounter.value
    }
  } else {
    agentStatus.value = null
  }

  chatMessages.addBotPlaceholder(messages)
  messageListRef.value?.scrollToBottom()

  // Start timeout as fallback
  startProcessingTimeout()

  if (files.length > 0 || !chatSocket.isConnected.value) {
    await sendMessageViaREST(message, files)
  } else {
    chatSocket.sendMessage(selectedChatbot.value.id, message, sessionId.value, selectedConversation.value?.id)
  }
}

async function sendMessageViaREST(message, files = []) {
  try {
    const result = await chatMessages.sendViaREST(
      selectedChatbot.value.id,
      message,
      sessionId.value,
      files,
      selectedConversation.value?.id || null
    )

    if (result.success) {
      if (result.sessionId) sessionId.value = result.sessionId
      if (result.conversationId && (!selectedConversation.value || selectedConversation.value.id !== result.conversationId)) {
        selectedConversation.value = {
          ...(selectedConversation.value || {}),
          id: result.conversationId,
          session_id: result.sessionId || sessionId.value,
          title: result.conversationTitle || selectedConversation.value?.title
        }
        conversations.value = [
          { id: result.conversationId, session_id: result.sessionId || sessionId.value, title: result.conversationTitle || 'Neuer Chat', message_count: 0 },
          ...conversations.value.filter(c => c.id !== result.conversationId)
        ]
      }
      if (result.conversationTitle) {
        updateConversationTitle(result.conversationId || selectedConversation.value?.id, result.conversationTitle)
      }
      chatMessages.updateBotMessage(messages, result.content, new Date().toLocaleTimeString(), false, result.sources)
      // Automatically show first source in panel
      if (result.sources && result.sources.length > 0) {
        sourcePanelComposable.openSourceFromCitation(result.sources[0])
      }
      if (result.mode && result.mode !== 'standard') {
        agentEventCounter.value++
        agentStatus.value = { type: 'complete', mode: result.mode, task_type: result.task_type, reasoning_steps: result.reasoning_steps || [], _eventId: agentEventCounter.value }
      }
    } else {
      chatMessages.setBotError(messages)
      showSnackbar(result.error || t('chat.sendFailed'), 'error')
    }
  } catch (error) {
    chatMessages.setBotError(messages)
    showSnackbar(t('chat.sendFailed'), 'error')
  } finally {
    clearProcessingTimeout()
    chatMessages.isProcessing.value = false
    messageListRef.value?.scrollToBottom()
  }
}

// ==================== UI UTILITIES ====================

function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// ==================== DRAFT PERSISTENCE ====================

/**
 * Save current draft message to localStorage
 * Saves per chatbot ID so each chatbot has its own draft
 */
function saveDraft() {
  if (!selectedChatbot.value) return

  const botId = selectedChatbot.value.id
  const draftText = newMessage.value?.trim()

  try {
    const drafts = JSON.parse(localStorage.getItem(DRAFT_STORAGE_KEY) || '{}')

    if (draftText) {
      drafts[botId] = {
        text: draftText,
        timestamp: Date.now(),
        conversationId: selectedConversation.value?.id || null
      }
    } else {
      // Remove draft if empty
      delete drafts[botId]
    }

    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(drafts))
  } catch (error) {
    logI18n('warn', 'logs.chatWithBots.draftSaveFailed', error)
  }
}

/**
 * Restore draft message from localStorage for current chatbot
 */
function restoreDraft() {
  if (!selectedChatbot.value) return

  const botId = selectedChatbot.value.id

  try {
    const drafts = JSON.parse(localStorage.getItem(DRAFT_STORAGE_KEY) || '{}')
    const draft = drafts[botId]

    if (draft?.text) {
      newMessage.value = draft.text
      // If draft has a conversation ID, try to select that conversation
      if (draft.conversationId) {
        const conv = conversations.value.find(c => c.id === draft.conversationId)
        if (conv) {
          selectConversation(conv)
        }
      }
    } else {
      newMessage.value = ''
    }
  } catch (error) {
    logI18n('warn', 'logs.chatWithBots.draftRestoreFailed', error)
    newMessage.value = ''
  }
}

/**
 * Clear draft for current chatbot (called after successful message send)
 */
function clearDraft() {
  if (!selectedChatbot.value) return

  const botId = selectedChatbot.value.id

  try {
    const drafts = JSON.parse(localStorage.getItem(DRAFT_STORAGE_KEY) || '{}')
    delete drafts[botId]
    localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(drafts))
  } catch (error) {
    logI18n('warn', 'logs.chatWithBots.draftDeleteFailed', error)
  }
}

/**
 * Start processing timeout as fallback
 */
function startProcessingTimeout() {
  clearProcessingTimeout()
  processingTimeoutId = setTimeout(() => {
    if (chatMessages.isProcessing.value) {
      logI18n('warn', 'logs.chatWithBots.processingTimeoutReset')
      chatMessages.isProcessing.value = false
      const lastIdx = messages.value.length - 1
      if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot' && messages.value[lastIdx].streaming) {
        messages.value[lastIdx].streaming = false
        if (!messages.value[lastIdx].content) {
          messages.value[lastIdx].content = t('chat.responseTimeoutMessage')
        }
      }
      showSnackbar(t('chat.responseTimeout'), 'warning')
    }
  }, PROCESSING_TIMEOUT_MS)
}

/**
 * Clear processing timeout
 */
function clearProcessingTimeout() {
  if (processingTimeoutId) {
    clearTimeout(processingTimeoutId)
    processingTimeoutId = null
  }
}

function handleToggleBot(bot) {
  sidebar.toggleBot(bot, selectChatbot, sidebar.loadBotConversations)
}

function handleSelectConversation(bot, conv) {
  if (selectedChatbot.value?.id !== bot.id) {
    // Select bot without creating new chat, then select the conversation
    selectChatbot(bot, false).then(() => selectConversation(conv))
  } else {
    selectConversation(conv)
  }
}

async function maybeAutoSelectFromRoute() {
  const raw = route.query.chatbot_id || route.query.bot
  const id = raw ? parseInt(String(raw), 10) : null
  if (!id || Number.isNaN(id)) return
  if (selectedChatbot.value?.id === id) return

  const bot = chatbots.value.find(b => b.id === id)
  if (!bot) {
    showSnackbar(t('chat.chatbotNotAvailable'), 'warning')
    return
  }
  await selectChatbot(bot)
}

// ==================== SOCKET HANDLERS ====================

function setupSocketHandlers() {
  chatSocket.registerHandlers({
    onSources: (data) => {
      chatMessages.currentSources.value = data.sources || []
      const lastIdx = messages.value.length - 1
      if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
        messages.value[lastIdx].sources = chatMessages.currentSources.value
      }
      // Automatically show first source in panel
      if (data.sources && data.sources.length > 0) {
        sourcePanelComposable.openSourceFromCitation(data.sources[0])
      }
    },
    onResponse: (data) => {
      const lastIdx = messages.value.length - 1
      if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
        if (data.content) {
          messages.value[lastIdx].content += data.content
          messageListRef.value?.scrollToBottom()
        }
        if (data.complete) {
          clearProcessingTimeout()
          messages.value[lastIdx].streaming = false
          messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
          if (chatMessages.currentSources.value.length > 0 && !messages.value[lastIdx].sources) {
            messages.value[lastIdx].sources = chatMessages.currentSources.value
          }
          chatMessages.currentSources.value = []
          chatMessages.isProcessing.value = false
          messageListRef.value?.scrollToBottom()
        }
      }
    },
    onComplete: (data) => {
      const convId = data.conversation_id || selectedConversation.value?.id
      const convTitle = data.title || selectedConversation.value?.title || 'Neuer Chat'

      if (convId && (!selectedConversation.value || selectedConversation.value.id !== convId)) {
        selectedConversation.value = { ...(selectedConversation.value || {}), id: convId, session_id: data.session_id || sessionId.value, title: convTitle }
        conversations.value = [{ id: convId, session_id: data.session_id || sessionId.value, title: convTitle }, ...conversations.value.filter(c => c.id !== convId)]
      }
      // Always add/update conversation in sidebar after first message completes
      if (convId && selectedChatbot.value?.id) {
        sidebar.upsertConversation(selectedChatbot.value.id, { id: convId, session_id: data.session_id || sessionId.value, title: convTitle })
      }
      if (data.title) updateConversationTitle(convId || selectedConversation.value?.id, data.title)
      if (data.session_id && !sessionId.value) sessionId.value = data.session_id
      if (data.mode && data.mode !== 'standard') agentStatus.value = { type: 'complete', ...data }
    },
    onAgentStatus: (data) => {
      agentEventCounter.value++
      agentStatus.value = { ...data, _eventId: agentEventCounter.value }
    },
    onTitleGenerating: (data) => {
      sidebar.startTitleStreaming(data.conversation_id || selectedConversation.value?.id)
    },
    onTitleDelta: (data) => {
      sidebar.appendTitleDelta(data.delta, data.conversation_id)
    },
    onTitleComplete: (data) => {
      const convId = data.conversation_id || sidebar.streamingTitle.value.conversationId
      if (data.title && convId) updateConversationTitle(convId, data.title)
      sidebar.completeTitleStreaming()
    },
    onError: (data) => {
      clearProcessingTimeout()
      const errMsg = String(data?.error || '')
      const lastIdx = messages.value.length - 1
      if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
        messages.value[lastIdx].content = errMsg || t('chat.errorOccurred')
        messages.value[lastIdx].streaming = false
        messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
      }
      chatMessages.isProcessing.value = false
      showSnackbar(errMsg || t('chat.sendFailed'), 'error')
    }
  })
}

// ==================== LIFECYCLE ====================

/**
 * Handle browser/tab close - save draft
 */
function handleBeforeUnload() {
  saveDraft()
}

onMounted(async () => {
  // Add beforeunload listener to save draft when closing tab/browser
  window.addEventListener('beforeunload', handleBeforeUnload)

  await withLoading('chatbots', loadChatbots)
  for (const bot of chatbots.value) {
    sidebar.loadBotConversations(bot.id)
  }
  await maybeAutoSelectFromRoute()
  chatSocket.initSocket()
  setupSocketHandlers()
})

onUnmounted(() => {
  // Remove beforeunload listener
  window.removeEventListener('beforeunload', handleBeforeUnload)
  // Save draft before leaving the page
  saveDraft()
  clearProcessingTimeout()
  chatSocket.disconnectSocket()
})
</script>

<style scoped>
/* Import extracted styles */
@import './ChatWithBots/styles/ChatWithBots.css';
</style>
