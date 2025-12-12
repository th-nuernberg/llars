/**
 * Session State Composable
 *
 * Manages all reactive state for JudgeSession component.
 */

import { ref, reactive, computed, watch } from 'vue';
import { PILLAR_CONFIG } from './useSessionConstants';

export function useSessionState(sessionId) {
  // Core session state
  const session = ref(null);
  const currentComparison = ref(null);
  const completedComparisons = ref([]);
  const queue = ref({ pending: [], current: null, stats: {} });

  // Robust progress tracking (event-based counting)
  // Instead of trusting reported values, we count completion events ourselves
  const completedCount = ref(0);      // Counted by us from events
  const confirmedTotal = ref(0);      // Total from API (doesn't change during session)
  const isCounterInitialized = ref(false);  // Track if we've initialized from API

  // Loading states
  const loading = ref(false);
  const actionLoading = ref(false);
  const queueLoading = ref(false);
  const reconnecting = ref(false);

  // UI state
  const fullscreenMode = ref(false);
  const expandedPanels = ref([]);
  const autoScrollEnabled = ref(true);
  const streamDisplayMode = ref('formatted'); // 'raw' or 'formatted'

  // Stream content
  const llmStreamContent = ref('');

  // Multi-worker state
  const workerCount = ref(1);
  const workerStreams = reactive({}); // { workerId: { content: '', comparison: null, isStreaming: false } }
  const workerPoolStatus = ref(null);

  // Multi-worker fullscreen state
  const multiWorkerFullscreenMode = ref(false);
  const multiWorkerDisplayMode = ref('grid'); // 'grid' or 'focus'
  const focusedWorkerId = ref(0);

  // Session Health State (for intelligent button logic)
  const sessionHealth = ref(null);

  // Element refs
  const streamOutput = ref(null);
  const fullscreenStreamOutput = ref(null);

  // Socket ref
  const socket = ref(null);

  // Computed: Progress percentage (uses event-based counting)
  const progress = computed(() => {
    const total = confirmedTotal.value || session.value?.total_comparisons || 0;
    if (!total) return 0;
    // Clamp to 100% max
    return Math.min(100, (completedCount.value / total) * 100);
  });

  // Initialize counter from API data (called once when session loads)
  const initializeProgressFromApi = (completed, total) => {
    console.log(`[Progress] initializeProgressFromApi called with: completed=${completed}, total=${total}`);

    // Handle null/undefined by converting to 0
    const safeCompleted = typeof completed === 'number' ? completed : 0;
    const safeTotal = typeof total === 'number' ? total : 0;

    // Always update total from API (even if 0, to track that we tried)
    if (safeTotal > 0) {
      confirmedTotal.value = safeTotal;
      console.log(`[Progress] Set confirmedTotal to ${safeTotal}`);
    }

    // Only initialize completed count if not already initialized,
    // or if API value is higher (handles page refresh mid-session)
    if (!isCounterInitialized.value || safeCompleted > completedCount.value) {
      completedCount.value = safeCompleted;
      isCounterInitialized.value = true;
      console.log(`[Progress] Initialized from API: ${safeCompleted}/${safeTotal}`);
    }
  };

  // Increment counter when a comparison completes (called on socket event)
  const incrementCompleted = () => {
    // Use confirmedTotal or fall back to session.total_comparisons
    const total = confirmedTotal.value || session.value?.total_comparisons || 0;

    // Always increment if we don't have a total yet (defensive)
    // or if we haven't reached the total
    if (total === 0 || completedCount.value < total) {
      completedCount.value++;
      console.log(`[Progress] Incremented: ${completedCount.value}/${total} (confirmedTotal: ${confirmedTotal.value})`);
    } else {
      console.log(`[Progress] Already at max: ${completedCount.value}/${total}`);
    }
  };

  // Reset progress tracking (for new session or session restart)
  const resetProgressTracking = () => {
    completedCount.value = 0;
    confirmedTotal.value = 0;
    isCounterInitialized.value = false;
    console.log('[Progress] Tracking reset');
  };

  // Computed: Is LLM currently streaming
  const isStreaming = computed(() => {
    return currentComparison.value?.llm_status === 'running';
  });

  // Computed: Is the session actually running (workers active)?
  const isActuallyRunning = computed(() => {
    if (session.value?.status !== 'running') return false;
    return sessionHealth.value?.workers_running === true;
  });

  // Computed: Should we show the Resume button?
  const showResumeButton = computed(() => {
    const status = session.value?.status;
    if (status === 'paused') return true;
    if (status === 'running' && sessionHealth.value?.needs_recovery) return true;
    return false;
  });

  // Computed: Active worker count
  const activeWorkerCount = computed(() => {
    let count = 0;
    for (let i = 0; i < workerCount.value; i++) {
      if (workerStreams[i]?.comparison || workerStreams[i]?.isStreaming) {
        count++;
      }
    }
    return count;
  });

  // Computed: Session pillars from session data
  const sessionPillars = computed(() => {
    if (!session.value?.pillar_ids) return [];
    return session.value.pillar_ids.map(id => ({
      id,
      name: PILLAR_CONFIG[id]?.name || `Säule ${id}`,
      short: PILLAR_CONFIG[id]?.short || `S${id}`,
      icon: PILLAR_CONFIG[id]?.icon || 'mdi-help-circle'
    }));
  });

  // Computed: Pillar pairs from session pillars
  const pillarPairs = computed(() => {
    const pillars = sessionPillars.value;
    const pairs = [];
    for (let i = 0; i < pillars.length; i++) {
      for (let j = i + 1; j < pillars.length; j++) {
        pairs.push({
          key: `${pillars[i].id}_${pillars[j].id}`,
          a: pillars[i].short,
          b: pillars[j].short,
          pillar_a: pillars[i].id,
          pillar_b: pillars[j].id
        });
      }
    }
    return pairs;
  });

  // Computed: Combine current and pending items for queue display
  const allQueueItems = computed(() => {
    const items = [];
    if (queue.value.current) {
      items.push({
        ...queue.value.current,
        status: 'running'
      });
    }
    if (queue.value.pending) {
      items.push(...queue.value.pending);
    }
    return items.sort((a, b) => a.queue_position - b.queue_position);
  });

  // Computed: Multi-worker column size
  const getMultiWorkerColSize = computed(() => {
    if (workerCount.value <= 2) return 6;
    if (workerCount.value <= 4) return 6;
    return 4;
  });

  // Computed: Selected worker's comparison (for Live tab)
  const selectedWorkerComparison = computed(() => {
    if (workerCount.value <= 1) {
      return currentComparison.value;
    }
    return workerStreams[focusedWorkerId.value]?.comparison || null;
  });

  // Computed: Selected worker's stream content (for Live tab)
  const selectedWorkerStreamContent = computed(() => {
    if (workerCount.value <= 1) {
      return llmStreamContent.value;
    }
    return workerStreams[focusedWorkerId.value]?.content || '';
  });

  // Computed: Is selected worker currently streaming
  const isSelectedWorkerStreaming = computed(() => {
    if (workerCount.value <= 1) {
      return isStreaming.value;
    }
    return workerStreams[focusedWorkerId.value]?.isStreaming || false;
  });

  // Check if a pair is currently being worked on
  const isPairActive = (pair) => {
    for (let i = 0; i < workerCount.value; i++) {
      const comp = workerStreams[i]?.comparison;
      if (comp) {
        if ((comp.pillar_a === pair.pillar_a && comp.pillar_b === pair.pillar_b) ||
            (comp.pillar_a === pair.pillar_b && comp.pillar_b === pair.pillar_a)) {
          return true;
        }
      }
    }
    return false;
  };

  // Initialize worker streams for multi-worker mode
  const initializeWorkerStreams = (count) => {
    for (let i = 0; i < count; i++) {
      if (!workerStreams[i]) {
        workerStreams[i] = {
          content: '',
          comparison: null,
          isStreaming: false
        };
      }
    }
  };

  return {
    // Session state
    session,
    currentComparison,
    completedComparisons,
    queue,
    sessionHealth,

    // Robust progress tracking (event-based counting)
    completedCount,
    confirmedTotal,

    // Loading states
    loading,
    actionLoading,
    queueLoading,
    reconnecting,

    // UI state
    fullscreenMode,
    expandedPanels,
    autoScrollEnabled,
    streamDisplayMode,
    llmStreamContent,

    // Multi-worker state
    workerCount,
    workerStreams,
    workerPoolStatus,
    multiWorkerFullscreenMode,
    multiWorkerDisplayMode,
    focusedWorkerId,

    // Element refs
    streamOutput,
    fullscreenStreamOutput,
    socket,

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
    isPairActive,
    initializeWorkerStreams,
    initializeProgressFromApi,
    incrementCompleted,
    resetProgressTracking
  };
}
