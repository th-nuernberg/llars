<template>
  <div class="single-comparison-view">
    <!-- Header with Pillars -->
    <div v-if="comparison" class="comparison-header">
      <div class="pillar-side pillar-a">
        <div class="pillar-badge">A</div>
        <div class="pillar-info">
          <span class="pillar-name">{{ getPillarName(comparison.pillar_a) }}</span>
          <span class="pillar-id">Pillar {{ comparison.pillar_a }}</span>
        </div>
      </div>

      <div class="comparison-meta">
        <v-icon v-if="isStreaming" color="secondary" class="rotating">mdi-loading</v-icon>
        <v-icon v-else-if="parsedResult?.winner" color="success">mdi-check-circle</v-icon>
        <v-icon v-else size="32">mdi-scale-balance</v-icon>
      </div>

      <div class="pillar-side pillar-b">
        <div class="pillar-info">
          <span class="pillar-name">{{ getPillarName(comparison.pillar_b) }}</span>
          <span class="pillar-id">Pillar {{ comparison.pillar_b }}</span>
        </div>
        <div class="pillar-badge">B</div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="comparison-content">
      <!-- Result Summary (if available) -->
      <div v-if="parsedResult?.winner" class="result-summary">
        <div class="winner-section">
          <div
            class="winner-badge"
            :class="'winner-' + parsedResult.winner.toLowerCase()"
          >
            {{ parsedResult.winner }}
          </div>
          <div class="winner-label">Gewinner</div>
        </div>

        <div class="confidence-section">
          <div class="confidence-value">{{ Math.round((parsedResult.confidence || 0) * 100) }}%</div>
          <div class="confidence-label">Konfidenz</div>
        </div>

        <!-- Score Summary -->
        <div v-if="parsedResult.criteria_scores" class="scores-overview">
          <div class="score-column side-a">
            <div class="score-header">A</div>
            <div class="score-total">{{ getTotalScore('a') }}</div>
          </div>
          <div class="score-criteria">
            <div
              v-for="criterion in CRITERIA_LIST"
              :key="criterion.key"
              class="criterion-row"
            >
              <span class="criterion-name">{{ criterion.short }}</span>
            </div>
          </div>
          <div class="score-column side-b">
            <div class="score-header">B</div>
            <div class="score-total">{{ getTotalScore('b') }}</div>
          </div>
        </div>
      </div>

      <!-- Streaming Content -->
      <div class="stream-container">
        <div class="stream-header">
          <span>LLM Analyse</span>
          <v-chip v-if="isStreaming" color="secondary" size="x-small" class="pulse-chip">
            <v-icon start size="12">mdi-broadcast</v-icon>
            Streaming
          </v-chip>
        </div>
        <div class="stream-content" ref="streamRef">
          <pre class="stream-text">{{ streamContent || 'Warte auf Analyse...' }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';

const props = defineProps({
  comparison: { type: Object, default: null },
  isStreaming: { type: Boolean, default: false },
  streamContent: { type: String, default: '' },
  parsedResult: { type: Object, default: null }
});

const streamRef = ref(null);

const PILLAR_NAMES = {
  1: 'Rollentausch',
  2: 'Feature-basiert',
  3: 'Anonymisiert',
  4: 'Synthetisch',
  5: 'Live'
};

const CRITERIA_LIST = [
  { key: 'counsellor_coherence', short: 'Koh.B' },
  { key: 'client_coherence', short: 'Koh.K' },
  { key: 'quality', short: 'Qual.' },
  { key: 'empathy', short: 'Emp.' },
  { key: 'authenticity', short: 'Auth.' },
  { key: 'solution_orientation', short: 'Lösg.' }
];

const getPillarName = (pillarId) => PILLAR_NAMES[pillarId] || `Pillar ${pillarId}`;

const getTotalScore = (side) => {
  if (!props.parsedResult?.criteria_scores) return 0;
  let total = 0;
  for (const criterion of CRITERIA_LIST) {
    const scores = props.parsedResult.criteria_scores[criterion.key];
    if (scores) {
      total += side === 'a' ? scores.score_a : scores.score_b;
    }
  }
  return total;
};

// Auto-scroll when streaming
watch(() => props.streamContent, async () => {
  if (props.isStreaming && streamRef.value) {
    await nextTick();
    streamRef.value.scrollTop = streamRef.value.scrollHeight;
  }
});
</script>

<style scoped>
.single-comparison-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 12px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.pillar-side {
  display: flex;
  align-items: center;
  gap: 12px;
}

.pillar-side.pillar-b {
  flex-direction: row-reverse;
  text-align: right;
}

.pillar-badge {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: white;
}

.pillar-side.pillar-a .pillar-badge {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
}

.pillar-side.pillar-b .pillar-badge {
  background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
}

.pillar-info {
  display: flex;
  flex-direction: column;
}

.pillar-name {
  font-size: 16px;
  font-weight: 600;
}

.pillar-id {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.comparison-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

/* Main Content */
.comparison-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

/* Result Summary */
.result-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48px;
  padding: 24px;
  background: rgba(var(--v-theme-surface), 0.8);
  border: 1px solid rgba(var(--v-theme-success), 0.3);
  border-radius: 12px;
  flex-shrink: 0;
}

.winner-section, .confidence-section {
  text-align: center;
}

.winner-badge {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: white;
  margin-bottom: 8px;
}

.winner-badge.winner-a {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
}

.winner-badge.winner-b {
  background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
}

.winner-badge.winner-tie {
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
}

.winner-label, .confidence-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.confidence-value {
  font-size: 36px;
  font-weight: 700;
  color: rgb(var(--v-theme-success));
  line-height: 1;
  margin-bottom: 8px;
}

/* Scores Overview */
.scores-overview {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.score-column {
  text-align: center;
  min-width: 60px;
}

.score-header {
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 4px;
}

.score-column.side-a .score-total {
  color: #2196F3;
}

.score-column.side-b .score-total {
  color: #4CAF50;
}

.score-total {
  font-size: 28px;
  font-weight: 700;
}

.score-criteria {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.criterion-row {
  display: flex;
  align-items: center;
  justify-content: center;
}

.criterion-name {
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Stream Container */
.stream-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
}

.stream-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  font-weight: 600;
  flex-shrink: 0;
}

.stream-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.stream-text {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.85);
}

/* Animations */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pulse-chip {
  animation: pulse-chip 1.5s ease-in-out infinite;
}

@keyframes pulse-chip {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
