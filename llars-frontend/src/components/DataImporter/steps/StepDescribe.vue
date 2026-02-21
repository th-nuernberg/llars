<template>
  <div class="step-describe">
    <!-- Split Layout: Data Preview | Intent + Chat -->
    <div class="describe-layout">
      <!-- Left: Data Preview -->
      <div class="data-preview-panel">
        <div class="panel-header">
          <LIcon size="20" color="primary" class="mr-2">mdi-database-eye</LIcon>
          <span class="panel-title">Deine Daten</span>
          <v-spacer />
          <v-chip size="small" variant="tonal" color="primary">
            {{ totalFiles }} {{ totalFiles === 1 ? 'Datei' : 'Dateien' }}
          </v-chip>
        </div>

        <div class="data-sample-container">
          <!-- Loading State -->
          <div v-if="loadingSample" class="sample-loading">
            <v-progress-circular indeterminate size="32" color="primary" />
            <span class="text-body-2 mt-2">Lade Vorschau...</span>
          </div>

          <!-- Sample Data -->
          <template v-else-if="sampleData">
            <div class="sample-tabs">
              <button
                v-for="(sample, idx) in sampleData.slice(0, 3)"
                :key="idx"
                class="sample-tab"
                :class="{ 'sample-tab--active': activeSampleIdx === idx }"
                @click="activeSampleIdx = idx"
              >
                {{ getSampleLabel(sample, idx) }}
              </button>
            </div>

            <div class="sample-code">
              <pre><code>{{ formatSample(sampleData[activeSampleIdx]) }}</code></pre>
            </div>

            <!-- Detected Structure -->
            <div v-if="detectedStructure" class="structure-summary">
              <div class="structure-item">
                <LIcon size="16" class="mr-1">mdi-format-list-bulleted</LIcon>
                <span>{{ detectedStructure.item_count || '?' }} Einträge</span>
              </div>
              <div v-if="detectedStructure.fields?.length" class="structure-item">
                <LIcon size="16" class="mr-1">mdi-code-braces</LIcon>
                <span>{{ detectedStructure.fields.length }} Felder</span>
              </div>
              <div v-if="detectedFormat" class="structure-item">
                <LIcon size="16" class="mr-1">mdi-file-document-outline</LIcon>
                <span>{{ detectedFormat }}</span>
              </div>
            </div>
          </template>

          <!-- No Data -->
          <div v-else class="no-sample">
            <LIcon size="48" color="grey-lighten-1">mdi-file-question</LIcon>
            <span class="text-body-2 text-medium-emphasis mt-2">
              Keine Vorschau verfügbar
            </span>
          </div>
        </div>
      </div>

      <!-- Right: Intent Input + Chat -->
      <div class="intent-panel">
        <div class="panel-header">
          <LIcon size="20" color="accent" class="mr-2">mdi-chat-question</LIcon>
          <span class="panel-title">{{ chat.hasAnalysis.value ? 'Chat mit KI' : 'Was möchtest du machen?' }}</span>
        </div>

        <!-- Initial Intent Input (before first analysis) -->
        <template v-if="!chat.hasAnalysis.value">
          <div class="intent-input-container">
            <textarea
              v-model="userIntent"
              class="intent-textarea"
              :placeholder="intentPlaceholder"
              rows="6"
              @input="onIntentChange"
              @keydown.ctrl.enter="runStreamingAnalysis"
            />

            <!-- Example Prompts -->
            <div class="example-prompts">
              <span class="example-label">Beispiele:</span>
              <button
                v-for="example in examplePrompts"
                :key="example.short"
                class="example-chip"
                @click="useExample(example)"
              >
                {{ example.short }}
              </button>
            </div>
          </div>

          <!-- AI Analysis Button -->
          <div class="analyze-section">
            <LBtn
              variant="primary"
              size="large"
              :loading="chat.streaming.value"
              :disabled="!canAnalyze"
              prepend-icon="wand"
              block
              @click="runStreamingAnalysis"
            >
              {{ chat.streaming.value ? 'Analysiere...' : 'KI analysieren lassen' }}
            </LBtn>
          </div>
        </template>

        <!-- Chat Interface (after first analysis) -->
        <template v-else>
          <div class="chat-container">
            <!-- Chat Messages -->
            <div ref="chatMessagesRef" class="chat-messages">
              <ChatMessage
                v-for="(msg, idx) in chat.messages.value"
                :key="idx"
                :message="msg"
              />
              <!-- Streaming message -->
              <ChatMessage
                v-if="chat.streaming.value && chat.streamingContent.value"
                :message="{ role: 'assistant', content: chat.streamingContent.value }"
                streaming
              />
            </div>

            <!-- Chat Input -->
            <div class="chat-input-container">
              <textarea
                v-model="followUpMessage"
                class="chat-input"
                placeholder="Verfeinere die Konfiguration... (Strg+Enter zum Senden)"
                rows="2"
                :disabled="chat.streaming.value"
                @keydown.ctrl.enter="sendFollowUp"
              />
              <LBtn
                variant="primary"
                size="small"
                :loading="chat.streaming.value"
                :disabled="!followUpMessage.trim() || chat.streaming.value"
                prepend-icon="send"
                @click="sendFollowUp"
              >
                Senden
              </LBtn>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Streaming Config Cards -->
    <v-expand-transition>
      <div v-if="chat.hasAnalysis.value || chat.streaming.value" class="config-cards-section">
        <div class="config-cards-header">
          <LIcon size="20" color="primary" class="mr-2">mdi-cog</LIcon>
          <span class="config-cards-title">Konfiguration</span>
          <v-chip v-if="chat.streaming.value" size="x-small" color="primary" variant="tonal" class="ml-2">
            Live
          </v-chip>
        </div>

        <div class="config-cards-grid">
          <!-- Task Type -->
          <ConfigCard
            title="Evaluationstyp"
            icon="mdi-target"
            :loading="chat.streamingFields.task_type.loading"
            :value="getTaskTypeLabel(chat.streamingFields.task_type.value)"
          >
            <div v-if="chat.streamingFields.task_type.value" class="task-type-badge">
              <LIcon size="18" class="mr-1">{{ getTaskTypeIcon(chat.streamingFields.task_type.value) }}</LIcon>
              {{ getTaskTypeLabel(chat.streamingFields.task_type.value) }}
            </div>
          </ConfigCard>

          <!-- Field Mapping -->
          <ConfigCard
            title="Feld-Mapping"
            icon="mdi-link-variant"
            :loading="chat.streamingFields.field_mapping.loading"
            :value="chat.streamingFields.field_mapping.value"
          >
            <template v-if="Object.keys(chat.streamingFields.field_mapping.value || {}).length">
              <div
                v-for="(target, source) in chat.streamingFields.field_mapping.value"
                :key="source"
                class="mapping-row-small"
              >
                <span class="mapping-source">{{ source }}</span>
                <LIcon size="12" class="mx-1" color="primary">mdi-arrow-right</LIcon>
                <span class="mapping-target">{{ target }}</span>
              </div>
            </template>
          </ConfigCard>

          <!-- Labels (for authenticity/labeling) -->
          <ConfigCard
            v-if="chat.showLabels.value"
            title="Labels"
            icon="mdi-tag-multiple"
            :loading="chat.streamingFields.labels.loading"
            :value="chat.streamingFields.labels.value"
          >
            <div v-if="chat.streamingFields.labels.value?.length" class="labels-list">
              <LTag
                v-for="(label, idx) in chat.streamingFields.labels.value"
                :key="idx"
                :color="label.color || '#b0ca97'"
                size="small"
              >
                {{ label.name || label }}
              </LTag>
            </div>
          </ConfigCard>

          <!-- Buckets (for ranking) -->
          <ConfigCard
            v-if="chat.showBuckets.value"
            title="Buckets"
            icon="mdi-format-list-bulleted"
            :loading="chat.streamingFields.buckets.loading"
            :value="chat.streamingFields.buckets.value"
          >
            <div v-if="chat.streamingFields.buckets.value?.length" class="buckets-list">
              <BucketChip
                v-for="(bucket, idx) in chat.streamingFields.buckets.value"
                :key="idx"
                :bucket="bucket"
                :index="idx"
              />
            </div>
          </ConfigCard>

          <!-- Scales (for rating) -->
          <ConfigCard
            v-if="chat.showScales.value"
            title="Bewertungsskalen"
            icon="mdi-star"
            :loading="chat.streamingFields.scales.loading"
            :value="chat.streamingFields.scales.value"
            class="config-card--wide"
          >
            <div v-if="chat.streamingFields.scales.value?.length" class="scales-list">
              <ScalePreview
                v-for="(scale, idx) in chat.streamingFields.scales.value"
                :key="idx"
                :scale="scale"
              />
            </div>
          </ConfigCard>
        </div>

        <!-- Alternative Task Types -->
        <div v-if="alternativeTaskTypes.length && !chat.streaming.value" class="alternatives-section">
          <span class="alternatives-label">Anderen Typ wählen:</span>
          <div class="alternatives-list">
            <button
              v-for="alt in alternativeTaskTypes"
              :key="alt.value"
              class="alternative-btn"
              :class="{ 'alternative-btn--selected': chat.streamingFields.task_type.value === alt.value }"
              @click="selectTaskType(alt.value)"
            >
              <LIcon size="18" class="mr-1">{{ alt.icon }}</LIcon>
              {{ alt.label }}
            </button>
          </div>
        </div>
      </div>
    </v-expand-transition>

    <!-- Legacy Analysis Results (fallback) -->
    <v-expand-transition>
      <div v-if="analysisResult && !chat.hasAnalysis.value" class="analysis-results">
        <div class="results-header">
          <LIcon size="24" color="success" class="mr-2">mdi-check-circle</LIcon>
          <span class="results-title">Verstanden!</span>
        </div>

        <div class="results-grid">
          <!-- Detected Task Type -->
          <div class="result-card">
            <div class="result-card-header">
              <LIcon size="18" class="mr-2">mdi-target</LIcon>
              Erkanntes Ziel
            </div>
            <div class="result-card-content">
              <div class="task-type-badge">
                <LIcon size="20" class="mr-2">{{ getTaskTypeIcon(analysisResult.task_type) }}</LIcon>
                {{ getTaskTypeLabel(analysisResult.task_type) }}
              </div>
              <p v-if="analysisResult.task_description" class="task-description">
                {{ analysisResult.task_description }}
              </p>
            </div>
          </div>

          <!-- Field Mapping Preview -->
          <div class="result-card">
            <div class="result-card-header">
              <LIcon size="18" class="mr-2">mdi-link-variant</LIcon>
              Feld-Mapping
            </div>
            <div class="result-card-content">
              <div
                v-for="(target, source) in analysisResult.field_mapping"
                :key="source"
                class="mapping-row"
              >
                <span class="mapping-source">{{ source }}</span>
                <LIcon size="14" class="mx-2" color="primary">mdi-arrow-right</LIcon>
                <span class="mapping-target">{{ target }}</span>
              </div>
              <div v-if="!Object.keys(analysisResult.field_mapping || {}).length" class="text-caption text-medium-emphasis">
                Automatisches Mapping wird verwendet
              </div>
            </div>
          </div>

          <!-- Evaluation Criteria (if applicable) -->
          <div v-if="analysisResult.evaluation_criteria?.length" class="result-card result-card--wide">
            <div class="result-card-header">
              <LIcon size="18" class="mr-2">mdi-star-outline</LIcon>
              Bewertungskriterien
            </div>
            <div class="result-card-content">
              <div class="criteria-list">
                <div
                  v-for="criterion in analysisResult.evaluation_criteria"
                  :key="criterion"
                  class="criterion-chip"
                >
                  {{ criterion }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Alternative Task Types -->
        <div v-if="alternativeTaskTypes.length" class="alternatives-section">
          <span class="alternatives-label">Oder meintest du:</span>
          <div class="alternatives-list">
            <button
              v-for="alt in alternativeTaskTypes"
              :key="alt.value"
              class="alternative-btn"
              :class="{ 'alternative-btn--selected': selectedTaskType === alt.value }"
              @click="selectTaskType(alt.value)"
            >
              <LIcon size="18" class="mr-1">{{ alt.icon }}</LIcon>
              {{ alt.label }}
            </button>
          </div>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import importService from '@/services/importService'
import { useWizardChat } from '../composables/useWizardChat'
import { ConfigCard, BucketChip, ScalePreview, ChatMessage } from '../components'

const props = defineProps({
  sessions: { type: Array, default: () => [] },
  session: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['analyzed', 'update:taskType', 'update:mapping', 'update:config'])

// Session ID computed for chat
const sessionId = computed(() => {
  return props.sessions?.[0]?.session_id || props.session?.session_id
})

// Initialize wizard chat
const chat = useWizardChat(sessionId)

// State
const userIntent = ref('')
const analyzing = ref(false)
const analysisResult = ref(null)
const sampleData = ref(null)
const loadingSample = ref(false)
const activeSampleIdx = ref(0)
const selectedTaskType = ref(null)
const followUpMessage = ref('')
const chatMessagesRef = ref(null)

// Computed
const totalFiles = computed(() => props.sessions?.length || (props.session ? 1 : 0))

const detectedStructure = computed(() => {
  if (props.sessions?.length) {
    // Aggregate from multiple sessions
    const totalItems = props.sessions.reduce((sum, s) => sum + (s.structure?.item_count || 0), 0)
    const firstSession = props.sessions[0]
    return {
      item_count: totalItems,
      fields: firstSession?.structure?.fields || [],
      format: firstSession?.detected_format
    }
  }
  return props.session?.structure
})

const detectedFormat = computed(() => {
  if (props.sessions?.length) {
    return props.sessions[0]?.detected_format
  }
  return props.session?.detected_format
})

const canAnalyze = computed(() => {
  return userIntent.value.trim().length > 10 && (props.sessions?.length || props.session)
})

const alternativeTaskTypes = computed(() => {
  // Use chat config or legacy analysis result
  const current = chat.streamingFields.task_type.value || analysisResult.value?.task_type
  if (!current) return []
  return taskTypes.filter(t => t.value !== current)
})

// Constants
const taskTypes = [
  { value: 'rating', label: 'Rating', icon: 'mdi-star' },
  { value: 'ranking', label: 'Ranking', icon: 'mdi-sort' },
  { value: 'comparison', label: 'Vergleich', icon: 'mdi-compare' },
  { value: 'authenticity', label: 'Echt/Fake', icon: 'mdi-shield-check' },
  { value: 'labeling', label: 'Klassifikation', icon: 'mdi-tag-multiple' },
  { value: 'mail_rating', label: 'Mail Rating', icon: 'mdi-email-star' }
]

const examplePrompts = [
  {
    short: 'Qualität bewerten',
    full: 'Ich möchte die Qualität der Berater-Antworten bewerten lassen, auf einer Skala von 1-5 für Freundlichkeit, Fachlichkeit und Hilfsbereitschaft.'
  },
  {
    short: 'LLM Vergleich',
    full: 'Das sind Antworten von verschiedenen LLMs auf dieselben Fragen. Ich möchte herausfinden welches Modell bessere Antworten gibt.'
  },
  {
    short: 'Echt oder Fake',
    full: 'Diese Konversationen sind teils echt, teils synthetisch generiert. Rater sollen erkennen welche echt und welche fake sind.'
  },
  {
    short: 'Kategorisieren',
    full: 'Die Nachrichten sollen nach Thema kategorisiert werden: Support-Anfrage, Beschwerde, Feedback, Kündigung.'
  }
]

const intentPlaceholder = `Beschreibe in eigenen Worten:
• Was für Daten sind das?
• Was soll damit passieren?
• Nach welchen Kriterien soll bewertet werden?

Beispiel: "Das sind Chatverläufe zwischen Kunden und Beratern. Ich möchte dass Kollegen die Antwortqualität auf einer Skala von 1-5 bewerten."`

// Methods
function getSampleLabel(sample, idx) {
  if (sample?.filename) {
    return sample.filename.length > 20 ? sample.filename.slice(0, 17) + '...' : sample.filename
  }
  return `Datei ${idx + 1}`
}

function formatSample(sample) {
  if (!sample) return ''
  // Show the raw data or first item
  const data = sample.raw_data || sample.data || sample
  try {
    return JSON.stringify(data, null, 2).slice(0, 1500) + (JSON.stringify(data).length > 1500 ? '\n...' : '')
  } catch {
    return String(data).slice(0, 1500)
  }
}

function useExample(example) {
  userIntent.value = example.full
}

function onIntentChange() {
  // Could add debounced analysis hints here
}

function getTaskTypeIcon(type) {
  const found = taskTypes.find(t => t.value === type)
  return found?.icon || 'mdi-help-circle'
}

function getTaskTypeLabel(type) {
  const found = taskTypes.find(t => t.value === type)
  return found?.label || type
}

function selectTaskType(type) {
  selectedTaskType.value = type

  // Update chat config
  if (chat.config.value) {
    chat.config.value.task_type = type
    chat.streamingFields.task_type.value = type
  }

  // Update legacy analysis result
  if (analysisResult.value) {
    analysisResult.value.task_type = type
  }

  emit('update:taskType', type)
  emitConfigUpdate()
}

async function loadSampleData() {
  loadingSample.value = true
  try {
    if (props.sessions?.length) {
      // Load sample from first few sessions
      sampleData.value = props.sessions.slice(0, 5).map(s => ({
        filename: s.filename || s.displayName,
        raw_data: s.raw_data || s.structure?.sample_data,
        detected_format: s.detected_format
      }))
    } else if (props.session?.session_id) {
      const result = await importService.getSample(props.session.session_id, 3)
      sampleData.value = result.sample || []
    }
  } catch (err) {
    console.error('Failed to load sample:', err)
  } finally {
    loadingSample.value = false
  }
}

async function runAnalysis() {
  if (!canAnalyze.value) return

  analyzing.value = true
  try {
    // Use first session for analysis
    const sessionIdValue = props.sessions?.[0]?.session_id || props.session?.session_id
    if (!sessionIdValue) {
      throw new Error('Keine Session verfügbar')
    }

    const result = await importService.aiAnalyzeIntent({
      session_id: sessionIdValue,
      user_intent: userIntent.value,
      file_count: totalFiles.value
    })

    analysisResult.value = result
    selectedTaskType.value = result.task_type

    emit('analyzed', {
      ...result,
      user_intent: userIntent.value
    })
  } catch (err) {
    console.error('Analysis failed:', err)
  } finally {
    analyzing.value = false
  }
}

/**
 * Run streaming analysis using the chat interface.
 */
async function runStreamingAnalysis() {
  if (!canAnalyze.value) return

  // Send initial message via chat
  await chat.sendMessage(userIntent.value)

  // Scroll to bottom after response
  await nextTick()
  scrollChatToBottom()

  // Emit config update
  emitConfigUpdate()
}

/**
 * Send a follow-up message to refine configuration.
 */
async function sendFollowUp() {
  if (!followUpMessage.value.trim() || chat.streaming.value) return

  const message = followUpMessage.value
  followUpMessage.value = ''

  await chat.sendMessage(message)

  // Scroll to bottom after response
  await nextTick()
  scrollChatToBottom()

  // Emit config update
  emitConfigUpdate()
}

/**
 * Scroll chat messages to bottom.
 */
function scrollChatToBottom() {
  if (chatMessagesRef.value) {
    chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight
  }
}

/**
 * Emit config update to parent.
 */
function emitConfigUpdate() {
  const config = chat.config.value
  if (config.task_type) {
    emit('update:taskType', config.task_type)
  }
  emit('update:config', config)
  emit('analyzed', {
    ...config,
    user_intent: userIntent.value,
    success: true
  })
}

// Lifecycle
onMounted(() => {
  loadSampleData()
})

watch(() => [props.sessions, props.session], () => {
  loadSampleData()
}, { deep: true })
</script>

<style scoped>
.step-describe {
  padding: 24px;
}

/* Split Layout */
.describe-layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  min-height: 400px;
}

@media (max-width: 900px) {
  .describe-layout {
    grid-template-columns: 1fr;
  }
}

/* Panels */
.data-preview-panel,
.intent-panel {
  display: flex;
  flex-direction: column;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  border-bottom: 1px solid rgba(var(--v-border-color), 0.1);
}

.panel-title {
  font-weight: 600;
  font-size: 0.95rem;
}

/* Data Preview */
.data-sample-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
}

