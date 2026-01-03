<!-- ChatSidebar.vue - Desktop sidebar for chat interface -->
<template>
  <aside class="chat-sidebar" :class="{ collapsed: collapsed }">
    <!-- Header with New Chat Button -->
    <div class="sidebar-header">
      <template v-if="!collapsed">
        <LBtn
          variant="primary"
          prepend-icon="mdi-plus"
          class="new-chat-btn"
          :disabled="!selectedChatbot"
          @click="$emit('new-chat')"
        >
          Neuer Chat
        </LBtn>
      </template>
      <LTooltip v-else text="Neuer Chat" location="right">
        <button
          class="new-chat-btn-mini"
          :disabled="!selectedChatbot"
          @click="$emit('new-chat')"
        >
          <v-icon size="20">mdi-plus</v-icon>
        </button>
      </LTooltip>
      <button
        class="collapse-btn"
        @click="$emit('toggle-collapse')"
        :title="collapsed ? 'Erweitern' : 'Zuklappen'"
      >
        <v-icon size="18">{{ collapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
      </button>
    </div>

    <!-- Search -->
    <div v-if="!collapsed" class="sidebar-search">
      <v-text-field
        :model-value="searchQuery"
        @update:model-value="$emit('update:searchQuery', $event)"
        placeholder="Chats durchsuchen..."
        density="compact"
        variant="outlined"
        hide-details
        prepend-inner-icon="mdi-magnify"
        clearable
        class="search-input"
      />
    </div>

    <!-- Chatbot Groups -->
    <nav class="sidebar-nav">
      <v-skeleton-loader v-if="loading" type="list-item@3" />
      <template v-else>
        <div
          v-for="bot in chatbots"
          :key="bot.id"
          class="chatbot-group"
          :class="{ expanded: expandedBots[bot.id], active: selectedChatbot?.id === bot.id }"
        >
          <!-- Chatbot Header (Expandable) -->
          <button
            class="chatbot-header"
            @click="$emit('toggle-bot', bot)"
            :title="collapsed ? bot.display_name : undefined"
          >
            <div class="chatbot-avatar">
              <v-avatar :color="bot.color || '#b0ca97'" size="28">
                <v-icon color="white" size="16">{{ bot.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
            </div>
            <template v-if="!collapsed">
              <div class="chatbot-info">
                <span class="chatbot-name">{{ bot.display_name }}</span>
                <div class="chatbot-meta">
                  <LTag
                    v-if="getChatbotTypeTag(bot)"
                    :variant="getChatbotTypeTag(bot).variant"
                    size="sm"
                  >
                    {{ getChatbotTypeTag(bot).label }}
                  </LTag>
                  <span v-if="getChatCount(bot.id)" class="chat-count">
                    {{ getChatCount(bot.id) }} Chats
                  </span>
                </div>
              </div>
              <v-icon class="expand-icon" size="18">
                {{ expandedBots[bot.id] ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </template>
          </button>

          <!-- Conversations List (Nested) -->
          <div
            v-if="!collapsed && expandedBots[bot.id]"
            class="conversations-list"
          >
            <v-skeleton-loader
              v-if="conversationsLoading && selectedChatbot?.id === bot.id"
              type="list-item@2"
              class="px-2"
            />
            <template v-else-if="getFilteredConversations(bot.id)?.length">
              <div
                v-for="conv in getFilteredConversations(bot.id)"
                :key="conv.id"
                class="conversation-item"
                :class="{
                  active: selectedConversation?.id === conv.id && selectedChatbot?.id === bot.id,
                  'title-streaming': getDisplayTitle(conv).isStreaming
                }"
                @click.stop="$emit('select-conversation', bot, conv)"
              >
                <v-icon size="16" class="conv-icon">mdi-chat-outline</v-icon>
                <span class="conv-title" :class="{ 'streaming-text': getDisplayTitle(conv).isStreaming }">
                  {{ getDisplayTitle(conv).text }}
                  <span v-if="getDisplayTitle(conv).isStreaming" class="typing-cursor"></span>
                </span>
                <div class="conv-actions">
                  <LTooltip text="Umbenennen" location="top">
                    <button class="conv-action" @click.stop="$emit('rename-conversation', conv)">
                      <v-icon size="14">mdi-pencil</v-icon>
                    </button>
                  </LTooltip>
                  <LTooltip text="Löschen" location="top">
                    <button class="conv-action delete" @click.stop="$emit('delete-conversation', conv)">
                      <v-icon size="14">mdi-delete</v-icon>
                    </button>
                  </LTooltip>
                </div>
              </div>
            </template>
            <div v-else class="no-chats">
              <span>Noch keine Chats</span>
            </div>
          </div>
        </div>

        <div v-if="chatbots.length === 0 && !collapsed" class="empty-sidebar">
          <v-icon size="32" class="mb-2">mdi-robot-off</v-icon>
          <div>Keine Chatbots verfügbar</div>
        </div>
      </template>
    </nav>

    <!-- Footer -->
    <div class="sidebar-footer">
      <div class="sidebar-divider"></div>
      <button
        class="footer-item"
        @click="$emit('navigate-home')"
        :title="collapsed ? 'Zur Startseite' : undefined"
      >
        <v-icon size="20">mdi-home</v-icon>
        <span v-if="!collapsed">Startseite</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  collapsed: {
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
  conversationsLoading: {
    type: Boolean,
    default: false
  },
  // Functions passed from parent
  getChatCount: {
    type: Function,
    required: true
  },
  getFilteredConversations: {
    type: Function,
    required: true
  },
  getDisplayTitle: {
    type: Function,
    required: true
  },
  getChatbotTypeTag: {
    type: Function,
    required: true
  }
})

defineEmits([
  'new-chat',
  'toggle-collapse',
  'update:searchQuery',
  'toggle-bot',
  'select-conversation',
  'rename-conversation',
  'delete-conversation',
  'navigate-home'
])
</script>

<style scoped>
.chat-sidebar {
  width: 280px;
  min-width: 280px;
  height: 100%;
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  flex-direction: column;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  flex-shrink: 0;
}

.chat-sidebar.collapsed {
  width: 60px;
  min-width: 60px;
}

/* Sidebar Header */
.sidebar-header {
  display: flex;
  align-items: center;
  padding: 12px;
  gap: 8px;
  min-height: 56px;
}

.new-chat-btn {
  flex: 1;
  border-radius: 16px 4px 16px 4px !important;
}

.new-chat-btn-mini {
  width: 36px;
  height: 36px;
  border-radius: 12px 4px 12px 4px;
  border: none;
  background: var(--llars-primary, #b0ca97);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.new-chat-btn-mini:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(176, 202, 151, 0.4);
}

.new-chat-btn-mini:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
  z-index: 10;
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
  transform: scale(1.1);
}

/* Make collapse button more prominent when sidebar is collapsed */
.collapsed .collapse-btn {
  width: 36px;
  height: 36px;
  background: var(--llars-primary, #b0ca97);
  color: white;
  border-radius: 8px 2px 8px 2px;
}

.collapsed .collapse-btn:hover {
  background: #9ab886;
  color: white;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(176, 202, 151, 0.4);
}

.collapsed .sidebar-header {
  flex-direction: column;
  padding: 12px 8px;
  gap: 8px;
}

/* Search */
.sidebar-search {
  padding: 0 12px 12px;
}

.search-input :deep(.v-field) {
  border-radius: 12px 4px 12px 4px !important;
  font-size: 13px;
}

.search-input :deep(.v-field__outline) {
  --v-field-border-opacity: 0.1;
}

/* Sidebar Nav */
.sidebar-nav {
  flex: 1;
  padding: 0 8px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Chatbot Group */
.chatbot-group {
  margin-bottom: 4px;
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.chatbot-group.active {
  background: rgba(var(--v-theme-primary), 0.06);
}

.chatbot-group.expanded {
  background: rgba(var(--v-theme-primary), 0.04);
}

.chatbot-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.85);
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: left;
}

.collapsed .chatbot-header {
  justify-content: center;
  padding: 10px;
}

.chatbot-header:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.chatbot-group.active .chatbot-header {
  color: rgb(var(--v-theme-on-surface));
}

.chatbot-avatar {
  flex-shrink: 0;
}

.chatbot-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chatbot-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chatbot-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.chat-count {
  font-size: 11px;
}

.expand-icon {
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: transform 0.2s ease;
}

/* Conversations List (Nested) */
.conversations-list {
  padding: 4px 0 8px 0;
}

.conversation-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px 8px 44px;
  cursor: pointer;
  transition: all 0.15s ease;
  border-radius: 8px 2px 8px 2px;
  margin: 2px 8px;
  position: relative;
}

.conversation-item:hover {
  background: rgba(var(--v-theme-primary), 0.1);
}

.conversation-item.active {
  background: rgba(var(--v-theme-primary), 0.18);
  color: rgb(var(--v-theme-primary));
}

.conversation-item.active .conv-icon {
  color: rgb(var(--v-theme-primary));
}

.conv-icon {
  color: rgba(var(--v-theme-on-surface), 0.5);
  flex-shrink: 0;
}

.conv-title {
  flex: 1;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conv-actions {
  display: none;
  gap: 2px;
}

.conversation-item:hover .conv-actions {
  display: flex;
}

.conv-action {
  width: 24px;
  height: 24px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.conv-action:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.conv-action.delete:hover {
  background: rgba(232, 160, 135, 0.2);
  color: #e8a087;
}

.no-chats {
  padding: 8px 12px 8px 44px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-style: italic;
}

.empty-sidebar {
  text-align: center;
  padding: 32px 16px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Divider */
.sidebar-divider {
  height: 1px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  margin: 0 12px;
}

/* Footer */
.sidebar-footer {
  margin-top: auto;
  padding: 8px;
}

.sidebar-footer .sidebar-divider {
  margin-bottom: 8px;
}

.footer-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.7);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.footer-item:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  color: rgb(var(--v-theme-on-surface));
}

.collapsed .footer-item {
  justify-content: center;
  padding: 12px;
}

.collapsed .footer-item span {
  display: none;
}

/* Streaming title animation */
.streaming-text {
  display: inline;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  background: rgb(var(--v-theme-primary));
  margin-left: 2px;
  animation: blink 0.8s infinite;
  vertical-align: middle;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.title-streaming {
  background: rgba(var(--v-theme-primary), 0.08);
}
</style>
