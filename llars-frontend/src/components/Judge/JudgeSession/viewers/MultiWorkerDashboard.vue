<template>
  <div class="multi-worker-dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <v-icon size="20" class="mr-2">mdi-account-group</v-icon>
        <span class="header-title">{{ activeWorkerCount }}/{{ workerCount }} Worker aktiv</span>
        <v-chip
          v-if="streamingWorkerCount"
          color="warning"
          size="x-small"
          class="ml-2 pulse-chip"
        >
          {{ streamingWorkerCount }} streaming
        </v-chip>
      </div>
      <div class="header-right">
        <v-btn-toggle v-model="viewMode" density="compact" mandatory>
          <v-btn value="grid" size="small" variant="text" title="Grid Ansicht">
            <v-icon size="18">mdi-view-grid</v-icon>
          </v-btn>
          <v-btn value="list" size="small" variant="text" title="Listen Ansicht">
            <v-icon size="18">mdi-view-list</v-icon>
          </v-btn>
        </v-btn-toggle>
        <v-btn
          icon="mdi-fullscreen"
          variant="text"
          size="small"
          @click="$emit('open-fullscreen')"
          title="Vollbild"
        ></v-btn>
      </div>
    </div>

    <!-- Worker Grid/List -->
    <div class="dashboard-content">
      <div class="workers-container" :class="viewMode">
        <div
          v-for="i in workerCount"
          :key="i - 1"
          class="worker-card"
          :class="{
            'is-streaming': workerStreams[i - 1]?.isStreaming,
            'has-result': getWorkerResult(i - 1)?.winner,
            'is-idle': !workerStreams[i - 1]?.comparison,
            'is-selected': selectedWorkerId === (i - 1)
          }"
          @click="selectWorker(i - 1)"
        >
          <!-- Worker Header -->
          <div class="worker-header" :style="{ '--worker-color': WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
            <div class="worker-badge" :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
              W{{ i }}
            </div>
            <div class="worker-status-row">
              <template v-if="workerStreams[i - 1]?.comparison">
                <span class="pillar-tag pillar-a">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }}</span>
                <v-icon size="12">mdi-arrow-left-right</v-icon>
                <span class="pillar-tag pillar-b">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}</span>
              </template>
              <span v-else class="idle-text">Idle</span>
            </div>
            <div class="worker-indicator">
              <v-icon
                v-if="workerStreams[i - 1]?.isStreaming"
                size="14"
                color="warning"
                class="streaming-icon"
              >mdi-circle</v-icon>
              <v-icon
                v-else-if="getWorkerResult(i - 1)?.winner"
                size="14"
                color="success"
              >mdi-check-circle</v-icon>
            </div>
          </div>

          <!-- Worker Body -->
          <div class="worker-body">
            <template v-if="workerStreams[i - 1]?.comparison">
              <!-- Result Row -->
              <div class="result-row">
                <div class="result-winner">
                  <span class="result-label">Gewinner:</span>
                  <span
                    class="winner-badge"
                    :class="{
                      'winner-a': getWorkerResult(i - 1)?.winner === 'A',
                      'winner-b': getWorkerResult(i - 1)?.winner === 'B',
                      'winner-tie': getWorkerResult(i - 1)?.winner === 'TIE',
                      'pending': !getWorkerResult(i - 1)?.winner
                    }"
                  >
                    {{ getWorkerResult(i - 1)?.winner || '...' }}
                  </span>
                </div>
                <div v-if="getWorkerResult(i - 1)?.confidence" class="result-confidence">
                  {{ Math.round(getWorkerResult(i - 1).confidence * 100) }}%
                </div>
              </div>

              <!-- Mini Score Dots -->
              <div class="score-mini-grid">
                <div
                  v-for="criterion in CRITERIA_KEYS.slice(0, 3)"
                  :key="criterion"
                  class="score-mini-row"
                >
                  <span class="criterion-mini-label">{{ CRITERIA_SHORT[criterion] }}</span>
                  <div class="score-mini-dots">
                    <span
                      v-for="n in 5"
                      :key="`a-${n}`"
                      class="mini-dot dot-a"
                      :class="{ filled: getScoreA(i - 1, criterion) >= n }"
                    ></span>
                    <span class="mini-divider">|</span>
                    <span
                      v-for="n in 5"
                      :key="`b-${n}`"
                      class="mini-dot dot-b"
                      :class="{ filled: getScoreB(i - 1, criterion) >= n }"
                    ></span>
                  </div>
                </div>
              </div>

              <!-- Stream Preview -->
              <div v-if="workerStreams[i - 1]?.isStreaming" class="stream-preview">
                <span class="stream-preview-text">{{ getStreamPreview(i - 1) }}</span>
                <span class="cursor-blink">|</span>
              </div>
            </template>

            <!-- Idle State -->
            <template v-else>
              <div class="idle-state">
                <v-icon size="28" color="grey-lighten-1">mdi-robot-off-outline</v-icon>
                <span>Wartet auf Aufgabe</span>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Detail Panel (when worker selected) -->
    <v-expand-transition>
      <div v-if="selectedWorkerId !== null" class="detail-panel">
        <div class="detail-header">
          <div class="detail-header-left">
            <v-icon size="16" class="mr-1">mdi-eye</v-icon>
            <span class="detail-title">Worker {{ selectedWorkerId + 1 }} Detail</span>
            <v-chip
              v-if="workerStreams[selectedWorkerId]?.isStreaming"
              color="warning"
              size="x-small"
              class="ml-2"
            >
              Live
            </v-chip>
          </div>
          <v-btn icon="mdi-close" size="x-small" variant="text" @click="selectedWorkerId = null"></v-btn>
        </div>

        <div class="detail-content">
          <!-- Comparison Info -->
          <div v-if="workerStreams[selectedWorkerId]?.comparison" class="comparison-info">
            <v-chip color="blue" size="x-small" class="mr-1">
              {{ workerStreams[selectedWorkerId].comparison.pillar_a_name || 'Säule ' + workerStreams[selectedWorkerId].comparison.pillar_a }}
            </v-chip>
            <span class="vs-label">vs</span>
            <v-chip color="green" size="x-small" class="ml-1">
              {{ workerStreams[selectedWorkerId].comparison.pillar_b_name || 'Säule ' + workerStreams[selectedWorkerId].comparison.pillar_b }}
            </v-chip>
          </div>

          <!-- Full Stream Output -->
          <div class="stream-output" ref="detailStreamRef">
            <pre v-if="workerStreams[selectedWorkerId]?.content">{{ workerStreams[selectedWorkerId].content }}</pre>
            <div v-else class="stream-empty">
              <v-progress-circular
                v-if="workerStreams[selectedWorkerId]?.isStreaming"
                indeterminate
                size="20"
                color="primary"
              ></v-progress-circular>
              <span>{{ workerStreams[selectedWorkerId]?.isStreaming ? 'Warte auf Ausgabe...' : 'Keine Ausgabe' }}</span>
            </div>
          </div>
        </div>
      </div>
    </v-expand-transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  workerCount: { type: Number, required: true },
  workerStreams: { type: Object, required: true },
  getWorkerParsedResult: { type: Function, required: true },
  getWorkerScoreA: { type: Function, required: true },
  getWorkerScoreB: { type: Function, required: true }
});

