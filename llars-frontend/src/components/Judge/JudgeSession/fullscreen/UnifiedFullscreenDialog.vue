<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    fullscreen
    transition="dialog-bottom-transition"
    class="unified-fullscreen-dialog"
  >
    <v-card class="fullscreen-card">
      <!-- Header -->
      <div class="fullscreen-header">
        <div class="header-left">
          <v-btn
            icon="mdi-close"
            variant="text"
            @click="close"
          ></v-btn>
          <div class="header-title-section">
            <v-icon size="24" class="mr-2">{{ modeIcon }}</v-icon>
            <div class="header-titles">
              <span class="header-title">{{ modeTitle }}</span>
              <span class="header-subtitle">{{ modeSubtitle }}</span>
            </div>
          </div>
        </div>

        <div class="header-center">
          <!-- Session Progress -->
          <div v-if="session" class="session-progress">
            <div class="progress-stat">
              <span class="stat-value">{{ displayCompleted }}</span>
              <span class="stat-label">Fertig</span>
            </div>
            <v-progress-linear
              :model-value="progressPercent"
              color="primary"
              height="6"
              rounded
              class="progress-bar"
            ></v-progress-linear>
            <div class="progress-stat">
              <span class="stat-value">{{ displayTotal }}</span>
              <span class="stat-label">Gesamt</span>
            </div>
          </div>
        </div>

        <div class="header-right">
          <!-- Mode Toggle for Multi-Worker -->
          <v-btn-toggle
            v-if="mode === 'live-multi'"
            v-model="multiViewMode"
            density="compact"
            mandatory
            class="mr-2"
          >
            <v-btn value="grid" size="small" variant="text" title="Übersicht">
              <v-icon size="18">mdi-view-grid</v-icon>
            </v-btn>
            <v-btn value="compare" size="small" variant="text" title="Vergleichen">
              <v-icon size="18">mdi-compare</v-icon>
            </v-btn>
            <v-btn value="focus" size="small" variant="text" title="Detail">
              <v-icon size="18">mdi-card-account-details</v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-chip v-if="mode.startsWith('live')" color="secondary" size="small" class="pulse-chip">
            <v-icon start size="14">mdi-broadcast</v-icon>
            Live
          </v-chip>
        </div>
      </div>

      <!-- Content -->
      <div class="fullscreen-content">
        <!-- Single Comparison View (Live or Historical) -->
        <template v-if="mode === 'live-single' || mode === 'historical'">
          <SingleComparisonView
            :comparison="comparison"
            :is-streaming="isStreaming"
            :stream-content="streamContent"
            :parsed-result="parsedResult"
          />
        </template>

        <!-- Multi-Worker View -->
        <template v-else-if="mode === 'live-multi'">
          <!-- Grid View -->
          <div v-if="multiViewMode === 'grid'" class="grid-view">
            <div class="workers-grid">
              <div
                v-for="i in workerCount"
                :key="i - 1"
                class="worker-card-grid"
                :class="{
                  'is-streaming': workerStreams[i - 1]?.isStreaming,
                  'has-result': getWorkerResult(i - 1)?.winner,
                  'is-idle': !workerStreams[i - 1]?.comparison
                }"
              >
                <!-- Card Header -->
                <div class="wcg-header" :style="{ '--worker-color': WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
                  <div class="wcg-badge" :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
                    W{{ i }}
                  </div>
                  <div v-if="workerStreams[i - 1]?.comparison" class="wcg-pillars">
                    <span class="pillar-tag pillar-a">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }}</span>
                    <v-icon size="16">mdi-arrow-left-right</v-icon>
                    <span class="pillar-tag pillar-b">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}</span>
                  </div>
                  <span v-else class="idle-label">Wartet...</span>
                  <v-icon
                    v-if="workerStreams[i - 1]?.isStreaming"
                    size="18"
                    color="secondary"
                    class="streaming-icon"
                  >mdi-circle</v-icon>
                </div>

                <!-- Card Body -->
                <div class="wcg-body">
                  <template v-if="workerStreams[i - 1]?.comparison">
                    <!-- Status -->
                    <div class="wcg-status">
                      <div v-if="workerStreams[i - 1]?.isStreaming" class="status-streaming">
                        <v-icon size="20" class="rotating">mdi-loading</v-icon>
                        <span>Analysiert...</span>
                      </div>
                      <div v-else-if="getWorkerResult(i - 1)?.winner" class="status-complete">
                        <div
                          class="winner-badge-large"
                          :class="'winner-' + getWorkerResult(i - 1).winner.toLowerCase()"
                        >
                          {{ getWorkerResult(i - 1).winner }}
                        </div>
                        <div class="confidence-display">
                          <span class="conf-value">{{ Math.round((getWorkerResult(i - 1).confidence || 0) * 100) }}%</span>
                          <span class="conf-label">Konfidenz</span>
                        </div>
                      </div>
                      <div v-else class="status-pending">
                        <v-icon size="24">mdi-clock-outline</v-icon>
                        <span>Ausstehend</span>
                      </div>
                    </div>

                    <!-- Mini Scores -->
                    <div v-if="getWorkerResult(i - 1)?.criteria_scores" class="wcg-scores">
                      <div class="score-summary">
                        <div class="score-side side-a">
                          <span class="side-label">A</span>
                          <span class="side-total">{{ getWorkerTotalScore(i - 1, 'a') }}</span>
                        </div>
                        <span class="score-vs">vs</span>
                        <div class="score-side side-b">
                          <span class="side-total">{{ getWorkerTotalScore(i - 1, 'b') }}</span>
                          <span class="side-label">B</span>
                        </div>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="wcg-idle">
                      <v-icon size="40" color="grey-lighten-1">mdi-robot-off-outline</v-icon>
                      <span>Wartet auf Aufgabe</span>
                    </div>
                  </template>
                </div>

                <!-- Card Footer -->
                <div class="wcg-footer">
                  <v-btn
                    v-if="workerStreams[i - 1]?.comparison"
                    variant="text"
                    size="small"
                    color="primary"
                    @click="openFocusView(i - 1)"
                  >
                    <v-icon start size="16">mdi-eye</v-icon>
                    Details
                  </v-btn>
                </div>
              </div>
            </div>
          </div>

          <!-- Compare View (NEW) -->
          <div v-else-if="multiViewMode === 'compare'" class="compare-view">
            <div class="compare-container">
              <!-- Left Worker -->
              <div class="compare-panel">
                <div class="compare-panel-header">
                  <v-select
                    v-model="compareWorkerLeft"
                    :items="workerSelectItems"
                    item-title="label"
                    item-value="value"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="worker-select"
                  ></v-select>
                </div>
                <CompareWorkerPanel
                  v-if="compareWorkerLeft !== null"
                  :worker-id="compareWorkerLeft"
                  :worker-stream="workerStreams[compareWorkerLeft]"
                  :worker-result="getWorkerResult(compareWorkerLeft)"
                  :worker-color="WORKER_COLORS[compareWorkerLeft % WORKER_COLORS.length]"
                  :criteria-list="CRITERIA_LIST"
                />
              </div>

              <!-- Divider -->
              <div class="compare-divider">
                <span class="divider-vs">VS</span>
              </div>

              <!-- Right Worker -->
              <div class="compare-panel">
                <div class="compare-panel-header">
                  <v-select
                    v-model="compareWorkerRight"
                    :items="workerSelectItems"
                    item-title="label"
                    item-value="value"
                    density="compact"
                    variant="outlined"
                    hide-details
                    class="worker-select"
                  ></v-select>
                </div>
                <CompareWorkerPanel
                  v-if="compareWorkerRight !== null"
                  :worker-id="compareWorkerRight"
                  :worker-stream="workerStreams[compareWorkerRight]"
                  :worker-result="getWorkerResult(compareWorkerRight)"
                  :worker-color="WORKER_COLORS[compareWorkerRight % WORKER_COLORS.length]"
                  :criteria-list="CRITERIA_LIST"
                />
              </div>
            </div>
          </div>

          <!-- Focus View (Redesigned) -->
          <div v-else-if="multiViewMode === 'focus'" class="focus-view">
            <!-- Worker Tabs -->
            <div class="focus-tabs">
              <v-btn
                v-for="i in workerCount"
                :key="i - 1"
                :variant="localFocusedWorkerId === (i - 1) ? 'flat' : 'text'"
                :color="localFocusedWorkerId === (i - 1) ? 'primary' : undefined"
                size="small"
                class="focus-tab"
                :class="{
                  'is-streaming': workerStreams[i - 1]?.isStreaming,
                  'has-result': getWorkerResult(i - 1)?.winner
                }"
                @click="localFocusedWorkerId = (i - 1)"
              >
                <div
                  class="tab-badge"
                  :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }"
                >W{{ i }}</div>
                <span class="tab-pillars" v-if="workerStreams[i - 1]?.comparison">
                  {{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }}↔{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}
                </span>
                <span v-else class="tab-idle">Idle</span>
                <v-icon
                  v-if="workerStreams[i - 1]?.isStreaming"
                  size="12"
                  color="secondary"
                  class="streaming-dot"
                >mdi-circle</v-icon>
              </v-btn>
            </div>

            <!-- Focus Content -->
            <FocusWorkerView
              v-if="focusedWorker"
              :worker-id="localFocusedWorkerId"
              :worker-stream="focusedWorker"
              :worker-result="getWorkerResult(localFocusedWorkerId)"
              :worker-color="WORKER_COLORS[localFocusedWorkerId % WORKER_COLORS.length]"
              :criteria-list="CRITERIA_LIST"
              :analysis-steps="ANALYSIS_STEPS"
            />
            <div v-else class="focus-empty">
              <v-icon size="64">mdi-account-question</v-icon>
              <span>Wähle einen Worker aus</span>
            </div>
          </div>
        </template>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import SingleComparisonView from './SingleComparisonView.vue';
