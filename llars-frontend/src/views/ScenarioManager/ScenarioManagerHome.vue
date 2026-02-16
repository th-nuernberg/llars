<template>
  <div class="scenario-manager">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <LIcon size="28" color="primary">mdi-clipboard-check-multiple-outline</LIcon>
        <h1 class="title">{{ $t('scenarioManager.title') }}</h1>
      </div>
      <div class="header-right" v-if="activeTab === 'own'">
        <LBtn variant="primary" @click="showWizard = true">
          <LIcon start>mdi-plus</LIcon>
          {{ $t('scenarioManager.newScenario') }}
        </LBtn>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="tab-bar">
      <LTabs v-model="activeTab" :tabs="tabs" variant="underlined" />
    </div>

    <!-- Content -->
    <div class="content">
      <!-- Loading State -->
      <div v-if="loading" class="scenarios-grid">
        <div v-for="n in 3" :key="n" class="skeleton-card">
          <v-skeleton-loader type="card" />
        </div>
      </div>

      <!-- My Scenarios Tab -->
      <template v-else-if="activeTab === 'own'">
        <div v-if="ownScenarios.length > 0" class="scenarios-grid">
          <div
            v-for="scenario in ownScenarios"
            :key="`own-${scenario.id}`"
            class="scenario-card-observer-target"
            :data-scenario-id="scenario.id"
            :ref="(element) => registerScenarioCard(scenario.id, element)"
          >
            <ScenarioOwnerCard
              :scenario="scenario"
              @open="openScenario"
              @settings="openSettings"
              @duplicate="duplicateScenario"
              @archive="archiveScenario"
              @delete="confirmDelete"
            />
          </div>
        </div>
        <div v-else class="empty-state">
          <LIcon size="64" color="grey-lighten-1">mdi-clipboard-plus-outline</LIcon>
          <h3>{{ $t('scenarioManager.empty.ownTitle') }}</h3>
          <p>{{ $t('scenarioManager.empty.ownDescription') }}</p>
          <LBtn variant="primary" @click="showWizard = true">
            <LIcon start>mdi-plus</LIcon>
            {{ $t('scenarioManager.newScenario') }}
          </LBtn>
        </div>
      </template>

      <!-- Invitations Tab -->
      <template v-else-if="activeTab === 'invitations'">
        <div v-if="invitedScenarios.length > 0" class="scenarios-grid">
          <div
            v-for="scenario in invitedScenarios"
            :key="`invitation-${scenario.id}`"
            class="scenario-card-observer-target"
            :data-scenario-id="scenario.id"
            :ref="(element) => registerScenarioCard(scenario.id, element)"
          >
            <ScenarioInviteCard
              :scenario="scenario"
              @accept="acceptInvitation"
              @reject="rejectInvitation"
              @evaluate="goToEvaluation"
              @leave="leaveScenario"
            />
          </div>
        </div>
        <div v-else class="empty-state">
          <LIcon size="64" color="grey-lighten-1">mdi-email-outline</LIcon>
          <h3>{{ $t('scenarioManager.empty.invitationsTitle') }}</h3>
          <p>{{ $t('scenarioManager.empty.invitationsDescription') }}</p>
        </div>
      </template>

      <!-- Data Format Tab -->
      <template v-else-if="activeTab === 'data-format'">
        <DataFormatGuide />
      </template>
    </div>

    <!-- New Scenario Wizard -->
    <v-dialog v-model="showWizard" max-width="900" persistent>
      <ScenarioWizard
        v-if="showWizard"
        :generation-job-id="generationJobId"
        @close="closeWizard"
        @created="onScenarioCreated"
      />
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="d-flex align-center">
          <LIcon color="error" class="mr-2">mdi-alert-circle-outline</LIcon>
          {{ $t('scenarioManager.delete.title') }}
        </v-card-title>
        <v-card-text>
          {{ $t('scenarioManager.delete.confirm', { name: scenarioToDelete?.scenario_name }) }}
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="text" @click="showDeleteDialog = false">
            {{ $t('common.cancel') }}
          </LBtn>
          <LBtn variant="danger" @click="deleteScenario" :loading="deleting">
            {{ $t('common.delete') }}
          </LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount, onMounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useScenarioManager } from './composables/useScenarioManager'
