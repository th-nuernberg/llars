<template>
  <div class="assistant-chat" ref="chatContainer">
    <!-- Welcome Message -->
    <div v-if="messages.length === 0" class="welcome-message">
      <div class="welcome-avatar">
        <LIcon size="32" color="white">mdi-robot-happy</LIcon>
      </div>
      <div class="welcome-content">
        <p class="welcome-title">{{ $t('floatingAi.welcome.title') }}</p>
        <p class="welcome-subtitle">{{ $t('floatingAi.welcome.subtitle') }}</p>
        <div class="welcome-features">
          <div class="feature-item">
            <LIcon size="16" color="success">mdi-check-circle</LIcon>
            <span>{{ $t('floatingAi.welcome.features.context') }}</span>
          </div>
          <div class="feature-item">
            <LIcon size="16" color="success">mdi-check-circle</LIcon>
            <span>{{ $t('floatingAi.welcome.features.insert') }}</span>
          </div>
          <div class="feature-item">
            <LIcon size="16" color="success">mdi-check-circle</LIcon>
            <span>{{ $t('floatingAi.welcome.features.quick') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <div
      v-for="msg in messages"
      :key="msg.id"
      class="chat-message"
      :class="msg.role"
    >
      <div class="message-avatar">
        <LIcon size="18" color="white">
          {{ msg.role === 'user' ? 'mdi-account' : 'mdi-robot' }}
        </LIcon>
      </div>
      <div class="message-body">
        <div class="message-content" v-html="formatMessage(msg.content)"></div>

        <!-- Suggestions with Action Buttons -->
        <div v-if="msg.suggestions?.length" class="message-suggestions">
          <div
            v-for="(suggestion, index) in msg.suggestions"
            :key="suggestion.id"
            class="suggestion-item"
          >
            <div class="suggestion-number">{{ index + 1 }}</div>
            <div class="suggestion-text">{{ truncateSuggestion(suggestion.text) }}</div>
            <div class="suggestion-actions">
              <LBtn
                variant="primary"
                size="small"
                @click="$emit('apply-action', { actionType: suggestion.actionType, text: suggestion.text })"
              >
                <LIcon size="14" class="mr-1">mdi-check</LIcon>
                {{ $t('floatingAi.actions.insert') }}
              </LBtn>
              <LBtn
                variant="text"
                size="small"
                @click="$emit('copy-text', suggestion.text)"
              >
                <LIcon size="14">mdi-content-copy</LIcon>
              </LBtn>
            </div>
          </div>
        </div>

        <!-- Artifacts (code blocks) -->
        <div v-if="msg.artifacts?.length" class="message-artifacts">
          <div
            v-for="artifact in msg.artifacts"
            :key="artifact.id"
            class="artifact-block"
          >
            <div class="artifact-header">
              <LIcon size="12" class="mr-1">mdi-code-tags</LIcon>
              {{ artifact.language || 'latex' }}
              <v-spacer />
              <LBtn
                variant="text"
                size="small"
                @click="$emit('apply-action', { actionType: 'insert', text: artifact.content })"
              >
                <LIcon size="14">mdi-plus</LIcon>
              </LBtn>
              <LBtn
                variant="text"
                size="small"
                @click="$emit('copy-text', artifact.content)"
              >
                <LIcon size="14">mdi-content-copy</LIcon>
              </LBtn>
            </div>
            <pre class="artifact-code">{{ artifact.content }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Indicator -->
    <div v-if="isLoading" class="chat-message assistant">
      <div class="message-avatar">
        <LIcon size="18" color="white">mdi-robot</LIcon>
      </div>
      <div class="message-body">
        <div class="loading-indicator">
          <v-progress-circular
            indeterminate
            size="16"
            width="2"
            color="primary"
          />
          <span>{{ $t('floatingAi.thinking') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  isLoading: {
    type: Boolean,
    default: false
  },
  context: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['apply-action', 'copy-text'])

const chatContainer = ref(null)

function formatMessage(content) {
  if (!content) return ''
  try {
    return marked.parse(content, { breaks: true })
  } catch {
    return content
  }
}

function truncateSuggestion(text) {
  if (text.length > 200) {
    return text.substring(0, 200) + '...'
  }
  return text
}

function scrollToBottom() {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

defineExpose({
  scrollToBottom
})
</script>

<style scoped>
.assistant-chat {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Welcome Message */
.welcome-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px 16px;
}

.welcome-avatar {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #88c4c8 0%, #b0ca97 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.welcome-content {
  max-width: 280px;
}

.welcome-title {
  font-weight: 600;
  font-size: 16px;
  margin-bottom: 4px;
}

.welcome-subtitle {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 16px;
}

.welcome-features {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Chat Messages */
.chat-message {
  display: flex;
  gap: 10px;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #88c4c8 0%, #b0ca97 100%);
}

.chat-message.user .message-avatar {
  background: rgba(var(--v-theme-primary), 0.8);
}

.message-body {
  max-width: 85%;
  min-width: 0;
}

.message-content {
  padding: 10px 12px;
  border-radius: 12px 12px 12px 4px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  font-size: 13px;
  line-height: 1.5;
}

.chat-message.user .message-content {
  border-radius: 12px 12px 4px 12px;
  background: rgba(var(--v-theme-primary), 0.1);
}

.message-content :deep(p) {
  margin: 0 0 0.5em 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(var(--v-theme-on-surface), 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.message-content :deep(pre) {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(strong) {
  font-weight: 600;
}

/* Suggestions */
.message-suggestions {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-item {
  background: rgba(var(--v-theme-on-surface), 0.04);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  padding: 10px;
}

.suggestion-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(var(--v-theme-primary), 0.2);
  color: rgb(var(--v-theme-primary));
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 6px;
}

.suggestion-text {
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 8px;
  word-break: break-word;
}

.suggestion-actions {
  display: flex;
  gap: 6px;
}

/* Artifacts */
.message-artifacts {
  margin-top: 10px;
}

.artifact-block {
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}

.artifact-header {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  font-size: 11px;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.artifact-code {
  padding: 10px;
  margin: 0;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Loading */
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
</style>
