<template>
  <div class="comparison-interface">
    <!-- Header with Info (hidden when embedded in EvaluationSession) -->
    <div v-if="!hideNavigation" class="comparison-header">
      <div class="header-info">
        <LIcon size="20" class="mr-2">mdi-compare-horizontal</LIcon>
        <h3>{{ $t('evaluation.comparison.title') }}</h3>
        <v-spacer />
        <LEvaluationStatus
          :status="currentItemStatus"
          :saving="saving"
        />
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loadingItem" class="loading-state">
      <v-progress-circular indeterminate color="primary" size="48" />
      <p>{{ $t('common.loading') }}</p>
    </div>

    <!-- Comparison Content -->
    <div v-else-if="currentItem" class="comparison-content">
      <!-- Two Options Side by Side -->
      <div class="options-container">
        <!-- Option A -->
        <div
          class="option-panel option-a"
          :class="{ selected: selectedOption === 'A' }"
          @click="selectOption('A')"
        >
          <div class="option-header">
            <LTag variant="primary" size="sm">Option A</LTag>
          </div>
          <div class="option-content">
            <LMessageList v-if="optionA.messages?.length > 0" :messages="optionA.messages" />
            <div v-else-if="optionA.content" class="content-text">{{ optionA.content }}</div>
            <div v-else class="empty-content">{{ $t('evaluation.comparison.noContent') }}</div>
          </div>
          <div class="option-footer">
            <button
              class="select-btn"
              :class="{ selected: selectedOption === 'A' }"
              :disabled="saving"
              @click.stop="selectOption('A')"
            >
              <LIcon size="20">{{ selectedOption === 'A' ? 'mdi-check-circle' : 'mdi-circle-outline' }}</LIcon>
              <span>{{ $t('evaluation.comparison.selectA') }}</span>
            </button>
          </div>
        </div>

        <!-- VS Divider -->
        <div class="vs-divider">
          <span class="vs-text">VS</span>
        </div>

        <!-- Option B -->
        <div
          class="option-panel option-b"
          :class="{ selected: selectedOption === 'B' }"
          @click="selectOption('B')"
        >
          <div class="option-header">
            <LTag variant="secondary" size="sm">Option B</LTag>
          </div>
          <div class="option-content">
            <LMessageList v-if="optionB.messages?.length > 0" :messages="optionB.messages" />
            <div v-else-if="optionB.content" class="content-text">{{ optionB.content }}</div>
            <div v-else class="empty-content">{{ $t('evaluation.comparison.noContent') }}</div>
          </div>
          <div class="option-footer">
            <button
              class="select-btn"
              :class="{ selected: selectedOption === 'B' }"
              :disabled="saving"
              @click.stop="selectOption('B')"
            >
              <LIcon size="20">{{ selectedOption === 'B' ? 'mdi-check-circle' : 'mdi-circle-outline' }}</LIcon>
              <span>{{ $t('evaluation.comparison.selectB') }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Tie Option -->
      <div class="tie-section">
        <button
          class="tie-btn"
          :class="{ selected: selectedOption === 'tie' }"
          :disabled="saving"
          @click="selectOption('tie')"
        >
          <LIcon size="20">mdi-equal</LIcon>
          <span>{{ $t('evaluation.comparison.tie') }}</span>
        </button>
      </div>

      <!-- Notes -->
      <div class="notes-section">
        <span class="section-label">{{ $t('evaluation.comparison.notesLabel') }}</span>
        <v-textarea
          v-model="notes"
          variant="outlined"
          density="compact"
          auto-grow
          rows="2"
          hide-details
          :placeholder="$t('evaluation.comparison.notesPlaceholder')"
          @blur="saveMetadata"
        />
      </div>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <LIcon size="64" color="grey-lighten-1">mdi-compare-horizontal-off</LIcon>
      <h3>{{ $t('evaluation.comparison.emptyTitle') }}</h3>
    </div>

    <!-- Navigation Footer (only shown if hideNavigation is false) -->
    <div class="nav-footer" v-if="items.length > 0 && !hideNavigation">
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
</template>

<script setup>
/**
 * ComparisonInterface.vue - A/B Comparison Interface
 *
 * Provides the UI for comparison evaluation where users choose
 * between two options (A vs B) or declare a tie.
 */
import { ref, computed, watch, onMounted, toRef } from 'vue'
import { usePanelResize } from '@/composables/usePanelResize'
import { useComparisonEvaluation } from '@/composables/useComparisonEvaluation'

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

// Comparison evaluation composable
const scenarioIdRef = toRef(props, 'scenarioId')
const {
  items,
  currentItem,
  currentItemIndex,
  optionA,
  optionB,
  selectedOption,
  notes,
  loading,
  loadingItem,
  saving,
  error,
  progress,
  hasNext,
  hasPrev,
  currentItemStatus,
  loadItems,
  loadItem,
  selectOption: doSelectOption,
  saveMetadata: doSaveMetadata,
  goNext,
  goPrev
} = useComparisonEvaluation(scenarioIdRef)

// Emit status changes to parent
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving changes to parent
watch(saving, (isSaving) => {
  emit('saving-change', isSaving)
})

// Select option (auto-saves)
async function selectOption(option) {
  if (!canEvaluate.value) return
  const result = await doSelectOption(option)
  if (result.success) {
    emit('item-completed', currentItem.value?.item_id)
    if (progress.value.completed === progress.value.total) {
      emit('all-completed')
    }
  }
}

// Save metadata on blur
function saveMetadata() {
  doSaveMetadata()
}

// Initialize on mount
onMounted(async () => {
  await loadItems()
  // Navigate to initial item if specified
  if (props.initialItemId && items.value.length > 0) {
    const targetItemId = Number(props.initialItemId)
    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
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
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetItemId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetItemId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      const item = items.value[targetIndex]
      await loadItem(item.thread_id || item.id || item.item_id)
    }
  }
})
</script>

