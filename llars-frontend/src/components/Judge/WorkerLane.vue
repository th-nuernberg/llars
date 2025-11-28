<template>
  <v-card
    variant="outlined"
    class="worker-lane"
    :class="{
      'lane-active': isActive,
      'lane-streaming': isStreaming,
      'lane-complete': !isStreaming && parsedResult?.winner
    }"
  >
    <!-- Worker Header - Glassmorphism Style -->
    <div class="worker-header" :class="`worker-header--${workerColorName}`">
      <div class="header-content">
        <!-- Worker Badge with Progress Ring -->
        <div class="worker-badge-container">
          <svg class="progress-ring" viewBox="0 0 44 44">
            <circle
              class="progress-ring-bg"
              cx="22" cy="22" r="18"
              fill="none"
              stroke-width="3"
            />
            <circle
              class="progress-ring-fill"
              :class="`ring-${workerColorName}`"
              cx="22" cy="22" r="18"
              fill="none"
              stroke-width="3"
              :stroke-dasharray="progressCircumference"
              :stroke-dashoffset="progressOffset"
            />
          </svg>
          <div class="worker-badge" :class="`badge-${workerColorName}`">
            <span class="badge-text">W{{ workerId + 1 }}</span>
          </div>
        </div>

        <!-- Worker Info -->
        <div class="worker-info">
          <span class="worker-title">Worker {{ workerId + 1 }}</span>
          <div class="worker-subtitle">
            <v-icon
              size="10"
              :color="statusColor"
              :class="{ 'rotating': isStreaming }"
            >
              {{ statusIcon }}
            </v-icon>
            <span class="status-text">{{ statusText }}</span>
          </div>
        </div>

        <v-spacer></v-spacer>

        <!-- Status Indicator -->
        <div class="status-indicator" :class="`status-${statusType}`">
          <div class="status-dot" :class="{ 'pulsing': isStreaming }"></div>
          <span class="status-label">{{ statusText }}</span>
        </div>

        <!-- Fullscreen Button -->
        <v-btn
          icon
          size="x-small"
          variant="text"
          class="fullscreen-btn"
          @click="$emit('open-fullscreen', workerId)"
          title="Vollbild"
        >
          <v-icon size="18">mdi-fullscreen</v-icon>
        </v-btn>
      </div>

      <!-- Pillar Pair Badge -->
      <div v-if="currentComparison" class="pillar-pair-badge">
        <div class="pillar-chip pillar-a">
          <v-icon size="12">{{ getPillarIcon(currentComparison.pillar_a) }}</v-icon>
          <span>{{ getPillarShortName(currentComparison.pillar_a_name) }}</span>
        </div>
        <v-icon size="14" class="vs-icon">mdi-sword-cross</v-icon>
        <div class="pillar-chip pillar-b">
          <v-icon size="12">{{ getPillarIcon(currentComparison.pillar_b) }}</v-icon>
          <span>{{ getPillarShortName(currentComparison.pillar_b_name) }}</span>
        </div>
      </div>
    </div>

    <v-divider></v-divider>

    <!-- Content Area -->
    <v-card-text class="pa-0 stream-container">
      <!-- Empty State -->
      <div v-if="!streamContent && !currentComparison" class="empty-state">
        <div class="empty-icon-container">
          <v-icon size="40" class="empty-icon">mdi-robot-off-outline</v-icon>
        </div>
        <span class="empty-text">Wartet auf Aufgabe...</span>
      </div>

      <!-- Live Result Display -->
      <div v-else class="worker-content">
        <!-- Battle Cards Section -->
        <div class="battle-section">
          <!-- Thread A Card -->
          <div
            class="battle-card battle-card-a"
            :class="{
              'is-winner': parsedResult?.winner === 'A',
              'is-loser': parsedResult?.winner === 'B'
            }"
          >
            <div class="battle-card-header">
              <span class="thread-label">A</span>
              <v-icon v-if="parsedResult?.winner === 'A'" size="16" color="warning" class="winner-icon">
                mdi-trophy
              </v-icon>
            </div>
            <div class="battle-card-pillar">
              <v-icon size="14">{{ getPillarIcon(currentComparison?.pillar_a) }}</v-icon>
              <span>{{ getPillarShortName(currentComparison?.pillar_a_name) }}</span>
            </div>
            <div class="battle-card-score">
              <span class="score-value">{{ totalScoreA }}</span>
              <span class="score-max">/30</span>
            </div>
            <div class="score-bar">
              <div class="score-bar-fill score-bar-a" :style="{ width: (totalScoreA / 30 * 100) + '%' }"></div>
            </div>
          </div>

          <!-- VS Indicator -->
          <div class="vs-container">
            <div class="vs-badge" :class="{ 'has-winner': parsedResult?.winner }">
              <v-icon
                v-if="isStreaming && !parsedResult?.winner"
                size="20"
                class="rotating"
              >
                mdi-loading
              </v-icon>
              <template v-else>
                <v-icon v-if="parsedResult?.winner" size="18" color="warning">mdi-trophy</v-icon>
                <span class="winner-letter">{{ parsedResult?.winner || 'VS' }}</span>
              </template>
            </div>
            <div v-if="parsedResult?.confidence" class="confidence-badge">
              {{ Math.round(parsedResult.confidence * 100) }}%
            </div>
          </div>

          <!-- Thread B Card -->
          <div
            class="battle-card battle-card-b"
            :class="{
              'is-winner': parsedResult?.winner === 'B',
              'is-loser': parsedResult?.winner === 'A'
            }"
          >
            <div class="battle-card-header">
              <span class="thread-label">B</span>
              <v-icon v-if="parsedResult?.winner === 'B'" size="16" color="warning" class="winner-icon">
                mdi-trophy
              </v-icon>
            </div>
            <div class="battle-card-pillar">
              <v-icon size="14">{{ getPillarIcon(currentComparison?.pillar_b) }}</v-icon>
              <span>{{ getPillarShortName(currentComparison?.pillar_b_name) }}</span>
            </div>
            <div class="battle-card-score">
              <span class="score-value">{{ totalScoreB }}</span>
              <span class="score-max">/30</span>
            </div>
            <div class="score-bar">
              <div class="score-bar-fill score-bar-b" :style="{ width: (totalScoreB / 30 * 100) + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- Dominance Bar -->
        <div class="dominance-section">
          <div class="dominance-bar">
            <div
              class="dominance-fill dominance-a"
              :style="{ width: dominanceA + '%' }"
            ></div>
            <div
              class="dominance-fill dominance-b"
              :style="{ width: dominanceB + '%' }"
            ></div>
          </div>
          <div class="dominance-label">
            <span v-if="scoreDiff > 0" class="diff-positive">A +{{ scoreDiff }}</span>
            <span v-else-if="scoreDiff < 0" class="diff-negative">B +{{ Math.abs(scoreDiff) }}</span>
            <span v-else class="diff-neutral">Gleichstand</span>
          </div>
        </div>

        <!-- Criteria Table -->
        <div class="criteria-section">
          <div class="criteria-header">
            <span class="criteria-title">Kriterien</span>
            <div class="criteria-legend">
              <span class="legend-a">A</span>
              <span class="legend-divider">|</span>
              <span class="legend-b">B</span>
              <span class="legend-diff">Diff</span>
            </div>
          </div>
          <div class="criteria-table">
            <div
              v-for="criterion in CRITERIA_CONFIG"
              :key="criterion.key"
              class="criteria-row"
              :class="{
                'row-streaming': isStreaming && !getScoreA(criterion.key) && !getScoreB(criterion.key)
              }"
            >
              <span class="criteria-name" :title="criterion.full">{{ criterion.short }}</span>
              <div class="criteria-scores">
                <!-- A Score Dots -->
                <div class="score-dots dots-a">
                  <div
                    v-for="n in 5"
                    :key="`a-${n}`"
                    class="score-dot"
                    :class="{
                      'dot-filled': getScoreA(criterion.key) >= n,
                      'dot-pending': !getScoreA(criterion.key) && isStreaming
                    }"
                  ></div>
                </div>
                <span class="score-divider">|</span>
                <!-- B Score Dots -->
                <div class="score-dots dots-b">
                  <div
                    v-for="n in 5"
                    :key="`b-${n}`"
                    class="score-dot"
                    :class="{
                      'dot-filled': getScoreB(criterion.key) >= n,
                      'dot-pending': !getScoreB(criterion.key) && isStreaming
                    }"
                  ></div>
                </div>
                <!-- Diff Indicator -->
                <div class="diff-indicator" :class="getDiffClass(criterion.key)">
                  {{ getDiffText(criterion.key) }}
                </div>
              </div>
            </div>
            <!-- Total Row -->
            <div class="criteria-row total-row">
              <span class="criteria-name">TOTAL</span>
              <div class="criteria-scores">
                <span class="total-score total-a">{{ totalScoreA }}</span>
                <span class="score-divider">|</span>
                <span class="total-score total-b">{{ totalScoreB }}</span>
                <div class="diff-indicator" :class="scoreDiff > 0 ? 'diff-positive' : scoreDiff < 0 ? 'diff-negative' : 'diff-neutral'">
                  {{ scoreDiff > 0 ? '+' + scoreDiff : scoreDiff < 0 ? scoreDiff : '0' }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Analysis Timeline -->
        <div class="timeline-section">
          <div class="timeline-header">
            <v-icon size="14">mdi-timeline-clock-outline</v-icon>
            <span>Analyse-Fortschritt</span>
            <span class="step-counter">{{ completedSteps }}/6</span>
          </div>
          <div class="timeline-track">
            <div
              v-for="(step, index) in STEP_CONFIG"
              :key="step.key"
              class="timeline-step"
              :class="{
                'step-complete': getStepByKey(step.key) && !getStepByKey(step.key)?.isStreaming,
                'step-active': getStepByKey(step.key)?.isStreaming,
                'step-pending': !getStepByKey(step.key)
              }"
            >
              <div class="step-node">
                <v-icon
                  v-if="getStepByKey(step.key)?.isStreaming"
                  size="12"
                  class="rotating"
                >
                  mdi-loading
                </v-icon>
                <v-icon
                  v-else-if="getStepByKey(step.key)"
                  size="12"
                >
                  mdi-check
                </v-icon>
                <span v-else class="step-number">{{ index + 1 }}</span>
              </div>
              <span class="step-label">{{ step.short }}</span>
              <div v-if="index < 5" class="step-connector" :class="{ 'connector-active': getStepByKey(step.key) }"></div>
            </div>
          </div>

          <!-- Live Step Preview -->
          <div v-if="currentActiveStep" class="live-preview">
            <div class="preview-header">
              <v-icon size="12" class="rotating">mdi-loading</v-icon>
              <span>{{ currentActiveStep.title }}</span>
            </div>
            <div class="preview-content">
              {{ truncateText(currentActiveStep.content, 120) }}<span class="cursor-blink">|</span>
            </div>
          </div>
        </div>

      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import {
  useWorkerState,
  useStreamParser,
  CRITERIA_CONFIG,
  STEP_CONFIG
} from './WorkerLane/composables';

