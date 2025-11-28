/**
 * Session State Composable
 *
 * Manages all reactive state for JudgeSession component.
 */

import { ref, reactive, computed } from 'vue';
import { PILLAR_CONFIG } from './useSessionConstants';

export function useSessionState(sessionId) {
  // Core session state
  const session = ref(null);
  const currentComparison = ref(null);
  const completedComparisons = ref([]);
  const queue = ref({ pending: [], current: null, stats: {} });

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

  // Computed: Progress percentage
  const progress = computed(() => {
    if (!session.value || !session.value.total_comparisons) return 0;
    return (session.value.completed_comparisons / session.value.total_comparisons) * 100;
  });

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

    // Methods
    isPairActive,
    initializeWorkerStreams
  };
}
