<template>
  <v-card variant="outlined" class="worker-lane" :class="{ 'lane-active': isActive, 'lane-streaming': isStreaming }">
    <!-- Worker Header -->
    <v-card-title class="py-2 px-3 d-flex align-center worker-header" :class="`bg-${workerColor}`">
      <v-avatar size="28" :color="workerColor" variant="flat" class="mr-2">
        <span class="text-caption font-weight-bold">W{{ workerId + 1 }}</span>
      </v-avatar>
      <span class="text-subtitle-2">Worker {{ workerId + 1 }}</span>
      <v-spacer></v-spacer>

      <!-- Status Chip -->
      <v-chip
        size="x-small"
        :color="statusChipColor"
        variant="flat"
        class="mr-2"
      >
        <v-icon start size="x-small" :class="{ 'rotating': isStreaming }">
          {{ statusIcon }}
        </v-icon>
        {{ statusText }}
      </v-chip>

      <!-- Fullscreen Button -->
      <v-btn
        icon
        size="x-small"
        variant="text"
        class="mr-1"
        @click="$emit('open-fullscreen', workerId)"
        title="Vollbild"
      >
        <v-icon size="small">mdi-fullscreen</v-icon>
      </v-btn>

      <!-- Current Comparison Info -->
      <v-chip v-if="currentComparison" size="x-small" variant="outlined">
        {{ currentComparison.pillar_a_name }} vs {{ currentComparison.pillar_b_name }}
      </v-chip>
    </v-card-title>

    <v-divider></v-divider>

    <v-card-text class="pa-2 stream-container">
      <!-- Empty State -->
      <div v-if="!streamContent && !currentComparison" class="d-flex flex-column align-center justify-center py-4 text-medium-emphasis">
        <v-icon size="32" class="mb-2">mdi-robot-off</v-icon>
        <span class="text-caption">Wartet auf Aufgabe...</span>
      </div>

      <!-- Live Result Display -->
      <div v-else class="worker-content">
        <!-- Winner and Confidence Display -->
        <div class="result-header mb-2">
          <div class="d-flex justify-space-between align-center">
            <!-- Thread A indicator -->
            <div class="thread-indicator thread-a" :class="{ 'is-winner': parsedResult?.winner === 'A' }">
              <span class="thread-letter">A</span>
            </div>

            <!-- Center: Winner Trophy -->
            <v-chip
              size="small"
              :color="parsedResult?.winner ? 'primary' : 'grey'"
              variant="flat"
              :class="{ 'pulse-chip': isStreaming && !parsedResult?.winner }"
            >
              <v-icon start size="small" :class="{ 'rotating': isStreaming && !parsedResult?.winner }">
                {{ isStreaming && !parsedResult?.winner ? 'mdi-loading' : 'mdi-trophy' }}
              </v-icon>
              {{ parsedResult?.winner || (isStreaming ? '...' : '-') }}
            </v-chip>

            <!-- Thread B indicator -->
            <div class="thread-indicator thread-b" :class="{ 'is-winner': parsedResult?.winner === 'B' }">
              <span class="thread-letter">B</span>
            </div>
          </div>

          <!-- Confidence Bar -->
          <div v-if="parsedResult?.confidence || isStreaming" class="confidence-bar mt-2">
            <v-progress-linear
              :model-value="parsedResult?.confidence ? parsedResult.confidence * 100 : 0"
              :indeterminate="isStreaming && !parsedResult?.confidence"
              :color="getConfidenceColor(parsedResult?.confidence || 0)"
              height="16"
              rounded
            >
              <template v-slot:default>
                <span class="text-caption font-weight-bold">
                  {{ parsedResult?.confidence ? Math.round(parsedResult.confidence * 100) + '%' : '' }}
                </span>
              </template>
            </v-progress-linear>
          </div>
        </div>

        <!-- Likert Scale Scores (formatted like fullscreen) -->
        <div class="likert-scores-compact">
          <div
            v-for="criterion in CRITERIA_SHORT"
            :key="criterion.key"
            class="likert-row-compact"
          >
            <span class="criterion-label">{{ criterion.short }}</span>
            <div class="likert-dots">
              <!-- A Score dots -->
              <div class="dots-group dots-a">
                <div
                  v-for="n in 5"
                  :key="`a-${n}`"
                  class="dot"
                  :class="{
                    'dot-filled': getScoreA(criterion.key) >= n,
                    'dot-pending': !getScoreA(criterion.key) && isStreaming
                  }"
                ></div>
              </div>
              <span class="score-divider">|</span>
              <!-- B Score dots -->
              <div class="dots-group dots-b">
                <div
                  v-for="n in 5"
                  :key="`b-${n}`"
                  class="dot"
                  :class="{
                    'dot-filled': getScoreB(criterion.key) >= n,
                    'dot-pending': !getScoreB(criterion.key) && isStreaming
                  }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Display Mode Toggle -->
        <div class="d-flex justify-center mt-2 mb-1">
          <v-btn-toggle
            v-model="displayMode"
            density="compact"
            mandatory
            size="x-small"
            color="primary"
            variant="outlined"
          >
            <v-btn value="formatted" size="x-small">
              <v-icon size="x-small">mdi-format-list-bulleted</v-icon>
            </v-btn>
            <v-btn value="raw" size="x-small">
              <v-icon size="x-small">mdi-code-braces</v-icon>
            </v-btn>
          </v-btn-toggle>
        </div>

        <!-- Formatted View -->
        <div v-if="displayMode === 'formatted'" class="formatted-output">
          <!-- Analysis Steps (compact) -->
          <div class="analysis-steps-compact">
            <div
              v-for="(stepDef, stepKey) in STEP_DEFINITIONS_COMPACT"
              :key="stepKey"
              class="step-compact"
              :class="{
                'step-active': getStepByKey(stepKey),
                'step-streaming': getStepByKey(stepKey)?.isStreaming
              }"
            >
              <v-icon
                size="12"
                :color="getStepByKey(stepKey) ? (getStepByKey(stepKey)?.isStreaming ? 'warning' : 'success') : 'grey'"
                :class="{ 'rotating': getStepByKey(stepKey)?.isStreaming }"
              >
                {{ getStepByKey(stepKey)?.isStreaming ? 'mdi-loading' : (getStepByKey(stepKey) ? 'mdi-check-circle' : 'mdi-circle-outline') }}
              </v-icon>
              <span class="step-label text-caption" :class="{ 'text-medium-emphasis': !getStepByKey(stepKey) }">
                {{ stepDef.short }}
              </span>
            </div>
          </div>

          <!-- Final Justification (if available) -->
          <div v-if="parsedResult?.final_justification" class="justification-compact mt-2">
            <div class="text-caption text-medium-emphasis mb-1">Begründung:</div>
            <div class="justification-text text-caption">{{ parsedResult.final_justification }}</div>
          </div>
        </div>

        <!-- Raw Stream Text -->
        <v-expansion-panels v-else v-model="expandedPanel" class="mt-2">
          <v-expansion-panel value="stream">
            <v-expansion-panel-title class="py-1 px-2">
              <v-icon size="small" class="mr-1" :class="{ 'rotating': isStreaming }">
                {{ isStreaming ? 'mdi-loading' : 'mdi-text-box' }}
              </v-icon>
              <span class="text-caption">Stream ({{ streamContent.length }} Zeichen)</span>
            </v-expansion-panel-title>
            <v-expansion-panel-text class="stream-panel">
              <pre class="stream-text">{{ streamContent }}<span v-if="isStreaming" class="cursor-blink">|</span></pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue';

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
  }
});

