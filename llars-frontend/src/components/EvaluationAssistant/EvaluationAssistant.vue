<template>
  <div class="evaluation-assistant-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <LBtn variant="tonal" prepend-icon="mdi-arrow-left" @click="goBack">
          {{ $t('navigation.back') }}
        </LBtn>
        <div class="header-info ml-4">
          <h1 class="page-title">
            {{ $t('evaluationAssistant.title') }}
          </h1>
          <div class="page-subtitle text-medium-emphasis">
            {{ scenario?.name || $t('evaluationAssistant.loading') }}
          </div>
        </div>
        <v-spacer />
        <div class="header-actions">
          <LTag v-if="connected" variant="success" size="sm">
            <LIcon size="12" class="mr-1">mdi-circle</LIcon>
            {{ $t('evaluationAssistant.connected') }}
          </LTag>
          <LTag v-else variant="warning" size="sm">
            <LIcon size="12" class="mr-1">mdi-circle-outline</LIcon>
            {{ $t('evaluationAssistant.disconnected') }}
          </LTag>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-container">
      <v-progress-circular indeterminate color="primary" size="48" />
      <p class="mt-4 text-medium-emphasis">{{ $t('evaluationAssistant.loading') }}</p>
    </div>

    <!-- Main Content -->
    <div v-else class="main-content">
      <!-- Left Panel: Progress & Controls -->
      <div class="left-panel" :style="leftPanelStyle">
        <div class="panel-content">
          <!-- Progress Section -->
          <div class="progress-section">
            <EvaluationProgress
              :status="status"
              :progress="progress"
              :current-evaluation="currentEvaluation"
              :token-usage="tokenUsage"
            />
          </div>

          <!-- Controls Section -->
          <div class="controls-section">
            <EvaluationControls
              :status="status"
              :scenario-id="scenarioId"
              :available-models="availableModels"
              :available-templates="availableTemplates"
              @start="handleStart"
              @stop="handleStop"
            />
          </div>

          <!-- Agreement Metrics Section -->
          <div v-if="agreementMetrics" class="metrics-section">
            <AgreementMetricsPanel :metrics="agreementMetrics" />
          </div>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Results & Transparency -->
      <div class="right-panel" :style="rightPanelStyle">
        <!-- Tab Navigation -->
        <div class="panel-tabs">
          <v-tabs v-model="activeTab" density="compact" color="primary">
            <v-tab value="results">
              <LIcon start size="18">mdi-format-list-bulleted</LIcon>
              {{ $t('evaluationAssistant.tabs.results') }}
              <v-chip size="x-small" class="ml-2">{{ sortedResults.length }}</v-chip>
            </v-tab>
            <v-tab value="live" :disabled="!isRunning">
              <LIcon start size="18">mdi-play-circle</LIcon>
              {{ $t('evaluationAssistant.tabs.live') }}
              <v-chip
                v-if="isRunning"
                size="x-small"
                color="success"
                class="ml-2 pulse-chip"
              >
                <LIcon size="10" class="mr-1">mdi-circle</LIcon>
              </v-chip>
            </v-tab>
            <v-tab value="comparison">
              <LIcon start size="18">mdi-compare</LIcon>
              {{ $t('evaluationAssistant.tabs.comparison') }}
            </v-tab>
          </v-tabs>
        </div>

        <!-- Tab Content -->
        <div class="panel-content">
          <v-window v-model="activeTab" class="tab-window">
            <!-- Results Tab -->
            <v-window-item value="results">
              <div class="results-container">
                <div v-if="sortedResults.length === 0" class="empty-state">
                  <LIcon size="64" color="grey">mdi-robot-outline</LIcon>
                  <p class="mt-4 text-medium-emphasis">{{ $t('evaluationAssistant.noResults') }}</p>
                </div>
                <div v-else class="results-list">
                  <ResponseCard
                    v-for="result in sortedResults"
                    :key="result.id"
                    :result="result"
                    :expanded="expandedResult === result.id"
                    @toggle="toggleResult(result.id)"
                    @view-details="viewResultDetails(result)"
                  />
                </div>
              </div>
            </v-window-item>

            <!-- Live Tab -->
            <v-window-item value="live">
              <div class="live-container">
                <div v-if="!currentEvaluation" class="empty-state">
                  <v-progress-circular
                    v-if="isRunning"
                    indeterminate
                    color="primary"
                    size="48"
                  />
                  <LIcon v-else size="64" color="grey">mdi-pause-circle-outline</LIcon>
                  <p class="mt-4 text-medium-emphasis">
                    {{ isRunning ? $t('evaluationAssistant.waitingForEval') : $t('evaluationAssistant.notRunning') }}
                  </p>
                </div>
                <div v-else class="live-evaluation">
                  <LiveEvaluationCard :evaluation="currentEvaluation" />
                </div>
              </div>
            </v-window-item>

            <!-- Comparison Tab -->
            <v-window-item value="comparison">
              <div class="comparison-container">
                <EvaluatorComparison
                  :results="sortedResults"
                  :scenario-id="scenarioId"
                />
              </div>
            </v-window-item>
          </v-window>
        </div>
      </div>
    </div>

    <!-- Error Snackbar -->
    <v-snackbar
      v-model="showError"
      color="error"
      timeout="5000"
      location="bottom right"
    >
      {{ error }}
      <template v-slot:actions>
        <v-btn variant="text" @click="clearError">
          {{ $t('common.close') }}
        </v-btn>
      </template>
    </v-snackbar>

    <!-- Result Detail Dialog -->
    <v-dialog v-model="showDetailDialog" max-width="800">
      <ResultDetailDialog
        v-if="selectedResult"
        :result="selectedResult"
        @close="closeDetailDialog"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useLLMEvaluation, EVAL_STATUS } from '@/composables/useLLMEvaluation'
