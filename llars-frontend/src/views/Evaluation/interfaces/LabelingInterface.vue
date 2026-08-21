<template>
  <LEvaluationLayout
    :title="scenario?.name || $t('evaluation.labeling.pageTitle')"
    :subtitle="cleanSource(currentItem?.subject) || $t('evaluation.labeling.emptyTitle')"
    :back-label="$t('common.back')"
    :status="evaluationStatus"
    :can-go-prev="hasPrev"
    :can-go-next="hasNext"
    :current-index="currentItemIndex"
    :total-items="items.length"
    :embedded="hideNavigation"
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
          <!-- Panel Header (hidden when embedded in EvaluationSession) -->
          <div v-if="!hideNavigation" class="panel-header">
            <LIcon size="20" class="mr-2">mdi-text-box-outline</LIcon>
            <span class="panel-title">{{ $t('evaluation.labeling.content') }}</span>
            <v-spacer />
            <!-- Mobile: read the (potentially long) content in a fullscreen
                 overlay so it doesn't compete with the category buttons /
                 feedback box in the cramped stacked layout. Hidden on desktop. -->
            <LIconBtn
              v-if="isMobile && (messages.length > 0 || content)"
              class="content-fullscreen-btn"
              icon="mdi-fullscreen"
              variant="default"
              size="x-small"
              :tooltip="$t('evaluation.labeling.readFullscreen')"
              @click.stop="fullscreenOpen = true"
            />
            <LTag v-if="items.length > 0" variant="info" size="small">
              {{ currentItemIndex + 1 }}/{{ items.length }}
            </LTag>
          </div>
          <div class="panel-content">
            <!-- Embedded mobile: the panel header (with its fullscreen button)
                 is hidden, so expose a floating trigger here instead. -->
            <LIconBtn
              v-if="isMobile && hideNavigation && (messages.length > 0 || content)"
              class="content-fullscreen-fab"
              icon="mdi-fullscreen"
              variant="default"
              size="small"
              :tooltip="$t('evaluation.labeling.readFullscreen')"
              @click.stop="fullscreenOpen = true"
            />
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
          <!-- Panel Header (hidden when embedded in EvaluationSession) -->
          <div v-if="!hideNavigation" class="panel-header">
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

              <!-- Co-Pilot suggestion (LLM pre-annotation). Clearly marked as a
                   suggestion and NEVER pre-selected: accepting requires a
                   deliberate click (anchoring reduction, PsyDefConv A.8).
                   Absent = disabled / not generated / failed / hidden control
                   item — the UI cannot and must not distinguish these. -->
              <div v-if="copilotSuggestions.length" class="copilot-card">
                <div class="copilot-header">
                  <LIcon size="16" class="mr-1" color="#88c4c8">mdi-robot-outline</LIcon>
                  <span class="copilot-title">{{ $t('evaluation.labeling.copilot.title') }}</span>
                  <v-spacer />
                  <span class="copilot-helpful-label">{{ $t('evaluation.labeling.copilot.helpfulQuestion') }}</span>
                  <LIconBtn
                    :icon="copilotHelpful === true ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                    variant="default"
                    size="x-small"
                    :tooltip="$t('evaluation.labeling.copilot.helpfulYes')"
                    @click="setHelpful(true)"
                  />
                  <LIconBtn
                    :icon="copilotHelpful === false ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                    variant="default"
                    size="x-small"
                    :tooltip="$t('evaluation.labeling.copilot.helpfulNo')"
                    @click="setHelpful(false)"
                  />
                </div>

                <div
                  v-for="(suggestion, idx) in copilotSuggestions"
                  :key="`${currentItem?.thread_id}-${idx}`"
                  class="copilot-suggestion"
                >
                  <div class="copilot-suggestion-head">
                    <LTag size="small" :variant="idx === 0 ? 'info' : 'default'">
                      {{ idx === 0
                        ? $t('evaluation.labeling.copilot.primary')
                        : $t('evaluation.labeling.copilot.secondary') }}
                    </LTag>
                    <span class="copilot-label-chip" :style="suggestionChipStyle(suggestion)">
                      {{ suggestionLabelName(suggestion) }}
                    </span>
                    <LTag size="small" :variant="confidenceVariant(suggestion.confidence)">
                      {{ $t(`evaluation.labeling.copilot.confidence.${suggestion.confidence || 'medium'}`) }}
                    </LTag>
                    <v-spacer />
                    <LBtn
                      size="small"
                      variant="secondary"
                      :disabled="!canEvaluate"
                      @click="applySuggestion(suggestion)"
                    >
                      {{ $t('evaluation.labeling.copilot.apply') }}
                    </LBtn>
                  </div>
                  <p v-if="suggestion.rationale" class="copilot-rationale">{{ suggestion.rationale }}</p>
                  <p v-if="suggestion.evidence" class="copilot-evidence">„{{ suggestion.evidence }}“</p>
                </div>

                <p class="copilot-guardrail">
                  <LIcon size="13" class="mr-1">mdi-shield-alert-outline</LIcon>
                  {{ $t('evaluation.labeling.copilot.guardrail') }}
                </p>
              </div>

              <!-- Category Buttons -->
              <div class="category-buttons">
                <LLabelButton
                  v-for="cat in categories"
                  :key="cat.id"
                  :category="cat"
                  :model-value="selectedCategory"
                  @select="selectCategory"
                />
              </div>

              <!-- Unsure Option -->
              <div v-if="evalConfig?.allowUnsure" class="unsure-option">
                <v-checkbox
                  :model-value="isUnsure"
                  :disabled="!canEvaluate"
                  :label="$t('evaluation.labeling.unsure')"
                  density="compact"
                  hide-details
                  @update:model-value="onUnsureChange"
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

    <!-- Mobile-only fullscreen read overlay for the content being labeled.
         Mirrors the ComparisonInterface fullscreen pattern (v-dialog fullscreen
         + top bar + close button) so a long conversation/text can be read
         comfortably without the category buttons and feedback box squeezing it.
         The overlay is read-only; labeling happens back on the main view. -->
    <v-dialog
      v-model="fullscreenOpen"
      fullscreen
      :scrim="false"
      transition="dialog-bottom-transition"
    >
      <div class="content-fullscreen">
        <div class="content-fullscreen-bar">
          <LIcon size="20" class="mr-2">mdi-text-box-outline</LIcon>
          <span class="content-fullscreen-title">{{ $t('evaluation.labeling.content') }}</span>
          <v-spacer />
          <LBtn variant="text" size="small" prepend-icon="mdi-close" @click="fullscreenOpen = false">
            {{ $t('common.close') }}
          </LBtn>
        </div>
        <div class="content-fullscreen-content">
          <LMessageList v-if="messages.length > 0" :messages="messages" />
          <div v-else-if="content" class="content-text">{{ content }}</div>
          <div v-else class="empty-content">{{ $t('evaluation.labeling.emptyTitle') }}</div>
        </div>
      </div>
    </v-dialog>
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
import { ref, computed, watch, onMounted, nextTick } from 'vue'
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

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const { isMobile } = useMobile()