import CompareWorkerPanel from './CompareWorkerPanel.vue';
import FocusWorkerView from './FocusWorkerView.vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mode: { type: String, default: 'live-single' },
  session: { type: Object, default: null },
  progress: { type: Number, default: 0 },
  currentComparison: { type: Object, default: null },
  isStreaming: { type: Boolean, default: false },
  llmStreamContent: { type: String, default: '' },
  autoScrollEnabled: { type: Boolean, default: true },
  workerCount: { type: Number, default: 1 },
  workerStreams: { type: Object, default: () => ({}) },
  focusedWorkerId: { type: Number, default: 0 },
  scoreCriteria: { type: Array, default: () => [] },
  stepDefinitions: { type: Object, default: () => ({}) },
  getWorkerParsedResult: { type: Function, default: () => null },
  getWorkerScoreA: { type: Function, default: () => 0 },
  getWorkerScoreB: { type: Function, default: () => 0 },
  getWorkerStep: { type: Function, default: () => null },
  getStepByKey: { type: Function, default: () => null },
  getStatusColor: { type: Function, default: () => 'grey' },
  getStatusIcon: { type: Function, default: () => 'mdi-circle' },
  getStatusText: { type: Function, default: () => '' },
  getConfidenceColor: { type: Function, default: () => 'grey' },
  completedCount: { type: Number, default: null },
  confirmedTotal: { type: Number, default: null }
});

