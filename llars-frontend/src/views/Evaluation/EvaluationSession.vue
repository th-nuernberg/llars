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
          <p v-if="scenario?.description && !hasBriefing" class="text-medium-emphasis">{{ scenario?.description }}</p>
        </div>
      </div>

      <div class="header-right">
        <!-- Progress Indicator -->
        <div class="progress-indicator">
          <span class="progress-text">
            {{ $t('evaluation.progress', { done: progress.completed, total: stageTotal }) }}
          </span>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: stagePercent + '%' }"
            />
          </div>
          <span class="progress-percent">{{ stagePercent }}%</span>
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
      <!-- Viewer Banner -->
      <div v-if="!canEvaluate" class="viewer-banner">
        <LIcon size="18" color="#D1BC8A">mdi-eye-outline</LIcon>
        <span>{{ $t('evaluation.viewerBanner') }}</span>
        <LTag variant="warning">{{ $t('evaluation.viewerReadOnly') }}</LTag>
      </div>

      <div v-if="hasBriefing" class="briefing-banner">
        <!-- On mobile the toggle re-opens the task as a pop-up dialog instead
             of expanding the inline banner (see openTaskPopup); on desktop it
             expands/collapses the inline body as before. -->
        <button class="briefing-toggle" @click="isMobile ? openTaskPopup() : toggleBriefing()">
          <LIcon size="16" class="mr-2" color="#88c4c8">mdi-clipboard-text-outline</LIcon>
          <span class="briefing-toggle-title">{{ $t('evaluation.briefing.title') }}</span>
          <!-- One-time fading hint: first-time evaluators see the briefing
               expanded; the hint nudges them that they can collapse it.
               The hint pulses to draw attention, then fades after ~10s.
               Suppressed on mobile (the task is a pop-up there, nothing to
               collapse). -->
          <span v-if="collapseHintVisible && !isMobile" class="hint-pill hint-pill--briefing">
            <LIcon size="14" class="hint-pill__arrow">mdi-arrow-right-bold</LIcon>
            {{ $t('evaluation.briefing.collapseHint') }}
          </span>
          <!-- Mobile: the chevron always points "tap to open the pop-up"; the
               inline body is never shown on a phone. -->
          <LIcon
            size="16"
            class="toggle-chevron"
            :class="{ rotated: briefingExpanded && !isMobile }"
          >{{ isMobile ? 'mdi-open-in-new' : 'mdi-chevron-down' }}</LIcon>
        </button>
        <!-- Inline body — desktop only. On mobile the task lives in the
             pop-up dialog below so the banner stays a thin tappable bar. -->
        <div v-show="briefingExpanded && !isMobile" class="briefing-body">
          <!-- The wrapping panel already says "Aufgabe", so the task
               markdown renders directly without a redundant sub-label.
               Criteria still get a sub-label because they're a
               distinct second section under the same banner. -->
          <div v-if="taskMarkdown" class="briefing-section">
            <LMarkdownContent :markdown="taskMarkdown" compact />
          </div>
          <div v-if="criteriaMarkdown" class="briefing-section">
            <span class="briefing-label">{{ $t('evaluation.briefing.criteria') }}</span>
            <LMarkdownContent :markdown="criteriaMarkdown" compact />
          </div>
        </div>
      </div>

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
              @item-progress="handleItemProgress"
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
            {{ $t('evaluation.caseNumber', { current: stageCurrent, total: stageTotal }) }}
          </span>
        </div>

        <LBtn
          variant="primary"
          size="small"
          :disabled="!hasNext"
          :class="{ 'next-button-pulse': nextButtonHighlighted }"
          @click="handleNext"
        >
          {{ $t('common.next') }}
          <LIcon end>mdi-chevron-right</LIcon>
        </LBtn>
      </div>

      <!-- Task ("Aufgabe") pop-up. Shown automatically ONCE on the very first
           entry into a scenario (see maybeAutoShowTaskPopup), regardless of
           screen size — the user wanted the same first-entry briefing pop-up on
           desktop/big screens as on mobile. On mobile it fully REPLACES the
           inline banner (the inline body is hidden via !isMobile); on desktop
           it is ADDITIVE — the inline expand/collapse banner above stays, and
           the thin "Aufgabe" bar re-opens this dialog on demand. Gated only on
           hasBriefing now (was isMobile && hasBriefing). -->
      <!-- :transition="false": the auto-opened briefing froze mid-fade
           (scrim/content stuck at ~0.2%/24% opacity) when the enter animation
           ran during the busy initial page load — no animation, no freeze. -->
      <v-dialog v-if="hasBriefing" v-model="taskPopupOpen" max-width="560" scrollable :transition="false">
        <div class="task-popup-card">
          <div class="task-popup-bar">
            <LIcon size="18" class="mr-2" color="#88c4c8">mdi-clipboard-text-outline</LIcon>
            <span class="task-popup-title">{{ $t('evaluation.briefing.title') }}</span>
            <v-spacer />
            <LBtn variant="text" size="small" prepend-icon="mdi-close" @click="taskPopupOpen = false">
              {{ $t('common.close') }}
            </LBtn>
          </div>
          <div class="task-popup-body">
            <div v-if="taskMarkdown" class="briefing-section">
              <LMarkdownContent :markdown="taskMarkdown" compact />
            </div>
            <div v-if="criteriaMarkdown" class="briefing-section">
              <span class="briefing-label">{{ $t('evaluation.briefing.criteria') }}</span>
              <LMarkdownContent :markdown="criteriaMarkdown" compact />
            </div>
          </div>
          <div class="task-popup-footer">
            <LBtn variant="primary" size="small" @click="taskPopupOpen = false">
              {{ $t('common.gotIt', 'Verstanden') }}
            </LBtn>
          </div>
        </div>
      </v-dialog>

      <!-- Universal one-time "thank you" confirmation. Fires after the rater's
           FIRST completed evaluation in this scenario (completed-count 0 → ≥1),
           for EVERY scenario type. Shown at most once per scenario via a
           per-scenario localStorage flag — see maybeShowFirstEvaluationNotice.
           This replaces the comparison-specific notice (which was removed from
           ComparisonInterface so it doesn't double-fire). -->
      <v-dialog v-model="firstEvalNoticeOpen" max-width="420" persistent>
        <div class="first-notice-card">
          <div class="first-notice-icon">
            <LIcon size="40" color="#98d4bb">mdi-check-circle</LIcon>
          </div>
          <h3 class="first-notice-title">{{ $t('evaluation.session.firstEvaluationNotice.title') }}</h3>
          <p class="first-notice-body">{{ $t('evaluation.session.firstEvaluationNotice.saved') }}</p>
          <p class="first-notice-body">{{ $t('evaluation.session.firstEvaluationNotice.next') }}</p>
          <LBtn variant="primary" size="small" @click="firstEvalNoticeOpen = false">
            {{ $t('evaluation.session.firstEvaluationNotice.button') }}
          </LBtn>
        </div>
      </v-dialog>
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
import { ref, computed, defineAsyncComponent, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useMobile } from '@/composables/useMobile'
import { useEvaluationSession, SESSION_STATUS } from '@/composables/useEvaluationSession'
import { useUserPreferences } from '@/composables/useUserPreferences'
import { FUNCTION_TYPE_MAP, EvaluationType } from '@/schemas/evaluationSchemas'
import { resolveCriteriaMarkdown, resolveTaskMarkdown, substituteBriefingVariables } from '@/utils/scenarioBriefing'

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
const { t, locale } = useI18n()
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

// Partial progress reported by a child interface ('item-progress'), keyed by
// item id. Needed because an interface can persist an INCOMPLETE state — e.g.
// labeling with two of three decision questions answered — which is neither
// "pending" nor "done". useEvaluationSession exposes `items` readonly (and a
// partial save must not bump the completed counter), so the session keeps the
// intermediate status in this map; it survives navigation inside the session
// without a reload. Entries are dropped once the item is genuinely completed.
const partialItemStatus = ref({})

// -----------------------------------------------------------------------------
// Universal "thank you for your first evaluation" pop-up
// -----------------------------------------------------------------------------
// Previously this congratulatory pop-up only fired on the FIRST A/B comparison
// (owned by ComparisonInterface via useFirstComparisonNotice). It now lives
// here in the session shell so it fires after the rater's FIRST completed
// evaluation in EVERY scenario type (ranking, rating, labeling, authenticity,
// comparison, …).
//
// Universal signal: the scenario's completed-count transitions 0 → ≥1. The
// child interfaces only ever persist a COMPLETE evaluation (and then
// markItemCompleted bumps progress.completed), so watching that increment fires
// strictly on a genuine save — never on partial interaction.
//
// Gated on a PER-SCENARIO localStorage key so it shows at most once per
// scenario and never again on reloads. Per-scenario (not per-user-global) is
// intentional: the user wanted the encouragement in each scenario type.
const FIRST_EVAL_NOTICE_KEY_PREFIX = 'llars:firstEvaluationNoticeSeen:'
const firstEvalNoticeOpen = ref(false)

function firstEvalNoticeKey() {
  return `${FIRST_EVAL_NOTICE_KEY_PREFIX}${scenarioId.value}`
}

function maybeShowFirstEvaluationNotice() {
  try {
    if (localStorage.getItem(firstEvalNoticeKey()) === '1') return
    localStorage.setItem(firstEvalNoticeKey(), '1')
  } catch {
    // localStorage may throw in private-mode — still show the notice once
    // this session rather than suppress it.
  }
  firstEvalNoticeOpen.value = true
}

// Watch the completed-count for the 0 → ≥1 transition. `oldVal === 0` ensures
// we only fire on the very first completion of the session; later increments
// (2nd, 3rd, … evaluation) are ignored. The per-scenario localStorage gate in
// maybeShowFirstEvaluationNotice() additionally prevents a repeat after reload
// (where completed loads as ≥1 from the start, so the 0→1 edge never recurs).
watch(() => progress.value?.completed || 0, (newVal, oldVal) => {
  if (oldVal === 0 && newVal >= 1) {
    maybeShowFirstEvaluationNotice()
  }
})
// After a successful selection in the child interface we pulse the
// "Weiter" button so the rater knows the next step (Sozialwissenschaften
// 2026-05-18). Cleared on the next item-load to avoid lingering
// attention bait once the user has moved on.
const nextButtonHighlighted = ref(false)

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
    // Reset status based on item's evaluated state. A partial save reported
    // during this session wins over the (then stale) list status.
    const itemId = newItem.thread_id || newItem.id || newItem.item_id
    currentItemStatus.value =
      partialItemStatus.value[itemId] ||
      newItem.status ||
      (newItem.evaluated ? 'done' : 'pending')
  }
}, { immediate: true })

