<!-- ChatWithBots.vue - Chat interface with ChatGPT-style grouped sidebar -->
<template>
  <div class="chat-page" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-if="isMobile"
      v-model="mobileSidebarOpen"
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
          @click="createConversation(); mobileSidebarOpen = false"
        >
          Neuer Chat
        </LBtn>
      </div>

      <div class="mobile-drawer-search pa-3">
        <v-text-field
          v-model="searchQuery"
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
        <v-skeleton-loader v-if="isLoading('chatbots')" type="list-item@3" />
        <template v-else>
          <div
            v-for="bot in chatbots"
            :key="'mobile-' + bot.id"
            class="mobile-chatbot-group"
          >
            <v-list-item
              :active="selectedChatbot?.id === bot.id"
              @click="toggleBot(bot)"
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
                    @click="selectConversationFromBot(bot, conv); mobileSidebarOpen = false"
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
          <v-list-item prepend-icon="mdi-home" title="Startseite" @click="router.push('/Home')" />
        </v-list>
      </template>
    </v-navigation-drawer>

    <div class="chat-container" ref="containerRef">
      <!-- Desktop Sidebar -->
      <aside v-if="!isMobile" class="chat-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <!-- Header with New Chat Button -->
        <div class="sidebar-header">
          <template v-if="!sidebarCollapsed">
            <LBtn
              variant="primary"
              prepend-icon="mdi-plus"
              class="new-chat-btn"
              :disabled="!selectedChatbot"
              @click="createConversation()"
            >
              Neuer Chat
            </LBtn>
          </template>
          <LTooltip v-else text="Neuer Chat" location="right">
            <button
              class="new-chat-btn-mini"
              :disabled="!selectedChatbot"
              @click="createConversation()"
            >
              <v-icon size="20">mdi-plus</v-icon>
            </button>
          </LTooltip>
          <button
            class="collapse-btn"
            @click="toggleSidebar"
            :title="sidebarCollapsed ? 'Erweitern' : 'Zuklappen'"
          >
            <v-icon size="18">{{ sidebarCollapsed ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
          </button>
        </div>

        <!-- Search -->
        <div v-if="!sidebarCollapsed" class="sidebar-search">
          <v-text-field
            v-model="searchQuery"
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
          <v-skeleton-loader v-if="isLoading('chatbots')" type="list-item@3" />
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
                @click="toggleBot(bot)"
                :title="sidebarCollapsed ? bot.display_name : undefined"
              >
                <div class="chatbot-avatar">
                  <v-avatar :color="bot.color || '#b0ca97'" size="28">
                    <v-icon color="white" size="16">{{ bot.icon || 'mdi-robot' }}</v-icon>
                  </v-avatar>
                </div>
                <template v-if="!sidebarCollapsed">
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
                  <v-icon
                    class="expand-icon"
                    size="18"
                  >
                    {{ expandedBots[bot.id] ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
                  </v-icon>
                </template>
              </button>

              <!-- Conversations List (Nested) -->
              <div
                v-if="!sidebarCollapsed && expandedBots[bot.id]"
                class="conversations-list"
              >
                <v-skeleton-loader
                  v-if="isLoading('conversations') && selectedChatbot?.id === bot.id"
                  type="list-item@2"
                  class="px-2"
                />
                <template v-else-if="botConversations[bot.id]?.length">
                  <div
                    v-for="conv in getFilteredConversations(bot.id)"
                    :key="conv.id"
                    class="conversation-item"
                    :class="{
                      active: selectedConversation?.id === conv.id && selectedChatbot?.id === bot.id,
                      'title-streaming': getDisplayTitle(conv).isStreaming
                    }"
                    @click.stop="selectConversationFromBot(bot, conv)"
                  >
                    <v-icon size="16" class="conv-icon">mdi-chat-outline</v-icon>
                    <span class="conv-title" :class="{ 'streaming-text': getDisplayTitle(conv).isStreaming }">
                      {{ getDisplayTitle(conv).text }}
                      <span v-if="getDisplayTitle(conv).isStreaming" class="typing-cursor"></span>
                    </span>
                    <div class="conv-actions">
                      <LTooltip text="Umbenennen" location="top">
                        <button class="conv-action" @click.stop="renameConversation(conv)">
                          <v-icon size="14">mdi-pencil</v-icon>
                        </button>
                      </LTooltip>
                      <LTooltip text="Löschen" location="top">
                        <button class="conv-action delete" @click.stop="deleteConversation(conv)">
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

            <div v-if="chatbots.length === 0 && !sidebarCollapsed" class="empty-sidebar">
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
            @click="router.push('/Home')"
            :title="sidebarCollapsed ? 'Zur Startseite' : undefined"
          >
            <v-icon size="20">mdi-home</v-icon>
            <span v-if="!sidebarCollapsed">Startseite</span>
          </button>
        </div>
      </aside>

      <!-- Main Chat Area -->
      <div class="chat-main" :style="sourcePanel.open ? leftPanelStyle() : {}">
        <!-- Chat Header -->
        <div v-if="selectedChatbot" class="chat-header">
          <div class="header-left">
            <!-- Mobile menu button -->
            <v-btn
              v-if="isMobile"
              icon
              variant="text"
              size="small"
              class="mr-2"
              @click="mobileSidebarOpen = true"
            >
              <v-icon>mdi-menu</v-icon>
            </v-btn>
            <v-avatar :color="selectedChatbot.color || '#b0ca97'" :size="isMobile ? 32 : 36" class="bot-avatar">
              <v-icon color="white" :size="isMobile ? 18 : 20">{{ selectedChatbot.icon || 'mdi-robot' }}</v-icon>
            </v-avatar>
            <div class="header-info">
              <div class="header-title" :class="{ 'streaming-text': getHeaderTitle().isStreaming }">
                {{ getHeaderTitle().text }}
                <span v-if="getHeaderTitle().isStreaming" class="typing-cursor"></span>
              </div>
              <div class="header-subtitle">
                {{ selectedChatbot.display_name }}
                <span class="model-name">• {{ selectedChatbot.model_name }}</span>
                <LTag v-if="capabilities?.vision" variant="success" size="sm" class="ml-1">
                  Vision
                </LTag>
              </div>
            </div>
          </div>
          <div class="header-actions">
            <LTooltip :text="sourcePanel.open ? 'Quellen ausblenden' : 'Quellen anzeigen'">
              <button class="header-action" @click="toggleSourcePanel">
                <v-icon size="20">{{ sourcePanel.open ? 'mdi-bookmark-off-outline' : 'mdi-bookmark-multiple-outline' }}</v-icon>
              </button>
            </LTooltip>
            <LTooltip text="Neuer Chat">
              <button class="header-action" @click="createConversation()">
                <v-icon size="20">mdi-plus</v-icon>
              </button>
            </LTooltip>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="!selectedChatbot" class="empty-state">
          <!-- Mobile menu button in empty state -->
          <v-btn
            v-if="isMobile"
            icon
            variant="tonal"
            color="primary"
            size="large"
            class="mb-4"
            @click="mobileSidebarOpen = true"
          >
            <v-icon>mdi-menu</v-icon>
          </v-btn>
          <v-icon :size="isMobile ? 60 : 80" color="grey-lighten-1">mdi-robot-confused</v-icon>
          <h3 :class="isMobile ? 'text-h6 mt-3' : 'text-h5 mt-4'">Chatbot auswählen</h3>
          <p class="text-medium-emphasis" :class="isMobile ? 'text-body-2 px-4' : ''">
            {{ isMobile ? 'Tippen Sie auf das Menü oben' : 'Wählen Sie einen Chatbot aus der Liste' }}, um eine Unterhaltung zu beginnen.
          </p>
        </div>

        <!-- Chat Messages -->
        <div v-else class="chat-messages" ref="chatContainer">
          <!-- Agent Reasoning Display (for ACT, ReAct, ReflAct modes) -->
          <AgentReasoningDisplay
            ref="agentReasoningRef"
            :agent-status="agentStatus"
            :is-processing="isProcessing"
          />

          <!-- Welcome Message -->
          <div v-if="messages.length === 0 && selectedChatbot.welcome_message" class="welcome-message">
            <v-card variant="tonal" color="primary" class="pa-4">
              <div class="d-flex align-center mb-2">
                <v-avatar :color="selectedChatbot.color || 'primary'" size="32" class="mr-2">
                  <v-icon color="white" size="18">{{ selectedChatbot.icon || 'mdi-robot' }}</v-icon>
                </v-avatar>
                <span class="font-weight-bold">{{ selectedChatbot.display_name }}</span>
              </div>
              {{ selectedChatbot.welcome_message }}
            </v-card>
          </div>

          <!-- Messages -->
          <div
            v-for="message in messages"
            :key="message.id"
            :class="['message-container', message.sender]"
          >
            <!-- Bot Avatar -->
            <template v-if="message.sender === 'bot'">
              <v-avatar :color="selectedChatbot?.color || 'primary'" size="36" class="message-avatar">
                <v-icon color="white" size="20">{{ selectedChatbot?.icon || 'mdi-robot' }}</v-icon>
              </v-avatar>
            </template>

            <div class="message">
              <!-- File attachments -->
              <div v-if="message.files && message.files.length > 0" class="message-files mb-2">
                <v-chip
                  v-for="(file, idx) in message.files"
                  :key="idx"
                  size="small"
                  variant="outlined"
                  class="mr-1 mb-1"
                >
                  <v-icon start size="14">
                    {{ getFileIcon(file.type) }}
                  </v-icon>
                  {{ file.filename }}
                </v-chip>
              </div>

              <div
                class="message-content"
                v-html="formatMessage(message.content, message.sources)"
                @click="handleFootnoteClick($event, message.sources)"
              ></div>

              <!-- Sources Legend -->
              <div v-if="message.sources && message.sources.length > 0" class="message-sources mt-2">
                <div class="sources-legend">
                  <div class="sources-header text-caption d-flex align-center mb-1">
                    <v-icon size="14" class="mr-1">mdi-bookmark-multiple</v-icon>
                    <span>Quellen</span>
                  </div>
                  <div class="sources-list">
                    <v-chip
                      v-for="source in message.sources"
                      :key="source.footnote_id"
                      size="x-small"
                      variant="tonal"
                      color="success"
                      class="source-chip mr-1 mb-1"
                      @click="showSourceDetail(source)"
                    >
                      <span class="font-weight-bold mr-1">[{{ source.footnote_id }}]</span>
                      <span class="text-truncate" style="max-width: 180px;">
                        {{ source.title || source.filename || 'Quelle' }}
                      </span>
                    </v-chip>
                  </div>
                </div>
              </div>

              <div v-if="message.streaming" class="stream-indicator">
                <v-progress-circular indeterminate size="12" width="2" />
              </div>
              <div class="message-timestamp">{{ message.timestamp }}</div>
            </div>
          </div>
        </div>

        <!-- Chat Input -->
        <div v-if="selectedChatbot" class="chat-input">
          <!-- File Preview -->
          <div v-if="selectedFiles.length > 0" class="file-preview mb-2">
            <v-chip
              v-for="(file, idx) in selectedFiles"
              :key="idx"
              closable
              size="small"
              class="mr-1"
              @click:close="removeFile(idx)"
            >
              <v-icon start size="14">{{ getFileIcon(file.type) }}</v-icon>
              {{ file.name }}
              <span class="text-caption ml-1">({{ formatFileSize(file.size) }})</span>
            </v-chip>
          </div>

          <div class="d-flex align-center gap-2">
            <!-- File Upload Button -->
            <v-btn
              icon
              variant="text"
              :disabled="isProcessing"
              @click="triggerFileInput"
              :title="fileUploadTooltip"
            >
              <v-icon>mdi-paperclip</v-icon>
            </v-btn>
            <input
              ref="fileInput"
              type="file"
              multiple
              :accept="acceptedFileTypes"
              style="display: none"
              @change="handleFileSelect"
            />

            <!-- Message Input -->
            <v-text-field
              v-model="newMessage"
              @keyup.enter="sendMessage"
              placeholder="Schreibe eine Nachricht..."
              variant="outlined"
              :loading="isProcessing"
              :disabled="isProcessing"
              hide-details
              density="comfortable"
              class="flex-grow-1"
            />

            <!-- Send Button -->
            <v-btn
              icon
              color="primary"
              :disabled="(!newMessage.trim() && selectedFiles.length === 0) || isProcessing"
              :loading="isProcessing"
              @click="sendMessage"
            >
              <v-icon>mdi-send</v-icon>
            </v-btn>
          </div>

          <!-- Supported file types info -->
          <div class="text-caption text-medium-emphasis mt-1">
            <template v-if="capabilities?.vision">
              Bilder, PDFs, Word, Excel, PowerPoint
            </template>
            <template v-else>
              PDFs, Word, Excel, PowerPoint (kein Bild-Support)
            </template>
          </div>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        v-if="sourcePanel.open"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Sources Side Panel - LLARS Design -->
      <div v-if="sourcePanel.open" class="sources-panel" :style="rightPanelStyle()">
        <div class="sources-panel-card">
          <!-- Panel Header -->
          <div class="sources-panel-header">
            <div class="header-title-area">
              <div class="source-icon">
                <v-icon size="20">mdi-bookmark-multiple</v-icon>
              </div>
              <div class="source-title-info">
                <span class="source-title">
                  {{ sourcePanel.source?.title || sourcePanel.source?.filename || 'Quelle' }}
                </span>
                <span v-if="sourcePanel.source?.collection_name" class="source-collection">
                  {{ sourcePanel.source.collection_name }}
                </span>
              </div>
            </div>
            <div class="header-actions">
              <LTooltip :text="sourcePanel.pinned ? 'Lösen' : 'Anheften'">
                <button
                  class="panel-action"
                  :class="{ active: sourcePanel.pinned }"
                  @click="sourcePanel.pinned = !sourcePanel.pinned"
                >
                  <v-icon size="18">{{ sourcePanel.pinned ? 'mdi-pin' : 'mdi-pin-outline' }}</v-icon>
                </button>
              </LTooltip>
              <LTooltip text="Schließen">
                <button class="panel-action close" @click="closeSourcePanel">
                  <v-icon size="18">mdi-close</v-icon>
                </button>
              </LTooltip>
            </div>
          </div>

          <!-- Custom Tabs -->
          <div class="source-tabs">
            <button
              class="source-tab"
              :class="{ active: sourcePanel.tab === 'excerpt' }"
              @click="sourcePanel.tab = 'excerpt'"
            >
              <v-icon size="16">mdi-text-box</v-icon>
              <span>Ausschnitt</span>
            </button>
            <button
              class="source-tab"
              :class="{ active: sourcePanel.tab === 'screenshot', disabled: !sourcePanel.source?.screenshot_url && !sourcePanel.source?.document_id }"
              :disabled="!sourcePanel.source?.screenshot_url && !sourcePanel.source?.document_id"
              @click="sourcePanel.tab = 'screenshot'"
            >
              <v-icon size="16">mdi-image</v-icon>
              <span>Screenshot</span>
            </button>
            <button
              class="source-tab"
              :class="{ active: sourcePanel.tab === 'document', disabled: !sourcePanel.source?.content_url }"
              :disabled="!sourcePanel.source?.content_url"
              @click="sourcePanel.tab = 'document'"
            >
              <v-icon size="16">mdi-file-document</v-icon>
              <span>Dokument</span>
            </button>
          </div>

          <!-- Tab Content -->
          <div class="sources-panel-body">
            <!-- Excerpt Tab -->
            <div v-if="sourcePanel.tab === 'excerpt'" class="tab-content">
              <div v-if="!sourcePanel.source" class="empty-source">
                <v-icon size="48" class="mb-2">mdi-bookmark-outline</v-icon>
                <div>Quelle auswählen</div>
              </div>
              <template v-else>
                <!-- Metadata Tags -->
                <div class="source-metadata">
                  <LTag v-if="sourcePanel.source.collection_name" variant="primary" size="sm" prepend-icon="mdi-folder">
                    {{ sourcePanel.source.collection_name }}
                  </LTag>
                  <LTag v-if="sourcePanel.source.page_number" variant="gray" size="sm" prepend-icon="mdi-book-open-page-variant">
                    Seite {{ sourcePanel.source.page_number }}
                  </LTag>
                  <LTag v-if="sourcePanel.source.chunk_index !== null && sourcePanel.source.chunk_index !== undefined" variant="gray" size="sm" prepend-icon="mdi-text">
                    Chunk {{ sourcePanel.source.chunk_index }}
                  </LTag>
                  <LTag v-if="sourcePanel.source.relevance !== null && sourcePanel.source.relevance !== undefined" variant="success" size="sm" prepend-icon="mdi-check-circle">
                    {{ ((sourcePanel.source.relevance || 0) * 100).toFixed(0) }}% relevant
                  </LTag>
                </div>

                <!-- Excerpt Text -->
                <div class="excerpt-box">
                  <div class="excerpt-label">
                    <v-icon size="14">mdi-format-quote-open</v-icon>
                    Textausschnitt
                  </div>
                  <div class="excerpt-text">
                    {{ sourcePanel.source.excerpt }}
                  </div>
                </div>

                <!-- Actions -->
                <div class="source-actions">
                  <LBtn
                    v-if="sourcePanel.source.download_url"
                    :href="sourcePanel.source.download_url"
                    target="_blank"
                    rel="noopener"
                    variant="primary"
                    size="small"
                    prepend-icon="mdi-download"
                  >
                    Download
                  </LBtn>
                  <LBtn
                    variant="text"
                    size="small"
                    prepend-icon="mdi-file-search"
                    :disabled="!sourcePanel.source.content_url"
                    @click="sourcePanel.tab = 'document'"
                  >
                    Volltext anzeigen
                  </LBtn>
                </div>
              </template>
            </div>

            <!-- Screenshot Tab -->
            <div v-else-if="sourcePanel.tab === 'screenshot'" class="tab-content">
              <v-skeleton-loader v-if="sourcePanel.loadingScreenshot" type="image" height="320" class="skeleton-llars" />
              <div v-else-if="sourcePanel.screenshotError" class="error-box">
                <v-icon size="24" color="error">mdi-alert-circle</v-icon>
                <span>{{ sourcePanel.screenshotError }}</span>
              </div>
              <div v-else class="screenshot-container">
                <div v-if="!sourcePanel.screenshotBlobUrl" class="empty-source">
                  <v-icon size="48" class="mb-2">mdi-image-off</v-icon>
                  <div>Kein Screenshot verfügbar</div>
                </div>
                <template v-else>
                  <div class="screenshot-actions">
                    <LBtn
                      size="small"
                      variant="secondary"
                      prepend-icon="mdi-fullscreen"
                      @click="openFullscreen('screenshot')"
                    >
                      Vergrößern
                    </LBtn>
                  </div>
                  <div class="screenshot-frame" @click="openFullscreen('screenshot')">
                    <v-img :src="sourcePanel.screenshotBlobUrl" contain max-height="420">
                      <template #placeholder>
                        <div class="d-flex align-center justify-center fill-height">
                          <v-progress-circular indeterminate color="primary" size="24" />
                        </div>
                      </template>
                    </v-img>
                  </div>
                </template>
              </div>
            </div>

            <!-- Document Tab -->
            <div v-else-if="sourcePanel.tab === 'document'" class="tab-content">
              <v-skeleton-loader v-if="sourcePanel.loadingContent" type="article" class="skeleton-llars" />
              <div v-else-if="sourcePanel.contentError" class="error-box">
                <v-icon size="24" color="error">mdi-alert-circle</v-icon>
                <span>{{ sourcePanel.contentError }}</span>
              </div>
              <div v-else class="document-container">
                <div v-if="!sourcePanel.documentContent" class="empty-source">
                  <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
                  <div>Kein Inhalt verfügbar</div>
                </div>
                <template v-else>
                  <div class="document-actions">
                    <LBtn
                      size="small"
                      variant="secondary"
                      prepend-icon="mdi-fullscreen"
                      @click="openFullscreen('document')"
                    >
                      Vergrößern
                    </LBtn>
                  </div>
                  <div class="document-text">
                    {{ sourcePanel.documentContent }}
                  </div>
                </template>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Fullscreen Dialog - LLARS Design -->
    <v-dialog v-model="fullscreenDialog.show" fullscreen transition="dialog-bottom-transition">
      <div class="fullscreen-dialog">
        <div class="fullscreen-header">
          <div class="fullscreen-title">
            <v-icon size="20" class="mr-2">{{ fullscreenDialog.type === 'screenshot' ? 'mdi-image' : 'mdi-file-document' }}</v-icon>
            <span>{{ sourcePanel.source?.title || sourcePanel.source?.filename || 'Quelle' }}</span>
          </div>
          <button class="fullscreen-close" @click="fullscreenDialog.show = false">
            <v-icon size="20">mdi-close</v-icon>
          </button>
        </div>
        <div class="fullscreen-body">
          <!-- Screenshot Fullscreen -->
          <template v-if="fullscreenDialog.type === 'screenshot'">
            <div class="fullscreen-image-wrapper">
              <img
                v-if="sourcePanel.screenshotBlobUrl"
                :src="sourcePanel.screenshotBlobUrl"
                alt="Screenshot"
                class="fullscreen-img"
              />
            </div>
          </template>
          <!-- Document Fullscreen -->
          <template v-else-if="fullscreenDialog.type === 'document'">
            <div class="fullscreen-document-wrapper">
              <div class="fullscreen-doc-text">
                {{ sourcePanel.documentContent }}
              </div>
            </div>
          </template>
        </div>
      </div>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>

    <!-- Source Detail Dialog -->
    <v-dialog v-model="sourceDialog.show" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-chip size="small" color="primary" class="mr-2">
            [{{ sourceDialog.source?.footnote_id }}]
          </v-chip>
          {{ sourceDialog.source?.title || sourceDialog.source?.filename || 'Quelle' }}
        </v-card-title>
        <v-card-subtitle v-if="sourceDialog.source?.collection_name">
          <v-icon size="14" class="mr-1">mdi-folder</v-icon>
          {{ sourceDialog.source?.collection_name }}
          <LTag variant="success" size="sm" class="ml-2">
            {{ ((sourceDialog.source?.relevance || 0) * 100).toFixed(0) }}% relevant
          </LTag>
        </v-card-subtitle>
        <v-card-subtitle v-if="sourceDialog.source?.filename">
          <v-icon size="14" class="mr-1">mdi-file</v-icon>
          {{ sourceDialog.source.filename }}
        </v-card-subtitle>
        <v-divider />
        <v-card-text class="source-excerpt">
          {{ sourceDialog.source?.excerpt }}
        </v-card-text>
        <v-card-actions>
          <v-btn
            variant="text"
            @click="pinSourceToPanel(sourceDialog.source)"
          >
            <v-icon start>mdi-pin</v-icon>
            Anheften
          </v-btn>
          <v-btn
            v-if="sourceDialog.source?.download_url"
            :href="sourceDialog.source.download_url"
            target="_blank"
            rel="noopener"
            color="primary"
            variant="tonal"
          >
            <v-icon start>mdi-download</v-icon>
            Dokument
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="sourceDialog.show = false">
            Schließen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { io } from 'socket.io-client'
import axios from 'axios'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useChatMessages } from './ChatWithBots/composables/useChatMessages.js'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'
import { useActiveDuration, useTypingMetrics, useScrollDepth, useVisibilityTracker } from '@/composables/useAnalyticsMetrics'
import { matomoTrackEvent } from '@/plugins/llars-metrics'
import { AUTH_STORAGE_KEYS, clearAuthStorage, getAuthStorageItem } from '@/utils/authStorage'
import AgentReasoningDisplay from './Chat/AgentReasoningDisplay.vue'

// Composable for chat message operations
const {
  isProcessing,
  currentSources,
  addUserMessage,
  addBotPlaceholder,
  updateBotMessage,
  setBotError,
  sendViaREST,
  getFileType
} = useChatMessages()

// Skeleton Loading
const { isLoading, withLoading } = useSkeletonLoading(['chatbots', 'conversations'])

// Panel Resize - for sources panel
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 65,
  minLeftPercent: 40,
  maxLeftPercent: 80,
  storageKey: 'chat-sources-panel-width'
})

