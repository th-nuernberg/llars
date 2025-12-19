<template>
  <div class="l-message" :class="messageClasses">
    <!-- Accent Border -->
    <div class="l-message__accent"></div>

    <!-- Message Content -->
    <div class="l-message__content">
      <!-- Header -->
      <div class="l-message__header">
        <LTag :variant="tagVariant" size="small">
          <v-icon v-if="showIcon" size="14" class="mr-1">{{ senderIcon }}</v-icon>
          {{ sender }}
        </LTag>
        <span v-if="timestamp" class="l-message__timestamp">{{ formattedTimestamp }}</span>
        <v-spacer />
        <div v-if="$slots.actions" class="l-message__actions">
          <slot name="actions" />
        </div>
      </div>

      <!-- Body -->
      <div class="l-message__body">
        <slot>{{ content }}</slot>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  sender: {
    type: String,
    required: true
  },
  content: {
    type: String,
    default: ''
  },
  timestamp: {
    type: [String, Date],
    default: null
  },
  senderType: {
    type: String,
    default: 'auto', // 'client' | 'advisor' | 'auto'
    validator: (v) => ['client', 'advisor', 'auto'].includes(v)
  },
  showIcon: {
    type: Boolean,
    default: true
  }
})

// Client detection patterns
const clientPatterns = [
  'ratsuchende person',
  'ratsuchender',
  'ratsuchend',
  'ratsuchende',
  'klient',
  'klientin',
  'client',
  'anfragender',
  'anfragende'
]

// Determine if sender is client
const isClient = computed(() => {
  if (props.senderType === 'client') return true
  if (props.senderType === 'advisor') return false

  // Auto-detect based on sender name
  const normalizedSender = String(props.sender || '').toLowerCase().trim()
  return clientPatterns.some(pattern => normalizedSender.includes(pattern))
})

// CSS classes
const messageClasses = computed(() => ({
  'l-message--client': isClient.value,
  'l-message--advisor': !isClient.value
}))

// Tag variant based on sender type
const tagVariant = computed(() => isClient.value ? 'primary' : 'secondary')

// Sender icon
const senderIcon = computed(() => isClient.value ? 'mdi-account' : 'mdi-account-tie')

// Format timestamp
const formattedTimestamp = computed(() => {
  if (!props.timestamp) return ''

  try {
    const date = props.timestamp instanceof Date ? props.timestamp : new Date(props.timestamp)
    return date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).replace(',', ' um') + ' Uhr'
  } catch {
    return props.timestamp
  }
})
</script>

<style scoped>
.l-message {
  display: flex;
  border-radius: var(--llars-radius-sm);
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.l-message:hover {
  box-shadow: var(--llars-shadow-sm);
}

/* Accent Border (left side) */
.l-message__accent {
  width: 4px;
  flex-shrink: 0;
}

.l-message--client .l-message__accent {
  background: var(--llars-primary);
}

.l-message--advisor .l-message__accent {
  background: var(--llars-secondary);
}

/* Content Area */
.l-message__content {
  flex: 1;
  padding: 12px 14px;
  min-width: 0;
}

/* Header */
.l-message__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.l-message__timestamp {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.l-message__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Body */
.l-message__body {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

/* Background tints based on sender type */
.l-message--client {
  background: var(--llars-gradient-primary-subtle);
}

.l-message--advisor {
  background: var(--llars-gradient-secondary-subtle);
}

/* Dark mode adjustments */
.v-theme--dark .l-message {
  border-color: rgba(var(--v-theme-on-surface), 0.12);
}

.v-theme--dark .l-message__body {
  color: rgba(var(--v-theme-on-surface), 0.9);
}
</style>