// Localize a value that may be a plain string or a localized object {de, en}.
// api_v1-created scenarios store option labels as localized objects (canonical
// evaluation_data_schemas shape); wizard/legacy scenarios store plain strings.
function localize(v) {
  if (v == null) return ''
  if (typeof v === 'string') return v
  return v[locale.value] || v.de || v.en || ''
}

// Normalize a provenance/source value for display. The backend can leak the
// raw Python enum text (e.g. "SourceType.HUMAN") into item subjects/headers;
// map the known source kinds to a friendly localized label and strip any
// leftover "SourceType." prefix so it never reaches the UI verbatim.
function cleanSource(v) {
  if (v == null) return ''
  const raw = String(v).replace(/^SourceType\./i, '').trim()
  const key = raw.toLowerCase()
  if (key === 'human') return t('evaluation.source.human')
  if (key === 'llm' || key === 'ai') return t('evaluation.source.ai')
  return raw
}

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

// When embedded in EvaluationSession (hideNavigation=true), LEvaluationLayout
// hides the action bar — and with it the explicit "Save & Next" button that
// used to be the ONLY trigger for the labeling POST. The session footer's
// "Next" button merely navigates, so without auto-save a labeling evaluation
// was never persisted (see ItemLabelingEvaluation — table stayed empty in
// production). We now auto-save on selection, mirroring ComparisonInterface
// (selectOption) and RatingInterface (dimension change), which both POST
// immediately rather than waiting on a submit button.
//
// `suppressAutoSave` gates the auto-save watchers while we programmatically
// reset + restore the inputs for a freshly-loaded item, so navigating between
// items doesn't re-POST the already-saved (or empty) value.
const suppressAutoSave = ref(false)
let feedbackTimer = null

