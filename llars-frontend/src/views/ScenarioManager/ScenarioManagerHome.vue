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
          <ScenarioOwnerCard
            v-for="scenario in ownScenarios"
            :key="scenario.id"
            :scenario="scenario"
            @open="openScenario"
            @settings="openSettings"
            @duplicate="duplicateScenario"
            @archive="archiveScenario"
            @delete="confirmDelete"
          />
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
          <ScenarioInviteCard
            v-for="scenario in invitedScenarios"
            :key="scenario.id"
            :scenario="scenario"
            @accept="acceptInvitation"
            @reject="rejectInvitation"
            @evaluate="goToEvaluation"
            @leave="leaveScenario"
          />
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
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter, useRoute } from 'vue-router'
import { useScenarioManager } from './composables/useScenarioManager'
import ScenarioOwnerCard from './components/ScenarioOwnerCard.vue'
import ScenarioInviteCard from './components/ScenarioInviteCard.vue'
import ScenarioWizard from './components/ScenarioWizard.vue'
import DataFormatGuide from './components/DataFormatGuide.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const {
  scenarios,
  loading,
  fetchScenarios,
  deleteScenarioById,
  respondToInvitation,
  duplicateScenario: duplicateScenarioApi,
  archiveScenario: archiveScenarioApi
} = useScenarioManager()

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
  await fetchScenarios('all')
}

async function rejectInvitation(scenario) {
  await respondToInvitation(scenario.id, 'reject')
  await fetchScenarios('all')
}

async function leaveScenario(scenario) {
  // Leaving a scenario = rejecting the invitation (hides it from evaluation list)
  await respondToInvitation(scenario.id, 'reject')
  await fetchScenarios('all')
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

onMounted(() => {
  fetchScenarios('all')

  // Check if we should open wizard with data from a generation job
  const fromGeneration = route.query.fromGeneration
  if (fromGeneration) {
    generationJobId.value = Number(fromGeneration)
    showWizard.value = true
  }
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
