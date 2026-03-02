<template>
  <div class="chat-panel">
    <ChatHeader
      :conversation="conversation"
      :show-back-button="showBackButton"
      @back="$emit('back')"
      @toggle-group-info="$emit('toggleGroupInfo')"
      @call="(type) => $emit('call', type)"
    />

    <!-- Messages -->
    <div style="position: relative; flex: 1; overflow: hidden; display: flex; flex-direction: column;">
    <div ref="messagesContainer" class="chat-messages" @scroll="onScroll">
      <LLoading v-if="isLoading && messages.length === 0" :text="$t('messaging.loadingMessages')" />

      <div v-if="hasMore && messages.length > 0" class="text-center py-2">
        <LBtn variant="text" size="small" @click="$emit('loadMore')" :loading="isLoading">
          {{ $t('messaging.loadMore') }}
        </LBtn>
      </div>

      <template v-for="item in messagesWithDateSeparators" :key="item.type === 'date-separator' ? item.date : item.type === 'unread-marker' ? 'unread' : item.id">
        <div v-if="item.type === 'date-separator'" class="date-separator">
          <span>{{ item.label }}</span>
        </div>
        <div v-else-if="item.type === 'unread-marker'" class="unread-marker">
          {{ t('messaging.newMessages') }}
        </div>
        <ChatMessageBubble
          v-else
          :message="item"
          :show-sender="isGroup"
          :is-first-in-group="item.isFirstInGroup !== false"
          :is-last-in-group="item.isLastInGroup !== false"
          :username="username"
          :user-avatar-map="userAvatarMap"
          @contextmenu="handleContextMenu"
          @reply="handleReply"
          @react="(payload) => emit('react', payload)"
        />
      </template>

      <div ref="bottomAnchor" />
    </div>

    <!-- New messages badge -->
    <div
      v-if="newMessageCount > 0 && !isNearBottom"
      class="new-messages-badge"
      @click="scrollToBottom"
    >
      &#8595; {{ newMessageCount }} {{ t('messaging.newMessages') }}
    </div>
    </div>

    <!-- Input -->
    <ChatInput
      ref="chatInputRef"
      :reply-to="replyTo"
      :typing-users="typingUsers"
      :encryption-enabled="conversation?.encryption_enabled"
      @send="handleSend"
      @cancel-reply="replyTo = null"
      @typing="$emit('typing')"
    />

    <!-- Context Menu -->
    <MessageContextMenu
      v-model="contextMenuVisible"
      :position="contextMenuPos"
      :message="contextMenuMessage"
      @reply="handleReply"
      @edit="handleEdit"
      @delete="handleDelete"
      @copy="handleCopy"
    />
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuth } from '@/composables/useAuth'
import ChatHeader from './ChatHeader.vue'
import ChatMessageBubble from './ChatMessageBubble.vue'
import ChatInput from './ChatInput.vue'
import MessageContextMenu from './MessageContextMenu.vue'

const props = defineProps({
  conversation: { type: Object, default: null },
  messages: { type: Array, default: () => [] },
  isLoading: { type: Boolean, default: false },
  hasMore: { type: Boolean, default: false },
  typingUsers: { type: Set, default: () => new Set() },
  showBackButton: { type: Boolean, default: false },
  lastReadMessageId: { type: Number, default: null },
})

const emit = defineEmits([
  'send', 'edit', 'delete', 'react', 'loadMore', 'typing', 'back', 'toggleGroupInfo', 'call',
])

const { t } = useI18n()
const { tokenParsed } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || '')

const messagesContainer = ref(null)
const bottomAnchor = ref(null)
const chatInputRef = ref(null)
const replyTo = ref(null)
const contextMenuVisible = ref(false)
const contextMenuPos = ref({ x: 0, y: 0 })
const contextMenuMessage = ref(null)

const isGroup = props.conversation?.conversation_type === 'group'

// ── User avatar map (from conversation participants) ────────────
const userAvatarMap = computed(() => {
  const map = {}
  for (const p of (props.conversation?.participants || [])) {
    map[p.username] = {
      seed: p.avatar_seed || p.username,
      url: p.avatar_url || null,
    }
  }
  return map
})

// ── Date separators + message grouping ──────────────────────────
const GROUP_THRESHOLD_MS = 5 * 60 * 1000 // 5 minutes