<style scoped>
.comparison-interface {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

/* Header */
.comparison-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.header-info {
  display: flex;
  align-items: center;
  flex: 1;
}

.header-info h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 600;
}

/* Loading & Empty States */
.loading-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Content */
.comparison-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Options Container */
.options-container {
  display: flex;
  gap: 8px;
  flex: 1;
  min-height: 300px;
}

.option-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 12px 3px 12px 3px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.option-panel:hover {
  border-color: rgba(var(--v-theme-on-surface), 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.option-a.selected {
  border-color: var(--llars-primary, #b0ca97);
  box-shadow: 0 0 0 3px rgba(176, 202, 151, 0.25);
}

.option-b.selected {
  border-color: var(--llars-secondary, #D1BC8A);
  box-shadow: 0 0 0 3px rgba(209, 188, 138, 0.25);
}

.option-header {
  padding: 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
}

.option-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.6;
}

.empty-content {
  color: rgba(var(--v-theme-on-surface), 0.4);
  text-align: center;
  padding: 24px;
}

.option-footer {
  padding: 12px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.2);
}

/* Select Button */
.select-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px;
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.select-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.option-a .select-btn.selected {
  background: var(--llars-primary, #b0ca97);
  border-color: transparent;
  color: white;
}

.option-b .select-btn.selected {
  background: var(--llars-secondary, #D1BC8A);
  border-color: transparent;
  color: white;
}

/* VS Divider */
.vs-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
}

.vs-text {
  font-size: 1.2rem;
  font-weight: 700;
  color: rgba(var(--v-theme-on-surface), 0.3);
}

/* Tie Section */
.tie-section {
  display: flex;
  justify-content: center;
}

.tie-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border: 2px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 8px 3px 8px 3px;
  background: transparent;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.tie-btn:hover:not(:disabled) {
  background: rgba(var(--v-theme-on-surface), 0.05);
}

.tie-btn.selected {
  background: var(--llars-accent, #88c4c8);
  border-color: transparent;
  color: white;
}

/* Notes Section */
.notes-section {
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.section-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  margin-bottom: 8px;
}

/* Navigation Footer */
.nav-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
  gap: 12px;
}

.nav-footer .nav-position {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(var(--v-theme-on-surface), 0.7);
  min-width: 60px;
  text-align: center;
}

/* Responsive */
@media (max-width: 768px) {
  .options-container {
    flex-direction: column;
  }

  .vs-divider {
    padding: 8px 0;
  }
}
</style>