// Function type from loaded scenario (function_type_id)
// Uses FUNCTION_TYPE_MAP from unified schema (evaluationSchemas.js)
// 1=ranking, 2=rating, 3=mail_rating, 4=comparison, 5=authenticity, 7=labeling

const functionType = computed(() => {
  // First try from loaded scenario data
  if (scenario.value?.function_type_id) {
    return FUNCTION_TYPE_MAP[scenario.value.function_type_id] || EvaluationType.RATING
  }
  // Fallback to route meta or params
  return route.meta?.functionType || route.params.type || EvaluationType.RATING
})

// Computed
const canEvaluate = computed(() => scenario.value?.can_evaluate !== false)
const isLoading = computed(() => status.value === SESSION_STATUS.LOADING)

// Default interface based on function type
const defaultInterface = computed(() => {
  const interfaces = {
    rating: defineAsyncComponent(() => import('./interfaces/RatingInterface.vue')),
    mail_rating: defineAsyncComponent(() => import('./interfaces/RatingInterface.vue')),
    ranking: defineAsyncComponent(() => import('./interfaces/RankingInterface.vue')),
    comparison: defineAsyncComponent(() => import('./interfaces/ComparisonInterface.vue')),
    // Communication Comparison reuses ComparisonInterface with a mode prop
    // (counselling-style A/B, distinct option colours, fly-out animation,
    // optional rater-note textarea). Same composable, same persistence —
    // just a different UI shell. See ComparisonInterface.vue for details.
    communication_comparison: defineAsyncComponent(() => import('./interfaces/ComparisonInterface.vue')),
    authenticity: defineAsyncComponent(() => import('./interfaces/AuthenticityInterface.vue')),
    labeling: defineAsyncComponent(() => import('./interfaces/LabelingInterface.vue')),
    // Conversation labeling gets its OWN interface rather than a mode prop on
    // LabelingInterface: the unit of decision differs (span, not item), so the
    // whole interaction — history pane, focus span, keyboard walk, resume — is
    // different rather than restyled.
    conversation_labeling: defineAsyncComponent(
      () => import('./interfaces/ConversationLabelingInterface.vue')
    )
  }
  return interfaces[functionType.value] || interfaces.rating
})

