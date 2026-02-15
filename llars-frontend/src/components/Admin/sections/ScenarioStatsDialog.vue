<template>
  <v-dialog
    v-model="dialogVisible"
    :fullscreen="isFullscreen"
    :max-width="isFullscreen ? undefined : '1100'"
    scrollable
  >
    <v-card class="stats-dialog">
      <!-- Header with gradient accent -->
      <div class="dialog-header">
        <div class="header-content">
          <div class="header-icon">
            <LIcon size="28">mdi-chart-box</LIcon>
          </div>
          <div class="header-text">
            <h2 class="header-title">{{ scenario?.name || 'Statistiken' }}</h2>
            <span class="header-subtitle">{{ subtitle }}</span>
          </div>
        </div>
        <div class="header-actions">
          <LIconBtn
            :icon="isFullscreen ? 'mdi-fullscreen-exit' : 'mdi-fullscreen'"
            :tooltip="isFullscreen ? 'Vollbild beenden' : 'Vollbild'"
            @click="toggleFullscreen"
          />
          <LIconBtn icon="mdi-close" tooltip="Schließen" @click="close" />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner">
          <v-progress-circular indeterminate color="primary" size="56" width="4" />
        </div>
        <p class="loading-text">Statistiken werden geladen...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state">
        <div class="error-icon">
          <LIcon size="48" color="error">mdi-alert-circle-outline</LIcon>
        </div>
        <p class="error-text">{{ error }}</p>
        <LBtn variant="primary" prepend-icon="mdi-refresh" @click="fetchStats">
          Erneut versuchen
        </LBtn>
      </div>

      <!-- Stats Content -->
      <div v-else class="stats-content" :class="{ 'fullscreen-content': isFullscreen }">
        <!-- Key Metrics Row -->
        <div class="metrics-grid">
          <div class="metric-card metric-total">
            <div class="metric-icon icon-secondary">
              <LIcon>mdi-format-list-numbered</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Aufgaben gesamt</span>
              <div class="metric-value-row">
                <span class="metric-value">{{ totalAssigned }}</span>
              </div>
              <span class="metric-hint">Zuweisungen an Viewer</span>
            </div>
          </div>

          <div class="metric-card metric-completed">
            <div class="metric-icon icon-success">
              <LIcon>mdi-check-circle-outline</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Abgeschlossen</span>
              <div class="metric-value-row">
                <span class="metric-value text-success">{{ totalDone }}</span>
              </div>
              <span class="metric-hint">Bereits bewertet</span>
            </div>
          </div>

          <div class="metric-card metric-progress">
            <div class="metric-icon icon-accent">
              <LIcon>mdi-percent-circle</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Fortschritt</span>
              <div class="metric-value-row">
                <span class="metric-value text-accent">{{ overallProgress }}%</span>
              </div>
              <div class="progress-bar-container">
                <div class="progress-bar-track">
                  <div class="progress-bar-fill" :style="{ width: overallProgress + '%' }"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="metric-card metric-users">
            <div class="metric-icon icon-warning">
              <LIcon>mdi-account-group</LIcon>
            </div>
            <div class="metric-body">
              <span class="metric-label">Nutzer</span>
              <div class="metric-value-row">
                <span class="metric-value">{{ totalUsers }}</span>
              </div>
              <span class="metric-hint">Viewer & Evaluatoren</span>
            </div>
          </div>
        </div>

        <!-- User Stats Section -->
        <div class="section-card users-section">
          <div class="section-header">
            <LIcon class="section-icon">mdi-account-group</LIcon>
            <h3 class="section-title">Benutzer-Fortschritt</h3>
            <div class="section-actions">
              <v-text-field
                v-model="userSearch"
                density="compact"
                variant="outlined"
                placeholder="Benutzer suchen..."
                prepend-inner-icon="mdi-magnify"
                hide-details
                class="search-input"
                clearable
              />
            </div>
          </div>

          <div class="section-toolbar">
            <LTabs v-model="roleTab" :tabs="roleTabs" class="role-tabs" />
          </div>

          <div class="users-table-wrapper">
            <table class="users-table">
              <thead>
                <tr>
                  <th class="th-user">Benutzer</th>
                  <th class="th-progress">Fortschritt</th>
                  <th class="th-status">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="user in filteredUsers"
                  :key="user.username"
                  class="user-row"
                >
                  <td class="td-user">
                      <div class="user-info">
                        <LAvatar
                          :username="user.username"
                          :seed="user.is_llm ? (user.model_id || user.username) : user.avatar_seed"
                          :src="user.is_llm ? null : user.avatar_url"
                          :variant="user.is_llm ? 'bottts-neutral' : 'initials'"
                          size="sm"
                          class="mr-2"
                        />
                        <div class="user-details">
                          <span class="user-name">{{ user.username }}</span>
                          <div class="user-tags">
                            <LTag :variant="roleTab === 'raters' ? 'primary' : 'gray'" size="sm">
                              {{ roleTab === 'raters' ? 'Evaluator' : 'Viewer' }}
                            </LTag>
                            <LTag v-if="user.is_llm" variant="info" size="sm">LLM</LTag>
                          </div>
                        </div>
                      </div>
                  </td>
                  <td class="td-progress">
                    <div class="progress-cell">
                      <div class="mini-progress-bar">
                        <div
                          class="mini-progress-fill"
                          :style="{ width: calculateProgress(user) + '%' }"
                          :class="getProgressClass(calculateProgress(user))"
                        ></div>
                      </div>
                      <span class="progress-text">
                        {{ user.done_threads || 0 }}/{{ user.total_threads || 0 }}
                        <span class="progress-percent">({{ Math.round(calculateProgress(user)) }}%)</span>
                      </span>
                    </div>
                  </td>
                  <td class="td-status">
                    <LTag :variant="getStatusVariant(user)" size="sm">
                      {{ getStatusLabel(user) }}
                    </LTag>
                  </td>
                </tr>
                <tr v-if="!filteredUsers.length">
                  <td colspan="3" class="empty-row">
                    <LIcon class="empty-icon">mdi-account-search</LIcon>
                    <span>Keine Benutzer gefunden</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="dialog-footer">
        <div class="footer-info">
          <LIcon size="14" class="mr-1">mdi-information-outline</LIcon>
          <span>Fortschritt basiert auf zugewiesenen Aufgaben</span>
        </div>
        <LBtn variant="cancel" @click="close">Schließen</LBtn>
      </div>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { getSocket } from '@/services/socketService'
