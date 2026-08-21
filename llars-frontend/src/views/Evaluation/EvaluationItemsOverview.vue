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
          <p v-if="scenario?.description && !hasBriefing" class="text-medium-emphasis">
            {{ scenario.description }}
          </p>
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

    <!-- Viewer Banner -->
    <div v-if="!canEvaluate && !loading" class="viewer-banner">
      <LIcon size="18" color="#D1BC8A">mdi-eye-outline</LIcon>
      <span>{{ $t('evaluation.viewerBanner') }}</span>
      <LTag variant="warning">{{ $t('evaluation.viewerReadOnly') }}</LTag>
    </div>

    <div v-if="hasBriefing && !loading" class="briefing-banner" :class="{ 'is-mobile': isMobile }">
      <!-- On mobile the toggle opens the task as a pop-up (matches the per-item
           EvaluationSession); on desktop it expands the inline body. -->
      <button class="briefing-toggle" @click="isMobile ? openTaskPopup() : toggleBriefing()">
        <LIcon size="16" class="mr-2" color="#88c4c8">mdi-clipboard-text-outline</LIcon>
        <span class="briefing-toggle-title">{{ $t('evaluation.briefing.title') }}</span>
        <LIcon size="16" class="toggle-chevron" :class="{ rotated: briefingExpanded && !isMobile }">{{ isMobile ? 'mdi-open-in-new' : 'mdi-chevron-down' }}</LIcon>
      </button>
      <!-- Inline body — desktop only; on mobile the task lives in the pop-up
           so the banner stays a thin tappable bar. -->
      <div v-show="briefingExpanded && !isMobile" class="briefing-body">
        <!-- The toggle already says "Aufgabe", so we drop the redundant
             "Aufgabenbeschreibung" sub-label (same pattern as the
             EvaluationSession briefing). Criteria keep their sub-label
             because they're a distinct second section. -->
        <div v-if="taskMarkdown" class="briefing-section">
          <LMarkdownContent :markdown="taskMarkdown" compact />
        </div>
        <div v-if="criteriaMarkdown" class="briefing-section">
          <span class="briefing-label">{{ $t('evaluation.briefing.criteria') }}</span>
          <LMarkdownContent :markdown="criteriaMarkdown" compact />
        </div>
      </div>
    </div>

    <!-- "Aufgabe" pop-up, auto-shown ONCE on first entry into a scenario on ALL
         screen sizes (the user wanted the same first-entry briefing pop-up on
         desktop too). On mobile it replaces the inline banner; on desktop it is
         additive (the inline expand/collapse banner stays as the on-demand view).
         Gated only on hasBriefing now (was isMobile && hasBriefing). -->
    <!-- :transition="false" — see EvaluationSession briefing dialog (frozen fade on load) -->
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

    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-chips">
        <button
          class="filter-chip"
          :class="{ active: activeFilter === 'all' }"
          @click="activeFilter = 'all'"
        >
          {{ $t('common.all') }} ({{ visibleItems.length }})
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
      <!-- Reward button: opens the same aggregated provenance popup the
           rater sees inside ComparisonInterface after a milestone. Lets
           the user check at any time how often they preferred a human,
           a trained AI or an untrained AI without having to wait for
           the next milestone. Only shown for comparison/comm-comparison
           scenarios with gamification on. Disabled until at least one
           item has been evaluated, since the popup would be empty
           otherwise. -->
      <LBtn
        v-if="gamification.enabled"
        variant="primary"
        size="small"
        class="reward-btn"
        :class="{ 'reward-btn--pulse': isAtMilestone }"
        :disabled="completedCount === 0"
        :title="$t('evaluation.comparison.gamification.viewHistory')"
        @click="rewardOpen = true"
      >
        <LIcon start>mdi-trophy-outline</LIcon>
        {{ $t('evaluation.comparison.gamification.rewardLabel') }}
      </LBtn>
    </div>

    <!-- Reward popup — aggregated preference statistics (human vs trained
         AI vs base AI). Same component the ComparisonInterface uses
         after each milestone; here it's user-triggered via the button
         above so they can peek any time. -->
    <ComparisonRewardDialog
      v-if="gamification.enabled"
      v-model="rewardOpen"
      :scenario-id="Number(props.scenarioId)"
      :milestone-count="completedCount"
      :is-first="completedCount <= gamification.first"
    />

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
      <!-- Progressive-reveal hint: tells the user how many more clicks
           until the next batch unlocks. Only shown while there is still
           something locked. -->
      <div
        v-if="gamification.progressiveReveal && itemsUntilNextUnlock > 0 && unlockedCount < items.length"
        class="reveal-hint"
      >
        <LIcon size="16" class="mr-1">mdi-lock-clock</LIcon>
        <span>
          {{ $t('evaluation.comparison.gamification.unlocksIn', { n: itemsUntilNextUnlock }) }}
        </span>
      </div>

      <div class="items-grid">
        <div
          v-for="(item, index) in filteredItems"
          :key="item.id || item.thread_id || index"
          class="item-card"
          :class="[
            getItemStatusClass(item),
            { 'milestone-card': isMilestoneIndex(index) }
          ]"
          :title="isMilestoneIndex(index)
            ? $t('evaluation.comparison.gamification.milestoneTooltip')
            : null"
          @click="goToItem(item, index)"
        >
          <!-- Milestone Reward Ribbon: shown ahead of time on item N where
               N matches `first` or `first + k*recurring`, so the user
               sees in the grid which clicks open a reward popup. Locked
               cards never render here — the filteredItems computed
               drops them entirely. -->
          <div
            v-if="isMilestoneIndex(index)"
            class="milestone-ribbon"
            :title="$t('evaluation.comparison.gamification.milestoneTooltip')"
          >
            <LIcon size="12" class="milestone-ribbon-icon">mdi-trophy-variant</LIcon>
            <span class="milestone-ribbon-label">
              {{ $t('evaluation.comparison.gamification.rewardLabel') }}
            </span>
          </div>

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
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import { resolveCriteriaMarkdown, resolveTaskMarkdown, substituteBriefingVariables } from '@/utils/scenarioBriefing'
import ComparisonRewardDialog from '@/views/Evaluation/interfaces/ComparisonRewardDialog.vue'
import { useMobile } from '@/composables/useMobile'