// Co-Pilot state. `copilotHelpful` is the per-item thumbs vote; it rides along
// with the next persist() (server only stores non-null values, so an untouched
// thumbs never clears an earlier vote). `itemShownAt` anchors the time-on-item
// measurement; the backend keeps only the FIRST written value per (user, item),
// so revisits don't distort the timing study.
const copilotHelpful = ref(null)
const itemShownAt = ref(null)

// Mobile-only fullscreen read mode for the content panel. The overlay renders
// the current item's messages/text read-only so a long conversation doesn't
// compete with the category buttons + feedback box in the stacked mobile layout.
// Desktop never shows the trigger (all triggers are isMobile-gated).
const fullscreenOpen = ref(false)

// Computed
const currentItem = computed(() => items.value[currentItemIndex.value] || null)

const messages = computed(() => {
  if (currentItemDetail.value?.messages) {
    return currentItemDetail.value.messages.map(m => ({
      ...m,
      // cleanSource: existing rows may carry raw enum text ("SourceType.HUMAN")
      // from older v1 imports — map to the friendly localized label.
      sender: cleanSource(m.sender) || 'Content'
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

// Unwrap the (possibly nested) config_json. api_v1 scenarios store the canonical
// shape `{type, config: {...}}` (sometimes nested again under eval_config),
// while manually/wizard-created scenarios pass the inner config directly.
const inner = computed(() =>
  props.config?.config || props.config?.eval_config?.config || props.config || {}
)

// Schema field is `labels`; legacy/wizard scenarios used `categories`.
const categories = computed(() => {
  return inner.value.labels || inner.value.categories || []
})

const evalConfig = computed(() => inner.value)

// Suggestions delivered per item by the session endpoint (server-side filtered;
// see session_service.py — hidden-control items simply have no suggestion).
const copilotSuggestions = computed(() =>
  currentItem.value?.copilot_suggestion?.suggestions || []
)

function suggestionCategory(suggestion) {
  return categories.value.find(c => c.id === suggestion.label_id) || null
}

function suggestionLabelName(suggestion) {
  const cat = suggestionCategory(suggestion)
  return cat ? categoryName(cat) : suggestion.label_id
}

function suggestionChipStyle(suggestion) {
  const color = suggestionCategory(suggestion)?.color || '#88c4c8'
  return { borderColor: color, color }
}

function confidenceVariant(confidence) {
  if (confidence === 'high') return 'success'
  if (confidence === 'low') return 'warning'
  return 'info'
}

// One-click adoption of a suggestion — still a deliberate action (the label is
// never pre-selected). Direct assignment instead of selectCategory() because
// the toggle semantics there would DESELECT when the suggestion matches the
// current choice. The auto-save watcher persists immediately.
function applySuggestion(suggestion) {
  if (!canEvaluate.value) return
  selectedCategory.value = suggestion.label_id
  isUnsure.value = false
}

function setHelpful(value) {
  copilotHelpful.value = value
  // Persist right away when a label already exists (log row gets the vote);
  // otherwise it rides along with the upcoming label save.
  if (canSubmit.value && !suppressAutoSave.value) persist()
}

// Display name per category. Schema items expose `label` as {de,en};
// legacy items expose `name` (string or {de,en}). Fall back to the id so a
// button is never blank. The submitted value stays `cat.id` (see selectCategory).
function categoryName(cat) {
  return localize(cat.label) || localize(cat.name) || cat.id || ''
}

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

// Status des AKTUELL angezeigten Items — NICHT das Aggregat evaluationStatus.
// Der Footer im EvaluationSession zeigt diesen Wert als Item-Status. Würde hier
// evaluationStatus (Gesamtfortschritt) emittiert, stünde bei einem frischen Item
// "In Bearbeitung" (weil ANDERE Items bereits erledigt sind) und bei einem schon
// erledigten Item beim Zurücknavigieren ebenfalls "In Bearbeitung" statt
// "Abgeschlossen". Labeling ist pro Item binär (Label gespeichert = evaluated),
// daher done | pending.
const currentItemStatus = computed(() => {
  const item = items.value[currentItemIndex.value]
  if (!item) return 'pending'
  return item.evaluated ? 'done' : 'pending'
})

// Emit den Status des aktuellen Items an den Parent (Footer-Status-Tag).
// immediate: schon beim ersten Render / nach jeder URL-Navigation korrekt.
watch(currentItemStatus, (newStatus) => {
  emit('status-change', newStatus)
}, { immediate: true })

// Emit saving/submitting changes to parent
watch(submitting, (isSaving) => {
  emit('saving-change', isSaving)
})

function selectCategory(categoryId) {
  if (!canEvaluate.value) return
  if (selectedCategory.value === categoryId) {
    selectedCategory.value = null
  } else {
    selectedCategory.value = categoryId
    isUnsure.value = false
  }
}

// "Unsure" and a concrete category are mutually exclusive buckets (the IRR
// analysis treats "unsure" as its own ordinal level). Checking unsure clears
// any picked category; selectCategory already clears unsure. Both writers
// mutate state synchronously so the auto-save watcher fires exactly once.
function onUnsureChange(val) {
  if (!canEvaluate.value) return
  isUnsure.value = val
  if (val) selectedCategory.value = null
}

async function loadItems() {
  loading.value = true
  try {
    const response = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = response.data.items || []

    // Navigate to initial item if specified
    if (props.initialItemId && items.value.length > 0) {
      const targetId = Number(props.initialItemId)
      const targetIndex = items.value.findIndex(item =>
        (item.thread_id || item.id || item.item_id) === targetId
      )
      if (targetIndex >= 0) {
        currentItemIndex.value = targetIndex
      }
    } else {
      // Default: find first incomplete item
      const firstIncomplete = items.value.findIndex(i => !i.evaluated)
      if (firstIncomplete >= 0) {
        currentItemIndex.value = firstIncomplete
      }
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

  // Gate the auto-save watchers: the reset below (and the restore further down)
  // mutate the bound inputs programmatically — without this guard navigating to
  // another item would immediately re-POST its empty/saved value.
  suppressAutoSave.value = true
  clearTimeout(feedbackTimer)

  // Reset state
  selectedCategory.value = null
  isUnsure.value = false
  feedback.value = ''
  currentItemDetail.value = null
  fullscreenOpen.value = false // don't keep stale content open across items
  copilotHelpful.value = null

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

  // Restore a previously-saved label so navigating back shows the prior choice.
  if (item.evaluation) {
    selectedCategory.value = item.evaluation.category_id || null
    feedback.value = item.evaluation.feedback || ''
    isUnsure.value = Boolean(item.evaluation.is_unsure)
  }

  // Re-enable auto-save only after the restore-driven reactivity has flushed,
  // so the watchers don't fire for our own programmatic restore.
  await nextTick()
  suppressAutoSave.value = false

  // Start the time-on-item clock only now: content + suggestion are visible,
  // restores are done — everything after this point is genuine decision time.
  itemShownAt.value = Date.now()
}

// Persist the current item's label. Shared by the auto-save watchers (embedded
// session flow) and the explicit "Save & Next" button (standalone flow, where
// the action bar is visible). Idempotent: the backend upserts by
// (user, item, scenario), so re-saving the same item just updates the row.
async function persist() {
  if (!canEvaluate.value || !canSubmit.value || !currentItem.value) return

  submitting.value = true

  try {
    await axios.post(
      `/api/evaluation/session/${props.scenarioId}/items/${currentItem.value.thread_id}/evaluate`,
      {
        function_type: 'labeling',
        category_id: selectedCategory.value,
        is_unsure: isUnsure.value,
        feedback: feedback.value,
        // Study logging (server no-ops when the scenario has no co-pilot):
        // only timing + helpful travel from the client; shown/suggestions/
        // acceptance are derived server-side against the suggestion cache.
        copilot: {
          time_on_item_ms: itemShownAt.value ? Date.now() - itemShownAt.value : null,
          helpful: copilotHelpful.value
        }
      }
    )

    items.value[currentItemIndex.value].evaluated = true
    items.value[currentItemIndex.value].evaluation = {
      category_id: selectedCategory.value,
      is_unsure: isUnsure.value,
      feedback: feedback.value
    }

    emit('item-completed', currentItem.value.thread_id)

    if (completedCount.value === items.value.length) {
      emit('all-completed')
    }
  } catch (err) {
    console.error('Failed to save labeling:', err)
  } finally {
    submitting.value = false
  }
}

// Explicit submit button (standalone / non-embedded layout): save, then advance.
async function handleSubmit() {
  if (!canSubmit.value || !currentItem.value) return
  await persist()
  if (hasNext.value) goNext()
}

// Auto-save the bucket choice the moment it changes. Skipped while
// loadCurrentItemDetail() is resetting/restoring inputs for a new item.
watch([selectedCategory, isUnsure], () => {
  if (suppressAutoSave.value || !canSubmit.value) return
  persist()
})

// Feedback is free text — debounce so we don't POST on every keystroke. Only
// persists once a bucket (category or unsure) is selected; feedback alone is
// not a valid evaluation (canSubmit guards this).
watch(feedback, () => {
  if (suppressAutoSave.value || !canSubmit.value) return
  clearTimeout(feedbackTimer)
  feedbackTimer = setTimeout(() => persist(), 800)
})

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

// Watch for initialItemId changes (e.g., when navigating between items via URL)
watch(() => props.initialItemId, (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetId = Number(newItemId)
    // Check if this item is already the current item
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      currentItemIndex.value = targetIndex
      loadCurrentItemDetail()
    }
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

/* Co-Pilot Suggestion Card */
.copilot-card {
  border: 1.5px dashed rgba(136, 196, 200, 0.7); /* accent — dashed = suggestion, not selection */
  border-radius: 16px 4px 16px 4px;
  padding: 12px 14px;
  background: rgba(136, 196, 200, 0.06);
}

.copilot-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.copilot-title {
  font-weight: 600;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.copilot-helpful-label {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-right: 2px;
}

.copilot-suggestion {
  padding: 8px 0;
}

.copilot-suggestion + .copilot-suggestion {
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.copilot-suggestion-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.copilot-label-chip {
  font-weight: 600;
  font-size: 0.9rem;
  padding: 2px 10px;
  border: 1.5px solid;
  border-radius: 6px 2px 6px 2px;
}

.copilot-rationale {
  margin: 6px 0 0;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.copilot-evidence {
  margin: 4px 0 0;
  font-size: 0.8rem;
  font-style: italic;
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.copilot-guardrail {
  display: flex;
  align-items: center;
  margin: 8px 0 0;
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Category Buttons */
.category-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

/* Small tablets (600–905px): isMobile is false here, so the panels would
   otherwise stay side-by-side at 50/50 and leave only ~290px per column.
   Stack them vertically and neutralise the resize handle (it still renders
   via v-if="!isMobile" but is meaningless in a vertical stack). 905px matches
   Vuetify's md breakpoint and the rest of the codebase's tablet cutoff. */
@media (max-width: 905px) {
  .content-panels {
    flex-direction: column;
  }

  /* Override the inline width set by leftPanelStyle()/rightPanelStyle() */
  .content-panels .panel {
    width: 100% !important;
    flex: none;
  }

  .content-panels .content-panel {
    max-height: 45vh;
    border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  }

  .content-panels .labeling-panel {
    flex: 1;
    min-height: 0;
  }

  /* Vertical stack → horizontal divider would be a dead row; hide it. */
  .content-panels .resize-divider {
    display: none;
  }
}

/* Mobile Styles (<600px, isMobile === true) */
.content-panels.is-mobile .panel {
  width: 100% !important;
}

.content-panels.is-mobile .content-panel {
  /* Reduced from 40vh: on phones the fullscreen read mode handles long
     content, so the inline preview can be smaller and leave room for the
     category buttons + unsure checkbox + feedback box. */
  max-height: 35vh;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

/* Floating fullscreen trigger for the embedded (hideNavigation) mobile case
   where the panel header — and its fullscreen button — is hidden. */
.content-fullscreen-fab {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  background: rgba(var(--v-theme-surface), 0.85);
  border-radius: 8px;
}

.content-panels.is-mobile .panel-content {
  position: relative; /* anchor for .content-fullscreen-fab */
}

/* Keep the auto-grow feedback textarea from pushing the action buttons out of
   reach on phones — cap it and let it scroll internally instead. */
.content-panels.is-mobile .feedback-section :deep(.v-textarea textarea) {
  max-height: 25vh;
  overflow-y: auto;
}

/* Fullscreen read overlay */
.content-fullscreen {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgb(var(--v-theme-surface));
}

.content-fullscreen-bar {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.1);
  background: rgba(var(--v-theme-surface-variant), 0.3);
  flex-shrink: 0;
}

.content-fullscreen-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.content-fullscreen-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.content-fullscreen-content .content-text {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 0.95rem;
}

.content-fullscreen-content .empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: rgba(var(--v-theme-on-surface), 0.5);
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