import { logI18n } from '@/utils/logI18n'
import LAvatar from '@/components/common/LAvatar.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  scenario: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue'])

// State
const isFullscreen = ref(false)
const loading = ref(false)
const error = ref(null)
const stats = ref(null)
const userSearch = ref('')
const roleTab = ref('raters')
const subscribedScenarioId = ref(null)

let socket = null
let socketListenersAttached = false

// Computed
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const subtitle = computed(() => {
  if (!props.scenario?.function_type_name) return 'Fortschrittsstatistiken'
  const labels = {
    mail_rating: 'Verlaufsbewertung',
    rating: 'Rating',
    ranking: 'Ranking',
    comparison: 'Gegenüberstellung',
    authenticity: 'Fake/Echt'
  }
  return `${labels[props.scenario.function_type_name] || 'Szenario'} – Fortschritt`
})

const raterStats = computed(() => stats.value?.rater_stats || [])
const evaluatorStats = computed(() => stats.value?.evaluator_stats || [])

const roleTabs = computed(() => {
  const tabs = []
  // raterStats contains EVALUATOR role users (who can interact/rate)
  if (raterStats.value.length || !evaluatorStats.value.length) {
    tabs.push({ value: 'raters', label: `Evaluator (${raterStats.value.length})`, icon: 'mdi-account-check' })
  }
  // evaluatorStats contains VIEWER role users (read-only) and LLMs
  if (evaluatorStats.value.length) {
    tabs.push({ value: 'evaluators', label: `Viewer (${evaluatorStats.value.length})`, icon: 'mdi-account-eye' })
  }
  return tabs
})

const activeUsers = computed(() => (
  roleTab.value === 'evaluators' ? evaluatorStats.value : raterStats.value
))

const filteredUsers = computed(() => {
  if (!userSearch.value) return activeUsers.value
  const search = userSearch.value.toLowerCase()
  return activeUsers.value.filter(u => u.username.toLowerCase().includes(search))
})

const totalAssigned = computed(() => {
  const base = raterStats.value.length ? raterStats.value : activeUsers.value
  return base.reduce((sum, u) => sum + (u.total_threads || 0), 0)
})

