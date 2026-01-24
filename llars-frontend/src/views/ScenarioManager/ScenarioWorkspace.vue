<template>
  <div class="scenario-workspace" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="workspace-header">
      <div class="header-left">
        <LBtn variant="text" @click="goBack" class="back-btn">
          <LIcon>mdi-arrow-left</LIcon>
        </LBtn>
        <div class="type-icon" :style="{ backgroundColor: typeColor + '20' }" v-if="scenario">
          <LIcon :color="typeColor">{{ typeIcon }}</LIcon>
        </div>
        <div class="header-text">
          <h1 class="title">{{ scenario?.scenario_name || $t('common.loading') }}</h1>
          <div class="subtitle-row">
            <LTag :variant="statusVariant" size="sm">{{ statusLabel }}</LTag>
            <span class="scenario-type" v-if="scenario">{{ typeName }}</span>
          </div>
        </div>
      </div>
      <div class="header-right">
        <LBtn variant="text" @click="refreshScenario" :loading="loading">
          <LIcon>mdi-refresh</LIcon>
        </LBtn>
        <v-menu v-if="isOwner">
          <template #activator="{ props }">
            <LBtn variant="text" v-bind="props">
              <LIcon>mdi-dots-vertical</LIcon>
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="showSettings = true">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-cog-outline</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.settings') }}</v-list-item-title>
            </v-list-item>
            <v-list-item @click="duplicateScenario">
              <template #prepend>
                <LIcon size="18" class="mr-2">mdi-content-copy</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.duplicate') }}</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item @click="confirmArchive" class="text-warning">
              <template #prepend>
                <LIcon size="18" class="mr-2" color="warning">mdi-archive-outline</LIcon>
              </template>
              <v-list-item-title>{{ $t('scenarioManager.actions.archive') }}</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>

    <!-- Quick Stats Bar (only for owners) -->
    <div class="stats-bar" v-if="scenario && isOwner">
      <div class="stat-item">
        <LIcon size="18" color="grey">mdi-email-outline</LIcon>
        <span class="stat-value">{{ scenario.thread_count || 0 }}</span>
        <span class="stat-label">{{ $t('scenarioManager.stats.threads') }}</span>
      </div>
      <div class="stat-item">
        <LIcon size="18" color="grey">mdi-account-multiple-outline</LIcon>
        <span class="stat-value">{{ scenario.user_count || 0 }}</span>
        <span class="stat-label">{{ $t('scenarioManager.stats.evaluators') }}</span>
      </div>
      <div class="stat-item" v-if="scenario.llm_evaluator_count">
        <LIcon size="18" color="grey">mdi-robot-outline</LIcon>
        <span class="stat-value">{{ scenario.llm_evaluator_count }}</span>
        <span class="stat-label">{{ $t('scenarioManager.stats.llmModels') }}</span>
      </div>
      <div class="stat-item progress-stat" v-if="progressPercent !== null">
        <div class="progress-mini">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
        <span class="stat-value">{{ progressPercent }}%</span>
        <span class="stat-label">{{ $t('scenarioManager.stats.complete') }}</span>
      </div>
      <div class="stat-item live-indicator" v-if="statsConnected">
        <span class="live-dot"></span>
        <span class="stat-label">Live</span>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-navigation">
      <LTabs v-model="activeTab" :tabs="tabs" />
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Loading State -->
      <div v-if="loading && !scenario" class="loading-state">
        <v-progress-circular indeterminate color="primary" size="48" />
        <span>{{ $t('common.loading') }}</span>
      </div>

      <!-- Overview Tab -->
      <ScenarioOverviewTab
        v-else-if="activeTab === 'overview'"
        :scenario="scenario"
        :live-stats="liveStats"
        @import-data="activeTab = 'data'"
        @start-evaluation="activeTab = 'evaluation'"
        @view-results="activeTab = 'evaluation'"
      />

      <!-- Data Tab -->
      <ScenarioDataTab
        v-else-if="activeTab === 'data'"
        :scenario="scenario"
        @data-imported="refreshScenario"
      />

      <!-- Evaluation Tab (EvaluationAssistant Integration) -->
      <ScenarioEvaluationTab
        v-else-if="activeTab === 'evaluation'"
        :scenario="scenario"
        :live-stats="liveStats"
        @evaluation-complete="refreshScenario"
      />

      <!-- Team Tab -->
      <ScenarioTeamTab
        v-else-if="activeTab === 'team'"
        :scenario="scenario"
        :live-stats="liveStats"
        @team-updated="refreshScenario"
      />
    </div>

    <!-- Settings Dialog -->
    <v-dialog v-model="showSettings" max-width="600">
      <ScenarioSettingsDialog
        v-if="showSettings"
        :scenario="scenario"
        @close="showSettings = false"
        @saved="onSettingsSaved"
      />
    </v-dialog>

    <!-- Duplicate Dialog -->
    <v-dialog v-model="showDuplicateDialog" max-width="450">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="primary" class="mr-2">mdi-content-copy</LIcon>
          {{ $t('scenarioManager.duplicate.title') }}
        </v-card-title>
        <v-card-text>
          <p class="mb-4">{{ $t('scenarioManager.duplicate.description', { name: scenario?.scenario_name }) }}</p>
          <v-text-field
            v-model="duplicateName"
            :label="$t('scenarioManager.duplicate.newName')"
            :placeholder="$t('scenarioManager.duplicate.newNamePlaceholder', { name: scenario?.scenario_name })"
            variant="outlined"
            density="comfortable"
            autofocus
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showDuplicateDialog = false" :disabled="duplicating">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="primary" @click="executeDuplicate" :loading="duplicating">
            <LIcon start>mdi-content-copy</LIcon>
            {{ $t('scenarioManager.actions.duplicate') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Archive Dialog -->
    <v-dialog v-model="showArchiveDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="warning" class="mr-2">mdi-archive-outline</LIcon>
          {{ $t('scenarioManager.archive.title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('scenarioManager.archive.confirm', { name: scenario?.scenario_name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showArchiveDialog = false" :disabled="archiving">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="warning" @click="executeArchive" :loading="archiving">
            <LIcon start>mdi-archive-outline</LIcon>
            {{ $t('scenarioManager.actions.archive') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useMobile } from '@/composables/useMobile'
import { useScenarioManager } from './composables/useScenarioManager'
import { useScenarioStats } from './composables/useScenarioStats'
import ScenarioOverviewTab from './components/tabs/ScenarioOverviewTab.vue'
import ScenarioDataTab from './components/tabs/ScenarioDataTab.vue'
import ScenarioEvaluationTab from './components/tabs/ScenarioEvaluationTab.vue'
import ScenarioTeamTab from './components/tabs/ScenarioTeamTab.vue'
import ScenarioSettingsDialog from './components/ScenarioSettingsDialog.vue'

const props = defineProps({
  id: {
    type: [String, Number],
    required: true
  }
})

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { isMobile } = useMobile()

const {
  currentScenario: scenario,
  loading,
  fetchScenario,
  updateScenario,
  duplicateScenario: duplicateScenarioApi,
  archiveScenario: archiveScenarioApi
} = useScenarioManager()

// Real-time stats subscription
const scenarioIdRef = computed(() => props.id ? Number(props.id) : null)
const {
  stats,
  userStatsList,
  humanProgress: liveHumanProgress,
  llmProgress: liveLlmProgress,
  overallProgress: liveOverallProgress,
  agreementMetrics: liveAgreementMetrics,
  connected: statsConnected,
  functionType: liveFunctionType,
  refresh: refreshStats
} = useScenarioStats(scenarioIdRef)

// UI State
const activeTab = ref('overview')
const showSettings = ref(false)
const showDuplicateDialog = ref(false)
const showArchiveDialog = ref(false)
const duplicateName = ref('')
const duplicating = ref(false)
const archiving = ref(false)
const snackbar = ref({ show: false, message: '', color: 'success' })

// Access control: Check if user is owner or in evaluate mode
const isEvaluatorMode = computed(() => {
  return route.query.mode === 'evaluate' || scenario.value?.is_owner === false
})

const isOwner = computed(() => scenario.value?.is_owner === true)

// Tabs configuration - evaluators only see the evaluation tab
const tabs = computed(() => {
  if (isEvaluatorMode.value) {
    return [
      { value: 'evaluation', label: t('scenarioManager.tabs.evaluation'), icon: 'mdi-clipboard-edit-outline' }
    ]
  }
  return [
    { value: 'overview', label: t('scenarioManager.tabs.overview'), icon: 'mdi-view-dashboard-outline' },
    { value: 'data', label: t('scenarioManager.tabs.data'), icon: 'mdi-database-outline' },
    { value: 'evaluation', label: t('scenarioManager.tabs.evaluation'), icon: 'mdi-clipboard-edit-outline' },
    { value: 'team', label: t('scenarioManager.tabs.team'), icon: 'mdi-account-group-outline' }
  ]
})

// Type mapping
const typeConfig = {
  1: { icon: 'mdi-podium', color: '#b0ca97', name: 'ranking', variant: 'success' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', name: 'rating', variant: 'warning' },
  3: { icon: 'mdi-email-outline', color: '#88c4c8', name: 'mailRating', variant: 'info' },
  4: { icon: 'mdi-compare-horizontal', color: '#c4a0d4', name: 'comparison', variant: 'primary' },
  5: { icon: 'mdi-shield-search', color: '#e8a087', name: 'authenticity', variant: 'danger' }
}

// Status mapping
const statusConfig = {
  draft: { variant: 'gray', label: 'draft' },
  data_collection: { variant: 'info', label: 'dataCollection' },
  evaluating: { variant: 'info', label: 'evaluating' },
  analyzing: { variant: 'info', label: 'analyzing' },
  completed: { variant: 'success', label: 'completed' },
  archived: { variant: 'gray', label: 'archived' }
}

// Computed
const typeIcon = computed(() => {
  return typeConfig[scenario.value?.function_type_id]?.icon || 'mdi-clipboard-outline'
})

const typeColor = computed(() => {
  return typeConfig[scenario.value?.function_type_id]?.color || '#888'
})

const typeName = computed(() => {
  const key = typeConfig[scenario.value?.function_type_id]?.name || 'unknown'
  return t(`scenarioManager.types.${key}`)
})

const statusVariant = computed(() => {
  return statusConfig[scenario.value?.status]?.variant || 'gray'
})

const statusLabel = computed(() => {
  const key = statusConfig[scenario.value?.status]?.label || 'draft'
  return t(`scenarioManager.status.${key}`)
})

const progressPercent = computed(() => {
  // Use live stats if available
  if (liveOverallProgress.value > 0) return liveOverallProgress.value
  // Fallback to scenario stats
  if (!scenario.value?.stats) return null
  const { completed, total } = scenario.value.stats
  if (!total) return null
  return Math.round((completed / total) * 100)
})

// Combined stats for child components
const liveStats = computed(() => ({
  humanProgress: liveHumanProgress.value,
  llmProgress: liveLlmProgress.value,
  overallProgress: liveOverallProgress.value,
  agreementMetrics: liveAgreementMetrics.value,
  userStatsList: userStatsList.value,
  connected: statsConnected.value,
  ratingDistribution: stats.value?.rating_distribution,
  pairwiseAgreement: stats.value?.pairwise_agreement,
  functionType: liveFunctionType.value,
  bucket_distribution: stats.value?.bucket_distribution,
  ranking_agreement: stats.value?.ranking_agreement
}))

// Methods
function goBack() {
  router.push({ name: 'ScenarioManager' })
}

async function refreshScenario() {
  await Promise.all([
    fetchScenario(props.id),
    refreshStats()
  ])
}

function duplicateScenario() {
  duplicateName.value = t('scenarioManager.duplicate.newNamePlaceholder', { name: scenario.value?.scenario_name })
  showDuplicateDialog.value = true
}

async function executeDuplicate() {
  if (!scenario.value) return
  duplicating.value = true
  try {
    const newScenario = await duplicateScenarioApi(scenario.value.id, duplicateName.value || null)
    showDuplicateDialog.value = false
    snackbar.value = {
      show: true,
      message: t('scenarioManager.duplicate.success'),
      color: 'success'
    }
    // Navigate to the new scenario
    router.push({ name: 'ScenarioWorkspace', params: { id: newScenario.id } })
  } catch (err) {
    snackbar.value = {
      show: true,
      message: err.response?.data?.error || 'Failed to duplicate scenario',
      color: 'error'
    }
  } finally {
    duplicating.value = false
  }
}

function confirmArchive() {
  showArchiveDialog.value = true
}

async function executeArchive() {
  if (!scenario.value) return
  archiving.value = true
  try {
    await archiveScenarioApi(scenario.value.id)
    showArchiveDialog.value = false
    snackbar.value = {
      show: true,
      message: t('scenarioManager.archive.success'),
      color: 'success'
    }
    // Navigate back to scenario list
    router.push({ name: 'ScenarioManager' })
  } catch (err) {
    snackbar.value = {
      show: true,
      message: err.response?.data?.error || 'Failed to archive scenario',
      color: 'error'
    }
  } finally {
    archiving.value = false
  }
}

async function onSettingsSaved(updates) {
  showSettings.value = false
  await refreshScenario()
}

// Watch for tab query parameter (read from URL)
watch(() => route.query.tab, (newTab) => {
  if (newTab && tabs.value.some(t => t.value === newTab)) {
    activeTab.value = newTab
  }
}, { immediate: true })

// Update URL when tab changes (for shareable links)
watch(activeTab, (newTab) => {
  if (newTab && newTab !== route.query.tab) {
    router.replace({ query: { ...route.query, tab: newTab } })
  }
})

// Auto-switch to evaluation tab in evaluator mode
watch(isEvaluatorMode, (isEvaluator) => {
  if (isEvaluator && activeTab.value !== 'evaluation') {
    activeTab.value = 'evaluation'
  }
}, { immediate: true })

onMounted(() => {
  fetchScenario(props.id)
})
</script>

<style scoped>
.scenario-workspace {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

/* Header */
.workspace-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  margin-left: -8px;
}

.type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
}

.subtitle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.scenario-type {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Stats Bar */
.stats-bar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-value {
  font-weight: 600;
  font-size: 0.95rem;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.progress-stat {
  flex: 1;
  max-width: 200px;
}

.progress-mini {
  flex: 1;
  height: 6px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-mini .progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* Live Indicator */
.live-indicator {
  margin-left: auto;
}

.live-dot {
  width: 8px;
  height: 8px;
  background-color: #4caf50;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(76, 175, 80, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(76, 175, 80, 0);
  }
}

/* Tab Navigation */
.tab-navigation {
  flex-shrink: 0;
  padding: 0 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Tab Content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 64px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Mobile Styles */
.scenario-workspace.is-mobile {
  height: calc(100vh - 88px);
}

.scenario-workspace.is-mobile .workspace-header {
  padding: 12px 16px;
}

.scenario-workspace.is-mobile .title {
  font-size: 1.1rem;
}

.scenario-workspace.is-mobile .stats-bar {
  padding: 8px 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.scenario-workspace.is-mobile .tab-content {
  padding: 16px;
}
</style>
