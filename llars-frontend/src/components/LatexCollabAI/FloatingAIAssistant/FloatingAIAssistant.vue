<!--
  FloatingAIAssistant.vue

  AI Writing Assistant for LaTeX documents.
  Uses LFloatingWindow for consistent LLARS design.
-->
<template>
  <LFloatingWindow
    v-model="isOpen"
    :title="$t('floatingAi.title')"
    icon="mdi-robot-happy"
    color="ai"
    :width="380"
    :height="500"
    :min-width="320"
    :min-height="350"
    storage-key="llars-ai-assistant-state"
    :show-close="true"
    :show-minimize="false"
    @close="handleClose"
  >
    <!-- Tags showing document context -->
    <template #tags>
      <LTag v-if="documentContext.title.value" variant="info" size="small">
        <LIcon size="12" class="mr-1">mdi-file-document</LIcon>
        {{ truncateTitle(documentContext.title.value) }}
      </LTag>
      <LTag v-if="documentContext.selectionText.value" variant="accent" size="small">
        <LIcon size="12" class="mr-1">mdi-selection</LIcon>
        {{ $t('floatingAi.selection') }}
      </LTag>
    </template>

    <!-- Main Content -->
    <div class="ai-assistant-content">
      <!-- Chat Messages -->
      <AIAssistantChat
        ref="chatRef"
        :messages="aiChat.messages.value"
        :is-loading="aiChat.isLoading.value"
        :context="documentContext.context.value"
        @apply-action="handleApplyAction"
        @copy-text="handleCopyText"
      />

      <!-- Input Area -->
      <AIAssistantInput
        v-model="chatInput"
        :is-loading="aiChat.isLoading.value"
        :context="documentContext.context.value"
        @send="sendMessage"
        @quick-action="handleQuickAction"
      />
    </div>
  </LFloatingWindow>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAIChat } from '../composables/useAIChat'
import { useDocumentContext } from './composables/useDocumentContext'
import { useAIAgentActions } from './composables/useAIAgentActions'
import aiWritingService from '@/services/aiWritingService'
import AIAssistantChat from './AIAssistantChat.vue'
import AIAssistantInput from './AIAssistantInput.vue'

const props = defineProps({
  editorRef: {
    type: Object,
    default: null
  },
  documentContent: {
    type: String,
    default: ''
  },
  fileName: {
    type: String,
    default: ''
  },
  cursorLine: {
    type: Number,
    default: 0
  },
  selectionText: {
    type: String,
    default: ''
  },
  selectionRange: {
    type: Object,
    default: () => ({ from: 0, to: 0 })
  }
})

const emit = defineEmits(['update:visible'])
const { t } = useI18n()

// Window state
const isOpen = ref(false)
const isMinimized = ref(true)
const unreadCount = ref(0)

// Composables - pass getter function for editor to ensure reactivity
const documentContext = useDocumentContext(() => props.editorRef)
const agentActions = useAIAgentActions(() => props.editorRef, documentContext)
const aiChat = useAIChat()

// Local state
const chatRef = ref(null)
const chatInput = ref('')

// Update document context when props change
watch(() => props.documentContent, (content) => {
  documentContext.updateContent(content)
}, { immediate: true })

watch(() => props.cursorLine, (line) => {
  documentContext.updateCursor(line)
})

watch(() => [props.selectionText, props.selectionRange], ([text, range]) => {
  documentContext.updateSelection(text, range?.from, range?.to)
})

watch(() => props.fileName, (name) => {
  documentContext.updateFileName(name)
})

// Track unread messages when minimized
watch(() => aiChat.messages.value.length, (newLen, oldLen) => {
  if (isMinimized.value && newLen > oldLen) {
    unreadCount.value++
  }
})

// Sync isOpen with isMinimized
watch(isOpen, (open) => {
  isMinimized.value = !open
  if (open) {
    unreadCount.value = 0
  }
})

// Helper functions
function truncateTitle(title) {
  return title.length > 20 ? title.substring(0, 20) + '...' : title
}

function handleClose() {
  isMinimized.value = true
}

function minimize() {
  isOpen.value = false
  isMinimized.value = true
}

function maximize() {
  isOpen.value = true
  isMinimized.value = false
}

/**
 * Send chat message with document context
 */
async function sendMessage() {
  if (!chatInput.value.trim() || aiChat.isLoading.value) return

  const message = chatInput.value.trim()
  chatInput.value = ''

  // Build context for AI
  const context = {
    title: documentContext.title.value,
    author: documentContext.author.value,
    abstract: documentContext.abstract.value,
    currentSection: documentContext.currentSection.value,
    selection: {
      text: documentContext.selectionText.value,
      from: documentContext.selectionRange.value.from,
      to: documentContext.selectionRange.value.to,
      hasSelection: documentContext.selectionText.value.length > 0
    },
    fileName: documentContext.fileName.value,
    wordCount: documentContext.wordCount.value
  }

  // Include relevant document content (not full document to save tokens)
  const contentForContext = buildContextContent()

  await aiChat.sendMessage(message, contentForContext, true)

  // Scroll chat to bottom
  await nextTick()
  chatRef.value?.scrollToBottom()
}

/**
 * Build context content for AI (limited to relevant sections)
 */
