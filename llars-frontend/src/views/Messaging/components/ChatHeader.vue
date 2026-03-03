<template>
  <div class="chat-header">
    <div class="chat-header-info">
      <!-- Back button (mobile) -->
      <LIconBtn
        v-if="showBackButton"
        icon="mdi-arrow-left"
        @click="$emit('back')"
        size="small"
      />
      <LAvatar
        :seed="avatarSeed"
        :src="avatarUrl"
        :username="displayName"
        size="sm"
      />
      <div>
        <div class="chat-header-name">{{ displayName }}</div>
        <div v-if="participantText" class="chat-header-participants">
          {{ participantText }}
        </div>
      </div>
    </div>

    <div class="chat-header-actions">
      <EncryptionBadge v-if="conversation?.encryption_enabled" />
      <LIconBtn
        icon="mdi-phone"
        :tooltip="hasPermission('feature:communication:voice') ? $t('messaging.call.voice') : $t('messaging.call.voiceDisabled')"
        :disabled="!hasPermission('feature:communication:voice')"
        @click="hasPermission('feature:communication:voice') && $emit('call', 'voice')"
        size="small"
      />
      <LIconBtn
        icon="mdi-video"
        :tooltip="hasPermission('feature:communication:video') ? $t('messaging.call.video') : $t('messaging.call.videoDisabled')"
        :disabled="!hasPermission('feature:communication:video')"
        @click="hasPermission('feature:communication:video') && $emit('call', 'video')"
        size="small"
      />
      <LIconBtn
        v-if="isGroup"
        icon="mdi-account-group"
        :tooltip="$t('messaging.groupInfo')"
        @click="$emit('toggleGroupInfo')"
        size="small"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { usePermissions } from '@/composables/usePermissions'
import EncryptionBadge from './EncryptionBadge.vue'

const props = defineProps({
  conversation: { type: Object, default: null },
  showBackButton: { type: Boolean, default: false },
})

defineEmits(['back', 'toggleGroupInfo', 'call'])

const { hasPermission } = usePermissions()

const { tokenParsed } = useAuth()
const username = computed(() => tokenParsed.value?.preferred_username || '')

const isGroup = computed(() => props.conversation?.conversation_type === 'group')

const displayName = computed(() => {
  if (!props.conversation) return ''
  if (isGroup.value) return props.conversation.name || 'Group'
  const other = (props.conversation.participants || []).find(
    (p) => p.username !== username.value
  )
  return other?.username || 'Chat'
})

const otherParticipant = computed(() => {
  if (!props.conversation || isGroup.value) return null
  return (props.conversation.participants || []).find(
    (p) => p.username !== username.value
  )
})

const avatarSeed = computed(() => {
  return otherParticipant.value?.avatar_seed || props.conversation?.avatar_seed || displayName.value
})

const avatarUrl = computed(() => {
  return otherParticipant.value?.avatar_url || null
})

const participantText = computed(() => {
  if (!isGroup.value) return ''
  const active = (props.conversation?.participants || []).filter((p) => p.is_active)
  return `${active.length} ${active.length === 1 ? 'member' : 'members'}`
})
</script>