.sample-loading,
.no-sample {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.sample-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  overflow-x: auto;
}

.sample-tab {
  padding: 6px 12px;
  font-size: 0.75rem;
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 6px 2px 6px 2px;
  background: transparent;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.sample-tab:hover {
  background: rgba(var(--v-theme-primary), 0.08);
}

.sample-tab--active {
  background: rgba(var(--v-theme-primary), 0.15);
  border-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-primary));
}

.sample-code {
  flex: 1;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px 2px 8px 2px;
  overflow: auto;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
}

.sample-code pre {
  margin: 0;
  padding: 12px;
}

.sample-code code {
  color: rgb(var(--v-theme-on-surface));
}

.structure-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}

.structure-item {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Intent Input */
.intent-input-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.intent-textarea {
  flex: 1;
  min-height: 150px;
  padding: 16px;
  border: 2px solid rgba(176, 202, 151, 0.3);
  border-radius: 12px 4px 12px 4px;
  background: rgba(255, 255, 255, 0.5);
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.6;
  resize: none;
  transition: border-color 0.2s;
}

.intent-textarea:focus {
  outline: none;
  border-color: #b0ca97;
}

.intent-textarea::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 0.85rem;
}

.example-prompts {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.example-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.example-chip {
  padding: 4px 10px;
  font-size: 0.75rem;
  border: 1px solid rgba(136, 196, 200, 0.4);
  border-radius: 12px;
  background: rgba(136, 196, 200, 0.1);
  color: #5a9a9e;
  cursor: pointer;
  transition: all 0.15s;
}

.example-chip:hover {
  background: rgba(136, 196, 200, 0.2);
  border-color: #88c4c8;
}

.analyze-section {
  padding: 16px;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
}

/* Analysis Results */
.analysis-results {
  margin-top: 24px;
  padding: 24px;
  background: rgba(152, 212, 187, 0.08);
  border: 1px solid rgba(152, 212, 187, 0.3);
  border-radius: 16px 4px 16px 4px;
}

.results-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.results-title {
  font-size: 1.1rem;
  font-weight: 600;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.result-card {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 12px 4px 12px 4px;
  overflow: hidden;
}

.result-card--wide {
  grid-column: 1 / -1;
}

.result-card-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  background: rgba(var(--v-theme-surface-variant), 0.4);
}

.result-card-content {
  padding: 16px;
}

.task-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  background: rgba(176, 202, 151, 0.2);
  border-radius: 8px 2px 8px 2px;
  font-weight: 600;
  color: #6a8a52;
}

