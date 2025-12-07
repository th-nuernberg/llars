<template>
  <v-container fluid class="judge-session">
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.push({ name: 'JudgeOverview' })"
          ></v-btn>
          <div class="ml-2">
            <h1 class="text-h4 font-weight-bold">{{ session?.session_name || 'Judge Session' }}</h1>
            <div class="d-flex align-center mt-1">
              <v-chip
                :color="getStatusColor(session?.status)"
                :prepend-icon="getStatusIcon(session?.status)"
                size="small"
                class="mr-2"
              >
                {{ getStatusText(session?.status) }}
              </v-chip>
              <span class="text-caption text-medium-emphasis">
                Session ID: {{ sessionId }}
              </span>
            </div>
          </div>
          <v-spacer></v-spacer>

          <!-- Action Buttons - Intelligent State-Based -->
          <div class="d-flex gap-2 align-center">
            <!-- Recovery Warning Badge -->
            <v-chip
              v-if="sessionHealth?.needs_recovery"
              color="warning"
              size="small"
              prepend-icon="mdi-alert"
              class="mr-2"
            >
              Wiederherstellung nötig
            </v-chip>

            <!-- START: Only for created/queued sessions -->
            <v-btn
              v-if="session?.status === 'created' || session?.status === 'queued'"
              color="success"
              prepend-icon="mdi-play"
              @click="startSession"
              :loading="actionLoading"
            >
              Starten
            </v-btn>

            <!-- PAUSE: Only when workers are actually running -->
            <v-btn
              v-if="isActuallyRunning"
              color="warning"
              prepend-icon="mdi-pause"
              @click="pauseSession"
              :loading="actionLoading"
            >
              Pause
            </v-btn>

            <!-- RESUME/RECOVER: When session needs recovery or is paused -->
            <v-btn
              v-if="showResumeButton"
              :color="sessionHealth?.needs_recovery ? 'error' : 'info'"
              :prepend-icon="sessionHealth?.needs_recovery ? 'mdi-restart-alert' : 'mdi-play'"
              @click="resumeSession"
              :loading="actionLoading"
            >
              {{ sessionHealth?.needs_recovery ? 'Wiederherstellen' : 'Fortsetzen' }}
            </v-btn>

            <!-- RESULTS: Completed sessions -->
            <v-btn
              v-if="session?.status === 'completed'"
              color="primary"
              prepend-icon="mdi-chart-box"
              @click="navigateToResults"
            >
              Ergebnisse
            </v-btn>

            <!-- Refresh -->
            <v-btn
              icon="mdi-refresh"
              variant="text"
              @click="refreshAll"
              :loading="loading"
              title="Seite aktualisieren"
            ></v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Progress Bar -->
    <v-row class="mb-4">
      <v-col cols="12">
        <SessionProgressBar
          :session="session"
          :progress="progress"
          :worker-count="workerCount"
          :format-date="formatDate"
        />
      </v-col>
    </v-row>

    <!-- Multi-Worker Live View (when worker_count > 1) -->
    <v-row v-if="workerCount > 1 && session?.status === 'running'" class="mb-4">
      <v-col cols="12">
        <WorkerLaneGrid
          :worker-count="workerCount"
          :active-worker-count="activeWorkerCount"
          :session="session"
          :progress="progress"
          :session-pillars="sessionPillars"
          :pillar-pairs="pillarPairs"
          :worker-streams="workerStreams"
          :get-pillar-color="getPillarColor"
          :get-pillar-icon="getPillarIcon"
          :is-pair-active="isPairActive"
          @open-fullscreen="openMultiWorkerFullscreen"
          @refresh="loadWorkerPoolStatus"
          @open-worker-fullscreen="openWorkerFullscreen"
        />
      </v-col>
    </v-row>

    <!-- Queue Display - Shows ALL pending comparisons -->
    <v-row class="mb-4">
      <v-col cols="12">
        <SessionQueuePanel
          :queue="queue"
          :all-queue-items="allQueueItems"
          :headers="queueHeaders"
          :loading="queueLoading"
          :get-queue-status-color="getQueueStatusColor"
          :get-queue-status-icon="getQueueStatusIcon"
          :get-queue-status-text="getQueueStatusText"
          @refresh="loadQueue"
        />
      </v-col>
    </v-row>

    <!-- Current Comparison View -->
    <v-row v-if="currentComparison">
      <v-col cols="12">
        <CurrentComparisonView
          :current-comparison="currentComparison"
          :session="session"
          :reconnecting="reconnecting"
          :is-streaming="isStreaming"
          :llm-stream-content="llmStreamContent"
          :parsed-stream-json="parsedStreamJson"
          :expanded-panels="expandedPanels"
          :auto-scroll-enabled="autoScrollEnabled"
          :format-criterion-name="formatCriterionName"
          :get-score-color="getScoreColor"
          @reconnect="reconnectToStream"
          @open-fullscreen="openFullscreen"
          @copy-stream="copyStreamToClipboard"
          @stream-scroll="handleStreamScroll"
          @enable-auto-scroll="enableAutoScroll"
          @update:expanded-panels="expandedPanels = $event"
        />
      </v-col>
    </v-row>

    <!-- Comparison History -->
    <v-row class="mt-4">
      <v-col cols="12">
        <ComparisonHistoryTable
          :completed-comparisons="completedComparisons"
          :headers="historyHeaders"
          :get-confidence-color="getConfidenceColor"
          :format-date="formatDate"
          @view-comparison="viewComparison"
        />
      </v-col>
    </v-row>
  </v-container>

  <!-- Single Worker Fullscreen Dialog -->
  <SingleWorkerFullscreenDialog
    v-model="fullscreenMode"
    :current-comparison="currentComparison"
    :session="session"
    :is-streaming="isStreaming"
    :llm-stream-content="llmStreamContent"
    :parsed-stream-json="parsedStreamJson"
    :stream-display-mode="streamDisplayMode"
    :auto-scroll-enabled="autoScrollEnabled"
    :progress="progress"
    :score-criteria="SCORE_CRITERIA"
    :step-definitions="STEP_DEFINITIONS"
    :get-step-by-key="getStepByKey"
    :get-status-color="getStatusColor"
    :get-status-icon="getStatusIcon"
    :get-status-text="getStatusText"
    @update:stream-display-mode="streamDisplayMode = $event"
    @close="closeFullscreen"
    @copy-stream="copyStreamToClipboard"
    @stream-scroll="handleStreamScroll"
    @enable-auto-scroll="enableAutoScroll"
  />

  <!-- Multi-Worker Fullscreen Dialog -->
  <MultiWorkerFullscreenDialog
    v-model="multiWorkerFullscreenMode"
    :display-mode="multiWorkerDisplayMode"
    :session="session"
    :active-worker-count="activeWorkerCount"
    :session-pillars="sessionPillars"
    :progress="progress"
    :worker-count="workerCount"
    :worker-streams="workerStreams"
    :worker-colors="WORKER_COLORS"
    :score-criteria="SCORE_CRITERIA"
    :step-definitions="STEP_DEFINITIONS"
    :focused-worker-id="focusedWorkerId"
    :get-multi-worker-col-size="getMultiWorkerColSize"
    :get-pillar-color="getPillarColor"
    :get-pillar-icon="getPillarIcon"
    :get-status-color="getStatusColor"
    :get-status-icon="getStatusIcon"
    :get-status-text="getStatusText"
    :get-worker-parsed-result="getWorkerParsedResult"
    :get-worker-score-a="getWorkerScoreA"
    :get-worker-score-b="getWorkerScoreB"
    :get-worker-step="getWorkerStep"
    :get-confidence-color="getConfidenceColor"
    @update:display-mode="multiWorkerDisplayMode = $event"
    @update:focused-worker-id="focusedWorkerId = $event"
    @close="closeMultiWorkerFullscreen"
  />
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import WorkerLane from './WorkerLane.vue';

