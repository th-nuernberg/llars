<template>
  <div class="overview-page">
    <!-- Header -->
    <div class="overview-header">
      <LBtn variant="tonal" prepend-icon="mdi-arrow-left" size="small" @click="goHome">
        {{ $t('navigation.home') }}
      </LBtn>
      <div class="header-info">
        <h1>{{ $t('evaluation.title') }}</h1>
        <p class="text-medium-emphasis">{{ $t('evaluation.subtitle') }}</p>
      </div>
      <div class="header-stats">
        <LTag v-if="availableScenarios.length > 0" variant="primary" size="small">
          {{ $t('evaluation.available', { count: availableScenarios.length }) }}
        </LTag>
      </div>
    </div>

    <!-- Filter Bar — same chip pattern as the per-scenario item overview
         (EvaluationItemsOverview) so both evaluation screens filter alike.
         Default is "Aktiv": finished studies stay reachable but no longer
         clutter the list of what still needs doing. -->
    <div class="filter-bar">
      <div class="filter-chips">
        <button
          v-for="f in filters"
          :key="f.key"
          class="filter-chip"
          :class="[`filter-${f.key}`, { active: activeFilter === f.key }]"
          :data-filter="f.key"
          @click="activeFilter = f.key"
        >
          {{ $t(f.labelKey) }} ({{ f.count }})
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="overview-content">
      <!-- Skeleton Loading -->
      <div v-if="isLoading('scenarios')" class="scenarios-grid">
        <div v-for="n in 6" :key="'skel-' + n" class="scenario-card-skeleton">
          <v-skeleton-loader type="list-item-avatar-two-line" />
        </div>
      </div>

      <template v-else>
        <!-- Scenarios Grid -->
        <div v-if="availableScenarios.length > 0" class="scenarios-grid">
          <div
            v-for="scenario in availableScenarios"
            :key="scenario.id"
            class="scenario-card"
            :class="{
              'is-completed': getProgress(scenario).percent === 100,
              'is-expired': isExpired(scenario),
              'is-new': newScenarioIds.has(scenario.id)
            }"
            :data-scenario-id="scenario.id"
            :ref="(element) => registerScenarioCard(scenario.id, element)"
            @click="goToEvaluation(scenario)"
          >
            <!-- Header Row: Icon, Type Tag, Status Badge -->
            <div class="card-header">
              <div class="header-left">
                <div class="type-icon" :style="{ backgroundColor: getTypeConfig(scenario).bgColor }">
                  <LIcon :color="getTypeConfig(scenario).color" size="18">{{ getTypeConfig(scenario).icon }}</LIcon>
                </div>
                <span
                  class="type-chip"
                  :style="{ backgroundColor: getTypeConfig(scenario).bgColor, color: getTypeConfig(scenario).color }"
                >
                  {{ $t(getTypeConfig(scenario).labelKey) }}
                </span>
                <!-- Expired scenarios stay visible (they used to vanish silently
                     once `end` passed) but are labelled so raters understand why
                     the study looks different. See isExpired(). -->
                <span v-if="isExpired(scenario)" class="expired-chip">
                  {{ $t('evaluation.expired') }}
                </span>
                <span v-if="newScenarioIds.has(scenario.id)" class="new-chip">
                  {{ $t('evaluation.justAdded') }}
                </span>
              </div>
              <LEvaluationStatus :status="getStatus(scenario)" />
            </div>

            <!-- Card Content -->
            <div class="card-content">
              <h3 class="card-title">{{ scenario.scenario_name }}</h3>
              <span class="owner-name">{{ scenario.is_owner ? $t('scenarioManager.card.owner') : scenario.owner_name }}</span>
            </div>

            <!-- Progress Bar (always at bottom) -->
            <div class="progress-section">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getProgress(scenario).percent + '%' }"></div>
              </div>
              <span class="progress-text">{{ getProgress(scenario).completed }}/{{ getProgress(scenario).total }}</span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <LIcon size="64" color="grey-lighten-1">mdi-clipboard-text-off-outline</LIcon>
          <h3>{{ $t('evaluation.noScenariosAvailable') }}</h3>
          <p class="text-medium-emphasis">
            {{ $t('evaluation.emptyHint') }}
          </p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useSkeletonLoading } from '@/composables/useSkeletonLoading'
