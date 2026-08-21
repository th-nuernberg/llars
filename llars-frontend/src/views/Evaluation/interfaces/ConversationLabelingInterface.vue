<template>
  <LEvaluationLayout
    :title="scenario?.name || $t('evaluation.conversationLabeling.pageTitle')"
    :subtitle="currentItem?.subject || ''"
    :back-label="$t('common.back')"
    :status="evaluationStatus"
    :saving="submitting"
    :can-go-prev="currentItemIndex > 0"
    :can-go-next="currentItemIndex < items.length - 1"
    :current-index="currentItemIndex"
    :total-items="items.length"
    :embedded="hideNavigation"
    @prev="goPrev"
    @next="goNext"
  >
    <div ref="containerRef" class="content-panels" :class="{ 'is-mobile': isMobile }">

      <!-- ===================== LEFT: conversation ===================== -->
      <div class="panel content-panel" :style="leftPanelStyle()">
        <div v-if="!hideNavigation" class="panel-header">
          <LIcon size="20" class="mr-2">mdi-forum-outline</LIcon>
          <span class="panel-title">{{ $t('evaluation.conversationLabeling.conversation') }}</span>
          <v-spacer />
          <LTag variant="info" size="small">{{ progressLabel }}</LTag>
        </div>

        <div ref="historyRef" class="panel-content">
          <div v-if="collapsedCount > 0" class="collapsed-hint">
            <LIcon size="14" class="mr-1">mdi-chevron-up</LIcon>
            {{ $t('evaluation.conversationLabeling.earlierMessages', { count: collapsedCount }) }}
          </div>

          <!-- The conversation unfolds turn by turn: finishing the last span
               of a counsellor message advances into the next one, which makes
               the client's reply appear. It is animated on purpose — the new
               turn is information the rater must actually read before deciding,
               so it should announce itself rather than silently appear. -->
          <TransitionGroup name="turn" tag="div" class="turn-list">
          <LMessage
            v-for="msg in visibleMessages"
            :key="msg.index"
            :sender="msg.role"
            :sender-type="msg.labelable ? 'advisor' : 'client'"
          >
            <!-- Context-only turn: nothing to decide, read it as prose. -->
            <template v-if="!msg.labelable">{{ msg.content }}</template>

            <!-- Labelable turn: rendered span by span so each carries its own
                 state and its own label chip. -->
            <template v-else>
              <span
                v-for="part in msg.parts"
                :key="part.key"
                :ref="(el) => registerSpanEl(part.spanId, el)"
                class="span"
                :class="spanClass(part)"
                @click="onSpanClick(part.spanId, $event)"
              >{{ part.text }}<span
                v-if="part.spanId && labelOf(part.spanId)"
                class="span-chip"
                :style="chipStyle(labelOf(part.spanId))"
              >{{ shortLabel(labelOf(part.spanId)) }}</span></span>
            </template>
          </LMessage>
          </TransitionGroup>

          <div v-if="futureMessagesHidden" class="hidden-hint">
            <LIcon size="14" class="mr-1">mdi-eye-off-outline</LIcon>
            {{ $t('evaluation.conversationLabeling.futureHidden') }}
          </div>
        </div>
      </div>

      <div
        v-if="!isMobile"
        class="resize-divider"
        :class="{ resizing: isResizing }"
        @mousedown="startResize"
      >
        <div class="resize-handle"></div>
      </div>

      <!-- ===================== RIGHT: decision ======================== -->
      <div class="panel labeling-panel" :style="rightPanelStyle()">
        <div v-if="!hideNavigation" class="panel-header">
          <LIcon size="20" class="mr-2">mdi-label-outline</LIcon>
          <span class="panel-title">{{ $t('evaluation.labeling.selectCategory') }}</span>
          <v-spacer />
          <LTag :variant="selectedCategory ? 'success' : 'default'" size="small">
            {{ selectedCategory ? $t('evaluation.labeling.selected') : $t('evaluation.labeling.notSelected') }}
          </LTag>
        </div>

        <div class="panel-content">
          <div v-if="currentSpan" class="labeling-section">

            <!-- The span under decision, quoted large. -->
            <div class="focus-block">
              <div class="focus-head">
                <LIcon size="16" class="mr-1" color="#4A6FA5">mdi-target</LIcon>
                <span class="focus-title">{{ $t('evaluation.conversationLabeling.currentSpan') }}</span>
                <v-spacer />
                <span class="span-counter">
                  {{ $t('evaluation.conversationLabeling.spanCounter', {
                    index: currentSpanOrdinal, total: allSpans.length
                  }) }}
                </span>
              </div>
              <blockquote
                class="focus-span"
                :class="{ 'is-splitting': splitMode }"
                @click="splitMode ? null : null"
              >{{ currentSpanText }}</blockquote>

            </div>

            <!-- Co-pilot suggestion. Marked as a suggestion and NEVER
                 pre-selected — accepting takes a deliberate click. -->
            <div v-if="copilotSuggestions.length" class="copilot-card">
              <div class="copilot-header">
                <LIcon size="16" class="mr-1" color="#88c4c8">mdi-robot-outline</LIcon>
                <span class="copilot-title">{{ $t('evaluation.labeling.copilot.title') }}</span>
                <v-spacer />
                <!-- Helpfulness vote, per span. Same control as classic
                     labeling; the log row it lands on is keyed by span. -->
                <span class="copilot-helpful-label">
                  {{ $t('evaluation.labeling.copilot.helpfulQuestion') }}
                </span>
                <LIconBtn
                  :icon="copilotHelpful === true ? 'mdi-thumb-up' : 'mdi-thumb-up-outline'"
                  variant="default"
                  size="x-small"
                  :disabled="!canEvaluate"
                  :tooltip="$t('evaluation.labeling.copilot.helpfulYes')"
                  @click="setHelpful(true)"
                />
                <LIconBtn
                  :icon="copilotHelpful === false ? 'mdi-thumb-down' : 'mdi-thumb-down-outline'"
                  variant="default"
                  size="x-small"
                  :disabled="!canEvaluate"
                  :tooltip="$t('evaluation.labeling.copilot.helpfulNo')"
                  @click="setHelpful(false)"
                />
              </div>
              <div
                v-for="(sug, idx) in copilotSuggestions"
                :key="sug.label_id"
                class="copilot-suggestion"
              >
                <div class="copilot-suggestion-head">
                  <LTag size="small" :variant="idx === 0 ? 'info' : 'default'">
                    {{ idx === 0
                      ? $t('evaluation.labeling.copilot.primary')
                      : $t('evaluation.labeling.copilot.secondary') }}
                  </LTag>
                  <span class="copilot-label-chip" :style="chipStyle(sug.label_id)">
                    {{ categoryName(sug.label_id) }}
                  </span>
                  <v-spacer />
                  <LBtn
                    size="small"
                    variant="secondary"
                    :disabled="!canEvaluate"
                    @click="applySuggestion(sug.label_id)"
                  >
                    {{ $t('evaluation.labeling.copilot.apply') }}
                  </LBtn>
                </div>
                <p v-if="sug.rationale" class="copilot-rationale">{{ sug.rationale }}</p>
                <p v-if="sug.evidence" class="copilot-evidence">„{{ sug.evidence }}"</p>
              </div>
              <p class="copilot-guardrail">
                <LIcon size="13" class="mr-1">mdi-shield-alert-outline</LIcon>
                {{ $t('evaluation.labeling.copilot.guardrail') }}
              </p>
            </div>

            <p class="category-instruction">
              {{ $t('evaluation.labeling.instruction') }}
            </p>

            <!-- Category buttons — the shared LLabelButton, so this screen and
                 classic labeling cannot drift apart again. -->
            <div class="category-buttons">
              <LLabelButton
                v-for="(cat, idx) in categories"
                :key="cat.id"
                :category="cat"
                :model-value="selectedCategory"
                :disabled="!canEvaluate"
                :hotkey="idx < 9 ? idx + 1 : null"
                @select="selectCategory"
              />
            </div>

            <div v-if="allowUnsure" class="unsure-option">
              <v-checkbox
                :model-value="isUnsure"
                :disabled="!canEvaluate"
                :label="$t('evaluation.labeling.unsure')"
                density="compact"
                hide-details
                @update:model-value="onUnsureChange"
              />
            </div>

            <!-- The unitizing is frozen at import time and a wrong boundary is
                 normally REPORTED via the flag card, not re-cut. These two are
                 the sanctioned exceptions, so they live down here as faint text
                 links rather than as controls in the decision flow. -->
            <div class="split-zone">
              <template v-if="!splitMode">
                <button
                  class="split-trigger"
                  :disabled="!canEvaluate"
                  @click="enterSplitMode"
                >
                  <LIcon size="15" class="mr-1">span-split</LIcon>
                  {{ $t('evaluation.conversationLabeling.split.trigger') }}
                </button>

                <!-- Always present, disabled until the marked spans can
                     actually become one unit. The rater marks them with
                     ctrl/cmd-click, so the control never has to guess which
                     neighbour was meant — the earlier version did, and that
                     is exactly what read as arbitrary. -->
                <button
                  class="merge-trigger"
                  :disabled="!canEvaluate || merging || !mergeSelectionValid"
                  @click="confirmMerge"
                >
                  <LIcon size="15" class="mr-1">span-merge</LIcon>
                  {{ $t('evaluation.conversationLabeling.merge.trigger') }}
                  <span v-if="mergeSelection.length" class="merge-count">
                    {{ mergeSelection.length }}
                  </span>
                </button>

                <span v-if="mergeHintKey" class="merge-hint">
                  {{ $t(`evaluation.conversationLabeling.merge.${mergeHintKey}`) }}
                </span>

                <!-- Two neighbours already carry the same label — the
                     block-merge signal. Marks them rather than merging, so the
                     same visible selection precedes every merge. -->
                <button
                  v-if="sameLabelMerge"
                  class="same-label-merge"
                  :disabled="!canEvaluate || merging"
                  @click="markSameLabelPair"
                >
                  <LIcon size="15" class="mr-1">span-merge</LIcon>
                  {{ $t('evaluation.conversationLabeling.merge.sameLabel') }}
                </button>
              </template>

              <div v-else class="split-panel">
                <p class="split-hint">{{ $t('evaluation.conversationLabeling.split.hint') }}</p>
                <div class="split-preview">
                  <span
                    v-for="(ch, i) in splitChars"
                    :key="i"
                    class="split-char"
                    :class="{ 'is-cut': i === splitAt }"
                    @click="splitAt = i"
                  >{{ ch }}</span>
                </div>
                <div v-if="splitAt !== null" class="split-halves">
                  <span class="split-half">„{{ splitLeftText }}"</span>
                  <LIcon size="14">mdi-plus</LIcon>
                  <span class="split-half">„{{ splitRightText }}"</span>
                </div>
                <div class="split-actions">
                  <LBtn variant="cancel" size="small" @click="cancelSplit">
                    {{ $t('common.cancel') }}
                  </LBtn>
                  <LBtn
                    variant="primary"
                    size="small"
                    :disabled="splitAt === null || splitting"
                    :loading="splitting"
                    @click="confirmSplit"
                  >
                    {{ $t('evaluation.conversationLabeling.split.confirm') }}
                  </LBtn>
                </div>
              </div>
            </div>

            <!-- Free-text note, same control as classic labeling but scoped to
                 the span rather than the item: with ~92 decisions per
                 conversation an item-level box could not say WHICH decision it
                 refers to. Opt-out via config, exactly like labeling. -->
            <div v-if="allowFeedback" class="feedback-section">
              <v-textarea
                v-model="feedback"
                :disabled="!canEvaluate"
                :label="$t('evaluation.labeling.feedback')"
                :placeholder="$t('evaluation.labeling.feedbackPlaceholder')"
                variant="outlined"
                density="compact"
                rows="2"
                auto-grow
                hide-details
              />
            </div>

            <!-- Auto-advance: on by default. At ~92 decisions per conversation
                 the click back into the text is the dominant cost. -->
            <div class="autoadvance-row">
              <v-switch
                v-model="autoAdvance"
                :label="$t('evaluation.conversationLabeling.autoAdvance')"
                density="compact"
                color="primary"
                hide-details
              />
              <span class="keyboard-hint">{{ $t('evaluation.conversationLabeling.keyboardHint') }}</span>
            </div>
          </div>

          <div v-else class="all-done">
            <LIcon size="56" color="#98d4bb">mdi-check-circle-outline</LIcon>
            <p>{{ $t('evaluation.conversationLabeling.allSpansDone') }}</p>
          </div>
        </div>
      </div>
    </div>
  </LEvaluationLayout>