// Import extracted components
import SessionProgressBar from './JudgeSession/SessionProgressBar.vue';
import WorkerLaneGrid from './JudgeSession/WorkerLaneGrid.vue';
import SessionQueuePanel from './JudgeSession/SessionQueuePanel.vue';
import CurrentComparisonView from './JudgeSession/CurrentComparisonView.vue';
import ComparisonHistoryTable from './JudgeSession/ComparisonHistoryTable.vue';
import SingleWorkerFullscreenDialog from './JudgeSession/SingleWorkerFullscreenDialog.vue';
import MultiWorkerFullscreenDialog from './JudgeSession/MultiWorkerFullscreenDialog.vue';

// Import composables
import {
  WORKER_COLORS,
  PILLAR_CONFIG,
  STEP_DEFINITIONS,
  SCORE_CRITERIA,
  QUEUE_HEADERS,
  HISTORY_HEADERS,
  useSessionHelpers,
  useSessionState,
  useSessionApi,
  useStreamParsing,
  useSessionSocket,
  useFullscreen
} from './JudgeSession/composables';

const route = useRoute();
const router = useRouter();
const sessionId = route.params.id;

// Initialize composables
const helpers = useSessionHelpers();
const state = useSessionState(sessionId);
const api = useSessionApi(sessionId, state, helpers);
const parsing = useStreamParsing(state);
const socketHandler = useSessionSocket(sessionId, state, api, helpers);
const fullscreen = useFullscreen(state, api);

