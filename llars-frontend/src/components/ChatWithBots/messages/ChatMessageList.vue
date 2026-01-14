<!-- ChatMessageList.vue - Chat messages display component -->
<template>
  <div class="chat-messages" ref="containerRef">
    <!-- Agent Reasoning Display (for ACT, ReAct, ReflAct modes) -->
    <slot name="agent-reasoning"></slot>

    <!-- Welcome Message -->
    <div v-if="messages.length === 0 && chatbot?.welcome_message" class="welcome-message">
      <v-card variant="tonal" color="primary" class="pa-4">
        <div class="d-flex align-center mb-2">
          <v-avatar :color="chatbot.color || 'primary'" size="32" class="mr-2">
            <LIcon color="white" size="18">{{ chatbot.icon || 'mdi-robot' }}</LIcon>
          </v-avatar>
          <span class="font-weight-bold">{{ chatbot.display_name }}</span>
        </div>
        {{ chatbot.welcome_message }}
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
        <v-avatar :color="chatbot?.color || 'primary'" size="36" class="message-avatar">
          <LIcon color="white" size="20">{{ chatbot?.icon || 'mdi-robot' }}</LIcon>
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
            <LIcon start size="14">
              {{ getFileIcon(file.type) }}
            </LIcon>
            {{ file.filename }}
          </v-chip>
        </div>

        <div
          class="message-content"
          v-html="formatMessage(message.content, message.sources)"
          @click="handleContentClick($event, message.sources)"
        ></div>

        <!-- Sources Legend -->
        <div v-if="message.sources && message.sources.length > 0" class="message-sources mt-2">
          <div class="sources-legend">
            <div class="sources-header text-caption d-flex align-center mb-1">
              <LIcon size="14" class="mr-1">mdi-text-box-multiple-outline</LIcon>
              <span>Quellen</span>
            </div>
            <div class="sources-list">
              <v-chip
                v-for="source in message.sources"
                :key="source.footnote_id"
                size="x-small"
                variant="tonal"
                color="success"
                class="source-chip mr-1 mb-1"
                @click.stop="handleSourceClick(source)"
              >
                <span class="font-weight-bold mr-1">[{{ source.footnote_id }}]</span>
                <span class="text-truncate" style="max-width: 180px;">
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
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { logI18n } from '@/utils/logI18n'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  chatbot: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['show-source', 'footnote-click'])

const containerRef = ref(null)

/**
 * Handle source chip click - explicit handler for debugging
 */
function handleSourceClick(source) {
  logI18n('log', 'logs.chatMessageList.sourceClicked', source)
  emit('show-source', source)
}

/**
 * Format message content with markdown and footnote support
 */
function formatMessage(content, sources = []) {
  if (!content) return ''

  let processedContent = content
  if (sources && sources.length > 0) {
    const sourceMap = {}
    sources.forEach(s => {
      sourceMap[s.footnote_id] = s
    })

    processedContent = content.replace(/\[(\d+)\]/g, (match, num) => {
      const footnoteId = parseInt(num)
      const source = sourceMap[footnoteId]
      if (source) {
        const title = source.title || 'Quelle ' + footnoteId
        return `<span class="footnote-ref" data-footnote-id="${footnoteId}" title="${title}">[${num}]</span>`
      }
      return match
    })
  }

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
 * Handle click on message content (for footnote refs)
 */
function handleContentClick(event, sources) {
  const target = event.target
  if (target.classList.contains('footnote-ref')) {
    const footnoteId = parseInt(target.dataset.footnoteId)
    if (sources && sources.length > 0) {
      const source = sources.find(s => s.footnote_id === footnoteId)
      if (source) {
        emit('footnote-click', source)
      }
    }
  }
}

/**
 * Scroll to bottom of messages
 */
function scrollToBottom() {
  nextTick(() => {
    if (containerRef.value) {
      containerRef.value.scrollTo({
        top: containerRef.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

// Watch messages for changes and scroll
watch(() => props.messages, () => {
  scrollToBottom()
}, { deep: true })

// Expose scrollToBottom for parent
defineExpose({ scrollToBottom, containerRef })
</script>

<style scoped>
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
  margin: 0 auto 16px;
}

.message-container {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-container.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-container.bot {
  margin-right: auto;
}

.message-avatar {
  flex-shrink: 0;
  margin-top: 4px;
}

.message {
  padding: 12px 16px;
  border-radius: 16px 4px 16px 4px;
  position: relative;
}

.message-container.user .message {
  background: linear-gradient(135deg, var(--llars-primary, #b0ca97) 0%, rgba(176, 202, 151, 0.85) 100%);
  color: white;
  border-radius: 16px 4px 4px 16px;
}

.message-container.bot .message {
  background: rgba(var(--v-theme-surface-variant), 0.5);
  color: rgb(var(--v-theme-on-surface));
}

.message-files {
  display: flex;
  flex-wrap: wrap;
}

.message-content {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content :deep(p) {
  margin: 0 0 8px;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

/* List styling with proper indentation */
.message-content :deep(ul),
.message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-content :deep(ul) {
  list-style-type: disc;
}

.message-content :deep(ol) {
  list-style-type: decimal;
}

.message-content :deep(li) {
  margin: 4px 0;
  padding-left: 4px;
}

.message-content :deep(li > ul),
.message-content :deep(li > ol) {
  margin: 4px 0;
}

/* Nested list styling */
.message-content :deep(ul ul) {
  list-style-type: circle;
}

.message-content :deep(ul ul ul) {
  list-style-type: square;
}

.message-content :deep(.footnote-ref) {
  color: rgb(var(--v-theme-primary));
  cursor: pointer;
  font-weight: 600;
  padding: 0 2px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.message-content :deep(.footnote-ref:hover) {
  background: rgba(var(--v-theme-primary), 0.15);
}

.message-container.user .message-content :deep(.footnote-ref) {
  color: white;
  text-decoration: underline;
}

.message-sources {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  padding-top: 8px;
}

.sources-legend {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  padding: 8px;
}

.sources-header {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
}

.source-chip {
  cursor: pointer;
  transition: transform 0.15s ease;
}

.source-chip:hover {
  transform: scale(1.02);
}

.stream-indicator {
  position: absolute;
  bottom: 8px;
  right: 8px;
}

.message-timestamp {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-top: 4px;
  text-align: right;
}

.message-container.user .message-timestamp {
  color: rgba(255, 255, 255, 0.7);
}
</style>
