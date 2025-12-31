<template>
  <div class="ai-sidebar" :class="{ collapsed: !expanded }">
    <!-- Header -->
    <div class="ai-sidebar-header" @click="expanded = !expanded">
      <div class="ai-header-content">
        <v-icon class="mr-2" :color="expanded ? 'white' : 'primary'">mdi-robot-happy</v-icon>
        <span v-if="expanded" class="ai-header-title">KI-Assistent</span>
      </div>
      <v-btn
        v-if="expanded"
        icon
        variant="text"
        size="small"
        color="white"
        @click.stop="expanded = false"
      >
        <v-icon>mdi-chevron-right</v-icon>
      </v-btn>
    </div>

    <!-- Content (when expanded) -->
    <template v-if="expanded">
      <div class="ai-sidebar-content">
        <!-- Quick Tools Section -->
        <div class="ai-section">
          <div class="ai-section-title">
            <v-icon size="16" class="mr-1">mdi-lightning-bolt</v-icon>
            Quick Tools
          </div>
          <div class="quick-tools-grid">
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-text-box-outline"
              :loading="loadingTool === 'abstract'"
              @click="runQuickTool('abstract')"
            >
              Abstract
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-format-title"
              :loading="loadingTool === 'titles'"
              @click="runQuickTool('titles')"
            >
              Titel
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-book-check"
              :loading="loadingTool === 'citations'"
              @click="runQuickTool('citations')"
            >
              Zitate prüfen
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-wrench"
              :loading="loadingTool === 'fixLatex'"
              @click="runQuickTool('fixLatex')"
            >
              Fix LaTeX
            </LBtn>
          </div>
        </div>

        <v-divider class="my-3" />

        <!-- Chat Section -->
        <div class="ai-section ai-chat-section">
          <div class="ai-section-title">
            <v-icon size="16" class="mr-1">mdi-chat</v-icon>
            Chat
            <v-spacer />
            <v-btn
              v-if="aiChat.hasMessages.value"
              icon
              variant="text"
              size="x-small"
              title="Chat leeren"
              @click="aiChat.clearHistory()"
            >
              <v-icon size="14">mdi-delete-outline</v-icon>
            </v-btn>
          </div>

          <div class="chat-messages" ref="chatMessagesRef">
            <!-- Welcome Message -->
            <div v-if="!aiChat.hasMessages.value" class="chat-message assistant">
              <div class="message-avatar">
                <v-icon size="20" color="white">mdi-robot</v-icon>
              </div>
              <div class="message-content">
                <p>Hallo! Ich bin dein KI-Schreibassistent.</p>
                <p class="text-caption text-medium-emphasis mt-2">
                  Ich kann dir helfen mit:
                </p>
                <ul class="feature-list">
                  <li><v-icon size="14" color="success">mdi-check</v-icon> Textformulierungen</li>
                  <li><v-icon size="14" color="success">mdi-check</v-icon> LaTeX-Fragen</li>
                  <li><v-icon size="14" color="success">mdi-check</v-icon> Dokumentstruktur</li>
                  <li><v-icon size="14" color="success">mdi-check</v-icon> Literatursuche</li>
                </ul>
              </div>
            </div>

            <!-- Chat History -->
            <div
              v-for="msg in aiChat.messages.value"
              :key="msg.id"
              class="chat-message"
              :class="msg.role"
            >
              <div class="message-avatar">
                <v-icon size="20" color="white">
                  {{ msg.role === 'user' ? 'mdi-account' : 'mdi-robot' }}
                </v-icon>
              </div>
              <div class="message-content">
                <div v-html="formatMessage(msg.content)"></div>
                <!-- Artifacts -->
                <div v-if="msg.artifacts?.length" class="message-artifacts">
                  <div
                    v-for="artifact in msg.artifacts"
                    :key="artifact.id"
                    class="artifact-block"
                  >
                    <div class="artifact-header">
                      <v-icon size="14" class="mr-1">mdi-code-tags</v-icon>
                      {{ artifact.language }}
                      <v-spacer />
                      <v-btn
                        size="x-small"
                        variant="text"
                        title="In Editor einfügen"
                        @click="$emit('insert-artifact', artifact.content)"
                      >
                        <v-icon size="14">mdi-plus</v-icon>
                      </v-btn>
                    </div>
                    <pre class="artifact-code">{{ artifact.content }}</pre>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading Indicator -->
            <div v-if="aiChat.isLoading.value" class="chat-message assistant">
              <div class="message-avatar">
                <v-icon size="20" color="white">mdi-robot</v-icon>
              </div>
              <div class="message-content">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  color="primary"
                />
                <span class="ml-2 text-medium-emphasis">Denke nach...</span>
              </div>
            </div>
          </div>

          <!-- Chat Input -->
          <div class="chat-input-container">
            <v-textarea
              v-model="chatInput"
              placeholder="Frage stellen... (Ctrl+Enter zum Senden)"
              rows="2"
              auto-grow
              hide-details
              density="compact"
              variant="outlined"
              @keydown.ctrl.enter="sendChatMessage"
              @keydown.enter.exact.prevent="sendChatMessage"
            />
            <LBtn
              variant="primary"
              size="small"
              :loading="aiChat.isLoading.value"
              :disabled="!chatInput.trim()"
              class="mt-2"
              @click="sendChatMessage"
            >
              <v-icon>mdi-send</v-icon>
            </LBtn>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="ai-sidebar-footer">
        <v-icon size="14" class="mr-1" color="primary">mdi-information</v-icon>
        <span class="text-caption">
          Tip: Nutze @-Commands im Editor
        </span>
      </div>
    </template>
  </div>

  <!-- Quick Tool Results Dialog -->
  <v-dialog v-model="toolResultDialog" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">{{ toolResultIcon }}</v-icon>
        {{ toolResultTitle }}
      </v-card-title>
      <v-card-text>
        <div v-if="toolResult" class="tool-result-content">
          <!-- Abstract -->
          <template v-if="toolResultType === 'abstract'">
            <p class="text-body-1">{{ toolResult.abstract }}</p>
            <p class="text-caption text-medium-emphasis mt-2">
              {{ toolResult.word_count }} Wörter
            </p>
          </template>

          <!-- Titles -->
          <template v-else-if="toolResultType === 'titles'">
            <v-list density="compact">
              <v-list-item
                v-for="(title, i) in toolResult.titles"
                :key="i"
                :title="title"
                @click="$emit('insert-artifact', title); toolResultDialog = false"
              >
                <template #prepend>
                  <v-chip size="x-small" color="primary">{{ i + 1 }}</v-chip>
                </template>
                <template #append>
                  <v-icon size="small">mdi-plus</v-icon>
                </template>
              </v-list-item>
            </v-list>
          </template>

          <!-- Citation Review -->
          <template v-else-if="toolResultType === 'citations'">
            <div class="d-flex gap-4 mb-4">
              <v-chip color="success" size="small">
                {{ toolResult.statistics?.cited || 0 }} belegt
              </v-chip>
              <v-chip color="warning" size="small">
                {{ toolResult.statistics?.uncited || 0 }} unbelegt
              </v-chip>
            </div>
            <v-list v-if="toolResult.warnings?.length" density="compact">
              <v-list-item
                v-for="(warning, i) in toolResult.warnings"
                :key="i"
                :subtitle="warning.reason"
              >
                <template #prepend>
                  <v-icon :color="warning.severity === 'high' ? 'error' : 'warning'" size="small">
                    mdi-alert
                  </v-icon>
                </template>
                <template #title>
                  <span class="text-body-2">{{ warning.text.substring(0, 80) }}...</span>
                </template>
              </v-list-item>
            </v-list>
            <p v-else class="text-success">Keine unbelegten Aussagen gefunden!</p>
          </template>

          <!-- Fix LaTeX -->
          <template v-else-if="toolResultType === 'fixLatex'">
            <div v-if="toolResult.errors?.length">
              <h4 class="text-subtitle-2 mb-2">Gefundene Fehler:</h4>
              <v-list density="compact">
                <v-list-item
                  v-for="(err, i) in toolResult.errors"
                  :key="i"
                  :subtitle="err.description"
                >
                  <template #prepend>
                    <v-icon color="error" size="small">mdi-alert-circle</v-icon>
                  </template>
                  <template #title>
                    <code>{{ err.original }}</code> → <code>{{ err.corrected }}</code>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-if="toolResult.suggestions?.length" class="mt-4">
              <h4 class="text-subtitle-2 mb-2">Vorschläge:</h4>
              <ul>
                <li v-for="(sug, i) in toolResult.suggestions" :key="i">{{ sug }}</li>
              </ul>
            </div>
            <p v-if="!toolResult.errors?.length && !toolResult.suggestions?.length" class="text-success">
              Keine Fehler gefunden!
            </p>
          </template>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="toolResultDialog = false">Schließen</LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { useAIChat } from '../composables/useAIChat'