const props = defineProps({
  workerId: {
    type: Number,
    required: true
  },
  currentComparison: {
    type: Object,
    default: null
  },
  streamContent: {
    type: String,
    default: ''
  },
  isStreaming: {
    type: Boolean,
    default: false
  },
  pairStats: {
    type: Object,
    default: null
  }
});

defineEmits(['open-fullscreen']);

const expandedPanel = ref(null);

// Initialize composables
const {
  workerColorName,
  isActive,
  statusType,
  statusColor,
  statusIcon,
  statusText,
  progressCircumference,
  progressOffset: progressOffsetFn,
  getPillarIcon,
  getPillarShortName,
  truncateText
} = useWorkerState(props);

const {
  parsedResult,
  parsedStreamSteps,
  getStepByKey,
  completedSteps,
  currentActiveStep,
  getScoreA,
  getScoreB,
  totalScoreA,
  totalScoreB,
  scoreDiff,
  dominanceA,
  dominanceB,
  getDiffClass,
  getDiffText
} = useStreamParser(props);

// Progress offset as computed (uses completedSteps from streamParser)
const progressOffset = computed(() => progressOffsetFn(completedSteps.value));

// Auto-expand panel when streaming starts
watch(() => props.isStreaming, (streaming) => {
  if (streaming) {
    expandedPanel.value = 'stream';
  }
});
</script>

