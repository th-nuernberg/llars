<template>
  <div class="chatbot-activity">
    <!-- Compact Header -->
    <div class="monitor-header">
      <div class="header-left">
        <v-icon size="24" color="white">mdi-robot</v-icon>
        <h2>Chatbot Activity</h2>
        <LTag :variant="connectionVariant" :prepend-icon="connectionIcon" size="small" class="connection-tag">
          {{ connectionLabel }}
        </LTag>
        <div v-if="connectionState === 'connected' && !paused" class="live-pulse"></div>
      </div>
      <div class="header-right">
        <v-select
          v-model="periodFilter"
          :items="periodOptions"
          variant="outlined"
          density="compact"
          hide-details
          class="period-select"
        />
        <LBtn
          :prepend-icon="paused ? 'mdi-play' : 'mdi-pause'"
          :variant="paused ? 'primary' : 'tonal'"
          size="small"
          @click="togglePause"
        >
          {{ paused ? 'Live' : 'Pause' }}
        </LBtn>
        <LBtn
          prepend-icon="mdi-refresh"
          variant="tonal"
          size="small"
          :loading="reloading"
          @click="reload"
        >
          Refresh
        </LBtn>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-bar">
      <div class="stat-card">
        <v-icon size="20" color="primary">mdi-robot</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_category?.chatbot || 0 }}</span>
          <span class="stat-label">Chatbots</span>
        </div>
      </div>
      <div class="stat-card">
        <v-icon size="20" color="accent">mdi-magic-staff</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_category?.wizard || 0 }}</span>
          <span class="stat-label">Wizard</span>
        </div>
      </div>
      <div class="stat-card">
        <v-icon size="20" color="success">mdi-message-text</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_category?.chat || 0 }}</span>
          <span class="stat-label">Chats</span>
        </div>
      </div>
      <div class="stat-card">
        <v-icon size="20" color="info">mdi-folder-multiple</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_category?.collection || 0 }}</span>
          <span class="stat-label">Collections</span>
        </div>
      </div>
      <div class="stat-card">
        <v-icon size="20" color="warning">mdi-file-document-multiple</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.by_category?.document || 0 }}</span>
          <span class="stat-label">Dokumente</span>
        </div>
      </div>
      <div class="stat-card stat-card--total">
        <v-icon size="20" color="grey">mdi-sigma</v-icon>
        <div class="stat-content">
          <span class="stat-value">{{ stats.total_events || 0 }}</span>
          <span class="stat-label">Gesamt</span>
        </div>
      </div>
    </div>

    <!-- Filters Bar -->
    <div class="filters-bar">
      <v-text-field
        v-model="search"
        placeholder="Suche (User, Message)"
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="search-field"
      />
      <v-select
        v-model="typeFilter"
        :items="typeOptions"
        placeholder="Typ"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="type-select"
      />
      <v-text-field
        v-model="userFilter"
        placeholder="User"
        prepend-inner-icon="mdi-account"
        variant="outlined"
        density="compact"
        hide-details
        clearable
        class="user-field"
      />
      <LTag variant="gray" size="small" prepend-icon="mdi-format-list-numbered">
        {{ filteredActivities.length }} Aktivitaten
      </LTag>
    </div>

    <!-- Activities Table -->
    <div class="activities-container">
      <v-skeleton-loader
        v-if="loading"
        type="table"
        class="skeleton-loader"
      />

      <div v-else class="activities-table-wrapper">
        <table class="activities-table">
          <thead>
            <tr>
              <th class="col-time">Zeit</th>
              <th class="col-type">Typ</th>
              <th class="col-user">User</th>
              <th class="col-message">Aktion</th>
              <th class="col-details">Details</th>
            </tr>
          </thead>
          <tbody ref="tableBody">
            <TransitionGroup name="activity-row">
              <tr
                v-for="activity in filteredActivities"
                :key="activity.id"
                :class="['activity-row', { 'activity-row--new': isNewActivity(activity.id) }]"
              >
                <td class="col-time">
                  <span class="time-text">{{ formatTime(activity.created_at) }}</span>
                </td>
                <td class="col-type">
                  <LTag :variant="getTypeVariant(activity.event_type)" size="small">
                    <v-icon size="14" class="mr-1">{{ getTypeIcon(activity.event_type) }}</v-icon>
                    {{ formatEventType(activity.event_type) }}
                  </LTag>
                </td>
                <td class="col-user">
                  <span class="user-text">{{ activity.username || '-' }}</span>
                </td>
                <td class="col-message">
                  <span class="message-text">{{ activity.message }}</span>
                </td>
                <td class="col-details">
                  <div v-if="activity.entity_type || activity.entity_id" class="details-content">
                    <LTag variant="gray" size="small">
                      {{ activity.entity_type }}:{{ activity.entity_id }}
                    </LTag>
                  </div>
                  <LTooltip v-if="activity.details" text="Details anzeigen" location="left">
                    <v-btn
                      icon
                      size="x-small"
                      variant="text"
                      @click="showDetails(activity)"
                    >
                      <v-icon size="16">mdi-information-outline</v-icon>
                    </v-btn>
                  </LTooltip>
                </td>
              </tr>
            </TransitionGroup>
          </tbody>
        </table>

        <div v-if="filteredActivities.length === 0" class="empty-state">
          <v-icon size="48" color="grey">mdi-robot-off</v-icon>
          <p>Keine Chatbot-Aktivitaten vorhanden</p>
        </div>
      </div>
    </div>

    <!-- Details Dialog -->
    <v-dialog v-model="detailsDialog" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-information</v-icon>
          Aktivitats-Details
        </v-card-title>
        <v-card-text>
          <pre class="details-json">{{ JSON.stringify(selectedActivity?.details, null, 2) }}</pre>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <LBtn variant="cancel" @click="detailsDialog = false">Schliessen</LBtn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'

