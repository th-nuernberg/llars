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
            <!-- A save is in flight (every click persists now — see persist()).
                 Sits next to the status tag so the rater sees that their partial
                 answer is being stored, not swallowed. -->
            <span v-if="submitting" class="saving-indicator" data-test="saving-indicator">
              <v-progress-circular indeterminate size="12" width="2" />
              {{ $t('evaluation.labeling.status.saving') }}
            </span>
            <!-- Three states: done (label/unsure set) | in progress (some input,
                 no label yet) | pending (untouched). -->
            <LTag :variant="headerStatusVariant" size="small" :data-status="headerStatus" data-test="header-status">
              {{ headerStatusLabel }}
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
                  <p v-if="suggestion.answers" class="copilot-answers">
                    {{ $t('evaluation.labeling.copilot.answers') }}:
                    <span v-for="(val, qid) in suggestion.answers" :key="qid" class="copilot-answer-chip">{{ qid }} = {{ val }}</span>
                    <span v-if="suggestion.consistent === false" class="copilot-answers-warn">
                      ≠ {{ suggestion.derived_label_id }}
                    </span>
                  </p>
                  <p v-if="suggestion.rationale" class="copilot-rationale">{{ suggestion.rationale }}</p>
                  <p v-if="suggestion.evidence" class="copilot-evidence">„{{ suggestion.evidence }}“</p>
                </div>

                <p class="copilot-guardrail">
                  <LIcon size="13" class="mr-1">mdi-shield-alert-outline</LIcon>
                  {{ $t('evaluation.labeling.copilot.guardrail') }}
                </p>
              </div>

              <!-- Question-first labeling: the rater answers the decision
                   questions (e.g. VRM: topic / presumption / frame, each S or G)
                   and the label is DERIVED from the answer key. Nothing is
                   pre-selected. The direct label choice stays available below
                   (expandable) and sets the answers backwards via the mapping. -->
              <div v-if="questionsEnabled" class="questions-section" data-test="questions-section">
                <div
                  v-for="(q, qi) in questionItems"
                  :key="q.id"
                  class="question-card"
                  :data-test="`question-${q.id}`"
                >
                  <div class="question-head">
                    <span class="question-num">{{ qi + 1 }}</span>
                    <span class="question-title">{{ localize(q.title) }}</span>
                  </div>
                  <p class="question-text">{{ localize(q.text) }}</p>
                  <div class="question-options">
                    <button
                      v-for="opt in q.options"
                      :key="opt.id"
                      type="button"
                      class="question-option"
                      :class="{ active: answers[q.id] === opt.id }"
                      :disabled="!canEvaluate"
                      :data-test="`answer-${q.id}-${opt.id}`"
                      @click="answerQuestion(q.id, opt.id)"
                    >
                      <span class="question-option-id">{{ opt.id }}</span>
                      <span class="question-option-label">{{ localize(opt.label) }}</span>
                      <span v-if="localize(opt.hint)" class="question-option-hint">{{ localize(opt.hint) }}</span>
                    </button>
                  </div>
                  <!-- Optional lean slider: supplementary info only ("rather
                       S … rather G"), never changes the derived label. -->
                  <div v-if="questionsConfig?.sliders && q.options.length === 2" class="question-lean">
                    <span class="lean-end">{{ q.options[0].id }}</span>
                    <v-slider
                      :model-value="leans[q.id] ?? 50"
                      :min="0"
                      :max="100"
                      :step="5"
                      density="compact"
                      hide-details
                      :disabled="!canEvaluate"
                      @update:model-value="setLean(q.id, $event)"
                    />
                    <span class="lean-end">{{ q.options[1].id }}</span>
                  </div>
                </div>

                <div class="derived-label" data-test="derived-label">
                  <template v-if="derivedCategory">
                    <span class="derived-caption">{{ $t('evaluation.labeling.questions.derived') }}</span>
                    <span class="copilot-label-chip derived-chip" :style="{ borderColor: derivedCategory.color, color: derivedCategory.color }">
                      {{ categoryName(derivedCategory) }}
                    </span>
                  </template>
                  <span v-else-if="answersComplete" class="derived-missing">
                    {{ $t('evaluation.labeling.questions.noMapping', { key: answerKey }) }}
                  </span>
                  <span v-else class="derived-pending">{{ $t('evaluation.labeling.questions.pending') }}</span>
                </div>

                <button
                  v-if="questionsConfig?.direct_selection !== false"
                  type="button"
                  class="direct-toggle"
                  data-test="direct-toggle"
                  @click="directOpen = !directOpen"
                >
                  <LIcon size="16" class="mr-1">{{ directOpen ? 'mdi-chevron-up' : 'mdi-chevron-down' }}</LIcon>
                  {{ $t('evaluation.labeling.questions.direct') }}
                </button>
              </div>

              <!-- Category Buttons (direct choice). Always visible in classic
                   mode; in question mode only when expanded. -->
              <div v-show="!questionsEnabled || directOpen" class="category-buttons" data-test="category-buttons">
                <p v-if="questionsEnabled" class="direct-hint">{{ $t('evaluation.labeling.questions.directHint') }}</p>
                <LLabelButton
                  v-for="cat in categories"
                  :key="cat.id"
                  :category="cat"
                  :model-value="selectedCategory"
                  @select="selectCategory"
                />
              </div>

              <!-- Second choice ("Platz 2"): NOT a multi-label. Only offered
                   once a first label exists; stored alongside it so "both
                   readings defensible" cases are not thrown away. -->
              <div v-if="secondChoiceEnabled && selectedCategory" class="second-choice-section" data-test="second-choice">
                <p class="second-choice-title">
                  {{ $t('evaluation.labeling.secondChoice.title') }}
                  <span class="second-choice-hint">{{ $t('evaluation.labeling.secondChoice.hint') }}</span>
                </p>
                <div class="second-choice-chips">
                  <button
                    v-for="cat in secondChoiceCandidates"
                    :key="cat.id"
                    type="button"
                    class="second-choice-chip"
                    :class="{ active: secondChoice === cat.id }"
                    :style="{ borderColor: cat.color || '#c9c9c2', color: cat.color || 'inherit' }"
                    :disabled="!canEvaluate"
                    :data-test="`second-${cat.id}`"
                    @click="toggleSecondChoice(cat.id)"
                  >
                    {{ categoryName(cat) }}
                  </button>
                </div>
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
                @blur="flushPendingSaves"
              />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- A failed save used to vanish into console.error only; the rater kept
         labeling and lost work. Surface it. -->
    <v-snackbar v-model="saveError" color="error" :timeout="6000">
      {{ $t('evaluation.labeling.saveError') }}
    </v-snackbar>

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
 *
 * Persistence model (prod incident scenario 758): EVERY click persists — a
 * question answer, a lean slider, the second choice, a direct label, "unsure",
 * an applied co-pilot suggestion, feedback. The auto-save gate is `hasAnyInput`,
 * NOT `canSubmit`: a rater who answered two of three questions and navigated
 * away used to lose both answers, because the old gate required a complete
 * (derivable) label. The backend accepts `category_id: null` together with a
 * non-empty `answers_json` and answers with the authoritative status of the row
 * it wrote ('done' | 'in_progress' | 'pending', see
 * services/evaluation/labeling_types.labeling_row_status), which this component
 * mirrors into the item list and emits upwards ('item-progress'). `canSubmit`
 * still gates the explicit "Save & Next" button and 'item-completed'.
 *
 * Study invariant: nothing is ever pre-selected, and a partial save NEVER
 * writes a label (category_id stays null until the answers derive one).
 */
import { ref, computed, watch, onMounted, nextTick, onBeforeUnmount } from 'vue'
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

// 'item-progress' carries EVERY persisted state of the current item — including
// a partial one ({ itemId, status: 'in_progress' }) — so the session shell can
// show "In Bearbeitung" instead of "Ausstehend". 'item-completed' stays
// reserved for a finished label (it bumps the session's completed counter).
const emit = defineEmits(['item-completed', 'item-progress', 'all-completed', 'status-change', 'saving-change'])

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

// Question-first labeling state. `answers` = {questionId: optionId};
// `leans` = optional slider values (0..100) per question; `answerSource`
// records how the label came about ("questions" | "direct" | "copilot").
const answers = ref({})
const leans = ref({})
const answerSource = ref(null)
const directOpen = ref(false)
// Second choice ("Platz 2") — never equal to selectedCategory.
const secondChoice = ref(null)
const saveError = ref(false)

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
// Debounced writers: free-text feedback (800 ms) and the lean sliders (300 ms —
// a drag fires one update per step). Both are flushed before navigation and on
// unmount (flushPendingSaves) so nothing is lost mid-debounce.
let feedbackTimer = null
let leanTimer = null
// The POST currently on the wire. Navigation awaits it so an item switch can't
// race the response of a partial save (which would land on the wrong item).
let inFlightPersist = null
// Overlapping saves: `submitting` must only clear when the LAST one finished.
let openRequests = 0

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

// --- Question-first labeling (DecisionQuestionsConfig) --------------------
const questionsConfig = computed(() => inner.value.questions || null)
const questionItems = computed(() => (questionsConfig.value?.items || []).filter(q => q && q.id && Array.isArray(q.options)))
const questionsEnabled = computed(() =>
  !!questionsConfig.value && questionsConfig.value.enabled !== false && questionItems.value.length > 0
)
const secondChoiceEnabled = computed(() =>
  inner.value.second_choice === true || inner.value.secondChoice === true
)

const answersComplete = computed(() =>
  questionItems.value.length > 0 && questionItems.value.every(q => !!answers.value[q.id])
)
const answerKey = computed(() =>
  answersComplete.value ? questionItems.value.map(q => answers.value[q.id]).join('') : null
)
const derivedCategoryId = computed(() => {
  if (!answerKey.value) return null
  const mapping = questionsConfig.value?.mapping || {}
  return mapping[answerKey.value] ?? null
})
const derivedCategory = computed(() =>
  categories.value.find(c => c.id === derivedCategoryId.value) || null
)
const secondChoiceCandidates = computed(() =>
  categories.value.filter(c => c.id !== selectedCategory.value)
)

// Reverse mapping: the answers that produce `categoryId`, or null when the
// mapping is ambiguous (several keys) or absent (flag cards, X).
function answersForCategory(categoryId) {
  const mapping = questionsConfig.value?.mapping || {}
  const keys = Object.keys(mapping).filter(k => mapping[k] === categoryId)
  if (keys.length !== 1) return null
  let rest = keys[0]
  const out = {}
  for (const q of questionItems.value) {
    const opt = q.options.find(o => rest.startsWith(String(o.id)))
    if (!opt) return null
    out[q.id] = opt.id
    rest = rest.slice(String(opt.id).length)
  }
  return rest.length === 0 ? out : null
}

// Answering a question re-derives the label. Nothing is pre-selected: the
// label appears only once every question has an answer AND the key maps.
function answerQuestion(questionId, optionId) {
  if (!canEvaluate.value) return
  answers.value = { ...answers.value, [questionId]: optionId }
  answerSource.value = 'questions'
  const derived = derivedCategoryId.value
  if (derived !== selectedCategory.value) {
    selectedCategory.value = derived
    if (derived) isUnsure.value = false
  }
  if (secondChoice.value && secondChoice.value === derived) secondChoice.value = null
}

function setLean(questionId, value) {
  if (!canEvaluate.value) return
  leans.value = { ...leans.value, [questionId]: Number(value) }
}

function toggleSecondChoice(categoryId) {
  if (!canEvaluate.value || categoryId === selectedCategory.value) return
  secondChoice.value = secondChoice.value === categoryId ? null : categoryId
}

// The `answers_json` sent with every save. A PARTIAL answer set is valid on
// purpose: it is what makes "two of three questions answered" survive a reload
// (`derived` is then null — the label is never guessed). A lean alone also
// counts as input, so dragging a slider before answering still persists.
function answersPayload() {
  if (!questionsEnabled.value) return null
  const payload = { ...answers.value }
  const hasLeans = Object.keys(leans.value).length > 0
  if (Object.keys(payload).length === 0 && !hasLeans && !answerSource.value) return null
  if (hasLeans) payload.lean = { ...leans.value }
  payload.derived = derivedCategoryId.value
  payload.source = answerSource.value
  return payload
}

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
  if (questionsEnabled.value) {
    const fromModel = suggestion.answers && Object.keys(suggestion.answers).length
      ? { ...suggestion.answers }
      : answersForCategory(suggestion.label_id)
    if (fromModel) answers.value = fromModel
    answerSource.value = 'copilot'
  }
  if (secondChoice.value === suggestion.label_id) secondChoice.value = null
  selectedCategory.value = suggestion.label_id
  isUnsure.value = false
}

