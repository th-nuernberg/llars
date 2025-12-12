<template>
  <div class="focus-worker-view">
    <!-- Worker Header -->
    <div class="focus-header" :style="{ '--worker-color': workerColor }">
      <div class="header-left">
        <div class="worker-badge" :style="{ backgroundColor: workerColor }">
          W{{ (workerId || 0) + 1 }}
        </div>
        <div v-if="workerStream?.comparison" class="header-pillars">
          <div class="pillar-tag pillar-a">
            <span class="pillar-badge">A</span>
            {{ getPillarName(workerStream.comparison.pillar_a) }}
          </div>
          <v-icon size="18">mdi-arrow-left-right</v-icon>
          <div class="pillar-tag pillar-b">
            {{ getPillarName(workerStream.comparison.pillar_b) }}
            <span class="pillar-badge">B</span>
          </div>
        </div>
        <span v-else class="header-idle">Kein aktiver Vergleich</span>
      </div>
      <div class="header-right">
        <div v-if="workerStream?.isStreaming" class="status-chip streaming">
          <v-icon size="14" class="rotating">mdi-loading</v-icon>
          Analysiert
        </div>
        <div v-else-if="workerResult?.winner" class="status-chip complete">
          <v-icon size="14">mdi-check-circle</v-icon>
          Fertig
        </div>
        <div v-else-if="workerStream?.comparison" class="status-chip pending">
          <v-icon size="14">mdi-clock-outline</v-icon>
          Ausstehend
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div v-if="workerStream?.comparison" class="focus-content">
      <!-- Content Tabs -->
      <div class="content-tabs">
        <v-btn
          v-for="tab in tabs"
          :key="tab.key"
          :variant="activeTab === tab.key ? 'flat' : 'text'"
          :color="activeTab === tab.key ? 'primary' : undefined"
          size="small"
          @click="activeTab = tab.key"
        >
          <v-icon start size="16">{{ tab.icon }}</v-icon>
          {{ tab.label }}
        </v-btn>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="overview-tab">
          <!-- Result Summary -->
          <div v-if="workerResult?.winner" class="result-card">
            <div class="result-main">
              <div
                class="winner-badge-lg"
                :class="'winner-' + workerResult.winner.toLowerCase()"
              >
                {{ workerResult.winner }}
              </div>
              <div class="result-info">
                <span class="result-label">Gewinner</span>
                <div class="result-confidence">
                  <span class="conf-value">{{ Math.round((workerResult.confidence || 0) * 100) }}%</span>
                  <span class="conf-label">Konfidenz</span>
                </div>
              </div>
            </div>

            <!-- Score Totals -->
            <div class="score-totals">
              <div class="total-box side-a">
                <span class="total-label">A</span>
                <span class="total-score">{{ getTotalScore('a') }}</span>
              </div>
              <span class="vs">vs</span>
              <div class="total-box side-b">
                <span class="total-score">{{ getTotalScore('b') }}</span>
                <span class="total-label">B</span>
              </div>
            </div>
          </div>

          <!-- Streaming Status -->
          <div v-else-if="workerStream?.isStreaming" class="streaming-card">
            <v-icon size="40" color="secondary" class="rotating">mdi-loading</v-icon>
            <span class="streaming-text">LLM analysiert die Threads...</span>
            <div class="streaming-progress">
              <div class="progress-bar-animated"></div>
            </div>
          </div>

          <!-- Pending Status -->
          <div v-else class="pending-card">
            <v-icon size="40">mdi-clock-outline</v-icon>
            <span>Warte auf Analyse</span>
          </div>
        </div>

        <!-- Scores Tab -->
        <div v-if="activeTab === 'scores'" class="scores-tab">
          <div v-if="workerResult?.criteria_scores" class="criteria-grid">
            <div
              v-for="criterion in criteriaList"
              :key="criterion.key"
              class="criterion-card"
            >
              <div class="criterion-header">
                <span class="criterion-name">{{ criterion.name }}</span>
              </div>
              <div class="criterion-body">
                <div class="score-display">
                  <div class="score-item side-a" :class="{ winner: isScoreHigher(criterion.key, 'a') }">
                    <span class="score-label">A</span>
                    <span class="score-value">{{ getCriterionScore(criterion.key, 'a') }}</span>
                  </div>
                  <div class="score-bar-container">
                    <div class="score-bar">
                      <div
                        class="bar-segment bar-a"
                        :style="{ width: getScorePercent(criterion.key, 'a') }"
                      ></div>
                      <div
                        class="bar-segment bar-b"
                        :style="{ width: getScorePercent(criterion.key, 'b') }"
                      ></div>
                    </div>
                  </div>
                  <div class="score-item side-b" :class="{ winner: isScoreHigher(criterion.key, 'b') }">
                    <span class="score-value">{{ getCriterionScore(criterion.key, 'b') }}</span>
                    <span class="score-label">B</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="no-scores">
            <v-icon size="48">mdi-chart-bar</v-icon>
            <span>Scores noch nicht verfügbar</span>
          </div>
        </div>

        <!-- Analysis Tab -->
        <div v-if="activeTab === 'analysis'" class="analysis-tab">
          <!-- Analysis Steps -->
          <div class="analysis-steps">
            <v-btn
              v-for="step in analysisSteps"
              :key="step.key"
              :variant="activeStep === step.key ? 'flat' : 'outlined'"
              :color="activeStep === step.key ? 'primary' : undefined"
              size="small"
              class="step-btn"
              @click="activeStep = step.key"
            >
              <v-icon start size="14">{{ step.icon }}</v-icon>
              {{ step.name }}
            </v-btn>
          </div>

          <!-- Step Content -->
          <div class="step-content">
            <div v-if="getStepContent(activeStep)" class="step-text">
              {{ getStepContent(activeStep) }}
            </div>
            <div v-else class="step-empty">
              <v-icon size="32">mdi-text-search</v-icon>
              <span>{{ workerStream?.isStreaming ? 'Wird analysiert...' : 'Kein Inhalt für diesen Schritt' }}</span>
            </div>
          </div>
        </div>

        <!-- Stream Tab -->
        <div v-if="activeTab === 'stream'" class="stream-tab">
          <div class="stream-header">
            <span>Raw LLM Output</span>
            <v-chip v-if="workerStream?.isStreaming" color="secondary" size="x-small" class="pulse">
              <v-icon start size="12">mdi-broadcast</v-icon>
              Live
            </v-chip>
          </div>
          <div class="stream-content" ref="streamRef">
            <pre>{{ workerStream?.content || 'Keine Ausgabe' }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- Idle State -->
    <div v-else class="focus-idle">
      <v-icon size="80" color="grey-lighten-1">mdi-robot-off-outline</v-icon>
      <span class="idle-title">Worker ist inaktiv</span>
      <span class="idle-subtitle">Wartet auf den nächsten Vergleich</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue';

const props = defineProps({
  workerId: { type: Number, default: 0 },
  workerStream: { type: Object, default: null },
  workerResult: { type: Object, default: null },
  workerColor: { type: String, default: '#9E9E9E' },
  criteriaList: { type: Array, default: () => [] },
  analysisSteps: { type: Array, default: () => [] }
});

const streamRef = ref(null);
const activeTab = ref('overview');
const activeStep = ref('step_1_overview');

const tabs = [
  { key: 'overview', label: 'Übersicht', icon: 'mdi-view-dashboard' },
  { key: 'scores', label: 'Scores', icon: 'mdi-chart-bar' },
  { key: 'analysis', label: 'Analyse', icon: 'mdi-text-search' },
  { key: 'stream', label: 'Stream', icon: 'mdi-console' }
];

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

const getScorePercent = (criterionKey, side) => {
  const score = getCriterionScore(criterionKey, side);
  const maxScore = 10;
  return `${(score / maxScore) * 100}%`;
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

const getStepContent = (stepKey) => {
  // Try to parse step content from LLM output
  const content = props.workerStream?.content;
  if (!content) return null;

  // Simple extraction based on step patterns
  const stepPatterns = {
    step_1_overview: /(?:overview|überblick|step\s*1)[:\s]*([^]*?)(?=(?:strengths|stärken|step\s*2)|$)/i,
    step_2_strengths_a: /(?:strengths?\s*(?:of\s*)?a|stärken\s*a|step\s*2)[:\s]*([^]*?)(?=(?:strengths?\s*(?:of\s*)?b|stärken\s*b|step\s*3)|$)/i,
    step_3_strengths_b: /(?:strengths?\s*(?:of\s*)?b|stärken\s*b|step\s*3)[:\s]*([^]*?)(?=(?:weaknesses|schwächen|step\s*4)|$)/i,
    step_4_weaknesses_a: /(?:weaknesses?\s*(?:of\s*)?a|schwächen\s*a|step\s*4)[:\s]*([^]*?)(?=(?:weaknesses?\s*(?:of\s*)?b|schwächen\s*b|step\s*5)|$)/i,
    step_5_weaknesses_b: /(?:weaknesses?\s*(?:of\s*)?b|schwächen\s*b|step\s*5)[:\s]*([^]*?)(?=(?:comparison|vergleich|step\s*6|final|winner)|$)/i,
    step_6_comparison: /(?:comparison|vergleich|step\s*6|final)[:\s]*([^]*?)(?=(?:\{|$))/i
  };

  const pattern = stepPatterns[stepKey];
  if (!pattern) return null;

  const match = content.match(pattern);
  if (match && match[1]) {
    return match[1].trim().substring(0, 1500);
  }
  return null;
};

// Auto-scroll stream content
watch(() => props.workerStream?.content, async () => {
  if (activeTab.value === 'stream' && props.workerStream?.isStreaming && streamRef.value) {
    await nextTick();
    streamRef.value.scrollTop = streamRef.value.scrollHeight;
  }
});

// Reset to overview when worker changes
watch(() => props.workerId, () => {
  activeTab.value = 'overview';
  activeStep.value = 'step_1_overview';
});
</script>

<style scoped>
.focus-worker-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Header */
.focus-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-left: 4px solid var(--worker-color, #9E9E9E);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.worker-badge {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: white;
}

.header-pillars {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pillar-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 500;
}

.pillar-badge {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: white;
}

.pillar-tag.pillar-a .pillar-badge {
  background: #2196F3;
}

.pillar-tag.pillar-b .pillar-badge {
  background: #4CAF50;
}

.header-idle {
  color: rgba(var(--v-theme-on-surface), 0.5);
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
}

.status-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
}

.status-chip.streaming {
  background: rgba(var(--v-theme-secondary), 0.15);
  color: rgb(var(--v-theme-secondary));
}

.status-chip.complete {
  background: rgba(var(--v-theme-success), 0.15);
  color: rgb(var(--v-theme-success));
}

.status-chip.pending {
  background: rgba(var(--v-theme-warning), 0.15);
  color: rgb(var(--v-theme-warning));
}

/* Content */
.focus-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
}

.content-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.tab-content {
  flex: 1;
  overflow: hidden;
}

/* Overview Tab */
.overview-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  background: rgb(var(--v-theme-surface));
  border: 2px solid rgba(var(--v-theme-success), 0.3);
  border-radius: 12px;
}