defineEmits(['open-fullscreen']);

const expandedPanel = ref(null);
const displayMode = ref('formatted'); // 'formatted' or 'raw'

// Short criterion names for compact display
const CRITERIA_SHORT = [
  { key: 'counsellor_coherence', short: 'BK' },
  { key: 'client_coherence', short: 'KK' },
  { key: 'quality', short: 'Q' },
  { key: 'empathy', short: 'E' },
  { key: 'authenticity', short: 'A' },
  { key: 'solution_orientation', short: 'LO' }
];

// Step definitions (compact version)
const STEP_DEFINITIONS_COMPACT = {
  'step_1': { short: 'BK', title: 'Berater-Kohärenz' },
  'step_2': { short: 'KK', title: 'Klienten-Kohärenz' },
  'step_3': { short: 'Q', title: 'Qualität' },
  'step_4': { short: 'E', title: 'Empathie' },
  'step_5': { short: 'A', title: 'Authentizität' },
  'step_6': { short: 'LO', title: 'Lösungsorientierung' }
};

// Worker colors (cycle through)
const WORKER_COLORS = ['blue', 'purple', 'teal', 'orange', 'pink'];

const workerColor = computed(() => WORKER_COLORS[props.workerId % WORKER_COLORS.length]);

const isActive = computed(() => props.currentComparison !== null || props.streamContent.length > 0);