defineEmits(['open-fullscreen', 'select-worker']);

const WORKER_COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#E91E63', '#795548', '#607D8B'];

const PILLAR_SHORTS = {
  1: 'Rolle',
  2: 'Feat',
  3: 'Anon',
  4: 'Synth',
  5: 'Live'
};

const CRITERIA_KEYS = ['counsellor_coherence', 'client_coherence', 'quality', 'empathy', 'authenticity', 'solution_orientation'];

const CRITERIA_SHORT = {
  counsellor_coherence: 'KB',
  client_coherence: 'KK',
  quality: 'QL',
  empathy: 'EM',
  authenticity: 'AU',
  solution_orientation: 'LÖ'
};

const viewMode = ref('grid');
const selectedWorkerId = ref(null);
const detailStreamRef = ref(null);

// Computed
const activeWorkerCount = computed(() => {
  let count = 0;
  for (let i = 0; i < props.workerCount; i++) {
    if (props.workerStreams[i]?.comparison || props.workerStreams[i]?.isStreaming) {
      count++;
    }
  }
  return count;
});

const streamingWorkerCount = computed(() => {
  let count = 0;
  for (let i = 0; i < props.workerCount; i++) {
    if (props.workerStreams[i]?.isStreaming) {
      count++;
    }
  }
  return count;
});

// Methods
const getPillarShort = (pillarId) => PILLAR_SHORTS[pillarId] || `S${pillarId}`;

const getWorkerResult = (workerId) => props.getWorkerParsedResult(workerId);

const getScoreA = (workerId, criterion) => props.getWorkerScoreA(workerId, criterion);

