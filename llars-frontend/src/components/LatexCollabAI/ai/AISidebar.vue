<template>
  <div class="ai-sidebar-wrapper">
    <div class="ai-sidebar" :class="{ collapsed: !expanded }">
    <!-- Header -->
    <div class="ai-sidebar-header" @click="expanded = !expanded">
      <div class="ai-header-content">
        <LIcon class="mr-2" :color="expanded ? 'white' : 'primary'">mdi-robot-happy</LIcon>
        <span v-if="expanded" class="ai-header-title">{{ $t('latexCollabAi.sidebar.title') }}</span>
      </div>
      <v-btn
        v-if="expanded"
        icon
        variant="text"
        size="small"
        color="white"
        @click.stop="expanded = false"
      >
        <LIcon>mdi-chevron-right</LIcon>
      </v-btn>
    </div>

    <!-- Content (when expanded) -->
    <template v-if="expanded">
      <div class="ai-sidebar-content">
        <!-- Quick Tools Section -->
        <div class="ai-section">
          <div class="ai-section-title">
            <LIcon size="16" class="mr-1">mdi-lightning-bolt</LIcon>
            {{ $t('latexCollabAi.sidebar.quickTools') }}
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
              {{ $t('latexCollabAi.sidebar.tools.abstract') }}
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-format-title"
              :loading="loadingTool === 'titles'"
              @click="runQuickTool('titles')"
            >
              {{ $t('latexCollabAi.sidebar.tools.titles') }}
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-book-check"
              :loading="loadingTool === 'citations'"
              @click="runQuickTool('citations')"
            >
              {{ $t('latexCollabAi.sidebar.tools.citations') }}
            </LBtn>
            <LBtn
              variant="outlined"
              size="small"
              block
              prepend-icon="mdi-wrench"
              :loading="loadingTool === 'fixLatex'"
              @click="runQuickTool('fixLatex')"
            >
              {{ $t('latexCollabAi.sidebar.tools.fixLatex') }}
            </LBtn>
          </div>
        </div>

        <v-divider class="my-3" />

        <!-- Chat Section -->
        <div class="ai-section ai-chat-section">
          <div class="ai-section-title">
            <LIcon size="16" class="mr-1">mdi-chat</LIcon>
            {{ $t('latexCollabAi.sidebar.chat.title') }}
            <v-spacer />
            <v-btn
              v-if="aiChat.hasMessages.value"
              icon
              variant="text"
              size="x-small"
              :title="$t('latexCollabAi.sidebar.chat.clear')"
              @click="clearChat"
            >
              <LIcon size="14">mdi-delete-outline</LIcon>
            </v-btn>
          </div>

          <div class="chat-messages" ref="chatMessagesRef">
            <!-- Welcome Message -->
            <div v-if="!aiChat.hasMessages.value" class="chat-message assistant">
              <div class="message-avatar">
                <LIcon size="20" color="white">mdi-robot</LIcon>
              </div>
              <div class="message-content">
                <p>{{ $t('latexCollabAi.sidebar.welcome.greeting') }}</p>
                <p class="text-caption text-medium-emphasis mt-2">
                  {{ $t('latexCollabAi.sidebar.welcome.intro') }}
                </p>
                <ul class="feature-list">
                  <li><LIcon size="14" color="success">mdi-check</LIcon> {{ $t('latexCollabAi.sidebar.welcome.items.phrasing') }}</li>
                  <li><LIcon size="14" color="success">mdi-check</LIcon> {{ $t('latexCollabAi.sidebar.welcome.items.latex') }}</li>
                  <li><LIcon size="14" color="success">mdi-check</LIcon> {{ $t('latexCollabAi.sidebar.welcome.items.structure') }}</li>
                  <li><LIcon size="14" color="success">mdi-check</LIcon> {{ $t('latexCollabAi.sidebar.welcome.items.literature') }}</li>
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
                <LIcon size="20" color="white">
                  {{ msg.role === 'user' ? 'mdi-account' : 'mdi-robot' }}
                </LIcon>
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
                      <LIcon size="14" class="mr-1">mdi-code-tags</LIcon>
                      {{ artifact.language }}
                      <v-spacer />
                      <v-btn
                        size="x-small"
                        variant="text"
                        :title="$t('latexCollabAi.sidebar.artifact.insert')"
                        @click="$emit('insert-artifact', artifact.content)"
                      >
                        <LIcon size="14">mdi-plus</LIcon>
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
                <LIcon size="20" color="white">mdi-robot</LIcon>
              </div>
              <div class="message-content">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  color="primary"
                />
                <span class="ml-2 text-medium-emphasis">{{ $t('latexCollabAi.sidebar.chat.thinking') }}</span>
              </div>
            </div>
          </div>

          <!-- Context Sources -->
          <div v-if="hasSentMessage" class="chat-context">
            <div class="context-label">
              <LIcon size="14" class="mr-1">mdi-file-document-multiple</LIcon>
              <span>{{ $t('latexCollabAi.sidebar.chat.contextLabel') }}</span>
            </div>
            <div class="context-files">
              <template v-if="contextSources.length">
                <v-chip
                  v-for="source in contextSources"
                  :key="source.id || source.path"
                  size="x-small"
                  variant="tonal"
                  color="primary"
                  :title="contextTooltip(source)"
                >
                  {{ contextDisplayName(source) }}<span v-if="source.truncated">…</span>
                </v-chip>
              </template>
              <span v-else class="context-empty">
                {{ $t('latexCollabAi.sidebar.chat.contextEmpty') }}
              </span>
            </div>
          </div>

          <!-- Chat Input -->
          <div class="chat-input-container">
            <v-textarea
              v-model="chatInput"
              :placeholder="$t('latexCollabAi.sidebar.chat.placeholder')"
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
              <LIcon>mdi-send</LIcon>
            </LBtn>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="ai-sidebar-footer">
        <LIcon size="14" class="mr-1" color="primary">mdi-information</LIcon>
        <span class="text-caption">
          {{ $t('latexCollabAi.sidebar.footerTip') }}
        </span>
      </div>
    </template>
  </div>

  <!-- Quick Tool Results Dialog -->
  <v-dialog v-model="toolResultDialog" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center">
        <LIcon class="mr-2" color="primary">{{ toolResultIcon }}</LIcon>
        {{ toolResultTitle }}
      </v-card-title>
      <v-card-text>
        <div v-if="toolResult" class="tool-result-content">
          <!-- Abstract -->
          <template v-if="toolResultType === 'abstract'">
            <p class="text-body-1">{{ toolResult.abstract }}</p>
            <p class="text-caption text-medium-emphasis mt-2">
              {{ $t('latexCollabAi.sidebar.toolResults.wordCount', { count: toolResult.word_count }) }}
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
                  <LIcon size="small">mdi-plus</LIcon>
                </template>
              </v-list-item>
            </v-list>
          </template>

          <!-- Citation Review -->
          <template v-else-if="toolResultType === 'citations'">
            <div class="d-flex gap-4 mb-4">
              <v-chip color="success" size="small">
                {{ $t('latexCollabAi.sidebar.toolResults.cited', { count: toolResult.statistics?.cited || 0 }) }}
              </v-chip>
              <v-chip color="warning" size="small">
                {{ $t('latexCollabAi.sidebar.toolResults.uncited', { count: toolResult.statistics?.uncited || 0 }) }}
              </v-chip>
            </div>
            <v-list v-if="toolResult.warnings?.length" density="compact">
              <v-list-item
                v-for="(warning, i) in toolResult.warnings"
                :key="i"
                :subtitle="warning.reason"
              >
                <template #prepend>
                  <LIcon :color="warning.severity === 'high' ? 'error' : 'warning'" size="small">
                    mdi-alert
                  </LIcon>
                </template>
                <template #title>
                  <span class="text-body-2">{{ warning.text.substring(0, 80) }}...</span>
                </template>
              </v-list-item>
            </v-list>
            <p v-else class="text-success">{{ $t('latexCollabAi.sidebar.toolResults.noUncited') }}</p>
          </template>

          <!-- Fix LaTeX -->
          <template v-else-if="toolResultType === 'fixLatex'">
            <div v-if="toolResult.errors?.length">
              <h4 class="text-subtitle-2 mb-2">{{ $t('latexCollabAi.sidebar.toolResults.errorsTitle') }}</h4>
              <v-list density="compact">
                <v-list-item
                  v-for="(err, i) in toolResult.errors"
                  :key="i"
                  :subtitle="err.description"
                >
                  <template #prepend>
                    <LIcon color="error" size="small">mdi-alert-circle</LIcon>
                  </template>
                  <template #title>
                    <code>{{ err.original }}</code> → <code>{{ err.corrected }}</code>
                  </template>
                </v-list-item>
              </v-list>
            </div>
            <div v-if="toolResult.suggestions?.length" class="mt-4">
              <h4 class="text-subtitle-2 mb-2">{{ $t('latexCollabAi.sidebar.toolResults.suggestionsTitle') }}</h4>
              <ul>
                <li v-for="(sug, i) in toolResult.suggestions" :key="i">{{ sug }}</li>
              </ul>
            </div>
            <p v-if="!toolResult.errors?.length && !toolResult.suggestions?.length" class="text-success">
              {{ $t('latexCollabAi.sidebar.toolResults.noErrors') }}
            </p>
          </template>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <LBtn variant="cancel" @click="toolResultDialog = false">{{ $t('common.close') }}</LBtn>
      </v-card-actions>
    </v-card>
  </v-dialog>
  </div>
