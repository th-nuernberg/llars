<template>
  <div class="judge-session-page">
    <!-- Loading State -->
    <div v-if="loading && !session" class="loading-container">
      <v-progress-circular indeterminate color="primary" size="48"></v-progress-circular>
      <p class="mt-4 text-medium-emphasis">Session wird geladen...</p>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Resizable Two-Panel Layout -->
      <div ref="containerRef" class="main-content">
        <!-- Left Panel: Session Info + Workers + Queue -->
        <div class="left-panel" :style="leftPanelStyle()">
          <div class="panel-header">
            <div class="d-flex align-center">
              <v-btn
                icon="mdi-arrow-left"
                variant="text"
                size="small"
                @click="$router.push({ name: 'JudgeOverview' })"
              ></v-btn>
              <div class="ml-2">
                <h2 class="panel-title">{{ session?.session_name || 'Judge Session' }}</h2>
                <div class="d-flex align-center gap-2">
                  <v-chip
                    :color="getStatusColor(session?.status)"
                    :prepend-icon="getStatusIcon(session?.status)"
                    size="x-small"
                  >
                    {{ getStatusText(session?.status) }}
                  </v-chip>
                  <span class="text-caption text-medium-emphasis">ID: {{ sessionId }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="panel-content-left">
            <!-- Session Progress (compact, fixed height) -->
            <div class="progress-section">
              <SessionProgressBar
                :session="session"
                :progress="progress"
                :worker-count="workerCount"
                :format-date="formatDate"
                :completed-count="completedCount"
                :confirmed-total="confirmedTotal"
              />
            </div>

            <!-- Queue Panel (fills remaining space) -->
            <div class="queue-section">
              <SessionQueuePanel
                :queue="queue"
                :all-queue-items="allQueueItems"
                :headers="queueHeaders"
                :loading="queueLoading"
                :get-queue-status-color="getQueueStatusColor"
                :get-queue-status-icon="getQueueStatusIcon"
                :get-queue-status-text="getQueueStatusText"
                compact
                @refresh="loadQueue"
              />
            </div>
          </div>
        </div>

        <!-- Resize Divider -->
        <div
          class="resize-divider"
          :class="{ resizing: isResizing }"
          @mousedown="startResize"
        >
          <div class="resize-handle"></div>
        </div>

        <!-- Right Panel: Tab-based navigation -->
        <div class="right-panel" :style="rightPanelStyle()">
          <!-- Tab Navigation -->
          <div class="panel-header tabs-header">
            <v-tabs v-model="activeTab" density="compact" color="primary">
              <v-tab value="live" :disabled="session?.status === 'completed'">
                <LIcon start size="18">mdi-play-circle</LIcon>
                Live
                <v-chip
                  v-if="workerCount > 1 && activeWorkerCount > 0"
                  size="x-small"
                  color="warning"
                  class="ml-2 pulse-chip"
                >
                  <LIcon size="10" class="mr-1">mdi-circle</LIcon>
                  {{ activeWorkerCount }}
                </v-chip>
                <v-chip
                  v-else-if="isStreaming"
                  size="x-small"
                  color="success"
                  class="ml-2 pulse-chip"
                >
                  <LIcon size="10" class="mr-1">mdi-circle</LIcon>
                </v-chip>
              </v-tab>
              <v-tab value="history">
                <LIcon start size="18">mdi-history</LIcon>
                Verlauf
                <v-chip size="x-small" class="ml-2">{{ completedComparisons.length }}</v-chip>
              </v-tab>
            </v-tabs>
            <v-btn
              icon="mdi-refresh"
              variant="text"
              size="small"
              @click="refreshAll"
              :loading="loading"
              title="Aktualisieren"
            ></v-btn>
          </div>

          <!-- Tab Content -->
          <v-window v-model="activeTab" class="tab-content">
            <!-- Live Tab: Current Comparison -->
            <v-window-item value="live" class="tab-window-item">
              <!-- Multi-Worker View with Toggle -->
              <div v-if="workerCount > 1" class="live-multi-worker-container">
                <!-- View Toggle Header -->
                <div class="live-view-header">
                  <div class="live-view-info">
                    <LIcon size="18" class="mr-2">mdi-account-group</LIcon>
                    <span class="live-view-title">{{ activeWorkerCount }}/{{ workerCount }} Worker aktiv</span>
                    <v-chip
                      v-if="activeWorkerCount > 0"
                      size="x-small"
                      color="secondary"
                      class="ml-2"
                    >
                      {{ activeWorkerCount }} streaming
                    </v-chip>
                  </div>
                  <div class="live-view-actions">
                    <v-btn-toggle v-model="liveViewMode" density="compact" mandatory color="primary">
                      <v-btn value="detailed" size="small" variant="text" title="Detaillierte Ansicht">
                        <LIcon size="18">mdi-view-grid</LIcon>
                      </v-btn>
                      <v-btn value="compact" size="small" variant="text" title="Kompakte Ansicht">
                        <LIcon size="18">mdi-view-list</LIcon>
                      </v-btn>
                    </v-btn-toggle>
                    <v-btn
                      icon="mdi-fullscreen"
                      variant="text"
                      size="small"
                      @click="openUnifiedFullscreen('live-multi')"
                      title="Vollbild"
                    ></v-btn>
                  </div>
                </div>

                <!-- Detailed View: WorkerLane Grid -->
                <div v-if="liveViewMode === 'detailed'" class="live-worker-grid">
                  <v-row>
                    <v-col
                      v-for="i in workerCount"
                      :key="i - 1"
                      :cols="workerCount <= 2 ? 6 : (workerCount <= 3 ? 4 : 3)"
                    >
                      <WorkerLane
                        :worker-id="i - 1"
                        :current-comparison="workerStreams[i - 1]?.comparison"
                        :stream-content="workerStreams[i - 1]?.content || ''"
                        :is-streaming="workerStreams[i - 1]?.isStreaming || false"
                        @open-fullscreen="openUnifiedFullscreen('live-multi')"
                      />
                    </v-col>
                  </v-row>
                </div>

                <!-- Compact View: MultiWorkerDashboard -->
                <div v-else class="live-worker-compact">
                  <MultiWorkerDashboard
                    :worker-count="workerCount"
                    :worker-streams="workerStreams"
                    :session="session"
                    :score-criteria="SCORE_CRITERIA"
                    :get-worker-parsed-result="getWorkerParsedResult"
                    :get-worker-score-a="getWorkerScoreA"
                    :get-worker-score-b="getWorkerScoreB"
                    @open-fullscreen="openUnifiedFullscreen('live-multi')"
                    @view-worker="focusWorker"
                  />
                </div>
              </div>

              <!-- Single Worker View -->
              <div v-else class="comparison-section">
                <ComparisonViewer
                  v-if="selectedWorkerComparison"
                  :comparison="selectedWorkerComparison"
                  :session="session"
                  :is-streaming="isSelectedWorkerStreaming"
                  :llm-stream-content="selectedWorkerStreamContent"
                  :auto-scroll-enabled="autoScrollEnabled"
                  mode="live"
                  @open-fullscreen="openUnifiedFullscreen('live-single')"
                  @stream-scroll="handleStreamScroll"
                  @enable-auto-scroll="enableAutoScroll"
                />
                <div v-else class="empty-state">
                  <LIcon size="48" color="grey">mdi-compare-horizontal</LIcon>
                  <p class="mt-2 text-medium-emphasis">Kein aktiver Vergleich</p>
                  <p class="text-caption text-medium-emphasis">
                    {{ session?.status === 'completed' ? 'Session abgeschlossen. Siehe Verlauf.' : 'Starten Sie die Session um Vergleiche zu generieren.' }}
                  </p>
                </div>
              </div>
            </v-window-item>

            <!-- History Tab: Completed Comparisons -->
            <v-window-item value="history" class="tab-window-item">
              <HistoryTab
                :comparisons="completedComparisons"
                :loading="loading"
                @view-detail="viewHistoricalComparison"
                @view-fullscreen="openHistoricalFullscreen"
                @refresh="loadCompletedComparisons"
              />
            </v-window-item>
          </v-window>
        </div>
      </div>

      <!-- Action Bar (fixed at bottom) -->
      <div class="action-bar">
        <!-- Recovery Warning -->
        <v-chip
          v-if="sessionHealth?.needs_recovery"
          color="warning"
          size="small"
          prepend-icon="mdi-alert"
          class="mr-2"
        >
          Wiederherstellung nötig
        </v-chip>

        <v-spacer></v-spacer>

        <!-- Action Buttons -->
        <div class="d-flex gap-2 align-center">
          <!-- START -->
          <LBtn
            v-if="session?.status === 'created' || session?.status === 'queued'"
            variant="primary"
            prepend-icon="mdi-play"
            @click="startSession"
            :loading="actionLoading"
          >
            Starten
          </LBtn>

          <!-- PAUSE -->
          <LBtn
            v-if="isActuallyRunning"
            variant="accent"
            prepend-icon="mdi-pause"
            @click="pauseSession"
            :loading="actionLoading"
          >
            Pause
          </LBtn>

          <!-- RESUME/RECOVER -->
          <LBtn
            v-if="showResumeButton"
            :variant="sessionHealth?.needs_recovery ? 'danger' : 'secondary'"
            :prepend-icon="sessionHealth?.needs_recovery ? 'mdi-restart-alert' : 'mdi-play'"
            @click="resumeSession"
            :loading="actionLoading"
          >
            {{ sessionHealth?.needs_recovery ? 'Wiederherstellen' : 'Fortsetzen' }}
          </LBtn>

          <!-- RESULTS -->
          <LBtn
            v-if="session?.status === 'completed'"
            variant="primary"
            prepend-icon="mdi-chart-box"
            @click="navigateToResults"
          >
            Ergebnisse
          </LBtn>
        </div>
      </div>
    </template>

    <!-- Unified Fullscreen Dialog (replaces Single + Multi Worker dialogs) -->
    <UnifiedFullscreenDialog
    v-model="unifiedFullscreenOpen"
    :mode="fullscreenMode"
    :session="session"
    :progress="progress"
    :current-comparison="fullscreenComparison"
    :is-streaming="isStreaming"
    :llm-stream-content="llmStreamContent"
    :auto-scroll-enabled="autoScrollEnabled"
    :worker-count="workerCount"
    :worker-streams="workerStreams"
    :focused-worker-id="focusedWorkerId"
    :score-criteria="SCORE_CRITERIA"
    :step-definitions="STEP_DEFINITIONS"
    :get-worker-parsed-result="getWorkerParsedResult"
    :get-worker-score-a="getWorkerScoreA"
    :get-worker-score-b="getWorkerScoreB"
    :get-worker-step="getWorkerStep"
    :get-step-by-key="getStepByKey"
    :get-status-color="getStatusColor"
    :get-status-icon="getStatusIcon"
    :get-status-text="getStatusText"
    :get-confidence-color="getConfidenceColor"
    :completed-count="completedCount"
    :confirmed-total="confirmedTotal"
    @close="closeUnifiedFullscreen"
    @stream-scroll="handleStreamScroll"
    @enable-auto-scroll="enableAutoScroll"
    @focus-worker="focusWorker"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// Import extracted components
import SessionProgressBar from './JudgeSession/SessionProgressBar.vue';
import SessionQueuePanel from './JudgeSession/SessionQueuePanel.vue';
import WorkerLane from './WorkerLane.vue';

// Import new unified components
import ComparisonViewer from './JudgeSession/viewers/ComparisonViewer.vue';
import MultiWorkerDashboard from './JudgeSession/viewers/MultiWorkerDashboard.vue';
import HistoryTab from './JudgeSession/tabs/HistoryTab.vue';
import UnifiedFullscreenDialog from './JudgeSession/fullscreen/UnifiedFullscreenDialog.vue';

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
import { usePanelResize } from '@/composables/usePanelResize';

const route = useRoute();
const router = useRouter();
const sessionId = route.params.id;

// Initialize panel resize composable
const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 40,
  minLeftPercent: 25,
  maxLeftPercent: 60,
  storageKey: 'judge-session-panel-width'
});

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
  expandedPanels,
  autoScrollEnabled,
  streamDisplayMode,
  llmStreamContent,
  workerCount,
  workerStreams,
  focusedWorkerId,
  streamOutput,
  fullscreenStreamOutput,
  // Robust progress tracking (event-based counting)
  completedCount,
  confirmedTotal,
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
  selectedWorkerComparison,
  selectedWorkerStreamContent,
  isSelectedWorkerStreaming,
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
  loadWorkerPoolStatus,
  loadCompletedComparisons
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
  openMultiWorkerFullscreen,
  closeMultiWorkerFullscreen,
  openWorkerFullscreen
} = fullscreen;

