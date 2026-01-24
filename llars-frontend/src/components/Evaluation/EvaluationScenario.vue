<!-- EvaluationScenario.vue - Scenario Items Overview -->
<template>
  <div class="scenario-page" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="scenario-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goBack">
        {{ $t('evaluation.backToEvaluations') }}
      </LBtn>
      <div class="header-info">
        <div class="header-title-row">
          <div class="type-badge" :style="{ backgroundColor: typeColor }">
            <LIcon size="16" color="white">{{ typeIcon }}</LIcon>
            <span>{{ typeLabel }}</span>
          </div>
          <h1>{{ scenario?.scenario_name || $t('evaluation.scenario.loading') }}</h1>
        </div>
        <p class="text-medium-emphasis">
          {{ scenario?.description || $t('evaluation.hub.noDescription') }}
        </p>
      </div>
      <div class="header-actions">
        <LTag variant="success" size="small">
          {{ $t('evaluation.progress', { done: completedCount, total: items.length }) }}
        </LTag>
      </div>
    </div>

    <!-- Content -->
    <div class="scenario-content">
      <div class="items-grid">
        <!-- Loading Skeletons -->
        <template v-if="isLoading('items')">
          <div v-for="n in 8" :key="'skel-' + n" class="item-card-skeleton">
            <v-skeleton-loader type="card" height="180" />
          </div>
        </template>

        <!-- Item Cards -->
        <template v-else>
          <div
            v-for="(item, index) in items"
            :key="item.id"
            class="item-card"
            :class="{
              'is-complete': isItemComplete(item),
              'is-in-progress': isItemInProgress(item)
            }"
            @click="navigateToItem(item, index)"
          >
            <!-- Status -->
            <LEvaluationStatus
              class="card-status"
              :status="getItemStatus(item)"
            />

            <!-- Card Content -->
            <div class="card-body">
              <div class="card-number">#{{ index + 1 }}</div>
              <h3 class="card-title">{{ getItemTitle(item) }}</h3>
              <p class="card-preview">{{ getItemPreview(item) }}</p>
            </div>

            <!-- Card Footer -->
            <div class="card-footer">
              <div class="card-score" v-if="hasScore(item)">
                <LIcon size="16" class="mr-1">mdi-star</LIcon>
                {{ getScoreText(item) }}
              </div>
              <div class="card-meta" v-if="getItemMeta(item)">
                {{ getItemMeta(item) }}
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-if="items.length === 0" class="empty-state">
            <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
            <h3>{{ $t('evaluation.scenario.emptyTitle') }}</h3>
            <p class="text-medium-emphasis">
              {{ $t('evaluation.scenario.emptyHint') }}
            </p>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { useMobile } from '@/composables/useMobile'

