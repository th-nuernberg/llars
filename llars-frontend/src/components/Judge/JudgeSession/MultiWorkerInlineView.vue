<template>
  <div class="multi-worker-inline">
    <!-- Header with view toggle -->
    <div class="mw-header">
      <div class="mw-title">
        <v-icon size="20" class="mr-2">mdi-account-group</v-icon>
        <span>{{ activeWorkerCount }}/{{ workerCount }} Worker aktiv</span>
      </div>
      <div class="mw-actions">
        <v-btn-toggle v-model="viewMode" mandatory density="compact" class="mr-2">
          <v-btn value="grid" size="small" variant="text">
            <v-icon size="18">mdi-view-grid</v-icon>
          </v-btn>
          <v-btn value="list" size="small" variant="text">
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

    <!-- Workers Grid View -->
    <div class="mw-content" :class="{ 'grid-view': viewMode === 'grid', 'list-view': viewMode === 'list' }">
      <div
        v-for="i in workerCount"
        :key="i - 1"
        class="worker-card"
        :class="{
          'is-streaming': workerStreams[i - 1]?.isStreaming,
          'has-comparison': workerStreams[i - 1]?.comparison,
          'is-selected': selectedWorkerId === i - 1
        }"
        @click="selectWorker(i - 1)"
      >
        <!-- Worker Header -->
        <div class="worker-header" :style="{ borderLeftColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
          <div class="worker-id">
            <span class="worker-badge" :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
              W{{ i }}
            </span>
            <v-icon
              v-if="workerStreams[i - 1]?.isStreaming"
              size="14"
              class="streaming-indicator"
            >mdi-circle</v-icon>
          </div>
          <div class="worker-status">
            <template v-if="workerStreams[i - 1]?.comparison">
              <span class="pillar-tag pillar-a">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }}</span>
              <v-icon size="12">mdi-arrow-left-right</v-icon>
              <span class="pillar-tag pillar-b">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}</span>
            </template>
            <span v-else class="text-medium-emphasis text-caption">Wartet...</span>
          </div>
        </div>

        <!-- Worker Content (compact) -->
        <div class="worker-body">
          <template v-if="workerStreams[i - 1]?.comparison">
            <!-- Result Summary -->
            <div class="result-row">
              <div class="result-winner">
                <span class="label">Gewinner:</span>
                <span
                  class="winner-badge"
                  :class="{
                    'winner-a': getWorkerParsedResult(i - 1)?.winner === 'A',
                    'winner-b': getWorkerParsedResult(i - 1)?.winner === 'B',
                    'winner-tie': getWorkerParsedResult(i - 1)?.winner === 'TIE',
                    'pending': !getWorkerParsedResult(i - 1)?.winner
                  }"
                >
                  {{ getWorkerParsedResult(i - 1)?.winner || '...' }}
                </span>
              </div>
              <div class="result-confidence" v-if="getWorkerParsedResult(i - 1)?.confidence">
                <span class="confidence-value">{{ Math.round(getWorkerParsedResult(i - 1).confidence * 100) }}%</span>
              </div>
            </div>

            <!-- Score Preview (mini dots) -->
            <div class="score-preview">
              <div
                v-for="criterion in scoreCriteria.slice(0, 3)"
                :key="criterion.key"
                class="score-row"
              >
                <span class="criterion-label">{{ criterion.shortLabel }}</span>
                <div class="score-dots">
                  <span
                    v-for="n in 5"
                    :key="`a-${n}`"
                    class="dot dot-a"
                    :class="{ filled: getWorkerScoreA(i - 1, criterion.key) >= n }"
                  ></span>
                  <span class="dot-divider">|</span>
                  <span
                    v-for="n in 5"
                    :key="`b-${n}`"
                    class="dot dot-b"
                    :class="{ filled: getWorkerScoreB(i - 1, criterion.key) >= n }"
                  ></span>
                </div>
              </div>
            </div>

            <!-- Stream preview (truncated) -->
            <div class="stream-preview" v-if="workerStreams[i - 1]?.isStreaming">
              <span class="stream-text">{{ getStreamPreview(i - 1) }}</span>
              <span class="cursor-blink">|</span>
            </div>
          </template>
          <template v-else>
            <div class="empty-worker">
              <v-icon size="24" color="grey-lighten-1">mdi-robot-off-outline</v-icon>
              <span class="text-caption text-medium-emphasis">Idle</span>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- Selected Worker Detail (expandable) -->
    <v-expand-transition>
      <div v-if="selectedWorkerId !== null && workerStreams[selectedWorkerId]?.comparison" class="selected-worker-detail">
        <div class="detail-header">
          <span class="detail-title">
            <v-icon size="16" class="mr-1">mdi-eye</v-icon>
            Worker {{ selectedWorkerId + 1 }} Detail
          </span>
          <LIconBtn icon="mdi-close" size="x-small" tooltip="Schließen" @click="selectedWorkerId = null" />
        </div>
        <div class="detail-content">
          <!-- Full stream output -->
          <div class="stream-output" ref="detailStreamRef">
            <pre>{{ workerStreams[selectedWorkerId]?.content || '' }}</pre>
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
  activeWorkerCount: { type: Number, default: 0 },
  workerStreams: { type: Object, required: true },
  scoreCriteria: { type: Array, default: () => [] },
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