</template>

<script setup>
/**
 * Conversation Labeling Interface (function_type 9).
 *
 * One item is a whole conversation; one DECISION is a single span inside it.
 * The rater walks the spans in reading order while the conversation history
 * stays on screen — the history is not decoration, it decides the label.
 *
 * Deliberately built as a close sibling of LabelingInterface: same two-panel
 * split, same panel headers, same category-button shape, same co-pilot card.
 * A rater moving between a classic and a conversation study should not have to
 * relearn anything; only the unit of decision differs.
 *
 * The conversation renders through LMessage (default slot), so the speech
 * bubbles are the real component rather than a lookalike — spans are injected
 * into the bubble body.
 *
 * Load-bearing behaviours, not cosmetics:
 *
 * 1. **Auto-advance, on by default.** After a decision the focus jumps to the
 *    next span. At ~92 decisions per conversation, having to click back into
 *    the text each time is the dominant cost of the whole task.
 * 2. **Already-decided spans show their label inline.** That is how a rater
 *    sees their own sequence and notices two identical labels in a row (the
 *    block-merge signal, and evidence on whether the segmentation is too fine).
 * 3. **Auto-save on selection.** Embedded in EvaluationSession the layout hides
 *    its action bar and with it any save button — an interface that waits for
 *    one persists nothing.
 *
 * Span boundaries are frozen at import time and stay that way by default: the
 * ordinary way to report a bad boundary is the dedicated label card, not a
 * re-cut. The one exception is the deliberately quiet "split" affordance below
 * the target span, for the case where a span plainly carries two distinct acts.
 * It is kept visually subordinate to the label buttons so that re-cutting stays
 * the exception it is meant to be.
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { usePanelResize } from '@/composables/usePanelResize'
import { useMobile } from '@/composables/useMobile'

const props = defineProps({
  scenarioId: { type: [Number, String], required: true },
  scenario: { type: Object, default: null },
  config: { type: Object, default: () => ({}) },
  initialItemId: { type: [Number, String], default: null },
  hideNavigation: { type: Boolean, default: false }
})

const emit = defineEmits(['item-completed', 'all-completed', 'status-change', 'saving-change'])

const { locale } = useI18n()

const { isMobile } = useMobile()
const { containerRef, leftPanelStyle, rightPanelStyle, startResize, isResizing } = usePanelResize({
  initialLeftPercent: 58, min: 40, max: 72,
  storageKey: 'llars-conversation-labeling-panel-width'
})

const items = ref([])
const currentItemIndex = ref(0)
const messages = ref([])
const submitting = ref(false)
const currentSpanId = ref(null)
const historyRef = ref(null)
const spanEls = new Map()
const votes = ref({})
const feedbacks = ref({})
const helpfuls = ref({})

const FEEDBACK_DEBOUNCE_MS = 800
let feedbackTimer = null
let pendingFeedbackSpan = null

// Auto-advance preference, persisted per browser. Default ON.
const AUTO_ADVANCE_KEY = 'llars:conversationLabeling:autoAdvance'
const autoAdvance = ref(true)
try {
  // Opt-out semantics: only the explicit string 'false' turns it off, so a
  // storage shim returning undefined keeps the useful default.
  if (localStorage.getItem(AUTO_ADVANCE_KEY) === 'false') autoAdvance.value = false
} catch (e) { /* private mode — keep the default */ }
watch(autoAdvance, (v) => {
  try { localStorage.setItem(AUTO_ADVANCE_KEY, String(v)) } catch (e) { /* non-fatal */ }
})