import { getSocket } from '@/services/socketService'

const router = useRouter()
const { tokenParsed } = useAuth()
const { isLoading, withLoading } = useSkeletonLoading(['scenarios'])

// All scenarios from backend
const allScenarios = ref([])
const currentUserId = computed(() => {
  return tokenParsed.value?.sub ? String(tokenParsed.value.sub) : ''
})
const currentUsername = computed(() => {
  const storedUsername = typeof window !== 'undefined' ? localStorage.getItem('username') : ''
  return tokenParsed.value?.preferred_username ||
    tokenParsed.value?.username ||
    tokenParsed.value?.name ||
    storedUsername ||
    ''
})

const scenarioCardElements = new Map()
const pendingScenarioStats = []
const queuedScenarioIds = new Set()
const loadingScenarioIds = new Set()
const resolvedScenarioIds = new Set()
const statsRetryCounts = new Map()
const MAX_CONCURRENT_STATS_REQUESTS = 1
const MAX_STATS_REQUEST_RETRIES = 2
const STATS_REQUEST_SPACING_MS = 300
const STATS_RATE_LIMIT_COOLDOWN_MS = 30000

let scenarioCardObserver = null
let activeStatsRequests = 0
let statsQueueTimer = null
let nextStatsRequestAt = 0
let statsRateLimitedUntil = 0

// Type configuration
// Labels resolve through the i18n `evaluation.types.<key>` namespace so
// both DE and EN render consistently. The icon/colour stays per-id here;
// only the visible string is localised.
const typeConfigs = {
  1: { icon: 'mdi-podium', color: '#b0ca97', bgColor: 'rgba(176, 202, 151, 0.15)', labelKey: 'evaluation.types.ranking' },
  2: { icon: 'mdi-star-outline', color: '#D1BC8A', bgColor: 'rgba(209, 188, 138, 0.15)', labelKey: 'evaluation.types.rating' },
  3: { icon: 'mdi-email-outline', color: '#e8a087', bgColor: 'rgba(232, 160, 135, 0.15)', labelKey: 'evaluation.types.mail_rating' },
  4: { icon: 'mdi-compare-horizontal', color: '#88c4c8', bgColor: 'rgba(136, 196, 200, 0.15)', labelKey: 'evaluation.types.comparison' },
  5: { icon: 'mdi-shield-search', color: '#c4a0d4', bgColor: 'rgba(196, 160, 212, 0.15)', labelKey: 'evaluation.types.authenticity' },
  7: { icon: 'mdi-tag-outline', color: '#98d4bb', bgColor: 'rgba(152, 212, 187, 0.15)', labelKey: 'evaluation.types.labeling' },
  // Communication Comparison (function_type_id=8): counselling-context
  // A/B picks where the rater chooses what they'd "send" to the client.
  // Same data shape as comparison(4); a distinct teal-blue identity so
  // researchers can spot them at a glance in the hub.
  8: { icon: 'mdi-message-arrow-right-outline', color: '#7BAFC5', bgColor: 'rgba(123, 175, 197, 0.15)', labelKey: 'evaluation.types.communication_comparison' },
  // Conversation Labeling (function_type_id=9): the work unit is a whole
  // conversation, the decision is a single span inside it. Labeling(7) config
  // shape, but with the conversation history kept in view — its own muted
  // teal so it reads as "labeling, but conversational".
  9: { icon: 'mdi-tag-multiple-outline', color: '#6FA8A0', bgColor: 'rgba(111, 168, 160, 0.15)', labelKey: 'evaluation.types.conversation_labeling' }
}

function getTypeConfig(scenario) {
  return typeConfigs[scenario.function_type_id] || typeConfigs[2]
}

// The backend derives `status` from the scenario's begin/end window
// (scenario_manager_api.format_scenario_for_api): once `end` passes it
// reports 'completed'. That is a schedule state, NOT an archival state —
// the evaluation endpoints have no date guard, so raters can still submit.
const isExpired = (scenario) => scenario?.status === 'completed'