// Table headers
const queueHeaders = QUEUE_HEADERS;

// ============================================
// TAB-BASED NAVIGATION STATE
// ============================================
const activeTab = ref('live');  // 'live' or 'history'
const liveViewMode = ref('detailed');  // 'detailed' (WorkerLane grid) or 'compact' (Dashboard)

// ============================================
// UNIFIED FULLSCREEN STATE
// ============================================
const unifiedFullscreenOpen = ref(false);
const fullscreenMode = ref('live-single');  // 'live-single', 'live-multi', 'historical'
const fullscreenComparison = ref(null);     // Comparison to show in fullscreen

// Open unified fullscreen dialog
const openUnifiedFullscreen = (mode) => {
  fullscreenMode.value = mode;
  if (mode === 'live-single') {
    fullscreenComparison.value = currentComparison.value;
  } else if (mode === 'live-multi') {
    fullscreenComparison.value = null;
  }
  unifiedFullscreenOpen.value = true;
};

// Close unified fullscreen dialog
const closeUnifiedFullscreen = () => {
  unifiedFullscreenOpen.value = false;
  fullscreenComparison.value = null;
};

// View historical comparison in detail (switches to live tab with detail view)
const viewHistoricalComparison = (comparison) => {
  fullscreenMode.value = 'historical';
  fullscreenComparison.value = comparison;
  unifiedFullscreenOpen.value = true;
};

