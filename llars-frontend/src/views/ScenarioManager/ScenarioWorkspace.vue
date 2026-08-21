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
        <v-menu v-if="canManage">
          <template #activator="{ props }">
            <LBtn variant="text" v-bind="props">
              <LIcon>mdi-dots-vertical</LIcon>
            </LBtn>
          </template>
          <v-list density="compact">
            <v-list-item @click="activeTab = 'settings'">
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
            <template v-if="isOwner">
              <v-divider />
              <v-list-item @click="confirmArchive" class="text-warning">
                <template #prepend>
                  <LIcon size="18" class="mr-2" color="warning">mdi-archive-outline</LIcon>
                </template>
                <v-list-item-title>{{ $t('scenarioManager.actions.archive') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="confirmDelete" class="text-error">
                <template #prepend>
                  <LIcon size="18" class="mr-2" color="error">mdi-delete-outline</LIcon>
                </template>
                <v-list-item-title>{{ $t('scenarioManager.actions.delete') }}</v-list-item-title>
              </v-list-item>
            </template>
          </v-list>
        </v-menu>
      </div>
    </div>

    <!-- Quick Stats Bar (for owners, managers, viewers) -->
    <div class="stats-bar" v-if="scenario && canViewAll">
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
      <LTabs v-model="activeTab" :tabs="tabs" variant="pill" />
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
        :live-stats="liveStats"
        @data-imported="refreshScenario"
      />

      <!-- Evaluation Tab (EvaluationAssistant Integration) -->
      <ScenarioEvaluationTab
        v-else-if="activeTab === 'evaluation'"
        :scenario="scenario"
        :live-stats="liveStats"
        @evaluation-complete="refreshScenario"
      />

      <!-- Assessors Tab (formerly Team) -->
      <ScenarioTeamTab
        v-else-if="activeTab === 'assessors'"
        :scenario="scenario"
        :live-stats="liveStats"
        :can-manage="canManage"
        @team-updated="refreshScenario"
        @refresh-stats="refreshStats"
      />

      <!-- Settings Tab (Owner/Manager only) -->
      <ScenarioSettingsTab
        v-else-if="activeTab === 'settings'"
        :scenario="scenario"
        :is-owner="isOwner"
        :can-manage="canManage"
        @saved="onSettingsSaved"
        @team-updated="refreshScenario"
      />
    </div>

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

    <!-- Delete Dialog (irreversible — drops the scenario + all its
         scenario_users / scenario_threads / comparison_sessions) -->
    <v-dialog v-model="showDeleteDialog" max-width="440">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="error" class="mr-2">mdi-delete-outline</LIcon>
          {{ $t('scenarioManager.delete.title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('scenarioManager.delete.confirm', { name: scenario?.scenario_name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showDeleteDialog = false" :disabled="deleting">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" @click="executeDelete" :loading="deleting">
            <LIcon start>mdi-delete-outline</LIcon>
            {{ $t('scenarioManager.actions.delete') }}
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
/**
 * Scenario Workspace Component
 *
 * Main workspace for managing a single evaluation scenario.
 *
 * SCHEMA GROUND TRUTH:
 * -------------------
 * Item-Daten werden über die Schema-API abgerufen:
 * - GET /api/scenarios/{id}/schema - Szenario-Übersicht
 * - GET /api/scenarios/{id}/items/{item_id}/schema - Item im Schema-Format
 *
 * Schema-Definitionen:
 * - Backend: app/schemas/evaluation_data_schemas.py
 * - Frontend: src/schemas/evaluationSchemas.js
 * - Composable: src/composables/useEvaluationSchema.js
 *
 * Dokumentation: .claude/plans/evaluation-data-schemas.md
 */
import { ref, computed, onMounted, onUnmounted, watch, provide } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useMobile } from '@/composables/useMobile'
import { useScenarioManager } from './composables/useScenarioManager'
import { useScenarioStats } from './composables/useScenarioStats'
import ScenarioOverviewTab from './components/tabs/ScenarioOverviewTab.vue'
import ScenarioDataTab from './components/tabs/ScenarioDataTab.vue'
import ScenarioEvaluationTab from './components/tabs/ScenarioEvaluationTab.vue'
import ScenarioTeamTab from './components/tabs/ScenarioTeamTab.vue'
import ScenarioSettingsTab from './components/tabs/ScenarioSettingsTab.vue'

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
  archiveScenario: archiveScenarioApi,
  deleteScenarioById,
  getScenarioTeam
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
  hasHumans,
  hasLLMs,
  refresh: refreshStats
} = useScenarioStats(scenarioIdRef)

// UI State
const activeTab = ref('overview')
const showDuplicateDialog = ref(false)
const showArchiveDialog = ref(false)
const duplicateName = ref('')
const duplicating = ref(false)
const archiving = ref(false)
const showDeleteDialog = ref(false)
const deleting = ref(false)
const snackbar = ref({ show: false, message: '', color: 'success' })

// Access control — prefer new manager_role field, fall back to legacy fields for backwards compat
const isOwner = computed(() =>
  scenario.value?.manager_role === 'owner' || scenario.value?.is_owner === true
)
const canManage = computed(() =>
  ['owner', 'editor'].includes(scenario.value?.manager_role) ||
  isOwner.value || scenario.value?.can_manage === true
)
const canViewAll = computed(() =>
  (scenario.value?.manager_role && scenario.value?.manager_role !== 'none') ||
  canManage.value || scenario.value?.is_viewer || scenario.value?.user_role === 'Viewer'
)

// User-origin map (keyed by username AND display_name -> origin object) shared
// with the Overview and Evaluation tabs, which render origins by name rather
// than from a full team payload. Loaded once here from the management-gated
// /team endpoint; Settings + Assessors use their own team payload directly.
// Viewers (non-managers) get a 403 on /team by design -> map stays empty -> no
// pills render, which is the intended access boundary for "where users came from".
const scenarioOrigins = ref({})       // name -> origin (per-user lookup)
const scenarioOriginsList = ref([])   // one origin per member (legend, no double count)
provide('scenarioOrigins', scenarioOrigins)
provide('scenarioOriginsList', scenarioOriginsList)

async function loadScenarioOrigins() {
  if (!scenarioIdRef.value || !canManage.value) {
    scenarioOrigins.value = {}
    scenarioOriginsList.value = []
    return
  }
  try {
    const data = await getScenarioTeam(scenarioIdRef.value)
    const map = {}
    const list = []
    for (const m of (data?.team || [])) {
      if (!m.origin) continue
      // Map is keyed by both username and display_name so name-based lookups in
      // the Overview/Evaluation tabs hit regardless of which is shown. The list
      // holds one entry per member so legend counts aren't doubled.
      if (m.username) map[m.username] = m.origin
      if (m.display_name) map[m.display_name] = m.origin
      if (!m.is_ai) list.push(m.origin)
    }
    scenarioOrigins.value = map
    scenarioOriginsList.value = list
  } catch (err) {
    scenarioOrigins.value = {}
    scenarioOriginsList.value = []
  }
}

// Tabs configuration based on manager_role:
// - Owner/Editor (manager_role=owner|editor): Overview | Data | Evaluation | Assessors | Settings
// - Viewer (manager_role=viewer): Overview | Data | Evaluation | Assessors (no settings)
// - Pure Assessor/Eval-Viewer (manager_role=none or not set): redirect to evaluation
const tabs = computed(() => {
  const baseTabs = [
    { value: 'overview', label: t('scenarioManager.tabs.overview'), icon: 'mdi-view-dashboard-outline' },
    { value: 'data', label: t('scenarioManager.tabs.data'), icon: 'mdi-database-outline' },
    { value: 'evaluation', label: t('scenarioManager.tabs.evaluation'), icon: 'mdi-clipboard-edit-outline' },
    { value: 'assessors', label: t('scenarioManager.tabs.assessors'), icon: 'mdi-account-group-outline' }
  ]

  if (canManage.value) {
    // Owner/Manager: all tabs + settings
    return [
      ...baseTabs,
      { value: 'settings', label: t('scenarioManager.tabs.settings'), icon: 'mdi-cog-outline' }
    ]
  }

  if (canViewAll.value) {
    // Viewer: all tabs except settings
    return baseTabs
  }

  // Pure assessor: evaluation only
  return [
    { value: 'evaluation', label: t('scenarioManager.tabs.evaluation'), icon: 'mdi-clipboard-edit-outline' }
  ]
})

// Type mapping
const typeConfig = {
  1: { icon: 'mdi-podium', color: '#b0ca97', name: 'ranking', variant: 'success' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', name: 'rating', variant: 'warning' },
  3: { icon: 'mdi-email-outline', color: '#88c4c8', name: 'mailRating', variant: 'info' },
  4: { icon: 'mdi-compare-horizontal', color: '#c4a0d4', name: 'comparison', variant: 'primary' },
  5: { icon: 'mdi-shield-search', color: '#e8a087', name: 'authenticity', variant: 'danger' },
  7: { icon: 'mdi-tag-multiple-outline', color: '#98d4bb', name: 'labeling', variant: 'success' },
  8: { icon: 'mdi-forum-outline', color: '#88c4c8', name: 'communicationComparison', variant: 'info' },
  // 9 = conversation_labeling: item is a conversation, the vote is a span in it
  9: { icon: 'mdi-tag-multiple-outline', color: '#6FA8A0', name: 'conversationLabeling', variant: 'accent' }
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
  ratingProvenanceAnalysis: stats.value?.rating_provenance_analysis,
  conversationProvenance: stats.value?.conversation_provenance,
  authenticityProvenance: stats.value?.authenticity_provenance,
  // Unified pairwise agreement - prefer pairwise_agreement, fallback to ranking_agreement
  pairwiseAgreement: stats.value?.pairwise_agreement || stats.value?.ranking_agreement,
  functionType: liveFunctionType.value,
  bucket_distribution: stats.value?.bucket_distribution,
  provenanceAnalysis: stats.value?.provenance_analysis,
  ranking_agreement: stats.value?.ranking_agreement,  // Deprecated, kept for backwards compatibility
  hasHumans: hasHumans.value,
  hasLLMs: hasLLMs.value
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
  // Team membership may have changed (invite/remove) -> refresh origin map.
  loadScenarioOrigins()
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

function confirmDelete() {
  showDeleteDialog.value = true
}

async function executeDelete() {
  if (!scenario.value) return
  deleting.value = true
  try {
    await deleteScenarioById(scenario.value.id)
    showDeleteDialog.value = false
    snackbar.value = {
      show: true,
      message: t('scenarioManager.delete.success'),
      color: 'success'
    }
    router.push({ name: 'ScenarioManager' })
  } catch (err) {
    snackbar.value = {
      show: true,
      message: err.response?.data?.error || err.message || 'Failed to delete scenario',
      color: 'error'
    }
  } finally {
    deleting.value = false
  }
}

async function onSettingsSaved() {
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
  // Refresh stats immediately when switching back to overview tab
  // so user sees the latest data without waiting for next socket event
  if (newTab === 'overview') {
    refreshStats()
  }
})

// Redirect pure assessors/eval-viewers to the dedicated evaluation interface.
// Users with a real manager_role (owner/editor/viewer) stay in the workspace.
watch(scenario, (sc) => {
  if (!sc) return
  const role = sc.manager_role
  // New field: redirect when manager_role is 'none' or missing
  const hasManagerAccess = role && role !== 'none'
  // Legacy fallback: keep old checks so older backend responses still work
  const hasLegacyAccess = sc.is_owner || sc.can_manage || sc.user_role === 'Viewer'

  if (!hasManagerAccess && !hasLegacyAccess) {
    // Pure assessors should use the evaluation items overview, not the workspace
    router.replace({ name: 'EvaluationItemsOverview', params: { scenarioId: sc.id } })
  }
}, { immediate: true })

onMounted(async () => {
  await fetchScenario(props.id)
  refreshStats()  // Also load stats initially
  loadScenarioOrigins()  // canManage is settled now that the scenario is loaded
})

// Reload origins when navigating to a different scenario (component may be
// reused on route param change) or once the loaded scenario settles access.
watch(scenarioIdRef, () => loadScenarioOrigins())
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
  padding: 8px 24px 12px;
  background-color: rgb(var(--v-theme-surface));
}

.tab-navigation :deep(.l-tabs) {
  margin-bottom: 0;
}

/* Tab Content */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
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

/*
 * Viewport-based responsive fixes (tablet + small screens).
 * The .is-mobile class above is driven by JS state; these media queries
 * cover the tablet range (e.g. ~552-960px) where the 5-item .stats-bar
 * (~838px) overflows the viewport. Scoped to <=960px so desktop never
 * regresses.
 */
@media (max-width: 960px) {
  .workspace-header {
    padding: 12px 16px;
  }

  /* Allow the title to shrink and ellipsis instead of pushing actions off-screen */
  .header-text {
    min-width: 0;
  }

  .title {
    font-size: 1.1rem;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* BLOCKER: wrap the 5 stat items so they fit narrow viewports without overflow */
  .stats-bar {
    flex-wrap: wrap;
    gap: 12px;
    padding: 8px 16px;
  }

  .tab-navigation {
    padding: 8px 12px;
  }

  .tab-navigation :deep(.l-tab) {
    padding: 8px 14px;
  }

  .tab-content {
    padding: 16px;
  }

  /* Keep this view's dialogs from touching screen edges on tablets/phones */
  :deep(.v-dialog) {
    width: 90vw;
  }
}
</style>
