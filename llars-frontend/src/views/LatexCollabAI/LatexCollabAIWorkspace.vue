<template>
  <div class="workspace-ai-container">
    <!-- Main Workspace (Original) -->
    <div class="workspace-main" :style="{ width: aiSidebarOpen ? 'calc(100% - 320px)' : '100%' }">
      <!-- Embed Original Workspace with AI base path and AI features enabled -->
      <LatexCollabWorkspaceOriginal
        ref="workspaceRef"
        base-path="/LatexCollab"
        :ai-enabled="true"
        v-model:ghost-text-enabled="ghostTextEnabled"
        :ghost-text-delay="800"
        @document-change="handleDocumentChange"
        @ai-command="handleAICommand"
        @ai-action="handleAIAction"
        @request-completion="handleRequestCompletion"
      />
    </div>

    <!-- AI Sidebar -->
    <transition name="slide-right">
      <AISidebar
        v-if="aiSidebarOpen"
        key="ai-sidebar"
        :document-content="currentDocumentContent"
        :get-context="getChatContext"
        @insert-artifact="insertTextAtCursor"
      />
    </transition>

    <!-- Floating AI Toggle Button (when sidebar closed) -->
    <transition name="fade">
      <v-btn
        v-if="!aiSidebarOpen"
        class="ai-toggle-fab"
        color="primary"
        icon
        size="large"
        elevation="4"
        :title="$t('latexCollabAi.workspace.actions.openAssistant')"
        @click="aiSidebarOpen = true"
      >
        <LIcon>llars:latex-collab-ai</LIcon>
      </v-btn>
    </transition>


    <!-- Citation Finder Dialog -->
    <v-dialog v-model="citationDialog" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon class="mr-2" color="primary">mdi-book-search</LIcon>
          {{ $t('latexCollabAi.citations.title') }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="citationSearchText"
            :label="$t('latexCollabAi.citations.claimLabel')"
            variant="outlined"
            density="compact"
            autofocus
          />

          <v-select
            v-model="selectedCollections"
            :items="availableCollections"
            item-title="name"
            item-value="id"
            :label="$t('latexCollabAi.citations.collectionsLabel')"
            variant="outlined"
            density="compact"
            multiple
            chips
            class="mt-3"
          />

          <LBtn
            variant="primary"
            :loading="citationLoading"
            :disabled="!citationSearchText.trim()"
            class="mt-3"
            @click="searchCitations"
          >
            <LIcon class="mr-1">mdi-magnify</LIcon>
            {{ $t('common.search') }}
          </LBtn>

          <!-- Results -->
          <div v-if="citationResults.length" class="mt-4">
            <h4 class="text-subtitle-2 mb-2">{{ $t('latexCollabAi.citations.resultsTitle') }}</h4>
            <v-list density="compact">
              <v-list-item
                v-for="(citation, i) in citationResults"
                :key="i"
                :subtitle="citation.snippet"
              >
                <template #prepend>
                  <v-chip size="x-small" :color="citation.relevance > 0.7 ? 'success' : 'warning'">
                    {{ Math.round(citation.relevance * 100) }}%
                  </v-chip>
                </template>
                <template #title>
                  <span class="text-body-2 font-weight-medium">{{ citation.title }}</span>
                  <span class="text-caption text-medium-emphasis ml-2">
                    {{ citation.authors?.join(', ') }} ({{ citation.year }})
                  </span>
                </template>
                <template #append>
                  <v-btn
                    size="small"
                    variant="text"
                    :title="$t('latexCollabAi.citations.insertBibtex')"
                    @click="insertCitation(citation)"
                  >
                    <LIcon>mdi-plus</LIcon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="citationDialog = false">{{ $t('common.close') }}</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Keyboard Shortcuts Help -->
    <v-dialog v-model="shortcutsDialog" max-width="500">
      <v-card>
        <v-card-title>
          <LIcon class="mr-2">mdi-keyboard</LIcon>
          {{ $t('latexCollabAi.shortcuts.title') }}
        </v-card-title>
        <v-card-text>
          <v-table density="compact">
            <tbody>
              <tr v-for="shortcut in shortcuts" :key="shortcut.keys">
                <td><kbd>{{ shortcut.keys }}</kbd></td>
                <td>{{ shortcut.description }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="shortcutsDialog = false">{{ $t('common.close') }}</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :timeout="3000" :color="snackbar.color">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import LatexCollabWorkspaceOriginal from '@/views/LatexCollab/LatexCollabWorkspace.vue'
import AISidebar from '@/components/LatexCollabAI/ai/AISidebar.vue'
import aiWritingService from '@/services/aiWritingService'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'
import { logI18n } from '@/utils/logI18n'

const route = useRoute()
const workspaceId = computed(() => Number(route.params.workspaceId))
const { t } = useI18n()

// Refs
const workspaceRef = ref(null)

// AI Sidebar state
const aiSidebarOpen = ref(false)

// Ghost text (inline AI completion) state
const ghostTextEnabled = ref(true)
const pendingCompletionPosition = ref(null)

// Document content (synced via observer or event)
const currentDocumentContent = ref('')

// Citation Dialog
const citationDialog = ref(false)
const citationSearchText = ref('')
const citationLoading = ref(false)
const citationResults = ref([])
const selectedCollections = ref([])
const availableCollections = ref([])

// Shortcuts Dialog
const shortcutsDialog = ref(false)

// Snackbar
const snackbar = ref({
  show: false,
  text: '',
  color: 'info'
})

// Keyboard shortcuts
const shortcuts = computed(() => ([
  { keys: 'Ctrl+Shift+A', description: t('latexCollabAi.shortcuts.toggleSidebar') },
  { keys: 'Ctrl+Shift+G', description: t('latexCollabAi.shortcuts.toggleGhostText') },
  { keys: 'Ctrl+Space', description: t('latexCollabAi.shortcuts.requestCompletion') },
  { keys: 'Tab', description: t('latexCollabAi.shortcuts.acceptSuggestion') },
  { keys: 'Esc', description: t('latexCollabAi.shortcuts.rejectSuggestion') },
  { keys: 'Ctrl+Shift+R', description: t('latexCollabAi.shortcuts.rewriteSelection') },
  { keys: 'Ctrl+Shift+E', description: t('latexCollabAi.shortcuts.expandSelection') },
  { keys: 'Ctrl+Shift+K', description: t('latexCollabAi.shortcuts.summarizeSelection') },
  { keys: 'Ctrl+Shift+C', description: t('latexCollabAi.shortcuts.findCitation') },
  { keys: 'Ctrl+Shift+/', description: t('latexCollabAi.shortcuts.showShortcuts') }
]))

// Methods
function handleDocumentChange(content) {
  currentDocumentContent.value = content
}

async function getChatContext() {
  try {
    const context = await workspaceRef.value?.getAiChatContext?.()
    if (context?.content) {
      return context
    }
  } catch (e) {
    console.warn('[LatexCollabAI] Konnte Kontext nicht laden:', e)
  }
  return { content: currentDocumentContent.value || '', sources: [] }
}

/**
 * Handle ghost text completion request from editor
 * Called when user pauses typing and ghost text is enabled
 */
async function handleRequestCompletion(request) {
  const { context, cursorPosition, documentPosition } = request

  // Store the position for when we get the result
  pendingCompletionPosition.value = documentPosition

  try {
    const result = await aiWritingService.complete({
      context,
      cursor_position: cursorPosition,
      document_type: 'latex',
      max_tokens: 100,
      temperature: 0.3
    })

    if (result.completion && pendingCompletionPosition.value === documentPosition) {
      // Position still matches, set the ghost text
      const editorRef = workspaceRef.value?.$refs?.editorRef
      if (editorRef?.setGhostText) {
        editorRef.setGhostText(result.completion, documentPosition)
      }
    }
  } catch (e) {
    logI18n('warn', 'logs.latexCollabAi.completionFailed', e)
  } finally {
    pendingCompletionPosition.value = null
  }
}

function showNotification(text, color = 'info') {
  snackbar.value = { show: true, text, color }
}

function insertTextAtCursor(text) {
  // Try to access editor and insert text
  // This is a placeholder - actual implementation depends on editor API
  showNotification(t('latexCollabAi.notifications.inserting'))
  // Copy to clipboard as fallback
  navigator.clipboard.writeText(text).then(() => {
    showNotification(t('latexCollabAi.notifications.clipboardCopied'), 'success')
  })
}

function handleFindCitation(text) {
  citationSearchText.value = text
  citationDialog.value = true
  citationResults.value = []
}

/**
 * Handle AI action from selection toolbar dropdown
 * @param {Object} event - AI action event with action, selectedText, range
 */
async function handleAIAction(event) {
  const { action, selectedText, range } = event
  if (!selectedText?.trim()) return

  aiProcessing.value = true

  try {
    let result

    switch (action) {
      case 'rewrite':
        result = await aiWritingService.rewrite({
          text: selectedText,
          style: 'academic',
          context: currentDocumentContent.value.substring(0, 500)
        })
        if (result.result) {
          replaceTextInEditor(result.result, range)
          showNotification(t('latexCollabAi.notifications.rewritten'), 'success')
        }
        break

      case 'expand':
        result = await aiWritingService.expand({
          text: selectedText,
          context: currentDocumentContent.value.substring(0, 500)
        })
        if (result.result) {
          replaceTextInEditor(result.result, range)
          showNotification(t('latexCollabAi.notifications.expanded'), 'success')
        }
        break

      case 'summarize':
        result = await aiWritingService.summarize({
          text: selectedText
        })
        if (result.result) {
          replaceTextInEditor(result.result, range)
          showNotification(t('latexCollabAi.notifications.summarized'), 'success')
        }
        break

      case 'fix':
        result = await aiWritingService.fixLatex(selectedText)
        if (result.corrected) {
          replaceTextInEditor(result.corrected, range)
          showNotification(t('latexCollabAi.notifications.latexFixed'), 'success')
        } else if (result.errors?.length) {
          showNotification(t('latexCollabAi.notifications.latexErrorsFound', { count: result.errors.length }), 'warning')
        } else {
          showNotification(t('latexCollabAi.notifications.latexErrorsNone'), 'success')
        }
        break

      default:
        logI18n('warn', 'logs.latexCollabAi.unknownAction', action)
    }
  } catch (e) {
    showNotification(t('latexCollabAi.notifications.error', { message: e.message }), 'error')
  } finally {
    aiProcessing.value = false
  }
}

/**
 * Replace text in editor at given range
 * @param {string} newText - Text to insert
 * @param {Object} range - Range with from/to positions
 */
function replaceTextInEditor(newText, range) {
  const editorRef = workspaceRef.value?.$refs?.editorRef
  if (editorRef?.replaceRange) {
    editorRef.replaceRange(newText, range.from, range.to)
  } else {
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(newText).then(() => {
      showNotification(t('latexCollabAi.notifications.clipboardCopied'), 'success')
    })
  }
}

// AI Command Handler (from @-commands in editor)
const aiProcessing = ref(false)
async function handleAICommand(cmdEvent) {
  const { command, args, selectedText } = cmdEvent
  aiProcessing.value = true

  try {
    let result

    switch (command) {
      case 'ai':
        // Free-form AI request via chat
        const chatContext = await getChatContext()
        result = await aiWritingService.chat({
          message: args || selectedText,
          document_content: chatContext.content
        })
        if (result.response) {
          insertTextAtCursor(result.response)
          showNotification(t('latexCollabAi.notifications.aiInserted'), 'success')
        }
        break

      case 'rewrite':
        result = await aiWritingService.rewrite({
          text: selectedText || args,
          style: 'academic',
          context: currentDocumentContent.value.substring(0, 500)
        })
        if (result.result) {
          insertTextAtCursor(result.result)
          showNotification(t('latexCollabAi.notifications.rewritten'), 'success')
        }
        break

      case 'expand':
        result = await aiWritingService.expand({
          text: selectedText || args,
          context: currentDocumentContent.value.substring(0, 500)
        })
        if (result.result) {
          insertTextAtCursor(result.result)
          showNotification(t('latexCollabAi.notifications.expanded'), 'success')
        }
        break

      case 'summarize':
        result = await aiWritingService.summarize({
          text: selectedText || args
        })
        if (result.result) {
          insertTextAtCursor(result.result)
          showNotification(t('latexCollabAi.notifications.summarized'), 'success')
        }
        break

      case 'fix':
        result = await aiWritingService.fixLatex(selectedText || currentDocumentContent.value)
        if (result.errors?.length) {
          showNotification(t('latexCollabAi.notifications.errorsFound', { count: result.errors.length }), 'warning')
        } else {
          showNotification(t('latexCollabAi.notifications.errorsNone'), 'success')
        }
        break

      case 'translate':
        // Use chat for translation with language arg
        const lang = args || 'en'
        result = await aiWritingService.chat({
          message: t('latexCollabAi.prompts.translate', { lang, text: selectedText }),
          document_content: ''
        })
        if (result.response) {
          insertTextAtCursor(result.response)
          showNotification(t('latexCollabAi.notifications.translated', { lang }), 'success')
        }
        break

      case 'cite':
        // Open citation dialog
        handleFindCitation(selectedText || args)
        break

      case 'abstract':
        result = await aiWritingService.generateAbstract(currentDocumentContent.value)
        if (result.abstract) {
          insertTextAtCursor(result.abstract)
          showNotification(t('latexCollabAi.notifications.abstractGenerated'), 'success')
        }
        break

      case 'titles':
        result = await aiWritingService.suggestTitles(currentDocumentContent.value)
        if (result.titles?.length) {
          const titlesText = result.titles.map((t, i) => `${i + 1}. ${t}`).join('\n')
          insertTextAtCursor(titlesText)
          showNotification(t('latexCollabAi.notifications.titlesGenerated', { count: result.titles.length }), 'success')
        }
        break

      default:
        // Unknown command - try via executeCommand
        result = await aiWritingService.executeCommand({
          command,
          args,
          selected_text: selectedText,
          document_content: currentDocumentContent.value
        })
        if (result.response) {
          insertTextAtCursor(result.response)
          showNotification(t('latexCollabAi.notifications.commandExecuted'), 'success')
        }
    }
  } catch (e) {
    showNotification(t('latexCollabAi.notifications.error', { message: e.message }), 'error')
  } finally {
    aiProcessing.value = false
  }
}

async function searchCitations() {
  if (!citationSearchText.value.trim()) return

  citationLoading.value = true
  try {
    const result = await aiWritingService.findCitations({
      claim: citationSearchText.value,
      context: currentDocumentContent.value.substring(0, 500),
      collection_ids: selectedCollections.value,
      limit: 10,
      format: 'bibtex'
    })
    citationResults.value = result.citations || []

    if (!citationResults.value.length) {
      showNotification(t('latexCollabAi.citations.noResults'), 'warning')
    }
  } catch (e) {
    showNotification(t('latexCollabAi.citations.searchError', { message: e.message }), 'error')
  } finally {
    citationLoading.value = false
  }
}

function insertCitation(citation) {
  if (citation.bibtex) {
    insertTextAtCursor(citation.bibtex)
    showNotification(t('latexCollabAi.citations.bibtexInserted'), 'success')
  }
  citationDialog.value = false
}

// Keyboard event handler
function handleKeydown(e) {
  // Ctrl+Shift+A: Toggle AI Sidebar
  if (e.ctrlKey && e.shiftKey && e.key === 'A') {
    e.preventDefault()
    aiSidebarOpen.value = !aiSidebarOpen.value
  }

  // Ctrl+Shift+G: Toggle Ghost Text
  if (e.ctrlKey && e.shiftKey && e.key === 'G') {
    e.preventDefault()
    ghostTextEnabled.value = !ghostTextEnabled.value
    showNotification(
      ghostTextEnabled.value ? t('latexCollabAi.notifications.ghostTextEnabled') : t('latexCollabAi.notifications.ghostTextDisabled'),
      ghostTextEnabled.value ? 'success' : 'info'
    )
  }

  // Ctrl+Shift+/: Show shortcuts
  if (e.ctrlKey && e.shiftKey && e.key === '/') {
    e.preventDefault()
    shortcutsDialog.value = true
  }

  // Ctrl+Shift+C: Open citation finder
  if (e.ctrlKey && e.shiftKey && e.key === 'C') {
    e.preventDefault()
    const selection = window.getSelection()?.toString()
    if (selection) {
      handleFindCitation(selection)
    } else {
      citationDialog.value = true
    }
  }
}

// Load available RAG collections
async function loadCollections() {
  try {
    const token = getAuthStorageItem(AUTH_STORAGE_KEYS.token)
    const response = await fetch('/api/rag/collections', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const data = await response.json()
    if (data.success) {
      availableCollections.value = data.collections || []
    }
  } catch (e) {
    logI18n('error', 'logs.latexCollabAi.collectionsLoadFailed', e)
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  loadCollections()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.workspace-ai-container {
  display: flex;
  height: calc(100vh - 94px);
  overflow: hidden;
  position: relative;
}

.workspace-main {
  flex: 1;
  min-width: 0;
  transition: width 0.3s ease;
  overflow: hidden;
}

/* Floating AI Toggle Button */
.ai-toggle-fab {
  position: fixed;
  bottom: 80px;
  right: 24px;
  z-index: 100;
}

/* Transitions */
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-right-enter-from,
.slide-right-leave-to {
  transform: translateX(100%);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Keyboard shortcuts */
kbd {
  background: rgba(var(--v-theme-on-surface), 0.08);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 4px;
  padding: 2px 6px;
  font-family: monospace;
  font-size: 12px;
}
</style>
