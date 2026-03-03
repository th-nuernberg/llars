<template>
  <div class="chat-input-area">
    <!-- No chat permission -->
    <div v-if="!canChat" class="text-center pa-3 text-medium-emphasis">
      <v-icon size="16" class="mr-1">mdi-lock</v-icon>
      {{ $t('messaging.chatDisabled') }}
    </div>
    <template v-else>
    <!-- Reply preview -->
    <div v-if="replyTo" class="chat-input-reply">
      <span>
        <v-icon size="14" class="mr-1">mdi-reply</v-icon>
        <strong>{{ replyTo.sender_username }}</strong>: {{ (replyTo.content || '').substring(0, 80) }}
      </span>
      <LIconBtn icon="mdi-close" size="x-small" @click="$emit('cancelReply')" />
    </div>

    <!-- Link Preview (compose-time) -->
    <div v-if="inputPreview" class="chat-input-link-preview">
      <a
        :href="inputPreview.url"
        target="_blank"
        rel="noopener noreferrer"
        class="link-preview-card link-preview-card--inline"
      >
        <img
          v-if="inputPreview.image_url"
          :src="proxyImageUrl(inputPreview.image_url)"
          :alt="inputPreview.title || ''"
          class="link-preview-image"
          referrerpolicy="no-referrer"
          @error="$event.target.style.display='none'"
        />
        <div class="link-preview-body">
          <div v-if="inputPreview.site_name || inputPreview.favicon_url" class="link-preview-site">
            <img
              v-if="inputPreview.favicon_url"
              :src="proxyImageUrl(inputPreview.favicon_url)"
              class="link-preview-favicon"
              referrerpolicy="no-referrer"
              @error="$event.target.style.display='none'"
            />
            <span v-if="inputPreview.site_name">{{ inputPreview.site_name }}</span>
          </div>
          <div v-if="inputPreview.title" class="link-preview-title">{{ inputPreview.title }}</div>
          <div v-if="inputPreview.description" class="link-preview-desc">{{ inputPreview.description }}</div>
        </div>
      </a>
      <LIconBtn
        icon="mdi-close"
        size="x-small"
        class="link-preview-dismiss"
        @click="dismissPreview"
      />
    </div>

    <!-- Typing indicator -->
    <TypingIndicator :typing-users="typingUsers" />

    <!-- Formatting toolbar -->
    <div class="chat-input-toolbar">
      <LIconBtn icon="mdi-format-bold" size="x-small" tooltip="Bold" @click="wrapSelection('**')" />
      <LIconBtn icon="mdi-format-italic" size="x-small" tooltip="Italic" @click="wrapSelection('_')" />
      <LIconBtn icon="mdi-format-strikethrough-variant" size="x-small" tooltip="Strikethrough" @click="wrapSelection('~~')" />
      <LIconBtn icon="mdi-code-tags" size="x-small" tooltip="Code" @click="wrapSelection('`')" />
      <div class="toolbar-separator" />
      <!-- Emoji picker -->
      <div class="emoji-picker-wrapper" ref="inputEmojiWrapperRef">
        <LIconBtn
          icon="mdi-emoticon-happy-outline"
          size="x-small"
          tooltip="Emoji"
          @click.stop="showInputEmoji = !showInputEmoji"
        />
        <Transition name="fade">
          <div v-if="showInputEmoji" class="emoji-picker-popover emoji-picker-above">
            <div class="emoji-picker-grid">
              <span
                v-for="emoji in inputEmojis"
                :key="emoji"
                class="emoji-picker-item"
                @click.stop="insertEmoji(emoji)"
              >
                {{ emoji }}
              </span>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Input row -->
    <div class="chat-input-row">
      <v-textarea
        ref="inputRef"
        v-model="messageText"
        :placeholder="$t('messaging.typeMessage')"
        rows="1"
        max-rows="5"
        auto-grow
        density="compact"
        variant="outlined"
        hide-details
        @keydown.enter.exact.prevent="handleSend"
        @input="onInput"
      />
      <LIconBtn
        icon="mdi-send"
        :tooltip="$t('messaging.send')"
        :disabled="!messageText.trim()"
        @click="handleSend"
        color="primary"
        class="send-btn"
      />
    </div>

    <!-- Encryption indicator -->
    <div v-if="encryptionEnabled" class="encryption-badge mt-1">
      <v-icon size="12">mdi-lock</v-icon>
      {{ $t('messaging.encrypted') }}
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { usePermissions } from '@/composables/usePermissions'
import TypingIndicator from './TypingIndicator.vue'

