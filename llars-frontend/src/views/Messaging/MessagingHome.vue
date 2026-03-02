<template>
  <div class="messaging-page" :class="{ 'chat-active': activeConversationId }">
    <!-- Communication disabled overlay (only after status is loaded) -->
    <Transition name="fade">
      <div v-if="showDisabledOverlay" class="messaging-disabled-overlay">
        <div class="messaging-disabled-content">
          <v-icon size="72" color="grey-lighten-1" class="mb-4">mdi-message-off-outline</v-icon>
          <h2 class="text-h5 font-weight-medium mb-2">{{ $t('messaging.unavailable') }}</h2>
          <p class="text-body-1" style="opacity: 0.6; max-width: 400px;">
            {{ $t('messaging.unavailableHint') }}
          </p>
          <LBtn variant="secondary" class="mt-6" prepend-icon="mdi-home" @click="$router.push('/home')">
            {{ $t('messaging.backToHome') }}
          </LBtn>
        </div>
      </div>
    </Transition>

    <!-- Conversation List (left panel) -->
    <ConversationList
      :conversations="sortedConversations"
      :active-conversation-id="activeConversationId"
      :is-loading="isLoading"
      @select="selectConversation"
      @new-chat="showNewChatDialog = true"
      @new-group="showCreateGroupDialog = true"
    />

    <!-- Chat Panel (right panel) -->
    <template v-if="activeConversation">
      <ChatPanel
        :conversation="activeConversation"
        :messages="chatMessages"
        :is-loading="chatLoading"
        :has-more="chatHasMore"
        :typing-users="typingUsers"
        :show-back-button="isMobile"
        :last-read-message-id="lastReadMessageId"
        @send="handleSend"
        @edit="handleEdit"
        @delete="handleDelete"
        @react="handleReact"
        @load-more="loadMore"
        @typing="emitTyping"
        @back="clearActiveConversation"
        @toggle-group-info="showGroupInfo = !showGroupInfo"
        @call="handleCall"
      />

      <!-- Active Call Panels -->
      <VoiceCallPanel
        v-if="isInCall && callType === 'voice'"
        :duration="callDuration"
        :is-muted="isMuted"
        @toggle-mute="toggleMute"
        @end-call="handleEndCall"
      />
      <VideoCallPanel
        v-if="isInCall && callType === 'video'"
        :local-tracks="localTracks"
        :remote-tracks="remoteTracks"
        :duration="callDuration"
        :is-muted="isMuted"
        :is-camera-off="isCameraOff"
        @toggle-mute="toggleMute"
        @toggle-camera="toggleCamera"
        @end-call="handleEndCall"
      />

      <!-- Transcription Side Panel -->
      <TranscriptionPanel
        v-if="isInCall && showTranscription"
        :chunks="transcriptChunks"
        :is-transcribing="isTranscribing"
        @close="showTranscription = false"
      />

      <!-- Group Info Side Panel -->
      <GroupInfoPanel
        v-if="showGroupInfo && activeConversation?.conversation_type === 'group'"
        :conversation="activeConversation"
        @add-member="handleAddMember"
        @remove-member="handleRemoveMember"
        @leave-group="handleLeaveGroup"
      />
    </template>

    <!-- No conversation selected -->
    <div v-else class="no-conversation-selected">
      <v-icon size="64">mdi-message-text-outline</v-icon>
      <p class="mt-4 text-h6">{{ $t('messaging.selectConversation') }}</p>
      <p class="text-body-2 mt-1" style="opacity: 0.6">
        {{ $t('messaging.selectConversationHint') }}
      </p>
    </div>

    <!-- Incoming Call Overlay -->
    <CallOverlay
      :incoming-call="incomingCall"
      @accept="acceptCall"
      @decline="declineCall"
    />

    <!-- Dialogs -->
    <NewChatDialog
      v-model="showNewChatDialog"
      @create="handleCreateDirectChat"
    />
    <CreateGroupDialog
      v-model="showCreateGroupDialog"
      @create="handleCreateGroup"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, toRef, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessaging } from './composables/useMessaging'