const props = defineProps({
  scenarioId: {
    type: [Number, String],
    required: true
  }
})

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const { isMobile } = useMobile()

// State
const scenario = ref(null)
const items = ref([])
const sessionConfig = ref({})
const loading = ref(true)
const error = ref(null)
const activeFilter = ref('all')
const canEvaluate = ref(true)
// Reward dialog open-state. Toggled by the trophy button in the
// filter row; the dialog itself lazy-loads the aggregated preference
// stats from /api/evaluation/session/<id>/preferences each time it
// opens, so the user always sees fresh counts.
const rewardOpen = ref(false)

// Type configuration (localized; computed so labels follow locale switches)
const typeConfigs = computed(() => ({
  1: { icon: 'mdi-podium', color: '#b0ca97', bgColor: 'rgba(176, 202, 151, 0.15)', label: t('scenarioManager.types.ranking') },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', bgColor: 'rgba(209, 188, 138, 0.15)', label: t('scenarioManager.types.rating') },
  3: { icon: 'mdi-email-outline', color: '#e8a087', bgColor: 'rgba(232, 160, 135, 0.15)', label: t('scenarioManager.types.mailRating') },
  4: { icon: 'mdi-compare-horizontal', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', label: t('scenarioManager.types.comparison') },
  5: { icon: 'mdi-shield-search', color: '#c4a0d4', bgColor: 'rgba(196, 160, 212, 0.15)', label: t('scenarioManager.types.authenticity') },
  7: { icon: 'mdi-tag-outline', color: '#98d4bb', bgColor: 'rgba(152, 212, 187, 0.15)', label: t('scenarioManager.types.labeling') },
  8: { icon: 'mdi-forum-outline', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', label: t('scenarioManager.types.communicationComparison') },
  // 9 = conversation_labeling: item is a conversation, the vote is a span in it
  9: { icon: 'mdi-tag-multiple-outline', color: '#6FA8A0', bgColor: 'rgba(111, 168, 160, 0.15)', label: t('scenarioManager.types.conversationLabeling') }
}))

const typeConfig = computed(() => {
  if (!scenario.value) return typeConfigs.value[2]
  return typeConfigs.value[scenario.value.function_type_id] || {
    icon: 'mdi-clipboard-outline', color: '#888', bgColor: 'rgba(136, 136, 136, 0.15)',
    label: t('scenarioManager.types.unknown')
  }
})

// Progress calculations.
//
// The status filter chips ("Alle / Ausstehend / In Bearbeitung / Abgeschlossen")
// must count over the currently VISIBLE window only. Under progressive-reveal the
// rater can only ever see/act on `unlockedCount` cards, so the chips read against
// that subset (e.g. "Alle (5)" not "Alle (96)"), widening as further batches
// unlock. `visibleItems` falls back to the full list when reveal is off.
const visibleItems = computed(() => {
  if (!gamification.value.progressiveReveal) return items.value
  return items.value.slice(0, unlockedCount.value)
})

// completedCount stays over the FULL list on purpose: done items always live
// inside the unlocked window, so the value is identical — and `unlockedCount`
// depends on it, so counting over `visibleItems` would be circular.
const completedCount = computed(() => items.value.filter(i => getItemStatus(i) === 'done').length)
const inProgressCount = computed(() => visibleItems.value.filter(i => getItemStatus(i) === 'in_progress').length)
const pendingCount = computed(() => visibleItems.value.filter(i => getItemStatus(i) === 'pending').length)

// Progress denominator follows the unlock window when progressive-reveal
// is on — the user only ever sees / works on `unlockedCount` cards at a
// time, so the header "X / Y completed" reads against the unlocked
// subset. Once they hit the next milestone, the window widens and the
// denominator grows with it. Without this, gamified scenarios always
// look <20 % done at the start, which is demotivating.
const progressTotal = computed(() => {
  if (gamification.value.progressiveReveal) {
    return Math.max(unlockedCount.value, 1)
  }
  return Math.max(items.value.length, 1)
})

const progress = computed(() => ({
  completed: completedCount.value,
  total: progressTotal.value
}))

const progressPercent = computed(() => {
  if (progressTotal.value === 0) return 0
  return Math.round((completedCount.value / progressTotal.value) * 100)
})

// Overview has no single "current item", so {{variable}} placeholders
// can't be substituted against per-item metadata. Fall back to a
// generic descriptor for `channel_label` so the briefing reads
// naturally ("ein Beratungsverlauf" rather than "ein {{channel_label}}").
// The per-item EvaluationSession substitutes with the actual item's
// metadata, so the rater sees the concrete format once they enter a card.
const OVERVIEW_FALLBACK_META = {
  channel_label: {
    de: 'Beratungsverlaufs (E-Mail, Chat oder Sprechstunde)',
    en: 'counselling exchange (email, chat or session)',
  },
}
const taskMarkdown = computed(() => substituteBriefingVariables(
  resolveTaskMarkdown(sessionConfig.value, locale.value),
  OVERVIEW_FALLBACK_META,
  locale.value,
))
const criteriaMarkdown = computed(() => substituteBriefingVariables(
  resolveCriteriaMarkdown(sessionConfig.value, locale.value),
  OVERVIEW_FALLBACK_META,
  locale.value,
))
const hasBriefing = computed(() => Boolean(taskMarkdown.value || criteriaMarkdown.value))
// v3 storage key — matches EvaluationSession.vue. The Aufgabe now starts
// COLLAPSED (thin bar) on every screen size; it's greeted via the first-entry
// pop-up instead. Only an explicit user expand ('true') keeps it open.
const BRIEFING_EXPANDED_KEY = 'llars:briefingExpanded:v3'
const briefingExpanded = ref(localStorage.getItem(BRIEFING_EXPANDED_KEY) === 'true')

function toggleBriefing() {
  briefingExpanded.value = !briefingExpanded.value
  localStorage.setItem(BRIEFING_EXPANDED_KEY, String(briefingExpanded.value))
}

// The "Aufgabe" shows as a pop-up the first time the user enters EACH scenario,
// on ALL screen sizes. Uses the SAME per-scenario key as EvaluationSession so
// the greeting fires once per scenario regardless of entry path (overview vs.
// a direct item link) — no double pop-up.
const TASK_POPUP_SEEN_KEY_PREFIX = 'llars:taskPopupAutoShown:v2:'
const taskPopupOpen = ref(false)
function taskPopupSeenKey() {
  return TASK_POPUP_SEEN_KEY_PREFIX + (props.scenarioId || 'x')
}
function openTaskPopup() {
  taskPopupOpen.value = true
}
function maybeAutoShowTaskPopup() {
  if (!hasBriefing.value) return
  const key = taskPopupSeenKey()
  if (localStorage.getItem(key) === '1') return
  localStorage.setItem(key, '1')
  // Defer past the initial render — see EvaluationSession.maybeAutoShowTaskPopup:
  // a synchronous open during mount leaves the dialog stuck mid-transition.
  nextTick(() => requestAnimationFrame(() => { taskPopupOpen.value = true }))
}
watch(hasBriefing, (has) => { if (has) maybeAutoShowTaskPopup() }, { immediate: true })

// Filtered items based on active filter.
//
// Progressive-reveal: when enabled, hide cards beyond the current
// unlock window completely. The user only sees the first N unlocked
// items; locked items don't render at all (no greyed-out cards, no
// lock overlay). The "X more to unlock the next batch" banner stays
// above the grid so the user knows new cards are coming.
const filteredItems = computed(() => {
  const base = activeFilter.value === 'all'
    ? items.value
    : items.value.filter(item => getItemStatus(item) === activeFilter.value)

  if (!gamification.value.progressiveReveal) return base
  return base.slice(0, unlockedCount.value)
})

// Gamification reward-system config — read from the same nested path the
// wizard writes to (config_json.eval_config.config.*) and fall back to
// the top-level for legacy seeders. Powers the trophy badge + milestone
// frame on the overview grid so the user sees in advance which click
// triggers the reward popup.
const gamification = computed(() => {
  const cfg = sessionConfig.value || {}
  const ec = cfg?.eval_config?.config || {}
  const get = (...keys) => {
    for (const k of keys) {
      if (ec[k] !== undefined) return ec[k]
      if (cfg[k] !== undefined) return cfg[k]
    }
    return undefined
  }
  const enabled =
    get('gamificationEnabled', 'gamification_enabled') === true
  const first = Number(
    get('gamificationFirstMilestone', 'gamification_first_milestone') ?? 10
  )
  const recurring = Number(
    get('gamificationRecurringMilestone', 'gamification_recurring_milestone') ?? 5
  )
  // Progressive reveal: only effective when gamification is also on.
  // Cards beyond the next milestone are hidden (or shown as locked, see
  // `progressiveLockedAt` below) until the user crosses it.
  const reveal =
    get('progressiveReveal', 'progressive_reveal') === true
  // Gamification (countdown badge, milestone-card frame, progressive
  // reveal) is only meaningful for the pairwise-comparison flow, which
  // covers both classic Comparison (function_type_id=4) and the
  // counselling-style Communication-Comparison (=8). Both share the
  // ItemComparisonEvaluation persistence and the same milestone schedule.
  const fnId = scenario.value?.function_type_id ?? null
  const isComparison = fnId === 4 || fnId === 8
  return {
    enabled: enabled && isComparison,
    progressiveReveal: enabled && isComparison && reveal,
    first: Number.isFinite(first) && first > 0 ? first : 10,
    recurring: Number.isFinite(recurring) && recurring > 0 ? recurring : 5
  }
})

// True when the rater has just hit a milestone and the reward popup
// is "due". Used to pulse the trophy button so the user notices that
// a fresh aggregated-preferences view is available. Cleared when the
// rater actually opens the dialog (via a watcher on rewardOpen, see
// below) and also resets whenever the next milestone schedule fires.
const isAtMilestone = computed(() => {
  const g = gamification.value
  if (!g.enabled) return false
  const c = completedCount.value
  if (c <= 0) return false
  if (c === g.first) return true
  if (g.recurring > 0 && c > g.first && (c - g.first) % g.recurring === 0) {
    return true
  }
  return false
})

// In progressive-reveal mode, how many cards has the user already
// unlocked? Schedule: 0..first-1 are open from the start (the user must
// complete `first` to hit the first reward, which then unlocks
// `recurring` more), so unlockedCount =
//   first             + (recurring × completed_milestones)
// where completed_milestones = floor((completed - first) / recurring) + 1
//   when completed >= first, else 0.
const unlockedCount = computed(() => {
  const g = gamification.value
  if (!g.progressiveReveal) return items.value.length
  const total = items.value.length
  const completed = completedCount.value
  if (completed < g.first) return Math.min(g.first, total)
  const milestonesHit = 1 + Math.floor((completed - g.first) / g.recurring)
  return Math.min(g.first + milestonesHit * g.recurring, total)
})

// Index past which cards are visually locked (not navigable). Used by
// the grid template's :class binding + click-guard.
function isLockedIndex(index) {
  const g = gamification.value
  if (!g.progressiveReveal) return false
  return index >= unlockedCount.value
}

// How many more comparisons until the next batch unlocks. Drives the
// "complete X more to unlock the next batch" hint shown above the grid.
const itemsUntilNextUnlock = computed(() => {
  const g = gamification.value
  if (!g.progressiveReveal) return 0
  const completed = completedCount.value
  if (completed < g.first) return g.first - completed
  const into = (completed - g.first) % g.recurring
  return g.recurring - into
})

// True for the 1-based ordinals matching the milestone schedule
// (first, first+recurring, first+2*recurring, …). The grid is 0-indexed,
// so we compare `index + 1` against the schedule.
function isMilestoneIndex(index) {
  const g = gamification.value
  if (!g.enabled) return false
  const ordinal = index + 1
  if (ordinal < g.first) return false
  if (ordinal === g.first) return true
  return (ordinal - g.first) % g.recurring === 0
}

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
    // Load scenario details and items in parallel
    const [scenarioResponse, sessionResponse] = await Promise.all([
      axios.get(`/api/scenarios/${props.scenarioId}`),
      axios.get(`/api/evaluation/session/${props.scenarioId}`)
    ])
    scenario.value = scenarioResponse.data
    items.value = sessionResponse.data.items || []
    sessionConfig.value = sessionResponse.data.config || {}
    canEvaluate.value = sessionResponse.data.scenario?.can_evaluate !== false
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

.briefing-body {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  padding: 4px 24px 12px;
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

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background: rgb(var(--v-theme-surface));
  flex-shrink: 0;
  gap: 12px;
}

.filter-chips {
  display: flex;
  gap: 8px;
  flex: 1 1 auto;
}

/* Reward-trigger button on the right end of the filter row. Pulses
   when a fresh milestone is reachable so the user notices that the
   aggregated-preference popup has something new to show. */
.reward-btn {
  flex-shrink: 0;
}
.reward-btn--pulse {
  animation: rewardBtnPulse 1.6s ease-in-out infinite;
}
@keyframes rewardBtnPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(176, 202, 151, 0.55); }
  50%      { box-shadow: 0 0 0 10px rgba(176, 202, 151, 0); }
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

/* Milestone-card highlight: signals upfront which click triggers a
   reward popup. The card uses LLARS beige (secondary) for both the
   border and the soft top→bottom gradient — keeps it warm and "reward-
   like" without competing with the green Primary used for status. */
.item-card.milestone-card {
  /* Force a uniform border on all four sides — explicit longhand
     overrides any status-* `border-left: 3px` that might otherwise
     sneak through. */
  border-width: 1.5px;
  border-style: solid;
  border-color: rgba(209, 188, 138, 0.7);
  background: linear-gradient(180deg,
    rgba(209, 188, 138, 0.18) 0%,
    rgba(209, 188, 138, 0.05) 32%,
    rgb(var(--v-theme-surface)) 100%);
  box-shadow: 0 1px 0 rgba(209, 188, 138, 0.5) inset,
              0 4px 14px -8px rgba(209, 188, 138, 0.55);
}
.item-card.milestone-card:hover {
  border-color: rgb(var(--v-theme-secondary));
  box-shadow: 0 1px 0 rgba(209, 188, 138, 0.6) inset,
              0 8px 24px -10px rgba(209, 188, 138, 0.7);
}

/* Reward ribbon: small pill in the top-left of the card that pairs the
   trophy with a "Belohnung / Reward" label. Beige gradient matches the
   card so it reads as integrated, not stuck-on. */
.milestone-ribbon {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px 3px 7px;
  border-radius: 10px 2px 10px 2px;
  background: linear-gradient(135deg,
    rgb(var(--v-theme-secondary)) 0%,
    color-mix(in srgb, rgb(var(--v-theme-secondary)) 75%, #b0a06e) 100%);
  color: white;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  box-shadow: 0 2px 6px -2px rgba(0, 0, 0, 0.18);
}

.milestone-ribbon-icon {
  color: white;
  filter: drop-shadow(0 1px 1px rgba(0, 0, 0, 0.2));
}

.milestone-ribbon-label {
  line-height: 1;
}

/* Push the item number down a bit so it doesn't overlap the ribbon. */
.item-card.milestone-card .item-number {
  margin-top: 22px;
}

/* Progressive-reveal lock state */
.item-card.locked-card {
  position: relative;
  cursor: not-allowed;
  opacity: 0.55;
  pointer-events: auto;
}

.item-card.locked-card:hover {
  /* override the regular .item-card:hover lift — locked cards stay put */
  transform: none;
  box-shadow: none;
}

.lock-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: rgba(var(--v-theme-surface-variant), 0.55);
  backdrop-filter: blur(2px);
  border-radius: inherit;
  z-index: 2;
}

.lock-icon {
  color: rgba(var(--v-theme-on-surface), 0.55);
}

.lock-label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(var(--v-theme-on-surface), 0.65);
}

/* Hint banner above the grid when progressive-reveal is active */
.reveal-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  padding: 10px 14px;
  border-radius: 12px 3px 12px 3px;
  background: linear-gradient(135deg,
    rgba(176, 202, 151, 0.15) 0%,
    rgba(136, 196, 200, 0.10) 100%);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.06);
  font-size: 0.88rem;
  color: rgba(var(--v-theme-on-surface), 0.75);
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

/* Phones: shrink the status filter chips so all four (Alle / Ausstehend /
   In Bearbeitung / Abgeschlossen) fit comfortably without horizontal scroll. */
@media (max-width: 600px) {
  .filter-bar {
    gap: 8px;
    padding: 8px 12px;
  }
  .filter-chips {
    gap: 6px;
  }
  .filter-chip {
    padding: 4px 9px;
    font-size: 0.72rem;
  }
}

/* Thin "Aufgabe" bar on mobile (the body is a pop-up there, not inline). */
.briefing-banner.is-mobile .briefing-toggle {
  padding: 4px 14px;
}
.briefing-banner.is-mobile .briefing-toggle-title {
  font-size: 0.82rem;
}

/* Mobile "Aufgabe" pop-up — mirrors EvaluationSession's task pop-up. */
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
