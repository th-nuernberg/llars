<template>
  <div class="conversation-list-panel">
    <div class="conversation-list-header">
      <h2>{{ $t('messaging.title') }}</h2>
      <div class="d-flex gap-1">
        <LIconBtn icon="mdi-account-plus" :tooltip="$t('messaging.newChat')" @click="$emit('newChat')" />
        <LIconBtn icon="mdi-account-group" :tooltip="$t('messaging.newGroup')" @click="$emit('newGroup')" />
      </div>
    </div>

    <div class="conversation-search">
      <v-text-field
        v-model="searchQuery"
        :placeholder="$t('messaging.searchPlaceholder')"
        prepend-inner-icon="mdi-magnify"
        density="compact"
        variant="outlined"
        hide-details
        clearable
      />
    </div>

    <div class="conversation-list-items">
      <LLoading v-if="isLoading" :text="$t('messaging.loading')" />
      <template v-else-if="filteredConversations.length > 0">
        <ConversationListItem
          v-for="conv in filteredConversations"
          :key="conv.id"
          :conversation="conv"
          :is-active="conv.id === activeConversationId"
          @select="$emit('select', $event)"
        />
      </template>
      <div v-else class="chat-empty-state pa-8">
        <v-icon size="48">mdi-message-outline</v-icon>
        <p class="mt-2">{{ $t('messaging.noConversations') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ConversationListItem from './ConversationListItem.vue'

const props = defineProps({
  conversations: { type: Array, default: () => [] },
  activeConversationId: { type: Number, default: null },
  isLoading: { type: Boolean, default: false },
})

defineEmits(['select', 'newChat', 'newGroup'])

const searchQuery = ref('')

const filteredConversations = computed(() => {
  if (!searchQuery.value) return props.conversations
  const q = searchQuery.value.toLowerCase()
  return props.conversations.filter((c) => {
    const name = c.name || ''
    const preview = c.last_message_preview || ''
    const participants = (c.participants || []).map((p) => p.username).join(' ')
    return name.toLowerCase().includes(q) ||
      preview.toLowerCase().includes(q) ||
      participants.toLowerCase().includes(q)
  })
})
</script>