// Open historical comparison in fullscreen
const openHistoricalFullscreen = (comparison) => {
  fullscreenMode.value = 'historical';
  fullscreenComparison.value = comparison;
  unifiedFullscreenOpen.value = true;
};

// Focus on a specific worker (from dashboard or selector)
const focusWorker = (workerId) => {
  focusedWorkerId.value = workerId;
  // If in fullscreen, keep it open, otherwise switch to Live tab
  if (!unifiedFullscreenOpen.value) {
    activeTab.value = 'live';
  }
};

// Session control actions (wrap API methods to pass polling callbacks)
const startSession = () => api.startSession(startPolling);
const pauseSession = () => api.pauseSession(stopPolling);
const resumeSession = () => api.resumeSession(startPolling);
const refreshAll = () => api.refreshAll();

// Navigation
const navigateToResults = () => {
  router.push({ name: 'JudgeResults', params: { id: sessionId } });
};

// Copy stream content to clipboard
const copyStreamToClipboard = () => copyToClipboard(llmStreamContent.value);

// Lifecycle
onMounted(async () => {
  console.log('[JudgeSession] Mounted, loading session...');
  await loadSession();
  console.log('[JudgeSession] Session loaded, setting up socket...');
  setupSocket();
  if (session.value?.status === 'running') {
    console.log('[JudgeSession] Session is running, starting polling');
    startPolling();
  }
  // Set initial tab based on session status
  if (session.value?.status === 'completed') {
    activeTab.value = 'history';
  }
  console.log('[JudgeSession] Mount complete');
});

onUnmounted(() => {
  console.log('[JudgeSession] Unmounting, cleaning up socket...');
  cleanupSocket();
  console.log('[JudgeSession] Cleanup complete');
});
</script>

<style scoped>
/* Import extracted styles */
@import './JudgeSession/styles/JudgeSession.css';
</style>
