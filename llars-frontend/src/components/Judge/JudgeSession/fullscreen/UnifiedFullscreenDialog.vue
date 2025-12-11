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
              <span class="stat-value">{{ session.completed_comparisons || 0 }}</span>
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
              <span class="stat-value">{{ session.total_comparisons || 0 }}</span>
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
            <v-btn value="grid" size="small" variant="text" title="Grid">
              <v-icon size="18">mdi-view-grid</v-icon>
            </v-btn>
            <v-btn value="focus" size="small" variant="text" title="Fokus">
              <v-icon size="18">mdi-focus-field</v-icon>
            </v-btn>
          </v-btn-toggle>

          <v-chip v-if="mode.startsWith('live')" color="warning" size="small" class="pulse-chip">
            <v-icon start size="14">mdi-broadcast</v-icon>
            Live
          </v-chip>
        </div>
      </div>

      <!-- Content -->
      <div class="fullscreen-content">
        <!-- Single Comparison View (Live or Historical) -->
        <template v-if="mode === 'live-single' || mode === 'historical'">
          <div class="single-view">
            <!-- Three Column Layout -->
            <div class="comparison-layout">
              <!-- Thread A -->
              <div class="thread-panel thread-a">
                <div class="thread-header">
                  <v-chip color="blue" variant="flat" prepend-icon="mdi-alpha-a-circle">
                    {{ comparison?.pillar_a_name || 'Thread A' }}
                  </v-chip>
                  <v-chip v-if="comparison?.winner === 'A'" color="warning" size="small" prepend-icon="mdi-trophy">
                    Gewinner
                  </v-chip>
                </div>
                <div class="thread-messages">
                  <div v-for="(msg, idx) in comparison?.thread_a_messages || []" :key="idx" class="message-item">
                    <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
                      <v-icon size="14" class="mr-1">
                        {{ msg.role === 'assistant' ? 'mdi-message-reply' : 'mdi-account' }}
                      </v-icon>
                      {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                    </div>
                    <div class="message-text">{{ msg.content }}</div>
                  </div>
                </div>
              </div>

              <!-- Center: Evaluation -->
              <div class="evaluation-panel">
                <div class="eval-header">
                  <v-icon
                    :color="comparison?.winner ? 'success' : (isStreaming ? 'warning' : 'grey')"
                    size="40"
                    :class="{ 'rotating': isStreaming && !comparison?.winner }"
                  >
                    {{ comparison?.winner ? 'mdi-check-circle' : (isStreaming ? 'mdi-loading' : 'mdi-clock-outline') }}
                  </v-icon>
                </div>

                <!-- Winner Display -->
                <div v-if="comparison?.winner" class="winner-display" :class="'winner-' + comparison.winner.toLowerCase()">
                  <v-icon size="48" color="warning">mdi-trophy</v-icon>
                  <div class="winner-letter">{{ comparison.winner }}</div>
                  <div v-if="comparison.confidence_score" class="confidence-badge">
                    {{ Math.round(comparison.confidence_score * 100) }}%
                  </div>
                </div>

                <!-- Score Table -->
                <div v-if="parsedResult?.criteria_scores" class="scores-table">
                  <div v-for="(scores, criterion) in parsedResult.criteria_scores" :key="criterion" class="score-row">
                    <span class="score-label">{{ formatCriterionName(criterion) }}</span>
                    <div class="score-values">
                      <span class="score-a" :class="{ 'is-higher': scores.score_a > scores.score_b }">
                        {{ scores.score_a }}
                      </span>
                      <span class="score-divider">:</span>
                      <span class="score-b" :class="{ 'is-higher': scores.score_b > scores.score_a }">
                        {{ scores.score_b }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Thread B -->
              <div class="thread-panel thread-b">
                <div class="thread-header">
                  <v-chip color="green" variant="flat" prepend-icon="mdi-alpha-b-circle">
                    {{ comparison?.pillar_b_name || 'Thread B' }}
                  </v-chip>
                  <v-chip v-if="comparison?.winner === 'B'" color="warning" size="small" prepend-icon="mdi-trophy">
                    Gewinner
                  </v-chip>
                </div>
                <div class="thread-messages">
                  <div v-for="(msg, idx) in comparison?.thread_b_messages || []" :key="idx" class="message-item">
                    <div class="message-role" :class="msg.role === 'assistant' ? 'role-counsellor' : 'role-client'">
                      <v-icon size="14" class="mr-1">
                        {{ msg.role === 'assistant' ? 'mdi-message-reply' : 'mdi-account' }}
                      </v-icon>
                      {{ msg.role === 'assistant' ? 'BERATER' : 'RATSUCHENDE' }}
                    </div>
                    <div class="message-text">{{ msg.content }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Stream/Analysis Section -->
            <div class="stream-panel">
              <div class="stream-header">
                <div class="stream-header-left">
                  <v-icon size="18" :class="{ 'rotating': isStreaming }">
                    {{ isStreaming ? 'mdi-loading' : 'mdi-robot' }}
                  </v-icon>
                  <span class="stream-title">LLM Analyse</span>
                  <v-chip size="x-small" :color="isStreaming ? 'warning' : 'success'">
                    {{ isStreaming ? 'Streamt...' : 'Abgeschlossen' }}
                  </v-chip>
                </div>
                <div class="stream-header-right">
                  <v-btn-toggle v-model="streamViewMode" density="compact" mandatory>
                    <v-btn value="formatted" size="x-small" variant="text">Formatiert</v-btn>
                    <v-btn value="raw" size="x-small" variant="text">Raw</v-btn>
                  </v-btn-toggle>
                </div>
              </div>

              <div class="stream-content" ref="streamRef">
                <!-- Formatted View -->
                <template v-if="streamViewMode === 'formatted' && parsedResult">
                  <div class="formatted-analysis">
                    <!-- Chain of Thought -->
                    <div v-if="parsedResult.chain_of_thought" class="cot-section">
                      <div
                        v-for="(step, key) in parsedResult.chain_of_thought"
                        :key="key"
                        class="cot-step"
                      >
                        <div class="cot-header">
                          <v-icon size="16" color="primary">mdi-thought-bubble</v-icon>
                          <span>{{ formatStepName(key) }}</span>
                        </div>
                        <div class="cot-content">{{ step }}</div>
                      </div>
                    </div>

                    <!-- Justification -->
                    <div v-if="parsedResult.final_justification" class="justification-section">
                      <div class="justification-header">
                        <v-icon size="16">mdi-gavel</v-icon>
                        <span>Begründung</span>
                      </div>
                      <div class="justification-content">{{ parsedResult.final_justification }}</div>
                    </div>
                  </div>
                </template>

                <!-- Raw View -->
                <template v-else>
                  <pre class="stream-pre">{{ streamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
                </template>
              </div>
            </div>
          </div>
        </template>

        <!-- Multi-Worker View -->
        <template v-else-if="mode === 'live-multi'">
          <div class="multi-view" :class="multiViewMode">
            <!-- Grid View -->
            <template v-if="multiViewMode === 'grid'">
              <div class="workers-grid">
                <div
                  v-for="i in workerCount"
                  :key="i - 1"
                  class="worker-card-full"
                  :class="{
                    'is-streaming': workerStreams[i - 1]?.isStreaming,
                    'has-result': getWorkerResult(i - 1)?.winner,
                    'is-idle': !workerStreams[i - 1]?.comparison,
                    'is-focused': localFocusedWorkerId === (i - 1)
                  }"
                  @click="localFocusedWorkerId = (i - 1)"
                >
                  <!-- Header -->
                  <div class="wc-header" :style="{ '--worker-color': WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
                    <div class="wc-badge" :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
                      W{{ i }}
                    </div>
                    <div v-if="workerStreams[i - 1]?.comparison" class="wc-pillars">
                      <span class="pillar-a">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }}</span>
                      <v-icon size="14">mdi-arrow-left-right</v-icon>
                      <span class="pillar-b">{{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}</span>
                    </div>
                    <span v-else class="idle-label">Idle</span>
                    <v-icon
                      v-if="workerStreams[i - 1]?.isStreaming"
                      size="16"
                      color="warning"
                      class="streaming-icon"
                    >mdi-circle</v-icon>
                  </div>

                  <div class="wc-body">
                    <template v-if="workerStreams[i - 1]?.comparison">
                      <!-- Winner & Confidence Row -->
                      <div class="wc-result-row">
                        <div class="wc-winner-section">
                          <span class="wc-label">Gewinner:</span>
                          <span
                            class="wc-winner"
                            :class="{
                              'winner-a': getWorkerResult(i - 1)?.winner === 'A',
                              'winner-b': getWorkerResult(i - 1)?.winner === 'B',
                              'winner-tie': getWorkerResult(i - 1)?.winner === 'TIE',
                              'pending': !getWorkerResult(i - 1)?.winner
                            }"
                          >
                            {{ getWorkerResult(i - 1)?.winner || '?' }}
                          </span>
                        </div>
                        <div class="wc-confidence-section">
                          <span class="wc-label">Konfidenz:</span>
                          <span class="wc-confidence-value" :class="{ 'has-value': getWorkerResult(i - 1)?.confidence }">
                            {{ getWorkerResult(i - 1)?.confidence ? Math.round(getWorkerResult(i - 1).confidence * 100) + '%' : '-' }}
                          </span>
                        </div>
                      </div>

                      <!-- Scores Section (Likert Dots) -->
                      <div class="wc-scores-section">
                        <div class="wc-scores-header">
                          <span class="wc-section-title">Bewertungen</span>
                        </div>
                        <div class="wc-scores-grid">
                          <div
                            v-for="criterion in CRITERIA_LIST"
                            :key="criterion.key"
                            class="wc-score-row"
                          >
                            <span class="wc-score-label">{{ criterion.short }}</span>
                            <div class="wc-score-dots">
                              <div class="wc-dots-group dots-a">
                                <span
                                  v-for="n in 5"
                                  :key="`a-${n}`"
                                  class="wc-dot"
                                  :class="{
                                    'filled': getWorkerScoreForCriterion(i - 1, criterion.key, 'a') >= n,
                                    'pending': !getWorkerResult(i - 1)?.criteria_scores
                                  }"
                                ></span>
                              </div>
                              <span class="wc-score-vs">:</span>
                              <div class="wc-dots-group dots-b">
                                <span
                                  v-for="n in 5"
                                  :key="`b-${n}`"
                                  class="wc-dot"
                                  :class="{
                                    'filled': getWorkerScoreForCriterion(i - 1, criterion.key, 'b') >= n,
                                    'pending': !getWorkerResult(i - 1)?.criteria_scores
                                  }"
                                ></span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <!-- Analysis Steps Progress -->
                      <div class="wc-steps-section">
                        <div class="wc-steps-header">
                          <span class="wc-section-title">Analyse-Schritte</span>
                        </div>
                        <div class="wc-steps-bar">
                          <div
                            v-for="step in ANALYSIS_STEPS"
                            :key="step.key"
                            class="wc-step-indicator"
                            :class="{
                              'completed': isStepCompleted(i - 1, step.key),
                              'active': isStepActive(i - 1, step.key)
                            }"
                            :title="step.name"
                          >
                            <v-icon size="12">{{ isStepCompleted(i - 1, step.key) ? 'mdi-check' : step.icon }}</v-icon>
                          </div>
                        </div>
                      </div>

                      <!-- Live Stream Preview -->
                      <div class="wc-stream-section">
                        <div class="wc-stream-content">
                          <pre>{{ getStreamPreview(i - 1, 150) }}<span v-if="workerStreams[i - 1]?.isStreaming" class="cursor-blink">|</span></pre>
                        </div>
                      </div>
                    </template>
                    <template v-else>
                      <div class="wc-idle">
                        <v-icon size="32">mdi-robot-off-outline</v-icon>
                        <span>Wartet auf Aufgabe</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>
            </template>

            <!-- Focus View -->
            <template v-else-if="multiViewMode === 'focus'">
              <div class="focus-layout">
                <!-- Worker Selector -->
                <div class="worker-selector">
                  <div
                    v-for="i in workerCount"
                    :key="i - 1"
                    class="selector-item"
                    :class="{
                      'is-selected': localFocusedWorkerId === (i - 1),
                      'is-streaming': workerStreams[i - 1]?.isStreaming
                    }"
                    @click="localFocusedWorkerId = (i - 1)"
                  >
                    <div class="selector-badge" :style="{ backgroundColor: WORKER_COLORS[(i - 1) % WORKER_COLORS.length] }">
                      W{{ i }}
                    </div>
                    <div class="selector-info">
                      <span v-if="workerStreams[i - 1]?.comparison" class="selector-pillars">
                        {{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_a) }} vs
                        {{ getPillarShort(workerStreams[i - 1]?.comparison?.pillar_b) }}
                      </span>
                      <span v-else class="selector-idle">Idle</span>
                    </div>
                    <v-icon
                      v-if="workerStreams[i - 1]?.isStreaming"
                      size="12"
                      color="warning"
                      class="streaming-icon"
                    >mdi-circle</v-icon>
                  </div>
                </div>

                <!-- Focused Worker Content -->
                <div class="focus-content">
                  <template v-if="focusedWorker?.comparison">
                    <div class="focus-header">
                      <span class="focus-title">Worker {{ localFocusedWorkerId + 1 }}</span>
                      <v-chip color="blue" size="small">
                        {{ focusedWorker.comparison.pillar_a_name || 'Säule ' + focusedWorker.comparison.pillar_a }}
                      </v-chip>
                      <span class="vs-label">vs</span>
                      <v-chip color="green" size="small">
                        {{ focusedWorker.comparison.pillar_b_name || 'Säule ' + focusedWorker.comparison.pillar_b }}
                      </v-chip>
                    </div>
                    <div class="focus-stream">
                      <pre>{{ focusedWorker.content || '' }}</pre>
                      <span v-if="focusedWorker.isStreaming" class="cursor-blink">|</span>
                    </div>
                  </template>
                  <template v-else>
                    <div class="focus-empty">
                      <v-icon size="48">mdi-robot-off-outline</v-icon>
                      <span>Dieser Worker hat keine aktive Aufgabe</span>
                    </div>
                  </template>
                </div>
              </div>
            </template>
          </div>
        </template>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mode: { type: String, default: 'live-single' }, // 'live-single', 'live-multi', 'historical'
  session: { type: Object, default: null },
  progress: { type: Object, default: null },
  currentComparison: { type: Object, default: null },
  isStreaming: { type: Boolean, default: false },
  llmStreamContent: { type: String, default: '' },
  autoScrollEnabled: { type: Boolean, default: true },
  workerCount: { type: Number, default: 1 },
  workerStreams: { type: Object, default: () => ({}) },
  focusedWorkerId: { type: Number, default: 0 },
  scoreCriteria: { type: Array, default: () => [] },
  stepDefinitions: { type: Array, default: () => [] },
  getWorkerParsedResult: { type: Function, default: () => null },
  getWorkerScoreA: { type: Function, default: () => 0 },
  getWorkerScoreB: { type: Function, default: () => 0 },
  getWorkerStep: { type: Function, default: () => null },
  getStepByKey: { type: Function, default: () => null },
  getStatusColor: { type: Function, default: () => 'grey' },
  getStatusIcon: { type: Function, default: () => 'mdi-circle' },
  getStatusText: { type: Function, default: () => '' },
  getConfidenceColor: { type: Function, default: () => 'grey' }
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