// Get initial item ID from props or route
const initialItemId = computed(() => {
  return props.itemId || route.params.itemId || null
})

// Per-item metadata source for {{variable}} substitution in the
// briefing. Falls back to the empty object so the substitute call
// just leaves placeholders untouched when no item is selected yet.
const itemMeta = computed(() => currentItem.value?.metadata_json || currentItem.value?.metadata || {})

const taskMarkdown = computed(() => substituteBriefingVariables(
  resolveTaskMarkdown(config.value, locale.value),
  itemMeta.value,
  locale.value,
))
const criteriaMarkdown = computed(() => substituteBriefingVariables(
  resolveCriteriaMarkdown(config.value, locale.value),
  itemMeta.value,
  locale.value,
))
const hasBriefing = computed(() => Boolean(taskMarkdown.value || criteriaMarkdown.value))

// Gamification "stage total": when the scenario has gamification enabled
// (Comparison flow), the visible progress denominator tracks the *next*
// milestone instead of the raw item count. Initially that's the first
// milestone (10 items); after each milestone fires the ceiling advances
// by `recurring` (5) until it caps at the real total. Keeps the header
// progress bar and the footer "Fall N / X" in sync with the reward
// gamification the rater is actually working toward.
const stageTotal = computed(() => {
  const cfg = config.value || {}
  const inner = cfg.eval_config?.config || cfg.eval_config || cfg
  const enabled = inner.gamification_enabled === true || inner.gamificationEnabled === true
  const itemsTotal = items.value.length || 0
  if (!enabled || itemsTotal === 0) return itemsTotal

  const rawFirst = inner.gamification_first_milestone ?? inner.gamificationFirstMilestone
  const rawRecurring = inner.gamification_recurring_milestone ?? inner.gamificationRecurringMilestone
  const first = Number.isFinite(Number(rawFirst)) ? Number(rawFirst) : 10
  const recurring = Number.isFinite(Number(rawRecurring)) ? Number(rawRecurring) : 5
  const completed = progress.value?.completed || 0

  if (completed < first) return Math.min(first, itemsTotal)
  if (recurring <= 0) return itemsTotal
  const k = Math.floor((completed - first) / recurring) + 1
  return Math.min(first + k * recurring, itemsTotal)
})
const stagePercent = computed(() => {
  const total = stageTotal.value
  if (!total) return 0
  return Math.min(100, Math.round(((progress.value?.completed || 0) / total) * 100))
})
const stageCurrent = computed(() => Math.min(currentIndex.value + 1, stageTotal.value || items.value.length))
// v3 keys — the Aufgabe now starts COLLAPSED on every screen size (a thin bar),
// because the task is greeted via the first-entry pop-up instead. Only an
// explicit user expand ('true') keeps it open on later visits.
const BRIEFING_EXPANDED_KEY = 'llars:briefingExpanded:v3'
const COLLAPSE_HINT_KEY = 'llars:briefingCollapseHintSeen:v3'
const briefingExpanded = ref(localStorage.getItem(BRIEFING_EXPANDED_KEY) === 'true')

