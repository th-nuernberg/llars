<template>
  <div class="evaluation-tab">
    <!-- LLM Evaluation Control Panel -->
    <div class="control-panel">
      <div class="panel-header">
        <LIcon color="primary" class="mr-2">mdi-robot-outline</LIcon>
        <h3>{{ $t('scenarioManager.evaluation.llmControl') }}</h3>
      </div>

      <div class="panel-content">
        <div class="control-row">
          <div class="control-group">
            <label>{{ $t('scenarioManager.evaluation.model') }}</label>
            <v-select
              v-model="selectedModel"
              :items="availableModels"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              hide-details
              :disabled="isRunning"
            />
          </div>

          <div class="control-group">
            <label>{{ $t('scenarioManager.evaluation.template') }}</label>
            <v-select
              v-model="selectedTemplate"
              :items="availableTemplates"
              item-title="name"
              item-value="id"
              variant="outlined"
              density="compact"
              hide-details
              :disabled="isRunning"
            />
          </div>
        </div>

        <div class="control-actions">
          <LBtn
            v-if="!isRunning"
            variant="primary"
            :disabled="!canStart"
            :loading="starting"
            @click="startEvaluation"
          >
            <LIcon start>mdi-play</LIcon>
            {{ $t('scenarioManager.evaluation.start') }}
          </LBtn>
          <LBtn
            v-else
            variant="danger"
            :loading="stopping"
            @click="stopEvaluation"
          >
            <LIcon start>mdi-stop</LIcon>
            {{ $t('scenarioManager.evaluation.stop') }}
          </LBtn>
          <LBtn variant="text" @click="showMetrics = true">
            <LIcon start>mdi-chart-line</LIcon>
            {{ $t('scenarioManager.evaluation.metrics') }}
          </LBtn>
        </div>
      </div>
    </div>

    <!-- Progress Section -->
    <div class="progress-section" v-if="evaluationStatus">
      <div class="progress-header">
        <h4>{{ $t('scenarioManager.evaluation.progress') }}</h4>
        <LTag :variant="statusVariant">{{ statusLabel }}</LTag>
      </div>

      <div class="progress-stats">
        <div class="progress-main">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-info">
            <span>{{ progress.completed }} / {{ progress.total }}</span>
            <span class="percent">{{ progressPercent }}%</span>
          </div>
        </div>

        <div class="progress-details">
          <div class="detail-item">
            <LIcon size="18" color="success">mdi-check-circle</LIcon>
            <span>{{ progress.completed }}</span>
            <span class="label">{{ $t('scenarioManager.evaluation.completed') }}</span>
          </div>
          <div class="detail-item">
            <LIcon size="18" color="warning">mdi-clock-outline</LIcon>
            <span>{{ progress.pending }}</span>
            <span class="label">{{ $t('scenarioManager.evaluation.pending') }}</span>
          </div>
          <div class="detail-item">
            <LIcon size="18" color="error">mdi-alert-circle</LIcon>
            <span>{{ progress.failed }}</span>
            <span class="label">{{ $t('scenarioManager.evaluation.failed') }}</span>
          </div>
        </div>
      </div>

      <!-- Token Usage -->
      <div class="token-usage" v-if="tokenUsage">
        <h4>{{ $t('scenarioManager.evaluation.tokenUsage') }}</h4>
        <div class="usage-stats">
          <div class="usage-item">
            <span class="usage-value">{{ formatNumber(tokenUsage.total_tokens) }}</span>
            <span class="usage-label">{{ $t('scenarioManager.evaluation.tokens') }}</span>
          </div>
          <div class="usage-item">
            <span class="usage-value">${{ tokenUsage.total_cost_usd?.toFixed(4) || '0.00' }}</span>
            <span class="usage-label">{{ $t('scenarioManager.evaluation.cost') }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Preview -->
    <div class="results-section">
      <div class="results-header">
        <h4>{{ $t('scenarioManager.evaluation.liveResults') }}</h4>
        <span class="results-count">{{ results.length }} {{ $t('scenarioManager.evaluation.evaluations') }}</span>
      </div>

      <div class="results-list" v-if="results.length > 0">
        <div
          v-for="result in displayedResults"
          :key="result.id"
          class="result-card"
        >
          <div class="result-header">
            <span class="thread-id">#{{ result.thread_id }}</span>
            <LTag :variant="result.status === 'success' ? 'success' : 'danger'" size="sm">
              {{ result.status }}
            </LTag>
          </div>
          <div class="result-content">
            <div class="result-model">
              <LIcon size="16">mdi-robot-outline</LIcon>
              {{ result.model_name }}
            </div>
            <div class="result-score" v-if="result.score !== undefined">
              <LIcon size="16">mdi-star</LIcon>
              {{ result.score }}
            </div>
            <div class="result-confidence" v-if="result.confidence">
              {{ Math.round(result.confidence * 100) }}% {{ $t('scenarioManager.evaluation.confidence') }}
            </div>
          </div>
        </div>
      </div>

      <div v-else class="results-empty">
        <LIcon size="48" color="grey-lighten-1">mdi-clipboard-text-clock-outline</LIcon>
        <p>{{ $t('scenarioManager.evaluation.noResults') }}</p>
      </div>
    </div>

    <!-- Agreement Metrics Dialog -->
    <v-dialog v-model="showMetrics" max-width="600">
      <v-card>
        <v-card-title>
          <LIcon color="primary" class="mr-2">mdi-chart-line</LIcon>
          {{ $t('scenarioManager.evaluation.agreementMetrics') }}
        </v-card-title>
        <v-card-text>
          <div class="metrics-grid" v-if="agreementMetrics">
            <div class="metric-card">
              <span class="metric-value">{{ agreementMetrics.kappa?.toFixed(3) || '-' }}</span>
              <span class="metric-label">Cohen's Kappa</span>
            </div>
            <div class="metric-card">
              <span class="metric-value">{{ agreementMetrics.accuracy?.toFixed(3) || '-' }}</span>
              <span class="metric-label">Accuracy</span>
            </div>
            <div class="metric-card">
              <span class="metric-value">{{ agreementMetrics.f1?.toFixed(3) || '-' }}</span>
              <span class="metric-label">F1 Score</span>
            </div>
          </div>
          <v-alert v-else type="info" variant="tonal">
            {{ $t('scenarioManager.evaluation.noMetricsYet') }}
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showMetrics = false">
            {{ $t('common.close') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLLMEvaluation } from '@/composables/useLLMEvaluation'

const props = defineProps({
  scenario: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['evaluation-complete'])

const { t } = useI18n()

// Use the existing LLM evaluation composable
const {
  status: evaluationStatus,
  progress,
  results,
  tokenUsage,
  agreementMetrics,
  isRunning,
  startEvaluation: doStartEvaluation,
  stopEvaluation: doStopEvaluation,
  connectToScenario,
  disconnect
} = useLLMEvaluation()

// State
const selectedModel = ref(null)
const selectedTemplate = ref(null)
const starting = ref(false)
const stopping = ref(false)
const showMetrics = ref(false)

// Mock data for models and templates (will be fetched from API)
const availableModels = ref([
  { id: 'gpt-4o', name: 'GPT-4o' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet' }
])

const availableTemplates = ref([
  { id: 'default', name: 'Standard Rating' },
  { id: 'detailed', name: 'Detailed Analysis' },
  { id: 'quick', name: 'Quick Assessment' }
])

// Computed
const canStart = computed(() => {
  return selectedModel.value && selectedTemplate.value && props.scenario?.thread_count > 0
})

const progressPercent = computed(() => {
  if (!progress.value?.total) return 0
  return Math.round((progress.value.completed / progress.value.total) * 100)
})

const statusVariant = computed(() => {
  const map = {
    'IDLE': 'default',
    'RUNNING': 'info',
    'COMPLETED': 'success',
    'ERROR': 'danger'
  }
  return map[evaluationStatus.value] || 'default'
})

const statusLabel = computed(() => {
  return t(`scenarioManager.evaluation.status.${evaluationStatus.value?.toLowerCase() || 'idle'}`)
})

const displayedResults = computed(() => {
  return results.value.slice(0, 10)
})

// Methods
function formatNumber(num) {
  if (!num) return '0'
  return num.toLocaleString()
}

async function startEvaluation() {
  starting.value = true
  try {
    await doStartEvaluation({
      scenario_id: props.scenario.id,
      model_id: selectedModel.value,
      template_id: selectedTemplate.value
    })
  } finally {
    starting.value = false
  }
}

async function stopEvaluation() {
  stopping.value = true
  try {
    await doStopEvaluation()
  } finally {
    stopping.value = false
  }
}

onMounted(() => {
  if (props.scenario?.id) {
    connectToScenario(props.scenario.id)
  }
  // Set default selections
  if (availableModels.value.length > 0) {
    selectedModel.value = availableModels.value[0].id
  }
  if (availableTemplates.value.length > 0) {
    selectedTemplate.value = availableTemplates.value[0].id
  }
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.evaluation-tab {
  max-width: 1000px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Control Panel */
.control-panel {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.panel-content {
  padding: 20px;
}

.control-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.control-group label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
}

.control-actions {
  display: flex;
  gap: 12px;
}

/* Progress Section */
.progress-section {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  padding: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.progress-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.progress-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-main {
  flex: 1;
}

.progress-bar {
  height: 12px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 6px;
  transition: width 0.3s ease;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.progress-info .percent {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.progress-details {
  display: flex;
  gap: 24px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
}

.detail-item .label {
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Token Usage */
.token-usage {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.token-usage h4 {
  margin: 0 0 12px;
  font-size: 0.85rem;
  font-weight: 600;
}

.usage-stats {
  display: flex;
  gap: 32px;
}

.usage-item {
  display: flex;
  flex-direction: column;
}

.usage-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.usage-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Results Section */
.results-section {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px;
  overflow: hidden;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.results-header h4 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

.results-count {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-card {
  padding: 12px 20px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.result-card:last-child {
  border-bottom: none;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.thread-id {
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.result-content {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.result-model,
.result-score {
  display: flex;
  align-items: center;
  gap: 4px;
}

.results-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  text-align: center;
}

.results-empty p {
  margin-top: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Metrics Dialog */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.metric-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background-color: rgba(var(--v-theme-primary), 0.05);
  border-radius: 8px;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.metric-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin-top: 4px;
}
</style>