function setHelpful(value) {
  copilotHelpful.value = value
  // Persist right away when there is already something to attach the vote to
  // (a label, an "unsure" or question answers); otherwise it rides along with
  // the next save. A thumbs alone has no row to write into.
  if (hasPersistablePayload.value && !suppressAutoSave.value) schedulePersist()
}

// Display name per category. Schema items expose `label` as {de,en};
// legacy items expose `name` (string or {de,en}). Fall back to the id so a
// button is never blank. The submitted value stays `cat.id` (see selectCategory).
function categoryName(cat) {
  return localize(cat.label) || localize(cat.name) || cat.id || ''
}

const hasNext = computed(() => currentItemIndex.value < items.value.length - 1)
const hasPrev = computed(() => currentItemIndex.value > 0)

// A COMPLETE evaluation: a bucket was reached (derived or directly chosen) or
// the rater declared themselves unsure. Gates the explicit "Save & Next" button
// and the 'item-completed' emit — NOT the auto-save (see hasAnyInput).
const canSubmit = computed(() => {
  return selectedCategory.value !== null || isUnsure.value
})

// ANY rater input on this item. This is the auto-save gate: the moment a single
// question is answered (or a slider moved, a second choice picked, feedback
// typed) the state goes to the server, so navigating away can't discard it.
const hasAnyInput = computed(() =>
  selectedCategory.value !== null ||
  isUnsure.value ||
  secondChoice.value !== null ||
  Object.keys(answers.value).length > 0 ||
  Object.keys(leans.value).length > 0 ||
  (feedback.value || '').trim().length > 0
)

