<template>
  <div class="l-message-list">
    <!-- Empty State -->
    <div v-if="!messages || messages.length === 0" class="l-message-list__empty">
      <LIcon size="48" color="grey-lighten-1">{{ emptyIcon }}</LIcon>
      <p class="text-medium-emphasis mt-2">{{ emptyText }}</p>
    </div>

    <!-- Messages -->
    <div v-else class="l-message-list__messages">
      <LMessage
        v-for="message in messages"
        :key="message[messageKey]"
        :sender="message[senderField]"
        :content="message[contentField]"
        :timestamp="message[timestampField]"
        :sender-type="getSenderType(message)"
        :show-icon="showIcons"
      >
        <!-- Pass through actions slot if provided -->
        <template v-if="$slots.actions" #actions>
          <slot name="actions" :message="message" />
        </template>

        <!-- Pass through default slot if provided (for custom content) -->
        <template v-if="$slots.content" #default>
          <slot name="content" :message="message" />
        </template>
      </LMessage>
    </div>
  </div>
</template>

<script setup>
import LMessage from './LMessage.vue'

const props = defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  messageKey: {
    type: String,
    default: 'message_id'
  },
  senderField: {
    type: String,
    default: 'sender'
  },
  contentField: {
    type: String,
    default: 'content'
  },
  timestampField: {
    type: String,
    default: 'timestamp'
  },
  senderTypeField: {
    type: String,
    default: null // If set, uses this field from message object
  },
  emptyIcon: {
    type: String,
    default: 'mdi-email-off-outline'
  },
  emptyText: {
    type: String,
    default: 'Keine Nachrichten gefunden.'
  },
  showIcons: {
    type: Boolean,
    default: true
  }
})

function getSenderType(message) {
  if (props.senderTypeField && message[props.senderTypeField]) {
    return message[props.senderTypeField]
  }
  return 'auto'
}
</script>

<style scoped>
.l-message-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.l-message-list__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
  flex: 1;
}

.l-message-list__messages {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