// Criteria for Likert scale display
const CRITERIA_LIST = [
  { key: 'counsellor_coherence', short: 'Koh.B', name: 'Berater Kohärenz' },
  { key: 'client_coherence', short: 'Koh.K', name: 'Klient Kohärenz' },
  { key: 'quality', short: 'Qual.', name: 'Qualität' },
  { key: 'empathy', short: 'Emp.', name: 'Empathie' },
  { key: 'authenticity', short: 'Auth.', name: 'Authentizität' },
  { key: 'solution_orientation', short: 'Lösg.', name: 'Lösungsorientierung' }
];

// Analysis steps for progress indicator
const ANALYSIS_STEPS = [
  { key: 'step_1_overview', icon: 'mdi-eye', name: 'Überblick' },
  { key: 'step_2_strengths_a', icon: 'mdi-thumb-up', name: 'Stärken A' },
  { key: 'step_3_strengths_b', icon: 'mdi-thumb-up', name: 'Stärken B' },
  { key: 'step_4_weaknesses_a', icon: 'mdi-thumb-down', name: 'Schwächen A' },
  { key: 'step_5_weaknesses_b', icon: 'mdi-thumb-down', name: 'Schwächen B' },
  { key: 'step_6_comparison', icon: 'mdi-scale-balance', name: 'Vergleich' }
];

