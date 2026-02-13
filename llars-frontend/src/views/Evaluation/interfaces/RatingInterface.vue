<template>
  <div class="rating-interface" ref="containerRef">
    <!-- Left Panel: Content to Rate -->
    <div class="left-panel" :style="leftPanelStyle()">
      <!-- Panel Header (hidden when embedded in EvaluationSession) -->
      <div v-if="!hideNavigation" class="panel-header">
        <LIcon size="20" class="mr-2">mdi-text-box-outline</LIcon>
        <h3>{{ $t('evaluation.rating.content') }}</h3>
      </div>

      <!-- Content Panel Component -->
      <ContentPanel
        :item="currentItem"
        :messages="messages"
        :content="content"
        :show-metadata="true"
      />
    </div>

    <!-- Resize Handle -->
    <div class="resize-handle" @mousedown="startResize">
      <div class="handle-line" />
    </div>

    <!-- Right Panel: Dimensional Rating -->
    <div class="right-panel" :style="rightPanelStyle()">
      <!-- Panel Header (hidden when embedded in EvaluationSession) -->
      <div v-if="!hideNavigation" class="panel-header">
        <LIcon size="20" class="mr-2">mdi-clipboard-check-outline</LIcon>
        <h3>{{ $t('evaluation.rating.dimensions') }}</h3>
        <v-spacer />
        <!-- Status Chip -->
        <LEvaluationStatus
          :status="currentItemStatus"
          :saving="saving"
        />
      </div>

      <!-- Loading State -->
      <div v-if="loadingItem" class="loading-state">
        <v-progress-circular indeterminate color="primary" size="32" />
        <span>{{ $t('common.loading') }}</span>
      </div>

      <!-- Dimension Ratings -->
      <div v-else-if="currentItem" class="rating-content">
        <!-- Dimension Cards -->
        <div class="dimension-list">
          <DimensionRatingCard
            v-for="dim in dimensions"
            :key="dim.id"
            :dimension="dim"
            :model-value="dimensionRatings[dim.id]"
            :labels="getDimensionLabels(dim)"
            :min="getDimensionMin(dim)"
            :max="getDimensionMax(dim)"
            :step="getDimensionStep(dim)"
            :disabled="submitting || !canEvaluate"
            @update:model-value="handleDimensionRating(dim.id, $event)"
          />
        </div>

        <!-- Overall Score Display -->
        <OverallScoreDisplay
          v-if="config?.showOverallScore !== false"
          :score="overallScore"
          :max-score="scaleMax"
          :labels="scaleLabels"
          :rated-count="ratedDimensionCount"
          :total-dimensions="dimensions.length"
          :show-progress="true"
        />

        <!-- Feedback Section -->
        <div v-if="config?.allowFeedback !== false" class="feedback-section">
          <v-textarea
            v-model="localFeedback"
            :label="$t('evaluation.rating.feedback')"
            :placeholder="$t('evaluation.rating.feedbackPlaceholder')"
            variant="outlined"
            density="compact"
            rows="2"
            auto-grow
            hide-details
            :disabled="submitting || !canEvaluate"
          />
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-clipboard-off-outline</LIcon>
        <h3>{{ $t('evaluation.rating.emptyTitle') }}</h3>
      </div>

      <!-- Rating Progress + Navigation Footer (hidden when embedded in EvaluationSession) -->
      <div class="rating-footer" v-if="currentItem && !hideNavigation">
        <div class="footer-progress" v-if="dimensions.length > 0">
          <span class="progress-label">
            {{ ratedDimensionCount }}/{{ dimensions.length }} {{ $t('evaluation.rating.rated') }}
          </span>
          <v-progress-linear
            :model-value="(ratedDimensionCount / dimensions.length) * 100"
            height="4"
            :color="canSubmit ? 'success' : 'primary'"
            rounded
            class="progress-bar"
          />
        </div>

        <!-- Navigation Buttons -->
        <div class="footer-nav">
          <LBtn
            variant="tonal"
            size="small"
            :disabled="!hasPrev"
            @click="goPrev"
          >
            <LIcon start>mdi-chevron-left</LIcon>
            {{ $t('common.previous') }}
          </LBtn>
          <span class="nav-position">
            {{ currentItemIndex + 1 }} / {{ items.length }}
          </span>
          <LBtn
            variant="primary"
            size="small"
            :disabled="!hasNext"
            @click="goNext"
          >
            {{ $t('common.next') }}
            <LIcon end>mdi-chevron-right</LIcon>
          </LBtn>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * RatingInterface.vue - Multi-Dimensional Rating Interface
 *
 * Provides the UI for rating content items on multiple dimensions
 * (e.g., Coherence, Fluency, Relevance, Consistency).
 *
 * Layout:
 * - Left Panel: Content to be rated (messages/text)
 * - Right Panel: Dimension rating cards with Likert scales
 *
 * This is the new generalized rating system that replaces the
 * feature-based rating with a text-based multi-dimensional approach.
 */
import { ref, computed, watch, onMounted, toRef } from 'vue'
import { usePanelResize } from '@/composables/usePanelResize'
import { useDimensionalRating } from '@/composables/useDimensionalRating'
import { DimensionRatingCard, ContentPanel, OverallScoreDisplay } from '@/components/Evaluation/rating'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  },
  scenario: {
    type: Object,
    default: null
  },
  config: {
    type: Object,
    default: () => ({})
  },
  initialItemId: {
    type: [Number, String],
    default: null
  },
  hideNavigation: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['item-completed', 'all-completed', 'status-change', 'saving-change'])