import ScenarioOwnerCard from './components/ScenarioOwnerCard.vue'
import ScenarioInviteCard from './components/ScenarioInviteCard.vue'
import ScenarioWizard from './components/ScenarioWizard.vue'
import DataFormatGuide from './components/DataFormatGuide.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const { tokenParsed } = useAuth()

const {
  scenarios,
  loading,
  fetchScenarios,
  fetchScenarioStats,
  deleteScenarioById,
  respondToInvitation,
  duplicateScenario: duplicateScenarioApi,
  archiveScenario: archiveScenarioApi
} = useScenarioManager()

const currentUserId = computed(() => {
  return tokenParsed.value?.sub ? String(tokenParsed.value.sub) : ''
})

const currentUsername = computed(() => {
  const storedUsername = typeof window !== 'undefined' ? localStorage.getItem('username') : ''
  return tokenParsed.value?.preferred_username ||
    tokenParsed.value?.username ||
    tokenParsed.value?.name ||
    storedUsername ||
    ''
})

const scenarioCardElements = new Map()
const pendingScenarioStats = []
const queuedScenarioIds = new Set()
const loadingScenarioIds = new Set()
const resolvedScenarioIds = new Set()
const cachedScenarioStats = new Map()
const cachedUserProgress = new Map()
const MAX_CONCURRENT_STATS_REQUESTS = 3

let scenarioCardObserver = null
let activeStatsRequests = 0

// UI State
// Read initial tab from URL query parameter
// Map URL tab values to internal tab values
const tabMapping = {
  'scenarios': 'own',
  'own': 'own',
  'invitations': 'invitations'
}
const urlTab = route.query.tab
const initialTab = tabMapping[urlTab] || 'own'
const activeTab = ref(initialTab)
const showWizard = ref(false)

// Sync tab with URL
watch(activeTab, (newTab) => {
  const query = { ...route.query }
  // Use user-friendly URL names
  if (newTab === 'own') {
    query.tab = 'scenarios'
  } else {
    query.tab = newTab
  }
  router.replace({ query })
})
const showDeleteDialog = ref(false)
const scenarioToDelete = ref(null)
const deleting = ref(false)

// Generation job ID for pre-loading data in wizard
const generationJobId = ref(null)

// Tabs
const tabs = computed(() => [
  {
    value: 'own',
    label: t('scenarioManager.tabs.myScenarios'),
    badge: ownScenarios.value.length || undefined
  },
  {
    value: 'invitations',
    label: t('scenarioManager.tabs.invitations'),
    badge: invitedScenarios.value.length || undefined
  },
  {
    value: 'data-format',
    label: t('scenarioManager.tabs.dataFormat')
  }
])

// Filtered Lists
const ownScenarios = computed(() => {
  return scenarios.value
    .filter(s => s.is_owner)
    .sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
})

const invitedScenarios = computed(() => {
  return scenarios.value
    .filter(s => !s.is_owner)
    .sort((a, b) => {
      // Pending first, then by date
      if (a.invitation?.status === 'pending' && b.invitation?.status !== 'pending') return -1
      if (b.invitation?.status === 'pending' && a.invitation?.status !== 'pending') return 1
      return new Date(b.invitation?.invited_at || b.created_at) - new Date(a.invitation?.invited_at || a.created_at)
    })
})

const visibleScenarioIds = computed(() => {
  if (activeTab.value === 'own') {
    return ownScenarios.value.map(scenario => scenario.id)
  }
  if (activeTab.value === 'invitations') {
    return invitedScenarios.value.map(scenario => scenario.id)
  }
  return []
})

function registerScenarioCard(scenarioId, element) {
  const existingElement = scenarioCardElements.get(scenarioId)
  if (existingElement && scenarioCardObserver) {
    scenarioCardObserver.unobserve(existingElement)
  }

  if (!element) {
    scenarioCardElements.delete(scenarioId)
    return
  }

  scenarioCardElements.set(scenarioId, element)
  element.dataset.scenarioId = String(scenarioId)

  if (scenarioCardObserver) {
    scenarioCardObserver.observe(element)
  }
}