import { useChat } from './composables/useChat'
import { useTypingIndicator } from './composables/useTypingIndicator'
import { useConversations } from './composables/useConversations'
import { useMobile } from '@/composables/useMobile'
import { useSnackbar } from '@/composables/useSnackbar'
import { useAuth } from '@/composables/useAuth'
import { useCommunicationAdmin } from '@/composables/useCommunicationAdmin'
import { usePermissions } from '@/composables/usePermissions'
import { useCallManager } from './composables/useCallManager'
import { useTranscription } from './composables/useTranscription'
import ConversationList from './components/ConversationList.vue'
import ChatPanel from './components/ChatPanel.vue'
import GroupInfoPanel from './components/GroupInfoPanel.vue'
import NewChatDialog from './components/NewChatDialog.vue'
import CreateGroupDialog from './components/CreateGroupDialog.vue'
import CallOverlay from './components/CallOverlay.vue'
import VoiceCallPanel from './components/VoiceCallPanel.vue'
import VideoCallPanel from './components/VideoCallPanel.vue'
import TranscriptionPanel from './components/TranscriptionPanel.vue'

import './styles/Messaging.css'

const route = useRoute()
const router = useRouter()
const { isMobile } = useMobile()
const { showError } = useSnackbar()
const { communicationEnabled, loaded: commLoaded, refreshCommunicationStatus } = useCommunicationAdmin()
const { hasPermission, fetchPermissions } = usePermissions()

// Only show overlay after both communication status AND permissions are loaded
const showDisabledOverlay = computed(() =>
  commLoaded.value && (!communicationEnabled.value || !hasPermission('feature:communication:access'))
)

// ── Poll for permission/status changes (reliable fallback for Socket.IO) ──
let _accessPollTimer = null
function startAccessPoll() {
  if (_accessPollTimer) return
  _accessPollTimer = setInterval(async () => {
    await Promise.all([
      refreshCommunicationStatus(),
      fetchPermissions(true),
    ])
  }, 10_000)
}
function stopAccessPoll() {
  if (_accessPollTimer) { clearInterval(_accessPollTimer); _accessPollTimer = null }
}

// ── Messaging state ───────────────────────────────────────────────
const {
  sortedConversations,
  activeConversationId,
  activeConversation,
  isLoading,
  fetchConversations,
  fetchUnreadCounts,
  setActiveConversation,
  createDirectChat,
  createGroupChat,
  updateConversationInList,
  initSocket,
  cleanup: cleanupMessaging,
} = useMessaging()

// ── Chat (messages for active conversation) ───────────────────────
const convIdRef = toRef(() => activeConversationId.value)

const {
  messages: chatMessages,
  isLoading: chatLoading,
  hasMore: chatHasMore,
  loadMore,
  sendMessage,
  editMessage,
  deleteMessage,
  toggleReaction,
  markAsRead,
  setupSocketListeners,
  cleanupSocketListeners,
} = useChat(convIdRef)

// ── Typing ────────────────────────────────────────────────────────
const {
  typingUsers,
  emitTyping,
  setupListeners: setupTypingListeners,
  cleanupListeners: cleanupTypingListeners,
} = useTypingIndicator(convIdRef)

// ── Call manager ─────────────────────────────────────────────────
const {
  isInCall,
  callType,
  callDuration,
  incomingCall,
  localTracks,
  remoteTracks,
  isMuted,
  isCameraOff,
  initiateCall,
  acceptCall,
  declineCall,
  endCall,
  toggleMute,
  toggleCamera,
  setupCallListeners,
  cleanupCallListeners,
} = useCallManager()

// ── Transcription ────────────────────────────────────────────────
const {
  chunks: transcriptChunks,
  isTranscribing,
  setupListeners: setupTranscriptionListeners,
  cleanupListeners: cleanupTranscriptionListeners,
  clearTranscript,
} = useTranscription()

const showTranscription = ref(false)

// ── Conversations management ──────────────────────────────────────
const { addMember, removeMember } = useConversations()

// ── UI State ──────────────────────────────────────────────────────
const showNewChatDialog = ref(false)
const showCreateGroupDialog = ref(false)
const showGroupInfo = ref(false)