// Socket.IO connection
const socket = ref(null)

const route = useRoute()
const router = useRouter()

// Mobile detection
const { isMobile, isTablet } = useMobile()
const mobileSidebarOpen = ref(false)

// Chatbot data
const chatbots = ref([])
const selectedChatbot = ref(null)
const capabilities = ref(null)
const conversations = ref([])
const selectedConversation = ref(null)

// Chat state
const messages = ref([])
const newMessage = ref('')
const sessionId = ref(null)

// UI state - sidebar with localStorage persistence
const sidebarCollapsed = ref(false)
const searchQuery = ref('')
const expandedBots = ref({})
const botConversations = ref({})

// Streaming title state
const streamingTitle = ref({
  conversationId: null,
  text: '',
  isStreaming: false
})

// Load sidebar state from localStorage
const storedSidebar = localStorage.getItem('sidebar_chat')
if (storedSidebar !== null) {
  sidebarCollapsed.value = storedSidebar === 'true'
}

// Load expanded state from localStorage
const storedExpanded = localStorage.getItem('chat_expanded_bots')
if (storedExpanded) {
  try {
    expandedBots.value = JSON.parse(storedExpanded)
  } catch {}
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_chat', String(sidebarCollapsed.value))
}

function toggleBot(bot) {
  if (sidebarCollapsed.value) {
    // In collapsed mode, just select the bot
    selectChatbot(bot)
    return
  }

  expandedBots.value[bot.id] = !expandedBots.value[bot.id]
  localStorage.setItem('chat_expanded_bots', JSON.stringify(expandedBots.value))

  // If expanding and not already selected, select the bot and load its conversations
  if (expandedBots.value[bot.id] && selectedChatbot.value?.id !== bot.id) {
    selectChatbot(bot)
  }

  // If expanding, ensure we have conversations loaded for this bot
  if (expandedBots.value[bot.id] && !botConversations.value[bot.id]) {
    loadBotConversations(bot.id)
  }
}

