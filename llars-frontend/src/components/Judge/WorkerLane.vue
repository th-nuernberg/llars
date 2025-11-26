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
        <!-- Winner Display -->
        <div class="d-flex justify-center mb-2">
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

          <v-chip
            v-if="parsedResult?.confidence"
            size="small"
            variant="outlined"
            class="ml-2"
            :color="getConfidenceColor(parsedResult.confidence)"
          >
            {{ Math.round(parsedResult.confidence * 100) }}%
          </v-chip>
        </div>

        <!-- Mini Scores Grid -->
        <div v-if="parsedResult?.criteria_scores" class="mini-scores">
          <div
            v-for="criterion in CRITERIA_SHORT"
            :key="criterion.key"
            class="score-item"
          >
            <span class="score-label text-caption">{{ criterion.short }}</span>
            <div class="score-values">
              <span class="score-a" :class="{ 'winner': parsedResult?.criteria_scores?.[criterion.key]?.score_a > parsedResult?.criteria_scores?.[criterion.key]?.score_b }">
                {{ parsedResult?.criteria_scores?.[criterion.key]?.score_a || '-' }}
              </span>
              <span class="vs">:</span>
              <span class="score-b" :class="{ 'winner': parsedResult?.criteria_scores?.[criterion.key]?.score_b > parsedResult?.criteria_scores?.[criterion.key]?.score_a }">
                {{ parsedResult?.criteria_scores?.[criterion.key]?.score_b || '-' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Stream Text (collapsed by default) -->
        <v-expansion-panels v-model="expandedPanel" class="mt-2">
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

const expandedPanel = ref(null);

// Short criterion names for compact display
const CRITERIA_SHORT = [
  { key: 'counsellor_coherence', short: 'BK' },
  { key: 'client_coherence', short: 'KK' },
  { key: 'quality', short: 'Q' },
  { key: 'empathy', short: 'E' },
  { key: 'authenticity', short: 'A' },
  { key: 'solution_orientation', short: 'LO' }
];

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
    criteria_scores: null
  };

  // Try to parse JSON
  try {
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      if (parsed.winner || parsed.criteria_scores || parsed.confidence) {
        result.winner = parsed.winner;
        result.confidence = parsed.confidence;
        result.criteria_scores = parsed.criteria_scores;
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

  return result.winner || result.confidence ? result : null;
});

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
  min-height: 200px;
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
  max-height: 300px;
  overflow-y: auto;
}

.worker-content {
  padding: 8px;
}

.mini-scores {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  padding: 8px;
  border-radius: 4px;
}

.score-item {
  text-align: center;
  padding: 4px;
}

.score-label {
  display: block;
  color: rgba(var(--v-theme-on-surface), 0.6);
  font-size: 10px;
  margin-bottom: 2px;
}

.score-values {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2px;
  font-size: 12px;
  font-weight: 600;
}

.score-a {
  color: rgb(33, 150, 243);
}

.score-b {
  color: rgb(76, 175, 80);
}

.score-a.winner, .score-b.winner {
  font-size: 14px;
  text-decoration: underline;
}

.vs {
  color: rgba(var(--v-theme-on-surface), 0.4);
}

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
</style>