const multiViewMode = ref('grid');
const streamViewMode = ref('formatted');
const localFocusedWorkerId = ref(props.focusedWorkerId);
const streamRef = ref(null);

// Sync local focused worker with prop
watch(() => props.focusedWorkerId, (val) => {
  localFocusedWorkerId.value = val;
});

// Aliases for backward compatibility
const comparison = computed(() => props.currentComparison);
const streamContent = computed(() => props.llmStreamContent);

// Computed
const modeIcon = computed(() => {
  if (props.mode === 'live-multi') return 'mdi-account-group';
  if (props.mode === 'historical') return 'mdi-history';
  return 'mdi-eye';
});

const modeTitle = computed(() => {
  if (props.mode === 'live-multi') return 'Multi-Worker Ansicht';
  if (props.mode === 'historical') return 'Historischer Vergleich';
  return 'Live Vergleich';
});

const modeSubtitle = computed(() => {
  if (props.mode === 'live-multi') return `${props.workerCount} Worker`;
  if (props.comparison) {
    return `#${(props.comparison.comparison_index ?? props.comparison.queue_position ?? 0) + 1}`;
  }
  return '';
});

const progressPercent = computed(() => {
  if (!props.session?.total_comparisons) return 0;
  return (props.session.completed_comparisons / props.session.total_comparisons) * 100;
});