const emit = defineEmits(['update:modelValue', 'close', 'stream-scroll', 'enable-auto-scroll', 'focus-worker']);

const WORKER_COLORS = ['#2196F3', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#E91E63', '#795548', '#607D8B'];

const PILLAR_SHORTS = {
  1: 'Rolle',
  2: 'Feat',
  3: 'Anon',
  4: 'Synth',
  5: 'Live'
};

const CRITERIA_LIST = [
  { key: 'counsellor_coherence', short: 'Koh.B', name: 'Berater Kohärenz' },
  { key: 'client_coherence', short: 'Koh.K', name: 'Klient Kohärenz' },
  { key: 'quality', short: 'Qual.', name: 'Qualität' },
  { key: 'empathy', short: 'Emp.', name: 'Empathie' },
  { key: 'authenticity', short: 'Auth.', name: 'Authentizität' },
  { key: 'solution_orientation', short: 'Lösg.', name: 'Lösungsorientierung' }
];

const ANALYSIS_STEPS = [
  { key: 'step_1_overview', icon: 'mdi-eye', name: 'Überblick' },
  { key: 'step_2_strengths_a', icon: 'mdi-thumb-up', name: 'Stärken A' },
  { key: 'step_3_strengths_b', icon: 'mdi-thumb-up', name: 'Stärken B' },
  { key: 'step_4_weaknesses_a', icon: 'mdi-thumb-down', name: 'Schwächen A' },
  { key: 'step_5_weaknesses_b', icon: 'mdi-thumb-down', name: 'Schwächen B' },
  { key: 'step_6_comparison', icon: 'mdi-scale-balance', name: 'Vergleich' }
];

// State
const multiViewMode = ref('grid');
const localFocusedWorkerId = ref(props.focusedWorkerId);
const compareWorkerLeft = ref(0);
const compareWorkerRight = ref(1);

// Sync local focused worker with prop
watch(() => props.focusedWorkerId, (val) => {
  localFocusedWorkerId.value = val;
});

// Initialize compare workers
watch(() => props.workerCount, (count) => {
  if (count > 0) {
    compareWorkerLeft.value = 0;
    compareWorkerRight.value = Math.min(1, count - 1);
  }
}, { immediate: true });

// Computed
const comparison = computed(() => props.currentComparison);
const streamContent = computed(() => props.llmStreamContent);

const modeIcon = computed(() => {
  if (props.mode === 'live-multi') return 'mdi-account-group';
  if (props.mode === 'historical') return 'mdi-history';
  return 'mdi-eye';
});

const modeTitle = computed(() => {
  if (props.mode === 'live-multi') return 'Multi-Worker Live View';
  if (props.mode === 'historical') return 'Historischer Vergleich';
  return 'Live Vergleich';
});

const modeSubtitle = computed(() => {
  if (props.mode === 'live-multi') return `${props.workerCount} Worker`;
  if (comparison.value) {
    return `#${(comparison.value.comparison_index ?? comparison.value.queue_position ?? 0) + 1}`;
  }
  return '';
});

const displayCompleted = computed(() => {
  if (props.completedCount !== null && props.completedCount >= 0) {
    return props.completedCount;
  }
  return props.session?.completed_comparisons || 0;
});

const displayTotal = computed(() => {
  if (props.confirmedTotal !== null && props.confirmedTotal > 0) {
    return props.confirmedTotal;
  }
  return props.session?.total_comparisons || 0;
});

const progressPercent = computed(() => {
  if (!displayTotal.value) return 0;
  return Math.min(100, (displayCompleted.value / displayTotal.value) * 100);
});

const focusedWorker = computed(() => {
  return props.workerStreams[localFocusedWorkerId.value];
});

const workerSelectItems = computed(() => {
  const items = [];
  for (let i = 0; i < props.workerCount; i++) {
    const stream = props.workerStreams[i];
    let label = `Worker ${i + 1}`;
    if (stream?.comparison) {
      label += ` - ${getPillarShort(stream.comparison.pillar_a)} vs ${getPillarShort(stream.comparison.pillar_b)}`;
    } else {
      label += ' - Idle';
    }
    items.push({ label, value: i });
  }
  return items;
});

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

// Methods
const close = () => {
  emit('update:modelValue', false);
  emit('close');
};

const getPillarShort = (pillarId) => PILLAR_SHORTS[pillarId] || `S${pillarId}`;

const getWorkerResult = (workerId) => props.getWorkerParsedResult(workerId);

const getWorkerTotalScore = (workerId, side) => {
  const result = props.getWorkerParsedResult(workerId);
  if (!result?.criteria_scores) return 0;
  let total = 0;
  for (const criterion of CRITERIA_LIST) {
    const scores = result.criteria_scores[criterion.key];
    if (scores) {
      total += side === 'a' ? scores.score_a : scores.score_b;
    }
  }
  return total;
};

const openFocusView = (workerId) => {
  localFocusedWorkerId.value = workerId;
  multiViewMode.value = 'focus';
};
</script>

<style scoped>
.fullscreen-card {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.fullscreen-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(var(--v-theme-primary), 0.1) 0%, rgba(var(--v-theme-surface-variant), 0.5) 100%);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.header-title-section {
  display: flex;
  align-items: center;
}

.header-titles {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-weight: 600;
  font-size: 16px;
}

.header-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Session Progress */
.session-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: rgba(var(--v-theme-surface), 0.8);
  border-radius: 8px;
}