let suppressAutoSave = false
let spanShownAt = Date.now()

const canEvaluate = computed(() => props.scenario?.can_evaluate !== false)
const currentItem = computed(() => items.value[currentItemIndex.value] || null)

// --- config ---------------------------------------------------------------
// Same precedence the BACKEND uses (locate_inner_config): eval_config.config
// first. The classic interface checks config.config first; where both exist
// and disagree, the backend's view is authoritative.
const inner = computed(() => {
  const c = props.config || props.scenario?.config_json || {}
  return c?.eval_config?.config || c?.config || c || {}
})
const categories = computed(() => inner.value.labels || inner.value.categories || [])
const allowUnsure = computed(() => inner.value.allowUnsure ?? inner.value.allow_unsure ?? true)
const allowFeedback = computed(
  () => (inner.value.allowFeedback ?? inner.value.allow_feedback ?? true) !== false
)
const contextWindow = computed(() => {
  const v = inner.value.context_window ?? inner.value.contextWindow
  return Number.isFinite(Number(v)) ? Number(v) : 3
})
const futureSpans = computed(() => inner.value.future_spans ?? inner.value.futureSpans ?? 'dimmed')
const noFutureMessages = computed(
  () => (inner.value.no_future_messages ?? inner.value.noFutureMessages ?? true) !== false
)

// --- span inventory -------------------------------------------------------
const allSpans = computed(() => {
  const block = currentItem.value?.metadata_json?.conversation_labeling
  return Array.isArray(block?.spans) ? block.spans : []
})
const labelableIndexes = computed(() => {
  const block = currentItem.value?.metadata_json?.conversation_labeling
  return Array.isArray(block?.labelable_messages) ? block.labelable_messages : []
})
const spanById = computed(() => Object.fromEntries(allSpans.value.map(s => [s.span_id, s])))
const currentSpan = computed(() => spanById.value[currentSpanId.value] || null)
const currentSpanOrdinal = computed(() => {
  const i = allSpans.value.findIndex(s => s.span_id === currentSpanId.value)
  return i < 0 ? 0 : i + 1
})

// Messages are ordered by DB id (= import order). Sorting by timestamp would
// be wrong: the importer stamps "now" when the payload carries none, so ties
// are possible — and reading order is exactly what this type depends on.
const orderedMessages = computed(() => [...messages.value].sort((a, b) => (a.id ?? 0) - (b.id ?? 0)))
const messageByIndex = computed(() =>
  Object.fromEntries(orderedMessages.value.map((m, i) => [i, m]))
)

const currentSpanText = computed(() => {
  const s = currentSpan.value
  if (!s) return ''
  const msg = messageByIndex.value[s.message_index]
  return msg ? String(msg.content || '').slice(s.start, s.end) : ''
})