const statusChipColor = computed(() => {
  if (props.isStreaming) return 'warning';
  if (props.currentComparison) return 'info';
  return 'grey';
});

const statusIcon = computed(() => {
  if (props.isStreaming) return 'mdi-loading';
  if (props.currentComparison) return 'mdi-play-circle';
  return 'mdi-sleep';
});

const statusText = computed(() => {
  if (props.isStreaming) return 'Streamt';
  if (props.currentComparison) return 'Arbeitet';
  return 'Wartet';
});

// Parse stream content for results
const parsedResult = computed(() => {
  if (!props.streamContent) return null;

  const content = props.streamContent.trim();
  const result = {
    winner: null,
    confidence: null,
    criteria_scores: null,
    scores: { A: {}, B: {} },
    final_justification: null
  };

  // Try to parse JSON
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.winner || parsed.criteria_scores || parsed.confidence || parsed.scores) {
        result.winner = parsed.winner;
        result.confidence = parsed.confidence;
        result.criteria_scores = parsed.criteria_scores;
        result.final_justification = parsed.final_justification;
        if (parsed.scores) {
          result.scores = parsed.scores;
        }
        return result;
      }
    }
  } catch (e) {
    // JSON not complete - try incremental parsing
  }

  // Incremental parsing
  const winnerMatch = content.match(/"winner"\s*:\s*"([AB])"/);
  if (winnerMatch) result.winner = winnerMatch[1];

  const confMatch = content.match(/"confidence"\s*:\s*([\d.]+)/);
  if (confMatch) result.confidence = parseFloat(confMatch[1]);

  // Extract individual scores from "scores": { "A": { ... }, "B": { ... } }
  for (const criterion of CRITERIA_SHORT) {
    // Try to find score for A
    const scoreAPattern = new RegExp(`"A"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
    const scoreAMatch = content.match(scoreAPattern);
    if (scoreAMatch) {
      result.scores.A[criterion.key] = parseInt(scoreAMatch[1]);
    }

    // Try to find score for B
    const scoreBPattern = new RegExp(`"B"[\\s\\S]*?"${criterion.key}"\\s*:\\s*(\\d+)`, 'm');
    const scoreBMatch = content.match(scoreBPattern);
    if (scoreBMatch) {
      result.scores.B[criterion.key] = parseInt(scoreBMatch[1]);
    }
  }

  // Extract final_justification
  const justMatch = content.match(/"final_justification"\s*:\s*"([^"]+)"/);
  if (justMatch) result.final_justification = justMatch[1];

  return result.winner || result.confidence || Object.keys(result.scores.A).length > 0 ? result : null;
});

// Parse stream steps incrementally
const parsedStreamSteps = computed(() => {
  if (!props.streamContent) return [];

  const content = props.streamContent;
  const steps = [];

  for (const [stepKey, stepDef] of Object.entries(STEP_DEFINITIONS_COMPACT)) {
    const stepPattern = new RegExp(`"${stepKey}"\\s*:\\s*"`, 'm');
    const stepMatch = content.match(stepPattern);

    if (stepMatch) {
      const startIdx = content.indexOf(stepMatch[0]) + stepMatch[0].length;
      let stepContent = '';
      let escaped = false;

      for (let i = startIdx; i < content.length; i++) {
        const char = content[i];
        if (escaped) {
          if (char === 'n') stepContent += '\n';
          else if (char === '"') stepContent += '"';
          else if (char === '\\') stepContent += '\\';
          else stepContent += char;
          escaped = false;
        } else if (char === '\\') {
          escaped = true;
        } else if (char === '"') {
          break;
        } else {
          stepContent += char;
        }
      }

      const isStepStreaming = !content.slice(startIdx).includes('"');

      steps.push({
        key: stepKey,
        title: stepDef.title,
        content: stepContent,
        isStreaming: isStepStreaming
      });
    }
  }

  return steps;
});