.progress-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 40px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
}

.stat-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.progress-bar {
  width: 150px;
}

/* Content */
.fullscreen-content {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

/* ============================================
   GRID VIEW
   ============================================ */
.grid-view {
  height: 100%;
  overflow-y: auto;
}

.workers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  align-content: start;
}

.worker-card-grid {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  min-height: 200px;
}

.worker-card-grid:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.worker-card-grid.is-streaming {
  border-color: rgb(var(--v-theme-secondary));
  box-shadow: 0 0 20px rgba(var(--v-theme-secondary), 0.2);
}

.worker-card-grid.has-result {
  border-color: rgba(var(--v-theme-success), 0.5);
}

.worker-card-grid.is-idle {
  opacity: 0.6;
}

/* Card Header */
.wcg-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left: 4px solid var(--worker-color, #ccc);
}

.wcg-badge {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.wcg-pillars {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
}

.pillar-tag {
  font-weight: 600;
  font-size: 13px;
}

.pillar-tag.pillar-a {
  color: #2196F3;
}

.pillar-tag.pillar-b {
  color: #4CAF50;
}

.idle-label {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 13px;
  flex: 1;
}

/* Card Body */
.wcg-body {
  flex: 1;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.wcg-status {
  text-align: center;
}

.status-streaming {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: rgb(var(--v-theme-secondary));
}

.status-complete {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.winner-badge-large {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
  color: white;
}

.winner-badge-large.winner-a {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
}

.winner-badge-large.winner-b {
  background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
}

.winner-badge-large.winner-tie {
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
}

.confidence-display {
  text-align: center;
}

.conf-value {
  font-size: 18px;
  font-weight: 600;
  color: rgb(var(--v-theme-success));
}

.conf-label {
  display: block;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.status-pending {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Scores Summary */
.wcg-scores {
  width: 100%;
}

.score-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 8px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.score-side {
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-side.side-a .side-total {
  color: #2196F3;
}

.score-side.side-b .side-total {
  color: #4CAF50;
}

.side-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.side-total {
  font-size: 20px;
  font-weight: 700;
}

.score-vs {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Card Footer */
.wcg-footer {
  padding: 8px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  display: flex;
  justify-content: center;
}

/* Idle State */
.wcg-idle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 13px;
}

/* ============================================
   COMPARE VIEW
   ============================================ */
.compare-view {
  height: 100%;
  overflow: hidden;
}

.compare-container {
  display: flex;
  height: 100%;
  gap: 0;
}

.compare-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.compare-panel-header {
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  flex-shrink: 0;
}

.worker-select {
  max-width: 300px;
}

.compare-divider {
  width: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

.divider-vs {
  font-size: 16px;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.4);
  transform: rotate(-90deg);
}

/* ============================================
   FOCUS VIEW
   ============================================ */
.focus-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.focus-tabs {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  flex-shrink: 0;
  overflow-x: auto;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.focus-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px !important;
  min-width: auto;
}

.focus-tab.is-streaming {
  border: 1px solid rgba(var(--v-theme-secondary), 0.5);
}

.focus-tab.has-result .tab-badge {
  box-shadow: 0 0 8px rgba(var(--v-theme-success), 0.4);
}

.tab-badge {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  color: white;
}

.tab-pillars {
  font-size: 12px;
  font-weight: 500;
}

.tab-idle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.streaming-dot {
  animation: blink 1s infinite;
}

.focus-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Animations */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.streaming-icon {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
