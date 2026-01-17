<template>
  <div class="chat-message" :class="[`chat-message--${message.role}`]">
    <div class="message-avatar">
      <LIcon v-if="message.role === 'assistant'" size="20" color="primary">
        mdi-robot
      </LIcon>
      <LIcon v-else size="20" color="secondary">
        mdi-account
      </LIcon>
    </div>
    <div class="message-content">
      <div class="message-header">
        <span class="message-author">
          {{ message.role === 'assistant' ? 'KI Assistent' : 'Du' }}
        </span>
        <span v-if="message.timestamp" class="message-time">
          {{ formatTime(message.timestamp) }}
        </span>
      </div>
      <div class="message-text">
        <template v-if="streaming">
          {{ content }}<span class="cursor-blink">|</span>
        </template>
        <template v-else>
          {{ content }}
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: {
    type: Object,
    required: true,
    validator: m => m && typeof m.role === 'string'
  },
  streaming: { type: Boolean, default: false }
})

const content = computed(() => {
  return props.message.content || ''
})

function formatTime(timestamp) {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return ''
  }
}
</script>

<style scoped>
.chat-message {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px 2px 8px 2px;
  margin-bottom: 8px;
}

.chat-message--user {
  background: rgba(209, 188, 138, 0.1);
}

.chat-message--assistant {
  background: rgba(176, 202, 151, 0.1);
}

.message-avatar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.chat-message--assistant .message-avatar {
  background: rgba(176, 202, 151, 0.2);
}

.chat-message--user .message-avatar {
  background: rgba(209, 188, 138, 0.2);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-author {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.message-time {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.message-text {
  font-size: 0.9rem;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: pre-wrap;
  word-break: break-word;
}

/* Blinking cursor for streaming */
.cursor-blink {
  animation: blink 1s infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