const URL_REGEX = /https?:\/\/[^\s<>\[\](){}'",;]+/gi

const inputEmojis = [
  '😊', '😂', '🤣', '❤️', '👍', '👎', '🎉', '🔥',
  '😮', '😢', '😡', '🤔', '👀', '🙏', '💯', '✅',
  '❌', '⭐', '💪', '🤝', '👏', '🚀', '💡', '🎯',
  '📌', '📎', '🔗', '💬', '✏️', '📝', '🗑️', '⏰',
]

const { hasPermission } = usePermissions()
const canChat = computed(() => hasPermission('feature:communication:chat'))

const props = defineProps({
  replyTo: { type: Object, default: null },
  typingUsers: { type: Set, default: () => new Set() },
  encryptionEnabled: { type: Boolean, default: false },
})

const emit = defineEmits(['send', 'cancelReply', 'typing'])

const messageText = ref('')
const inputRef = ref(null)
const showInputEmoji = ref(false)
const inputEmojiWrapperRef = ref(null)

// ── Formatting helpers ───────────────────────────────────────────
const wrapSelection = (marker) => {
  const textarea = inputRef.value?.$el?.querySelector('textarea')
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const text = messageText.value

  if (start === end) {
    // No selection — insert markers and place cursor between them
    messageText.value = text.slice(0, start) + marker + marker + text.slice(end)
    nextTick(() => {
      textarea.selectionStart = textarea.selectionEnd = start + marker.length
      textarea.focus()
    })
  } else {
    // Wrap selection
    const selected = text.slice(start, end)
    messageText.value = text.slice(0, start) + marker + selected + marker + text.slice(end)
    nextTick(() => {
      textarea.selectionStart = start + marker.length
      textarea.selectionEnd = end + marker.length
      textarea.focus()
    })
  }
}

const insertEmoji = (emoji) => {
  const textarea = inputRef.value?.$el?.querySelector('textarea')
  const pos = textarea ? textarea.selectionStart : messageText.value.length
  messageText.value = messageText.value.slice(0, pos) + emoji + messageText.value.slice(pos)
  showInputEmoji.value = false
  nextTick(() => {
    if (textarea) {
      textarea.selectionStart = textarea.selectionEnd = pos + emoji.length
      textarea.focus()
    }
  })
}

// Close emoji picker on click outside
const onClickOutside = (e) => {
  if (inputEmojiWrapperRef.value && !inputEmojiWrapperRef.value.contains(e.target)) {
    showInputEmoji.value = false
  }
}
onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))

// ── Link Preview in Compose ──────────────────────────────────────
const inputPreview = ref(null)
const lastFetchedUrl = ref('')
const previewDismissed = ref(false)
let debounceTimer = null

const proxyImageUrl = (url) => {
  if (!url) return ''
  return `/api/messaging/link-preview/image?url=${encodeURIComponent(url)}`
}

const fetchInputPreview = async (url) => {
  if (url === lastFetchedUrl.value) return
  lastFetchedUrl.value = url

  try {
    const { data } = await axios.get('/api/messaging/link-preview', {
      params: { url },
    })
    if (data.preview && !previewDismissed.value) {
      inputPreview.value = data.preview
    }
  } catch {
    // Silently fail — preview is non-critical
  }
}

const dismissPreview = () => {
  inputPreview.value = null
  previewDismissed.value = true
}

watch(messageText, (text) => {
  clearTimeout(debounceTimer)

  if (!text || props.encryptionEnabled) {
    inputPreview.value = null
    lastFetchedUrl.value = ''
    return
  }

  URL_REGEX.lastIndex = 0
  const matches = text.match(URL_REGEX)
  if (!matches || matches.length === 0) {
    inputPreview.value = null
    lastFetchedUrl.value = ''
    previewDismissed.value = false
    return
  }

  // Use the last URL found (most recently typed/pasted)
  const url = matches[matches.length - 1].replace(/[.,;:!?)]+$/, '')

  if (url === lastFetchedUrl.value) return
  previewDismissed.value = false

  debounceTimer = setTimeout(() => fetchInputPreview(url), 600)
})

// ── Send / Input ─────────────────────────────────────────────────
const handleSend = () => {
  const text = messageText.value.trim()
  if (!text) return

  emit('send', text, {
    replyToId: props.replyTo?.id || null,
    linkPreviews: inputPreview.value ? [inputPreview.value] : null,
  })
  messageText.value = ''
  inputPreview.value = null
  lastFetchedUrl.value = ''
  previewDismissed.value = false
  nextTick(() => inputRef.value?.focus())
}

const onInput = () => {
  emit('typing')
}

const focus = () => {
  nextTick(() => inputRef.value?.focus())
}

defineExpose({ focus })
</script>