function getChatCount(botId) {
  return botConversations.value[botId]?.length || 0
}

function getFilteredConversations(botId) {
  const convs = botConversations.value[botId] || []
  if (!searchQuery.value) return convs

  const query = searchQuery.value.toLowerCase()
  return convs.filter(c =>
    (c.title || 'Neuer Chat').toLowerCase().includes(query)
  )
}

/**
 * Get display title for a conversation (handles streaming state)
 */
function getDisplayTitle(conv) {
  // Check if this conversation is currently streaming its title
  if (streamingTitle.value.isStreaming && streamingTitle.value.conversationId === conv.id) {
    return {
      text: streamingTitle.value.text || '',
      isStreaming: true
    }
  }
  return {
    text: conv.title || 'Neuer Chat',
    isStreaming: false
  }
}

/**
 * Check if header title should show streaming state
 */
function getHeaderTitle() {
  if (streamingTitle.value.isStreaming && streamingTitle.value.conversationId === selectedConversation.value?.id) {
    return {
      text: streamingTitle.value.text || '',
      isStreaming: true
    }
  }
  return {
    text: selectedConversation.value?.title || selectedChatbot.value?.display_name || '',
    isStreaming: false
  }
}

async function loadBotConversations(botId) {
  try {
    const response = await axios.get(`/api/chatbots/${botId}/conversations`)
    botConversations.value[botId] = response.data.conversations || []
  } catch (error) {
    console.error('Error loading bot conversations:', error)
    botConversations.value[botId] = []
  }
}