function buildContextContent() {
  const content = documentContext.content.value
  const selection = documentContext.selectionText.value

  // If there's a selection, prioritize that
  if (selection && selection.length > 50) {
    return `[Selected Text]\n${selection}\n\n[Document Title]\n${documentContext.title.value || 'Untitled'}`
  }

  // Otherwise, send title + abstract + current section
  let contextParts = []

  if (documentContext.title.value) {
    contextParts.push(`\\title{${documentContext.title.value}}`)
  }

  if (documentContext.abstract.value) {
    contextParts.push(`\\begin{abstract}\n${documentContext.abstract.value}\n\\end{abstract}`)
  }

  // Add current section context if available
  const currentSection = documentContext.currentSection.value
  if (currentSection) {
    const sectionStart = currentSection.index
    const nextSection = documentContext.sections.value.find(s => s.index > sectionStart)
    const sectionEnd = nextSection ? nextSection.index : content.length
    const sectionContent = content.substring(sectionStart, Math.min(sectionEnd, sectionStart + 2000))
    contextParts.push(sectionContent)
  }

  return contextParts.join('\n\n') || content.substring(0, 3000)
}

/**
 * Handle quick action from input area
 */
async function handleQuickAction(actionType) {
  const selection = documentContext.selectionText.value

  let result
  try {
    switch (actionType) {
      case 'title':
        // Use full document content from props if documentContext is empty
        const titleContent = documentContext.content.value || props.documentContent
        if (!titleContent || titleContent.length < 50) {
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: t('floatingAi.errors.noContent') || 'Kein Dokumentinhalt verfügbar.',
            timestamp: new Date()
          })
          return
        }
        result = await aiWritingService.suggestTitles(titleContent)
        if (result.titles?.length) {
          addAISuggestions(
            t('floatingAi.suggestions.titleIntro'),
            result.titles,
            'replace_title'
          )
        }
        break

      case 'abstract':
        const abstractContent = documentContext.content.value || props.documentContent
        if (!abstractContent || abstractContent.length < 50) {
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: t('floatingAi.errors.noContent') || 'Kein Dokumentinhalt verfügbar.',
            timestamp: new Date()
          })
          return
        }
        result = await aiWritingService.generateAbstract(abstractContent)
        if (result.abstract) {
          addAISuggestions(
            t('floatingAi.suggestions.abstractIntro'),
            [result.abstract],
            'replace_abstract'
          )
        }
        break

      case 'rewrite':
        if (!selection) {
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: t('floatingAi.errors.noSelection'),
            timestamp: new Date()
          })
          return
        }
        result = await aiWritingService.rewrite({ text: selection, style: 'academic' })
        if (result.result) {
          addAISuggestions(
            t('floatingAi.suggestions.rewriteIntro'),
            [result.result],
            'replace_selection'
          )
        }
        break

      case 'expand':
        if (!selection) {
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: t('floatingAi.errors.noSelection'),
            timestamp: new Date()
          })
          return
        }
        result = await aiWritingService.expand({ text: selection })
        if (result.result) {
          addAISuggestions(
            t('floatingAi.suggestions.expandIntro'),
            [result.result],
            'replace_selection'
          )
        }
        break

      case 'fix':
        const fixContent = documentContext.content.value || props.documentContent
        result = await aiWritingService.fixLatex(fixContent)
        if (result.errors?.length || result.suggestions?.length) {
          const msg = formatFixResults(result)
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: msg,
            timestamp: new Date()
          })
        } else {
          aiChat.messages.value.push({
            id: Date.now(),
            role: 'assistant',
            content: t('floatingAi.suggestions.noErrors'),
            timestamp: new Date()
          })
        }
        break
    }
  } catch (e) {
    console.error('Quick action error:', e)
    aiChat.messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: t('floatingAi.errors.actionFailed'),
      timestamp: new Date()
    })
  }

  await nextTick()
  chatRef.value?.scrollToBottom()
}

/**
 * Add AI suggestions with action buttons to chat
 */
function addAISuggestions(intro, suggestions, actionType) {
  aiChat.messages.value.push({
    id: Date.now(),
    role: 'assistant',
    content: intro,
    suggestions: suggestions.map((text, index) => ({
      id: `${Date.now()}-${index}`,
      text,
      actionType
    })),
    timestamp: new Date()
  })
}

/**
 * Format fix results as readable message
 */
function formatFixResults(result) {
  let msg = ''
  if (result.errors?.length) {
    msg += `**${t('floatingAi.fix.errorsFound', { count: result.errors.length })}**\n\n`
    result.errors.forEach(err => {
      msg += `- \`${err.original}\` → \`${err.corrected}\`: ${err.description}\n`
    })
  }
  if (result.suggestions?.length) {
    msg += `\n**${t('floatingAi.fix.suggestions')}**\n\n`
    result.suggestions.forEach(sug => {
      msg += `- ${sug}\n`
    })
  }
  return msg
}

/**
 * Handle apply action from chat (insert/replace)
 */
async function handleApplyAction(action) {
  const { actionType, text } = action

  let result
  switch (actionType) {
    case 'replace_title':
      result = await agentActions.replaceTitle(text)
      break
    case 'replace_abstract':
      result = await agentActions.replaceAbstract(text)
      break
    case 'replace_selection':
      result = await agentActions.replaceSelection(text)
      break
    default:
      result = await agentActions.insertAtCursor(text)
  }

  if (result.success) {
    aiChat.messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: t('floatingAi.actions.applied'),
      timestamp: new Date()
    })
  } else {
    aiChat.messages.value.push({
      id: Date.now(),
      role: 'assistant',
      content: t('floatingAi.actions.failed', { error: result.error }),
      timestamp: new Date()
    })
  }

  await nextTick()
  chatRef.value?.scrollToBottom()
}

/**
 * Handle copy text to clipboard
 */
async function handleCopyText(text) {
  await agentActions.copyToClipboard(text)
}

// Expose for parent
defineExpose({
  minimize,
  maximize,
  isMinimized,
  unreadCount
})
</script>

<style scoped>
.ai-assistant-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
</style>
