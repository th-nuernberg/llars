<template>
  <div class="evaluation-session" :class="{ 'is-mobile': isMobile }">
    <!-- Header -->
    <div class="session-header">
      <div class="header-left">
        <LBtn variant="tonal" size="small" @click="goBack">
          <LIcon start>mdi-arrow-left</LIcon>
          {{ $t('common.back') }}
        </LBtn>
        <div class="header-info">
          <h1>{{ scenario?.name || $t('evaluation.session.title') }}</h1>
          <p class="text-medium-emphasis">{{ scenario?.description }}</p>
        </div>
      </div>

      <div class="header-right">
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

    <!-- Loading State -->
    <div v-if="isLoading" class="session-loading">
      <v-progress-circular indeterminate size="48" color="primary" />
      <p>{{ $t('evaluation.session.loading') }}</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="session-error">
      <LIcon size="48" color="error">mdi-alert-circle-outline</LIcon>
      <h3>{{ $t('evaluation.session.error') }}</h3>
      <p>{{ error }}</p>
      <LBtn variant="primary" @click="reload">
        {{ $t('common.retry') }}
      </LBtn>
    </div>

    <!-- Empty State -->
    <div v-else-if="items.length === 0" class="session-empty">
      <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
      <h3>{{ $t('evaluation.session.noItems') }}</h3>
      <p class="text-medium-emphasis">{{ $t('evaluation.session.noItemsHint') }}</p>
      <LBtn variant="primary" @click="goBack">
        {{ $t('common.back') }}
      </LBtn>
    </div>

    <!-- Session Complete -->
    <div v-else-if="isComplete && !currentItem" class="session-complete">
      <LIcon size="64" color="success">mdi-check-circle-outline</LIcon>
      <h3>{{ $t('evaluation.session.complete') }}</h3>
      <p class="text-medium-emphasis">{{ $t('evaluation.session.completeMessage') }}</p>
      <LBtn variant="primary" @click="goBack">
        {{ $t('evaluation.backToEvaluations') }}
      </LBtn>
    </div>

    <!-- Main Content - Interface Component + Unified Footer -->
    <template v-else>
      <div class="session-content">
        <router-view
          v-slot="{ Component }"
          :scenario="scenario"
          :config="config"
          :current-item="currentItem"
          :progress="progress"
        >
          <keep-alive>
            <component
              :is="Component || defaultInterface"
              :key="scenarioId"
              :scenario-id="scenarioId"
              :scenario="scenario"
              :config="config"
              :current-item="currentItem"
              :initial-item-id="initialItemId"
              :hide-navigation="true"
              @status-change="handleStatusChange"
              @saving-change="handleSavingChange"
              @item-completed="handleItemCompleted"
            />
          </keep-alive>
        </router-view>
      </div>

      <!-- Unified Navigation Footer -->
      <div class="session-footer">
        <LBtn
          variant="tonal"
          size="small"
          :disabled="!hasPrev"
          @click="handlePrev"
        >
          <LIcon start>mdi-chevron-left</LIcon>
          {{ $t('common.previous') }}
        </LBtn>

        <div class="footer-center">
          <LEvaluationStatus
            :status="currentItemStatus"
            :saving="isSaving"
          />
          <span class="nav-position">
            {{ $t('evaluation.caseNumber', { current: currentIndex + 1, total: items.length }) }}
          </span>
        </div>

        <LBtn
          variant="primary"
          size="small"
          :disabled="!hasNext"
          @click="handleNext"
        >
          {{ $t('common.next') }}
          <LIcon end>mdi-chevron-right</LIcon>
        </LBtn>
      </div>
    </template>
  </div>
</template>

<script setup>
/**
 * EvaluationSession.vue - Evaluation Session Wrapper
 *
 * Provides the main layout and navigation for evaluation sessions.
 * Wraps type-specific interfaces (RatingInterface, RankingInterface, etc.)
 * and handles progress tracking, navigation, and state management.
 *
 * Unified layout structure:
 * - Header: Back button, scenario name, overall progress
 * - Content: Interface-specific evaluation UI
 * - Footer: Previous/Next navigation, status tag, case number
 */
import { ref, computed, defineAsyncComponent, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMobile } from '@/composables/useMobile'
import { useEvaluationSession, SESSION_STATUS } from '@/composables/useEvaluationSession'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  },
  itemId: {
    type: [Number, String],
    default: null
  }
})

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()

// Get scenario ID from props or route
const scenarioId = computed(() => {
  return Number(props.scenarioId || route.params.scenarioId)
})

// Use evaluation session composable
const {
  status,
  items,
  scenario,
  config,
  error,
  progress,
  currentItem,
  currentIndex,
  hasNext,
  hasPrev,
  progressPercent,
  isComplete,
  isReady,
  loadSession,
  goToItemById,
  goNext,
  goPrev,
  markItemCompleted
} = useEvaluationSession(scenarioId.value)

// Local state for current item status (updated by child interfaces)
const currentItemStatus = ref('pending')
const isSaving = ref(false)

// Watch for session ready and navigate to initial item if provided
watch(isReady, (ready) => {
  if (ready && initialItemId.value) {
    goToItemById(initialItemId.value)
  }
}, { immediate: true })