</template>

<script setup>
import { computed, ref, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAIChat } from '../composables/useAIChat'
import aiWritingService from '@/services/aiWritingService'
import { marked } from 'marked'

const props = defineProps({
  documentContent: {
    type: String,
    default: ''
  },
  getContext: {
    type: Function,
    default: null
  }
})

const emit = defineEmits(['insert-artifact'])
const { t } = useI18n()

// State
const expanded = ref(true)
const chatInput = ref('')
const chatMessagesRef = ref(null)
const loadingTool = ref(null)
const contextSources = ref([])
const hasSentMessage = ref(false)

// Tool result dialog
const toolResultDialog = ref(false)
const toolResultType = ref('')
const toolResultTitle = computed(() => {
  if (!toolResultType.value) return ''
  return t(`latexCollabAi.sidebar.toolResults.title.${toolResultType.value}`)
})
const toolResultIcon = computed(() => ({
  abstract: 'mdi-text-box-outline',
  titles: 'mdi-format-title',
  citations: 'mdi-book-check',
  fixLatex: 'mdi-wrench'
}[toolResultType.value] || ''))
const toolResult = ref(null)

// AI Chat composable
const aiChat = useAIChat()

// Methods
async function sendChatMessage() {
  if (!chatInput.value.trim() || aiChat.isLoading.value) return

  const message = chatInput.value.trim()
  chatInput.value = ''

  const { content, sources } = await resolveChatContext()
  contextSources.value = sources
  hasSentMessage.value = true

  await aiChat.sendMessage(message, content, true)

  // Scroll to bottom
  await nextTick()
  scrollChatToBottom()
}