// --- votes ----------------------------------------------------------------
const selectedCategory = computed(() => votes.value[currentSpanId.value]?.category_id ?? null)
const isUnsure = computed(() => votes.value[currentSpanId.value]?.is_unsure === true)
const labelOf = (spanId) => votes.value[spanId]?.category_id || null
const isDecided = (spanId) => {
  const v = votes.value[spanId]
  return !!v && (v.category_id != null || v.is_unsure === true)
}
const decidedCount = computed(() => allSpans.value.filter(s => isDecided(s.span_id)).length)
const progressLabel = computed(() => `${decidedCount.value}/${allSpans.value.length}`)
const evaluationStatus = computed(() => {
  if (!allSpans.value.length) return 'pending'
  if (decidedCount.value >= allSpans.value.length) return 'done'
  return decidedCount.value > 0 ? 'in_progress' : 'pending'
})

// --- co-pilot -------------------------------------------------------------
// Keyed per span; an absent entry is indistinguishable from "no suggestion"
// (that is the point — the hidden control subset must stay covert).
const copilotSuggestions = computed(() => {
  const bySpan = currentItem.value?.copilot_suggestion?.spans
  if (bySpan && currentSpanId.value) return bySpan[currentSpanId.value]?.suggestions || []
  return []
})

// --- message rendering ----------------------------------------------------
const currentMessageIndex = computed(() => currentSpan.value?.message_index ?? 0)
const collapsedCount = computed(() =>
  contextWindow.value < 0 ? 0 : Math.max(0, currentMessageIndex.value - contextWindow.value)
)
const futureMessagesHidden = computed(
  () => noFutureMessages.value && currentMessageIndex.value < orderedMessages.value.length - 1
)

const visibleMessages = computed(() => {
  const out = []
  const msgs = orderedMessages.value
  const cur = currentMessageIndex.value
  const first = contextWindow.value < 0 ? 0 : Math.max(0, cur - contextWindow.value)
  const last = noFutureMessages.value ? cur : msgs.length - 1

  for (let i = first; i <= Math.min(last, msgs.length - 1); i++) {
    const m = msgs[i]
    if (!m) continue
    const labelable = labelableIndexes.value.includes(i)
    out.push({
      index: i,
      role: m.sender || m.role || '',
      content: m.content || '',
      labelable,
      parts: labelable ? splitIntoParts(m.content || '', i) : []
    })
  }
  return out
})

/**
 * Cut a message into span parts plus the gaps between them, so the bubble
 * still reads as continuous prose rather than a row of chips.
 */
function splitIntoParts(text, messageIndex) {
  const spans = allSpans.value
    .filter(s => s.message_index === messageIndex)
    .sort((a, b) => a.start - b.start)

  const parts = []
  let cursor = 0
  for (const s of spans) {
    if (s.start > cursor) {
      parts.push({ key: `gap-${messageIndex}-${cursor}`, text: text.slice(cursor, s.start), spanId: null })
    }
    parts.push({ key: s.span_id, text: text.slice(s.start, s.end), spanId: s.span_id })
    cursor = s.end
  }
  if (cursor < text.length) {
    parts.push({ key: `gap-${messageIndex}-end`, text: text.slice(cursor), spanId: null })
  }
  return parts
}

function spanClass(part) {
  if (!part.spanId) return 'span-gap'
  const isCurrent = part.spanId === currentSpanId.value
  const decided = isDecided(part.spanId)
  const curIdx = allSpans.value.findIndex(s => s.span_id === currentSpanId.value)
  const thisIdx = allSpans.value.findIndex(s => s.span_id === part.spanId)
  const isFuture = !decided && !isCurrent && thisIdx > curIdx

  return {
    'span-current': isCurrent,
    'span-marked': mergeSelection.value.includes(part.spanId),
    'span-done': decided && !isCurrent,
    'span-future': isFuture && futureSpans.value === 'dimmed',
    'span-hidden': isFuture && futureSpans.value === 'hidden'
  }
}

// --- helpers --------------------------------------------------------------
// Mirrors LabelingInterface.localize: the ACTIVE locale wins, with de/en only
// as fallbacks. Without locale.value an English rater reads German category
// names and definitions — the label text comes from scenario config, not from
// the i18n catalogue, so nothing else would catch it.
function localize(v) {
  if (!v) return ''
  if (typeof v === 'string') return v
  return v[locale.value] || v.de || v.en || ''
}
function categoryName(id) {
  const c = categories.value.find(x => x.id === id)
  return c ? (localize(c.label) || localize(c.name) || c.id) : id
}
function shortLabel(id) {
  const name = categoryName(id)
  return name.length <= 3 ? name : name.slice(0, 1).toUpperCase()
}
function categoryColor(id) {
  return categories.value.find(x => x.id === id)?.color || '#b0ca97'
}
function chipStyle(id) {
  return { backgroundColor: categoryColor(id), color: '#22301c' }
}
function registerSpanEl(spanId, el) {
  if (!spanId) return
  if (el) spanEls.set(spanId, el)
  else spanEls.delete(spanId)
}

// --- navigation -----------------------------------------------------------
function focusSpan(spanId) {
  if (!spanId) return
  currentSpanId.value = spanId
  nextTick(scrollCurrentIntoView)
}
function scrollCurrentIntoView() {
  const el = spanEls.get(currentSpanId.value)
  if (el?.scrollIntoView) el.scrollIntoView({ block: 'center', behavior: 'smooth' })
}
function firstUndecidedSpanId() {
  return allSpans.value.find(s => !isDecided(s.span_id))?.span_id || null
}
function goToNextSpan() {
  const idx = allSpans.value.findIndex(s => s.span_id === currentSpanId.value)
  const next = allSpans.value[idx + 1]
  if (next) { focusSpan(next.span_id); return true }
  currentSpanId.value = null
  emit('item-completed', currentItem.value?.thread_id ?? currentItem.value?.id)
  return false
}
function goToPrevSpan() {
  const idx = allSpans.value.findIndex(s => s.span_id === currentSpanId.value)
  const prev = allSpans.value[idx - 1]
  if (prev) focusSpan(prev.span_id)
}
function goNext() {
  if (currentItemIndex.value < items.value.length - 1) currentItemIndex.value += 1
}
function goPrev() {
  if (currentItemIndex.value > 0) currentItemIndex.value -= 1
}

// --- selection ------------------------------------------------------------
function setVote(spanId, vote) {
  votes.value = { ...votes.value, [spanId]: vote }
}

// --- per-span note and co-pilot helpfulness --------------------------------
// Both are kept OUTSIDE `votes`: the auto-save watcher fires on every change to
// `votes`, which is right for a category click but would mean one POST per
// keystroke for a free-text note.

const feedback = computed({
  get: () => feedbacks.value[currentSpanId.value] ?? '',
  set: (value) => {
    const sid = currentSpanId.value
    if (!sid) return
    feedbacks.value = { ...feedbacks.value, [sid]: value }
    scheduleFeedbackSave(sid)
  }
})

