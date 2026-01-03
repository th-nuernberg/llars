<template>
  <div class="workspace-ai-container">
    <!-- Main Workspace (Original) -->
    <div class="workspace-main" :style="{ width: aiSidebarOpen ? 'calc(100% - 320px)' : '100%' }">
      <!-- Embed Original Workspace with AI base path and AI features enabled -->
      <LatexCollabWorkspaceOriginal
        ref="workspaceRef"
        base-path="/LatexCollabAI"
        :ai-enabled="true"
        v-model:ghost-text-enabled="ghostTextEnabled"
        :ghost-text-delay="800"
        @document-change="handleDocumentChange"
        @ai-command="handleAICommand"
        @request-completion="handleRequestCompletion"
      />
    </div>

    <!-- AI Sidebar -->
    <transition name="slide-right">
      <AISidebar
        v-if="aiSidebarOpen"
        key="ai-sidebar"
        :document-content="currentDocumentContent"
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
        title="KI-Assistent öffnen (Ctrl+Shift+A)"
        @click="aiSidebarOpen = true"
      >
        <v-icon>mdi-robot-outline</v-icon>
      </v-btn>
    </transition>

    <!-- Selection Context Menu -->
    <AISelectionMenu
      :visible="selectionMenuVisible"
      :position="selectionMenuPosition"
      :selected-text="selectedText"
      :document-content="currentDocumentContent"
      @close="selectionMenuVisible = false"
      @rewrite="handleRewrite"
      @expand="handleExpand"
      @summarize="handleSummarize"
      @find-citation="handleFindCitation"
      @ask-chat="handleAskChat"
      @fix-latex="handleFixLatex"
    />

    <!-- Citation Finder Dialog -->
    <v-dialog v-model="citationDialog" max-width="700">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-book-search</v-icon>
          Zitat finden
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="citationSearchText"
            label="Zu belegende Aussage"
            variant="outlined"
            density="compact"
            autofocus
          />

          <v-select
            v-model="selectedCollections"
            :items="availableCollections"
            item-title="name"
            item-value="id"
            label="Collections durchsuchen"
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
            <v-icon class="mr-1">mdi-magnify</v-icon>
            Suchen
          </LBtn>

          <!-- Results -->
          <div v-if="citationResults.length" class="mt-4">
            <h4 class="text-subtitle-2 mb-2">Gefundene Quellen:</h4>
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
                    title="BibTeX einfügen"
                    @click="insertCitation(citation)"
                  >
                    <v-icon>mdi-plus</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="citationDialog = false">Schließen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Keyboard Shortcuts Help -->
    <v-dialog v-model="shortcutsDialog" max-width="500">
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-keyboard</v-icon>
          KI-Tastenkürzel
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
          <LBtn variant="cancel" @click="shortcutsDialog = false">Schließen</LBtn>
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
import LatexCollabWorkspaceOriginal from '@/views/LatexCollab/LatexCollabWorkspace.vue'
import AISidebar from '@/components/LatexCollabAI/ai/AISidebar.vue'
import AISelectionMenu from '@/components/LatexCollabAI/ai/AISelectionMenu.vue'
import aiWritingService from '@/services/aiWritingService'
import { AUTH_STORAGE_KEYS, getAuthStorageItem } from '@/utils/authStorage'

const route = useRoute()
const workspaceId = computed(() => Number(route.params.workspaceId))

// Refs
const workspaceRef = ref(null)

// AI Sidebar state
const aiSidebarOpen = ref(false)

// Ghost text (inline AI completion) state
const ghostTextEnabled = ref(true)
const pendingCompletionPosition = ref(null)

// Document content (synced via observer or event)
const currentDocumentContent = ref('')

// Selection Menu state
const selectionMenuVisible = ref(false)
const selectionMenuPosition = ref(null)
const selectedText = ref('')

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
const shortcuts = [
  { keys: 'Ctrl+Shift+A', description: 'KI-Sidebar ein/ausblenden' },
  { keys: 'Ctrl+Shift+G', description: 'Ghost Text ein/ausschalten' },
  { keys: 'Ctrl+Space', description: 'Textvervollständigung anfordern' },
  { keys: 'Tab', description: 'Vorschlag akzeptieren' },
  { keys: 'Esc', description: 'Vorschlag ablehnen' },
  { keys: 'Ctrl+Shift+R', description: 'Markierung umformulieren' },
  { keys: 'Ctrl+Shift+E', description: 'Markierung erweitern' },
  { keys: 'Ctrl+Shift+K', description: 'Markierung kürzen' },
  { keys: 'Ctrl+Shift+C', description: 'Zitat suchen' },
  { keys: 'Ctrl+Shift+/', description: 'Tastenkürzel anzeigen' }
]