.result-main {
  display: flex;
  align-items: center;
  gap: 16px;
}

.winner-badge-lg {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  color: white;
}

.winner-badge-lg.winner-a {
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
}

.winner-badge-lg.winner-b {
  background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%);
}

.winner-badge-lg.winner-tie {
  background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
}

.result-info {
  display: flex;
  flex-direction: column;
}

.result-label {
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.result-confidence {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.conf-value {
  font-size: 28px;
  font-weight: 700;
  color: rgb(var(--v-theme-success));
}

.conf-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.score-totals {
  display: flex;
  align-items: center;
  gap: 16px;
}

.total-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px;
}

.total-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.total-score {
  font-size: 24px;
  font-weight: 700;
}

.total-box.side-a .total-score {
  color: #2196F3;
}

.total-box.side-b .total-score {
  color: #4CAF50;
}

.vs {
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.streaming-card, .pending-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 12px;
}

.streaming-text {
  font-size: 16px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.streaming-progress {
  width: 200px;
  height: 4px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar-animated {
  height: 100%;
  width: 50%;
  background: rgb(var(--v-theme-secondary));
  animation: progress-slide 1.5s ease-in-out infinite;
}

@keyframes progress-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}

.pending-card {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Scores Tab */
.scores-tab {
  height: 100%;
  overflow-y: auto;
}

.criteria-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.criterion-card {
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 8px;
  padding: 12px;
}

.criterion-header {
  margin-bottom: 10px;
}

.criterion-name {
  font-weight: 600;
  font-size: 14px;
}

.criterion-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 60px;
}

.score-item.side-b {
  flex-direction: row-reverse;
}

.score-label {
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.score-value {
  font-size: 18px;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.score-item.winner .score-value {
  color: rgb(var(--v-theme-success));
}

.score-item.side-a .score-value {
  color: #2196F3;
}

.score-item.side-b .score-value {
  color: #4CAF50;
}

.score-bar-container {
  flex: 1;
}

.score-bar {
  height: 8px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 4px;
  display: flex;
  gap: 2px;
}

.bar-segment {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.bar-segment.bar-a {
  background: #2196F3;
}

.bar-segment.bar-b {
  background: #4CAF50;
  margin-left: auto;
}

.no-scores {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Analysis Tab */
.analysis-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.analysis-steps {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  flex-shrink: 0;
}

.step-btn {
  text-transform: none !important;
}

.step-content {
  flex: 1;
  overflow-y: auto;
  background: rgba(var(--v-theme-surface-variant), 0.2);
  border-radius: 8px;
  padding: 16px;
}

.step-text {
  font-size: 14px;
  line-height: 1.7;
  white-space: pre-wrap;
}

.step-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Stream Tab */
.stream-tab {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.stream-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-radius: 8px 8px 0 0;
  font-weight: 600;
  font-size: 13px;
  flex-shrink: 0;
}

.stream-content {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 0 0 8px 8px;
  padding: 16px;
}

.stream-content pre {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  color: #d4d4d4;
}

/* Idle State */
.focus-idle {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.idle-title {
  font-size: 18px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.idle-subtitle {
  font-size: 14px;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

/* Animations */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pulse {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}
</style>