const messagesWithDateSeparators = computed(() => {
  const result = []
  let lastDate = null

  for (const msg of props.messages) {
    const msgDate = msg.created_at ? new Date(msg.created_at).toDateString() : null
    if (msgDate && msgDate !== lastDate) {
      lastDate = msgDate
      const d = new Date(msg.created_at)
      const today = new Date()
      const yesterday = new Date()
      yesterday.setDate(yesterday.getDate() - 1)

      let label
      if (d.toDateString() === today.toDateString()) {
        label = t('messaging.today')
      } else if (d.toDateString() === yesterday.toDateString()) {
        label = t('messaging.yesterday')
      } else {
        label = d.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' })
      }

      result.push({ type: 'date-separator', date: msgDate, label })
    }
    // Shallow copy so we can add grouping flags without mutating readonly props
    result.push({ ...msg })
  }

  // Insert unread marker after lastReadMessageId
  if (props.lastReadMessageId) {
    const lastReadIdx = result.findIndex(
      (item) => item.type !== 'date-separator' && item.type !== 'unread-marker' && item.id === props.lastReadMessageId
    )
    // Only insert if there are messages after the last-read one
    if (lastReadIdx >= 0 && lastReadIdx < result.length - 1) {
      result.splice(lastReadIdx + 1, 0, { type: 'unread-marker' })
    }
  }

  // Compute grouping flags (isFirstInGroup / isLastInGroup)
  for (let i = 0; i < result.length; i++) {
    const item = result[i]
    if (item.type === 'date-separator' || item.type === 'unread-marker') continue

    const prev = i > 0 ? result[i - 1] : null
    const next = i < result.length - 1 ? result[i + 1] : null

    const sameGroupAsPrev = prev
      && prev.type !== 'date-separator'
      && prev.type !== 'unread-marker'
      && prev.sender_username === item.sender_username
      && item.created_at && prev.created_at
      && (new Date(item.created_at) - new Date(prev.created_at)) < GROUP_THRESHOLD_MS

    const sameGroupAsNext = next
      && next.type !== 'date-separator'
      && next.type !== 'unread-marker'
      && next.sender_username === item.sender_username
      && item.created_at && next.created_at
      && (new Date(next.created_at) - new Date(item.created_at)) < GROUP_THRESHOLD_MS

    item.isFirstInGroup = !sameGroupAsPrev
    item.isLastInGroup = !sameGroupAsNext
  }

  return result
})

// ── Scroll tracking ─────────────────────────────────────────────
const isNearBottom = ref(true)
const newMessageCount = ref(0)

const checkNearBottom = () => {
  const el = messagesContainer.value
  if (!el) return true
  return (el.scrollHeight - el.scrollTop - el.clientHeight) < 100
}

// Auto-scroll on new messages (only if near bottom)
watch(() => props.messages.length, (newLen, oldLen) => {
  if (isNearBottom.value) {
    nextTick(() => {
      bottomAnchor.value?.scrollIntoView({ behavior: 'smooth' })
    })
  } else if (newLen > oldLen) {
    newMessageCount.value += (newLen - oldLen)
  }
})

const scrollToBottom = () => {
  bottomAnchor.value?.scrollIntoView({ behavior: 'smooth' })
  newMessageCount.value = 0
}

const onScroll = () => {
  isNearBottom.value = checkNearBottom()
  if (isNearBottom.value) {
    newMessageCount.value = 0
  }
  if (messagesContainer.value?.scrollTop === 0 && props.hasMore) {
    emit('loadMore')
  }
}

const handleSend = (text, options) => {
  emit('send', text, { ...options, replyToId: replyTo.value?.id })
  replyTo.value = null
}

const handleContextMenu = (event, message) => {
  contextMenuPos.value = { x: event.clientX, y: event.clientY }
  contextMenuMessage.value = message
  contextMenuVisible.value = true
}

const handleReply = (message) => {
  replyTo.value = message
  chatInputRef.value?.focus()
}

const handleEdit = (message) => {
  // For simplicity, use prompt - a proper inline editor would be better
  const newContent = prompt('Edit message:', message.content)
  if (newContent && newContent !== message.content) {
    emit('edit', message.id, newContent)
  }
}

const handleDelete = (message) => {
  emit('delete', message.id)
}

const handleCopy = (message) => {
  navigator.clipboard.writeText(message.content || '')
}
</script>