// One-time fading hint near the toggle. Suppressed forever once dismissed —
// either via explicit toggle click or after the auto-fade timer expires.
const collapseHintVisible = ref(
  briefingExpanded.value && localStorage.getItem(COLLAPSE_HINT_KEY) !== '1'
)

function dismissCollapseHint() {
  if (!collapseHintVisible.value) return
  collapseHintVisible.value = false
  localStorage.setItem(COLLAPSE_HINT_KEY, '1')
}

if (collapseHintVisible.value) {
  // Auto-dismiss after ~10s so it doesn't linger if the user ignores it.
  // The CSS animation handles the visual fade-out earlier (8s mark).
  setTimeout(dismissCollapseHint, 10000)
}

// -----------------------------------------------------------------------------
// Task ("Aufgabe") pop-up
// -----------------------------------------------------------------------------
// The long task/briefing auto-opens ONCE as a pop-up dialog on the first case
// (item index 0), the very first time a rater enters this scenario — on ALL
// screen sizes (the user explicitly wanted the same first-entry briefing pop-up
// on desktop/big screens, not just mobile). The one-time auto-open is gated on
// a localStorage flag so it never pops up again on later reloads.
//   - Mobile: this pop-up REPLACES the inline banner (inline body is hidden via
//     !isMobile) and the thin "Aufgabe" bar re-opens it on tap.
//   - Desktop: this pop-up is ADDITIVE — the inline expand/collapse banner
//     above is preserved as the on-demand view; the auto-popup just greets the
//     rater once on first entry.
// PER-SCENARIO seen-flag (v2): the pop-up greets the rater the first time they
// enter EACH scenario — not once globally. (v1 was a single global key, so the
// briefing pop-up only ever fired for the very first scenario a user opened.)
const TASK_POPUP_SEEN_KEY_PREFIX = 'llars:taskPopupAutoShown:v2:'
const taskPopupOpen = ref(false)