const auth = useAuth()

const activities = ref([])
const stats = ref({})
const loading = ref(true)
const reloading = ref(false)
const paused = ref(false)
const search = ref('')
const typeFilter = ref(null)
const userFilter = ref('')
const periodFilter = ref('24h')
const lastEventId = ref(0)
const tableBody = ref(null)
const detailsDialog = ref(false)
const selectedActivity = ref(null)

// Track new activities for animation
const newActivityIds = ref(new Set())
const NEW_ACTIVITY_DURATION = 2000

const connectionState = ref('disconnected')
const streamAbortController = ref(null)
let reconnectTimer = null

const periodOptions = [
  { title: 'Letzte Stunde', value: '1h' },
  { title: 'Letzte 24h', value: '24h' },
  { title: 'Letzte 7 Tage', value: '7d' },
  { title: 'Letzte 30 Tage', value: '30d' }
]

const typeOptions = [
  { title: 'Alle', value: null },
  { title: 'Chatbot', value: 'chatbot' },
  { title: 'Wizard', value: 'wizard' },
  { title: 'Chat', value: 'chat' },
  { title: 'Collection', value: 'collection' },
  { title: 'Dokument', value: 'document' }
]

const connectionLabel = computed(() => {
  if (paused.value) return 'Pausiert'
  if (connectionState.value === 'connected') return 'Live'
  if (connectionState.value === 'connecting') return 'Verbinde...'
  if (connectionState.value === 'error') return 'Fehler'
  return 'Offline'
})

const connectionVariant = computed(() => {
  if (paused.value) return 'gray'
  if (connectionState.value === 'connected') return 'success'
  if (connectionState.value === 'connecting') return 'warning'
  if (connectionState.value === 'error') return 'danger'
  return 'gray'
})

const connectionIcon = computed(() => {
  if (paused.value) return 'mdi-pause-circle-outline'
  if (connectionState.value === 'connected') return 'mdi-wifi'
  if (connectionState.value === 'connecting') return 'mdi-wifi-sync'
  if (connectionState.value === 'error') return 'mdi-wifi-off'
  return 'mdi-wifi-off'
})

const filteredActivities = computed(() => {
  const q = String(search.value || '').trim().toLowerCase()
  const type = typeFilter.value
  const user = String(userFilter.value || '').trim().toLowerCase()

  return activities.value.filter((a) => {
    if (type && !a.event_type?.startsWith(type + '.')) return false
    if (user && !a.username?.toLowerCase().includes(user)) return false
    if (!q) return true

    const haystack = [
      a.event_type,
      a.message,
      a.username,
      a.entity_type,
      a.entity_id
    ].filter(Boolean).join(' ').toLowerCase()
    return haystack.includes(q)
  })
})

const formatTime = (iso) => {
  try {
    const date = new Date(iso)
    return date.toLocaleTimeString('de-DE', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }) + ' ' + date.toLocaleDateString('de-DE', {
      day: '2-digit',
      month: '2-digit'
    })
  } catch {
    return iso
  }
}

const formatEventType = (type) => {
  if (!type) return '-'
  const parts = type.split('.')
  return parts[1] || parts[0]
}

