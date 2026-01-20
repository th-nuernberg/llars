<template>
  <div class="content-panel">
    <!-- Messages View -->
    <div v-if="messages && messages.length" class="messages-container">
      <div
        v-for="(message, index) in messages"
        :key="message.message_id || index"
        class="message-bubble"
        :class="getSenderClass(message.sender)"
      >
        <!-- Message Header -->
        <div class="message-header">
          <span class="message-sender">{{ getSenderLabel(message.sender) }}</span>
          <v-chip
            v-if="message.generated_by && message.generated_by !== 'Human'"
            size="x-small"
            color="info"
            variant="tonal"
            class="ml-2"
          >
            <v-icon start size="12">mdi-robot</v-icon>
            {{ message.generated_by }}
          </v-chip>
          <span v-if="message.timestamp" class="message-time">
            {{ formatTime(message.timestamp) }}
          </span>
        </div>

        <!-- Message Content -->
        <div class="message-content" v-html="formatContent(message.content)" />
      </div>
    </div>

    <!-- Plain Text View (fallback) -->
    <div v-else-if="content" class="plain-content">
      <div v-html="formatContent(content)" />
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <v-icon size="48" color="grey-lighten-1">mdi-text-box-outline</v-icon>
      <p>{{ $t('evaluation.rating.noContent') }}</p>
    </div>

    <!-- Metadata Footer (optional) -->
    <div v-if="item && showMetadata" class="content-footer">
      <div class="metadata-row">
        <span v-if="item.subject" class="metadata-item">
          <v-icon size="14">mdi-tag</v-icon>
          {{ item.subject }}
        </span>
        <span v-if="item.chat_id" class="metadata-item">
          <v-icon size="14">mdi-identifier</v-icon>
          ID: {{ item.chat_id }}
        </span>
        <span v-if="messages" class="metadata-item">
          <v-icon size="14">mdi-message-text</v-icon>
          {{ messages.length }} {{ $t('evaluation.rating.messages') }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * ContentPanel - Displays the content to be rated
 *
 * Shows messages in a chat-like format or plain text content.
 * Used in the left panel of the rating interface.
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  item: {
    type: Object,
    default: null
  },
  messages: {
    type: Array,
    default: () => []
  },
  content: {
    type: String,
    default: ''
  },
  showMetadata: {
    type: Boolean,
    default: true
  }
})

// Sender labels mapping
const senderLabels = computed(() => ({
  'Berater': t('evaluation.rating.counselor'),
  'Counselor': t('evaluation.rating.counselor'),
  'Klient': t('evaluation.rating.client'),
  'Client': t('evaluation.rating.client'),
  'System': t('evaluation.rating.system')
}))

// Get CSS class for message bubble based on sender
function getSenderClass(sender) {
  const lowerSender = (sender || '').toLowerCase()
  if (lowerSender.includes('berater') || lowerSender.includes('counselor')) {
    return 'sender-counselor'
  }
  if (lowerSender.includes('klient') || lowerSender.includes('client')) {
    return 'sender-client'
  }
  return 'sender-system'
}

// Get localized sender label
function getSenderLabel(sender) {
  return senderLabels.value[sender] || sender
}

// Format timestamp
function formatTime(timestamp) {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}

// Format content with basic markdown support
function formatContent(content) {
  if (!content) return ''

  // Escape HTML first
  let formatted = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // Basic markdown-like formatting
  // **bold**
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  // *italic*
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
  // Line breaks
  formatted = formatted.replace(/\n/g, '<br>')

  return formatted
}
</script>

<style scoped>
.content-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
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

/* Message Bubble */
.message-bubble {
  max-width: 90%;
  padding: 12px 16px;
  border-radius: 12px 4px 12px 4px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.message-bubble.sender-counselor {
  align-self: flex-start;
  background: rgba(136, 196, 200, 0.15);
  border-color: rgba(136, 196, 200, 0.3);
}

.message-bubble.sender-client {
  align-self: flex-end;
  background: rgba(176, 202, 151, 0.15);
  border-color: rgba(176, 202, 151, 0.3);
}

.message-bubble.sender-system {
  align-self: center;
  max-width: 80%;
  background: rgba(var(--v-theme-on-surface), 0.05);
  font-style: italic;
}

/* Message Header */
.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.message-sender {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.message-time {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-left: auto;
}

/* Message Content */
.message-content {
  font-size: 0.95rem;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
  word-wrap: break-word;
}

.message-content :deep(strong) {
  font-weight: 600;
}

.message-content :deep(em) {
  font-style: italic;
}

/* Plain Content View */
.plain-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  font-size: 0.95rem;
  line-height: 1.7;
  color: rgb(var(--v-theme-on-surface));
  white-space: pre-wrap;
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}

/* Metadata Footer */
.content-footer {
  padding: 12px 16px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.metadata-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.metadata-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.metadata-item .v-icon {
  opacity: 0.7;
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar,
.plain-content::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track,
.plain-content::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb,
.plain-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover,
.plain-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}

/* Responsive */
@media (max-width: 600px) {
  .message-bubble {
    max-width: 95%;
    padding: 10px 14px;
  }

  .messages-container {
    padding: 12px;
    gap: 12px;
  }
}
</style>