const copilotHelpful = computed(() => helpfuls.value[currentSpanId.value] ?? null)

/** Toggle the thumbs; clicking the active one clears the vote again. */
function setHelpful(value) {
  const sid = currentSpanId.value
  if (!canEvaluate.value || !sid) return
  helpfuls.value = { ...helpfuls.value, [sid]: helpfuls.value[sid] === value ? null : value }
  // Only persist once a label exists — the log row is created by the label
  // save. Otherwise the vote rides along with the upcoming save.
  if (votes.value[sid]) persistSpan(sid)
}

function scheduleFeedbackSave(spanId) {
  pendingFeedbackSpan = spanId
  clearTimeout(feedbackTimer)
  feedbackTimer = setTimeout(() => {
    feedbackTimer = null
    flushFeedbackSave()
  }, FEEDBACK_DEBOUNCE_MS)
}

/**
 * Write a pending note immediately. Called on span change and on unmount:
 * leaving a span with an unsaved note in flight would silently drop it, and at
 * ~92 spans a rater switches spans constantly.
 */
function flushFeedbackSave() {
  clearTimeout(feedbackTimer)
  feedbackTimer = null
  const sid = pendingFeedbackSpan
  pendingFeedbackSpan = null
  if (sid && votes.value[sid]) persistSpan(sid)
}

function selectCategory(id) {
  if (!canEvaluate.value || !currentSpanId.value) return
  const cur = votes.value[currentSpanId.value] || {}
  // Clicking the selected category again clears it — same affordance as the
  // classic interface. Auto-advance must NOT fire on a clear.
  const next = cur.category_id === id ? null : id
  setVote(currentSpanId.value, { category_id: next, is_unsure: false })
  if (next != null) maybeAdvance()
}

function onUnsureChange(value) {
  if (!canEvaluate.value || !currentSpanId.value) return
  setVote(currentSpanId.value, { category_id: null, is_unsure: !!value })
  if (value) maybeAdvance()
}

function applySuggestion(labelId) {
  if (!canEvaluate.value || !currentSpanId.value) return
  // Direct assignment, not selectCategory(): a suggestion must never toggle
  // off an identical existing choice.
  setVote(currentSpanId.value, { category_id: labelId, is_unsure: false })
  maybeAdvance()
}

/**
 * Advance after a decision, once the save for THIS span has been dispatched.
 * The tick lets the auto-save watcher observe the change first, so the request
 * still carries the span it belongs to.
 */
function maybeAdvance() {
  if (!autoAdvance.value) return
  nextTick(() => goToNextSpan())
}

// --- span splitting (hidden feature) --------------------------------------
// Kept deliberately out of the primary flow: re-segmenting mid-study makes
// units incomparable between raters, so the normal answer to a bad boundary is
// the ⚑ label card. This is the sanctioned exception, two steps deep.
const splitMode = ref(false)
const splitAt = ref(null)
const splitting = ref(false)
const merging = ref(false)

// Characters of the focus span, so the cut point can be picked visually. A
// numeric offset field would be unusable: the rater thinks in words.
const splitChars = computed(() => Array.from(currentSpanText.value))
const splitLeftText = computed(() => currentSpanText.value.slice(0, splitAt.value ?? 0))
const splitRightText = computed(() => currentSpanText.value.slice(splitAt.value ?? 0))

function enterSplitMode() {
  splitMode.value = true
  splitAt.value = null
}
function cancelSplit() {
  splitMode.value = false
  splitAt.value = null
}

async function confirmSplit() {
  const span = currentSpan.value
  const item = currentItem.value
  if (!span || !item || splitAt.value === null) return
  // The endpoint expects an offset in MESSAGE coordinates — the same system
  // start/end use — so translate from the in-span index here, on the side that
  // already knows both.
  const offset = Number(span.start) + Number(splitAt.value)

  splitting.value = true
  try {
    const itemId = item.thread_id ?? item.id
    const { data } = await axios.post(
      `/api/evaluation/session/${props.scenarioId}/items/${itemId}/spans/split`,
      { span_id: span.span_id, offset }
    )
    // Rewrite the local span index from the server's answer rather than
    // patching it client-side: the server renumbered span_index and dropped the
    // now-meaningless vote, and guessing at that would drift.
    const block = { ...(item.metadata_json?.conversation_labeling || {}), spans: data.spans }
    items.value[currentItemIndex.value] = {
      ...item,
      metadata_json: { ...(item.metadata_json || {}), conversation_labeling: block }
    }
    // The original span's vote is gone server-side; mirror that locally.
    // The split span no longer exists; its vote was deleted server-side for
    // every rater, so drop the local note and helpfulness vote with it.
    const nextVotes = { ...votes.value }
    const nextFeedbacks = { ...feedbacks.value }
    const nextHelpfuls = { ...helpfuls.value }
    delete nextVotes[span.span_id]
    delete nextFeedbacks[span.span_id]
    delete nextHelpfuls[span.span_id]
    suppressAutoSave = true
    votes.value = nextVotes
    feedbacks.value = nextFeedbacks
    helpfuls.value = nextHelpfuls
    await nextTick()
    suppressAutoSave = false

    cancelSplit()
    // Land on the first half so the rater immediately judges what they cut.
    focusSpan(data.new_span_ids?.[0] || null)
    emit('status-change', evaluationStatus.value)
  } catch (e) {
    console.error('[ConversationLabeling] split failed', e)
  } finally {
    splitting.value = false
  }
}

/**
 * Spans the rater has explicitly marked for merging (ctrl/cmd-click).
 *
 * The previous version guessed the partner — it merged with the following span,
 * or the preceding one if there was none. That reads as arbitrary, because it
 * is: nothing on screen said which neighbour was meant. Now the rater marks
 * exactly what should become one unit, and the control stays disabled until
 * that selection is actually mergeable.
 */
const mergeSelection = ref([])

/**
 * Whether the marked spans can become one unit.
 *
 * Same three conditions the server enforces: at least two, an unbroken run in
 * reading order, one message, no gaps. Checked here as well so the button can
 * show its state instead of failing on click.
 */