import aiWritingService from '@/services/aiWritingService'
import { marked } from 'marked'

const props = defineProps({
  documentContent: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['insert-artifact'])

// State
const expanded = ref(true)
const chatInput = ref('')
const chatMessagesRef = ref(null)
const loadingTool = ref(null)

// Tool result dialog
const toolResultDialog = ref(false)
const toolResultType = ref('')
const toolResultTitle = ref('')
const toolResultIcon = ref('')
const toolResult = ref(null)

// AI Chat composable
const aiChat = useAIChat()

// Methods
async function sendChatMessage() {
  if (!chatInput.value.trim() || aiChat.isLoading.value) return

  const message = chatInput.value.trim()
  chatInput.value = ''

  await aiChat.sendMessage(message, props.documentContent, false)

  // Scroll to bottom
  await nextTick()
  scrollChatToBottom()
}

function scrollChatToBottom() {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

function formatMessage(content) {
  // Simple markdown rendering
  try {
    return marked.parse(content, { breaks: true })
  } catch {
    return content
  }
}

async function runQuickTool(tool) {
  if (loadingTool.value) return

  loadingTool.value = tool

  try {
    switch (tool) {
      case 'abstract':
        toolResultType.value = 'abstract'
        toolResultTitle.value = 'Generiertes Abstract'
        toolResultIcon.value = 'mdi-text-box-outline'
        toolResult.value = await aiWritingService.generateAbstract(props.documentContent)
        break

      case 'titles':
        toolResultType.value = 'titles'
        toolResultTitle.value = 'Titel-Vorschläge'
        toolResultIcon.value = 'mdi-format-title'
        toolResult.value = await aiWritingService.suggestTitles(props.documentContent)
        break

      case 'citations':
        toolResultType.value = 'citations'
        toolResultTitle.value = 'Zitat-Analyse'
        toolResultIcon.value = 'mdi-book-check'
        toolResult.value = await aiWritingService.reviewCitations(props.documentContent)
        break

      case 'fixLatex':
        toolResultType.value = 'fixLatex'
        toolResultTitle.value = 'LaTeX-Fehlerprüfung'
        toolResultIcon.value = 'mdi-wrench'
        toolResult.value = await aiWritingService.fixLatex(props.documentContent)
        break
    }

    toolResultDialog.value = true
  } catch (e) {
    console.error('Quick tool error:', e)
  } finally {
    loadingTool.value = null
  }
}

// Watch for new messages to scroll
watch(() => aiChat.messages.value.length, () => {
  nextTick(() => scrollChatToBottom())
})
</script>

<style scoped>
.ai-sidebar {
  width: 320px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.08);
  transition: width 0.2s ease;
}

.ai-sidebar.collapsed {
  width: 48px;
}

.ai-sidebar-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: linear-gradient(135deg, #88c4c8, #b0ca97);
  color: white;
  cursor: pointer;
  user-select: none;
}

.ai-sidebar.collapsed .ai-sidebar-header {
  background: transparent;
  padding: 12px 8px;
  justify-content: center;
}

.ai-header-content {
  display: flex;
  align-items: center;
}

.ai-header-title {
  font-weight: 600;
  font-size: 14px;
}

.ai-sidebar-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px;
}