function buildUserProgressFromStats(statsData, fallbackTotal = 0) {
  const userId = currentUserId.value
  const username = currentUsername.value
  if (!userId && !username) {
    return null
  }

  const normalizedUsername = username ? username.toLowerCase() : ''
  const raterStats = Array.isArray(statsData?.rater_stats) ? statsData.rater_stats : []
  const evaluatorStats = Array.isArray(statsData?.evaluator_stats) ? statsData.evaluator_stats : []
  const humanEvaluatorStats = evaluatorStats.filter(entry => !entry?.is_llm)
  const allHumanStats = [...raterStats, ...humanEvaluatorStats]
  const userStat = allHumanStats.find(
    entry => (
      (userId && String(entry?.user_id || '') === userId) ||
      (normalizedUsername && String(entry?.username || '').toLowerCase() === normalizedUsername)
    )
  )

  if (!userStat) {
    return null
  }

  const completed = Number(userStat.done_threads ?? userStat.voted_count ?? 0)
  const progressing = Number(userStat.progressing_threads ?? 0)
  const total = Number(userStat.total_threads ?? fallbackTotal)

  return {
    completed: Number.isFinite(completed) ? completed : 0,
    progressing: Number.isFinite(progressing) ? progressing : 0,
    total: Number.isFinite(total) ? total : fallbackTotal
  }
}

function buildScenarioStatsFromResponse(statsData, fallbackScenario) {
  const raterStats = Array.isArray(statsData?.rater_stats) ? statsData.rater_stats : []
  const evaluatorStats = Array.isArray(statsData?.evaluator_stats) ? statsData.evaluator_stats : []
  const humanStats = [...raterStats, ...evaluatorStats.filter(entry => !entry?.is_llm)]
  const llmStats = evaluatorStats.filter(entry => entry?.is_llm)

  const humanCompleted = humanStats.reduce((sum, entry) => sum + Number(entry?.done_threads ?? entry?.voted_count ?? 0), 0)
  const humanTotal = humanStats.reduce((sum, entry) => sum + Number(entry?.total_threads ?? 0), 0)
  const llmCompleted = llmStats.reduce((sum, entry) => sum + Number(entry?.done_threads ?? entry?.voted_count ?? 0), 0)
  const llmTotal = llmStats.reduce((sum, entry) => sum + Number(entry?.total_threads ?? 0), 0)

  const totalEvaluations = Number(
    statsData?.total_evaluations ??
    fallbackScenario?.stats?.total ??
    fallbackScenario?.thread_count ??
    0
  )
  const completedEvaluations = Number(
    statsData?.completed_evaluations ??
    fallbackScenario?.stats?.completed ??
    0
  )

  return {
    total: Number.isFinite(totalEvaluations) ? totalEvaluations : 0,
    completed: Number.isFinite(completedEvaluations) ? completedEvaluations : 0,
    human_total: Number.isFinite(humanTotal) ? humanTotal : 0,
    human_completed: Number.isFinite(humanCompleted) ? humanCompleted : 0,
    llm_total: Number.isFinite(llmTotal) ? llmTotal : 0,
    llm_completed: Number.isFinite(llmCompleted) ? llmCompleted : 0
  }
}

async function loadScenarioStats(scenarioId) {
  try {
    const statsData = await fetchScenarioStats(scenarioId)
    const scenarioIndex = scenarios.value.findIndex(scenario => scenario.id === scenarioId)
    if (scenarioIndex < 0) {
      return
    }

    const scenario = scenarios.value[scenarioIndex]
    const stats = buildScenarioStatsFromResponse(statsData, scenario)
    const userProgress = buildUserProgressFromStats(statsData, scenario.thread_count)

    cachedScenarioStats.set(scenarioId, stats)
    if (userProgress) {
      cachedUserProgress.set(scenarioId, userProgress)
    }

    scenarios.value[scenarioIndex] = {
      ...scenario,
      stats,
      user_progress: userProgress || scenario.user_progress
    }
  } catch (error) {
    console.warn(`Error loading stats for scenario ${scenarioId}:`, error)
  }
}