async function selectConversationFromBot(bot, conv) {
  if (selectedChatbot.value?.id !== bot.id) {
    await selectChatbot(bot)
  }
  await selectConversation(conv)
}

async function renameConversation(conv) {
  const newTitle = prompt('Neuer Chat-Titel:', conv.title || 'Neuer Chat')
  if (!newTitle || newTitle === conv.title) return

  try {
    await axios.patch(`/api/chatbots/${selectedChatbot.value?.id}/conversations/${conv.id}`, {
      title: newTitle
    })
    // Update local state
    conv.title = newTitle
    if (selectedConversation.value?.id === conv.id) {
      selectedConversation.value.title = newTitle
    }
    // Update in botConversations
    const botId = selectedChatbot.value?.id
    if (botId && botConversations.value[botId]) {
      const idx = botConversations.value[botId].findIndex(c => c.id === conv.id)
      if (idx !== -1) {
        botConversations.value[botId][idx].title = newTitle
      }
    }
    showSnackbar('Chat umbenannt', 'success')
  } catch (error) {
    console.error('Error renaming conversation:', error)
    showSnackbar('Fehler beim Umbenennen', 'error')
  }
}

async function deleteConversation(conv) {
  if (!confirm('Diesen Chat wirklich löschen?')) return

  const botId = selectedChatbot.value?.id
  try {
    await axios.delete(`/api/chatbots/${botId}/conversations/${conv.id}`)

    // Remove from conversations list
    conversations.value = conversations.value.filter(c => c.id !== conv.id)

    // Remove from botConversations
    if (botId && botConversations.value[botId]) {
      botConversations.value[botId] = botConversations.value[botId].filter(c => c.id !== conv.id)
    }

    // If this was the selected conversation, select another or create new
    if (selectedConversation.value?.id === conv.id) {
      if (conversations.value.length > 0) {
        await selectConversation(conversations.value[0])
      } else {
        await createConversation()
      }
    }

    showSnackbar('Chat gelöscht', 'success')
  } catch (error) {
    console.error('Error deleting conversation:', error)
    showSnackbar('Fehler beim Löschen', 'error')
  }
}

const selectedFiles = ref([])

const sourcePanel = ref({
  open: false,
  pinned: false,
  tab: 'excerpt',
  source: null,
  documentContent: '',
  loadedDocumentId: null,
  screenshotBlobUrl: null,
  loadedScreenshotDocumentId: null,
  loadingScreenshot: false,
  screenshotError: null,
  loadingContent: false,
  contentError: null
})

// Refs
const chatContainer = ref(null)
const fileInput = ref(null)

// Snackbar state
const snackbar = ref({
  show: false,
  text: '',
  color: 'success'
})

// Source detail dialog state
const sourceDialog = ref({
  show: false,
  source: null
})

// Fullscreen dialog state
const fullscreenDialog = ref({
  show: false,
  type: null // 'screenshot' or 'document'
})

// Agent reasoning display state
const agentStatus = ref(null)
const agentEventCounter = ref(0)
const agentReasoningRef = ref(null)

// ==================== ANALYTICS ====================

// Entity dimension for the selected chatbot
const chatbotEntity = computed(() => selectedChatbot.value ? `bot:${selectedChatbot.value.id}` : '')