<style scoped>
.worker-lane {
  transition: all 0.3s ease;
  min-height: 420px;
  overflow: hidden;
  border-radius: 12px;
}

.worker-lane.lane-active {
  border-color: rgb(var(--v-theme-primary));
}

.worker-lane.lane-streaming {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 20px rgba(var(--v-theme-warning), 0.2);
}

.worker-lane.lane-complete {
  border-color: rgb(var(--v-theme-success));
}

/* Worker Header - Compact */
.worker-header {
  padding: 6px 8px;
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.9) 0%, rgba(var(--v-theme-surface-variant), 0.5) 100%);
  backdrop-filter: blur(10px);
}

.worker-header--blue { border-left: 3px solid #2196F3; }
.worker-header--purple { border-left: 3px solid #9C27B0; }
.worker-header--teal { border-left: 3px solid #009688; }
.worker-header--orange { border-left: 4px solid #FF9800; }
.worker-header--pink { border-left: 4px solid #E91E63; }

.header-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Progress Ring - Compact */
.worker-badge-container {
  position: relative;
  width: 32px;
  height: 32px;
}

.progress-ring {
  position: absolute;
  top: 0;
  left: 0;
  transform: rotate(-90deg);
  width: 32px;
  height: 32px;
}

.progress-ring-bg {
  stroke: rgba(var(--v-theme-on-surface), 0.1);
}

.progress-ring-fill {
  transition: stroke-dashoffset 0.3s ease;
}

.ring-blue { stroke: #2196F3; }
.ring-purple { stroke: #9C27B0; }
.ring-teal { stroke: #009688; }
.ring-orange { stroke: #FF9800; }
.ring-pink { stroke: #E91E63; }

.worker-badge {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.badge-blue { background: linear-gradient(135deg, #2196F3, #1976D2); }
.badge-purple { background: linear-gradient(135deg, #9C27B0, #7B1FA2); }
.badge-teal { background: linear-gradient(135deg, #009688, #00796B); }
.badge-orange { background: linear-gradient(135deg, #FF9800, #F57C00); }
.badge-pink { background: linear-gradient(135deg, #E91E63, #C2185B); }

.badge-text {
  color: white;
  font-weight: 700;
  font-size: 9px;
}

.worker-info {
  flex: 1;
}

.worker-title {
  font-weight: 600;
  font-size: 12px;
  color: rgb(var(--v-theme-on-surface));
}

.worker-subtitle {
  display: none; /* Hide subtitle for compact view */
}

.status-text {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Status Indicator - Compact */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 9px;
  font-weight: 500;
}

.status-indicator.status-streaming {
  background: rgba(var(--v-theme-warning), 0.15);
  color: rgb(var(--v-theme-warning));
}

.status-indicator.status-active {
  background: rgba(var(--v-theme-info), 0.15);
  color: rgb(var(--v-theme-info));
}

.status-indicator.status-idle {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-dot.pulsing {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

.fullscreen-btn {
  opacity: 0.7;
  transition: opacity 0.2s;
}

.fullscreen-btn:hover {
  opacity: 1;
}

/* Pillar Pair Badge - Compact */
.pillar-pair-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 6px;
  padding: 4px 8px;
  background: rgba(var(--v-theme-surface), 0.6);
  border-radius: 12px;
}

.pillar-chip {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 8px;
  font-size: 9px;
  font-weight: 500;
}

.pillar-chip.pillar-a {
  background: rgba(33, 150, 243, 0.15);
  color: #2196F3;
}

.pillar-chip.pillar-b {
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.vs-icon {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Stream Container - No scroll, fit content */
.stream-container {
  overflow: visible;
}

/* Empty State - Compact */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 12px;
  text-align: center;
}

.empty-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.empty-icon {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

.empty-text {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Worker Content - Compact */
.worker-content {
  padding: 8px;
}

/* Battle Section - Compact */
.battle-section {
  display: flex;
  align-items: stretch;
  gap: 6px;
  margin-bottom: 8px;
}

.battle-card {
  flex: 1;
  padding: 6px;
  border-radius: 8px;
  text-align: center;
  transition: all 0.3s ease;
}

.battle-card-a {
  background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(33, 150, 243, 0.05) 100%);
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.battle-card-b {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
  border: 1px solid rgba(76, 175, 80, 0.2);
}

.battle-card.is-winner {
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(var(--v-theme-warning), 0.3);
}

.battle-card.is-loser {
  opacity: 0.6;
}

.battle-card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-bottom: 2px;
}

.thread-label {
  font-size: 14px;
  font-weight: 700;
}

.battle-card-a .thread-label { color: #2196F3; }
.battle-card-b .thread-label { color: #4CAF50; }

.winner-icon {
  animation: bounce 0.5s ease;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}

.battle-card-pillar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 3px;
}

.battle-card-score {
  margin-bottom: 2px;
}

.score-value {
  font-size: 16px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.score-max {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.score-bar {
  height: 3px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.score-bar-a { background: #2196F3; }
.score-bar-b { background: #4CAF50; }

/* VS Container - Compact */
.vs-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-width: 36px;
}

.vs-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(var(--v-theme-surface-variant), 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.vs-badge.has-winner {
  background: linear-gradient(135deg, rgba(var(--v-theme-warning), 0.2) 0%, rgba(var(--v-theme-warning), 0.1) 100%);
}

.winner-letter {
  font-size: 11px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.confidence-badge {
  margin-top: 2px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Dominance Section - Compact */
.dominance-section {
  margin-bottom: 6px;
}

.dominance-bar {
  display: flex;
  height: 4px;
  border-radius: 2px;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.dominance-fill {
  transition: width 0.3s ease;
}

.dominance-a { background: #2196F3; }
.dominance-b { background: #4CAF50; }

.dominance-label {
  text-align: center;
  margin-top: 2px;
  font-size: 9px;
  font-weight: 600;
}

.diff-positive { color: #2196F3; }
.diff-negative { color: #4CAF50; }
.diff-neutral { color: rgba(var(--v-theme-on-surface), 0.5); }

/* Criteria Section - Compact */
.criteria-section {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 6px;
  padding: 6px;
  margin-bottom: 6px;
}

.criteria-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
}

.criteria-title {
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.criteria-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 8px;
}

.legend-a { color: #2196F3; font-weight: 600; }
.legend-b { color: #4CAF50; font-weight: 600; }
.legend-divider { color: rgba(var(--v-theme-on-surface), 0.3); }
.legend-diff { color: rgba(var(--v-theme-on-surface), 0.5); }

.criteria-table {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.criteria-row {
  display: flex;
  align-items: center;
  padding: 2px 0;
}

.criteria-row.row-streaming {
  opacity: 0.5;
}

.criteria-row.total-row {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  margin-top: 2px;
  padding-top: 4px;
  font-weight: 600;
}

.criteria-name {
  width: 26px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.criteria-scores {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
}

.score-dots {
  display: flex;
  gap: 2px;
}

.score-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.12);
  transition: all 0.2s ease;
}

.dots-a .score-dot.dot-filled { background: #2196F3; }
.dots-b .score-dot.dot-filled { background: #4CAF50; }

.score-dot.dot-pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.score-divider {
  color: rgba(var(--v-theme-on-surface), 0.2);
  font-size: 8px;
  margin: 0 1px;
}

.diff-indicator {
  width: 18px;
  text-align: right;
  font-size: 8px;
  font-weight: 600;
}

.total-score {
  font-size: 10px;
  font-weight: 700;
  width: 30px;
  text-align: center;
}

.total-a { color: #2196F3; }
.total-b { color: #4CAF50; }

/* Timeline Section - Compact */
.timeline-section {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 6px;
  padding: 6px;
  margin-bottom: 6px;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 6px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.step-counter {
  margin-left: auto;
  padding: 1px 4px;
  background: rgba(var(--v-theme-primary), 0.1);
  border-radius: 8px;
  font-size: 8px;
  color: rgb(var(--v-theme-primary));
}

.timeline-track {
  display: flex;
  justify-content: space-between;
  position: relative;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-node {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  z-index: 1;
}

.timeline-step.step-complete .step-node {
  background: rgb(var(--v-theme-success));
  color: white;
}

.timeline-step.step-active .step-node {
  background: rgb(var(--v-theme-warning));
  color: white;
  box-shadow: 0 0 10px rgba(var(--v-theme-warning), 0.4);
}

.step-label {
  font-size: 7px;
  margin-top: 2px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.timeline-step.step-complete .step-label,
.timeline-step.step-active .step-label {
  color: rgb(var(--v-theme-on-surface));
  font-weight: 500;
}

.step-connector {
  position: absolute;
  top: 9px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  z-index: 0;
}

.step-connector.connector-active {
  background: rgb(var(--v-theme-success));
}

.step-number {
  font-size: 8px;
}

/* Live Preview - Compact */
.live-preview {
  margin-top: 6px;
  padding: 4px 6px;
  background: rgba(var(--v-theme-warning), 0.1);
  border-radius: 4px;
  border-left: 2px solid rgb(var(--v-theme-warning));
}

.preview-header {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 8px;
  font-weight: 600;
  color: rgb(var(--v-theme-warning));
  margin-bottom: 2px;
}

.preview-content {
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.8);
  line-height: 1.3;
  max-height: 32px;
  overflow: hidden;
}

/* Justification Section */
.justification-section {
  background: rgba(var(--v-theme-primary), 0.08);
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 12px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.justification-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  margin-bottom: 6px;
}

.justification-content {
  font-size: 11px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.8);
  max-height: 60px;
  overflow-y: auto;
}

/* View Toggle */
.view-toggle {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

/* Raw Panel */
.raw-panel {
  margin-top: 8px;
}

.raw-panel-title {
  font-size: 12px;
  min-height: 36px !important;
  padding: 0 12px !important;
}

.raw-panel-content {
  max-height: 120px;
  overflow-y: auto;
}

.stream-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 10px;
  line-height: 1.4;
}

/* Animations */
.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

.rotating {
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