function processStatsQueue() {
  while (activeStatsRequests < MAX_CONCURRENT_STATS_REQUESTS && pendingScenarioStats.length > 0) {
    const scenarioId = pendingScenarioStats.shift()
    queuedScenarioIds.delete(scenarioId)

    if (resolvedScenarioIds.has(scenarioId) || loadingScenarioIds.has(scenarioId)) {
      continue
    }

    activeStatsRequests += 1
    loadingScenarioIds.add(scenarioId)

    loadScenarioStats(scenarioId)
      .finally(() => {
        activeStatsRequests -= 1
        loadingScenarioIds.delete(scenarioId)
        resolvedScenarioIds.add(scenarioId)
        processStatsQueue()
      })
  }
}

function queueScenarioStatsLoad(scenarioId) {
  if (
    resolvedScenarioIds.has(scenarioId) ||
    queuedScenarioIds.has(scenarioId) ||
    loadingScenarioIds.has(scenarioId)
  ) {
    return
  }

  queuedScenarioIds.add(scenarioId)
  pendingScenarioStats.push(scenarioId)
  processStatsQueue()
}

function queueVisibleScenarioStatsLoad() {
  visibleScenarioIds.value.forEach(scenarioId => queueScenarioStatsLoad(scenarioId))
}

function observeScenarioCards() {
  if (!scenarioCardObserver) {
    return
  }
  for (const element of scenarioCardElements.values()) {
    scenarioCardObserver.observe(element)
  }
}

function setupScenarioCardObserver() {
  if (scenarioCardObserver) {
    scenarioCardObserver.disconnect()
  }

  if (typeof window === 'undefined' || typeof window.IntersectionObserver !== 'function') {
    queueVisibleScenarioStatsLoad()
    return
  }

  scenarioCardObserver = new window.IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) {
          return
        }

        const scenarioId = Number(entry.target?.dataset?.scenarioId)
        if (!Number.isFinite(scenarioId)) {
          return
        }

        queueScenarioStatsLoad(scenarioId)
        scenarioCardObserver?.unobserve(entry.target)
      })
    },
    {
      root: null,
      rootMargin: '160px 0px',
      threshold: 0.1
    }
  )

  observeScenarioCards()
}

function pruneStatsCaches() {
  const activeIds = new Set(scenarios.value.map(scenario => scenario.id))

  for (const scenarioId of resolvedScenarioIds) {
    if (!activeIds.has(scenarioId)) {
      resolvedScenarioIds.delete(scenarioId)
    }
  }

  for (const scenarioId of queuedScenarioIds) {
    if (!activeIds.has(scenarioId)) {
      queuedScenarioIds.delete(scenarioId)
    }
  }

  for (const scenarioId of loadingScenarioIds) {
    if (!activeIds.has(scenarioId)) {
      loadingScenarioIds.delete(scenarioId)
    }
  }

  for (let index = pendingScenarioStats.length - 1; index >= 0; index -= 1) {
    if (!activeIds.has(pendingScenarioStats[index])) {
      pendingScenarioStats.splice(index, 1)
    }
  }

  for (const scenarioId of cachedScenarioStats.keys()) {
    if (!activeIds.has(scenarioId)) {
      cachedScenarioStats.delete(scenarioId)
    }
  }

  for (const scenarioId of cachedUserProgress.keys()) {
    if (!activeIds.has(scenarioId)) {
      cachedUserProgress.delete(scenarioId)
    }
  }
}

function applyCachedScenarioStats() {
  scenarios.value = scenarios.value.map(scenario => {
    const cachedStats = cachedScenarioStats.get(scenario.id)
    const cachedProgress = cachedUserProgress.get(scenario.id)
    if (!cachedStats && !cachedProgress) {
      return scenario
    }
    return {
      ...scenario,
      stats: cachedStats || scenario.stats,
      user_progress: cachedProgress || scenario.user_progress
    }
  })
}

async function refreshScenarios() {
  await fetchScenarios('all', false)
  pruneStatsCaches()
  applyCachedScenarioStats()
}

// Actions
function openScenario(scenario) {
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id } })
}