// Session active time tracking for chatbot interactions
useActiveDuration({
  category: 'chat',
  action: 'session_active_ms',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

// Typing metrics for chat input
const typingMetrics = useTypingMetrics({
  category: 'chat',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

// Track typing in the input field
watch(newMessage, (newVal, oldVal) => {
  if (newVal.length > oldVal.length) {
    typingMetrics.recordInput(newVal.length - oldVal.length)
  }
})

// Scroll depth tracking for chat messages
useScrollDepth(chatContainer, {
  category: 'chat',
  action: 'scroll_depth',
  name: () => chatbotEntity.value,
  dimensions: () => ({ entity: chatbotEntity.value })
})

// Track chatbot selection as an action
function trackChatbotSelect(bot) {
  matomoTrackEvent('chat', 'chatbot_select', `bot:${bot.id}`, 1, {
    entity: `bot:${bot.id}`
  })
}

// Track message send as an action (with message length bucket, no content)
function trackMessageSend(charCount) {
  const bucket = charCount < 50 ? 'short' : charCount < 200 ? 'medium' : 'long'
  matomoTrackEvent('chat', 'message_send', `${chatbotEntity.value}|len:${bucket}`, charCount, {
    entity: chatbotEntity.value
  })
}

// ==================== HELPER FUNCTIONS ====================

/**
 * Get the appropriate tag info for a chatbot based on its type
 * Priority: Agent Mode > RAG > null
 */
function getChatbotTypeTag(bot) {
  const agentMode = bot.prompt_settings?.agent_mode

  // Agent modes take priority
  if (agentMode && agentMode !== 'standard') {
    const agentTags = {
      'act': { label: 'ACT', variant: 'success' },
      'react': { label: 'ReAct', variant: 'accent' },
      'reflact': { label: 'ReflAct', variant: 'secondary' }
    }
    return agentTags[agentMode] || null
  }

  // RAG-enabled chatbot
  if (bot.rag_enabled) {
    return { label: 'RAG', variant: 'info' }
  }

  // Simple chatbot - no tag
  return null
}

// ==================== COMPUTED PROPERTIES ====================

const acceptedFileTypes = computed(() => {
  const types = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']
  if (capabilities.value?.vision) {
    types.push('.png', '.jpg', '.jpeg', '.gif', '.webp')
  }
  return types.join(',')
})

const fileUploadTooltip = computed(() => {
  if (capabilities.value?.vision) {
    return 'Bilder und Dokumente hochladen'
  }
  return 'Dokumente hochladen (PDF, Word, Excel, PowerPoint)'
})

// ==================== CHATBOT MANAGEMENT ====================

/**
 * Load available chatbots from API
 */
async function loadChatbots() {
  try {
    const response = await axios.get('/api/chatbots')
    if (response.data.success) {
      // Only show active chatbots
      chatbots.value = response.data.chatbots.filter(b => b.is_active)
    }
  } catch (error) {
    console.error('Error loading chatbots:', error)
    showSnackbar('Fehler beim Laden der Chatbots', 'error')
  }
}

async function maybeAutoSelectFromRoute() {
  const raw = route.query.chatbot_id || route.query.bot
  const id = raw ? parseInt(String(raw), 10) : null
  if (!id || Number.isNaN(id)) return
  if (selectedChatbot.value?.id === id) return

  const bot = chatbots.value.find(b => b.id === id)
  if (!bot) {
    showSnackbar('Chatbot nicht verfügbar oder keine Berechtigung', 'warning')
    return
  }

  await selectChatbot(bot)
}

// ==================== CONVERSATIONS ====================

async function loadConversations(autoSelect = true) {
  if (!selectedChatbot.value) return
  const botId = selectedChatbot.value.id

  await withLoading('conversations', async () => {
    try {
      const response = await axios.get(`/api/chatbots/${botId}/conversations`)
      conversations.value = response.data.conversations || []
      // Also update botConversations for sidebar
      botConversations.value[botId] = conversations.value
    } catch (error) {
      console.error('Error loading conversations:', error)
      conversations.value = []
      botConversations.value[botId] = []
      showSnackbar('Fehler beim Laden der Chats', 'error')
    }
  })

  if (conversations.value.length === 0) {
    await createConversation()
    return
  }

  if (autoSelect && conversations.value.length > 0) {
    await selectConversation(conversations.value[0])
  }
}

async function createConversation(title = null) {
  if (!selectedChatbot.value) return
  const botId = selectedChatbot.value.id

  try {
    const response = await axios.post(`/api/chatbots/${botId}/conversations`, {
      title: title || 'Neuer Chat'
    })
    if (response.data.success) {
      const convo = response.data.conversation
      conversations.value = [convo, ...conversations.value]
      // Also update botConversations for sidebar
      botConversations.value[botId] = [convo, ...(botConversations.value[botId] || []).filter(c => c.id !== convo.id)]
      await selectConversation(convo)
    }
  } catch (error) {
    console.error('Error creating conversation:', error)
    showSnackbar('Fehler beim Anlegen des Chats', 'error')
  }
}

async function selectConversation(conversation) {
  if (!conversation || !selectedChatbot.value) return
  selectedConversation.value = conversation
  sessionId.value = conversation.session_id

  // Reset source panel when switching conversations (sources are chat-specific)
  if (!sourcePanel.value.pinned) {
    sourcePanel.value.open = false
  }
  sourcePanel.value.source = null
  sourcePanel.value.tab = 'excerpt'

  // Close fullscreen dialog if open
  fullscreenDialog.value.show = false

  await loadConversationMessages(conversation.id)
}

async function loadConversationMessages(conversationId) {
  if (!selectedChatbot.value || !conversationId) return

  // Reset agent display before loading new conversation
  agentStatus.value = null
  if (agentReasoningRef.value?.reset) {
    agentReasoningRef.value.reset()
  }

  try {
    const response = await axios.get(`/api/chatbots/${selectedChatbot.value.id}/conversations/${conversationId}`)
    if (response.data.success) {
      const convo = response.data.conversation
      selectedConversation.value = {
        ...convo
      }
      sessionId.value = convo.session_id
      messages.value = (convo.messages || []).map(m => ({
        id: m.id,
        sender: m.role === 'user' ? 'user' : 'bot',
        content: m.content,
        sources: m.rag_sources,
        agentTrace: Array.isArray(m.agent_trace) ? m.agent_trace : [],
        streamMetadata: m.stream_metadata || null,
        timestamp: m.created_at ? new Date(m.created_at).toLocaleTimeString() : '',
        streaming: false
      }))

      // Load agent trace from last assistant message if available
      const lastAgentMessage = [...(convo.messages || [])]
        .reverse()
        .find(m => m.role === 'assistant' && Array.isArray(m.agent_trace) && m.agent_trace.length > 0)

      if (lastAgentMessage) {
        agentEventCounter.value++
        agentStatus.value = {
          type: 'complete',
          mode: lastAgentMessage.stream_metadata?.mode || selectedChatbot.value?.prompt_settings?.agent_mode || 'standard',
          task_type: selectedChatbot.value?.prompt_settings?.task_type || 'lookup',
          reasoning_steps: lastAgentMessage.agent_trace,
          _eventId: agentEventCounter.value
        }
      }
      // If no agent message found, agentStatus stays null (already reset above)
    }
  } catch (error) {
    console.error('Error loading conversation messages:', error)
    showSnackbar('Fehler beim Laden des Chats', 'error')
    messages.value = []
  }
}

function updateConversationTitle(conversationId, title) {
  if (!conversationId || !title) return
  if (selectedConversation.value?.id === conversationId) {
    selectedConversation.value = {
      ...selectedConversation.value,
      title
    }
  }
  const idx = conversations.value.findIndex(c => c.id === conversationId)
  if (idx !== -1) {
    conversations.value[idx] = {
      ...conversations.value[idx],
      title
    }
  }

  // Also update in botConversations for sidebar display
  if (selectedChatbot.value?.id) {
    const convs = botConversations.value[selectedChatbot.value.id]
    if (convs) {
      const botIdx = convs.findIndex(c => c.id === conversationId)
      if (botIdx !== -1) {
        convs[botIdx] = { ...convs[botIdx], title }
      }
    }
  }
}

/**
 * Select a chatbot and load its chat history
 */
async function selectChatbot(bot) {
  trackChatbotSelect(bot)
  selectedChatbot.value = bot
  messages.value = []
  selectedFiles.value = []
  sessionId.value = null
  selectedConversation.value = null
  conversations.value = []
  // Reset agent reasoning display
  agentStatus.value = null
  if (agentReasoningRef.value?.reset) {
    agentReasoningRef.value.reset()
  }

  // Expand this bot in sidebar
  expandedBots.value[bot.id] = true
  localStorage.setItem('chat_expanded_bots', JSON.stringify(expandedBots.value))

  // Load capabilities
  try {
    const response = await axios.get(`/api/chatbots/${bot.id}/capabilities`)
    if (response.data.success) {
      capabilities.value = response.data.capabilities
    }
  } catch (error) {
    console.error('Error loading capabilities:', error)
    capabilities.value = { vision: false, rag: bot.rag_enabled }
  }

  await loadConversations()
}

// ==================== CHAT PERSISTENCE ====================

/**
 * Save current chat to localStorage
 */
function saveChat() {
  // Persistence now handled server-side; keep function as no-op for compatibility
}

/**
 * Clear current chat and localStorage
 */
async function clearChat() {
  await createConversation()
}

// ==================== FILE HANDLING ====================

/**
 * Trigger file input dialog
 */
function triggerFileInput() {
  fileInput.value?.click()
}

/**
 * Handle file selection from input
 */
function handleFileSelect(event) {
  const files = Array.from(event.target.files)
  for (const file of files) {
    if (file.size > 10 * 1024 * 1024) {
      showSnackbar(`${file.name} ist zu groß (max 10MB)`, 'error')
      continue
    }
    selectedFiles.value.push(file)
  }
  // Reset input
  event.target.value = ''
}

/**
 * Remove file from selection
 */
function removeFile(index) {
  selectedFiles.value.splice(index, 1)
}

// ==================== MESSAGE SENDING ====================

/**
 * Main message sending function
 * Handles both text-only and file upload scenarios
 * Uses Socket.IO for streaming when available, falls back to REST API
 */
async function sendMessage() {
  if ((!newMessage.value.trim() && selectedFiles.value.length === 0) || isProcessing.value) return
  if (!selectedChatbot.value) return
  if (!sessionId.value) {
    sessionId.value = crypto.randomUUID()
  }
  if (!selectedConversation.value) {
    await createConversation()
  }

  const userMessage = newMessage.value.trim()
  const files = [...selectedFiles.value]
  const hasFiles = files.length > 0

  // Analytics: Track message send
  if (userMessage) {
    trackMessageSend(userMessage.length)
  }

  // Add user message to chat
  addUserMessage(messages, userMessage, files)

  // Clear input
  newMessage.value = ''
  selectedFiles.value = []
  isProcessing.value = true

  if (agentReasoningRef.value?.reset) {
    agentReasoningRef.value.reset()
  }

  const agentMode = selectedChatbot.value?.prompt_settings?.agent_mode
  if (agentMode && agentMode !== 'standard') {
    agentEventCounter.value++
    agentStatus.value = {
      type: 'init',
      mode: agentMode,
      task_type: selectedChatbot.value?.prompt_settings?.task_type || 'lookup',
      max_iterations: selectedChatbot.value?.prompt_settings?.agent_max_iterations || 5,
      _eventId: agentEventCounter.value
    }
  } else {
    agentStatus.value = null
  }

  // Add placeholder for bot response
  addBotPlaceholder(messages)
  scrollToBottom()

  // Files require REST API (Socket.IO doesn't support file uploads)
  // Also use REST as fallback if socket is not connected
  if (hasFiles || !socket.value?.connected) {
    await sendMessageViaREST(userMessage, files)
  } else {
    // Use Socket.IO for streaming text-only messages
    socket.value.emit('chatbot:stream', {
      chatbot_id: selectedChatbot.value.id,
      message: userMessage,
      session_id: sessionId.value,
      conversation_id: selectedConversation.value?.id,
      username: null,
      token: getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    })
  }
}

/**
 * Send message via REST API
 * Handles both text-only and file upload
 */
async function sendMessageViaREST(userMessage, files = []) {
  try {
    const result = await sendViaREST(
      selectedChatbot.value.id,
      userMessage,
      sessionId.value,
      files,
      selectedConversation.value?.id || null
    )

    if (result.success) {
      if (result.sessionId) {
        sessionId.value = result.sessionId
      }
      if (result.conversationId && (!selectedConversation.value || selectedConversation.value.id !== result.conversationId)) {
        selectedConversation.value = {
          ...(selectedConversation.value || {}),
          id: result.conversationId,
          session_id: result.sessionId || sessionId.value,
          title: result.conversationTitle || selectedConversation.value?.title
        }
        conversations.value = [
          {
            id: result.conversationId,
            session_id: result.sessionId || sessionId.value,
            title: result.conversationTitle || selectedConversation.value?.title || 'Neuer Chat',
            message_count: 0
          },
          ...conversations.value.filter(c => c.id !== result.conversationId)
        ]
      }
      if (result.conversationTitle) {
        updateConversationTitle(result.conversationId || selectedConversation.value?.id, result.conversationTitle)
      }
      updateBotMessage(
        messages,
        result.content,
        new Date().toLocaleTimeString(),
        false,
        result.sources
      )
      if (result.mode && result.mode !== 'standard') {
        agentEventCounter.value++
        agentStatus.value = {
          type: 'complete',
          mode: result.mode,
          task_type: result.task_type,
          reasoning_steps: result.reasoning_steps || [],
          _eventId: agentEventCounter.value
        }
      }
      if (selectedConversation.value) {
        selectedConversation.value.message_count = (selectedConversation.value.message_count || 0) + 2
      }
    } else {
      setBotError(messages)
      showSnackbar(result.error || 'Fehler beim Senden', 'error')
    }
  } catch (error) {
    console.error('Chat error:', error)
    setBotError(messages)
    showSnackbar('Fehler beim Senden', 'error')
  } finally {
    isProcessing.value = false
    scrollToBottom()
  }
}

// ==================== UI UTILITIES ====================

/**
 * Scroll chat container to bottom
 */
function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

/**
 * Show snackbar notification
 */
function showSnackbar(text, color = 'success') {
  snackbar.value = { show: true, text, color }
}

// ==================== MESSAGE FORMATTING ====================

/**
 * Format message content with markdown and footnote support
 */
function formatMessage(content, sources = []) {
  if (!content) return ''

  // Replace footnote references [1], [2], etc. with clickable links
  let processedContent = content
  if (sources && sources.length > 0) {
    // Create a map of footnote_id to source
    const sourceMap = {}
    sources.forEach(s => {
      sourceMap[s.footnote_id] = s
    })

    // Replace [1], [2], etc. with clickable footnote links
    processedContent = content.replace(/\[(\d+)\]/g, (match, num) => {
      const footnoteId = parseInt(num)
      const source = sourceMap[footnoteId]
      if (source) {
        const title = source.title || 'Quelle ' + footnoteId
        // Create a clickable footnote reference (inline, not superscript)
        return `<span class="footnote-ref" data-footnote-id="${footnoteId}" title="${title}">[${num}]</span>`
      }
      return match
    })
  }

  // Parse markdown and sanitize
  const html = marked.parse(processedContent, { breaks: true })
  return DOMPurify.sanitize(html, {
    ADD_ATTR: ['data-footnote-id', 'title']
  })
}

/**
 * Get icon for file type
 */
function getFileIcon(type) {
  switch (type) {
    case 'image': return 'mdi-image'
    case 'pdf': return 'mdi-file-pdf-box'
    case 'word': return 'mdi-file-word'
    case 'excel': return 'mdi-file-excel'
    case 'powerpoint': return 'mdi-file-powerpoint'
    default: return 'mdi-file'
  }
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ==================== SOURCE HANDLING ====================

/**
 * Show source detail dialog
 */
function showSourceDetail(source) {
  if (sourcePanel.value.pinned) {
    openSourceInPanel(source)
    return
  }

  sourceDialog.value = { show: true, source }
}

function openSourceFromCitation(source) {
  if (!source) return
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
  openSourceInPanel(source)
}

function toggleSourcePanel() {
  if (sourcePanel.value.open) {
    closeSourcePanel()
    return
  }
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
}

function closeSourcePanel() {
  sourcePanel.value.open = false
  sourcePanel.value.pinned = false
  sourcePanel.value.tab = 'excerpt'
}

function pinSourceToPanel(source) {
  if (!source) return
  sourcePanel.value.open = true
  sourcePanel.value.pinned = true
  sourceDialog.value.show = false
  openSourceInPanel(source)
}

function openSourceInPanel(source) {
  sourcePanel.value.source = source
  sourcePanel.value.tab = 'excerpt'
  sourcePanel.value.contentError = null
  sourcePanel.value.screenshotError = null

  if (sourcePanel.value.loadedDocumentId !== source?.document_id) {
    sourcePanel.value.documentContent = ''
    sourcePanel.value.loadedDocumentId = source?.document_id || null
  }

  if (sourcePanel.value.loadedScreenshotDocumentId !== source?.document_id) {
    if (sourcePanel.value.screenshotBlobUrl && String(sourcePanel.value.screenshotBlobUrl).startsWith('blob:')) {
      URL.revokeObjectURL(sourcePanel.value.screenshotBlobUrl)
    }
    sourcePanel.value.screenshotBlobUrl = null
    sourcePanel.value.loadedScreenshotDocumentId = source?.document_id || null
  }
}

async function loadPanelDocumentContent() {
  const source = sourcePanel.value.source
  if (!source?.content_url) return
  if (sourcePanel.value.documentContent) return

  sourcePanel.value.loadingContent = true
  sourcePanel.value.contentError = null
  try {
    const response = await axios.get(source.content_url)
    if (response.data?.success) {
      sourcePanel.value.documentContent = response.data.content || ''
    } else {
      sourcePanel.value.contentError = response.data?.error || 'Konnte Dokumenttext nicht laden'
    }
  } catch (error) {
    sourcePanel.value.contentError = error.response?.data?.error || 'Konnte Dokumenttext nicht laden'
  } finally {
    sourcePanel.value.loadingContent = false
  }
}

async function loadPanelScreenshot() {
  const source = sourcePanel.value.source
  if (!source?.screenshot_url && !source?.document_id) return
  if (sourcePanel.value.screenshotBlobUrl) return

  const url = source.screenshot_url || `/api/rag/documents/${source.document_id}/screenshot`

  sourcePanel.value.loadingScreenshot = true
  sourcePanel.value.screenshotError = null
  try {
    const response = await axios.get(url, { responseType: 'blob' })
    sourcePanel.value.screenshotBlobUrl = URL.createObjectURL(response.data)
  } catch (error) {
    sourcePanel.value.screenshotError = error.response?.data?.error || 'Konnte Screenshot nicht laden'
    sourcePanel.value.screenshotBlobUrl = null
  } finally {
    sourcePanel.value.loadingScreenshot = false
  }
}

watch(
  () => sourcePanel.value.tab,
  async (tab) => {
    if (tab === 'document') {
      await loadPanelDocumentContent()
    }
    if (tab === 'screenshot') {
      await loadPanelScreenshot()
    }
  }
)

/**
 * Handle click on footnote references in message content
 */
function handleFootnoteClick(event, sources) {
  const target = event.target
  if (target.classList.contains('footnote-ref')) {
    const footnoteId = parseInt(target.dataset.footnoteId)
    if (sources && sources.length > 0) {
      const source = sources.find(s => s.footnote_id === footnoteId)
      if (source) {
        openSourceFromCitation(source)
      }
    }
  }
}

/**
 * Open fullscreen dialog for screenshot or document
 */
function openFullscreen(type) {
  fullscreenDialog.value = { show: true, type }
}

// ==================== SOCKET.IO SETUP ====================

/**
 * Initialize Socket.IO connection and event handlers
 */
function initSocket() {
  const rawBase = import.meta.env.VITE_API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
  const trimmedBase = String(rawBase || '').replace(/\/+$/, '')
  const baseUrl = trimmedBase.endsWith('/api')
    ? trimmedBase.slice(0, -4)
    : (trimmedBase || (typeof window !== 'undefined' ? window.location.origin : ''))
  const socketioEnableWebsocket = String(import.meta.env.VITE_SOCKETIO_ENABLE_WEBSOCKET || '').toLowerCase() === 'true'
  const socketioTransports = socketioEnableWebsocket ? ['polling', 'websocket'] : ['polling']

  socket.value = io(baseUrl, {
    path: '/socket.io/',
    transports: socketioTransports,
    upgrade: socketioEnableWebsocket
  })

  socket.value.on('connect', () => {
    console.log('ChatWithBots: Socket connected')
  })

  socket.value.on('disconnect', () => {
    console.log('ChatWithBots: Socket disconnected')
  })

  // Sources are sent BEFORE streaming, so we store them for the current message
  socket.value.on('chatbot:sources', (data) => {
    currentSources.value = data.sources || []
    // Assign sources to the current bot message placeholder
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx].sources = currentSources.value
    }
  })

  // Streaming response chunks
  socket.value.on('chatbot:response', (data) => {
    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      if (data.content) {
        messages.value[lastIdx].content += data.content
        scrollToBottom()
      }
      if (data.complete) {
        messages.value[lastIdx].streaming = false
        messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
        // Ensure sources are assigned
        if (currentSources.value.length > 0 && !messages.value[lastIdx].sources) {
          messages.value[lastIdx].sources = currentSources.value
        }
        currentSources.value = []
        if (selectedConversation.value) {
          selectedConversation.value.message_count = (selectedConversation.value.message_count || 0) + 2
        }
        isProcessing.value = false
        saveChat()
        scrollToBottom()
      }
    }
  })

  // Completion metadata
  socket.value.on('chatbot:complete', (data) => {
    console.log('Chatbot response complete:', data)
    const convId = data.conversation_id
    const convTitle = data.title || selectedConversation.value?.title || 'Neuer Chat'

    if (convId && (!selectedConversation.value || selectedConversation.value.id !== convId)) {
      selectedConversation.value = {
        ...(selectedConversation.value || {}),
        id: convId,
        session_id: data.session_id || sessionId.value,
        title: convTitle
      }
      conversations.value = [
        {
          id: convId,
          session_id: data.session_id || sessionId.value,
          title: convTitle
        },
        ...conversations.value.filter(c => c.id !== convId)
      ]

      // Also add/update in botConversations for sidebar
      if (selectedChatbot.value?.id) {
        const botId = selectedChatbot.value.id
        if (!botConversations.value[botId]) {
          botConversations.value[botId] = []
        }
        const existingIdx = botConversations.value[botId].findIndex(c => c.id === convId)
        if (existingIdx === -1) {
          // Add new conversation at the beginning
          botConversations.value[botId].unshift({
            id: convId,
            session_id: data.session_id || sessionId.value,
            title: convTitle
          })
        } else {
          // Update existing
          botConversations.value[botId][existingIdx] = {
            ...botConversations.value[botId][existingIdx],
            title: convTitle
          }
        }
      }
    }
    if (data.title) {
      updateConversationTitle(convId || selectedConversation.value?.id, data.title)
    }
    if (data.session_id && !sessionId.value) {
      sessionId.value = data.session_id
    }
    // Reset agent status on completion
    if (data.mode && data.mode !== 'standard') {
      agentStatus.value = { type: 'complete', ...data }
    }
  })

  // Agent status updates (for ACT, ReAct, ReflAct modes)
  socket.value.on('chatbot:agent_status', (data) => {
    // Add unique counter to ensure Vue detects each event
    agentEventCounter.value++
    agentStatus.value = { ...data, _eventId: agentEventCounter.value }
    console.log('Agent status:', data.type, agentEventCounter.value)
  })

  // Title streaming events
  socket.value.on('chatbot:title_generating', (data) => {
    const convId = data.conversation_id || selectedConversation.value?.id
    streamingTitle.value = {
      conversationId: convId,
      text: '',
      isStreaming: true
    }
  })

  socket.value.on('chatbot:title_delta', (data) => {
    if (streamingTitle.value.isStreaming && data.delta) {
      // Update conversation_id if provided (for first message when selectedConversation isn't set yet)
      if (data.conversation_id && !streamingTitle.value.conversationId) {
        streamingTitle.value.conversationId = data.conversation_id
      }
      streamingTitle.value.text += data.delta
    }
  })

  socket.value.on('chatbot:title_complete', (data) => {
    const convId = data.conversation_id || streamingTitle.value.conversationId
    if (data.title && convId) {
      // Update conversation title in all relevant places
      updateConversationTitle(convId, data.title)
    }

    // Reset streaming state after a brief delay for animation
    setTimeout(() => {
      streamingTitle.value = {
        conversationId: null,
        text: '',
        isStreaming: false
      }
    }, 300)
  })

  // Error handling
  socket.value.on('chatbot:error', (data) => {
    const errMsg = String(data?.error || '')
    console.error('Chatbot error:', errMsg)

    const code = String(data?.code || '')
    const lower = errMsg.toLowerCase()
    const isAuthError = (
      code.startsWith('AUTH_') ||
      lower.includes('authentication required') ||
      lower.includes('authentication failed') ||
      lower.includes('jwt expired')
    )

    if (isAuthError) {
      clearAuthStorage()
      try {
        localStorage.removeItem('username')
      } catch {}

      const current = `${window.location.pathname}${window.location.search}${window.location.hash}`
      window.location.href = `/login?redirect=${encodeURIComponent(current)}`
      return
    }

    const lastIdx = messages.value.length - 1
    if (lastIdx >= 0 && messages.value[lastIdx].sender === 'bot') {
      messages.value[lastIdx].content = errMsg || 'Ein Fehler ist aufgetreten.'
      messages.value[lastIdx].streaming = false
      messages.value[lastIdx].timestamp = new Date().toLocaleTimeString()
    }
    isProcessing.value = false
    showSnackbar(errMsg || 'Fehler beim Senden', 'error')
  })
}

/**
 * Disconnect Socket.IO connection
 */
function disconnectSocket() {
  if (socket.value) {
    socket.value.disconnect()
    socket.value = null
  }
}

// ==================== WATCHERS ====================

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

// ==================== LIFECYCLE HOOKS ====================

onMounted(async () => {
  await withLoading('chatbots', async () => {
    await loadChatbots()
  })

  // Preload conversations for all chatbots (for sidebar counts)
  for (const bot of chatbots.value) {
    loadBotConversations(bot.id)
  }

  await maybeAutoSelectFromRoute()
  initSocket()
})

onUnmounted(() => {
  disconnectSocket()
})
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 94px); /* 64px AppBar + 30px Footer */
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

.chat-container {
  height: 100%;
  display: flex;
  overflow: hidden;
}

/* ==================== MODERN GROUPED SIDEBAR ==================== */
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
  border-radius: 16px 4px 16px 4px !important; /* LLARS asymmetric */
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
}