function taskPopupSeenKey() {
  return TASK_POPUP_SEEN_KEY_PREFIX + (scenarioId.value || 'x')
}

function openTaskPopup() {
  taskPopupOpen.value = true
}

// Auto-show the pop-up the first time ANY rater is on case 1 of THIS scenario
// with a briefing present (no isMobile gate — all screen sizes). Re-runs as
// briefing/ready state resolves; the per-scenario seen-flag fires it at most
// once per scenario.
function maybeAutoShowTaskPopup() {
  if (!hasBriefing.value) return
  if (currentIndex.value !== 0) return
  const key = taskPopupSeenKey()
  if (localStorage.getItem(key) === '1') return
  localStorage.setItem(key, '1')
  // Defer the open past the initial render: setting taskPopupOpen while the
  // page is still mounting (deep link / full reload) left the v-dialog stuck
  // mid-enter-transition — unstyled transparent text floating over the
  // content with dead pointer events.
  nextTick(() => requestAnimationFrame(() => { taskPopupOpen.value = true }))
}

// Trigger the auto-show once the briefing is known (hasBriefing flips true
// after the config loads) while still on the first case.
watch(hasBriefing, (has) => {
  if (has) maybeAutoShowTaskPopup()
}, { immediate: true })

function toggleBriefing() {
  briefingExpanded.value = !briefingExpanded.value
  localStorage.setItem(BRIEFING_EXPANDED_KEY, String(briefingExpanded.value))
  // Once the user has consciously toggled the briefing, remember that
  // choice and stop auto-collapsing on item-transitions — see the watch
  // below. The flag persists across sessions so a user who values having
  // the briefing open keeps it open forever.
  localStorage.setItem(BRIEFING_USER_TOUCHED_KEY, '1')
  briefingUserTouched.value = true
  dismissCollapseHint()
}

// Auto-collapse after the FIRST navigation away from the initial item.
// Reasoning (Sozialwissenschaften 2026-05-18): the task description is most useful
// on case #1 — by case #2 the rater has internalised it and the wall
// of text starts eating into the conversation/options space. We collapse
// once when the user clicks "Weiter" on the very first item, but leave
// the manual toggle as the source of truth from there on. If the user
// explicitly toggles (touched flag set) we never auto-collapse again.
const BRIEFING_USER_TOUCHED_KEY = 'llars:briefingUserTouched:v2'
const briefingUserTouched = ref(localStorage.getItem(BRIEFING_USER_TOUCHED_KEY) === '1')