// Destructure state for template access
const {
  session,
  currentComparison,
  completedComparisons,
  queue,
  sessionHealth,
  loading,
  actionLoading,
  queueLoading,
  reconnecting,
  fullscreenMode,
  expandedPanels,
  autoScrollEnabled,
  streamDisplayMode,
  llmStreamContent,
  workerCount,
  workerStreams,
  multiWorkerFullscreenMode,
  multiWorkerDisplayMode,
  focusedWorkerId,
  streamOutput,
  fullscreenStreamOutput,
  // Computed
  progress,
  isStreaming,
  isActuallyRunning,
  showResumeButton,
  activeWorkerCount,
  sessionPillars,
  pillarPairs,
  allQueueItems,
  getMultiWorkerColSize,
  // Methods
  isPairActive
} = state;

// Destructure helpers for template access
const {
  getStatusColor,
  getStatusIcon,
  getStatusText,
  getConfidenceColor,
  getPillarName,
  getPillarIcon,
  getPillarColor,
  getQueueStatusColor,
  getQueueStatusIcon,
  getQueueStatusText,
  formatDate,
  formatCriterionName,
  getScoreColor,
  copyToClipboard
} = helpers;

// Destructure API methods
const {
  loadSession,
  loadQueue,
  loadWorkerPoolStatus
} = api;

// Destructure parsing methods
const {
  parsedStreamJson,
  parsedStreamSteps,
  getStepByKey,
  getWorkerParsedResult,
  getWorkerScoreA,
  getWorkerScoreB,
  getWorkerStep
} = parsing;

// Destructure socket methods
const {
  setupSocket,
  cleanupSocket,
  startPolling,
  stopPolling,
  reconnectToStream,
  handleStreamScroll,
  enableAutoScroll
} = socketHandler;

// Destructure fullscreen methods
const {
  openFullscreen: openFullscreenBase,
  closeFullscreen,
  openMultiWorkerFullscreen,
  closeMultiWorkerFullscreen,
  openWorkerFullscreen
} = fullscreen;

// Wrap openFullscreen to pass reconnectToStream
const openFullscreen = () => openFullscreenBase(reconnectToStream);

// Table headers
const queueHeaders = QUEUE_HEADERS;
const historyHeaders = HISTORY_HEADERS;

// Session control actions (wrap API methods to pass polling callbacks)
const startSession = () => api.startSession(startPolling);
const pauseSession = () => api.pauseSession(stopPolling);
const resumeSession = () => api.resumeSession(startPolling);
const refreshAll = () => api.refreshAll();

// Navigation
const navigateToResults = () => {
  router.push({ name: 'JudgeResults', params: { id: sessionId } });
};