.task-description {
  margin-top: 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.mapping-row {
  display: flex;
  align-items: center;
  padding: 6px 0;
  font-size: 0.85rem;
}

.mapping-source {
  font-family: 'Fira Code', monospace;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.mapping-target {
  font-weight: 500;
  color: rgb(var(--v-theme-primary));
}

.criteria-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.criterion-chip {
  padding: 6px 12px;
  background: rgba(209, 188, 138, 0.2);
  border-radius: 6px 2px 6px 2px;
  font-size: 0.85rem;
  color: #8a7a52;
}

/* Alternatives */
.alternatives-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-border-color), 0.15);
}

.alternatives-label {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.alternatives-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.alternative-btn {
  display: flex;
  align-items: center;
  padding: 8px 14px;
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 8px 2px 8px 2px;
  background: transparent;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.15s;
}

.alternative-btn:hover {
  background: rgba(var(--v-theme-primary), 0.08);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.alternative-btn--selected {
  background: rgba(var(--v-theme-primary), 0.15);
  border-color: rgb(var(--v-theme-primary));
}

/* Chat Interface */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  max-height: 300px;
}

.chat-input-container {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-border-color), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.chat-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid rgba(var(--v-border-color), 0.2);
  border-radius: 8px 2px 8px 2px;
  background: rgba(255, 255, 255, 0.6);
  font-family: inherit;
  font-size: 0.9rem;
  line-height: 1.4;
  resize: none;
  transition: border-color 0.15s;
}

.chat-input:focus {
  outline: none;
  border-color: rgb(var(--v-theme-primary));
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-input::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Config Cards Section */
.config-cards-section {
  margin-top: 24px;
  padding: 20px;
  background: rgba(176, 202, 151, 0.08);
  border: 1px solid rgba(176, 202, 151, 0.2);
  border-radius: 16px 4px 16px 4px;
}

.config-cards-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.config-cards-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
}

.config-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.config-card--wide {
  grid-column: 1 / -1;
}

/* Small mapping row for config cards */
.mapping-row-small {
  display: flex;
  align-items: center;
  padding: 3px 0;
  font-size: 0.75rem;
}

.mapping-row-small .mapping-source {
  font-family: 'Fira Code', monospace;
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.mapping-row-small .mapping-target {
  font-size: 0.75rem;
  font-weight: 500;
}

/* Labels list */
.labels-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

/* Buckets list */
.buckets-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Scales list */
.scales-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style>