watch(currentIndex, (newIdx, oldIdx) => {
  // Only fire on the first transition (item 0 → item 1+). Subsequent
  // navigations leave the briefing in whatever state the user prefers.
  if (oldIdx === 0 && newIdx > 0 && briefingExpanded.value && !briefingUserTouched.value) {
    briefingExpanded.value = false
    localStorage.setItem(BRIEFING_EXPANDED_KEY, 'false')
    dismissCollapseHint()
  }
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
  // Clear the pulse-attention so the user doesn't get re-prompted on the
  // next item (which starts pending again).
  nextButtonHighlighted.value = false
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

// --- Leertaste = "Weiter" (opt-in Shortcut) --------------------------------
// Standardmäßig AUS; jeder User aktiviert den Shortcut selbst unter Settings →
// Präferenzen (persistiert pro User, siehe useUserPreferences). Gilt für ALLE
// Szenario-Typen, solange man in der Evaluation ist. Ausnahme: Fokus in einem
// Textfeld/Editable — dort tippt die Leertaste ganz normal ein Leerzeichen.
const { spacebarAdvance } = useUserPreferences()

function isEditableTarget(el) {
  if (!el) return false
  const tag = (el.tagName || '').toUpperCase()
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true
  if (el.isContentEditable) return true
  const role = el.getAttribute && el.getAttribute('role')
  return role === 'textbox' || role === 'combobox'
}

function onEvaluationKeydown(e) {
  if (!spacebarAdvance.value) return
  // Leertaste (key ' ' bzw. code 'Space'); keine Modifier, kein Auto-Repeat.
  if (e.key !== ' ' && e.code !== 'Space') return
  if (e.ctrlKey || e.metaKey || e.altKey || e.shiftKey) return
  if (e.repeat) return
  if (isEditableTarget(e.target)) return
  if (!hasNext.value) return
  // Standard-Scrollen der Seite durch die Leertaste unterdrücken.
  e.preventDefault()
  handleNext()
}

onMounted(() => {
  window.addEventListener('keydown', onEvaluationKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onEvaluationKeydown)
})

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

// Copy of the partial-status map without one entry (kept immutable so the
// watchers/templates reading it actually re-evaluate).
function withoutItem(map, itemId) {
  const next = { ...map }
  delete next[itemId]
  return next
}

// Handle an INCOMPLETE but persisted state from a child interface (e.g. a
// labeling item with some — but not all — decision questions answered). The
// footer tag flips to "In Bearbeitung" and the status is remembered per item so
// navigating away and back doesn't fall back to "Ausstehend". Never touches the
// completed counter — only handleItemCompleted does.
function handleItemProgress(payload) {
  const itemId = payload?.itemId ?? payload?.thread_id ?? payload
  const status = payload?.status || 'in_progress'
  if (!itemId) return

  if (status === 'done') {
    // Completion arrives via item-completed; drop the stale partial marker.
    partialItemStatus.value = withoutItem(partialItemStatus.value, itemId)
  } else {
    partialItemStatus.value = { ...partialItemStatus.value, [itemId]: status }
  }

  const currentId = currentItem.value?.thread_id || currentItem.value?.id || currentItem.value?.item_id
  if (currentId === itemId) {
    currentItemStatus.value = status
  }
}

// Handle item completion - update progress without reloading
function handleItemCompleted(itemId) {
  partialItemStatus.value = withoutItem(partialItemStatus.value, itemId)
  markItemCompleted(itemId)
  // Pulse the Weiter button to signal the next step once a selection
  // lands. Skip when there's nothing left to advance to.
  if (hasNext.value) {
    nextButtonHighlighted.value = true
  }
}
</script>

<style scoped>
/* Universal one-time thank-you dialog — on-brand card (LLARS asymmetric
   radius, success-tinted check). Mirrors the comparison .first-notice-card
   styling; centralised here now that the session shell owns the notice. */
.first-notice-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
  padding: 28px 24px 24px;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
}
.first-notice-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(152, 212, 187, 0.18);
}
.first-notice-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}
.first-notice-body {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.5;
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.85;
}

.evaluation-session {
  /* Sozialwissenschaften 2026-05-18: viewport-fit shell — no outer page scroll.
     Header (64 px) + footer (30 px) sit at the AppBar/Footer of the
     global layout, leaving 100vh - 94px for this view. The child
     content panels (context-body, option-content) handle their own
     scrolling inside. Using `height` instead of `min-height` + an
     explicit `overflow: hidden` ensures the browser can't grow the
     outer doc above the viewport. */
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

/* Viewer Banner */
.viewer-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 24px;
  background: rgba(209, 188, 138, 0.12);
  border-bottom: 1px solid rgba(209, 188, 138, 0.3);
  font-size: 0.82rem;
  color: rgba(var(--v-theme-on-surface), 0.8);
  flex-shrink: 0;
}

.briefing-banner {
  background: rgba(136, 196, 200, 0.08);
  border-bottom: 1px solid rgba(136, 196, 200, 0.25);
  flex-shrink: 0;
}

.briefing-toggle {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 6px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  color: rgba(var(--v-theme-on-surface), 0.8);
}

.briefing-toggle:hover {
  background: rgba(136, 196, 200, 0.08);
}

.briefing-toggle-title {
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  flex: 1;
  text-align: left;
}

.toggle-chevron {
  transition: transform 0.2s ease;
}

.toggle-chevron.rotated {
  transform: rotate(180deg);
}

/* First-session attention pill — clearly visible accent-tinted badge
   that pulses gently to draw attention, then fades after ~10s.
   Removed from layout entirely once the visibility ref flips. */
