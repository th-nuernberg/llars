<template>
  <div class="comparison-view">
    <!-- Header Bar -->
    <div class="comparison-header" :class="{ 'historical-header': isHistorical }">
      <div class="d-flex align-center gap-2">
        <LIcon size="20">{{ isHistorical ? 'mdi-history' : 'mdi-eye' }}</LIcon>
        <span class="header-title">{{ isHistorical ? 'Verlauf Detail' : 'Aktueller Vergleich' }}</span>
        <v-chip size="x-small" variant="outlined">
          #{{ (currentComparison.comparison_index || currentComparison.queue_position || 0) + 1 }} / {{ session?.total_comparisons }}
        </v-chip>
        <v-chip v-if="isHistorical && currentComparison.winner" size="x-small" :color="currentComparison.winner === 'A' ? 'blue' : 'green'">
          Gewinner: {{ currentComparison.winner }}
        </v-chip>
      </div>
      <div class="d-flex align-center gap-2">
        <!-- Close button for historical view -->
        <v-btn
          v-if="isHistorical"
          variant="tonal"
          size="x-small"
          color="grey"
          @click="$emit('close')"
        >
          <LIcon start size="14">mdi-arrow-left</LIcon>
          Zurück
        </v-btn>
        <v-btn
          v-if="session?.status === 'running' && !isHistorical"
          color="error"
          variant="tonal"
          size="x-small"
          :loading="reconnecting"
          @click="$emit('reconnect')"
        >
          <LIcon start size="14" :class="{ 'pulse-icon': isStreaming }">mdi-broadcast</LIcon>
          {{ isStreaming ? 'Live' : 'Verbinden' }}
        </v-btn>
        <v-btn
          variant="text"
          size="x-small"
          @click="$emit('open-fullscreen')"
          title="Vollbild"
        >
          <LIcon size="18">mdi-fullscreen</LIcon>
        </v-btn>
      </div>
    </div>

    <!-- Main Content Area (fills remaining height) -->
    <div class="comparison-content">
      <!-- Thread A -->
      <div class="thread-panel thread-a">
        <div class="thread-header-bar">
          <v-chip color="blue" variant="flat" size="small" prepend-icon="mdi-alpha-a-circle">
            Thread A - {{ currentComparison.pillar_a_name }}
          </v-chip>
        </div>
        <div class="thread-messages">
          <div v-for="(msg, idx) in currentComparison.thread_a_messages" :key="idx" class="message-item">
            <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
              <LIcon size="12" class="mr-1">
                {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
              </LIcon>
              {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>
      </div>

      <!-- Center: Evaluation Status -->
      <div class="evaluation-panel">
        <div class="eval-status-card">
          <LIcon
            :color="currentComparison.llm_status === 'completed' ? 'success' : 'info'"
            size="28"
            :class="{ 'rotating': currentComparison.llm_status === 'running' }"
          >
            {{ currentComparison.llm_status === 'completed' ? 'mdi-check-circle' : 'mdi-loading' }}
          </LIcon>
          <div class="eval-status-text">
            {{ currentComparison.llm_status === 'completed' ? 'Bewertet' : 'Bewertet...' }}
          </div>
        </div>

        <div v-if="currentComparison.winner" class="winner-display" :class="'winner-' + currentComparison.winner.toLowerCase()">
          <LIcon size="32" color="warning">mdi-trophy</LIcon>
          <div class="winner-letter">{{ currentComparison.winner }}</div>
          <div class="winner-label">Gewinner</div>
        </div>

        <div v-if="currentComparison.confidence_score" class="confidence-display">
          <div class="confidence-label">Konfidenz</div>
          <div class="confidence-value">{{ Math.round(currentComparison.confidence_score * 100) }}%</div>
        </div>
      </div>

      <!-- Thread B -->
      <div class="thread-panel thread-b">
        <div class="thread-header-bar">
          <v-chip color="green" variant="flat" size="small" prepend-icon="mdi-alpha-b-circle">
            Thread B - {{ currentComparison.pillar_b_name }}
          </v-chip>
        </div>
        <div class="thread-messages">
          <div v-for="(msg, idx) in currentComparison.thread_b_messages" :key="idx" class="message-item">
            <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
              <LIcon size="12" class="mr-1">
                {{ msg.role === 'user' ? 'mdi-account' : 'mdi-message-reply' }}
              </LIcon>
              {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
            </div>
            <div class="message-text">{{ msg.content }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stream Output Section (fixed height) -->
    <div class="stream-section">
      <div class="stream-header">
        <div class="d-flex align-center gap-2">
          <LIcon size="16" :class="{ 'rotating': isStreaming }">
            {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
          </LIcon>
          <span class="stream-title">LLM Ausgabe</span>
          <v-chip size="x-small" :color="isStreaming ? 'warning' : (llmStreamContent ? 'success' : 'grey')">
            {{ isStreaming ? 'Streamt...' : (llmStreamContent ? 'Fertig' : 'Warte...') }}
          </v-chip>
          <v-chip size="x-small" color="info" v-if="llmStreamContent">
            {{ llmStreamContent.length }} Z.
          </v-chip>
        </div>
        <div class="d-flex align-center gap-1">
          <v-btn-toggle v-model="viewMode" density="compact" mandatory>
            <v-btn value="formatted" size="x-small" variant="text">
              <LIcon size="14">mdi-format-list-bulleted</LIcon>
            </v-btn>
            <v-btn value="raw" size="x-small" variant="text">
              <LIcon size="14">mdi-code-braces</LIcon>
            </v-btn>
          </v-btn-toggle>
          <v-btn
            size="x-small"
            variant="text"
            @click="$emit('copy-stream')"
            :disabled="!llmStreamContent"
            title="Kopieren"
          >
            <LIcon size="14">mdi-content-copy</LIcon>
          </v-btn>
        </div>
      </div>

      <div class="stream-content" ref="streamOutput" @scroll="$emit('stream-scroll', $event)">
        <!-- Formatted View -->
        <template v-if="viewMode === 'formatted' && parsedStreamJson">
          <div class="formatted-view">
            <!-- Winner & Confidence Row -->
            <div class="result-row">
              <div class="result-side result-a" :class="{ 'is-winner': parsedStreamJson.winner === 'A' }">
                <div class="result-letter">A</div>
                <div class="result-pillar">{{ currentComparison.pillar_a_name }}</div>
              </div>
              <div class="result-center">
                <v-chip :color="parsedStreamJson.winner === 'TIE' ? 'warning' : 'success'" size="small">
                  <LIcon start size="14">mdi-trophy</LIcon>
                  {{ parsedStreamJson.winner || '?' }}
                </v-chip>
                <div v-if="parsedStreamJson.confidence" class="confidence-bar">
                  <div class="confidence-fill" :style="{ width: (parsedStreamJson.confidence * 100) + '%' }"></div>
                  <span class="confidence-text">{{ Math.round(parsedStreamJson.confidence * 100) }}%</span>
                </div>
              </div>
              <div class="result-side result-b" :class="{ 'is-winner': parsedStreamJson.winner === 'B' }">
                <div class="result-letter">B</div>
                <div class="result-pillar">{{ currentComparison.pillar_b_name }}</div>
              </div>
            </div>

            <!-- Criteria Scores -->
            <div v-if="parsedStreamJson.criteria_scores" class="criteria-grid">
              <div v-for="(scores, criterion) in parsedStreamJson.criteria_scores" :key="criterion" class="criteria-row">
                <div class="criteria-label">{{ formatCriterionName(criterion) }}</div>
                <div class="criteria-scores-row">
                  <div class="score-chip score-a" :class="getScoreClass(scores.score_a)">{{ scores.score_a }}</div>
                  <div class="score-vs">vs</div>
                  <div class="score-chip score-b" :class="getScoreClass(scores.score_b)">{{ scores.score_b }}</div>
                </div>
              </div>
            </div>

            <!-- Justification -->
            <div v-if="parsedStreamJson.final_justification" class="justification-box">
              <div class="justification-label">Begründung</div>
              <div class="justification-text">{{ parsedStreamJson.final_justification }}</div>
            </div>
          </div>
        </template>

        <!-- Raw View / Streaming -->
        <template v-else>
          <pre v-if="llmStreamContent" class="stream-pre">{{ llmStreamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
          <div v-else class="stream-empty">
            <v-progress-circular v-if="isStreaming" indeterminate color="primary" size="24"></v-progress-circular>
            <LIcon v-else size="24">mdi-text-box-outline</LIcon>
            <span>{{ isStreaming ? 'Warte auf Ausgabe...' : 'Stream startet wenn Vergleich beginnt' }}</span>
          </div>
        </template>

        <!-- Follow Button -->
        <v-btn
          v-if="!autoScrollEnabled && isStreaming"
          class="follow-btn"
          color="primary"
          size="x-small"
          rounded
          @click="$emit('enable-auto-scroll')"
        >
          <LIcon start size="14">mdi-arrow-down</LIcon>
          Folgen
        </v-btn>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  currentComparison: {
    type: Object,
    required: true
  },
  session: {
    type: Object,
    default: null
  },
  reconnecting: {
    type: Boolean,
    default: false
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  llmStreamContent: {
    type: String,
    default: ''
  },
  parsedStreamJson: {
    type: Object,
    default: null
  },
  expandedPanels: {
    type: Array,
    default: () => []
  },
  autoScrollEnabled: {
    type: Boolean,
    default: true
  },
  isHistorical: {
    type: Boolean,
    default: false
  },
  formatCriterionName: {
    type: Function,
    required: true
  },
  getScoreColor: {
    type: Function,
    required: true
  }
});

defineEmits(['reconnect', 'open-fullscreen', 'copy-stream', 'stream-scroll', 'enable-auto-scroll', 'update:expanded-panels', 'close']);

const viewMode = ref('formatted');

const getScoreClass = (score) => {
  if (score >= 4) return 'score-high';
  if (score >= 3) return 'score-mid';
  return 'score-low';
};
</script>

<style scoped>
/* ============================================
   FIXED HEIGHT LAYOUT
   ============================================ */
.comparison-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Header */
.comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.comparison-header.historical-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-info), 0.1) 0%, rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-left: 3px solid rgb(var(--v-theme-info));
}

.header-title {
  font-weight: 600;
  font-size: 14px;
}

/* Main Content - Three Columns */
.comparison-content {
  display: flex;
  flex: 1;
  min-height: 0; /* Important for flex children to shrink */
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

.thread-header-bar {
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

/* Evaluation Panel */
.evaluation-panel {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  gap: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.15);
}

.eval-status-card {
  text-align: center;
}

.eval-status-text {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
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

.winner-letter {
  font-size: 28px;
  font-weight: 700;
  margin: 4px 0;
}

.winner-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.confidence-display {
  text-align: center;
}

.confidence-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.confidence-value {
  font-size: 18px;
  font-weight: 600;
}

/* Stream Section - Fixed Height */
.stream-section {
  height: 200px; /* Fixed height */
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface-variant), 0.1);
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
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
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

/* Formatted View */
.formatted-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.result-side {
  flex: 1;
  text-align: center;
  padding: 8px;
  border-radius: 6px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  transition: all 0.3s ease;
}

.result-side.is-winner {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(var(--v-theme-success), 0.3);
}

.result-a.is-winner {
  background: rgba(33, 150, 243, 0.2);
}

.result-b.is-winner {
  background: rgba(76, 175, 80, 0.2);
}

.result-letter {
  font-size: 20px;
  font-weight: 700;
}

.result-pillar {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.result-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.confidence-bar {
  width: 80px;
  height: 6px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  position: relative;
  overflow: hidden;
}

.confidence-fill {
  height: 100%;
  background: rgb(var(--v-theme-success));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.confidence-text {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Criteria Grid */
.criteria-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.criteria-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 4px;
}

.criteria-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.criteria-scores-row {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-chip {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: white;
}

.score-a {
  background: rgb(33, 150, 243);
}

.score-b {
  background: rgb(76, 175, 80);
}

.score-high {
  opacity: 1;
}

.score-mid {
  opacity: 0.7;
}

.score-low {
  opacity: 0.5;
}

.score-vs {
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Justification */
.justification-box {
  padding: 8px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 4px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.justification-label {
  font-size: 10px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
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

.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