const totalDone = computed(() => {
  const base = raterStats.value.length ? raterStats.value : activeUsers.value
  return base.reduce((sum, u) => sum + (u.done_threads || 0), 0)
})

const overallProgress = computed(() => {
  if (!totalAssigned.value) return 0
  return Math.round((totalDone.value / totalAssigned.value) * 100)
})

const totalUsers = computed(() => raterStats.value.length + evaluatorStats.value.length)

// Methods
async function fetchStats() {
  if (!props.scenario?.scenario_id) return
  loading.value = true
  error.value = null

  try {
    const response = await axios.get(`/api/admin/scenario_progress_stats/${props.scenario.scenario_id}`)
    stats.value = response.data
  } catch (err) {
    logI18n('error', 'logs.admin.stats.fetchStatsFailed', err)
    error.value = err.response?.data?.message || 'Fehler beim Laden der Statistiken'
  } finally {
    loading.value = false
  }
}

function calculateProgress(user) {
  if (!user.total_threads) return 0
  return ((user.done_threads || 0) / user.total_threads) * 100
}

function getProgressClass(percent) {
  if (percent >= 80) return 'progress-success'
  if (percent >= 50) return 'progress-accent'
  if (percent >= 25) return 'progress-warning'
  return 'progress-danger'
}

function getStatusLabel(user) {
  if (!user.total_threads) return 'Keine Aufgaben'
  if (!user.done_threads) return 'Neu'
  if (user.done_threads < user.total_threads) return 'In Arbeit'
  return 'Fertig'
}