// Which slice of the list is shown. Defaults to 'active': the hub answers
// "what still needs doing", so finished studies must not clutter it. They stay
// one click away under "Beendet" / "Alle" — the earlier bug was that they
// vanished with no way back, not that they were listed at all.
const activeFilter = ref('active')

// Progress state of a scenario for the current user, mirroring the per-item
// chips on EvaluationItemsOverview so both screens use one vocabulary.
function progressState(scenario) {
  const { completed, total } = getProgress(scenario)
  if (total > 0 && completed >= total) return 'done'
  if (completed > 0 || (scenario.user_progress?.progressing || 0) > 0) return 'in_progress'
  return 'pending'
}

function matchesFilter(scenario, key) {
  switch (key) {
    case 'all':
      return true
    case 'expired':
      return isExpired(scenario)
    // The progress buckets deliberately exclude expired studies: an elapsed
    // scenario is not something the rater can still be "pending" on.
    case 'active':
      return !isExpired(scenario)
    case 'pending':
    case 'in_progress':
    case 'done':
      return !isExpired(scenario) && progressState(scenario) === key
    default:
      return true
  }
}

const accessibleScenarios = computed(() => {
  return allScenarios.value
    .filter(s => {
      // Show scenarios where user is owner OR has accepted invitation
      const isOwner = s.is_owner
      const isInvited = s.invitation?.status === 'accepted'

      const isHidden = s.status === 'archived' || s.status === 'draft'

      return (isOwner || isInvited) && !isHidden
    })
    // Newest first. The API exposes `begin` as the creation timestamp
    // (format_scenario_for_api sets created_at from it), so a scenario created
    // today always leads regardless of ownership or schedule state.
    .sort((a, b) => new Date(b.begin || b.created_at || 0) - new Date(a.begin || a.created_at || 0))
})

// Counts come from the full accessible set, so each chip always shows the
// true total for its bucket rather than a count of what the current filter
// happens to leave visible.
const FILTER_DEFS = [
  { key: 'active', labelKey: 'evaluation.filters.active' },
  { key: 'pending', labelKey: 'evaluation.status.pending' },
  { key: 'in_progress', labelKey: 'evaluation.status.inProgress' },
  { key: 'done', labelKey: 'evaluation.status.done' },
  { key: 'expired', labelKey: 'evaluation.filters.expired' },
  { key: 'all', labelKey: 'common.all' },
]

const filters = computed(() =>
  FILTER_DEFS.map(def => ({
    ...def,
    count: accessibleScenarios.value.filter(s => matchesFilter(s, def.key)).length,
  }))
)

// What the grid actually renders. Expired studies stay openable when shown —
// the evaluation endpoints have no date guard, so a rater who still wants to
// finish (or re-read) a finished study can.
const availableScenarios = computed(() =>
  accessibleScenarios.value.filter(s => matchesFilter(s, activeFilter.value))
)

function getProgress(scenario) {
  const completed = scenario.user_progress?.completed || 0
  const total = scenario.user_progress?.total || scenario.thread_count || 0
  const percent = total > 0 ? Math.round((completed / total) * 100) : 0
  return { completed, total, percent }
}

function getStatus(scenario) {
  const progress = getProgress(scenario)
  if (progress.percent === 100) return 'done'
  // Show 'in_progress' if any items are completed OR if any are currently being worked on
  const progressing = scenario.user_progress?.progressing || 0
  if (progress.completed > 0 || progressing > 0) return 'in_progress'
  if (scenario.invitation?.status === 'pending') return 'pending'
  return 'pending'
}

function registerScenarioCard(scenarioId, element) {
  const existingElement = scenarioCardElements.get(scenarioId)
  if (existingElement && scenarioCardObserver) {
    scenarioCardObserver.unobserve(existingElement)
  }

  if (!element) {
    scenarioCardElements.delete(scenarioId)
    return
  }

  scenarioCardElements.set(scenarioId, element)
  element.dataset.scenarioId = String(scenarioId)

  if (scenarioCardObserver) {
    scenarioCardObserver.observe(element)
  }
}