// Methods
function handleDocumentChange(content) {
  currentDocumentContent.value = content
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
    console.warn('[AI Workspace] Completion request failed:', e)
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
  showNotification('Text wird eingefügt...')
  // Copy to clipboard as fallback
  navigator.clipboard.writeText(text).then(() => {
    showNotification('Text in Zwischenablage kopiert (Ctrl+V zum Einfügen)', 'success')
  })
}

// Selection Menu Handlers
function handleRewrite(result) {
  insertTextAtCursor(result)
  showNotification('Text umformuliert', 'success')
}

function handleExpand(result) {
  insertTextAtCursor(result)
  showNotification('Text erweitert', 'success')
}

function handleSummarize(result) {
  insertTextAtCursor(result)
  showNotification('Text gekürzt', 'success')
}

function handleFindCitation(text) {
  citationSearchText.value = text
  citationDialog.value = true
  citationResults.value = []
}

function handleAskChat(text) {
  // Open sidebar and pre-fill chat
  aiSidebarOpen.value = true
  showNotification('Frage im Chat: ' + text.substring(0, 50) + '...')
}

function handleFixLatex(result) {
  if (result.errors?.length) {
    showNotification(`${result.errors.length} LaTeX-Fehler gefunden`, 'warning')
  } else {
    showNotification('Keine LaTeX-Fehler gefunden', 'success')
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
        result = await aiWritingService.chat({
          message: args || selectedText,
          document_content: currentDocumentContent.value
        })
        if (result.response) {
          insertTextAtCursor(result.response)
          showNotification('KI-Antwort eingefügt', 'success')
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
          showNotification('Text umformuliert', 'success')
        }
        break

      case 'expand':
        result = await aiWritingService.expand({
          text: selectedText || args,
          context: currentDocumentContent.value.substring(0, 500)
        })
        if (result.result) {
          insertTextAtCursor(result.result)
          showNotification('Text erweitert', 'success')
        }
        break

      case 'summarize':
        result = await aiWritingService.summarize({
          text: selectedText || args
        })
        if (result.result) {
          insertTextAtCursor(result.result)
          showNotification('Text zusammengefasst', 'success')
        }
        break

      case 'fix':
        result = await aiWritingService.fixLatex(selectedText || currentDocumentContent.value)
        if (result.errors?.length) {
          showNotification(`${result.errors.length} Fehler gefunden`, 'warning')
        } else {
          showNotification('Keine Fehler gefunden', 'success')
        }
        break

      case 'translate':
        // Use chat for translation with language arg
        const lang = args || 'en'
        result = await aiWritingService.chat({
          message: `Übersetze den folgenden Text ins ${lang}: ${selectedText}`,
          document_content: ''
        })
        if (result.response) {
          insertTextAtCursor(result.response)
          showNotification(`Übersetzt nach ${lang}`, 'success')
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
          showNotification('Abstract generiert', 'success')
        }
        break

      case 'titles':
        result = await aiWritingService.suggestTitles(currentDocumentContent.value)
        if (result.titles?.length) {
          const titlesText = result.titles.map((t, i) => `${i + 1}. ${t}`).join('\n')
          insertTextAtCursor(titlesText)
          showNotification(`${result.titles.length} Titelvorschläge generiert`, 'success')
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
          showNotification('Befehl ausgeführt', 'success')
        }
    }
  } catch (e) {
    showNotification(`Fehler: ${e.message}`, 'error')
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
      showNotification('Keine passenden Quellen gefunden', 'warning')
    }
  } catch (e) {
    showNotification('Fehler bei der Suche: ' + e.message, 'error')
  } finally {
    citationLoading.value = false
  }
}

function insertCitation(citation) {
  if (citation.bibtex) {
    insertTextAtCursor(citation.bibtex)
    showNotification('BibTeX-Eintrag eingefügt', 'success')
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
      ghostTextEnabled.value ? 'Ghost Text aktiviert' : 'Ghost Text deaktiviert',
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

// Selection change handler for context menu
function handleSelectionChange() {
  const selection = window.getSelection()
  const text = selection?.toString().trim()

  if (text && text.length > 10) {
    selectedText.value = text

    // Get selection position
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()

    selectionMenuPosition.value = {
      x: rect.left + rect.width / 2,
      y: rect.top
    }

    // Delay showing menu
    setTimeout(() => {
      if (window.getSelection()?.toString().trim() === text) {
        selectionMenuVisible.value = true
      }
    }, 300)
  } else {
    selectionMenuVisible.value = false
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
    console.error('Failed to load collections:', e)
  }
}

// Lifecycle
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.addEventListener('selectionchange', handleSelectionChange)
  loadCollections()
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.removeEventListener('selectionchange', handleSelectionChange)
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