const props = defineProps({
  scenarioId: {
    type: [String, Number],
    required: true
  }
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()
const { isLoading, withLoading } = useSkeletonLoading(['items'])

// Data
const scenario = ref(null)
const items = ref([])

// Type config - rating and mail_rating use the same RaterDetail component (only dimensions differ)
const TYPE_CONFIG = {
  1: { key: 'ranking', icon: 'mdi-podium', color: '#7986cb', itemRoute: 'RankerDetail' },
  2: { key: 'rating', icon: 'mdi-star-outline', color: '#b0ca97', itemRoute: 'RaterDetail' },
  3: { key: 'mail_rating', icon: 'mdi-email-outline', color: '#d1bc8a', itemRoute: 'RaterDetail' },
  4: { key: 'comparison', icon: 'mdi-compare-horizontal', color: '#88c4c8', itemRoute: 'ComparisonDetail' },
  5: { key: 'authenticity', icon: 'mdi-shield-search', color: '#e8a087', itemRoute: 'AuthenticityDetail' },
  7: { key: 'labeling', icon: 'mdi-label-outline', color: '#ce93d8', itemRoute: 'LabelingDetail' }
}

// Computed
const typeConfig = computed(() => {
  const typeId = scenario.value?.function_type_id
  return TYPE_CONFIG[typeId] || { key: 'unknown', icon: 'mdi-help-circle', color: '#9e9e9e' }
})

const typeIcon = computed(() => typeConfig.value.icon)
const typeColor = computed(() => typeConfig.value.color)
const typeLabel = computed(() => t(`evaluation.types.${typeConfig.value.key}`))

const completedCount = computed(() =>
  items.value.filter(item => isItemComplete(item)).length
)

// Methods
function isItemComplete(item) {
  // Check various completion indicators based on type
  if (item.evaluated !== undefined) return item.evaluated
  if (item.completed !== undefined) return item.completed
  if (item.ranked !== undefined) return item.ranked
  if (item.labeled !== undefined) return item.labeled
  // Backend returns 'Done' (ProgressionStatus enum value)
  if (item.status === 'Done' || item.status === 'done' || item.status === 'completed') return true
  return false
}

function isItemInProgress(item) {
  // Backend returns 'Progressing' (ProgressionStatus enum value)
  if (item.status === 'Progressing' || item.status === 'in_progress') return true
  // For rating: check if some dimensions are rated
  if (item.dimension_ratings) {
    const ratedCount = Object.values(item.dimension_ratings).filter(v => v !== null).length
    return ratedCount > 0 && !isItemComplete(item)
  }
  return false
}

function getItemStatus(item) {
  if (isItemComplete(item)) return 'done'
  if (isItemInProgress(item)) return 'in_progress'
  return 'pending'
}

function getItemTitle(item) {
  // Try various title fields
  return item.subject || item.title || item.name || `Item #${item.item_id || item.thread_id || item.id}`
}

function getItemPreview(item) {
  // Try to get preview text - for threads, use sender info
  const text = item.content || item.preview || item.text || item.sender || ''
  if (!text) return t('evaluation.scenario.noPreview')
  // Truncate to 100 characters
  return text.length > 100 ? text.substring(0, 100) + '...' : text
}

function hasScore(item) {
  return item.overall_score !== undefined || item.score !== undefined
}

function getScoreText(item) {
  const score = item.overall_score ?? item.score
  if (score === undefined || score === null) return ''
  const config = scenario.value?.config_json || {}
  const max = config.max || 5
  return `${score.toFixed(1)}/${max}`
}

function getItemMeta(item) {
  const typeId = scenario.value?.function_type_id

  // Show message count if available
  if (item.message_count) {
    return `${item.message_count} ${t('evaluation.scenario.messages')}`
  }

  switch (typeId) {
    case 2: // rating
    case 3: // mail_rating
      if (item.dimension_ratings) {
        const rated = Object.values(item.dimension_ratings).filter(v => v !== null).length
        const total = Object.keys(item.dimension_ratings).length
        return `${rated}/${total} ${t('evaluation.scenario.dimensionsRated')}`
      }
      break
    case 1: // ranking
      if (item.features_ranked !== undefined) {
        return `${item.features_ranked} ${t('evaluation.scenario.featuresRanked')}`
      }
      break
  }
  return null
}

function navigateToItem(item, index) {
  const typeId = scenario.value?.function_type_id
  const scenarioId = props.scenarioId
  // Rating endpoint returns item_id, other endpoints return thread_id
  const itemId = item.item_id || item.thread_id || item.id

  // Navigate based on evaluation type
  // Pass scenarioId as query param for back navigation
  switch (typeId) {
    case 1: // ranking
      router.push({
        name: 'RankerDetail',
        params: { id: itemId },
        query: { from: scenarioId }
      })
      break
    case 2: // rating
      // Rating navigates to the scenario with specific item index
      // Use index instead of item_id to ensure correct position
      router.push({
        name: 'RaterDetail',
        params: { id: scenarioId },
        query: { from: scenarioId, index: index }
      })
      break
    case 3: // mail_rating
      router.push({
        name: 'HistoryGenerationDetail',
        params: { id: itemId },
        query: { from: scenarioId }
      })
      break
    case 4: // comparison
      router.push({
        name: 'ComparisonDetail',
        params: { session_id: item.session_id || itemId },
        query: { from: scenarioId }
      })
      break
    case 5: // authenticity
      router.push({
        name: 'AuthenticityDetail',
        params: { id: itemId },
        query: { from: scenarioId }
      })
      break
    case 7: // labeling
      // Labeling uses the generic evaluation session
      router.push({ name: 'EvaluationSession', params: { scenarioId: scenarioId } })
      break
    default:
      console.warn('Unknown evaluation type:', typeId)
  }
}

function goBack() {
  router.push({ name: 'EvaluationHub' })
}

async function loadScenario() {
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_BASE_URL}/api/scenarios/${props.scenarioId}`
    )
    scenario.value = response.data.scenario || response.data
  } catch (error) {
    console.error('Error loading scenario:', error)
  }
}

async function loadItems() {
  if (!scenario.value) return

  try {
    const typeId = scenario.value.function_type_id
    let response

    // Use type-specific endpoints to ensure consistent ordering
    if (typeId === 2) {
      // Rating - use the dimensional rating endpoint
      response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/evaluation/rating/${props.scenarioId}/items`
      )
      items.value = response.data.items || []
    } else {
      // Other types - use generic threads endpoint
      response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/api/scenarios/${props.scenarioId}/threads`,
        { params: { per_page: 100 } }
      )
      items.value = response.data.threads || response.data.items || []
    }
  } catch (error) {
    console.error('Error loading items:', error)
    items.value = []
  }
}

// Lifecycle
onMounted(async () => {
  await withLoading('items', async () => {
    await loadScenario()
    await loadItems()
  })
})

// Watch for route changes
watch(() => props.scenarioId, async () => {
  await withLoading('items', async () => {
    await loadScenario()
    await loadItems()
  })
})
</script>

<style scoped>
.scenario-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.scenario-header {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.header-title-row h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.7rem;
  font-weight: 600;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.header-info p {
  margin: 0;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 4px;
}

/* Content */
.scenario-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* Items Grid */
.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

/* Item Card */
.item-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  min-height: 160px;
  overflow: hidden;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.item-card.is-complete {
  border-left: 3px solid var(--llars-success, #98d4bb);
}

.item-card.is-in-progress {
  border-left: 3px solid var(--llars-primary, #b0ca97);
}

/* Status */
.card-status {
  position: absolute;
  top: 12px;
  right: 12px;
}

/* Card Body */
.card-body {
  flex: 1;
  padding: 16px;
  padding-right: 140px; /* Space for status tag */
}

.card-number {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.4);
  margin-bottom: 4px;
}

.card-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-preview {
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Card Footer */
.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.card-score {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--llars-primary, #b0ca97);
}

.card-meta {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state h3 {
  margin: 16px 0 8px 0;
  font-size: 1.1rem;
}

.empty-state p {
  max-width: 400px;
}

/* Skeleton */
.item-card-skeleton {
  min-height: 160px;
}

/* Mobile Styles */
.scenario-page.is-mobile {
  max-width: 100vw;
  overflow-x: hidden;
}

.scenario-page.is-mobile .scenario-header {
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
}

.scenario-page.is-mobile .header-title-row {
  flex-wrap: wrap;
  gap: 8px;
}

.scenario-page.is-mobile .header-title-row h1 {
  font-size: 1.25rem;
  width: 100%;
}

.scenario-page.is-mobile .header-info p {
  font-size: 0.8rem;
}

.scenario-page.is-mobile .header-actions {
  width: 100%;
}

.scenario-page.is-mobile .scenario-content {
  padding: 16px;
}

.scenario-page.is-mobile .items-grid {
  grid-template-columns: 1fr;
  gap: 12px;
}

.scenario-page.is-mobile .item-card {
  min-height: 140px;
}

.scenario-page.is-mobile .card-title {
  font-size: 0.9rem;
}
</style>