.hint-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin: 0 10px;
  padding: 2px 10px;
  border-radius: 12px 3px 12px 3px;
  background: rgba(136, 196, 200, 0.18);
  border: 1px solid rgba(136, 196, 200, 0.55);
  color: rgba(var(--v-theme-on-surface), 0.85);
  font-size: 0.78rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  white-space: nowrap;
  pointer-events: none;
  animation: hint-pill-cycle 10s ease-in-out forwards;
}

.hint-pill__arrow {
  animation: hint-arrow-nudge 1.4s ease-in-out infinite;
}

@keyframes hint-pill-cycle {
  0%   { opacity: 0; transform: translateX(-4px) scale(0.95); }
  6%   { opacity: 1; transform: translateX(0)    scale(1); }
  60%  { opacity: 1; transform: translateX(0)    scale(1); }
  100% { opacity: 0; transform: translateX(0)    scale(1); }
}

@keyframes hint-arrow-nudge {
  0%, 100% { transform: translateX(0); }
  50%      { transform: translateX(3px); }
}

.briefing-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  padding: 4px 24px 12px;
  /* Cap height so expanding the briefing never eats the evaluation area.
     overflow-y: auto adds a scrollbar only when content exceeds the cap. */
  max-height: 40vh;
  overflow-y: auto;
}

.briefing-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.briefing-label {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Content Area — fills available height between header and footer.
   The interior child (comparison/rating/etc. interface) takes care
   of its own scrolling; we just clip overflow so the outer shell
   never grows. `min-height: 0` is required for nested flex children
   to shrink below their intrinsic content size. */
.session-content {
  flex: 1 1 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-height: 0;
}

/* Unified Navigation Footer — sits at the bottom of the viewport.
   No longer position-sticky since the parent now uses a fixed-height
   flex shell (overflow-hidden); the footer is just a flex-shrink:0
   sibling underneath the content. */
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

/* "Weiter" button attention-pulse — kicks in after an item is marked
   completed and stays animated until the user actually clicks Weiter
   (handleNext clears the flag). Uses an outward-pulsing box-shadow ring
   plus a subtle scale tick so it's noticeable without being noisy. */
.next-button-pulse {
  animation: nextButtonPulse 1.4s ease-in-out infinite;
  position: relative;
}
@keyframes nextButtonPulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(176, 202, 151, 0.65);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(176, 202, 151, 0);
    transform: scale(1.03);
  }
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
/* Mobile shell height (Steigerwald 2026-06-05): the desktop `100vh - 94px`
   is WRONG on a phone — `100vh` includes the mobile URL bar, so the flex-pinned
   `.session-footer` was pushed below the visible viewport and the rater couldn't
   reach the nav row. Fix: use `100dvh` (dynamic viewport height, excludes the
   URL bar) minus the ACTUAL global chrome read from App.vue:
     - AppBar: Vuetify stock `v-app-bar` = 64px (App.vue uses no height/density
       override; `.is-mobile` only changes padding, not the 64px toolbar).
     - Global footer: forced to 24px on mobile via
       `.llars-footer.is-mobile { max-height: 24px }` in App.vue.
   → 64 + 24 = 88px. A plain `100vh` line precedes the `100dvh` line as a
   fallback for browsers without dvh support. */
.evaluation-session.is-mobile {
  height: calc(100vh - 88px);
  height: calc(100dvh - 88px);
}

.evaluation-session.is-mobile .session-header {
  /* Compact ONE-LINE header (Steigerwald 2026-06-05): keep the header a flex
     ROW on mobile (was column, which wasted two rows). "← Zurück" + title +
     a small progress bar + "%" sit on a single thin strip. The wordy
     "X / Y abgeschlossen" text is hidden (the footer already shows "Fall N/X").
     Reduced padding turns the header into a slim bar above the content. */
  flex-direction: row;
  gap: 8px;
  padding: 5px 12px;
}

.evaluation-session.is-mobile .header-left {
  /* Let the title row take the leftover width and ellipsize the scenario
     name instead of wrapping. min-width:0 is required for the child <h1>
     ellipsis to engage inside a flex row. */
  flex: 1;
  min-width: 0;
  gap: 8px;
}

.evaluation-session.is-mobile .header-info {
  min-width: 0;
  flex: 1;
}