.ai-section {
  flex-shrink: 0;
}

.ai-section-title {
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
}

.quick-tools-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

/* Chat Section */
.ai-chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.chat-message {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
  padding: 0 4px;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #88c4c8, #b0ca97);
}

.chat-message.user .message-avatar {
  background: rgba(var(--v-theme-primary), 0.8);
}

.message-content {
  max-width: 80%;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  font-size: 13px;
  line-height: 1.5;
}

.chat-message.user .message-content {
  background: rgba(var(--v-theme-primary), 0.1);
}

.message-content p {
  margin: 0;
}

.message-content :deep(p) {
  margin: 0 0 0.5em 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(code) {
  background: rgba(var(--v-theme-on-surface), 0.1);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.message-content :deep(pre) {
  background: rgba(var(--v-theme-on-surface), 0.08);
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.feature-list {
  margin: 8px 0 0 0;
  padding-left: 0;
  list-style: none;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  margin: 4px 0;
}

/* Artifacts */
.message-artifacts {
  margin-top: 8px;
}

.artifact-block {
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 6px;
  overflow: hidden;
  margin-top: 8px;
}

.artifact-header {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  font-size: 11px;
  text-transform: uppercase;
}

.artifact-code {
  padding: 8px;
  margin: 0;
  font-size: 12px;
  overflow-x: auto;
}

.chat-input-container {
  flex-shrink: 0;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Footer */
.ai-sidebar-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.04);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Tool Result */
.tool-result-content {
  max-height: 400px;
  overflow-y: auto;
}
</style>