// ── Last Read Message ID (for unread marker) ─────────────────────
const { tokenParsed } = useAuth()
const currentUsername = computed(() => tokenParsed.value?.preferred_username || '')

const lastReadMessageId = computed(() => {
  if (!activeConversation.value) return null
  const participants = activeConversation.value.participants || []
  const me = participants.find((p) => p.username === currentUsername.value)
  return me?.last_read_message_id || null
})

// ── Actions ───────────────────────────────────────────────────────
const selectConversation = (id) => {
  setActiveConversation(id)
  showGroupInfo.value = false
  router.replace({ path: `/messaging/${id}` })
  // Mark as read after a short delay
  setTimeout(() => markAsRead(), 500)
}

const clearActiveConversation = () => {
  setActiveConversation(null)
  router.replace({ path: '/messaging' })
}

const handleSend = async (text, options) => {
  await sendMessage(text, options)
}

const handleEdit = async (messageId, newContent) => {
  await editMessage(messageId, newContent)
}

const handleDelete = async (messageId) => {
  await deleteMessage(messageId)
}

const handleReact = ({ messageId, emoji }) => {
  toggleReaction(messageId, emoji)
}

const handleCreateDirectChat = async (username) => {
  try {
    const conv = await createDirectChat(username)
    selectConversation(conv.id)
  } catch (err) {
    showError('Failed to create chat')
  }
}

const handleCreateGroup = async ({ name, members, description }) => {
  try {
    const conv = await createGroupChat(name, members, description)
    selectConversation(conv.id)
  } catch (err) {
    showError('Failed to create group')
  }
}

const handleAddMember = async (username) => {
  try {
    const conv = await addMember(activeConversationId.value, username)
    updateConversationInList(conv)
  } catch (err) {
    showError('Failed to add member')
  }
}

const handleRemoveMember = async (username) => {
  try {
    await removeMember(activeConversationId.value, username)
    await fetchConversations()
  } catch (err) {
    showError('Failed to remove member')
  }
}

const handleCall = (type) => {
  if (!activeConversationId.value) return
  clearTranscript()
  initiateCall(activeConversationId.value, type)
}

const handleEndCall = () => {
  endCall(activeConversationId.value)
  clearTranscript()
  showTranscription.value = false
}

const handleLeaveGroup = async () => {
  try {
    const { tokenParsed } = useAuth()
    const currentUsername = tokenParsed.value?.preferred_username
    if (!currentUsername) return
    await removeMember(activeConversationId.value, currentUsername)
    clearActiveConversation()
    await fetchConversations()
  } catch (err) {
    showError('Failed to leave group')
  }
}

// ── Re-load data when access is restored ─────────────────────────
watch(showDisabledOverlay, async (disabled, wasDisabled) => {
  // Access just restored → reload conversations and messages
  if (wasDisabled && !disabled) {
    await fetchConversations()
    await fetchUnreadCounts()
    const convId = route.params.conversationId
    if (convId) {
      const numId = Number(convId)
      if (activeConversationId.value === numId) {
        setActiveConversation(null)
        await nextTick()
      }
      setActiveConversation(numId)
    }
  }
})

// ── Lifecycle ─────────────────────────────────────────────────────
onMounted(async () => {
  await fetchConversations()
  await fetchUnreadCounts()
  initSocket()
  setupSocketListeners()
  setupTypingListeners()
  setupCallListeners()
  setupTranscriptionListeners()
  startAccessPoll()

  // Open conversation from URL param
  const convId = route.params.conversationId
  if (convId) {
    const numId = Number(convId)
    // Force watcher to fire even if same conversation was active before (singleton state)
    if (activeConversationId.value === numId) {
      setActiveConversation(null)
      await nextTick()
    }
    setActiveConversation(numId)
  }
})

onUnmounted(() => {
  stopAccessPoll()
  cleanupSocketListeners()
  cleanupTypingListeners()
  cleanupCallListeners()
  cleanupTranscriptionListeners()
  cleanupMessaging()
})
</script>