// Watch for route changes (when navigating between items)
watch(() => route.params.itemId, (newItemId) => {
  if (isReady.value && newItemId) {
    goToItemById(newItemId)
  }
})

// Watch for current item changes to reset status
watch(currentItem, (newItem) => {
  if (newItem) {
    // Reset status based on item's evaluated state
    currentItemStatus.value = newItem.status || (newItem.evaluated ? 'done' : 'pending')
  }
}, { immediate: true })

// Function type from loaded scenario (function_type_id)
// 1=ranking, 2=rating, 3=mail_rating, 4=comparison, 5=authenticity, 7=labeling
const FUNCTION_TYPE_MAP = {
  1: 'ranking',
  2: 'rating',
  3: 'mail_rating',
  4: 'comparison',
  5: 'authenticity',
  7: 'labeling'
}

const functionType = computed(() => {
  // First try from loaded scenario data
  if (scenario.value?.function_type_id) {
    return FUNCTION_TYPE_MAP[scenario.value.function_type_id] || 'rating'
  }
  // Fallback to route meta or params
  return route.meta?.functionType || route.params.type || 'rating'
})

// Computed
const isLoading = computed(() => status.value === SESSION_STATUS.LOADING)

// Default interface based on function type
const defaultInterface = computed(() => {
  const interfaces = {
    rating: defineAsyncComponent(() => import('./interfaces/RatingInterface.vue')),
    mail_rating: defineAsyncComponent(() => import('./interfaces/RatingInterface.vue')),
    ranking: defineAsyncComponent(() => import('./interfaces/RankingInterface.vue')),
    comparison: defineAsyncComponent(() => import('./interfaces/ComparisonInterface.vue')),
    authenticity: defineAsyncComponent(() => import('./interfaces/AuthenticityInterface.vue')),
    labeling: defineAsyncComponent(() => import('./interfaces/LabelingInterface.vue'))
  }
  return interfaces[functionType.value] || interfaces.rating
})

// Get initial item ID from props or route
const initialItemId = computed(() => {
  return props.itemId || route.params.itemId || null
})

// Navigation
function goBack() {
  // Go back to items overview for this scenario
  router.push({ name: 'EvaluationItemsOverview', params: { scenarioId: scenarioId.value } })
}

function reload() {
  loadSession()
}

// Handle navigation with route update
function handleNext() {
  if (hasNext.value) {
    const nextIndex = currentIndex.value + 1
    const nextItem = items.value[nextIndex]
    const nextItemId = nextItem?.thread_id || nextItem?.id || nextItem?.item_id
    if (nextItemId) {
      router.push({
        name: 'EvaluationSessionItem',
        params: { scenarioId: scenarioId.value, itemId: nextItemId }
      })
    }
  }
}

function handlePrev() {
  if (hasPrev.value) {
    const prevIndex = currentIndex.value - 1
    const prevItem = items.value[prevIndex]
    const prevItemId = prevItem?.thread_id || prevItem?.id || prevItem?.item_id
    if (prevItemId) {
      router.push({
        name: 'EvaluationSessionItem',
        params: { scenarioId: scenarioId.value, itemId: prevItemId }
      })
    }
  }
}

// Handle status updates from child interfaces
function handleStatusChange(newStatus) {
  currentItemStatus.value = newStatus
}

function handleSavingChange(saving) {
  isSaving.value = saving
}

// Handle item completion - update progress without reloading
function handleItemCompleted(itemId) {
  markItemCompleted(itemId)
}
</script>

<style scoped>
.evaluation-session {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

/* Header */
.session-header {
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

/* Navigation Buttons */
.nav-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Content Area */
.session-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* Unified Navigation Footer */
.session-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
}

.footer-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-center .nav-position {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.8);
  white-space: nowrap;
}

/* Loading State */
.session-loading {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.session-loading p {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Error State */
.session-error {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 24px;
}

.session-error h3 {
  margin: 0;
  color: rgb(var(--v-theme-error));
}

.session-error p {
  color: rgba(var(--v-theme-on-surface), 0.6);
  max-width: 400px;
}

/* Empty State */
.session-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 24px;
}

.session-empty h3 {
  margin: 0;
}

.session-empty p {
  max-width: 400px;
}

/* Complete State */
.session-complete {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  text-align: center;
  padding: 24px;
}

.session-complete h3 {
  margin: 0;
  color: rgb(var(--v-theme-success));
}

.session-complete p {
  max-width: 400px;
}

/* Mobile Adjustments */
.evaluation-session.is-mobile .session-header {
  flex-direction: column;
  gap: 12px;
  padding: 12px 16px;
}

.evaluation-session.is-mobile .header-left,
.evaluation-session.is-mobile .header-right {
  width: 100%;
}

.evaluation-session.is-mobile .header-right {
  justify-content: space-between;
}

.evaluation-session.is-mobile .progress-bar {
  width: 80px;
}

.evaluation-session.is-mobile .header-info h1 {
  font-size: 1rem;
}

.evaluation-session.is-mobile .session-footer {
  padding: 10px 16px;
}

.evaluation-session.is-mobile .footer-center {
  gap: 8px;
}

.evaluation-session.is-mobile .footer-center .nav-position {
  font-size: 0.8rem;
}
</style>