// View comparison in detail
const viewComparison = (comparison) => {
  currentComparison.value = comparison;
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// Copy stream content to clipboard
const copyStreamToClipboard = () => copyToClipboard(llmStreamContent.value);

// Lifecycle
onMounted(async () => {
  await loadSession();
  setupSocket();
  if (session.value?.status === 'running') {
    startPolling();
  }
});

onUnmounted(() => {
  cleanupSocket();
});
</script>

<style scoped>
.judge-session {
  max-width: 1600px;
  margin: 0 auto;
}

.thread-container {
  height: 100%;
}

.thread-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.message-item {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.message-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.message-role {
  color: rgb(var(--v-theme-primary));
  text-transform: uppercase;
}

.message-content {
  white-space: pre-wrap;
  word-wrap: break-word;
}

.evaluation-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
}

.winner-card {
  animation: winnerPulse 1s ease-in-out;
}

@keyframes winnerPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.cot-step {
  padding: 12px;
  background-color: rgba(var(--v-theme-surface), 0.5);
  border-left: 3px solid rgb(var(--v-theme-primary));
  border-radius: 4px;
}

.json-preview {
  background-color: rgba(var(--v-theme-surface), 0.5);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.prompt-preview {
  background-color: rgba(var(--v-theme-info), 0.08);
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  font-family: 'Courier New', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 500px;
  overflow-y: auto;
}

.stream-output {
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.stream-output pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.thread-card {
  max-height: 500px;
  overflow-y: auto;
}

.history-table :deep(tbody tr) {
  cursor: pointer;
}

.history-table :deep(tbody tr:hover) {
  background-color: rgba(var(--v-theme-primary), 0.05);
}

/* Stream panel content - limit height to prevent overflow */
.stream-panel-content :deep(.v-expansion-panel-text__wrapper) {
  max-height: 500px;
  overflow-y: auto;
}

/* Stream output styles */
.stream-output-container {
  margin-top: 16px;
  position: relative;
}

.stream-pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
}

.cursor-blink {
  animation: blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
  font-weight: bold;
}

@keyframes blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

/* Formatted JSON output */
.formatted-json-output {
  border: 1px solid rgba(var(--v-theme-success), 0.3);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(var(--v-theme-success), 0.05) 0%, rgba(var(--v-theme-success), 0.02) 100%);
  max-height: 350px;
  overflow-y: auto;
}

.justification-text {
  background-color: rgba(var(--v-theme-surface), 0.8);
  padding: 12px;
  border-radius: 6px;
  font-style: italic;
  line-height: 1.6;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.criteria-scores :deep(.v-table) {
  background: transparent;
}

.criteria-scores :deep(th) {
  background-color: rgba(var(--v-theme-surface-variant), 0.5) !important;
  font-weight: bold;
}

.criteria-scores :deep(td),
.criteria-scores :deep(th) {
  padding: 8px 12px !important;
}

/* Pulsing live icon */
.pulse-icon {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.1);
  }
}

/* Fullscreen styles */
.fullscreen-card {
  height: 100vh;
  overflow: hidden;
}

.fullscreen-content {
  overflow: hidden;
}

.fullscreen-content .h-100 {
  height: 100%;
}

.thread-scroll {
  max-height: calc(100vh - 250px);
}

.stream-scroll {
  max-height: calc(100vh - 400px);
}

.stream-pre-fullscreen {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: rgb(var(--v-theme-on-surface));
}

.criteria-table-fullscreen {
  background: transparent !important;
}

.criteria-table-fullscreen th {
  background-color: rgba(var(--v-theme-surface-variant), 0.3) !important;
}

.bg-success-lighten-5 {
  background-color: rgba(var(--v-theme-success), 0.08) !important;
}

/* Fullscreen dialog transitions */
.fullscreen-dialog .v-card {
  border-radius: 0 !important;
}

/* Result display header - always visible */
.result-display-header {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.8) 0%, rgba(var(--v-theme-surface-variant), 0.4) 100%);
  min-height: 120px;
}

.winner-card-fullscreen {
  transition: all 0.3s ease;
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
}

/* Follow button - fixed at bottom right of stream container */
.follow-btn {
  position: sticky;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: bounce-in 0.3s ease-out;
}

@keyframes bounce-in {
  0% {
    transform: translateX(-50%) translateY(20px);
    opacity: 0;
  }
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

.position-relative {
  position: relative;
}

/* Formatted stream view styles */
.formatted-stream-view {
  padding: 8px;
}

.cot-steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cot-step-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface-variant), 0.6) 0%, rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid rgb(var(--v-theme-primary));
  transition: all 0.3s ease;
}

.cot-step-card.current-step {
  border-left-color: rgb(var(--v-theme-warning));
  background: linear-gradient(135deg, rgba(var(--v-theme-warning), 0.15) 0%, rgba(var(--v-theme-warning), 0.05) 100%);
  box-shadow: 0 2px 8px rgba(var(--v-theme-warning), 0.2);
}

