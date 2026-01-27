<template>
  <div class="items-overview">
    <!-- Header -->
    <div class="overview-header">
      <div class="header-left">
        <LBtn variant="tonal" size="small" @click="goBack">
          <LIcon start>mdi-arrow-left</LIcon>
          {{ $t('evaluation.backToEvaluations') }}
        </LBtn>
        <div class="header-info">
          <h1>{{ scenario?.name || $t('evaluation.session.title') }}</h1>
          <p class="text-medium-emphasis">{{ scenario?.description }}</p>
        </div>
      </div>

      <div class="header-right">
        <!-- Type Badge -->
        <div class="type-badge" :style="{ backgroundColor: typeConfig.bgColor }">
          <LIcon :color="typeConfig.color" size="18">{{ typeConfig.icon }}</LIcon>
          <span :style="{ color: typeConfig.color }">{{ typeConfig.label }}</span>
        </div>

        <!-- Progress Indicator -->
        <div class="progress-indicator">
          <span class="progress-text">
            {{ $t('evaluation.progress', { done: progress.completed, total: progress.total }) }}
          </span>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: progressPercent + '%' }"
            />
          </div>
          <span class="progress-percent">{{ progressPercent }}%</span>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-chips">
        <button
          class="filter-chip"
          :class="{ active: activeFilter === 'all' }"
          @click="activeFilter = 'all'"
        >
          {{ $t('common.all') }} ({{ items.length }})
        </button>
        <button
          class="filter-chip pending"
          :class="{ active: activeFilter === 'pending' }"
          @click="activeFilter = 'pending'"
        >
          {{ $t('evaluation.status.pending') }} ({{ pendingCount }})
        </button>
        <button
          class="filter-chip in-progress"
          :class="{ active: activeFilter === 'in_progress' }"
          @click="activeFilter = 'in_progress'"
        >
          {{ $t('evaluation.status.inProgress') }} ({{ inProgressCount }})
        </button>
        <button
          class="filter-chip done"
          :class="{ active: activeFilter === 'done' }"
          @click="activeFilter = 'done'"
        >
          {{ $t('evaluation.status.done') }} ({{ completedCount }})
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <v-progress-circular indeterminate size="48" color="primary" />
      <p>{{ $t('common.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <LIcon size="48" color="error">mdi-alert-circle-outline</LIcon>
      <h3>{{ $t('common.error') }}</h3>
      <p>{{ error }}</p>
      <LBtn variant="primary" @click="loadData">
        {{ $t('common.retry') }}
      </LBtn>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredItems.length === 0" class="empty-state">
      <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
      <h3 v-if="activeFilter === 'all'">{{ $t('evaluation.session.noItems') }}</h3>
      <h3 v-else>{{ $t('evaluation.noItemsInFilter') }}</h3>
      <LBtn v-if="activeFilter !== 'all'" variant="tonal" @click="activeFilter = 'all'">
        {{ $t('evaluation.showAll') }}
      </LBtn>
    </div>

    <!-- Items Grid -->
    <div v-else class="items-content">
      <div class="items-grid">
        <div
          v-for="(item, index) in filteredItems"
          :key="item.id || item.thread_id || index"
          class="item-card"
          :class="getItemStatusClass(item)"
          @click="goToItem(item, index)"
        >
          <!-- Status Badge -->
          <LEvaluationStatus
            class="item-status"
            :status="getItemStatus(item)"
          />

          <!-- Item Number -->
          <div class="item-number">
            <span>#{{ getItemNumber(item, index) }}</span>
          </div>

          <!-- Item Content Preview -->
          <div class="item-content">
            <h3 class="item-title">{{ getItemTitle(item) }}</h3>
            <p class="item-preview">{{ getItemPreview(item) }}</p>
          </div>

          <!-- Item Meta -->
          <div class="item-meta">
            <span v-if="item.message_count" class="meta-item">
              <LIcon size="14">mdi-message-outline</LIcon>
              {{ item.message_count }}
            </span>
            <span v-if="item.feature_count" class="meta-item">
              <LIcon size="14">mdi-tag-outline</LIcon>
              {{ item.feature_count }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * EvaluationItemsOverview.vue - Items Overview for a Scenario
 *
 * Displays all items of a scenario as cards with status tags.
 * Users can filter by status and click on an item to start evaluation.
 */
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// State
const scenario = ref(null)
const items = ref([])
const loading = ref(true)
const error = ref(null)
const activeFilter = ref('all')

// Type configuration
const typeConfigs = {
  1: { icon: 'mdi-podium', color: '#b0ca97', bgColor: 'rgba(176, 202, 151, 0.15)', label: 'Ranking' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', bgColor: 'rgba(209, 188, 138, 0.15)', label: 'Rating' },
  3: { icon: 'mdi-email-outline', color: '#e8a087', bgColor: 'rgba(232, 160, 135, 0.15)', label: 'Mail Rating' },
  4: { icon: 'mdi-compare-horizontal', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', label: 'Comparison' },
  5: { icon: 'mdi-shield-search', color: '#c4a0d4', bgColor: 'rgba(196, 160, 212, 0.15)', label: 'Authenticity' },
  7: { icon: 'mdi-tag-outline', color: '#98d4bb', bgColor: 'rgba(152, 212, 187, 0.15)', label: 'Labeling' }
}

const typeConfig = computed(() => {
  if (!scenario.value) return typeConfigs[2]
  return typeConfigs[scenario.value.function_type_id] || typeConfigs[2]
})

// Progress calculations
const completedCount = computed(() => items.value.filter(i => getItemStatus(i) === 'done').length)
const inProgressCount = computed(() => items.value.filter(i => getItemStatus(i) === 'in_progress').length)
const pendingCount = computed(() => items.value.filter(i => getItemStatus(i) === 'pending').length)

const progress = computed(() => ({
  completed: completedCount.value,
  total: items.value.length
}))

const progressPercent = computed(() => {
  if (items.value.length === 0) return 0
  return Math.round((completedCount.value / items.value.length) * 100)
})

// Filtered items based on active filter
const filteredItems = computed(() => {
  if (activeFilter.value === 'all') return items.value

  return items.value.filter(item => {
    const status = getItemStatus(item)
    return status === activeFilter.value
  })
})

// Get item status
function getItemStatus(item) {
  // Use backend status if available
  if (item.status) {
    // Map backend status to frontend status
    // Handle various formats: lowercase, capitalized, and enum values
    const statusMap = {
      // Lowercase (from session_service)
      'done': 'done',
      'in_progress': 'in_progress',
      'pending': 'pending',
      // Capitalized (from ProgressionStatus enum .value)
      'Done': 'done',
      'Progressing': 'in_progress',
      'Not Started': 'pending',
      // Uppercase (enum names)
      'DONE': 'done',
      'PROGRESSING': 'in_progress',
      'NOT_STARTED': 'pending'
    }
    return statusMap[item.status] || 'pending'
  }

  // Fallback: Check various status indicators
  if (item.evaluated || item.ranked || item.rated) {
    return 'done'
  }
  if (item.in_progress || item.started) {
    return 'in_progress'
  }
  return 'pending'
}

// Get status class for card styling
function getItemStatusClass(item) {
  return `status-${getItemStatus(item)}`
}

// Get item number for display
function getItemNumber(item, index) {
  return item.position || item.order || index + 1
}

// Get item title
function getItemTitle(item) {
  return item.subject || item.title || item.name || t('evaluation.item', { num: item.id || item.thread_id || 'N/A' })
}

// Get item preview text
function getItemPreview(item) {
  // Try to get first message content or other preview
  if (item.preview) return truncate(item.preview, 100)
  if (item.content) return truncate(item.content, 100)
  if (item.first_message) return truncate(item.first_message, 100)
  return t('evaluation.clickToView')
}

function truncate(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

// Load scenario and items data
async function loadData() {
  loading.value = true
  error.value = null

  try {
    // Load scenario details
    const scenarioResponse = await axios.get(`/api/scenarios/${props.scenarioId}`)
    scenario.value = scenarioResponse.data

    // Load items via evaluation session endpoint
    const sessionResponse = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = sessionResponse.data.items || []
  } catch (err) {
    console.error('Failed to load data:', err)
    error.value = err.response?.data?.error || err.response?.data?.message || t('common.error')
  } finally {
    loading.value = false
  }
}

// Navigation
function goBack() {
  router.push({ name: 'EvaluationHub' })
}

function goToItem(item, index) {
  // Navigate to the evaluation session with the specific item
  router.push({
    name: 'EvaluationSessionItem',
    params: {
      scenarioId: props.scenarioId,
      itemId: item.thread_id || item.id || item.item_id
    }
  })
}

// Initialize
onMounted(() => {
  loadData()
})

// Watch for scenario changes
watch(() => props.scenarioId, (newId) => {
  if (newId) {
    loadData()
  }
})
</script>

<style scoped>
.items-overview {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.overview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-info h1 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
}

.header-info p {
  font-size: 0.8rem;
  margin: 2px 0 0 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

/* Type Badge */
.type-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px 3px 8px 3px;
  font-size: 0.8rem;
  font-weight: 600;
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.progress-bar {
  width: 120px;
  height: 6px;
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--llars-primary, #b0ca97), var(--llars-success, #98d4bb));
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-percent {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
  min-width: 35px;
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
}

.filter-chips {
  display: flex;
  gap: 8px;
}

.filter-chip {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 20px;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.filter-chip:hover {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.filter-chip.active {
  background: rgba(var(--v-theme-primary), 0.15);
  border-color: rgb(var(--v-theme-primary));
  color: rgb(var(--v-theme-primary));
}

.filter-chip.pending.active {
  background: rgba(var(--v-theme-warning), 0.15);
  border-color: rgb(var(--v-theme-warning));
  color: rgb(var(--v-theme-warning));
}

.filter-chip.in-progress.active {
  background: rgba(136, 196, 200, 0.15);
  border-color: #88c4c8;
  color: #88c4c8;
}

.filter-chip.done.active {
  background: rgba(152, 212, 187, 0.15);
  border-color: #98d4bb;
  color: #3d8b6a;
}

/* Content Area */
.items-content {
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

.item-card {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

/* Status-based card styling */
.item-card.status-done {
  border-left: 3px solid var(--llars-success, #98d4bb);
}

.item-card.status-in_progress {
  border-left: 3px solid var(--llars-accent, #88c4c8);
}

.item-card.status-pending {
  border-left: 3px solid rgba(var(--v-theme-on-surface), 0.2);
}

.item-status {
  position: absolute;
  top: 12px;
  right: 12px;
}

.item-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.item-content {
  flex: 1;
  padding-right: 80px;
}

.item-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0 0 6px 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-preview {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-meta {
  display: flex;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.06);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Loading & Error States */
.loading-state,
.error-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 48px;
  text-align: center;
}

.loading-state p,
.error-state p,
.empty-state p {
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 400px;
}

.error-state h3 {
  color: rgb(var(--v-theme-error));
  margin: 0;
}

.empty-state h3 {
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .overview-header {
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }

  .header-left,
  .header-right {
    width: 100%;
  }

  .header-right {
    justify-content: space-between;
  }

  .progress-bar {
    width: 80px;
  }

  .filter-bar {
    padding: 10px 16px;
    overflow-x: auto;
  }

  .filter-chips {
    min-width: max-content;
  }

  .items-content {
    padding: 16px;
  }

  .items-grid {
    grid-template-columns: 1fr;
  }
}
</style>
