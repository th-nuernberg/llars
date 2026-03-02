<template>
  <div class="message-row" :class="[alignment, { grouped: !isFirstInGroup }]">
    <!-- System message -->
    <div v-if="message.message_type === 'system'" class="message-bubble system">
      {{ message.content }}
    </div>

    <!-- Normal message -->
    <template v-else>
      <LAvatar
        v-if="!isSent && isFirstInGroup"
        :username="message.sender_username"
        :seed="message.sender_username"
        size="xs"
      />
      <div
        class="message-bubble"
        :class="{ sent: isSent, received: !isSent }"
        @contextmenu.prevent="$emit('contextmenu', $event, message)"
      >
        <!-- Sender name (group chats, received only, first in group) -->
        <div v-if="!isSent && showSender && isFirstInGroup" class="message-sender">
          {{ message.sender_username }}
        </div>

        <!-- Reply preview -->
        <div v-if="message.reply_to_preview" class="message-reply-preview">
          <strong>{{ message.reply_to_preview.sender_username }}</strong>:
          {{ message.reply_to_preview.content }}
        </div>

        <!-- Content -->
        <div v-if="message.is_deleted" class="message-content message-deleted">
          {{ $t('messaging.messageDeleted') }}
        </div>
        <div v-else class="message-content">{{ message.content }}</div>

        <!-- Attachments -->
        <div v-if="message.attachments?.length" class="mt-1">
          <v-chip
            v-for="att in message.attachments"
            :key="att.id"
            size="small"
            variant="outlined"
            prepend-icon="mdi-attachment"
            class="mr-1"
            @click="downloadAttachment(att)"
          >
            {{ att.filename }}
          </v-chip>
        </div>

        <!-- Reactions display -->
        <div v-if="message.reactions?.length" class="message-reactions">
          <span
            v-for="r in message.reactions"
            :key="r.emoji"
            class="reaction-chip"
            :class="{ 'reaction-mine': r.usernames.includes(username) }"
            @click.stop="$emit('react', { messageId: message.id, emoji: r.emoji })"
          >
            {{ r.emoji }} {{ r.count > 1 ? r.count : '' }}
          </span>
        </div>

        <!-- Hover actions -->
        <div v-if="!message.is_deleted" class="message-actions">
          <span
            v-for="emoji in quickReactions"
            :key="emoji"
            class="quick-reaction-btn"
            @click.stop="$emit('react', { messageId: message.id, emoji })"
          >
            {{ emoji }}
          </span>
          <LIconBtn
            icon="mdi-reply"
            size="x-small"
            :tooltip="$t('messaging.reply')"
            @click.stop="$emit('reply', message)"
          />
          <LIconBtn
            icon="mdi-content-copy"
            size="x-small"
            :tooltip="$t('messaging.copy')"
            @click.stop="copyContent"
          />
        </div>

        <!-- Meta -->
        <div class="message-meta">
          <span v-if="message.is_edited" class="message-edited">{{ $t('messaging.edited') }}</span>
          <v-icon v-if="message.is_encrypted" size="12">mdi-lock</v-icon>
          <span>{{ formattedTime }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const quickReactions = ['👍', '❤️', '😄', '😮', '😢']

const props = defineProps({
  message: { type: Object, required: true },
  showSender: { type: Boolean, default: false },
  isFirstInGroup: { type: Boolean, default: true },
  isLastInGroup: { type: Boolean, default: true },
  username: { type: String, default: '' },
})

defineEmits(['contextmenu', 'reply', 'react'])

const isSent = computed(() => props.message.sender_username === props.username)

const alignment = computed(() => {
  if (props.message.message_type === 'system') return 'system'
  return isSent.value ? 'sent' : 'received'
})

const formattedTime = computed(() => {
  if (!props.message.created_at) return ''
  return new Date(props.message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
})

const copyContent = () => {
  navigator.clipboard.writeText(props.message.content || '')
}

const downloadAttachment = (att) => {
  window.open(`/api/messaging/attachments/${att.id}`, '_blank')
}
</script>