// Not everything the rater can touch is storable on its own: feedback (and, in
// classic mode without questions, anything else) has no row to attach to while
// there is neither a bucket nor an answers_json. Those keystrokes ride along
// with the next real save instead of POSTing an empty partial the backend would
// reject.
const hasPersistablePayload = computed(() =>
  selectedCategory.value !== null || isUnsure.value || answersPayload() !== null
)

// Header tag state. Derived from the CURRENT input (not the round-trip status)
// so it flips the instant the rater clicks; the "Speichern…" indicator next to
// it covers the POST itself.
const headerStatus = computed(() => {
  if (canSubmit.value) return 'done'
  return hasAnyInput.value ? 'in_progress' : 'pending'
})

const headerStatusVariant = computed(() => {
  if (headerStatus.value === 'done') return 'success'
  return headerStatus.value === 'in_progress' ? 'warning' : 'default'
})

const headerStatusLabel = computed(() => {
  if (headerStatus.value === 'done') return t('evaluation.labeling.selected')
  if (headerStatus.value === 'in_progress') return t('evaluation.labeling.status.inProgress')
  return t('evaluation.labeling.notSelected')
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
// "Abgeschlossen".
// Drei Zustände seit den Teilspeicherungen: done (Label gespeichert) |
// in_progress (Teilantworten gespeichert, noch kein Label) | pending.
const currentItemStatus = computed(() => {
  const item = items.value[currentItemIndex.value]
  if (!item) return 'pending'
  if (item.evaluated) return 'done'
  // The backend spells the partial state either way ('in_progress' from the
  // session service, 'Progressing' from the ProgressionStatus enum).
  const status = String(item.status || '').toLowerCase()
  return status === 'in_progress' || status === 'progressing' ? 'in_progress' : 'pending'
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
    if (questionsEnabled.value) answers.value = {}
  } else {
    if (questionsEnabled.value) {
      // Direct choice answers the questions backwards (when the mapping is
      // unambiguous); otherwise the answers are cleared so a stale triple
      // can't contradict the chosen label.
      answers.value = answersForCategory(categoryId) || {}
      answerSource.value = 'direct'
    }
    if (secondChoice.value === categoryId) secondChoice.value = null
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

// A prefill row without a category but WITH rater input = a partial save
// (question answers / leans / second choice / unsure / a comment).
function isPartialEvaluation(evaluation) {
  if (!evaluation) return false
  if (evaluation.category_id) return false
  const saved = evaluation.answers_json
  const hasAnswers = !!saved && typeof saved === 'object' && Object.keys(saved).length > 0
  return hasAnswers ||
    Boolean(evaluation.is_unsure) ||
    Boolean(evaluation.second_choice_id) ||
    Boolean((evaluation.feedback || '').trim())
}

async function loadItems() {
  loading.value = true
  try {
    const response = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    // Partially-answered items come back with `evaluated: false` and a prefill
    // row carrying answers but no category. Mark them so footer/status read
    // "In Bearbeitung" instead of "Ausstehend" after a reload — unless the
    // backend already said so itself.
    items.value = (response.data.items || []).map(item =>
      !item.status && !item.evaluated && isPartialEvaluation(item.evaluation)
        ? { ...item, status: 'in_progress' }
        : item
    )

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
  // Drop any debounce still pointing at the PREVIOUS item — the callers
  // (goNext/goPrev/initialItemId) flushed it already; a leftover timer would
  // fire against the freshly reset inputs.
  clearTimeout(feedbackTimer)
  feedbackTimer = null
  clearTimeout(leanTimer)
  leanTimer = null

  // Reset state
  selectedCategory.value = null
  isUnsure.value = false
  feedback.value = ''
  answers.value = {}
  leans.value = {}
  answerSource.value = null
  secondChoice.value = null
  directOpen.value = false
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

  // Restore a previously-saved state so navigating back shows the prior input.
  // This deliberately also covers a PARTIAL row (category_id null, answers
  // present): the two answers a rater gave before leaving must come back as
  // active buttons — without a label being (re-)selected.
  if (item.evaluation) {
    selectedCategory.value = item.evaluation.category_id || null
    feedback.value = item.evaluation.feedback || ''
    isUnsure.value = Boolean(item.evaluation.is_unsure)
    secondChoice.value = item.evaluation.second_choice_id || null
    const saved = item.evaluation.answers_json
    if (saved && typeof saved === 'object') {
      const restored = {}
      for (const q of questionItems.value) {
        if (saved[q.id]) restored[q.id] = saved[q.id]
      }
      answers.value = restored
      leans.value = saved.lean && typeof saved.lean === 'object' ? { ...saved.lean } : {}
      answerSource.value = saved.source || null
    }
  }

  // Re-enable auto-save only after the restore-driven reactivity has flushed,
  // so the watchers don't fire for our own programmatic restore.
  await nextTick()
  suppressAutoSave.value = false

  // Start the time-on-item clock only now: content + suggestion are visible,
  // restores are done — everything after this point is genuine decision time.
  itemShownAt.value = Date.now()
}

// Normalize the item status the backend reports for the row it just upserted
// ('done' | 'in_progress' | 'pending', see labeling_types.labeling_row_status).
// The server is authoritative — it knows whether the stored row carries a
// label. `complete` is only the fallback for older backends that answer with
// the former constant 'completed' or no status at all.
function normalizeSavedStatus(serverStatus, complete) {
  const value = String(serverStatus || '').toLowerCase()
  if (value === 'done' || value === 'completed') return 'done'
  if (value === 'in_progress' || value === 'progressing') return 'in_progress'
  if (value === 'pending' || value === 'not_started') return 'pending'
  return complete ? 'done' : 'in_progress'
}

// Persist the current item's state — complete OR partial. Shared by the
// auto-save watchers (embedded session flow) and the explicit "Save & Next"
// button (standalone flow, where the action bar is visible). Idempotent: the
// backend upserts by (user, item, scenario), so re-saving just updates the row.
//
// Nothing is guessed: `category_id` stays null until the answers derive a label
// (or the rater picks one directly), so a partial save can never invent one.
async function persist() {
  if (!canEvaluate.value || !currentItem.value) return
  // Feedback/leans without anything to attach them to would be an empty row.
  if (!hasPersistablePayload.value) return

  // Capture the target: a save started here must land on THIS item even if the
  // response arrives after the rater has navigated on.
  const index = currentItemIndex.value
  const item = items.value[index]
  const complete = canSubmit.value
  const payload = answersPayload()

  openRequests++
  submitting.value = true

  const request = axios.post(
    `/api/evaluation/session/${props.scenarioId}/items/${item.thread_id}/evaluate`,
    {
      function_type: 'labeling',
      category_id: selectedCategory.value,
      is_unsure: isUnsure.value,
      feedback: feedback.value,
      second_choice_id: secondChoice.value,
      answers_json: payload,
      // Study logging (server no-ops when the scenario has no co-pilot):
      // only timing + helpful travel from the client; shown/suggestions/
      // acceptance are derived server-side against the suggestion cache.
      copilot: {
        time_on_item_ms: itemShownAt.value ? Date.now() - itemShownAt.value : null,
        helpful: copilotHelpful.value
      }
    }
  )
  inFlightPersist = request

  try {
    const response = await request
    const status = normalizeSavedStatus(response?.data?.status, complete)

    item.status = status
    item.evaluated = status === 'done'
    item.evaluation = {
      category_id: selectedCategory.value,
      is_unsure: isUnsure.value,
      feedback: feedback.value,
      second_choice_id: secondChoice.value,
      answers_json: payload
    }

    // Every save reports progress; only a finished label counts as completed
    // (the session shell bumps its completed counter on 'item-completed').
    emit('item-progress', { itemId: item.thread_id, status })

    if (status === 'done') {
      emit('item-completed', item.thread_id)

      if (completedCount.value === items.value.length) {
        emit('all-completed')
      }
    }
  } catch (err) {
    console.error('Failed to save labeling:', err)
    saveError.value = true
  } finally {
    if (inFlightPersist === request) inFlightPersist = null
    openRequests = Math.max(0, openRequests - 1)
    if (openRequests === 0) submitting.value = false
  }
}

// Coalesce the watchers that fire together in one tick (answering a question
// changes `answers` AND `selectedCategory`) into a single POST. The queue flag
// is re-checked inside the microtask so flushPendingSaves() can claim the
// pending save synchronously without it running twice.
let persistQueued = false
function schedulePersist() {
  if (persistQueued) return
  persistQueued = true
  Promise.resolve().then(() => {
    if (!persistQueued) return
    persistQueued = false
    persist()
  })
}

// Flush anything still in a debounce (feedback 800 ms, leans 300 ms) or queued
// for the next microtask, then wait for the request on the wire. Navigating
// away used to clear the feedback timer and reset the inputs BEFORE the POST
// went out — the comment (and, since partial saves exist, half-answered
// questions) were silently lost. Called on blur, before goNext/goPrev and on
// unmount.
async function flushPendingSaves() {
  let pending = false

  if (feedbackTimer) {
    clearTimeout(feedbackTimer)
    feedbackTimer = null
    pending = true
  }
  if (leanTimer) {
    clearTimeout(leanTimer)
    leanTimer = null
    pending = true
  }
  if (persistQueued) {
    persistQueued = false
    pending = true
  }

  if (pending && !suppressAutoSave.value && hasAnyInput.value && currentItem.value) {
    await persist()
  }

  // A save started a tick earlier may still be on the wire.
  if (inFlightPersist) {
    try {
      await inFlightPersist
    } catch {
      // persist() already surfaced the failure via the saveError snackbar.
    }
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
  if (suppressAutoSave.value || !hasAnyInput.value) return
  schedulePersist()
})

// Second choice and question answers persist immediately too — the gate is
// `hasAnyInput`, not `canSubmit`: a single answered question is already worth
// storing (it comes back as a partial row, status "in Bearbeitung").
watch(secondChoice, () => {
  if (suppressAutoSave.value || !hasAnyInput.value) return
  schedulePersist()
})
watch(answers, () => {
  if (suppressAutoSave.value || !hasAnyInput.value) return
  schedulePersist()
}, { deep: true })

// Lean sliders emit one update per step while dragging — debounce 300 ms so a
// drag becomes a single POST. Flushed on navigation/blur/unmount.
watch(leans, () => {
  if (suppressAutoSave.value || !hasAnyInput.value) return
  clearTimeout(leanTimer)
  leanTimer = setTimeout(() => {
    leanTimer = null
    persist()
  }, 300)
}, { deep: true })

// Feedback is free text — debounce so we don't POST on every keystroke.
// hasPersistablePayload (checked inside persist) still holds a comment back
// while there is neither a bucket nor an answer to attach it to. Pending saves
// are flushed on blur and before navigation (flushPendingSaves).
watch(feedback, () => {
  if (suppressAutoSave.value || !hasAnyInput.value) return
  clearTimeout(feedbackTimer)
  feedbackTimer = setTimeout(() => {
    feedbackTimer = null
    persist()
  }, 800)
})

async function goNext() {
  if (!hasNext.value) return
  await flushPendingSaves()
  currentItemIndex.value++
  loadCurrentItemDetail()
}

async function goPrev() {
  if (!hasPrev.value) return
  await flushPendingSaves()
  currentItemIndex.value--
  loadCurrentItemDetail()
}

// Fire-and-forget: a lifecycle hook can't await, but the pending POST is still
// sent before the component goes away (the browser keeps the request alive).
onBeforeUnmount(() => {
  flushPendingSaves()
})

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

// Watch for initialItemId changes (e.g., when navigating between items via URL).
// This is the path the EMBEDDED session footer takes (its Next/Previous buttons
// push a route), so — like goNext/goPrev — it must flush a pending/in-flight
// partial save BEFORE the item switches, otherwise the response would land on
// the wrong item and the last click would be lost.
watch(() => props.initialItemId, async (newItemId) => {
  if (newItemId && items.value.length > 0) {
    const targetId = Number(newItemId)
    // Check if this item is already the current item
    const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
    if (currentId === targetId) return // Already on this item

    const targetIndex = items.value.findIndex(item =>
      (item.thread_id || item.id || item.item_id) === targetId
    )
    if (targetIndex >= 0 && targetIndex !== currentItemIndex.value) {
      await flushPendingSaves()
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

/* "Speichern…" while a (partial) save is on the wire — sits left of the status
   tag in the labeling panel header. */
.saving-indicator {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  margin-right: 8px;
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
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
/* ---- question-first labeling ---- */
.questions-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 14px;
}
.question-card {
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  border-radius: 8px;
  padding: 10px 12px;
  background: rgba(var(--v-theme-surface), 1);
}
.question-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.question-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.85);
  color: rgb(var(--v-theme-surface));
  font-size: 0.75rem;
  font-weight: 700;
}
.question-title {
  font-weight: 600;
  font-size: 0.85rem;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.question-text {
  margin: 0 0 8px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
}
.question-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}
.question-option {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 8px 10px;
  border: 1.5px solid rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 8px;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.question-option:hover:not(:disabled) {
  border-color: rgba(var(--v-theme-on-surface), 0.5);
}
.question-option.active {
  border-color: #88c4c8;
  background: rgba(136, 196, 200, 0.18);
}
.question-option:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.question-option-id {
  font-weight: 700;
  font-size: 0.9rem;
}
.question-option-label {
  font-size: 0.8rem;
}
.question-option-hint {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
.question-lean {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}
.lean-end {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
.derived-label {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 32px;
  font-size: 0.85rem;
}
.derived-caption {
  color: rgba(var(--v-theme-on-surface), 0.7);
}
.derived-chip {
  font-weight: 700;
}
.derived-missing {
  color: rgb(var(--v-theme-warning));
}
.derived-pending {
  color: rgba(var(--v-theme-on-surface), 0.55);
  font-style: italic;
}
.direct-toggle {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  padding: 4px 8px;
  border: none;
  background: transparent;
  color: rgba(var(--v-theme-on-surface), 0.7);
  font-size: 0.8rem;
  cursor: pointer;
  text-decoration: underline dotted;
}
.direct-hint {
  width: 100%;
  margin: 0 0 6px;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* ---- second choice ---- */
.second-choice-section {
  margin-top: 12px;
}
.second-choice-title {
  margin: 0 0 6px;
  font-size: 0.8rem;
  font-weight: 600;
}
.second-choice-hint {
  font-weight: 400;
  color: rgba(var(--v-theme-on-surface), 0.6);
}
.second-choice-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.second-choice-chip {
  padding: 3px 10px;
  border: 1.5px solid;
  border-radius: 999px;
  background: transparent;
  font-size: 0.78rem;
  cursor: pointer;
  opacity: 0.75;
}
.second-choice-chip.active {
  opacity: 1;
  font-weight: 700;
  box-shadow: 0 0 0 2px rgba(var(--v-theme-on-surface), 0.12);
}
.second-choice-chip:disabled {
  cursor: not-allowed;
  opacity: 0.4;
}
.copilot-answers {
  margin: 4px 0 0;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}
.copilot-answer-chip {
  display: inline-block;
  margin-left: 4px;
  padding: 0 6px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.25);
  border-radius: 4px;
  font-weight: 600;
}
.copilot-answers-warn {
  margin-left: 6px;
  color: rgb(var(--v-theme-warning));
  font-weight: 600;
}

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
