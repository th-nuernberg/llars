<template>
  <LEvaluationLayout
    :title="scenario?.name || $t('evaluation.labeling.pageTitle')"
    :subtitle="currentItem?.subject || $t('evaluation.labeling.emptyTitle')"
    :back-label="$t('common.back')"
    :status="evaluationStatus"
    :can-go-prev="hasPrev"
    :can-go-next="hasNext"
    :current-index="currentItemIndex"
    :total-items="items.length"
    @back="navigateBack"
    @prev="goPrev"
    @next="goNext"
  >
    <!-- Main Content -->
    <div ref="containerRef" class="content-panels" :class="{ 'is-mobile': isMobile }">
      <!-- Loading State -->
      <template v-if="loading">
        <div class="panel left-panel">
          <v-skeleton-loader type="card" class="fill-height" />
        </div>
        <div class="panel right-panel">
          <v-skeleton-loader type="card" class="fill-height" />
        </div>
      </template>

      <!-- Loaded Content -->
      <template v-else>
        <!-- Content Panel (links) - Messages/Text -->
        <div class="panel content-panel" :style="leftPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">mdi-text-box-outline</LIcon>
            <span class="panel-title">{{ $t('evaluation.labeling.content') }}</span>
            <v-spacer />
            <LTag v-if="items.length > 0" variant="info" size="small">
              {{ currentItemIndex + 1 }}/{{ items.length }}
            </LTag>
          </div>
          <div class="panel-content">
            <!-- Loading item details -->
            <div v-if="loadingItem" class="loading-content">
              <v-progress-circular indeterminate color="primary" size="32" />
              <span>{{ $t('common.loading') }}</span>
            </div>
            <!-- Messages Display -->
            <LMessageList v-else-if="messages.length > 0" :messages="messages" />
            <!-- Plain Content Display -->
            <div v-else-if="content" class="plain-content">
              <div class="content-text">{{ content }}</div>
            </div>
            <!-- Empty State -->
            <div v-else class="empty-content">
              <LIcon size="48" color="grey-lighten-1">mdi-text-box-remove-outline</LIcon>
              <p>{{ $t('evaluation.labeling.emptyTitle') }}</p>
            </div>
          </div>
        </div>

        <!-- Resize Divider (hidden on mobile) -->
        <div
          v-if="!isMobile"
          class="resize-divider"
          :class="{ 'resizing': isResizing }"
          @mousedown="startResize"
        >
          <div class="resize-handle"></div>
        </div>

        <!-- Labeling Panel (rechts) - Category Selection -->
        <div class="panel labeling-panel" :style="rightPanelStyle()">
          <div class="panel-header">
            <LIcon size="20" class="mr-2">mdi-label-outline</LIcon>
            <span class="panel-title">{{ $t('evaluation.labeling.selectCategory') }}</span>
            <v-spacer />
            <LTag :variant="selectedCategory ? 'success' : 'default'" size="small">
              {{ selectedCategory ? $t('evaluation.labeling.selected') : $t('evaluation.labeling.notSelected') }}
            </LTag>
          </div>
          <div class="panel-content">
            <!-- Category Selection -->
            <div class="category-section">
              <p class="category-instruction">
                {{ $t('evaluation.labeling.instruction') }}
              </p>

              <!-- Category Buttons -->
              <div class="category-buttons">
                <button
                  v-for="cat in categories"
                  :key="cat.id"
                  class="category-btn"
                  :class="{ selected: selectedCategory === cat.id }"
                  :style="getCategoryStyle(cat)"
                  @click="selectCategory(cat.id)"
                >
                  <span class="category-name">{{ cat.name }}</span>
                  <span v-if="cat.description" class="category-desc">{{ cat.description }}</span>
                </button>
              </div>

              <!-- Unsure Option -->
              <div v-if="evalConfig?.allowUnsure" class="unsure-option">
                <v-checkbox
                  v-model="isUnsure"
                  :label="$t('evaluation.labeling.unsure')"
                  density="compact"
                  hide-details
                />
              </div>
            </div>

            <!-- Feedback Section -->
            <div v-if="evalConfig?.allowFeedback !== false" class="feedback-section">
              <v-textarea
                v-model="feedback"
                :label="$t('evaluation.labeling.feedback')"
                :placeholder="$t('evaluation.labeling.feedbackPlaceholder')"
                variant="outlined"
                density="compact"
                rows="2"
                auto-grow
                hide-details
              />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Action Bar -->
    <template #action-bar-right>
      <LBtn
        :variant="canSubmit ? 'primary' : 'secondary'"
        :disabled="!canSubmit || submitting"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ hasNext ? $t('evaluation.labeling.saveAndNext') : $t('evaluation.labeling.complete') }}
        <LIcon end>{{ hasNext ? 'mdi-arrow-right' : 'mdi-check' }}</LIcon>
      </LBtn>
    </template>
  </LEvaluationLayout>