function buildUserProgressFromStats(statsData, fallbackTotal = 0) {
  const backendResolvedProgress = statsData?.current_user_progress
  if (backendResolvedProgress && typeof backendResolvedProgress === 'object') {
    const completed = Number(backendResolvedProgress.completed ?? 0)
    const progressing = Number(backendResolvedProgress.progressing ?? 0)
    const total = Number(backendResolvedProgress.total ?? fallbackTotal)
    return {
      completed: Number.isFinite(completed) ? completed : 0,
      progressing: Number.isFinite(progressing) ? progressing : 0,
      total: Number.isFinite(total) ? total : fallbackTotal
    }
  }

  const userId = currentUserId.value
  const username = currentUsername.value
  if (!userId && !username) {
    return null
  }
  const normalizedUsername = username ? username.toLowerCase() : ''

  const raterStats = Array.isArray(statsData?.rater_stats) ? statsData.rater_stats : []
  const evaluatorStats = Array.isArray(statsData?.evaluator_stats) ? statsData.evaluator_stats : []
  const humanEvaluatorStats = evaluatorStats.filter(entry => !entry?.is_llm)
  const allHumanStats = [...raterStats, ...humanEvaluatorStats]
  const userStat = allHumanStats.find(
    entry => (
      (userId && String(entry?.user_id || '') === userId) ||
      (normalizedUsername && String(entry?.username || '').toLowerCase() === normalizedUsername)
    )
  )

  if (!userStat) {
    return null
  }

  const completed = Number(userStat.done_threads ?? userStat.voted_count ?? 0)
  const progressing = Number(userStat.progressing_threads ?? 0)
  const total = Number(userStat.total_threads ?? fallbackTotal)

  return { completed, progressing, total }
}

async function loadScenarioStats(scenarioId) {
  try {
    const response = await axios.get(`/api/scenarios/${scenarioId}/stats`)
    const scenarioIndex = allScenarios.value.findIndex(scenario => scenario.id === scenarioId)
    if (scenarioIndex < 0) {
      return { success: true }
    }

    const scenario = allScenarios.value[scenarioIndex]
    const userProgress = buildUserProgressFromStats(response.data, scenario.thread_count)
    if (!userProgress) {
      return { success: true }
    }

    allScenarios.value[scenarioIndex] = {
      ...scenario,
      user_progress: userProgress
    }
    return { success: true }
  } catch (error) {
    console.warn(`Error loading stats for scenario ${scenarioId}:`, error)
    return {
      success: false,
      statusCode: Number(error?.response?.status || 0),
      retryAfterMs: parseRetryAfterMs(error?.response?.headers?.['retry-after'])
    }
  }
}

function parseRetryAfterMs(retryAfterHeader) {
  if (!retryAfterHeader) {
    return 0
  }

  const headerValue = Array.isArray(retryAfterHeader) ? retryAfterHeader[0] : retryAfterHeader
  const seconds = Number(headerValue)
  if (Number.isFinite(seconds) && seconds > 0) {
    return Math.round(seconds * 1000)
  }

  const timestamp = Date.parse(String(headerValue))
  if (!Number.isFinite(timestamp)) {
    return 0
  }

  return Math.max(0, timestamp - Date.now())
}

function shouldRetryStatsRequest(statusCode) {
  if (!Number.isFinite(statusCode) || statusCode <= 0) {
    return true
  }

  if (statusCode >= 500) {
    return true
  }

  return statusCode === 408 || statusCode === 425
}

function scheduleStatsQueue(delayMs = 0) {
  if (statsQueueTimer) {
    return
  }

  statsQueueTimer = setTimeout(() => {
    statsQueueTimer = null
    processStatsQueue()
  }, Math.max(0, Math.round(delayMs)))
}