const viewMode = ref('grid');
const selectedWorkerId = ref(null);
const detailStreamRef = ref(null);

const getPillarShort = (pillarId) => PILLAR_SHORTS[pillarId] || `S${pillarId}`;

const getStreamPreview = (workerId) => {
  const content = props.workerStreams[workerId]?.content || '';
  return content.slice(-80).replace(/\n/g, ' ');
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

// Auto-scroll detail stream
watch(() => props.workerStreams[selectedWorkerId.value]?.content, () => {
  if (detailStreamRef.value) {
    detailStreamRef.value.scrollTop = detailStreamRef.value.scrollHeight;
  }
});

// Short labels for criteria
const scoreCriteria = computed(() => {
  return (props.scoreCriteria || []).map(c => ({
    ...c,
    shortLabel: c.label?.substring(0, 4) || c.key?.substring(0, 4)
  }));
});
</script>

<style scoped>
.multi-worker-inline {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.mw-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.1);
  flex-shrink: 0;
}

.mw-title {
  display: flex;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
}

.mw-actions {
  display: flex;
  align-items: center;
}

.mw-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.mw-content.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
  align-content: start;
}

.mw-content.list-view {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mw-content.list-view .worker-card {
  flex-direction: row;
  align-items: center;
}

.mw-content.list-view .worker-body {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.worker-card {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
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
  border-color: rgba(var(--v-theme-warning), 0.5);
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(var(--v-theme-warning), 0.2); }
  50% { box-shadow: 0 0 0 4px rgba(var(--v-theme-warning), 0.1); }
}

.worker-card.is-selected {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}

.worker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left: 3px solid transparent;
}

.worker-id {
  display: flex;
  align-items: center;
  gap: 4px;
}

.worker-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  color: white;
}

.streaming-indicator {
  color: rgb(var(--v-theme-warning));
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.worker-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.pillar-tag {
  padding: 1px 4px;
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

.worker-body {
  padding: 8px;
  min-height: 60px;
}

.result-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.result-winner {
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-winner .label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.winner-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 20px;
  padding: 0 6px;
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
  font-size: 11px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.score-preview {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-bottom: 6px;
}

.score-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.criterion-label {
  width: 28px;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
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

.stream-preview {
  font-family: 'Fira Code', monospace;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 4px 6px;
  border-radius: 4px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
}

.empty-worker {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 4px;
}

/* Selected Worker Detail */
.selected-worker-detail {
  flex-shrink: 0;
  max-height: 200px;
  border-top: 1px solid rgba(var(--v-theme-primary), 0.2);
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  background: rgba(var(--v-theme-primary), 0.05);
}

.detail-title {
  display: flex;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
}

.detail-content {
  padding: 8px;
}

.stream-output {
  max-height: 140px;
  overflow-y: auto;
  background: rgb(var(--v-theme-surface));
  border-radius: 4px;
  padding: 8px;
}

.stream-output pre {
  margin: 0;
  font-family: 'Fira Code', monospace;
  font-size: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