const focusedWorker = computed(() => {
  return props.workerStreams[localFocusedWorkerId.value];
});

// Parse the current stream content to get result
const parsedResult = computed(() => {
  if (!streamContent.value) return null;
  try {
    // Try to extract JSON from the stream content
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

const getStreamPreview = (workerId, length = 100) => {
  const content = props.workerStreams[workerId]?.content || '';
  return content.slice(-length);
};

// Get score for a specific criterion from worker result
const getWorkerScoreForCriterion = (workerId, criterionKey, side) => {
  const result = props.getWorkerParsedResult(workerId);
  if (!result?.criteria_scores?.[criterionKey]) return 0;
  return side === 'a' ? result.criteria_scores[criterionKey].score_a : result.criteria_scores[criterionKey].score_b;
};

// Check if a step is completed in the worker's chain of thought
const isStepCompleted = (workerId, stepKey) => {
  const result = props.getWorkerParsedResult(workerId);
  return result?.chain_of_thought?.[stepKey] !== undefined;
};

// Check if a step is currently being processed (last non-empty step)
const isStepActive = (workerId, stepKey) => {
  const result = props.getWorkerParsedResult(workerId);
  if (!result?.chain_of_thought) return false;

  const completedSteps = ANALYSIS_STEPS.filter(s => result.chain_of_thought[s.key] !== undefined);
  if (completedSteps.length === 0) return stepKey === 'step_1_overview';

  const lastCompleted = completedSteps[completedSteps.length - 1];
  const lastIndex = ANALYSIS_STEPS.findIndex(s => s.key === lastCompleted.key);
  const nextIndex = lastIndex + 1;

  if (nextIndex < ANALYSIS_STEPS.length) {
    return ANALYSIS_STEPS[nextIndex].key === stepKey;
  }
  return false;
};

const formatCriterionName = (key) => {
  const names = {
    counsellor_coherence: 'Berater Kohärenz',
    client_coherence: 'Klient Kohärenz',
    quality: 'Qualität',
    empathy: 'Empathie',
    authenticity: 'Authentizität',
    solution_orientation: 'Lösungsorientierung'
  };
  return names[key] || key;
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

// Auto-scroll stream
watch(() => props.streamContent, () => {
  if (streamRef.value) {
    nextTick(() => {
      streamRef.value.scrollTop = streamRef.value.scrollHeight;
    });
  }
});
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

/* Single View */
.single-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 16px;
}

.comparison-layout {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 16px;
}

/* Thread Panels */
.thread-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden;
}

.thread-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
}

.thread-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.message-item {
  padding: 12px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.message-item:last-child {
  border-bottom: none;
}

.message-role {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 6px;
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
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Evaluation Panel */
.evaluation-panel {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  gap: 16px;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.winner-display {
  text-align: center;
  padding: 16px;
  border-radius: 12px;
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
  font-size: 48px;
  font-weight: 700;
  margin: 8px 0;
}

.confidence-badge {
  font-size: 18px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Scores Table */
.scores-table {
  width: 100%;
}

.score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.score-label {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.score-values {
  display: flex;
  align-items: center;
  gap: 4px;
}

.score-a, .score-b {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
}

.score-a {
  background: rgba(33, 150, 243, 0.15);
  color: #2196F3;
}

.score-b {
  background: rgba(76, 175, 80, 0.15);
  color: #4CAF50;
}

.score-a.is-higher, .score-b.is-higher {
  transform: scale(1.1);
  font-weight: 700;
}

.score-divider {
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Stream Panel */
.stream-panel {
  height: 250px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden;
}

.stream-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
}

.stream-header-left, .stream-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stream-title {
  font-weight: 600;
  font-size: 14px;
}

.stream-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.stream-pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  line-height: 1.5;
}

/* Formatted Analysis */
.formatted-analysis {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cot-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cot-step {
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.cot-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 6px;
}

.cot-content {
  font-size: 12px;
  line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

.justification-section {
  padding: 12px;
  background: rgba(var(--v-theme-primary), 0.05);
  border-radius: 6px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.justification-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 13px;
  margin-bottom: 8px;
}

.justification-content {
  font-size: 13px;
  line-height: 1.6;
}

/* Multi-Worker View */
.multi-view {
  height: 100%;
  overflow: hidden;
}

.workers-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 12px;
  height: 100%;
  overflow-y: auto;
  align-content: start;
  padding: 4px;
}

.worker-card-full {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
  height: 320px;
}

.worker-card-full:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.worker-card-full.is-streaming {
  border-color: rgba(var(--v-theme-warning), 0.6);
  box-shadow: 0 0 12px rgba(var(--v-theme-warning), 0.2);
}

.worker-card-full.has-result {
  border-color: rgba(var(--v-theme-success), 0.4);
}

.worker-card-full.is-focused {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 2px rgba(var(--v-theme-primary), 0.2);
}

.wc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left: 3px solid var(--worker-color, #ccc);
}

.wc-badge {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.wc-pillars {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.pillar-a {
  color: #2196F3;
  font-weight: 600;
  font-size: 12px;
}

.pillar-b {
  color: #4CAF50;
  font-weight: 600;
  font-size: 12px;
}

.idle-label {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 12px;
}

.wc-body {
  flex: 1;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 0;
}

/* Result Row */
.wc-result-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 8px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 6px;
  flex-shrink: 0;
  height: 36px;
}

.wc-winner-section,
.wc-confidence-section {
  display: flex;
  align-items: center;
  gap: 6px;
}

.wc-label {
  font-size: 10px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
}

.wc-winner {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 24px;
  padding: 0 8px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
}

.wc-winner.winner-a {
  background: #2196F3;
  color: white;
}

.wc-winner.winner-b {
  background: #4CAF50;
  color: white;
}

.wc-winner.winner-tie {
  background: #FF9800;
  color: white;
}

.wc-winner.pending {
  background: rgba(var(--v-theme-on-surface), 0.1);
  color: rgba(var(--v-theme-on-surface), 0.4);
  animation: pulse-pending 1.5s ease-in-out infinite;
}

@keyframes pulse-pending {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

.wc-confidence-value {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.wc-confidence-value.has-value {
  color: rgb(var(--v-theme-success));
}

/* Scores Section */
.wc-scores-section {
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 6px;
  padding: 6px 8px;
  height: 110px;
}

.wc-scores-header {
  margin-bottom: 4px;
}

.wc-section-title {
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.wc-scores-grid {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.wc-score-row {
  display: flex;
  align-items: center;
  gap: 6px;
  height: 14px;
}

.wc-score-label {
  width: 36px;
  font-size: 9px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  flex-shrink: 0;
}

.wc-score-dots {
  display: flex;
  align-items: center;
  gap: 2px;
  flex: 1;
}

.wc-dots-group {
  display: flex;
  gap: 2px;
}

.wc-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.1);
  transition: all 0.2s ease;
}

.wc-dot.pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.wc-dots-group.dots-a .wc-dot.filled {
  background: #2196F3;
  box-shadow: 0 0 4px rgba(33, 150, 243, 0.5);
}

.wc-dots-group.dots-b .wc-dot.filled {
  background: #4CAF50;
  box-shadow: 0 0 4px rgba(76, 175, 80, 0.5);
}

.wc-score-vs {
  font-size: 9px;
  color: rgba(var(--v-theme-on-surface), 0.3);
  margin: 0 2px;
}

/* Steps Section */
.wc-steps-section {
  flex-shrink: 0;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 6px;
  padding: 6px 8px;
  height: 40px;
}

.wc-steps-header {
  margin-bottom: 4px;
}

.wc-steps-bar {
  display: flex;
  justify-content: space-between;
  gap: 4px;
}

.wc-step-indicator {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 4px;
  background: rgba(var(--v-theme-on-surface), 0.05);
  color: rgba(var(--v-theme-on-surface), 0.3);
  transition: all 0.2s ease;
}

.wc-step-indicator.completed {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
}

.wc-step-indicator.active {
  background: rgba(var(--v-theme-warning), 0.2);
  color: rgb(var(--v-theme-warning));
  animation: step-active 1s ease-in-out infinite;
}

@keyframes step-active {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* Stream Section */
.wc-stream-section {
  flex: 1;
  min-height: 60px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.wc-stream-content {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 4px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.05);
}

.wc-stream-content pre {
  margin: 0;
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 9px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.3;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.wc-idle {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 12px;
}

/* Focus Layout */
.focus-layout {
  display: flex;
  height: 100%;
  gap: 16px;
}

.worker-selector {
  width: 200px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.selector-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.selector-item:hover {
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.selector-item.is-selected {
  border-color: rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}

.selector-item.is-streaming {
  border-color: rgba(var(--v-theme-warning), 0.5);
}

.selector-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: white;
}

.selector-info {
  flex: 1;
}

.selector-pillars {
  font-size: 11px;
  font-weight: 500;
}

.selector-idle {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.focus-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: 8px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  overflow: hidden;
}

.focus-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.focus-title {
  font-weight: 600;
  font-size: 14px;
  margin-right: 8px;
}

.vs-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.focus-stream {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.focus-stream pre {
  margin: 0;
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}

.focus-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Animations */
.rotating {
  animation: rotate 2s linear infinite;
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

.cursor-blink {
  animation: cursor-blink 1s step-end infinite;
  color: rgb(var(--v-theme-primary));
}

@keyframes cursor-blink {
  from, to { opacity: 1; }
  50% { opacity: 0; }
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