function processStatsQueue() {
  if (pendingScenarioStats.length === 0) {
    return
  }

  const now = Date.now()
  if (statsRateLimitedUntil > now) {
    scheduleStatsQueue(statsRateLimitedUntil - now)
    return
  }

  while (activeStatsRequests < MAX_CONCURRENT_STATS_REQUESTS && pendingScenarioStats.length > 0) {
    const waitForSpacingMs = nextStatsRequestAt - Date.now()
    if (waitForSpacingMs > 0) {
      scheduleStatsQueue(waitForSpacingMs)
      return
    }

    const scenarioId = pendingScenarioStats.shift()
    queuedScenarioIds.delete(scenarioId)

    if (resolvedScenarioIds.has(scenarioId) || loadingScenarioIds.has(scenarioId)) {
      continue
    }

    activeStatsRequests += 1
    loadingScenarioIds.add(scenarioId)
    nextStatsRequestAt = Date.now() + STATS_REQUEST_SPACING_MS

    loadScenarioStats(scenarioId)
      .then(result => {
        if (result.success) {
          resolvedScenarioIds.add(scenarioId)
          statsRetryCounts.delete(scenarioId)
          return
        }

        if (result.statusCode === 429) {
          const cooldownMs = result.retryAfterMs || STATS_RATE_LIMIT_COOLDOWN_MS
          statsRateLimitedUntil = Math.max(statsRateLimitedUntil, Date.now() + cooldownMs)
        }

        if (shouldRetryStatsRequest(result.statusCode)) {
          const retryCount = (statsRetryCounts.get(scenarioId) || 0) + 1
          if (retryCount <= MAX_STATS_REQUEST_RETRIES) {
            statsRetryCounts.set(scenarioId, retryCount)
            queuedScenarioIds.add(scenarioId)
            pendingScenarioStats.push(scenarioId)
            if (statsRateLimitedUntil > Date.now()) {
              scheduleStatsQueue(statsRateLimitedUntil - Date.now())
            }
            return
          }
        }

        statsRetryCounts.delete(scenarioId)
        resolvedScenarioIds.add(scenarioId)
      })
      .finally(() => {
        activeStatsRequests -= 1
        loadingScenarioIds.delete(scenarioId)
        processStatsQueue()
      })
  }
}

function queueScenarioStatsLoad(scenarioId) {
  if (
    resolvedScenarioIds.has(scenarioId) ||
    queuedScenarioIds.has(scenarioId) ||
    loadingScenarioIds.has(scenarioId)
  ) {
    return
  }

  queuedScenarioIds.add(scenarioId)
  pendingScenarioStats.push(scenarioId)
  processStatsQueue()
}

function observeScenarioCards() {
  if (!scenarioCardObserver) {
    return
  }

  for (const element of scenarioCardElements.values()) {
    scenarioCardObserver.observe(element)
  }
}

function setupScenarioCardObserver() {
  if (scenarioCardObserver) {
    scenarioCardObserver.disconnect()
  }

  if (typeof window === 'undefined' || typeof window.IntersectionObserver !== 'function') {
    availableScenarios.value.forEach(scenario => queueScenarioStatsLoad(scenario.id))
    return
  }

  scenarioCardObserver = new window.IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) {
          return
        }

        const scenarioId = Number(entry.target?.dataset?.scenarioId)
        if (!Number.isFinite(scenarioId)) {
          return
        }

        queueScenarioStatsLoad(scenarioId)
        scenarioCardObserver?.unobserve(entry.target)
      })
    },
    {
      root: null,
      rootMargin: '160px 0px',
      threshold: 0.1
    }
  )

  observeScenarioCards()
}

// ---------------------------------------------------------------------------
// Live access grants
//
// When someone adds this user to a scenario, the backend pushes it to their
// personal invite room (socketio_handlers/events_scenarios.py). Previously a
// rater sitting on this page had no idea a study had been shared with them
// until they reloaded — they had to be told out-of-band.
//
// Runs over the existing Socket.IO connection rather than a second realtime
// transport: the app already holds an authenticated socket for presence, and
// the server derives the room from the token identity, so no client can
// subscribe to someone else's invitations.
// ---------------------------------------------------------------------------

// Ids that should render with the arrival highlight. Cleared per-scenario after
// the animation so a later re-render doesn't replay it.
const newScenarioIds = ref(new Set())
const highlightTimers = new Map()
let socket = null
let socketHandlersAttached = false

const HIGHLIGHT_MS = 6000

function markScenarioAsNew(scenarioId) {
  newScenarioIds.value = new Set(newScenarioIds.value).add(scenarioId)

  const existing = highlightTimers.get(scenarioId)
  if (existing) clearTimeout(existing)

  highlightTimers.set(scenarioId, setTimeout(() => {
    const next = new Set(newScenarioIds.value)
    next.delete(scenarioId)
    newScenarioIds.value = next
    highlightTimers.delete(scenarioId)
  }, HIGHLIGHT_MS))
}