function openSettings(scenario) {
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id }, query: { tab: 'settings' } })
}

async function duplicateScenario(scenario) {
  try {
    const newScenario = await duplicateScenarioApi(scenario.id)
    router.push({ name: 'ScenarioWorkspace', params: { id: newScenario.id } })
  } catch (err) {
    console.error('Failed to duplicate scenario:', err)
  }
}

async function archiveScenario(scenario) {
  try {
    await archiveScenarioApi(scenario.id)
  } catch (err) {
    console.error('Failed to archive scenario:', err)
  }
}

function confirmDelete(scenario) {
  scenarioToDelete.value = scenario
  showDeleteDialog.value = true
}

async function deleteScenario() {
  if (!scenarioToDelete.value) return
  deleting.value = true
  try {
    await deleteScenarioById(scenarioToDelete.value.id)
    showDeleteDialog.value = false
    scenarioToDelete.value = null
  } finally {
    deleting.value = false
  }
}

async function acceptInvitation(scenario) {
  await respondToInvitation(scenario.id, 'accept')
  await refreshScenarios()
}

async function rejectInvitation(scenario) {
  await respondToInvitation(scenario.id, 'reject')
  await refreshScenarios()
}

async function leaveScenario(scenario) {
  // Leaving a scenario = rejecting the invitation (hides it from evaluation list)
  await respondToInvitation(scenario.id, 'reject')
  await refreshScenarios()
}

function goToEvaluation(scenario) {
  // Navigate to evaluation items overview for invited evaluators
  router.push({ name: 'EvaluationItemsOverview', params: { scenarioId: scenario.id } })
}

function onScenarioCreated(scenario) {
  showWizard.value = false
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id } })
}

function closeWizard() {
  showWizard.value = false
  generationJobId.value = null
  // Clear query param from URL
  if (route.query.fromGeneration) {
    router.replace({ query: {} })
  }
}

onMounted(async () => {
  await refreshScenarios()
  await nextTick()
  setupScenarioCardObserver()

  // Check if we should open wizard with data from a generation job
  const fromGeneration = route.query.fromGeneration
  if (fromGeneration) {
    generationJobId.value = Number(fromGeneration)
    showWizard.value = true
  }
})

watch(
  () => `${activeTab.value}:${visibleScenarioIds.value.join(',')}`,
  async () => {
    await nextTick()
    observeScenarioCards()
    queueVisibleScenarioStatsLoad()
  }
)

onBeforeUnmount(() => {
  if (scenarioCardObserver) {
    scenarioCardObserver.disconnect()
    scenarioCardObserver = null
  }
  scenarioCardElements.clear()
})
</script>

<style scoped>
.scenario-manager {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-background));
}

/* Page Header */
.page-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 1.4rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
}

/* Tab Bar */
.tab-bar {
  flex-shrink: 0;
  padding: 0 24px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Content */
.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.data-format {
  max-width: 980px;
}

/* Scenarios Grid */
.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.scenario-card-observer-target {
  min-width: 0;
}

@media (max-width: 900px) {
  .scenarios-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    padding: 12px 16px;
  }

  .tab-bar {
    padding: 0 16px;
  }

  .content {
    padding: 16px;
  }

  .title {
    font-size: 1.2rem;
  }
}

/* Skeleton */
.skeleton-card {
  min-height: 180px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state h3 {
  margin: 16px 0 8px;
  font-size: 1.1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.empty-state p {
  margin-bottom: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 320px;
}

.ideal-data-card {
  margin: 16px 0 24px;
}

.ideal-data-intro {
  margin-bottom: 12px;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.ideal-data-list {
  margin: 0 0 16px;
  padding-left: 18px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.ideal-data-list li {
  margin-bottom: 6px;
}

.ideal-data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.ideal-data-example {
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 12px;
}

.ideal-data-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.75);
  margin-bottom: 8px;
}

.ideal-data-code {
  font-family: "IBM Plex Mono", "Courier New", monospace;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  color: rgba(var(--v-theme-on-surface), 0.85);
  margin: 0;
}

.ideal-data-hint {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: rgba(var(--v-theme-on-surface), 0.7);
}
</style>
