<template>
  <div
    class="conversation-item"
    :class="{ active: isActive }"
    @click="$emit('select', conversation.id)"
  >
    <LAvatar
      :seed="avatarSeed"
      :src="avatarUrl"
      :username="displayName"
      size="sm"
    />
    <div class="conversation-item-content">
      <div class="conversation-item-header">
        <span class="conversation-item-name">{{ displayName }}</span>
        <span class="conversation-item-time">{{ formattedTime }}</span>
      </div>
      <div class="conversation-item-preview">
        {{ conversation.last_message_preview || $t('messaging.noMessages') }}
      </div>
    </div>
    <v-badge
      v-if="unreadCount > 0"
      :content="unreadCount"
      color="primary"
      inline
      class="ml-2"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth'

const props = defineProps({
  conversation: { type: Object, required: true },
  isActive: { type: Boolean, default: false },
})

defineEmits(['select'])

const { tokenParsed } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || '')

const displayName = computed(() => {
  if (props.conversation.conversation_type === 'group') {
    return props.conversation.name || 'Group'
  }
  const other = (props.conversation.participants || []).find(
    (p) => p.username !== username.value
  )
  return other?.username || 'Unknown'
})

const otherParticipant = computed(() => {
  if (props.conversation.conversation_type === 'group') return null
  return (props.conversation.participants || []).find(
    (p) => p.username !== username.value
  )
})

const avatarSeed = computed(() => {
  return otherParticipant.value?.avatar_seed || props.conversation.avatar_seed || displayName.value
})

const avatarUrl = computed(() => {
  return otherParticipant.value?.avatar_url || null
})

const unreadCount = computed(() => {
  return props.conversation.unread_count || 0
})

const formattedTime = computed(() => {
  const dateStr = props.conversation.last_message_at
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date

  if (diff < 86400000) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  if (diff < 604800000) {
    return date.toLocaleDateString([], { weekday: 'short' })
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
})
</script>