.cot-step-header {
  font-size: 14px;
  color: rgb(var(--v-theme-on-surface));
}

.cot-step-content {
  color: rgba(var(--v-theme-on-surface), 0.85);
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.scores-section {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  padding: 16px;
}

.justification-section {
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
  padding: 16px;
}

.raw-fallback {
  padding: 8px;
}

/* Display mode toggle button styles */
.v-btn-toggle .v-btn {
  text-transform: none;
}

/* ============================================
   LIKERT SCALE STYLES
   ============================================ */
.likert-scales-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
  padding: 12px;
}

.likert-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.likert-label {
  width: 140px;
  flex-shrink: 0;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.likert-scale {
  display: flex;
  gap: 4px;
  align-items: center;
}

.likert-vs {
  width: 30px;
  text-align: center;
  flex-shrink: 0;
}

.likert-dot {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border: 2px solid rgba(var(--v-theme-on-surface), 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  position: relative;
}

.likert-dot.likert-pending {
  animation: likert-pulse 1.5s ease-in-out infinite;
}

.likert-dot.likert-active {
  transform: scale(1.1);
}

.likert-dot.likert-a-color {
  background: rgba(33, 150, 243, 0.8);
  border-color: rgb(33, 150, 243);
}

.likert-dot.likert-b-color {
  background: rgba(76, 175, 80, 0.8);
  border-color: rgb(76, 175, 80);
}

.likert-value {
  color: white;
  font-size: 10px;
  font-weight: bold;
}

@keyframes likert-pulse {
  0%, 100% {
    opacity: 0.3;
    transform: scale(1);
  }
  50% {
    opacity: 0.6;
    transform: scale(1.05);
  }
}

/* Winner highlight animation */
.winner-highlight {
  animation: winner-glow 2s ease-in-out infinite;
}

@keyframes winner-glow {
  0%, 100% {
    box-shadow: 0 0 5px rgba(var(--v-theme-success), 0.3);
  }
  50% {
    box-shadow: 0 0 20px rgba(var(--v-theme-success), 0.6);
  }
}

/* ============================================
   STRUCTURED STEPS STYLES
   ============================================ */
.structured-steps-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.structured-step {
  background: rgba(var(--v-theme-surface-variant), 0.4);
  border-radius: 8px;
  border-left: 4px solid rgba(var(--v-theme-on-surface), 0.2);
  overflow: hidden;
  transition: all 0.3s ease;
}

.structured-step.step-active {
  border-left-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.08);
}

.structured-step.step-streaming {
  border-left-color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.1);
  box-shadow: 0 2px 8px rgba(var(--v-theme-warning), 0.2);
}

.structured-step.step-pending {
  opacity: 0.6;
}

.step-header {
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
}

.step-content {
  padding: 0 16px 16px 16px;
}

.step-text {
  font-size: 13px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.9);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.step-placeholder {
  padding: 8px 16px 12px 16px;
  min-height: 32px;
}

/* ============================================
   MULTI-WORKER FULLSCREEN STYLES
   ============================================ */

.multi-worker-grid {
  overflow-y: auto;
}

.worker-col {
  display: flex;
  flex-direction: column;
}

.worker-fullscreen-card {
  transition: all 0.3s ease;
  min-height: 400px;
}

.worker-fullscreen-card.worker-streaming {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 15px rgba(var(--v-theme-warning), 0.3);
}

.worker-fullscreen-card.worker-active {
  border-color: rgb(var(--v-theme-primary));
}

.comparison-info {
  font-size: 12px;
}

/* Thread badges */
.thread-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  transition: all 0.3s ease;
}

.thread-badge.thread-a {
  background: rgba(33, 150, 243, 0.2);
  color: rgb(33, 150, 243);
  border: 2px solid rgba(33, 150, 243, 0.3);
}

.thread-badge.thread-b {
  background: rgba(76, 175, 80, 0.2);
  color: rgb(76, 175, 80);
  border: 2px solid rgba(76, 175, 80, 0.3);
}

.thread-badge.is-winner {
  transform: scale(1.2);
  box-shadow: 0 0 15px currentColor;
}

.thread-badge.thread-a.is-winner {
  background: rgb(33, 150, 243);
  color: white;
}

.thread-badge.thread-b.is-winner {
  background: rgb(76, 175, 80);
  color: white;
}

