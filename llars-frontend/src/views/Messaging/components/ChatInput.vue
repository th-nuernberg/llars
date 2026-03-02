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

    <!-- Typing indicator -->
    <TypingIndicator :typing-users="typingUsers" />

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
import { ref, nextTick, computed } from 'vue'
import { usePermissions } from '@/composables/usePermissions'
import TypingIndicator from './TypingIndicator.vue'

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

const handleSend = () => {
  const text = messageText.value.trim()
  if (!text) return

  emit('send', text, {
    replyToId: props.replyTo?.id || null,
  })
  messageText.value = ''
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
