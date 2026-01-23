<template>
  <div class="rating-interface" ref="containerRef">
    <!-- Left Panel: Content to Rate -->
    <div class="left-panel" :style="leftPanelStyle()">
      <div class="panel-header">
        <LIcon size="20" class="mr-2">mdi-text-box-outline</LIcon>
        <h3>{{ $t('evaluation.rating.content') }}</h3>
        <v-spacer />
        <LTag v-if="items.length > 0" variant="info" size="sm">
          {{ currentItemIndex + 1 }}/{{ items.length }}
        </LTag>
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
      <div class="panel-header">
        <LIcon size="20" class="mr-2">mdi-clipboard-check-outline</LIcon>
        <h3>{{ $t('evaluation.rating.dimensions') }}</h3>
        <v-spacer />
        <LTag :variant="canSubmit ? 'success' : 'default'" size="sm">
          {{ ratedDimensionCount }}/{{ dimensions.length }} {{ $t('evaluation.rating.rated') }}
        </LTag>
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
            :disabled="submitting"
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
            :disabled="submitting"
          />
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state">
        <LIcon size="48" color="grey-lighten-1">mdi-clipboard-off-outline</LIcon>
        <h3>{{ $t('evaluation.rating.emptyTitle') }}</h3>
      </div>

      <!-- Bottom Action Bar -->
      <div class="action-bar" v-if="currentItem">
        <LBtn
          variant="text"
          :disabled="!hasPrev || submitting"
          @click="handlePrev"
        >
          <LIcon start>mdi-arrow-left</LIcon>
          {{ $t('common.back') }}
        </LBtn>

        <div class="progress-indicator">
          <span class="progress-text">
            {{ progress.completed }}/{{ progress.total }}
            {{ $t('evaluation.rating.itemsCompleted') }}
          </span>
          <v-progress-linear
            :model-value="progress.percent"
            height="4"
            :color="progress.percent === 100 ? 'success' : 'primary'"
            rounded
            class="progress-bar"
          />
        </div>

        <LBtn
          :variant="canSubmit ? 'primary' : 'secondary'"
          :disabled="!canSubmit || submitting"
          :loading="submitting"
          @click="handleSubmit"
        >
          {{ hasNext ? $t('evaluation.rating.saveAndNext') : $t('evaluation.rating.complete') }}
          <LIcon end>{{ hasNext ? 'mdi-arrow-right' : 'mdi-check' }}</LIcon>
        </LBtn>
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
import { useI18n } from 'vue-i18n'
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
  }
})

const emit = defineEmits(['item-completed', 'all-completed'])

const { t } = useI18n()

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

  loadItems,
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

// Handle dimension rating change
function handleDimensionRating(dimensionId, value) {
  setDimensionRating(dimensionId, value)
}

// Handle submit and next
async function handleSubmit() {
  // Sync feedback before submit
  feedback.value = localFeedback.value

  const result = await submitRating({ autoAdvance: hasNext.value })

  if (result.success) {
    emit('item-completed', currentItem.value?.item_id)

    // Check if all completed
    if (progress.value.completed === progress.value.total) {
      emit('all-completed')
    }
  }
}

// Handle previous navigation
async function handlePrev() {
  await goPrev()
}

// Initialize on mount
onMounted(() => {
  loadItems()
})

// Watch for scenario changes
watch(() => props.scenarioId, (newId) => {
  if (newId) {
    loadItems()
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

/* Action Bar */
.action-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.progress-indicator {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.progress-text {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.progress-bar {
  width: 100%;
  max-width: 200px;
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

  .action-bar {
    flex-wrap: wrap;
    justify-content: center;
  }

  .progress-indicator {
    order: -1;
    width: 100%;
    margin-bottom: 8px;
  }
}
</style>