function handleAccessGranted(payload) {
  const scenario = payload?.scenario
  if (!scenario?.id) return

  const index = allScenarios.value.findIndex(s => s.id === scenario.id)
  if (index >= 0) {
    // Already known (e.g. a role change on an existing membership) — refresh
    // it in place instead of adding a duplicate card.
    allScenarios.value[index] = { ...allScenarios.value[index], ...scenario }
  } else {
    allScenarios.value = [scenario, ...allScenarios.value]
  }

  markScenarioAsNew(scenario.id)

  // The card is new to the DOM, so the IntersectionObserver has to pick it up
  // before its progress stats will load.
  nextTick(() => observeScenarioCards())
}

function subscribeToAccessGrants() {
  socket = getSocket()
  if (!socket || socketHandlersAttached) return

  const emitSubscribe = () => socket.emit('scenario:subscribe_invites', {})

  socket.on('scenario:access_granted', handleAccessGranted)
  // Re-join after every reconnect — room membership lives on the server side
  // and is lost when the socket drops.
  socket.on('connect', emitSubscribe)
  socketHandlersAttached = true

  if (socket.connected) emitSubscribe()
}

function teardownAccessGrants() {
  highlightTimers.forEach(clearTimeout)
  highlightTimers.clear()

  if (!socket) return
  try {
    if (socket.connected) socket.emit('scenario:unsubscribe_invites', {})
    socket.off('scenario:access_granted', handleAccessGranted)
  } catch (e) {
    // Socket already torn down — nothing to clean up.
  }
  socket = null
  socketHandlersAttached = false
}

async function fetchScenarios() {
  try {
    const response = await axios.get('/api/scenarios', {
      params: { filter: 'all', include_stats: 'false' }
    })
    allScenarios.value = response.data.scenarios || []
  } catch (error) {
    console.error('Error fetching scenarios:', error)
  }
}

function goToEvaluation(scenario) {
  // Navigate to the items overview for this scenario
  router.push({ name: 'EvaluationItemsOverview', params: { scenarioId: scenario.id } })
}

function goHome() {
  router.push('/Home')
}

onMounted(async () => {
  await withLoading('scenarios', fetchScenarios)
  await nextTick()
  setupScenarioCardObserver()
  subscribeToAccessGrants()
})

watch(
  () => availableScenarios.value.map(scenario => scenario.id).join(','),
  async () => {
    await nextTick()
    observeScenarioCards()
  }
)

onBeforeUnmount(() => {
  if (scenarioCardObserver) {
    scenarioCardObserver.disconnect()
    scenarioCardObserver = null
  }
  if (statsQueueTimer) {
    clearTimeout(statsQueueTimer)
    statsQueueTimer = null
  }
  scenarioCardElements.clear()
  teardownAccessGrants()
})
</script>

<style scoped>
.overview-page {
  height: calc(100vh - 94px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
}

.overview-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.header-info {
  flex: 1;
}

.header-info h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
}

.header-info p {
  margin: 4px 0 0 0;
  font-size: 0.9rem;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 8px;
}

.overview-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.scenario-card {
  position: relative;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 12px 4px 12px 4px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.scenario-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
  border-color: rgba(var(--v-theme-primary), 0.3);
}

.scenario-card.is-completed {
  border-left: 3px solid rgb(var(--v-theme-success));
}

/* Finished studies read as "greyed out" but stay fully interactive: the card
   keeps its pointer cursor and click handler, a desaturating veil just marks it
   as no longer collecting. The veil sits in ::after with pointer-events:none so
   it never intercepts the click. Hovering lifts it, which both confirms the
   card is live and makes the content readable again. */
.scenario-card.is-expired {
  filter: grayscale(0.75);
  opacity: 0.78;
  transition: filter 0.18s ease, opacity 0.18s ease;
}

.scenario-card.is-expired::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: rgba(var(--v-theme-on-surface), 0.06);
  pointer-events: none;
  transition: opacity 0.18s ease;
}

.scenario-card.is-expired:hover {
  filter: grayscale(0);
  opacity: 1;
}