/* Likert scores fullscreen */
.likert-scores-fullscreen {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 12px;
  border-radius: 8px;
}

.likert-row-fullscreen {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.likert-row-fullscreen:last-child {
  margin-bottom: 0;
}

.criterion-label-full {
  width: 120px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.likert-dots-full {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 3px;
}

.dots-group-full {
  display: flex;
  gap: 3px;
}

.dot-full {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: all 0.2s ease;
}

.dots-group-full.dots-a .dot-full.dot-filled {
  background: rgb(33, 150, 243);
}

.dots-group-full.dots-b .dot-full.dot-filled {
  background: rgb(76, 175, 80);
}

.dot-full.dot-pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.score-divider-full {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-size: 12px;
  margin: 0 6px;
}

/* Analysis steps progress */
.analysis-steps-progress {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  padding: 8px;
  border-radius: 6px;
}

.steps-row {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.4);
  transition: all 0.2s ease;
}

.step-indicator.step-complete {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
}

.step-indicator.step-active {
  background: rgba(var(--v-theme-warning), 0.2);
  color: rgb(var(--v-theme-warning));
}

/* Justification fullscreen */
.justification-fullscreen {
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

/* Worker selector for focus view */
.worker-selector {
  display: flex;
  flex-direction: column;
}

.worker-selector-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.worker-selector-item:hover {
  background: rgba(var(--v-theme-surface-variant), 0.5);
}

.worker-selector-item.selected {
  background: rgba(var(--v-theme-primary), 0.15);
  border: 2px solid rgb(var(--v-theme-primary));
}

.worker-selector-item.streaming {
  background: rgba(var(--v-theme-warning), 0.15);
  border: 2px solid rgb(var(--v-theme-warning));
}

.worker-mini-info {
  flex: 1;
  min-width: 0;
}

/* Winner glow effect */
.winner-glow {
  box-shadow: 0 0 20px rgba(var(--v-theme-success), 0.4);
}

/* Likert scales large (focus view) */
.likert-scales-large {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.likert-row-large {
  display: flex;
  align-items: center;
  gap: 16px;
}

.criterion-label-large {
  width: 160px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.likert-visual-large {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 8px;
}

.score-side {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-side.score-a-side {
  flex-direction: row;
}

.score-side.score-b-side {
  flex-direction: row-reverse;
}

.score-dot-large {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: all 0.2s ease;
}

.score-side.score-a-side .score-dot-large.filled {
  background: rgb(33, 150, 243);
}

.score-side.score-b-side .score-dot-large.filled {
  background: rgb(76, 175, 80);
}

.score-dot-large.pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

.score-value {
  font-weight: bold;
  font-size: 16px;
  min-width: 24px;
  text-align: center;
}

.score-side.score-a-side .score-value {
  color: rgb(33, 150, 243);
}

.score-side.score-b-side .score-value {
  color: rgb(76, 175, 80);
}

.vs-label {
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 14px;
  padding: 0 8px;
}

/* Steps detailed (focus view) */
.steps-detailed {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-detailed {
  padding: 12px;
  border-radius: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  transition: all 0.2s ease;
}

.step-detailed.active {
  background: rgba(var(--v-theme-primary), 0.1);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.step-detailed.streaming {
  background: rgba(var(--v-theme-warning), 0.15);
  border-left: 3px solid rgb(var(--v-theme-warning));
}

.step-content-detailed {
  padding-left: 36px;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(var(--v-theme-on-surface), 0.85);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.result-summary {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 16px;
  border-radius: 8px;
}

/* ============================================
   ENHANCED DASHBOARD HEADER STYLES
   ============================================ */

.worker-pool-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.15);
  background: linear-gradient(135deg,
    rgba(var(--v-theme-surface), 0.95) 0%,
    rgba(var(--v-theme-surface-variant), 0.5) 100%);
}

.worker-pool-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.08) 0%,
    rgba(var(--v-theme-surface-variant), 0.3) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.1);
  padding: 16px 20px;
}

.header-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.header-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon-badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.2) 0%,
    rgba(var(--v-theme-primary), 0.1) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.2);
}

.header-title-text {
  display: flex;
  flex-direction: column;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.header-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(var(--v-theme-surface), 0.6);
  padding: 8px 12px;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Pillars Overview Bar */
.pillars-overview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 8px;
  flex-wrap: wrap;
}

