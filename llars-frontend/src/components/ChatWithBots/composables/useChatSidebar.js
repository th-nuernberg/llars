/**
 * useChatSidebar.js
 * Composable for managing chat sidebar state and interactions
 */
import { ref, computed } from 'vue'
import axios from 'axios'

export function useChatSidebar() {
  // Sidebar UI state with localStorage persistence
  const sidebarCollapsed = ref(false)
  const searchQuery = ref('')
  const expandedBots = ref({})
  const botConversations = ref({})
  const mobileSidebarOpen = ref(false)

  // Streaming title state
  const streamingTitle = ref({
    conversationId: null,
    text: '',
    isStreaming: false
  })

  // Load sidebar state from localStorage
  function loadSidebarState() {
    const storedSidebar = localStorage.getItem('sidebar_chat')
    // Default to expanded (false = not collapsed)
    if (storedSidebar !== null) {
      sidebarCollapsed.value = storedSidebar === 'true'
    } else {
      // Ensure sidebar starts expanded by default
      sidebarCollapsed.value = false
    }

    const storedExpanded = localStorage.getItem('chat_expanded_bots')
    if (storedExpanded) {
      try {
        expandedBots.value = JSON.parse(storedExpanded)
      } catch {
        expandedBots.value = {}
      }
    }
  }

  /**
   * Force expand the sidebar (for recovery from broken state)
   */
  function expandSidebar() {
    sidebarCollapsed.value = false
    localStorage.setItem('sidebar_chat', 'false')
  }

  /**
   * Toggle sidebar collapsed state
   */
  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
    localStorage.setItem('sidebar_chat', String(sidebarCollapsed.value))
  }

  /**
   * Toggle bot expansion in sidebar
   * @param {Object} bot - The chatbot object
   * @param {Function} onBotSelect - Callback when bot is selected
   * @param {Function} onLoadConversations - Callback to load conversations
   */
  function toggleBot(bot, onBotSelect, onLoadConversations) {
    if (sidebarCollapsed.value) {
      // In collapsed mode, just select the bot
      if (onBotSelect) onBotSelect(bot)
      return
    }

    expandedBots.value[bot.id] = !expandedBots.value[bot.id]
    localStorage.setItem('chat_expanded_bots', JSON.stringify(expandedBots.value))

    // If expanding and not already selected, select the bot
    if (expandedBots.value[bot.id] && onBotSelect) {
      onBotSelect(bot)
    }

    // If expanding, ensure we have conversations loaded
    if (expandedBots.value[bot.id] && !botConversations.value[bot.id] && onLoadConversations) {
      onLoadConversations(bot.id)
    }
  }

  /**
   * Expand a specific bot in the sidebar
   */
  function expandBot(botId) {
    expandedBots.value[botId] = true
    localStorage.setItem('chat_expanded_bots', JSON.stringify(expandedBots.value))
  }

  /**
   * Get chat count for a bot
   */
  function getChatCount(botId) {
    return botConversations.value[botId]?.length || 0
  }

  /**
   * Get filtered conversations for a bot based on search query
   */
  function getFilteredConversations(botId) {
    const convs = botConversations.value[botId] || []
    if (!searchQuery.value) return convs

    const query = searchQuery.value.toLowerCase()
    return convs.filter(c =>
      (c.title || 'Neuer Chat').toLowerCase().includes(query)
    )
  }

  /**
   * Load conversations for a specific bot
   */
  async function loadBotConversations(botId) {
    try {
      const response = await axios.get(`/api/chatbots/${botId}/conversations`)
      botConversations.value[botId] = response.data.conversations || []
    } catch (error) {
      console.error('Error loading bot conversations:', error)
      botConversations.value[botId] = []
    }
  }

  /**
   * Update conversations for a bot
   */
  function setBotConversations(botId, conversations) {
    botConversations.value[botId] = conversations
  }

  /**
   * Add or update a conversation in bot conversations
   */
  function upsertConversation(botId, conversation) {
    if (!botConversations.value[botId]) {
      botConversations.value[botId] = []
    }
    const existingIdx = botConversations.value[botId].findIndex(c => c.id === conversation.id)
    if (existingIdx === -1) {
      botConversations.value[botId].unshift(conversation)
    } else {
      botConversations.value[botId][existingIdx] = {
        ...botConversations.value[botId][existingIdx],
        ...conversation
      }
    }
  }

  /**
   * Remove a conversation from bot conversations
   */
  function removeConversation(botId, conversationId) {
    if (botConversations.value[botId]) {
      botConversations.value[botId] = botConversations.value[botId].filter(c => c.id !== conversationId)
    }
  }

  /**
   * Update conversation title in bot conversations
   */
  function updateConversationTitle(botId, conversationId, title) {
    const convs = botConversations.value[botId]
    if (convs) {
      const idx = convs.findIndex(c => c.id === conversationId)
      if (idx !== -1) {
        convs[idx] = { ...convs[idx], title }
      }
    }
  }

  /**
   * Get display title for a conversation (handles streaming state)
   */
  function getDisplayTitle(conv) {
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
   * Start title streaming for a conversation
   */
  function startTitleStreaming(conversationId) {
    streamingTitle.value = {
      conversationId,
      text: '',
      isStreaming: true
    }
  }

  /**
   * Append delta to streaming title
   */
  function appendTitleDelta(delta, conversationId = null) {
    if (streamingTitle.value.isStreaming && delta) {
      if (conversationId && !streamingTitle.value.conversationId) {
        streamingTitle.value.conversationId = conversationId
      }
      streamingTitle.value.text += delta
    }
  }

  /**
   * Complete title streaming
   */
  function completeTitleStreaming() {
    setTimeout(() => {
      streamingTitle.value = {
        conversationId: null,
        text: '',
        isStreaming: false
      }
    }, 300)
  }

  /**
   * Get the appropriate tag info for a chatbot based on its type
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

  // Initialize on creation
  loadSidebarState()

  return {
    // State
    sidebarCollapsed,
    searchQuery,
    expandedBots,
    botConversations,
    mobileSidebarOpen,
    streamingTitle,

    // Sidebar actions
    toggleSidebar,
    expandSidebar,
    toggleBot,
    expandBot,

    // Conversation helpers
    getChatCount,
    getFilteredConversations,
    loadBotConversations,
    setBotConversations,
    upsertConversation,
    removeConversation,
    updateConversationTitle,
    getDisplayTitle,

    // Title streaming
    startTitleStreaming,
    appendTitleDelta,
    completeTitleStreaming,

    // Utilities
    getChatbotTypeTag
  }
}
