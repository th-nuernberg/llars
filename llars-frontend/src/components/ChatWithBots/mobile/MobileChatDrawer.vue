<!--
  MobileChatDrawer.vue

  Mobile navigation drawer for ChatWithBots.
  Displays chatbot list with expandable conversation groups.
-->
<template>
  <v-navigation-drawer
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    temporary
    width="300"
    class="mobile-chat-drawer"
  >
    <div class="mobile-drawer-header">
      <LBtn
        variant="primary"
        prepend-icon="mdi-plus"
        block
        :disabled="!selectedChatbot"
        @click="$emit('new-chat'); $emit('update:modelValue', false)"
      >
        Neuer Chat
      </LBtn>
    </div>

    <div class="mobile-drawer-search pa-3">
      <v-text-field
        :model-value="searchQuery"
        @update:model-value="$emit('update:searchQuery', $event)"
        placeholder="Chats durchsuchen..."
        density="compact"
        variant="outlined"
        hide-details
        prepend-inner-icon="mdi-magnify"
        clearable
      />
    </div>

    <v-divider />

    <!-- Chatbot Groups in Drawer -->
    <div class="mobile-drawer-content">
      <v-skeleton-loader v-if="loading" type="list-item@3" />
      <template v-else>
        <div
          v-for="bot in chatbots"
          :key="'mobile-' + bot.id"
          class="mobile-chatbot-group"
        >
          <v-list-item
            :active="selectedChatbot?.id === bot.id"
            @click="$emit('toggle-bot', bot)"
            class="mobile-chatbot-header"
          >
            <template #prepend>
              <v-avatar :color="bot.color || '#b0ca97'" size="32">
                <v-icon color="white" size="18">{{ bot.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
            </template>
            <v-list-item-title>{{ bot.display_name }}</v-list-item-title>
            <v-list-item-subtitle v-if="getChatCount(bot.id)">
              {{ getChatCount(bot.id) }} Chats
            </v-list-item-subtitle>
            <template #append>
              <v-icon>{{ expandedBots[bot.id] ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</v-icon>
            </template>
          </v-list-item>

          <v-expand-transition>
            <div v-if="expandedBots[bot.id]" class="mobile-conversations-list">
              <v-list density="compact" class="py-0">
                <v-list-item
                  v-for="conv in getFilteredConversations(bot.id)"
                  :key="'mobile-conv-' + conv.id"
                  :active="selectedConversation?.id === conv.id && selectedChatbot?.id === bot.id"
                  @click="handleConversationClick(bot, conv)"
                  class="mobile-conversation-item"
                >
                  <template #prepend>
                    <v-icon size="16">mdi-chat-outline</v-icon>
                  </template>
                  <v-list-item-title class="text-body-2">
                    {{ getDisplayTitle(conv).text }}
                  </v-list-item-title>
                </v-list-item>
                <v-list-item v-if="!getFilteredConversations(bot.id)?.length" disabled>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Noch keine Chats
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </div>
          </v-expand-transition>
        </div>
      </template>
    </div>

    <template #append>
      <v-divider />
      <v-list density="compact">
        <v-list-item prepend-icon="mdi-home" title="Startseite" @click="$emit('navigate-home')" />
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  searchQuery: {
    type: String,
    default: ''
  },
  chatbots: {
    type: Array,
    default: () => []
  },
  selectedChatbot: {
    type: Object,
    default: null
  },
  selectedConversation: {
    type: Object,
    default: null
  },
  expandedBots: {
    type: Object,
    default: () => ({})
  },
  loading: {
    type: Boolean,
    default: false
  },
  getChatCount: {
    type: Function,
    default: () => 0
  },
  getFilteredConversations: {
    type: Function,
    default: () => []
  },
  getDisplayTitle: {
    type: Function,
    default: () => ({ text: '' })
  }
})

const emit = defineEmits([
  'update:modelValue',
  'update:searchQuery',
  'new-chat',
  'toggle-bot',
  'select-conversation',
  'navigate-home'
])

function handleConversationClick(bot, conv) {
  emit('select-conversation', bot, conv)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.mobile-chat-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-drawer-header {
  padding: 16px;
}

.mobile-drawer-content {
  flex: 1;
  overflow-y: auto;
}

.mobile-chatbot-group {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.mobile-conversations-list {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  padding-left: 16px;
}
</style>