async function resolveChatContext() {
  if (typeof props.getContext !== 'function') {
    return { content: props.documentContent, sources: [] }
  }

  try {
    const context = await props.getContext()
    const content = typeof context?.content === 'string' ? context.content : props.documentContent
    const sources = Array.isArray(context?.sources) ? context.sources : []
    return { content, sources }
  } catch (e) {
    console.warn('[AISidebar] Kontext konnte nicht geladen werden:', e)
    return { content: props.documentContent, sources: [] }
  }
}

function contextDisplayName(source) {
  const rawPath = String(source?.path || '')
  if (rawPath) {
    const parts = rawPath.split('/')
    return parts[parts.length - 1] || rawPath
  }
  return source?.title || ''
}

function contextTooltip(source) {
  const rawPath = String(source?.path || source?.title || '')
  if (!rawPath) return ''
  return source?.truncated ? `${rawPath} ${t('latexCollabAi.sidebar.chat.contextTruncatedSuffix')}` : rawPath
}

function scrollChatToBottom() {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

function clearChat() {
  aiChat.clearHistory()
  contextSources.value = []
  hasSentMessage.value = false
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
        toolResult.value = await aiWritingService.generateAbstract(props.documentContent)
        break

      case 'titles':
        toolResultType.value = 'titles'
        toolResult.value = await aiWritingService.suggestTitles(props.documentContent)
        break

      case 'citations':
        toolResultType.value = 'citations'
        toolResult.value = await aiWritingService.reviewCitations(props.documentContent)
        break

      case 'fixLatex':
        toolResultType.value = 'fixLatex'
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

.chat-context {
  flex-shrink: 0;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.context-label {
  display: flex;
  align-items: center;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.4px;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.context-files {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.context-empty {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
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
