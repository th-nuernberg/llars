<template>
  <div class="compare-worker-panel">
    <!-- No Worker Selected -->
    <div v-if="workerId === null" class="panel-empty">
      <v-icon size="48">mdi-account-question</v-icon>
      <span>Worker auswählen</span>
    </div>

    <!-- Worker Content -->
    <template v-else>
      <!-- Status Header -->
      <div class="panel-status" :style="{ '--worker-color': workerColor }">
        <div v-if="workerStream?.isStreaming" class="status-badge status-streaming">
          <v-icon size="16" class="rotating">mdi-loading</v-icon>
          <span>Analysiert</span>
        </div>
        <div v-else-if="workerResult?.winner" class="status-badge status-complete">
          <v-icon size="16">mdi-check-circle</v-icon>
          <span>Fertig</span>
        </div>
        <div v-else-if="workerStream?.comparison" class="status-badge status-pending">
          <v-icon size="16">mdi-clock-outline</v-icon>
          <span>Ausstehend</span>
        </div>
        <div v-else class="status-badge status-idle">
          <v-icon size="16">mdi-sleep</v-icon>
          <span>Idle</span>
        </div>
      </div>

      <!-- Pillars (if active) -->
      <div v-if="workerStream?.comparison" class="panel-pillars">
        <div class="pillar-item pillar-a">
          <span class="pillar-badge">A</span>
          <span class="pillar-name">{{ getPillarName(workerStream.comparison.pillar_a) }}</span>
        </div>
        <v-icon size="20" color="grey">mdi-arrow-left-right</v-icon>
        <div class="pillar-item pillar-b">
          <span class="pillar-name">{{ getPillarName(workerStream.comparison.pillar_b) }}</span>
          <span class="pillar-badge">B</span>
        </div>
      </div>

      <!-- Result (if available) -->
      <div v-if="workerResult?.winner" class="panel-result">
        <!-- Winner -->
        <div class="result-winner">
          <div
            class="winner-badge"
            :class="'winner-' + workerResult.winner.toLowerCase()"
          >
            {{ workerResult.winner }}
          </div>
          <div class="winner-info">
            <span class="winner-label">Gewinner</span>
            <span class="winner-confidence">
              {{ Math.round((workerResult.confidence || 0) * 100) }}% Konfidenz
            </span>
          </div>
        </div>

        <!-- Criteria Scores -->
        <div class="result-criteria">
          <div
            v-for="criterion in criteriaList"
            :key="criterion.key"
            class="criterion-item"
          >
            <div class="criterion-header">
              <span class="criterion-name">{{ criterion.name || criterion.short }}</span>
            </div>
            <div class="criterion-scores">
              <div class="score score-a" :class="{ higher: isScoreHigher(criterion.key, 'a') }">
                {{ getCriterionScore(criterion.key, 'a') }}
              </div>
              <div class="score-bar">
                <div
                  class="bar-fill bar-a"
                  :style="{ width: getScoreBarWidth(criterion.key, 'a') }"
                ></div>
                <div
                  class="bar-fill bar-b"
                  :style="{ width: getScoreBarWidth(criterion.key, 'b'), marginLeft: 'auto' }"
                ></div>
              </div>
              <div class="score score-b" :class="{ higher: isScoreHigher(criterion.key, 'b') }">
                {{ getCriterionScore(criterion.key, 'b') }}
              </div>
            </div>
          </div>
        </div>

        <!-- Total Scores -->
        <div class="result-totals">
          <div class="total-item side-a">
            <span class="total-label">A Gesamt</span>
            <span class="total-value">{{ getTotalScore('a') }}</span>
          </div>
          <div class="total-item side-b">
            <span class="total-label">B Gesamt</span>
            <span class="total-value">{{ getTotalScore('b') }}</span>
          </div>
        </div>
      </div>

      <!-- Stream Preview (if streaming or no result yet) -->
      <div v-else-if="workerStream?.comparison" class="panel-stream">
        <div class="stream-label">
          <v-icon size="14">mdi-text</v-icon>
          <span>LLM Output</span>
        </div>
        <div class="stream-preview">
          <pre>{{ truncateStream(workerStream.content) || 'Warte auf Analyse...' }}</pre>
        </div>
      </div>

      <!-- Idle State -->
      <div v-else class="panel-idle">
        <v-icon size="64" color="grey-lighten-1">mdi-robot-off-outline</v-icon>
        <span>Worker wartet auf nächste Aufgabe</span>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  workerId: { type: Number, default: null },
  workerStream: { type: Object, default: null },
  workerResult: { type: Object, default: null },
  workerColor: { type: String, default: '#9E9E9E' },
  criteriaList: { type: Array, default: () => [] }
});