</template>

<script setup>
/**
 * LabelingInterface.vue - Category Labeling Interface
 *
 * Provides the UI for labeling/categorizing content items.
 * Uses the same layout as RaterDetail (LEvaluationLayout).
 *
 * Layout:
 * - Left Panel: Content to be labeled (messages/text)
 * - Right Panel: Category selection buttons
 */
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'
import axios from 'axios'

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

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isMobile } = useMobile()

// Panel resize composable
const {
  containerRef,
  leftPanelStyle,
  rightPanelStyle,
  startResize,
  isResizing
} = usePanelResize({
  initialLeftPercent: 50,
  minLeftPercent: 35,
  maxLeftPercent: 65,
  storageKey: 'llars-labeling-panel-width'
})

// State
const items = ref([])
const currentItemIndex = ref(0)
const loading = ref(true)
const loadingItem = ref(false)
const submitting = ref(false)
const selectedCategory = ref(null)
const isUnsure = ref(false)
const feedback = ref('')
const currentItemDetail = ref(null)

// Computed
const currentItem = computed(() => items.value[currentItemIndex.value] || null)

const messages = computed(() => {
  if (currentItemDetail.value?.messages) {
    return currentItemDetail.value.messages.map(m => ({
      ...m,
      sender: m.sender || 'Content'
    }))
  }
  return []
})

const content = computed(() => {
  if (messages.value.length > 0) {
    return messages.value.map(m => m.content).join('\n\n')
  }
  const item = currentItem.value
  if (!item) return ''
  return item.content || ''
})

const categories = computed(() => {
  return props.config?.categories || []
})

const evalConfig = computed(() => props.config || {})

const hasNext = computed(() => currentItemIndex.value < items.value.length - 1)
const hasPrev = computed(() => currentItemIndex.value > 0)

const canSubmit = computed(() => {
  return selectedCategory.value !== null || isUnsure.value
})

const completedCount = computed(() => {
  return items.value.filter(i => i.evaluated).length
})

const evaluationStatus = computed(() => {
  if (completedCount.value === 0) return 'pending'
  if (completedCount.value >= items.value.length) return 'done'
  return 'in_progress'
})

// Methods
function getCategoryStyle(cat) {
  const isSelected = selectedCategory.value === cat.id
  const baseColor = cat.color || '#b0ca97'

  return {
    '--category-color': baseColor,
    '--category-bg': isSelected ? baseColor : 'transparent',
    '--category-text': isSelected ? '#fff' : baseColor,
    borderColor: baseColor
  }
}

function selectCategory(categoryId) {
  if (selectedCategory.value === categoryId) {
    selectedCategory.value = null
  } else {
    selectedCategory.value = categoryId
    isUnsure.value = false
  }
}

async function loadItems() {
  loading.value = true
  try {
    const response = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = response.data.items || []

    const firstIncomplete = items.value.findIndex(i => !i.evaluated)
    if (firstIncomplete >= 0) {
      currentItemIndex.value = firstIncomplete
    }

    await loadCurrentItemDetail()
  } catch (err) {
    console.error('Failed to load labeling items:', err)
  } finally {
    loading.value = false
  }
}

