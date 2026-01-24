<template>
  <div class="overview-page">
    <!-- Header -->
    <div class="overview-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goHome">
        {{ $t('navigation.home') }}
      </LBtn>
      <div class="header-info">
        <h1>{{ $t('evaluation.title') }}</h1>
        <p class="text-medium-emphasis">{{ $t('evaluation.subtitle') }}</p>
      </div>
      <div class="header-stats">
        <LTag v-if="availableScenarios.length > 0" variant="primary" size="small">
          {{ $t('evaluation.available', { count: availableScenarios.length }) }}
        </LTag>
      </div>
    </div>

    <!-- Content -->
    <div class="overview-content">
      <!-- Skeleton Loading -->
      <div v-if="isLoading('scenarios')" class="scenarios-grid">
        <div v-for="n in 6" :key="'skel-' + n" class="scenario-card-skeleton">
          <v-skeleton-loader type="list-item-avatar-two-line" />
        </div>
      </div>

      <template v-else>
        <!-- Scenarios Grid -->
        <div v-if="availableScenarios.length > 0" class="scenarios-grid">
          <div
            v-for="scenario in availableScenarios"
            :key="scenario.id"
            class="scenario-card"
            :class="{ 'is-completed': getProgress(scenario).percent === 100 }"
            @click="goToEvaluation(scenario)"
          >
            <!-- Header Row: Icon, Type Tag, Status Badge -->
            <div class="card-header">
              <div class="header-left">
                <div class="type-icon" :style="{ backgroundColor: getTypeConfig(scenario).bgColor }">
                  <LIcon :color="getTypeConfig(scenario).color" size="18">{{ getTypeConfig(scenario).icon }}</LIcon>
                </div>
                <span
                  class="type-chip"
                  :style="{ backgroundColor: getTypeConfig(scenario).bgColor, color: getTypeConfig(scenario).color }"
                >
                  {{ getTypeConfig(scenario).label }}
                </span>
              </div>
              <LEvaluationStatus :status="getStatus(scenario)" />
            </div>

            <!-- Card Content -->
            <div class="card-content">
              <h3 class="card-title">{{ scenario.scenario_name }}</h3>
              <span class="owner-name">{{ scenario.is_owner ? $t('scenarioManager.card.owner') : scenario.owner_name }}</span>
            </div>

            <!-- Progress Bar (always at bottom) -->
            <div class="progress-section">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getProgress(scenario).percent + '%' }"></div>
              </div>
              <span class="progress-text">{{ getProgress(scenario).completed }}/{{ getProgress(scenario).total }}</span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
          <h3>{{ $t('evaluation.noScenariosAvailable') }}</h3>
          <p class="text-medium-emphasis">
            {{ $t('evaluation.emptyHint') }}
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'

const router = useRouter()
const { isLoading, withLoading } = useSkeletonLoading(['scenarios'])

// All scenarios from backend
const allScenarios = ref([])

// Type configuration
const typeConfigs = {
  1: { icon: 'mdi-podium', color: '#b0ca97', bgColor: 'rgba(176, 202, 151, 0.15)', label: 'Ranking' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', bgColor: 'rgba(209, 188, 138, 0.15)', label: 'Rating' },
  3: { icon: 'mdi-email-outline', color: '#e8a087', bgColor: 'rgba(232, 160, 135, 0.15)', label: 'Mail Rating' },
  4: { icon: 'mdi-compare-horizontal', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', label: 'Comparison' },
  5: { icon: 'mdi-shield-search', color: '#c4a0d4', bgColor: 'rgba(196, 160, 212, 0.15)', label: 'Authenticity' },
  7: { icon: 'mdi-tag-outline', color: '#98d4bb', bgColor: 'rgba(152, 212, 187, 0.15)', label: 'Labeling' }
}

function getTypeConfig(scenario) {
  return typeConfigs[scenario.function_type_id] || typeConfigs[2]
}

// Available scenarios: All scenarios where user is owner OR invited
// Filter by status: only active scenarios
const availableScenarios = computed(() => {
  return allScenarios.value
    .filter(s => {
      // Show scenarios where user is owner OR has accepted/pending invitation
      const isOwner = s.is_owner
      const isInvited = s.invitation?.status === 'accepted'
      const isPending = s.invitation?.status === 'pending'

      // Only show active scenarios (not archived/draft for non-owners)
      const isActive = ['evaluating', 'data_collection', 'active'].includes(s.status)
      const showForOwner = isOwner && s.status !== 'archived'

      return (showForOwner || ((isInvited || isPending) && isActive))
    })
    .sort((a, b) => {
      // Owner scenarios first, then by progress, then by date
      if (a.is_owner !== b.is_owner) return a.is_owner ? -1 : 1
      return new Date(b.begin || 0) - new Date(a.begin || 0)
    })
})

function getProgress(scenario) {
  const completed = scenario.user_progress?.completed || 0
  const total = scenario.user_progress?.total || scenario.thread_count || 0
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0
  return { completed, total, percent }
}

function getStatus(scenario) {
  const progress = getProgress(scenario)
  if (progress.percent === 100) return 'done'
  if (progress.completed > 0) return 'in_progress'
  if (scenario.invitation?.status === 'pending') return 'pending'
  return 'pending'
}

async function fetchScenarios() {
  try {
    const response = await axios.get('/api/scenarios', {
      params: { filter: 'all', include_stats: 'true' }
    })
    allScenarios.value = response.data.scenarios || []
  } catch (error) {
    console.error('Error fetching scenarios:', error)
  }
}

function goToEvaluation(scenario) {
  // Navigate to the items overview for this scenario
  router.push({ name: 'EvaluationItemsOverview', params: { scenarioId: scenario.id } })
}

function goHome() {
  router.push('/Home')
}

onMounted(async () => {
  await withLoading('scenarios', fetchScenarios)
})
</script>

<style scoped>
.overview-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-info h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-info p {
  margin: 4px 0 0 0;
  font-size: 0.9rem;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.scenario-card {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.scenario-card.is-completed {
  border-left: 3px solid rgb(var(--v-theme-success));
}

/* Header row with icon, type tag and status badge */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px 3px 8px 3px;
  flex-shrink: 0;
}

.type-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.7rem;
  font-weight: 600;
}

/* Card content */
.card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
}

.owner-name {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Progress Section (always at bottom) */
.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  margin-top: auto;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: nowrap;
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
}

.empty-state p {
  max-width: 400px;
}

/* Responsive */
@media (max-width: 768px) {
  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .overview-header {
    flex-wrap: wrap;
  }

  .header-info {
    order: 2;
    width: 100%;
    margin-top: 12px;
  }
}
</style>
