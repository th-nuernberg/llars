<template>
  <div class="results-tab">
    <!-- Export Actions -->
    <div class="tab-header">
      <h3>{{ $t('scenarioManager.results.title') }}</h3>
      <div class="header-actions">
        <span v-if="liveStats?.connected" class="live-badge">
          <span class="live-dot"></span>
          Live
        </span>
        <LBtn variant="secondary" @click="refreshResults" :loading="loading">
          <LIcon start>mdi-refresh</LIcon>
          {{ $t('common.refresh') }}
        </LBtn>
        <v-menu>
          <template #activator="{ props }">
            <LBtn variant="primary" v-bind="props">
              <LIcon start>mdi-download</LIcon>
              {{ $t('scenarioManager.results.export') }}
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="exportResults('json')">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-code-json</LIcon>
              </template>
              <v-list-item-title>JSON</v-list-item-title>
            </v-list-item>
            <v-list-item @click="exportResults('csv')">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-file-delimited</LIcon>
              </template>
              <v-list-item-title>CSV</v-list-item-title>
            </v-list-item>
            <v-list-item @click="exportResults('xlsx')">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-file-excel</LIcon>
              </template>
              <v-list-item-title>Excel</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(176, 202, 151, 0.15);">
          <LIcon color="#b0ca97" size="24">mdi-check-circle-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.totalEvaluations }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.totalEvaluations') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(136, 196, 200, 0.15);">
          <LIcon color="#88c4c8" size="24">mdi-account-multiple-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.humanEvaluators }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.humanEvaluators') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(196, 160, 212, 0.15);">
          <LIcon color="#c4a0d4" size="24">mdi-robot-outline</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.llmEvaluators }}</span>
          <span class="summary-label">{{ $t('scenarioManager.results.llmEvaluators') }}</span>
        </div>
      </div>

      <div class="summary-card">
        <div class="summary-icon" style="background-color: rgba(209, 188, 138, 0.15);">
          <LIcon color="#D1BC8A" size="24">mdi-percent</LIcon>
        </div>
        <div class="summary-content">
          <span class="summary-value">{{ summaryStats.agreementRate }}%</span>
          <span class="summary-label">{{ $t('scenarioManager.results.agreementRate') }}</span>
        </div>
      </div>
    </div>

    <!-- Agreement Metrics -->
    <div class="section" v-if="agreementMetrics?.alpha !== null || agreementMetrics?.kappa !== null">
      <h4 class="section-title">{{ $t('scenarioManager.results.agreementMetrics') }}</h4>
      <div class="metrics-grid">
        <div class="metric-card" v-if="agreementMetrics?.kappa !== null && agreementMetrics?.kappa !== undefined">
          <span class="metric-name">Cohen's Kappa</span>
          <span class="metric-value" :class="getKappaClass(agreementMetrics.kappa)">
            {{ agreementMetrics.kappa?.toFixed(3) || '-' }}
          </span>
          <span class="metric-interpretation">{{ getKappaInterpretation(agreementMetrics.kappa) }}</span>
        </div>
        <div class="metric-card" v-if="agreementMetrics?.alpha !== null && agreementMetrics?.alpha !== undefined">
          <span class="metric-name">Krippendorff's Alpha</span>
          <span class="metric-value" :class="getKappaClass(agreementMetrics.alpha)">
            {{ agreementMetrics.alpha?.toFixed(3) || '-' }}
          </span>
          <span class="metric-interpretation">{{ agreementMetrics.interpretation || '' }}</span>
        </div>
        <div class="metric-card" v-if="agreementMetrics?.fleiss !== null && agreementMetrics?.fleiss !== undefined">
          <span class="metric-name">Fleiss' Kappa</span>
          <span class="metric-value">{{ agreementMetrics.fleiss?.toFixed(3) || '-' }}</span>
        </div>
        <div class="metric-card" v-if="agreementMetrics?.accuracy !== null && agreementMetrics?.accuracy !== undefined">
          <span class="metric-name">{{ $t('scenarioManager.results.accuracy') || 'Accuracy' }}</span>
          <span class="metric-value" :class="getAccuracyClass(agreementMetrics.accuracy)">
            {{ agreementMetrics.accuracy }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Results by Evaluator -->
    <div class="section">
      <h4 class="section-title">{{ $t('scenarioManager.results.byEvaluator') }}</h4>
      <div class="evaluators-list">
        <div
          v-for="evaluator in evaluatorStatsList"
          :key="evaluator.id"
          class="evaluator-card"
          @click="toggleEvaluatorDetails(evaluator)"
        >
          <div class="evaluator-info">
            <div class="evaluator-avatar" :class="{ 'is-llm': evaluator.isLLM }">
              <LIcon size="20">{{ evaluator.isLLM ? 'mdi-robot-outline' : 'mdi-account' }}</LIcon>
            </div>
            <div class="evaluator-details">
              <span class="evaluator-name">{{ evaluator.name }}</span>
              <span class="evaluator-type">{{ evaluator.isLLM ? 'LLM' : $t('scenarioManager.results.human') }}</span>
            </div>
          </div>
          <div class="evaluator-stats">
            <div class="stat-item">
              <span class="stat-value">{{ evaluator.completed }}</span>
              <span class="stat-label">{{ $t('scenarioManager.results.completed') }}</span>
            </div>
            <div class="stat-item" v-if="evaluator.accuracy !== null && evaluator.accuracy !== undefined">
              <span class="stat-value" :class="getAccuracyClass(evaluator.accuracy)">{{ evaluator.accuracy }}%</span>
              <span class="stat-label">{{ $t('scenarioManager.results.accuracy') || 'Accuracy' }}</span>
            </div>
          </div>
          <div class="evaluator-progress">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :class="{ 'is-llm': evaluator.isLLM }"
                :style="{ width: evaluator.progress + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ evaluator.progress }}%</span>
          </div>
          <LIcon class="expand-icon" :class="{ 'expanded': expandedEvaluator === evaluator.id }">
            mdi-chevron-down
          </LIcon>
        </div>

        <!-- Expanded Evaluator Details -->
        <div
          v-if="expandedEvaluator && expandedEvaluatorData"
          class="evaluator-expanded"
        >
          <div class="expanded-header">
            <h5>{{ $t('scenarioManager.results.evaluationDetails') || 'Evaluation Details' }} - {{ expandedEvaluatorData.name }}</h5>
            <LBtn variant="text" size="small" @click="expandedEvaluator = null">
              <LIcon>mdi-close</LIcon>
            </LBtn>
          </div>

          <!-- Voted Threads for LLM -->
          <div v-if="expandedEvaluatorData.isLLM && expandedEvaluatorData.votedThreads?.length > 0" class="thread-results">
            <h6>{{ $t('scenarioManager.results.completedThreads') || 'Completed Evaluations' }}</h6>
            <div class="thread-list">
              <div
                v-for="thread in expandedEvaluatorData.votedThreads.slice(0, 20)"
                :key="thread.thread_id"
                class="thread-item"
              >
                <div class="thread-info">
                  <span class="thread-id">#{{ thread.thread_id }}</span>
                  <span class="thread-subject" v-if="thread.subject">{{ thread.subject }}</span>
                </div>
                <div class="thread-result">
                  <LTag v-if="thread.vote" :variant="thread.vote === 'fake' ? 'danger' : 'success'" size="sm">
                    {{ thread.vote }}
                  </LTag>
                  <span v-if="thread.confidence" class="confidence">
                    {{ thread.confidence }}% {{ $t('scenarioManager.results.confidence') || 'confidence' }}
                  </span>
                  <LIcon
                    v-if="thread.is_correct !== undefined"
                    :color="thread.is_correct ? 'success' : 'error'"
                    size="18"
                  >
                    {{ thread.is_correct ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </LIcon>
                </div>
              </div>
              <div v-if="expandedEvaluatorData.votedThreads.length > 20" class="more-threads">
                + {{ expandedEvaluatorData.votedThreads.length - 20 }} {{ $t('scenarioManager.results.more') || 'more' }}
              </div>
            </div>
          </div>

          <!-- Pending Threads -->
          <div v-if="expandedEvaluatorData.pendingThreads?.length > 0" class="thread-results pending">
            <h6>{{ $t('scenarioManager.results.pendingThreads') || 'Pending Evaluations' }}</h6>
            <div class="thread-list">
              <div
                v-for="thread in expandedEvaluatorData.pendingThreads.slice(0, 10)"
                :key="thread.thread_id"
                class="thread-item pending"
              >
                <div class="thread-info">
                  <span class="thread-id">#{{ thread.thread_id }}</span>
                  <span class="thread-subject" v-if="thread.subject">{{ thread.subject }}</span>
                </div>
                <LTag variant="default" size="sm">Pending</LTag>
              </div>
              <div v-if="expandedEvaluatorData.pendingThreads.length > 10" class="more-threads">
                + {{ expandedEvaluatorData.pendingThreads.length - 10 }} {{ $t('scenarioManager.results.more') || 'more' }}
              </div>
            </div>
          </div>
        </div>

        <div v-if="evaluatorStatsList.length === 0" class="empty-state">
          <LIcon size="48" color="grey-lighten-1">mdi-chart-box-outline</LIcon>
          <p>{{ $t('scenarioManager.results.noEvaluators') }}</p>
        </div>
      </div>
    </div>

    <!-- Results Distribution Chart (placeholder) -->
    <div class="section">
      <h4 class="section-title">{{ $t('scenarioManager.results.distribution') }}</h4>
      <div class="chart-placeholder">
        <LIcon size="64" color="grey-lighten-1">mdi-chart-bar</LIcon>
        <p>{{ $t('scenarioManager.results.chartComingSoon') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useScenarioManager } from '../../composables/useScenarioManager'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  },
  liveStats: {
    type: Object,
    default: () => ({})
  }
})

const { t } = useI18n()
const { exportResults: doExport } = useScenarioManager()

// State
const loading = ref(false)
const expandedEvaluator = ref(null)

// Use live stats if available
const evaluatorStatsList = computed(() => {
  return props.liveStats?.userStatsList || []
})

const agreementMetrics = computed(() => {
  return props.liveStats?.agreementMetrics || null
})

const expandedEvaluatorData = computed(() => {
  if (!expandedEvaluator.value) return null
  return evaluatorStatsList.value.find(e => e.id === expandedEvaluator.value)
})

// Computed
const summaryStats = computed(() => {
  const users = evaluatorStatsList.value
  const humanCount = users.filter(u => !u.isLLM).length
  const llmCount = users.filter(u => u.isLLM).length
  const totalCompleted = users.reduce((sum, u) => sum + (u.completed || 0), 0)

  // Calculate agreement rate from accuracy if available
  const usersWithAccuracy = users.filter(u => u.accuracy !== null && u.accuracy !== undefined)
  const avgAccuracy = usersWithAccuracy.length > 0
    ? Math.round(usersWithAccuracy.reduce((sum, u) => sum + u.accuracy, 0) / usersWithAccuracy.length)
    : 0

  return {
    totalEvaluations: totalCompleted,
    humanEvaluators: humanCount || props.scenario?.user_count || 0,
    llmEvaluators: llmCount || props.scenario?.llm_evaluator_count || 0,
    agreementRate: agreementMetrics.value?.accuracy || avgAccuracy || 0
  }
})

// Methods
function getKappaClass(kappa) {
  if (kappa === null || kappa === undefined) return ''
  if (kappa >= 0.8) return 'excellent'
  if (kappa >= 0.6) return 'good'
  if (kappa >= 0.4) return 'moderate'
  return 'poor'
}

function getAccuracyClass(accuracy) {
  if (accuracy === null || accuracy === undefined) return ''
  if (accuracy >= 80) return 'excellent'
  if (accuracy >= 60) return 'good'
  if (accuracy >= 40) return 'moderate'
  return 'poor'
}

function getKappaInterpretation(kappa) {
  if (kappa === null || kappa === undefined) return '-'
  if (kappa >= 0.8) return t('scenarioManager.results.kappa.excellent')
  if (kappa >= 0.6) return t('scenarioManager.results.kappa.good')
  if (kappa >= 0.4) return t('scenarioManager.results.kappa.moderate')
  if (kappa >= 0.2) return t('scenarioManager.results.kappa.fair')
  return t('scenarioManager.results.kappa.poor')
}

function toggleEvaluatorDetails(evaluator) {
  if (expandedEvaluator.value === evaluator.id) {
    expandedEvaluator.value = null
  } else {
    expandedEvaluator.value = evaluator.id
  }
}

async function refreshResults() {
  loading.value = true
  try {
    // Stats are refreshed via parent component's real-time subscription
    await new Promise(resolve => setTimeout(resolve, 300))
  } finally {
    loading.value = false
  }
}

async function exportResults(format) {
  try {
    const data = await doExport(props.scenario.id, format)
    // Handle download
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      downloadBlob(blob, `scenario-${props.scenario.id}-results.json`)
    } else {
      downloadBlob(data, `scenario-${props.scenario.id}-results.${format}`)
    }
  } catch (error) {
    console.error('Export failed:', error)
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.results-tab {
  max-width: 1200px;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.tab-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  color: #4caf50;
}

.live-dot {
  width: 6px;
  height: 6px;
  background-color: #4caf50;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}

/* Summary Grid */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
}

.summary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

.summary-content {
  display: flex;
  flex-direction: column;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.summary-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Section */
.section {
  margin-bottom: 32px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 16px;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  text-align: center;
}

.metric-name {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.metric-value.excellent { color: #4caf50; }
.metric-value.good { color: #8bc34a; }
.metric-value.moderate { color: #ff9800; }
.metric-value.poor { color: #f44336; }

.metric-interpretation {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-top: 4px;
}

/* Evaluators List */
.evaluators-list {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.evaluator-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  cursor: pointer;
  transition: background-color 0.2s;
}

.evaluator-card:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

.evaluator-card:last-child {
  border-bottom: none;
}

.evaluator-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
}

.evaluator-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: rgba(var(--v-theme-primary), 0.1);
  color: rgb(var(--v-theme-primary));
}

.evaluator-avatar.is-llm {
  background-color: rgba(var(--v-theme-accent), 0.1);
  color: rgb(var(--v-theme-accent));
}

.evaluator-details {
  display: flex;
  flex-direction: column;
}

.evaluator-name {
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

.evaluator-type {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.evaluator-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.stat-value.excellent { color: #4caf50; }
.stat-value.good { color: #8bc34a; }
.stat-value.moderate { color: #ff9800; }
.stat-value.poor { color: #f44336; }

.stat-label {
  font-size: 0.7rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.evaluator-progress {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 3px;
}

.progress-fill.is-llm {
  background-color: rgb(var(--v-theme-accent));
}

.progress-text {
  font-size: 0.8rem;
  font-weight: 500;
  min-width: 40px;
  text-align: right;
}

.expand-icon {
  transition: transform 0.2s;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

/* Expanded Evaluator Details */
.evaluator-expanded {
  padding: 20px;
  background-color: rgba(var(--v-theme-on-surface), 0.02);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.expanded-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.expanded-header h5 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.thread-results {
  margin-bottom: 16px;
}

.thread-results h6 {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 10px;
}

.thread-results.pending h6 {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.thread-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.thread-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
}

.thread-item.pending {
  opacity: 0.6;
}

.thread-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.thread-id {
  font-weight: 600;
  font-size: 0.85rem;
  color: rgb(var(--v-theme-on-surface));
}

.thread-subject {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.thread-result {
  display: flex;
  align-items: center;
  gap: 10px;
}

.confidence {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.more-threads {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  padding: 8px 14px;
  text-align: center;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  text-align: center;
}

.empty-state p {
  margin-top: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Chart Placeholder */
.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  background-color: rgb(var(--v-theme-surface));
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 12px;
}

.chart-placeholder p {
  margin-top: 16px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}
</style>