async function loadCurrentItemDetail() {
  const item = currentItem.value
  if (!item) return

  // Reset state
  selectedCategory.value = null
  isUnsure.value = false
  feedback.value = ''
  currentItemDetail.value = null

  loadingItem.value = true
  try {
    const response = await axios.get(
      `/api/scenarios/${props.scenarioId}/threads/${item.thread_id}`
    )
    currentItemDetail.value = response.data.thread || response.data
  } catch (err) {
    console.error('Failed to load item details:', err)
  } finally {
    loadingItem.value = false
  }

  if (item.evaluation) {
    selectedCategory.value = item.evaluation.category_id || null
    feedback.value = item.evaluation.feedback || ''
  }
}

async function handleSubmit() {
  if (!canSubmit.value || !currentItem.value) return

  submitting.value = true

  try {
    await axios.post(
      `/api/evaluation/session/${props.scenarioId}/items/${currentItem.value.thread_id}/evaluate`,
      {
        function_type: 'labeling',
        category_id: selectedCategory.value,
        is_unsure: isUnsure.value,
        feedback: feedback.value
      }
    )

    items.value[currentItemIndex.value].evaluated = true
    items.value[currentItemIndex.value].evaluation = {
      category_id: selectedCategory.value,
      feedback: feedback.value
    }

    emit('item-completed', currentItem.value.thread_id)

    if (completedCount.value === items.value.length) {
      emit('all-completed')
    } else if (hasNext.value) {
      goNext()
    }
  } catch (err) {
    console.error('Failed to submit labeling:', err)
  } finally {
    submitting.value = false
  }
}

function goNext() {
  if (!hasNext.value) return
  currentItemIndex.value++
  loadCurrentItemDetail()
}

function goPrev() {
  if (!hasPrev.value) return
  currentItemIndex.value--
  loadCurrentItemDetail()
}

function navigateBack() {
  const fromScenario = route.query.from
  if (fromScenario) {
    router.push({ name: 'EvaluationScenario', params: { scenarioId: fromScenario } })
  } else {
    router.push({ name: 'EvaluationHub' })
  }
}

// Watch for item changes
watch(currentItemIndex, () => {
  loadCurrentItemDetail()
})

// Initialize
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
/* Content Panels Layout */
.content-panels {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-panels.is-mobile {
  flex-direction: column;
}

/* Panel Base Styles */
.panel {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-surface));
}

.content-panel {
  flex-shrink: 0;
}

.labeling-panel {
  flex: 1;
  min-width: 0;
}

/* Panel Header */
.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: rgba(var(--v-theme-surface-variant), 0.3);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.panel-title {
  font-weight: 600;
  font-size: 0.9rem;
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Loading Content */
.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 16px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Plain Content */
.plain-content {
  padding: 16px;
}

.content-text {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 0.95rem;
}

/* Empty Content */
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Resize Divider */
.resize-divider {
  width: 6px;
  cursor: col-resize;
  background: rgba(var(--v-theme-on-surface), 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  flex-shrink: 0;
}

.resize-divider:hover,
.resize-divider.resizing {
  background: rgba(var(--v-theme-primary), 0.2);
}

.resize-handle {
  width: 3px;
  height: 40px;
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

/* Category Section */
.category-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.category-instruction {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-align: center;
}

/* Category Buttons */
.category-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 20px 24px;
  border: 2px solid var(--category-color);
  border-radius: 16px 4px 16px 4px;
  background: var(--category-bg);
  color: var(--category-text);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  text-align: center;
}

.category-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.category-btn.selected {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.category-name {
  font-size: 1.1rem;
  font-weight: 600;
}

.category-desc {
  font-size: 0.8rem;
  opacity: 0.8;
}

/* Unsure Option */
.unsure-option {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

/* Feedback Section */
.feedback-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Mobile Styles */
.content-panels.is-mobile .panel {
  width: 100% !important;
}

.content-panels.is-mobile .content-panel {
  max-height: 40vh;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Scrollbar styling */
.panel-content::-webkit-scrollbar {
  width: 6px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 3px;
}

.panel-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}
</style>