// Get step by key
const getStepByKey = (stepKey) => {
  return parsedStreamSteps.value.find(s => s.key === stepKey);
};

// Get score for criterion A
const getScoreA = (criterionKey) => {
  return parsedResult.value?.scores?.A?.[criterionKey] ||
         parsedResult.value?.criteria_scores?.[criterionKey]?.score_a ||
         0;
};

// Get score for criterion B
const getScoreB = (criterionKey) => {
  return parsedResult.value?.scores?.B?.[criterionKey] ||
         parsedResult.value?.criteria_scores?.[criterionKey]?.score_b ||
         0;
};

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return 'success';
  if (confidence >= 0.6) return 'info';
  if (confidence >= 0.4) return 'warning';
  return 'error';
};

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
  min-height: 280px;
}

.worker-lane.lane-active {
  border-color: rgb(var(--v-theme-primary));
}

.worker-lane.lane-streaming {
  border-color: rgb(var(--v-theme-warning));
  box-shadow: 0 0 10px rgba(var(--v-theme-warning), 0.3);
}

.worker-header {
  background: linear-gradient(90deg, rgba(var(--v-theme-surface-variant), 0.8) 0%, rgba(var(--v-theme-surface-variant), 0.4) 100%);
}

.stream-container {
  max-height: 400px;
  overflow-y: auto;
}

.worker-content {
  padding: 8px;
}

/* Result Header with A vs B */
.result-header {
  background: rgba(var(--v-theme-surface-variant), 0.2);
  padding: 8px;
  border-radius: 8px;
}

.thread-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.3s ease;
}

.thread-indicator.thread-a {
  background: rgba(33, 150, 243, 0.2);
  color: rgb(33, 150, 243);
  border: 2px solid rgba(33, 150, 243, 0.3);
}

.thread-indicator.thread-b {
  background: rgba(76, 175, 80, 0.2);
  color: rgb(76, 175, 80);
  border: 2px solid rgba(76, 175, 80, 0.3);
}

.thread-indicator.is-winner {
  transform: scale(1.2);
  box-shadow: 0 0 10px currentColor;
}

.thread-indicator.thread-a.is-winner {
  background: rgb(33, 150, 243);
  color: white;
}

.thread-indicator.thread-b.is-winner {
  background: rgb(76, 175, 80);
  color: white;
}

/* Likert Scores Compact */
.likert-scores-compact {
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 8px;
  border-radius: 4px;
  margin-top: 8px;
}

.likert-row-compact {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.likert-row-compact:last-child {
  margin-bottom: 0;
}

.criterion-label {
  width: 24px;
  font-size: 10px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.likert-dots {
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
  gap: 2px;
}

.dots-group {
  display: flex;
  gap: 2px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: all 0.2s ease;
}

.dots-a .dot.dot-filled {
  background: rgb(33, 150, 243);
}

.dots-b .dot.dot-filled {
  background: rgb(76, 175, 80);
}

.dot.dot-pending {
  animation: dot-pulse 1s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.6; }
}

.score-divider {
  color: rgba(var(--v-theme-on-surface), 0.3);
  font-size: 10px;
  margin: 0 4px;
}

/* Analysis Steps Compact */
.analysis-steps-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 4px;
}

.step-compact {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  border-radius: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  transition: all 0.2s ease;
}

.step-compact.step-active {
  background: rgba(var(--v-theme-success), 0.1);
}

.step-compact.step-streaming {
  background: rgba(var(--v-theme-warning), 0.2);
}

.step-label {
  font-size: 10px;
}

/* Justification */
.justification-compact {
  background: rgba(var(--v-theme-primary), 0.1);
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.justification-text {
  line-height: 1.4;
  max-height: 60px;
  overflow-y: auto;
}

/* Stream Panel */
.stream-panel :deep(.v-expansion-panel-text__wrapper) {
  max-height: 150px;
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
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.8; }
}

/* Formatted output container */
.formatted-output {
  margin-top: 8px;
}
</style>