// Computed prop for hideNavigation to use in template
const hideNavigation = computed(() => props.hideNavigation)
const canEvaluate = computed(() => props.scenario?.can_evaluate !== false)

// Panel resize composable
const { containerRef, leftPanelStyle, rightPanelStyle, startResize } = usePanelResize({
  initialLeftPercent: 45,
  minLeftPercent: 30,
  maxLeftPercent: 60,
  storageKey: 'llars-dimensional-rating-panel-width'
})

// Dimensional rating composable
const scenarioIdRef = toRef(props, 'scenarioId')
const {
  items,
  currentItem,
  currentItemIndex,
  messages,
  content,
  config,
  dimensionRatings,
  feedback,

  loading,
  loadingItem,
  submitting,
  saving,
  error,

  dimensions,
  scaleMin,
  scaleMax,
  scaleStep,
  scaleLabels,
  overallScore,
  ratedDimensionCount,
  canSubmit,
  progress,
  hasNext,
  hasPrev,
  currentItemStatus,

  loadItems,
  loadItem,
  setDimensionRating,
  submitRating,
  goNext,
  goPrev
} = useDimensionalRating(scenarioIdRef)

// Local feedback state (synced with composable)
const localFeedback = ref('')

watch(feedback, (newVal) => {
  localFeedback.value = newVal || ''
}, { immediate: true })

watch(localFeedback, (newVal) => {
  feedback.value = newVal
})

// Emit status changes to parent
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving changes to parent
watch(saving, (isSaving) => {
  emit('saving-change', isSaving)
})

// Per-dimension scale helpers
// Returns the minimum value for a dimension (uses dimension's scale if available, else global)
function getDimensionMin(dim) {
  return dim.scale?.min ?? scaleMin.value
}

// Returns the maximum value for a dimension (uses dimension's scale if available, else global)
function getDimensionMax(dim) {
  return dim.scale?.max ?? scaleMax.value
}

// Returns the step value for a dimension (uses dimension's scale if available, else global)
function getDimensionStep(dim) {
  return dim.scale?.step ?? scaleStep.value
}

// Returns the labels for a dimension (uses dimension's scale labels if available, else global)
function getDimensionLabels(dim) {
  // If dimension has its own scale with labels, use those
  if (dim.scale?.labels && Object.keys(dim.scale.labels).length > 0) {
    return dim.scale.labels
  }
  // Otherwise use global labels
  return scaleLabels.value
}

// Handle dimension rating change (auto-saves via composable)
function handleDimensionRating(dimensionId, value) {
  if (!canEvaluate.value) return
  setDimensionRating(dimensionId, value)

  // Emit item-completed when all dimensions are rated
  if (canSubmit.value) {
    // Auto-complete the rating when all dimensions are filled
    submitRating({ autoAdvance: false }).then(result => {
      if (result.success) {
        emit('item-completed', currentItem.value?.item_id)

        // Check if all completed
        if (progress.value.completed === progress.value.total) {
          emit('all-completed')
        }
      }
    })
  }
}

// Initialize on mount
onMounted(async () => {
  await loadItems()
  // Navigate to initial item if specified
  if (props.initialItemId && items.value.length > 0) {
    const targetItemId = Number(props.initialItemId)
    const targetIndex = items.value.findIndex(item =>
      item.item_id === targetItemId || item.thread_id === targetItemId || item.id === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      await loadItem(items.value[targetIndex].item_id)
    }
  }
})

// Watch for scenario changes
watch(() => props.scenarioId, (newId) => {
  if (newId) {
    loadItems()
  }
})

// Watch for initialItemId changes (e.g., when navigating between items via URL)
watch(() => props.initialItemId, async (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetItemId = Number(newItemId)
    // Check if this item is already the current item
    const currentId = currentItem.value?.item_id || currentItem.value?.thread_id || currentItem.value?.id
    if (currentId === targetItemId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      item.item_id === targetItemId || item.thread_id === targetItemId || item.id === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      await loadItem(items.value[targetIndex].item_id)
    }
  }
})
</script>

<style scoped>
.rating-interface {
  display: flex;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

/* Panels */
.left-panel,
.right-panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.left-panel {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}

/* Resize Handle */
.resize-handle {
  width: 6px;
  cursor: col-resize;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-handle:hover {
  background: rgba(var(--v-theme-primary), 0.15);
}

.handle-line {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

/* Loading State */
.loading-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Rating Content */
.rating-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Dimension List */
.dimension-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Feedback Section */
.feedback-section {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Empty State */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.empty-state h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 500;
}

/* Rating Footer */
.rating-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  gap: 16px;
}

.footer-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.footer-progress .progress-label {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  white-space: nowrap;
}

.footer-progress .progress-bar {
  flex: 1;
  max-width: 150px;
}

.footer-nav {
  display: flex;
  align-items: center;
  gap: 12px;
}

.footer-nav .nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Scrollbar styling */
.rating-content::-webkit-scrollbar {
  width: 6px;
}

.rating-content::-webkit-scrollbar-track {
  background: transparent;
}

.rating-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.rating-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}

/* Responsive */
@media (max-width: 768px) {
  .rating-interface {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100% !important;
  }

  .left-panel {
    max-height: 40vh;
    border-right: none;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .resize-handle {
    display: none;
  }

  .rating-footer {
    flex-direction: column;
    gap: 12px;
  }

  .footer-progress {
    width: 100%;
    justify-content: center;
  }

  .footer-nav {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