.pillars-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pillars-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.pillar-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.2s ease;
  background: color-mix(in srgb, var(--pillar-color) 15%, transparent);
  color: var(--pillar-color);
  border: 1px solid var(--pillar-color);
}

.pillar-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background: color-mix(in srgb, var(--pillar-color) 25%, transparent);
}

.pairs-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.pairs-label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.pairs-progress {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.pair-chip {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
  background: rgba(var(--v-theme-surface-variant), 0.5);
  color: rgba(var(--v-theme-on-surface), 0.7);
  transition: all 0.2s ease;
}

.pair-chip.pair-active {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
  animation: pair-pulse 2s ease-in-out infinite;
}

@keyframes pair-pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(var(--v-theme-success), 0.3);
  }
  50% {
    box-shadow: 0 0 0 4px rgba(var(--v-theme-success), 0);
  }
}

.pair-vs {
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Worker Grid Container */
.worker-grid-container {
  padding: 16px;
}

/* Responsive adjustments */
@media (max-width: 960px) {
  .header-top-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-stats {
    width: 100%;
    justify-content: space-around;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .pillars-overview {
    flex-direction: column;
    align-items: flex-start;
  }

  .pairs-info {
    margin-left: 0;
    margin-top: 8px;
  }
}

/* ============================================
   FULLSCREEN HEADER STYLES
   ============================================ */

.fullscreen-header {
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.15) 0%,
    rgba(var(--v-theme-surface-variant), 0.5) 100%);
  border-bottom: 1px solid rgba(var(--v-theme-primary), 0.2);
  padding: 0;
}

.fullscreen-header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  gap: 16px;
}

.fullscreen-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fullscreen-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.fullscreen-icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg,
    rgba(var(--v-theme-primary), 0.25) 0%,
    rgba(var(--v-theme-primary), 0.1) 100%);
  border: 1px solid rgba(var(--v-theme-primary), 0.3);
}

.fullscreen-title-text {
  display: flex;
  flex-direction: column;
}

.fullscreen-title {
  font-size: 16px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.fullscreen-subtitle {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.fullscreen-header-stats {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(var(--v-theme-surface), 0.7);
  padding: 8px 16px;
  border-radius: 8px;
}

.fullscreen-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 50px;
}

.fullscreen-stat-value {
  font-size: 18px;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.fullscreen-stat-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.fullscreen-stat-divider {
  width: 1px;
  height: 30px;
  background: rgba(var(--v-theme-on-surface), 0.15);
}

.fullscreen-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fullscreen-mode-toggle {
  border-color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Pillar Progress Bar in Fullscreen */
.fullscreen-pillars-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: rgba(var(--v-theme-surface), 0.5);
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.05);
  gap: 16px;
}

.fullscreen-pillars-chips {
  display: flex;
  gap: 8px;
}

.fullscreen-pillar-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 600;
  background: var(--pillar-bg);
  color: var(--pillar-color);
  border: 1px solid var(--pillar-color);
  transition: all 0.2s ease;
}

.fullscreen-pillar-badge:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.fullscreen-progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  max-width: 400px;
}

.fullscreen-progress-text {
  font-size: 14px;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  min-width: 40px;
  text-align: right;
}

/* Enhanced Worker Cards in Fullscreen Grid */
.multi-worker-fullscreen-dialog .worker-fullscreen-card {
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.multi-worker-fullscreen-dialog .worker-fullscreen-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.multi-worker-fullscreen-dialog .worker-fullscreen-card.worker-streaming {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 20px rgba(var(--v-theme-warning), 0.3);
}

.multi-worker-fullscreen-dialog .worker-fullscreen-card.worker-active {
  border-color: rgba(var(--v-theme-primary), 0.5);
}

/* Responsive Fullscreen Header */
@media (max-width: 1200px) {
  .fullscreen-header-main {
    flex-wrap: wrap;
  }

  .fullscreen-header-stats {
    order: 3;
    width: 100%;
    justify-content: center;
    margin-top: 8px;
  }
}

@media (max-width: 768px) {
  .fullscreen-pillars-bar {
    flex-direction: column;
    gap: 12px;
  }

  .fullscreen-progress-container {
    max-width: 100%;
    width: 100%;
  }
}
</style>