const getTypeIcon = (type) => {
  if (!type) return 'mdi-help'
  const prefix = type.split('.')[0]
  const action = type.split('.')[1]
  const icons = {
    'chatbot.created': 'mdi-robot-happy',
    'chatbot.updated': 'mdi-robot-outline',
    'chatbot.deleted': 'mdi-robot-off',
    'chatbot.duplicated': 'mdi-content-copy',
    'wizard.started': 'mdi-magic-staff',
    'wizard.completed': 'mdi-check-circle',
    'wizard.failed': 'mdi-alert-circle',
    'wizard.cancelled': 'mdi-close-circle',
    'chat.created': 'mdi-message-plus',
    'chat.deleted': 'mdi-message-off',
    'collection.created': 'mdi-folder-plus',
    'collection.updated': 'mdi-folder-edit',
    'collection.deleted': 'mdi-folder-remove',
    'document.uploaded': 'mdi-file-upload',
    'document.deleted': 'mdi-file-remove'
  }
  return icons[type] || {
    chatbot: 'mdi-robot',
    wizard: 'mdi-magic-staff',
    chat: 'mdi-message-text',
    collection: 'mdi-folder-multiple',
    document: 'mdi-file-document'
  }[prefix] || 'mdi-help'
}

const getTypeVariant = (type) => {
  if (!type) return 'gray'
  const prefix = type.split('.')[0]
  const action = type.split('.')[1]

  // Deleted actions are always warning
  if (action === 'deleted' || action === 'failed' || action === 'cancelled') {
    return 'warning'
  }

  return {
    chatbot: 'primary',
    wizard: 'accent',
    chat: 'success',
    collection: 'info',
    document: 'secondary'
  }[prefix] || 'gray'
}

const isNewActivity = (id) => newActivityIds.value.has(id)

const markAsNew = (id) => {
  newActivityIds.value.add(id)
  setTimeout(() => {
    newActivityIds.value.delete(id)
  }, NEW_ACTIVITY_DURATION)
}

const addActivity = (activity) => {
  if (!activity?.id) return
  if (activity.id <= lastEventId.value) return
  lastEventId.value = activity.id

  markAsNew(activity.id)

  activities.value.unshift(activity)
  if (activities.value.length > 500) {
    activities.value.length = 500
  }
}

const showDetails = (activity) => {
  selectedActivity.value = activity
  detailsDialog.value = true
}

const stopStream = () => {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (streamAbortController.value) {
    streamAbortController.value.abort()
    streamAbortController.value = null
  }
  if (!paused.value) connectionState.value = 'disconnected'
}

const scheduleReconnect = () => {
  if (paused.value) return
  if (reconnectTimer) return
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    startStream()
  }, 2000)
}

const parseAndHandleSseChunk = (chunk, state) => {
  state.buffer += chunk

  const parts = state.buffer.split('\n\n')
  state.buffer = parts.pop() || ''

  for (const part of parts) {
    const lines = part.split('\n')
    let eventName = null
    let id = null
    const dataLines = []

    for (const line of lines) {
      if (line.startsWith('event:')) eventName = line.slice(6).trim()
      else if (line.startsWith('id:')) id = Number(line.slice(3).trim())
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
    }

    if (eventName === 'ping') continue
    const dataStr = dataLines.join('\n').trim()
    if (!dataStr) continue

    try {
      const parsed = JSON.parse(dataStr)
      if (id && parsed && !parsed.id) parsed.id = id
      addActivity(parsed)
    } catch {
      // ignore invalid payloads
    }
  }
}