const mergeSelectionValid = computed(() => {
  const ids = mergeSelection.value
  if (ids.length < 2) return false

  const list = allSpans.value
  const positions = ids
    .map(id => list.findIndex(s => s.span_id === id))
    .sort((a, b) => a - b)
  if (positions.some(p => p < 0)) return false

  const [lo, hi] = [positions[0], positions[positions.length - 1]]
  if (hi - lo + 1 !== positions.length) return false          // hole in the run

  const run = list.slice(lo, hi + 1)
  if (run.some(s => s.message_index !== run[0].message_index)) return false
  for (let i = 1; i < run.length; i += 1) {
    if (!onlyWhitespaceBetween(run[i - 1], run[i])) return false
  }
  return true
})

/**
 * Whether nothing but whitespace sits between two spans.
 *
 * Real segmentations leave the separator out of every span — sentence spans are
 * typically one space apart — so demanding exact contiguity would grey the merge
 * button out on every genuine conversation. Absorbing a space is harmless;
 * absorbing words is not, because nobody decided about them. Mirrors the
 * server's rule so the button state matches what the endpoint will accept.
 */
function onlyWhitespaceBetween(left, right) {
  const gapStart = Number(left.end)
  const gapEnd = Number(right.start)
  if (gapStart === gapEnd) return true
  if (gapEnd < gapStart) return false
  const text = messages.value?.[left.message_index]?.content
  if (typeof text !== 'string') return false
  return text.slice(gapStart, gapEnd).trim() === ''
}

/** Why the button is disabled, for the hint next to it. */
const mergeHintKey = computed(() => {
  if (mergeSelection.value.length < 2) return 'markMore'
  return mergeSelectionValid.value ? null : 'notJoinable'
})

/**
 * Click on a span: ctrl/cmd marks it for merging, a plain click focuses it.
 *
 * Marking deliberately does NOT move the focus — otherwise picking the second
 * span would drag the rater away from what they are deciding.
 */
function onSpanClick(spanId, event) {
  if (!spanId) return
  if (event?.metaKey || event?.ctrlKey) {
    event.preventDefault()
    toggleMergeMark(spanId)
    return
  }
  // A plain click is a normal navigation, so an unrelated selection would only
  // be confusing baggage.
  mergeSelection.value = []
  focusSpan(spanId)
}

function toggleMergeMark(spanId) {
  const marked = mergeSelection.value
  mergeSelection.value = marked.includes(spanId)
    ? marked.filter(id => id !== spanId)
    : [...marked, spanId]
}

/**
 * The pair to pre-mark for "I labeled both the same, so they belong together".
 *
 * Two moments count, and only covering the first would make it unreachable in
 * practice: auto-advance moves on the instant the second half is decided, so
 * the rater is never standing on the pair they just completed.
 *
 *   a) standing ON one of them — offer it with its neighbour
 *   b) standing on the NEXT, still undecided span — offer the pair behind
 *
 * Clicking it MARKS the two rather than merging them, so the same visible
 * selection precedes every merge. Doing it automatically would be wrong, not
 * merely bold: the segmentation is shared by every rater, so acting on one
 * rater's labels would change the units the others are working on and delete
 * their votes on both halves.
 */
const sameLabelMerge = computed(() => {
  const list = allSpans.value
  const idx = list.findIndex(s => s.span_id === currentSpanId.value)
  if (idx < 0) return null

  const labelOfSpan = (s) => (s ? votes.value[s.span_id]?.category_id : null)
  const joinable = (left, right) =>
    !!left && !!right &&
    left.message_index === right.message_index &&
    onlyWhitespaceBetween(left, right)

  const current = list[idx]
  if (labelOfSpan(current)) {
    for (const neighbour of [list[idx - 1], list[idx + 1]]) {
      const pair = neighbour && (list.indexOf(neighbour) < idx
        ? joinable(neighbour, current)
        : joinable(current, neighbour))
      if (pair && labelOfSpan(neighbour) === labelOfSpan(current)) {
        return { a: current.span_id, b: neighbour.span_id }
      }
    }
    return null
  }

  // Undecided: look at the two spans just finished.
  const prev = list[idx - 1]
  const prevPrev = list[idx - 2]
  if (joinable(prevPrev, prev) && labelOfSpan(prev) && labelOfSpan(prevPrev) === labelOfSpan(prev)) {
    return { a: prevPrev.span_id, b: prev.span_id }
  }
  return null
})

function markSameLabelPair() {
  const pair = sameLabelMerge.value
  if (!pair) return
  mergeSelection.value = [pair.a, pair.b]
}


/**
 * Merge the spans the rater marked into one.
 *
 * Every vote on them disappears — server-side for every rater. That is
 * deliberate and symmetrical with splitting: decisions about the parts are not
 * a decision about the whole, and keeping one would put an opinion in someone's
 * mouth. The rater lands on the merged span and decides once.
 */
async function confirmMerge() {
  const item = currentItem.value
  const ids = [...mergeSelection.value]
  if (!item || merging.value || !mergeSelectionValid.value) return

  merging.value = true
  try {
    const itemId = item.thread_id ?? item.id
    const { data } = await axios.post(
      `/api/evaluation/session/${props.scenarioId}/items/${itemId}/spans/merge`,
      { span_ids: ids }
    )
    const block = { ...(item.metadata_json?.conversation_labeling || {}), spans: data.spans }
    items.value[currentItemIndex.value] = {
      ...item,
      metadata_json: { ...(item.metadata_json || {}), conversation_labeling: block }
    }

    const nextVotes = { ...votes.value }
    const nextFeedbacks = { ...feedbacks.value }
    const nextHelpfuls = { ...helpfuls.value }
    for (const gone of ids) {
      delete nextVotes[gone]
      delete nextFeedbacks[gone]
      delete nextHelpfuls[gone]
    }
    suppressAutoSave = true
    votes.value = nextVotes
    feedbacks.value = nextFeedbacks
    helpfuls.value = nextHelpfuls
    await nextTick()
    suppressAutoSave = false

    mergeSelection.value = []
    focusSpan(data.new_span_id || null)
    emit('status-change', evaluationStatus.value)
  } catch (e) {
    console.error('[ConversationLabeling] merge failed', e)
  } finally {
    merging.value = false
  }
}

