<template>
  <div class="comparison-viewer" :class="{ 'historical-mode': isHistorical }">
    <!-- Header -->
    <div class="viewer-header">
      <div class="header-left">
        <v-btn
          v-if="isHistorical"
          icon="mdi-arrow-left"
          variant="text"
          size="small"
          @click="$emit('close')"
        ></v-btn>
        <v-icon size="20" class="mr-2">{{ isHistorical ? 'mdi-history' : 'mdi-eye' }}</v-icon>
        <span class="header-title">{{ isHistorical ? 'Vergleich #' + comparisonIndex : 'Live Vergleich' }}</span>
        <v-chip size="x-small" variant="outlined" class="ml-2">
          {{ pillarAName }} vs {{ pillarBName }}
        </v-chip>
      </div>
      <div class="header-right">
        <v-chip
          v-if="!isHistorical && isStreaming"
          color="warning"
          size="x-small"
          prepend-icon="mdi-broadcast"
          class="pulse-chip"
        >
          Live
        </v-chip>
        <v-chip
          v-else-if="comparison?.winner"
          :color="comparison.winner === 'A' ? 'blue' : (comparison.winner === 'B' ? 'green' : 'warning')"
          size="x-small"
        >
          Gewinner: {{ comparison.winner }}
        </v-chip>
        <v-btn
          icon="mdi-fullscreen"
          variant="text"
          size="small"
          @click="$emit('open-fullscreen')"
          title="Vollbild"
        ></v-btn>
      </div>
    </div>

    <!-- Main Content: Three Column Layout -->
    <div class="viewer-content">
      <!-- Thread A -->
      <div class="thread-panel thread-a">
        <div class="thread-header">
          <v-chip color="blue" variant="flat" size="small" prepend-icon="mdi-alpha-a-circle">
            {{ pillarAName }}
          </v-chip>
          <v-chip v-if="comparison?.winner === 'A'" color="warning" size="x-small" prepend-icon="mdi-trophy">
            Gewinner
          </v-chip>
        </div>
        <div class="thread-messages">
          <div v-for="(msg, idx) in threadAMessages" :key="idx" class="message-item">
            <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
              <v-icon size="12" class="mr-1">
                {{ msg.role === 'assistant' ? 'mdi-message-reply' : 'mdi-account' }}
              </v-icon>
              {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
          <div v-if="!threadAMessages?.length" class="empty-messages">
            <v-icon size="24">mdi-message-off</v-icon>
            <span>Keine Nachrichten</span>
          </div>
        </div>
      </div>

      <!-- Center: Evaluation -->
      <div class="evaluation-panel">
        <div class="eval-status">
          <v-icon
            :color="comparison?.winner ? 'success' : (isStreaming ? 'warning' : 'grey')"
            size="32"
            :class="{ 'rotating': isStreaming && !comparison?.winner }"
          >
            {{ comparison?.winner ? 'mdi-check-circle' : (isStreaming ? 'mdi-loading' : 'mdi-clock-outline') }}
          </v-icon>
          <span class="status-text">
            {{ comparison?.winner ? 'Abgeschlossen' : (isStreaming ? 'Analysiert...' : 'Wartend') }}
          </span>
        </div>

        <!-- Winner Display -->
        <div v-if="comparison?.winner" class="winner-display" :class="'winner-' + comparison.winner.toLowerCase()">
          <v-icon size="36" color="warning">mdi-trophy</v-icon>
          <div class="winner-letter">{{ comparison.winner }}</div>
          <div v-if="comparison.confidence_score" class="confidence-value">
            {{ Math.round(comparison.confidence_score * 100) }}%
          </div>
        </div>

        <!-- Scores Preview -->
        <div v-if="parsedResult?.criteria_scores" class="scores-preview">
          <div v-for="(scores, criterion) in parsedResult.criteria_scores" :key="criterion" class="score-row">
            <span class="score-label">{{ formatCriterionShort(criterion) }}</span>
            <div class="score-dots">
              <span
                v-for="n in 5"
                :key="`a-${n}`"
                class="dot dot-a"
                :class="{ filled: scores.score_a >= n }"
              ></span>
              <span class="dot-divider">|</span>
              <span
                v-for="n in 5"
                :key="`b-${n}`"
                class="dot dot-b"
                :class="{ filled: scores.score_b >= n }"
              ></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Thread B -->
      <div class="thread-panel thread-b">
        <div class="thread-header">
          <v-chip color="green" variant="flat" size="small" prepend-icon="mdi-alpha-b-circle">
            {{ pillarBName }}
          </v-chip>
          <v-chip v-if="comparison?.winner === 'B'" color="warning" size="x-small" prepend-icon="mdi-trophy">
            Gewinner
          </v-chip>
        </div>
        <div class="thread-messages">
          <div v-for="(msg, idx) in threadBMessages" :key="idx" class="message-item">
            <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
              <v-icon size="12" class="mr-1">
                {{ msg.role === 'assistant' ? 'mdi-message-reply' : 'mdi-account' }}
              </v-icon>
              {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
          <div v-if="!threadBMessages?.length" class="empty-messages">
            <v-icon size="24">mdi-message-off</v-icon>
            <span>Keine Nachrichten</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stream/Result Section -->
    <div class="stream-section">
      <div class="stream-header">
        <div class="stream-header-left">
          <v-icon size="16" :class="{ 'rotating': isStreaming }">
            {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
          </v-icon>
          <span class="stream-title">LLM Analyse</span>
          <v-chip size="x-small" :color="isStreaming ? 'warning' : (streamContent ? 'success' : 'grey')">
            {{ isStreaming ? 'Streamt...' : (streamContent ? 'Fertig' : 'Wartend') }}
          </v-chip>
        </div>
        <div class="stream-header-right">
          <v-btn-toggle v-model="viewMode" density="compact" mandatory>
            <v-btn value="formatted" size="x-small" variant="text" title="Formatiert">
              <v-icon size="14">mdi-format-list-bulleted</v-icon>
            </v-btn>
            <v-btn value="raw" size="x-small" variant="text" title="Raw JSON">
              <v-icon size="14">mdi-code-json</v-icon>
            </v-btn>
          </v-btn-toggle>
          <v-btn
            icon="mdi-content-copy"
            variant="text"
            size="x-small"
            :disabled="!streamContent"
            @click="copyToClipboard"
            title="Kopieren"
          ></v-btn>
        </div>
      </div>

      <div class="stream-content" ref="streamRef" @scroll="handleScroll">
        <!-- Formatted View -->
        <template v-if="viewMode === 'formatted' && parsedResult">
          <div class="formatted-result">
            <!-- Chain of Thought -->
            <div v-if="parsedResult.chain_of_thought" class="cot-section">
              <div class="cot-title">Chain of Thought</div>
              <div
                v-for="(step, key) in parsedResult.chain_of_thought"
                :key="key"
                class="cot-step"
              >
                <div class="cot-step-header">
                  <v-icon size="14" color="primary">mdi-thought-bubble</v-icon>
                  <span>{{ formatStepName(key) }}</span>
                </div>
                <div class="cot-step-content">{{ step }}</div>
              </div>
            </div>

            <!-- Justification -->
            <div v-if="parsedResult.final_justification" class="justification-section">
              <div class="justification-title">Begründung</div>
              <div class="justification-text">{{ parsedResult.final_justification }}</div>
            </div>
          </div>
        </template>

        <!-- Raw View -->
        <template v-else>
          <pre v-if="streamContent" class="stream-pre">{{ streamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
          <div v-else class="stream-empty">
            <v-progress-circular v-if="isStreaming" indeterminate size="24" color="primary"></v-progress-circular>
            <v-icon v-else size="24">mdi-text-box-outline</v-icon>
            <span>{{ isStreaming ? 'Warte auf Ausgabe...' : 'Keine Ausgabe' }}</span>
          </div>
        </template>

        <!-- Follow Button -->
        <v-btn
          v-if="!autoScroll && isStreaming"
          class="follow-btn"
          color="primary"
          size="x-small"
          rounded
          @click="enableAutoScroll"
        >
          <v-icon start size="14">mdi-arrow-down</v-icon>
          Folgen
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  comparison: { type: Object, default: null },
  session: { type: Object, default: null },
  mode: { type: String, default: 'live' }, // 'live' or 'historical'
  isStreaming: { type: Boolean, default: false },
  llmStreamContent: { type: String, default: '' },
  autoScrollEnabled: { type: Boolean, default: true }
});

const emit = defineEmits(['close', 'open-fullscreen', 'stream-scroll', 'enable-auto-scroll']);

// Computed aliases for backward compatibility
const isHistorical = computed(() => props.mode === 'historical');
const streamContent = computed(() => props.llmStreamContent);

// Parse JSON from stream content
const parsedResult = computed(() => {
  if (!streamContent.value) return null;
  try {
    const jsonMatch = streamContent.value.match(/\{[\s\S]*"winner"[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }
    return null;
  } catch (e) {
    return null;
  }
});

const viewMode = ref('formatted');
const autoScroll = ref(true);
const streamRef = ref(null);

// Computed
const comparisonIndex = computed(() =>
  (props.comparison?.comparison_index ?? props.comparison?.queue_position ?? 0) + 1
);

const pillarAName = computed(() => props.comparison?.pillar_a_name || `Säule ${props.comparison?.pillar_a}`);
const pillarBName = computed(() => props.comparison?.pillar_b_name || `Säule ${props.comparison?.pillar_b}`);

const threadAMessages = computed(() => props.comparison?.thread_a_messages || []);
const threadBMessages = computed(() => props.comparison?.thread_b_messages || []);

// Methods
const formatCriterionShort = (key) => {
  const names = {
    counsellor_coherence: 'Koh.B',
    client_coherence: 'Koh.K',
    quality: 'Qual.',
    empathy: 'Emp.',
    authenticity: 'Auth.',
    solution_orientation: 'Lösg.'
  };
  return names[key] || key.substring(0, 4);
};

const formatStepName = (key) => {
  const names = {
    step_1_overview: 'Überblick',
    step_2_strengths_a: 'Stärken A',
    step_3_strengths_b: 'Stärken B',
    step_4_weaknesses_a: 'Schwächen A',
    step_5_weaknesses_b: 'Schwächen B',
    step_6_comparison: 'Vergleich'
  };
  return names[key] || key;
};

const copyToClipboard = () => {
  navigator.clipboard.writeText(streamContent.value);
};

const handleScroll = (event) => {
  const el = event.target;
  const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50;
  if (!isNearBottom && autoScroll.value) {
    autoScroll.value = false;
  }
  emit('stream-scroll', event);
};

const enableAutoScroll = () => {
  autoScroll.value = true;
  if (streamRef.value) {
    streamRef.value.scrollTop = streamRef.value.scrollHeight;
  }
  emit('enable-auto-scroll');
};

// Auto-scroll on new content
watch(() => streamContent.value, () => {
  if (autoScroll.value && streamRef.value) {
    nextTick(() => {
      streamRef.value.scrollTop = streamRef.value.scrollHeight;
    });
  }
});
</script>

<style scoped>
.comparison-viewer {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.comparison-viewer.historical-mode {
  border-left: 3px solid rgb(var(--v-theme-info));
}

/* Header */
.viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.header-title {
  font-weight: 600;
  font-size: 14px;
}

/* Content: Three columns */
.viewer-content {
  display: flex;
  flex: 0 0 auto;
  max-height: 40%;
  min-height: 120px;
  overflow: hidden;
}

/* Thread Panels */
.thread-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.thread-a {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.thread-b {
  border-left: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.thread-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px;
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.thread-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.message-item {
  padding: 8px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.message-item:last-child {
  border-bottom: none;
}

.message-role {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.role-counsellor {
  color: rgb(var(--v-theme-primary));
}

.role-client {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.message-text {
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Evaluation Panel */
.evaluation-panel {
  width: 140px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  gap: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.15);
}

.eval-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.status-text {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.winner-display {
  text-align: center;
  padding: 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-success), 0.1);
}

.winner-display.winner-a {
  background: rgba(33, 150, 243, 0.15);
}

.winner-display.winner-b {
  background: rgba(76, 175, 80, 0.15);
}

.winner-display.winner-tie {
  background: rgba(255, 152, 0, 0.15);
}

.winner-letter {
  font-size: 32px;
  font-weight: 700;
  margin: 4px 0;
}

.confidence-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Scores Preview */
.scores-preview {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-label {
  width: 36px;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.score-dots {
  display: flex;
  align-items: center;
  gap: 2px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.dot.filled.dot-a {
  background: #2196F3;
}

.dot.filled.dot-b {
  background: #4CAF50;
}

.dot-divider {
  margin: 0 2px;
  font-size: 8px;
  color: rgba(var(--v-theme-on-surface), 0.2);
}

/* Stream Section */
.stream-section {
  flex: 1;
  min-height: 150px;
  display: flex;
  flex-direction: column;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.1);
  overflow: hidden;
}

.stream-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.stream-header-left, .stream-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stream-title {
  font-size: 12px;
  font-weight: 600;
}

.stream-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px 12px;
  position: relative;
}

.stream-pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', monospace;
  font-size: 11px;
  line-height: 1.4;
}

.stream-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 12px;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

/* Formatted Result */
.formatted-result {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cot-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cot-title, .justification-title {
  font-size: 11px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
}

.cot-step {
  padding: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 4px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.cot-step-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 4px;
}

.cot-step-content {
  font-size: 11px;
  line-height: 1.4;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.justification-section {
  padding: 8px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 4px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.justification-text {
  font-size: 11px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* Follow Button */
.follow-btn {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
}

/* Animations */
.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