import { usePanelResize } from '@/composables/usePanelResize'

// Components
import EvaluationProgress from './EvaluationProgress.vue'
import EvaluationControls from './EvaluationControls.vue'
import AgreementMetricsPanel from './AgreementMetricsPanel.vue'
import ResponseCard from './ResponseCard.vue'
import LiveEvaluationCard from './LiveEvaluationCard.vue'
import EvaluatorComparison from './EvaluatorComparison.vue'
import ResultDetailDialog from './ResultDetailDialog.vue'

const route = useRoute()
const router = useRouter()

// Props
const props = defineProps({
  id: {
    type: [String, Number],
    default: null
  }
})

// Get scenario ID from props or route
const scenarioId = computed(() => {
  return props.id || route.params.id
})

// Panel resize
const { leftPanelStyle, rightPanelStyle, startResize, isResizing } = usePanelResize({
  initialLeftPercent: 35,
  storageKey: 'eval-assistant-panel-width',
  minLeftPercent: 25,
  maxLeftPercent: 50
})

// LLM Evaluation composable
const {
  status,
  progress,
  results,
  currentEvaluation,
  agreementMetrics,
  tokenUsage,
  error,
  connected,
  isRunning,
  isCompleted,
  hasError,
  progressPercent,
  sortedResults,
  startEvaluation,
  stopEvaluation,
  clearError,
  fetchProgress,
  fetchAgreementMetrics
} = useLLMEvaluation(scenarioId.value)

// Local state
const loading = ref(true)
const scenario = ref(null)
const activeTab = ref('results')
const expandedResult = ref(null)
const showError = ref(false)
const showDetailDialog = ref(false)
const selectedResult = ref(null)
const availableModels = ref([])
const availableTemplates = ref([])

// Watch for errors
watch(error, (newError) => {
  if (newError) {
    showError.value = true
  }
})

// Auto-switch to live tab when evaluation starts
watch(isRunning, (running) => {
  if (running && activeTab.value !== 'live') {
    activeTab.value = 'live'
  }
})

// Methods
function goBack() {
  router.push({ name: 'EvaluationHub' })
}

function toggleResult(resultId) {
  expandedResult.value = expandedResult.value === resultId ? null : resultId
}

function viewResultDetails(result) {
  selectedResult.value = result
  showDetailDialog.value = true
}

function closeDetailDialog() {
  showDetailDialog.value = false
  selectedResult.value = null
}

async function handleStart(options) {
  try {
    await startEvaluation(options)
    activeTab.value = 'live'
  } catch (err) {
    console.error('Failed to start evaluation:', err)
  }
}

async function handleStop() {
  try {
    await stopEvaluation()
    activeTab.value = 'results'
  } catch (err) {
    console.error('Failed to stop evaluation:', err)
  }
}

async function fetchScenario() {
  try {
    const response = await axios.get(`/api/scenarios/${scenarioId.value}`)
    scenario.value = response.data
  } catch (err) {
    console.error('Failed to fetch scenario:', err)
  }
}

async function fetchAvailableModels() {
  try {
    const response = await axios.get('/api/llm/models/available')
    availableModels.value = response.data.models || []
  } catch (err) {
    console.error('Failed to fetch available models:', err)
  }
}

async function fetchAvailableTemplates() {
  try {
    const response = await axios.get('/api/evaluation/prompt-templates', {
      params: { task_type: scenario.value?.function_type?.name }
    })
    availableTemplates.value = response.data.templates || []
  } catch (err) {
    console.error('Failed to fetch templates:', err)
  }
}

// Initialize
onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchScenario(),
      fetchAvailableModels(),
      fetchProgress()
    ])
    // Fetch templates after scenario is loaded
    if (scenario.value) {
      await fetchAvailableTemplates()
    }
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.evaluation-assistant-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header {
  flex-shrink: 0;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgb(var(--v-theme-surface));
}

.header-content {
  display: flex;
  align-items: center;
}

.header-info {
  display: flex;
  flex-direction: column;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.page-subtitle {
  font-size: 0.875rem;
}

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.loading-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.left-panel {
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  overflow: hidden;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-background));
  overflow: hidden;
}

.resize-divider {
  width: 4px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  cursor: col-resize;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgb(var(--v-theme-primary));
}

.resize-handle {
  width: 2px;
  height: 32px;
  background: rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 1px;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.progress-section,
.controls-section,
.metrics-section {
  margin-bottom: 16px;
}

.panel-tabs {
  flex-shrink: 0;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgb(var(--v-theme-surface));
}

.tab-window {
  height: 100%;
}

.results-container,
.live-container,
.comparison-container {
  min-height: 100%;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.live-evaluation {
  padding: 16px;
}

.pulse-chip {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
</style>