const PILLAR_NAMES = {
  1: 'Rollentausch',
  2: 'Feature-basiert',
  3: 'Anonymisiert',
  4: 'Synthetisch',
  5: 'Live'
};

const getPillarName = (pillarId) => PILLAR_NAMES[pillarId] || `Pillar ${pillarId}`;

const getCriterionScore = (criterionKey, side) => {
  const scores = props.workerResult?.criteria_scores?.[criterionKey];
  if (!scores) return 0;
  return side === 'a' ? scores.score_a : scores.score_b;
};

const isScoreHigher = (criterionKey, side) => {
  const scoreA = getCriterionScore(criterionKey, 'a');
  const scoreB = getCriterionScore(criterionKey, 'b');
  return side === 'a' ? scoreA > scoreB : scoreB > scoreA;
};

const getScoreBarWidth = (criterionKey, side) => {
  const score = getCriterionScore(criterionKey, side);
  const maxScore = 10; // Assuming 1-10 scale
  return `${(score / maxScore) * 50}%`;
};

const getTotalScore = (side) => {
  if (!props.workerResult?.criteria_scores) return 0;
  let total = 0;
  for (const criterion of props.criteriaList) {
    const scores = props.workerResult.criteria_scores[criterion.key];
    if (scores) {
      total += side === 'a' ? scores.score_a : scores.score_b;
    }
  }
  return total;
};

const truncateStream = (content) => {
  if (!content) return '';
  const maxLength = 500;
  if (content.length > maxLength) {
    return content.slice(-maxLength) + '...';
  }
  return content;
};
</script>

<style scoped>
.compare-worker-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 16px;
}

/* Empty State */
.panel-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Status */
.panel-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--worker-color, #9E9E9E);
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.status-streaming {
  background: rgba(var(--v-theme-secondary), 0.15);
  color: rgb(var(--v-theme-secondary));
}

.status-complete {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
}

.status-pending {
  background: rgba(var(--v-theme-warning), 0.15);
  color: rgb(var(--v-theme-warning));
}

.status-idle {
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Pillars */
.panel-pillars {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.pillar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pillar-item.pillar-b {
  flex-direction: row-reverse;
}

.pillar-badge {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.pillar-item.pillar-a .pillar-badge {
  background: #2196F3;
}

.pillar-item.pillar-b .pillar-badge {
  background: #4CAF50;
}

.pillar-name {
  font-size: 14px;
  font-weight: 500;
}

/* Result */
.panel-result {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.result-winner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.winner-badge {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  color: white;
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

.winner-info {
  display: flex;
  flex-direction: column;
}

.winner-label {
  font-size: 16px;
  font-weight: 600;
}

.winner-confidence {
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Criteria */
.result-criteria {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.criterion-item {
  background: rgba(var(--v-theme-surface), 0.5);
  border-radius: 6px;
  padding: 8px 12px;
}

.criterion-header {
  margin-bottom: 6px;
}

.criterion-name {
  font-size: 12px;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.criterion-scores {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score {
  width: 32px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.score.score-a.higher {
  color: #2196F3;
}

.score.score-b.higher {
  color: #4CAF50;
}

.score-bar {
  flex: 1;
  height: 6px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  display: flex;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.bar-fill.bar-a {
  background: #2196F3;
}

.bar-fill.bar-b {
  background: #4CAF50;
}

/* Totals */
.result-totals {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.total-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.total-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.total-value {
  font-size: 28px;
  font-weight: 700;
}

.total-item.side-a .total-value {
  color: #2196F3;
}

.total-item.side-b .total-value {
  color: #4CAF50;
}

/* Stream Preview */
.panel-stream {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stream-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 8px;
}

.stream-preview {
  flex: 1;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 8px;
  padding: 12px;
  overflow: auto;
}

.stream-preview pre {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

/* Idle State */
.panel-idle {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.4);
  font-size: 14px;
}

/* Animations */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