const getScoreB = (workerId, criterion) => props.getWorkerScoreB(workerId, criterion);

const getStreamPreview = (workerId) => {
  const content = props.workerStreams[workerId]?.content || '';
  return content.slice(-60).replace(/\n/g, ' ');
};

const selectWorker = (workerId) => {
  if (selectedWorkerId.value === workerId) {
    selectedWorkerId.value = null;
  } else {
    selectedWorkerId.value = workerId;
    nextTick(() => {
      if (detailStreamRef.value) {
        detailStreamRef.value.scrollTop = detailStreamRef.value.scrollHeight;
      }
    });
  }
};

// Auto-scroll detail panel
watch(() => props.workerStreams[selectedWorkerId.value]?.content, () => {
  if (detailStreamRef.value) {
    nextTick(() => {
      detailStreamRef.value.scrollTop = detailStreamRef.value.scrollHeight;
    });
  }
});
</script>

<style scoped>
.multi-worker-dashboard {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

/* Header */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
  background: rgba(var(--v-theme-primary), 0.05);
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

/* Content */
.dashboard-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* Workers Container */
.workers-container {
  display: grid;
  gap: 8px;
}

.workers-container.grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  align-content: start;
}

.workers-container.list {
  grid-template-columns: 1fr;
}

.workers-container.list .worker-card {
  flex-direction: row;
}

.workers-container.list .worker-body {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Worker Card */
.worker-card {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.worker-card:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.worker-card.is-streaming {
  border-color: rgba(var(--v-theme-warning), 0.6);
  animation: pulse-border 2s ease-in-out infinite;
}

.worker-card.has-result {
  border-color: rgba(var(--v-theme-success), 0.4);
}

.worker-card.is-idle {
  opacity: 0.6;
}

.worker-card.is-selected {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.3); }
  50% { box-shadow: 0 0 0 4px rgba(var(--v-theme-warning), 0.1); }
}

/* Worker Header */
.worker-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left: 3px solid var(--worker-color, #ccc);
}

.worker-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.worker-status-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.pillar-tag {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
}

.pillar-tag.pillar-a {
  background: rgba(33, 150, 243, 0.15);
  color: #2196F3;
}

.pillar-tag.pillar-b {
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.idle-text {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 11px;
}

.worker-indicator {
  flex-shrink: 0;
}

.streaming-icon {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* Worker Body */
.worker-body {
  padding: 8px;
  min-height: 80px;
}

.result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.result-winner {
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.winner-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 22px;
  padding: 0 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
}

.winner-badge.winner-a {
  background: #2196F3;
  color: white;
}

.winner-badge.winner-b {
  background: #4CAF50;
  color: white;
}

.winner-badge.winner-tie {
  background: #FF9800;
  color: white;
}

.winner-badge.pending {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.5);
  animation: pulse-bg 1.5s ease-in-out infinite;
}

@keyframes pulse-bg {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.result-confidence {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

/* Score Mini Grid */
.score-mini-grid {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 8px;
}

.score-mini-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.criterion-mini-label {
  width: 20px;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-weight: 600;
}

.score-mini-dots {
  display: flex;
  align-items: center;
  gap: 2px;
}

.mini-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.mini-dot.filled.dot-a {
  background: #2196F3;
}

.mini-dot.filled.dot-b {
  background: #4CAF50;
}

.mini-divider {
  margin: 0 2px;
  font-size: 8px;
  color: rgba(var(--v-theme-on-surface), 0.2);
}

/* Stream Preview */
.stream-preview {
  padding: 4px 6px;
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.stream-preview-text {
  opacity: 0.8;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
}

/* Idle State */
.idle-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 4px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 11px;
}

/* Detail Panel */
.detail-panel {
  flex-shrink: 0;
  max-height: 220px;
  border-top: 2px solid rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-surface-variant), 0.2);
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(var(--v-theme-primary), 0.08);
  flex-shrink: 0;
}

.detail-header-left {
  display: flex;
  align-items: center;
}

.detail-title {
  font-size: 13px;
  font-weight: 600;
}

.detail-content {
  flex: 1;
  padding: 8px 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comparison-info {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.vs-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin: 0 4px;
}

.stream-output {
  flex: 1;
  overflow-y: auto;
  background: rgb(var(--v-theme-surface));
  border-radius: 4px;
  padding: 8px;
  min-height: 0;
}

.stream-output pre {
  margin: 0;
  font-family: 'Fira Code', monospace;
  font-size: 10px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
}

.stream-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 11px;
}

/* Animations */
.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