.evaluation-session.is-mobile .header-info h1 {
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Compact "Zurück" button — tighter padding so it doesn't crowd the title. */
.evaluation-session.is-mobile .header-left :deep(.v-btn) {
  min-width: 0;
  padding: 0 10px;
}

.evaluation-session.is-mobile .header-right {
  /* Just the mini progress bar + "%" on the right edge; no longer full-width. */
  flex-shrink: 0;
  gap: 6px;
}

/* Hide the verbose "X / Y abgeschlossen" copy on mobile — redundant with the
   footer's "Fall N/X" and the bar + "%" already communicate progress. */
.evaluation-session.is-mobile .progress-text {
  display: none;
}

.evaluation-session.is-mobile .progress-indicator {
  gap: 6px;
}

.evaluation-session.is-mobile .progress-bar {
  width: 54px;
}

.evaluation-session.is-mobile .progress-percent {
  font-size: 0.78rem;
  min-width: 30px;
}

/* "Aufgabe" briefing bar — slim tappable strip on mobile (Steigerwald
   2026-06-05). It opens the task as a pop-up on a phone, so the bar only needs
   the clipboard icon + "Aufgabe" + the open-in-new chevron; trim its vertical
   padding hard and tighten the icon line so it reads as a one-line strip. */
.evaluation-session.is-mobile .briefing-toggle {
  padding: 2px 12px;
  line-height: 1.05;
}

/* Shrink the clipboard + chevron icons so the "Aufgabe" strip is barely
   taller than its text (Steigerwald 2026-06-05 mobile pass). */
.evaluation-session.is-mobile .briefing-toggle :deep(.v-icon) {
  font-size: 14px !important;
}

.evaluation-session.is-mobile .briefing-toggle-title {
  font-size: 0.78rem;
}

.evaluation-session.is-mobile .briefing-body {
  padding: 4px 16px 8px;
  max-height: 30vh;
}

.evaluation-session.is-mobile .viewer-banner {
  padding: 4px 16px;
}

/* Bottom nav bar (Previous / Completed / Case N/5 / Next) — slimmer on
   mobile (Steigerwald 2026-06-03). Trim the row padding, shrink the LBtn
   min-height + their internal padding, and tighten the centre status so
   the whole footer is a thin strip and the mail panels keep the room. */
.evaluation-session.is-mobile .session-footer {
  padding: 5px 12px;
  /* Now that the shell height is correct (100dvh - 88px) this flex-pinned
     footer always lands inside the visible viewport, directly above the global
     app footer. A stronger top border + subtle upward shadow make it read as a
     pinned nav bar rather than blending into the content above. */
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.14);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.08);
  z-index: 1;
}

.evaluation-session.is-mobile .footer-center {
  /* De-squeeze the centre cluster (status tag + "Fall N/X"): a sensible gap so
     the two don't collide on a narrow phone. */
  gap: 10px;
  min-width: 0;
}

.evaluation-session.is-mobile .footer-center .nav-position {
  font-size: 0.85rem;
}

/* Footer status: icon only on mobile — the "Abgeschlossen/In Bearbeitung"
   label eats width and the check/clock icon already conveys it. */
.evaluation-session.is-mobile .footer-center :deep(.status-label) {
  display: none;
}

/* Keep the footer a thin strip but make the buttons comfortably tappable
   (≈38px, no fixed height cap) with proper internal padding — 26px was below
   a safe touch target (Steigerwald 2026-06-03 mobile pass). */
.evaluation-session.is-mobile .session-footer :deep(.v-btn) {
  min-height: 38px;
  padding: 6px 16px;
  font-size: 0.78rem;
}

.evaluation-session.is-mobile .session-footer :deep(.v-btn .v-icon) {
  font-size: 16px;
}

/* Mobile task pop-up card — on-brand (LLARS asymmetric radius), top bar with
   close, scrolling body capped to the viewport, footer "Verstanden". Mirrors
   the briefing-body layout so the task/criteria sections render identically to
   the desktop inline banner, just inside a dialog. */
.task-popup-card {
  display: flex;
  flex-direction: column;
  max-height: 80vh;
  background: rgb(var(--v-theme-surface));
  border-radius: 16px 4px 16px 4px;
  overflow: hidden;
}
.task-popup-bar {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(136, 196, 200, 0.3);
  background: rgba(136, 196, 200, 0.1);
  flex-shrink: 0;
}
.task-popup-title {
  font-size: 0.92rem;
  font-weight: 600;
  letter-spacing: 0.03em;
}
.task-popup-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.task-popup-footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}
</style>