.collapse-btn:hover {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
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

/* ==================== MAIN CHAT AREA ==================== */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
  overflow: hidden;
  min-width: 0;
}

/* Chat Header - Modern LLARS Style */
.chat-header {
  padding: 12px 20px;
  background: linear-gradient(180deg, rgba(var(--v-theme-primary), 0.08) 0%, rgba(var(--v-theme-primary), 0.02) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.bot-avatar {
  flex-shrink: 0;
  border-radius: 12px 4px 12px 4px !important;
}

.header-info {
  min-width: 0;
}

.header-title {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.model-name {
  opacity: 0.7;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.header-action {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.05);
  border-radius: 10px 4px 10px 4px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.header-action:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  max-width: 600px;
  margin: 0 auto;
}

.message-container {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 80%;
}

.message-container.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.message {
  padding: 12px 16px;
  border-radius: 12px;
  position: relative;
  min-width: 100px;
}

.message-container.user .message {
  background: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-on-primary));
  border-bottom-right-radius: 4px;
}

.message-container.bot .message {
  background: rgb(var(--v-theme-surface-variant));
  color: rgb(var(--v-theme-on-surface));
  border-bottom-left-radius: 4px;
}

.message-content {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-content :deep(p) {
  margin-bottom: 0.5em;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

/* Listen-Einrückung für bessere Lesbarkeit */
.message-content :deep(ul),
.message-content :deep(ol) {
  padding-left: 1.5em;
  margin-left: 0.5em;
  margin-top: 0.5em;
  margin-bottom: 0.5em;
}

/* Verschachtelte Listen weniger einrücken */
.message-content :deep(ul ul),
.message-content :deep(ol ol),
.message-content :deep(ul ol),
.message-content :deep(ol ul) {
  margin-left: 0;
  margin-top: 0.25em;
  margin-bottom: 0.25em;
}

/* List-Item Abstände */
.message-content :deep(li) {
  margin-bottom: 0.25em;
}

.message-content :deep(li:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
}

/* Footnote references styling */
.message-content :deep(.footnote-ref) {
  color: #5a8a4a;
  cursor: pointer;
  font-weight: 600;
  font-size: inherit;
  padding: 0 2px;
  border-radius: 3px;
  transition: all 0.2s ease;
}

.message-content :deep(.footnote-ref:hover) {
  background: rgba(90, 138, 74, 0.15);
  text-decoration: underline;
}

/* Dark mode: etwas heller für Kontrast */
.v-theme--dark .message-content :deep(.footnote-ref) {
  color: #8ab878;
}

.v-theme--dark .message-content :deep(.footnote-ref:hover) {
  background: rgba(138, 184, 120, 0.2);
}

.message-files {
  display: flex;
  flex-wrap: wrap;
}

.message-sources {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  padding-top: 8px;
}

.sources-legend {
  padding: 4px 0;
}

.sources-header {
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.7;
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.source-chip {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.source-chip:hover {
  transform: scale(1.05);
}

.source-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.source-item:last-child {
  border-bottom: none;
}

.message-timestamp {
  font-size: 0.75rem;
  opacity: 0.7;
  margin-top: 4px;
}

.stream-indicator {
  margin-top: 8px;
}

.chat-input {
  padding: 16px 24px;
  background: rgb(var(--v-theme-surface));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

/* ==================== SOURCES PANEL - LLARS DESIGN ==================== */
.sources-panel {
  background: rgb(var(--v-theme-surface));
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  min-width: 0;
}

/* Resize Divider */
.resize-divider {
  width: 6px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: background-color 0.2s ease;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.2);
}

.resize-handle {
  width: 4px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: var(--llars-primary, #b0ca97);
}

/* Panel Card */
.sources-panel-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Panel Header */
.sources-panel-header {
  padding: 12px 16px;
  background: linear-gradient(180deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-primary), 0.03) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 56px;
}

.header-title-area {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.source-icon {
  width: 36px;
  height: 36px;
  background: var(--llars-primary, #b0ca97);
  border-radius: 10px 4px 10px 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.source-title-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 2px;
}

.source-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-collection {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sources-panel-header .header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.panel-action {
  width: 32px;
  height: 32px;
  border: none;
  background: rgba(var(--v-theme-on-surface), 0.06);
  border-radius: 8px 3px 8px 3px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.panel-action:hover {
  background: rgba(var(--v-theme-primary), 0.15);
  color: rgb(var(--v-theme-primary));
}

.panel-action.active {
  background: rgba(var(--v-theme-primary), 0.2);
  color: var(--llars-primary, #b0ca97);
}

.panel-action.close:hover {
  background: rgba(232, 160, 135, 0.2);
  color: #e8a087;
}

/* Custom Tabs */
.source-tabs {
  display: flex;
  padding: 8px 12px;
  gap: 6px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.source-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  background: transparent;
  border-radius: 10px 4px 10px 4px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.source-tab:hover:not(.disabled) {
  background: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-on-surface));
}

.source-tab.active {
  background: var(--llars-primary, #b0ca97);
  color: white;
  box-shadow: 0 2px 8px rgba(176, 202, 151, 0.3);
}

.source-tab.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Panel Body */
.sources-panel-body {
  flex: 1;
  overflow: hidden;
}

.tab-content {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
}

/* Empty State */
.empty-source {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-align: center;
}

/* Error Box */
.error-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(232, 160, 135, 0.1);
  border: 1px solid rgba(232, 160, 135, 0.3);
  border-radius: 12px 4px 12px 4px;
  color: #e8a087;
}

/* Metadata Tags */
.source-metadata {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

/* Excerpt Box */
.excerpt-box {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  margin-bottom: 16px;
}

.excerpt-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  font-size: 12px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.excerpt-text {
  padding: 14px;
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: rgb(var(--v-theme-on-surface));
}

/* Source Actions */
.source-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Screenshot Container */
.screenshot-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screenshot-actions {
  display: flex;
  justify-content: flex-end;
}

.screenshot-frame {
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
  cursor: zoom-in;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.screenshot-frame:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

/* Document Container */
.document-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-actions {
  display: flex;
  justify-content: flex-end;
}

.document-text {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: rgb(var(--v-theme-on-surface));
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}

/* Skeleton Loader LLARS style */
.skeleton-llars :deep(.v-skeleton-loader__bone) {
  border-radius: 12px 4px 12px 4px;
}

.file-preview {
  display: flex;
  flex-wrap: wrap;
}

.gap-2 {
  gap: 8px;
}

/* Source detail dialog (legacy) */
.source-excerpt {
  white-space: pre-wrap;
  line-height: 1.6;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  font-size: 0.9rem;
  max-height: 400px;
  overflow-y: auto;
}

/* ==================== FULLSCREEN DIALOG - LLARS DESIGN ==================== */
.fullscreen-dialog {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
}

.fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(180deg, var(--llars-primary, #b0ca97) 0%, #9ab886 100%);
  color: white;
  min-height: 56px;
}

.fullscreen-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 15px;
  min-width: 0;
}

.fullscreen-title span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.fullscreen-close {
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px 4px 10px 4px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.fullscreen-close:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.05);
}

.fullscreen-body {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgb(var(--v-theme-background));
}

.fullscreen-image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: auto;
  padding: 24px;
}

.fullscreen-img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  border-radius: 16px 4px 16px 4px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.2);
}

.fullscreen-document-wrapper {
  width: 100%;
  height: 100%;
  overflow: auto;
  padding: 32px;
}

.fullscreen-doc-text {
  max-width: 900px;
  margin: 0 auto;
  white-space: pre-wrap;
  line-height: 1.9;
  font-size: 15px;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  padding: 32px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
}

@media (max-width: 960px) {
  .chat-sidebar {
    display: none;
  }

  .message-container {
    max-width: 90%;
  }

  .resize-divider {
    display: none;
  }

  .sources-panel {
    position: fixed;
    top: 64px;
    left: 0;
    right: 0;
    bottom: 30px;
    width: 100% !important;
    z-index: 100;
  }
}

/* ==================== TITLE STREAMING ANIMATION ==================== */
.streaming-text {
  display: inline-flex;
  align-items: center;
}

.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1em;
  background: var(--llars-primary, #b0ca97);
  margin-left: 2px;
  animation: blink 0.8s steps(1) infinite;
  vertical-align: middle;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

.title-streaming .conv-title {
  color: var(--llars-primary, #b0ca97);
  font-weight: 500;
}

.header-title.streaming-text {
  color: var(--llars-primary, #b0ca97);
}

/* Smooth text appearance animation */
.conv-title.streaming-text,
.header-title.streaming-text {
  animation: textAppear 0.15s ease-out;
}

@keyframes textAppear {
  from {
    opacity: 0.7;
  }
  to {
    opacity: 1;
  }
}

/* ========================================
   MOBILE RESPONSIVE STYLES
   ======================================== */

/* Mobile chat page */
.chat-page.is-mobile {
  height: 100vh;
  height: 100dvh;
}

.chat-page.is-mobile .chat-container {
  width: 100%;
}

.chat-page.is-mobile .chat-main {
  width: 100%;
  flex: 1;
}

/* Mobile drawer styles */
.mobile-chat-drawer {
  background-color: rgb(var(--v-theme-surface)) !important;
}

.mobile-drawer-header {
  padding: 16px;
}

.mobile-drawer-content {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-chatbot-group {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.mobile-chatbot-header {
  min-height: 56px;
}

.mobile-conversations-list {
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  padding-left: 16px;
}

.mobile-conversation-item {
  min-height: 44px;
}

/* Mobile chat header */
.chat-page.is-mobile .chat-header {
  padding: 8px 12px;
}

.chat-page.is-mobile .header-info {
  min-width: 0;
}

.chat-page.is-mobile .header-title {
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-page.is-mobile .header-subtitle {
  font-size: 0.7rem;
}

.chat-page.is-mobile .model-name {
  display: none;
}

/* Mobile empty state */
.chat-page.is-mobile .empty-state {
  padding: 24px 16px;
}

/* Mobile messages */
.chat-page.is-mobile .chat-messages {
  padding: 12px;
}

.chat-page.is-mobile .message-container {
  gap: 8px;
}

.chat-page.is-mobile .message-avatar {
  width: 28px !important;
  height: 28px !important;
}

.chat-page.is-mobile .message {
  max-width: 90%;
  padding: 10px 12px;
  font-size: 0.9rem;
}

/* Mobile input area */
.chat-page.is-mobile .chat-input-area {
  padding: 8px 12px;
}

.chat-page.is-mobile .input-actions {
  gap: 4px;
}

/* Hide sources panel on mobile by default */
.chat-page.is-mobile .sources-panel {
  display: none;
}

/* Tablet styles */
.chat-page.is-tablet .chat-sidebar {
  width: 240px;
  min-width: 240px;
}

.chat-page.is-tablet .chat-sidebar.collapsed {
  width: 56px;
  min-width: 56px;
}
</style>
