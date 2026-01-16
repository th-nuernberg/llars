<template>
  <div class="scenario-manager" :class="{ 'is-mobile': isMobile }">
    <!-- Page Header -->
    <div class="page-header">
      <div class="header-left">
        <LIcon size="32" color="primary">mdi-clipboard-check-multiple-outline</LIcon>
        <div class="header-text">
          <h1 class="title">{{ $t('scenarioManager.title') }}</h1>
          <p class="subtitle" v-if="!isMobile">{{ $t('scenarioManager.subtitle') }}</p>
        </div>
      </div>
      <div class="header-right">
        <LBtn variant="primary" @click="createNewScenario">
          <LIcon start>mdi-plus</LIcon>
          {{ $t('scenarioManager.newScenario') }}
        </LBtn>
      </div>
    </div>

    <!-- Main Content -->
    <div ref="containerRef" class="main-content">
      <!-- Left Panel: Filters -->
      <div v-if="!isMobile" class="left-panel" :style="leftPanelStyle()">
        <div class="panel-header">
          <LIcon class="mr-2">mdi-filter-variant</LIcon>
          <span>{{ $t('scenarioManager.filters.title') }}</span>
        </div>
        <div class="panel-content">
          <!-- Ownership Filter -->
          <div class="filter-section">
            <div class="filter-label">{{ $t('scenarioManager.filters.ownership') }}</div>
            <div class="filter-options">
              <div
                v-for="opt in ownershipOptions"
                :key="opt.value"
                class="filter-option"
                :class="{ active: filters.ownership === opt.value }"
                @click="filters.ownership = opt.value"
              >
                <LIcon :color="filters.ownership === opt.value ? 'primary' : undefined">
                  {{ opt.icon }}
                </LIcon>
                <span class="filter-option-label">{{ opt.label }}</span>
                <span class="filter-option-count">{{ getOwnershipCount(opt.value) }}</span>
              </div>
            </div>
          </div>

          <!-- Status Filter -->
          <div class="filter-section">
            <div class="filter-label">{{ $t('scenarioManager.filters.status') }}</div>
            <div class="filter-options">
              <div
                v-for="opt in statusOptions"
                :key="opt.value"
                class="filter-option"
                :class="{ active: filters.status === opt.value }"
                @click="filters.status = opt.value"
              >
                <LIcon :color="filters.status === opt.value ? 'primary' : undefined">
                  {{ opt.icon }}
                </LIcon>
                <span class="filter-option-label">{{ opt.label }}</span>
                <span class="filter-option-count">{{ getStatusCount(opt.value) }}</span>
              </div>
            </div>
          </div>

          <!-- Type Filter -->
          <div class="filter-section">
            <div class="filter-label">{{ $t('scenarioManager.filters.type') }}</div>
            <div class="filter-options">
              <div
                v-for="opt in typeOptions"
                :key="opt.value"
                class="filter-option"
                :class="{ active: filters.type === opt.value }"
                @click="filters.type = opt.value"
              >
                <LIcon :color="filters.type === opt.value ? 'primary' : undefined">
                  {{ opt.icon }}
                </LIcon>
                <span class="filter-option-label">{{ opt.label }}</span>
                <span class="filter-option-count">{{ getTypeCount(opt.value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Resize Divider -->
      <div
        v-if="!isMobile"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- Right Panel: Scenarios Grid -->
      <div class="right-panel" :style="isMobile ? {} : rightPanelStyle()">
        <!-- Mobile Filters -->
        <div v-if="isMobile" class="mobile-filters">
          <v-select
            v-model="filters.ownership"
            :items="ownershipOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            class="mobile-filter-select"
          />
          <v-select
            v-model="filters.status"
            :items="statusOptions"
            item-title="label"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            class="mobile-filter-select"
          />
        </div>

        <div class="panel-header">
          <LIcon class="mr-2">mdi-clipboard-list-outline</LIcon>
          <span>{{ currentFilterLabel }}</span>
          <v-spacer />
          <LTag variant="primary" size="sm">
            {{ $t('scenarioManager.count', { count: filteredScenarios.length }) }}
          </LTag>
        </div>

        <div class="panel-content">
          <!-- Loading State -->
          <div v-if="loading" class="scenarios-grid">
            <v-skeleton-loader
              v-for="n in 4"
              :key="'skeleton-' + n"
              type="card"
              class="scenario-skeleton"
            />
          </div>

          <!-- Scenarios Grid -->
          <div v-else-if="filteredScenarios.length > 0" class="scenarios-grid">
            <ScenarioCard
              v-for="scenario in filteredScenarios"
              :key="scenario.id"
              :scenario="scenario"
              @click="openScenario(scenario)"
              @edit="editScenario(scenario)"
              @delete="confirmDeleteScenario(scenario)"
              @invitation-changed="onInvitationChanged"
            />
          </div>

          <!-- Empty State -->
          <div v-else class="empty-state">
            <LIcon size="80" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
            <h3>{{ $t('scenarioManager.empty.title') }}</h3>
            <p>{{ $t('scenarioManager.empty.description') }}</p>
            <LBtn variant="primary" @click="createNewScenario">
              <LIcon start>mdi-plus</LIcon>
              {{ $t('scenarioManager.empty.action') }}
            </LBtn>
          </div>
        </div>
      </div>
    </div>

    <!-- New Scenario Wizard Dialog -->
    <v-dialog v-model="showWizard" max-width="900" persistent>
      <ScenarioWizard
        v-if="showWizard"
        @close="showWizard = false"
        @created="onScenarioCreated"
      />
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="450">
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
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'
import { useScenarioManager } from './composables/useScenarioManager'
import ScenarioCard from './components/ScenarioCard.vue'
import ScenarioWizard from './components/ScenarioWizard.vue'

const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()

const {
  scenarios,
  loading,
  fetchScenarios,
  deleteScenarioById,
  respondToInvitation
} = useScenarioManager()

const {
  isResizing,
  containerRef,
  startResize,
  leftPanelStyle,
  rightPanelStyle
} = usePanelResize({
  initialLeftPercent: 22,
  minLeftPercent: 18,
  maxLeftPercent: 35,
  storageKey: 'scenario-manager-panel-width'
})

// UI State
const showWizard = ref(false)
const showDeleteDialog = ref(false)
const scenarioToDelete = ref(null)
const deleting = ref(false)

// Filters
const filters = ref({
  ownership: 'all',
  status: 'all',
  type: 'all'
})

// Filter Options
const ownershipOptions = computed(() => [
  { value: 'all', label: t('scenarioManager.filters.all'), icon: 'mdi-view-grid-outline' },
  { value: 'own', label: t('scenarioManager.filters.own'), icon: 'mdi-account-outline' },
  { value: 'invited', label: t('scenarioManager.filters.invited'), icon: 'mdi-email-check-outline' },
  { value: 'rejected', label: t('scenarioManager.filters.rejected'), icon: 'mdi-email-remove-outline' }
])

const statusOptions = computed(() => [
  { value: 'all', label: t('scenarioManager.filters.allStatus'), icon: 'mdi-format-list-bulleted' },
  { value: 'draft', label: t('scenarioManager.status.draft'), icon: 'mdi-file-document-edit-outline' },
  { value: 'active', label: t('scenarioManager.status.active'), icon: 'mdi-play-circle-outline' },
  { value: 'completed', label: t('scenarioManager.status.completed'), icon: 'mdi-check-circle-outline' },
  { value: 'archived', label: t('scenarioManager.status.archived'), icon: 'mdi-archive-outline' }
])

const typeOptions = computed(() => [
  { value: 'all', label: t('scenarioManager.filters.allTypes'), icon: 'mdi-shape-outline' },
  { value: 1, label: t('scenarioManager.types.ranking'), icon: 'mdi-sort-variant' },
  { value: 2, label: t('scenarioManager.types.rating'), icon: 'mdi-star-outline' },
  { value: 3, label: t('scenarioManager.types.mailRating'), icon: 'mdi-email-outline' },
  { value: 4, label: t('scenarioManager.types.comparison'), icon: 'mdi-compare-horizontal' },
  { value: 5, label: t('scenarioManager.types.authenticity'), icon: 'mdi-shield-search' }
])

// Computed
const filteredScenarios = computed(() => {
  let result = scenarios.value

  // Ownership/Invitation filter
  if (filters.value.ownership === 'own') {
    result = result.filter(s => s.is_owner)
  } else if (filters.value.ownership === 'invited') {
    // Accepted invitations (not owned)
    result = result.filter(s => !s.is_owner && s.invitation?.status !== 'rejected')
  } else if (filters.value.ownership === 'rejected') {
    // Rejected invitations
    result = result.filter(s => !s.is_owner && s.invitation?.status === 'rejected')
  }

  // Status filter
  if (filters.value.status !== 'all') {
    if (filters.value.status === 'active') {
      result = result.filter(s => ['data_collection', 'evaluating', 'analyzing'].includes(s.status))
    } else {
      result = result.filter(s => s.status === filters.value.status)
    }
  }

  // Type filter
  if (filters.value.type !== 'all') {
    result = result.filter(s => s.function_type_id === filters.value.type)
  }

  return result
})

const currentFilterLabel = computed(() => {
  if (filters.value.ownership === 'own') return t('scenarioManager.sections.own')
  if (filters.value.ownership === 'invited') return t('scenarioManager.sections.invited')
  if (filters.value.ownership === 'rejected') return t('scenarioManager.sections.rejected')
  return t('scenarioManager.sections.all')
})

// Count helpers
function getOwnershipCount(value) {
  if (value === 'all') return scenarios.value.length
  if (value === 'own') return scenarios.value.filter(s => s.is_owner).length
  if (value === 'invited') return scenarios.value.filter(s => !s.is_owner && s.invitation?.status !== 'rejected').length
  if (value === 'rejected') return scenarios.value.filter(s => !s.is_owner && s.invitation?.status === 'rejected').length
  return 0
}

function getStatusCount(value) {
  if (value === 'all') return scenarios.value.length
  if (value === 'active') {
    return scenarios.value.filter(s => ['data_collection', 'evaluating', 'analyzing'].includes(s.status)).length
  }
  return scenarios.value.filter(s => s.status === value).length
}

function getTypeCount(value) {
  if (value === 'all') return scenarios.value.length
  return scenarios.value.filter(s => s.function_type_id === value).length
}

// Actions
function createNewScenario() {
  showWizard.value = true
}

function openScenario(scenario) {
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id } })
}