// --- persistence ----------------------------------------------------------
async function persistSpan(spanId) {
  const item = currentItem.value
  const vote = votes.value[spanId]
  if (!item || !vote) return
  if (vote.category_id == null && !vote.is_unsure) return

  submitting.value = true
  emit('saving-change', true)
  try {
    const itemId = item.thread_id ?? item.id
    await axios.post(
      `/api/evaluation/session/${props.scenarioId}/items/${itemId}/evaluate`,
      {
        function_type: 'conversation_labeling',
        span_id: spanId,
        category_id: vote.category_id,
        is_unsure: !!vote.is_unsure,
        feedback: feedbacks.value[spanId] ?? '',
        // time_on_item_ms is first-write-only server side, so a revisit cannot
        // overwrite the original measurement. `helpful` stays updatable — it is
        // an opinion about the suggestion, not a measurement.
        copilot: {
          time_on_item_ms: Date.now() - spanShownAt,
          helpful: helpfuls.value[spanId] ?? null
        }
      }
    )
    emit('status-change', evaluationStatus.value)
    if (evaluationStatus.value === 'done') emit('item-completed', itemId)
  } catch (e) {
    console.error('[ConversationLabeling] save failed', e)
  } finally {
    submitting.value = false
    emit('saving-change', false)
  }
}

// Auto-save on every decision change. Mandatory: embedded mode has no save
// button at all.
watch(votes, (nv, ov) => {
  if (suppressAutoSave) return
  for (const spanId of Object.keys(nv)) {
    if (JSON.stringify(nv[spanId]) !== JSON.stringify(ov?.[spanId])) persistSpan(spanId)
  }
}, { deep: true })

watch(currentSpanId, () => {
  // Write any note still sitting in the debounce before the span changes —
  // otherwise it would be saved against the span the rater just left.
  flushFeedbackSave()
  spanShownAt = Date.now()
  // Close the split panel on navigation: an open cut point belongs to the span
  // it was opened on, never to the next one.
  cancelSplit()
})

// --- keyboard -------------------------------------------------------------
function onKeydown(e) {
  if (!currentSpanId.value || !canEvaluate.value) return
  const tag = (e.target?.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || e.target?.isContentEditable) return

  if (e.key >= '1' && e.key <= '9') {
    const cat = categories.value[Number(e.key) - 1]
    if (cat) { e.preventDefault(); selectCategory(cat.id) }
    return
  }
  if (e.key === 'Enter') {
    e.preventDefault()
    // Only advance on a decided span — Enter on an untouched one would skip it
    // and leave a silent hole in the sequence.
    if (isDecided(currentSpanId.value)) goToNextSpan()
    return
  }
  if (e.key === 'Backspace') {
    e.preventDefault()
    goToPrevSpan()
  }
}

// --- loading --------------------------------------------------------------
async function loadItems() {
  try {
    const { data } = await axios.get(`/api/evaluation/session/${props.scenarioId}`)
    items.value = data.items || []
    if (props.initialItemId != null) {
      const i = items.value.findIndex(
        it => String(it.thread_id ?? it.id) === String(props.initialItemId)
      )
      if (i >= 0) currentItemIndex.value = i
    }
    await loadCurrentItem()
  } catch (e) {
    console.error('[ConversationLabeling] loading items failed', e)
  }
}

async function loadCurrentItem() {
  const item = currentItem.value
  if (!item) return
  suppressAutoSave = true
  spanEls.clear()
  messages.value = []

  const saved = item.evaluation?.spans || {}
  votes.value = Object.fromEntries(
    Object.entries(saved).map(([sid, v]) => [sid, {
      category_id: v.category_id ?? null,
      is_unsure: v.is_unsure === true
    }])
  )
  feedbacks.value = Object.fromEntries(
    Object.entries(saved).map(([sid, v]) => [sid, v.feedback || ''])
  )
  // Helpfulness lives in the co-pilot log rather than the evaluation row and is
  // not read back — same as classic labeling. It starts blank per conversation.
  helpfuls.value = {}

  try {
    const itemId = item.thread_id ?? item.id
    const { data } = await axios.get(`/api/scenarios/${props.scenarioId}/threads/${itemId}`)
    messages.value = data?.thread?.messages || []
  } catch (e) {
    console.error('[ConversationLabeling] loading conversation failed', e)
  }

  // Resume at the first undecided span — at ~20 minutes per conversation this
  // is a requirement, not a convenience.
  currentSpanId.value = firstUndecidedSpanId() || allSpans.value[0]?.span_id || null

  await nextTick()
  suppressAutoSave = false
  spanShownAt = Date.now()
  scrollCurrentIntoView()
  emit('status-change', evaluationStatus.value)
}

watch(currentItemIndex, loadCurrentItem)

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  loadItems()
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  // Leaving the interface with a note still in the debounce would drop it.
  flushFeedbackSave()
})
</script>