const startStream = async () => {
  if (paused.value) return
  stopStream()

  const token = auth.getToken()
  if (!token) {
    connectionState.value = 'error'
    return
  }

  connectionState.value = 'connecting'
  const controller = new AbortController()
  streamAbortController.value = controller

  const streamState = { buffer: '' }

  try {
    const url = `/api/admin/chatbot-activity/stream?after_id=${encodeURIComponent(String(lastEventId.value || 0))}`
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`
      },
      signal: controller.signal
    })

    if (!response.ok || !response.body) {
      connectionState.value = 'error'
      scheduleReconnect()
      return
    }

    connectionState.value = 'connected'

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (controller.signal.aborted) break
      parseAndHandleSseChunk(decoder.decode(value, { stream: true }), streamState)
    }

    if (!controller.signal.aborted) {
      connectionState.value = 'error'
      scheduleReconnect()
    }
  } catch (e) {
    if (!controller.signal.aborted) {
      connectionState.value = 'error'
      scheduleReconnect()
    }
  }
}

const loadInitial = async () => {
  loading.value = true
  try {
    const [activitiesRes, statsRes] = await Promise.all([
      axios.get('/api/admin/chatbot-activity', { params: { limit: 200, period: periodFilter.value } }),
      axios.get('/api/admin/chatbot-activity/stats', { params: { period: periodHoursFromFilter(periodFilter.value) } })
    ])

    const list = Array.isArray(activitiesRes.data?.activities) ? activitiesRes.data.activities : []
    activities.value = list.sort((a, b) => (b.id || 0) - (a.id || 0))
    lastEventId.value = activities.value.length ? activities.value[0].id : 0

    stats.value = statsRes.data?.stats || {}
  } catch (e) {
    console.error('Failed to load chatbot activities:', e)
  } finally {
    loading.value = false
  }
}

const periodHoursFromFilter = (filter) => {
  const hours = { '1h': 1, '24h': 24, '7d': 168, '30d': 720 }
  return hours[filter] || 24
}

const reload = async () => {
  reloading.value = true
  try {
    await loadInitial()
    if (!paused.value) startStream()
  } finally {
    reloading.value = false
  }
}

const togglePause = () => {
  paused.value = !paused.value
}

watch(paused, (val) => {
  if (val) {
    stopStream()
    connectionState.value = 'disconnected'
  } else {
    startStream()
  }
})

watch(periodFilter, () => {
  reload()
})

onMounted(async () => {
  await loadInitial()
  startStream()
})

onBeforeUnmount(() => {
  stopStream()
})
</script>

<style scoped>
.chatbot-activity {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  gap: 12px;
}

/* Header */
.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--llars-gradient-hero-cool);
  padding: 12px 16px;
  border-radius: var(--llars-radius);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.connection-tag {
  margin-left: 4px;
}

/* Live pulse indicator */
.live-pulse {
  width: 8px;
  height: 8px;
  background: #4ade80;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7);
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
  100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.period-select {
  width: 140px;
  background: rgba(255,255,255,0.9);
  border-radius: 8px;
}

/* Stats Bar */
.stats-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: var(--llars-radius-sm);
  padding: 10px 14px;
  flex: 1;
  min-width: 120px;
}

.stat-card--total {
  background: rgba(var(--v-theme-primary), 0.08);
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

.stat-label {
  font-size: 0.75rem;
  color: rgb(var(--v-theme-on-surface-variant));
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Filters Bar */
.filters-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  flex-shrink: 0;
}

.search-field {
  flex: 1;
  max-width: 250px;
}

.type-select {
  width: 140px;
  flex-shrink: 0;
}

.user-field {
  width: 150px;
  flex-shrink: 0;
}

/* Activities Container */
.activities-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: rgb(var(--v-theme-surface));
  border-radius: var(--llars-radius-sm);
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.skeleton-loader {
  flex: 1;
}

.activities-table-wrapper {
  flex: 1;
  overflow: auto;
}

/* Custom Table */
.activities-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.activities-table thead {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgb(var(--v-theme-surface));
}

.activities-table th {
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgb(var(--v-theme-on-surface-variant));
  border-bottom: 2px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: linear-gradient(180deg, rgb(var(--v-theme-surface)) 0%, rgba(var(--v-theme-surface), 0.95) 100%);
}

.activities-table td {
  padding: 8px 12px;
  vertical-align: top;
  border-bottom: 1px solid rgba(var(--v-border-color), calc(var(--v-border-opacity) * 0.5));
}

/* Column widths */
.col-time { width: 130px; }
.col-type { width: 140px; }
.col-user { width: 120px; }
.col-message { width: auto; }
.col-details { width: 140px; }

.time-text {
  color: rgb(var(--v-theme-on-surface-variant));
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 0.8rem;
}

.user-text {
  font-weight: 500;
}

.message-text {
  word-break: break-word;
}

.details-content {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* Activity Row Animations */
.activity-row {
  transition: background-color 0.3s ease, opacity 0.3s ease;
}

.activity-row:hover {
  background: rgba(var(--v-theme-primary), 0.04);
}

.activity-row--new {
  animation: highlight-fade 2s ease-out;
}

@keyframes highlight-fade {
  0% { background: rgba(var(--v-theme-success), 0.25); }
  100% { background: transparent; }
}

/* TransitionGroup animations */
.activity-row-enter-active {
  animation: slide-in 0.4s ease-out;
}

.activity-row-leave-active {
  animation: fade-out 0.2s ease-out;
}

.activity-row-move {
  transition: transform 0.3s ease;
}

@keyframes slide-in {
  0% { opacity: 0; transform: translateX(-20px); }
  100% { opacity: 1; transform: translateX(0); }
}

@keyframes fade-out {
  0% { opacity: 1; }
  100% { opacity: 0; }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  gap: 12px;
  color: rgb(var(--v-theme-on-surface-variant));
}

.empty-state p {
  margin: 0;
  font-size: 0.875rem;
}

/* Details Dialog */
.details-json {
  background: rgba(var(--v-theme-on-surface), 0.05);
  padding: 12px;
  border-radius: 8px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Mono', monospace;
  font-size: 0.85rem;
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .filters-bar {
    flex-wrap: wrap;
  }

  .search-field {
    max-width: none;
    flex: 1 1 200px;
  }

  .stats-bar {
    justify-content: center;
  }

  .stat-card {
    flex: 0 0 auto;
  }
}
</style>