function editScenario(scenario) {
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id }, query: { tab: 'settings' } })
}

function confirmDeleteScenario(scenario) {
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

function onScenarioCreated(scenario) {
  showWizard.value = false
  router.push({ name: 'ScenarioWorkspace', params: { id: scenario.id } })
}

function onInvitationChanged({ id, status }) {
  // Refresh scenarios to update counts and visibility
  loadScenarios()
}

async function loadScenarios() {
  // Fetch all scenarios including rejected ones to show correct counts
  await fetchScenarios('all')
}

onMounted(() => {
  loadScenarios()
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
  gap: 16px;
}

.header-text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 1.5rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  margin: 0;
  line-height: 1.2;
}

.subtitle {
  font-size: 0.875rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* Left Panel */
.left-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: rgb(var(--v-theme-surface));
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-width: 200px;
}

/* Right Panel */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 400px;
}

/* Panel Header */
.panel-header {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  font-weight: 500;
  color: rgb(var(--v-theme-on-surface));
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Resize Divider */
.resize-divider {
  flex-shrink: 0;
  width: 6px;
  background-color: rgb(var(--v-theme-surface));
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.2s;
}

.resize-divider:hover,
.resize-divider.resizing {
  background-color: rgba(var(--v-theme-primary), 0.1);
}

.resize-handle {
  width: 2px;
  height: 40px;
  background-color: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 1px;
  transition: background-color 0.2s, height 0.2s;
}

.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background-color: rgb(var(--v-theme-primary));
  height: 60px;
}

/* Filter Sections */
.filter-section {
  margin-bottom: 24px;
}

.filter-label {
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.filter-option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.filter-option:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.filter-option.active {
  background-color: rgba(var(--v-theme-primary), 0.12);
}

.filter-option-label {
  flex: 1;
  font-size: 0.875rem;
  color: rgb(var(--v-theme-on-surface));
}

.filter-option-count {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background-color: rgba(var(--v-theme-on-surface), 0.08);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Scenarios Grid */
.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.scenario-skeleton {
  min-height: 180px;
}

/* Mobile Filters */
.mobile-filters {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background-color: rgb(var(--v-theme-surface));
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.mobile-filter-select {
  flex: 1;
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
  font-size: 1.25rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

.empty-state p {
  margin-bottom: 24px;
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 400px;
}

/* Mobile Styles */
.scenario-manager.is-mobile {
  height: calc(100vh - 88px);
}

.scenario-manager.is-mobile .page-header {
  padding: 12px 16px;
}

.scenario-manager.is-mobile .title {
  font-size: 1.2rem;
}

.scenario-manager.is-mobile .scenarios-grid {
  grid-template-columns: 1fr;
}
</style>