<style scoped>
/* Layout mirrors LabelingInterface so the two studies feel like one product. */
.content-panels {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
.content-panels.is-mobile {
  flex-direction: column;
}

.panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.labeling-panel {
  border-left: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.panel-title {
  font-size: 0.9rem;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.resize-divider {
  width: 8px;
  cursor: col-resize;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.resize-divider:hover .resize-handle,
.resize-divider.resizing .resize-handle {
  background: rgb(var(--v-theme-primary));
}
.resize-handle {
  width: 3px;
  height: 40px;
  border-radius: 2px;
  background: rgba(var(--v-theme-on-surface), 0.15);
  transition: background 0.2s ease;
}

/* --- conversation ------------------------------------------------------ */
.collapsed-hint,
.hidden-hint {
  display: flex;
  align-items: center;
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.55);
  font-style: italic;
  padding: 6px 2px 10px;
}

/* Spans live inside the LMessage bubble body — the bubble itself is the real
   component, so only the span layer is styled here. Line height is generous:
   the chips sit inline and the text must stay comfortably readable. */
:deep(.l-message__body) {
  font-size: 1rem;
  line-height: 1.95;
}

.span {
  border-radius: 4px;
  padding: 2px 1px;
  transition: background 0.15s ease, opacity 0.15s ease;
}

.span:not(.span-gap) {
  cursor: pointer;
}

.span:not(.span-gap):hover {
  background: rgba(111, 168, 160, 0.15);
}

/* Current target — the eye must not have to search for it. */
/* Deep slate blue, deliberately OUTSIDE the LLARS palette.
   The five brand colours (primary green, secondary sand, accent teal, success
   mint, danger salmon) are exactly what label sets draw from, so the cursor
   must not be one of them - the previous teal sat in the same family as
   "E - Edification" and read like a category rather than a position.
   Nothing in the palette is dark or blue, so this stays distinct even in
   greyscale, and it reads as UI chrome rather than one more label. */
.span-current {
  background: rgba(74, 111, 165, 0.16);
  box-shadow: 0 0 0 2px #4A6FA5;
}

.span-done {
  background: rgba(var(--v-theme-on-surface), 0.06);
}

/* Marked for merging (ctrl/cmd-click). A dashed outline rather than a fill:
   it has to be distinguishable from BOTH the current span (solid ring) and a
   decided one (filled), and it can sit on top of either. */
/* Achromatic on purpose. Label colours come from the scenario config, so any
   hue chosen here could collide in some other study - this one was literally
   the colour of "Q - Question" in the VRM set. Neutral plus the dashed stroke
   can never clash, and the dashing already separates it from the solid ring
   of the current span. */
.span-marked {
  outline: 2px dashed rgba(var(--v-theme-on-surface), 0.5);
  outline-offset: 1px;
  border-radius: 3px;
}

.span-future {
  opacity: 0.4;
}

.span-hidden {
  visibility: hidden;
}

/* Inline label of a decided span. This is what makes the rater's own sequence
   visible — two identical chips in a row are the block-merge signal. */
.span-chip {
  display: inline-block;
  margin-left: 4px;
  padding: 1px 7px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.72rem;
  font-weight: 700;
  vertical-align: 1px;
}

/* --- decision panel ---------------------------------------------------- */
.labeling-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.focus-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.focus-head {
  display: flex;
  align-items: center;
}

.focus-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.span-counter {
  font-size: 0.85rem;
  font-variant-numeric: tabular-nums;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.focus-span {
  margin: 0;
  padding: 16px 18px;
  border-left: 4px solid #4A6FA5;
  background: rgba(111, 168, 160, 0.1);
  border-radius: 0 16px 16px 0;
  font-size: 1.15rem;
  line-height: 1.6;
}

.category-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* The keyboard hint is an addition over classic labeling — at ~92 decisions
   per conversation the digit keys are the difference between a usable and an
   exhausting task. It stays deliberately quiet so the button still reads like
   its counterpart in the main study: no filled chip, just the colour of the
   category at low contrast. */

.unsure-option {
  display: flex;
  align-items: center;
}

/* Instruction, helpfulness label and note section are lifted verbatim from
   LabelingInterface so the two labeling screens read as one interface. */
.category-instruction {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
  text-align: center;
}

.copilot-helpful-label {
  font-size: 0.72rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
  margin-right: 2px;
}

.feedback-section {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.autoadvance-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-top: 4px;
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}

.keyboard-hint {
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Dashed frame: a suggestion, not a selection. */
.copilot-card {
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 16px 4px 16px 4px;
  padding: 12px 14px;
}

.copilot-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.copilot-title {
  font-size: 0.85rem;
  font-weight: 600;
}

.copilot-suggestion {
  margin-bottom: 8px;
}

.copilot-suggestion-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.copilot-label-chip {
  padding: 2px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.85rem;
  font-weight: 600;
}

.copilot-rationale,
.copilot-evidence {
  margin: 4px 0 0;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.copilot-evidence {
  font-style: italic;
}

.copilot-guardrail {
  display: flex;
  align-items: center;
  margin: 6px 0 0;
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.all-done {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
  font-size: 1rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

/* --- span splitting and merging (quiet tools) ---------------------------- */
/* They sit at the BOTTOM of the panel, just above the note field: both change
   the segmentation for every rater, so they belong out of the decision rhythm
   rather than next to the span they would alter. One horizontal row of faint
   text links — present when needed, invisible when not. */
.split-zone {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 4px;
}

.split-trigger,
.merge-trigger,
.same-label-merge {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  padding: 2px 4px;
  border: none;
  background: none;
  color: rgba(var(--v-theme-on-surface), 0.35);
  font-family: inherit;
  font-size: 0.75rem;
  cursor: pointer;
  transition: color 0.15s ease;
}

.split-trigger:hover:not(:disabled),
.merge-trigger:hover:not(:disabled),
.same-label-merge:hover:not(:disabled) {
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.split-trigger:disabled,
.merge-trigger:disabled,
.same-label-merge:disabled {
  opacity: 0.4;
  cursor: default;
}

/* One step less faint than the others: it only appears once the rater has
   ALREADY labeled both halves the same, so it confirms something they just
   expressed rather than proposing something new. */
.same-label-merge {
  color: rgba(var(--v-theme-on-surface), 0.55);
}

/* How many spans are currently marked — the button's own count, so the rater
   can tell at a glance whether the second ctrl-click registered. */
.merge-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 15px;
  height: 15px;
  margin-left: 5px;
  padding: 0 3px;
  border-radius: 6px 2px 6px 2px;
  background: rgba(var(--v-theme-on-surface), 0.6);
  color: rgb(var(--v-theme-surface));
  font-size: 0.65rem;
  font-weight: 700;
}

/* Says WHY the button is greyed out. Without it a disabled control is just a
   dead end — the rater cannot know that ctrl-click is what unlocks it. */
.merge-hint {
  font-size: 0.72rem;
  font-style: italic;
  color: rgba(var(--v-theme-on-surface), 0.4);
}

.split-panel {
  margin-top: 8px;
  padding: 12px 14px;
  border: 1px dashed rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 16px 4px 16px 4px;
}

.split-hint {
  margin: 0 0 8px;
  font-size: 0.8rem;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

/* Character-level picker: the rater thinks in words, not offsets, so the cut
   point is chosen by clicking into the text. */
.split-preview {
  font-size: 1.02rem;
  line-height: 1.9;
  margin-bottom: 10px;
}

.split-char {
  cursor: text;
  border-left: 2px solid transparent;
}
.split-char:hover {
  border-left-color: rgba(var(--v-theme-on-surface), 0.35);
}
.split-char.is-cut {
  border-left-color: #e8a087;
  background: rgba(232, 160, 135, 0.18);
}

.split-halves {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
  font-size: 0.85rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
}

.split-half {
  padding: 3px 8px;
  border-radius: 6px 2px 6px 2px;
  background: rgba(var(--v-theme-on-surface), 0.06);
}

.split-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.focus-span.is-splitting {
  opacity: 0.5;
}

/* Reveal of a newly unlocked turn. Enter only — leaving turns are never
   removed during normal work, so no leave animation is needed. */
.turn-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.turn-enter-active {
  transition: opacity 0.45s ease, transform 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.turn-enter-from {
  opacity: 0;
  transform: translateY(14px);
}

.turn-move {
  transition: transform 0.35s ease;
}

@media (prefers-reduced-motion: reduce) {
  .span { transition: none; }
  /* The turn still appears — it just does not move. */
  .turn-enter-active,
  .turn-move { transition: none; }
}
</style>