function getStatusVariant(user) {
  if (!user.total_threads) return 'gray'
  if (!user.done_threads) return 'warning'
  if (user.done_threads < user.total_threads) return 'info'
  return 'success'
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

function close() {
  dialogVisible.value = false
  isFullscreen.value = false
}

function handleSocketStats(payload) {
  if (!payload || payload.kind !== 'progress') return
  if (!props.scenario?.scenario_id || payload.scenario_id !== props.scenario.scenario_id) return
  stats.value = payload.stats
  error.value = null
  loading.value = false
}

function subscribeScenario(scenarioId) {
  if (!socket || !scenarioId) return
  if (subscribedScenarioId.value === scenarioId) return

  if (subscribedScenarioId.value) {
    socket.emit('scenario:unsubscribe', { scenario_id: subscribedScenarioId.value })
  }

  subscribedScenarioId.value = scenarioId
  socket.emit('scenario:subscribe', { scenario_id: scenarioId })
}

function setupSocket() {
  socket = getSocket()
  if (!socket) return

  if (socketListenersAttached) {
    if (socket.connected && props.modelValue && props.scenario?.scenario_id) {
      subscribeScenario(props.scenario.scenario_id)
    }
    return
  }

  socket.on('scenario:stats', handleSocketStats)
  socket.on('scenario:stats_updated', handleSocketStats)
  socket.on('connect', handleSocketConnect)
  socketListenersAttached = true

  if (socket.connected && props.modelValue && props.scenario?.scenario_id) {
    subscribeScenario(props.scenario.scenario_id)
  }
}

function cleanupSocket() {
  if (!socket) return
  socket.off('scenario:stats', handleSocketStats)
  socket.off('scenario:stats_updated', handleSocketStats)
  socket.off('connect', handleSocketConnect)
  if (subscribedScenarioId.value) {
    socket.emit('scenario:unsubscribe', { scenario_id: subscribedScenarioId.value })
  }
  subscribedScenarioId.value = null
  socketListenersAttached = false
}

function handleSocketConnect() {
  if (props.modelValue && props.scenario?.scenario_id) {
    subscribeScenario(props.scenario.scenario_id)
  }
}

// Watchers
watch(() => roleTabs.value, (tabs) => {
  if (!tabs.length) return
  if (!tabs.find(t => t.value === roleTab.value)) {
    roleTab.value = tabs[0].value
  }
})

watch(() => [props.modelValue, props.scenario?.scenario_id], ([isOpen, scenarioId], [wasOpen, prevScenarioId]) => {
  if (!isOpen) {
    cleanupSocket()
    stats.value = null
    error.value = null
    return
  }

  setupSocket()

  if (scenarioId) {
    fetchStats()
    subscribeScenario(scenarioId)
  }
})

onUnmounted(() => {
  cleanupSocket()
})
</script>

<style scoped>
/* LLARS Design Variables */
.stats-dialog {
  --llars-primary: #b0ca97;
  --llars-secondary: #D1BC8A;
  --llars-accent: #88c4c8;
  --llars-success: #98d4bb;
  --llars-warning: #e8c87a;
  --llars-danger: #e8a087;
  --llars-radius: 16px 4px 16px 4px;
  --llars-radius-sm: 8px 2px 8px 2px;

  display: flex;
  flex-direction: column;
  max-height: 90vh;
  overflow: hidden;
  border-radius: var(--llars-radius) !important;
}

/* Header */
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--llars-primary) 0%, var(--llars-accent) 100%);
  color: white;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.header-subtitle {
  font-size: 0.875rem;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.header-actions :deep(.v-btn) {
  color: white !important;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  gap: 16px;
}

.loading-text,
.error-text {
  color: rgba(0, 0, 0, 0.6);
  font-size: 1rem;
}

.error-icon {
  width: 80px;
  height: 80px;
  background: rgba(232, 160, 135, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Content */
.stats-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.fullscreen-content {
  padding: 32px;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.metric-card {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--llars-radius-sm);
  padding: 20px;
  display: flex;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.metric-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.metric-icon.icon-success { background: rgba(152, 212, 187, 0.2); color: #4a9f7e; }
.metric-icon.icon-accent { background: rgba(136, 196, 200, 0.2); color: #5a9a9e; }
.metric-icon.icon-secondary { background: rgba(209, 188, 138, 0.2); color: #9a8a5a; }
.metric-icon.icon-warning { background: rgba(232, 200, 122, 0.2); color: #9a8a4a; }

.metric-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.metric-label {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.6);
  font-weight: 500;
}

.metric-value-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.metric-value {
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
}

.metric-value.text-success { color: #4a9f7e; }
.metric-value.text-accent { color: #5a9a9e; }

.metric-hint {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
}

.progress-bar-container {
  margin-top: 4px;
}

.progress-bar-track {
  height: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--llars-accent);
  border-radius: 3px;
  transition: width 0.5s ease;
}

/* Section Cards */
.section-card {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: var(--llars-radius-sm);
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.section-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.section-icon {
  color: var(--llars-primary);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
  flex: 1;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.search-input {
  max-width: 220px;
}

.search-input :deep(.v-field) {
  border-radius: var(--llars-radius-sm) !important;
}

.role-tabs {
  width: 100%;
}

/* Users Table */
.users-table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 420px;
  position: relative;
  background:
    linear-gradient(white 30%, transparent),
    linear-gradient(transparent, white 70%) 0 100%,
    radial-gradient(farthest-side at 50% 0, rgba(0,0,0,.12), transparent),
    radial-gradient(farthest-side at 50% 100%, rgba(0,0,0,.12), transparent) 0 100%;
  background-repeat: no-repeat;
  background-size: 100% 40px, 100% 40px, 100% 12px, 100% 12px;
  background-attachment: local, local, scroll, scroll;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
}

.users-table th {
  text-align: left;
  padding: 12px 20px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(0, 0, 0, 0.5);
  background: #f9f9f9;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.users-table td {
  padding: 14px 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.user-row {
  cursor: default;
  transition: background-color 0.15s;
}

.user-row:hover {
  background: rgba(176, 202, 151, 0.08);
}

.user-row:last-child td {
  border-bottom: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--llars-radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  flex-shrink: 0;
}

.user-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.user-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.user-name {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.87);
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 160px;
}

.mini-progress-bar {
  height: 6px;
  background: rgba(0, 0, 0, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.mini-progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.mini-progress-fill.progress-success { background: var(--llars-success); }
.mini-progress-fill.progress-accent { background: var(--llars-accent); }
.mini-progress-fill.progress-warning { background: var(--llars-warning); }
.mini-progress-fill.progress-danger { background: var(--llars-danger); }

.progress-text {
  font-size: 0.8125rem;
  color: rgba(0, 0, 0, 0.7);
}

.progress-percent {
  color: rgba(0, 0, 0, 0.5);
}

.empty-row {
  text-align: center;
  padding: 40px 20px !important;
  color: rgba(0, 0, 0, 0.5);
}

.empty-icon {
  margin-right: 8px;
  opacity: 0.5;
}

/* Footer */
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.02);
}

.footer-info {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
}

/* Responsive */
@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .section-toolbar {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