.scenario-card.is-expired:hover::after {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .scenario-card.is-expired,
  .scenario-card.is-expired::after {
    transition: none;
  }
}

/* Filter bar — visually identical to the chips on EvaluationItemsOverview
   so a rater sees the same control in the same place on both screens. */
.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 24px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  flex-shrink: 0;
}

.filter-chips {
  display: flex;
  gap: 8px;
  flex: 1 1 auto;
  flex-wrap: wrap;
}

.filter-chip {
  display: flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.15);
  border-radius: 20px;
  background: transparent;
  color: inherit;
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

.filter-chip.filter-pending.active {
  background: rgba(var(--v-theme-warning), 0.15);
  border-color: rgb(var(--v-theme-warning));
  color: rgb(var(--v-theme-warning));
}

.filter-chip.filter-in_progress.active {
  background: rgba(136, 196, 200, 0.15);
  border-color: #88c4c8;
  color: #88c4c8;
}

.filter-chip.filter-done.active {
  background: rgba(152, 212, 187, 0.15);
  border-color: #98d4bb;
  color: #3d8b6a;
}

/* Expired: same muted grey as the card veil, so the chip and the cards it
   reveals read as the same category. */
.filter-chip.filter-expired.active {
  background: rgba(var(--v-theme-on-surface), 0.1);
  border-color: rgba(var(--v-theme-on-surface), 0.4);
  color: rgba(var(--v-theme-on-surface), 0.7);
}

@media (max-width: 600px) {
  .filter-bar {
    padding: 8px 12px;
  }
  .filter-chip {
    padding: 5px 10px;
    font-size: 0.72rem;
  }
}

/* Arrival animation for a scenario pushed in live over Socket.IO. The card
   slides in once, then a ring pulses so the eye is drawn to it even if the
   rater was looking elsewhere on the page. Both stop on their own — the
   highlight class is removed after HIGHLIGHT_MS. */
.scenario-card.is-new {
  animation: scenario-arrive 0.45s ease-out, scenario-pulse 1.6s ease-out 0.45s 2;
}

.new-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  background: rgba(176, 202, 151, 0.25);
  color: #5d7a45;
}

@keyframes scenario-arrive {
  from {
    opacity: 0;
    transform: translateY(-10px) scale(0.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes scenario-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(176, 202, 151, 0.65);
  }
  70% {
    box-shadow: 0 0 0 12px rgba(176, 202, 151, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(176, 202, 151, 0);
  }
}

/* Respect the OS setting: the card still appears and still carries the
   "just added" chip, it just doesn't move or pulse. */
@media (prefers-reduced-motion: reduce) {
  .scenario-card.is-new {
    animation: none;
  }
}

/* Header row with icon, type tag and status badge */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* Allow the status to drop below when a long type label (e.g.
     "Kommunikations-Vergleich") makes the left group too wide, instead of
     the chip text wrapping mid-word and looking broken. */
  flex-wrap: wrap;
  row-gap: 6px;
  margin-bottom: 10px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.type-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px 3px 8px 3px;
  flex-shrink: 0;
}

.type-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
}

/* Expired = scheduling window elapsed. Muted rather than alarming: the
   scenario is still openable, it just isn't actively collecting. */
.expired-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 6px 2px 6px 2px;
  font-size: 0.7rem;
  font-weight: 600;
  white-space: nowrap;
  background: rgba(var(--v-theme-on-surface), 0.08);
  color: rgba(var(--v-theme-on-surface), 0.6);
}

/* Card content */
.card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.card-title {
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.3;
}

.owner-name {
  font-size: 0.75rem;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

/* Progress Section (always at bottom) */
.progress-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background-color: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 6px;
  margin-top: auto;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background-color: rgba(var(--v-theme-on-surface), 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: rgb(var(--v-theme-primary));
  border-radius: 2px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.7);
  white-space: nowrap;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}

.empty-state h3 {
  margin: 16px 0 8px;
  font-size: 1.1rem;
  font-weight: 600;
}

.empty-state p {
  max-width: 400px;
}

/* Responsive */
@media (max-width: 768px) {
  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .overview-header {
    flex-wrap: wrap;
  }

  .header-info {
    order: 2;
    width: 100%;
    margin-top: 12px;
  }
}
</style>
